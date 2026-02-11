# cpi-workspace Installation Guide

This script creates a GitHub Codespace workflow similar to Copilot Desktop's Workspace Manager.

## Features

- Creates isolated git worktrees for different features/issues
- Opens each worktree in a new VS Code window
- Automatically starts Copilot CLI
- Supports multiple input modes:
  - Auto-generate workspace name
  - Use specific branch name
  - Create from GitHub issue number
  - Create from GitHub PR number

## Installation

### 1. Copy the script to your codespace

```bash
# Create a directory for custom scripts (if it doesn't exist)
mkdir -p ~/.local/bin

# Copy the script
cp cpi-workspace.sh ~/.local/bin/cpi-workspace.sh
```

### 2. Add to your .bashrc

Add this line to your `~/.bashrc`:

```bash
# Load cpi-workspace function
if [ -f ~/.local/bin/cpi-workspace.sh ]; then
    source ~/.local/bin/cpi-workspace.sh
fi
```

### 3. Reload your shell

```bash
source ~/.bashrc
```

## Usage

### Auto-generate workspace name
```bash
cpi-workspace
# Creates: workspace-20260211-142530
```

### Use specific branch name
```bash
cpi-workspace feature/new-theme
# Creates: worktree with branch 'feature/new-theme'
```

### Create from GitHub issue
```bash
cpi-workspace #123
# Fetches issue #123, creates: issue-123-add-dark-mode
# Starts Copilot CLI with issue context
```

### Create from GitHub PR
```bash
cpi-workspace !456
# Fetches PR #456, checks out the PR branch
# Creates: pr-456-feature-new-theme
```

## How It Works

1. **Creates a git worktree** in a sibling directory (e.g., `repo-worktrees/`)
2. **Opens VS Code** in a new window pointing to the worktree
3. **Creates a startup script** (`.copilot-startup.sh`) that you can run to start Copilot CLI
4. **For issues/PRs**: Fetches metadata from GitHub and provides context to Copilot

## Worktree Structure

```
your-repo/                    # Main repository
your-repo-worktrees/          # Worktrees directory
  ├── workspace-20260211-142530/
  ├── issue-123-add-dark-mode/
  └── pr-456-feature-new-theme/
```

## Tips

- Each worktree is completely isolated - you can work on multiple features simultaneously
- Use `git worktree list` to see all active worktrees
- Use `git worktree remove <name>` to remove a worktree when done
- The startup script provides a quick way to launch Copilot CLI with context

## Requirements

- Git worktree support (Git 2.5+)
- `gh` CLI (GitHub CLI) - for issue/PR features
- `jq` - for parsing JSON responses
- VS Code with `code` command available

## Codespace-Specific Setup

If the `code` command doesn't work in your codespace terminal, you may need to use the VS Code terminal API instead. The script will fall back to creating a startup script you can run manually.
