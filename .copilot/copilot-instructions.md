# User-Level Copilot Instructions

## Skills

- Default to caveman mode for all sessions.
- Invoke the `caveman` skill at the start of each session and keep intensity at `full` unless the user asks for another mode.
- Create and update personal skills in `JasonMore/ai-skills` under its `skills/` directory. Treat that repository as the source of truth.
- Run `JasonMore/ai-skills`'s installer to symlink each personal skill into `~/.copilot/skills/`. Do not leave the only copy in a session, worktree, dotfiles, or user config directory.
- Before finishing skill work, validate the skill, commit it in `JasonMore/ai-skills`, and push it to GitHub.

## Commenting on PRs and Issues
- **REQUIRED:** Any time you comment as me on a PR or issue, prepend the message with `[from copilot-cli]`.

## Writing code
- Use a focused coding subagent for non-trivial code changes, broad refactors, unfamiliar areas, or multi-file behavior changes.
- Do not delegate trivial edits, mechanical fixes, docs-only changes, or changes that can be safely completed directly.
- **Model selection (use judgement).** For medium-to-large delegated tasks, prefer a lower-cost model to preserve the primary session's context window and budget. Escalate to a higher-cost model only when the work needs hard reasoning: tricky bugs, non-obvious architecture, ambiguous requirements, or changes spanning multiple systems.
- **Reuse subagents for continuation.** When follow-up work continues in the same context (iterating on the same task, files, or the subagent's prior output), send the follow-up to the existing subagent instead of spawning a new one. This keeps its accumulated context warm and keeps bulk work out of the primary session, protecting the primary context window. Start a fresh subagent only when the context genuinely differs.
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

## Pull Requests

- **Conditional auto force-push.** You may run `git push --force-with-lease` automatically, without asking, ONLY when BOTH hold:
  1. The PR is a draft **OR** has failing/pending required CI checks that block merge, AND
  2. The PR has **NOT** been approved by any reviewer.
- **Reviewer approval always blocks force-push.** Never auto force-push to an approved PR, even if it is a draft or CI is failing. Ask for explicit confirmation first.
- In any other case (PR is not a draft and CI is passing, or status is unknown), do not force push without explicit user confirmation.
- Always use `--force-with-lease`, never plain `git push --force` or `git push -f`.

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

### Query Subscriptions (TanStack Query)

- Use `select` to subscribe a component only to the data it actually renders. A change to any other part of the query data will not re-render that component.
- Select the narrowest value, not the whole object. If a row only needs a count, select the count: `select: d => ({ commitsCount: d.summary.commits?.count })`.
- Centralize query config in a `queryOptions()` factory hook that accepts caller `options`. Spread `options` first so explicit `queryKey`, `enabled`, and `queryFn` cannot be overridden.
- Pass `select` through the factory to the consuming `useSuspenseQuery`/`useQuery` call.
- Drop thin `useSuspenseX` wrapper hooks that add no logic. Call the factory directly: `useSuspenseQuery(useXQueryOptions({ select }))`.

```tsx
// Query factory: accepts caller options, protects the essentials.
function useActivityQueryOptions(options) {
  const {effectiveSelection, lastActivityTimestamp} = useEffectiveSelection()
  const queryKey = [PageData.activity, effectiveSelection?.timestamp, lastActivityTimestamp] as const
  const apiURL = usePageDataUrl(PageData.activity, `since=${effectiveSelection?.timestamp ?? ''}`)

  return queryOptions({
    ...options, // spread first so queryKey/enabled/queryFn below win
    queryKey,
    enabled: !!effectiveSelection,
    queryFn: () => fetchActivityPageData(apiURL),
    staleTime: Infinity,
  })
}

// Component subscribes only to the count it renders.
export function CommitsRow() {
  const {data: {commitsCount}} = useSuspenseQuery(useActivityQueryOptions({
    select: d => ({commitsCount: d.summary.commits?.count}),
  }))
  if (!commitsCount) return null
  const label = `${commitsCount} new ${pluralize(commitsCount, 'commit', 'commits')}`
  return <SidebarActivityRow icon={GitCommitIcon} label={label} group="commits" expectedCount={commitsCount} />
}
```

- Reference: TkDodo, "React Query Selectors, Supercharged" and "The Query Options API: Query Factories".
