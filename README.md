dotfile

Includes a `workspace` helper (see `workspace.sh`) that creates a git worktree in a sibling `*-worktrees/` directory and opens it in a new VS Code window.
Codespaces install flow also migrates legacy `.vscode/mcp.json` files to `.mcp.json` for Copilot CLI compatibility.
Installs a macOS `copilot-notify` launchd daemon (see `.copilot/bin/copilot-notify.sh`) that fires push notifications when local, Codespace, or cloud Copilot agent sessions finish or need input.
Keeps personal Copilot skills in `.copilot/skills/` and symlinks them into `~/.copilot/skills/`, so GitHub remains the source of truth.
