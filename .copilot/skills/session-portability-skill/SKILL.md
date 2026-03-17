---
description: This skill should be used when the user asks to "transfer my session", "move session to codespace", "sync session", "port session", "resume session in codespace", "copy session to codespace", "move session to local", or needs to migrate Copilot CLI session state between local and Codespace environments.
metadata:
    github-owner: github
    github-path: session-portability-skill
    github-ref: main
    github-repo: agent-skills
    github-sha: 3c077c01540bcd24d1e26914a922202984e3dfd4
    github-tree-sha: 421aeb0d8fb678002d0ae10c73b0b65ee128e68e
name: session-portability
---
# Session Portability

Migrate Copilot CLI sessions between local machines and GitHub Codespaces so you can resume work across environments.

## When to Use

- User wants to continue a local Copilot CLI session in a Codespace
- User wants to bring a Codespace session back to their local machine
- User asks about transferring, syncing, or porting session state
- User wants to resume a session started in a different environment

## Prerequisites

Before starting, verify:

1. **GitHub CLI** is installed and authenticated: `gh auth status`
2. **Codespace exists** and is running: `gh cs list`
3. **Session ID** is known: `ls ~/.copilot/session-state/`
4. **gh cs ssh** works: `gh cs ssh -c <codespace-name> -- echo ok`

## ⚠️ Security Considerations

### Session Data Contains Sensitive Information

Session data in `events.jsonl` contains the **full conversation history** including:
- Tool call results (file contents, command output)
- Source code that was read or generated
- Secrets, credentials, or API keys that appeared in conversation
- Internal system details discussed during the session

**You MUST:**
- Warn the user that session data may contain sensitive information
- Recommend they review `events.jsonl` before transferring
- Never transfer to shared or untrusted Codespaces
- Only transfer the specific session directory needed — never the entire `~/.copilot/` directory

### Token and Credential Safety

**NEVER pass tokens via command line arguments.** Tokens in command arguments are visible in:
- Process listings (`ps aux`)
- Shell history (`~/.bash_history`, `~/.zsh_history`)
- System audit logs

**Safe authentication methods for Codespaces:**
1. Run `gh auth login` interactively inside the Codespace
2. Set `GITHUB_TOKEN` or `COPILOT_GITHUB_TOKEN` via Codespace secrets in repository settings (they are injected as env vars, never visible in commands)
3. Pipe tokens via stdin if automation is required: `echo "$TOKEN" | gh cs ssh -c <name> -- gh auth login --with-token`

**NEVER do this:**
```bash
# ❌ DANGEROUS: Token visible in process list and shell history
gh cs ssh -c <name> -- "export COPILOT_GITHUB_TOKEN=ghp_abc123..."
```

### Path Validation

Session IDs are UUIDs. Before transferring, validate the session ID format to prevent path traversal:
- Valid: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- Invalid: `../../../etc/passwd`, `foo/../../bar`

Reject any session ID that contains `/`, `..`, or does not match UUID format.

### Transfer Security

`gh cs cp` uses SSH/SCP under the hood, so data is **encrypted in transit**. However:
- Verify the target Codespace is one you own and trust
- Do not transfer sessions to shared or org-wide Codespaces where others have access
- Consider deleting the session from the source after confirming a successful transfer

## Process: Local → Codespace

### Step 1: Identify the Session

```bash
ls ~/.copilot/session-state/
```

Each directory is a session UUID. To inspect a session before transfer:

```bash
# Check workspace metadata
cat ~/.copilot/session-state/<session-id>/workspace.yaml

# Review conversation history for sensitive content
head -20 ~/.copilot/session-state/<session-id>/events.jsonl
```

### Step 2: Validate the Session ID

Confirm the session ID is a valid UUID (no path traversal):

```bash
SESSION_ID="<session-id>"
if [[ "$SESSION_ID" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
  echo "Valid session ID"
else
  echo "Invalid session ID — aborting"
  exit 1
fi
```

### Step 3: Identify the Target Codespace

```bash
gh cs list
```

Pick the codespace name from the output.

### Step 4: Create the Target Directory

```bash
CODESPACE="<codespace-name>"
gh cs ssh -c "$CODESPACE" -- "mkdir -p /home/vscode/.copilot/session-state/"
```

### Step 5: Copy the Session

Use the `-e` flag — tilde (`~`) expansion does not work with `gh cs cp`:

```bash
gh cs cp -e -r ~/.copilot/session-state/"$SESSION_ID" \
  "remote:/home/vscode/.copilot/session-state/$SESSION_ID" \
  -c "$CODESPACE"
```

### Step 6: Patch workspace.yaml

Rewrite machine-specific paths to match the Codespace environment. Determine the repo name from the current workspace.yaml:

```bash
# Read the current repo name from workspace.yaml
REPO_NAME=$(grep 'repository:' ~/.copilot/session-state/"$SESSION_ID"/workspace.yaml | awk '{print $2}' | xargs basename)

# Patch paths in the Codespace
gh cs ssh -c "$CODESPACE" -- "sed -i \
  -e 's|^cwd:.*|cwd: /workspaces/$REPO_NAME|' \
  -e 's|^git_root:.*|git_root: /workspaces/$REPO_NAME|' \
  /home/vscode/.copilot/session-state/$SESSION_ID/workspace.yaml"
```

> **Note:** Copilot may auto-patch `workspace.yaml` on resume, but explicitly patching it ensures reliability.

### Step 7: Authenticate in the Codespace

SSH sessions do not inherit VS Code authentication. Set up auth inside the Codespace:

```bash
# Interactive login (recommended)
gh cs ssh -c "$CODESPACE" -- gh auth login

# Or use Codespace secrets (set GITHUB_TOKEN or COPILOT_GITHUB_TOKEN
# in your repo's Codespace secrets via Settings → Secrets → Codespaces)
```

### Step 8: Resume the Session

```bash
gh cs ssh -c "$CODESPACE" -- "cd /workspaces/$REPO_NAME && copilot --resume $SESSION_ID"
```

Or open the Codespace in VS Code / browser and run from the integrated terminal.

## Process: Codespace → Local

### Step 1: Identify the Session in the Codespace

```bash
CODESPACE="<codespace-name>"
gh cs ssh -c "$CODESPACE" -- "ls /home/vscode/.copilot/session-state/"
```

### Step 2: Validate and Review

Validate the session ID is a UUID (same check as above). Review contents for sensitive data before copying to local:

```bash
gh cs ssh -c "$CODESPACE" -- "head -20 /home/vscode/.copilot/session-state/<session-id>/events.jsonl"
```

### Step 3: Copy to Local

```bash
SESSION_ID="<session-id>"
gh cs cp -e -r \
  "remote:/home/vscode/.copilot/session-state/$SESSION_ID" \
  ~/.copilot/session-state/"$SESSION_ID" \
  -c "$CODESPACE"
```

### Step 4: Patch workspace.yaml for Local

```bash
# Rewrite paths to your local working directory
LOCAL_CWD=$(pwd)
LOCAL_GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$LOCAL_CWD")

sed -i.bak \
  -e "s|^cwd:.*|cwd: $LOCAL_CWD|" \
  -e "s|^git_root:.*|git_root: $LOCAL_GIT_ROOT|" \
  ~/.copilot/session-state/"$SESSION_ID"/workspace.yaml

rm ~/.copilot/session-state/"$SESSION_ID"/workspace.yaml.bak
```

### Step 5: Resume Locally

```bash
copilot --resume "$SESSION_ID"
```

## Session Data Anatomy

| File | Purpose | Portable? |
|------|---------|-----------|
| `events.jsonl` | Full conversation replay | ✅ Yes — self-contained |
| `workspace.yaml` | Metadata (cwd, git_root, repo, branch) | ⚠️ Needs path rewriting |
| `files/` | Working files | ✅ Yes |
| `checkpoints/` | Git checkpoint data | ✅ Yes |
| `session.db` | Session database | ✅ Yes |
| `plan.md` | Session plan | ✅ Yes |

## Troubleshooting

### Authentication Errors

**Problem:** `copilot --resume` fails with auth errors in the Codespace.

SSH sessions don't inherit VS Code OAuth. Fix by running `gh auth login` inside the Codespace, or setting a Codespace secret:

1. Go to repo Settings → Secrets and variables → Codespaces
2. Add `GITHUB_TOKEN` or `COPILOT_GITHUB_TOKEN`
3. Rebuild the Codespace to pick up the new secret

### `gh cs cp` Fails with Tilde Paths

**Problem:** `gh cs cp -r ~/... remote:~/...` fails.

Tilde expansion doesn't work with `gh cs cp`. Use the `-e` flag and absolute paths:
```bash
# ❌ Fails
gh cs cp -r ~/session remote:~/session

# ✅ Works
gh cs cp -e -r ~/.copilot/session-state/ID remote:/home/vscode/.copilot/session-state/ID
```

### Session Resumes but Paths Are Wrong

**Problem:** Copilot resumes but can't find the repo or working directory.

Patch `workspace.yaml` to match the target environment's paths (see Steps 6 or 4 above). The `cwd` and `git_root` fields must point to valid directories.

### Codespace Not Found

**Problem:** `gh cs ssh` or `gh cs cp` can't find the Codespace.

```bash
# List available Codespaces
gh cs list

# Start a stopped Codespace
gh cs start -c <codespace-name>
```

## Boundaries

**This skill WILL:**
- Transfer individual sessions between local and Codespace environments
- Patch `workspace.yaml` paths for the target environment
- Guide authentication setup in Codespaces
- Validate session IDs to prevent path traversal

**This skill will NOT:**
- Sync sessions automatically or continuously
- Transfer the entire `~/.copilot/` directory
- Handle transfers between two Codespaces (use local as intermediary)
- Manage Codespace creation or configuration
- Forward or inject credentials into remote environments via command arguments
