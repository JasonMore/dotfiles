# Example: Session Portability

## Scenario 1: Transfer a Local Session to a Codespace

### User Request

> "Transfer my current session to my Codespace"

### Agent Response

The agent identifies the current session, validates the ID, checks for a running Codespace, and performs the transfer:

```
I'll transfer your current session to your Codespace. Let me walk through this step by step.

1. Finding your current session...
   Session ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

2. Validating session ID format... ✅ Valid UUID

3. ⚠️  Security note: Session data in events.jsonl contains your full conversation
   history, which may include source code or sensitive information. This will be
   transferred over SSH (encrypted in transit) to your Codespace.

4. Finding your Codespace...
   Available: fluffy-space-disco-abc123 (github/my-repo)

5. Creating target directory...
   $ gh cs ssh -c fluffy-space-disco-abc123 -- "mkdir -p /home/vscode/.copilot/session-state/"

6. Copying session data...
   $ gh cs cp -e -r ~/.copilot/session-state/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
       remote:/home/vscode/.copilot/session-state/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
       -c fluffy-space-disco-abc123

7. Patching workspace.yaml paths for Codespace...
   cwd: /workspaces/my-repo
   git_root: /workspaces/my-repo

8. Verifying transfer...
   ✅ Session transferred successfully!

To resume in your Codespace, open it and run:
   copilot --resume a1b2c3d4-e5f6-7890-abcd-ef1234567890

Note: You may need to run `gh auth login` in the Codespace terminal
if you haven't authenticated there yet.
```

### Outcome

The session is copied to the Codespace with paths patched. The user can open the Codespace and resume the session.

---

## Scenario 2: Bring a Codespace Session Back to Local

### User Request

> "Copy my Codespace session to my local machine so I can keep working offline"

### Agent Response

```
I'll bring your Codespace session to your local machine.

1. Listing sessions in your Codespace...
   $ gh cs ssh -c fluffy-space-disco-abc123 -- "ls /home/vscode/.copilot/session-state/"
   Found: f9e8d7c6-b5a4-3210-fedc-ba0987654321

2. Validating session ID format... ✅ Valid UUID

3. ⚠️  Security reminder: This session data contains your full conversation history.
   Make sure your local machine is trusted and secure.

4. Copying session to local...
   $ gh cs cp -e -r \
       remote:/home/vscode/.copilot/session-state/f9e8d7c6-b5a4-3210-fedc-ba0987654321 \
       ~/.copilot/session-state/f9e8d7c6-b5a4-3210-fedc-ba0987654321 \
       -c fluffy-space-disco-abc123

5. Patching workspace.yaml for local paths...
   cwd: /Users/you/code/my-repo
   git_root: /Users/you/code/my-repo

6. ✅ Session ready locally!

Resume with:
   copilot --resume f9e8d7c6-b5a4-3210-fedc-ba0987654321
```

### Outcome

The session is copied from the Codespace to the local machine with paths updated. The user can resume offline.

---

## Scenario 3: Auth Issues After Transfer

### User Request

> "I transferred my session but copilot --resume gives me an auth error"

### Agent Response

```
SSH sessions into Codespaces don't inherit VS Code's OAuth authentication.
You need to authenticate separately. Here are your options:

Option 1 — Interactive login (recommended):
   Open a terminal in your Codespace and run:
   $ gh auth login

Option 2 — Codespace secrets (persistent):
   1. Go to your repo → Settings → Secrets and variables → Codespaces
   2. Add a secret named GITHUB_TOKEN or COPILOT_GITHUB_TOKEN
   3. Rebuild the Codespace to pick up the new secret

⚠️  Do NOT pass tokens via command arguments like:
   gh cs ssh -c name -- "export TOKEN=ghp_..."
   This exposes the token in shell history and process listings.

After authenticating, try resuming again:
   $ copilot --resume a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Outcome

The user authenticates properly in the Codespace without exposing credentials, and the session resumes successfully.
