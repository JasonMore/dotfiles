# Reference: One-on-One File Structure

## File Locations

One-on-one note files: `Github/one-one/@<person>.md`
Transcript files: `Github/one-one/<person>/<YYYY-MM-DD> <time> <participants>.md`

## Known People and Directories

| Directory | Note File | Person |
|-----------|-----------|--------|
| `blakewilliams/` | `@blakewilliams.md` | Blake Williams |
| `emma/` | `@emmaviolet.md` | Emma |
| `jfuchs/` | `@jfuchs.md` | Jon Fuchs |
| `jonmagic/` | `@jonmagic.md` | Jon Magic |
| `jose/` | `@joseinthearena.md` | Jose |
| `mattcoasta7/` | `@mattcosta.md` | Matt Costa |
| `maya/` | `@mayaross.md` | Maya Ross |
| `skylar/` | `@skylaranderson.md` | Skylar Anderson |

Note: The directory name and `@` file name may not always match exactly. When in doubt, list the directory contents to confirm mappings.

## Date Heading Conventions

Files use different heading levels for dates:
- Some files use `#` (h1): `# 2026-02-11`
- Some files use `##` (h2): `## 2026-02-12`

Always match the existing convention in each file. Look at the most recent date heading to determine the pattern.

## Transcript Format

Transcripts use timestamped dialogue entries:
```
[@JasonMore] HH:MM:SS
Message text.

[Person Name (@handle, pronouns)] HH:MM:SS
Response text.
```

## Summary Output Format

Always use `##` level headings for summary sections (TL;DR, Key Discussion Points, etc.), regardless of the date heading level. This creates a consistent hierarchy:

```markdown
# 2026-02-11         <- date heading (matches file convention)
...existing notes...

## TL;DR             <- always ## for summary sections
## Key Discussion Points
## Action Items
## Follow-up Items
## References
```
