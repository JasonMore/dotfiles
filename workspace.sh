#!/usr/bin/env bash

# workspace: Create a git worktree and open it in a new VS Code window
# Usage:
#   workspace                                              # Auto-generate worktree name
#   workspace branch-name                                  # Use specific branch name
#   workspace #123                                         # Create from issue number
#   workspace !456                                         # Create from PR number
#   workspace https://github.com/owner/repo/pull/123       # Create from PR URL
#   workspace https://github.com/owner/repo/issues/456     # Create from issue URL

workspace() {
    local worktree_name=""
    local branch_name=""
    local issue_context=""

    # Get the git root directory
    local git_root
    git_root=$(git rev-parse --show-toplevel 2>/dev/null)
    if [ -z "$git_root" ]; then
        echo "Error: Not in a git repository"
        return 1
    fi

    # Directory for worktrees (sibling to main repo)
    local worktrees_dir="${git_root}-worktrees"
    mkdir -p "$worktrees_dir"

    # Parse input
    if [ -z "${1:-}" ]; then
        # Auto-generate worktree name with timestamp
        worktree_name="workspace-$(date +%Y%m%d-%H%M%S)"
        branch_name="$worktree_name"

    elif [[ "$1" =~ ^https?://github\.com/[^/]+/[^/]+/pull/([0-9]+) ]]; then
        # GitHub PR URL format: https://github.com/owner/repo/pull/123
        local pr_num="${BASH_REMATCH[1]}"
        echo "Detected GitHub PR URL: #$pr_num"
        echo "Fetching PR #$pr_num details from GitHub..."

        if ! command -v gh >/dev/null 2>&1; then
            echo "Error: 'gh' is required for PR/issue lookups"
            return 1
        fi
        if ! command -v jq >/dev/null 2>&1; then
            echo "Error: 'jq' is required for PR/issue lookups"
            return 1
        fi

        local pr_data
        pr_data=$(gh pr view "$pr_num" --json title,headRefName 2>/dev/null)
        if [ -z "$pr_data" ]; then
            echo "Error: Could not fetch PR #$pr_num"
            return 1
        fi

        local pr_title
        pr_title=$(echo "$pr_data" | jq -r '.title')
        branch_name=$(echo "$pr_data" | jq -r '.headRefName')
        worktree_name="pr-$pr_num-$(echo "$branch_name" | sed 's/\//-/g')"
        issue_context="Reviewing PR #$pr_num: $pr_title"

    elif [[ "$1" =~ ^https?://github\.com/[^/]+/[^/]+/issues/([0-9]+) ]]; then
        # GitHub issue URL format: https://github.com/owner/repo/issues/123
        local issue_num="${BASH_REMATCH[1]}"
        echo "Detected GitHub issue URL: #$issue_num"
        echo "Fetching issue #$issue_num details from GitHub..."

        if ! command -v gh >/dev/null 2>&1; then
            echo "Error: 'gh' is required for PR/issue lookups"
            return 1
        fi
        if ! command -v jq >/dev/null 2>&1; then
            echo "Error: 'jq' is required for PR/issue lookups"
            return 1
        fi

        local issue_data
        issue_data=$(gh issue view "$issue_num" --json title,body 2>/dev/null)
        if [ -z "$issue_data" ]; then
            echo "Error: Could not fetch issue #$issue_num"
            return 1
        fi

        local issue_title
        issue_title=$(echo "$issue_data" | jq -r '.title')
        worktree_name="issue-$issue_num-$(echo "$issue_title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | cut -c1-50)"
        branch_name="$worktree_name"
        issue_context="Working on issue #$issue_num: $issue_title"

    elif [[ "$1" =~ ^#([0-9]+)$ ]]; then
        # Issue number format: #123
        local issue_num="${BASH_REMATCH[1]}"
        echo "Fetching issue #$issue_num details from GitHub..."

        if ! command -v gh >/dev/null 2>&1; then
            echo "Error: 'gh' is required for PR/issue lookups"
            return 1
        fi
        if ! command -v jq >/dev/null 2>&1; then
            echo "Error: 'jq' is required for PR/issue lookups"
            return 1
        fi

        local issue_data
        issue_data=$(gh issue view "$issue_num" --json title,body 2>/dev/null)
        if [ -z "$issue_data" ]; then
            echo "Error: Could not fetch issue #$issue_num"
            return 1
        fi

        local issue_title
        issue_title=$(echo "$issue_data" | jq -r '.title')
        worktree_name="issue-$issue_num-$(echo "$issue_title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | cut -c1-50)"
        branch_name="$worktree_name"
        issue_context="Working on issue #$issue_num: $issue_title"

    elif [[ "$1" =~ ^!([0-9]+)$ ]]; then
        # PR number format: !456
        local pr_num="${BASH_REMATCH[1]}"
        echo "Fetching PR #$pr_num details from GitHub..."

        if ! command -v gh >/dev/null 2>&1; then
            echo "Error: 'gh' is required for PR/issue lookups"
            return 1
        fi
        if ! command -v jq >/dev/null 2>&1; then
            echo "Error: 'jq' is required for PR/issue lookups"
            return 1
        fi

        local pr_data
        pr_data=$(gh pr view "$pr_num" --json title,headRefName 2>/dev/null)
        if [ -z "$pr_data" ]; then
            echo "Error: Could not fetch PR #$pr_num"
            return 1
        fi

        local pr_title
        pr_title=$(echo "$pr_data" | jq -r '.title')
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

    echo ""
    echo "✓ Workspace ready!"
    echo "  Path: $worktree_path"
    if [ -n "$issue_context" ]; then
        echo "  Context: $issue_context"
    fi
}

export -f workspace
