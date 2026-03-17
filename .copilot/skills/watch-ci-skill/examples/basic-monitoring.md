# Example: Basic PR Monitoring

Monitor a PR until all required checks pass.

## Scenario

You've just pushed code to a PR and want to continue working while CI runs. You want to be notified when checks complete.

## User Request

> "Watch CI on PR #456 and let me know when it's done"

## Agent Response

```
🔍 Monitoring PR #456: feat: add user authentication

Current status:
○ build (pending)
○ test (pending)
○ lint (pending)
✓ security-scan (passed)

Running in background... I'll notify you when all checks complete.

Command: gh pr checks 456 --required --watch &
PID: 12345
```

## Success Notification (after ~5 minutes)

```
✅ All checks passed for PR #456!

Final status:
✓ build (2m 14s)
✓ test (4m 32s)
✓ lint (38s)
✓ security-scan (54s)

Next steps:
• Ready to merge (all requirements met)
• Run: gh pr merge 456 --squash
```
