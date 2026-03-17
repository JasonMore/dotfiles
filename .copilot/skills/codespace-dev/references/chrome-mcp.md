# Chrome MCP Tools

Use these tools to control the local Chrome browser.

## Navigate

| Tool | What it does |
|------|-------------|
| `navigate_page(url="...")` | Go to URL |
| `navigate_page(type="reload")` | Refresh |
| `navigate_page(type="back")` | Go back |
| `new_page(url="...")` | Open in new tab |
| `list_pages` | List open tabs |
| `select_page(pageId=N)` | Switch tab |

## Read the Page

| Tool | What it does |
|------|-------------|
| `take_snapshot()` | Accessibility tree with uids. Best for finding elements |
| `take_screenshot()` | Visual screenshot. Best for layout checks |
| `evaluate_script(function="() => document.title")` | Run JS |
| `wait_for(text=["some text"])` | Wait for content |

## Interact

| Tool | What it does |
|------|-------------|
| `click(uid="...")` | Click element |
| `fill(uid="...", value="...")` | Type into input or select |
| `fill_form(elements=[...])` | Fill multiple fields at once |
| `type_text(text="...")` | Type into focused element |
| `press_key(key="Enter")` | Press key or combo |
| `hover(uid="...")` | Hover over element |
| `upload_file(uid="...", filePath="...")` | Upload file |
| `handle_dialog(action="accept")` | Handle alert/confirm |

## Debug

| Tool | What it does |
|------|-------------|
| `list_console_messages` | Browser console output |
| `list_network_requests` | Network traffic |
| `get_network_request(reqid=N)` | Request details |

## Typical Flow

```
1. navigate_page(url="http://localhost:8880")
2. wait_for(text=["Sign in"])
3. take_snapshot()              → find element uids
4. fill(uid="login", value="admin")
5. click(uid="submit")
6. take_screenshot()            → verify result
```

Always use `take_snapshot` before interacting. It gives you the uid for each element.
