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

# ============ Aliases ============
alias ff='script/toggle-feature-flag'

# ============ Workspace Memory Management ============
memup() {
  local workspace_dir="/workspaces/github-ui"
  local package_json="$workspace_dir/package.json"
  
  if [[ ! -d "$workspace_dir" ]]; then
    echo "Error: Workspace directory not found: $workspace_dir"
    return 1
  fi
  
  if [[ ! -f "$package_json" ]]; then
    echo "Error: package.json not found: $package_json"
    return 1
  fi
  
  echo "Setting package.json to skip-worktree..."
  (cd "$workspace_dir" && git update-index --skip-worktree package.json)
  
  echo "Updating memory settings in package.json..."
  # Use node to update the package.json with increased memory settings
  node -e "
    const fs = require('fs');
    const packagePath = process.argv[1];
    
    try {
      const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
      
      // Globally replace all max-old-space-size values with 22288
      if (pkg.scripts) {
        Object.keys(pkg.scripts).forEach(scriptName => {
          pkg.scripts[scriptName] = pkg.scripts[scriptName].replace(/--max-old-space-size=\d+/g, '--max-old-space-size=22288');
        });
      }
      
      fs.writeFileSync(packagePath, JSON.stringify(pkg, null, 2) + '\n');
    } catch (error) {
      console.error('Error updating package.json:', error.message);
      process.exit(1);
    }
  " "$package_json"
  
  if [[ $? -ne 0 ]]; then
    echo "Error: Failed to update memory settings in package.json"
    return 1
  fi
  
  echo "Memory settings updated successfully!"
  echo "All scripts with max-old-space-size have been updated to 22288"
}

reset-memup() {
  local workspace_dir="/workspaces/github-ui"
  local package_json="$workspace_dir/package.json"
  
  if [[ ! -d "$workspace_dir" ]]; then
    echo "Error: Workspace directory not found: $workspace_dir"
    return 1
  fi
  
  echo "Resetting skip-worktree flag..."
  (cd "$workspace_dir" && git update-index --no-skip-worktree package.json)
  
  echo "Resetting package.json to HEAD..."
  (cd "$workspace_dir" && git checkout HEAD -- package.json)
  
  echo "package.json has been reset successfully!"
}

# ============ workspace (git worktree helper) ==========
if [[ -f "$HOME/.local/bin/workspace.sh" ]]; then
  source "$HOME/.local/bin/workspace.sh"
fi
