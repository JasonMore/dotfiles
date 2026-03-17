# GitHub Discussions Skill

Work with GitHub Discussions using the command line - list, create, read, comment, and manage discussions efficiently.

## Prerequisites

### Install gh-discussions extension

```bash
gh extension install github/gh-discussions
```

### Verify installation

```bash
gh discussions --help
```

## When to Use This Skill

- Creating discussions for announcements, Q&A, or ideas
- Reading and browsing existing discussions
- Commenting on discussions
- Managing discussion status (close, edit)
- Searching for specific topics
- Automating discussion workflows

## Installation

### Personal Skills
```bash
gh hubber-skills install github-discussions-skill
```

### Project Skills
```bash
gh hubber-skills install github-discussions-skill --project
```

## Usage

This skill activates when you ask Copilot to:
- "Create a discussion about [topic]"
- "List discussions in [repo]"
- "Show me discussion #123"
- "Comment on discussion [number]"
- "Close discussion [number]"
- "Find discussions about [topic]"

The skill will:
1. Use `gh discussions` commands to interact with GitHub
2. Format output in readable ways
3. Suggest next actions based on context
4. Handle common workflows efficiently

## Features

- **List discussions** - Browse by category, page, or filter
- **Create discussions** - With title, body, and category
- **Read discussions** - View full content and comments
- **Comment** - Add responses to discussions
- **Manage** - Edit, close, or update discussions
- **Search** - Find relevant discussions by topic

## Examples

### Browse discussions
```bash
# User: "List discussions in github/agent-skills"
# Agent uses: gh discussions list -R github/agent-skills
```

### Create announcement
```bash
# User: "Create a discussion announcing the new watch-ci skill"
# Agent uses: gh discussions create -R github/agent-skills -c "Show and tell" -t "New Skill: Watch CI"
```

### Read and comment
```bash
# User: "Show me discussion #5 and add a comment"
# Agent uses: gh discussions show 5 && gh discussions comments add 5
```

## Common Workflows

### Announcement Flow
1. List categories to pick the right one
2. Create discussion with title and body
3. Confirm creation and share link

### Q&A Flow
1. Search existing discussions first
2. If no match, create new discussion in Q&A category
3. Monitor for responses

### Feedback Collection
1. Create discussion for feedback
2. Watch for comments
3. Summarize feedback from comments

---

**Required:** GitHub CLI with [`gh-discussions`](https://github.com/github/gh-discussions) extension installed
