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

**Hot reload:** The server watches for file changes and rebuilds automatically. After editing files (Ruby, JS/TS, CSS), just refresh the browser — no server restart needed. The UI build (Vite/rspack) also hot-reloads frontend assets.

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

Edit files → hot reload rebuilds automatically → refresh browser → verify. Repeat.

```bash
# Edit
gh cs ssh -c NAME -- "cd /workspaces/github && sed -i 's/old/new/' path/to/file.rb"

# Just refresh — no restart needed
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

## Surviving Interruptions

The user may stop you mid-task. Design for resumption:

1. **Use `nohup` and `&` for server commands.** The server runs inside the codespace, not locally. It survives local interruptions.
2. **Port forwarding dies when your local shell dies.** Always restart it first:
   ```bash
   gh cs ports forward 80:8880 -c NAME
   ```
3. **Check state before acting.** On resumption:
   ```bash
   # Is the codespace running?
   gh cs list -R github/github --json name,state
   
   # Is the server up?
   gh cs ssh -c NAME -- "curl -s -o /dev/null -w '%{http_code}' http://github.localhost/status"
   
   # Is port forwarding alive?
   curl -s -o /dev/null -w '%{http_code}' http://localhost:8880/status
   ```
4. **Re-establish port forwarding as async bash** (not detached — detached dies quickly for port forwards).
5. **Feature flag initializers persist across restarts.** No need to re-add them.

## Feature Flags

Many features are behind Vexi feature flags. See the project skill at `.github/skills/feature-flags/SKILL.md` for full details.

Quick version — to enable a flag in the codespace:

```bash
# Persistent — all processes see it (recommended)
gh cs ssh -c NAME -- 'cd /workspaces/github && bin/rails runner "FeatureFlag.vexi_management.enable_feature_flag(\"flag_name\")"'
```

No server restart needed. The flag persists to the backing store and is visible to the web server immediately.

To disable when done:

```bash
gh cs ssh -c NAME -- 'cd /workspaces/github && bin/rails runner "FeatureFlag.vexi_management.disable_feature_flag(\"flag_name\")"'
```

**Important:** `FeatureFlag.vexi.add_override` is per-process in-memory only. It does NOT affect the web server. Always use `vexi_management` instead.

## Dev Login

Default seed user: `monalisa`. Password is auto-filled on the login page.

1. Navigate to `http://localhost:8880/login`
2. Click **Sign in** — credentials are pre-filled
3. If an OTP/2FA screen appears, the code is auto-filled — just click **Verify**
4. Session persists across page navigations

If the password isn't working, reset it:

```bash
gh cs ssh -c NAME -- 'cd /workspaces/github && bin/rails runner '"'"'u = User.find_by(login: "monalisa"); u.password = "password"; u.save(validate: false)'"'"''
```

## Disable Accessibility Scanner

The dev app shows an accessibility scanner overlay that clutters Chrome MCP snapshots. Disable it by setting a cookie:

```javascript
// Via Chrome MCP evaluate_script
() => {
  const expires = new Date(Date.now() + 100 * 365 * 24 * 60 * 60 * 1000).toUTCString();
  document.cookie = `accessibilityScan=false; path=/; expires=${expires}`;
}
```

Or after navigating to a page:

```
evaluate_script(function: "() => { document.cookie = 'accessibilityScan=false; path=/; expires=' + new Date(Date.now() + 3.156e12).toUTCString(); }")
```

Do this once after first login. The cookie lasts ~100 years.

## Uploading Screenshots to PRs

Chrome MCP can take screenshots of the local dev app. To add them to a PR description:

1. **Save screenshots to files:**
   ```
   take_screenshot(filePath="/tmp/screenshot-collapsed.png")
   take_screenshot(filePath="/tmp/screenshot-expanded.png")
   ```

2. **Compress (macOS `sips`):**
   ```bash
   sips -s format jpeg -s formatOptions 50 /tmp/screenshot-collapsed.png --out /tmp/screenshot-collapsed.jpg
   ```

3. **Upload to the PR branch via GitHub Contents API:**
   ```bash
   CONTENT=$(base64 -i /tmp/screenshot-collapsed.jpg)
   gh api repos/OWNER/REPO/contents/.github/screenshots/collapsed.jpg \
     --method PUT \
     -f message="Add screenshot: collapsed state" \
     -f branch="my-feature-branch" \
     -f content="$CONTENT" \
     --jq '.content.download_url'
   ```

4. **Reference in PR body:**
   ```markdown
   ![Collapsed](https://raw.githubusercontent.com/OWNER/REPO/BRANCH/.github/screenshots/collapsed.jpg)
   ```

5. **Update the PR description:**
   ```bash
   # Write body to a file first (heredocs break in zsh with HTML comments)
   # Use the create_file tool to write /tmp/pr_body.md, then:
   gh pr edit PR_NUMBER -R OWNER/REPO --body-file /tmp/pr_body.md
   rm /tmp/pr_body.md
   ```

**Why not use GitHub's upload/policies API?** It requires a browser session cookie — a CLI token alone returns 422.

**Why not navigate to github.com directly?** Chrome MCP hits the SSO/Okta login wall for internal repos. Use `gh` CLI for all github.com operations instead.

## Gotchas

- **Branch is `master`**, not `main`
- Port forward must stay running. If it dies, restart it
- Server takes 1-3 min to boot. Poll `/status` before browsing
- The app expects `github.localhost` as hostname. Port-forwarded `localhost:8880` works for most pages
- For full hostname match, add `127.0.0.1 github.localhost` to local `/etc/hosts` and forward 80:80
- **SSH PATH misses Node.** `gh cs ssh` doesn't load `remoteEnv` from devcontainer.json. System Node is v10; the codespace terminal gets v24 from `vendor/node/`. The correct Node lives at `/workspaces/github/vendor/node/` (symlinked to `node-v24.8.0-linux-x64/bin/`). Fix: prefix commands with the right PATH:
  ```bash
  gh cs ssh -c NAME -- 'export PATH="/workspaces/github/vendor/node:/workspaces/github/vendor/node/bin:$PATH" && node --version'
  ```
  **Root cause:** `.devcontainer/sshrc` adds Go to `/etc/profile` for SSH but skips Node. The `remoteEnv.PATH` in `devcontainer.json` includes `/workspaces/github/vendor/node` — but only for VS Code terminals, not SSH.
- **Feature flags: use `vexi_management`, not `add_override`.** `add_override` is per-process in-memory. `vexi_management.enable_feature_flag` persists to the backing store.
- **Clean up temp initializers** when done: `rm config/initializers/z_temp_feature_flags.rb`
- **`script/toggle-feature-flag` needs Ruby 3.x.** Codespace may have Ruby 2.7. Use `bin/rails runner` with `vexi_management` instead.
- **Chrome MCP only works on localhost.** Don't navigate to github.com — SSO blocks you. Use `gh` CLI for github.com API calls.
- **Use `sips` for image compression on macOS.** PIL/Pillow not installed. `sips -s format jpeg -s formatOptions 50 in.png --out out.jpg`

## References

- [references/ports.md](references/ports.md) — Port map and service details
- [references/chrome-mcp.md](references/chrome-mcp.md) — Chrome MCP tool reference
