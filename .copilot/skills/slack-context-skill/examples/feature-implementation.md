# Example: Extract Feature Requirements

Fetch a Slack discussion about a feature and use it to implement the feature.

## Scenario

Your team discussed implementing OAuth authentication in Slack. You want to use that conversation as context for implementation.

## User Request

> "Fetch context from this Slack thread and help me implement it: https://github.slack.com/archives/C123ABC/p1234567890"

## Agent Response - Step 1: Security Warning

```
⚠️  SECURITY WARNING

You're about to fetch Slack messages that may contain:
• Personal information (PII)
• Confidential business information
• Private conversations
• Credentials or secrets

Before proceeding:
✓ Do you have permission to share this conversation?
✓ Does it contain sensitive information?
✓ Is it appropriate for AI processing?

Continue? (y/n)
```

## User: "y"

## Agent Response - Step 2: Fetch and Display

```
Fetching Slack thread...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Fetched Slack Conversation:

> **alice** at 2026-02-06 10:15 CST
>
> We should add OAuth support for third-party integrations

> **bob** at 2026-02-06 10:18 CST
>
> Agreed. Let's use OAuth 2.0 with PKCE for security

> **alice** at 2026-02-06 10:20 CST
>
> Endpoints we'll need:
> - /oauth/authorize
> - /oauth/token
> - /oauth/revoke

> **charlie** at 2026-02-06 10:25 CST
>
> Don't forget refresh tokens. 7-day expiry for access tokens?

> **bob** at 2026-02-06 10:27 CST
>
> Perfect. And store tokens encrypted in the database

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  Review the above for sensitive information:
   • Names, emails, customer references
   • Credentials, tokens, API keys
   • Confidential product/business info

Ready to proceed with this context? (y/n)
```

## User: "y"

## Agent Response - Step 3: Summarize and Propose

```
✅ Context confirmed.

📊 Discussion Summary:
• Participants: alice, bob, charlie
• Topic: OAuth 2.0 implementation
• Duration: ~12 minutes

Requirements Extracted:

1. OAuth 2.0 with PKCE
   - Provides better security for public clients
   
2. Endpoints needed:
   • POST /oauth/authorize - Start auth flow
   • POST /oauth/token - Exchange code for token
   • POST /oauth/revoke - Revoke tokens

3. Token Configuration:
   • Access tokens: 7-day expiry
   • Refresh tokens: Supported
   • Storage: Encrypted in database

4. Security measures:
   • Use PKCE (Proof Key for Code Exchange)
   • Encrypt tokens at rest

Should I create these endpoints following OAuth 2.0 spec?
```

## User: "yes, start with the authorize endpoint"

## Agent Implements

```
Creating OAuth authorize endpoint...

File: src/api/oauth/authorize.ts

[Agent creates the endpoint with proper OAuth flow, PKCE support, etc.]

✓ Created authorize endpoint
✓ Added PKCE generation
✓ Added state parameter validation
✓ Integrated with auth service

Next: Should I create the token endpoint?
```

## Key Points

- Security warnings shown twice (before fetch, before use)
- Full content displayed for user review
- User explicitly confirms at each step
- Agent extracts technical requirements
- Implementation follows the discussed approach
