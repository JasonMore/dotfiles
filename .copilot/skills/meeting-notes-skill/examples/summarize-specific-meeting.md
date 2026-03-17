# Example: Summarize a Specific Meeting

Demonstrates processing a single, specific meeting transcript.

## Scenario

Jason just finished a meeting with Blake and wants to immediately summarize it.

## User Request

> "Summarize my meeting with Blake from today"

## Agent Response - Step 1: Find the Transcript

The agent searches for today's transcript in the blakewilliams subdirectory:

```bash
find "Github/one-one/blakewilliams" -name "2026-02-11*" -type f
```

Output:
```
Github/one-one/blakewilliams/2026-02-11 10.10.30  Blake _ Jason.md
```

## Agent Response - Step 2: Confirm

```
I found the transcript:

- **Blake Williams** - `2026-02-11 10.10.30  Blake _ Jason.md`
  Target file: `Github/one-one/@blakewilliams.md`

Shall I summarize and insert it?
```

## Agent Response - Step 3: Process and Insert

After user confirms, the agent reads the transcript, generates the summary, and inserts it under the matching date heading in `@blakewilliams.md`.

The output format follows:

```markdown
# 2026-02-11
[[one-one/blakewilliams/2026-02-11 10.10.30  Blake _ Jason.md]]
throw together really quick rfc docs

SDLC stuff is important
- heavy focus engineers on ground being productive
- goal: "how to rapidly iterate faster than before"

use storming, norming, forming

## TL;DR
...3 sentence summary...

## Key Discussion Points
- **Topic**: Details...

## Action Items
- [ ] Task description (Person)

## Follow-up Items
- Item to revisit later

## References
- **Name**: Description or link
```

Note how the existing handwritten notes (transcript link, raw notes) are preserved above the formatted summary sections.
