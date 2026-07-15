#!/usr/bin/env bash
#
# seed-fixture-prs.sh — seed small/medium/large synthetic PRs into a PROXIMA
# review lab's seed repo so a PR render/perf path (e.g. diff_entries) can be
# profiled.
#
# PROXIMA ONLY. This targets throwaway proxima labs (*.octoca.ts.net) that hold
# synthetic data. Do NOT run it against a normal review-lab.github.com lab —
# those carry real production data. The script refuses any non-proxima host.
#
# Usage:
#   seed-fixture-prs.sh <lab-host> [owner/repo] [scenario]
#
#   <lab-host>   e.g. proxima-review-lab-<owner>-<branch>.octoca.ts.net
#                (the host from the .deploy "your lab is available at ..." URL)
#   [owner/repo] seed repo inside the lab to open PRs in (default: test/rails)
#   [scenario]   short slug used in branch names, PR titles, and file paths
#                (default: fixture). Set this per investigation so runs don't
#                collide and the PRs describe what you're testing.
#
# Every gh/git call runs under `env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST` so a
# set enterprise token/host does not shadow the lab host. Requires: gh, git;
# Tailscale for proxima labs. Auth to the lab host must already be done (this
# script does NOT run the interactive `gh auth login` flow).
#
# The script fails closed: any push or PR-create error stops the run instead of
# printing a "ready" URL for a PR that was never created.

set -euo pipefail

LAB="${1:?usage: seed-fixture-prs.sh <lab-host> [owner/repo] [scenario]}"
REPO="${2:-test/rails}"
SCENARIO="${3:-fixture}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d%H%M%S)-$$}"
PREFIX="${SCENARIO}_fixtures"
WORK="${WORK:-$(mktemp -d "${TMPDIR:-/tmp}/lab-seed.XXXXXX")}"
trap 'rm -rf "$WORK"' EXIT

GH()  { env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST gh  "$@"; }
GIT() { env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST git "$@"; }

say() { printf '\n\033[1m==> %s\033[0m\n' "$*" >&2; }
die() { printf '\n\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

# --- 0. proxima guard: refuse non-proxima hosts (they hold real prod data) ---
case "$LAB" in
  *.octoca.ts.net) ;;
  *) die "refusing to seed '$LAB': this skill is proxima-only (*.octoca.ts.net).
  Normal review-lab.github.com labs carry real production data — do not seed them." ;;
esac

# --- 0b. prerequisites -----------------------------------------------------
for cmd in gh git; do
  command -v "$cmd" >/dev/null 2>&1 || die "missing required command: $cmd"
done

# --- 1. auth check (never runs the interactive login flow) -----------------
say "Checking auth to $LAB"
if ! LOGIN=$(GH api --hostname "$LAB" user -q .login 2>/dev/null); then
  die "Not authenticated to $LAB (or host unreachable — proxima labs need Tailscale).
  A CLI agent cannot complete browser OAuth. Ask the user to run, then re-run this script:
    env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST gh auth login --hostname $LAB --git-protocol https --web
    env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST gh auth setup-git --hostname $LAB"
fi
echo "Authenticated as: $LOGIN"
GH auth setup-git --hostname "$LAB" >/dev/null 2>&1 || true

# --- 2. resolve seed repo + default base branch ----------------------------
say "Resolving $REPO on $LAB"
BASE_BRANCH=$(GH repo view "$REPO" --hostname "$LAB" \
  --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null) \
  || die "cannot read $REPO on $LAB — wrong repo, or no read access."
echo "Seed repo $REPO, base branch $BASE_BRANCH"

# --- 3. write probe (per-run ref, fail fast) -------------------------------
say "Confirming write access to $REPO"
PROBE="gh-write-check-${RUN_ID}"
SHA=$(GH api --hostname "$LAB" "repos/$REPO/git/ref/heads/$BASE_BRANCH" -q .object.sha) \
  || die "cannot read base ref heads/$BASE_BRANCH."
GH api -X POST --hostname "$LAB" "repos/$REPO/git/refs" \
  -f "ref=refs/heads/$PROBE" -f "sha=$SHA" >/dev/null \
  || die "no write access to $REPO (create ref failed). Sort auth/permissions first."
GH api -X DELETE --hostname "$LAB" "repos/$REPO/git/refs/heads/$PROBE" >/dev/null || true
echo "Write access confirmed (base $BASE_BRANCH = ${SHA:0:12})"

# --- 4. clone --------------------------------------------------------------
say "Cloning $REPO"
GIT clone --depth 1 --single-branch --branch "$BASE_BRANCH" \
  "https://$LAB/$REPO.git" "$WORK" >/dev/null 2>&1 \
  || die "clone failed for https://$LAB/$REPO.git"
cd "$WORK"
GIT config user.name  "$LOGIN" >/dev/null 2>&1 || true
GIT config user.email "$LOGIN@users.noreply.github.com" >/dev/null 2>&1 || true

# --- 5. generate one ruby fixture file (~200 lines), no external runtime ----
gen_file() {
  # $1 = path, $2 = class seed
  local path="$1" seed="$2" cls sanitized first rest i
  # Portable (BSD/GNU sed, bash 3.2): sanitize to word chars, then force a
  # valid Ruby constant — upper-case first letter, prefix "C" if non-alpha.
  sanitized=$(printf '%s' "$seed" | sed 's/[^A-Za-z0-9]/_/g')
  first=$(printf '%s' "$sanitized" | cut -c1 | tr '[:lower:]' '[:upper:]')
  rest=$(printf '%s' "$sanitized" | cut -c2-)
  case "$first" in [A-Z]) ;; *) first="C$first" ;; esac
  cls="${first}${rest}"
  mkdir -p "$(dirname "$path")"
  {
    printf '# frozen_string_literal: true\n\n'
    printf '# Synthetic fixture %s for render/perf profiling.\n' "$seed"
    printf 'class %s\n' "$cls"
    for i in $(seq 0 39); do
      printf '  def method_%d(a, b, c)\n' "$i"
      printf '    total = a + b + c + %d\n' "$i"
      printf '    total = total * 2 if total.positive?\n'
      printf '    values = [a, b, c].map { |v| v.to_s.rjust(4, "0") }\n'
      printf '    "#{values.join("-")}::#{total}"\n'
      printf '  end\n\n'
    done
    printf 'end\n'
  } > "$path"
}

# --- 6. seed one size: branch, files, commit, push (fail closed), open PR ---
seed_size() {
  # $1 = size label, $2 = file count, $3 = layout(small|dir), $4 = filestem
  local size="$1" count="$2" layout="$3" stem="$4"
  local branch="${SCENARIO}/${size}-${RUN_ID}"
  say "Seeding $size ($count file(s)) on $branch"

  GIT checkout -q "$BASE_BRANCH"
  GIT checkout -q -b "$branch"

  if [ "$layout" = "small" ]; then
    gen_file "$PREFIX/$stem" "${SCENARIO}_${size}"
  else
    local i nn
    for i in $(seq 1 "$count"); do
      nn=$(printf '%02d' "$i")
      gen_file "$PREFIX/$size/${stem}_${nn}.rb" "${SCENARIO}_${size}_${nn}"
    done
  fi

  GIT add -A >/dev/null
  GIT commit -q -m "$SCENARIO fixture: $size ($count file(s))"
  GIT push -q --force-with-lease origin "$branch" \
    || die "push failed for $branch"

  local num
  num=$(GH pr create -R "$REPO" --hostname "$LAB" \
        --head "$branch" --base "$BASE_BRANCH" \
        --title "$SCENARIO fixture: $size ($count files)" \
        --body "Synthetic $size Ruby diff to exercise the render + cache path." \
        | grep -oE '[0-9]+$' | tail -1) \
    || die "pr create failed for $branch"
  [ -n "${num:-}" ] || die "pr create returned no PR number for $branch"

  echo "$size|$num|$layout|$count|$stem"
}

RESULTS=()
RESULTS+=("$(seed_size small   1 small "${SCENARIO}_small.rb")")
RESULTS+=("$(seed_size medium 15 dir   worker)")
RESULTS+=("$(seed_size large  60 dir   handler)")

# --- 7. report ready-to-use endpoint URLs ----------------------------------
# NOTE: the page_data XHR needs a browser user_session cookie, which the gh
# token does NOT provide. These curls are a template — drive them from an
# authenticated browser session (or hand the PR URLs to the user).
ENDPOINT="${ENDPOINT:-page_data/diff_entries}"
say "Seeded PRs (drive the endpoint from an authenticated browser session)"
for row in "${RESULTS[@]}"; do
  IFS='|' read -r size num layout count stem <<<"$row"
  if [ "$layout" = "small" ]; then
    paths="$PREFIX/$stem"
  else
    paths=""
    for i in $(seq 1 "$count"); do
      nn=$(printf '%02d' "$i")
      paths+="$PREFIX/$size/${stem}_${nn}.rb,"
    done
    paths="${paths%,}"
  fi
  echo
  echo "  $size  PR #$num"
  echo "    https://$LAB/$REPO/pull/$num"
  echo "    curl -s -H 'X-Requested-With: XMLHttpRequest' \\"
  echo "      'https://$LAB/$REPO/pull/$num/$ENDPOINT?paths=$paths'"
done

echo
echo "Done. Endpoint needs a browser session; read server ms from x-runtime × 1000."
