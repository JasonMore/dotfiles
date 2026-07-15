# gh against a review-lab host — auth, `env -u`, and write checks

Deep detail for the `seed-review-lab-prs` skill. The lab is a full github.com clone on
its own hostname with its own auth. Treating it like github.com is the main failure mode.

## Why `env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST` on every command

`gh` resolves the target host and token in this order:

1. `GH_HOST` env var (forces a host)
2. `GH_TOKEN` / `GITHUB_TOKEN` env var (a token, implicitly for github.com or `GH_HOST`)
3. `--hostname` flag
4. the keyring entry for the resolved host

If your shell exports an enterprise `GH_TOKEN`, `GITHUB_TOKEN`, or `GH_HOST` (common on
GitHub-managed machines and in agent/CI environments), it wins over `--hostname` and the
keyring. The result: calls either 401 (wrong token for the lab) or silently hit the wrong
server. **A set `GITHUB_TOKEN` alone is enough** to send you to github.com even with
`--hostname` present, so unset all three. Unsetting them for the duration of the command
removes the ambiguity, so `--hostname $LAB` and the lab's keyring entry are what get used.

```bash
GH()  { env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST gh  "$@"; }
GIT() { env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST git "$@"; }
```

This same quirk is why `gh agent-task` and `gh project` calls elsewhere use
`env -u GITHUB_TOKEN -u GH_TOKEN` — a set token env var shadows the interactive login.

## Per-host auth is independent (and interactive — the user's job)

```bash
env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST gh auth login \
  --hostname "$LAB" --git-protocol https --web
```

- `--web` runs the browser OAuth flow against the lab. **A CLI agent cannot complete this**
  — if the auth check fails, stop and ask the user to run this command, then resume.
- On the Tailnet the browser must reach the lab, so the user must be on Tailscale first.
- This writes a keyring entry for `$LAB` only. Your github.com / enterprise logins are
  untouched, and vice-versa. `gh auth status --hostname $LAB` shows just this host.
- `gh auth setup-git --hostname "$LAB"` installs the git credential helper for the lab
  host so `git clone`/`git push` over HTTPS use the lab token — no PAT in the URL.

Verify before doing anything else:

```bash
env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST gh api --hostname "$LAB" user -q .login
```

## Write probe (fail fast)

Read access is not write access on some labs. Prove you can write refs before generating
and pushing a whole fixture tree:

```bash
BASE=$(GH api --hostname "$LAB" repos/test/rails/git/ref/heads/main -q .object.sha)
GH api -X POST   --hostname "$LAB" repos/test/rails/git/refs \
  -f ref=refs/heads/gh-write-check-$$ -f sha="$BASE"
GH api -X DELETE --hostname "$LAB" repos/test/rails/git/refs/heads/gh-write-check-$$
```

Use a per-run ref name (`-$$` or a timestamp) so two seeders on the same shared lab don't
delete each other's probe. If the POST 403s, the seed will fail — stop and sort
auth/permissions first.

## The two sessions gotcha (CLI token ≠ browser session)

The lab's browser/XHR session and the `gh`/API session are separate, and they authenticate
different things:

- **CLI seeding** uses the API/git token from `gh auth` — that's all it needs to create
  branches and PRs.
- **The `page_data` XHR** (e.g. `diff_entries`) needs a browser `user_session` cookie. The
  `gh` token does **not** grant one. A raw `curl` with the CLI token gets 302-redirected to
  the login page — it never reaches the render path. Drive that endpoint from an
  authenticated **browser** session (or a cookie copied from one), not the CLI.
- Even within the browser, the long-lived HTML cookie and the JSON/XHR session can expire
  on their own: the page loads 200 while `diff_entries` returns 401. Re-login in that
  browser when that happens.

## Tailnet + ephemerality

- proxima labs: `*.octoca.ts.net`, corp Tailnet only. `review-lab` labs:
  `*.review-lab.github.com`.
- proxima TTL ~48h, review-lab ~4h. When the lab is recreated it gets a fresh DB — the
  seeded PRs are gone and you re-run `seed-fixture-prs.sh` against the new host. A plain
  branch *redeploy* keeps the DB (and the PRs); only lab recreation wipes them.

## Seed repo + base branch

Default seed repo is `test/rails`. The base branch is **not assumed** — the script resolves
the repo's default branch from the lab:

```bash
GH repo view test/rails --hostname "$LAB" --json nameWithOwner,defaultBranchRef \
  -q '.nameWithOwner + " default=" + .defaultBranchRef.name'
```

If the lab seeds a different repo, pass it as the 2nd arg to the script
(`seed-fixture-prs.sh <lab-host> <owner/repo> <scenario>`).
