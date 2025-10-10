export ZSH="${HOME}/.oh-my-zsh"

ZSH_THEME="robbyrussell"
plugins=(git z)

if [[ -d "${ZSH}" ]]; then
	source "${ZSH}/oh-my-zsh.sh"
else
	echo "[dotfiles] Oh My Zsh not found at ${ZSH}; skipping load" >&2
fi 