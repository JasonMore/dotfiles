#!/bin/bash

# cpi-workspace: Create a git worktree and open it in a new VS Code window with Copilot CLI
# Usage:
#   cpi-workspace                    # Auto-generate worktree name
#   cpi-workspace branch-name        # Use specific branch name
#   cpi-workspace #123               # Create from issue number
#   cpi-workspace !456               # Create from PR number

cpi-workspace() {
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
    
    # Open in new VS Code window
    echo "Opening VS Code in new window..."
    code "$worktree_path"
    
    # Wait a moment for VS Code to open
    sleep 2
    
    # Create a startup script for the terminal
    local startup_script="$worktree_path/.copilot-startup.sh"
    cat > "$startup_script" << 'EOF'
#!/bin/bash
clear
echo "=========================================="
echo "   Copilot Workspace Ready"
echo "=========================================="
EOF
    
    if [ -n "$issue_context" ]; then
        echo "echo \"$issue_context\"" >> "$startup_script"
        echo "echo \"\"" >> "$startup_script"
        # Start Copilot CLI with issue context
        echo "gh copilot suggest \"$issue_context. Create a plan for implementing this.\"" >> "$startup_script"
    else
        echo "echo \"Branch: $branch_name\"" >> "$startup_script"
        echo "echo \"\"" >> "$startup_script"
        echo "echo 'Starting Copilot CLI...'\"" >> "$startup_script"
        echo "echo \"\"" >> "$startup_script"
        echo "gh copilot suggest" >> "$startup_script"
    fi
    
    chmod +x "$startup_script"
    
    echo ""
    echo "✓ Workspace ready!"
    echo "  Path: $worktree_path"
    echo "  VS Code should open automatically"
    echo ""
    echo "To start Copilot CLI in the new window, run:"
    echo "  bash .copilot-startup.sh"
    echo ""
    echo "Or just run: gh copilot suggest"
}

# Export the function
export -f cpi-workspace
