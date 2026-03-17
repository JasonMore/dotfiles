# Org Search Skill Tests

Tests that the skill follows the multi-step search process and presents evidence-backed answers.

---

## Test: Reads READMEs Before Deep Search

**Prompt:**
```
How does authentication work in the github/example-app organization?
```

**Expected Behavior:**
The response should prioritize reading README files from discovered repos before performing broad issue or PR searches.
The skill explicitly states: "For every discovered repo, read its README.md before doing deeper searches."
It should NOT jump directly to org-wide issue search for architecture questions.

---

## Test: Declines When Specific Issue Is Requested

**Prompt:**
```
Can you look up issue #1234 in github/my-repo?
```

**Expected Behavior:**
The response should fetch the issue directly rather than performing an org-wide search.
The skill states this is "Not appropriate when user wants a specific issue or PR by number."
It should NOT run the full discover-repos, search-surfaces, dig-into-evidence process for a direct issue lookup.

---

## Test: Reports Confidence Level with Evidence

**Prompt:**
```
Why did the platform team decide to use PostgreSQL instead of DynamoDB?
```

**Expected Behavior:**
The response should include:
- A direct answer (or acknowledgment that evidence is insufficient)
- Links to evidence (issues, PRs, discussions, or docs)
- A confidence level (High/Medium/Low) with justification
- Follow-up suggestions if the answer is uncertain

It should NOT present inferences as definitive facts without noting the confidence level.
