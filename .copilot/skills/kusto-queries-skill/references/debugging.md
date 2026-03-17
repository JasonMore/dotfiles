# KQL Debugging & Error Handling Reference

Use this reference only when the user is debugging query errors, unexpected empty/partial results, or performance/runtime failures.

## Debugging Workflow

1. Capture the exact error text
2. Identify where failure occurs: parse, semantic, runtime, or result quality
3. Reduce to a minimal repro query
4. Apply the matching fix pattern below
5. Re-run with a narrower time range first

## Common Syntax Issues

### `let` statements must be directly followed by the query body

- **Symptom:** Parsing error after `let` definitions (for example, `No tabular expression statement found`)
- **Cause:** A blank line separates `let` statements from the query body
- **Fix:** Keep `let` statements contiguous and place the table/query immediately after

```kql
// INVALID
let start_time = ago(30d);

github_v1_request
| where timestamp > start_time
```

```kql
// VALID
let start_time = ago(30d);
github_v1_request
| where timestamp > start_time
```

## Runtime & Result Issues

### Query Timeout
- **Symptom:** `Request execution has exceeded the timeout`
- **Cause:** Query scans too much data or uses expensive operators early
- **Fix:** Tighten time filters, move `where` clauses up, pre-filter before `join`, add `take`/`limit`

### No Results Returned
- **Symptom:** Query returns an empty result set
- **Cause:** Wrong column name, wrong filter value, or no data in selected time range
- **Fix:** Verify column schema, validate filter literals, widen time range to sanity-check, take just a few rows to confirm data exists

### Partial Results Warning
- **Symptom:** `Query completed with partial results`
- **Cause:** Memory/row limits reached during execution
- **Fix:** Add stricter filters, aggregate earlier, or split query into smaller stages

## Quick Triage Checklist

- [ ] Error message captured exactly
- [ ] Query reduced to minimal repro
- [ ] Time filter applied first
- [ ] Joined tables pre-filtered
- [ ] Column names verified from schema
- [ ] `let` declarations contiguous with query body
