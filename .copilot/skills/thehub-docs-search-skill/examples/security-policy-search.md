# Example: Finding Security Policies

How to search for and retrieve security policies and compliance documentation.

## Scenario

You need to understand GitHub's security policies for handling production access and incident response.

## User Request

> "What's the policy on production access and incident response?"

## Agent Response - Step 1: Recognize Security Context

```
⚠️  Security policy search

I'll search thehub for security policies on:
• Production access control
• Incident response procedures

These docs may contain sensitive information. I'll provide source links
and summaries for your review.
```

## Agent Response - Step 2: Search Security Directory

**Local clone (preferred):**

> `THEHUB_ROOT` is set during the skill's local-clone detection step (see "Local vs API Access" in SKILL.md).

```bash
# Search security directory paths
echo "=== Security policy documents ==="
find "$THEHUB_ROOT/docs/security" -name '*.md' | grep -i "access\|incident"

# Search content
echo "=== Searching security policies ==="
grep -ri "production access" "$THEHUB_ROOT/docs/security" --include='*.md' -l

grep -ri "incident response" "$THEHUB_ROOT/docs/security" --include='*.md' -l
```

**API fallback:**

```bash
# Search security directory paths
echo "=== Security policy documents ==="
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/security/' | grep -i "access\|incident"

# Search content
echo "=== Searching security policies ==="
gh search code "production access" \
  --repo github/thehub \
  --path "docs/security/" \
  --filename "*.md" \
  --limit 5

gh search code "incident response" \
  --repo github/thehub \
  --path "docs/security/" \
  --filename "*.md" \
  --limit 5
```

## Agent Response - Step 3: Present Findings

```
🔒 Found security policy documents:

1. 📄 Production Access Control Policy
   🔗 https://thehub.github.com/docs/security/access-control-policy.md
   Owner: security-team (#security)
   Last updated: 2024-01-15
   
   Covers:
   • Access approval workflows
   • Principle of least privilege
   • Access review procedures
   • Emergency access protocols
   • Access logging and auditing

2. 📄 Incident Response Guide
   🔗 https://thehub.github.com/docs/security/incident-response-guide.md
   Owner: security-operations (#security-ops)
   Last updated: 2024-02-01
   
   Covers:
   • Incident classification
   • Response procedures
   • Escalation paths
   • Communication protocols
   • Post-incident review

3. 📄 Production Environment Standards
   🔗 https://thehub.github.com/docs/security/production-standards.md
   Owner: security-compliance (#security-compliance)
   
   Covers:
   • Environment separation
   • Access requirements
   • Change management
   • Audit requirements
```

## Agent Response - Step 4: Confirm Before Retrieving

```
Would you like me to:

1. Fetch and summarize the access control policy?
2. Show the incident response workflow?
3. Retrieve specific sections from these docs?
4. Find related compliance documentation?

These are internal security policies - I'll show you the information
directly for your review.
```

## User Follow-up

> "Show me the incident response workflow"

## Agent Response - Step 5: Retrieve and Summarize

**Local clone (preferred):**

```bash
# Read incident response guide
CONTENT=$(cat "$THEHUB_ROOT/docs/security/incident-response-guide.md")

# Extract frontmatter
OWNER=$(echo "$CONTENT" | awk '/^---$/,/^---$/' | grep '^owner_slack:' | cut -d: -f2- | xargs)

# Present structured summary
```

**API fallback:**

```bash
# Fetch incident response guide
CONTENT=$(gh api "repos/github/thehub/contents/docs/security/incident-response-guide.md" \
  --jq '.content' | base64 -d)

# Extract frontmatter
OWNER=$(echo "$CONTENT" | awk '/^---$/,/^---$/' | grep '^owner_slack:' | cut -d: -f2- | xargs)

# Present structured summary
```

```
🔒 Incident Response Guide

🔗 https://thehub.github.com/docs/security/incident-response-guide.md
Owner: security-operations
Contact: #security-ops

=== Incident Classification ===

Severity Levels:
• SEV-1: Critical - Immediate threat to user data or service availability
• SEV-2: High - Significant security concern, limited immediate impact  
• SEV-3: Medium - Security issue requiring attention, no immediate risk
• SEV-4: Low - Minor security concern, informational

=== Response Workflow ===

1. **Detect & Report**
   • Alert via #security-incidents or security@github.com
   • Include: what, when, where, impact assessment
   • Do NOT discuss publicly

2. **Assess & Classify**
   • Security on-call reviews within 15 minutes (SEV-1/2)
   • Assigns severity level
   • Determines response team

3. **Contain & Mitigate**
   • Immediate containment actions
   • Preserve evidence
   • Document all actions
   • Communicate to stakeholders

4. **Investigate & Remediate**
   • Root cause analysis
   • Implement fixes
   • Verify remediation
   • Update security controls

5. **Post-Incident Review**
   • Document lessons learned
   • Update procedures
   • Share findings (where appropriate)

=== Escalation Paths ===

SEV-1: Immediate escalation to:
• Security on-call (PagerDuty)
• Security leadership
• VP Engineering (if data breach suspected)
• Legal (if regulatory implications)

SEV-2/3: Standard escalation via security-ops

=== Communication ===

Internal:
• #security-incidents (private channel)
• Status updates every 30 min (SEV-1), every 2 hours (SEV-2)
• Post-mortem in #security-postmortems

External:
• Coordinated through Security + Comms teams
• Legal review required
• Follow disclosure policy

=== Emergency Contacts ===

• Security On-Call: PagerDuty "Security" schedule
• Security Operations: #security-ops
• Security Leadership: #security-leadership
• Emergency hotline: security@github.com
```

## Agent Response - Step 6: Provide Context

```
📋 Key Points:

✅ Report suspected incidents immediately via #security-incidents
✅ Preserve evidence - don't "fix" things before reporting
✅ Follow severity classification - when in doubt, escalate
✅ Document all actions during incident response
✅ Coordinate external communication through proper channels

🔗 Related Security Documentation:

• Access control policy: https://thehub.github.com/docs/security/access-control-policy.md
• Security operations runbook: https://thehub.github.com/docs/security/security-ops-runbook.md
• Data breach procedures: https://thehub.github.com/docs/security/data-breach-response.md
• Compliance requirements: https://thehub.github.com/docs/security/compliance-standards.md

💬 Security Support:

• Incident reporting: #security-incidents (private)
• General security questions: #security
• Security operations: #security-ops
• Policy questions: #security-compliance

⚠️  Security Reminder:

These procedures contain sensitive operational security information.
• Do not share outside GitHub
• Follow classification guidelines
• Report suspected incidents immediately
• When in doubt, ask in #security
```

## Key Patterns Demonstrated

### 1. Security Context Awareness
- Recognized search was for security policies
- Added appropriate warnings about sensitive content
- Confirmed before retrieving detailed information

### 2. Structured Security Information
- Clear severity classifications
- Step-by-step procedures
- Escalation paths and contacts
- Communication protocols

### 3. Appropriate Handling
- Presented information directly to user
- Included security reminders
- Provided proper contact channels
- Referenced related policies

### 4. Actionable Guidance
- Clear "what to do" instructions
- Contact information for follow-up
- Related documentation links
- Reminders about information sensitivity

## Additional Security Searches

### Finding Compliance Documentation

**Local clone (preferred):**
```bash
find "$THEHUB_ROOT/docs/security" -name '*.md' | grep -i "compliance\|standard"
```

**API fallback:**
```bash
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/security/' | grep -i "compliance\|standard"
```

### Access Control Policies

**Local clone (preferred):**
```bash
grep -ri "access control\|authorization" "$THEHUB_ROOT/docs/security" --include='*.md' -l
```

**API fallback:**
```bash
gh search code "access control OR authorization" \
  --repo github/thehub \
  --path "docs/security/" \
  --filename "*.md"
```

### Security Operations

**Local clone (preferred):**
```bash
find "$THEHUB_ROOT/docs/security" -name '*.md' | grep -i "operation\|runbook"
```

**API fallback:**
```bash
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/security/' | grep -i "operation\|runbook"
```

## Tips for Security Searches

- Always search `docs/security/` for policy documents
- Look for terms: policy, procedure, standard, guide, runbook
- Pay attention to owner_team for the right point of contact
- Check last updated dates for currency
- Cross-reference multiple policies for complete picture
- When in doubt about applying a policy, ask in #security
- Some policies link to more detailed runbooks
- Emergency procedures often have dedicated Slack channels

## Security Search Etiquette

- **Respect sensitivity** - Don't share security docs unnecessarily
- **Use proper channels** - #security-incidents is private for a reason
- **Ask when unsure** - Security team prefers questions over assumptions
- **Follow processes** - Policies exist for good reasons
- **Report issues** - If you find gaps in documentation, let security know
