# User-Level Copilot Instructions

## Writing style

- Use ASD-STE100 Simplified Technical English for all prose.

## Commenting on PRs and Issues
- **REQUIRED:** Any time you comment as me on a PR or issue, prepend the message with `[from copilot-cli]`.

## Writing code
- Make small, clear code changes directly.
- Use one focused coding subagent only when a task is broad, risky, unfamiliar, or spans several files.
- Do not delegate trivial edits, mechanical fixes, docs-only changes, or changes that can be safely completed directly.
- Do not spawn more than one subagent for the same coding task unless I ask for parallel review or the work has separate parts.
- Use the newest stable model available for subagents. If model choice is unclear, ask.
- When follow-up work continues in the same context, send it to the existing subagent instead of spawning a new one.
- When delegating, give the subagent exact goal, scope, constraints, relevant files, expected behavior, and validation plan.
- Ask the subagent to run the smallest targeted checks that cover the change.
- The main agent must review the subagent's diff before finalizing.

## Preserving user changes

- Treat user-made changes as authoritative, whether committed or uncommitted, including changes made after Copilot generated or edited the same code.
- Before editing a file that Copilot previously touched, inspect its current contents and diff. Preserve all user changes and integrate around them.
- Never restore an earlier Copilot version over newer user work, overwrite manual edits, or treat prior agent output as the source of truth.
- If user changes conflict with the requested task or make intent unclear, stop and ask before modifying or reverting them.
- Do not revert unexpected changes. Assume they are intentional user work unless the user explicitly says otherwise.

## Validation
- Run the smallest deterministic checks that cover the change.
- For code changes, prefer targeted typecheck, lint, and tests for the changed package or feature.
- Run full suites only when the change is cross-cutting, touches shared infra, or targeted checks cannot cover the risk.
- A review subagent is optional. Use it only for broad refactors, risky behavior changes, security-sensitive code, or when I ask for review.
- Use Playwright for browser UI behavior, end-to-end user flows, or visual interaction validation.
- Do not use Playwright as default validation for APIs, CLIs, libraries, backend-only code, config, migrations, scripts, or type-only changes.
- Before asking the user how to validate, inspect available scripts, tests, README files, CI config, and nearby test patterns.

## Anti-hallucination
- Always validate against real data, not assumed state. Verify components render with actual fixture data, not invented or placeholder data.
- When testing UI changes, confirm the component is renderable and uses a mergeable or realistic scenario, not a broken or unmergeable fixture.
- If validation cannot run or data is unavailable, report the exact blocker, what was not verified, and the remaining risk.
- Never claim a change is validated unless the executed check directly exercises the changed behavior with real inputs.

## Pull Requests

- Always open pull requests as drafts using the `--draft` flag.
- **Conditional auto force-push.** You may run `git push --force-with-lease` automatically, without asking, ONLY when BOTH hold:
  1. The PR is a draft **OR** has failing/pending required CI checks that block merge, AND
  2. The PR has **NOT** been approved by any reviewer.
- **Reviewer approval always blocks force-push.** Never auto force-push to an approved PR, even if it is a draft or CI is failing. Ask for explicit confirmation first.
- In any other case (PR is not a draft and CI is passing, or status is unknown), do not force push without explicit user confirmation.
- Always use `--force-with-lease`, never plain `git push --force` or `git push -f`.
- Do not address PR review comments if the PR is already mergeable. If the merge status is mergeable, stop and ask whether to address the comments before making changes.

## Notifications

- When you need user input or attention, run `osascript -e 'display notification "MESSAGE" with title "Copilot" sound name "Glass"'` to send a macOS push notification. Replace `MESSAGE` with a short summary.

## Slack

- Prefer the Slack MCP for Slack operations: read threads, send messages, and fetch context.
- Fall back to the `gh-slack` CLI extension when the Slack MCP is unavailable, fails, or is not configured.
- If both the Slack MCP and `gh-slack` fail, report the exact blocker instead of guessing at Slack content.

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
