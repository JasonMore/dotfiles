---
name: dotfiles-setup
description: |
  Helps users set up and manage dotfiles configuration for development environments,
  including shell configuration (zsh), git settings, tmux, and codespace initialization.
  Use when users want to configure their development environment or understand dotfile setups.
license: MIT
author: JasonMore
tags:
  - dotfiles
  - configuration
  - shell
  - git
  - development-environment
version: 1.0.0
---

# Dotfiles Setup

## Overview
This skill helps with setting up and managing dotfiles for development environments. It provides guidance on configuring shells, version control, terminal multiplexers, and development tools.

## When to Use
- Setting up a new development environment
- Configuring shell (zsh) with oh-my-zsh
- Managing git global configuration
- Setting up tmux for terminal multiplexing
- Installing and configuring development tools
- Troubleshooting dotfile-related issues

## Key Features

### Shell Configuration
- Zsh with oh-my-zsh framework
- Custom shell aliases and functions
- Shell history management with Atuin

### Git Configuration
- Global gitignore setup
- Auto-setup for remote tracking branches (`push.autoSetupRemote`)
- Pull rebase configuration

### Tmux Configuration
- Terminal multiplexer setup
- Persistent terminal sessions

### Codespaces Support
- Automatic environment setup for GitHub Codespaces
- MCP server configuration for Copilot CLI
- Tool installation automation

## Instructions

### Setting Up Dotfiles
1. Clone the dotfiles repository to a known location
2. Run the install script to configure the environment
3. Restart the shell to apply changes

### Customizing Configuration
1. Edit configuration files in the dotfiles directory
2. For zsh: modify `.zshrc`
3. For git: modify `.gitignore_global` or use git config commands
4. For tmux: modify `.tmux.conf`
5. Re-run install script or manually symlink updated files

### Adding New Tools
1. Add installation logic to the `install` script
2. Add configuration files to the repository
3. Update symlinks or copy commands in install script
4. Test in a clean environment

## File Structure
```
dotfiles/
├── .copilot/           # Copilot configuration and skills
│   └── skills/         # Custom Copilot skills
├── .gitignore_global   # Global git ignore patterns
├── .tmux.conf          # Tmux configuration
├── .zshrc              # Zsh shell configuration
├── install             # Installation script
└── README.md           # Documentation
```

## Common Operations

### Install Script Functions
- Set default shell to zsh
- Configure git settings (push.autoSetupRemote, pull.rebase)
- Setup global gitignore
- Link tmux configuration
- Install oh-my-zsh (in Codespaces)
- Install and configure Atuin for shell history
- Setup MCP servers for Copilot CLI

### Environment Detection
The install script detects GitHub Codespaces via the `$CODESPACES` environment variable and enables Codespaces-specific features.

## Examples

### Setting Up a New Environment
```bash
# Clone dotfiles
git clone https://github.com/JasonMore/dotfiles ~/dotfiles

# Run installation
cd ~/dotfiles
./install
```

### Updating Configuration
```bash
# Edit configuration
vim ~/dotfiles/.zshrc

# Re-link
ln -sf ~/dotfiles/.zshrc ~/.zshrc

# Restart shell
exec zsh
```

## Notes
- Always test changes in a safe environment before applying to production
- Keep sensitive data (API keys, tokens) in environment variables, not in dotfiles
- Use global gitignore for IDE-specific files (.idea, .vscode, etc.)
- The install script is idempotent and safe to run multiple times
