# gh against a review-lab host — auth, `env -u`, and write checks

Deep detail for the `seed-review-lab-prs` skill. The lab is a full github.com clone on
its own hostname with its own auth. Treating it like github.com is the main failure mode.

## Why `env -u GH_TOKEN -u GH_HOST` on every command

`gh` resolves the target host and token in this order:

1. `GH_HOST` env var (forces a host)
2. `GH_TOKEN` / `GITHUB_TOKEN` env var (a token, implicitly for github.com or `GH_HOST`)
3. `--hostname` flag
4. the keyring entry for the resolved host

If your shell exports an enterprise `GH_TOKEN`/`GH_HOST` (common on GitHub-managed
machines), it wins over `--hostname` and the keyring. The result: calls either 401
(wrong token for the lab) or silently hit the wrong server. Unsetting both for the
duration of the command removes the ambiguity, so `--hostname $LAB` and the lab's keyring
entry are what get used.

```bash
GH()  { env -u GH_TOKEN -u GH_HOST gh  "$@"; }
GIT() { env -u GH_TOKEN -u GH_HOST git "$@"; }
```

This same quirk is why `gh agent-task` and `gh project` calls elsewhere use
`env -u GITHUB_TOKEN -u GH_TOKEN` — a set token env var shadows the interactive login.

## Per-host auth is independent

```bash
env -u GH_TOKEN -u GH_HOST gh auth login \
  --hostname "$LAB" --git-protocol https --web --skip-ssh-key
```

- `--web` runs the device/browser OAuth flow against the lab. On the Tailnet the browser
  must reach the lab, so be on Tailscale first.
- This writes a keyring entry for `$LAB` only. Your github.com / enterprise logins are
  untouched, and vice-versa. `gh auth status --hostname $LAB` shows just this host.
- `gh auth setup-git --hostname "$LAB"` installs the git credential helper for the lab
  host so `git clone`/`git push` over HTTPS use the lab token — no PAT in the URL.

Verify before doing anything else:

```bash
env -u GH_TOKEN -u GH_HOST gh api --hostname "$LAB" user -q .login
```

## Write probe (fail fast)

Read access is not write access on some labs. Prove you can write refs before generating
and pushing a whole fixture tree:

```bash
BASE=$(GH api --hostname "$LAB" repos/test/rails/git/ref/heads/main -q .object.sha)
GH api -X POST   --hostname "$LAB" repos/test/rails/git/refs \
  -f ref=refs/heads/gh-write-check -f sha="$BASE"
GH api -X DELETE --hostname "$LAB" repos/test/rails/git/refs/heads/gh-write-check
```

If the POST 403s, the seed will fail — stop and sort auth/permissions first.

## The two sessions gotcha

The lab's browser/XHR session and the `gh`/API session are separate. When profiling via a
browser (or CDP) you can see the HTML page load 200 while the `page_data` XHR returns 401,
because the long-lived cookie still authenticates HTML but the JSON session expired. For
CLI seeding this doesn't bite (you use the API token), but if you later drive the endpoint
from a browser and get 401 on `diff_entries`, re-login in that browser.

## Tailnet + ephemerality

- proxima labs: `*.octoca.ts.net`, corp Tailnet only. `review-lab` labs:
  `*.review-lab.github.com`.
- proxima TTL ~48h, review-lab ~4h. When the lab is recreated it gets a fresh DB — the
  seeded PRs are gone and you re-run `seed-fixture-prs.sh` against the new host. A plain
  branch *redeploy* keeps the DB (and the PRs); only lab recreation wipes them.

## Seed repo

Default is `test/rails` with default branch `main`. Confirm on a given lab:

```bash
GH repo view test/rails --hostname "$LAB" --json nameWithOwner,defaultBranchRef \
  -q '.nameWithOwner + " default=" + .defaultBranchRef.name'
```

If the lab seeds a different repo, pass it as the 2nd arg to the script.
