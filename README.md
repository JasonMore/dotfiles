testing

Includes a local-only `workspace` helper (see `workspace.sh`) that creates a git worktree in a sibling `*-worktrees/` directory and opens it in a new VS Code window.
When `CODESPACES` is non-empty, the installer skips this helper and zsh does not load it. Calls through an old installation fail before any worktree changes. Copilot instructions also require use of the current checkout in Codespaces.
Codespaces install flow also migrates legacy `.vscode/mcp.json` files to `.mcp.json` for Copilot CLI compatibility.
Installs a macOS `copilot-notify` launchd daemon (see `.copilot/bin/copilot-notify.sh`) that fires push notifications when local, Codespace, or cloud Copilot agent sessions finish or need input.
Clones `JasonMore/ai-skills` (Jason-authored skills only) and runs its installer so personal Copilot skills persist across Codespaces. Personal AI skills always install last, so they win any same-name skill conflicts with other installers.
Installs `i-have-adhd` globally and keeps its output rules active through the shared Copilot instructions.
In Codespaces, installs Impeccable into `~/.agents/skills/impeccable` with
`npx --yes impeccable install --providers=codex --scope=global --no-hooks --yes`.
This step needs no input and does not add project hooks. Personal AI skills still install last.
`.copilot/mcp-config.json` is symlinked to `~/.copilot/mcp-config.json` and registers global MCP servers for Copilot Desktop/CLI.

## Mergiraf

The installer adds [Mergiraf](https://mergiraf.org/) with Homebrew on macOS
and a pinned, checksum-verified 0.20.0 Linux release in Codespaces. Git uses
Mergiraf for files without an explicit merge attribute, while existing Git
attributes and merge-driver settings stay in place. If another `merge.default`
is already set, the installer keeps it and reports that Mergiraf was not
enabled as the default. Existing conflict styles also stay in place; otherwise,
Git uses `diff3`, which Mergiraf recommends for manual conflict resolution.

Run `mergiraf review <merge-id>` with the ID printed after an automatic
resolution. To use Git's normal merge behavior for one command, prefix it
with `mergiraf=0`.

## Reliability model

`install` is split into strict **core** steps (local symlinks/config; abort on
failure) and **optional** integrations (Atuin, agent skills, gh-stack,
Copilot coder plugin, Impeccable, Mergiraf, i-have-adhd, personal AI skills).
Optional steps run through a named runner that logs the exact failed step and
exit status, then continues; a missing secret, network hiccup, or external
installer failure never blocks the rest of the install. Personal AI skills
(`JasonMore/ai-skills`) always install last, so they stay authoritative even
if an earlier optional step failed.

## Repairing a partial Codespaces install

If a Codespace was created before this fix, an optional-step failure may have
aborted the install before personal AI skills were set up. One observed case
was `gh repo clone` running before GitHub CLI authentication was ready.
Codespaces won't rerun the install automatically.
To repair it, rerun the installer manually from the Codespace terminal:

```sh
/workspaces/.codespaces/.persistedshare/dotfiles/install
```

It's safe to rerun any time; every step is idempotent, and any optional
failures are printed as a summary at the end with the exact step name.

## HG560T34 monitor role

`set-monitor-role.py` targets the connected HG560T34 with vendor `4a8b` and
product `6034`. It sets `DisplayIsTV` to `false` in a local display override.
It preserves other override settings and saves a backup before changing an
existing file. The override affects all monitors with the same vendor/product
IDs. It does not change the monitor firmware.

Preview without changing system files:

```sh
python3 set-monitor-role.py
```

Install the override, then save your work and restart the Mac:

```sh
sudo python3 set-monitor-role.py --apply
```

After restart, run `python3 set-monitor-role.py --check`, then turn on Night
Shift to check its visible effect. The script does not restart the Mac or
WindowServer. Installing the override alone does not prove Night Shift works.

## Tests

`tests/run_tests.sh` runs behavioral tests against the real `install` script
using an isolated `$HOME` and a mocked `PATH` (no real network, system, or
account changes). Run with:

```sh
bash tests/run_tests.sh
```
