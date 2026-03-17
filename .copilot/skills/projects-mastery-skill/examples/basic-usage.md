# Example: Weekly Project Triage and Planning

## Scenario
A PM wants to clean up a project before weekly planning: stale statuses, missing priorities, and unassigned in-progress work.

## User Request
> "Run triage on org project 42, normalize status/priority, and summarize risks."

## Agent Response
```bash
# 1) Baseline
gh project view 42 --owner acme --format json
gh project field-list 42 --owner acme --format json
gh project item-list 42 --owner acme --limit 200 --format json > /tmp/items.json

# 2) Identify stale state (example jq)
jq -r '.items[] | select(.status=="In Progress" and (.assignees|length==0)) | .id' /tmp/items.json

# 3) Update item status/priority
gh project item-edit --id PVTITEM_1 --project-id PVT_PROJECT --field-id STATUS_FIELD --single-select-option-id STATUS_TODO
gh project item-edit --id PVTITEM_1 --project-id PVT_PROJECT --field-id PRIORITY_FIELD --single-select-option-id PRIORITY_P1

# 4) Archive done + old
gh project item-archive 42 --owner acme --id PVTITEM_99

# 5) Publish outcome (GraphQL status update example)
gh api graphql -f query='\
mutation($input: CreateProjectV2StatusUpdateInput!) {\
  createProjectV2StatusUpdate(input: $input) {\
    projectV2StatusUpdate { id status }\
  }\
}' -f input='{"projectId":"PVT_PROJECT","status":"AT_RISK","body":"3 unowned in-progress items remain"}'
```

## Outcome
- Project state normalized for planning
- Stale and done work reduced
- Risks clearly surfaced for owner assignment
