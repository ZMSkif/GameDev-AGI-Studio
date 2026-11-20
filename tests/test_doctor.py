"""Unit tests for scripts/doctor.py: it installs and changes nothing, shows every fix, and reads Windows right."""
import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "doctor.py"
_spec = importlib.util.spec_from_file_location("doctor", SCRIPT)
dr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dr)


class FakeTools:
    """Stands in for shutil.which and subprocess.run; records every argv and env it was given."""

    def __init__(self, present=("claude", "git", "bash", "python", "gh", "codex"), answers=None):
        self.present, self.answers, self.calls, self.envs = set(present), dict(answers or {}), [], []

    def which(self, name):
        return f"C:/fake/{name}.exe" if name in self.present else None

    def run(self, argv, **kwargs):
        name = Path(argv[0]).stem.lower()
        argv = [name, *argv[1:]]
        self.calls.append(argv)
        self.envs.append(kwargs.get("env"))
        key = " ".join(argv[:3])
        defaults = {
            "claude --version": (0, "2.1.325 (Claude Code)"),
            "git --version": (0, "git version 2.56.0.windows.2"),
            "bash --version": (0, "GNU bash, version 5.2.37"),
            "gh --version": (0, "gh version 2.104.0"),
            "gh auth status": (0, "Logged in to github.com"),
            "gh repo view": (0, '{"name":"GameDev-AGI-Studio"}'),
            "gh issue list": (0, '[{"number":164}]'),
        }
        if name in ("python", "py", "python3"):
            code, out = self.answers.get(name, (0, "3.11.9"))
        else:
            code, out = self.answers.get(key, defaults.get(key, (127, "")))
        return subprocess.CompletedProcess(argv, code, stdout=out, stderr="")


class DoctorCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)
        self.config = self.home / ".claude"
        (self.config / "plugins").mkdir(parents=True)
        self.bash = self.home / "Git" / "bin" / "bash.exe"
        self.bash.parent.mkdir(parents=True)
        self.bash.write_text("", encoding="utf-8")
        self.plugin(installed="0.4.1", enabled=True)

    def plugin(self, installed=None, enabled=None, raw=None, install_path=None, marketplace=None):
        entry = {"scope": "user", "version": installed}
        if install_path:
            entry["installPath"] = str(install_path)
        plugins = {} if installed is None else {dr.PLUGIN_ID: [entry]}
        (self.config / "plugins" / "installed_plugins.json").write_text(
            raw if raw is not None else json.dumps({"version": 2, "plugins": plugins}), encoding="utf-8")
        settings = {} if enabled is None else {"enabledPlugins": {dr.PLUGIN_ID: enabled}}
        (self.config / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
        known = self.config / "plugins" / "known_marketplaces.json"
        if marketplace:
            known.write_text(json.dumps({dr.MARKETPLACE: {"source": {"source": "directory", "path": str(marketplace)},
                                                          "installLocation": str(marketplace)}}), encoding="utf-8")
        elif known.exists():
            known.unlink()

    def check(self, tools, *args, env=None):
        out = io.StringIO()
        environ = {"CLAUDE_CONFIG_DIR": str(self.config), **(env or {})}
        with mock.patch.object(dr.shutil, "which", side_effect=tools.which), \
                mock.patch.object(dr.subprocess, "run", side_effect=tools.run), \
                mock.patch.object(dr, "bash_candidates", return_value=[self.bash]), \
                mock.patch.object(dr, "folder_version", return_value="0.4.1"), \
                mock.patch.object(dr.Path, "home", return_value=self.home), \
                mock.patch.dict(os.environ, environ), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            if "CLAUDE_CODE_GIT_BASH_PATH" not in environ:
                os.environ.pop("CLAUDE_CODE_GIT_BASH_PATH", None)
            code = dr.main(["--json", *args])
        return code, {r["key"]: r for r in json.loads(out.getvalue())}


class ReadOnlyTest(DoctorCase):
    def test_every_command_it_starts_is_on_the_allowlist(self):
        for tools in (FakeTools(), FakeTools(present=())):
            self.check(tools, "--lang", "en", "--github")
            self.assertTrue(tools.calls or not tools.present)
            for argv in tools.calls:
                self.assertTrue(dr.allowed(argv), argv)
        for command in dr.ALLOWED_COMMANDS:
            self.assertFalse({"install", "add", "remove", "uninstall", "update", "upgrade", "login", "logout",
                              "delete", "config", "enable", "plugin", "edit", "close", "create"} & set(command),
                             command)

    def test_only_exact_commands_are_allowed(self):
        refused = (["winget", "install", "Git.Git"], ["claude", "plugin", "install", "x"], ["pip", "install", "x"],
                   ["gh", "auth", "login"], ["claude", "plugin", "list"], ["codex", "--version"],
                   ["git", "config", "x"], ["C:/x/claude.exe", "plugin", "marketplace", "add", "."],
                   ["python", "-c", "import shutil; shutil.copy('a', 'b')"],
                   ["python", "-c", dr.PY_PROBE, "extra"], ["claude", "--version", "plugin"],
                   ["gh", "issue", "list", "-R", dr.REPO, "--limit", "1", "--json", "number"],
                   ["gh", "repo", "view", "a/b; rm -rf x", "--json", "name"], ["gh", "repo", "delete", dr.REPO], [])
        for argv in refused:
            with self.subTest(argv=argv):
                self.assertFalse(dr.allowed(argv))
                with self.assertRaises(ValueError):
                    dr.run(argv)
        self.assertTrue(dr.allowed([r"C:\Program Files\Git\bin\bash.exe", "--version"]))
        self.assertTrue(dr.allowed(["gh", "repo", "view", "someone/other-repo", "--json", "name"]))

    def test_run_passes_no_input_a_timeout_and_the_safe_environment(self):
        with mock.patch.object(dr.shutil, "which", return_value="C:/fake/git.exe"), \
                mock.patch.object(dr.subprocess, "run",
                                  return_value=subprocess.CompletedProcess([], 0, "git version 2", "")) as run:
            self.assertEqual(dr.run(["git", "--version"]), (0, "git version 2"))
        kwargs = run.call_args.kwargs
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertTrue(kwargs["capture_output"])
        self.assertEqual(kwargs["timeout"], 60.0)
        self.assertEqual(kwargs["env"]["PYTHON_MANAGER_AUTOMATIC_INSTALL"], "false")
        with mock.patch.object(dr.shutil, "which", return_value="C:/fake/gh.exe"), \
                mock.patch.object(dr.subprocess, "run", side_effect=subprocess.TimeoutExpired("gh", 60)):
            self.assertEqual(dr.run(["gh", "auth", "status"])[0], 124)
        with mock.patch.object(dr.shutil, "which", return_value=None):
            self.assertEqual(dr.run(["gh", "--version"]), (127, ""))

    def test_codex_and_the_plugin_list_are_never_started(self):
        tools = FakeTools()
        self.check(tools, "--github")
        self.assertNotIn("codex", [c[0] for c in tools.calls])
        self.assertNotIn(["claude", "plugin", "list"], [c[:3] for c in tools.calls])

    def test_without_github_flag_no_gh_command_runs(self):
        tools = FakeTools()
        code, rows = self.check(tools)
        self.assertEqual(code, 0, rows)
        self.assertNotIn("gh", [c[0] for c in tools.calls])
        self.assertFalse({"gh", "gh_auth", "repo", "decisions"} & set(rows))

    def test_python_probes_cannot_trigger_an_automatic_install(self):
        tools = FakeTools()
        with mock.patch.dict(os.environ, {"PYLAUNCHER_ALLOW_INSTALL": "1", "PYLAUNCHER_ALWAYS_INSTALL": "1"}):
            self.check(tools)
        envs = [e for c, e in zip(tools.calls, tools.envs) if c[0] in ("python", "py", "python3")]
        self.assertTrue(envs)
        for env in envs:
            self.assertEqual(env["PYTHON_MANAGER_AUTOMATIC_INSTALL"], "false")
            self.assertFalse([k for k in env if k.upper().startswith("PYLAUNCHER_")])

    def test_the_script_writes_no_files(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for token in ("write_text", "write_bytes", "unlink", "rmtree", "mkdir", "os.remove", "os.rename", "Popen",
                      "os.system", "Request("):
            self.assertNotIn(token, source, token)
        self.assertIsNone(re.search(r"(?<![\w.])open\(", source))      # urlopen( is the one HTTP GET


class ResultTest(DoctorCase):
    def test_everything_present_passes(self):
        code, rows = self.check(FakeTools(), "--github")
        self.assertEqual(code, 0, rows)
        self.assertTrue(all(r["ok"] for r in rows.values()), rows)
        self.assertEqual(rows["plugin"]["detail"], "установлен и включён, версия 0.4.1")

    def test_the_repository_named_is_the_one_checked(self):
        tools = FakeTools()
        self.check(tools, "--github", "--repo", "someone/other-repo")
        gh_calls = [c for c in tools.calls if c[0] == "gh" and c[1] in ("repo", "issue")]
        self.assertEqual(len(gh_calls), 2)
        for call in gh_calls:
            self.assertIn("someone/other-repo", call)
        self.assertIn("decision", gh_calls[1])
        self.assertEqual(dr.main(["--repo", "not a repo"]), 2)

    def test_a_bare_pc_fails_every_required_check_with_a_fix(self):
        self.plugin(installed=None)
        self.bash.unlink()
        code, rows = self.check(FakeTools(present=()), "--lang", "en", "--github")
        self.assertEqual(code, 1)
        for key in ("claude", "git", "git_bash", "python", "gh"):
            self.assertFalse(rows[key]["ok"], key)
            self.assertTrue(rows[key]["fix"], key)
        self.assertEqual(rows["claude"]["who"], "you")
        for key in ("git", "python", "gh"):
            self.assertEqual(rows[key]["who"], "claude_yes")
            self.assertIn("winget install", rows[key]["fix"])
            self.assertIn("--accept-package-agreements", rows[key]["fix"])
            self.assertIn(f'cd "{dr.PLUGIN_ROOT}"', rows[key]["fix"])
            self.assertIn("claude --continue", rows[key]["fix"])
        for key, needs in (("gh_auth", "gh"), ("repo", "gh_auth"), ("decisions", "repo"), ("plugin", "claude")):
            self.assertTrue(rows[key]["skipped"], key)
            self.assertIn(rows[needs]["label"], rows[key]["detail"])

    def test_the_text_report_shows_each_fix_and_who_does_it(self):
        self.plugin(installed=None)
        out = io.StringIO()
        tools = FakeTools(present=("claude", "python"))
        with mock.patch.object(dr.shutil, "which", side_effect=tools.which), \
                mock.patch.object(dr.subprocess, "run", side_effect=tools.run), \
                mock.patch.object(dr, "bash_candidates", return_value=[]), \
                mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.config)}), \
                contextlib.redirect_stdout(out):
            os.environ.pop("CLAUDE_CODE_GIT_BASH_PATH", None)
            code = dr.main(["--lang", "en"])
        text = out.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("Git (required): not found", text)
        self.assertIn("Fix [Claude, after your yes; Windows may ask you to approve]: Install Git for Windows", text)
        self.assertIn("Fix [Claude can do it]: Install the plugin from this folder", text)
        self.assertIn("required item(s) missing", text)

    def test_claude_installed_but_not_on_path(self):
        local = self.home / ".local" / "bin"
        local.mkdir(parents=True)
        (local / ("claude.exe" if os.name == "nt" else "claude")).write_text("", encoding="utf-8")
        _, rows = self.check(FakeTools(present=("git", "python")), "--lang", "en")
        self.assertFalse(rows["claude"]["ok"])
        self.assertIn("not on PATH", rows["claude"]["detail"])
        self.assertIn(str(local), rows["claude"]["fix"])

    def test_claude_older_than_tested_passes_with_an_update_hint(self):
        _, rows = self.check(FakeTools(answers={"claude --version": (0, "2.0.1 (Claude Code)")}), "--lang", "en")
        self.assertTrue(rows["claude"]["ok"])
        self.assertIn("winget upgrade Anthropic.ClaudeCode", rows["claude"]["fix"])

    @unittest.skipUnless(os.name == "nt", "Git Bash is looked up this way on Windows only")
    def test_git_bash_must_run_and_a_bad_override_is_reported(self):
        _, rows = self.check(FakeTools())
        self.assertTrue(rows["git_bash"]["ok"])
        _, rows = self.check(FakeTools(answers={"bash --version": (1, "")}))
        self.assertFalse(rows["git_bash"]["ok"])                       # the file exists but does not run
        readme = REPO_ROOT / "README.md"
        _, rows = self.check(FakeTools(), "--lang", "en", env={"CLAUDE_CODE_GIT_BASH_PATH": str(readme)})
        self.assertFalse(rows["git_bash"]["ok"])                       # never papered over by a found bash
        self.assertIn("CLAUDE_CODE_GIT_BASH_PATH", rows["git_bash"]["detail"])
        self.assertEqual(rows["git_bash"]["who"], "you")

    def test_git_bash_is_looked_for_next_to_git(self):
        git = self.home / "Tools" / "Git" / "cmd" / "git.exe"
        with mock.patch.object(dr.shutil, "which", return_value=str(git)), mock.patch.dict(os.environ, {}, clear=True):
            found = dr.bash_candidates()
        self.assertEqual(found[:2], [git.resolve().parent.parent / "bin" / "bash.exe",
                                     git.resolve().parent.parent / "usr" / "bin" / "bash.exe"])

    def test_python_fallback_store_alias_and_too_old(self):
        _, rows = self.check(FakeTools(present=("claude", "git", "python", "py"),
                                       answers={"python": (0, "3.7.9"), "py": (0, "3.13.1")}))
        self.assertTrue(rows["python"]["ok"])
        self.assertIn("py 3.13.1", rows["python"]["detail"])
        tools = FakeTools(answers={"python": (9009, ""), "py": (127, ""), "python3": (9009, "")})
        tools.which = lambda name: (r"C:\Users\x\AppData\Local\Microsoft\WindowsApps\python.exe"
                                    if name == "python" else FakeTools().which(name) if name != "py" else None)
        _, rows = self.check(tools, "--lang", "en")
        self.assertFalse(rows["python"]["ok"])
        self.assertIn("Microsoft Store", rows["python"]["detail"])
        _, rows = self.check(FakeTools(answers={"python": (0, "3.8.10"), "py": (127, ""), "python3": (127, "")}),
                             "--lang", "en")
        self.assertFalse(rows["python"]["ok"])
        self.assertIn("3.8.10", rows["python"]["detail"])

    def test_gh_failures_say_whether_access_or_the_network_is_the_problem(self):
        _, rows = self.check(FakeTools(answers={"gh auth status": (1, "You are not logged into any GitHub hosts. "
                                                                       "Run gh auth login")}), "--lang", "en",
                             "--github")
        self.assertEqual((rows["gh_auth"]["ok"], rows["gh_auth"]["who"]), (False, "you"))
        self.assertIn("gh auth login", rows["gh_auth"]["fix"])
        _, rows = self.check(FakeTools(answers={"gh repo view": (1, "GraphQL: Could not resolve to a Repository")}),
                             "--lang", "en", "--github")
        self.assertEqual(rows["repo"]["detail"], "no access")
        self.assertIn("only the owner", rows["repo"]["fix"])
        for key, answer in (("gh auth status", (1, "error connecting to api.github.com: dial tcp: i/o timeout")),
                            ("gh repo view", (1, "error connecting to api.github.com")),
                            ("gh issue list", (124, "timed out"))):
            with self.subTest(key=key):
                _, rows = self.check(FakeTools(answers={key: answer}), "--lang", "en", "--github")
                row = {"gh auth status": "gh_auth", "gh repo view": "repo", "gh issue list": "decisions"}[key]
                self.assertIn("could not check", rows[row]["detail"])
                self.assertIn("internet", rows[row]["fix"])

    def test_decisions_need_a_real_json_list(self):
        for answer in ((0, "[]"), (0, "[]\n"), (0, "[garbage"), (0, "{}"), (0, '[{"title":"x"}]')):
            with self.subTest(answer=answer):
                _, rows = self.check(FakeTools(answers={"gh issue list": answer}), "--github")
                self.assertFalse(rows["decisions"]["ok"])

    def test_plugin_missing_disabled_elsewhere_or_unreadable(self):
        cases = ((dict(installed=None), "not installed", "claude plugin marketplace add"),
                 (dict(installed="0.4.1", enabled=False), "installed but disabled", "claude plugin enable"),
                 (dict(installed="0.4.1", enabled=None), "installed but disabled", "claude plugin enable"),
                 (dict(installed="0.1.0", enabled=True, install_path=self.home / "old"),
                  "installed from another place", "Updating"),
                 (dict(raw="not json"), "could not read the plugin list", "claude plugin list"))
        for kwargs, detail, fix in cases:
            with self.subTest(kwargs=kwargs):
                self.plugin(**kwargs)
                _, rows = self.check(FakeTools(), "--lang", "en")
                self.assertFalse(rows["plugin"]["ok"])
                self.assertIn(detail, rows["plugin"]["detail"])
                self.assertIn(fix, rows["plugin"]["fix"])
        (self.config / "plugins" / "installed_plugins.json").unlink()
        _, rows = self.check(FakeTools(), "--lang", "en")
        self.assertEqual(rows["plugin"]["detail"], "not installed")

    def test_a_plugin_loaded_in_place_from_this_folder_passes_whatever_version_was_recorded(self):
        for kwargs in (dict(install_path=dr.PLUGIN_ROOT), dict(marketplace=dr.PLUGIN_ROOT)):
            with self.subTest(kwargs=kwargs):
                self.plugin(installed="0.4.0", enabled=True, **kwargs)
                _, rows = self.check(FakeTools(), "--lang", "en")
                self.assertTrue(rows["plugin"]["ok"], rows["plugin"])
                self.assertEqual(rows["plugin"]["detail"], "installed from this folder and enabled, version 0.4.1")

    def test_hindsight_is_optional_and_only_read(self):
        with mock.patch.object(dr.urllib.request, "urlopen", side_effect=dr.urllib.error.URLError("refused")):
            code, rows = self.check(FakeTools(), "--hindsight")
        self.assertEqual(code, 0)
        self.assertFalse(rows["hindsight"]["ok"])
        self.assertFalse(rows["hindsight"]["required"])

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b'{"status":"healthy","database":"connected"}'
        with mock.patch.object(dr.urllib.request, "urlopen", return_value=Resp()) as urlopen:
            _, rows = self.check(FakeTools(), "--hindsight", "http://127.0.0.1:9999")
        self.assertTrue(rows["hindsight"]["ok"])
        self.assertEqual(urlopen.call_args.args, ("http://127.0.0.1:9999/health",))   # a plain GET, no body
        self.assertNotIn("data", urlopen.call_args.kwargs)


class OutputTest(unittest.TestCase):
    def run_doctor(self, *args, encoding=None):
        keep = ("SystemRoot", "SystemDrive", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "HOME")
        env = {k: os.environ[k] for k in keep if k in os.environ}
        env["PATH"] = os.path.dirname(sys.executable)
        if encoding:
            env["PYTHONIOENCODING"] = encoding
        with tempfile.TemporaryDirectory() as cwd:          # nothing a child might create lands in the repository
            return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, cwd=cwd, capture_output=True,
                                  timeout=120)

    def test_marks_fall_back_on_a_console_that_cannot_print_them(self):
        self.assertEqual(dr.marks_for(io.TextIOWrapper(io.BytesIO(), encoding="utf-8")), ("✅", "❌", "⏭"))
        self.assertEqual(dr.marks_for(io.TextIOWrapper(io.BytesIO(), encoding="cp1251")), ("[OK]", "[FAIL]", "[SKIP]"))

    def test_a_pipe_gets_readable_utf8(self):
        done = self.run_doctor("--lang", "ru")
        self.assertIn(done.returncode, (0, 1), done.stderr.decode("utf-8", "replace"))
        text = done.stdout.decode("utf-8")                   # strict: a cp1251 byte here would raise
        self.assertIn("проверка компьютера", text)
        self.assertIn("❌" if done.returncode else "✅", text)

    def test_a_console_encoding_that_cannot_print_does_not_crash(self):
        for encoding, lang in (("cp1251", "ru"), ("cp1251", "en"), ("ascii", "ru")):
            with self.subTest(encoding=encoding, lang=lang):
                done = self.run_doctor("--lang", lang, encoding=encoding)
                self.assertIn(done.returncode, (0, 1), done.stderr.decode(encoding, "replace"))
                self.assertNotIn(b"Traceback", done.stderr)
                self.assertIn(b"[FAIL]" if done.returncode else b"[OK]", done.stdout)

    def test_both_languages_have_the_same_keys_and_fields(self):
        self.assertEqual(set(dr.TEXT["ru"]), set(dr.TEXT["en"]))
        for key, text in dr.TEXT["ru"].items():
            self.assertEqual(set(re.findall(r"{(\w+)}", text)), set(re.findall(r"{(\w+)}", dr.TEXT["en"][key])), key)

    def test_bad_argument(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(dr.main(["--lang", "de"]), 2)


if __name__ == "__main__":
    unittest.main()
