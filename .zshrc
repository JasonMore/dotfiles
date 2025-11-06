# ============ Oh My Zsh (shell framework) ============
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git)

if [[ -f "${ZSH}/oh-my-zsh.sh" ]]; then
  source "${ZSH}/oh-my-zsh.sh"
else
  echo "[dotfiles] oh-my-zsh not found; skipping framework initialization."
fi

# ============ Atuin (history search/sync) ============
if [[ -f "$HOME/.atuin/bin/env" ]]; then
  source "$HOME/.atuin/bin/env"
fi

if command -v atuin >/dev/null 2>&1; then
  eval "$(atuin init zsh)"
fi

# ============ History behavior ============
HISTFILE=~/.zsh_history
HISTSIZE=20000
SAVEHIST=20000
setopt SHARE_HISTORY HIST_IGNORE_ALL_DUPS

# ============ Copilot CLI ============
export COPILOT_ALLOW_ALL=true

cpi() {
  if [[ -n "$1" ]]; then
    copilot --add-dir /workspaces -p "$*"
  else
    copilot --add-dir /workspaces
  fi
}
