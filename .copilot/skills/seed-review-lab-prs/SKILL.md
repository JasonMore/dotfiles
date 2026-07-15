---
name: seed-review-lab-prs
description: Use when the user wants to seed synthetic test PRs into a running review lab so a PR's render or perf path can be exercised over real HTTP — phrases like "create test PRs in the review lab", "seed the proxima lab with PRs", "add small/medium/large diff PRs to the lab", "push test data to review-lab for profiling", "make fixture PRs to benchmark diff_entries". Drives `gh`/`git` against the lab HOST (not github.com), creates PRs in the lab's seed repo, and prints ready-to-use endpoint URLs. Pairs with `deploy-review-lab` (which only deploys the lab).
---

# Seed test PRs into a review lab (for PR render / perf testing)

A review lab (`review-lab`, `proxima-review-lab`) is a full, throwaway github.com clone
running your branch. To benchmark a PR page path (e.g. the diff `page_data` XHR) you need
**real PRs with controlled diff sizes inside the lab**. This skill creates them with the
`gh` CLI pointed at the **lab host**, then hands you the endpoint URLs to profile.

It does not deploy the lab — use `deploy-review-lab` for that first. Run this after the
lab is live.

## When to use this skill

- "Seed the proxima lab with small/medium/large PRs so I can profile diff rendering."
- "I need fixture PRs in the review lab to A/B a cache."
- "Push test data into the lab for the `diff_entries` benchmark."

## The one rule that trips everyone: target the LAB host, not github.com

The lab is a **separate GitHub host** with its **own auth**. A set `GH_TOKEN`/`GH_HOST`
(your enterprise creds) shadows the lab, so every call 401s or hits the wrong server. So
**every** `gh`/`git` command runs under `env -u GH_TOKEN -u GH_HOST` and names the lab
host.

```bash
LAB=proxima-review-lab-<owner>-<branch>.octoca.ts.net   # from the .deploy "done!" URL
GH="env -u GH_TOKEN -u GH_HOST gh"
```

- proxima labs are on the corp **Tailnet** (`*.octoca.ts.net`) — be on Tailscale.
- Labs are **ephemeral** (proxima ~48h). After a fresh deploy, re-seed.
- The seed repo inside the lab is usually **`test/rails`** (default branch `main`). Confirm
  with `$GH repo view test/rails --hostname $LAB`.

## Fast path

```bash
scripts/seed-fixture-prs.sh <lab-host>
# auth-checks, clones test/rails, generates small/medium/large fixtures,
# pushes 3 branches, opens 3 PRs, prints their numbers + diff_entries URLs.
```

Then jump to [Drive the endpoint](#5-drive-the-endpoint-why-you-seeded). The rest of this
doc is the manual flow the script automates, plus recovery when a step fails.

## Manual flow

### 1. Authenticate to the lab host (once per lab)

```bash
env -u GH_TOKEN -u GH_HOST gh auth login \
  --hostname "$LAB" --git-protocol https --web --skip-ssh-key
$GH api --hostname "$LAB" user -q .login      # verify: prints your lab login
$GH auth setup-git --hostname "$LAB"          # wire git to use this host's token
```

Auth is per-host: this creates a lab-only entry and does not touch your github.com login.

### 2. Prove write access before doing work

Create then delete a throwaway ref. If this fails, stop — seeding will fail too.

```bash
BASE=$($GH api --hostname "$LAB" repos/test/rails/git/ref/heads/main -q .object.sha)
$GH api -X POST --hostname "$LAB" repos/test/rails/git/refs \
  -f ref=refs/heads/gh-write-check -f sha="$BASE"
$GH api -X DELETE --hostname "$LAB" repos/test/rails/git/refs/heads/gh-write-check \
  && echo "write confirmed"
```

### 3. Clone the seed repo

```bash
WORK=/tmp/lab-seed && rm -rf "$WORK"
env -u GH_TOKEN -u GH_HOST git clone --depth 1 --single-branch --branch main \
  "https://$LAB/test/rails.git" "$WORK"
```

### 4. Generate fixtures, push, open PRs

**Diff size is the independent variable** — keep three tiers so perf differences show
(wins concentrate on large diffs). The convention used for the diff-lines work:

| size   | files | path prefix                              |
|--------|------:|------------------------------------------|
| small  | 1     | `diff_lines_cache_test/sample_small.rb`  |
| medium | 15    | `diff_lines_cache_test/medium/worker_NN.rb` |
| large  | 60    | `diff_lines_cache_test/large/handler_NN.rb` |

For each size: make a branch off `main`, write the files (~200 lines each so the diff is
real), commit, push, then open the PR **in the lab**:

```bash
$GH pr create -R "$LAB/test/rails" \
  --head diff-lines-cache/<size> --base main \
  --title "Diff-lines fixture: <size>" --body "Synthetic diff to exercise diff_entries."
```

`scripts/seed-fixture-prs.sh` does all three sizes and prints the resulting PR numbers.

### 5. Drive the endpoint (why you seeded)

Each PR now exists at `/test/rails/pull/<n>`. Hit the page_data XHR with the file list.
The XHR path **requires** `X-Requested-With: XMLHttpRequest` (without it you get the HTML
shell, not JSON):

```
GET https://$LAB/test/rails/pull/<n>/page_data/diff_entries?paths=<comma-separated-files>
    -H 'X-Requested-With: XMLHttpRequest'
```

The script prints a ready URL per PR. Read the server timing off the `x-runtime` response
header (×1000 = ms) and compare response bytes for correctness.

## Verify

```bash
$GH pr list -R "$LAB/test/rails"
$GH api --hostname "$LAB" repos/test/rails/pulls/<n> \
  -q '.title + " files=" + (.changed_files|tostring) + " +" + (.additions|tostring)'
```

## Gotchas

- **`env -u GH_TOKEN -u GH_HOST` on every call.** The #1 failure mode.
- **Tailnet:** proxima labs only resolve on Tailscale.
- **Ephemeral:** the lab expires; re-run the script against the new host.
- **Seed PRs survive branch redeploys** — they live in the lab's DB, not your git branch.
  You only re-seed when the *lab itself* is recreated.
- **XHR needs `X-Requested-With`**, and the lab's XHR session can expire independently of
  the HTML session — if page_data 401s while the HTML page loads, re-auth (step 1).

## Boundaries

Stops at "PRs exist in the lab and the diff_entries URLs are printed." It does not deploy
the lab (`deploy-review-lab`) or run the profiling sweep itself.

## References

- `references/gh-lab-host-auth.md` — per-host auth, `env -u`, write-probe, Tailnet detail.
