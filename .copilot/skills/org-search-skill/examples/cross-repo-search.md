# Example: Cross-Repo Information Search

## Scenario

An engineer is trying to understand how deployment works across the organization. They know it involves multiple services and repos but don't know the full picture. They want to understand the end-to-end flow and who to contact for questions.

## User Request

> "How does our deployment pipeline work? I know there are multiple repos involved but I don't know the full picture. Search in the acme org."

## Agent Response

### Step 1: Analyze the Question

- **Type:** Architecture/Process (hybrid)
- **Key terms:** deployment, pipeline, multi-repo
- **Scope:** `acme` org
- **Priority surfaces:** Code/docs (primary), issues, discussions

### Step 2: Discover Repos

Agent searches repos related to "deploy", "pipeline", "CI/CD":

```
Found repos:
- acme/deploy-cli (description: "CLI tool for service deployments")
- acme/platform-infra (description: "Infrastructure and deployment automation")
- acme/ci-config (description: "Shared CI/CD configuration and workflows")
- acme/service-template (description: "Template for new services with standard deploy config")
- acme/deploy-docs (description: "Deployment documentation and runbooks")
```

### Step 3: Search Surfaces

**Code/docs search** (README, docs/, CONTRIBUTING files):

In `acme/deploy-docs`:
```
docs/deployment-guide.md - "End-to-End Deployment Guide"
docs/runbooks/rollback.md - "Rollback Procedures"
docs/architecture/pipeline-overview.md - "Deployment Pipeline Architecture"
```

In `acme/deploy-cli`:
```
README.md - "Deploy CLI: deploy, promote, rollback services"
```

In `acme/platform-infra`:
```
docs/pipeline-stages.md - "Pipeline Stages: build → test → stage → canary → prod"
```

**Issues search** (`org:acme deployment pipeline architecture`):

```
#456 (acme/platform-infra) - "Deployment pipeline v2 design"
  State: closed, Labels: architecture, RFC
  Snippet: "New deployment pipeline with canary stages..."

#78 (acme/deploy-docs) - "Document the full deployment flow"
  State: closed
  Snippet: "End-to-end guide covering all stages..."
```

**Discussions search:**
```
Discussion #12 (acme/platform-infra) - "Deployment best practices Q&A"
  Category: Q&A
  Snippet: "Common questions about deployment stages and promotion..."
```

### Step 4: Dig Into Evidence

Agent reads the pipeline architecture doc from `acme/deploy-docs`:
- 5-stage pipeline: Build → Test → Staging → Canary → Production
- All services use the shared CI/CD config from `acme/ci-config`
- The `deploy-cli` is the primary tool for triggering deployments
- Canary stage runs for 30 minutes with automated health checks
- Production promotion requires manual approval for tier-1 services

Agent reads the Deploy CLI README:
- `deploy promote SERVICE --to production` — promote to prod
- `deploy rollback SERVICE` — rollback to previous version
- `deploy status SERVICE` — check deployment status

Agent reads the RFC issue (#456):
- Pipeline v2 was adopted in August 2025
- Key change: added canary stage between staging and prod
- Decision driven by two production incidents from direct staging→prod promotion

Agent checks CODEOWNERS in `acme/platform-infra`:
- `* @acme/platform-team`
- Platform team owns the deployment infrastructure

### Step 5: Synthesize Answer

```
**Answer:** The deployment pipeline at acme is a 5-stage process: Build → Test →
Staging → Canary (30 min) → Production. It's managed across several repos:
`acme/platform-infra` (infrastructure), `acme/ci-config` (shared workflows),
`acme/deploy-cli` (developer tool), and `acme/deploy-docs` (documentation).

**Evidence:**
- [Deployment Pipeline Architecture](https://github.com/acme/deploy-docs/blob/main/docs/architecture/pipeline-overview.md)
  — Full architecture diagram and stage descriptions
- [End-to-End Deployment Guide](https://github.com/acme/deploy-docs/blob/main/docs/deployment-guide.md)
  — Step-by-step guide for deploying services
- [Deployment pipeline v2 design](https://github.com/acme/platform-infra/issues/456)
  — RFC explaining why the canary stage was added (two prod incidents)
- [Deploy CLI README](https://github.com/acme/deploy-cli#readme)
  — CLI commands: deploy promote, rollback, status
- [Pipeline Stages](https://github.com/acme/platform-infra/blob/main/docs/pipeline-stages.md)
  — Detailed stage configuration and promotion criteria

**Context:** The current pipeline (v2) was adopted in August 2025 after two
production incidents caused by direct staging-to-production promotion. The canary
stage was added as a safety gate. Tier-1 services require manual approval for
production promotion; tier-2+ services can auto-promote if canary health checks
pass. The @acme/platform-team owns the pipeline infrastructure — reach them at
#platform-team on Slack.

**Confidence:** High — Found comprehensive documentation, the design RFC, and
consistent information across multiple repos.

**Follow-up suggestions:**
- "What are the rollback procedures if a deployment fails?"
- "How do I add a new service to the deployment pipeline?"
- "What's the difference between tier-1 and tier-2 service deployment?"
- "Who is the DRI for the platform team?"
```

## Outcome

The engineer now has a complete picture of the deployment pipeline — the stages, the tools, the key repos, the history behind the design, and who to contact. They have links to dig deeper into any aspect.

## Key Takeaways

- **Cross-repo questions** require repo discovery as the first step — the answer was spread across 5 repos
- **Architecture questions** benefit from searching docs first, then issues for context
- **Following the RFC** revealed the *why* behind the current design (production incidents)
- **The answer combined** documentation (the "what"), RFCs (the "why"), and CODEOWNERS (the "who")
- **Comprehensive discovery** found repos the user didn't know about (`deploy-docs`, `ci-config`)
