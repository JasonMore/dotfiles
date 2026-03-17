# Example: Repairing an Outdated CLI Command

## Scenario

The user is using the `watch-ci-skill` and encounters an error because the skill requires a `gh` CLI version that isn't documented as a prerequisite.

## User Request

> "The watch-ci skill isn't working. When it tries to list workflow runs, I get 'unknown flag: --json status' — can you fix it?"

## Agent Diagnosis

### Step 1: Identify the Skill

- **Skill**: `watch-ci-skill`
- **What they tried**: Watching CI for a PR
- **What happened**: `unknown flag: --json status` error
- **What they expected**: Workflow runs listed and monitored

### Step 2: Inspect the Skill

The agent fetches `watch-ci-skill/SKILL.md` and finds:

```bash
gh run list --workflow ci.yml --json status,conclusion,headBranch
```

### Step 3: Reproduce

The agent checks the user's `gh` version and runs the command:
```bash
gh --version
# gh version 1.14.0 (2021-05-25)

gh run list --workflow ci.yml --json status,conclusion,headBranch
# unknown flag: --json status
```

Then tests on a newer version to confirm the command itself is valid:
```bash
gh --version
# gh version 2.45.0 (2024-03-01)

gh run list --workflow ci.yml --json status,conclusion,headBranch
# Works — the command is correct, but requires gh 2.x+
```

### Step 4: Diagnose

**Category**: Missing prerequisite
**Root Cause**: The skill uses `gh run list --json` which requires `gh` CLI v2.0+, but doesn't document this minimum version requirement. Users with `gh` v1.x see an "unknown flag" error.

### Step 5: Propose Fix

Add a prerequisites section to SKILL.md noting the minimum `gh` CLI version, and add a version check before running commands:

```markdown
## Prerequisites
- `gh` CLI version 2.0 or later (`gh --version` to check)
```

### Step 6: Open Issue + PR

The agent asks the user: "I found the problem — the skill doesn't document that it requires gh CLI v2+. Want me to open an issue and PR to fix this?"

User confirms, and the agent opens:
- **Issue**: "Bug: watch-ci-skill — no minimum gh CLI version documented"
- **PR**: "Fix: watch-ci-skill — add prerequisite version check" (closes the issue)
