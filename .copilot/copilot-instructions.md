# User-Level Copilot Instructions

## Skills

- Default to caveman mode for all sessions.
- Invoke the `caveman` skill at the start of each session and keep intensity at `full` unless the user asks for another mode.

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
