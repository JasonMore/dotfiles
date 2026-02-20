---
name: github-issues
description: Instructs Copilot to use the gh CLI when accessing GitHub issues, not browser navigation.
---

## Purpose

You ensure GitHub issues and pull requests are accessed using the `gh` CLI, not by navigating to URLs in a browser.

## Rules

- **Never navigate to a GitHub URL to load an issue or pull request.**
- Always use the `gh` CLI to fetch issue and pull request details.

## Examples

Incorrect:
> Navigate to `https://github.com/owner/repo/issues/123` to read the issue.

Correct:
> Run `gh issue view 123` to read the issue.

## Common gh CLI Commands

- View an issue: `gh issue view <number>`
- List issues: `gh issue list`
- View a pull request: `gh pr view <number>`
- List pull requests: `gh pr list`
- View issue comments: `gh issue view <number> --comments`
