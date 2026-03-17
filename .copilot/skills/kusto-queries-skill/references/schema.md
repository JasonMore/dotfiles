# Schema Discovery via Azure MCP

Instead of maintaining hard-coded table schemas, use the **Azure MCP server** to fetch live schema information directly from Azure Data Explorer.

## Prerequisites

### 1. Install and authenticate the Azure CLI

```bash
az login --tenant 398a6654-997b-47e9-b12b-9515b896b4de
```

Authenticate with your `@githubazure.com` credentials when prompted.

### 2. Add the Azure MCP server to Copilot CLI

Run `/mcp add azure` and fill in the fields:

| Field | Value |
|-------|-------|
| **Server Type** | `Local` |
| **Command** | `npx -y @azure/mcp@latest server start` |
| **Environment Variables** | *(leave empty)* |
| **Tools** | `*` (all tools) |

### 3. Verify connectivity

Once the Azure MCP server is running, you can query the GitHub data warehouse cluster:

```
https://gh-analytics.eastus.kusto.windows.net
```

## Notable Databases

| Database | Description |
|----------|-------------|
| `hydro` | Contains data for all Hydro events (e.g., `github_v1_request` for API request logs). This is the primary source for event-driven product metrics. |
| `snapshots` | Contains a copy of every table from our MySQL clusters. Useful for querying relational data (users, repos, orgs, etc.) without hitting production databases. |

> **`snapshots` tip:** Every table has a corresponding `_current` function that always points to the most recent snapshot. For example, `github_blanket_memex_memex_projects` has `github_blanket_memex_memex_projects_current`. **Always prefer the `_current` functions** — they stay updated automatically and contain less data than the full snapshot tables.

## Fetching Table Schemas

With the Azure MCP server available, use its **Kusto tools** to discover databases, tables, and column schemas at query time:

1. **List databases** — Ask the MCP to list databases on the `gh-analytics.eastus.kusto.windows.net` cluster.
2. **List tables** — Ask the MCP to list tables in a specific database (e.g., `hydro`).
3. **Get table schema** — Ask the MCP to describe a specific table's columns and types.
4. **Preview data** — Run a small `| take 5` query via the MCP to see sample values.

### Example: discovering the schema for `github_v1_request`

> "Use the Azure MCP Kusto tools to get the schema of the `github_v1_request` table in the `hydro` database on the `gh-analytics.eastus.kusto.windows.net` cluster."

This returns live column names, types, and doc-strings directly from ADX — always up to date, no manual maintenance required.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Azure MCP server not found | Run `/mcp add azure` again and ensure the server is listed |
| Authentication error | Re-run `az login --tenant 398a6654-997b-47e9-b12b-9515b896b4de` with `@githubazure.com` credentials |
| Cannot reach cluster | Verify VPN/network access to `gh-analytics.eastus.kusto.windows.net` |
| MCP tools not loading | Ensure **Tools** is set to `*` (all tools) when adding the server |
