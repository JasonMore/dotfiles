---
name: codespace-dev
description: >
  Drive a github/github codespace from the local laptop. Use when the user asks to
  "start a codespace", "develop in a codespace", "run the server", "make changes
  remotely", "open the app in a browser", or wants to build and test features
  inside a codespace while running Copilot CLI locally. Covers creating codespaces,
  remote file editing, starting the dev server, port forwarding, and browser
  verification via Chrome MCP.
author: JasonMore
---

# Codespace Dev Workflow

Build and test github/github features inside a remote codespace. Run Copilot CLI on your laptop. Edit files, start the server, forward ports, and verify in the browser — all without opening VS Code.

## When to Use

- User wants to develop in a codespace from the terminal
- User asks to start a server, run tests, or make changes in a codespace
- User wants to visually verify changes in a browser

## Workflow

### 1. Create or find a codespace

```bash
# Create new (default branch is master, not main)
gh cs create -R github/github -d "gh-gh mar17" -b master

# Find existing
gh cs list -R github/github --json name,state,displayName
```

Store the codespace name. Use it as `-c NAME` in all commands.

### 2. Edit files remotely

Pick the best method for the change size:

```bash
# Small edits: SSH + sed
gh cs ssh -c NAME -- "cd /workspaces/github && sed -i 's/old/new/' path/to/file.rb"

# Read files
gh cs ssh -c NAME -- "cat /workspaces/github/app/models/user.rb"

# Copy files to codespace
gh cs cp local_file.rb remote:/workspaces/github/app/models/ -c NAME

# Copy from codespace
gh cs cp remote:/workspaces/github/app/models/user.rb ./ -c NAME

# Multi-file: use git
gh cs ssh -c NAME -- "cd /workspaces/github && git pull origin my-branch"
```

Batch SSH commands when possible. Each call has ~5-8s overhead.

### 3. Start the dev server

```bash
gh cs ssh -c NAME -- "cd /workspaces/github && nohup script/server --ui > /tmp/server.log 2>&1 &"
```

Server flags: `--ui` (UI assets), `--vite`, `--rspack`, `--debug`, `--multi-tenant`.

Poll until ready (~1-3 min):

```bash
gh cs ssh -c NAME -- "curl -s -o /dev/null -w '%{http_code}' http://github.localhost/status"
# Returns 200 when ready
```

Check server logs if something fails:

```bash
gh cs ssh -c NAME -- "tail -50 /tmp/server.log"
```

### 4. Forward ports

```bash
# Forward web server (port 80) to localhost:8880
gh cs ports forward 80:8880 -c NAME
```

This runs as a long-lived process. Keep it alive in a background shell.

For port details, see [references/ports.md](references/ports.md).

### 5. Browse with Chrome MCP

Use Chrome MCP tools to view and interact with the app on localhost:

1. `navigate_page(url="http://localhost:8880")` — open the app
2. `take_snapshot()` — get page structure (accessibility tree with uids)
3. `click(uid="...")` — click elements
4. `fill(uid="...", value="...")` — type into inputs
5. `take_screenshot()` — visual check
6. `wait_for(text=["Expected text"])` — wait for content

For the full tool list, see [references/chrome-mcp.md](references/chrome-mcp.md).

### 6. Iterate

Edit files → server auto-reloads → refresh browser → verify. Repeat.

```bash
# Edit
gh cs ssh -c NAME -- "cd /workspaces/github && sed -i 's/old/new/' path/to/file.rb"

# Refresh
navigate_page(type="reload")

# Check
take_snapshot()
take_screenshot()
```

## Key Facts

- Repo root in codespace: `/workspaces/github/`
- UI repo: `/workspaces/github-ui/`
- Main web app: port 80
- Default hostname: `github.localhost`
- Health check: `http://github.localhost/status`
- Process manager: Overmind (runs ~40 services from Procfile)

## Gotchas

- **Branch is `master`**, not `main`
- Port forward must stay running. If it dies, restart it
- Server takes 1-3 min to boot. Poll `/status` before browsing
- The app expects `github.localhost` as hostname. Port-forwarded `localhost:8880` works for most pages
- For full hostname match, add `127.0.0.1 github.localhost` to local `/etc/hosts` and forward 80:80

## References

- [references/ports.md](references/ports.md) — Port map and service details
- [references/chrome-mcp.md](references/chrome-mcp.md) — Chrome MCP tool reference
