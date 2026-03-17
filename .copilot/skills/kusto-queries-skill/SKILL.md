---
description: This skill should be used when the user asks to "write a Kusto query", "optimize this Kusto query", "help me with KQL", "find the right Kusto table", "debug this Kusto query", "query product metrics", or needs help writing, optimizing, or debugging Kusto Query Language (KQL) queries in Azure Data Explorer.
metadata:
    github-owner: github
    github-path: kusto-queries-skill
    github-ref: main
    github-repo: agent-skills
    github-sha: e4ce2bd6f737248cd2648712159a7e6cb57d962a
    github-tree-sha: eb643f1a767c4635713e3027c404cf52affb0f75
name: kusto-queries
---
# Kusto Queries Skill — Write Performant KQL for Azure Data Explorer

You are an expert at writing and optimizing Kusto Query Language (KQL) queries in Azure Data Explorer (ADX) for querying product metrics from the GitHub data warehouse.

## When to Use This Skill

**Appropriate use cases:**
- Writing new Kusto queries from scratch to answer product questions
- Optimizing slow or expensive queries for better performance
- Common query patterns: aggregations, time series, joins, percentiles
- Schema/table discovery: finding the right tables and columns
- Debugging query errors or unexpected results

## Prerequisites

- Access to the GitHub Azure Data Explorer cluster (`gh-analytics.eastus.kusto.windows.net`)
- **Azure MCP server** configured in Copilot CLI — see [references/schema.md](references/schema.md) for setup instructions
- Familiarity with the [Azure Data Explorer web UI](https://dataexplorer.azure.com/)
- For help, reach out in Slack in the [`#kusto` channel](https://github-grid.enterprise.slack.com/archives/C0115QA83E1)

## Process

### Step 1: Understand the User's Question

Clarify what the user wants to measure or analyze:

1. **What metric?** (e.g., request count, latency, error rate)
2. **What filters?** (e.g., specific endpoint, time range, HTTP status)
3. **What granularity?** (e.g., daily, hourly, per-endpoint)
4. **What output?** (e.g., time series chart, single number, top-N list)

### Step 2: Identify the Right Table

Use the **Azure MCP server** to discover tables and schemas live from the cluster. This avoids relying on hard-coded schemas that can drift out of date.

1. **List tables** — Use Azure MCP Kusto tools to list tables in the target database (e.g., `hydro`) on the `gh-analytics.eastus.kusto.windows.net` cluster.
2. **Get schema** — Use Azure MCP Kusto tools to fetch the full column schema for the table you need.
3. **Preview data** — Run a small `| take 5` query via the MCP to see sample values and confirm the table is correct.

For full setup instructions and troubleshooting, see [references/schema.md](references/schema.md).

> **Tip:** A commonly used table is **`github_v1_request`** (database: `hydro`), which contains HTTP request logs for GitHub's API.

### Step 3: Write the Query

Follow this structure for well-organized queries:

```kql
// 1. Define parameters with let statements
let start_time = ago(30d);
let end_time = now();
let target_endpoint = "/repos/{owner}/{repo}/issues";
// 2. Query the table with filters ordered correctly
github_v1_request
| where timestamp between (start_time .. end_time)       // datetime filter FIRST
| where api_route == target_endpoint                       // string filter next
| where http_status >= 200 and http_status < 300           // numeric filter last
// 3. Aggregate / transform
| summarize request_count = count() by bin(timestamp, 1d)
// 4. Sort and present
| order by timestamp asc
```

### Step 4: Optimize the Query

Apply the performance best practices below to ensure the query is efficient.

If the user is troubleshooting failures (syntax/runtime/errors), load [references/debugging.md](references/debugging.md); otherwise, do not load it to keep context usage small.

---

## Query Performance Best Practices

### 1. Order of `where` Clauses

Move `where` clauses as high up in the query as possible. Filter in this priority order:

1. **`datetime` columns first** — Kusto is optimized for time-series data. Filtering on `timestamp` reduces the number of database shards queried.
2. **`string` and `dynamic` columns next** — Order by selectivity (most selective first).
3. **Numeric columns** — e.g., `| where http_status >= 500`
4. **Unindexed scan filters last** — e.g., `| where description contains "value"`

### 2. Order of `join` Clauses

- Place `join` clauses **after** as many filters as possible.
- Always pre-filter the joined table inline:

```kql
// BAD: joins unfiltered table
| join some_table on $left.id == $right.id

// GOOD: pre-filter the joined table
| join (some_table | where state == "open") on $left.id == $right.id
```

- For snapshot data (current/previous day), use the `GetLatestSnapshotView` helper:

```kql
| join GetLatestSnapshotView(github_mysql1_sub_issues) on $left.sub_issue_id == $right.id
```

- Avoid joining tables whose data is not needed in the final result.

### 3. Avoid Filtering on Calculated Columns

Computed columns via `extend` are evaluated for every row. Prefer alternatives:

**Use case-insensitive operators instead of `tolower()`:**
```kql
// BAD
| extend lowercase_value = tolower(value)
| where lowercase_value == "something"

// GOOD
| where value =~ "something"
```

**Convert the searched value instead of every row:**
```kql
// BAD
| extend converted = unicode_codepoints_to_string(value)
| where converted == "something"

// GOOD
let target = unicode_codepoints_from_string("something");
some_table | where value == target
```

**Query the expression directly instead of extending then filtering:**
```kql
// BAD
| extend value = tostring(values[0])
| where isnotempty(value)

// GOOD
| where isnotempty(tostring(values[0]))
```

### 4. Prefer `has` over `contains`

- `has` uses tokenization for fast full-word search.
- `contains` does substring matching (slower).
- Use `has` when searching for whole words; `contains` only for substrings.

### 5. Prefer Case-Sensitive Operators

Case-insensitive operators are slower:

| Prefer | Over |
|--------|------|
| `==` | `=~` |
| `in` | `in~` |
| `contains_cs` | `contains` |
| `has_cs` | `has` |

### 6. Pre-check Dynamic Fields Before Parsing JSON

JSON parsing is expensive. Pre-filter with a text search:

```kql
// BAD
| where DynamicJsonColumn["Key"]["Key2"] == "something"

// GOOD
| where DynamicJsonColumn has_cs "something"     // fast text search first
| where DynamicJsonColumn["Key"]["Key2"] == "something"
```

### 7. Use Limits for Top-N Queries

```kql
// Apply limit when you only need top results
| top 100 by elapsed_ms desc

// Or use take/limit
| take 100
```

### 8. Use `dcount` over `count_distinct`

- `dcount` — fast approximation, good for large datasets
- `count_distinct` — exact count, but slower and limited to 100M distinct values

---

## Output Format

When presenting query results to the user, include:

1. **The KQL query** in a fenced code block with `kql` language tag
2. **Explanation** of what the query does and key design decisions
3. **Performance notes** explaining why filters/joins are ordered a certain way
4. **Sample output** showing expected columns and format

```
✅ Query written for: Daily API request count for /repos/{owner}/{repo}/issues over 30 days

📊 Expected output columns:
- timestamp (datetime) — day bucket
- request_count (long) — number of requests that day

⚡ Performance notes:
- timestamp filter applied first (shard pruning)
- api_route filter uses string equality (indexed)
```

## Debugging Behavior

To keep the context window small, do **not** load debugging guidance by default.

Only when the user is troubleshooting query failures, syntax errors, empty/partial results, or runtime issues, consult:

- [references/debugging.md](references/debugging.md)

Use [references/debugging.md](references/debugging.md) as the source of truth for syntax pitfalls (including `let` placement), timeout handling, and step-by-step debugging workflow.

## Boundaries

**Will:**
- Write new KQL queries from natural language descriptions
- Optimize existing queries using performance best practices
- Explain query logic and design decisions
- Help find the right tables and columns
- Suggest query patterns for common analytics questions

**Will Not:**
- Modify cluster configuration or permissions
- Create or alter tables/materialized views
- Execute queries on behalf of the user
- Access data outside the known schema

## Quick Reference

```kql
// Filter template (correct order)
TableName
| where timestamp >= ago(7d)         // 1. datetime first
| where string_col == "value"        // 2. string next
| where numeric_col > threshold      // 3. numeric last
| summarize count() by bin(timestamp, 1h)
| order by timestamp asc
```

**Key links:**
- [KQL reference](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/)
- [KQL best practices](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/best-practices)
- Slack: [`#kusto`](https://github-grid.enterprise.slack.com/archives/C0115QA83E1)
