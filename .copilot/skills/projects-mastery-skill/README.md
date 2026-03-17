# Projects Mastery Skill

Run GitHub Projects like a project manager using `gh project`, `gh api graphql`, and REST endpoints for Projects v2 operations.

## When to Use This Skill

- Running backlog triage and weekly planning in GitHub Projects
- Keeping project fields, status, and item metadata consistent
- Automating project updates across many items
- Mixing CLI + GraphQL + REST for precise control
- Publishing reliable project status updates

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Project scope on token:

```bash
gh auth status
gh auth refresh -s project
```

For read-only workflows, `read:project` can be enough.

## Installation

### Personal Skills
```bash
gh hubber-skills install projects-mastery-skill
```

### Project Skills
```bash
gh hubber-skills install projects-mastery-skill --project
```

## Usage

This skill activates when you ask Copilot to:
- "manage this GitHub project"
- "organize project items and status"
- "update project fields in bulk"
- "use GraphQL for ProjectV2"
- "run project triage"

The skill will:
1. Validate project context and auth scopes
2. Inventory fields/items/views
3. Apply repeatable triage and update workflows
4. Use the right API surface for each task
5. Return clear operational summaries and next actions

## Features

- **API surface selection** - Chooses between `gh project`, GraphQL, and REST with rationale
- **Field-safe updates** - Uses field type checks and option/iteration validation
- **PM operating cadence** - Supports intake, triage, planning, and reporting loops
- **Bulk operations** - Repeatable CLI and API scripts for large projects
- **Failure playbooks** - Handles common mutation and permission errors explicitly

## Examples

See [`examples/basic-usage.md`](./examples/basic-usage.md) for a full project triage and planning session.

---

**Required:** GitHub CLI with `project` auth scope
