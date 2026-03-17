# Update Status Skill

Draft high-signal weekly tracking issue updates in GitHub's expected format using current project context.

## When to Use This Skill

- You need to post a weekly status update on a tracking issue
- You want a concise summary of current progress, risks, and next milestones
- You need updates aligned to GitHub How We Work and Howie report formatting
- You want milestone-aware updates (staff ship, Public Preview, GA)

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Access to the target tracking repository and related linked artifacts

## Installation

### Using gh-hubber-skills (Recommended)

```bash
gh extension install github/gh-hubber-skills
gh hubber-skills install update-status-skill
```

### Manual Installation

```bash
cp -r update-status-skill ~/.copilot/skills/
```

## Usage

This skill activates when you ask Copilot to:
- "Write a weekly update for this tracking issue"
- "Update status on issue #1234"
- "Summarize project progress for this epic issue"
- "Draft a Howie-style status update"

The skill will:
1. Read the tracking issue and recent report comments
2. Gather context from linked issues/PRs/docs
3. Identify upcoming ship points (staff ship, Public Preview, GA)
4. Produce a concise update draft in expected format
5. Ask for confirmation before posting

## Features

- **Howie-compatible format** - Uses `Trending`, `Target date`, `Update`, and `Summary` sections with data markers
- **Context gathering** - Pulls status from linked issues and PRs instead of guessing
- **Milestone framing** - Focuses on next meaningful ship points and dependencies
- **Concise writing** - Produces a human-readable update tuned for async review

## Examples

See [`examples/basic-usage.md`](./examples/basic-usage.md) for an end-to-end flow.
