---
name: zsh-config
description: |
  Assists with Zsh shell configuration, oh-my-zsh setup, plugin management, and
  shell customization. Use when users need help with shell setup, configuration,
  themes, plugins, or shell productivity enhancements.
license: MIT
author: JasonMore
tags:
  - zsh
  - shell
  - oh-my-zsh
  - terminal
  - productivity
version: 1.0.0
---

# Zsh Configuration

## Overview
This skill helps users configure and optimize Zsh (Z shell), including oh-my-zsh framework setup, plugin management, theme customization, and productivity enhancements.

## When to Use
- Setting up Zsh for the first time
- Installing and configuring oh-my-zsh
- Managing Zsh plugins and themes
- Creating custom aliases and functions
- Troubleshooting shell issues
- Optimizing shell workflow

## Installation

### Set Zsh as Default Shell
```bash
# Change default shell to zsh
sudo chsh "$(id -un)" --shell "/usr/bin/zsh"

# Or for current user
chsh -s /usr/bin/zsh
```

### Install Oh-My-Zsh
Oh-My-Zsh is a framework for managing Zsh configuration:
```bash
# Clone oh-my-zsh
git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git ~/.oh-my-zsh

# Or use the official installer
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

## Configuration

### Configuration File
- Location: `~/.zshrc`
- Source from dotfiles: symlink from dotfiles repository

### Reload Configuration
After making changes:
```bash
# Reload configuration
source ~/.zshrc

# Or restart shell
exec zsh
```

## Oh-My-Zsh Features

### Themes
Change the shell appearance:
```bash
# Edit .zshrc
ZSH_THEME="robbyrussell"  # Default theme

# Popular themes:
# - robbyrussell (simple, fast)
# - agnoster (powerline-style)
# - powerlevel10k (highly customizable)
# - pure (minimal)
```

### Plugins
Enable built-in plugins by editing `~/.zshrc`:
```bash
plugins=(
  git              # Git aliases and functions
  docker           # Docker completion
  npm              # NPM completion
  node             # Node.js shortcuts
  sudo             # ESC ESC to prepend sudo
  history          # History management
  z                # Jump to frequent directories
)
```

### Common Plugins

#### Git Plugin
Provides numerous git aliases:
- `gst` → `git status`
- `gco` → `git checkout`
- `gcm` → `git commit -m`
- `gp` → `git push`
- `gl` → `git pull`

#### Docker Plugin
- Completion for docker commands
- Aliases for common docker operations

#### Z Plugin
Jump to frequently used directories:
```bash
# After visiting /long/path/to/project
z project  # Jumps to /long/path/to/project
```

## Customization

### Aliases
Add custom aliases to `~/.zshrc`:
```bash
# Navigation
alias ..='cd ..'
alias ...='cd ../..'
alias ~='cd ~'

# Safety
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Listing
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'

# Git shortcuts
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
```

### Functions
Create custom functions:
```bash
# Create and enter directory
mkcd() {
  mkdir -p "$1" && cd "$1"
}

# Extract archives
extract() {
  if [ -f "$1" ]; then
    case "$1" in
      *.tar.gz) tar xzf "$1" ;;
      *.zip)    unzip "$1" ;;
      *.tar)    tar xf "$1" ;;
      *)        echo "Unknown archive type" ;;
    esac
  fi
}
```

### Environment Variables
Set environment variables:
```bash
# Editor
export EDITOR='vim'
export VISUAL='vim'

# Path additions
export PATH="$HOME/bin:$PATH"

# Language settings
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

## History Management

### Basic Configuration
```bash
# History file
HISTFILE=~/.zsh_history

# History size
HISTSIZE=10000
SAVEHIST=10000

# Options
setopt SHARE_HISTORY          # Share history between sessions
setopt HIST_IGNORE_DUPS       # Ignore duplicate commands
setopt HIST_IGNORE_SPACE      # Ignore commands starting with space
setopt HIST_VERIFY            # Verify before executing history command
```

### Atuin Integration
Atuin provides advanced shell history with sync:
```bash
# Install atuin
curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh

# Login (requires account)
atuin login -u username -k key -p password

# Search history
# Ctrl+R for interactive search
```

## Productivity Tips

### Key Bindings
Common Zsh key bindings:
- `Ctrl+R`: Search history
- `Ctrl+A`: Beginning of line
- `Ctrl+E`: End of line
- `Ctrl+U`: Clear line before cursor
- `Ctrl+K`: Clear line after cursor
- `Ctrl+W`: Delete word before cursor
- `Alt+.`: Insert last argument from previous command

### Auto-completion
```bash
# Enable completion
autoload -Uz compinit
compinit

# Case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'

# Menu selection
zstyle ':completion:*' menu select
```

### Directory Navigation
```bash
# Auto-cd (type directory name without cd)
setopt AUTO_CD

# Directory stack
setopt AUTO_PUSHD
setopt PUSHD_IGNORE_DUPS

# Use directory stack
dirs -v    # Show directory stack
cd -2      # Jump to 3rd directory in stack
```

## Common Workflows

### Development Environment
```zsh
# Quick project navigation
alias proj='cd ~/projects'
alias work='cd ~/work'

# Start common services
alias startdb='docker-compose up -d postgres'
alias stopdb='docker-compose stop postgres'

# Development shortcuts
alias dev='npm run dev'
alias test='npm test'
alias build='npm run build'
```

### Git Workflow
```zsh
# Quick commit
gac() {
  git add -A && git commit -m "$*"
}

# Quick push
gacp() {
  git add -A && git commit -m "$*" && git push
}

# Branch cleanup
gbclean() {
  git branch --merged | grep -v "\*\|main\|master" | xargs -n 1 git branch -d
}
```

## Troubleshooting

### Slow Shell Startup
```bash
# Profile startup time
time zsh -i -c exit

# Identify slow plugins
# Comment out plugins one by one in .zshrc

# Use lazy loading for heavy tools
# Instead of: eval "$(nvm init)"
# Use lazy loading wrapper
```

### Completion Not Working
```bash
# Rebuild completion cache
rm -f ~/.zcompdump
compinit

# Check plugin order in .zshrc
# Completion plugins should come early
```

### Theme Not Displaying Correctly
```bash
# Install required fonts (e.g., Powerline fonts)
# Check terminal color support
echo $TERM

# Try simpler theme
ZSH_THEME="robbyrussell"
```

## Best Practices
- Keep `.zshrc` organized (use sections/comments)
- Document custom aliases and functions
- Regular cleanup of unused plugins
- Use version control for dotfiles
- Test changes in new shell before committing
- Backup `.zshrc` before major changes
- Use conditionals for machine-specific config

## Notes
- Oh-My-Zsh updates itself periodically
- Plugin order matters (some depend on others)
- Many plugins add aliases that might conflict
- History is shared between all terminal sessions
- Symlinked `.zshrc` allows centralized dotfile management
