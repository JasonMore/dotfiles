# Codespace Workspace Structure

Understanding the directory layout when working in a codespace.

## Default Directory Layout

```
/
├── home/
│   └── vscode/              # User home directory (default SSH landing)
│       ├── .bashrc
│       ├── .gitconfig
│       └── ...
├── workspaces/              # Repository workspace root
│   ├── <repo-name>/         # Main repository
│   │   ├── .git/
│   │   ├── README.md
│   │   └── ...
│   ├── <related-repo>/      # Additional repos (if multi-repo setup)
│   └── .codespaces/         # Codespace metadata
│       ├── .persistedshare/ # Persistent shared data
│       └── shared/          # Temporary shared data
```

## Key Paths

| Path | Description |
|------|-------------|
| `/home/vscode` | User home directory, default SSH landing location |
| `/workspaces/` | Parent directory for all repositories |
| `/workspaces/<repo-name>/` | Main repository root (e.g., `/workspaces/github/`) |
| `/workspaces/.codespaces/` | Codespace metadata and shared resources |

## Multi-Repository Codespaces

Some repositories include related repositories automatically:

**Example: github/github**
```
/workspaces/
├── github/          # Main monorepo
├── github-ui/       # Related frontend repo
└── packages/        # Shared packages
    └── ui-commands/
```

When working with multi-repo codespaces:
- Each repo is a sibling directory under `/workspaces/`
- All repos are pre-cloned and available
- You can navigate between them: `cd /workspaces/<other-repo>`

## Working Directory Behavior

### SSH Connection
```bash
gh cs ssh -c codespace-name
# Starts in: /home/vscode
```

### VS Code Connection
```bash
gh cs code -c codespace-name
# Opens: /workspaces/<repo-name>/
```

### Running Commands via SSH
```bash
# Run in home directory
gh cs ssh -c codespace-name -- pwd
# Output: /home/vscode

# Run in repository
gh cs ssh -c codespace-name -- "cd /workspaces/<repo-name> && pwd"
# Output: /workspaces/<repo-name>
```

## File Copying Paths

When using `gh cs cp`, use the `remote:` prefix:

```bash
# Repository files
gh cs cp local.txt remote:/workspaces/<repo-name>/

# Home directory files
gh cs cp local.txt remote:/home/vscode/

# Shared data
gh cs cp local.txt remote:/workspaces/.codespaces/shared/
```

## Discovering Repository Structure

```bash
# List all repositories in workspace
gh cs ssh -c codespace-name -- "ls -la /workspaces"

# Find the main repository
gh cs ssh -c codespace-name -- "ls -d /workspaces/*/.git | head -1 | xargs dirname"

# Show directory tree
gh cs ssh -c codespace-name -- "tree -L 2 /workspaces"
```

## Persistence

- **Persistent**: `/workspaces/<repo-name>/` (repository files)
- **Persistent**: `/workspaces/.codespaces/.persistedshare/`
- **Persistent**: `/home/vscode/` (home directory)
- **Temporary**: `/workspaces/.codespaces/shared/` (cleared on rebuild)

Repository changes persist across codespace stop/start cycles but are lost if the codespace is deleted.
