# User-Level Copilot Instructions

## Skills

- Default to caveman mode for all sessions.
- Invoke the `caveman` skill at the start of each session and keep intensity at `full` unless the user asks for another mode.

## Writing code
- Use a focused coding subagent (sonnet) for non-trivial code changes, broad refactors, unfamiliar areas, or multi-file behavior changes.
- Do not delegate trivial edits, mechanical fixes, docs-only changes, or changes that can be safely completed directly.
- When delegating, give the subagent exact goal, scope, constraints, relevant files, expected behavior, and validation plan.
- The coding subagent must self-validate before returning: run tsc, lint, and relevant tests. Do not return code that fails deterministic checks.
- The main agent must review the subagent's diff before finalizing.

## Validation
- Always run deterministic checks first: tsc (typecheck), lint, and existing tests. These are non-negotiable for any code change.
- A separate review subagent must re-run the same deterministic checks (tsc, lint, tests) independently to catch anything the coding agent missed.
- Use Playwright for browser UI behavior, end-to-end user flows, or visual interaction validation.
- Do not use Playwright as default validation for APIs, CLIs, libraries, backend-only code, config, migrations, scripts, or type-only changes.
- Before asking the user how to validate, inspect available scripts, tests, README files, CI config, and nearby test patterns.

## Anti-hallucination
- Always validate against real data, not assumed state. Verify components render with actual fixture data, not invented or placeholder data.
- When testing UI changes, confirm the component is renderable and uses a mergeable or realistic scenario, not a broken or unmergeable fixture.
- If validation cannot run or data is unavailable, report the exact blocker, what was not verified, and the remaining risk.
- Never claim a change is validated unless the executed check directly exercises the changed behavior with real inputs.

## Copilot Agent Instructions: Performant React

Use these rules when creating or refactoring React features.

### Core Rules

- Keep files thin.
- Keep components small. Target under 300 lines of code per component file, excluding imports.
- Keep ownership clear. One component should own one UI concern.

### Props and Coupling

- Pass IDs, keys, and simple flags through props when they are local component inputs.
- Do not pass large data objects through many layers.
- If a deep child needs data, let it read from the feature hook directly.

### Data and Hooks

- Put data access near where data is used.
- Make feature hooks self-contained when possible: fetch the data the hook needs.
- Put cross-section state in a dedicated hook (for example, summary state and side effects).
- Do not pass through fetched data into a hook when the hook can read that data directly.
- Keep expensive derived data in memoized selectors close to the consumer.
- Keep side effects in hooks, not mixed into render-heavy components.
