# Example: Weekly update for a tracking issue

## Scenario
A user wants a weekly update drafted for a planning-tracking issue that has multiple linked PRs and dependent issues.

## User Request
> "Draft this week's status update for github/planning-tracking#2358 in our standard format."

## Agent Flow
1. Read issue body and recent comments.
2. Collect linked issue/PR URLs.
3. Check the state of each linked artifact.
4. Draft a short report with trend, target date, update, and summary.
5. Ask for confirmation before posting.

## Example Draft Output

```markdown
### Trending

<!-- data key="trending" start -->
🟡 at risk
<!-- data end -->

### Target date

<!-- data key="target_date" start -->
2026-03-07
<!-- data end -->

### Update

<!-- data key="update" start -->
We completed the AgentAssignment migration planning and aligned API sequencing with partner teams. The highest risk remains integration sequencing across assignment, GraphQL/API sourcing, and frontend rendering. For staff ship, we need to land assignment creation + task linkage and validate issue-level visibility behind expected permission checks. Public Preview requires stable issue rendering plus clear failure handling for missing task data; GA requires production hardening and rollout validation at target scale.
<!-- data end -->

### Summary

<!-- data key="summary" start -->
Core implementation sequencing is now clear, but delivery risk is still centered on cross-team dependency timing and security-safe visibility rules.
<!-- data end -->

<!-- data key="isReport" value="true" -->
<!-- data key="howieReportName" value="short" -->
```

## Outcome
The user gets a concise, evidence-based report draft that follows expected GitHub tracking update structure and can be posted with one confirmation.
