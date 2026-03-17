# thehub Repository Structure and Conventions

Comprehensive reference for the github/thehub repository structure, documentation conventions, and metadata.

## Repository Overview

**Repository:** github/thehub  
**Purpose:** GitHub's internal knowledge base and documentation hub  
**Size:** 5,000+ documentation files  
**Access:** Internal (GitHub employees only)  
**URL:** https://thehub.github.com

## Directory Structure

### Top-Level Organization

```
github/thehub
├── docs/                  Primary documentation directory
│   ├── epd/              Engineering & Product Development
│   ├── security/         Security & Compliance
│   ├── guides/           General guides
│   ├── teams/            Team-specific docs
│   ├── products/         Product documentation
│   ├── news/             Announcements & updates
│   └── [other areas]/    Additional doc categories
│
├── _layouts/             Jekyll layout templates
├── _includes/            Reusable Jekyll components
├── assets/               Images, CSS, JavaScript
├── _config.yml           Jekyll site configuration
└── README.md             Repository documentation
```

## Documentation Areas

### docs/epd/ - Engineering & Product Development

**Purpose:** Engineering practices, product development processes, and technical standards.

```
docs/epd/
├── engineering/          Engineering practices and standards
│   ├── deployment/      Deployment guides and procedures
│   ├── testing/         Testing practices and standards
│   ├── monitoring/      Observability and monitoring
│   ├── architecture/    Architecture guidelines
│   └── tools/           Engineering tools and setups
│
├── product/             Product development and management
│   ├── design/          Design systems and guidelines
│   ├── pm-guides/       Product management guides
│   ├── research/        User research and insights
│   └── processes/       Product development processes
│
└── data/                Data engineering and analytics
    ├── pipelines/       Data pipeline documentation
    ├── privacy/         Data privacy guidelines
    ├── analytics/       Analytics practices
    └── governance/      Data governance policies
```

**Common Topics:**
- Service tier definitions and SLAs
- Deployment procedures and best practices
- Code review guidelines
- Testing strategies and standards
- Monitoring and alerting setup
- Incident management procedures
- API design standards
- Database patterns and migrations
- Performance requirements
- Security checklists

### docs/security/ - Security & Compliance

**Purpose:** Security policies, compliance standards, and operational security.

```
docs/security/
├── policies/            Security policies
│   ├── access-control   Access and authorization policies
│   ├── data-handling    Data classification and handling
│   ├── compliance       Compliance requirements (SOC2, etc.)
│   └── governance       Security governance framework
│
├── operations/          Security operations
│   ├── incident/        Incident response procedures
│   ├── monitoring/      Security monitoring and SIEM
│   ├── vulnerability/   Vulnerability management
│   └── forensics/       Digital forensics procedures
│
└── standards/           Security standards
    ├── authentication   Authentication standards
    ├── encryption       Encryption requirements
    ├── network          Network security standards
    └── application      Application security standards
```

**Common Topics:**
- Access control policies
- Incident response procedures
- Security operations runbooks
- Compliance standards (SOC2, ISO, GDPR)
- Vulnerability management
- Security training requirements
- Data classification and handling
- Audit and logging requirements
- Security review processes
- Emergency procedures

### docs/guides/ - General Guides

**Purpose:** How-to guides, tool documentation, and general workflows.

```
docs/guides/
├── onboarding/          New Hubber onboarding
│   ├── week-1           First week guides
│   ├── tools-setup      Tool setup instructions
│   ├── team-intros      Team introductions
│   └── resources        Resources for new hires
│
├── tools/               Tool guides and tutorials
│   ├── slack            Slack usage and best practices
│   ├── github           GitHub features and workflows
│   ├── vpn              VPN and network access
│   ├── zoom             Video conferencing
│   └── productivity     Productivity tool guides
│
└── workflows/           Common workflows
    ├── expense          Expense reporting
    ├── pto              PTO and time off
    ├── travel           Travel booking and policies
    └── collaboration    Collaboration best practices
```

**Common Topics:**
- New hire onboarding checklists
- Tool setup and configuration
- Workflow guides and processes
- Best practices for collaboration
- Company policies and procedures
- Resource directories
- FAQ documents
- Quick reference guides

### docs/teams/ - Team Documentation

**Purpose:** Team-specific processes, runbooks, and documentation.

```
docs/teams/
├── platform/            Platform engineering teams
├── product/             Product teams
├── support/             Support and operations
├── security/            Security team docs
├── data/                Data teams
└── [team-name]/         Other teams

Each team directory typically contains:
├── README.md            Team overview
├── processes/           Team processes
├── runbooks/            Operational runbooks
├── architecture/        Architecture docs
└── onboarding/          Team onboarding
```

**Common Topics:**
- Team mission and responsibilities
- On-call procedures and runbooks
- Service ownership
- Escalation procedures
- Team processes and rituals
- Architecture documentation
- Troubleshooting guides
- Metrics and dashboards

### docs/products/ - Product Documentation

**Purpose:** Product and service documentation, specifications, and architecture.

```
docs/products/
├── actions/             GitHub Actions
├── copilot/             GitHub Copilot
├── packages/            GitHub Packages
├── codespaces/          GitHub Codespaces
├── security/            GitHub Security (GHAS)
└── [product-name]/      Other products

Each product directory typically contains:
├── architecture/        Product architecture
├── operations/          Operations and runbooks
├── api/                 API documentation
├── deployment/          Deployment procedures
└── troubleshooting/     Troubleshooting guides
```

**Common Topics:**
- Product architecture and design
- API specifications
- Operational runbooks
- Deployment procedures
- Feature documentation
- Troubleshooting guides
- Performance characteristics
- Monitoring and metrics

### docs/news/ - News and Announcements

**Purpose:** Company news, announcements, and updates.

```
docs/news/
├── all-hands/           All-hands meeting notes
├── updates/             Company updates
├── launches/            Product launches
├── org-changes/         Organizational changes
└── quarterly/           Quarterly updates
```

## Jekyll Conventions

### Frontmatter Format

Every documentation file includes YAML frontmatter:

```yaml
---
layout: page           # Jekyll layout template
title: Document Title  # Page title (displayed)
owner_team: team-name  # Team responsible for doc
owner_slack: #channel  # Slack channel for questions
tags:                  # Optional tags
  - deployment
  - security
last_updated: 2024-02-01  # Optional last update date
---
```

### Required Fields

- `layout` - Jekyll layout (usually "page" or "default")
- `title` - Human-readable document title
- `owner_team` - Team responsible for maintaining the doc
- `owner_slack` - Slack channel for questions and feedback

### Optional Fields

- `tags` - Array of topic tags for categorization
- `last_updated` - Date of last significant update
- `author` - Document author(s)
- `reviewers` - Document reviewers
- `related` - Links to related documentation
- `status` - Draft, published, deprecated
- `version` - Document version number

### Example Frontmatter

```yaml
---
layout: page
title: Production Deployment Guide
owner_team: engineering-productivity
owner_slack: #eng-prod
tags:
  - deployment
  - production
  - ci-cd
last_updated: 2024-02-01
author: platform-team
related:
  - /docs/epd/engineering/service-tiers.md
  - /docs/security/deployment-security.md
---
```

## URL Mapping

thehub.github.com URLs map directly to the docs/ directory:

```
File path:              docs/epd/engineering/deployment.md
thehub.github.com URL:  https://thehub.github.com/docs/epd/engineering/deployment

File path:              docs/security/incident-response.md
thehub.github.com URL:  https://thehub.github.com/docs/security/incident-response
```

**Note:** The `.md` extension is typically omitted in URLs (handled by Jekyll).

## File Naming Conventions

### Markdown Files

- Use lowercase with hyphens: `deployment-guide.md`
- Be descriptive: `production-access-policy.md` not `access.md`
- Avoid spaces and special characters
- Use `.md` extension

### Directory Names

- Use lowercase with hyphens
- Be concise but clear
- Group related docs together
- Plural for collections: `guides/`, `policies/`, `runbooks/`

### Common Patterns

```
[topic]-guide.md          # How-to guides
[topic]-policy.md         # Policy documents
[topic]-standard.md       # Standards and requirements
[topic]-runbook.md        # Operational runbooks
[topic]-reference.md      # Reference documentation
[topic]-faq.md           # Frequently asked questions
```

## Content Structure

### Typical Document Structure

```markdown
---
[frontmatter]
---

# Document Title

Brief one-sentence description.

## Overview

High-level introduction to the topic.

## Prerequisites

Required knowledge, access, or setup.

## [Main Content Sections]

Detailed content organized by topic.

## Examples

Concrete examples and use cases.

## Troubleshooting

Common issues and solutions.

## Related Documentation

Links to related docs.

## Questions?

Contact information and support channels.
```

### Section Ordering Guidelines

1. **Title and description** - Clear, concise introduction
2. **Overview** - Context and purpose
3. **Prerequisites** - What you need before starting
4. **Main content** - Core information organized logically
5. **Examples** - Practical examples and use cases
6. **Troubleshooting** - Common problems and solutions
7. **Related docs** - Links to additional resources
8. **Support** - Where to get help

## Search and Discovery

### Finding Documents

Always prefer a local clone of `github/thehub` when available. Fall back to the GitHub API if no clone is found. `THEHUB_ROOT` is set during the skill's local-clone detection step (see "Local vs API Access" in SKILL.md).

**Local clone (preferred):**
```bash
# By path
find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "TERM"

# By content
grep -ri "TERM" "$THEHUB_ROOT/docs" --include='*.md' -l

# By directory
find "$THEHUB_ROOT/docs/security" -name '*.md'
```

**API fallback:**
```bash
# By path
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/' | grep -i "TERM"

# By content
gh search code "TERM" --repo github/thehub --filename "*.md"

# By directory
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/security/'
```

### Common Search Terms

| Need | Search Term | Directory |
|------|-------------|-----------|
| Deployment | deploy, release, rollout | docs/epd/engineering/ |
| Security | policy, compliance, incident | docs/security/ |
| Tools | setup, configure, install | docs/guides/tools/ |
| Team info | team, on-call, runbook | docs/teams/ |
| Product docs | architecture, api, operations | docs/products/ |
| Onboarding | onboard, new hire, setup | docs/guides/onboarding/ |

## Best Practices

### For Document Authors

- Always include complete frontmatter
- Keep docs up to date
- Link to related documentation
- Include concrete examples
- Provide contact information
- Use clear, descriptive titles
- Follow consistent formatting
- Tag documents appropriately

### For Document Consumers

- Check frontmatter for owner and contact
- Verify last_updated date for currency
- Follow related documentation links
- Contact owner_slack with questions
- Report outdated or incorrect information
- Bookmark frequently used docs

### For Searchers

- Start with category-specific searches
- Use multiple search strategies
- Check multiple related docs
- Verify doc currency and ownership
- Follow up with owner teams for clarification

## Metadata Fields Reference

| Field | Purpose | Required | Example |
|-------|---------|----------|---------|
| `layout` | Jekyll template | Yes | `page`, `default` |
| `title` | Document title | Yes | `Production Deployment Guide` |
| `owner_team` | Responsible team | Yes | `engineering-productivity` |
| `owner_slack` | Contact channel | Yes | `#eng-prod` |
| `tags` | Topic tags | No | `[deployment, ci-cd]` |
| `last_updated` | Update date | No | `2024-02-01` |
| `author` | Document author | No | `platform-team` |
| `status` | Document status | No | `published`, `draft` |
| `version` | Version number | No | `1.2.0` |
| `related` | Related docs | No | List of paths |

## Commands Reference

All commands below show local clone (preferred) and GitHub API (fallback) alternatives.

### List All Docs

**Local:**
```bash
find "$THEHUB_ROOT/docs" -name '*.md'
```

**API fallback:**
```bash
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[] | select(.path | startswith("docs/") and endswith(".md")) | .path'
```

### Count Docs by Directory

**Local:**
```bash
cd "$THEHUB_ROOT" && find docs -name '*.md' | cut -d/ -f1-4 | sort | uniq -c
```

**API fallback:**
```bash
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[] | select(.path | startswith("docs/") and endswith(".md")) | .path' \
  | cut -d/ -f1-2 | sort | uniq -c
```

### Retrieve Document

**Local:**
```bash
cat "$THEHUB_ROOT/docs/path/to/doc.md"
```

**API fallback:**
```bash
gh api "repos/github/thehub/contents/docs/path/to/doc.md" \
  --jq '.content' | base64 -d
```

### Search Documents

**Local:**
```bash
grep -ri "search term" "$THEHUB_ROOT/docs" --include='*.md' -l
```

**API fallback:**
```bash
gh search code "search term" \
  --repo github/thehub \
  --filename "*.md" \
  --path "docs/" \
  --limit 20
```

### Get Document Metadata

**Local:**
```bash
cat "$THEHUB_ROOT/docs/path/to/doc.md" | awk '/^---$/,/^---$/'
```

**API fallback:**
```bash
gh api "repos/github/thehub/contents/docs/path/to/doc.md" \
  --jq '{name: .name, path: .path, size: .size, sha: .sha}'
```

## Additional Resources

- **thehub.github.com** - Browse documentation
- **#thehub-help** - Help with thehub
- **#docs** - Documentation discussions
- **github/thehub** - Repository (for those with access)

---

Last updated: 2024-02-09
