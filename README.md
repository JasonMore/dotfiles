# dotfiles

Personal shell, Git, tmux, and GitHub Copilot configuration for macOS and
GitHub Codespaces.

The repository uses `install` as its entry point. The script links configuration
files from this repository into the home directory, configures Git, and installs
optional tools for the current environment.

## What it configures

The installer always:

- Configures Git to set upstream branches automatically, use merge-based pulls,
  and use this repository's `.gitignore_global`.
- Links `.tmux.conf` to `~/.tmux.conf`.
- Installs `workspace.sh` at `~/.local/bin/workspace.sh`.
- Links the shared Copilot instructions to `~/.copilot/` and `~/.github/`.
- Links the Playwright MCP configuration to `~/.copilot/mcp-config.json`.
- Installs the global `i-have-adhd` skill and personal skills from
  `JasonMore/ai-skills`.

On macOS, the installer also installs a launchd agent that sends notifications
for completed local and Codespaces Copilot CLI turns. Cloud task monitoring is
available but is off by default.

In GitHub Codespaces, the installer also:

- Sets zsh as the login shell and installs Oh My Zsh.
- Links `.zshrc` and enables Atuin when it is available.
- Migrates legacy `.vscode/mcp.json` files to `.mcp.json`.
- Configures the VS Code Ruby LSP to use `bin/safe-ruby`.
- Installs Copilot agent configuration, shared agent skills, `gh-stack`, and the
  Copilot coder plugin.

## Install

GitHub Codespaces runs the dotfiles installer automatically when this repository
is selected as the user's dotfiles repository.

For a manual installation, clone the repository and run:

```sh
./install
```

The core setup requires Bash and Git. Some optional features also require
network access, GitHub CLI authentication, Node.js with `npx`, `jq`, or platform
tools such as `launchctl`. The installer reports a warning and continues when an
optional integration fails.

The installer is designed to be run again. In a Codespace, the persisted clone
is usually at:

```sh
/workspaces/.codespaces/.persistedshare/dotfiles/install
```

This command retries optional steps that failed during initial Codespace
creation.

## Workspace helper

The `workspace` function creates Git worktrees in a sibling
`<repository>-worktrees/` directory and opens them in a new VS Code window. The
`.zshrc` file loads the function from `~/.local/bin/workspace.sh`.

```sh
workspace                         # Create a timestamped branch and worktree
workspace my-branch               # Create or open a named branch worktree
workspace '#123'                  # Create a worktree for a GitHub issue
workspace '!456'                  # Create a worktree for a pull request
workspace --list                  # List worktrees
workspace --delete my-branch      # Remove a worktree
```

Issue and pull request forms require an authenticated GitHub CLI. Full GitHub
issue and pull request URLs are also accepted.

## Installer reliability

Core steps change local configuration and must succeed. A core failure stops the
installer.

Optional steps depend on network access, authentication, secrets, or external
installers. Each optional step reports its own result. A failure does not stop
later optional steps. Personal skills install last so that they take precedence
over skills with the same name from other sources.

## Repository layout

| Path | Purpose |
| --- | --- |
| `install` | Main installer for local systems and Codespaces |
| `.zshrc` | Codespaces zsh configuration and helper functions |
| `.tmux.conf` | tmux defaults, terminal support, mouse, and clipboard settings |
| `.copilot/` | Shared Copilot instructions, MCP configuration, skills, and notifications |
| `install-agent-skills` | Installs skills from `github/agent-config` and `gh-hubber-skills` |
| `install-copilot-plugin` | Installs or updates `github/copilot-coder-plugin` |
| `workspace.sh` | Creates, lists, opens, and removes Git worktrees |
| `tests/` | Isolated behavioral tests for the installer |

## Tests

Run the behavioral installer tests with:

```sh
bash tests/run_tests.sh
```

The test suite uses an isolated home directory and mocked external commands. It
does not change the real user account or make network requests.
