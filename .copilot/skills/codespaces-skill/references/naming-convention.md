# Codespace Naming Convention

Standard naming pattern for easy identification and organization.

## Pattern

```
<abbreviated-repo> <month><day>
```

**Components:**
- `<abbreviated-repo>`: Shortened repository name
- `<month>`: Lowercase 3-letter month abbreviation (jan, feb, mar, etc.)
- `<day>`: Day of month (1-31, no leading zero)

## Examples

| Repository | Display Name | Created |
|------------|--------------|---------|
| `github/github` | `"gh-gh feb17"` | February 17 |
| `github/github-ui` | `"gh-ui feb11"` | February 11 |
| `github/ops` | `"gh-ops jan29"` | January 29 |
| `github/azure-mcp-codespace` | `"azure-mcp jan29"` | January 29 |
| `myorg/frontend` | `"frontend mar05"` | March 5 |
| `myorg/api` | `"api apr12"` | April 12 |

## Repository Abbreviations

Common abbreviations for GitHub internal repos:

| Full Repository | Abbreviation |
|-----------------|--------------|
| `github/github` | `gh-gh` |
| `github/github-ui` | `gh-ui` |
| `github/ops` | `gh-ops` |

For other repositories:
- Use a short, memorable abbreviation
- Remove redundant words (e.g., `azure-mcp-codespace` → `azure-mcp`)
- Keep it concise but recognizable

## Usage

### When creating a codespace:

```bash
# Use the naming convention in -d flag
gh cs create -R github/github -d "gh-gh feb17"
gh cs create -R github/github-ui -d "gh-ui feb17"
gh cs create -R github/ops -d "gh-ops feb17"
```

### Generating the date programmatically:

**Bash:**
```bash
# Generate today's date in the correct format
TODAY=$(date +"%b %d" | tr 'A-Z' 'a-z' | sed 's/ 0/ /;s/ //')
# Result: "feb17" or "jan29" or "dec05"

# Create with today's date
gh cs create -R github/github -d "gh-gh $TODAY"
```

**Manual:**
- January → jan
- February → feb
- March → mar
- April → apr
- May → may
- June → jun
- July → jul
- August → aug
- September → sep
- October → oct
- November → nov
- December → dec

## Benefits

1. **Easy identification**: Quickly see which repo and when created
2. **Chronological sorting**: Names sort naturally when listed
3. **Cleanup decisions**: Old dates indicate candidates for deletion
4. **Consistent format**: Standard pattern across all codespaces

## When to Delete

Review codespaces by age:
```bash
# List with last used date
gh cs list --json displayName,lastUsedAt,repository

# Delete old codespaces (e.g., older than 14 days)
gh cs delete --days 14
```

Codespaces with older dates in the display name are good candidates for cleanup.
