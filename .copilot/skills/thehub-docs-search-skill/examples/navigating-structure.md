# Example: Navigating Documentation Structure

Understanding and exploring the thehub directory structure to find the right documentation area.

## Scenario

You're new to GitHub and want to understand where different types of documentation are located and how to browse the thehub structure effectively.

## User Request

> "Help me understand the thehub documentation structure and where to find different types of docs"

## Agent Response - Step 1: Explain Structure

```
📚 Understanding thehub Structure

github/thehub is GitHub's internal knowledge base with 5,000+ documentation files.
Let me show you the main documentation areas and how to navigate them.
```

## Agent Response - Step 2: Fetch Top-Level Structure

**Local clone (preferred):**

> `THEHUB_ROOT` is set during the skill's local-clone detection step (see "Local vs API Access" in SKILL.md).

```bash
# Get top-level docs structure
find "$THEHUB_ROOT/docs" -maxdepth 2 -type d | sort
```

**API fallback:**

```bash
# Get top-level docs structure
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[] | select(.path | startswith("docs/")) | .path' \
  | cut -d/ -f1-2 | sort -u
```

```
📂 Main Documentation Areas:

docs/
├── epd/              Engineering & Product Development
│   ├── engineering/  Engineering practices, standards, deployment
│   ├── product/      Product development, design, PM guides
│   └── data/         Data engineering, analytics, privacy
│
├── security/         Security policies, compliance, operations
│   ├── policies/     Access control, data handling, compliance
│   ├── operations/   Incident response, security runbooks
│   └── standards/    Security standards and requirements
│
├── guides/           General guides and how-tos
│   ├── onboarding/   New Hubber onboarding materials
│   ├── tools/        Tool guides (Slack, Zoom, VPN, etc.)
│   └── workflows/    Common workflows and processes
│
├── teams/            Team-specific documentation
│   ├── platform/     Platform engineering teams
│   ├── product/      Product teams
│   └── support/      Support and operations teams
│
├── products/         Product and service documentation
│   ├── actions/      GitHub Actions
│   ├── copilot/      GitHub Copilot
│   ├── packages/     GitHub Packages
│   └── [more...]     Other GitHub products
│
└── news/             Company news and announcements
    ├── all-hands/    All-hands meeting notes
    ├── updates/      Company updates
    └── launches/     Product launches
```

## Agent Response - Step 3: Show How to Explore

```
🔍 Navigation Strategies:

1. **Browse by Category**
   Know what you need? Start with the right top-level directory.

2. **Search by Topic**
   Not sure where to look? Search across all docs.

3. **Follow References**
   Docs often link to related documentation.

4. **Check Frontmatter**
   Each doc has owner_team and owner_slack for questions.

Let me show you examples for each approach...
```

## Example 1: Browse by Category

### User Ask: "Show me what engineering docs are available"

**Local clone (preferred):**
```bash
# List engineering docs
find "$THEHUB_ROOT/docs/epd/engineering" -name '*.md' | head -20
```

**API fallback:**
```bash
# List engineering docs
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/epd/engineering/' | head -20
```

```
📂 docs/epd/engineering/

Common Topics:
• deployment-guide.md         - How to deploy to production
• service-tiers.md            - Service tier classifications
• monitoring-standards.md     - Observability and monitoring
• incident-management.md      - Handling production incidents
• testing-practices.md        - Testing standards and patterns
• code-review-guidelines.md   - Code review best practices
• architecture-reviews.md     - Architecture review process
• api-design-guide.md         - RESTful API design standards
• database-practices.md       - Database patterns and migrations
• performance-standards.md    - Performance requirements
• security-checklist.md       - Security review checklist
• on-call-guide.md           - On-call responsibilities

🔗 Browse all: find "$THEHUB_ROOT/docs/epd/engineering" -name '*.md'
   (or: gh api 'repos/github/thehub/git/trees/main?recursive=1' \
   --jq '.tree[].path' | grep '^docs/epd/engineering/')
```

## Example 2: Search Across Categories

### User Ask: "Where can I find information about deploying services?"

**Local clone (preferred):**
```bash
# Search all docs for deployment info
grep -ri "deploy" "$THEHUB_ROOT/docs" --include='*.md' -l
```

**API fallback:**
```bash
# Search all docs for deployment info
gh search code "deploy" \
  --repo github/thehub \
  --filename "*.md" \
  --limit 10
```

```
🔍 Deployment Documentation Found In:

docs/epd/engineering/
• deployment-guide.md         - General deployment practices
• continuous-deployment.md    - CD pipeline setup
• rollback-procedures.md      - How to rollback deployments

docs/products/actions/
• deploying-with-actions.md   - Using Actions for deployment
• deployment-workflows.md     - Workflow templates

docs/security/
• deployment-security.md      - Security requirements for deploys
• production-access.md        - Required access for deployments

docs/teams/platform/
• platform-deployment.md      - Platform-specific procedures
• kubernetes-deployments.md   - K8s deployment patterns

💡 Tip: Start with docs/epd/engineering/deployment-guide.md for general practices,
       then check product-specific docs for your service.
```

## Example 3: Explore by File Pattern

### User Ask: "Find all runbooks"

**Local clone (preferred):**
```bash
# Find all files with 'runbook' in name
find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "runbook"
```

**API fallback:**
```bash
# Find all files with 'runbook' in name
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep -i "runbook"
```

```
📖 Runbooks Found:

docs/epd/engineering/
• incident-runbook.md
• on-call-runbook.md
• deployment-runbook.md

docs/security/
• security-ops-runbook.md
• incident-response-runbook.md

docs/products/actions/
• actions-runbook.md
• runner-troubleshooting-runbook.md

docs/products/packages/
• packages-operations-runbook.md

💡 Runbooks are operational guides for handling specific scenarios.
   Each usually includes step-by-step procedures, escalation paths,
   and troubleshooting tips.
```

## Example 4: Find Documentation by Owner

### User Ask: "What docs does the platform team maintain?"

**Local clone (preferred):**
```bash
# Search for docs owned by platform team
grep -ri "owner_team: platform" "$THEHUB_ROOT/docs" --include='*.md' -l
```

**API fallback:**
```bash
# Search for docs owned by platform team
gh search code "owner_team: platform" \
  --repo github/thehub \
  --filename "*.md"
```

```
👥 Platform Team Documentation:

docs/teams/platform/
• platform-overview.md
• platform-architecture.md
• platform-services.md

docs/epd/engineering/
• kubernetes-guide.md            (owner: platform-infrastructure)
• container-standards.md         (owner: platform-containers)
• load-balancer-config.md       (owner: platform-networking)

💬 Contact: #platform-team

💡 Tip: Search owner_team in frontmatter to find all docs maintained
       by a specific team.
```

## Example 5: Browse Recent Updates

### User Ask: "What docs have been updated recently?"

**Local clone (preferred):**
```bash
# Get recently modified docs
find "$THEHUB_ROOT/docs" -name '*.md' -mtime -7 | head -10
```

**API fallback:**
```bash
# Get recent commits to docs/
gh api repos/github/thehub/commits \
  --jq '.[] | select(.commit.message | contains("docs/")) | {date: .commit.author.date, message: .commit.message}' \
  | head -10
```

```
📅 Recently Updated Docs:

2024-02-08: Updated deployment-guide.md - Added canary deployment section
2024-02-07: New doc: service-mesh-guide.md
2024-02-06: Updated security/incident-response.md - New escalation paths
2024-02-05: Updated products/copilot/copilot-architecture.md
2024-02-04: New doc: guides/remote-work-guide.md

💡 Tip: Check commit history to see what's new or changed.
```

## Quick Reference Commands

All commands below show local clone (preferred) and API fallback alternatives.

### List All Top-Level Directories

**Local:**
```bash
find "$THEHUB_ROOT/docs" -maxdepth 1 -type d | sort
```

**API fallback:**
```bash
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[] | select(.type == "tree" and (.path | startswith("docs/"))) | .path' \
  | cut -d/ -f1-2 | sort -u
```

### Count Docs by Directory

**Local:**
```bash
cd "$THEHUB_ROOT" && find docs -name '*.md' | cut -d/ -f1-4 | sort | uniq -c
```

**API fallback:**
```bash
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[] | select(.path | endswith(".md")) | .path' \
  | cut -d/ -f1-2 | sort | uniq -c
```

### Find All Docs with Specific Tag

**Local:**
```bash
grep -ri "tags: onboarding" "$THEHUB_ROOT/docs" --include='*.md' -l
```

**API fallback:**
```bash
# Search frontmatter tags
gh search code "tags: onboarding" \
  --repo github/thehub \
  --filename "*.md"
```

### Get Doc Metadata

**Local:**
```bash
# Read doc and extract frontmatter
cat "$THEHUB_ROOT/docs/path/to/doc.md" | awk '/^---$/,/^---$/'
```

**API fallback:**
```bash
# Fetch doc and extract frontmatter
gh api "repos/github/thehub/contents/docs/path/to/doc.md" \
  --jq '.content' | base64 -d | awk '/^---$/,/^---$/'
```

## Navigation Best Practices

### 1. Start Broad, Then Narrow

```
User: "How do I handle an incident?"

Good approach:
1. Check docs/security/ for incident policies
2. Check docs/epd/engineering/ for technical runbooks  
3. Check docs/teams/ for team-specific procedures
```

### 2. Use Directory Context

```
Engineering question  → docs/epd/engineering/
Security policy      → docs/security/
Tool usage          → docs/guides/tools/
Product docs        → docs/products/{product}/
Team process        → docs/teams/{team}/
```

### 3. Cross-Reference Related Docs

```
Deployment guide usually links to:
• Security requirements
• Service tier standards
• Monitoring setup
• Incident procedures
```

### 4. Check Multiple Perspectives

```
For "deploying Actions":
• docs/epd/engineering/deployment-guide.md    (general practices)
• docs/products/actions/deployment.md         (product-specific)
• docs/security/deployment-security.md        (security view)
• docs/teams/actions/runbook.md              (operations view)
```

## Common Documentation Patterns

### Policy Documents
- Location: `docs/security/`, `docs/epd/`
- Keywords: policy, standard, requirement, compliance
- Have clear owner_team and approval process

### How-To Guides
- Location: `docs/guides/`, `docs/epd/engineering/`
- Keywords: guide, how-to, tutorial, walkthrough
- Step-by-step instructions

### Runbooks
- Location: Various, often `docs/products/`, `docs/teams/`
- Keywords: runbook, operations, troubleshooting
- Operational procedures and troubleshooting

### Reference Documentation
- Location: `docs/products/`, `docs/epd/`
- Keywords: reference, architecture, specification
- Technical details and specifications

## Tips for Effective Navigation

✅ **Do:**
- Start with category that matches your need
- Use search when you're unsure where to look
- Check doc frontmatter for owner and contact
- Follow related links in documentation
- Browse directory listings to discover docs

❌ **Don't:**
- Try to read everything at once (5,000+ docs!)
- Ignore frontmatter metadata
- Forget to check for updated versions
- Skip related documentation links

## Need Help?

- **Can't find docs:** Ask in #eng-help or #github-help
- **Docs outdated:** Contact owner_team from frontmatter
- **Docs missing:** Ask in relevant team channel
- **Structure questions:** Ask in #thehub-help

---

💡 Remember: thehub is searchable! When in doubt, use search rather than
   trying to guess the file location.
