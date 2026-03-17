# Codespaces Skill

Create, open, and connect to GitHub Codespaces using the GitHub CLI - manage your cloud development environments from the terminal.

## When to Use This Skill

- Creating a new codespace for a repository
- Opening an existing codespace in VS Code or the browser
- SSHing into a codespace
- Listing, stopping, or deleting codespaces
- Forwarding ports or copying files
- Any codespace management from the terminal

## Prerequisites

```bash
# Verify gh is installed and authenticated
gh auth status

# Codespace commands are built into gh CLI - no extension needed
gh cs --help
```

## Installation

### Using gh-skills (Recommended)

```bash
# Install the extension
gh extension install github/gh-skills

# Install the skill
gh skills install codespaces
```

### Manual Installation

**Personal Skills**
```bash
cp -r codespaces-skill ~/.copilot/skills/
```

**Project Skills**
```bash
cp -r codespaces-skill /path/to/repo/.github/skills/
```

## Usage

This skill activates when you ask Copilot to:
- "Create a codespace for owner/repo"
- "Open my codespace in VS Code"
- "SSH into my codespace"
- "List my codespaces"
- "Stop my codespace"
- "Delete old codespaces"
- "Forward port 3000 from my codespace"

The skill will:
1. Check for existing codespaces when relevant
2. Run the appropriate `gh cs` command
3. Confirm the operation succeeded
4. Provide next steps (e.g., how to connect after creating)

## Common Commands

| Command | Description |
|---------|-------------|
| `gh cs create -R owner/repo` | Create a codespace |
| `gh cs list` | List your codespaces |
| `gh cs code` | Open in VS Code |
| `gh cs code -w` | Open in VS Code (browser) |
| `gh cs ssh` | SSH into a codespace |
| `gh cs stop` | Stop a running codespace |
| `gh cs delete` | Delete a codespace |
| `gh cs ports forward 8080:8080` | Forward a port |
| `gh cs cp local remote:/path` | Copy files |

## Examples

### Create and open a codespace
```
User: "Create a codespace for github/docs on the main branch"
Agent: Creates the codespace, then opens it in VS Code
```

### Connect to an existing codespace
```
User: "SSH into my codespace for github/github"
Agent: Lists matching codespaces, connects via SSH
```

### Clean up codespaces
```
User: "Delete all my codespaces older than 7 days"
Agent: Runs gh cs delete --days 7
```

## Tips

- Use `gh cs` as a shorthand for `gh codespace`
- Specify `-R owner/repo` to skip the interactive repo picker
- Use `-c codespace-name` to target a specific codespace
- Add `--json` to any list/view command for machine-readable output
- Set up SSH config with `gh cs ssh --config` for native SSH integration
- **Always use display names** with the convention: `"<abbreviated-repo> <month><day>"`
  - Examples: `"gh-gh feb17"`, `"gh-ui feb11"`, `"gh-ops jan29"`

---

**Required:** GitHub CLI (`gh`) with authentication (`gh auth login`)
