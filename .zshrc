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
    const packagePath = '$package_json';
    const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    
    const scriptsToUpdate = ['webpack', 'webpack:alloy', 'webpack:alloy:serve', 'webpack:css:serve'];
    const memoryFlag = '--max-old-space-size=12288';
    
    scriptsToUpdate.forEach(scriptName => {
      if (pkg.scripts && pkg.scripts[scriptName]) {
        let script = pkg.scripts[scriptName];
        // Remove existing max-old-space-size flags
        script = script.replace(/--max-old-space-size=\d+\s*/g, '');
        // Add the new flag at the beginning if it starts with node
        if (script.startsWith('node ')) {
          script = 'node ' + memoryFlag + ' ' + script.substring(5);
        } else {
          // For other commands, prepend NODE_OPTIONS
          script = 'NODE_OPTIONS=\"' + memoryFlag + '\" ' + script;
        }
        pkg.scripts[scriptName] = script;
      }
    });
    
    fs.writeFileSync(packagePath, JSON.stringify(pkg, null, 2) + '\n');
  "
  
  echo "Memory settings updated successfully!"
  echo "Modified scripts: webpack, webpack:alloy, webpack:alloy:serve, webpack:css:serve"
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
