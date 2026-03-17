---
description: This skill should be used when the user asks to "write a weekly update", "update status on this tracking issue", "draft a Howie status update", "summarize progress for issue", or needs a concise tracking issue update with ship-point framing (staff ship, public preview, GA).
metadata:
    github-owner: github
    github-path: update-status-skill
    github-ref: main
    github-repo: agent-skills
    github-sha: c979087362ff01325f63be6e63bf9f89289645eb
    github-tree-sha: 5638128c60b6ea3253dcb26f82d7235ad83ed953
name: update-status
---
# Update Status - Weekly Tracking Issue Updates

Produce concise, context-grounded weekly updates for GitHub tracking issues using expected report structure.

## When to Use This Skill

- Updating Initiative or Epic tracking issues on a weekly cadence
- Converting scattered progress into a single issue update
- Communicating risk/trend changes and target date confidence
- Framing progress by next ship points (staff ship, Public Preview, GA)

## Process

### 1) Validate target issue and report style

Confirm the issue exists and inspect recent comments for existing report format.

```bash
gh issue view ISSUE_NUMBER --repo OWNER/REPO --json title,url,body,comments
```

If prior report comments contain markers like `howieReportName`, keep using the same style.

### 2) Gather current context from linked materials

Collect links from issue body and recent status comments, then inspect each linked artifact.

```bash
gh issue view ISSUE_NUMBER --repo OWNER/REPO --json body,comments \
  --jq '.body, (.comments[].body // "")' \
  | grep -Eo 'https://github\\.com/[^ )]+' \
  | sort -u
```

For each relevant link:
- Issue links: read state, assignee, updated-at, and newest comments
- PR links: read state, check status, merge state, and blocking feedback
- Release links (if present): read release phase and expected ship timing

### 3) Derive trend, milestones, and narrative

Synthesize facts into four decisions:

1. **Trending** (on track / at risk / off track / done)
2. **Target date** (keep, move, or unknown)
3. **Update** (what changed this week, blockers, next actions)
4. **Summary** (one tight paragraph)

Always include near-term milestone framing:
- What must happen before **staff ship**
- What remains before **Public Preview**
- What remains before **GA**

If one milestone is not relevant, say so explicitly instead of omitting it silently.

### 4) Draft in expected issue comment format

Use this template for short weekly reports:

```markdown
### Trending

<!-- data key="trending" start -->
🟢 on track
<!-- data end -->

### Target date

<!-- data key="target_date" start -->
YYYY-MM-DD
<!-- data end -->

### Update

<!-- data key="update" start -->
[Concise update paragraph(s), including milestone framing]
<!-- data end -->

### Summary

<!-- data key="summary" start -->
[One-paragraph summary]
<!-- data end -->

<!-- data key="isReport" value="true" -->
<!-- data key="howieReportName" value="short" -->
```

### 5) Confirm before posting

Never post automatically. Show the draft and ask for approval first.

If approved:

```bash
gh issue comment ISSUE_NUMBER --repo OWNER/REPO --body-file /tmp/status-update.md
```

## Writing Guidelines

- Lead with changes since the last report
- Name blockers and owners directly
- Avoid vague language ("making progress", "in flight") without specifics
- Keep update focused on next decision points and ship points
- Prefer short paragraphs and bullets over long prose

## Error Handling

### Missing or inaccessible issue
- **Symptom:** `gh issue view` fails
- **Fix:** verify repo/issue number and GitHub auth before continuing

### Weak evidence for trend
- **Symptom:** conflicting signals (many open blockers, but no concrete delivery risk called out)
- **Fix:** mark as at risk, explain uncertainty, and request missing data

### No clear milestone mapping
- **Symptom:** unclear relation to staff ship/Public Preview/GA
- **Fix:** include a "milestone assumptions" line and ask user to confirm

## Boundaries

**Will:**
- Draft concise weekly updates in expected format
- Ground statements in linked artifact evidence
- Frame next steps around ship points

**Will Not:**
- Post updates without explicit confirmation
- Invent dates, progress, or milestones
- Replace formal release management workflows

## Effectiveness Check: Skill vs Agent

This is a strong **skill** because the workflow is repeatable, format-sensitive, and benefits from clear structure and guardrails.

Consider escalating to a dedicated **agent** if you need always-on monitoring, cross-repo background polling, or automatic posting/alerts without human prompts.
