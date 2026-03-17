---
description: This skill should be used when the user says "this skill isn't working", "report a bug in this skill", "fix this skill", "this skill is broken", "file a skill issue", "repair this skill", or when a skill from the agent-skills repo produces errors or unexpected output and the user wants to diagnose and fix it.
metadata:
    github-owner: github
    github-path: skill-repair-skill
    github-ref: main
    github-repo: agent-skills
    github-sha: def55b52d8c6c1222e1f079734a5c3e5575605ca
    github-tree-sha: 8a5765b08c52dc289b456df0fdcbcea90f587ac8
name: skill-repair
---
# Skill Repair

You are a meta-skill that diagnoses broken skills from the `github/agent-skills` repository and opens issues or PRs to fix them.

## When to Use

- A user reports that a skill isn't working as expected
- A skill produces errors, unexpected output, or fails silently
- A skill references outdated CLI commands, missing tools, or incorrect syntax
- The user explicitly asks to report a bug or fix a skill

## Diagnostic Process

When the user reports a skill problem, follow these steps in order:

### Step 1: Identify the Broken Skill

Ask the user which skill is having problems. If it's obvious from context (e.g., they just used it), confirm your understanding.

Gather:
- **Skill name**: The directory name (e.g., `watch-ci-skill`, `chatops-skill`)
- **What they tried**: The trigger phrase or action that failed
- **What happened**: Error messages, unexpected output, or silent failure
- **What they expected**: The correct behavior

### Step 2: Retrieve and Inspect the Skill

Fetch the skill's source files from `github/agent-skills` on the `main` branch:

```bash
gh api repos/github/agent-skills/contents/{skill-name}/SKILL.md --jq '.content' | base64 -d
gh api repos/github/agent-skills/contents/{skill-name}/README.md --jq '.content' | base64 -d
```

Check for common problems:
- **Outdated commands**: CLI flags or tools that no longer exist
- **Missing dependencies**: Tools the skill assumes are available but aren't
- **Incorrect trigger phrases**: Frontmatter description doesn't match actual use cases
- **Logic errors**: Steps that produce wrong results or are in the wrong order
- **Missing error handling**: No guidance for when things go wrong
- **Stale references**: Links, APIs, or patterns that have changed

### Step 3: Reproduce the Problem

Try to reproduce the failure by following the skill's instructions exactly as written. Document:
- The exact step that fails
- The error message or incorrect output
- The environment context (OS, tools available, versions)

### Step 4: Diagnose the Root Cause

Classify the problem:

| Category | Description | Example |
|----------|-------------|---------|
| **Outdated command** | CLI syntax has changed | `gh pr create --json` flag doesn't exist |
| **Missing dependency** | Tool not available | Skill assumes `jq` is installed |
| **Bad instructions** | Steps are wrong or incomplete | Skill says to run X but should run Y |
| **Trigger mismatch** | Frontmatter doesn't match use cases | Description says "create" but skill handles "update" |
| **Missing error handling** | No recovery path for common failures | Skill doesn't handle API rate limits |
| **Scope creep** | Skill tries to do too much | Overlaps with another skill's responsibility |

### Step 5: Propose a Fix

Based on the diagnosis, decide the appropriate action:

- **Clear fix available** → Open a PR with the fix
- **Problem identified but fix unclear** → Open an issue with detailed diagnosis
- **Multiple possible approaches** → Open an issue describing options, let maintainers decide

Always ask the user before opening anything.

## Opening an Issue

Use this format:

```bash
gh issue create --repo github/agent-skills \
  --title "Bug: {skill-name} — {brief description}" \
  --label "bug" \
  --body "## Skill
{skill-name}

## Problem
{What the user tried and what went wrong}

## Expected Behavior
{What should have happened}

## Root Cause
{Your diagnosis of why it's broken}

## Reproduction Steps
1. {Step 1}
2. {Step 2}
3. {Step 3}

## Environment
- OS: {detected OS}
- Relevant tools: {versions of tools involved}

## Suggested Fix
{If you have a proposed fix, describe it here}
"
```

## Opening a PR

When the fix is clear:

1. **Create a branch** directly in `github/agent-skills` (do not fork):
   ```bash
   # Slugify the description: lowercase, spaces to hyphens, strip special chars
   BRANCH_NAME="fix/$(echo '{skill-name}-{brief-description}' | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')"
   git checkout -b "$BRANCH_NAME" main
   ```

2. **Make the fix**: Edit only the files that need to change (usually `SKILL.md`, sometimes `README.md`)

3. **Validate**: Re-read the fixed skill and mentally walk through the steps. Verify:
   - Commands are syntactically correct
   - Referenced tools exist and flags are valid
   - Steps are in logical order
   - Error handling covers the failure case that was reported

4. **Open the PR**:
   ```bash
   gh pr create --repo github/agent-skills \
     --title "Fix: {skill-name} — {brief description}" \
     --body "Closes #{issue-number}

   ## Problem
   {Brief description of what was broken}

   ## Fix
   {What was changed and why}

   ## Validation
   {How the fix was verified}
   "
   ```

## What This Skill Will NOT Do

- **Proactively monitor skills** — this is reactive, triggered by the user reporting a problem
- **Fix infrastructure issues** — CI, deployment, or repo configuration problems are out of scope
- **Modify skills unprompted** — always asks the user before making changes or opening issues/PRs
- **Rewrite entire skills** — fixes should be surgical and targeted

## Output Format

After diagnosis, present findings to the user:

```
## Diagnosis: {skill-name}

**Problem**: {one-sentence summary}
**Category**: {Outdated command | Missing dependency | Bad instructions | ...}
**Root Cause**: {detailed explanation}
**Suggested Fix**: {what needs to change}

**Next steps**:
- [ ] Open an issue in github/agent-skills
- [ ] Open a PR with the fix
- [ ] Both (issue for tracking + PR for fix)
```

## Examples

### Example 1: Outdated CLI Command

**User**: "The watch-ci skill isn't working — it says 'unknown flag' when trying to list workflow runs"

**Agent response**:
1. Fetch `watch-ci-skill/SKILL.md` from the repo
2. Find the command using the deprecated flag
3. Check current `gh` CLI docs for the correct syntax
4. Present diagnosis and offer to open an issue/PR

### Example 2: Missing Error Handling

**User**: "The slack-context skill crashes when the Slack link is expired"

**Agent response**:
1. Fetch `slack-context-skill/SKILL.md`
2. Look for error handling around link fetching
3. Identify that there's no handling for expired/invalid links
4. Propose adding a validation step and error message
5. Offer to open an issue/PR

### Example 3: Trigger Phrase Mismatch

**User**: "I said 'help me fix this issue' but the skill-repair skill didn't activate"

**Agent response**:
1. Check frontmatter description for trigger phrases
2. Note that "help me fix this issue" isn't listed
3. Propose adding the missing trigger phrase
4. Offer to open a PR with the updated frontmatter
