# Slack Context Skill

Extract context from Slack conversations to inform agent tasks and decisions.

## ⚠️ Security Warning

**READ THIS BEFORE USING:**

This skill accesses Slack messages which may contain:
- Personal information (PII)
- Confidential business information
- Private conversations
- Credentials or secrets
- Internal-only discussions

**Before using this skill:**
- ✅ Ensure you have permission to share the conversation
- ✅ Review the thread for sensitive information
- ✅ Redact any secrets, PII, or confidential data
- ✅ Consider if the context is appropriate for AI processing
- ❌ Never share customer data, passwords, or tokens
- ❌ Don't use for private/sensitive conversations

**Your responsibility:** You are accountable for what you share with AI agents. When in doubt, don't share.

## Prerequisites

### 1. Install gh slack extension

```bash
gh extension install rneatherway/gh-slack
```

### 2. Configure authentication

```bash
# Set up Slack authentication for your team
eval $(gh slack auth -t github)
```

### 3. Verify access

```bash
# Test reading a public message
gh slack read <slack-permalink>
```

## When to Use This Skill

**Good use cases:**
- Technical discussions about implementation approaches
- Public feature requests or bug reports
- Architecture decisions documented in Slack
- Team discussions about code structure
- Open-source project planning

**Bad use cases:**
- Private customer conversations
- HR or personnel discussions
- Security incident details
- Confidential product plans
- Anything with PII or credentials

## Installation

### Personal Skills
```bash
cp -r slack-context-skill ~/.copilot/skills/
```

### Project Skills
```bash
cp -r slack-context-skill /path/to/repo/.github/skills/
```

## Usage

This skill activates when you ask Copilot to:
- "Fetch context from this Slack thread: [link]"
- "Read this Slack conversation and help me implement what we discussed"
- "Get the requirements from this Slack thread"
- "Extract the technical details from this chat"

The skill will:
1. Fetch the Slack thread using `gh slack read`
2. Present the context for your review
3. Ask for confirmation before proceeding
4. Help you use the context for your task

## Features

- **Security-first** - Always prompts for confirmation before using Slack data
- **Thread extraction** - Pulls full conversation threads, not just single messages
- **Context formatting** - Structures Slack messages for agent consumption
- **Redaction prompts** - Reminds you to remove sensitive info

## Examples

### Extract feature requirements
```bash
# User: "Fetch the requirements from this Slack thread: https://github.slack.com/archives/C123/p456"
# Agent: I'll fetch that thread. Remember: Review for sensitive info before I use it.
#
# [Shows thread content]
#
# I found a discussion about adding OAuth support. Ready to proceed? (y/n)
```

### Implementation guidance
```bash
# User: "Read this conversation and help implement what we discussed"
# Agent: Fetched 5 messages discussing API rate limiting.
#        Key points:
#        - Use token bucket algorithm
#        - 100 requests per minute limit
#        - Return 429 with Retry-After header
#
# Should I proceed with implementation? (y/n)
```

## Best Practices

1. **Always review** the fetched content before confirming
2. **Redact sensitive info** like names, emails, customer references
3. **Use public channels** when possible
4. **Link to issues/PRs** instead when appropriate (they're safer)
5. **Delete context** after task completion if it's sensitive

---

**Required:** GitHub CLI with [`gh-slack`](https://github.com/rneatherway/gh-slack) extension installed and configured
