# CLI Flow Detail

## Pipeline stages (in order)

1. **resolve-codespace-name** — Run
   `gh codespace list --json name,displayName,repository,state` and resolve
   `--codespace` to an actual codespace `name`. An exact `name` match wins
   immediately (no ambiguity check needed; names are already unique).
   Otherwise the value is matched against `displayName`; exactly one match
   resolves, zero or multiple matches both fail outright rather than
   guessing. Every later stage uses this resolved name, never the raw
   `--codespace` value.
2. **detect-gateway** — Check Gateway.app candidates (both `Gateway.app` and
   `JetBrains Gateway.app`, under `/Applications` and `~/Applications`, or
   `--gateway-app-path`). If missing and `--install-gateway` was not passed,
   stop and ask the user to confirm `brew install --cask jetbrains-gateway`.
   If confirmed, pass `--install-gateway` and re-run. The resolved app path
   is verified to exist (including after a fresh install) and carried
   through the whole pipeline for the final `open` call.
3. **open-vscode** — Run `gh codespace code -c NAME`. This mirrors how a
   user would normally open the codespace in VS Code and forces it to
   start. VS Code itself owns Codespaces port discovery/forwarding once it
   connects; this script only needs the codespace running, not any specific
   forwarded port, and does not read VS Code's output.
4. **refresh-ssh-config / refresh-ssh-codespaces** — Run
   `gh codespace ssh -c NAME --config`, fetching only this one codespace's
   `Host` block. `gh codespace ssh --config` with no `-c` regenerates every
   visible codespace at once, but exits non-zero and skips any codespace
   that isn't "Available" (`skipping unavailable codespace <name>: Shutdown`)
   — that failure is unrelated to whether the *target* codespace is fine,
   so fetching just the target sidesteps it entirely. The fetched block is
   parsed and validated (stage 5, below) **before** any write happens, then
   merged into the existing `~/.ssh/codespaces` file: only the block(s)
   matching this codespace's name marker (`cs.NAME` / `cs.NAME.*`) are
   replaced; every other codespace's block — including ones for codespaces
   that are currently Shutdown — is kept, in its original order. If the
   file doesn't exist yet, it's created containing just the new block. The
   result is written atomically (temp file in the same directory, then
   `os.replace`, mode `0600`). This is not a full regeneration: it never
   trusts that every codespace is reachable, and it never drops a block for
   a codespace that wasn't just fetched. The merge operates on ordered
   segments, not a blocks-only rebuild: any preamble before the first
   `Host` line (comments, global directives) and any non-matching block
   (including a `Host *` wildcard block) are replayed byte-for-byte in
   their original position; only the matching block is replaced, in
   place, at its original position — it is never moved to the end of the
   file. If no existing block matches, the new block is appended after
   everything else, since there's no original position to preserve.
5. **ensure-ssh-include** — Append `Include ~/.ssh/codespaces` to the top of
   `~/.ssh/config` only if an equivalent `Include` line (whitespace-insensitive)
   isn't already present. Atomic write, same technique as above. All existing
   lines are preserved byte-for-byte. This follows the official `gh` example
   directly: the include stays a separate file, never merged into the main
   config.
6. **parse-ssh-target** — Extract the `Host cs.NAME.<ref>` alias and its
   `User` value for this codespace out of the single-codespace config text
   from stage 4, before that stage's write happens. Fails if zero or more
   than one matching block is found in the fetched output — a malformed or
   ambiguous fetch is caught here, never reaches `~/.ssh/codespaces`.
7. **verify-ssh-connection** — `ssh -- <alias> true`. Confirms the alias
   actually connects before any backend work happens over it, so a
   connectivity failure is never confused with "no backend installed yet".
8. **detect-arch** — `ssh -- <alias> uname -m`, unless `--arch` was passed
   explicitly. Never assumes `x86_64`; only runs once the SSH alias is
   verified to actually connect.
9. **ensure-backend** — Over the verified SSH alias, probe for an existing,
   verified WebStorm backend in one round trip:
   `ssh -- <alias> bash -lc '<script>'`, where `<script>` loops over every
   `<dist-dir>/WebStorm-*/bin/remote-dev-server.sh` glob match (restricted to
   `WebStorm-*`, never any other JetBrains product sharing the dist dir; a
   stale or partial first match never masks a later valid one) and echoes
   the first one whose install's `product-info.json` greps
   `"productCode" : "WS"`. Nothing is ever echoed unless that check passes.
   If found, reuse it (no network call).
   Otherwise:
   - `curl -fsSL` the JetBrains releases API
     (`https://data.services.jetbrains.com/products/releases?code=WS&latest=true&type=release`)
     locally, and pick `downloads.linux.link` or `downloads.linuxARM64.link`
     based on the detected/explicit arch.
   - `ssh -- <alias> ...` runs `mkdir -p <dist-dir> && curl -fsSL <url> -o
     <dist-dir>/webstorm-backend-<build>.tar.gz && tar -xzf ... && rm -f
     ...`. It deliberately does **not** guess or echo the extracted
     directory name: the tarball extracts to `WebStorm-<build>` (JetBrains's
     internal build number, e.g. `262.8665.341`), not `WebStorm-<version>`
     (the calendar-style marketing version used only in the download
     filename), and that naming isn't guaranteed to stay stable either.
   - After extraction, the script re-runs the same probe from this stage to
     discover and re-verify the real installed path. If that re-probe finds
     nothing, `install-backend` fails rather than trusting a guess.
10. **ensure-remote-dev-server-running** — `remote-dev-server.sh run` is a
    long-lived server that never exits, so it is never waited on
    synchronously. Instead:
    - Query `ssh -- <alias> bash -lc '<backend-path> status'` first. Its
      output is prefixed (or trailed) by live-observed diagnostic noise
      (`error: XDG_RUNTIME_DIR is invalid...`) around a literal `STATUS:`
      marker followed by a JSON object (`appPid`, `backendUnresponsive`,
      `idePath`, `gatewayLink`, ...). Parsing uses
      `json.JSONDecoder().raw_decode()` on the text right after the
      marker, which reads only the first complete JSON object and ignores
      whatever noise follows it (pretty-printed/multi-line JSON with
      trailing stderr text appended after it is live-confirmed to parse
      correctly this way); the script searches combined stdout+stderr for
      the marker rather than assuming which stream carries it, and treats
      a missing/unparsable marker as "nothing running yet", never a hard
      failure.
    - If that status already reports a ready, responsive backend for this
      same project, its `gatewayLink` is reused immediately and no new
      backend is started. The project path used for that comparison comes
      from a literal `projectPath` JSON key if present, else the
      `projectPath` query parameter parsed out of `gatewayLink`'s own URL
      fragment with `urllib.parse`. **`idePath` is never used as a
      project-path stand-in** — live evidence shows it names the WebStorm
      backend *install* directory (e.g. `.../WebStorm-262.21148.7`), not
      the project; treating it as one previously caused false project
      mismatches and duplicate backend starts. Missing project info
      (neither source present) is never treated as a mismatch, only
      conflicting info is. `modalDialogIsOpened` is not inspected at all —
      it reflects Gateway/IDE UI state, not backend health, and must never
      gate reuse either way.
    - An existing backend reporting `backendUnresponsive: true` fails the
      stage immediately rather than being reused or silently replaced.
    - Otherwise, starts the backend detached over one SSH round trip:
      `bash -lc 'mkdir -p <logdir>; nohup <backend-path> run <project-path>
      --ssh-link-host <alias> --ssh-link-user <user> --ssh-link-port 22 >
      <per-project-log> 2>&1 < /dev/null & disown'`. This returns almost
      immediately — the `&`/`disown` are what let it survive the SSH
      session exiting; `;` (not `&&`) between `mkdir` and the backgrounded
      job keeps the two effects clearly separate.
    - Then polls the same `status` command every `--poll-interval` seconds
      (default 3s) until it reports a ready, matching `gatewayLink`, up to
      `--start-timeout` seconds (default 180s) total, at which point it
      fails with the last observed status in the error message. No other
      flags are passed to `remote-dev-server.sh`; nothing invents or
      assumes undocumented EULA-bypass flags (see "Manual, one-time steps"
      below), and the script never calls it with `--help` — that's treated
      as an unknown launch config and surfaces as a WebStorm error dialog
      on a real backend, not a usage message.
11. **open-gateway-link** — `open -a <Gateway.app> <link>` when the Gateway
    app path resolved in stage 2 is known, targeting it explicitly. Falls
    back to plain `open <link>` only if no local Gateway.app path was
    resolved (the registered `jetbrains-gateway://` URL handler can fail to
    resolve by name, e.g. for an app installed as `Gateway.app`). No
    AppleScript, no Computer Use, no UI automation either way. This stage
    only dispatches the link — see "Manual, one-time steps" below for what
    still happens inside Gateway after that.

## Auth: `--use-keyring-auth`

Some environments (for example, a Copilot agent sandbox) inject
`GH_TOKEN`/`GITHUB_TOKEN` into every subprocess for their own purposes. If
that injected token lacks the `codespace` scope, it shadows a correctly
scoped token already in the user's `gh` keyring, and every `gh codespace
...` call in this pipeline fails. `--use-keyring-auth` builds a copy of
`os.environ` with `GH_TOKEN` and `GITHUB_TOKEN` removed and passes it as
`env=` to every `subprocess.run` call this script makes (`gh`, `ssh`,
`curl`, `open`, `brew`) — never to the running script's own process, which
keeps its real environment untouched. Because `env=` only affects a direct
child, and any grandchild process (notably `ssh`'s `ProxyCommand`, which
itself execs `gh codespace ssh --stdio ...`) inherits whatever environment
its parent process has, stripping the two vars on the direct `subprocess.run`
call is sufficient to cover the `ProxyCommand` case too, with no special
casing needed for it. When the flag is omitted, `env=None` is passed
instead, which is full, unmodified inheritance — the default, unchanged
behavior. `--dry-run` prints which auth mode would be used (`inherited
environment` or `--use-keyring-auth`, stripped-var names only) but never
prints token values.

## Shell-quoting rule

Every value interpolated into a remote command is passed through
`sh_quote()` (a `shlex.quote()` wrapper) except path values that start with
`~`, which go through `shell_path()` instead. `shell_path()` leaves a
leading `~` or `~user` segment unquoted so the remote shell still expands
it to `$HOME`, and `shlex.quote()`-escapes everything after it — but only
when the `~`/`~user` prefix matches a strict, safe charset (letters,
digits, `_`, `.`, `-`). Anything else (`~$(...)`, embedded quotes or
backticks before the first `/`) raises `ValueError` instead of being
emitted as unsafe shell text; `main()` reports this as
`[invalid-input] ...` and exits non-zero. Plain `shlex.quote()` on a
`~`-prefixed string would wrap the whole path in single quotes and
silently defeat tilde expansion, which is why `shell_path()` exists at
all.

Every `ssh` invocation puts `--` immediately after `ssh` and before the
target alias: `["ssh", "--", alias, ...remote command...]`. `--` must end
ssh's own option parsing *before* the hostname, not after it —
`["ssh", alias, "--", "true"]` makes ssh treat `-- true` as the remote
command string itself (malformed); `["ssh", "--", alias, "true"]` runs
`true` as the remote command, with `alias` protected from being misparsed
as an ssh option even if it happens to start with `-`.

OpenSSH does not preserve our Python list's argv boundaries once the
command reaches the remote side: everything after the destination is
joined with a single space and handed, as one string, to the remote
user's login shell to parse and execute. A multi-word/multi-statement
script (the probe loop, the install chain, the detached remote-dev-server
start, the status check) can never be passed as its own bare argv element — the
remote shell would parse its internal spaces, quotes, and keywords
itself instead of ever handing it to `bash -lc` as a single argument
(this is exactly how a live `zsh:1: parse error near do` surfaced).
`build_ssh_remote_shell_command()` fixes this by quoting the whole
assembled script with `sh_quote()` *before* it becomes one argv element,
so the text ssh reconstructs on the wire is `bash -lc '<script>'` — one
quoted token the remote shell hands to `-lc` intact. `verify-ssh-connection`
and `detect-arch` stay as plain, unquoted multi-word commands (`true`,
`uname -m`) since they carry no metacharacters and need no such wrapping.

## Why generic SSH, not the JetBrains GitHub Codespaces plugin

That plugin is deprecated and unmaintained. This skill uses the same SSH
alias any other tool would use — `ssh cs.NAME.<ref>` — via a normal
`~/.ssh/config` `Include`, so Gateway's generic "Connect via SSH" flow works
without any codespace-specific plugin.

## `--dry-run` and the resolved-name placeholder

`build_plan()` is pure: it never calls `subprocess.run` or `urlopen`, so it
cannot know whether `--codespace` is already the exact name or an
unresolved `displayName` — that only gets resolved live, by the
`gh codespace list ...` stage. So `--dry-run` prints the raw `--codespace`
value only in that one resolve-list line's description, and prints the
literal placeholder `<resolved-codespace-name>` everywhere else (the SSH
alias, `gh codespace code`, `gh codespace ssh --config`, and every later
stage) instead of guessing. A real run substitutes the actual resolved
name at that point and proceeds normally.

## Fail-fast contract

Every stage raises `StageError(stage, message)` on failure. Nothing catches
and silently retries with a different codespace, repo, backend, or release.
`main()` prints `[<stage>] <message>` to stderr and exits non-zero.
`shell_path()` validation failures raise `ValueError` before any stage
runs, and `main()` reports those as `[invalid-input] <message>` separately.

## Manual steps (not automated)

- Accepting the Gateway/WebStorm EULA on first launch.
- Activating a WebStorm license (JetBrains account login or license key) the
  first time the backend runs interactively.
- `remote-dev-server.sh` may also prompt on its very first invocation inside
  a brand-new codespace. No additional CLI flags or documented
  EULA-bypass behavior for it could be confirmed, so none are assumed or
  invented here — if a first run hangs or fails, SSH in once, run the
  backend interactively to get past the prompt, then retry.
- **Every run, not just the first:** observed with Gateway 2025.3, opening
  a valid `jetbrains-gateway://connect#...&deploy=false` link prefills
  Gateway's "Connect to SSH" form (host, user, port) but does not click its
  own **Check Connection and Continue** button or launch JetBrains Client
  automatically. The user clicks Continue themselves. The deep link is
  confirmed to get the form to a correctly prefilled, ready-to-confirm
  state — it does not, by itself, complete the connection or open the
  project.
- **After the user clicks Continue:** Gateway takes over completely. It
  uploads its own worker binary to the codespace and launches/matches the
  local JetBrains Client itself. This skill does not install, upload, or
  otherwise manage either the worker binary or JetBrains Client — that is
  entirely Gateway's responsibility, separate from the WebStorm
  `remote-dev-server.sh` backend this skill installs and starts in stages
  6–10. Confirmed live on Gateway 2025.3: a 2.44 MB worker binary upload
  followed by WebStorm opening successfully, with no changes needed to
  this skill.

These require UI interaction inside the Gateway/WebStorm window itself, which
this skill does not drive.
