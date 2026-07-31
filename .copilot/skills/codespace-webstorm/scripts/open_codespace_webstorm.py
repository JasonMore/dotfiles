#!/usr/bin/env python3
"""Connect an existing GitHub Codespace to WebStorm via JetBrains Gateway.

Pipeline (each stage fails hard, with no silent fallback):

0. Resolve ``--codespace`` to the actual codespace ``name`` via
   ``gh codespace list``: an exact ``name`` match wins outright, otherwise a
   unique ``displayName`` match is used. Zero or ambiguous matches fail
   rather than guessing.
1. Detect JetBrains Gateway.app locally. Install only if ``--install-gateway``
   was passed (the caller must get user confirmation first).
2. Open the codespace in VS Code (``gh codespace code``). VS Code owns port
   discovery/forwarding once it connects; this script only needs the
   codespace running, not any specific forwarded port.
3. Fetch this one codespace's SSH config block with
   ``gh codespace ssh -c NAME --config`` and merge/replace only its ``Host``
   block into the existing ``~/.ssh/codespaces`` (every other codespace's
   block -- including Shutdown ones -- is preserved byte-for-byte). Make
   sure ``~/.ssh/config`` includes it exactly once.
4. Parse the codespace's SSH alias/user from the fetched block (before the
   merge/write above happens), then verify the SSH connection actually
   works before doing anything else remote.
5. Detect the codespace's CPU architecture (``uname -m``) unless the caller
   passed ``--arch`` explicitly.
6. Reuse an installed WebStorm backend on the codespace (verified via
   ``product-info.json``), or resolve the latest release from the
   JetBrains API and install it. The installed path is always rediscovered
   and verified after extraction; a guessed path is never trusted.
7. Run ``remote-dev-server.sh`` on the codespace and parse the
   ``jetbrains-gateway://connect#...`` link from its output.
8. Open that link locally with ``open -a <Gateway.app>`` (falling back to
   plain ``open`` only if no local Gateway.app path is known). No
   AppleScript/UI automation.

Pass ``--use-keyring-auth`` when an injected ``GH_TOKEN``/``GITHUB_TOKEN``
lacks the ``codespace`` scope: it strips those two variables from every
child subprocess's environment (gh, ssh, curl, and anything ssh's
``ProxyCommand`` execs), without touching this process's own environment,
so ``gh`` falls back to its keyring-stored credentials.

All external effects (subprocess calls, HTTP GETs) go through a ``Runner``
so tests can substitute fakes. Nothing here uses AppleScript, osascript, or
any UI automation: the only "GUI" touch point is handing a URL to ``open``.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, List, Optional, Sequence

PRODUCT_CODE = "WS"
PRODUCT_NAME = "WebStorm"
RELEASES_URL = (
    "https://data.services.jetbrains.com/products/releases"
    "?code={code}&latest=true&type=release"
)
SSH_INCLUDE_LINE = "Include ~/.ssh/codespaces"
SSH_MATCH_BLOCK = "Match all\nInclude ~/.ssh/codespaces\n"
DEFAULT_DIST_DIR = "~/.cache/JetBrains/RemoteDev/dist"
DEFAULT_SSH_LINK_PORT = 22
DEFAULT_START_TIMEOUT_SECONDS = 180.0
DEFAULT_POLL_INTERVAL_SECONDS = 3.0
# remote-dev-server.sh run is a long-lived server process that never exits
# on its own, so its own stdout is never waited on. Its per-project log,
# once started detached, lives here instead.
REMOTE_DEV_SERVER_LOG_DIR = "~/.cache/JetBrains/RemoteDev/logs"
STATUS_MARKER = "STATUS:"
GATEWAY_APP_CANDIDATES = (
    Path("/Applications/JetBrains Gateway.app"),
    Path("/Applications/Gateway.app"),
    Path.home() / "Applications" / "JetBrains Gateway.app",
    Path.home() / "Applications" / "Gateway.app",
)
GATEWAY_LINK_RE = re.compile(r"jetbrains-gateway://connect#\S+")
AUTH_ENV_VARS_TO_STRIP = ("GH_TOKEN", "GITHUB_TOKEN")
# --dry-run never calls a subprocess, so it cannot run 'gh codespace list'
# and cannot know whether --codespace is already the actual name or a
# displayName that still needs resolving. Every command shown for a stage
# that runs AFTER the live resolve-codespace-name stage uses this
# placeholder instead of the raw --codespace value, so the plan never
# prints a possibly-wrong displayName as if it were already resolved.
RESOLVED_CODESPACE_PLACEHOLDER = "<resolved-codespace-name>"


class StageError(Exception):
    """Raised when a pipeline stage fails. Carries the stage name so the
    caller can report exactly where things broke, with no silent fallback.
    """

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(f"[{stage}] {message}")
        self.stage = stage
        self.message = message


@dataclasses.dataclass
class CommandResult:
    args: List[str]
    returncode: int
    stdout: str
    stderr: str


def _child_env(strip_auth_env: bool) -> Optional[dict]:
    """Return the env to pass to a child subprocess: ``None`` to simply
    inherit the parent process's environment unmodified (the default), or
    a *copy* of it with ``GH_TOKEN``/``GITHUB_TOKEN`` removed when
    ``strip_auth_env`` is True. Never mutates ``os.environ`` itself, so
    the parent process (and anything else it spawns later) keeps its own
    environment intact either way.
    """
    if not strip_auth_env:
        return None
    return {k: v for k, v in os.environ.items() if k not in AUTH_ENV_VARS_TO_STRIP}


def _decode_partial_output(data: object) -> str:
    """``subprocess.TimeoutExpired.stdout``/``.stderr`` can be ``None``,
    ``str``, or (observed in practice, even with ``text=True``) raw
    ``bytes`` captured before the timeout fired. Normalize all three to a
    plain ``str`` so callers never have to special-case it.
    """
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", "replace")
    return data


def _run_command_impl(
    cmd: Sequence[str],
    *,
    input_text: Optional[str] = None,
    timeout: Optional[int] = None,
    strip_auth_env: bool = False,
) -> CommandResult:
    try:
        proc = subprocess.run(
            list(cmd),
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_child_env(strip_auth_env),
        )
    except FileNotFoundError as exc:
        raise StageError("run-command", f"executable not found: {cmd[0]} ({exc})")
    except subprocess.TimeoutExpired as exc:
        # A command can outlive its timeout by design (e.g. a long-lived
        # remote server process). Turn this into an ordinary non-zero
        # CommandResult -- preserving whatever partial output was
        # captured -- instead of letting a raw traceback escape. Callers
        # decide what a timeout means for their own stage and raise
        # their own StageError.
        stderr = _decode_partial_output(exc.stderr)
        stderr += f"\n[run-command] timed out after {timeout}s"
        return CommandResult(list(cmd), 124, _decode_partial_output(exc.stdout), stderr)
    return CommandResult(list(cmd), proc.returncode, proc.stdout, proc.stderr)


def _default_run_command(
    cmd: Sequence[str],
    *,
    input_text: Optional[str] = None,
    timeout: Optional[int] = None,
) -> CommandResult:
    return _run_command_impl(cmd, input_text=input_text, timeout=timeout, strip_auth_env=False)


def make_run_command(strip_auth_env: bool) -> Callable[..., CommandResult]:
    """Build a ``run_command`` callable for ``Runner``. When
    ``strip_auth_env`` is True, every command this callable runs (gh, ssh,
    curl, tar, open, brew -- and anything ssh's ``ProxyCommand`` execs,
    since it inherits this same child env) is launched with ``GH_TOKEN``
    and ``GITHUB_TOKEN`` removed from *its* environment only. This is what
    ``--use-keyring-auth`` uses to force ``gh`` to fall back to its
    keyring-stored credentials instead of an injected token that may lack
    the ``codespace`` scope.
    """

    def _run_command(
        cmd: Sequence[str],
        *,
        input_text: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        return _run_command_impl(
            cmd, input_text=input_text, timeout=timeout, strip_auth_env=strip_auth_env
        )

    return _run_command


def _default_http_get(url: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
        return resp.read()


@dataclasses.dataclass
class Runner:
    """Dependency boundary for all external effects. Tests inject fakes for
    ``run_command``, ``http_get``, ``sleep`` and ``monotonic`` instead of
    touching the real system or the real clock (the latter two make the
    remote-dev-server status poll loop instant and deterministic in tests).
    """

    run_command: Callable[..., CommandResult] = _default_run_command
    http_get: Callable[[str], bytes] = _default_http_get
    sleep: Callable[[float], None] = time.sleep
    monotonic: Callable[[], float] = time.monotonic


@dataclasses.dataclass
class SSHTarget:
    alias: str
    user: str


@dataclasses.dataclass
class ReleaseInfo:
    version: str
    build: str
    download_url: str


def sh_quote(value: str) -> str:
    """Shell-quote a single value for embedding in a remote command string."""
    return shlex.quote(value)


_TILDE_PATH_RE = re.compile(r"^~([A-Za-z0-9_.-]*)(/.*)?$")


def shell_path(path: str) -> str:
    """Shell-quote a remote path, keeping a leading ``~`` or ``~user``
    unquoted so the remote shell still expands it to the home directory.
    The remainder is quoted normally, so this stays safe for paths with
    spaces or shell metacharacters.

    Only a bare ``~`` or a ``~user`` prefix made of a strict, safe username
    charset (letters, digits, ``_``, ``.``, ``-``) is ever left unquoted.
    Anything else (e.g. ``~$(...)``, embedded quotes/backticks before the
    first ``/``) is rejected outright rather than emitted as unsafe shell
    text.
    """
    if not path.startswith("~"):
        return sh_quote(path)
    match = _TILDE_PATH_RE.match(path)
    if not match:
        raise ValueError(f"unsafe or unsupported tilde path: {path!r}")
    user, rest = match.group(1), match.group(2) or ""
    prefix = f"~{user}"
    if rest in ("", "/"):
        return prefix + rest
    return f"{prefix}/{sh_quote(rest[1:])}"


# ---------------------------------------------------------------------------
# Stage 0: resolve the actual codespace name (not its display name)
# ---------------------------------------------------------------------------


def build_codespace_list_command() -> List[str]:
    return ["gh", "codespace", "list", "--json", "name,displayName,repository,state"]


def resolve_codespace_name(requested: str, runner: Runner) -> str:
    """Resolve ``requested`` (as passed to ``--codespace``) to the actual
    codespace ``name``.

    Every other stage needs the real ``name`` (e.g.
    ``stage-ui-for-you-analytics-7wvww9grg3xqp6``), not the human-friendly
    ``displayName`` VS Code shows in its window title (e.g.
    ``stage-ui-for-you-analytics``); passing a displayName straight to
    ``gh codespace ssh -c`` / ``gh codespace code -c`` fails. This always
    lists codespaces and resolves ``requested`` two ways:

    1. An exact ``name`` match always wins, with no ambiguity check -
       actual names are already unique.
    2. Otherwise, ``requested`` is matched against ``displayName``. If
       exactly one codespace has that display name, its real name is
       used. Zero or multiple matches both fail outright: this never
       guesses which codespace a duplicate/absent display name means.
    """
    cmd = build_codespace_list_command()
    result = runner.run_command(cmd, timeout=60)
    if result.returncode != 0:
        raise StageError(
            "resolve-codespace-name", result.stderr.strip() or "gh codespace list failed"
        )
    try:
        codespaces = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise StageError(
            "resolve-codespace-name", f"could not parse 'gh codespace list' JSON: {exc}"
        )

    for cs in codespaces:
        if cs.get("name") == requested:
            return requested

    display_matches = [cs.get("name") for cs in codespaces if cs.get("displayName") == requested]
    if len(display_matches) == 1:
        return display_matches[0]
    if not display_matches:
        raise StageError(
            "resolve-codespace-name",
            f"no codespace found with name or display name '{requested}'; run "
            "'gh codespace list' to see available codespaces and pass the exact name",
        )
    raise StageError(
        "resolve-codespace-name",
        f"display name '{requested}' matches multiple codespaces "
        f"({', '.join(display_matches)}); pass the exact --codespace <name> instead",
    )


# ---------------------------------------------------------------------------
# Stage 1: JetBrains Gateway detection / install
# ---------------------------------------------------------------------------


def find_gateway_app(
    candidates: Sequence[Path] = GATEWAY_APP_CANDIDATES,
) -> Optional[Path]:
    """Return the first existing Gateway.app path among ``candidates``, or
    None if none of them exist.
    """
    for path in candidates:
        if path.exists():
            return path
    return None


def detect_gateway_installed(
    candidates: Sequence[Path] = GATEWAY_APP_CANDIDATES,
) -> bool:
    return find_gateway_app(candidates) is not None


def ensure_gateway(
    runner: Runner,
    *,
    install_gateway: bool,
    candidates: Sequence[Path] = GATEWAY_APP_CANDIDATES,
) -> Path:
    """Return the path to the installed Gateway.app, installing it via
    Homebrew first if missing and the caller passed ``install_gateway=True``
    (the caller must get user confirmation before doing that). Verifies the
    app actually exists after installing rather than assuming success.
    """
    existing = find_gateway_app(candidates)
    if existing:
        return existing
    if not install_gateway:
        raise StageError(
            "detect-gateway",
            "JetBrains Gateway is not installed. Ask the user to confirm, "
            "then rerun with --install-gateway to run "
            "'brew install --cask jetbrains-gateway'.",
        )
    result = runner.run_command(["brew", "install", "--cask", "jetbrains-gateway"])
    if result.returncode != 0:
        raise StageError("install-gateway", result.stderr.strip() or "brew install failed")
    installed = find_gateway_app(candidates)
    if not installed:
        raise StageError(
            "install-gateway",
            "brew install succeeded but Gateway.app was not found at any known path",
        )
    return installed


# ---------------------------------------------------------------------------
# Stage 2: open the codespace in VS Code
# ---------------------------------------------------------------------------


def build_open_vscode_command(codespace_name: str) -> List[str]:
    return ["gh", "codespace", "code", "-c", codespace_name]


def open_codespace_in_vscode(codespace_name: str, runner: Runner) -> None:
    cmd = build_open_vscode_command(codespace_name)
    result = runner.run_command(cmd, timeout=60)
    if result.returncode != 0:
        raise StageError("open-vscode", result.stderr.strip() or "gh codespace code failed")


# ---------------------------------------------------------------------------
# Stage 3: refresh ~/.ssh/codespaces (selected codespace only) and
# ~/.ssh/config
# ---------------------------------------------------------------------------


def build_ssh_config_command(codespace_name: str) -> List[str]:
    """Build the command that fetches SSH config for one codespace:
    ``gh codespace ssh -c NAME --config``.

    A prior version of this script omitted ``-c`` to match the general
    ``gh codespace ssh --config > ~/.ssh/codespaces`` example, on the
    assumption that would emit every codespace's ``Host`` block. In
    practice ``gh`` skips (and warns about, then exits non-zero on) any
    codespace that isn't currently "Available" -- e.g. Shutdown -- even
    when the one this run actually targets is Available. That made the
    whole refresh fail because of *unrelated* codespaces. Fetching only
    the selected codespace's block with ``-c`` avoids depending on the
    state of every other codespace, at the cost of needing to merge this
    one block into the existing file ourselves (see
    ``merge_ssh_codespaces_text``) instead of trusting a full regenerate.
    """
    return ["gh", "codespace", "ssh", "-c", codespace_name, "--config"]


def fetch_ssh_config_text(codespace_name: str, runner: Runner) -> str:
    """Fetch the SSH config block for exactly one codespace."""
    cmd = build_ssh_config_command(codespace_name)
    result = runner.run_command(cmd, timeout=120)
    if result.returncode != 0:
        raise StageError(
            "refresh-ssh-config", result.stderr.strip() or "gh codespace ssh --config failed"
        )
    if not result.stdout.strip():
        raise StageError("refresh-ssh-config", "gh codespace ssh --config returned no output")
    return result.stdout


def atomic_write_text(path: Path, content: str, mode: int) -> None:
    """Write ``content`` to ``path`` atomically: write to a sibling temp
    file, chmod it, then rename over the destination. Never leaves a
    partially-written file at ``path``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    renamed = False
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.chmod(tmp_name, mode)
        os.replace(tmp_name, path)
        renamed = True
    finally:
        if not renamed and os.path.exists(tmp_name):
            os.unlink(tmp_name)


def compute_ssh_include_update(existing_config_text: str) -> Optional[str]:
    """Return the new ``~/.ssh/config`` text, or ``None`` if the include
    line is already present (no write needed - keeps the operation
    idempotent).
    """
    for line in existing_config_text.splitlines():
        if line.strip() == SSH_INCLUDE_LINE:
            return None
    if existing_config_text and not existing_config_text.endswith("\n"):
        existing_config_text += "\n"
    return existing_config_text + "\n" + SSH_MATCH_BLOCK


_HOST_RE = re.compile(r"^Host\s+(\S+)\s*$")
_USER_RE = re.compile(r"^\s*User\s+(\S+)\s*$")


def parse_ssh_config_segments(config_text: str) -> tuple:
    """Split raw ssh config text into ``(preamble_lines, blocks)``.

    ``preamble_lines`` is every line before the first ``Host`` line,
    verbatim -- comments, blank lines, or global directives (e.g. a
    leading ``Include`` or a header comment). ``blocks`` is an ordered
    list of ``(alias, block_lines)`` pairs, one per ``Host`` line
    (including wildcard hosts like ``Host *``), in their original file
    order. ``block_lines`` keeps every line verbatim (including the
    ``Host`` line itself and any trailing blank separator line before the
    next block/EOF), so re-joining a block's lines with ``"\\n"``
    reproduces that block's original bytes exactly.

    This is the byte-preserving foundation for ``merge_ssh_codespaces_text``:
    every segment (preamble and every non-target block) must be replayed
    unchanged and in its original position, never rebuilt or reordered.
    """
    preamble: List[str] = []
    blocks: List[tuple] = []
    current_alias: Optional[str] = None
    current_lines: Optional[List[str]] = None
    for line in config_text.splitlines():
        host_match = _HOST_RE.match(line)
        if host_match:
            if current_lines is not None:
                blocks.append((current_alias, current_lines))
            current_alias = host_match.group(1)
            current_lines = [line]
        elif current_lines is not None:
            current_lines.append(line)
        else:
            preamble.append(line)
    if current_lines is not None:
        blocks.append((current_alias, current_lines))
    return preamble, blocks


def parse_ssh_config_blocks(config_text: str) -> List[tuple]:
    """Return just the ``(alias, block_lines)`` pairs from
    ``parse_ssh_config_segments``, discarding any preamble. Used by callers
    (``parse_ssh_target``) that only need to find/validate a specific
    codespace's block and don't touch surrounding file structure.
    """
    _preamble, blocks = parse_ssh_config_segments(config_text)
    return blocks


def _alias_matches_codespace(alias: Optional[str], codespace_name: str) -> bool:
    """True if ``alias`` (a ``Host`` line's target, or None for odd input)
    belongs to ``codespace_name`` (``cs.<name>`` or ``cs.<name>.<ref>``).
    """
    if alias is None:
        return False
    marker = f"cs.{codespace_name}."
    exact = f"cs.{codespace_name}"
    return alias == exact or alias.startswith(marker)


def find_blocks_for_codespace(blocks: List[tuple], codespace_name: str) -> List[tuple]:
    """Return every ``(alias, block_lines)`` pair whose alias belongs to
    ``codespace_name`` (``cs.<name>`` or ``cs.<name>.<ref>``).
    """
    return [(alias, lines) for alias, lines in blocks if _alias_matches_codespace(alias, codespace_name)]


def merge_ssh_codespaces_text(
    existing_text: str, selected_config_text: str, codespace_name: str
) -> str:
    """Merge the freshly-fetched single-codespace config block into the
    existing ``~/.ssh/codespaces`` text, replacing only the block(s) that
    belong to ``codespace_name`` and preserving every other byte -- other
    codespaces' blocks, wildcard ``Host *`` blocks, comments, blank lines,
    and any preamble before the first ``Host`` line -- exactly as-is and in
    their original order (including if the file didn't exist before, in
    which case ``existing_text`` is simply ``""``).

    The target codespace's block is replaced *in place* at its original
    position when it already exists, never rebuilt at the end of the file.
    If no existing block matches, the new block is appended after
    everything else (there is no "original position" to preserve).

    Callers must validate ``selected_config_text`` (e.g. via
    ``parse_ssh_target``) *before* calling this, so a malformed/ambiguous
    fetch never reaches the write path. This function still re-checks
    defensively and raises the same stage error if that invariant is ever
    violated.
    """
    _selected_preamble, selected_blocks = parse_ssh_config_segments(selected_config_text)
    selected_matches = find_blocks_for_codespace(selected_blocks, codespace_name)
    if len(selected_matches) != 1:
        raise StageError(
            "refresh-ssh-codespaces",
            f"expected exactly one ssh config block for '{codespace_name}' in the "
            f"selected 'gh codespace ssh -c ... --config' output, found "
            f"{len(selected_matches)}",
        )
    _, new_block_lines = selected_matches[0]

    existing_preamble, existing_blocks = parse_ssh_config_segments(existing_text)
    target_positions = [
        i for i, (alias, _lines) in enumerate(existing_blocks)
        if _alias_matches_codespace(alias, codespace_name)
    ]

    if target_positions:
        # Replace the first matching block in place, at its original
        # position; drop any other stale matches for the same codespace
        # (e.g. a leftover block from an earlier branch) without leaving a
        # gap or moving anything else.
        replace_at = target_positions[0]
        drop = set(target_positions[1:])
        new_blocks = []
        for i, (alias, lines) in enumerate(existing_blocks):
            if i == replace_at:
                new_blocks.append((codespace_name, new_block_lines))
            elif i in drop:
                continue
            else:
                new_blocks.append((alias, lines))
    else:
        new_blocks = existing_blocks + [(codespace_name, new_block_lines)]

    merged_lines = list(existing_preamble)
    for _alias, lines in new_blocks:
        merged_lines.extend(lines)
    merged_text = "\n".join(merged_lines)
    if merged_text and not merged_text.endswith("\n"):
        merged_text += "\n"
    return merged_text


def write_ssh_codespaces_file(
    ssh_codespaces_path: Path,
    selected_config_text: str,
    codespace_name: str,
) -> None:
    """Merge ``selected_config_text`` (this codespace's block only) into
    the existing ``~/.ssh/codespaces`` file and write the result
    atomically. Every other codespace's block -- including ones for
    codespaces that are currently Shutdown -- is preserved untouched.
    """
    existing_text = ssh_codespaces_path.read_text() if ssh_codespaces_path.exists() else ""
    merged_text = merge_ssh_codespaces_text(existing_text, selected_config_text, codespace_name)
    atomic_write_text(ssh_codespaces_path, merged_text, 0o600)


def ensure_ssh_include(ssh_config_path: Path) -> bool:
    """Add the ``Include ~/.ssh/codespaces`` block to ``ssh_config_path`` if
    missing. Returns True if the file was changed, False if it already had
    the include (idempotent, no duplicate).
    """
    existing_text = ssh_config_path.read_text() if ssh_config_path.exists() else ""
    new_text = compute_ssh_include_update(existing_text)
    if new_text is None:
        return False
    atomic_write_text(ssh_config_path, new_text, 0o600)
    return True


# ---------------------------------------------------------------------------
# Stage 4: parse the SSH alias/user for the codespace
# ---------------------------------------------------------------------------


def parse_ssh_target(config_text: str, codespace_name: str) -> SSHTarget:
    """Parse the ``Host cs.<name>.<ref> / User <user>`` block for this
    codespace out of ``config_text`` (normally the single-codespace output
    of ``gh codespace ssh -c NAME --config``). Fails if zero or more than
    one matching block is found -- this validation must run, and must
    raise, before ``write_ssh_codespaces_file`` ever touches disk.
    """
    blocks = parse_ssh_config_blocks(config_text)
    matches = find_blocks_for_codespace(blocks, codespace_name)

    if not matches:
        raise StageError(
            "parse-ssh-target",
            f"no 'Host cs.{codespace_name}.*' block found in ssh config output",
        )
    if len(matches) > 1:
        aliases = ", ".join(alias for alias, _ in matches)
        raise StageError(
            "parse-ssh-target",
            f"ambiguous ssh config: found multiple hosts for {codespace_name}: {aliases}",
        )

    alias, block = matches[0]
    user = None
    for line in block[1:]:
        user_match = _USER_RE.match(line)
        if user_match:
            user = user_match.group(1)
            break
    if not user:
        raise StageError("parse-ssh-target", f"no User line found for host {alias}")

    return SSHTarget(alias=alias, user=user)


# ---------------------------------------------------------------------------
# Stage 4b: verify the SSH connection actually works
# ---------------------------------------------------------------------------


def build_ssh_verify_command(ssh_alias: str) -> List[str]:
    # ``--`` must end ssh's own option parsing BEFORE the hostname, not
    # after it. ``[ssh, alias, --, true]`` makes ssh treat "-- true" as the
    # remote command string (malformed); ``[ssh, --, alias, true]`` runs
    # "true" as the remote command, with alias protected from being
    # misparsed as an option even if it starts with "-".
    return ["ssh", "--", ssh_alias, "true"]


def build_ssh_remote_shell_command(ssh_alias: str, remote_script: str) -> List[str]:
    """Build an ``ssh`` argv that runs a multi-word/multi-statement
    ``remote_script`` via ``bash -lc`` on the codespace.

    OpenSSH does NOT preserve our Python list's argv boundaries across the
    wire: everything after the destination is joined with a single space
    and handed to the remote user's login shell (zsh, on a stock
    codespace) to parse and execute as one command line. So passing
    ``remote_script`` as its own bare argv element used to leak its
    internal syntax -- spaces, ``for``/``do``/``done``, embedded quotes --
    straight into that outer remote shell, which then failed trying to
    parse ``bash -lc for p in ... do ... done`` itself (``zsh:1: parse
    error near do``) instead of ever handing the loop to ``bash -lc`` as a
    single argument.

    Quoting the assembled script with :func:`sh_quote` before it becomes
    one argv element ensures the text ssh reconstructs on the wire is
    ``bash -lc '<script>'`` -- one shell-quoted token the remote shell
    hands to ``-lc`` intact, regardless of what it contains (including
    embedded quotes, semicolons, or attempted command injection).
    """
    return ["ssh", "--", ssh_alias, "bash", "-lc", sh_quote(remote_script)]


def verify_ssh_connection(ssh_alias: str, runner: Runner) -> None:
    """Confirm the freshly-written SSH alias actually connects before doing
    any backend work over it. Kept as its own stage so a connectivity
    failure is never confused with "no backend installed yet".
    """
    cmd = build_ssh_verify_command(ssh_alias)
    result = runner.run_command(cmd, timeout=30)
    if result.returncode != 0:
        raise StageError(
            "verify-ssh-connection",
            result.stderr.strip() or f"could not connect to '{ssh_alias}' over ssh",
        )


# ---------------------------------------------------------------------------
# Stage 4c: detect the codespace's CPU architecture
# ---------------------------------------------------------------------------


def build_detect_arch_command(ssh_alias: str) -> List[str]:
    # See build_ssh_verify_command: ``--`` goes before the alias.
    return ["ssh", "--", ssh_alias, "uname", "-m"]


def detect_remote_arch(ssh_alias: str, runner: Runner) -> str:
    """Detect the codespace's CPU architecture with ``uname -m``. Callers
    should only use this when the user did not pass an explicit ``--arch``;
    never silently assume x86_64.
    """
    cmd = build_detect_arch_command(ssh_alias)
    result = runner.run_command(cmd, timeout=30)
    if result.returncode != 0:
        raise StageError("detect-arch", result.stderr.strip() or "uname -m failed")
    arch = result.stdout.strip()
    if not arch:
        raise StageError("detect-arch", "uname -m returned no output")
    return arch


# ---------------------------------------------------------------------------
# Stage 5: resolve/reuse the WebStorm backend
# ---------------------------------------------------------------------------


def build_backend_probe_script(dist_dir: str) -> str:
    """Return the raw (unquoted) probe script text -- the part that later
    becomes a single quoted argument via :func:`build_ssh_remote_shell_command`.
    Kept separate so callers/tests can inspect script content directly
    without unwrapping an outer quoting layer first.
    """
    dist_expr = shell_path(dist_dir)
    glob_expr = f"{dist_expr}/{PRODUCT_NAME}-*/bin/remote-dev-server.sh"
    product_needle = sh_quote(f'"productCode" *: *"{PRODUCT_CODE}"')
    return (
        f"for p in {glob_expr}; do "
        'if [ -f "$p" ]; then '
        'root=$(dirname "$(dirname "$p")"); '
        f'if grep -q {product_needle} "$root/product-info.json" 2>/dev/null; then echo "$p"; break; fi; '
        "fi; "
        "done"
    )


def build_backend_probe_command(ssh_alias: str, dist_dir: str) -> List[str]:
    """Probe for an existing, verified WebStorm backend. Restricted to
    ``WebStorm-*`` directories (never reuses some other JetBrains product
    installed under the same dist dir) and cross-checked against
    ``product-info.json``'s ``productCode`` before it is ever echoed back,
    so a guessed or wrong-product path is never trusted.

    Multiple ``WebStorm-*`` dirs can exist under one dist dir (stale partial
    installs, older builds left behind). Iterate ALL glob candidates and
    echo the first one that actually passes the product-info.json check;
    a single bad/partial first match must never mask a later valid one.
    """
    return build_ssh_remote_shell_command(ssh_alias, build_backend_probe_script(dist_dir))


def find_existing_backend(ssh_alias: str, dist_dir: str, runner: Runner) -> Optional[str]:
    """Return the remote path to an existing ``remote-dev-server.sh``, or
    None if no backend is installed yet.
    """
    cmd = build_backend_probe_command(ssh_alias, dist_dir)
    result = runner.run_command(cmd, timeout=30)
    if result.returncode != 0:
        raise StageError("probe-backend", result.stderr.strip() or "ssh probe failed")
    path = result.stdout.strip()
    return path or None


def _arch_download_key(arch: str) -> str:
    if arch in ("x86_64", "amd64"):
        return "linux"
    if arch in ("aarch64", "arm64"):
        return "linuxARM64"
    raise StageError("resolve-release", f"unsupported architecture: {arch}")


def parse_release_metadata(payload: bytes, arch: str) -> ReleaseInfo:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise StageError("resolve-release", f"could not parse JetBrains releases JSON: {exc}")

    releases = data.get(PRODUCT_CODE)
    if not releases:
        raise StageError("resolve-release", f"no releases found for product code {PRODUCT_CODE}")

    release = releases[0]
    key = _arch_download_key(arch)
    downloads = release.get("downloads", {})
    download = downloads.get(key)
    if not download or "link" not in download:
        raise StageError("resolve-release", f"no '{key}' download in latest release metadata")

    version = release.get("version")
    build = release.get("build")
    if not version or not build:
        raise StageError("resolve-release", "release metadata missing version/build")

    return ReleaseInfo(version=version, build=build, download_url=download["link"])


def resolve_latest_release(runner: Runner, arch: str) -> ReleaseInfo:
    url = RELEASES_URL.format(code=PRODUCT_CODE)
    payload = runner.http_get(url)
    return parse_release_metadata(payload, arch)


def build_backend_install_script(dist_dir: str, download_url: str, build: str) -> str:
    """Return the raw (unquoted) install script text. See
    :func:`build_backend_probe_script` for why this is kept separate from
    the ssh-command builder.
    """
    dist_dir_expr = shell_path(dist_dir)
    tarball_expr = f"{dist_dir_expr}/{sh_quote(f'webstorm-backend-{build}.tar.gz')}"
    return " && ".join(
        [
            f"mkdir -p {dist_dir_expr}",
            f"curl -fsSL {sh_quote(download_url)} -o {tarball_expr}",
            f"tar -xzf {tarball_expr} -C {dist_dir_expr}",
            f"rm -f {tarball_expr}",
        ]
    )


def build_backend_install_command(ssh_alias: str, dist_dir: str, download_url: str, build: str) -> List[str]:
    """Download and extract the WebStorm backend. Deliberately does not
    guess or echo the extracted directory name: JetBrains tarballs extract
    to ``WebStorm-<build>``, not ``WebStorm-<version>``, and that naming
    isn't guaranteed to stay stable, so the caller must rediscover and
    verify the real path afterwards (see ``find_existing_backend``). The
    staging tarball name only needs to be unique; ``build`` is a stable,
    unique identifier for it.
    """
    script = build_backend_install_script(dist_dir, download_url, build)
    return build_ssh_remote_shell_command(ssh_alias, script)


def install_backend(
    ssh_alias: str, dist_dir: str, release: ReleaseInfo, runner: Runner
) -> str:
    cmd = build_backend_install_command(ssh_alias, dist_dir, release.download_url, release.build)
    result = runner.run_command(cmd, timeout=600)
    if result.returncode != 0:
        raise StageError("install-backend", result.stderr.strip() or "backend install failed")
    # Never trust a guessed path: rediscover and re-verify the backend the
    # same way an already-installed one would be found and validated.
    backend_path = find_existing_backend(ssh_alias, dist_dir, runner)
    if not backend_path:
        raise StageError(
            "install-backend",
            "installed WebStorm backend was not found (or failed product "
            "verification) after extraction",
        )
    return backend_path


def ensure_backend(
    ssh_alias: str, dist_dir: str, arch: str, runner: Runner
) -> str:
    """Reuse an installed backend if one exists. Otherwise resolve the
    latest release from the JetBrains API and install it. Never mixes the
    two: if a backend already exists we never contact the release API.
    """
    existing = find_existing_backend(ssh_alias, dist_dir, runner)
    if existing:
        return existing
    release = resolve_latest_release(runner, arch)
    return install_backend(ssh_alias, dist_dir, release, runner)


# ---------------------------------------------------------------------------
# Stage 6: start (or reuse) remote-dev-server.sh, then poll for the Gateway
# link
#
# 'remote-dev-server.sh run' is a long-lived server process by design -- it
# never exits on its own. Waiting on it synchronously (as an earlier version
# of this script did) either hangs forever or, once a timeout is added,
# leaks a raw subprocess.TimeoutExpired traceback once that timeout fires,
# even though the backend is running fine. So instead: start it detached
# (nohup'd, redirected to a stable per-project log, disowned) and poll its
# separate 'status' subcommand -- which returns promptly -- until it reports
# a ready gatewayLink. An already-running backend for the same project is
# reused outright; we never start a second instance.
# ---------------------------------------------------------------------------


def build_remote_dev_server_script(
    backend_path: str,
    remote_project_path: str,
    ssh_alias: str,
    ssh_link_user: str,
    ssh_link_port: int = DEFAULT_SSH_LINK_PORT,
) -> str:
    """Return the raw (unquoted) remote-dev-server invocation text. See
    :func:`build_backend_probe_script` for why this is kept separate from
    the ssh-command builder. Only 'run' and 'status' are ever invoked --
    both are real, live-observed remote-dev-server.sh subcommands; no
    other flag or subcommand is invented.
    """
    return "{binary} run {project} --ssh-link-host {host} --ssh-link-user {user} --ssh-link-port {port}".format(
        binary=sh_quote(backend_path),
        project=sh_quote(remote_project_path),
        host=sh_quote(ssh_alias),
        user=sh_quote(ssh_link_user),
        port=sh_quote(str(ssh_link_port)),
    )


def build_remote_dev_server_command(
    ssh_alias: str,
    backend_path: str,
    remote_project_path: str,
    ssh_link_user: str,
    ssh_link_port: int = DEFAULT_SSH_LINK_PORT,
) -> List[str]:
    """The plain (foreground) 'run ...' ssh command. Only used as a
    building block for :func:`build_start_detached_script` -- never run
    directly, since it would block forever/until timeout.
    """
    script = build_remote_dev_server_script(
        backend_path, remote_project_path, ssh_alias, ssh_link_user, ssh_link_port
    )
    return build_ssh_remote_shell_command(ssh_alias, script)


def parse_gateway_link(output: str) -> str:
    """Extract and validate a 'jetbrains-gateway://connect#...' link found
    anywhere in ``output``. Used both to sanity-check a gatewayLink pulled
    out of status JSON, and as a general-purpose parser for raw text.
    """
    match = GATEWAY_LINK_RE.search(output)
    if not match:
        raise StageError(
            "parse-gateway-link", "no 'jetbrains-gateway://connect#...' link in server output"
        )
    return match.group(0)


def gateway_link_project_path(link: Optional[str]) -> Optional[str]:
    """Extract the 'projectPath' query parameter from a gatewayLink's URL
    fragment, e.g. 'jetbrains-gateway://connect#idePath=...&projectPath=
    %2Fworkspaces%2Fgithub-ui...' -> '/workspaces/github-ui'.

    Best-effort only: returns ``None`` (never raises) if ``link`` is falsy,
    unparsable, or carries no 'projectPath' -- callers treat that as "no
    project info available", not a hard failure.
    """
    if not link:
        return None
    fragment = urllib.parse.urlsplit(link).fragment
    if not fragment:
        return None
    values = urllib.parse.parse_qs(fragment).get("projectPath")
    if not values:
        return None
    return values[0] or None


_LOG_SLUG_UNSAFE_RE = re.compile(r"[^A-Za-z0-9_.-]")


def remote_dev_server_log_path(remote_project_path: str) -> str:
    """A stable, per-project remote log path: re-running this skill against
    the same project always targets the same log file rather than a fresh
    throwaway path each time.
    """
    slug = _LOG_SLUG_UNSAFE_RE.sub("_", remote_project_path.strip("/")) or "project"
    return f"{REMOTE_DEV_SERVER_LOG_DIR}/{slug}.log"


def build_start_detached_script(
    backend_path: str,
    remote_project_path: str,
    ssh_alias: str,
    ssh_link_user: str,
    ssh_link_port: int = DEFAULT_SSH_LINK_PORT,
) -> str:
    """Raw (unquoted) script that starts remote-dev-server.sh fully
    detached from the ssh session: stdio redirected to a stable per-project
    log, stdin from /dev/null, backgrounded, and disowned so it survives
    this ssh command (and its shell) exiting. This command itself returns
    almost immediately -- it never waits for the server to finish, because
    the server never finishes.
    """
    run_cmd = build_remote_dev_server_script(
        backend_path, remote_project_path, ssh_alias, ssh_link_user, ssh_link_port
    )
    log_path = remote_dev_server_log_path(remote_project_path)
    log_expr = shell_path(log_path)
    log_dir_expr = shell_path(REMOTE_DEV_SERVER_LOG_DIR)
    # ';' (not '&&') between mkdir and the backgrounded job: '&&' would let
    # the trailing '&' background the whole 'mkdir && nohup ...' list, which
    # still works but needlessly obscures what actually got backgrounded.
    return f"mkdir -p {log_dir_expr}; nohup {run_cmd} > {log_expr} 2>&1 < /dev/null & disown"


def build_start_detached_command(
    ssh_alias: str,
    backend_path: str,
    remote_project_path: str,
    ssh_link_user: str,
    ssh_link_port: int = DEFAULT_SSH_LINK_PORT,
) -> List[str]:
    script = build_start_detached_script(
        backend_path, remote_project_path, ssh_alias, ssh_link_user, ssh_link_port
    )
    return build_ssh_remote_shell_command(ssh_alias, script)


def build_backend_status_command(ssh_alias: str, backend_path: str) -> List[str]:
    script = f"{sh_quote(backend_path)} status"
    return build_ssh_remote_shell_command(ssh_alias, script)


def parse_backend_status(combined_output: str) -> Optional[dict]:
    """Parse 'remote-dev-server.sh status' output.

    Live evidence: the command can emit diagnostic noise (observed:
    'error: XDG_RUNTIME_DIR is invalid...') around the actual payload, and
    the payload itself is a JSON object following a literal 'STATUS:'
    marker rather than being raw JSON on its own. It isn't clear which
    stream (stdout/stderr) carries which part, so callers pass a combined
    view and this just searches for the marker. Live output also showed
    pretty-printed (multi-line) JSON followed by *more* noise appended
    after it (e.g. stderr text concatenated after stdout), so a plain
    'json.loads' of the whole remainder fails too -- only the first
    complete JSON object, wherever it ends, is wanted.

    Returns ``None`` -- never raises -- when the marker/JSON is missing or
    unparsable: "no status yet" (backend not started, or still starting)
    is an expected transient poll state, not a hard failure.
    """
    idx = combined_output.find(STATUS_MARKER)
    if idx == -1:
        return None
    rest = combined_output[idx + len(STATUS_MARKER):].lstrip()
    if not rest:
        return None
    try:
        data, _end = json.JSONDecoder().raw_decode(rest)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return data
    return None


def backend_status_gateway_link(status: dict) -> Optional[str]:
    link = status.get("gatewayLink") or None
    if link is None:
        return None
    return parse_gateway_link(link)


def backend_status_project_path(status: dict) -> Optional[str]:
    """Resolve the project path a running/starting backend is associated
    with, checked in this priority order:

    1. A literal 'projectPath' key in the status JSON, if some version
       ever emits one.
    2. The 'projectPath' query parameter parsed out of 'gatewayLink's URL
       fragment (e.g. '...#idePath=...&projectPath=%2Fworkspaces%2Ffoo').

    'idePath' -- the WebStorm backend *installation* directory the IDE
    process was launched from (e.g. '/home/vscode/.cache/.../WebStorm-262...')
    -- is never used as a project-path stand-in. Live evidence showed
    idePath naming the backend install, not the project, which caused
    false project mismatches and duplicate backend starts when it was
    used as a fallback.
    """
    literal = status.get("projectPath")
    if literal:
        return literal
    return gateway_link_project_path(status.get("gatewayLink"))


def backend_status_matches_project(status: dict, expected_project_path: str) -> bool:
    """True unless the status names a *different* project than requested.
    Missing project info is not treated as a mismatch (there's nothing to
    validate against); only conflicting info is -- this is what stops a
    different project's already-running session from ever being reused
    silently.
    """
    project_path = backend_status_project_path(status)
    if not project_path:
        return True
    return project_path.rstrip("/") == expected_project_path.rstrip("/")


def backend_status_is_ready(status: dict, expected_project_path: str) -> bool:
    if status.get("backendUnresponsive"):
        return False
    if not backend_status_gateway_link(status):
        return False
    return backend_status_matches_project(status, expected_project_path)


def query_backend_status(ssh_alias: str, backend_path: str, runner: Runner) -> Optional[dict]:
    cmd = build_backend_status_command(ssh_alias, backend_path)
    result = runner.run_command(cmd, timeout=30)
    # 'status' can legitimately exit non-zero while still printing a
    # useful STATUS: JSON blob (or none at all, e.g. before anything has
    # started) -- readiness is judged purely by whether a STATUS: payload
    # parses, not by the exit code.
    return parse_backend_status(result.stdout + "\n" + result.stderr)


def start_remote_dev_server_detached(
    ssh_target: SSHTarget,
    backend_path: str,
    remote_project_path: str,
    runner: Runner,
) -> None:
    cmd = build_start_detached_command(
        ssh_target.alias, backend_path, remote_project_path, ssh_target.user
    )
    result = runner.run_command(cmd, timeout=30)
    if result.returncode != 0:
        raise StageError(
            "start-remote-dev-server",
            result.stderr.strip() or "failed to start remote-dev-server.sh in the background",
        )


def ensure_remote_dev_server_running(
    ssh_target: SSHTarget,
    backend_path: str,
    remote_project_path: str,
    runner: Runner,
    *,
    timeout: float = DEFAULT_START_TIMEOUT_SECONDS,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> str:
    """Return a ready Gateway link for ``remote_project_path``, starting the
    backend only if nothing suitable is already running.
    """
    status = query_backend_status(ssh_target.alias, backend_path, runner)
    if status is not None:
        if status.get("backendUnresponsive"):
            raise StageError(
                "start-remote-dev-server",
                f"existing backend at {backend_path} is unresponsive: {json.dumps(status)}",
            )
        if backend_status_is_ready(status, remote_project_path):
            return backend_status_gateway_link(status)

    start_remote_dev_server_detached(ssh_target, backend_path, remote_project_path, runner)

    deadline = runner.monotonic() + timeout
    last_status: Optional[dict] = None
    while True:
        status = query_backend_status(ssh_target.alias, backend_path, runner)
        if status is not None:
            last_status = status
            if status.get("backendUnresponsive"):
                raise StageError(
                    "start-remote-dev-server",
                    f"backend at {backend_path} became unresponsive while starting: "
                    f"{json.dumps(status)}",
                )
            if backend_status_is_ready(status, remote_project_path):
                return backend_status_gateway_link(status)
        if runner.monotonic() >= deadline:
            detail = (
                f"; last status: {json.dumps(last_status)}"
                if last_status is not None
                else "; no STATUS: output was ever observed"
            )
            raise StageError(
                "start-remote-dev-server",
                f"timed out after {timeout:.0f}s waiting for a ready gateway link for "
                f"{remote_project_path}{detail}",
            )
        runner.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Stage 7: open the Gateway link locally
# ---------------------------------------------------------------------------


def build_open_link_command(link: str, gateway_app_path: Optional[Path] = None) -> List[str]:
    """Open the Gateway deep link. When a concrete Gateway.app path is
    known, target it explicitly with ``open -a <path>`` instead of relying
    only on the registered ``jetbrains-gateway://`` URL handler, which can
    fail to resolve (e.g. app installed as ``Gateway.app`` under a
    non-default name/location).
    """
    if gateway_app_path is not None:
        return ["open", "-a", str(gateway_app_path), link]
    return ["open", link]


def open_gateway_link(link: str, gateway_app_path: Optional[Path], runner: Runner) -> None:
    cmd = build_open_link_command(link, gateway_app_path)
    result = runner.run_command(cmd, timeout=30)
    if result.returncode != 0:
        raise StageError("open-gateway-link", result.stderr.strip() or "open failed")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def resolve_remote_project_path(args: argparse.Namespace) -> str:
    if args.remote_project_path:
        return args.remote_project_path
    if args.repo:
        repo_name = args.repo.rstrip("/").split("/")[-1]
        return f"/workspaces/{repo_name}"
    raise StageError(
        "resolve-project-path",
        "pass --remote-project-path, or --repo owner/repo to derive /workspaces/<repo>",
    )


def build_plan(args: argparse.Namespace) -> List[str]:
    """Describe, in order, the commands the real run would execute. Used
    for --dry-run: no subprocess, no HTTP call, no filesystem write happens.
    """
    remote_project_path = resolve_remote_project_path(args)
    # The actual codespace name is only known once 'gh codespace list' is
    # actually run (see resolve_codespace_name); --dry-run never runs it,
    # so every later command uses a placeholder rather than assuming
    # --codespace is already the resolved name.
    ssh_alias_placeholder = f"cs.{RESOLVED_CODESPACE_PLACEHOLDER}.<branch>"
    gateway_candidates = args.gateway_app_path or list(GATEWAY_APP_CANDIDATES)
    gateway_app_path = find_gateway_app(gateway_candidates)
    plan = []
    if args.use_keyring_auth:
        plan.append(
            "auth: --use-keyring-auth (GH_TOKEN/GITHUB_TOKEN stripped from every "
            "child subprocess env, including ssh's ProxyCommand; gh falls back "
            "to its keyring-stored credentials)"
        )
    else:
        plan.append(
            "auth: inherit parent environment (GH_TOKEN/GITHUB_TOKEN passed "
            "through to child processes if set)"
        )
    plan.append(
        " ".join(build_codespace_list_command())
        + f" (resolve --codespace '{args.codespace}' by exact name or unique "
        "displayName; this live, read-only stage is what determines the "
        f"actual name -- shown below as '{RESOLVED_CODESPACE_PLACEHOLDER}')"
    )
    if gateway_app_path is None:
        if args.install_gateway:
            plan.append("brew install --cask jetbrains-gateway")
        else:
            plan.append(
                "[BLOCKED] JetBrains Gateway not found; rerun with --install-gateway "
                "after user confirms"
            )
    plan.append(
        " ".join(build_open_vscode_command(RESOLVED_CODESPACE_PLACEHOLDER))
        + " (actual name resolved live above, not known during --dry-run)"
    )
    plan.append(
        " ".join(build_ssh_config_command(RESOLVED_CODESPACE_PLACEHOLDER))
        + " (selected codespace only; merged into ~/.ssh/codespaces, other "
        "aliases untouched)"
    )
    plan.append(f"merge + write {args.ssh_codespaces_path} (atomic, 0600)")
    plan.append(f"ensure 'Include ~/.ssh/codespaces' in {args.ssh_config_path}")
    plan.append(" ".join(build_ssh_verify_command(ssh_alias_placeholder)))
    if args.arch:
        plan.append(f"using --arch {args.arch} (no remote detection needed)")
    else:
        plan.append(" ".join(build_detect_arch_command(ssh_alias_placeholder)) + " (detect arch)")
    plan.append(
        " ".join(build_backend_probe_command(ssh_alias_placeholder, args.dist_dir))
    )
    plan.append(f"GET {RELEASES_URL.format(code=PRODUCT_CODE)} (only if no backend found)")
    backend_placeholder = (
        f"{args.dist_dir}/{PRODUCT_NAME}-<build>/bin/remote-dev-server.sh (rediscovered, verified)"
    )
    plan.append(
        " ".join(build_backend_status_command(ssh_alias_placeholder, backend_placeholder))
        + " (check for an already-running backend for this project first; reuse its "
        "gatewayLink and skip starting a new one if found)"
    )
    plan.append(
        " ".join(
            build_start_detached_command(
                ssh_alias_placeholder, backend_placeholder, remote_project_path, "<ssh-user>"
            )
        )
        + f" (only if not already running; log: {remote_dev_server_log_path(remote_project_path)})"
    )
    plan.append(
        " ".join(build_backend_status_command(ssh_alias_placeholder, backend_placeholder))
        + f" (poll every {args.poll_interval:.0f}s, up to {args.start_timeout:.0f}s, for a "
        "ready gatewayLink)"
    )
    if gateway_app_path is not None:
        plan.append(
            " ".join(build_open_link_command("jetbrains-gateway://connect#...", gateway_app_path))
        )
    else:
        plan.append("open jetbrains-gateway://connect#... (parsed from status gatewayLink)")
    return plan


def run(args: argparse.Namespace, runner: Runner) -> str:
    """Execute the full pipeline for real. Returns the Gateway link that
    was opened. Raises StageError at the exact stage that fails.
    """
    remote_project_path = resolve_remote_project_path(args)
    codespace_name = resolve_codespace_name(args.codespace, runner)

    gateway_candidates = args.gateway_app_path or list(GATEWAY_APP_CANDIDATES)
    gateway_app_path = ensure_gateway(
        runner, install_gateway=args.install_gateway, candidates=gateway_candidates
    )
    open_codespace_in_vscode(codespace_name, runner)

    config_text = fetch_ssh_config_text(codespace_name, runner)
    # Validate/parse the selected output BEFORE any write happens: a
    # malformed or ambiguous fetch must fail here, never reach the merge
    # step and never touch ~/.ssh/codespaces.
    ssh_target = parse_ssh_target(config_text, codespace_name)
    write_ssh_codespaces_file(args.ssh_codespaces_path, config_text, codespace_name)
    ensure_ssh_include(args.ssh_config_path)

    verify_ssh_connection(ssh_target.alias, runner)
    arch = args.arch or detect_remote_arch(ssh_target.alias, runner)

    backend_path = ensure_backend(ssh_target.alias, args.dist_dir, arch, runner)
    link = ensure_remote_dev_server_running(
        ssh_target,
        backend_path,
        remote_project_path,
        runner,
        timeout=args.start_timeout,
        poll_interval=args.poll_interval,
    )
    open_gateway_link(link, gateway_app_path, runner)
    return link


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Connect a GitHub Codespace to WebStorm via JetBrains Gateway."
    )
    parser.add_argument(
        "--codespace",
        "-c",
        required=True,
        help="Codespace name, or its unique VS Code displayName (resolved via "
        "'gh codespace list'; ambiguous display names are rejected)",
    )
    parser.add_argument("--repo", "-R", help="owner/repo, used to derive /workspaces/<repo>")
    parser.add_argument(
        "--remote-project-path", help="Explicit project path on the codespace (overrides --repo)"
    )
    parser.add_argument(
        "--arch",
        default=None,
        choices=["x86_64", "amd64", "aarch64", "arm64"],
        help="Codespace CPU architecture. Detected remotely with 'uname -m' "
        "over ssh if omitted; never silently assumed.",
    )
    parser.add_argument(
        "--dist-dir",
        default=DEFAULT_DIST_DIR,
        help="Remote WebStorm backend install directory",
    )
    parser.add_argument(
        "--ssh-config-path",
        type=Path,
        default=Path.home() / ".ssh" / "config",
        help="Local ~/.ssh/config path (override for testing)",
    )
    parser.add_argument(
        "--ssh-codespaces-path",
        type=Path,
        default=Path.home() / ".ssh" / "codespaces",
        help="Local ~/.ssh/codespaces path (override for testing)",
    )
    parser.add_argument(
        "--install-gateway",
        action="store_true",
        help="Install JetBrains Gateway via Homebrew if missing (get user confirmation first)",
    )
    parser.add_argument(
        "--gateway-app-path",
        type=Path,
        action="append",
        default=None,
        help="Path to JetBrains Gateway.app to check (repeatable; overrides the default candidates)",
    )
    parser.add_argument(
        "--use-keyring-auth",
        action="store_true",
        help="Strip GH_TOKEN/GITHUB_TOKEN from every child subprocess's env "
        "(gh, ssh, curl, and ssh's ProxyCommand), forcing 'gh' to fall back "
        "to its keyring-stored credentials. Use when an injected GH_TOKEN "
        "lacks the 'codespace' scope. Never touches this process's own env.",
    )
    parser.add_argument(
        "--start-timeout",
        type=float,
        default=DEFAULT_START_TIMEOUT_SECONDS,
        help="Seconds to poll remote-dev-server.sh status for a ready "
        f"gateway link before failing (default: {DEFAULT_START_TIMEOUT_SECONDS:.0f})",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Seconds to wait between remote-dev-server.sh status polls "
        f"(default: {DEFAULT_POLL_INTERVAL_SECONDS:.0f})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the commands that would run; touch nothing",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        if args.dry_run:
            for line in build_plan(args):
                print(line)
            return 0

        runner = Runner(run_command=make_run_command(args.use_keyring_auth))
        link = run(args, runner)
    except StageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        # Raised by shell_path()/argument validation before any stage runs
        # (e.g. an unsafe --dist-dir); never emit unsafe shell text instead.
        print(f"error: [invalid-input] {exc}", file=sys.stderr)
        return 1
    print(f"Opened WebStorm via JetBrains Gateway: {link}")
    print(
        "If this is the first connection, finish the one-time Gateway/WebStorm "
        "EULA and license activation manually in the Gateway window. The "
        "remote-dev-server.sh backend itself may also prompt on its very "
        "first run in this codespace; if this hangs or fails, SSH in once "
        "and run it interactively to accept, then rerun this script."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
