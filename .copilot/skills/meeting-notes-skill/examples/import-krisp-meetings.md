# Example: Import Today's Krisp Meetings

Demonstrates how the agent checks for existing transcripts and uses `krisp-import` CLI to fetch any missing ones before summarization.

## Scenario

Jason uses Krisp.ai for meeting transcripts. At the end of the day he wants today's Krisp meetings imported into the vault so the summarization flow can process them.

## User Request

> "Update my one-on-one notes from today's meetings"

## Agent Response - Step 1: Build Calendar Manifest

Agent fetches WorkIQ calendar and writes a session-local manifest:

```json
{
  "schema_version": 1,
  "timezone": "America/Chicago",
  "generated_at": "2026-05-18T17:00:00-05:00",
  "events": [{
    "event_id": "workiq-event-123",
    "title": "David / Jason 1:1",
    "start": "2026-05-18T10:30:00-05:00",
    "end": "2026-05-18T11:00:00-05:00",
    "organizer": {"display_name": "Jason More", "email": "jason@example.com"},
    "attendees": [{
      "display_name": "David Poll",
      "email": "david@example.com",
      "type": "required",
      "response": "accepted"
    }]
  }]
}
```

## Agent Response - Step 2: Check Existing Transcripts

Agent checks both roots:

```bash
find one-one -name "2026-05-18*" -type f 2>/dev/null
find "meetings/meeting transcripts" -name "2026-05-18*" -type f 2>/dev/null
```

No files found for today.

## Agent Response - Step 3: Run krisp-import CLI

Since no transcripts exist yet, the agent runs `krisp-import` with `VAULT_ROOT` set to the working vault so files land where the wikilinks resolve:

```bash
VAULT_ROOT="$PWD" krisp-import 2026-05-18 \
  --calendar-manifest "$CALENDAR_MANIFEST"
```

Output:
```
Searching Krisp for meetings on 2026-05-18 (range: 2026-05-17 to 2026-05-19)...

Meeting: David / Jason 1:1
  Calendar match: workiq-event-123
  Canonical invitees: David Poll, Jason More
  Route: one-one/davidpoll
  Exact speaker-set match: true
  Unresolved reason: none
  Imported: .../one-one/davidpoll/2026-05-18 10.30.00 David _ Jason 1_1.md

Done: 1 imported, 0 skipped, 0 already present.
```

If manifest is missing, invalid, ambiguous, or has no usable invitees, route is
`meetings/meeting transcripts` and output includes unresolved reason. Krisp speakers never change
destination.

## Agent Response - Step 4: Report

```
Imported 1 transcript from Krisp via krisp-import:
  1:1   Github/one-one/davidpoll/2026-05-18 10.30.00 David _ Jason 1_1.md  (-> @davidpoll.md)

Next step: summarize these imported transcripts and insert meeting notes.
```

The agent then continues with the normal summarization flow.

## Fallback: If krisp-import Is Not Installed

If `krisp-import` is unavailable, agent may use Krisp MCP. Same WorkIQ routing and attribution rules
still apply. If neither source works, report blocker:

```
krisp-import is not installed. To set it up:
  npm install -g @statechange/krisp-cli
  krisp auth
Then run: krisp-import
```
