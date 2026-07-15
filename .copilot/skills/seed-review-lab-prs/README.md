# seed-review-lab-prs

Seed synthetic small/medium/large test PRs into a running review lab's `test/rails` repo,
using the `gh` CLI pointed at the **lab host**, so a PR render/perf path (e.g. the
`diff_entries` page_data XHR) can be profiled over real HTTP.

Complements `deploy-review-lab`: that skill *deploys* a lab; this one *seeds test data into*
a lab that's already up.

## Quick start

```bash
# after the lab is deployed and you're on Tailscale:
scripts/seed-fixture-prs.sh proxima-review-lab-<owner>-<branch>.octoca.ts.net
```

Prints the created PR numbers and a ready `curl` for each PR's `diff_entries` endpoint.

## Files

- `SKILL.md` — when to use, the 9-step flow, gotchas, how to drive the endpoint.
- `scripts/seed-fixture-prs.sh` — auth-check → clone → generate 3 sizes → push → open 3
  PRs → print URLs. Takes `<lab-host> [seed-repo]`.
- `references/gh-lab-host-auth.md` — per-host auth, the `env -u GH_TOKEN -u GH_HOST` rule,
  the write probe, Tailnet + ephemerality detail.

## Requires

`gh`, `git`, `node`; Tailscale for proxima labs; an authenticated lab-host login
(`gh auth login --hostname <lab> --web`).
