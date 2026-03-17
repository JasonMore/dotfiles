# Example: Finding Who Is Responsible for a Workstream

## Scenario

A product manager needs to coordinate with the team responsible for the authentication service. They don't know whether it's called "auth", "identity", or "IAM" internally, and they don't know which repo or team owns it.

## User Request

> "Who is the DRI for authentication at acme? I need to coordinate on a new SSO integration."

## Agent Response

### Step 1: Analyze the Question

- **Type:** Ownership/DRI
- **Key terms:** authentication, DRI, SSO
- **Scope:** `acme` org
- **Priority surfaces:** CODEOWNERS, issues (assignees), README files

### Step 2: Discover Repos

Agent searches repos in `acme` related to "auth", "authentication", "identity":

```
Found repos:
- acme/identity-service (description: "Core authentication and identity management")
- acme/auth-proxy (description: "Authentication proxy for internal services")
- acme/sso-connector (description: "SSO integration connectors")
```

### Step 3: Search Surfaces

**CODEOWNERS file** in `acme/identity-service`:
```
# Identity Service Ownership
* @acme/identity-team
/src/sso/ @acme/identity-team @acme/security-team
```

**README.md** in `acme/identity-service`:
```
## Team

- **DRI:** @maria-chen
- **Team:** @acme/identity-team (#identity-team on Slack)
- **Security contact:** @acme/security-team
```

**Issues search** (`org:acme authentication DRI owner`):
```
#201 (acme/identity-service) - "Q1 2026 Identity Team Charter"
  Assigned to: @maria-chen
  Labels: team-charter, identity
  Snippet: "DRI: Maria Chen. Team mission: own authentication..."

#88 (acme/sso-connector) - "SSO integration roadmap"
  Assigned to: @maria-chen, @james-k
  Labels: roadmap, SSO
  Snippet: "SSO integration plans for Q1 2026..."
```

### Step 4: Dig Into Evidence

Agent reads the team charter issue (#201):
- Maria Chen is DRI for the identity/authentication workstream
- Team includes 4 engineers and 1 PM
- Slack channel: #identity-team
- The team covers: authentication, SSO, identity management, session handling

Agent reads the SSO roadmap issue (#88):
- There's an active SSO integration project
- James K is engineering lead for SSO specifically

### Step 5: Synthesize Answer

```
**Answer:** Maria Chen (@maria-chen) is the DRI for authentication at acme.
The work is owned by the @acme/identity-team. For SSO specifically, James K
(@james-k) is the engineering lead.

**Evidence:**
- [Q1 2026 Identity Team Charter](https://github.com/acme/identity-service/issues/201)
  — Team charter listing Maria Chen as DRI
- [identity-service README](https://github.com/acme/identity-service#team)
  — Team section with DRI and contact info
- [CODEOWNERS](https://github.com/acme/identity-service/blob/main/CODEOWNERS)
  — @acme/identity-team owns the codebase, @acme/security-team co-owns SSO
- [SSO integration roadmap](https://github.com/acme/sso-connector/issues/88)
  — Active SSO project led by James K

**Context:** The identity team covers authentication, SSO, identity management,
and session handling. For your SSO integration coordination, James K (@james-k)
is the most direct contact. Reach the team at #identity-team on Slack.

**Confidence:** High — Found consistent ownership information across CODEOWNERS,
README, and team charter.

**Follow-up suggestions:**
- "What's the current SSO integration roadmap?"
- "What authentication standards does the identity team use?"
- "Are there any active SSO integration projects I could collaborate on?"
```

## Outcome

The PM now knows exactly who to contact (Maria for overall auth, James for SSO specifically), which Slack channel to use, and which repos are relevant. They also discovered there's an active SSO roadmap they can review.

## Key Takeaways

- **Ownership questions** should check CODEOWNERS, README, and team charter issues first
- **Multiple repos** may be involved — the skill discovered three auth-related repos
- **Layered ownership** is common — org DRI vs specific-project lead
- **Contact channels** (Slack, email) are often in README or team charters
- **Cross-referencing** CODEOWNERS with README and issues gave high-confidence answer
