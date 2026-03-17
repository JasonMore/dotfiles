# Docs Search Skill

Search and retrieve documentation from GitHub's internal knowledge base (github/thehub).

## When to Use This Skill

- Need to find engineering practices or development guides
- Looking up security policies and compliance standards
- Searching for deployment or operational procedures
- Finding team guides and onboarding materials
- Discovering service documentation
- Looking up incident response procedures
- Finding company announcements and news

## Prerequisites

### Required

- **GitHub CLI (`gh`)** - Install from https://cli.github.com (only required for API fallback; local clone mode works offline)
- **GitHub authentication** - Must be authenticated as a Hubber with access to github/thehub (only required when no local clone is available)
- **Local clone or repository access** - Either a local clone of github/thehub (preferred) or API access to the repository

### Verify Setup

```bash
# Check gh is installed (needed for API fallback)
gh --version

# Verify authentication (only needed if no local clone)
gh auth status

# Test access to thehub (only needed if no local clone)
gh api repos/github/thehub
```

## Installation

### Using gh-skills (Recommended)

```bash
gh extension install github/gh-skills
gh skills install thehub-docs-search
```

### Manual Installation

**Personal skills** (available across all your projects):
```bash
cp -r thehub-docs-search-skill ~/.copilot/skills/
```

**Project-specific skills**:
```bash
cp -r thehub-docs-search-skill /path/to/your/repo/.github/skills/
```

## Usage

This skill activates when you ask Copilot to:
- "Search thehub for [topic]"
- "Find docs on [topic]"
- "What's the policy on [topic]?"
- "How do I [action]?" (for GitHub-internal processes)
- "Find the engineering guide for [topic]"
- "Look up the deployment docs"
- "Search internal docs about [topic]"

The skill will:
1. Check if github/thehub is cloned locally (preferred for speed and offline use)
2. Fall back to the GitHub API if no local clone is found
3. Search using efficient path and content strategies
4. Identify the most relevant documentation
5. Retrieve and present key information
6. Provide links to the full docs on thehub.github.com
7. Suggest related docs and next steps

## Features

- **Local-first access** - Prefers reading from a local clone of github/thehub for speed and offline use; falls back to GitHub API automatically
- **Multi-strategy search** - Combines path search and content search for comprehensive results
- **Smart navigation** - Understands thehub directory structure (engineering, security, guides)
- **Metadata extraction** - Parses Jekyll frontmatter (title, owner_team, owner_slack)
- **Formatted output** - Presents docs with clear attribution and summaries
- **Direct links** - Always provides thehub.github.com URLs
- **Error handling** - Graceful handling of missing docs and access issues

## thehub Directory Structure

The skill understands these key areas:

| Directory | Content |
|-----------|---------|
| `docs/epd/engineering/` | Engineering practices, deployment guides, services |
| `docs/security/` | Security policies, compliance, standards |
| `docs/guides/` | General guides (onboarding, tools, workflows) |
| `docs/news/` | Company news and announcements |
| `docs/teams/` | Team-specific documentation |
| `docs/products/` | Product documentation |

## Examples

### Search for deployment docs

```bash
# User: "Search thehub for deployment guides"
# Agent searches paths and content, returns:
#
# 📄 Production Deployment Guide
# 🔗 https://thehub.github.com/docs/epd/engineering/deployment-guide
# Owner: engineering-productivity (#eng-prod)
#
# Key sections:
# • Pre-deployment checklist
# • Deployment procedures
# • Rollback process
```

### Find security policy

```bash
# User: "What's the policy on production access?"
# Agent searches security docs, returns:
#
# 📄 Production Access Control Policy
# 🔗 https://thehub.github.com/docs/security/access-control
# Owner: security-team (#security)
#
# Summary:
# Production access requires manager approval and security training...
```

### Look up service documentation

```bash
# User: "Find docs on service tiers"
# Agent searches and returns multiple relevant docs:
#
# Found 3 relevant documents:
# 
# 1. 📄 Service Tier Definitions
#    🔗 https://thehub.github.com/docs/epd/engineering/service-tiers
#
# 2. 📄 Service Tier SLAs
#    🔗 https://thehub.github.com/docs/products/sla-standards
```

### Browse by category

```bash
# User: "Show me guides on incident response"
# Agent searches specific directory:
#
# 📄 Incident Response Guide
# 🔗 https://thehub.github.com/docs/security/incident-response
# Owner: security-operations (#security-ops)
```

## Common Use Cases

### For Engineers
- Deployment procedures and best practices
- Service documentation and runbooks
- Engineering standards and conventions
- Tool guides and tutorials

### For Security
- Security policies and compliance requirements
- Incident response procedures
- Access control policies
- Security operations guides

### For New Hubbers
- Onboarding guides
- Team documentation
- Process guides
- Company policies

### For Managers
- Team processes
- Organizational docs
- Policy references
- Announcement archives

## Tips

- **Be specific** - More specific search terms yield better results
- **Try directory hints** - Mention "security", "engineering", or "guides" to help narrow search
- **Check related docs** - The skill will suggest related documentation
- **Use links** - Always review the full doc on thehub.github.com for complete context
- **Ask for summaries** - Request "summarize the key points" for long docs
- **Contact owners** - Use the owner_slack channel from doc metadata for questions

## Local Clone (Recommended)

For faster searches and offline access, clone github/thehub locally. The skill will automatically discover the clone at runtime — no hardcoded paths needed.

**Discovery order:**
1. `THEHUB_LOCAL_PATH` environment variable (if set)
2. Sibling directories of the current repo (e.g. `../thehub`)
3. Common code directories via `find` or `locate`
4. Falls back to GitHub API if no local clone is found

**Optional:** Set the `THEHUB_LOCAL_PATH` environment variable to point to your clone:

```bash
export THEHUB_LOCAL_PATH="$HOME/code/github/thehub"
```

## Limitations

- **Read-only** - Cannot create or modify thehub docs (by design)
- **Access required** - Must have Hubber access to github/thehub (for API fallback)
- **Rate limits** - Subject to GitHub API rate limits when using API fallback (local clone avoids this)
- **Search scope** - Only searches github/thehub repository
- **Content in context** - Presents summaries; full docs should be reviewed on thehub.github.com

## Troubleshooting

### "Cannot access github/thehub"

You may not have the required permissions. This requires:
- Being a GitHub employee (Hubber)
- Valid GitHub authentication
- Access to internal repositories

Contact #github-help for access issues.

### "No results found"

Try:
- Broader search terms
- Different keywords
- Browsing the directory structure
- Asking in #eng-help or relevant Slack channels

### Rate limit warnings

If you see rate limit warnings:
- Clone github/thehub locally to avoid API rate limits entirely
- Wait a few minutes before searching again
- Use more specific searches to reduce API calls
- The skill caches directory listings to help reduce calls

## Security Note

Some documentation in thehub contains sensitive information about internal processes, security policies, and operational procedures. The skill:
- Always presents doc content directly to you
- Provides source attribution and links
- Does not use doc content in background operations
- Respects document ownership and contact channels

When viewing sensitive docs, handle them according to GitHub's information security policies.

## Support

- **Skill issues**: Open an issue in github/agent-skills
- **thehub access**: Contact #github-help on Slack
- **Documentation questions**: Use the owner_slack channel from the doc metadata
- **General help**: Ask in #eng-help on Slack

---

**Required:** GitHub CLI with authenticated access to github/thehub
