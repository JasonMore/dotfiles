# Example: Searching for Engineering Documentation

How to find and retrieve engineering documentation from thehub.

## Scenario

You're working on a new service and need to understand GitHub's deployment procedures and service tier requirements.

## User Request

> "Search thehub for deployment guides and service tier documentation"

## Agent Response - Step 1: Clarify and Search

```
I'll search thehub for deployment and service tier documentation.

Searching in:
• docs/epd/engineering/ (engineering practices)
• docs/products/ (product/service docs)
```

## Agent Response - Step 2: Execute Combined Search

The agent first checks if `github/thehub` is cloned locally. If found, it uses local file operations; otherwise it falls back to the GitHub API.

**Local clone (preferred):**

> `THEHUB_ROOT` is set during the skill's local-clone detection step (see "Local vs API Access" in SKILL.md).

```bash
# Search paths for deployment
echo "=== Deployment guides ==="
find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "deploy"

# Search paths for service tiers
echo "=== Service tier docs ==="
find "$THEHUB_ROOT/docs" -name '*.md' | grep -i "tier"

# Content search
echo "=== Searching content ==="
grep -ri "deployment guide" "$THEHUB_ROOT/docs/epd/engineering" --include='*.md' -l
```

**API fallback:**

```bash
# Search paths for deployment
echo "=== Deployment guides ==="
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/' | grep -i "deploy"

# Search paths for service tiers
echo "=== Service tier docs ==="
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/' | grep -i "tier"

# Content search
echo "=== Searching content ==="
gh search code "deployment guide" \
  --repo github/thehub \
  --path "docs/epd/engineering/" \
  --filename "*.md" \
  --limit 5
```

## Agent Response - Step 3: Present Results

```
📚 Found relevant documentation:

1. 📄 Production Deployment Guide
   🔗 https://thehub.github.com/docs/epd/engineering/deployment-guide.md
   Owner: engineering-productivity (#eng-prod)
   
   Topics covered:
   • Pre-deployment checklist and requirements
   • Automated deployment via GitHub Actions
   • Approval workflows and gates
   • Rollback procedures
   • Post-deployment verification

2. 📄 Service Tier Definitions
   🔗 https://thehub.github.com/docs/epd/engineering/service-tiers.md
   Owner: engineering-standards (#eng-standards)
   
   Topics covered:
   • Service tier classifications (Tier 0-4)
   • SLA requirements per tier
   • Support expectations
   • Infrastructure requirements
   • Monitoring and alerting standards

3. 📄 Deployment Best Practices
   🔗 https://thehub.github.com/docs/epd/engineering/deployment-practices.md
   Owner: platform-engineering (#platform-eng)
   
   Topics covered:
   • Blue-green deployments
   • Canary releases
   • Feature flags
   • Database migrations
   • Zero-downtime deployments
```

## Agent Response - Step 4: Retrieve Key Details

```
Would you like me to:

1. Fetch and summarize the deployment guide?
2. Show the service tier requirements table?
3. Find service-specific deployment docs?
4. Search for related runbooks?

Let me know which would be most helpful!
```

## User Follow-up

> "Show me the service tier requirements"

## Agent Response - Step 5: Fetch and Present Details

**Local clone (preferred):**

```bash
# Read the service tier doc
cat "$THEHUB_ROOT/docs/epd/engineering/service-tiers.md"
```

**API fallback:**

```bash
# Fetch the service tier doc
gh api "repos/github/thehub/contents/docs/epd/engineering/service-tiers.md" \
  --jq '.content' | base64 -d
```

```
📄 Service Tier Definitions

🔗 https://thehub.github.com/docs/epd/engineering/service-tiers.md
Owner: engineering-standards (#eng-standards)

=== Service Tier Overview ===

| Tier | Description | SLA | Example Services |
|------|-------------|-----|------------------|
| Tier 0 | Mission critical | 99.99% | github.com, API |
| Tier 1 | Core services | 99.9% | Actions, Packages |
| Tier 2 | Important features | 99.5% | Copilot, Codespaces |
| Tier 3 | Standard features | 99.0% | Projects, Wikis |
| Tier 4 | Best effort | No SLA | Experimental features |

=== Requirements by Tier ===

Tier 0-1 Requirements:
• 24/7 on-call rotation
• Automated deployment with rollback
• Multi-region redundancy
• Real-time monitoring and alerting
• Incident response runbooks

Tier 2-3 Requirements:
• Business hours on-call
• Automated deployment
• Monitoring and alerting
• Basic incident procedures

Tier 4 Requirements:
• Best effort support
• Standard deployment
• Basic health checks

=== Determining Your Service Tier ===

Consider:
• Customer impact of outages
• Revenue impact
• User base size
• Regulatory requirements
• Data sensitivity

Contact #eng-standards for tier determination.
```

## Agent Response - Step 6: Suggest Next Steps

```
📝 Key Takeaways:

• New services should start at Tier 3 and move up based on criticality
• Each tier has specific deployment and monitoring requirements
• Tier 0-1 services require 24/7 coverage and advanced deployment practices

🔗 Related Documentation:

• Deployment guide: https://thehub.github.com/docs/epd/engineering/deployment-guide.md
• SLA standards: https://thehub.github.com/docs/products/sla-standards.md
• Monitoring setup: https://thehub.github.com/docs/epd/engineering/observability.md

💬 Questions?

• Service tier determination: #eng-standards
• Deployment support: #eng-prod
• General engineering: #eng-help
```

## Key Patterns Demonstrated

### 1. Multi-Doc Search
- Searched for related topics simultaneously
- Presented multiple relevant docs
- Let user choose what to explore further

### 2. Structured Presentation
- Clear document hierarchy
- Links to source material
- Owner and contact information
- Key topics outlined

### 3. Interactive Follow-up
- Offered specific next actions
- Fetched detailed content on request
- Provided related documentation
- Suggested contact channels

### 4. Context-Aware Navigation
- Knew to search engineering directories
- Understood relationship between deployment and service tiers
- Connected to related topics (SLAs, monitoring)

## Alternative Search Approaches

### By Directory

**Local clone (preferred):**
```bash
# List all engineering docs
find "$THEHUB_ROOT/docs/epd/engineering" -name '*.md' | sort
```

**API fallback:**
```bash
# List all engineering docs
gh api 'repos/github/thehub/git/trees/main?recursive=1' \
  --jq '.tree[].path' | grep '^docs/epd/engineering/' | sort
```

### By Content Keywords

**Local clone (preferred):**
```bash
# Search for specific concepts
grep -ri "blue-green deployment" "$THEHUB_ROOT/docs" --include='*.md' -l
```

**API fallback:**
```bash
# Search for specific concepts
gh search code "blue-green deployment" \
  --repo github/thehub \
  --filename "*.md"
```

### By Service Name

**Local clone (preferred):**
```bash
# Find docs for a specific service
grep -ri "Actions deployment" "$THEHUB_ROOT/docs" --include='*.md' -l
```

**API fallback:**
```bash
# Find docs for a specific service
gh search code "Actions deployment" \
  --repo github/thehub \
  --path "docs/" \
  --filename "*.md"
```

## Tips for Engineering Searches

- Start with `docs/epd/engineering/` for practices and standards
- Check `docs/products/` for service-specific documentation
- Look for "guide", "practice", "standard" in filenames
- Parse frontmatter for owner_team to find the right contacts
- Cross-reference with runbooks and operational docs
