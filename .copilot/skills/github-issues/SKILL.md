---
name: github-issues
description: Fetch GitHub issues and pull requests using the gh CLI, not browser navigation
license: MIT
author: JasonMore
tags: [github, gh, cli, issues, pull-requests]
version: 1.0.0
---

# Fetch GitHub Issues and Pull Requests

When you need to read a GitHub issue or pull request, always use the `gh` CLI. Never navigate to a GitHub URL - URL navigation does not work in a codespace environment and will return a 404.

## Rules

- **Never** use web fetch or URL navigation to read GitHub issues or pull requests.
- **Always** use `gh issue view` or `gh pr view` to fetch issue and PR details.

## Fetching an Issue

```bash
# View an issue in the current repo
gh issue view <number>

# View an issue in a specific repo
gh issue view <number> -R <owner>/<repo>

# View with full body and comments
gh issue view <number> -R <owner>/<repo> --comments

# Fetch structured JSON data
gh issue view <number> -R <owner>/<repo> --json title,body,comments
```

## Fetching a Pull Request

```bash
# View a PR in the current repo
gh pr view <number>

# View a PR in a specific repo
gh pr view <number> -R <owner>/<repo>

# Fetch structured JSON data
gh pr view <number> -R <owner>/<repo> --json title,body,comments
```

## Example

Given a reference to `https://github.com/github/web-systems/issues/4750`, run:

```bash
gh issue view 4750 -R github/web-systems --json title,body
```
