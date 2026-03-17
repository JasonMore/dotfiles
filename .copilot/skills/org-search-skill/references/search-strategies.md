# Search Strategies Reference

Detailed reference for search strategies used by the org-search skill. This supplements the main SKILL.md with technical details and advanced patterns.

## GitHub Search Surfaces Overview

| Surface | API | Best For | Limitations |
|---------|-----|----------|-------------|
| Issues (Semantic) | `GET /search/issues?search_type=semantic` | Natural language questions, decisions, context | Requires repo to be semantically indexed |
| Issues (Lexical) | `gh search issues` / Search Issues API | Keyword-based search, fallback | Only keyword matching |
| Similar Issues | `GET /repos/:owner/:repo/issues/:number/semantically_similar` | Expanding from a known issue | Requires a starting issue; max 3 results by default |
| Pull Requests | `gh search prs` / Search PRs API | Implementation rationale, code changes | PR descriptions vary in quality |
| Discussions | `gh api search/discussions` | RFCs, Q&A, architecture | May not be enabled on all repos; search API may 404 |
| Code | `gh search code` / Search Code API | Documentation, config, ADRs | Limited to indexed files; no binary |
| Repos | `gh search repos` / Search Repos API | Repo discovery | Only searches name/description/topics |
| Commits | `gh search commits` | Historical tracking | Commit messages are often terse |

## ISS Semantic Search

GitHub's Issues Semantic Search (ISS) uses vector embeddings (Azure OpenAI text-embedding-3-small) to enable semantic understanding of issues. This is the **preferred search method** for this skill because the questions we handle are natural language questions where keyword matching often fails.

### How it works

1. Issues and PRs are indexed with vector embeddings generated from title, body, and comments
2. Your search query is also embedded into a vector
3. Cosine similarity finds conceptually related content
4. Results combine semantic and lexical signals (hybrid search)

### Semantic Search API

```bash
# Natural language search for issues
gh api -X GET "/search/issues" \
  -f q="is:issue repo:OWNER/REPO natural language question here" \
  -f search_type=semantic \
  -f per_page=10
```

Key points:
- Add `search_type=semantic` to the search/issues endpoint
- Use natural language in the query — describe what you're looking for
- Works best with 5+ word queries; short queries may fall back to lexical-only
- Combine with standard filters: `is:issue`, `is:open`, `repo:`, `label:`
- **Does NOT support `org:`, `user:`, or `owner:` qualifiers** — must scope to `repo:OWNER/REPO`
- Queries with quotes or OR operators fall back to lexical search

### Similar Issues API

```bash
# Find issues similar to a known issue
gh api "/repos/OWNER/REPO/issues/NUMBER/semantically_similar" \
  --jq '.[] | {title: .title, url: .html_url, state: .state}'

# With custom result count
gh api "/repos/OWNER/REPO/issues/NUMBER/semantically_similar?per_page=5"
```

Key points:
- Returns issues ranked by cosine similarity
- Defaults to max 3 results; use `per_page` for more
- Great for expanding context once you find one relevant issue
- Can reveal related decisions, follow-ups, and duplicates

### When semantic search is unavailable

Semantic search may not be available if:
- The repo has not been semantically indexed yet
- Feature flags are not enabled for the org
- The API returns an error or empty results

In these cases, fall back to standard lexical search (`gh search issues`).

## Query Syntax Reference

### Issue and PR Search

```
# Scoping
org:ORGNAME              Search within an org
repo:OWNER/REPO          Search within a specific repo
user:USERNAME            Search by author

# Filters
is:issue / is:pr         Type filter
is:open / is:closed      State filter
is:merged                Merged PRs only
label:LABEL              By label
assignee:USERNAME        By assignee
author:USERNAME          By author
milestone:"NAME"         By milestone

# Date filters
created:>2025-01-01      Created after date
updated:>2025-01-01      Updated after date
closed:>2025-01-01       Closed after date

# Content
in:title                 Search in title only
in:body                  Search in body only
in:comments              Search in comments

# Combine
org:acme label:RFC is:closed PostgreSQL    # Closed RFCs about PostgreSQL in acme
```

### Code Search

```
# Scoping
repo:OWNER/REPO          Within a specific repo
org:ORGNAME              Within an org
path:docs/               Within a directory
path:*.md                Matching file pattern

# File filters
filename:README.md       Specific filename
filename:*.md            File extension
language:markdown        By language

# Content
"exact phrase"           Exact match
word1 word2              Both words

# Examples
org:acme path:docs/ filename:*.md "deployment"
repo:acme/service CODEOWNERS
org:acme filename:ADR path:docs/adr/
```

### Repository Search

```
# Scoping
org:ORGNAME              Within an org

# Filters
language:LANG            Primary language
topic:TOPIC              By topic label
archived:false           Exclude archived

# Sorting
sort:updated             Most recently updated
sort:stars               Most starred

# Examples
org:acme billing payments
org:acme topic:infrastructure sort:updated
```

## Repo Discovery Strategies

### Strategy 1: Name and Description Match

Search repos whose name or description matches the question's terms.

```bash
gh search repos "billing payments" --owner acme --limit 10
```

**Pros:** Fast, finds obviously named repos
**Cons:** Misses repos with non-obvious names (e.g., a billing service named "stripe-integration")

### Strategy 2: Issue-Based Inference

Search issues across the org and note which repos they live in.

```bash
# Find repos that have issues discussing the topic
gh search issues "PostgreSQL migration" --owner acme --limit 20 \
  --json repository --jq '.[].repository.nameWithOwner' | sort -u
```

**Pros:** Finds repos where the topic was actually discussed, even if the repo name doesn't mention it
**Cons:** Slower, requires two-step search

### Strategy 3: Code-Based Inference

Search code across the org to find repos containing relevant files.

```bash
# Find repos with ADRs about the topic
gh search code "PostgreSQL" --owner acme --filename "*.md" --limit 20 \
  --json repository --jq '.[].repository.nameWithOwner' | sort -u
```

**Pros:** Finds documentation and code references
**Cons:** May surface irrelevant repos that just mention the term

### Strategy 4: Combined (Recommended)

Run all three in parallel, merge results, and prioritize repos found by multiple strategies.

## Surface-Specific Search Patterns

### Finding Decisions

```bash
# Semantic search for decisions (preferred — understands intent)
# NOTE: Semantic search requires repo: scoping, not org:
gh api -X GET "/search/issues" \
  -f q="is:issue repo:OWNER/REPO why did we decide TOPIC" \
  -f search_type=semantic \
  -f per_page=10

# Labeled decision records (lexical fallback)
gh search issues "TOPIC" --owner acme --label decision --limit 10
gh search issues "TOPIC" --owner acme --label RFC --limit 10
gh search issues "TOPIC" --owner acme --label ADR --limit 10

# Expand from a known decision issue
gh api "/repos/OWNER/REPO/issues/NUMBER/semantically_similar" \
  --jq '.[] | {title: .title, url: .html_url}'

# Architecture Decision Records in code
gh search code "TOPIC" --owner acme --path "docs/adr/" --filename "*.md"
gh search code "TOPIC" --owner acme --path "docs/decisions/" --filename "*.md"

# Discussions in RFC category
gh api "search/discussions?q=org:acme+TOPIC+category:RFC" 2>/dev/null

# Discussion search via CLI
gh search issues --type discussion "TOPIC decision" --repo OWNER/REPO
```

### Finding Ownership

```bash
# CODEOWNERS files
gh search code "" --owner acme --filename CODEOWNERS --limit 20

# Read specific CODEOWNERS
gh api "repos/OWNER/REPO/contents/CODEOWNERS" --jq '.content' | base64 -d
gh api "repos/OWNER/REPO/contents/.github/CODEOWNERS" --jq '.content' | base64 -d

# Team mentions in issues
gh search issues "DRI owner team TOPIC" --owner acme --limit 10

# Status updates with DRI mentions
gh search code "DRI" --owner acme --path "status-updates/" --filename "*.md" --limit 10
gh search code "DRI" --owner acme --path "reports/" --filename "*.md" --limit 10

# Issue-fields metadata (epic/milestone issues with structured DRI fields)
# Look for issues with tables like: | DRI | @username |
gh search issues "DRI TOPIC" --owner acme --limit 10

# README team sections
gh search code "DRI" --owner acme --filename README.md --limit 10
gh search code "team" --owner acme --filename README.md --limit 10
```

### Finding Architecture

```bash
# Documentation files
gh search code "TOPIC" --owner acme --filename README.md --limit 20
gh search code "TOPIC" --owner acme --path "docs/" --filename "*.md" --limit 20

# Architecture docs specifically
gh search code "architecture" --owner acme --path "docs/" --filename "*.md" --limit 10

# Design documents
gh search issues "TOPIC design architecture" --owner acme --label design --limit 10
```

### Finding Status

```bash
# Semantic search for status/progress
# NOTE: Semantic search requires repo: scoping, not org:
gh api -X GET "/search/issues" \
  -f q="is:issue repo:OWNER/REPO status progress TOPIC" \
  -f search_type=semantic \
  -f per_page=10

# Open issues with milestones (lexical)
gh search issues "TOPIC" --owner acme --state open --limit 10

# Recently closed issues (completed work)
gh search issues "TOPIC" --owner acme --state closed --sort updated --limit 10

# Merged PRs (shipped work)
gh search prs "TOPIC" --owner acme --merged --sort updated --limit 10
```

### Finding Process

```bash
# Contributing guides
gh search code "TOPIC" --owner acme --filename CONTRIBUTING.md --limit 10

# Runbooks
gh search code "TOPIC" --owner acme --path "docs/runbooks/" --filename "*.md" --limit 10
gh search code "TOPIC" --owner acme --path "runbooks/" --filename "*.md" --limit 10

# Process documentation
gh search code "process procedure workflow" --owner acme --filename "*.md" --limit 20

# Status updates and reports
gh search code "TOPIC" --owner acme --path "status-updates/" --filename "*.md" --limit 10
gh search code "TOPIC" --owner acme --path ".github/" --filename "*.md" --limit 10
```

### Finding Historical Context

```bash
# Closed issues sorted by date
gh search issues "TOPIC" --owner acme --state closed --sort created --order asc --limit 10

# Merged PRs sorted by date
gh search prs "TOPIC" --owner acme --merged --sort created --order asc --limit 10

# Old discussions
gh api "search/discussions?q=org:acme+TOPIC&sort=created&order=asc" 2>/dev/null
```

## Query Reformulation Patterns

When initial searches return few results, systematically broaden:

### Level 1: Synonyms

| Original | Try Also |
|----------|----------|
| PostgreSQL | postgres, pg, database, DB |
| authentication | auth, login, identity, IAM, SSO |
| deployment | deploy, release, ship, rollout |
| migration | migrate, upgrade, transition |
| API | endpoint, service, interface |
| monitoring | observability, metrics, alerts |

### Level 2: Generalization

| Specific → General |
|---------------------|
| "PostgreSQL migration plan" → "database migration" |
| "billing service authentication" → "service authentication" |
| "Q4 deployment freeze" → "deployment freeze" |

### Level 3: Domain Expansion

| Topic → Related Terms |
|------------------------|
| billing → payments, invoicing, subscription, pricing |
| auth → identity, SSO, OAuth, SAML, login, session |
| deploy → CI/CD, pipeline, release, canary, rollback |

### Level 4: Rephrase and Reduce

- **Rephrase as natural language** (for semantic search): Instead of keywords, describe what you're looking for as a question or statement
- **Remove qualifiers:** Drop `label:` filters, broaden date ranges, remove `is:open`/`is:closed`
- **Expand from a hit:** If you find one relevant issue, use the Similar Issues API to discover related ones

### Level 5: Structural

Try different search surfaces if the primary one is empty:
- Issues empty → try PRs (decisions might be in PR descriptions)
- PRs empty → try discussions (RFC might be a discussion, not an issue)
- All empty → try code search (answer might be in docs)

## Error Handling

### API Rate Limiting

If rate-limited during search:
- Prioritize the most promising surface and repos
- Use more targeted queries instead of broad sweeps
- Inform the user and suggest continuing later

### Access Denied

If a repo or resource is inaccessible:
- Note it in the output: "Could not access repo X (permission denied)"
- Continue searching other accessible repos
- Suggest the user check access if the blocked repo seems critical

### No Results

If all searches return empty results:
1. Verify the org name is correct
2. Try broader search terms (see Query Reformulation Patterns above)
3. Search without repo scope (org-wide) using keyword search
4. Ask the user for more context or alternative terms

## Reading Deep Into Results

### Issue Deep-Read Checklist

1. Read the issue body (the original post)
2. Read **all comments** — decisions are often made in comments
3. Check **linked PRs** — implementation details and discussions
4. Check **linked issues** — related context and follow-ups
5. Check **labels** — reveal categorization (RFC, decision, bug, etc.)
6. Check **assignees** — reveals ownership
7. Check **milestone** — reveals project/timeline context
8. Check **timeline events** — cross-references, label changes, status updates

### PR Deep-Read Checklist

1. Read the PR description
2. Check **linked issues** (via "Closes #X" or "Fixes #X")
3. Read **review comments** — often contain decision rationale
4. Check **files changed** — what was actually modified
5. Check **reviewers** — reveals who has authority/knowledge

### Code Deep-Read Checklist

1. Read the file content
2. Check **inline comments** — may explain "why"
3. Check **git blame** — who last modified and when
4. Check **commit messages** — may reference issues or explain changes
5. Look at **surrounding files** — README in same directory, related configs
