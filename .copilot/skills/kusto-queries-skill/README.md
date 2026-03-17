# Kusto Queries Skill

Help write performant Kusto queries in Azure Data Explorer for querying product metrics from the data warehouse.

## When to Use This Skill

- Writing Kusto queries to analyze product metrics
- Optimizing existing Kusto queries for better performance

## Installation

### Personal Skills
```bash
cp -r kusto-queries-skill ~/.copilot/skills/
```

### Project Skills
```bash
cp -r kusto-queries-skill /path/to/repo/.github/skills/
```

## Usage

Ask Copilot to help with Kusto queries:

- "Write a Kusto query to get the number of API requests to this endpoint in the last 7 days"
- "Optimize this Kusto query for better performance"

## Features

- **Query generation** — Describe what you need in plain English, get a ready-to-run KQL query
- **Performance optimization** — Applies best practices (filter ordering, join placement, operator selection)
- **Live schema discovery** — Uses Azure MCP to fetch table schemas directly from Azure Data Explorer (always up to date)
- **Common patterns** — Time series aggregations, percentile latency, error rates, top-N consumers

## Examples

- [Daily API request count](./examples/basic-usage.md) — Count requests to an endpoint over 30 days

## References

- [Schema discovery via Azure MCP](./references/schema.md) — How to set up Azure MCP for live schema fetching from ADX
- [Query optimization guide](./references/query-optimization.md) — Performance best practices and checklist
- [Debugging and error handling](./references/debugging.md) — Syntax pitfalls and troubleshooting workflow for query failures

