"""Unit tests for scripts/doctor.py: read-only by construction, every fix shown, bare-PC behaviour."""
import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "doctor.py"
_spec = importlib.util.spec_from_file_location("doctor", SCRIPT)
dr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dr)

PLUGIN_JSON = json.dumps([{"id": "other@x", "version": "1.0.0"}, {"id": dr.PLUGIN_ID, "version": "0.4.0"}])


class FakeTools:
    """Answers subprocess.run for the tools that 'exist'; records every argv."""

    def __init__(self, present=("claude", "git", "bash", "python", "gh", "codex"), answers=None):
        self.present, self.answers, self.calls = set(present), dict(answers or {}), []

    def which(self, name):
        return f"C:/fake/{name}.exe" if name in self.present else None

    def run(self, argv, **kwargs):
        name = Path(argv[0]).stem
        argv = [name, *argv[1:]]
        self.calls.append(argv)
        key = " ".join(argv[:3])
        defaults = {
            "claude --version": (0, "2.1.325 (Claude Code)"),
            "claude plugin list": (0, PLUGIN_JSON),
            "git --version": (0, "git version 2.56.0.windows.2"),
            "bash --version": (0, "GNU bash, version 5.2"),
            "gh --version": (0, "gh version 2.104.0"),
            "gh auth status": (0, "Logged in"),
            "gh repo view": (0, '{"name":"GameDev-AGI-Studio"}'),
            "gh issue list": (0, '[{"number":1}]'),
            "codex --version": (0, "codex-cli 0.169.0"),
        }
        code, out = self.answers.get(key, defaults.get(key, (0, "3.11.9" if name in ("python", "py", "python3") else "")))
        return subprocess.CompletedProcess(argv, code, stdout=out, stderr="")


class DoctorCase(unittest.TestCase):
    def check(self, tools, *args, bash_path="C:/Program Files/Git/bin/bash.exe"):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(dr.shutil, "which", side_effect=tools.which), \
                mock.patch.object(dr.subprocess, "run", side_effect=tools.run), \
                mock.patch.object(dr, "git_bash_path", return_value=Path(bash_path) if bash_path else None), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = dr.main(["--json", *args])
        return code, {r["key"]: r for r in json.loads(out.getvalue())}


class ReadOnlyTest(DoctorCase):
    def test_every_command_it_runs_is_a_read(self):
        for tools in (FakeTools(), FakeTools(present=())):
            self.check(tools, "--lang", "en")
            for argv in tools.calls:
                self.assertTrue(dr.allowed(argv), argv)
        for prefix in dr.ALLOWED_COMMANDS:
            self.assertFalse({"install", "add", "remove", "uninstall", "update", "upgrade", "login", "logout",
                              "delete", "config"} & set(prefix), prefix)

    def test_a_command_outside_the_allowlist_is_refused(self):
        for argv in (["winget", "install", "Git.Git"], ["claude", "plugin", "install", "x"], ["pip", "install", "x"],
                     ["gh", "auth", "login"], ["claude", "plugin", "marketplace", "add", "."], ["git", "config", "x"]):
            with self.subTest(argv=argv):
                with self.assertRaises(ValueError):
                    dr.run(argv)

    def test_the_script_writes_no_files(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for token in ("write_text", "write_bytes", "unlink", "rmtree", "mkdir", "os.remove", "os.rename", "Popen",
                      "os.system"):
            self.assertNotIn(token, source, token)
        self.assertIsNone(re.search(r"(?<![\w.])open\(", source))      # urlopen( is the one HTTP GET


class ResultTest(DoctorCase):
    def test_everything_present_passes(self):
        code, rows = self.check(FakeTools())
        self.assertEqual(code, 0)
        self.assertTrue(all(r["ok"] for r in rows.values()), rows)
        self.assertEqual(rows["plugin"]["detail"], "установлен, версия 0.4.0")

    def test_a_bare_pc_fails_every_required_check_with_a_fix(self):
        code, rows = self.check(FakeTools(present=()), "--lang", "en", bash_path=None)
        self.assertEqual(code, 1)
        for key in ("claude", "git", "git_bash", "python", "gh"):
            self.assertFalse(rows[key]["ok"], key)
            self.assertTrue(rows[key]["fix"], key)
        self.assertEqual(rows["claude"]["who"], "you")
        for key in ("git", "python", "gh"):
            self.assertEqual(rows[key]["who"], "claude")
            self.assertIn("winget install", rows[key]["fix"])
        for key, needs in (("gh_auth", "gh"), ("repo", "gh_auth"), ("decisions", "repo"), ("plugin", "claude")):
            self.assertTrue(rows[key]["skipped"], key)
            self.assertIn(rows[needs]["label"], rows[key]["detail"])

    def test_people_steps_are_marked_for_the_person(self):
        tools = FakeTools(answers={"gh auth status": (1, "not logged in")})
        _, rows = self.check(tools, "--lang", "en")
        self.assertEqual((rows["gh_auth"]["ok"], rows["gh_auth"]["who"]), (False, "you"))
        tools = FakeTools(answers={"gh repo view": (1, "HTTP 404")})
        _, rows = self.check(tools, "--lang", "en")
        self.assertEqual((rows["repo"]["ok"], rows["repo"]["who"]), (False, "you"))
        self.assertIn("ZMSkif", rows["repo"]["fix"])

    def test_no_decisions_visible_fails(self):
        _, rows = self.check(FakeTools(answers={"gh issue list": (0, "[]")}))
        self.assertFalse(rows["decisions"]["ok"])

    def test_python_store_alias_and_too_old(self):
        tools = FakeTools(present=("claude", "git", "gh", "python"), answers={})
        tools.which = lambda name: (r"C:\Users\x\AppData\Local\Microsoft\WindowsApps\python.exe" if name == "python"
                                    else FakeTools().which(name) if name in ("claude", "git", "gh") else None)
        original = tools.run

        def run(argv, **kw):
            if Path(argv[0]).stem == "python":
                return subprocess.CompletedProcess(argv, 9009, stdout="", stderr="")
            return original(argv, **kw)
        tools.run = run
        _, rows = self.check(tools, "--lang", "en")
        self.assertFalse(rows["python"]["ok"])
        self.assertIn("Microsoft Store", rows["python"]["detail"])
        old = FakeTools(answers={"python -c " + dr.PY_PROBE: (0, "3.8.10")})
        old_run = old.run
        old.run = lambda argv, **kw: (subprocess.CompletedProcess(argv, 0, stdout="3.8.10", stderr="")
                                      if Path(argv[0]).stem == "python" else old_run(argv, **kw))
        _, rows = self.check(old, "--lang", "en")
        self.assertFalse(rows["python"]["ok"])
        self.assertIn("3.8.10", rows["python"]["detail"])

    def test_claude_older_than_tested_passes_with_an_update_hint(self):
        _, rows = self.check(FakeTools(answers={"claude --version": (0, "2.0.1 (Claude Code)")}), "--lang", "en")
        self.assertTrue(rows["claude"]["ok"])
        self.assertIn("claude update", rows["claude"]["fix"])

    def test_plugin_missing_or_bad_json(self):
        for answer in ((0, "[]"), (0, "not json"), (1, "")):
            with self.subTest(answer=answer):
                _, rows = self.check(FakeTools(answers={"claude plugin list": answer}))
                self.assertFalse(rows["plugin"]["ok"])
                self.assertIn("claude plugin marketplace add", rows["plugin"]["fix"])

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
        self.assertEqual(urlopen.call_args[0][0], "http://127.0.0.1:9999/health")


class OutputTest(unittest.TestCase):
    def test_marks_fall_back_on_a_console_that_cannot_print_them(self):
        self.assertEqual(dr.marks_for(io.TextIOWrapper(io.BytesIO(), encoding="utf-8")), ("✅", "❌", "⏭"))
        self.assertEqual(dr.marks_for(io.TextIOWrapper(io.BytesIO(), encoding="cp1251")), ("[OK]", "[FAIL]", "[SKIP]"))

    def test_a_piped_cp1251_console_does_not_crash(self):
        env = {"PATH": os.path.dirname(sys.executable), "PYTHONIOENCODING": "cp1251",
               "SystemRoot": os.environ.get("SystemRoot", "")}
        for lang in ("ru", "en"):
            done = subprocess.run([sys.executable, str(SCRIPT), "--lang", lang], env=env, capture_output=True,
                                  timeout=120)
            self.assertIn(done.returncode, (0, 1), done.stderr.decode("cp1251", "replace"))
            self.assertNotIn(b"Traceback", done.stderr)
            self.assertIn(b"[FAIL]" if done.returncode else b"[OK]", done.stdout)

    def test_both_languages_have_the_same_keys(self):
        self.assertEqual(set(dr.TEXT["ru"]), set(dr.TEXT["en"]))
        for lang in dr.TEXT:
            for key, text in dr.TEXT[lang].items():
                self.assertEqual(set(re.findall(r"{(\w+)}", text)), set(re.findall(r"{(\w+)}", dr.TEXT["en"][key])),
                                 (lang, key))

    def test_bad_argument(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(dr.main(["--lang", "de"]), 2)


if __name__ == "__main__":
    unittest.main()
