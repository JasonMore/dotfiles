# ============ Atuin (history search/sync) ============
eval "$(atuin init zsh)"

# ============ Starship (prompt) ============
eval "$(starship init zsh)"

# ============ Git aliases (replace oh-my-zsh plugin) ============
alias gst='git status'
alias gco='git checkout'
alias gaa='git add --all'
alias gcmsg='git commit -m'
alias gp='git push'
alias gl='git pull'
alias grh='git reset --hard'
alias gcl='git clone'
alias gdf='git diff'
alias gbr='git branch'
alias gsw='git switch'

# ============ History behavior ============
HISTFILE=~/.zsh_history
HISTSIZE=20000
SAVEHIST=20000
setopt SHARE_HISTORY HIST_IGNORE_ALL_DUPS