---
name: tmux-config
description: |
  Assists with tmux terminal multiplexer configuration and usage. Provides guidance
  on tmux setup, session management, window/pane operations, and configuration customization.
  Use when users need help with tmux setup, configuration, or operations.
license: MIT
author: JasonMore
tags:
  - tmux
  - terminal
  - multiplexer
  - productivity
version: 1.0.0
---

# Tmux Configuration

## Overview
This skill helps users configure and use tmux, a terminal multiplexer that enables multiple terminal sessions within a single window. It provides guidance on installation, configuration, and common operations.

## When to Use
- Setting up tmux for the first time
- Customizing tmux configuration
- Learning tmux key bindings and commands
- Troubleshooting tmux issues
- Managing terminal sessions, windows, and panes
- Optimizing tmux workflow

## Key Concepts

### Sessions
A tmux session is a collection of windows, managed independently from the terminal. Sessions persist even if you disconnect, allowing you to resume work later.

### Windows
Windows are like tabs in a terminal. Each window can contain multiple panes.

### Panes
Panes are split sections within a window, each running its own shell.

## Configuration

### Configuration File Location
- Repository: `.tmux.conf` in the dotfiles directory
- System: Symlinked to `~/.tmux.conf`

### Applying Configuration
After modifying `.tmux.conf`:
1. Reload configuration: `tmux source-file ~/.tmux.conf`
2. Or restart tmux sessions

## Common Operations

### Session Management
```bash
# Start new session
tmux

# Start named session
tmux new -s session-name

# List sessions
tmux ls

# Attach to session
tmux attach -t session-name

# Detach from session (inside tmux)
Ctrl+b, then d

# Kill session
tmux kill-session -t session-name
```

### Window Management
```bash
# Create new window (inside tmux)
Ctrl+b, then c

# Switch to window by number
Ctrl+b, then 0-9

# Next window
Ctrl+b, then n

# Previous window
Ctrl+b, then p

# Rename window
Ctrl+b, then ,

# Kill window
Ctrl+b, then &
```

### Pane Management
```bash
# Split horizontally
Ctrl+b, then "

# Split vertically
Ctrl+b, then %

# Navigate between panes
Ctrl+b, then arrow keys

# Resize pane
Ctrl+b, then Ctrl+arrow keys

# Close pane
Ctrl+b, then x
# Or simply: exit
```

## Customization Tips

### Status Bar
Customize the status bar in `.tmux.conf`:
```bash
# Set status bar position
set-option -g status-position top

# Set colors
set -g status-bg colour235
set -g status-fg colour136
```

### Key Bindings
Change or add key bindings:
```bash
# Change prefix from Ctrl+b to Ctrl+a
set -g prefix C-a
unbind C-b
bind C-a send-prefix

# Enable mouse support
set -g mouse on
```

### Copy Mode
```bash
# Enter copy mode
Ctrl+b, then [

# Navigate with vi-like keys (if enabled)
# Search: /, n for next
# Copy: Space to start, Enter to copy
# Paste: Ctrl+b, then ]
```

## Workflow Examples

### Development Workflow
```bash
# Start development session
tmux new -s dev

# Split into editor and terminal
Ctrl+b, then "

# Create separate window for git operations
Ctrl+b, then c

# Create window for logs/monitoring
Ctrl+b, then c
```

### Long-Running Tasks
```bash
# Start session for build
tmux new -s build

# Run long command
npm run build

# Detach (build continues)
Ctrl+b, then d

# Later, reattach
tmux attach -t build
```

## Troubleshooting

### Configuration Not Loading
- Check file location: `~/.tmux.conf`
- Verify symlink: `ls -la ~/.tmux.conf`
- Reload manually: `tmux source-file ~/.tmux.conf`

### Colors Not Working
- Ensure terminal supports 256 colors
- Add to `.tmux.conf`: `set -g default-terminal "screen-256color"`

### Mouse Not Working
- Enable in config: `set -g mouse on`
- Reload configuration

## Best Practices
- Use named sessions for different projects
- Keep sessions organized (max 5-10 active sessions)
- Regularly clean up old sessions
- Learn the most common key bindings first
- Customize status bar to show relevant information
- Use copy mode for efficient text selection

## Notes
- Tmux sessions persist across terminal disconnections
- Configuration changes require reload or restart
- Use `tmux list-keys` to see all key bindings
- Compatible with most shells (bash, zsh, fish)
