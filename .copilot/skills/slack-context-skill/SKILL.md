---
name: slack-context
description: This skill should be used when the user asks to "fetch context from Slack", "read this Slack thread", "get requirements from Slack", "extract Slack conversation", "use this Slack discussion", "pull context from chat", or provides a Slack permalink and wants to use that conversation as context for a task.
---

# Slack Context - Extract Context from Slack Conversations

Retrieves Slack thread content using `gh slack read` to inform agent tasks and decisions.

## When to Use This Skill

**Trigger phrases:**
- "Fetch context from this Slack thread: [url]"
- "Read this Slack conversation and implement what we discussed"
- "Get the requirements from this Slack chat"
- "Use this Slack thread as context"
- "Extract details from this Slack discussion"

**Appropriate use cases:**
- Technical implementation discussions (architecture, APIs)
- Feature requests documented in team channels
- Bug reports with reproduction steps
- Open design discussions
- Code review feedback consolidated in chat

## Process

### Step 1: Identify Slack URL

Extract the Slack permalink from user input:

**Formats:**
- `https://[workspace].slack.com/archives/[CHANNEL]/p[TIMESTAMP]`
- `https://github.slack.com/archives/C098RMYF7TR/p1770412315291609`

**Validate:**
- URL contains `/archives/`
- Has channel ID (C[A-Z0-9]+) or DM ID (D[A-Z0-9]+)
- Has message timestamp (p[0-9]+)

### Step 2: Fetch Thread Content

Use `gh slack read` command:

```bash
gh slack read <slack-permalink>
```

**Expected output format:**
```
> **username** at 2026-02-06 15:11 CST
>
> Message content here
>

> **another-user** at 2026-02-06 15:23 CST
>
> Reply content here
```

### Step 3: Parse and Summarize

Extract key information:

**Parse structure:**
- Author names
- Timestamps
- Message content
- Thread structure (replies)

**Summarize:**
```
📊 Conversation Summary:
• Participants: user1, user2, user3
• Messages: 5
• Duration: 2 hours
• Topic: Feature implementation discussion

Key Points:
1. Decided to use OAuth for authentication
2. API rate limit: 100 req/min
3. Return 429 status with Retry-After header
4. Timeline: Complete by end of week
```

### Step 6: Use Context Appropriately

**Good practices:**
- Focus on technical details
- Extract requirements, not opinions about people
- Summarize decisions, not conversations
- Reference Slack for source, don't copy verbatim

## Error Handling

### Extension Not Installed

```bash
if ! gh extension list | grep -q "slack"; then
    echo "❌ gh-slack extension not installed"
    echo ""
    echo "Install with:"
    echo "  gh extension install rneatherway/gh-slack"
    echo ""
    echo "Then authenticate:"
    echo "  eval \$(gh slack auth -t github)"
    exit 1
fi
```

### Authentication Failed

```bash
if ! gh slack read "$URL" 2>&1 | grep -v "Error"; then
    echo "❌ Failed to fetch Slack thread"
    echo ""
    echo "Possible causes:"
    echo "  • Not authenticated (run: gh slack auth -t github)"
    echo "  • No access to this channel"
    echo "  • Invalid URL format"
    echo "  • Thread was deleted"
    exit 1
fi
```

### Invalid URL Format

```bash
if ! echo "$URL" | grep -q "slack.com/archives/C[A-Z0-9]*/p[0-9]*"; then
    echo "❌ Invalid Slack URL format"
    echo ""
    echo "Expected format:"
    echo "  https://workspace.slack.com/archives/C123ABC/p1234567890123456"
    exit 1
fi
```

## Output Formats

### Minimal Summary
When context is simple, provide brief summary:
```
📋 Slack Context (5 messages):
Main points:
• Use Redis for caching
• 5-minute TTL
• Handle cache misses gracefully

Ready to implement Redis caching?
```

### Detailed Context
When context is complex, provide structured breakdown:
```
📋 Slack Thread Context

Thread: https://github.slack.com/archives/C098/p177041
Channel: #engineering
Participants: 4 people
Duration: 3 hours

Discussion Topic: API Rate Limiting Strategy

Requirements Identified:
1. Token bucket algorithm
   - Mentioned by: user1
   - Rationale: Handles bursts better than fixed window
   
2. 100 requests per minute per user
   - Mentioned by: user2
   - Based on: Current 99th percentile usage

3. Response format for rate limit exceeded
   - Status: 429 Too Many Requests
   - Headers: Retry-After, X-RateLimit-*
   
4. Exemptions for internal services
   - Separate limit: 1000 req/min
   - Auth: Service tokens

Implementation Notes:
• Store counters in Redis
• Use sliding window for accuracy
• Monitor and alert on high usage

Next Steps Agreed:
1. Create design doc (assigned: user3)
2. Implement rate limiter middleware
3. Add metrics/dashboards
4. Roll out to staging first

Should I proceed with implementation?
```

## Integration with Tasks

### Code Implementation
```
User: "Read this Slack thread and implement the API we discussed"

Agent: [Fetches, shows warning, gets consent]

I see you discussed a user profile API with these endpoints:
• GET /api/v1/users/:id
• PATCH /api/v1/users/:id  
• DELETE /api/v1/users/:id

Should I create these endpoints following the patterns discussed?
```

### Bug Fix
```
User: "Fetch this bug report from Slack and fix it"

Agent: [Fetches thread with bug details]

Bug Summary:
• Issue: Login fails for users with special characters in email
• Reproduction: Email with + sign (user+test@example.com)
• Root cause: Email validation regex too restrictive
• Fix needed: Update regex to allow RFC 5322 valid emails

Should I update the validation logic?
```

### Documentation
```
User: "Create docs based on this Slack architecture discussion"

Agent: [Fetches, reviews, confirms]

Based on the discussion, I'll document:
• System architecture diagram
• Service responsibilities
• Communication patterns
• Deployment topology

Create docs in /docs/architecture/?
```

## Boundaries

**Will:**
- Fetch Slack threads via gh-slack extension
- Summarize technical discussions
- Extract requirements and decisions
- Help implement based on context

**Will Not:**
- Store or cache Slack content permanently
- Share Slack content with other services
- Fetch from URLs that aren't Slack permalinks

## Configuration

### Prerequisites Check

Before running, verify:

```bash
# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not installed"
    echo "Install: https://cli.github.com/"
    exit 1
fi

# Check gh-slack extension
if ! gh extension list | grep -q rneatherway/gh-slack; then
    echo "❌ gh-slack extension not installed"
    echo "Install: gh extension install rneatherway/gh-slack"
    exit 1
fi

# Check authentication
if ! gh slack auth status &> /dev/null; then
    echo "⚠️  Not authenticated with Slack"
    echo "Run: eval \$(gh slack auth -t github)"
fi
```

### Environment Variables

Optionally set:
- `GH_SLACK_TEAM`: Default Slack team name

## Quick Reference

**Command pattern:**
```bash
gh slack read <slack-url>
```

**URL format:**
```
https://[workspace].slack.com/archives/[CHANNEL_ID]/p[TIMESTAMP]
```
