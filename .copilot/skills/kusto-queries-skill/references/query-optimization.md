# Kusto Query Optimization Reference

A comprehensive guide to writing performant KQL queries. Based on the [official Kusto Query Best Practices](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/best-practices) and internal experience.

## Why Optimize?

Slow queries consume cluster resources, affecting other users' queries and increasing costs. You can review costly queries in the [expensive Kusto queries dashboard](https://dataexplorer.azure.com/dashboards/04a3e5b1-3b3f-4fa2-ae0c-6e4ccc0b8a14?p-_startTime=7days&p-_endTime=now#c2148949-8b99-46c8-ba4d-e2afc4444bdc).

For help, reach out in the [`#kusto` Slack channel](https://github-grid.enterprise.slack.com/archives/C0115QA83E1).

---

## Rule 1: Order of `where` Clauses

**The order of `where` clauses has a large effect on performance.** Move them as high as possible and order by priority:

1. **`datetime` filters first** — Kusto can prune entire data shards.
   ```kql
   | where timestamp >= ago(7d)
   ```
2. **`string` / `dynamic` filters next** — Order by selectivity (most selective first).
   ```kql
   | where id == "abc123"          // very selective
   | where api_route == "/some/route"  // less selective
   ```
3. **Numeric filters** — e.g., `| where http_status >= 500`
4. **Unindexed scan filters last** — e.g., `| where description contains "value"`

---

## Rule 2: Order of `join` Clauses

- Place `join` **after** as many filters as possible.
- Pre-filter the joined table to reduce its size:

```kql
// Before:
| join some_issues_table on $left.issue_id == $right.id

// After:
| join (some_issues_table | where state == "open") on $left.issue_id == $right.id
```

- For latest snapshot data, use `GetLatestSnapshotView`:

```kql
| join GetLatestSnapshotView(github_mysql1_sub_issues) on $left.sub_issue_id == $right.id
```

- Avoid joining tables whose data is not needed in the final result.

---

## Rule 3: Avoid Filtering on Calculated Columns

Computed columns via `extend` are evaluated for every row. Prefer these alternatives:

### Use case-insensitive operators instead of `tolower()`

```kql
// Bad
| extend lowercase_value = tolower(value)
| where lowercase_value == "something"

// Good
| where value =~ "something"
```

### Convert the searched value instead of every row

```kql
// Bad
| extend converted_name = unicode_codepoints_to_string(value)
| where converted_name == "something"

// Good
let target_name = unicode_codepoints_from_string("something");
some_table | where value == target_name
```

### Query the expression directly

```kql
// Bad
| extend value = tostring(values[0])
| where isnotempty(value)

// Good
| where isnotempty(tostring(values[0]))
```

---

## Rule 4: `has` vs `contains`

| Operator | Behavior | Speed |
|----------|----------|-------|
| `has` | Full-word tokenized search | Fast |
| `contains` | Substring match | Slow |

Use `has` for whole words; `contains` only when partial matches are needed.

---

## Rule 5: Prefer Case-Sensitive Operators

Case-insensitive operators are slower:

| Prefer (faster) | Over (slower) |
|------------------|---------------|
| `==` | `=~` |
| `in` | `in~` |
| `contains_cs` | `contains` |
| `has_cs` | `has` |

---

## Rule 6: Pre-check Dynamic Fields Before JSON Parsing

JSON parsing is expensive. Pre-filter with a text search:

```kql
// Bad — parses JSON for every row
| where DynamicJsonColumn["Key"]["Key2"] == "something"

// Good — text search first, then parse only matching rows
| where DynamicJsonColumn has_cs "something"
| where DynamicJsonColumn["Key"]["Key2"] == "something"
```

---

## Rule 7: Use Limits

Apply limits when you only need top-N results:

```kql
| top 100 by elapsed_ms desc
// or equivalently:
| order by elapsed_ms desc
| take 100
```

---

## Rule 8: `dcount` vs `count_distinct`

| Function | Behavior | Use When |
|----------|----------|----------|
| `dcount` | Fast approximation | Large datasets, dashboards |
| `count_distinct` | Exact count (≤100M values) | Precision required |

---

## Quick Checklist

- [ ] `where timestamp` is the first filter
- [ ] String filters ordered by selectivity
- [ ] `join` placed after all possible filters
- [ ] Joined tables are pre-filtered inline
- [ ] No unnecessary `extend` before `where`
- [ ] Using `has` instead of `contains` where possible
- [ ] Using case-sensitive operators where possible
- [ ] Dynamic column pre-checked with `has_cs` before JSON access
- [ ] `limit` / `take` applied for top-N queries
- [ ] Using `dcount` instead of `count_distinct` when approximation is acceptable

---

## Further Reading

- [KQL reference](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/)
- [Query best practices](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/best-practices)
- [Expensive Kusto queries dashboard](https://dataexplorer.azure.com/dashboards/04a3e5b1-3b3f-4fa2-ae0c-6e4ccc0b8a14?p-_startTime=7days&p-_endTime=now#c2148949-8b99-46c8-ba4d-e2afc4444bdc)
