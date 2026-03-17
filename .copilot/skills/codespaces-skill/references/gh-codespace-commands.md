# gh codespace Command Reference

Quick reference for all `gh codespace` (alias: `gh cs`) subcommands.

## Subcommands

| Command | Description |
|---------|-------------|
| `gh cs create` | Create a codespace |
| `gh cs list` | List codespaces |
| `gh cs code` | Open in VS Code |
| `gh cs ssh` | SSH into a codespace |
| `gh cs stop` | Stop a running codespace |
| `gh cs delete` | Delete codespaces |
| `gh cs view` | View codespace details |
| `gh cs ports` | List ports in a codespace |
| `gh cs ports forward` | Forward ports |
| `gh cs ports visibility` | Change port visibility |
| `gh cs cp` | Copy files between local and codespace |
| `gh cs logs` | Access codespace logs |
| `gh cs rebuild` | Rebuild a codespace |
| `gh cs edit` | Edit codespace settings |
| `gh cs jupyter` | Open in JupyterLab |

## Create Flags

| Flag | Description |
|------|-------------|
| `-R, --repo` | Repository (owner/repo) |
| `-b, --branch` | Branch name |
| `-m, --machine` | Machine type |
| `-d, --display-name` | Display name (max 48 chars) |
| `-l, --location` | Region (EastUs, SouthEastAsia, WestEurope, WestUs2) |
| `--idle-timeout` | Idle timeout (e.g., "10m", "1h") |
| `--retention-period` | Auto-delete after shutdown (max 30 days) |
| `--devcontainer-path` | Path to devcontainer.json |
| `-s, --status` | Show creation status |
| `-w, --web` | Create from browser |

## SSH Flags

| Flag | Description |
|------|-------------|
| `-c, --codespace` | Codespace name |
| `-R, --repo` | Filter by repo |
| `--config` | Output OpenSSH config |
| `--profile` | SSH profile name |
| `-d, --debug` | Enable debug logging |

## Code (VS Code) Flags

| Flag | Description |
|------|-------------|
| `-c, --codespace` | Codespace name |
| `-R, --repo` | Filter by repo |
| `--insiders` | Use VS Code Insiders |
| `-w, --web` | Use VS Code in browser |

## List JSON Fields

`createdAt`, `displayName`, `gitStatus`, `lastUsedAt`, `machineName`, `name`, `owner`, `repository`, `state`, `vscsTarget`

## View JSON Fields

`billableOwner`, `createdAt`, `devcontainerPath`, `displayName`, `environmentId`, `gitStatus`, `idleTimeoutMinutes`, `lastUsedAt`, `location`, `machineDisplayName`, `machineName`, `name`, `owner`, `prebuild`, `recentFolders`, `repository`, `retentionExpiresAt`, `retentionPeriodDays`, `state`, `vscsTarget`

## Port Visibility Options

- `private` - Only you can access (default)
- `org` - Members of the organization can access
- `public` - Anyone with the URL can access
