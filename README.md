# Dotfiles

Personal dotfiles for development environment configuration.

## Features

- **Shell Configuration**: Zsh with oh-my-zsh framework
- **Git Configuration**: Global settings and ignore patterns
- **Tmux Configuration**: Terminal multiplexer setup
- **GitHub Copilot Skills**: Custom skills for dotfiles management
- **Codespaces Support**: Automatic setup for GitHub Codespaces

## Installation

Clone this repository and run the install script:

```bash
git clone https://github.com/JasonMore/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install
```

The install script will:
1. Set zsh as the default shell
2. Configure git with optimal settings
3. Link configuration files (tmux, zsh)
4. Install development tools (oh-my-zsh, Atuin) in Codespaces
5. Install Copilot skills to `~/.copilot/skills`

## Copilot Skills

This repository includes custom GitHub Copilot skills for:
- **dotfiles-setup**: General dotfiles configuration and management
- **git-config**: Git configuration and workflow optimization
- **tmux-config**: Tmux terminal multiplexer setup and usage
- **zsh-config**: Zsh shell configuration with oh-my-zsh

See [.copilot/skills/README.md](.copilot/skills/README.md) for more details.

## Configuration Files

- `.gitignore_global`: Global git ignore patterns (IDE files, OS files)
- `.tmux.conf`: Tmux configuration
- `.zshrc`: Zsh shell configuration
- `install`: Installation script

## Customization

1. Fork this repository
2. Modify configuration files as needed
3. Update the install script for any new tools
4. Run `./install` to apply changes

## License

MIT