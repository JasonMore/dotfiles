# Session Portability

Migrate Copilot CLI sessions between local machines and GitHub Codespaces to resume work across environments.

## When to Use This Skill

- You started a Copilot CLI session locally and want to continue it in a Codespace
- You started a session in a Codespace and want to bring it back to your local machine
- You need to pick up where you left off after switching environments

## Prerequisites

- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated
- [Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli) installed
- An active GitHub Codespace for the target repository

## Installation

### Personal Skill

```bash
cp -r session-portability-skill ~/.copilot/skills/
```

### Project Skill

```bash
cp -r session-portability-skill /path/to/repo/.github/skills/
```

## Usage

Trigger this skill by asking Copilot to transfer or migrate a session:

- "Transfer my session to my Codespace"
- "Move this session to Codespace"
- "Resume this session in Codespace"
- "Copy my Codespace session to local"
- "Port my session to local"

## Features

- **Bidirectional transfer** — local → Codespace and Codespace → local
- **Automatic path patching** — rewrites `workspace.yaml` paths for the target environment
- **Security-first** — validates session IDs, warns about sensitive data, never exposes tokens in command arguments
- **Auth guidance** — walks through Codespace authentication setup

## Security

⚠️ Session data (`events.jsonl`) contains full conversation history, which may include source code, secrets, or credentials. The skill:

- Warns users to review session contents before transfer
- Validates session IDs are UUIDs to prevent path traversal
- Never passes tokens via command line arguments
- Recommends `gh auth login` or Codespace secrets for authentication
- Only transfers individual sessions, not the entire `~/.copilot/` directory

See the [Security Considerations section in SKILL.md](SKILL.md#security-considerations) for full details.

## Examples

See [examples/example-transfer.md](examples/example-transfer.md) for a complete walkthrough.

---

**Required:** GitHub CLI (`gh`) with Copilot extension, access to GitHub Codespaces
