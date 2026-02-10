# Copilot Skills

This directory contains custom Copilot skills for managing dotfiles and development environment configurations.

## Available Skills

### dotfiles-setup
Helps users set up and manage dotfiles configuration for development environments, including shell configuration (zsh), git settings, tmux, and codespace initialization.

**Use when:**
- Setting up a new development environment
- Configuring shells, git, or tmux
- Understanding dotfile setups
- Troubleshooting configuration issues

**Tags:** dotfiles, configuration, shell, git, development-environment

### git-config
Provides guidance on git configuration management, including global settings, gitignore patterns, and workflow optimization.

**Use when:**
- Setting up git on a new machine
- Configuring global git settings
- Managing gitignore patterns
- Optimizing git workflow

**Tags:** git, version-control, configuration, workflow

### tmux-config
Assists with tmux terminal multiplexer configuration and usage. Provides guidance on tmux setup, session management, window/pane operations, and configuration customization.

**Use when:**
- Setting up tmux for the first time
- Customizing tmux configuration
- Learning tmux key bindings and commands
- Managing terminal sessions, windows, and panes

**Tags:** tmux, terminal, multiplexer, productivity

### zsh-config
Assists with Zsh shell configuration, oh-my-zsh setup, plugin management, and shell customization.

**Use when:**
- Setting up Zsh for the first time
- Installing and configuring oh-my-zsh
- Managing Zsh plugins and themes
- Creating custom aliases and functions

**Tags:** zsh, shell, oh-my-zsh, terminal, productivity

## Installation

These skills are automatically installed when you run the dotfiles install script:

```bash
./install
```

The install script will:
1. Create the `~/.copilot/skills` directory
2. Copy all skills from the repository's `.copilot/skills/` directory
3. Make them available to GitHub Copilot

## Manual Installation

If you want to install the skills manually:

```bash
mkdir -p ~/.copilot/skills
cp -r ~/dotfiles/.copilot/skills/* ~/.copilot/skills/
```

## Skill Structure

Each skill is contained in its own directory with a `SKILL.md` file that includes:
- YAML frontmatter with metadata (name, description, tags, etc.)
- Detailed instructions and guidance
- Common use cases and examples
- Best practices and troubleshooting tips

## Using the Skills

Once installed, these skills will be available to GitHub Copilot across all your projects. Copilot will automatically use the relevant skill when you ask questions or request help related to:
- Dotfiles configuration
- Git setup and usage
- Tmux configuration
- Zsh and shell customization

## Updating Skills

To update the skills after making changes to the repository:

```bash
cd ~/dotfiles
cp -r .copilot/skills/* ~/.copilot/skills/
```

Or simply re-run the install script:

```bash
cd ~/dotfiles
./install
```
