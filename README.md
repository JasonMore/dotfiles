dotfile

Includes a `workspace` helper (see `workspace.sh`) that creates a git worktree in a sibling `*-worktrees/` directory and opens it in a new VS Code window.
Codespaces install flow also migrates legacy `.vscode/mcp.json` files to `.mcp.json` for Copilot CLI compatibility.
Installs a macOS `copilot-notify` launchd daemon (see `.copilot/bin/copilot-notify.sh`) that fires push notifications when local, Codespace, or cloud Copilot agent sessions finish or need input.
Clones `JasonMore/ai-skills` (Jason-authored skills only — never grepika) and runs its installer so personal Copilot skills persist across Codespaces. This install runs last so it wins any same-name skill conflicts with other installers (e.g. `install-agent-skills`, `install-caveman-skills`, `install-grepika-skills`).
`.copilot/mcp-config.json` is symlinked to `~/.copilot/mcp-config.json` and registers global MCP servers for Copilot Desktop/CLI, including `grepika` (`npx -y @agentika/grepika@latest --mcp`) for token-efficient code search.
Codespaces setup also runs `install-grepika-skills`, which freshly installs the grepika skills (`plugins/grepika/skills/*`) directly from upstream `agentika-labs/grepika` into `~/.copilot/skills` on every run. This runs after the other Codespaces skill installers (so it wins any name collisions with them) but before the final `JasonMore/ai-skills` install.
