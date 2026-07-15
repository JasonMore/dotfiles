# seed-review-lab-prs

Seed synthetic small/medium/large test PRs into a running **proxima** review
lab's seed repo (default `test/rails`), using the `gh` CLI pointed at the **lab
host**, so a PR render/perf path (e.g. the `diff_entries` page_data XHR) can be
profiled over real HTTP.

**Proxima labs only** (`*.octoca.ts.net`, on Tailscale). Never point this at a
normal `review-lab.github.com` lab — those carry real production data. The script
refuses any non-proxima host. Complements `deploy-review-lab`: that skill
*deploys* a lab; this one *seeds test data into* a proxima lab that's already up.

## Quick start

```bash
# after the proxima lab is deployed and you're on Tailscale + authed:
scripts/seed-fixture-prs.sh <proxima-host>.octoca.ts.net [owner/repo] [scenario]
```

- `owner/repo` — seed repo in the lab (default `test/rails`).
- `scenario` — slug for branch names, PR titles, and fixture paths (default
  `fixture`). Set it per investigation (e.g. `diff-lines-cache`).

Prints the created PR numbers and a template `curl` for each PR's endpoint. The
script **fails closed**: a failed push or PR-create stops the run instead of
printing a URL for a PR that was never created.

## Files

- `SKILL.md` — when to use, the manual flow, gotchas, how to drive the endpoint.
- `scripts/seed-fixture-prs.sh` — auth-check → resolve base branch → clone →
  generate 3 sizes → push unique branches → open 3 PRs → print URLs. Takes
  `<lab-host> [owner/repo] [scenario]`.
- `references/gh-lab-host-auth.md` — per-host auth, the
  `env -u GH_TOKEN -u GITHUB_TOKEN -u GH_HOST` rule, the write probe, the
  browser-vs-CLI session split, Tailnet + ephemerality detail.

## Requires

`gh`, `git`; Tailscale (proxima labs are Tailnet-only); an authenticated lab-host
login. The interactive `gh auth login --web` and Tailscale connection are the
**user's** job — a CLI agent can't do them and the script stops with the exact
command to hand
over.
