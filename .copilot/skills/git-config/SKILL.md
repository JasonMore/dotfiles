---
name: git-config
description: |
  Provides guidance on git configuration management, including global settings,
  gitignore patterns, and workflow optimization. Use when users need help with
  git configuration, global settings, or repository management practices.
license: MIT
author: JasonMore
tags:
  - git
  - version-control
  - configuration
  - workflow
version: 1.0.0
---

# Git Configuration

## Overview
This skill helps users configure git for optimal workflow, including global settings, ignore patterns, and repository management best practices.

## When to Use
- Setting up git on a new machine
- Configuring global git settings
- Managing gitignore patterns
- Optimizing git workflow
- Troubleshooting git configuration issues
- Understanding git best practices

## Key Configuration Areas

### Global User Settings
```bash
# Set your identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Auto Setup Remote Tracking
Enable automatic remote tracking branch setup when pushing:
```bash
git config --global push.autoSetupRemote true
```

This eliminates the need to use `--set-upstream` or `-u` flag on first push.

### Pull Strategy
Configure how git handles pulls:
```bash
# Use merge strategy (recommended for beginners)
git config --global pull.rebase false

# Or use rebase strategy (cleaner history)
git config --global pull.rebase true
```

### Global Gitignore

#### Setup
The global gitignore file excludes files across all repositories:
```bash
# Set global gitignore location
git config --global core.excludesfile ~/.gitignore_global
```

#### Common Patterns
Typical patterns in `.gitignore_global`:
```
# IDE files
.idea/
.vscode/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Build artifacts
*.log
*.tmp
node_modules/
dist/
build/
```

## Configuration Management

### View Current Configuration
```bash
# View all settings
git config --list

# View specific setting
git config user.name

# View setting with origin
git config --show-origin user.name
```

### Configuration Levels
Git has three configuration levels:
1. **System** (`--system`): All users on the machine
2. **Global** (`--global`): Current user, all repositories
3. **Local** (default): Specific repository only

### Edit Configuration Directly
```bash
# Edit global config
git config --global --edit

# Edit local config
git config --edit
```

## Workflow Optimizations

### Aliases
Create shortcuts for common commands:
```bash
# Status shortcut
git config --global alias.st status

# Checkout shortcut
git config --global alias.co checkout

# Branch shortcut
git config --global alias.br branch

# Commit shortcut
git config --global alias.ci commit

# Pretty log
git config --global alias.lg "log --graph --oneline --all"
```

### Default Branch
Set default branch name for new repositories:
```bash
git config --global init.defaultBranch main
```

### Editor
Set your preferred editor:
```bash
git config --global core.editor "vim"
# Or: "nano", "code --wait", "subl -w", etc.
```

## Best Practices

### Identity Management
- Use work email for work repositories
- Use personal email for personal projects
- Consider using directory-specific config for automatic switching

### Ignore Patterns
- Use global gitignore for IDE and OS files
- Use repository gitignore for project-specific patterns
- Never commit sensitive data (use environment variables)

### Commit Hygiene
- Write clear, descriptive commit messages
- Use present tense ("Add feature" not "Added feature")
- Keep commits atomic (one logical change per commit)

### Branch Management
- Use descriptive branch names
- Follow naming conventions (feature/, bugfix/, etc.)
- Clean up merged branches regularly

## Common Scenarios

### Setting Up New Machine
```bash
# Configure identity
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Configure workflow
git config --global push.autoSetupRemote true
git config --global pull.rebase false

# Setup global gitignore
git config --global core.excludesfile ~/.gitignore_global
```

### Switching Between Work and Personal
```bash
# For work directory
cd ~/work
git config user.email "work@company.com"

# For personal projects
cd ~/personal
git config user.email "personal@email.com"
```

### Verifying Configuration
```bash
# Check current user
git config user.name
git config user.email

# Check all settings
git config --list --show-origin
```

## Troubleshooting

### Wrong Identity in Commits
```bash
# Check current identity
git config user.email

# Fix for repository
git config user.email "correct@email.com"

# Amend last commit author
git commit --amend --author="Name <email@example.com>"
```

### Global Gitignore Not Working
```bash
# Verify it's set
git config core.excludesfile

# Verify file exists
ls -la ~/.gitignore_global

# Re-apply if needed
git config --global core.excludesfile ~/.gitignore_global
```

### Push Requires --set-upstream
```bash
# Enable auto setup
git config --global push.autoSetupRemote true

# Or use once
git push --set-upstream origin branch-name
```

## Advanced Configuration

### Credential Management
```bash
# Cache credentials (15 min default)
git config --global credential.helper cache

# Store credentials (less secure)
git config --global credential.helper store

# OS-specific helpers
git config --global credential.helper osxkeychain  # macOS
git config --global credential.helper manager      # Windows
```

### Line Endings
```bash
# Windows
git config --global core.autocrlf true

# macOS/Linux
git config --global core.autocrlf input
```

## Notes
- Global configuration is stored in `~/.gitconfig`
- Local configuration is stored in `.git/config` within each repository
- Global gitignore helps keep repository-specific `.gitignore` files clean
- Configuration can be overridden at repository level when needed
