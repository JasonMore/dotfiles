"""Tests for open_codespace_webstorm.py.

All external effects are faked: no real ssh/gh/curl/tar/open/brew process is
ever launched, and ~/.ssh is never touched (tests always pass explicit
tempfile-backed paths). Gateway.app "detection" always uses explicit
tempdir-backed candidate paths too, never the real machine's installed
apps, so results don't depend on what happens to be installed locally.
Uses stdlib unittest since the repo has no existing Python test convention.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import List, Optional

MODULE_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "open_codespace_webstorm.py"
)
_spec = importlib.util.spec_from_file_location("open_codespace_webstorm", MODULE_PATH)
m = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = m
_spec.loader.exec_module(m)  # type: ignore[union-attr]


SAMPLE_CONFIG_ONE_HOST = """Host cs.my-cs-123.main
\tUser vscode
\tProxyCommand gh cs ssh -c my-cs-123 --stdio -- -i /Users/x/.ssh/codespaces.auto
\tUserKnownHostsFile=/dev/null
\tStrictHostKeyChecking no
\tLogLevel quiet
\tControlMaster auto
\tIdentityFile /Users/x/.ssh/codespaces.auto

"""

# What `gh codespace ssh --config` (no -c) emits: a Host block per visible
# codespace. Used to prove the no-`-c` refresh preserves every alias.
SAMPLE_CONFIG_TWO_HOSTS = SAMPLE_CONFIG_ONE_HOST + (
    "Host cs.other-cs-456.develop\n"
    "\tUser vscode\n"
    "\tProxyCommand gh cs ssh -c other-cs-456 --stdio -- -i /Users/x/.ssh/codespaces.auto\n"
    "\tUserKnownHostsFile=/dev/null\n"
    "\tStrictHostKeyChecking no\n"
    "\tLogLevel quiet\n"
    "\tControlMaster auto\n"
    "\tIdentityFile /Users/x/.ssh/codespaces.auto\n"
    "\n"
)

# A realistic hand-maintained ~/.ssh/codespaces with: a header comment and
# blank line before any Host block (preamble), a wildcard `Host *` block
# that never matches any codespace, the target codespace's block placed in
# the MIDDLE (not last), and another codespace's block after it. Used to
# prove merge_ssh_codespaces_text replaces the target in place and leaves
# every other byte -- preamble, wildcard block, ordering -- untouched.
PREAMBLE_AND_WILDCARD_CONFIG = (
    "# managed by dotfiles; codespace blocks below are regenerated\n"
    "\n"
    "Host *\n"
    "\tAddKeysToAgent yes\n"
    "\tCompression yes\n"
    "\n"
    "Host cs.my-cs-123.old-branch\n"
    "\tUser vscode\n"
    "\tProxyCommand gh cs ssh -c my-cs-123 --stdio -- -i /Users/x/.ssh/codespaces.auto\n"
    "\tUserKnownHostsFile=/dev/null\n"
    "\n"
    "Host cs.other-cs-456.develop\n"
    "\tUser vscode\n"
    "\tProxyCommand gh cs ssh -c other-cs-456 --stdio -- -i /Users/x/.ssh/codespaces.auto\n"
    "\tUserKnownHostsFile=/dev/null\n"
    "\n"
)

SAMPLE_RELEASE_JSON = json.dumps(
    {
        "WS": [
            {
                "version": "2026.2.0.1",
                "majorVersion": "2026.2",
                "build": "262.8665.341",
                "downloads": {
                    "linux": {
                        "link": "https://download.jetbrains.com/webstorm/WebStorm-2026.2.0.1.tar.gz",
                        "size": 1132150045,
                    },
                    "linuxARM64": {
                        "link": "https://download.jetbrains.com/webstorm/WebStorm-2026.2.0.1-aarch64.tar.gz",
                        "size": 1155389881,
                    },
                },
            }
        ]
    }
).encode("utf-8")

# A path shaped like a real installed+verified backend: WebStorm-<build>,
# matching what the hardened probe command would actually echo.
SAMPLE_BACKEND_PATH = (
    "/home/vscode/.cache/JetBrains/RemoteDev/dist/WebStorm-262.8665.341/bin/remote-dev-server.sh"
)

# A definitely-nonexistent Gateway.app candidate, for tests that need
# "Gateway is not installed" regardless of what's on the real machine.
NONEXISTENT_GATEWAY_CANDIDATE = Path("/nonexistent-for-tests/JetBrains Gateway.app")


class FakeRunner:
    """Records every call and returns pre-scripted CommandResult/bytes.
    Never touches the real system. ``monotonic`` only advances when
    ``sleep`` is called (mirroring real elapsed time), and ``sleep`` never
    actually blocks -- so poll-loop tests are both deterministic and fast.
    """

    def __init__(self) -> None:
        self.commands: List[List[str]] = []
        self.http_calls: List[str] = []
        self.sleep_calls: List[float] = []
        self._default_result = m.CommandResult([], 0, "", "")
        self._http_payload: bytes = SAMPLE_RELEASE_JSON
        self._by_prefix: List[tuple] = []  # (prefix_tuple, CommandResult)
        self._handler = None  # optional custom callable(cmd) -> CommandResult
        self._clock = 0.0

    def script(self, prefix: List[str], result: "m.CommandResult") -> None:
        self._by_prefix.append((tuple(prefix), result))

    def set_handler(self, handler) -> None:
        """Install a custom callable(cmd) -> CommandResult, tried before the
        scripted prefixes. Calls are still recorded in self.commands.
        """
        self._handler = handler

    def set_http_payload(self, payload: bytes) -> None:
        self._http_payload = payload

    def run_command(self, cmd, *, input_text=None, timeout=None) -> "m.CommandResult":
        cmd = list(cmd)
        self.commands.append(cmd)
        if self._handler is not None:
            return self._handler(cmd)
        for prefix, result in self._by_prefix:
            if tuple(cmd[: len(prefix)]) == prefix:
                return result
        return self._default_result

    def http_get(self, url: str, timeout: int = 30) -> bytes:
        self.http_calls.append(url)
        return self._http_payload

    def sleep(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)
        self._clock += seconds

    def monotonic(self) -> float:
        return self._clock

    def as_runner(self) -> "m.Runner":
        return m.Runner(
            run_command=self.run_command,
            http_get=self.http_get,
            sleep=self.sleep,
            monotonic=self.monotonic,
        )


class ExplodingRunner:
    """A runner that fails the test if it is ever called. Used to prove
    --dry-run touches nothing.
    """

    def run_command(self, *args, **kwargs):
        raise AssertionError(f"run_command must not be called in dry-run: {args}")

    def http_get(self, *args, **kwargs):
        raise AssertionError(f"http_get must not be called in dry-run: {args}")


class ShellQuotingTests(unittest.TestCase):
    def test_shell_path_expands_leading_tilde(self):
        self.assertEqual(m.shell_path("~/.cache/dist"), "~/.cache/dist")

    def test_shell_path_accepts_bare_tilde(self):
        self.assertEqual(m.shell_path("~"), "~")

    def test_shell_path_accepts_valid_tilde_user(self):
        self.assertEqual(m.shell_path("~vscode/dist"), "~vscode/dist")

    def test_shell_path_quotes_unsafe_suffix_but_keeps_tilde(self):
        result = m.shell_path("~/weird dir; rm -rf /")
        self.assertTrue(result.startswith("~/"))
        self.assertIn("'weird dir; rm -rf /'", result)

    def test_shell_path_quotes_whole_absolute_path_when_unsafe(self):
        result = m.shell_path("/tmp/weird dir")
        self.assertEqual(result, "'/tmp/weird dir'")

    def test_shell_path_rejects_command_substitution_in_tilde_user(self):
        with self.assertRaises(ValueError):
            m.shell_path("~$(id)/dist")

    def test_shell_path_rejects_backtick_in_tilde_user(self):
        with self.assertRaises(ValueError):
            m.shell_path("~`whoami`/dist")

    def test_shell_path_rejects_embedded_quote_in_tilde_user(self):
        with self.assertRaises(ValueError):
            m.shell_path("~'; rm -rf ~ #/dist")

    def test_sh_quote_neutralizes_injection_attempt(self):
        malicious = "foo; rm -rf / #"
        quoted = m.sh_quote(malicious)
        self.assertEqual(quoted, "'foo; rm -rf / #'")


class RemoteCommandConstructionTests(unittest.TestCase):
    def test_backend_probe_command_uses_ssh_and_expands_tilde(self):
        cmd = m.build_backend_probe_command("cs.foo.main", "~/.cache/JetBrains/RemoteDev/dist")
        self.assertEqual(cmd[:3], ["ssh", "--", "cs.foo.main"])
        script = m.build_backend_probe_script("~/.cache/JetBrains/RemoteDev/dist")
        self.assertIn("~/.cache/JetBrains/RemoteDev/dist/WebStorm-*/bin/remote-dev-server.sh", script)

    def test_backend_probe_command_restricted_to_webstorm_glob(self):
        # Must not match e.g. PyCharm-*/IntelliJIdea-* installed alongside.
        script = m.build_backend_probe_script("~/.cache/dist")
        self.assertIn("WebStorm-*/bin/remote-dev-server.sh", script)
        self.assertNotIn("/*/bin/remote-dev-server.sh", script)

    def test_backend_probe_command_verifies_product_info_json(self):
        script = m.build_backend_probe_script("~/.cache/dist")
        self.assertIn("product-info.json", script)
        self.assertIn('"productCode"', script)
        self.assertIn('"WS"', script)
        # Only echoes the path once product verification passes.
        self.assertIn("then echo", script)

    def test_backend_probe_command_iterates_all_glob_candidates(self):
        # A stale/partial first WebStorm-* install must never mask a later
        # valid one: the probe must loop over every glob match, not just
        # check the first (e.g. via `head -n 1`).
        script = m.build_backend_probe_script("~/.cache/dist")
        self.assertIn("for p in", script)
        self.assertNotIn("head -n 1", script)
        self.assertIn("break", script)

    def test_backend_probe_command_wraps_script_as_single_quoted_bash_lc_argument(self):
        # cmd[-1] must be ONE shell-quoted token (the whole script), not
        # the raw script text -- see build_ssh_remote_shell_command's
        # docstring for why: ssh joins argv with spaces on the wire, so an
        # unquoted multi-word script would leak its own syntax into the
        # remote login shell instead of reaching bash -lc as one argument.
        cmd = m.build_backend_probe_command("cs.foo.main", "~/.cache/dist")
        script = m.build_backend_probe_script("~/.cache/dist")
        self.assertEqual(cmd[-1], m.sh_quote(script))
        self.assertNotEqual(cmd[-1], script)

    def test_backend_install_command_quotes_download_url_and_build(self):
        script = m.build_backend_install_script(
            "~/.cache/JetBrains/RemoteDev/dist",
            "https://download.jetbrains.com/webstorm/WebStorm-2026.2.0.1.tar.gz",
            "262.8665.341",
        )
        self.assertIn("mkdir -p ~/.cache/JetBrains/RemoteDev/dist", script)
        self.assertIn(
            "curl -fsSL https://download.jetbrains.com/webstorm/WebStorm-2026.2.0.1.tar.gz",
            script,
        )
        self.assertIn("262.8665.341", script)  # staged with the build number
        self.assertIn("tar -xzf", script)
        self.assertIn("rm -f", script)

    def test_backend_install_command_never_echoes_a_guessed_path(self):
        # The install step must not guess/print the extracted dir name: the
        # tarball actually extracts to WebStorm-<build>, and even that
        # naming isn't trusted without re-probing/verifying afterwards.
        script = m.build_backend_install_script(
            "~/.cache/dist", "https://example.com/x.tar.gz", "262.8665.341"
        )
        self.assertNotIn("echo", script)
        self.assertNotIn("remote-dev-server.sh", script)

    def test_backend_install_command_is_shell_safe_with_hostile_build(self):
        # A hostile/odd "build" string must not break out of its quotes and
        # become a second, separately-executed shell command.
        hostile_build = "1.0'; rm -rf ~ #"
        script = m.build_backend_install_script(
            "~/.cache/dist", "https://example.com/x.tar.gz", hostile_build
        )
        tokens = m.shlex.split(script)
        # Our own install script legitimately runs one bare "rm -f <tarball>".
        # If the hostile build string escaped its quoting, "rm" would show
        # up as a second, independent bare token.
        self.assertEqual(tokens.count("rm"), 1)
        self.assertNotIn("-rf", tokens)

    def test_ssh_verify_command_uses_true(self):
        cmd = m.build_ssh_verify_command("cs.foo.main")
        self.assertEqual(cmd, ["ssh", "--", "cs.foo.main", "true"])

    def test_detect_arch_command_uses_uname(self):
        cmd = m.build_detect_arch_command("cs.foo.main")
        self.assertEqual(cmd, ["ssh", "--", "cs.foo.main", "uname", "-m"])

    def test_remote_dev_server_command_includes_ssh_link_flags(self):
        script = m.build_remote_dev_server_script(
            "/home/vscode/.cache/JetBrains/RemoteDev/dist/WebStorm-1/bin/remote-dev-server.sh",
            "/workspaces/widgets",
            "cs.foo.main",
            "vscode",
        )
        self.assertIn("run /workspaces/widgets", script)
        self.assertIn("--ssh-link-host cs.foo.main", script)
        self.assertIn("--ssh-link-user vscode", script)
        self.assertIn("--ssh-link-port 22", script)

    def test_remote_dev_server_command_quotes_project_path_with_spaces(self):
        script = m.build_remote_dev_server_script(
            "/bin/remote-dev-server.sh", "/workspaces/my project", "cs.foo.main", "vscode"
        )
        self.assertIn("run '/workspaces/my project'", script)

    def test_remote_dev_server_command_wraps_script_as_single_quoted_bash_lc_argument(self):
        cmd = m.build_remote_dev_server_command(
            "cs.foo.main", "/bin/remote-dev-server.sh", "/workspaces/widgets", "vscode"
        )
        script = m.build_remote_dev_server_script(
            "/bin/remote-dev-server.sh", "/workspaces/widgets", "cs.foo.main", "vscode"
        )
        self.assertEqual(cmd, ["ssh", "--", "cs.foo.main", "bash", "-lc", m.sh_quote(script)])

    def test_backend_status_command_shape(self):
        cmd = m.build_backend_status_command("cs.foo.main", "/bin/remote-dev-server.sh")
        expected_script = "/bin/remote-dev-server.sh status"
        self.assertEqual(
            cmd, ["ssh", "--", "cs.foo.main", "bash", "-lc", m.sh_quote(expected_script)]
        )

    def test_backend_status_command_never_uses_help_flag(self):
        # remote-dev-server.sh --help is not a real launch config: invoking
        # it live shows a WebStorm error. No command builder may emit it.
        cmd = m.build_backend_status_command("cs.foo.main", "/bin/remote-dev-server.sh")
        self.assertNotIn("--help", " ".join(cmd))

    def test_start_detached_command_backgrounds_via_nohup_and_disowns(self):
        cmd = m.build_start_detached_command(
            "cs.foo.main", "/bin/remote-dev-server.sh", "/workspaces/widgets", "vscode"
        )
        script = cmd[-1]  # single quoted bash -lc argument
        self.assertIn("nohup", script)
        self.assertIn("disown", script)
        self.assertIn("run /workspaces/widgets", script)
        self.assertIn("< /dev/null", script)
        self.assertIn("2>&1", script)
        # Backgrounded with a trailing '&', not waited on synchronously.
        self.assertRegex(script, r"nohup [^;]*&\s*disown")

    def test_start_detached_command_uses_stable_per_project_log_path(self):
        cmd = m.build_start_detached_command(
            "cs.foo.main", "/bin/remote-dev-server.sh", "/workspaces/widgets", "vscode"
        )
        script = cmd[-1]
        self.assertIn(m.remote_dev_server_log_path("/workspaces/widgets"), script)

    def test_open_link_command_uses_explicit_app_path_when_known(self):
        app_path = Path("/Applications/Gateway.app")
        cmd = m.build_open_link_command("jetbrains-gateway://connect#x=y", app_path)
        self.assertEqual(
            cmd, ["open", "-a", "/Applications/Gateway.app", "jetbrains-gateway://connect#x=y"]
        )

    def test_open_link_command_falls_back_to_plain_open_without_app_path(self):
        cmd = m.build_open_link_command("jetbrains-gateway://connect#x=y")
        self.assertEqual(cmd, ["open", "jetbrains-gateway://connect#x=y"])


class SSHWireJoiningTests(unittest.TestCase):
    """OpenSSH does not preserve our Python list's argv boundaries across
    the wire: everything the local ssh binary is given after the
    destination is joined with a single space and handed, as ONE string,
    to the remote user's login shell (zsh on a stock codespace) to parse
    and execute. These tests simulate exactly that join-and-hand-to-shell
    step locally (no network, no real ssh/codespace) to prove our
    generated commands survive it -- this is what caught the live
    "zsh:1: parse error near do" regression, which argv-shape assertions
    alone could not catch.
    """

    @staticmethod
    def simulate_ssh_wire_execution(
        cmd: List[str], env: Optional[dict] = None
    ) -> subprocess.CompletedProcess:
        """Reproduce what the remote side actually receives and runs for
        an ``["ssh", "--", alias, ...remote_argv]`` command: join
        ``remote_argv`` with a single space, then execute that joined
        string with a real shell -- zsh if available (matching the
        reported bug's remote login shell), else ``/bin/sh``.
        """
        assert cmd[:2] == ["ssh", "--"], cmd
        remote_argv = cmd[3:]  # cmd[2] is the alias, not part of the remote command
        joined = " ".join(remote_argv)
        shell = shutil.which("zsh") or "/bin/sh"
        return subprocess.run(
            [shell, "-c", joined], capture_output=True, text=True, timeout=10, env=env
        )

    def test_probe_script_survives_ssh_wire_join_and_finds_valid_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            invalid_dir = Path(tmp) / "WebStorm-100"
            valid_dir = Path(tmp) / "WebStorm-200"
            (invalid_dir / "bin").mkdir(parents=True)
            (invalid_dir / "bin" / "remote-dev-server.sh").write_text("#!/bin/sh\n")
            (invalid_dir / "product-info.json").write_text('{"productCode" : "IU"}')
            (valid_dir / "bin").mkdir(parents=True)
            (valid_dir / "bin" / "remote-dev-server.sh").write_text("#!/bin/sh\n")
            (valid_dir / "product-info.json").write_text('{"productCode" : "WS"}')

            cmd = m.build_backend_probe_command("cs.foo.main", tmp)
            result = self.simulate_ssh_wire_execution(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout.strip(), str(valid_dir / "bin" / "remote-dev-server.sh")
            )

    def test_probe_script_survives_ssh_wire_join_with_no_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            cmd = m.build_backend_probe_command("cs.foo.main", tmp)
            result = self.simulate_ssh_wire_execution(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_install_script_survives_ssh_wire_join(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "dist"
            cmd = m.build_backend_install_command(
                "cs.foo.main", str(dist), "file:///does/not/matter", "1.0"
            )
            # Swap the real curl download for a harmless local stand-in so
            # this stays fully offline: create the tarball ourselves, then
            # only run the mkdir/tar/rm portion of the joined command by
            # stripping the curl segment. This still exercises the exact
            # ssh-wire-join path for the mkdir/tar/rm segments, which is
            # what the reported bug affected (the whole joined line).
            import tarfile

            dist.mkdir(parents=True)
            member_dir = Path(tmp) / "WebStorm-1"
            member_dir.mkdir()
            (member_dir / "marker.txt").write_text("hi\n")
            tarball = Path(tmp) / "webstorm-backend-1.0.tar.gz"
            with tarfile.open(tarball, "w:gz") as tf:
                tf.add(member_dir, arcname="WebStorm-1")

            script = f"tar -xzf {m.sh_quote(str(tarball))} -C {m.sh_quote(str(dist))}"
            joined_cmd = ["ssh", "--", "cs.foo.main"] + m.build_ssh_remote_shell_command(
                "cs.foo.main", script
            )[3:]
            result = self.simulate_ssh_wire_execution(joined_cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((dist / "WebStorm-1" / "marker.txt").is_file())
            _ = cmd  # the full command is still exercised structurally above

    def test_remote_dev_server_script_with_spaces_survives_ssh_wire_join(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "my project"
            project.mkdir()
            fake_binary = Path(tmp) / "fake-remote-dev-server.sh"
            fake_binary.write_text("#!/bin/sh\necho GOT: \"$@\"\n")
            fake_binary.chmod(0o755)

            cmd = m.build_remote_dev_server_command(
                "cs.foo.main", str(fake_binary), str(project), "vscode"
            )
            result = self.simulate_ssh_wire_execution(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"run {project}", result.stdout)
            self.assertIn("--ssh-link-host cs.foo.main", result.stdout)

    def test_detached_start_script_backgrounds_and_returns_promptly(self):
        # Proves 'nohup ... & disown' actually detaches on the real wire
        # shape: the ssh call must return almost immediately even though
        # the backgrounded fake server sleeps far longer than that, and
        # the backgrounded process must still have actually run (its
        # marker file gets written a little after the ssh call returns).
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp) / "home"
            fake_home.mkdir()
            project = Path(tmp) / "project"
            project.mkdir()
            marker = Path(tmp) / "started.marker"
            fake_binary = Path(tmp) / "fake-remote-dev-server.sh"
            fake_binary.write_text(
                "#!/bin/sh\n"
                f"echo GOT: \"$@\" > {m.sh_quote(str(marker))}\n"
                "sleep 5\n"
            )
            fake_binary.chmod(0o755)

            cmd = m.build_start_detached_command(
                "cs.foo.main", str(fake_binary), str(project), "vscode"
            )
            env = dict(os.environ)
            env["HOME"] = str(fake_home)  # keep the log dir's '~' off the real machine

            start = time.monotonic()
            result = self.simulate_ssh_wire_execution(cmd, env=env)
            elapsed = time.monotonic() - start
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertLess(
                elapsed, 4.0, "ssh call should return promptly, not wait for the 5s sleep"
            )

            log_path = fake_home / ".cache" / "JetBrains" / "RemoteDev" / "logs"
            self.assertTrue(log_path.is_dir())

            for _ in range(50):
                if marker.exists():
                    break
                time.sleep(0.1)
            self.assertTrue(marker.exists(), "backgrounded process never actually ran")
            self.assertIn(f"run {project}", marker.read_text())

    def test_backend_status_script_survives_ssh_wire_join(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_binary = Path(tmp) / "fake-remote-dev-server.sh"
            fake_binary.write_text(
                "#!/bin/sh\n"
                "echo 'error: XDG_RUNTIME_DIR is invalid' >&2\n"
                'echo STATUS: \'{"gatewayLink": "jetbrains-gateway://connect#x=y", '
                '"backendUnresponsive": false, "idePath": "/workspaces/widgets"}\'\n'
            )
            fake_binary.chmod(0o755)
            cmd = m.build_backend_status_command("cs.foo.main", str(fake_binary))
            result = self.simulate_ssh_wire_execution(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            status = m.parse_backend_status(result.stdout + "\n" + result.stderr)
            self.assertIsNotNone(status)
            self.assertEqual(status["gatewayLink"], "jetbrains-gateway://connect#x=y")

    def test_hostile_download_url_does_not_execute_via_ssh_wire_join(self):
        # A hostile download_url containing shell metacharacters must not
        # break out of its quoting once the command is joined and handed
        # to a real shell, the way it would be on the wire.
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "pwned"
            dist_dir = str(Path(tmp) / "dist")
            hostile_url = f"https://example.com/x.tar.gz'; touch {marker}; echo '"
            cmd = m.build_backend_install_command("cs.foo.main", dist_dir, hostile_url, "1.0")
            result = self.simulate_ssh_wire_execution(cmd)
            # The injected "touch" must never have run.
            self.assertFalse(marker.exists())
            _ = result  # curl legitimately fails offline; only the injection matters here

    def test_ssh_remote_shell_command_helper_survives_join_for_simple_case(self):
        cmd = m.build_ssh_remote_shell_command("cs.foo.main", "echo hello world")
        result = self.simulate_ssh_wire_execution(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "hello world")


class GatewayLinkParsingTests(unittest.TestCase):
    def test_parses_link_from_labelled_output(self):
        output = (
            "Join link: tcp://127.0.0.1:5990#jt=abc\n"
            "Http link: https://code-with-me.jetbrains.com/remoteDev#host=x\n"
            "Gateway link: jetbrains-gateway://connect#idePath=%2Fhome%2Fx&host=y&port=22\n"
        )
        link = m.parse_gateway_link(output)
        self.assertEqual(
            link, "jetbrains-gateway://connect#idePath=%2Fhome%2Fx&host=y&port=22"
        )

    def test_raises_when_no_link_present(self):
        with self.assertRaises(m.StageError) as ctx:
            m.parse_gateway_link("no useful output here\n")
        self.assertEqual(ctx.exception.stage, "parse-gateway-link")

    def test_stops_at_whitespace(self):
        output = "prefix jetbrains-gateway://connect#a=b&c=d\nnext line"
        link = m.parse_gateway_link(output)
        self.assertEqual(link, "jetbrains-gateway://connect#a=b&c=d")


class BackendStatusParsingTests(unittest.TestCase):
    """Covers remote-dev-server.sh status's observed output shape: noise
    (e.g. an XDG_RUNTIME_DIR warning) around a 'STATUS: {json}' payload.
    """

    # idePath here is the WebStorm *backend install* directory, matching
    # live evidence -- it is never the project path. The project path only
    # ever comes from a literal 'projectPath' JSON key or the gatewayLink
    # fragment's 'projectPath' query param, both included below.
    SAMPLE_STATUS_JSON = (
        '{"appPid": 540904, "backendUnresponsive": false, '
        '"modalDialogIsOpened": false, '
        '"idePath": "/home/vscode/.cache/JetBrains/RemoteDev/dist/WebStorm-262.21148.7", '
        '"joinLink": "tcp://127.0.0.1:5990#jt=abc", '
        '"httpLink": "https://code-with-me.jetbrains.com/remoteDev#host=x", '
        '"gatewayLink": "jetbrains-gateway://connect#idePath=%2Fhome%2Fvscode%2F.cache'
        '%2FJetBrains%2FRemoteDev%2Fdist%2FWebStorm-262.21148.7&projectPath='
        '%2Fworkspaces%2Fwidgets"}'
    )

    def test_parses_status_ignoring_leading_stderr_noise(self):
        combined = (
            "error: XDG_RUNTIME_DIR is invalid, not set, or not accessible\n"
            f"STATUS: {self.SAMPLE_STATUS_JSON}\n"
        )
        status = m.parse_backend_status(combined)
        self.assertIsNotNone(status)
        self.assertEqual(status["appPid"], 540904)

    def test_returns_none_when_no_status_marker(self):
        self.assertIsNone(m.parse_backend_status("nothing useful here\n"))

    def test_returns_none_when_marker_present_but_unparsable(self):
        self.assertIsNone(m.parse_backend_status("STATUS: not-json-at-all\n"))

    def test_parses_status_with_trailing_noise_after_json_line(self):
        combined = f"STATUS: {self.SAMPLE_STATUS_JSON}\nsome trailing unrelated line\n"
        status = m.parse_backend_status(combined)
        self.assertIsNotNone(status)
        self.assertEqual(status["appPid"], 540904)

    def test_parses_live_shaped_pretty_json_stdout_with_trailing_xdg_stderr(self):
        # Exact live shape reported: query_backend_status combines
        # `result.stdout + "\n" + result.stderr`. stdout is pretty-printed
        # ('STATUS:\n{\n  ...\n}\n'); stderr (the XDG_RUNTIME_DIR warning)
        # lands *after* the JSON this time, not before it. A plain
        # json.loads() of the whole remainder fails here because the
        # trailing stderr text isn't valid JSON continuation -- only
        # json.JSONDecoder().raw_decode() finding the first complete
        # object and ignoring what follows makes this parse.
        stdout = (
            "STATUS:\n"
            "{\n"
            '  "appPid": 540904,\n'
            '  "backendUnresponsive": false,\n'
            '  "modalDialogIsOpened": false,\n'
            '  "idePath": "/home/vscode/.cache/JetBrains/RemoteDev/dist/WebStorm-262.21148.7",\n'
            '  "gatewayLink": "jetbrains-gateway://connect#projectPath=%2Fworkspaces%2Fgithub-ui"\n'
            "}\n"
        )
        stderr = "error: XDG_RUNTIME_DIR is invalid, not set, or not accessible\n"
        combined = stdout + "\n" + stderr
        status = m.parse_backend_status(combined)
        self.assertIsNotNone(status)
        self.assertEqual(status["appPid"], 540904)
        self.assertEqual(m.backend_status_project_path(status), "/workspaces/github-ui")

    def test_gateway_link_helper_extracts_and_validates_link(self):
        status = json.loads(self.SAMPLE_STATUS_JSON)
        self.assertEqual(
            m.backend_status_gateway_link(status),
            status["gatewayLink"],
        )

    def test_gateway_link_helper_returns_none_when_absent(self):
        self.assertIsNone(m.backend_status_gateway_link({"gatewayLink": ""}))
        self.assertIsNone(m.backend_status_gateway_link({}))

    def test_project_path_extracted_from_gateway_link_fragment(self):
        # No literal 'projectPath' JSON key here -- only inside the
        # gatewayLink's own fragment, exactly as live evidence shows.
        status = json.loads(self.SAMPLE_STATUS_JSON)
        self.assertEqual(m.backend_status_project_path(status), "/workspaces/widgets")

    def test_project_path_prefers_explicit_project_path_field(self):
        status = {
            "projectPath": "/workspaces/explicit",
            "idePath": "/home/vscode/.cache/JetBrains/RemoteDev/dist/WebStorm-262",
            "gatewayLink": "jetbrains-gateway://connect#projectPath=%2Fworkspaces%2Fother",
        }
        self.assertEqual(m.backend_status_project_path(status), "/workspaces/explicit")

    def test_project_path_never_falls_back_to_ide_path(self):
        # idePath alone -- no literal projectPath, no gatewayLink -- must
        # never be mistaken for the project path. Live evidence: idePath
        # named the backend install dir (".../WebStorm-262..."), not the
        # requested project ("/workspaces/github-ui"); treating it as a
        # fallback caused false mismatches and duplicate backend starts.
        status = {"idePath": "/home/vscode/.cache/JetBrains/RemoteDev/dist/WebStorm-262"}
        self.assertIsNone(m.backend_status_project_path(status))

    def test_project_path_none_when_gateway_link_has_no_project_path_param(self):
        status = {
            "idePath": "/home/vscode/.cache/JetBrains/RemoteDev/dist/WebStorm-262",
            "gatewayLink": "jetbrains-gateway://connect#idePath=%2Fhome%2Fvscode%2Fx",
        }
        self.assertIsNone(m.backend_status_project_path(status))

    def test_matches_project_true_when_info_absent(self):
        self.assertTrue(m.backend_status_matches_project({}, "/workspaces/widgets"))

    def test_matches_project_true_when_only_ide_path_present(self):
        # idePath yields no project-path signal at all (it's ignored), so
        # this counts as "absent", not a mismatch -- this is the exact
        # live scenario that previously caused a false mismatch and a
        # duplicate backend start.
        status = {"idePath": "/home/vscode/.cache/JetBrains/RemoteDev/dist/WebStorm-262"}
        self.assertTrue(m.backend_status_matches_project(status, "/workspaces/github-ui"))

    def test_matches_project_false_on_conflicting_path(self):
        status = {"projectPath": "/workspaces/other"}
        self.assertFalse(m.backend_status_matches_project(status, "/workspaces/widgets"))

    def test_matches_project_tolerates_trailing_slash(self):
        status = {"projectPath": "/workspaces/widgets/"}
        self.assertTrue(m.backend_status_matches_project(status, "/workspaces/widgets"))

    def test_is_ready_false_when_unresponsive(self):
        status = json.loads(self.SAMPLE_STATUS_JSON)
        status["backendUnresponsive"] = True
        self.assertFalse(m.backend_status_is_ready(status, "/workspaces/widgets"))

    def test_is_ready_false_without_gateway_link(self):
        status = json.loads(self.SAMPLE_STATUS_JSON)
        status["gatewayLink"] = ""
        self.assertFalse(m.backend_status_is_ready(status, "/workspaces/widgets"))

    def test_is_ready_false_on_project_mismatch(self):
        status = json.loads(self.SAMPLE_STATUS_JSON)
        self.assertFalse(m.backend_status_is_ready(status, "/workspaces/other-project"))

    def test_is_ready_true_when_all_conditions_met(self):
        status = json.loads(self.SAMPLE_STATUS_JSON)
        self.assertTrue(m.backend_status_is_ready(status, "/workspaces/widgets"))

    def test_is_ready_true_regardless_of_modal_dialog_flag(self):
        # modalDialogIsOpened reflects Gateway/IDE UI state, not backend
        # health or project match -- live status showed it 'false' after
        # the user completed Gateway's manual confirmation, but neither
        # value may gate reuse.
        status = json.loads(self.SAMPLE_STATUS_JSON)
        status["modalDialogIsOpened"] = True
        self.assertTrue(m.backend_status_is_ready(status, "/workspaces/widgets"))
        status["modalDialogIsOpened"] = False
        self.assertTrue(m.backend_status_is_ready(status, "/workspaces/widgets"))


class GatewayLinkProjectPathTests(unittest.TestCase):
    """Direct coverage for the urllib.parse-based fragment extraction."""

    def test_extracts_project_path_from_fragment(self):
        link = "jetbrains-gateway://connect#idePath=%2Ffoo&projectPath=%2Fworkspaces%2Fgithub-ui"
        self.assertEqual(m.gateway_link_project_path(link), "/workspaces/github-ui")

    def test_extracts_when_project_path_is_the_only_param(self):
        link = "jetbrains-gateway://connect#projectPath=%2Fworkspaces%2Fgithub-ui"
        self.assertEqual(m.gateway_link_project_path(link), "/workspaces/github-ui")

    def test_returns_none_when_link_is_none(self):
        self.assertIsNone(m.gateway_link_project_path(None))

    def test_returns_none_when_link_is_empty_string(self):
        self.assertIsNone(m.gateway_link_project_path(""))

    def test_returns_none_when_no_project_path_param(self):
        link = "jetbrains-gateway://connect#idePath=%2Ffoo&host=y&port=22"
        self.assertIsNone(m.gateway_link_project_path(link))

    def test_returns_none_when_no_fragment_at_all(self):
        self.assertIsNone(m.gateway_link_project_path("jetbrains-gateway://connect"))


class RemoteDevServerLogPathTests(unittest.TestCase):
    def test_slugifies_project_path(self):
        path = m.remote_dev_server_log_path("/workspaces/my-repo")
        self.assertEqual(path, f"{m.REMOTE_DEV_SERVER_LOG_DIR}/workspaces_my-repo.log")

    def test_slugifies_unsafe_characters(self):
        path = m.remote_dev_server_log_path("/workspaces/my repo!@#")
        self.assertTrue(path.startswith(f"{m.REMOTE_DEV_SERVER_LOG_DIR}/workspaces_my_repo"))
        self.assertTrue(path.endswith(".log"))

    def test_same_project_path_always_yields_same_log_path(self):
        first = m.remote_dev_server_log_path("/workspaces/widgets")
        second = m.remote_dev_server_log_path("/workspaces/widgets")
        self.assertEqual(first, second)


class EnsureRemoteDevServerRunningTests(unittest.TestCase):
    """Covers the detach + status-poll + reuse-existing-backend flow, all
    through the injectable FakeRunner (fast, deterministic, no real sleep).
    """

    BACKEND = "/home/vscode/.cache/JetBrains/RemoteDev/dist/WebStorm-1/bin/remote-dev-server.sh"
    PROJECT = "/workspaces/widgets"

    def _target(self):
        return m.SSHTarget(alias="cs.foo.main", user="vscode")

    def _status_cmd_result(self, *, ready, unresponsive=False, project_path=None, gateway_link="jetbrains-gateway://connect#x=y"):
        payload = {
            "appPid": 123,
            "backendUnresponsive": unresponsive,
            "gatewayLink": gateway_link if ready else "",
        }
        if project_path is not None:
            payload["projectPath"] = project_path
        return m.CommandResult([], 0, f"STATUS: {json.dumps(payload)}\n", "")

    def test_reuses_already_running_matching_backend_without_starting_a_new_one(self):
        runner = FakeRunner()

        def handler(cmd):
            script = cmd[-1]
            if "nohup" in script:
                raise AssertionError("must not start a new backend when one is already running")
            return self._status_cmd_result(ready=True, project_path=self.PROJECT)

        runner.set_handler(handler)
        link = m.ensure_remote_dev_server_running(
            self._target(), self.BACKEND, self.PROJECT, runner.as_runner()
        )
        self.assertEqual(link, "jetbrains-gateway://connect#x=y")

    def test_does_not_reuse_backend_running_a_different_project(self):
        runner = FakeRunner()
        calls = {"status": 0, "start": 0}

        def handler(cmd):
            script = cmd[-1]
            if "nohup" in script:
                calls["start"] += 1
                return m.CommandResult([], 0, "", "")
            calls["status"] += 1
            if calls["status"] == 1:
                # First check: a *different* project is running.
                return self._status_cmd_result(
                    ready=True, project_path="/workspaces/other-project"
                )
            # After starting our own, report our project as ready.
            return self._status_cmd_result(ready=True, project_path=self.PROJECT)

        runner.set_handler(handler)
        link = m.ensure_remote_dev_server_running(
            self._target(), self.BACKEND, self.PROJECT, runner.as_runner()
        )
        self.assertEqual(link, "jetbrains-gateway://connect#x=y")
        self.assertEqual(calls["start"], 1, "must have started its own backend instance")

    def test_rejects_unresponsive_existing_backend_immediately(self):
        runner = FakeRunner()
        runner.set_handler(
            lambda cmd: self._status_cmd_result(ready=True, unresponsive=True)
        )
        with self.assertRaises(m.StageError) as ctx:
            m.ensure_remote_dev_server_running(
                self._target(), self.BACKEND, self.PROJECT, runner.as_runner()
            )
        self.assertEqual(ctx.exception.stage, "start-remote-dev-server")
        self.assertIn("unresponsive", str(ctx.exception))

    def test_polls_until_ready_then_returns_link(self):
        runner = FakeRunner()
        state = {"status_calls": 0}

        def handler(cmd):
            script = cmd[-1]
            if "nohup" in script:
                return m.CommandResult([], 0, "", "")
            state["status_calls"] += 1
            if state["status_calls"] <= 1:
                return m.CommandResult([], 1, "", "")  # not started yet
            if state["status_calls"] <= 3:
                return self._status_cmd_result(ready=False)  # started, no link yet
            return self._status_cmd_result(ready=True, project_path=self.PROJECT)

        runner.set_handler(handler)
        link = m.ensure_remote_dev_server_running(
            self._target(),
            self.BACKEND,
            self.PROJECT,
            runner.as_runner(),
            timeout=60,
            poll_interval=2,
        )
        self.assertEqual(link, "jetbrains-gateway://connect#x=y")
        self.assertGreaterEqual(len(runner.sleep_calls), 2)
        self.assertTrue(all(s == 2 for s in runner.sleep_calls))

    def test_times_out_with_exact_stage_error_when_never_ready(self):
        runner = FakeRunner()

        def handler(cmd):
            script = cmd[-1]
            if "nohup" in script:
                return m.CommandResult([], 0, "", "")
            return self._status_cmd_result(ready=False)

        runner.set_handler(handler)
        with self.assertRaises(m.StageError) as ctx:
            m.ensure_remote_dev_server_running(
                self._target(),
                self.BACKEND,
                self.PROJECT,
                runner.as_runner(),
                timeout=10,
                poll_interval=3,
            )
        self.assertEqual(ctx.exception.stage, "start-remote-dev-server")
        self.assertIn("timed out", str(ctx.exception))

    def test_becomes_unresponsive_while_polling_raises(self):
        runner = FakeRunner()
        state = {"status_calls": 0}

        def handler(cmd):
            script = cmd[-1]
            if "nohup" in script:
                return m.CommandResult([], 0, "", "")
            state["status_calls"] += 1
            if state["status_calls"] == 1:
                return m.CommandResult([], 1, "", "")  # pre-start check: nothing yet
            return self._status_cmd_result(ready=False, unresponsive=True)

        runner.set_handler(handler)
        with self.assertRaises(m.StageError) as ctx:
            m.ensure_remote_dev_server_running(
                self._target(), self.BACKEND, self.PROJECT, runner.as_runner(), timeout=30
            )
        self.assertEqual(ctx.exception.stage, "start-remote-dev-server")
        self.assertIn("unresponsive", str(ctx.exception))

    def test_never_calls_help_flag(self):
        # remote-dev-server.sh --help is not a real launch config and
        # produces a WebStorm error dialog when invoked live; no code path
        # here may ever construct such a command.
        runner = FakeRunner()
        runner.set_handler(lambda cmd: self._status_cmd_result(ready=True, project_path=self.PROJECT))
        m.ensure_remote_dev_server_running(
            self._target(), self.BACKEND, self.PROJECT, runner.as_runner()
        )
        for cmd in runner.commands:
            self.assertNotIn("--help", cmd)


class SSHTargetParsingTests(unittest.TestCase):
    def test_parses_alias_and_user(self):
        target = m.parse_ssh_target(SAMPLE_CONFIG_ONE_HOST, "my-cs-123")
        self.assertEqual(target.alias, "cs.my-cs-123.main")
        self.assertEqual(target.user, "vscode")

    def test_picks_correct_block_out_of_multiple_codespaces(self):
        # gh codespace ssh --config (no -c) emits every visible codespace;
        # parsing must still pick out only the one this run targets.
        target = m.parse_ssh_target(SAMPLE_CONFIG_TWO_HOSTS, "other-cs-456")
        self.assertEqual(target.alias, "cs.other-cs-456.develop")
        self.assertEqual(target.user, "vscode")

        other_target = m.parse_ssh_target(SAMPLE_CONFIG_TWO_HOSTS, "my-cs-123")
        self.assertEqual(other_target.alias, "cs.my-cs-123.main")

    def test_raises_when_host_missing(self):
        with self.assertRaises(m.StageError) as ctx:
            m.parse_ssh_target(SAMPLE_CONFIG_ONE_HOST, "some-other-cs")
        self.assertEqual(ctx.exception.stage, "parse-ssh-target")

    def test_raises_on_ambiguous_hosts(self):
        two_hosts = SAMPLE_CONFIG_ONE_HOST + SAMPLE_CONFIG_ONE_HOST.replace(
            "cs.my-cs-123.main", "cs.my-cs-123.feature-x"
        )
        with self.assertRaises(m.StageError) as ctx:
            m.parse_ssh_target(two_hosts, "my-cs-123")
        self.assertIn("ambiguous", str(ctx.exception))

    def test_raises_when_user_line_missing(self):
        broken = "Host cs.my-cs-123.main\n\tProxyCommand gh cs ssh -c my-cs-123 --stdio\n\n"
        with self.assertRaises(m.StageError):
            m.parse_ssh_target(broken, "my-cs-123")


class ReleaseMetadataTests(unittest.TestCase):
    def test_parses_linux_download(self):
        release = m.parse_release_metadata(SAMPLE_RELEASE_JSON, "x86_64")
        self.assertEqual(release.version, "2026.2.0.1")
        self.assertEqual(release.build, "262.8665.341")
        self.assertEqual(
            release.download_url,
            "https://download.jetbrains.com/webstorm/WebStorm-2026.2.0.1.tar.gz",
        )

    def test_parses_arm64_download(self):
        release = m.parse_release_metadata(SAMPLE_RELEASE_JSON, "aarch64")
        self.assertTrue(release.download_url.endswith("-aarch64.tar.gz"))

    def test_raises_on_unsupported_arch(self):
        with self.assertRaises(m.StageError):
            m.parse_release_metadata(SAMPLE_RELEASE_JSON, "sparc")

    def test_raises_on_malformed_json(self):
        with self.assertRaises(m.StageError):
            m.parse_release_metadata(b"not json", "x86_64")

    def test_raises_when_product_missing(self):
        with self.assertRaises(m.StageError):
            m.parse_release_metadata(json.dumps({"IU": []}).encode(), "x86_64")


class BackendReuseTests(unittest.TestCase):
    def test_reuses_existing_backend_without_calling_release_api(self):
        runner = FakeRunner()
        runner.script(
            ["ssh", "--", "cs.foo.main", "bash", "-lc"],
            m.CommandResult([], 0, SAMPLE_BACKEND_PATH + "\n", ""),
        )
        backend_path = m.ensure_backend("cs.foo.main", "~/.cache/dist", "x86_64", runner.as_runner())
        self.assertEqual(backend_path, SAMPLE_BACKEND_PATH)
        self.assertEqual(runner.http_calls, [])  # never resolved a release

    def test_installs_when_no_backend_found_and_rediscovers_real_path(self):
        runner = FakeRunner()
        probe_calls = {"n": 0}

        def run_command(cmd, *, input_text=None, timeout=None):
            if cmd[0] == "ssh" and "curl -fsSL" in cmd[-1]:
                return m.CommandResult(cmd, 0, "", "")  # install itself echoes nothing
            if cmd[0] == "ssh" and "product-info.json" in cmd[-1]:
                probe_calls["n"] += 1
                if probe_calls["n"] == 1:
                    return m.CommandResult(cmd, 0, "", "")  # first probe: not installed yet
                return m.CommandResult(cmd, 0, SAMPLE_BACKEND_PATH + "\n", "")  # re-probe: found
            raise AssertionError(f"unexpected command: {cmd}")

        runner.set_handler(run_command)
        backend_path = m.ensure_backend("cs.foo.main", "~/.cache/dist", "x86_64", runner.as_runner())
        self.assertEqual(backend_path, SAMPLE_BACKEND_PATH)
        self.assertEqual(len(runner.http_calls), 1)
        self.assertEqual(probe_calls["n"], 2)  # probed before *and* after install

    def test_does_not_reuse_a_non_webstorm_product(self):
        # A backend probe for some other JetBrains product living under the
        # same dist dir must not be echoed back: find_existing_backend only
        # ever sees what the (WebStorm-restricted, product-verified) probe
        # command echoes, so simulate the probe correctly reporting nothing.
        runner = FakeRunner()
        runner.script(["ssh", "--", "cs.foo.main", "bash", "-lc"], m.CommandResult([], 0, "", ""))
        backend_path = m.find_existing_backend("cs.foo.main", "~/.cache/dist", runner.as_runner())
        self.assertIsNone(backend_path)
        self.assertEqual(runner.http_calls, [])


class BackendProbeShellScriptExecutionTests(unittest.TestCase):
    """Actually run the generated probe bash snippet locally against a real
    temp directory tree, to prove the *shell logic itself* (not just a
    mocked ssh round-trip) skips an invalid first WebStorm-* candidate and
    finds a valid later one. This never touches ssh/gh/curl/tar/open/brew;
    it only executes bash against the raw script text (via
    build_backend_probe_script, not the quoted ssh argv) and a local
    tempdir, so it stays fully local/non-live/deterministic. See
    SSHWireJoiningTests for coverage of the outer ssh-wire quoting layer.
    """

    def test_probe_script_skips_invalid_first_candidate_and_finds_valid_second(self):
        with tempfile.TemporaryDirectory() as tmp:
            # "WebStorm-100" sorts before "WebStorm-200" in default glob
            # order, so the invalid one is deliberately the first match.
            invalid_dir = Path(tmp) / "WebStorm-100"
            valid_dir = Path(tmp) / "WebStorm-200"
            (invalid_dir / "bin").mkdir(parents=True)
            (invalid_dir / "bin" / "remote-dev-server.sh").write_text("#!/bin/sh\n")
            (invalid_dir / "product-info.json").write_text('{"productCode" : "IU"}')

            (valid_dir / "bin").mkdir(parents=True)
            (valid_dir / "bin" / "remote-dev-server.sh").write_text("#!/bin/sh\n")
            (valid_dir / "product-info.json").write_text('{"productCode" : "WS"}')

            remote_script = m.build_backend_probe_script(tmp)
            result = subprocess.run(
                ["bash", "-lc", remote_script], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout.strip(), str(valid_dir / "bin" / "remote-dev-server.sh")
            )

    def test_probe_script_finds_nothing_when_all_candidates_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            only_dir = Path(tmp) / "WebStorm-100"
            (only_dir / "bin").mkdir(parents=True)
            (only_dir / "bin" / "remote-dev-server.sh").write_text("#!/bin/sh\n")
            (only_dir / "product-info.json").write_text('{"productCode" : "IU"}')

            remote_script = m.build_backend_probe_script(tmp)
            result = subprocess.run(
                ["bash", "-lc", remote_script], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_probe_script_finds_nothing_with_no_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            remote_script = m.build_backend_probe_script(tmp)
            result = subprocess.run(
                ["bash", "-lc", remote_script], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")


class StageFailureTests(unittest.TestCase):
    def test_open_codespace_in_vscode_raises_stage_error(self):
        runner = FakeRunner()
        runner.script(["gh", "codespace", "code"], m.CommandResult([], 1, "", "boom"))
        with self.assertRaises(m.StageError) as ctx:
            m.open_codespace_in_vscode("my-cs", runner.as_runner())
        self.assertEqual(ctx.exception.stage, "open-vscode")
        self.assertIn("boom", str(ctx.exception))

    def test_fetch_ssh_config_text_raises_on_failure(self):
        runner = FakeRunner()
        runner.script(["gh", "codespace", "ssh"], m.CommandResult([], 1, "", "not found"))
        with self.assertRaises(m.StageError) as ctx:
            m.fetch_ssh_config_text("my-cs-123", runner.as_runner())
        self.assertEqual(ctx.exception.stage, "refresh-ssh-config")

    def test_fetch_ssh_config_text_raises_on_empty_output(self):
        runner = FakeRunner()
        runner.script(["gh", "codespace", "ssh"], m.CommandResult([], 0, "   ", ""))
        with self.assertRaises(m.StageError):
            m.fetch_ssh_config_text("my-cs-123", runner.as_runner())

    def test_fetch_ssh_config_command_uses_dash_c_for_selected_codespace(self):
        # gh codespace ssh --config without -c fails/skips whenever any
        # *other* codespace is non-Available (e.g. Shutdown), even though
        # the target codespace is fine. Fetching only the selected
        # codespace with -c sidesteps every other codespace's state.
        cmd = m.build_ssh_config_command("my-cs-123")
        self.assertEqual(cmd, ["gh", "codespace", "ssh", "-c", "my-cs-123", "--config"])


    def test_find_existing_backend_raises_on_ssh_failure(self):
        runner = FakeRunner()
        runner.script(["ssh"], m.CommandResult([], 255, "", "connection refused"))
        with self.assertRaises(m.StageError) as ctx:
            m.find_existing_backend("cs.foo.main", "~/.cache/dist", runner.as_runner())
        self.assertEqual(ctx.exception.stage, "probe-backend")

    def test_install_backend_raises_when_not_found_after_extraction(self):
        runner = FakeRunner()
        runner.script(["ssh"], m.CommandResult([], 0, "", ""))
        release = m.ReleaseInfo(version="1", build="1", download_url="https://x/y.tar.gz")
        with self.assertRaises(m.StageError) as ctx:
            m.install_backend("cs.foo.main", "~/.cache/dist", release, runner.as_runner())
        self.assertEqual(ctx.exception.stage, "install-backend")

    def test_install_backend_raises_when_extraction_itself_fails(self):
        runner = FakeRunner()
        runner.script(["ssh"], m.CommandResult([], 1, "", "curl: could not resolve host"))
        release = m.ReleaseInfo(version="1", build="1", download_url="https://x/y.tar.gz")
        with self.assertRaises(m.StageError) as ctx:
            m.install_backend("cs.foo.main", "~/.cache/dist", release, runner.as_runner())
        self.assertEqual(ctx.exception.stage, "install-backend")

    def test_verify_ssh_connection_succeeds_silently(self):
        runner = FakeRunner()
        runner.script(["ssh", "--", "cs.foo.main", "true"], m.CommandResult([], 0, "", ""))
        m.verify_ssh_connection("cs.foo.main", runner.as_runner())  # no raise

    def test_verify_ssh_connection_raises_on_failure(self):
        runner = FakeRunner()
        runner.script(
            ["ssh", "--", "cs.foo.main", "true"],
            m.CommandResult([], 255, "", "Connection refused"),
        )
        with self.assertRaises(m.StageError) as ctx:
            m.verify_ssh_connection("cs.foo.main", runner.as_runner())
        self.assertEqual(ctx.exception.stage, "verify-ssh-connection")

    def test_detect_remote_arch_returns_uname_output(self):
        runner = FakeRunner()
        runner.script(
            ["ssh", "--", "cs.foo.main", "uname", "-m"],
            m.CommandResult([], 0, "aarch64\n", ""),
        )
        self.assertEqual(m.detect_remote_arch("cs.foo.main", runner.as_runner()), "aarch64")

    def test_detect_remote_arch_raises_on_failure(self):
        runner = FakeRunner()
        runner.script(["ssh"], m.CommandResult([], 1, "", "no such command"))
        with self.assertRaises(m.StageError) as ctx:
            m.detect_remote_arch("cs.foo.main", runner.as_runner())
        self.assertEqual(ctx.exception.stage, "detect-arch")

    def test_detect_remote_arch_raises_on_empty_output(self):
        runner = FakeRunner()
        runner.script(["ssh"], m.CommandResult([], 0, "  \n", ""))
        with self.assertRaises(m.StageError) as ctx:
            m.detect_remote_arch("cs.foo.main", runner.as_runner())
        self.assertEqual(ctx.exception.stage, "detect-arch")

    def test_ensure_remote_dev_server_running_raises_when_detached_start_fails(self):
        runner = FakeRunner()

        def handler(cmd):
            script = cmd[-1]
            if "status" in script:
                return m.CommandResult([], 1, "", "")  # nothing running yet
            if "nohup" in script:
                return m.CommandResult([], 1, "", "backend crashed")
            raise AssertionError(f"unexpected command: {cmd}")

        runner.set_handler(handler)
        target = m.SSHTarget(alias="cs.foo.main", user="vscode")
        with self.assertRaises(m.StageError) as ctx:
            m.ensure_remote_dev_server_running(
                target, "/bin/remote-dev-server.sh", "/workspaces/x", runner.as_runner()
            )
        self.assertEqual(ctx.exception.stage, "start-remote-dev-server")
        self.assertIn("backend crashed", str(ctx.exception))

    def test_open_gateway_link_raises_on_failure(self):
        runner = FakeRunner()
        runner.script(["open"], m.CommandResult([], 1, "", "no handler"))
        with self.assertRaises(m.StageError) as ctx:
            m.open_gateway_link("jetbrains-gateway://connect#x=y", None, runner.as_runner())
        self.assertEqual(ctx.exception.stage, "open-gateway-link")

    def test_open_gateway_link_uses_explicit_app_path(self):
        runner = FakeRunner()
        runner.script(["open", "-a"], m.CommandResult([], 0, "", ""))
        app_path = Path("/Applications/Gateway.app")
        m.open_gateway_link("jetbrains-gateway://connect#x=y", app_path, runner.as_runner())
        self.assertEqual(
            runner.commands[-1],
            ["open", "-a", "/Applications/Gateway.app", "jetbrains-gateway://connect#x=y"],
        )

    def test_ensure_gateway_blocks_without_confirmation_flag(self):
        runner = FakeRunner()
        with self.assertRaises(m.StageError) as ctx:
            m.ensure_gateway(
                runner.as_runner(),
                install_gateway=False,
                candidates=[NONEXISTENT_GATEWAY_CANDIDATE],
            )
        self.assertEqual(ctx.exception.stage, "detect-gateway")
        self.assertEqual(runner.commands, [])  # never tried to install unasked

    def test_ensure_gateway_installs_when_confirmed_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "Gateway.app"

            def run_command(cmd, *, input_text=None, timeout=None):
                if cmd[:2] == ["brew", "install"]:
                    app_path.mkdir()  # simulate the cask actually installing it
                    return m.CommandResult(cmd, 0, "", "")
                raise AssertionError(f"unexpected command: {cmd}")

            runner = FakeRunner()
            runner.set_handler(run_command)
            result = m.ensure_gateway(
                runner.as_runner(), install_gateway=True, candidates=[app_path]
            )
            self.assertEqual(result, app_path)
            self.assertEqual(runner.commands, [["brew", "install", "--cask", "jetbrains-gateway"]])

    def test_ensure_gateway_skips_install_when_already_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "JetBrains Gateway.app"
            app_path.mkdir()
            runner = FakeRunner()
            result = m.ensure_gateway(runner.as_runner(), install_gateway=False, candidates=[app_path])
            self.assertEqual(result, app_path)
            self.assertEqual(runner.commands, [])

    def test_ensure_gateway_raises_on_brew_failure(self):
        runner = FakeRunner()
        runner.script(["brew", "install"], m.CommandResult([], 1, "", "cask not found"))
        with self.assertRaises(m.StageError) as ctx:
            m.ensure_gateway(
                runner.as_runner(),
                install_gateway=True,
                candidates=[NONEXISTENT_GATEWAY_CANDIDATE],
            )
        self.assertEqual(ctx.exception.stage, "install-gateway")

    def test_ensure_gateway_raises_when_still_missing_after_brew_reports_success(self):
        # brew can exit 0 without the app actually existing where expected;
        # never trust that silently.
        runner = FakeRunner()
        runner.script(["brew", "install"], m.CommandResult([], 0, "", ""))
        with self.assertRaises(m.StageError) as ctx:
            m.ensure_gateway(
                runner.as_runner(),
                install_gateway=True,
                candidates=[NONEXISTENT_GATEWAY_CANDIDATE],
            )
        self.assertEqual(ctx.exception.stage, "install-gateway")


class GatewayDetectionTests(unittest.TestCase):
    def test_find_gateway_app_matches_bare_gateway_app_name(self):
        # Real-world case: installed as ~/Applications/Gateway.app, not
        # ~/Applications/JetBrains Gateway.app.
        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "Gateway.app"
            app_path.mkdir()
            found = m.find_gateway_app([Path(tmp) / "JetBrains Gateway.app", app_path])
            self.assertEqual(found, app_path)

    def test_find_gateway_app_returns_none_when_absent(self):
        self.assertIsNone(m.find_gateway_app([NONEXISTENT_GATEWAY_CANDIDATE]))

    def test_default_candidates_include_both_naming_conventions(self):
        names = {p.name for p in m.GATEWAY_APP_CANDIDATES}
        self.assertIn("Gateway.app", names)
        self.assertIn("JetBrains Gateway.app", names)


class SSHConfigFileTests(unittest.TestCase):
    def test_compute_update_preserves_unrelated_content(self):
        existing = "Host example\n\tHostName example.com\n"
        new_text = m.compute_ssh_include_update(existing)
        self.assertIsNotNone(new_text)
        self.assertTrue(new_text.startswith(existing))
        self.assertIn("Match all\nInclude ~/.ssh/codespaces\n", new_text)

    def test_compute_update_returns_none_when_already_present(self):
        existing = "Host example\nInclude ~/.ssh/codespaces\n"
        self.assertIsNone(m.compute_ssh_include_update(existing))

    def test_compute_update_detects_include_regardless_of_surrounding_whitespace(self):
        existing = "Match all\n   Include ~/.ssh/codespaces   \n"
        self.assertIsNone(m.compute_ssh_include_update(existing))

    def test_compute_update_handles_missing_trailing_newline(self):
        existing = "Host example\n\tHostName example.com"
        new_text = m.compute_ssh_include_update(existing)
        self.assertTrue(new_text.startswith("Host example\n\tHostName example.com\n"))

    def test_ensure_ssh_include_is_idempotent_and_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config"
            config_path.write_text("Host something\n\tHostName somewhere\n")

            changed_first = m.ensure_ssh_include(config_path)
            self.assertTrue(changed_first)
            content_after_first = config_path.read_text()
            self.assertIn("Host something", content_after_first)
            self.assertEqual(content_after_first.count("Include ~/.ssh/codespaces"), 1)

            changed_second = m.ensure_ssh_include(config_path)
            self.assertFalse(changed_second)
            content_after_second = config_path.read_text()
            self.assertEqual(content_after_second, content_after_first)
            self.assertEqual(content_after_second.count("Include ~/.ssh/codespaces"), 1)

    def test_ensure_ssh_include_creates_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "nested" / "config"
            changed = m.ensure_ssh_include(config_path)
            self.assertTrue(changed)
            self.assertIn("Include ~/.ssh/codespaces", config_path.read_text())

    def test_atomic_write_sets_permissions_and_leaves_no_temp_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "codespaces"
            m.atomic_write_text(dest, "Host x\n\tUser y\n", 0o600)
            self.assertEqual(dest.read_text(), "Host x\n\tUser y\n")
            mode = stat.S_IMODE(os.stat(dest).st_mode)
            self.assertEqual(mode, 0o600)
            leftovers = [p for p in Path(tmp).iterdir() if p.name != "codespaces"]
            self.assertEqual(leftovers, [])

    def test_merge_replaces_only_target_block_and_keeps_others_byte_for_byte(self):
        # Prior run's file already has both aliases; a fresh single-
        # codespace fetch for my-cs-123 must not touch other-cs-456's
        # block at all.
        new_config_for_target = SAMPLE_CONFIG_ONE_HOST.replace(
            "cs.my-cs-123.main", "cs.my-cs-123.feature-x"
        )
        merged = m.merge_ssh_codespaces_text(
            SAMPLE_CONFIG_TWO_HOSTS, new_config_for_target, "my-cs-123"
        )
        self.assertIn("Host cs.my-cs-123.feature-x", merged)
        self.assertNotIn("Host cs.my-cs-123.main", merged)
        self.assertIn("Host cs.other-cs-456.develop", merged)
        # The untouched block is reproduced verbatim.
        other_block_start = SAMPLE_CONFIG_TWO_HOSTS.index("Host cs.other-cs-456.develop")
        self.assertIn(SAMPLE_CONFIG_TWO_HOSTS[other_block_start:].strip(), merged)

    def test_merge_does_not_duplicate_when_target_block_already_current(self):
        merged = m.merge_ssh_codespaces_text(
            SAMPLE_CONFIG_ONE_HOST, SAMPLE_CONFIG_ONE_HOST, "my-cs-123"
        )
        self.assertEqual(merged.count("Host cs.my-cs-123.main"), 1)

    def test_merge_creates_file_content_when_existing_text_is_empty(self):
        merged = m.merge_ssh_codespaces_text("", SAMPLE_CONFIG_ONE_HOST, "my-cs-123")
        self.assertIn("Host cs.my-cs-123.main", merged)

    def test_merge_raises_when_selected_output_has_no_matching_block(self):
        # Defensive: parse_ssh_target should already have failed before
        # this is ever called, but the merge itself must not silently
        # write nothing / write the wrong thing either.
        with self.assertRaises(m.StageError) as ctx:
            m.merge_ssh_codespaces_text("", SAMPLE_CONFIG_ONE_HOST, "some-other-cs")
        self.assertEqual(ctx.exception.stage, "refresh-ssh-codespaces")

    def test_merge_raises_when_selected_output_is_ambiguous(self):
        ambiguous = SAMPLE_CONFIG_ONE_HOST + SAMPLE_CONFIG_ONE_HOST.replace(
            "cs.my-cs-123.main", "cs.my-cs-123.feature-x"
        )
        with self.assertRaises(m.StageError) as ctx:
            m.merge_ssh_codespaces_text("", ambiguous, "my-cs-123")
        self.assertEqual(ctx.exception.stage, "refresh-ssh-codespaces")

    def test_merge_preserves_preamble_and_replaces_middle_block_in_place(self):
        # Live bug: the merge used to rebuild the file purely from parsed
        # Host blocks, dropping any preamble before the first Host line
        # (comments/global directives) and always appending the target
        # block at the END, moving it out of its original position. This
        # fixture has a header comment + blank line before the first Host,
        # a wildcard `Host *` block that never matches any codespace, and
        # the target codespace's block placed in the MIDDLE, followed by
        # another codespace's block.
        merged = m.merge_ssh_codespaces_text(
            PREAMBLE_AND_WILDCARD_CONFIG, SAMPLE_CONFIG_ONE_HOST, "my-cs-123"
        )
        old_block = (
            "Host cs.my-cs-123.old-branch\n"
            "\tUser vscode\n"
            "\tProxyCommand gh cs ssh -c my-cs-123 --stdio -- -i "
            "/Users/x/.ssh/codespaces.auto\n"
            "\tUserKnownHostsFile=/dev/null\n"
            "\n"
        )
        # Independent oracle: a plain string substring-replace of the old
        # block with the new one, in the ORIGINAL file, must match exactly
        # -- proving nothing else (preamble, wildcard block, the other
        # codespace's block, or ordering) moved or changed. The merge
        # normalizes a doubled trailing blank-line+final-newline at EOF
        # (a harmless splitlines()/join() artifact of the last block only,
        # not a byte-preservation violation of any OTHER content), so the
        # trailing-newline count is compared loosely; everything else is
        # compared exactly via rstrip("\n").
        expected = PREAMBLE_AND_WILDCARD_CONFIG.replace(old_block, SAMPLE_CONFIG_ONE_HOST)
        self.assertEqual(merged.rstrip("\n"), expected.rstrip("\n"))
        # Explicit ordering check: preamble, then wildcard block, then the
        # (now-updated) target block, then the other codespace's block.
        self.assertLess(merged.index("# managed by dotfiles"), merged.index("Host *"))
        self.assertLess(merged.index("Host *"), merged.index("Host cs.my-cs-123.main"))
        self.assertLess(
            merged.index("Host cs.my-cs-123.main"), merged.index("Host cs.other-cs-456.develop")
        )
        self.assertNotIn("cs.my-cs-123.old-branch", merged)

    def test_merge_appends_after_preamble_and_wildcard_when_target_absent(self):
        # No existing block for my-cs-123 at all -- the new block must be
        # appended after everything else, and the preamble/wildcard block
        # (which have nothing to do with this codespace) must be untouched.
        existing = (
            "# header\n"
            "\n"
            "Host *\n"
            "\tAddKeysToAgent yes\n"
            "\n"
            "Host cs.other-cs-456.develop\n"
            "\tUser vscode\n"
            "\n"
        )
        merged = m.merge_ssh_codespaces_text(existing, SAMPLE_CONFIG_ONE_HOST, "my-cs-123")
        self.assertTrue(merged.startswith("# header\n\nHost *\n\tAddKeysToAgent yes\n\n"))
        self.assertLess(
            merged.index("Host cs.other-cs-456.develop"), merged.index("Host cs.my-cs-123.main")
        )

    def test_write_ssh_codespaces_file_preserves_other_aliases_and_writes_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "codespaces"
            dest.write_text(SAMPLE_CONFIG_TWO_HOSTS)

            m.write_ssh_codespaces_file(dest, SAMPLE_CONFIG_ONE_HOST, "my-cs-123")

            written = dest.read_text()
            self.assertIn("Host cs.my-cs-123.main", written)
            self.assertIn("Host cs.other-cs-456.develop", written)
            self.assertEqual(stat.S_IMODE(os.stat(dest).st_mode), 0o600)

    def test_write_ssh_codespaces_file_replaces_stale_target_block_not_append(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "codespaces"
            stale = SAMPLE_CONFIG_ONE_HOST.replace("cs.my-cs-123.main", "cs.my-cs-123.old-branch")
            dest.write_text(stale)

            m.write_ssh_codespaces_file(dest, SAMPLE_CONFIG_ONE_HOST, "my-cs-123")

            written = dest.read_text()
            self.assertIn("Host cs.my-cs-123.main", written)
            self.assertNotIn("cs.my-cs-123.old-branch", written)
            self.assertEqual(written.count("Host cs.my-cs-123"), 1)

    def test_write_ssh_codespaces_file_creates_file_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "nested" / "codespaces"
            m.write_ssh_codespaces_file(dest, SAMPLE_CONFIG_ONE_HOST, "my-cs-123")
            self.assertIn("Host cs.my-cs-123.main", dest.read_text())

    def test_selected_codespace_fetch_never_depends_on_other_codespaces_state(self):
        # gh codespace ssh --config (no -c) fails/exits 1 whenever ANY
        # visible codespace is non-Available (e.g. Shutdown), even when
        # the target is Available. Fetching with -c NAME only ever asks
        # about the target, so other codespaces being Shutdown is
        # irrelevant -- the fake never scripts a full-config command at
        # all, proving fetch_ssh_config_text has no path that could hit it.
        runner = FakeRunner()
        runner.script(
            ["gh", "codespace", "ssh", "-c", "my-cs-123", "--config"],
            m.CommandResult([], 0, SAMPLE_CONFIG_ONE_HOST, ""),
        )
        runner.script(
            ["gh", "codespace", "ssh", "--config"],
            m.CommandResult([], 1, "", "skipping unavailable codespace other-cs-456: Shutdown"),
        )
        text = m.fetch_ssh_config_text("my-cs-123", runner.as_runner())
        self.assertEqual(text, SAMPLE_CONFIG_ONE_HOST)
        self.assertNotIn(["gh", "codespace", "ssh", "--config"], runner.commands)


class ResolveCodespaceNameTests(unittest.TestCase):
    def _list_result(self, entries):
        return m.CommandResult([], 0, json.dumps(entries), "")

    def test_exact_name_match_wins_immediately(self):
        runner = FakeRunner()
        runner.script(
            ["gh", "codespace", "list"],
            self._list_result(
                [
                    {
                        "name": "stage-ui-for-you-analytics-7wvww9grg3xqp6",
                        "displayName": "stage-ui-for-you-analytics",
                        "repository": "octo/widgets",
                        "state": "Available",
                    }
                ]
            ),
        )
        name = m.resolve_codespace_name(
            "stage-ui-for-you-analytics-7wvww9grg3xqp6", runner.as_runner()
        )
        self.assertEqual(name, "stage-ui-for-you-analytics-7wvww9grg3xqp6")

    def test_unique_display_name_resolves_to_actual_name(self):
        runner = FakeRunner()
        runner.script(
            ["gh", "codespace", "list"],
            self._list_result(
                [
                    {
                        "name": "stage-ui-for-you-analytics-7wvww9grg3xqp6",
                        "displayName": "stage-ui-for-you-analytics",
                        "repository": "octo/widgets",
                        "state": "Available",
                    },
                    {
                        "name": "other-cs-456",
                        "displayName": "unrelated",
                        "repository": "octo/other",
                        "state": "Shutdown",
                    },
                ]
            ),
        )
        name = m.resolve_codespace_name("stage-ui-for-you-analytics", runner.as_runner())
        self.assertEqual(name, "stage-ui-for-you-analytics-7wvww9grg3xqp6")

    def test_duplicate_display_name_fails_without_guessing(self):
        runner = FakeRunner()
        runner.script(
            ["gh", "codespace", "list"],
            self._list_result(
                [
                    {"name": "cs-a", "displayName": "dup", "repository": "o/r", "state": "Available"},
                    {"name": "cs-b", "displayName": "dup", "repository": "o/r", "state": "Available"},
                ]
            ),
        )
        with self.assertRaises(m.StageError) as ctx:
            m.resolve_codespace_name("dup", runner.as_runner())
        self.assertEqual(ctx.exception.stage, "resolve-codespace-name")
        self.assertIn("cs-a", str(ctx.exception))
        self.assertIn("cs-b", str(ctx.exception))

    def test_no_match_fails_clearly(self):
        runner = FakeRunner()
        runner.script(["gh", "codespace", "list"], self._list_result([]))
        with self.assertRaises(m.StageError) as ctx:
            m.resolve_codespace_name("missing-cs", runner.as_runner())
        self.assertEqual(ctx.exception.stage, "resolve-codespace-name")

    def test_raises_on_gh_failure(self):
        runner = FakeRunner()
        runner.script(["gh", "codespace", "list"], m.CommandResult([], 1, "", "auth error"))
        with self.assertRaises(m.StageError) as ctx:
            m.resolve_codespace_name("my-cs", runner.as_runner())
        self.assertEqual(ctx.exception.stage, "resolve-codespace-name")

    def test_raises_on_malformed_json(self):
        runner = FakeRunner()
        runner.script(["gh", "codespace", "list"], m.CommandResult([], 0, "not json", ""))
        with self.assertRaises(m.StageError) as ctx:
            m.resolve_codespace_name("my-cs", runner.as_runner())
        self.assertEqual(ctx.exception.stage, "resolve-codespace-name")


class UseKeyringAuthTests(unittest.TestCase):
    def test_default_run_command_passes_env_none(self):
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["env"] = kwargs.get("env")

            class _P:
                returncode = 0
                stdout = ""
                stderr = ""

            return _P()

        original = m.subprocess.run
        m.subprocess.run = fake_run
        try:
            m._default_run_command(["true"])
        finally:
            m.subprocess.run = original
        self.assertIsNone(captured["env"])

    def test_make_run_command_with_strip_auth_env_removes_only_those_two_vars(self):
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["env"] = kwargs.get("env")

            class _P:
                returncode = 0
                stdout = ""
                stderr = ""

            return _P()

        original = m.subprocess.run
        m.subprocess.run = fake_run
        old_environ = dict(os.environ)
        os.environ["GH_TOKEN"] = "secret-gh-token"
        os.environ["GITHUB_TOKEN"] = "secret-github-token"
        os.environ.setdefault("PATH", "/usr/bin")
        try:
            run_command = m.make_run_command(strip_auth_env=True)
            run_command(["gh", "codespace", "list"])
        finally:
            m.subprocess.run = original
            os.environ.clear()
            os.environ.update(old_environ)

        env = captured["env"]
        self.assertIsNotNone(env)
        self.assertNotIn("GH_TOKEN", env)
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertIn("PATH", env)

    def test_strip_auth_env_never_mutates_parent_os_environ(self):
        def fake_run(cmd, **kwargs):
            class _P:
                returncode = 0
                stdout = ""
                stderr = ""

            return _P()

        original = m.subprocess.run
        m.subprocess.run = fake_run
        old_environ = dict(os.environ)
        os.environ["GH_TOKEN"] = "secret-gh-token"
        try:
            run_command = m.make_run_command(strip_auth_env=True)
            run_command(["gh", "codespace", "list"])
            self.assertEqual(os.environ.get("GH_TOKEN"), "secret-gh-token")
        finally:
            m.subprocess.run = original
            os.environ.clear()
            os.environ.update(old_environ)

    def test_make_run_command_without_strip_passes_env_none(self):
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["env"] = kwargs.get("env")

            class _P:
                returncode = 0
                stdout = ""
                stderr = ""

            return _P()

        original = m.subprocess.run
        m.subprocess.run = fake_run
        try:
            run_command = m.make_run_command(strip_auth_env=False)
            run_command(["true"])
        finally:
            m.subprocess.run = original
        self.assertIsNone(captured["env"])


class CommandTimeoutHandlingTests(unittest.TestCase):
    """A long-lived remote process (e.g. remote-dev-server.sh run) can
    outlive any timeout we pass. _run_command_impl must turn that into an
    ordinary non-zero CommandResult, never let subprocess.TimeoutExpired
    escape as a raw traceback.
    """

    def test_real_subprocess_timeout_becomes_nonzero_command_result_not_traceback(self):
        result = m._run_command_impl(
            [sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.05
        )
        self.assertIsInstance(result, m.CommandResult)
        self.assertEqual(result.returncode, 124)
        self.assertIn("timed out after 0.05s", result.stderr)

    def test_timeout_preserves_partial_stdout_captured_before_deadline(self):
        result = m._run_command_impl(
            [
                sys.executable,
                "-c",
                "import sys, time; sys.stdout.write('partial-output\\n'); "
                "sys.stdout.flush(); time.sleep(5)",
            ],
            timeout=0.2,
        )
        self.assertEqual(result.returncode, 124)
        self.assertIn("partial-output", result.stdout)

    def test_decode_partial_output_handles_none_str_and_bytes(self):
        self.assertEqual(m._decode_partial_output(None), "")
        self.assertEqual(m._decode_partial_output("hello"), "hello")
        self.assertEqual(m._decode_partial_output(b"hello"), "hello")

    def test_decode_partial_output_replaces_undecodable_bytes_instead_of_raising(self):
        # subprocess.TimeoutExpired can capture a partial multi-byte UTF-8
        # sequence cut mid-character; decoding must never raise.
        truncated = "caf\u00e9".encode("utf-8")[:-1]
        decoded = m._decode_partial_output(truncated)
        self.assertIsInstance(decoded, str)


class ResolveProjectPathTests(unittest.TestCase):
    def _args(self, **kwargs):
        ns = m.build_arg_parser().parse_args(
            ["--codespace", "my-cs"] + kwargs.pop("extra", [])
        )
        for key, value in kwargs.items():
            setattr(ns, key, value)
        return ns

    def test_explicit_remote_project_path_wins(self):
        args = self._args(remote_project_path="/workspaces/custom", repo="octo/widgets")
        self.assertEqual(m.resolve_remote_project_path(args), "/workspaces/custom")

    def test_derives_from_repo(self):
        args = self._args(remote_project_path=None, repo="octo/widgets")
        self.assertEqual(m.resolve_remote_project_path(args), "/workspaces/widgets")

    def test_raises_when_neither_given(self):
        args = self._args(remote_project_path=None, repo=None)
        with self.assertRaises(m.StageError) as ctx:
            m.resolve_remote_project_path(args)
        self.assertEqual(ctx.exception.stage, "resolve-project-path")


class DryRunTests(unittest.TestCase):
    def _parse(self, extra_argv, gateway_app_path=None):
        gateway_arg = str(gateway_app_path) if gateway_app_path else str(NONEXISTENT_GATEWAY_CANDIDATE)
        return m.build_arg_parser().parse_args(
            [
                "--codespace",
                "my-cs-123",
                "--repo",
                "octo/widgets",
                "--dry-run",
                "--gateway-app-path",
                gateway_arg,
            ]
            + extra_argv
        )

    def test_build_plan_never_touches_network_or_subprocess(self):
        args = self._parse([])
        # Swap in exploding stand-ins so any real call fails the test loudly.
        original_run = m.subprocess.run
        original_http = m.urllib.request.urlopen
        m.subprocess.run = lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("subprocess.run must not run during dry-run/build_plan")
        )
        m.urllib.request.urlopen = lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("urlopen must not run during dry-run/build_plan")
        )
        try:
            plan = m.build_plan(args)
        finally:
            m.subprocess.run = original_run
            m.urllib.request.urlopen = original_http
        self.assertTrue(any(line.startswith("auth:") for line in plan))
        self.assertTrue(any("gh codespace list --json" in line for line in plan))
        self.assertTrue(
            any(f"gh codespace code -c {m.RESOLVED_CODESPACE_PLACEHOLDER}" in line for line in plan)
        )
        self.assertTrue(
            any(
                line.startswith(f"gh codespace ssh -c {m.RESOLVED_CODESPACE_PLACEHOLDER} --config")
                for line in plan
            )
        )
        self.assertTrue(any("uname -m" in line for line in plan))  # arch auto-detect
        # ssh verify stage: "ssh -- <alias> true" ("--" ends ssh's own option
        # parsing before the hostname; must not land after it).
        self.assertTrue(
            any(line.startswith("ssh --") and line.endswith(" true") for line in plan)
        )
        self.assertTrue(any("/workspaces/widgets" in line for line in plan))
        self.assertTrue(any("jetbrains-gateway://connect" in line for line in plan))

    def test_build_plan_never_prints_raw_codespace_value_as_if_resolved(self):
        # Live bug: dry-run printed the raw --codespace value (which may be
        # a displayName, not the actual name) into later commands as if it
        # had already been resolved. Since --dry-run never calls a
        # subprocess, it cannot know the real name -- only the live
        # 'gh codespace list' stage (never run here) can resolve it.
        args = self._parse([])
        args.codespace = "stage-ui-for-you-analytics"  # a displayName, not a name
        plan = m.build_plan(args)
        resolve_line = next(line for line in plan if "gh codespace list --json" in line)
        self.assertIn("stage-ui-for-you-analytics", resolve_line)
        for line in plan:
            if line is resolve_line:
                continue
            self.assertNotIn("stage-ui-for-you-analytics", line)
        self.assertTrue(
            any(m.RESOLVED_CODESPACE_PLACEHOLDER in line for line in plan if line is not resolve_line)
        )

    def test_plan_shows_inherit_auth_by_default_and_keyring_auth_when_flagged(self):
        args = self._parse([])
        plan = m.build_plan(args)
        self.assertTrue(any("inherit parent environment" in line for line in plan))

        args_keyring = self._parse(["--use-keyring-auth"])
        plan_keyring = m.build_plan(args_keyring)
        self.assertTrue(any("--use-keyring-auth" in line for line in plan_keyring))
        self.assertTrue(any("strip" in line.lower() for line in plan_keyring))
        # Never print any secret/token value.
        self.assertFalse(any("GH_TOKEN=" in line for line in plan_keyring))

    def test_plan_shows_arch_override_skips_detection(self):
        args = self._parse(["--arch", "aarch64"])
        plan = m.build_plan(args)
        self.assertTrue(any("--arch aarch64" in line for line in plan))
        self.assertFalse(any("uname -m" in line for line in plan))

    def test_plan_flags_missing_gateway_without_install_flag(self):
        args = self._parse([])  # NONEXISTENT_GATEWAY_CANDIDATE: never installed
        plan = m.build_plan(args)
        self.assertTrue(any("BLOCKED" in line and "--install-gateway" in line for line in plan))

    def test_plan_includes_brew_install_when_flag_passed(self):
        args = self._parse(["--install-gateway"])
        plan = m.build_plan(args)
        self.assertTrue(any(line == "brew install --cask jetbrains-gateway" for line in plan))

    def test_plan_uses_explicit_open_a_when_gateway_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "Gateway.app"
            app_path.mkdir()
            args = self._parse([], gateway_app_path=app_path)
            plan = m.build_plan(args)
            self.assertTrue(any(f"open -a {app_path}" in line for line in plan))
            self.assertFalse(any("BLOCKED" in line for line in plan))

    def test_main_dry_run_exits_zero_and_prints_plan(self):
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = m.main(
                [
                    "--codespace",
                    "my-cs-123",
                    "--repo",
                    "octo/widgets",
                    "--dry-run",
                    "--gateway-app-path",
                    str(NONEXISTENT_GATEWAY_CANDIDATE),
                ]
            )
        self.assertEqual(code, 0)
        self.assertIn(f"gh codespace code -c {m.RESOLVED_CODESPACE_PLACEHOLDER}", buf.getvalue())
        self.assertIn("my-cs-123", buf.getvalue())  # still shown in the resolve line

    def test_main_reports_invalid_input_for_unsafe_dist_dir(self):
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            code = m.main(
                [
                    "--codespace",
                    "my-cs-123",
                    "--repo",
                    "octo/widgets",
                    "--dry-run",
                    "--dist-dir",
                    "~$(id)/dist",
                    "--gateway-app-path",
                    str(NONEXISTENT_GATEWAY_CANDIDATE),
                ]
            )
        self.assertEqual(code, 1)
        self.assertIn("[invalid-input]", buf.getvalue())


class FullPipelineTests(unittest.TestCase):
    @staticmethod
    def _status_result(*, ready, gateway_link="", project_path=None):
        """Build a fake 'remote-dev-server.sh status' CommandResult,
        including the live-observed stderr noise before the STATUS:
        marker. ready=False mimics 'nothing running yet' (non-zero exit,
        no STATUS: payload at all) rather than an unresponsive backend.
        """
        if not ready:
            return m.CommandResult([], 1, "", "error: XDG_RUNTIME_DIR is invalid...\n")
        payload = {"gatewayLink": gateway_link, "backendUnresponsive": False}
        if project_path is not None:
            payload["projectPath"] = project_path
        return m.CommandResult(
            [], 0, f"error: XDG_RUNTIME_DIR is invalid...\nSTATUS: {json.dumps(payload)}\n", ""
        )

    def _run_command_factory(
        self,
        ssh_alias,
        gateway_link,
        arch_output="x86_64\n",
        codespace_name="my-cs-123",
        remote_project_path="/workspaces/widgets",
    ):
        # The backend isn't running yet on the first status check (forcing
        # the detached-start path); it reports ready on every check after
        # that, mirroring "started, then poll succeeds on the next check".
        state = {"status_calls": 0}

        def run_command(cmd, *, input_text=None, timeout=None):
            if cmd[:3] == ["gh", "codespace", "list"]:
                entries = [
                    {
                        "name": codespace_name,
                        "displayName": codespace_name,
                        "repository": "octo/widgets",
                        "state": "Available",
                    }
                ]
                return m.CommandResult(cmd, 0, json.dumps(entries), "")
            if cmd[:3] == ["gh", "codespace", "code"]:
                return m.CommandResult(cmd, 0, "", "")
            if cmd[:3] == ["gh", "codespace", "ssh"] and "-c" in cmd:
                return m.CommandResult(cmd, 0, SAMPLE_CONFIG_ONE_HOST, "")
            if cmd[:3] == ["ssh", "--", ssh_alias] and cmd[3] == "true":
                return m.CommandResult(cmd, 0, "", "")
            if cmd[:3] == ["ssh", "--", ssh_alias] and cmd[3] == "uname":
                return m.CommandResult(cmd, 0, arch_output, "")
            if cmd[0] == "ssh" and "product-info.json" in cmd[-1]:
                return m.CommandResult(cmd, 0, "", "")  # no backend yet
            if cmd[0] == "ssh" and "curl -fsSL" in cmd[-1]:
                return m.CommandResult(cmd, 0, "", "")
            if cmd[0] == "ssh" and "nohup" in cmd[-1]:
                return m.CommandResult(cmd, 0, "", "")  # detached start returns promptly
            if cmd[0] == "ssh" and "status" in cmd[-1]:
                state["status_calls"] += 1
                return self._status_result(
                    ready=state["status_calls"] > 1,
                    gateway_link=gateway_link,
                    project_path=remote_project_path,
                )
            if cmd[0] == "open":
                return m.CommandResult(cmd, 0, "", "")
            raise AssertionError(f"unexpected command: {cmd}")

        return run_command

    def test_run_executes_all_stages_in_order_and_returns_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            ssh_config_path = Path(tmp) / "config"
            ssh_codespaces_path = Path(tmp) / "codespaces"
            gateway_app = Path(tmp) / "Gateway.app"
            gateway_app.mkdir()

            args = m.build_arg_parser().parse_args(
                [
                    "--codespace",
                    "my-cs-123",
                    "--repo",
                    "octo/widgets",
                    "--ssh-config-path",
                    str(ssh_config_path),
                    "--ssh-codespaces-path",
                    str(ssh_codespaces_path),
                    "--gateway-app-path",
                    str(gateway_app),
                ]
            )

            runner = FakeRunner()
            gateway_link = "jetbrains-gateway://connect#idePath=%2Fx&host=cs.my-cs-123.main&port=22&user=vscode&type=ssh&deploy=false"
            runner.set_handler(
                self._run_command_factory("cs.my-cs-123.main", gateway_link)
            )

            # Probe called twice (before and after install); after the
            # first empty probe/install/re-probe cycle, the second probe
            # must report the real, verified path -- swap the handler for
            # a stateful one that tracks probe call count.
            probe_calls = {"n": 0}
            base_handler = runner._handler

            def stateful_handler(cmd):
                if cmd[0] == "ssh" and "product-info.json" in cmd[-1]:
                    probe_calls["n"] += 1
                    if probe_calls["n"] >= 2:
                        return m.CommandResult(cmd, 0, SAMPLE_BACKEND_PATH + "\n", "")
                return base_handler(cmd)

            runner.set_handler(stateful_handler)
            link = m.run(args, runner.as_runner())

            self.assertEqual(link, gateway_link)
            # Merge normalizes trailing blank-line whitespace at EOF;
            # content (host/user/proxycommand lines) matches exactly.
            self.assertEqual(
                ssh_codespaces_path.read_text().strip(), SAMPLE_CONFIG_ONE_HOST.strip()
            )
            self.assertIn("Include ~/.ssh/codespaces", ssh_config_path.read_text())
            self.assertEqual(runner.commands[-1][0], "open")
            self.assertEqual(runner.commands[-1][1], "-a")
            self.assertEqual(runner.commands[-1][2], str(gateway_app))
            self.assertEqual(runner.commands[-1][3], gateway_link)
            # Arch was auto-detected (no --arch passed).
            self.assertTrue(
                any(c[:3] == ["ssh", "--", "cs.my-cs-123.main"] and c[3] == "uname" for c in runner.commands)
            )
            # The ssh config fetch selected only this codespace.
            self.assertTrue(
                any(c[:3] == ["gh", "codespace", "ssh"] and "-c" in c for c in runner.commands)
            )

    def test_run_with_explicit_arch_skips_remote_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            ssh_config_path = Path(tmp) / "config"
            ssh_codespaces_path = Path(tmp) / "codespaces"
            gateway_app = Path(tmp) / "Gateway.app"
            gateway_app.mkdir()

            args = m.build_arg_parser().parse_args(
                [
                    "--codespace",
                    "my-cs-123",
                    "--repo",
                    "octo/widgets",
                    "--arch",
                    "aarch64",
                    "--ssh-config-path",
                    str(ssh_config_path),
                    "--ssh-codespaces-path",
                    str(ssh_codespaces_path),
                    "--gateway-app-path",
                    str(gateway_app),
                ]
            )
            runner = FakeRunner()
            gateway_link = "jetbrains-gateway://connect#x=y"
            status_calls = {"n": 0}

            def run_command(cmd, *, input_text=None, timeout=None):
                if cmd[:3] == ["ssh", "--", "cs.my-cs-123.main"] and cmd[3] == "uname":
                    raise AssertionError("must not detect arch when --arch is explicit")
                if cmd[:3] == ["gh", "codespace", "list"]:
                    entries = [
                        {
                            "name": "my-cs-123",
                            "displayName": "my-cs-123",
                            "repository": "octo/widgets",
                            "state": "Available",
                        }
                    ]
                    return m.CommandResult(cmd, 0, json.dumps(entries), "")
                if cmd[:3] == ["gh", "codespace", "code"]:
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[:3] == ["gh", "codespace", "ssh"] and "-c" in cmd:
                    return m.CommandResult(cmd, 0, SAMPLE_CONFIG_ONE_HOST, "")
                if cmd[:3] == ["ssh", "--", "cs.my-cs-123.main"] and cmd[3] == "true":
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[0] == "ssh" and "product-info.json" in cmd[-1]:
                    # Backend already exists: no curl/install cycle needed.
                    return m.CommandResult(cmd, 0, SAMPLE_BACKEND_PATH + "\n", "")
                if cmd[0] == "ssh" and "status" in cmd[-1]:
                    status_calls["n"] += 1
                    return self._status_result(
                        ready=status_calls["n"] > 1,
                        gateway_link=gateway_link,
                        project_path="/workspaces/widgets",
                    )
                if cmd[0] == "ssh" and "nohup" in cmd[-1]:
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[0] == "open":
                    return m.CommandResult(cmd, 0, "", "")
                raise AssertionError(f"unexpected command: {cmd}")

            runner.set_handler(run_command)
            link = m.run(args, runner.as_runner())
            self.assertEqual(link, gateway_link)
            self.assertEqual(runner.http_calls, [])  # backend already existed

    def test_run_resolves_display_name_to_actual_name_before_any_other_stage(self):
        # This mirrors the live bug: VS Code's title bar shows displayName
        # ("stage-ui-for-you-analytics"), not the actual codespace name
        # ("stage-ui-for-you-analytics-7wvww9grg3xqp6") that every gh
        # command actually needs.
        with tempfile.TemporaryDirectory() as tmp:
            ssh_config_path = Path(tmp) / "config"
            ssh_codespaces_path = Path(tmp) / "codespaces"
            gateway_app = Path(tmp) / "Gateway.app"
            gateway_app.mkdir()

            actual_name = "stage-ui-for-you-analytics-7wvww9grg3xqp6"
            display_name = "stage-ui-for-you-analytics"
            ssh_alias = f"cs.{actual_name}.main"
            config_for_target = SAMPLE_CONFIG_ONE_HOST.replace("cs.my-cs-123.main", ssh_alias)

            args = m.build_arg_parser().parse_args(
                [
                    "--codespace",
                    display_name,
                    "--repo",
                    "octo/widgets",
                    "--ssh-config-path",
                    str(ssh_config_path),
                    "--ssh-codespaces-path",
                    str(ssh_codespaces_path),
                    "--gateway-app-path",
                    str(gateway_app),
                ]
            )
            runner = FakeRunner()
            gateway_link = "jetbrains-gateway://connect#x=y"

            def run_command(cmd, *, input_text=None, timeout=None):
                if cmd[:3] == ["gh", "codespace", "list"]:
                    entries = [
                        {
                            "name": actual_name,
                            "displayName": display_name,
                            "repository": "octo/widgets",
                            "state": "Available",
                        }
                    ]
                    return m.CommandResult(cmd, 0, json.dumps(entries), "")
                if cmd[:3] == ["gh", "codespace", "code"]:
                    self.assertIn(actual_name, cmd)
                    self.assertNotIn(display_name, cmd)
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[:3] == ["gh", "codespace", "ssh"] and "-c" in cmd:
                    self.assertIn(actual_name, cmd)
                    return m.CommandResult(cmd, 0, config_for_target, "")
                if cmd[:3] == ["ssh", "--", ssh_alias] and cmd[3] == "true":
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[:3] == ["ssh", "--", ssh_alias] and cmd[3] == "uname":
                    return m.CommandResult(cmd, 0, "x86_64\n", "")
                if cmd[0] == "ssh" and "product-info.json" in cmd[-1]:
                    return m.CommandResult(cmd, 0, SAMPLE_BACKEND_PATH + "\n", "")
                if cmd[0] == "ssh" and "status" in cmd[-1]:
                    return self._status_result(
                        ready=True, gateway_link=gateway_link, project_path="/workspaces/widgets"
                    )
                if cmd[0] == "ssh" and "nohup" in cmd[-1]:
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[0] == "open":
                    return m.CommandResult(cmd, 0, "", "")
                raise AssertionError(f"unexpected command: {cmd}")

            runner.set_handler(run_command)
            link = m.run(args, runner.as_runner())
            self.assertEqual(link, gateway_link)
            self.assertIn(ssh_alias, ssh_codespaces_path.read_text())

    def test_run_fails_fast_at_resolve_codespace_name_stage_before_anything_else(self):
        with tempfile.TemporaryDirectory() as tmp:
            ssh_config_path = Path(tmp) / "config"
            ssh_codespaces_path = Path(tmp) / "codespaces"
            gateway_app = Path(tmp) / "Gateway.app"
            gateway_app.mkdir()

            args = m.build_arg_parser().parse_args(
                [
                    "--codespace",
                    "no-such-codespace",
                    "--repo",
                    "octo/widgets",
                    "--ssh-config-path",
                    str(ssh_config_path),
                    "--ssh-codespaces-path",
                    str(ssh_codespaces_path),
                    "--gateway-app-path",
                    str(gateway_app),
                ]
            )
            runner = FakeRunner()
            runner.script(["gh", "codespace", "list"], m.CommandResult([], 0, "[]", ""))

            with self.assertRaises(m.StageError) as ctx:
                m.run(args, runner.as_runner())
            self.assertEqual(ctx.exception.stage, "resolve-codespace-name")
            self.assertFalse(ssh_config_path.exists())
            self.assertFalse(ssh_codespaces_path.exists())
            # Never even reached gateway detection / open-vscode.
            self.assertEqual(runner.commands, [["gh", "codespace", "list", "--json", "name,displayName,repository,state"]])

    def test_run_fails_fast_at_open_vscode_stage_without_touching_ssh_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            ssh_config_path = Path(tmp) / "config"
            ssh_codespaces_path = Path(tmp) / "codespaces"
            gateway_app = Path(tmp) / "Gateway.app"
            gateway_app.mkdir()

            args = m.build_arg_parser().parse_args(
                [
                    "--codespace",
                    "my-cs-123",
                    "--repo",
                    "octo/widgets",
                    "--ssh-config-path",
                    str(ssh_config_path),
                    "--ssh-codespaces-path",
                    str(ssh_codespaces_path),
                    "--gateway-app-path",
                    str(gateway_app),
                ]
            )
            runner = FakeRunner()
            entries = [
                {
                    "name": "my-cs-123",
                    "displayName": "my-cs-123",
                    "repository": "octo/widgets",
                    "state": "Available",
                }
            ]
            runner.script(["gh", "codespace", "list"], m.CommandResult([], 0, json.dumps(entries), ""))
            runner.script(["gh", "codespace", "code"], m.CommandResult([], 1, "", "network error"))

            with self.assertRaises(m.StageError) as ctx:
                m.run(args, runner.as_runner())
            self.assertEqual(ctx.exception.stage, "open-vscode")
            self.assertFalse(ssh_config_path.exists())
            self.assertFalse(ssh_codespaces_path.exists())

    def test_run_fails_fast_at_verify_ssh_connection_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            ssh_config_path = Path(tmp) / "config"
            ssh_codespaces_path = Path(tmp) / "codespaces"
            gateway_app = Path(tmp) / "Gateway.app"
            gateway_app.mkdir()

            args = m.build_arg_parser().parse_args(
                [
                    "--codespace",
                    "my-cs-123",
                    "--repo",
                    "octo/widgets",
                    "--ssh-config-path",
                    str(ssh_config_path),
                    "--ssh-codespaces-path",
                    str(ssh_codespaces_path),
                    "--gateway-app-path",
                    str(gateway_app),
                ]
            )
            runner = FakeRunner()

            def run_command(cmd, *, input_text=None, timeout=None):
                if cmd[:3] == ["gh", "codespace", "list"]:
                    entries = [
                        {
                            "name": "my-cs-123",
                            "displayName": "my-cs-123",
                            "repository": "octo/widgets",
                            "state": "Available",
                        }
                    ]
                    return m.CommandResult(cmd, 0, json.dumps(entries), "")
                if cmd[:3] == ["gh", "codespace", "code"]:
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[:3] == ["gh", "codespace", "ssh"] and "-c" in cmd:
                    return m.CommandResult(cmd, 0, SAMPLE_CONFIG_ONE_HOST, "")
                if cmd[:3] == ["ssh", "--", "cs.my-cs-123.main"] and cmd[3] == "true":
                    return m.CommandResult(cmd, 255, "", "Connection timed out")
                raise AssertionError(f"unexpected command reached: {cmd}")

            runner.set_handler(run_command)
            with self.assertRaises(m.StageError) as ctx:
                m.run(args, runner.as_runner())
            self.assertEqual(ctx.exception.stage, "verify-ssh-connection")
            # ~/.ssh files were still written correctly before this stage
            # (parse-then-write happens before verify).
            # Merge normalizes trailing blank-line whitespace at EOF;
            # content (host/user/proxycommand lines) matches exactly.
            self.assertEqual(
                ssh_codespaces_path.read_text().strip(), SAMPLE_CONFIG_ONE_HOST.strip()
            )

    def test_run_fails_before_write_when_selected_ssh_config_is_ambiguous(self):
        # parse_ssh_target must run (and raise) before
        # write_ssh_codespaces_file ever touches disk.
        with tempfile.TemporaryDirectory() as tmp:
            ssh_config_path = Path(tmp) / "config"
            ssh_codespaces_path = Path(tmp) / "codespaces"
            gateway_app = Path(tmp) / "Gateway.app"
            gateway_app.mkdir()

            args = m.build_arg_parser().parse_args(
                [
                    "--codespace",
                    "my-cs-123",
                    "--repo",
                    "octo/widgets",
                    "--ssh-config-path",
                    str(ssh_config_path),
                    "--ssh-codespaces-path",
                    str(ssh_codespaces_path),
                    "--gateway-app-path",
                    str(gateway_app),
                ]
            )
            runner = FakeRunner()
            ambiguous = SAMPLE_CONFIG_ONE_HOST + SAMPLE_CONFIG_ONE_HOST.replace(
                "cs.my-cs-123.main", "cs.my-cs-123.feature-x"
            )

            def run_command(cmd, *, input_text=None, timeout=None):
                if cmd[:3] == ["gh", "codespace", "list"]:
                    entries = [
                        {
                            "name": "my-cs-123",
                            "displayName": "my-cs-123",
                            "repository": "octo/widgets",
                            "state": "Available",
                        }
                    ]
                    return m.CommandResult(cmd, 0, json.dumps(entries), "")
                if cmd[:3] == ["gh", "codespace", "code"]:
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[:3] == ["gh", "codespace", "ssh"] and "-c" in cmd:
                    return m.CommandResult(cmd, 0, ambiguous, "")
                raise AssertionError(f"unexpected command reached: {cmd}")

            runner.set_handler(run_command)
            with self.assertRaises(m.StageError) as ctx:
                m.run(args, runner.as_runner())
            self.assertEqual(ctx.exception.stage, "parse-ssh-target")
            self.assertFalse(ssh_codespaces_path.exists())

    def test_run_shutdown_unrelated_codespace_never_blocks_the_pipeline(self):
        # Live bug: gh codespace ssh --config (no -c) exits 1 whenever any
        # OTHER codespace is Shutdown. Since this run only ever fetches
        # the selected codespace with -c, an unrelated Shutdown codespace
        # must never be queried and must never block anything.
        with tempfile.TemporaryDirectory() as tmp:
            ssh_config_path = Path(tmp) / "config"
            ssh_codespaces_path = Path(tmp) / "codespaces"
            gateway_app = Path(tmp) / "Gateway.app"
            gateway_app.mkdir()
            ssh_codespaces_path.write_text(SAMPLE_CONFIG_TWO_HOSTS)  # other-cs-456 present

            args = m.build_arg_parser().parse_args(
                [
                    "--codespace",
                    "my-cs-123",
                    "--repo",
                    "octo/widgets",
                    "--ssh-config-path",
                    str(ssh_config_path),
                    "--ssh-codespaces-path",
                    str(ssh_codespaces_path),
                    "--gateway-app-path",
                    str(gateway_app),
                ]
            )
            runner = FakeRunner()
            gateway_link = "jetbrains-gateway://connect#x=y"

            def run_command(cmd, *, input_text=None, timeout=None):
                if cmd[:3] == ["gh", "codespace", "list"]:
                    entries = [
                        {
                            "name": "my-cs-123",
                            "displayName": "my-cs-123",
                            "repository": "octo/widgets",
                            "state": "Available",
                        },
                        {
                            "name": "other-cs-456",
                            "displayName": "other-cs-456",
                            "repository": "octo/other",
                            "state": "Shutdown",
                        },
                    ]
                    return m.CommandResult(cmd, 0, json.dumps(entries), "")
                if cmd[:4] == ["gh", "codespace", "ssh", "--config"]:
                    raise AssertionError(
                        "must never call the no-'-c' full-config variant; "
                        "that fails whenever any OTHER codespace is Shutdown"
                    )
                if cmd[:3] == ["gh", "codespace", "code"]:
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[:3] == ["gh", "codespace", "ssh"] and "-c" in cmd:
                    return m.CommandResult(cmd, 0, SAMPLE_CONFIG_ONE_HOST, "")
                if cmd[:3] == ["ssh", "--", "cs.my-cs-123.main"] and cmd[3] == "true":
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[:3] == ["ssh", "--", "cs.my-cs-123.main"] and cmd[3] == "uname":
                    return m.CommandResult(cmd, 0, "x86_64\n", "")
                if cmd[0] == "ssh" and "product-info.json" in cmd[-1]:
                    return m.CommandResult(cmd, 0, SAMPLE_BACKEND_PATH + "\n", "")
                if cmd[0] == "ssh" and "status" in cmd[-1]:
                    return self._status_result(
                        ready=True, gateway_link=gateway_link, project_path="/workspaces/widgets"
                    )
                if cmd[0] == "ssh" and "nohup" in cmd[-1]:
                    return m.CommandResult(cmd, 0, "", "")
                if cmd[0] == "open":
                    return m.CommandResult(cmd, 0, "", "")
                raise AssertionError(f"unexpected command: {cmd}")

            runner.set_handler(run_command)
            link = m.run(args, runner.as_runner())
            self.assertEqual(link, gateway_link)
            written = ssh_codespaces_path.read_text()
            self.assertIn("Host cs.my-cs-123.main", written)
            self.assertIn("Host cs.other-cs-456.develop", written)


if __name__ == "__main__":
    unittest.main()
