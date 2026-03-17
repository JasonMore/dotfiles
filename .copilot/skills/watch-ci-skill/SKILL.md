---
name: watch-ci
description: This skill should be used when the user asks to "watch CI", "monitor checks", "alert when CI passes", "alert when CI fails", "watch build status", "let me know when it's green", "monitor PR checks", "keep an eye on CI", "watch for failures", or needs background monitoring of GitHub Actions workflow runs, status checks, or CI/CD pipelines.
---

# Watch CI - Background CI/CD Monitoring

Monitors GitHub Actions workflows, status checks, and CI/CD pipelines in the background, providing notifications when checks complete, fail, or require attention.

## When to Use This Skill

- User wants to monitor CI status without blocking their workflow
- Waiting for checks to pass on a pull request
- Need notification when specific checks fail
- Monitoring multiple PRs or branches simultaneously
- Want to take action automatically when CI completes (e.g., auto-merge)

## Core Functionality

### 1. Identify Target to Monitor

Determine what to watch:

**Priority order:**
1. Explicit PR number provided by user (`PR #123`)
2. Current branch's associated PR
3. Most recent commit on current branch
4. Specific workflow run ID if provided

**Command to detect PR:**
```bash
# Get PR for current branch
gh pr view --json number,title,url,headRefName -q '.number'

# Get PR by number
gh pr view 123 --json number,title,url
```

### 2. Poll Check Status

Use `gh pr checks` with appropriate flags:

**For monitoring:**
```bash
# Watch required checks only
gh pr checks PR_NUMBER --required --watch --interval 30

# Watch all checks
gh pr checks PR_NUMBER --watch --interval 30

# Fail fast (exit on first failure)
gh pr checks PR_NUMBER --required --fail-fast --watch
```

**Output format:**
```
✓ build
✓ test
✗ lint (failed)
⊘ deploy (skipped)
○ security-scan (pending)
```

### 3. Run as Background Task

**Important:** Always suggest running as background task unless user explicitly requests foreground:

```bash
# Background with notification
gh pr checks PR_NUMBER --required --watch &

# Store PID for later reference
echo $! > /tmp/watch-ci-$PR_NUMBER.pid
```

**Notification integration:**
- Use system notifications when available (`osascript` on macOS, `notify-send` on Linux)
- Fall back to terminal output with clear status
- Log to temporary file for review: `/tmp/watch-ci-$PR_NUMBER.log`

### 4. Determine Status and Next Actions

**On Success (all green):**
- Notify user: "✅ All checks passed for PR #123"
- Suggest next action:
  - "Ready to merge?" (if mergeable)
  - "Waiting for review approval" (if reviews required)
  - "Auto-merging now" (if user requested)

**On Failure:**
- Notify user: "❌ Checks failed for PR #123"
- Show which checks failed
- Provide links to logs:
  ```bash
  gh pr checks PR_NUMBER --required
  gh run view RUN_ID --log-failed
  ```
- Suggest actions:
  - "View failed logs?"
  - "Re-run failed jobs?"
  - "Want me to analyze the failure?"

**On Partial (some required pending):**
- Continue monitoring
- Only notify on state change

## Implementation Pattern

### Background Process Template

```bash
#!/bin/bash
# watch-ci-background.sh

PR_NUMBER=$1
NOTIFY_ON_SUCCESS=${2:-true}
NOTIFY_ON_FAILURE=${3:-true}

# Start monitoring
gh pr checks "$PR_NUMBER" --required --watch --interval 30 > "/tmp/watch-ci-$PR_NUMBER.log" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ] && [ "$NOTIFY_ON_SUCCESS" = "true" ]; then
    # All checks passed
    osascript -e "display notification \"All checks passed!\" with title \"PR #$PR_NUMBER\""
    echo "✅ All required checks passed for PR #$PR_NUMBER"
elif [ $EXIT_CODE -ne 0 ] && [ "$NOTIFY_ON_FAILURE" = "true" ]; then
    # Checks failed
    osascript -e "display notification \"Some checks failed\" with title \"PR #$PR_NUMBER\""
    echo "❌ Some checks failed for PR #$PR_NUMBER"
    gh pr checks "$PR_NUMBER" --required
fi

# Cleanup
rm -f "/tmp/watch-ci-$PR_NUMBER.pid"
```

### Integration with User's Existing Workflow

If user mentions having a custom notification script, offer to:
1. Use their existing script
2. Enhance it with agent capabilities
3. Integrate it into the monitoring workflow

## Advanced Features

### Multi-PR Monitoring

When monitoring multiple PRs:
```bash
# Track multiple PRs
for pr in 123 456 789; do
    gh pr checks $pr --required --watch &
    echo $! > /tmp/watch-ci-$pr.pid
done

# Check all background monitors
for pidfile in /tmp/watch-ci-*.pid; do
    pr=$(basename "$pidfile" | sed 's/watch-ci-\(.*\)\.pid/\1/')
    if kill -0 $(cat "$pidfile") 2>/dev/null; then
        echo "PR #$pr: still monitoring"
    else
        echo "PR #$pr: monitoring completed"
    fi
done
```

### Auto-Actions on Success

When user requests auto-merge or other actions:

```bash
# Watch and auto-merge
gh pr checks PR_NUMBER --required --watch && \
  gh pr merge PR_NUMBER --auto --squash
```

### Filtering Specific Checks

Monitor only certain checks:
```bash
# Get all check names
gh pr checks PR_NUMBER --json name -q '.[].name'

# Watch specific workflow
gh run list --workflow=ci.yml --branch=BRANCH --limit=1 --json status,conclusion
```

## Output Format

### Progress Notification
```
🔍 Monitoring PR #123: feat: add new feature
📊 Required checks: 4 pending, 0 failed
⏱️  Polling every 30 seconds...
```

### Success Notification
```
✅ All checks passed for PR #123!

Status:
✓ build (2m 34s)
✓ test (5m 12s)  
✓ lint (45s)
✓ security (1m 03s)

Next steps:
• Ready to merge (all requirements met)
• Run: gh pr merge 123 --squash
```

### Failure Notification
```
❌ Checks failed for PR #123

Failed checks:
✗ test - https://github.com/owner/repo/actions/runs/12345
  Exit code: 1
  Duration: 3m 22s

✓ build (passed)
✓ lint (passed)

Next steps:
• View logs: gh run view 12345 --log-failed
• Re-run: gh run rerun 12345
• Want me to analyze the failure?
```

## Error Handling

### PR Not Found
```bash
if ! gh pr view PR_NUMBER &>/dev/null; then
    echo "❌ PR #$PR_NUMBER not found"
    echo "Available PRs:"
    gh pr list --limit 10
    exit 1
fi
```

### No Checks Configured
```bash
checks=$(gh pr checks PR_NUMBER --json name -q 'length')
if [ "$checks" -eq 0 ]; then
    echo "⚠️  No status checks configured for this PR"
    echo "Monitoring commit status instead..."
fi
```

### Authentication Issues
```bash
if ! gh auth status &>/dev/null; then
    echo "❌ Not authenticated with GitHub"
    echo "Run: gh auth login"
    exit 1
fi
```

## Integration Points

### With User Scripts
- Detect and offer to use existing notification scripts
- Wrap them with agent intelligence (retry logic, better notifications)

### With GitHub CLI Extensions
- Compatible with `gh-dash`, `gh-pr-view` and other extensions
- Can trigger other gh commands on status changes

### With System Notifications
- macOS: `osascript -e 'display notification'`
- Linux: `notify-send`
- Windows: PowerShell `New-BurntToastNotification`

## Boundaries

**Will:**
- Monitor GitHub Actions workflows and status checks
- Run as background task by default
- Provide notifications on status changes
- Suggest next actions based on results
- Handle multiple PRs simultaneously

**Will Not:**
- Monitor non-GitHub CI systems without explicit integration
- Modify PR or trigger actions without user confirmation (unless explicitly requested)
- Continue monitoring indefinitely (default timeout: 2 hours)

## Configuration Options

User can specify preferences:
- `--interval`: Polling interval (default: 30s)
- `--timeout`: Maximum monitoring time (default: 2h)
- `--required-only`: Only watch required checks (default: true)
- `--notify`: Notification preference (success, failure, both, none)
- `--auto-action`: Action to take on success (merge, nothing)

## Examples

### Example 1: Basic Usage
```
User: "watch CI and let me know when it's green"

Agent: I'll monitor CI for PR #456 in the background.
       Running: gh pr checks 456 --required --watch &
       
       I'll notify you when:
       ✓ All required checks pass
       ✗ Any check fails
```

### Example 2: Specific PR
```
User: "monitor checks for PR #789"

Agent: Monitoring PR #789: fix: resolve login issue
       
       Current status:
       ○ build (pending)
       ○ test (pending)
       ✓ lint (passed)
       
       I'll keep watching and update you when complete.
```

### Example 3: Auto-merge
```
User: "watch CI and auto-merge when green"

Agent: Setting up CI monitoring with auto-merge for PR #123.
       
       Plan:
       1. Monitor all required checks
       2. When all pass → auto-merge with squash
       
       Running in background... I'll notify you when merged.
```

### Example 4: Multiple PRs
```
User: "watch CI for PRs #100, #101, and #102"

Agent: Monitoring 3 PRs in parallel:
       
       • PR #100: 2 pending checks
       • PR #101: all green ✓
       • PR #102: 1 failing check ✗
       
       I'll notify you as each one completes.
```

## Quick Reference

**Common Commands:**
```bash
# Watch current PR
gh pr checks --required --watch

# Watch specific PR
gh pr checks 123 --required --watch

# Fail fast on first error
gh pr checks 123 --fail-fast --watch

# Get PR number for current branch
gh pr view --json number -q .number

# View logs for failed run
gh run view RUN_ID --log-failed

# Re-run failed jobs
gh run rerun RUN_ID --failed
```

**Notification Examples:**
```bash
# macOS
osascript -e 'display notification "All checks passed!" with title "PR #123"'

# Linux  
notify-send "PR #123" "All checks passed!"

# Cross-platform with echo + bell
echo -e "\a✅ All checks passed for PR #123"
```
