# Example: Finding Why a Technical Decision Was Made

## Scenario

A developer joins a team that uses PostgreSQL for their primary data store. They know the team evaluated DynamoDB at some point but chose PostgreSQL. They want to understand the rationale.

## User Request

> "Why did we choose PostgreSQL over DynamoDB for the payments service? Search in the acme org."

## Agent Response

### Step 1: Analyze the Question

- **Type:** Decision/Rationale
- **Key terms:** PostgreSQL, DynamoDB, payments service
- **Scope:** `acme` org
- **Priority surfaces:** Issues, discussions, ADR files

### Step 2: Discover Repos

Agent searches for repos in `acme` org related to "payments" and "database":

```
Found repos:
- acme/payments-service (from name match)
- acme/platform-infra (from issue match: "Database decision for payments")
- acme/architecture-decisions (from name match)
```

### Step 3: Search Surfaces

**Issues search** (`org:acme PostgreSQL DynamoDB payments`):
```
#342 (acme/payments-service) - "RFC: Database selection for payments service"
  State: closed, Labels: RFC, decision
  Snippet: "Evaluated PostgreSQL, DynamoDB, and CockroachDB..."

#89 (acme/platform-infra) - "Database infrastructure for new payment flows"
  State: closed, Labels: infrastructure
  Snippet: "Need to provision PostgreSQL cluster for payments..."
```

**Discussions search** (`org:acme PostgreSQL payments decision`):
```
Discussion #15 (acme/architecture-decisions) - "Database strategy Q4 2025"
  Category: RFC
  Snippet: "After benchmarking, PostgreSQL offers better consistency guarantees..."
```

**Code search** (ADR files):
```
acme/architecture-decisions/docs/adr/0023-payments-database.md
  Snippet: "# ADR 0023: PostgreSQL for Payments Service"
```

### Step 4: Dig Into Evidence

Agent reads issue #342 body and comments:
- Original post: Comparison matrix of PostgreSQL vs DynamoDB vs CockroachDB
- Comment by @sarah: "DynamoDB doesn't support the transaction patterns we need for payment reconciliation"
- Comment by @alex: "PostgreSQL's ACID guarantees are critical for financial data"
- Linked PR: #350 "Add PostgreSQL infrastructure for payments"

Agent reads ADR 0023:
- Decision: PostgreSQL chosen for ACID transactions, relational query patterns, team expertise
- Rejected: DynamoDB (eventual consistency unsuitable for financial reconciliation), CockroachDB (operational complexity not justified at current scale)

### Step 5: Synthesize Answer

```
**Answer:** PostgreSQL was chosen over DynamoDB for the payments service primarily
because of its ACID transaction guarantees, which are critical for payment
reconciliation. DynamoDB's eventual consistency model was deemed unsuitable for
financial data integrity.

**Evidence:**
- [RFC: Database selection for payments service](https://github.com/acme/payments-service/issues/342)
  — Full comparison matrix evaluating PostgreSQL, DynamoDB, and CockroachDB
- [ADR 0023: PostgreSQL for Payments Service](https://github.com/acme/architecture-decisions/blob/main/docs/adr/0023-payments-database.md)
  — Formal decision record with rationale
- [Database strategy Q4 2025](https://github.com/acme/architecture-decisions/discussions/15)
  — Broader discussion with benchmarking results

**Context:** The decision was made in October 2025. CockroachDB was also considered
but rejected due to operational complexity at the team's current scale. The team noted
this could be revisited if scale requirements change significantly.

**Confidence:** High — Found both an RFC issue with community discussion and a
formal ADR documenting the decision.

**Follow-up suggestions:**
- "What were the specific DynamoDB consistency issues that disqualified it?"
- "Has the scale assessment changed since the original decision?"
- "Who was involved in the database selection process?"
```

## Outcome

The developer gets a clear answer with links to the original decision records. They can read the full RFC and ADR for more detail, or follow up with the people who made the decision.

## Key Takeaways

- **Decision questions** should prioritize issues (especially those labeled RFC/decision) and ADR files
- **Searching multiple surfaces** found both the informal discussion (issue) and formal record (ADR)
- **Reading comments** was critical — the rationale was elaborated in comments, not just the issue body
- **Cross-referencing** the ADR with the issue gave a complete picture
