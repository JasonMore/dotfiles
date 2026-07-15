#!/usr/bin/env bash
#
# seed-fixture-prs.sh — seed small/medium/large synthetic PRs into a review lab's
# `test/rails` repo so a PR render/perf path (e.g. diff_entries) can be profiled.
#
# Usage:
#   seed-fixture-prs.sh <lab-host> [seed-repo]
#
#   <lab-host>   e.g. proxima-review-lab-<owner>-<branch>.octoca.ts.net
#                (the host from the .deploy "your lab is available at ..." URL)
#   [seed-repo]  owner/repo inside the lab to open PRs in (default: test/rails)
#
# Everything runs under `env -u GH_TOKEN -u GH_HOST` so your enterprise token/host
# does not shadow the lab host. Requires: gh, git, node; Tailscale for proxima labs.

set -euo pipefail

LAB="${1:?usage: seed-fixture-prs.sh <lab-host> [seed-repo]}"
REPO="${2:-test/rails}"
BASE_BRANCH="main"
PREFIX="diff_lines_cache_test"
WORK="${WORK:-/tmp/lab-seed-$$}"

GH() { env -u GH_TOKEN -u GH_HOST gh "$@"; }
GIT() { env -u GH_TOKEN -u GH_HOST git "$@"; }

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

# --- 1. auth check ---------------------------------------------------------
say "Checking auth to $LAB"
if ! LOGIN=$(GH api --hostname "$LAB" user -q .login 2>/dev/null); then
  echo "Not authenticated to $LAB. Run:"
  echo "  env -u GH_TOKEN -u GH_HOST gh auth login --hostname $LAB --git-protocol https --web --skip-ssh-key"
  exit 1
fi
echo "Authenticated as: $LOGIN"
GH auth setup-git --hostname "$LAB" >/dev/null 2>&1 || true

# --- 2. write probe --------------------------------------------------------
say "Confirming write access to $REPO"
SHA=$(GH api --hostname "$LAB" "repos/$REPO/git/ref/heads/$BASE_BRANCH" -q .object.sha)
GH api -X POST --hostname "$LAB" "repos/$REPO/git/refs" \
  -f ref=refs/heads/gh-write-check -f sha="$SHA" >/dev/null
GH api -X DELETE --hostname "$LAB" "repos/$REPO/git/refs/heads/gh-write-check" >/dev/null
echo "Write access confirmed (base $BASE_BRANCH = ${SHA:0:12})"

# --- 3. clone --------------------------------------------------------------
say "Cloning $REPO"
rm -rf "$WORK"
GIT clone --depth 1 --single-branch --branch "$BASE_BRANCH" \
  "https://$LAB/$REPO.git" "$WORK" >/dev/null 2>&1
cd "$WORK"
GIT config user.name  "$LOGIN" >/dev/null 2>&1 || true
GIT config user.email "$LOGIN@users.noreply.github.com" >/dev/null 2>&1 || true

# --- 4. generate one ruby fixture file (~200 lines) ------------------------
gen_file() {
  # $1 = path, $2 = class seed
  local path="$1" seed="$2"
  node -e '
    const fs=require("fs"), path=process.argv[1], seed=process.argv[2];
    const cls=seed.replace(/[^A-Za-z0-9]/g,"_").replace(/^(.)/,(m)=>m.toUpperCase());
    let out=`# frozen_string_literal: true\n\n# Synthetic fixture ${seed} for diff_entries profiling.\nclass ${cls}\n`;
    for (let i=0;i<40;i++){
      out+=`  def method_${i}(a, b, c)\n`;
      out+=`    total = a + b + c + ${i}\n`;
      out+=`    total = total * 2 if total.positive?\n`;
      out+=`    values = [a, b, c].map { |v| v.to_s.rjust(4, "0") }\n`;
      out+=`    "#{values.join("-")}::#{total}"\n`;
      out+=`  end\n\n`;
    }
    out+="end\n";
    fs.mkdirSync(require("path").dirname(path),{recursive:true});
    fs.writeFileSync(path,out);
  ' "$path" "$seed"
}

seed_size() {
  # $1 = size label, $2 = branch, $3 = file count, $4 = layout(small|dir), $5 = filestem
  local size="$1" branch="$2" count="$3" layout="$4" stem="$5"
  say "Seeding $size ($count file(s)) on $branch"
  GIT checkout -q "$BASE_BRANCH"
  GIT branch -q -D "$branch" 2>/dev/null || true
  GIT checkout -q -b "$branch"

  if [ "$layout" = "small" ]; then
    gen_file "$PREFIX/$stem" "$size"
  else
    rm -rf "$PREFIX/$size"
    for i in $(seq 1 "$count"); do
      nn=$(printf '%02d' "$i")
      gen_file "$PREFIX/$size/${stem}_${nn}.rb" "${size}_${nn}"
    done
  fi

  GIT add -A >/dev/null
  GIT commit -q -m "Diff-lines fixture: $size ($count file(s))"
  GIT push -q -f origin "$branch" 2>&1 | tail -1 || true

  local num
  num=$(GH pr create -R "$LAB/$REPO" --head "$branch" --base "$BASE_BRANCH" \
        --title "Diff-lines fixture: $size ($count files)" \
        --body "Synthetic $size Ruby diff to exercise the diff_entries render + cache path." \
        2>/dev/null | grep -oE '[0-9]+$' | tail -1) || true
  if [ -z "${num:-}" ]; then
    # PR may already exist for this head — look it up
    num=$(GH pr list -R "$LAB/$REPO" --head "$branch" --json number -q '.[0].number' 2>/dev/null || true)
  fi
  echo "$size|$num|$layout|$count|$stem"
}

RESULTS=()
RESULTS+=("$(seed_size small  diff-lines-cache/small   1  small sample_small.rb)")
RESULTS+=("$(seed_size medium diff-lines-cache/medium  15 dir   worker)")
RESULTS+=("$(seed_size large  diff-lines-cache/large   60 dir   handler)")

# --- 5. report ready-to-use endpoint URLs ----------------------------------
say "Seeded PRs + diff_entries URLs"
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
  echo "  $size  PR #${num:-?}"
  echo "    https://$LAB/$REPO/pull/${num:-?}"
  echo "    curl -s -H 'X-Requested-With: XMLHttpRequest' \\"
  echo "      'https://$LAB/$REPO/pull/${num:-?}/page_data/diff_entries?paths=$paths'"
done

echo
echo "Done. (Read server ms from the x-runtime response header × 1000.)"
