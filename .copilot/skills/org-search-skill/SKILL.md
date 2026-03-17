---
description: This skill should be used when the user asks to "find out why", "who is responsible for", "what was decided about", "search across repos for", "find information about", "what's the status of", "how does X work", "who is the DRI for", or needs to find information scattered across GitHub issues, PRs, discussions, code, and documentation within an organization. This is NOT for finding a specific issue or PR — it's for answering questions about decisions, ownership, architecture, processes, and historical context when the user doesn't know where to look.
metadata:
    github-owner: github
    github-path: org-search-skill
    github-ref: main
    github-repo: agent-skills
    github-sha: aa297c419ded9a6e44dc4157689f7647c42803d7
    github-tree-sha: 56dfd5b64ab4191883dfbf5ffb8fc8b06db48133
name: org-search
---
# Org Search - Find Information Across GitHub

Search for answers to questions across an organization's GitHub presence — issues, PRs, discussions, code, docs, and more — when the user has a question but doesn't know which repo or surface holds the answer.

> **Reference:** For detailed API syntax, query patterns, and command examples, see [`references/search-strategies.md`](references/search-strategies.md).

## When to Use This Skill

**Trigger phrases:**
- "Why was X implemented this way?"
- "Who is the DRI for [workstream]?"
- "What was decided about [topic]?"
- "How does [system] work?"
- "What's the status of [project]?"
- "What's our process for [workflow]?"
- "Find information about [topic] in [org]"
- "Search across repos for [topic]"
- "When did we switch from X to Y?"

**Not appropriate when:**
- User wants a specific issue or PR by number (just fetch it directly)
- User wants to create/modify content (use other tools)
- User wants to search within a single file (use regular search)

## Process Overview

```
1. Analyze the Question  → Classify type, extract key terms, determine scope
2. Discover Repos        → Find relevant repos if user only provided org
3. Search Surfaces       → Search issues, PRs, discussions, code, docs
4. Dig Into Evidence     → Read top hits, follow cross-references
5. Synthesize Answer     → Compose answer with evidence and links
```

## Step 1: Analyze the Question

Before searching, understand what the user is actually asking. This determines which surfaces to prioritize.

### Classify the Question Type

| Type | Signals | Priority Surfaces | Example |
|------|---------|-------------------|---------|
| **Decision/Rationale** | "why", "decided", "chose", "rationale" | Issues, PRs, discussions | "Why did we choose PostgreSQL over DynamoDB?" |
| **Ownership/DRI** | "who owns", "DRI", "responsible", "team" | CODEOWNERS, issues (assignments), team files | "Who is DRI for the billing service?" |
| **Architecture** | "how does", "architecture", "design", "flow" | Code (READMEs, docs/), issues, discussions | "How does authentication work?" |
| **Status/Progress** | "status", "progress", "shipped", "done" | Issues (open/closed), PRs (merged), milestones | "What's the status of the DB migration?" |
| **Process/Policy** | "process", "policy", "how do we", "procedure" | Docs (CONTRIBUTING, ADRs), discussions, issues | "What's our incident response process?" |
| **Historical** | "when did", "history", "changed", "used to" | Issues (closed), PRs (merged), git history | "When did we switch from REST to GraphQL?" |

### Determine Scope

Ask the user for clarification **only if** the scope is truly ambiguous:
- If user mentions an org → use that org
- If user mentions a repo → search that repo directly
- If user mentions a team or service → use it as a search term for repo discovery
- If nothing is mentioned → ask which org to search

## Step 2: Discover Relevant Repos

**Skip this step if the user already provided specific repos.**

When the user only provides an org, discover which repos are most likely to contain the answer using multiple signals in parallel:

1. **Search repos by name/description** — Search the org for repos matching the question's key terms. Run 2-3 variations (e.g., "billing", "payments", "billing service") since each often surfaces unique repos.

2. **Scout issues to infer repos** — Search issues org-wide with keyword search. The repos where matching issues live are likely relevant. This works even for private repos that don't appear in repo search.

3. **Combine and prioritize** — Repos found via both name AND issue matching rank highest. Filter out archived repos. Cap at 5-8 repos to keep the search focused.

If repo discovery yields nothing, try shorter/broader query fragments, ask the user to narrow down, or search the entire org's issues with keyword search.

> **Tip:** Use standard (keyword) search for repo discovery, then use semantic search within the discovered repos for deeper results.

## Step 3: Search Across Surfaces

Search multiple surfaces based on the question type. Run searches in parallel when possible.

### Always read the README first

For **every discovered repo**, read its README.md before doing deeper searches. The README was consistently the single most valuable source in testing — it contains team/DRI info, architecture overviews, links to docs, and related repos. Following links FROM the README is higher-signal than broad search.

### Which surfaces to search per question type

| Question Type | README | Issues | PRs | Code/Docs | Special Files |
|--------------|--------|--------|-----|-----------|---------------|
| Decision/Rationale | ✅ First | ✅ Primary | ✅ Check | ✅ ADR files | docs/adr/, docs/decisions/ |
| Ownership/DRI | ✅ First | ✅ Check | ⬜ Skip | ⬜ Skip | CODEOWNERS, status-updates/ |
| Architecture | ✅ First | ⬜ Skip broad | ✅ Check | ✅ Primary | docs/architecture.md |
| Status/Progress | ✅ First | ✅ Semantic | ✅ Check | ⬜ Skip | status-updates/ |
| Process/Policy | ✅ First | ✅ Check | ⬜ Skip | ✅ Primary | CONTRIBUTING |
| Historical | ✅ First | ✅ Oldest first | ✅ Merged | ⬜ Skip | — |

**Key constraints:**
- Semantic search (`search_type=semantic`) requires `repo:` scoping — does not support `org:` qualifiers. Use keyword search for org-wide discovery, then semantic search within discovered repos.
- Scope issue searches to discovered repos. Broad org-wide searches can return 10,000-60,000 results dominated by noise.
- For architecture questions, skip broad org-wide issue search. Go straight to repo discovery → README → docs/ files.

## Step 4: Dig Into Evidence

Don't stop at search results — read into the most promising hits (top 3-5).

For each hit:
1. Read the full issue/PR body and comments — decisions are often made in comments
2. Check linked issues/PRs — cross-references often lead to the actual decision
3. Check who participated — this may answer ownership questions

### Follow cross-references

This is one of the highest-signal strategies:
- "Closes #123" in a PR → read the linked issue
- "See also #456" or "Superseded by #789" → follow the chain
- README links to `docs/architecture.md` or parent initiatives → follow for context
- Issue bodies embed Slack transcripts → rich context for decisions

> Following internal links was consistently the most productive way to deepen understanding. A single README often links to 3-5 related repos that no search would find.

For historical questions, check the README's milestones/timeline section, list oldest issues, and note when issues were opened/closed and PRs were merged.

## Step 5: Synthesize Answer

Present your findings in this structure:

```
**Answer:** [1-3 sentence direct answer to the question]

**Evidence:**
- [Issue/PR title](URL) — [Brief summary of what this tells us]
- [Issue/PR title](URL) — [Brief summary]
- [File name](URL) — [What this document explains]

**Context:** [Any additional nuance, timeline, or caveats]

**Confidence:** [High/Medium/Low] — [Why this confidence level]

**Follow-up suggestions:**
- [Suggested question to dig deeper]
- [Related area to explore]
```

### Confidence Levels

- **High** — Found direct, explicit evidence (e.g., a decision record, an RFC, a clear comment)
- **Medium** — Found related evidence that implies the answer but isn't explicit
- **Low** — Found tangential evidence; the answer is an inference

### When Evidence Is Insufficient

If you cannot find a clear answer, report what you searched, the closest results you found, and suggest next steps: relevant Slack channels (from CODEOWNERS/team files), people who worked on related topics, or a refined question to try.

This is a **read-only search skill** — never modify content, and always present evidence for the user to evaluate rather than making definitive claims without sources.
