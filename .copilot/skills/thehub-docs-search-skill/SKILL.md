---
name: thehub-docs-search
description: This skill should be used when the user asks to "search thehub", "find docs on", "look up in thehub", "search internal docs", "what's the policy on", "how do I deploy", "find the guide for", "search for documentation about", or needs to search and retrieve documentation from github/thehub.
---

# Docs Search - GitHub Internal Documentation Search

Search and retrieve documentation from GitHub's internal knowledge base (github/thehub) with 5,000+ docs covering engineering practices, product development, security policies, team guides, and more.

## When to Use This Skill

**Trigger phrases:**
- "Search thehub for [topic]"
- "Find docs on [topic]"
- "Look up the [guide/policy] for [topic]"
- "What's the policy on [topic]?"
- "How do I [action]?" (for engineering/deployment tasks)
- "Find the engineering guide for [topic]"
- "Search internal docs about [topic]"

**Appropriate use cases:**
- Finding engineering practices and development guides
- Looking up security policies and standards
- Discovering deployment and operational procedures
- Finding team guides and onboarding materials
- Searching for service documentation
- Looking up incident response procedures
- Finding company news and announcements

## Prerequisites Check

First, check for a local clone of `github/thehub`. GitHub CLI auth and API access are only required when falling back to the API.

```bash
# 1. Check for local clone first (no auth required)
if [ -n "${THEHUB_LOCAL_PATH:-}" ] && [ -d "$THEHUB_LOCAL_PATH/docs" ]; then
    THEHUB_ROOT="$THEHUB_LOCAL_PATH"
elif [ -d "../thehub/docs" ]; then
    THEHUB_ROOT="../thehub"
else
    THEHUB_ROOT=""
fi

# 2. If no local clone, verify GitHub CLI auth for API fallback
if [ -z "$THEHUB_ROOT" ]; then
    if ! gh auth status &>/dev/null; then
        echo "❌ Not authenticated with GitHub"
        echo "Run: gh auth login"
        echo "Or clone github/thehub locally for offline access"
        exit 1
    fi

    if ! gh api repos/github/thehub &>/dev/null; then
        echo "❌ Cannot access github/thehub repository"
        echo "You may not have the required permissions"
        echo "Or clone github/thehub locally for offline access"
        exit 1
    fi
fi
```

## Local vs API Access

**Always prefer a local clone of `github/thehub` when available.** Reading from a local clone is faster, avoids API rate limits, and works offline.

### Detecting a Local Clone

Check if `github/thehub` is cloned locally before making API calls. Do **not** hardcode assumed clone paths — discover the clone at runtime using techniques like:

- Checking sibling directories of the current repository (e.g. `../thehub`)
- Using `find` or `locate` to search common code directories
- Checking the `THEHUB_LOCAL_PATH` environment variable if set by the user

```bash
# Example: check for THEHUB_LOCAL_PATH env var, then try sibling directory
if [ -n "$THEHUB_LOCAL_PATH" ] && [ -d "$THEHUB_LOCAL_PATH/docs" ]; then
    THEHUB_ROOT="$THEHUB_LOCAL_PATH"
elif [ -d "../thehub/docs" ]; then
    THEHUB_ROOT="../thehub"
else
    THEHUB_ROOT=""
fi
```

### Local Operations (Preferred)

When a local clone is available, use local file operations:

| API Operation | Local Equivalent |
|---------------|-----------------|
| `gh api .../git/trees/main?recursive=1` | `find "$THEHUB_ROOT/docs" -name '*.md'` |
| `gh api .../contents/docs/path.md --jq '.content' \| base64 -d` | `cat "$THEHUB_ROOT/docs/path.md"` |
| `gh search code "TERM" --repo github/thehub` | `grep -ri "TERM" "$THEHUB_ROOT/docs" --include='*.md'` |
| `gh api repos/github/thehub` (access check) | `[ -d "$THEHUB_ROOT/docs" ]` |

### API Fallback

If no local clone is found, fall back to `gh api` and `gh search code` commands as shown throughout this skill. All API-based commands remain valid fallbacks.

## Understanding thehub Structure

The github/thehub repository organizes documentation in the `docs/` directory:

| Directory | Content |
|-----------|---------|
| `docs/epd/engineering/` | Engineering practices, development guides, products & services |
| `docs/security/` | Security policies, operations, standards, compliance |
| `docs/guides/` | General guides (Hubot, onboarding, tools, workflows) |
| `docs/news/` | Company news, announcements, updates |
| `docs/teams/` | Team-specific documentation and processes |
| `docs/products/` | Product documentation and specifications |

**Jekyll frontmatter:** Docs use YAML frontmatter with:
- `layout` - Page template
- `title` - Document title
- `owner_team` - Team responsible for the doc
- `owner_slack` - Slack channel for questions

**URLs:** thehub.github.com URLs map directly to the docs/ directory structure.

## Core Search Strategies

### Strategy 1: Search by Filename/Path

Best for: Finding specific docs when you know approximate names or paths.

**Option A: Local clone (preferred)**

```bash
# Search for matching file paths
find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "SEARCH_TERM"

# Examples:
find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "deploy"
find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "incident"
```

**Option B: GitHub API (fallback)**

```bash
# Search the tree for matching paths
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep -i "SEARCH_TERM"

# Examples:
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep -i "deploy"

gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep -i "incident"

# Filter to docs directory only
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/' | grep -i "SEARCH_TERM"
```

**Output format:** Returns matching file paths like:
```
docs/epd/engineering/deployment-guide.md
docs/security/incident-response.md
docs/guides/production-access.md
```

**Pros:** Fast, good for known terms, shows directory structure
**Cons:** Misses content that's in the file but not in the filename

### Strategy 2: Search Doc Contents

Best for: Finding docs by keywords, topics, or concepts mentioned in content.

**Option A: Local clone (preferred)**

```bash
# Search markdown files for content
grep -ri "SEARCH_TERM" "$THEHUB_ROOT/docs" --include='*.md' -l

# Examples:
grep -ri "service tier" "$THEHUB_ROOT/docs" --include='*.md' -l
grep -ri "observability" "$THEHUB_ROOT/docs" --include='*.md' -l

# Search within specific directory
grep -ri "deployment" "$THEHUB_ROOT/docs/epd/engineering" --include='*.md' -l
```

**Option B: GitHub API (fallback)**

```bash
# Search markdown files for content
gh search code "SEARCH_TERM" \
  --repo github/thehub \
  --filename "*.md" \
  --limit 20

# Examples:
gh search code "service tier" \
  --repo github/thehub \
  --filename "*.md"

gh search code "observability" \
  --repo github/thehub \
  --filename "*.md" \
  --limit 10

# Search within specific directory
gh search code "deployment" \
  --repo github/thehub \
  --path "docs/epd/engineering/" \
  --filename "*.md"
```

**Output format:** Returns matching files with snippets:
```
docs/epd/engineering/services.md
    ...service tier definitions...

docs/security/compliance.md
    ...service tier requirements...
```

**Pros:** Finds relevant content regardless of filename
**Cons:** May return many results, need to filter relevance

### Strategy 3: Combined Search (Recommended)

Use both strategies for comprehensive results:

**Option A: Local clone (preferred)**

```bash
# 1. First try path search (fast)
echo "=== Searching paths ==="
find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "SEARCH_TERM"

# 2. Then search content
echo "=== Searching content ==="
grep -ri "SEARCH_TERM" "$THEHUB_ROOT/docs" --include='*.md' -l
```

**Option B: GitHub API (fallback)**

```bash
# 1. First try path search (fast)
echo "=== Searching paths ==="
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/' | grep -i "SEARCH_TERM"

# 2. Then search content
echo "=== Searching content ==="
gh search code "SEARCH_TERM" \
  --repo github/thehub \
  --filename "*.md" \
  --limit 10
```

### Strategy 4: Directory-Specific Search

When the topic maps to a known directory:

**Option A: Local clone (preferred)**

```bash
# Engineering topics
find "$THEHUB_ROOT/docs/epd/engineering" -name '*.md' | grep -i "TERM"

# Security topics
find "$THEHUB_ROOT/docs/security" -name '*.md' | grep -i "TERM"

# General guides
find "$THEHUB_ROOT/docs/guides" -name '*.md' | grep -i "TERM"
```

**Option B: GitHub API (fallback)**

```bash
# Engineering topics
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/epd/engineering/' | grep -i "TERM"

# Security topics
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/security/' | grep -i "TERM"

# General guides
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/guides/' | grep -i "TERM"
```

## Retrieving Documentation

Once you've identified relevant docs, fetch their content:

### Basic Retrieval

**Option A: Local clone (preferred)**

```bash
# Read a specific doc directly
cat "$THEHUB_ROOT/docs/path/to/doc.md"

# Example:
cat "$THEHUB_ROOT/docs/epd/engineering/deployment.md"
```

**Option B: GitHub API (fallback)**

```bash
# Fetch a specific doc
gh api "repos/github/thehub/contents/docs/path/to/doc.md" \
  --jq '.content' | base64 -d

# Example:
gh api "repos/github/thehub/contents/docs/epd/engineering/deployment.md" \
  --jq '.content' | base64 -d
```

### Retrieve with Frontmatter Parsing

**Option A: Local clone (preferred)**

```bash
# Get doc content directly
DOC_CONTENT=$(cat "$THEHUB_ROOT/docs/epd/engineering/deployment.md")

# Extract title from frontmatter
echo "$DOC_CONTENT" | awk '/^---$/,/^---$/' | grep '^title:' | cut -d: -f2- | xargs

# Extract owner team
echo "$DOC_CONTENT" | awk '/^---$/,/^---$/' | grep '^owner_team:' | cut -d: -f2- | xargs
```

**Option B: GitHub API (fallback)**

```bash
# Get doc content and parse frontmatter
DOC_CONTENT=$(gh api "repos/github/thehub/contents/docs/epd/engineering/deployment.md" \
  --jq '.content' | base64 -d)

# Extract title from frontmatter
echo "$DOC_CONTENT" | awk '/^---$/,/^---$/' | grep '^title:' | cut -d: -f2- | xargs

# Extract owner team
echo "$DOC_CONTENT" | awk '/^---$/,/^---$/' | grep '^owner_team:' | cut -d: -f2- | xargs
```

### Retrieve Multiple Docs

When search returns multiple relevant docs:

**Option A: Local clone (preferred)**

```bash
# Get list of matching files
DOCS=$(find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "SEARCH_TERM" | head -5)

# Read each doc
for doc in $DOCS; do
    echo "=== $doc ==="
    cat "$doc"
    echo ""
done
```

**Option B: GitHub API (fallback)**

```bash
# Get list of matching files
DOCS=$(gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/' | grep -i "SEARCH_TERM" | head -5)

# Fetch each doc
for doc in $DOCS; do
    echo "=== $doc ==="
    gh api "repos/github/thehub/contents/$doc" --jq '.content' | base64 -d
    echo ""
done
```

## Presenting Results

### Format for User Consumption

Always present retrieved docs with:

1. **Clear source attribution** with thehub.github.com link
2. **Frontmatter metadata** (title, owner_team, owner_slack)
3. **Key sections or summary** rather than full dump
4. **Next steps or related docs**

**Template:**

```
📄 Found: [Doc Title]
🔗 https://thehub.github.com/docs/path/to/doc

Owner: [owner_team] (Slack: [owner_slack])

Key sections:
• [Section 1]
• [Section 2]

Summary:
[Brief 2-3 sentence summary of most relevant content]

Related docs:
• [Related doc 1]
• [Related doc 2]
```

### Example Output

```
📄 Found: Production Deployment Guide
🔗 https://thehub.github.com/docs/epd/engineering/deployment-guide

Owner: engineering-productivity (#eng-prod)

Key sections:
• Pre-deployment checklist
• Deployment procedures
• Rollback process
• Post-deployment verification

Summary:
All production deployments must go through the standard deployment pipeline
with approval from the service owner. Deployments are automated via GitHub
Actions with manual approval gates. Rollback procedures are documented for
all service tiers.

Next steps:
• Check service-specific deployment docs in docs/products/
• Review the incident response guide if issues occur
• Contact #eng-prod for deployment support
```

## Search Workflow

Follow this systematic approach:

### 1. Clarify Search Intent

If the user's request is vague, clarify:
- What specific information are they looking for?
- Which area is most relevant (engineering/security/guides)?
- Are they looking for a policy, procedure, guide, or reference?

### 2. Execute Search

**Option A: Local clone (preferred)**

```bash
echo "Searching thehub for: [TOPIC]"
echo ""

# Path search
echo "=== Matching documents ==="
PATHS=$(find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "[SEARCH_TERM]")

if [ -n "$PATHS" ]; then
    echo "$PATHS"
else
    echo "No path matches found"
fi

echo ""
echo "=== Content search ==="
grep -ri "[SEARCH_TERM]" "$THEHUB_ROOT/docs" --include='*.md' -l
```

**Option B: GitHub API (fallback)**

```bash
# Combined search approach
echo "Searching thehub for: [TOPIC]"
echo ""

# Path search
echo "=== Matching documents ==="
PATHS=$(gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/' | grep -i "[SEARCH_TERM]")

if [ -n "$PATHS" ]; then
    echo "$PATHS"
else
    echo "No path matches found"
fi

echo ""
echo "=== Content search ==="
gh search code "[SEARCH_TERM]" \
  --repo github/thehub \
  --filename "*.md" \
  --limit 10
```

### 3. Filter and Rank Results

Prioritize results by relevance:
1. Exact filename matches
2. Docs in the most relevant directory
3. Recent docs (check last modified if available)
4. Docs with owner information

### 4. Retrieve and Summarize

Fetch the top 2-3 most relevant docs:

**Option A: Local clone (preferred)**

```bash
# Get top result
TOP_DOC="docs/path/to/most-relevant.md"

# Read content
CONTENT=$(cat "$THEHUB_ROOT/$TOP_DOC")

# Extract key information
TITLE=$(echo "$CONTENT" | awk '/^---$/,/^---$/' | grep '^title:' | cut -d: -f2- | xargs)
OWNER=$(echo "$CONTENT" | awk '/^---$/,/^---$/' | grep '^owner_team:' | cut -d: -f2- | xargs)

# Present to user with link
echo "📄 $TITLE"
echo "🔗 https://thehub.github.com/$TOP_DOC"
echo "Owner: $OWNER"
```

**Option B: GitHub API (fallback)**

```bash
# Get top result
TOP_DOC="docs/path/to/most-relevant.md"

# Fetch content
CONTENT=$(gh api "repos/github/thehub/contents/$TOP_DOC" \
  --jq '.content' | base64 -d)

# Extract key information
TITLE=$(echo "$CONTENT" | awk '/^---$/,/^---$/' | grep '^title:' | cut -d: -f2- | xargs)
OWNER=$(echo "$CONTENT" | awk '/^---$/,/^---$/' | grep '^owner_team:' | cut -d: -f2- | xargs)

# Present to user with link
echo "📄 $TITLE"
echo "🔗 https://thehub.github.com/$TOP_DOC"
echo "Owner: $OWNER"
```

### 5. Offer Related Search

Suggest related searches or docs:
- "Want me to search for related topics?"
- "Should I check the security docs as well?"
- "Would you like the team contact information?"

## Common Search Patterns

### Pattern 1: "How do I [action]?"

Map to engineering/guides:

**Option A: Local clone (preferred)**

```bash
# Try engineering first
grep -ri "[action]" "$THEHUB_ROOT/docs/epd/engineering" --include='*.md' -l

# Fall back to guides
grep -ri "[action]" "$THEHUB_ROOT/docs/guides" --include='*.md' -l
```

**Option B: GitHub API (fallback)**

```bash
# Try engineering first
gh search code "[action]" \
  --repo github/thehub \
  --path "docs/epd/engineering/" \
  --filename "*.md"

# Fall back to guides
gh search code "[action]" \
  --repo github/thehub \
  --path "docs/guides/" \
  --filename "*.md"
```

### Pattern 2: "What's the policy on [topic]?"

Map to security/compliance:

**Option A: Local clone (preferred)**

```bash
# Search security policies
grep -ri "[topic]" "$THEHUB_ROOT/docs/security" --include='*.md' -l

# Check for policy docs specifically
find "$THEHUB_ROOT/docs/security" -name '*.md' | grep -i "policy" | grep -i "[topic]"
```

**Option B: GitHub API (fallback)**

```bash
# Search security policies
gh search code "[topic]" \
  --repo github/thehub \
  --path "docs/security/" \
  --filename "*.md"

# Check for policy docs specifically
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/security/' | grep -i "policy" | grep -i "[topic]"
```

### Pattern 3: "Find the guide for [topic]"

Check guides directory:

**Option A: Local clone (preferred)**

```bash
# Search guides by path
find "$THEHUB_ROOT/docs/guides" -name '*.md' | grep -i "[topic]"

# Content search in guides
grep -ri "[topic]" "$THEHUB_ROOT/docs/guides" --include='*.md' -l
```

**Option B: GitHub API (fallback)**

```bash
# Search guides
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/guides/' | grep -i "[topic]"

# Content search in guides
gh search code "[topic]" \
  --repo github/thehub \
  --path "docs/guides/" \
  --filename "*.md"
```

### Pattern 4: Service/Product Documentation

**Option A: Local clone (preferred)**

```bash
# Search products directory
find "$THEHUB_ROOT/docs/products" -name '*.md' | grep -i "[service_name]"

# Or engineering services
find "$THEHUB_ROOT/docs/epd/engineering" -name '*.md' | grep -i "[service_name]"
```

**Option B: GitHub API (fallback)**

```bash
# Search products directory
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/products/' | grep -i "[service_name]"

# Or engineering services
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/epd/engineering/' | grep -i "[service_name]"
```

## Error Handling

### No Results Found

```bash
if [ -z "$SEARCH_RESULTS" ]; then
    echo "⚠️  No docs found for '[SEARCH_TERM]'"
    echo ""
    echo "Suggestions:"
    echo "• Try different keywords or broader terms"
    echo "• Check spelling"
    if [ -n "$THEHUB_ROOT" ]; then
        echo "• Browse directory structure: find $THEHUB_ROOT/docs -name '*.md' | head -30"
    else
        echo "• Browse directory structure: gh api repos/github/thehub/git/trees/main?recursive=1"
    fi
    echo "• Ask in #eng-help or #github-help Slack channels"
fi
```

### Access Denied

```bash
if ! gh api repos/github/thehub &>/dev/null; then
    echo "❌ Cannot access github/thehub"
    echo ""
    echo "This may mean:"
    echo "• You don't have GitHub access (need to be a Hubber)"
    echo "• Your GitHub token needs refresh: gh auth login"
    echo "• Network/VPN issues"
    echo ""
    echo "Contact #github-help for access issues"
    exit 1
fi
```

### Rate Limiting

```bash
# Check rate limit before heavy operations
RATE_REMAINING=$(gh api rate_limit --jq '.rate.remaining')

if [ "$RATE_REMAINING" -lt 10 ]; then
    echo "⚠️  GitHub API rate limit low: $RATE_REMAINING requests remaining"
    echo "Consider waiting or using more specific searches"
fi
```

### Invalid Doc Path

```bash
# Handle missing files gracefully (local or API)
if [ -n "$THEHUB_ROOT" ]; then
    if [ ! -f "$THEHUB_ROOT/$DOC_PATH" ]; then
        echo "❌ Doc not found: $DOC_PATH"
        echo ""
        echo "The document may have been:"
        echo "• Moved to a different location"
        echo "• Renamed"
        echo "• Deleted"
        echo ""
        echo "Try searching by content instead"
    fi
elif ! gh api "repos/github/thehub/contents/$DOC_PATH" &>/dev/null; then
    echo "❌ Doc not found: $DOC_PATH"
    echo ""
    echo "The document may have been:"
    echo "• Moved to a different location"
    echo "• Renamed"
    echo "• Deleted"
    echo ""
    echo "Try searching by content instead"
fi
```

## Performance Considerations

### Efficient Searching

**Do:**
- Prefer a local clone of `github/thehub` when available (fastest, no rate limits)
- Use directory filters when possible (`--path` flag or local directory paths)
- Limit results (`--limit 10`)
- Cache tree listings for multiple searches (when using API)
- Search paths first (faster than content search)

**Don't:**
- Fetch all docs without filtering
- Search without directory context
- Retrieve full content unnecessarily
- Ignore API rate limits (when using API fallback)
- Hardcode assumed clone paths

### Caching Tree Structure

For multiple searches in one session:

```bash
# Cache the tree once
TREE_CACHE="/tmp/thehub-tree-cache.txt"

if [ ! -f "$TREE_CACHE" ] || [ $(find "$TREE_CACHE" -mmin +60) ]; then
    gh api 'repos/github/thehub/git/trees/main?recursive=1' \
      --jq '.tree[].path' > "$TREE_CACHE"
fi

# Use cached tree for searches
grep '^docs/' "$TREE_CACHE" | grep -i "SEARCH_TERM"
```

## Security and Sensitivity

### Handle Sensitive Information

Some thehub docs contain sensitive information (policies, security procedures, internal processes).

**Important guidelines:**
- Always present doc content directly to the user
- Don't use doc content silently in background operations
- Don't expose sensitive information in logs or temp files
- When in doubt about sensitivity, show the source link and let user review
- Respect document ownership and contact channels

### User Confirmation

For sensitive topics (security, compliance, access), confirm intent:

```
⚠️  This search relates to security policies.

Found: docs/security/access-control-policy.md

This document may contain sensitive information.
Would you like me to:
1. Show you the link to review directly
2. Provide a summary of key points
3. Fetch specific sections you need
```

## Integration with Other Workflows

### With Incident Response

**Local clone (preferred):**
```bash
find "$THEHUB_ROOT/docs" -name '*.md' | grep -i 'incident'
```

**API fallback:**
```bash
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep 'incident' | grep 'docs/'
```

### With Onboarding

**Local clone (preferred):**
```bash
find "$THEHUB_ROOT/docs/guides" -name '*.md' | grep -i 'onboard'
```

**API fallback:**
```bash
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/guides/' | grep -i 'onboard'
```

### With Deployment

**Local clone (preferred):**
```bash
grep -ri "deploy [SERVICE_NAME]" "$THEHUB_ROOT/docs/epd/engineering" --include='*.md' -l
```

**API fallback:**
```bash
gh search code "deploy [SERVICE_NAME]" \
  --repo github/thehub \
  --path "docs/epd/engineering/" \
  --filename "*.md"
```

## Boundaries

**Will:**
- Search github/thehub repository documentation
- Retrieve and present doc content with proper attribution
- Navigate the docs directory structure
- Provide thehub.github.com links
- Handle frontmatter metadata
- Suggest related docs and next steps

**Will Not:**
- Modify or create docs in thehub (read-only)
- Search other repositories unless explicitly requested
- Make assumptions about sensitive information
- Cache sensitive doc content
- Operate without proper GitHub authentication

## Quick Reference

**Essential Commands:**

**Local clone (preferred):**

```bash
# Search paths
find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "TERM"

# Search content
grep -ri "TERM" "$THEHUB_ROOT/docs" --include='*.md' -l

# Retrieve doc
cat "$THEHUB_ROOT/docs/path/to/doc.md"

# Check availability
[ -d "$THEHUB_ROOT/docs" ] && echo "Available" || echo "Not found"
```

**GitHub API (fallback):**

```bash
# Search paths
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/' | grep -i "TERM"

# Search content
gh search code "TERM" --repo github/thehub --filename "*.md" --limit 10

# Retrieve doc
gh api "repos/github/thehub/contents/docs/path/to/doc.md" \
  --jq '.content' | base64 -d

# Check access
gh api repos/github/thehub --silent

# Rate limit
gh api rate_limit --jq '.rate.remaining'
```

**Directory Quick Map:**

```
docs/epd/engineering/  → Engineering practices, deployment, services
docs/security/         → Security policies, compliance, standards  
docs/guides/           → Onboarding, tools, workflows
docs/news/             → Announcements, updates
docs/teams/            → Team-specific docs
docs/products/         → Product specifications
```

**URL Format:**

```
https://thehub.github.com/docs/path/to/doc
```

## Examples

See the `examples/` directory for detailed scenarios:
- Searching for engineering practices
- Finding security policies
- Navigating the docs structure
- Retrieving and summarizing documentation
