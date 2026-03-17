# Example: Process Today's Meeting Transcripts

Demonstrates the full workflow of finding, summarizing, and inserting meeting notes.

## Scenario

Jason has finished his meetings for the day and wants to update his one-on-one notes.

## User Request

> "Update my one-on-one notes from today's meetings"

## Agent Response - Step 1: Find Today's Transcripts

The agent searches for transcript files matching today's date:

```bash
find "Github/one-one" -name "2026-02-12*" -type f
```

Output:
```
Github/one-one/jfuchs/2026-02-12 11.35.54  Jason _ Jon.md
```

## Agent Response - Step 2: Ask User Which to Process

```
I found 1 meeting transcript from today:

1. **Jon Fuchs** - `2026-02-12 11.35.54  Jason _ Jon.md`
   Target file: `Github/one-one/@jfuchs.md`

Which transcripts would you like me to summarize and insert?
```

## Agent Response - Step 3: Read and Summarize

The agent reads the full transcript, identifies key themes, decisions, and action items, then generates the summary.

## Agent Response - Step 4: Insert Summary

The agent finds the `## 2026-02-12` heading in `@jfuchs.md` and inserts the summary after existing content:

```markdown
## 2026-02-12
![[Pasted image 20260212114748.png]]

milestone 7 dev ux issue https://github.com/github/core-ux/issues/1519

## TL;DR
Jason and Jon discussed app shell data architecture in the UI service, focusing on separating blocking vs. non-blocking user data to improve server render performance. They aligned on the UI service's nested route architecture as the path to smarter data loading, with deferred counts as a fallback threat for slow feature team payloads. Jose has asked Jason to refocus on React SDLC, and Jon offered to help scope Milestone 7 of the UI service initiative as a potential overlap area.

## Key Discussion Points
- **App Shell Data Flow**: Jon shared a diagram showing how data flows into the app shell via layout routes (global nav, repo, PR show). The plan is to separate blocking initial layout data from non-blocking deferred data, reducing what blocks SSR.
- **User Data in Server Renders**: Jason's intuition that user-specific data slows requests was directionally confirmed by Jon, though Jon noted almost all GitHub data involves authorization checks. Emma is exploring approaches where counts stay in the server render but must be fast and cacheable.
- **Deferred Counts Strategy**: Jon wants to keep deferred counts as a "threat" to feature teams who own making their counts fast. Emma is trying an approach that avoids deferring counts entirely.
- **Issues Team IndexedDB Work**: Jason is working with the issues team to extract reusable patterns from their local caching approach, though Jon expressed frustration that issues team's Relay-based implementation is not reusable.
- **React SDLC and Jose's Feedback**: Jose asked Jason to refocus on React SDLC, specifically state management. Jon noted M7 of the UI service is focused on DX and rapid iteration, and there may be overlap.
- **Milestone 7 Scoping**: M7 covers local dev (vs Codespaces), preview deploys, fast CI, and AI effectiveness in UI service. Jon offered to assign M7 to Jason to flesh out scope.

## Action Items
- [ ] Schedule 30-minute follow-up with Jon to discuss React SDLC in depth (Jason)
- [ ] Wait for Jose's response on SDLC vs UI service scope clarification before starting group thread (Jason)
- [ ] Consider setting up group DM with Jon and Jose to align on SDLC direction (Jason, after Jose responds)

## Follow-up Items
- Explore overlap between UI service Milestone 7 and React SDLC work Jose is requesting
- Investigate cookie or shared worker approach for client-to-server communication about cached data
- Continue working with issues team to extract reusable caching patterns from their Relay/IndexedDB approach
- Jon is out next week: schedule follow-up for today, tomorrow, or week after

## References
- **Milestone 7 Dev UX Issue**: https://github.com/github/core-ux/issues/1519
- **UI Service Milestone 7**: Focused on DX, local development, preview deploys, fast CI, and AI integration
- **IndexedDB Caching**: Issues team approach using local browser storage for repo tab counts and similar data
- **Relay**: GraphQL client used by issues team (Jon considers not reusable for broader adoption)
```

## Agent Response - Step 5: Confirm

```
Done! I've added the meeting summary to Github/one-one/@jfuchs.md under the 2026-02-12 heading.

The summary includes:
- TL;DR (3 sentences)
- 6 key discussion points
- 3 action items
- 4 follow-up items
- 4 references

Would you like me to adjust anything?
```
