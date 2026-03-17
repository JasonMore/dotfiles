# Skill Repair

A meta-skill that detects when skills from the `github/agent-skills` repo aren't working as expected, diagnoses the problem, and opens issues or PRs to fix them.

## When to Use This Skill

- A skill you're using produces errors or unexpected output
- A skill's CLI commands are outdated or broken
- A skill is missing dependencies or tools it expects
- You want to report a bug in a skill back to the repo
- You want to propose a fix for a broken skill

## Features

- **Diagnose**: Identifies why a skill failed — bad instructions, missing tools, outdated commands, incorrect logic
- **Report**: Opens a well-structured issue in `github/agent-skills` with reproduction steps and diagnostic context
- **Repair**: Cuts a PR with a targeted fix when the root cause is clear
- **Validate**: Checks the proposed fix against the skill's documented examples

## Installation

```bash
gh extension install github/gh-hubber-skills
gh hubber-skills install skill-repair-skill
```

Or to install as a project-level skill:

```bash
gh hubber-skills install skill-repair-skill --project
```

## Usage

When a skill isn't working as expected, tell the agent:

- "this skill isn't working"
- "report a bug in this skill"
- "fix this skill"
- "this skill is broken"
- "file a skill issue"
- "repair this skill"

The agent will walk through diagnosis, then offer to open an issue, a PR, or both.

## Examples

See the [examples/](examples/) directory for detailed scenarios.
