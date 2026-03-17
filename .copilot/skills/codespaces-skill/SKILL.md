---
name: codespaces
description: This skill should be used when the user asks "create a codespace", "open a codespace", "connect to a codespace", "SSH into a codespace", "list my codespaces", "delete a codespace", "stop a codespace", "forward a port", or needs help creating, managing, or connecting to GitHub Codespaces using the GitHub CLI.
---

# Codespaces - Create, Open, and Connect via GitHub CLI

Helps agents create, list, connect to, and manage GitHub Codespaces using `gh codespace` (alias: `gh cs`) commands.

## When to Use This Skill

- User wants to create a new codespace for a repository
- User wants to open an existing codespace in VS Code or a browser
- User wants to SSH into a codespace
- User wants to list, stop, or delete codespaces
- User wants to forward or manage ports in a codespace
- User wants to copy files to/from a codespace
- User asks anything about working with GitHub Codespaces from the terminal

## Prerequisites

```bash
# Verify gh CLI is installed and authenticated
gh auth status

# Codespace commands are built into gh - no extension needed
gh codespace --help
```

## Codespace Workspace Structure

When you SSH into a codespace, you start in `/home/vscode`. The repository files are located in `/workspaces/`:

```
/workspaces/
├── <repo-name>/           # Main repository (e.g., github/github)
├── <related-repos>/       # Any related repositories (multi-repo setups)
└── .codespaces/           # Codespace metadata
    ├── .persistedshare/   # Shared persistent data
    └── shared/            # Shared temporary data
```

**Important paths:**
- **Repository root**: `/workspaces/<repo-name>/` (e.g., `/workspaces/github/`)
- **Home directory**: `/home/vscode` (default SSH landing directory)
- **Workspace parent**: `/workspaces/` (contains all repositories)

**Multi-repository codespaces:**
Some repositories (like `github/github`) automatically include related repositories in `/workspaces/`. For example, `github/github` codespaces include both `/workspaces/github/` and `/workspaces/github-ui/`.

## Core Commands

### 1. Create a Codespace

**Naming Convention:**
Use abbreviated repo names with month and day for easy identification:
- `github/github` → `"gh-gh feb17"`
- `github/github-ui` → `"gh-ui feb17"`
- `github/ops` → `"gh-ops feb17"`
- Pattern: `"<abbreviated-repo> <month><day>"`

```bash
# Interactive: pick repo and branch
gh cs create

# Specify repo
gh cs create -R owner/repo

# Specify repo and branch
gh cs create -R owner/repo -b main

# Specify machine type
gh cs create -R owner/repo -m basicLinux32gb

# Set a display name using naming convention
gh cs create -R github/github -d "gh-gh feb17"
gh cs create -R github/github-ui -d "gh-ui feb17"
gh cs create -R github/ops -d "gh-ops feb17"

# Set idle timeout and retention
gh cs create -R owner/repo --idle-timeout 30m --retention-period 72h

# Use a specific devcontainer config
gh cs create -R owner/repo --devcontainer-path .devcontainer/python/devcontainer.json

# Create and open in browser
gh cs create -R owner/repo -w
```

**Common machine types:**
- `basicLinux32gb` - 2 cores, 8 GB RAM, 32 GB storage
- `standardLinux32gb` - 4 cores, 16 GB RAM, 32 GB storage
- `premiumLinux` - 8 cores, 32 GB RAM, 64 GB storage
- `largePremiumLinux` - 16 cores, 64 GB RAM, 128 GB storage

### 2. List Codespaces

```bash
# List your codespaces
gh cs list

# JSON output with specific fields
gh cs list --json name,repository,state,machineName

# Filter by repo
gh cs list -R owner/repo

# Limit results
gh cs list -L 10
```

### 3. Connect: Open in VS Code

```bash
# Interactive picker
gh cs code

# Open a specific codespace
gh cs code -c codespace-name-12345

# Open in VS Code Insiders
gh cs code --insiders

# Open in VS Code in the browser
gh cs code -w

# Filter by repo
gh cs code -R owner/repo
```

### 4. Connect: SSH

```bash
# Interactive picker
gh cs ssh

# SSH into a specific codespace
gh cs ssh -c codespace-name-12345

# Run a command over SSH
gh cs ssh -c codespace-name-12345 -- ls -la

# Filter by repo
gh cs ssh -R owner/repo

# Generate SSH config for native SSH client integration
gh cs ssh --config > ~/.ssh/codespaces
printf 'Match all\nInclude ~/.ssh/codespaces\n' >> ~/.ssh/config
# Then use: ssh codespace-name-12345
```

**SSH notes:**
- You start in `/home/vscode` when SSH connects
- Navigate to the repository: `cd /workspaces/<repo-name>`
- List all repositories: `ls /workspaces/`
- The codespace may include multiple repositories in `/workspaces/` for multi-repo setups

### 5. Stop a Codespace

```bash
# Interactive picker
gh cs stop

# Stop a specific codespace
gh cs stop -c codespace-name-12345
```

### 6. Delete Codespaces

```bash
# Interactive picker
gh cs delete

# Delete a specific codespace
gh cs delete -c codespace-name-12345

# Delete all your codespaces (with confirmation)
gh cs delete --all

# Force delete (skip confirmation for unsaved changes)
gh cs delete -c codespace-name-12345 --force

# Delete codespaces older than 7 days
gh cs delete --days 7
```

### 7. View Codespace Details

```bash
# Interactive picker
gh cs view

# View a specific codespace
gh cs view -c codespace-name-12345

# View as JSON
gh cs view -c codespace-name-12345 --json displayName,state,machineName,lastUsedAt
```

### 8. Port Forwarding

```bash
# List ports for a codespace
gh cs ports -c codespace-name-12345

# Forward a local port to a codespace port
gh cs ports forward 8080:8080 -c codespace-name-12345

# Forward multiple ports
gh cs ports forward 8080:8080 3000:3000 -c codespace-name-12345

# Change port visibility
gh cs ports visibility 8080:public -c codespace-name-12345
gh cs ports visibility 8080:private -c codespace-name-12345
gh cs ports visibility 8080:org -c codespace-name-12345
```

### 9. Copy Files

```bash
# Copy from local to codespace
gh cs cp local-file.txt remote:/workspaces/<repo-name>/ -c codespace-name-12345

# Copy from codespace to local
gh cs cp remote:/workspaces/<repo-name>/file.txt ./local-dir/ -c codespace-name-12345

# Recursive copy
gh cs cp -r local-dir remote:/workspaces/<repo-name>/ -c codespace-name-12345
```

**Path notes:**
- Use `remote:/workspaces/<repo-name>/` for repository files
- Use `remote:/home/vscode/` for home directory files
- Replace `<repo-name>` with the actual repository name (e.g., `github` for `github/github`)

### 10. View Logs

```bash
# View creation logs
gh cs logs -c codespace-name-12345
```

### 11. Rebuild a Codespace

```bash
# Rebuild (uses cache)
gh cs rebuild -c codespace-name-12345

# Full rebuild (no cache)
gh cs rebuild --full -c codespace-name-12345
```

## Common Workflows

### Create and connect to a codespace

```bash
# Create codespace with proper naming convention (e.g., for github/github on Feb 17)
gh cs create -R github/github -d "gh-gh feb17" -b main
# Output: codespace-name-abc123

# Open in VS Code
gh cs code -c codespace-name-abc123

# Or SSH in
gh cs ssh -c codespace-name-abc123
```

**Generate current date for display name:**
```bash
# Bash: Generate today's display name for github/github
DISPLAY_NAME="gh-gh $(date +"%b %d" | tr 'A-Z' 'a-z' | sed 's/ 0/ /;s/ //')"
gh cs create -R github/github -d "$DISPLAY_NAME"
```

### Find and resume a codespace

```bash
# List codespaces for a repo
gh cs list -R owner/repo --json name,state,displayName

# Connect to an existing one
gh cs code -c codespace-name-12345
```

### Clean up old codespaces

```bash
# See what would be deleted
gh cs list --json name,lastUsedAt,repository

# Delete codespaces older than 14 days
gh cs delete --days 14
```

## Process for Helping Users

### Step 1: Identify the Goal
- Are they creating, connecting, or managing?
- Do they have a specific repo in mind?
- Do they need a specific machine size or branch?

**When creating a new codespace:**
- Always set a display name using the convention: `"<abbreviated-repo> <month><day>"`
- Examples:
  - `github/github` → `gh cs create -R github/github -d "gh-gh feb17"`
  - `github/github-ui` → `gh cs create -R github/github-ui -d "gh-ui feb17"`
  - `github/ops` → `gh cs create -R github/ops -d "gh-ops feb17"`
- Use the current month abbreviation (jan, feb, mar, etc.) and day (01-31)

### Step 2: Check Existing Codespaces
Before creating a new one, check if they already have a matching codespace:
```bash
gh cs list -R owner/repo --json name,state,displayName,branch
```

### Step 3: Execute the Command
Run the appropriate `gh cs` command. For interactive commands, prefer specifying flags explicitly to avoid interactive prompts that may not work well in this context.

### Step 4: Confirm Success
After creating or connecting, verify the result:
```bash
# After creating
gh cs view -c "$CS_NAME" --json name,state,displayName

# After connecting via SSH, run a test command
gh cs ssh -c "$CS_NAME" -- echo "Connected successfully"
```

## Error Handling

### No codespaces available
```
If `gh cs list` returns empty, guide the user to create one with `gh cs create`.
```

### Repository not found or no access
```
Verify the user has access to the repository:
  gh repo view owner/repo
```

### Machine type not available
```
List available machine types by starting `gh cs create` interactively,
or check the repository's codespace settings on GitHub.
```

### Codespace creation fails
```
Common causes:
- Organization policy restrictions
- Billing limits reached
- Invalid devcontainer.json configuration
- Branch does not exist

Check: gh cs create -R owner/repo -s  (shows status during creation)
```

## Boundaries

**Will:**
- Create, list, connect to, stop, delete codespaces
- Forward ports and copy files
- Help with SSH configuration for codespaces
- Run commands inside codespaces via SSH

**Will Not:**
- Modify repository devcontainer configurations (unless asked separately)
- Change organization codespace policies
- Manage codespace secrets (use `gh secret` commands for that)
