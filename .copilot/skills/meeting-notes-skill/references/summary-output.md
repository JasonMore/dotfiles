# Summary and Snippet Output

Use these rules only after the user selects transcripts to process.

## Summary sections

Use these `##` headings with a 🤖 prefix:

1. `## 🤖 TL;DR`
2. `## 🤖 Key Discussion Points`
3. `## 🤖 Action Items`
4. `## 🤖 Follow-up Items`
5. `## 🤖 References`

TL;DR must contain exactly three specific, useful sentences.

Key discussion points use bold topic labels. Keep technical facts, choices, reasons, names, and
context. Action items use `- [ ] 🤖 Task (Owner)`. Include only clear actions. Follow-up items
hold topics that need more work or later discussion. References list links, tools, docs, and
concepts named in the meeting.

Keep prose concise. Use GitHub-flavored Markdown. Do not use em dashes or en dashes.

## Attribution

Use importer `exact_speaker_set_match` and rejection reasons:

- `true`: Krisp labels may identify speakers.
- `false`: Reject all Krisp labels. Never salvage matching labels.
- Existing file without matching trusted index metadata is always `false`, even when current Krisp
  metadata now matches WorkIQ. Do not assume local labels were refreshed.
- One-on-one: WorkIQ routing identifies sole non-Jason participant, so summary may normalize all
  non-Jason dialogue to that person.
- Group: Use generic attribution unless transcript text independently proves identity.
- Never assign an action item to a guessed person. Use `Unassigned` when owner is unclear.

Raw Krisp notes, transcript, and labels stay unchanged.

## Insert into the running note

Find the target date heading. Append the summary after all existing content for that date and
before the next date heading. Never replace user content. Use `##` for summary headings even when
the date heading uses `#`.

If the date heading is missing, add it at the top with the file's existing date-heading level.

## Update the daily snippet

For each processed meeting:

1. Find or create the day heading.
2. Find an existing meeting section with fuzzy matching.
3. Preserve a user-created heading and all text below it.
4. Append generated content after user text.
5. Create a `## 🤖` heading only when no matching heading exists.

Match in this order:

1. Same transcript or running-note wikilink target.
2. Clear participant, topic, or time overlap.
3. Link to the same running group note.

New one-on-one heading:

```markdown
## 🤖 1:1 with David ([[one-one/davidpoll/2026-05-21 10.30.00 David _ Jason 1_1|notes]])
```

New group heading:

```markdown
## 🤖 PR Overview Sync ([[meetings/meeting transcripts/2026-07-30 12.30.00 PR Overview Sync|notes]])
```

Add the TL;DR in a callout:

```markdown
> [!quote]+ Copilot: 1:1 with David
> Discussed overview ship timing and parity targets. David flagged preview UX as a blocker. Jason will finish the estimate form by Friday.
```

Use the Krisp summary above `# Transcript` as the TL;DR source when present. Otherwise use the
new summary.

## Merge action items

Read the selected transcript's action items. Convert each to:

```markdown
- [ ] 🤖 Description (Owner)
```

Merge items into the snippet's `# todo` section:

1. Use the person's category for a one-on-one.
2. Use the meeting or topic for a group meeting.
3. Create a missing category before `**random thoughts**`.
4. Preserve all existing items and their order.
5. Deduplicate with lowercase text after removing punctuation and the 🤖 prefix.

## Finish

Report what was added and where. Offer to adjust the result.
