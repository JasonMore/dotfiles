# Org Search Skill

Find answers to questions about decisions, ownership, architecture, processes, and history by searching across an organization's GitHub issues, PRs, discussions, code, and documentation.

## When to Use This Skill

- You have a **question** (not a query for a specific issue/PR), like "Why was X built this way?" or "Who owns the billing service?"
- You **don't know which repo** to look in — you just know the org
- You need to find **decisions, rationale, ownership, or context** scattered across multiple repos and surfaces
- You're onboarding and need to understand past decisions or architecture
- You need to trace **historical context** (when/why something changed)

## Prerequisites

- GitHub CLI (`gh`) v2.40.0+ installed and authenticated
- Access to the organization you want to search

## Installation

### Personal Skills
```bash
cp -r org-search-skill ~/.copilot/skills/
```

### Project Skills
```bash
cp -r org-search-skill /path/to/repo/.github/skills/
```

## Usage

This skill activates when you ask Copilot questions like:

- "Why did we choose PostgreSQL over DynamoDB?"
- "Who is the DRI for the auth service?"
- "What was decided about the API versioning strategy?"
- "How does the deployment pipeline work?"
- "What's the status of the database migration?"
- "When did we deprecate the v1 API?"

The skill will:

1. **Analyze your question** to determine what kind of information you're looking for
2. **Discover relevant repos** in the org (if you didn't specify repos)
3. **Search across multiple surfaces** — issues, PRs, discussions, code, docs
4. **Read into top results** — bodies, comments, linked references
5. **Synthesize an answer** with evidence links and confidence level

## Features

- **Multi-surface search** — Searches issues, PRs, discussions, code, docs, CODEOWNERS, and ADRs
- **Org-level repo discovery** — Finds relevant repos when you only know the org
- **Question-type-aware** — Prioritizes different surfaces based on whether you're asking about decisions, ownership, architecture, status, process, or history
- **Query reformulation** — Automatically broadens search when initial results are sparse
- **Evidence-based answers** — Every answer includes links to the sources with confidence level
- **Cross-reference following** — Traces linked issues/PRs to find the full context

## Question Types Supported

| Type | Example | Primary Sources |
|------|---------|-----------------|
| Decisions & Rationale | "Why did we choose X?" | Issues, discussions, ADRs |
| Ownership & DRIs | "Who owns the billing service?" | CODEOWNERS, issues, README |
| Architecture | "How does auth work?" | Code/docs, issues, discussions |
| Status & Progress | "Is the migration done?" | Issues, PRs, milestones |
| Process & Policy | "How do we handle deploys?" | Docs, discussions, issues |
| Historical Context | "When did we switch to GraphQL?" | Closed issues, merged PRs |

## Examples

See the [`examples/`](./examples/) directory for detailed scenarios:

- [Decision Search](./examples/decision-search.md) — Finding why a technical choice was made
- [Ownership Search](./examples/ownership-search.md) — Finding who is DRI for a workstream
- [Cross-Repo Search](./examples/cross-repo-search.md) — Tracing information across multiple repos in an org

## Background

This skill is inspired by the [info-recall-agent](https://github.com/github/info-recall-agent) prototype, which demonstrated that answering organizational knowledge questions requires searching across multiple GitHub surfaces with intelligent query reformulation and evidence synthesis. This skill encodes that search methodology as a Copilot skill.
