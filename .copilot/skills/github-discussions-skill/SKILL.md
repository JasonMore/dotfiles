---
name: github-discussions
description: This skill should be used when the user asks to "create a discussion", "list discussions", "show discussion", "comment on discussion", "close discussion", "find discussions about", "browse discussions", or needs to interact with GitHub Discussions using the gh-discussions CLI extension.
---

# GitHub Discussions - Command Line Discussion Management

Interact with GitHub Discussions efficiently using the `gh discussions` CLI extension for browsing, creating, reading, commenting, and managing discussions.

## When to Use This Skill

**Trigger phrases:**
- "Create a discussion about [topic]"
- "List discussions in [repo]"
- "Show me discussion #[number]"
- "Comment on discussion [number]"
- "Close discussion [number]"
- "Find discussions about [topic]"
- "Browse discussions"

**Appropriate use cases:**
- Announcements of new features or updates
- Q&A and support questions
- Gathering feedback or ideas
- Team discussions and decisions
- Show and tell posts
- General community engagement

## Prerequisites Check

Before using, verify the gh-discussions extension is installed:

```bash
if ! gh extension list | grep -q "gh-discussions"; then
    echo "❌ gh-discussions extension not installed"
    echo "Install with: gh extension install github/gh-discussions"
    exit 1
fi
```

## Core Commands

### 1. List Discussions

**Command:**
```bash
gh discussions list [flags]
```

**Common flags:**
- `-R, --repository owner/repo` - Specify repository
- `-c, --category "name"` - Filter by category
- `-p, --page N` - Page number for pagination

**Usage examples:**
```bash
# List all discussions
gh discussions list -R github/agent-skills

# Filter by category
gh discussions list -R github/agent-skills -c "Show and tell"

# Browse page 2
gh discussions list -R github/agent-skills -p 2
```

**Output format:**
The command returns a list with discussion numbers, titles, authors, and metadata.

**When to use:**
- User wants to browse discussions
- Looking for existing discussions on a topic
- Need to get a discussion number for other operations

### 2. Show Discussion Details

**Command:**
```bash
gh discussions show <number> [flags]
```

**Flags:**
- `-R, --repository owner/repo` - Specify repository

**Usage:**
```bash
# View discussion #5
gh discussions show 5 -R github/agent-skills
```

**Output includes:**
- Discussion title
- Author and creation date
- Full body content
- Category
- Status (open/closed)
- URL

**When to use:**
- User asks to see specific discussion
- Need to read full content before commenting
- Checking discussion status

### 3. Create Discussion

**Command:**
```bash
gh discussions create [flags]
```

**Required flags:**
- `-t, --title "Title"` - Discussion title
- `-c, --category "Category"` - Discussion category
- `-R, --repository owner/repo` - Target repository

**Body input:**
The command opens an editor for body content unless piped.

**Usage:**
```bash
# Interactive (opens editor)
gh discussions create -R github/agent-skills -c "Show and tell" -t "New Skill Available"

# With piped content
echo "Check out the new watch-ci skill!" | gh discussions create -R github/agent-skills -c "Show and tell" -t "New Skill: Watch CI"

# From file
gh discussions create -R github/agent-skills -c "Q&A" -t "Question about skills" < body.txt
```

**Common categories:**
- "Show and tell"
- "Q&A"
- "Ideas"
- "General"
- "Announcements"

**Process:**
1. Determine appropriate category
2. Craft clear, descriptive title
3. Prepare body content (can use markdown)
4. Execute create command
5. Capture discussion number/URL from output

### 4. View Comments

**Command:**
```bash
gh discussions comments <number> [flags]
```

**Flags:**
- `-R, --repository owner/repo` - Specify repository

**Usage:**
```bash
# Show all comments on discussion #5
gh discussions comments 5 -R github/agent-skills
```

**Output includes:**
- Comment author
- Timestamp
- Comment body
- Comment ID (for replies)

**When to use:**
- Reading discussion thread
- Before adding a comment
- Summarizing discussion feedback

### 5. Edit Discussion

**Command:**
```bash
gh discussions edit <number> [flags]
```

**Flags:**
- `-t, --title "New Title"` - Update title
- `-R, --repository owner/repo` - Specify repository

**Usage:**
```bash
# Update title
gh discussions edit 5 -R github/agent-skills -t "Updated Title"
```

**Note:** Body editing requires interactive editor

### 6. Close Discussion

**Command:**
```bash
gh discussions close <number> [flags]
```

**Flags:**
- `-R, --repository owner/repo` - Specify repository

**Usage:**
```bash
# Close discussion #5
gh discussions close 5 -R github/agent-skills
```

**When to use:**
- Discussion is resolved
- Topic is no longer relevant
- Consolidating duplicate discussions

## Common Workflows

### Workflow 1: Create Announcement

```bash
# Step 1: Prepare content
TITLE="New Agent Skill: Watch CI"
BODY=$(cat << 'EOF'
We've added a new skill for monitoring CI pipelines!

## Features
- Background monitoring
- Notifications on status change
- Auto-merge on success

## Install
\`\`\`bash
gh hubber-skills install watch-ci-skill
\`\`\`
EOF
)

# Step 2: Create discussion
echo "$BODY" | gh discussions create \
  -R github/agent-skills \
  -c "Show and tell" \
  -t "$TITLE"

# Step 3: Capture and share URL
# Output will include discussion URL
```

### Workflow 2: Browse and Comment

```bash
# Step 1: List discussions in category
gh discussions list -R github/agent-skills -c "Q&A"

# Step 2: Read specific discussion
gh discussions show 5 -R github/agent-skills

# Step 3: View existing comments
gh discussions comments 5 -R github/agent-skills

# Step 4: Add comment (opens editor)
# Note: commenting requires interactive input or API
```

### Workflow 3: Find and Close Resolved

```bash
# Step 1: List discussions
gh discussions list -R github/agent-skills

# Step 2: Check if resolved
gh discussions show 3 -R github/agent-skills

# Step 3: Close if resolved
gh discussions close 3 -R github/agent-skills
```

## Repository Detection

When user doesn't specify repository:

```bash
# Try to detect current repo
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)

if [ -n "$REPO" ]; then
    echo "Using current repository: $REPO"
    gh discussions list -R "$REPO"
else
    echo "Please specify repository with -R owner/repo"
fi
```

## Output Formatting

### Parse List Output

List command returns text format. Common parsing:

```bash
# Get discussion numbers
gh discussions list -R github/agent-skills | grep -oP '^\s*\K\d+'

# Extract titles
gh discussions list -R github/agent-skills | awk '{print $2}'
```

### Format for Display

```bash
# Pretty print discussion
gh discussions show 5 -R github/agent-skills | sed 's/^/  /'
```

## Error Handling

### Extension Not Installed

```bash
if ! command -v gh-discussions &> /dev/null; then
    echo "❌ gh-discussions extension not found"
    echo ""
    echo "Install with:"
    echo "  gh extension install github/gh-discussions"
    exit 1
fi
```

### Repository Not Found

```bash
if ! gh discussions list -R github/nonexistent 2>&1; then
    echo "❌ Repository not found or no access"
    echo "Check repository name and permissions"
    exit 1
fi
```

### Discussion Not Found

```bash
if ! gh discussions show 999 -R github/agent-skills 2>&1; then
    echo "❌ Discussion #999 not found"
    echo "List discussions: gh discussions list -R github/agent-skills"
    exit 1
fi
```

## Integration Patterns

### With Labels

After creating discussion, add labels via API:

```bash
DISCUSSION_NUM=$(gh discussions create ... | grep -oP '/#\K\d+')
gh api graphql -f query="..."  # Use GraphQL to add labels
```

### With Workflows

Discussions can trigger workflows via:
- `discussion` event
- `discussion_comment` event

### With Notifications

Monitor discussions:
```bash
# Watch for new discussions
gh discussions list -R github/agent-skills | tee /tmp/discussions.txt
```

## Best Practices

### Title Guidelines

**Good titles:**
- "New Skill: GitHub Discussions Management"
- "Question: How to update skills?"
- "Idea: Skill versioning system"

**Poor titles:**
- "Help" (too vague)
- "Skill" (not descriptive)
- "????????" (unclear)

### Body Content

- Use markdown for formatting
- Include clear sections
- Add code blocks with syntax highlighting
- Link to relevant resources
- Use bullet points for readability

### Category Selection

| Category | Use For |
|----------|---------|
| Show and tell | Announcements, demos, showcases |
| Q&A | Questions, support requests |
| Ideas | Feature requests, suggestions |
| General | Everything else |
| Announcements | Important updates (if available) |

### Comment Etiquette

- Read existing comments first
- Stay on topic
- Be constructive and helpful
- Use @mentions for responses
- Edit instead of multiple comments

## Limitations

**Current limitations:**
- No native comment creation in CLI (requires API or interactive)
- No search functionality (use `list` and grep)
- No reaction/emoji support
- No pin/lock operations
- Limited edit capabilities

**Workarounds:**
- Use GitHub API for advanced operations
- Combine with `gh api` for missing features
- Use web interface for complex edits

## Quick Reference

**Browse:**
```bash
gh discussions list -R owner/repo
gh discussions list -R owner/repo -c "Category"
```

**Read:**
```bash
gh discussions show <number> -R owner/repo
gh discussions comments <number> -R owner/repo
```

**Create:**
```bash
echo "body" | gh discussions create -R owner/repo -c "Category" -t "Title"
```

**Manage:**
```bash
gh discussions edit <number> -R owner/repo -t "New Title"
gh discussions close <number> -R owner/repo
```

**Check status:**
```bash
gh extension list | grep discussions
gh discussions --version
```
