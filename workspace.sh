#!/bin/bash

# workspace: Create a git worktree and open it in a new VS Code window
# Usage:
#   workspace                                              # Auto-generate worktree name
#   workspace branch-name                                  # Use specific branch name
#   workspace #123                                         # Create from issue number
#   workspace !456                                         # Create from PR number
#   workspace https://github.com/owner/repo/pull/123       # Create from PR URL
#   workspace https://github.com/owner/repo/issues/456     # Create from issue URL
#   workspace --list                                       # List all workspaces
#   workspace --delete <workspace-name>                    # Delete a workspace

migrate_legacy_mcp_config() {
    local repo_path="$1"
    local legacy_config="${repo_path}/.vscode/mcp.json"
    local new_config="${repo_path}/.mcp.json"
    local temp_config=""

    if [[ ! -f "${legacy_config}" || -f "${new_config}" ]]; then
        return 0
    fi

    if ! command -v jq >/dev/null 2>&1; then
        echo "Warning: jq not found; skipping MCP migration for ${repo_path}"
        return 0
    fi

    if ! jq -e 'has("servers") and (.servers | type == "object")' "${legacy_config}" >/dev/null 2>&1; then
        echo "Warning: ${legacy_config} is missing a valid .servers object; skipping MCP migration"
        return 0
    fi

    temp_config="$(mktemp)"
    if jq '{mcpServers: .servers}' "${legacy_config}" > "${temp_config}"; then
        mv "${temp_config}" "${new_config}"
        echo "Migrated MCP config: ${legacy_config} -> ${new_config}"
    else
        rm -f "${temp_config}"
        echo "Warning: Failed to migrate ${legacy_config}"
    fi
}

workspace() {
    # Handle flags
    if [ "$1" = "--list" ]; then
        # Get the git root directory
        local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
        if [ -z "$git_root" ]; then
            echo "Error: Not in a git repository"
            return 1
        fi
        
        local worktrees_dir="$git_root-worktrees"
        
        if [ ! -d "$worktrees_dir" ]; then
            echo "No workspaces found."
            echo "Worktrees directory does not exist: $worktrees_dir"
            return 0
        fi
        
        echo "Workspaces in $worktrees_dir:"
        echo ""
        
        # List directories in worktrees directory
        local count=0
        if [ -d "$worktrees_dir" ]; then
            for ws in "$worktrees_dir"/*; do
                if [ -d "$ws" ]; then
                    local name=$(basename "$ws")
                    # Get branch name from git worktree list
                    local branch=$(git worktree list | grep "$ws" | sed -n 's/.*\[\(.*\)\].*/\1/p')
                    if [ -n "$branch" ]; then
                        printf "  %-40s [%s]\n" "$name" "$branch"
                    else
                        printf "  %s\n" "$name"
                    fi
                    count=$((count + 1))
                fi
            done
        fi
        
        if [ $count -eq 0 ]; then
            echo "  (no workspaces found)"
        else
            echo ""
            echo "Total: $count workspace(s)"
        fi
        echo ""
        echo "Use 'workspace --delete <name>' to remove a workspace"
        return 0
    fi
    
    if [ "$1" = "--delete" ]; then
        if [ -z "$2" ]; then
            echo "Usage: workspace --delete <workspace-name>"
            echo ""
            echo "Available workspaces:"
            workspace --list
            return 1
        fi
        
        # Get the git root directory
        local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
        if [ -z "$git_root" ]; then
            echo "Error: Not in a git repository"
            return 1
        fi
        
        local worktrees_dir="$git_root-worktrees"
        local worktree_path="$worktrees_dir/$2"
        
        if [ ! -d "$worktree_path" ]; then
            echo "Error: Workspace '$2' not found at $worktree_path"
            echo ""
            echo "Available workspaces:"
            workspace --list
            return 1
        fi
        
        echo "Removing workspace: $2"
        echo "Path: $worktree_path"
        
        if git worktree remove "$worktree_path" 2>/dev/null; then
            echo "✓ Workspace removed successfully"
        elif git worktree remove --force "$worktree_path" 2>/dev/null; then
            echo "✓ Workspace removed (forced)"
        else
            echo "Error: Failed to remove workspace"
            echo "You may need to remove it manually or use: git worktree remove --force"
            return 1
        fi
        return 0
    fi
    
    local worktree_name=""
    local branch_name=""
    local issue_context=""
    local base_dir=""
    
    # Get the git root directory
    local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
    if [ -z "$git_root" ]; then
        echo "Error: Not in a git repository"
        return 1
    fi
    
    # Directory for worktrees (sibling to main repo)
    local worktrees_dir="$git_root-worktrees"
    mkdir -p "$worktrees_dir"
    
    # Parse input
    if [ -z "$1" ]; then
        # Auto-generate worktree name with timestamp
        worktree_name="workspace-$(date +%Y%m%d-%H%M%S)"
        branch_name="$worktree_name"
    elif [[ "$1" =~ ^https?://github\.com/[^/]+/[^/]+/pull/([0-9]+) ]]; then
        # GitHub PR URL format: https://github.com/owner/repo/pull/123
        local pr_num="${BASH_REMATCH[1]:-${match[1]}}"
        echo "Detected GitHub PR URL: #$pr_num"
        echo "Fetching PR #$pr_num details from GitHub..."
        
        local repo=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
        if [ -z "$repo" ]; then
            echo "Error: Could not determine repository. Make sure 'gh' is installed and authenticated."
            return 1
        fi
        
        local pr_data=$(gh pr view "$pr_num" --json title,headRefName 2>/dev/null)
        if [ -z "$pr_data" ]; then
            echo "Error: Could not fetch PR #$pr_num"
            return 1
        fi
        
        local pr_title=$(echo "$pr_data" | jq -r '.title')
        branch_name=$(echo "$pr_data" | jq -r '.headRefName')
        worktree_name="pr-$pr_num-$(echo "$branch_name" | sed 's/\//-/g')"
        issue_context="Reviewing PR #$pr_num: $pr_title"
        
        # Fetch the PR branch from remote
        echo "Fetching remote branch..."
        git fetch origin "$branch_name:$branch_name" 2>/dev/null || git fetch origin "pull/$pr_num/head:$branch_name" 2>/dev/null
        
    elif [[ "$1" =~ ^https?://github\.com/[^/]+/[^/]+/issues/([0-9]+) ]]; then
        # GitHub issue URL format: https://github.com/owner/repo/issues/123
        local issue_num="${BASH_REMATCH[1]:-${match[1]}}"
        echo "Detected GitHub issue URL: #$issue_num"
        echo "Fetching issue #$issue_num details from GitHub..."
        
        local repo=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
        if [ -z "$repo" ]; then
            echo "Error: Could not determine repository. Make sure 'gh' is installed and authenticated."
            return 1
        fi
        
        local issue_data=$(gh issue view "$issue_num" --json title,body 2>/dev/null)
        if [ -z "$issue_data" ]; then
            echo "Error: Could not fetch issue #$issue_num"
            return 1
        fi
        
        local issue_title=$(echo "$issue_data" | jq -r '.title')
        worktree_name="issue-$issue_num-$(echo "$issue_title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | cut -c1-50)"
        branch_name="$worktree_name"
        issue_context="Working on issue #$issue_num: $issue_title"
        
    elif [[ "$1" =~ ^#([0-9]+)$ ]]; then
        # Issue number format: #123
        local issue_num="${BASH_REMATCH[1]}"
        echo "Fetching issue #$issue_num details from GitHub..."
        
        # Get repository info
        local repo=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
        if [ -z "$repo" ]; then
            echo "Error: Could not determine repository. Make sure 'gh' is installed and authenticated."
            return 1
        fi
        
        # Fetch issue details
        local issue_data=$(gh issue view "$issue_num" --json title,body 2>/dev/null)
        if [ -z "$issue_data" ]; then
            echo "Error: Could not fetch issue #$issue_num"
            return 1
        fi
        
        local issue_title=$(echo "$issue_data" | jq -r '.title')
        # Create branch name from issue number and title
        worktree_name="issue-$issue_num-$(echo "$issue_title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | cut -c1-50)"
        branch_name="$worktree_name"
        issue_context="Working on issue #$issue_num: $issue_title"
        
    elif [[ "$1" =~ ^!([0-9]+)$ ]]; then
        # PR number format: !456
        local pr_num="${BASH_REMATCH[1]}"
        echo "Fetching PR #$pr_num details from GitHub..."
        
        local repo=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
        if [ -z "$repo" ]; then
            echo "Error: Could not determine repository. Make sure 'gh' is installed and authenticated."
            return 1
        fi
        
        local pr_data=$(gh pr view "$pr_num" --json title,headRefName 2>/dev/null)
        if [ -z "$pr_data" ]; then
            echo "Error: Could not fetch PR #$pr_num"
            return 1
        fi
        
        local pr_title=$(echo "$pr_data" | jq -r '.title')
        branch_name=$(echo "$pr_data" | jq -r '.headRefName')
        worktree_name="pr-$pr_num-$(echo "$branch_name" | sed 's/\//-/g')"
        issue_context="Reviewing PR #$pr_num: $pr_title"
        
        # Fetch the PR branch from remote
        echo "Fetching remote branch..."
        git fetch origin "$branch_name:$branch_name" 2>/dev/null || git fetch origin "pull/$pr_num/head:$branch_name" 2>/dev/null
        
    else
        # Use provided branch name
        branch_name="$1"
        worktree_name="$1"
    fi
    
    local worktree_path="$worktrees_dir/$worktree_name"
    
    # Check if worktree already exists
    if [ -d "$worktree_path" ]; then
        echo "Error: Worktree already exists at $worktree_path"
        echo "Opening existing worktree in VS Code..."
        migrate_legacy_mcp_config "$worktree_path"
        code "$worktree_path"
        return 0
    fi
    
    echo "Creating worktree: $worktree_name"
    echo "Branch: $branch_name"
    echo "Path: $worktree_path"
    
    # Create the worktree
    if git worktree add -b "$branch_name" "$worktree_path" 2>/dev/null; then
        echo "✓ Worktree created successfully"
    elif git worktree add "$worktree_path" "$branch_name" 2>/dev/null; then
        echo "✓ Worktree created from existing branch"
    else
        echo "Error: Failed to create worktree"
        return 1
    fi

    migrate_legacy_mcp_config "$worktree_path"
    
    # Open in new VS Code window
    echo "Opening VS Code in new window..."
    code "$worktree_path"
    
    echo ""
    echo "✓ Workspace ready!"
    echo "  Path: $worktree_path"
    if [ -n "$issue_context" ]; then
        echo "  Context: $issue_context"
    fi
}

# export -f is bash-only; zsh doesn't support it
if [ -n "$BASH_VERSION" ]; then
    export -f workspace
fi
