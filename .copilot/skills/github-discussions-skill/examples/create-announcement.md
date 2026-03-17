# Example: Creating an Announcement

Create a discussion to announce a new skill in the repository.

## Scenario

You've just added a new skill to the agent-skills repository and want to announce it to Hubbers.

## User Request

> "Create a discussion announcing the new github-discussions skill"

## Agent Response - Step 1: Prepare Content

```
I'll create an announcement in the agent-skills repository.

Preparing discussion:
• Title: "New Skill: GitHub Discussions Management 🎉"
• Category: "Show and tell"
• Repository: github/agent-skills
```

## Agent Response - Step 2: Format Body

```markdown
We've added a new skill for managing GitHub Discussions from the command line!

## What It Does

The **github-discussions-skill** helps you:
- 📋 List and browse discussions
- ✨ Create discussions with proper formatting
- 💬 Read discussions and comments
- 🔧 Manage discussion status
- 🔍 Find discussions by category

## Prerequisites

Install the gh-discussions extension:
\`\`\`bash
gh extension install github/gh-discussions
\`\`\`

## Quick Install

\`\`\`bash
gh hubber-skills install github-discussions-skill
\`\`\`

## Use Cases

- Creating announcements
- Q&A workflows
- Gathering feedback
- Team discussions
- Show and tell posts

Check out the full documentation: [github-discussions-skill](./github-discussions-skill/)

---

Have questions or feedback? Comment below! 💬
```

## Agent Response - Step 3: Execute

```bash
Creating discussion...

Command:
gh discussions create \
  -R github/agent-skills \
  -c "Show and tell" \
  -t "New Skill: GitHub Discussions Management 🎉"

✅ Discussion created!
📝 Discussion #6
🔗 https://github.com/github/agent-skills/discussions/6
```

## Agent Response - Step 4: Follow Up

```
Discussion successfully created!

Next steps:
• Share the link with your team
• Monitor comments for questions
• Consider adding the eng-show-and-tell label for roundup inclusion

Would you like me to:
1. Add a label to the discussion?
2. Create a summary of the skill features?
3. Draft a Slack message to share?
```

## Key Points

- Clear, descriptive title with emoji
- Well-formatted body with sections
- Code blocks for installation commands
- Links to documentation
- Call-to-action for engagement
- Professional but friendly tone

## Variations

### For Q&A
```bash
gh discussions create \
  -R github/agent-skills \
  -c "Q&A" \
  -t "How do I update an installed skill?"
```

### For Ideas
```bash
gh discussions create \
  -R github/agent-skills \
  -c "Ideas" \
  -t "Idea: Skill dependency management"
```
