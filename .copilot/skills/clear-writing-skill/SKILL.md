---
name: clear-writing
description: >
  This skill should be used when the user asks to "write a PR description",
  "draft an issue", "write documentation", "summarize this", "create a description",
  "write release notes", "describe this change", "write a comment", "draft a message",
  "explain this", or any task that produces written prose or markdown output.
  Applies Hemingway-style readability rules to all generated text.
---

# Clear Writing - Hemingway Readability Rules

Apply these rules to ALL prose and markdown you produce. The goal: terse, clear writing
that anyone can read without strain. Target a grade 6-9 reading level.

## Core Rules

### 1. Use short, simple words

Pick the shortest, most common word that fits. One-syllable words are best.
Never use a complex word to sound smart.

| Instead of       | Write         |
|------------------|---------------|
| utilize          | use           |
| implement        | build, add    |
| facilitate       | help          |
| functionality    | feature       |
| modifications    | changes       |
| requirements     | needs         |
| subsequently     | then, next    |
| demonstrate      | show          |
| comprehensive    | full, complete|
| approximately    | about, around |
| nevertheless     | still, yet    |
| additionally     | also          |
| methodology      | method, way   |
| prerequisite     | requirement   |
| incorporation    | adding        |
| discontinue      | stop, end     |
| aforementioned   | this, that    |

### 2. Keep sentences short

Break long sentences into two or three short ones. Mix in short punchy sentences
for rhythm. If a sentence needs a second read to parse, it is too long.

Aim for 14 words or fewer per sentence on average. Some can be longer if they
follow a clear chain of logic, but scatter short ones throughout.

### 3. Cut adverbs ending in -ly

Most -ly adverbs are filler. Remove them unless they change the meaning.

- Bad: "This significantly improves performance"
- Good: "This improves performance by 40%"
- Bad: "The test consistently fails"
- Good: "The test fails every run"

### 4. Use positive, direct language

Say what IS true, not what ISN'T. Avoid double negatives and hedging.

- Bad: "This is not unlike the old approach"
- Good: "This is like the old approach"
- Bad: "It's not impossible to do this manually"
- Good: "You can do this by hand"

### 5. Cut filler phrases

Remove phrases that add no meaning:

- "In order to" - just write "To"
- "It is worth noting that" - cut it, just state the thing
- "As a matter of fact" - cut it
- "Due to the fact that" - write "Because"
- "At this point in time" - write "Now"
- "For the purpose of" - write "To" or "For"
- "In the event that" - write "If"
- "With regard to" - write "About" or "On"
- "A number of" - write "Some" or "Several"
- "The vast majority of" - write "Most"

### 6. Prefer active voice

Put the subject first. Say who does what.

- Bad: "The configuration was updated by the script"
- Good: "The script updated the config"
- Bad: "The issue can be resolved by restarting the service"
- Good: "Restart the service to fix this"

### 7. Keep paragraphs short

Two to four sentences per paragraph in most cases. Use bullet lists for three
or more related items. White space helps readers.

## Applying the Rules

When producing markdown (PR descriptions, issues, docs, summaries, comments):

1. Write the content
2. Reread each sentence - can you cut a word? Do it.
3. Replace any word over three syllables if a shorter one works
4. Break sentences longer than 20 words
5. Remove every -ly adverb that does not change the meaning
6. Cut filler phrases
7. Flip passive voice to active where possible

Do NOT make writing choppy or robotic. Vary sentence length for rhythm.
A few longer sentences are fine when they follow a clear chain of thought.
The goal is clarity, not a telegram.

## What Good Output Looks Like

For detailed before/after examples, see [references/examples.md](references/examples.md).
