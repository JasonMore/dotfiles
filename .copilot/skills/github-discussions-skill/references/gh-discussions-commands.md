# gh-discussions Command Reference

Quick reference for the gh-discussions CLI extension.

## Installation

```bash
gh extension install github/gh-discussions
```

**Repository:** https://github.com/github/gh-discussions

## Commands Overview

| Command | Purpose |
|---------|---------|
| `list` | List all discussions in a repository |
| `show` | Display a specific discussion |
| `create` | Create a new discussion |
| `edit` | Edit a discussion title |
| `close` | Close a discussion |
| `comments` | Show comments on a discussion |

## Command Details

### list

List discussions in a repository.

```bash
gh discussions list [flags]

Flags:
  -c, --category string     Filter by category name
  -p, --page int            Page number (default: 1)
  -R, --repository string   Repository (owner/name)
```

**Examples:**
```bash
# List all discussions
gh discussions list -R github/agent-skills

# Filter by category
gh discussions list -R github/agent-skills -c "Show and tell"

# Second page
gh discussions list -R github/agent-skills -p 2
```

### show

Display full details of a discussion.

```bash
gh discussions show <number> [flags]

Flags:
  -R, --repository string   Repository (owner/name)
```

**Examples:**
```bash
# Show discussion #5
gh discussions show 5 -R github/agent-skills
```

**Output includes:**
- Title
- Author
- Creation date
- Body content
- Category
- Status
- URL

### create

Create a new discussion.

```bash
gh discussions create [flags]

Flags:
  -c, --category string     Category name (required)
  -t, --title string        Title (required)
  -R, --repository string   Repository (owner/name)
```

**Body input:** Reads from stdin or opens editor

**Examples:**
```bash
# Interactive (opens editor)
gh discussions create -R github/agent-skills \
  -c "Show and tell" \
  -t "New Feature"

# With piped content
echo "Check this out!" | gh discussions create \
  -R github/agent-skills \
  -c "Show and tell" \
  -t "New Feature"

# From file
gh discussions create -R github/agent-skills \
  -c "Q&A" \
  -t "Question" < body.txt
```

### edit

Edit a discussion's title.

```bash
gh discussions edit <number> [flags]

Flags:
  -t, --title string        New title
  -R, --repository string   Repository (owner/name)
```

**Examples:**
```bash
# Update title
gh discussions edit 5 -R github/agent-skills \
  -t "Updated Title"
```

**Note:** Body editing requires interactive editor session.

### close

Close a discussion.

```bash
gh discussions close <number> [flags]

Flags:
  -R, --repository string   Repository (owner/name)
```

**Examples:**
```bash
# Close discussion #5
gh discussions close 5 -R github/agent-skills
```

### comments

Show comments on a discussion.

```bash
gh discussions comments <number> [flags]

Flags:
  -R, --repository string   Repository (owner/name)
```

**Examples:**
```bash
# Show all comments
gh discussions comments 5 -R github/agent-skills
```

**Output includes:**
- Comment author
- Timestamp
- Comment body
- Comment ID

## Common Categories

Standard GitHub Discussions categories:

- **Show and tell** - Showcases, demos, announcements
- **Q&A** - Questions and support
- **Ideas** - Feature requests and suggestions
- **General** - General discussions
- **Announcements** - Important updates

**Note:** Available categories depend on repository configuration.

## Global Flags

Available on all commands:

```bash
-d, --debug     Show debug output
-h, --help      Show help
-v, --version   Show version
```

## Tips

### Repository Shorthand

If working in a cloned repository:

```bash
# Auto-detect current repo
gh discussions list
```

Without `-R` flag, uses current repository context.

### Pagination

Large repositories may require pagination:

```bash
gh discussions list -R github/agent-skills -p 1
gh discussions list -R github/agent-skills -p 2
gh discussions list -R github/agent-skills -p 3
```

### Category Names

Category names are case-sensitive and must match exactly:

```bash
# ✅ Correct
gh discussions list -c "Show and tell"

# ❌ Wrong
gh discussions list -c "show and tell"
gh discussions list -c "Show And Tell"
```

### Body Content Formatting

Use markdown in discussion bodies:

```bash
cat << 'EOF' | gh discussions create -R repo -c "General" -t "Title"
# Heading

**Bold** and *italic* text

- Bullet points
- More bullets

\`\`\`bash
code blocks
\`\`\`
EOF
```

## Limitations

**Current gaps:**
- No native comment creation (must use API)
- No search/filter beyond category
- No label management
- No reaction handling
- Limited editing (title only via CLI)

**Workarounds:**
- Use `gh api` for advanced operations
- Combine with GitHub GraphQL API
- Use web interface for complex tasks

## Further Reading

- [gh-discussions GitHub Repository](https://github.com/github/gh-discussions)
- [GitHub Discussions Documentation](https://docs.github.com/en/discussions)
- [GitHub CLI Manual](https://cli.github.com/manual/)
