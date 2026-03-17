# GitHub CLI Check Commands Reference

Reference for `gh pr checks` and related commands used in CI monitoring.

## Core Commands

### gh pr checks

Monitor pull request status checks.

```bash
# View current status
gh pr checks [PR_NUMBER]

# Watch for changes
gh pr checks [PR_NUMBER] --watch

# Only required checks
gh pr checks [PR_NUMBER] --required

# Exit on first failure
gh pr checks [PR_NUMBER] --fail-fast

# Custom polling interval
gh pr checks [PR_NUMBER] --watch --interval 30
```

### gh run commands

Work with workflow runs.

```bash
# List recent runs
gh run list --limit 10

# View specific run
gh run view RUN_ID

# View failed logs
gh run view RUN_ID --log-failed

# Re-run failed jobs
gh run rerun RUN_ID --failed

# Watch a specific run
gh run watch RUN_ID
```

## Exit Codes

- `0` - All checks passed
- `1` - Some checks failed
- `2` - Error occurred (auth, network, etc.)

## JSON Output

For programmatic access:

```bash
# Get check status as JSON
gh pr checks PR_NUMBER --json name,status,conclusion,detailsUrl

# Parse with jq
gh pr checks PR_NUMBER --json name,status | jq '.[] | select(.status=="completed")'
```

## Notification Integration

### macOS
```bash
osascript -e 'display notification "Message" with title "Title"'
```

### Linux
```bash
notify-send "Title" "Message"
```

### Cross-platform (terminal bell)
```bash
echo -e "\a✅ Done"
```
