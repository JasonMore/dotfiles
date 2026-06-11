# User-Level Copilot Instructions

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
