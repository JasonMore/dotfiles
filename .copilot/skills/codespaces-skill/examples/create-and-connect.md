# Example: Create and Connect to a Codespace

Create a new codespace for a repository and connect to it.

## Scenario

You want to start working on github/github in a cloud development environment.

## User Request

> "Create a codespace for github/github and open it in VS Code"

## Agent Response - Step 1: Check Existing Codespaces

```bash
gh cs list -R github/github --json name,state,displayName
```

Output:
```json
[
  {
    "displayName": "gh-gh feb15",
    "name": "shiny-winner-9w7ww77vgc74p4",
    "state": "Shutdown"
  }
]
```

Found an existing codespace from Feb 15. Creating a new one with today's date.

## Agent Response - Step 2: Create the Codespace with Naming Convention

```bash
# Today is February 17, so use "gh-gh feb17"
gh cs create -R github/github -d "gh-gh feb17"
```

Output:
```
  ✓ Codespaces usage for this repository is paid for by github
test-gh-gh-feb17-wxrxx7wp72v5p9
```

## Agent Response - Step 3: Open in VS Code

```bash
gh cs code -c test-gh-gh-feb17-wxrxx7wp72v5p9
```

## Agent Summary

```
Created and opened codespace for github/github:
- Name: test-gh-gh-feb17-wxrxx7wp72v5p9
- Display name: gh-gh feb17
- Status: Available

VS Code should be opening now. You can also connect via:
- SSH: gh cs ssh -c test-gh-gh-feb17-wxrxx7wp72v5p9
- Browser: gh cs code -c test-gh-gh-feb17-wxrxx7wp72v5p9 -w
```

## Naming Convention Examples

| Repository | Display Name | Pattern |
|------------|--------------|---------|
| github/github | "gh-gh feb17" | `<repo-abbrev> <month><day>` |
| github/github-ui | "gh-ui feb17" | `<repo-abbrev> <month><day>` |
| github/ops | "gh-ops feb17" | `<repo-abbrev> <month><day>` |

**Date format:** Lowercase month abbreviation + day (e.g., "feb17", "jan29", "dec05")

## Alternate: SSH Connection

If the user asked to SSH instead:

```bash
# Create with naming convention
gh cs create -R github/github -d "gh-gh feb17"
# Returns: test-gh-gh-feb17-wxrxx7wp72v5p9

# SSH in
gh cs ssh -c test-gh-gh-feb17-wxrxx7wp72v5p9
```
