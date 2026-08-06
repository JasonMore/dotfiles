dotfile

Includes a `workspace` helper (see `workspace.sh`) that creates a git worktree in a sibling `*-worktrees/` directory and opens it in a new VS Code window.
Codespaces install flow also migrates legacy `.vscode/mcp.json` files to `.mcp.json` for Copilot CLI compatibility.
Installs a macOS `copilot-notify` launchd daemon (see `.copilot/bin/copilot-notify.sh`) that fires push notifications when local, Codespace, or cloud Copilot agent sessions finish or need input.
Clones `JasonMore/ai-skills` and runs its installer so personal Copilot skills persist across Codespaces.

## Reliability model

`install` is split into strict **core** steps (local symlinks/config; abort on
failure) and **optional** integrations (Atuin, agent skills, gh-stack,
caveman, Copilot coder plugin, personal AI skills). Optional steps run
through a named runner that logs the exact failed step and exit status, then
continues — a missing secret, network hiccup, or external installer failure
never blocks the rest of the install. Personal AI skills (`JasonMore/ai-skills`)
always install last, so they stay authoritative even if an earlier optional
step failed.

## Repairing a partial Codespaces install

If a Codespace was created before this fix, an optional-step failure may have
aborted the install before personal AI skills were set up. One observed case
was `gh repo clone` running before GitHub CLI authentication was ready.
Codespaces won't rerun the install automatically.
To repair it, rerun the installer manually from the Codespace terminal:

```sh
/workspaces/.codespaces/.persistedshare/dotfiles/install
```

It's safe to rerun any time — every step is idempotent, and any optional
failures are printed as a summary at the end with the exact step name.

## Tests

`tests/run_tests.sh` runs behavioral tests against the real `install` script
using an isolated `$HOME` and a mocked `PATH` (no real network, system, or
account changes). Run with:

```sh
bash tests/run_tests.sh
```
