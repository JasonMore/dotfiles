#!/usr/bin/env bash
#
# copilot-notify.sh
# Watches remote Copilot coding-agent tasks (+ optional Codespaces) and fires a
# macOS push notification the moment an agent ENDS a run, or needs your input.
#
# "Agent ended"  = a task transitions in_progress -> (idle | completed | waiting_for_user).
# "Needs input"  = task state is waiting_for_user.
# "Ready to review" = completed task whose PR is OPEN.
#
# Detection is transition-based: it snapshots every task's state each poll and
# notifies on the CHANGE, so you get pinged within ~$INTERVAL seconds of the
# agent stopping. This is polling (not push); set INTERVAL low for low latency.
#
# Usage:
#   ./copilot-notify.sh            # poll once (seeds snapshot on first run)
#   ./copilot-notify.sh --loop     # poll forever every $INTERVAL seconds
#   ./copilot-notify.sh --dry-run  # print current states, no notify/snapshot write
#
# Env knobs:
#   INTERVAL=5              seconds between polls in --loop mode (default 5)
#   INCLUDE_CODESPACES=1    also ping when a codespace becomes Available
#   STATE_DIR=~/.copilot    where the snapshot lives
#
# Auth: strips GH_TOKEN/GITHUB_TOKEN (a PAT missing codespace/OAuth scopes) so
# gh uses the keyring account that has them.

set -uo pipefail

INTERVAL="${INTERVAL:-5}"
STATE_DIR="${STATE_DIR:-$HOME/.copilot}"
SNAP_FILE="$STATE_DIR/notify-snapshot.tsv"      # id<TAB>state<TAB>name
INCLUDE_CODESPACES="${INCLUDE_CODESPACES:-1}"

# --- Cloud coding-agent tasks ----------------------------------------------
# poll_once watches `gh agent-task list` (cloud/remote coding-agent tasks). The
# GitHub Copilot DESKTOP APP already fires its own notifications for ALL of your
# cloud tasks regardless of where they were started, so these are redundant and
# OFF by default. Set MONITOR_CLOUD=1 to re-enable (e.g. on a machine without the
# app installed).
MONITOR_CLOUD="${MONITOR_CLOUD:-0}"

# Source of an agent's last response text (Line 2 of every notification).
SESSION_STORE_DB="${SESSION_STORE_DB:-$STATE_DIR/session-store.db}"
# Max chars of the response shown on Line 2.
BODY_MAX="${BODY_MAX:-100}"

# --- Codespace agents ------------------------------------------------------
# Copilot CLI agents running INSIDE codespaces keep their own session-store.db.
# We SSH into each Available codespace ~every CS_INTERVAL seconds, read the
# latest completed turn per session, and notify when a new turn appears.
CS_INTERVAL="${CS_INTERVAL:-30}"
CS_SNAP="$STATE_DIR/notify-codespace-snapshot.tsv"   # name<TAB>session_id<TAB>last_turn

# --- Local terminal Copilot CLI sessions -----------------------------------
# The GitHub Copilot DESKTOP APP already fires its own notifications for the
# sessions you start in it, so we deliberately DO NOT ping those. Instead we
# watch local *terminal* `copilot` CLI sessions, which the app never notifies
# about. Their state lives in ~/.copilot/session-store.db (same schema the
# codespace poller reads remotely); a finished turn = a new non-empty
# assistant_response. App sessions are separated out by cwd: the app runs its
# sessions under $HOME/.copilot/ (copilot-worktrees/ and chats/), terminal CLI
# sessions run in real repo dirs. Detection is turn-based (is_running is NOT
# maintained for CLI sessions), mirroring poll_codespaces but against the local db.
MONITOR_LOCAL="${MONITOR_LOCAL:-1}"
# cwd prefix that marks an app-managed (not terminal-CLI) session; excluded.
LOCAL_EXCLUDE_PREFIX="${LOCAL_EXCLUDE_PREFIX:-$HOME/.copilot/}"
# Only consider sessions touched within this window (bounds the query + snapshot).
LOCAL_MAX_AGE="${LOCAL_MAX_AGE:-2 days}"
# State file cols: session_id<TAB>last_turn
LOCAL_SNAP="$STATE_DIR/notify-local-turns.tsv"

DRY_RUN=0; LOOP=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --loop)    LOOP=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

mkdir -p "$STATE_DIR"; touch "$SNAP_FILE"

# Run a command with a timeout. Prefers gtimeout/timeout, falls back to perl's
# alarm (always present on macOS) so a hung gh/SSH call can't stall the loop.
run_to() {
  local secs="$1"; shift
  if command -v gtimeout >/dev/null 2>&1; then gtimeout "$secs" "$@";
  elif command -v timeout  >/dev/null 2>&1; then timeout  "$secs" "$@";
  elif command -v perl     >/dev/null 2>&1; then perl -e 'alarm shift; exec @ARGV' "$secs" "$@";
  else "$@"; fi
}

gh_k() {
  run_to 20 env -u GH_TOKEN -u GITHUB_TOKEN gh "$@"
}

notify() {
  local title="$1" msg="$2"
  title=${title//\"/\\\"}; msg=${msg//\"/\\\"}
  osascript -e "display notification \"$msg\" with title \"$title\" sound name \"Glass\"" >/dev/null 2>&1
}

# gh with a longer timeout, for slow codespace SSH calls.
gh_cs() {
  run_to 60 env -u GH_TOKEN -u GITHUB_TOKEN gh "$@"
}

# Truncate a string to $BODY_MAX chars for Line 2.
body_trunc() {
  local s="$1"
  s="${s//$'\n'/ }"; s="${s//$'\t'/ }"
  [ "${#s}" -gt "$BODY_MAX" ] && s="${s:0:$BODY_MAX}…"
  printf '%s' "$s"
}

# Last 2 path segments of a filesystem path: /a/b/c/d -> c/d
dir_tail() {
  local p="${1%/}"
  [ -z "$p" ] && return 0
  local base="${p##*/}" rest="${p%/*}" parent
  parent="${rest##*/}"
  if [ -n "$parent" ] && [ "$parent" != "$base" ]; then
    printf '%s/%s' "$parent" "$base"
  else
    printf '%s' "$base"
  fi
}

# Current task snapshot: id<TAB>state<TAB>shortname<TAB>repo<TAB>pr<TAB>prstate
snapshot_tasks() {
  gh_k agent-task list --limit 100 \
    --json id,name,state,pullRequestNumber,pullRequestState,repository \
    --jq '.[] | "\(.id)\t\(.state)\t\((.name // "untitled")[0:70])\t\(.repository // "-")\t\(.pullRequestNumber // "-")\t\(.pullRequestState // "-")"' \
    2>/dev/null
}

# Snapshot of local terminal-CLI sessions with their latest COMPLETED turn.
# Emits: session_id<TAB>turn_index<TAB>cwd<TAB>response  (one row per active CLI
# session). App-managed sessions (cwd under $LOCAL_EXCLUDE_PREFIX) are excluded,
# as are those with no cwd. Only sessions updated within $LOCAL_MAX_AGE count.
snapshot_local() {
  [ -f "$SESSION_STORE_DB" ] || return 0
  local esc
  esc="$(printf '%s' "$LOCAL_EXCLUDE_PREFIX" | sed "s/'/''/g")"
  sqlite3 -noheader -separator $'\t' "file:$SESSION_STORE_DB?mode=ro" "
    SELECT s.id,
           t.turn_index,
           s.cwd,
           substr(replace(replace(t.assistant_response,char(10),' '),char(13),' '),1,$BODY_MAX)
    FROM sessions s
    JOIN turns t ON t.session_id = s.id
    WHERE s.updated_at > datetime('now','-$LOCAL_MAX_AGE')
      AND s.cwd IS NOT NULL AND trim(s.cwd) <> ''
      AND s.cwd NOT LIKE '${esc}%'
      AND t.assistant_response IS NOT NULL AND trim(t.assistant_response) <> ''
      AND t.turn_index = (SELECT MAX(t2.turn_index) FROM turns t2
                          WHERE t2.session_id = s.id
                            AND t2.assistant_response IS NOT NULL
                            AND trim(t2.assistant_response) <> '');
  " 2>/dev/null
}

# Watch local terminal-CLI sessions; notify ONCE per newly-completed turn.
# Turn-based (is_running is not maintained for CLI sessions), mirroring
# poll_codespaces but against the local session-store.db. State ($LOCAL_SNAP):
# session_id<TAB>last_turn. Global seed suppression: on the daemon's very first
# run (snapshot file empty) record every session's current max turn WITHOUT
# notifying, to avoid a startup flood from the historical backlog. After that a
# brand-new session (no prior row -> pturn=-1) fires on its first completed turn,
# and any session fires whenever its turn_index advances.
poll_local() {
  [ "$MONITOR_LOCAL" = "1" ] || return 0
  command -v sqlite3 >/dev/null 2>&1 || return 0
  local cur pinged=0 seeding=0 out=""
  [ ! -s "$LOCAL_SNAP" ] && seeding=1
  cur="$(snapshot_local)"           # id<TAB>turn<TAB>cwd<TAB>response
  [ -z "$cur" ] && return 0

  while IFS=$'\t' read -r id turn cwd resp; do
    [ -z "${id:-}" ] && continue
    [ -z "${turn:-}" ] && continue

    if [ "$DRY_RUN" = "1" ]; then
      printf 'local  [local : %s]  turn=%s  %s\n' "$(dir_tail "$cwd")" "$turn" "$resp"
      continue
    fi

    local prior pturn
    prior="$(grep -F "$id"$'\t' "$LOCAL_SNAP" 2>/dev/null | head -1)"
    pturn="$(printf '%s' "$prior" | cut -f2)"; [ -z "$pturn" ] && pturn=-1

    if [ "$seeding" != "1" ] && [ "$turn" -gt "$pturn" ] 2>/dev/null; then
      notify "local : $(dir_tail "$cwd")" "$(body_trunc "$resp")"
      pinged=$((pinged + 1))
    fi
    out="${out}${id}	${turn}
"
  done <<< "$cur"

  [ "$DRY_RUN" = "1" ] && return 0
  printf '%s' "$out" > "$LOCAL_SNAP"
  [ "$seeding" = "1" ] && echo "$(date '+%H:%M:%S')  seeded local snapshot" || echo "$(date '+%H:%M:%S')  local pings=$pinged"
}

poll_once() {
  [ "$MONITOR_CLOUD" = "1" ] || return 0
  local cur pinged=0
  cur="$(snapshot_tasks)"
  [ -z "$cur" ] && { echo "$(date '+%H:%M:%S')  no tasks / auth issue"; return; }

  local seeding=0
  [ ! -s "$SNAP_FILE" ] && seeding=1   # first ever run: seed only, don't flood

  while IFS=$'\t' read -r id st name repo prnum prstate; do
    [ -z "${id:-}" ] && continue
    local old
    old="$(grep -F "$id"$'\t' "$SNAP_FILE" | head -1 | cut -f2)"
    [ -z "$old" ] && old="__new__"

    if [ "$DRY_RUN" = "1" ]; then
      printf '%-14s %s\n' "$st" "$name"
      continue
    fi
    [ "$seeding" = "1" ] && continue
    [ "$st" = "$old" ] && continue     # no change, skip

    # Fire only on meaningful transitions
    case "$st" in
      idle|completed|waiting_for_user)
        if [ "$old" = "in_progress" ] || [ "$old" = "__new__" ]; then
          local title msg
          title="cloud : ${repo:--}"
          [ "$prnum" != "-" ] && title="$title#$prnum"
          msg="$name · $st"
          [ "$prnum" != "-" ] && [ "$prstate" != "-" ] && msg="$msg ($prstate)"
          notify "$title" "$(body_trunc "$msg")"; pinged=$((pinged+1))
        fi
        ;;
    esac
  done <<< "$cur"

  # Persist new snapshot
  if [ "$DRY_RUN" != "1" ]; then
    printf '%s\n' "$cur" | cut -f1-3 > "$SNAP_FILE"
    if [ "$seeding" = "1" ]; then
      echo "$(date '+%H:%M:%S')  seeded snapshot ($(grep -c . "$SNAP_FILE") tasks), no pings"
    else
      echo "$(date '+%H:%M:%S')  pings=$pinged"
    fi
  fi
}

# Shorten a codespace slug: strip a trailing random hash token.
#   stage-ui-ghost-author-55g55gv47c4455 -> stage-ui-ghost-author
cs_label() {
  local name="$1" last="${1##*-}"
  case "$last" in
    *[0-9]*) [ "${#last}" -ge 6 ] && name="${name%-*}" ;;
  esac
  printf '%s' "$name"
}

# Poll Copilot CLI agents running inside Available codespaces. For each, SSH in,
# read the latest completed turn per session from its session-store.db, and
# notify when a session's turn_index increases (a new response landed).
# State ($CS_SNAP): name<TAB>session_id<TAB>last_turn. Seeds silently on first run.
poll_codespaces() {
  [ "$INCLUDE_CODESPACES" = "1" ] || return 0
  local seeding=0 pinged=0 out=""
  [ ! -s "$CS_SNAP" ] && seeding=1

  local names
  names="$(gh_cs codespace list --json name,state,repository \
            --jq '.[] | select(.state=="Available") | "\(.name)\t\(.repository // "-")"' 2>/dev/null)"
  [ -z "$names" ] && { [ "$DRY_RUN" != "1" ] && echo "$(date '+%H:%M:%S')  codespaces: none available"; return 0; }

  # Codespaces ship python3 (with sqlite3) but not the sqlite3 CLI. We base64 a
  # small python program locally and decode+run it remotely to dodge SSH quoting.
  local pysrc b64
  pysrc="import sqlite3,os
p=os.path.expanduser('~/.copilot/session-store.db')
try:
    c=sqlite3.connect('file:%s?mode=ro'%p,uri=True)
except Exception:
    raise SystemExit(0)
q=\"\"\"
SELECT t.session_id, t.turn_index,
       substr(replace(replace(t.assistant_response,char(10),' '),char(13),' '),1,${BODY_MAX})
FROM turns t
WHERE t.assistant_response IS NOT NULL AND trim(t.assistant_response)<>''
  AND t.turn_index=(SELECT MAX(turn_index) FROM turns t2
                    WHERE t2.session_id=t.session_id
                      AND t2.assistant_response IS NOT NULL
                      AND trim(t2.assistant_response)<>'')
\"\"\"
try:
    for r in c.execute(q):
        print('%s|%s|%s'%(r[0],r[1],(r[2] or '').replace('|','/')))
except Exception:
    pass"
  b64="$(printf '%s' "$pysrc" | base64 | tr -d '\n')"

  local name repo rows
  while IFS=$'\t' read -r name repo; do
    [ -z "${name:-}" ] && continue
    local reptail="${repo##*/}"
    local label
    label="$(cs_label "$name")"

    rows="$(gh_cs codespace ssh -c "$name" -- "echo $b64 | base64 -d | python3" 2>/dev/null)"

    while IFS='|' read -r sid turn resp; do
      [ -z "${sid:-}" ] && continue
      [ -z "${turn:-}" ] && continue

      if [ "$DRY_RUN" = "1" ]; then
        printf 'codespace %s/%s  session=%s turn=%s  %s\n' "$label" "$reptail" "$sid" "$turn" "$resp"
        continue
      fi

      local prior pturn
      prior="$(grep -F "$name	$sid	" "$CS_SNAP" 2>/dev/null | head -1)"
      pturn="$(printf '%s' "$prior" | cut -f3)"; [ -z "$pturn" ] && pturn=-1

      if [ "$seeding" != "1" ] && [ "$turn" -gt "$pturn" ] 2>/dev/null; then
        notify "codespace : $label/$reptail" "$(body_trunc "$resp")"
        pinged=$((pinged + 1))
      fi
      out="${out}${name}	${sid}	${turn}
"
    done <<< "$rows"
  done <<< "$names"

  [ "$DRY_RUN" = "1" ] && return 0
  printf '%s' "$out" > "$CS_SNAP"
  [ "$seeding" = "1" ] && echo "$(date '+%H:%M:%S')  seeded codespace snapshot" || echo "$(date '+%H:%M:%S')  codespace pings=$pinged"
}

if [ "$LOOP" = "1" ]; then
  # Single-instance guard: prevent launchd/manual double-spawn from running two
  # loops that collide on gh calls. Atomic mkdir lock storing our PID.
  LOCK_DIR="$STATE_DIR/notify.lock"
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    old_pid="$(cat "$LOCK_DIR/pid" 2>/dev/null)"
    if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
      echo "$(date '+%H:%M:%S')  another instance (pid $old_pid) is running; exiting"
      exit 0
    fi
    # stale lock: take it over
    rm -rf "$LOCK_DIR"; mkdir "$LOCK_DIR"
  fi
  echo $$ > "$LOCK_DIR/pid"
  trap 'rm -rf "$LOCK_DIR"' EXIT INT TERM

  echo "Watching every ${INTERVAL}s (pid $$). Ctrl-C to stop."
  cs_last=$((SECONDS - CS_INTERVAL))   # run codespace poll on first iteration
  while true; do
    poll_once
    poll_local
    if [ "$INCLUDE_CODESPACES" = "1" ] && [ $((SECONDS - cs_last)) -ge "$CS_INTERVAL" ]; then
      poll_codespaces
      cs_last=$SECONDS
    fi
    sleep "$INTERVAL"
  done
else
  poll_once
  poll_local
  poll_codespaces
fi
