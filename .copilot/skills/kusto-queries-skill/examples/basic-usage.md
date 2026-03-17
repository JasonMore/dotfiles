# Example: Daily API Requests to a Specific Endpoint

## Scenario 1: `issues#show` page requests over the last 30 days

### User Request

> "Write a Kusto query to get the number of daily API requests to the `issues#show` page over the last 30 days"

### Agent Response

Here's a KQL query that gives you daily request counts for that page (using the `github_v1_request` table in the `hydro` database):

```kql
// Daily API request count for the Issues endpoint over 30 days
let start_time = ago(30d);
let end_time = now();
github_v1_request
| where timestamp between (start_time .. end_time)
| where controller == "IssuesController"
| where controller_action == "show"
| summarize request_count = count() by bin(timestamp, 1d)
| order by timestamp asc
```
