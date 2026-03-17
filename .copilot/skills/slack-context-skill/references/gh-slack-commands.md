# gh-slack Command Reference

Quick reference for the gh-slack extension commands.

## Installation

```bash
gh extension install rneatherway/gh-slack
```

**Repository:** https://github.com/rneatherway/gh-slack

## Authentication

```bash
# Authenticate with Slack (GitHub team)
eval $(gh slack auth -t github)

# Check auth status
gh slack auth status
```

## Reading Messages

### Basic Read

```bash
# Read a single message
gh slack read <slack-permalink>

# Read with details
gh slack read --details <slack-permalink>
```

### Permalink Format

Slack permalinks have this format:
```
https://[workspace].slack.com/archives/[CHANNEL_ID]/p[TIMESTAMP]
```

Example:
```
https://github.slack.com/archives/C098RMYF7TR/p1770412315291609
```

Where:
- `C098RMYF7TR` is the channel ID
- `p1770412315291609` is the message timestamp (with `p` prefix)

## Sending Messages

```bash
# Send to a channel
gh slack send -m "message" -c channel-name -t team-name

# Using configured defaults
gh slack send -m "message"
```

## API Access

For advanced usage:

```bash
# Post a message via API
gh slack api post chat.postMessage -b '{"channel":"C123","text":"Hello"}'
```

## Configuration

Add to `~/.config/gh/config.yml`:

```yaml
extensions:
  slack:
    team: github
    channel: ops
    bot: robot
```

## Output Format

### Standard message format:
```
> **username** at 2026-02-06 15:11 CST
>
> Message content here
>
```

### Thread replies:
All messages in a thread are returned in chronological order with the same format.

## Common Issues

### "expected slack.com subdomain"
- You need to use the full Slack permalink, not a shortened URL
- Format must be: `https://[workspace].slack.com/archives/...`

### Authentication errors
- Run: `eval $(gh slack auth -t github)`
- Ensure you have access to the Slack workspace

### No access to channel
- The bot/user must be a member of private channels
- Public channels should work if you have workspace access

## Security Notes

- Credentials are stored securely by gh CLI
- API tokens are temporary and workspace-specific
- Always review fetched content before sharing with AI
- Don't commit auth tokens to version control

## Further Reading

- [gh-slack GitHub Repository](https://github.com/rneatherway/gh-slack)
- [GitHub CLI Extensions Docs](https://docs.github.com/en/github-cli/github-cli/using-github-cli-extensions)
- [Slack API Documentation](https://api.slack.com/)
