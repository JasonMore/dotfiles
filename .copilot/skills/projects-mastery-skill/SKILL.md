---
description: This skill should be used when the user asks to "manage a GitHub project", "organize project work", "update project fields", "run project triage", "use GraphQL for ProjectV2", "use REST for projects", or needs project-manager style control of GitHub Projects.
metadata:
    github-owner: github
    github-path: projects-mastery-skill
    github-ref: main
    github-repo: agent-skills
    github-sha: 4bdb20a2e5dd92a952dc963494905df4f75b1ff6
    github-tree-sha: 3872893d94f08b641a43f31e4b6592b06cecec18
name: projects-mastery
---
# Projects Mastery - GitHub Projects Operations at PM Level

Operate GitHub Projects (Projects v2) with production-grade discipline using:
- `gh project` for fast operator workflows
- GraphQL for authoritative ProjectV2 operations and rich mutations
- REST Projects v2 endpoints for direct API workflows and automation integration

## Core Principles

1. **Project is the source of execution truth**: backlog, priority, and delivery state live in project fields/views.
2. **Use the smallest surface that solves the task**:
   - Use `gh project` for common workflows
   - Use GraphQL for node-ID workflows and advanced field updates
   - Use REST Projects v2 for endpoint-driven integrations and external automation
3. **Never perform destructive operations without confirmation**: deleting items/fields/projects requires explicit confirmation.
4. **Keep status and iteration hygiene tight**: stale status and orphaned items are treated as defects.

## Preflight Checklist

Run this before any edits:

```bash
gh auth status
gh auth refresh -s project
```

Validate project command availability:

```bash
gh project --help
```

If the user requested read-only analysis, prefer `read:project` scope.

## API Selection Matrix

| Need | Best Surface | Why |
| --- | --- | --- |
| Quick list/view/edit/archive | `gh project` | Fastest operator loop |
| Set field values precisely | GraphQL | Native `updateProjectV2ItemFieldValue` semantics |
| Bulk endpoint-based integrations | REST Projects v2 | Predictable HTTP endpoints |
| Add issue/PR by URL | `gh project item-add` | Minimal ceremony |
| Add content by Node ID | GraphQL `addProjectV2ItemById` | Strong typing + item ID return |

## Operational Playbook

### 1) Discover and Baseline

```bash
# Find target projects
gh project list --owner <owner> --format json

# Inspect one project
gh project view <number> --owner <owner> --format json

# Inventory fields and items
gh project field-list <number> --owner <owner> --format json
gh project item-list <number> --owner <owner> --limit 200 --format json
```

Required baseline output:
- Project owner + number
- Item count and archive count
- Field map (id, name, type)
- Status field option IDs
- Iteration IDs (if applicable)

### 2) Field Governance (Schema Hygiene)

Use deterministic fields for execution:
- Status (single-select)
- Priority (single-select)
- Iteration (iteration)
- Target date (date)
- Estimate (number)
- Notes (text)

CLI create examples:

```bash
gh project field-create <number> --owner <owner> --name "Priority" --data-type SINGLE_SELECT --single-select-options "P0,P1,P2"
gh project field-create <number> --owner <owner> --name "Estimate" --data-type NUMBER
gh project field-create <number> --owner <owner> --name "Target date" --data-type DATE
```

### 3) Item Intake

#### CLI (URL-based)
```bash
gh project item-add <number> --owner <owner> --url https://github.com/<org>/<repo>/issues/<n>
gh project item-create <number> --owner <owner> --title "Draft work" --body "Context"
```

#### GraphQL (node ID-based)
```bash
gh api graphql -f query='\
mutation($input: AddProjectV2ItemByIdInput!) {\
  addProjectV2ItemById(input: $input) {\
    item { id }\
  }\
}' -f input='{"projectId":"PROJECT_NODE_ID","contentId":"CONTENT_NODE_ID"}'
```

### 4) Field Updates (Single Value Per Mutation)

Use `gh project item-edit` when possible:

```bash
# text
gh project item-edit --id <item-id> --project-id <project-id> --field-id <field-id> --text "Needs design review"

# number
gh project item-edit --id <item-id> --project-id <project-id> --field-id <field-id> --number 5

# date
gh project item-edit --id <item-id> --project-id <project-id> --field-id <field-id> --date 2026-02-20

# single-select
gh project item-edit --id <item-id> --project-id <project-id> --field-id <field-id> --single-select-option-id <option-id>

# iteration
gh project item-edit --id <item-id> --project-id <project-id> --field-id <field-id> --iteration-id <iteration-id>

# clear
gh project item-edit --id <item-id> --project-id <project-id> --field-id <field-id> --clear
```

GraphQL authoritative form:

```bash
gh api graphql -f query='\
mutation($input: UpdateProjectV2ItemFieldValueInput!) {\
  updateProjectV2ItemFieldValue(input: $input) {\
    projectV2Item { id updatedAt }\
  }\
}' -f input='{"projectId":"PROJECT_NODE_ID","itemId":"ITEM_NODE_ID","fieldId":"FIELD_NODE_ID","value":{"singleSelectOptionId":"OPTION_ID"}}'
```

### 5) Planning and Cadence Management

- Use board/roadmap views for weekly execution and long-range planning.
- Keep WIP constrained by status lanes.
- Reconcile stale items each cycle:
  - No assignee + in-progress status
  - Past target date + not done
  - No iteration + scheduled milestone window

### 6) Status Updates and Visibility

Project status updates are first-class signals for stakeholders.

GraphQL supports status update lifecycle (`createProjectV2StatusUpdate`, `updateProjectV2StatusUpdate`, `deleteProjectV2StatusUpdate`).

Always include:
- Current state (`ON_TRACK`, `AT_RISK`, etc.)
- Date window
- Short narrative and top blockers

### 7) REST Projects v2 Endpoints (When HTTP Flows Are Needed)

Use with `gh api` and `X-GitHub-Api-Version: 2022-11-28`.

Representative endpoints:
- `GET /orgs/{org}/projectsV2`
- `GET /orgs/{org}/projectsV2/{project_number}`
- `GET /orgs/{org}/projectsV2/{project_number}/fields`
- `GET /orgs/{org}/projectsV2/{project_number}/items`
- `POST /orgs/{org}/projectsV2/{project_number}/items`
- `POST /orgs/{org}/projectsV2/{project_number}/drafts`
- `POST /orgs/{org}/projectsV2/{project_number}/views`

User-owned variants exist (for example drafts):
- `POST /user/{user_id}/projectsV2/{project_number}/drafts`

## Source-Informed Guardrails (from github/github and github-ui)

When using field-value mutation semantics, enforce these constraints:

1. `ProjectV2FieldValue` must include **exactly one** of:
   - `text`, `number`, `date`, `singleSelectOptionId`, `iterationId`
2. The selected single-select option ID must belong to the target field.
3. Iteration ID must belong to the target iteration field.
4. Archived items cannot be updated or cleared.
5. Title field updates are restricted (only draft-issue context).
6. Some special fields have unsupported clear/update paths in mutation behavior.

## Error Handling

### Missing scope
- **Symptom:** permission/auth errors on project operations
- **Fix:** `gh auth refresh -s project`

### Invalid node IDs
- **Symptom:** `Could not resolve to a node with the global id of '...'`
- **Fix:** refresh IDs by querying project/field/item again before mutating

### Invalid field value payload
- **Symptom:** `must include exactly one ...`
- **Fix:** send one value key only in `ProjectV2FieldValue`

### Archived item writes
- **Symptom:** cannot update or clear archived item
- **Fix:** unarchive first (`gh project item-archive ... --undo`) or choose active item

## Output Contract

When executing project management tasks, return:

1. **State Summary**
   - project, scope, counts, key risks
2. **Actions Performed**
   - exact commands/mutations run
3. **Delta**
   - items changed, statuses moved, fields updated
4. **Follow-ups**
   - next triage or planning actions

Example concise output:

```text
Project github/123 triage complete.
- 18 items reviewed, 11 updated, 2 archived.
- Status normalized (Todo/In Progress/Done) and 6 priorities corrected.
- 3 risks remain: missing assignees on in-progress items.
Next: assign owners and publish status update (AT_RISK) with blocker notes.
```

## Boundaries

**Will:**
- Manage project state with CLI, GraphQL, and REST workflows
- Keep fields and item lifecycle consistent
- Automate repetitive updates safely

**Will Not:**
- Perform destructive operations without confirmation
- Assume IDs/field mappings without checking current project schema
- Hide mutation failures or silently skip invalid updates

## Quick Reference

```bash
# Discover
gh project list --owner <owner> --format json
gh project field-list <number> --owner <owner> --format json
gh project item-list <number> --owner <owner> --limit 200 --format json

# Intake
gh project item-add <number> --owner <owner> --url <issue-or-pr-url>
gh project item-create <number> --owner <owner> --title "..." --body "..."

# Update
gh project item-edit --id <item-id> --project-id <project-id> --field-id <field-id> --text "..."
gh project item-edit --id <item-id> --project-id <project-id> --field-id <field-id> --clear

# Archive/unarchive
gh project item-archive <number> --owner <owner> --id <item-id>
gh project item-archive <number> --owner <owner> --id <item-id> --undo

# Link/unlink
gh project link <number> --owner <owner> --repo <repo>
gh project unlink <number> --owner <owner> --repo <repo>
```
