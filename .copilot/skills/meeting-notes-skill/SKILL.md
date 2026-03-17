---
name: meeting-notes
description: This skill should be used when the user asks to "summarize my meeting", "update my one-on-one notes", "process today's meeting transcript", "format meeting notes", "add meeting summary", "update 1:1 notes", "summarize transcript", or needs to find today's meeting transcripts and insert formatted summaries into their one-on-one note files.
---

# Meeting Notes - One-on-One Transcript Summarizer

Finds today's meeting transcripts, summarizes them, and inserts formatted summaries into the correct one-on-one note files in the Obsidian vault.

## When to Use This Skill

- User wants to process meeting transcripts from today
- User asks to update their one-on-one notes with a meeting summary
- User wants to summarize a specific meeting transcript
- User asks to format meeting notes from a transcript file

## Core Functionality

### 1. Find Today's Meeting Transcripts

Search the `Github/one-one/` directory tree for transcript files matching today's date.

Transcript files live in person-specific subdirectories and follow this naming pattern:
`Github/one-one/<person>/<YYYY-MM-DD> <time> <participants>.md`

Example: `Github/one-one/jfuchs/2026-02-12 11.35.54  Jason _ Jon.md`

```bash
# Find all transcript files for today's date
find "Github/one-one" -name "$(date +%Y-%m-%d)*" -type f
```

### 2. Match Transcripts to One-on-One Note Files

One-on-one note files are at: `Github/one-one/@<person>.md`

The person subdirectory name maps to the `@<person>.md` file. For example:
- Transcript in `Github/one-one/jfuchs/` maps to `Github/one-one/@jfuchs.md`
- Transcript in `Github/one-one/blakewilliams/` maps to `Github/one-one/@blakewilliams.md`

### 3. Present Found Transcripts to User

**IMPORTANT:** Always ask the user which transcripts they want to process. Never auto-process without confirmation.

Present a list of found transcripts and ask the user to select which ones to update. Show:
- The person's name (from the subdirectory)
- The transcript filename
- The target one-on-one file

### 4. Read the Transcript

Read the full transcript file. Transcripts are formatted as timestamped dialogue:
```
[@JasonMore] 11:35:42
Blue.

[Jon (@jfuchs, he/him)] 11:39:06
Hey, I'm sorry about that.
```

### 5. Generate the Summary

Your main directive is to automatically format meeting transcripts in GitHub-flavored Markdown using the following structure:

#### Required Sections

**## TL;DR**
- Exactly 3 sentences summarizing the most important takeaways
- Be specific and actionable, not vague

**## Key Discussion Points**
- Use bold headers for each point (e.g., `**Topic Name**:`)
- Include specific details, names, and context from the conversation
- Capture technical decisions and their rationale

**## Action Items**
- Use checkbox format: `- [ ] Description (Responsible Person)`
- Include the directly responsible individual when applicable
- Only include concrete, actionable items that were explicitly or implicitly agreed upon

**## Follow-up Items**
- Items to revisit later or track over time
- Things that need more investigation or future discussion

**## References**
- Resources, links, documents, tools, or concepts mentioned in the meeting
- Use bold for the reference name followed by a description
- Include any URLs or issue links mentioned

#### Writing Style Rules
- Never use em dashes (-). Use colons (:), periods (.), or hyphens (-) instead.
- Be concise but capture important nuance
- Use GitHub-flavored Markdown
- Attribute decisions and opinions to the right people
- Preserve technical accuracy of any code, architecture, or system discussions

### 6. Insert the Summary into the One-on-One File

Find the correct date heading in the one-on-one file and insert the summary AFTER any existing content under that date heading but BEFORE the next date heading.

**CRITICAL: Insertion Logic**

The one-on-one files have date headings (either `## YYYY-MM-DD` or `# YYYY-MM-DD`). Today's date heading should already exist with some raw notes under it.

1. Find today's date heading in the file
2. Find the end of the existing content under that heading (everything before the next heading)
3. Append the formatted summary after the existing content
4. Do NOT replace or remove any existing content under the date heading
5. Add a blank line before the summary sections for readability

For example, if the file has:
```markdown
## 2026-02-12
![[Pasted image 20260212114748.png]]

milestone 7 dev ux issue https://...
# 2026-01-12
```

After insertion it should look like:
```markdown
## 2026-02-12
![[Pasted image 20260212114748.png]]

milestone 7 dev ux issue https://...

## TL;DR
...

## Key Discussion Points
...

## Action Items
...

## Follow-up Items
...

## References
...

# 2026-01-12
```

### 7. Confirmation

After insertion, show the user what was added and where. Offer to make adjustments if needed.

## Important Notes

- The vault root is the current working directory (the Obsidian vault)
- One-on-one files use `@` prefix: `@jfuchs.md`, `@blakewilliams.md`
- Transcript subdirectories do NOT use `@` prefix: `jfuchs/`, `blakewilliams/`
- Date headings in note files may use `#` or `##` - match the existing convention in each file
- Always preserve existing content. Never overwrite or remove notes the user has already written
- If a date heading for today doesn't exist yet, create one at the top of the file using the same heading level convention as the rest of the file
