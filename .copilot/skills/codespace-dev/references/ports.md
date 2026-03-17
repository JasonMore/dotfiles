# Codespace Ports

## Primary Ports

| Port | Label | Use |
|------|-------|-----|
| **80** | web | Main Rails app. Browse this one |
| **10042** | static-dev | Static asset server |
| **2206** | Copilot API | Copilot dev API |
| **3306** | mysql | Database |
| **8090** | fm-lite | Feature management |
| **8091** | authzd | Authorization |
| **8092** | authnd | Authentication |
| **8025** | mailhog | Email test UI |
| **9222** | chrome-remote-debug | Chrome DevTools Protocol |
| **6006** | react-storybook | Component dev |
| **63315** | vitest | Test runner |
| **8088** | notifyd | Notifications |
| **28081** | spokesd | Spokes |
| **8080** | memory-alpha | Memory Alpha |
| **5800** | memex-vnc | Memex VNC |

## List Ports

```bash
# All ports with browse URLs
gh cs ports -c NAME --json sourcePort,browseUrl,visibility

# What's listening in the codespace
gh cs ssh -c NAME -- "ss -tlnp | grep LISTEN"
```

## Forward Ports

```bash
# Single port
gh cs ports forward 80:8880 -c NAME

# Multiple ports
gh cs ports forward 80:8880 10042:10042 8025:8025 -c NAME

# Change visibility (for sharing)
gh cs ports visibility 80:public -c NAME
```

## Browse URLs

Each port gets a URL like `https://CODESPACE-PORT.app.github.dev`. Get it with:

```bash
gh cs ports -c NAME --json sourcePort,browseUrl | jq -r '.[] | select(.sourcePort==80) .browseUrl'
```

These URLs need GitHub auth. Chrome MCP works if you're logged into GitHub in Chrome.
