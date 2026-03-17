# Meeting Notes Skill

Find today's meeting transcripts and insert formatted summaries into your one-on-one note files.

## When to Use This Skill

- Processing meeting transcripts from today
- Updating one-on-one notes with meeting summaries
- Formatting raw meeting transcripts into structured notes

## Prerequisites

Meeting transcripts should be saved in the Obsidian vault under:
```
Github/one-one/<person>/<YYYY-MM-DD> <time> <participants>.md
```

One-on-one note files should exist at:
```
Github/one-one/@<person>.md
```

## Installation

### Manual Installation

**Personal Skills**
```bash
cp -r meeting-notes-skill ~/.copilot/skills/
```

## Usage

This skill activates when you ask Copilot to:
- "Summarize my meetings from today"
- "Update my one-on-one notes"
- "Process today's meeting transcripts"
- "Format my meeting with Jon"
- "Add meeting summary to my 1:1 notes"

The skill will:
1. Search for today's transcript files in `Github/one-one/`
2. Present found transcripts and ask which to process
3. Read the selected transcript(s)
4. Generate a structured summary with TL;DR, Key Discussion Points, Action Items, Follow-up Items, and References
5. Insert the summary into the matching `@person.md` file under today's date heading
6. Show what was added for confirmation

## Output Format

Each summary includes these sections:

| Section | Description |
|---------|-------------|
| **TL;DR** | 3-sentence summary of key takeaways |
| **Key Discussion Points** | Detailed topics with context and decisions |
| **Action Items** | Checkbox-format tasks with responsible individuals |
| **Follow-up Items** | Things to revisit or investigate later |
| **References** | Links, docs, tools, and concepts mentioned |

## Example

### Before (raw notes in `@jfuchs.md`)
```markdown
## 2026-02-12
![[Pasted image 20260212114748.png]]

milestone 7 dev ux issue https://...
```

### After (with summary inserted)
```markdown
## 2026-02-12
![[Pasted image 20260212114748.png]]

milestone 7 dev ux issue https://...

## TL;DR
Jason and Jon discussed data flow in the UI service...

## Key Discussion Points
- **App Shell Data Architecture**: Jon shared...

## Action Items
- [ ] Schedule follow-up meeting to discuss React SDLC (Jason)

## Follow-up Items
- Explore M7 UI service milestone scope...

## References
- **Milestone 7 Dev UX Issue**: https://github.com/github/core-ux/issues/1519
```

## Tips

- Run this skill at the end of your meeting day to batch-process all transcripts
- Existing notes under a date heading are always preserved
- The skill asks for confirmation before processing, so you can select specific meetings
- Summaries follow the same format used in your existing notes (see `@blakewilliams.md` for reference)

---

**Required:** Obsidian vault with meeting transcripts in `Github/one-one/<person>/` directories
