---
name: seed-review-lab-prs
description: Seed synthetic small/medium/large PRs into a running **proxima** review lab (*.octoca.ts.net) with gh/git against the lab host, then print page_data endpoint URLs for PR render/perf profiling. Use when the user wants test PRs of controlled diff sizes inside a proxima lab to benchmark a page path. Proxima only — never seed a normal review-lab (it carries real prod data). Pairs with deploy-review-lab.
---

# Seed test PRs into a proxima review lab (for PR render / perf testing)

A proxima review lab is a full, throwaway github.com clone running your branch on
the corp Tailnet. To benchmark a PR page path (e.g. the diff `page_data` XHR) you
need **real PRs with controlled diff sizes inside the lab**. This skill creates
them with the `gh` CLI pointed at the **lab host**, then hands you the endpoint
URLs to profile.

It does not deploy the lab — use `deploy-review-lab` for that first. Run this
after the lab is live.

## Proxima labs only — never seed a normal review-lab

This skill is for **proxima** labs (`*.octoca.ts.net`) — private, throwaway
clones with synthetic data that are safe to write junk PRs into.

**Do not** point it at a normal `review-lab.github.com` lab. Those carry **real
production data**, so seeding fixture PRs there is unsafe. If the host is not
`*.octoca.ts.net`, stop.

## When to use this skill

- "Seed the proxima lab with small/medium/large PRs so I can profile diff rendering."
- "I need fixture PRs in the proxima lab to A/B a cache."
- "Push test data into the proxima lab for the `diff_entries` benchmark."

## Before you start: two things a CLI agent cannot do itself

1. **Interactive auth.** Logging into the lab host uses browser OAuth
   (`gh auth login --web`). An agent can't click through it. If the auth check
   fails, **stop and ask the user** to run the login command, then resume. Don't
   try to complete the flow yourself.
2. **Network reach.** Proxima labs sit on the corp Tailnet. If the host doesn't
   resolve, **ask the user to connect Tailscale**. You can't do it for them.

The script fails fast with the exact commands to hand the user when either is
missing.

## The one rule that trips everyone: target the LAB host, not github.com

The lab is a **separate GitHub host** with its **own auth**. A set `GH_TOKEN`,
`GITHUB_TOKEN`, or `GH_HOST` (your enterprise creds) shadows the lab, so every
call 401s or hits the wrong server. So **every** `gh`/`git` command runs under
`env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST` and names the lab host.

```bash
LAB=<host from the .deploy "done!" URL>
GH="env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST gh"
```

## Lab facts

Proxima labs are on the corp **Tailnet**, so you must be on Tailscale to reach
them:

| host shape | network | TTL |
|------------|---------|-----|
| `proxima-review-lab-<owner>-<branch>.octoca.ts.net` | corp Tailnet (Tailscale) | ~48h |

The lab is ephemeral: when it is **recreated** its DB resets and the seeded PRs
are gone — re-seed. A plain branch **redeploy** keeps the DB and the PRs.

## Fast path

```bash
scripts/seed-fixture-prs.sh <lab-host> [owner/repo] [scenario]
# auth-checks, resolves the base branch, clones the seed repo, generates
# small/medium/large fixtures, pushes 3 unique branches, opens 3 PRs, prints
# their numbers + endpoint URLs. Fails closed if any push/PR-create fails.
```

`scenario` (default `fixture`) names the branches, PR titles, and fixture paths.
**Set it per investigation** (e.g. `diff-lines-cache`) so parallel runs don't
collide and the PRs say what they test. The seed repo defaults to `test/rails`;
pass a different `owner/repo` if the lab seeds another.

Then jump to [Drive the endpoint](#5-drive-the-endpoint). The rest of this doc is
the manual flow the script automates, plus recovery when a step fails.

## Manual flow

### 1. Authenticate to the lab host (user does this once per lab)

```bash
env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST gh auth login \
  --hostname "$LAB" --git-protocol https --web
$GH api --hostname "$LAB" user -q .login      # verify: prints your lab login
$GH auth setup-git --hostname "$LAB"          # wire git to use this host's token
```

Auth is per-host: this creates a lab-only entry and does not touch your
github.com login. (`--web` is interactive — see the boundary above.)

### 2. Prove write access before doing work

Create then delete a throwaway ref. If this fails, stop — seeding will fail too.

```bash
BASE=$($GH api --hostname "$LAB" repos/<owner/repo>/git/ref/heads/<base> -q .object.sha)
$GH api -X POST --hostname "$LAB" repos/<owner/repo>/git/refs \
  -f ref=refs/heads/gh-write-check-$$ -f sha="$BASE"
$GH api -X DELETE --hostname "$LAB" repos/<owner/repo>/git/refs/heads/gh-write-check-$$ \
  && echo "write confirmed"
```

### 3. Clone the seed repo

```bash
WORK=$(mktemp -d) 
env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST git clone --depth 1 --single-branch \
  --branch <base> "https://$LAB/<owner/repo>.git" "$WORK"
```

### 4. Generate fixtures, push, open PRs

**Diff size is the independent variable** — keep three tiers so perf differences
show (wins concentrate on large diffs). The script uses small (1 file), medium,
and large (many files), each ~200+ lines so the diff is real. For each size:
make a **uniquely named** branch off base (`<scenario>/<size>-<run-id>`), write
the files, commit, `push --force-with-lease`, then open the PR **in the lab**:

```bash
$GH pr create -R "<owner/repo>" --hostname "$LAB" \
  --head <scenario>/<size>-<run-id> --base <base> \
  --title "<scenario> fixture: <size>" --body "Synthetic diff to exercise the render path."
```

Unique branch names matter: a shared lab may have other seeders, and
force-pushing a fixed branch would clobber their work.

### 5. Drive the endpoint

Each PR now exists at `/<owner/repo>/pull/<n>`. Hit the page_data XHR with the
file list. The XHR path **requires** `X-Requested-With: XMLHttpRequest` (without
it you get the HTML shell, not JSON):

```
GET https://$LAB/<owner/repo>/pull/<n>/page_data/diff_entries?paths=<csv>
    -H 'X-Requested-With: XMLHttpRequest'
```

**Auth caveat:** this endpoint needs a browser `user_session` cookie. The `gh`
token does **not** grant one, so a raw `curl` with the CLI token gets redirected
to login. Drive the URL from an **authenticated browser session** (or a cookie
copied from one) — or just hand the PR URLs to the user. Read server timing off
the `x-runtime` response header (×1000 = ms).

## Verify

```bash
$GH pr list -R "<owner/repo>" --hostname "$LAB"
$GH api --hostname "$LAB" repos/<owner/repo>/pulls/<n> \
  -q '.title + " files=" + (.changed_files|tostring) + " +" + (.additions|tostring)'
```

## Gotchas

- **`env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST` on every call.** The #1 failure
  mode. A set `GITHUB_TOKEN` alone is enough to send you to github.com.
- **Auth + Tailscale are the user's job.** Ask; don't try to automate them.
- **Ephemeral:** lab recreation wipes the DB; re-run the script. A branch
  redeploy keeps the seeded PRs.
- **XHR needs a browser session**, separate from the CLI token and from the HTML
  page session — each can expire on its own.

## Boundaries

Stops at "PRs exist in the lab and the endpoint URLs are printed." It does not
deploy the lab (`deploy-review-lab`), authenticate for you, connect Tailscale, or
run the profiling sweep itself.

## References

- `references/gh-lab-host-auth.md` — per-host auth, the `env -u` rule, the write
  probe, browser-vs-CLI sessions, Tailnet + ephemerality.
