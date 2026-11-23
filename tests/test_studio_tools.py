"""The tool catalog is valid and every action respects its rules: yes first, owner decisions, secrets in .env."""

import copy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import studio_tools as st  # noqa: E402

DECISION = "https://github.com/example/studio/issues/150#issuecomment-1"


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = st.load_catalog()

    def test_every_tool_is_complete(self):
        for tool in self.catalog["tools"]:
            with self.subTest(tool=tool["id"]):
                self.assertTrue(tool["source"].startswith("https://"))
                if tool["who"] != "claude_yes":
                    self.assertFalse({"all", "windows", "darwin", "linux"} & tool.get("install", {}).keys())
                if tool["cost"]["kind"] == "paid":
                    self.assertTrue(tool.get("account"))
                for skill in tool.get("used_by", []):
                    self.assertTrue((ROOT / "skills" / skill / "SKILL.md").is_file(), skill)

    def test_shell_syntax_and_bad_entries_are_refused(self):
        broken = copy.deepcopy(self.catalog)
        broken["tools"][0]["install"] = {"all": ["sh", "-c", "curl x | sh"]}
        with self.assertRaisesRegex(ValueError, "shell syntax"):
            st.validate_catalog(broken)
        broken = copy.deepcopy(self.catalog)
        tool = next(t for t in broken["tools"] if t["who"] == "person")
        tool["install"]["all"] = ["npm", "install", "-g", "x"]
        with self.assertRaisesRegex(ValueError, "only claude_yes"):
            st.validate_catalog(broken)
        broken = copy.deepcopy(self.catalog)
        broken["tools"][1]["id"] = broken["tools"][0]["id"]
        with self.assertRaisesRegex(ValueError, "unique"):
            st.validate_catalog(broken)

    def test_install_command_substitutes_tokens(self):
        tool = st.tool_by_id(self.catalog, "img2threejs")
        argv = st.install_command(tool, Path("/games/robot"), python="/py")
        self.assertEqual(st.install_steps(tool, Path("/games/robot"), python="/py"), [argv])
        self.assertEqual(argv[:5], ["git", "clone", "--depth", "1", "--branch"])
        self.assertEqual(Path(argv[-1]).parts[-2:], (".tools", "img2threejs"))
        pip = st.install_command(st.tool_by_id(self.catalog, "playwright"), Path("/g"), python="/py")
        self.assertEqual(pip[:4], ["/py", "-m", "pip", "install"])
        self.assertNotIn("{pip_user}", pip)
        self.assertIsNone(st.install_command(st.tool_by_id(self.catalog, "higgsfield"), Path("/g")))


class ActionTests(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory(prefix="game ")
        self.addCleanup(scratch.cleanup)
        self.game = Path(scratch.name)
        (self.game / ".gamedev-studio").write_text("", encoding="utf-8")
        self.catalog = st.load_catalog()

    def test_find_game_walks_up_to_the_marker(self):
        deep = self.game / "src" / "scenes"
        deep.mkdir(parents=True)
        self.assertEqual(st.find_game(deep), self.game.resolve())

    def test_install_needs_yes_and_never_runs_manual_tools(self):
        with self.assertRaisesRegex(st.ToolError, "explicit yes"):
            st.install(st.tool_by_id(self.catalog, "ffmpeg"), self.game, False)
        with self.assertRaisesRegex(st.ToolError, "person or the owner"):
            st.install(st.tool_by_id(self.catalog, "codex"), self.game, True)
        with self.assertRaisesRegex(st.ToolError, "waits for a decision"):
            st.install(st.tool_by_id(self.catalog, "godot-mcp"), self.game, True)

    def test_install_runs_the_exact_catalog_argv_without_a_shell(self):
        tool = st.tool_by_id(self.catalog, "img2threejs")
        process = mock.MagicMock()
        process.stdout = iter(["Cloning\n"])
        process.wait.return_value = 0
        with mock.patch.object(st.shutil, "which", return_value="/usr/bin/git"), \
                mock.patch.object(st.subprocess, "Popen", return_value=process) as popen:
            lines = []
            result = st.install(tool, self.game, True, on_line=lines.append)
        argv = popen.call_args.args[0]
        self.assertIsInstance(argv, list)
        self.assertNotIn("shell", popen.call_args.kwargs)
        expected = st.install_command(tool, self.game)
        self.assertEqual(argv[0], "/usr/bin/git")  # the program the name resolves to, never a shell
        self.assertEqual(argv[1:], expected[1:])
        self.assertEqual(result["gitignore_added"], [".tools/"])
        self.assertIn(".tools/", (self.game / ".gitignore").read_text(encoding="utf-8"))

    def test_owner_tool_needs_a_decision_link(self):
        with self.assertRaisesRegex(st.ToolError, "owner's decision"):
            st.set_enabled(self.catalog, self.game, "hindsight", True)
        entry = st.set_enabled(self.catalog, self.game, "hindsight", True, DECISION)
        self.assertEqual(entry, {"enabled": True, "decision": DECISION})
        with self.assertRaises(st.ToolError):
            st.set_enabled(self.catalog, self.game, "godot-mcp", True)

    def test_secret_goes_to_ignored_env_and_never_into_settings(self):
        (self.game / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
        result = st.set_secret(self.catalog, self.game, "fal", "FAL_KEY", "abc123")
        self.assertEqual(result, {"saved": True, "gitignore_added": [".env"]})
        st.set_secret(self.catalog, self.game, "fal", "FAL_KEY", "def456")
        self.assertEqual((self.game / ".env").read_text(encoding="utf-8"), "FAL_KEY=def456\n")
        self.assertIn(".env", (self.game / ".gitignore").read_text(encoding="utf-8").splitlines())
        rows = {row["id"]: row for row in st.status(self.catalog, self.game)}
        self.assertNotIn("def456", json.dumps(rows))
        self.assertTrue(rows["fal"]["config"][0]["set"])
        for bad in ("", "two\nlines"):
            with self.assertRaises(st.ToolError):
                st.set_secret(self.catalog, self.game, "fal", "FAL_KEY", bad)
        with self.assertRaises(st.ToolError):
            st.set_secret(self.catalog, self.game, "fal", "OTHER_KEY", "x")
        with self.assertRaises(st.ToolError):
            st.set_setting(self.catalog, self.game, "fal", "FAL_KEY", "x")

    def test_settings_validate_urls_and_paths(self):
        with self.assertRaises(st.ToolError):
            st.set_setting(self.catalog, self.game, "hindsight", "hindsight_url", "ftp://x")
        st.set_setting(self.catalog, self.game, "hindsight", "hindsight_url", "http://127.0.0.1:8888")
        self.assertEqual(st.load_settings(self.game)["settings"]["hindsight_url"], "http://127.0.0.1:8888")
        with self.assertRaises(st.ToolError):
            st.set_setting(self.catalog, self.game, "chromium", "chromium_path", str(self.game / "nope"))

    def test_git_checkout_detection_checks_the_commit(self):
        tool = st.tool_by_id(self.catalog, "img2threejs")
        git = self.game / ".tools" / "img2threejs" / ".git"
        git.mkdir(parents=True)
        (git / "HEAD").write_text("0" * 40 + "\n", encoding="utf-8")
        installed, detail = st.detect(tool, self.game, st.load_settings(self.game))
        self.assertFalse(installed)
        self.assertIn("another commit", detail)
        (git / "HEAD").write_text(tool["detect"]["commit"] + "\n", encoding="utf-8")
        self.assertTrue(st.detect(tool, self.game, st.load_settings(self.game))[0])


if __name__ == "__main__":
    unittest.main()


class LicenceGateTests(unittest.TestCase):
    """Non-commercial tools are installable, but their outputs are tracked and kept out of releases."""

    def setUp(self):
        scratch = TemporaryDirectory(prefix="game ")
        self.addCleanup(scratch.cleanup)
        self.game = Path(scratch.name) / "game"
        self.game.mkdir()
        (self.game / ".gamedev-studio").write_text("", encoding="utf-8")
        self.tools = Path(scratch.name) / "tools"
        patcher = mock.patch.dict("os.environ", {"GAMEDEV_STUDIO_TOOLS": str(self.tools)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.catalog = st.load_catalog()

    def test_motion_tools_are_pinned_installs_with_a_gate(self):
        for tid in ("prompt2rig", "motion2mixamorig"):
            with self.subTest(tool=tid):
                tool = st.tool_by_id(self.catalog, tid)
                self.assertEqual(tool["who"], "claude_yes")
                self.assertEqual(tool["commercial"], "non_commercial")
                self.assertTrue(tool["licence_gate"])
                steps = st.install_steps(tool, self.game, python="/py")
                self.assertEqual(steps[0][:2], ["git", "clone"])
                self.assertTrue(steps[0][-1].startswith(str(self.tools)))
                self.assertEqual(steps[1][-1], tool["detect"]["commit"])
        steps = st.install_steps(st.tool_by_id(self.catalog, "motion2mixamorig"), self.game, python="/py")
        self.assertEqual(steps[2], ["/py", "-m", "venv", str(self.tools / "Motion2MixamoRig" / ".venv")])
        self.assertTrue(all(step[0].startswith(str(self.tools)) for step in steps[3:]))

    def test_gate_only_on_non_commercial_tools(self):
        broken = copy.deepcopy(self.catalog)
        tool = next(t for t in broken["tools"] if t["id"] == "ffmpeg")
        tool["licence_gate"] = [{"ru": "x", "en": "x"}]
        with self.assertRaisesRegex(ValueError, "licence gate"):
            st.validate_catalog(broken)

    def fake_finished_m2mr(self):
        """What a finished Motion2MixamoRig install leaves: the pinned checkout and the m2mr program in its venv."""
        tool = st.tool_by_id(self.catalog, "motion2mixamorig")
        folder = self.tools / "Motion2MixamoRig"
        (folder / ".git").mkdir(parents=True)
        (folder / ".git" / "HEAD").write_text(tool["detect"]["commit"] + "\n", encoding="utf-8")
        program = folder / ".venv" / ("Scripts/m2mr.exe" if st.platform_key() == "windows" else "bin/m2mr")
        program.parent.mkdir(parents=True)
        program.write_bytes(b"")
        return program

    def test_virtualenv_programs_are_not_required_up_front(self):
        tool = st.tool_by_id(self.catalog, "motion2mixamorig")
        self.fake_finished_m2mr()
        process = mock.MagicMock()
        process.stdout = iter([])
        process.wait.return_value = 0
        with mock.patch.object(st.shutil, "which", return_value="/usr/bin/git"), \
                mock.patch.object(st, "check_prerequisite", return_value=(True, "ok")), \
                mock.patch.object(st.subprocess, "Popen", return_value=process) as popen:
            result = st.install(tool, self.game, True, python="/py")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(popen.call_count, len(result["steps"]) - 1)  # the folder is already a clone: no git clone
        for call in popen.call_args_list:
            self.assertIsInstance(call.args[0], list)
            self.assertNotIn("shell", call.kwargs)

    def test_copy_skills_keeps_existing_skills(self):
        source = self.tools / "pack" / "skills"
        for name in ("alpha", "beta"):
            (source / name).mkdir(parents=True)
            (source / name / "SKILL.md").write_text(name, encoding="utf-8")
        (source / "notes").mkdir()
        target = self.game / ".claude" / "skills"
        (target / "beta").mkdir(parents=True)
        (target / "beta" / "SKILL.md").write_text("mine", encoding="utf-8")
        lines = []
        self.assertEqual(st.copy_skills(source, target, lines.append), 0)
        self.assertEqual((target / "alpha" / "SKILL.md").read_text(encoding="utf-8"), "alpha")
        self.assertEqual((target / "beta" / "SKILL.md").read_text(encoding="utf-8"), "mine")
        self.assertFalse((target / "notes").exists())
        self.assertIn("kept existing beta", lines)

    def test_threejs_skills_install_without_npm(self):
        steps = st.install_steps(st.tool_by_id(self.catalog, "threejs-game-skills"), self.game)
        self.assertEqual(steps[-1], {"copy_skills": [str(self.tools / "threejs-game-skills" / "skills"),
                                                     str(self.game / ".claude" / "skills")]})
        self.assertFalse(any(isinstance(step, list) and step[0] == "npx" for step in steps))

    def test_mark_reference_and_licence(self):
        take = self.game / "anim" / "run.fbx"
        take.parent.mkdir()
        take.write_bytes(b"motion")
        self.assertEqual(st.mark_reference(self.catalog, self.game, "prompt2rig", [str(take)]), ["anim/run.fbx"])
        ledger = st.load_ledger(self.game)
        record = ledger["files"][st.file_hash(take)]
        self.assertEqual((record["path"], record["tool"]), ("anim/run.fbx", "prompt2rig"))
        with self.assertRaisesRegex(st.ToolError, "no commercial restriction"):
            st.mark_reference(self.catalog, self.game, "kimodo", [str(take)])
        with self.assertRaisesRegex(st.ToolError, "https link"):
            st.set_licence(self.catalog, self.game, "prompt2rig", "http://example.com")
        with self.assertRaisesRegex(st.ToolError, "needs no separate"):
            st.set_licence(self.catalog, self.game, "ffmpeg", "https://example.com")
        st.set_licence(self.catalog, self.game, "prompt2rig", DECISION)
        row = next(r for r in st.status(self.catalog, self.game, "en") if r["id"] == "prompt2rig")
        self.assertEqual(row["commercial_effective"], "licensed")
        with self.assertRaisesRegex(st.ToolError, "cleared for commercial use"):
            st.mark_reference(self.catalog, self.game, "prompt2rig", [str(take)])
        st.set_licence(self.catalog, self.game, "prompt2rig", "")
        row = next(r for r in st.status(self.catalog, self.game, "en") if r["id"] == "prompt2rig")
        self.assertEqual(row["commercial_effective"], "non_commercial")


    def test_owner_accepted_risk_stops_marking_and_releases_files(self):
        take = self.game / "run.fbx"
        take.write_bytes(b"motion")
        st.mark_reference(self.catalog, self.game, "prompt2rig", [str(take)])
        other = self.game / "pose.fbx"
        other.write_bytes(b"pose")
        st.mark_reference(self.catalog, self.game, "motion2mixamorig", [str(other)])
        result = st.accept_risk(self.catalog, self.game, "prompt2rig")
        self.assertEqual(result["released"], 1)
        self.assertEqual([item["tool"] for item in st.load_ledger(self.game)["files"].values()], ["motion2mixamorig"])
        row = next(r for r in st.status(self.catalog, self.game, "ru") if r["id"] == "prompt2rig")
        self.assertEqual(row["commercial_effective"], "owner_accepted")
        with self.assertRaisesRegex(st.ToolError, "cleared for commercial use"):
            st.mark_reference(self.catalog, self.game, "prompt2rig", [str(take)])
        with self.assertRaisesRegex(st.ToolError, "no commercial restriction"):
            st.accept_risk(self.catalog, self.game, "ffmpeg")
        st.accept_risk(self.catalog, self.game, "prompt2rig", False)
        row = next(r for r in st.status(self.catalog, self.game, "ru") if r["id"] == "prompt2rig")
        self.assertEqual(row["commercial_effective"], "non_commercial")


class PrerequisiteTests(unittest.TestCase):
    """Every tool says up front what it needs to be installed and to be used, and who installs each part."""

    def setUp(self):
        scratch = TemporaryDirectory(prefix="game ")
        self.addCleanup(scratch.cleanup)
        self.game = Path(scratch.name) / "game"
        self.game.mkdir()
        (self.game / ".gamedev-studio").write_text("", encoding="utf-8")
        self.tools = Path(scratch.name) / "tools"
        patcher = mock.patch.dict("os.environ", {"GAMEDEV_STUDIO_TOOLS": str(self.tools)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.catalog = st.load_catalog()

    def test_known_install_needs_are_declared(self):
        needs = {tool["id"]: tool.get("prerequisites", {}) for tool in self.catalog["tools"]}
        self.assertIn("msvc-build-tools", needs["motion2mixamorig"]["install"])
        self.assertIn("python-3-11", needs["motion2mixamorig"]["install"])
        self.assertEqual(needs["kimodo"]["use"], ["linux", "nvidia-gpu-17gb"])
        self.assertIn("node-18", needs["prompt2rig"]["use"])
        self.assertIn("mixar-app", needs["mixar-claude"]["use"])
        self.assertIn("blender-5-2", needs["blender-skills"]["use"])
        for tool in self.catalog["tools"]:
            steps = st.install_steps(tool, self.game, python="/py") or []
            programs = {step[0] for step in steps if isinstance(step, list)}
            with self.subTest(tool=tool["id"]):
                if "git" in programs:
                    self.assertIn("git", needs[tool["id"]].get("install", []))
                if "claude" in programs:
                    self.assertIn("claude-cli", needs[tool["id"]].get("install", []))
        msvc = st.prerequisite_by_id(self.catalog, "msvc-build-tools")
        self.assertEqual(msvc["platforms"], ["windows"])
        self.assertEqual(msvc["install"]["windows"][:2], ["winget", "install"])

    def test_bad_prerequisites_are_refused(self):
        broken = copy.deepcopy(self.catalog)
        next(t for t in broken["tools"] if t["id"] == "kimodo")["prerequisites"] = {"use": ["no-such-thing"]}
        with self.assertRaisesRegex(ValueError, "known prerequisite ids"):
            st.validate_catalog(broken)
        broken = copy.deepcopy(self.catalog)
        broken["tools"][0]["requires_programs"] = ["git"]
        with self.assertRaisesRegex(ValueError, "replaced by prerequisites"):
            st.validate_catalog(broken)
        broken = copy.deepcopy(self.catalog)
        st.prerequisite_by_id(broken, "git").pop("install")
        with self.assertRaisesRegex(ValueError, "needs install commands"):
            st.validate_catalog(broken)
        broken = copy.deepcopy(self.catalog)
        st.prerequisite_by_id(broken, "linux")["install"] = {"all": ["wsl", "--install"]}
        with self.assertRaisesRegex(ValueError, "only claude_yes prerequisites"):
            st.validate_catalog(broken)

    def test_missing_install_prerequisite_stops_before_any_command(self):
        tool = st.tool_by_id(self.catalog, "motion2mixamorig")

        def check(pre, *args, **kwargs):
            return (False, "missing") if pre["id"] == "msvc-build-tools" else (True, "ok")

        with mock.patch.object(st, "check_prerequisite", side_effect=check), \
                mock.patch.object(st.subprocess, "Popen") as popen:
            with self.assertRaises(st.PrerequisiteError) as raised:
                st.install(tool, self.game, True, python="/py", lang="ru")
        popen.assert_not_called()
        self.assertEqual([row["id"] for row in raised.exception.rows], ["msvc-build-tools"])
        self.assertIn("prereq msvc-build-tools --yes", str(raised.exception))
        self.assertIn("для установки", str(raised.exception))

    def test_person_prerequisites_only_show_instructions(self):
        with self.assertRaisesRegex(st.ToolError, "WSL2"):
            st.install_prerequisite(self.catalog, "linux", self.game, True, lang="en")
        with self.assertRaisesRegex(st.ToolError, "explicit yes"):
            st.install_prerequisite(self.catalog, "msvc-build-tools", self.game, False)

    def test_with_prerequisites_installs_claude_ones_first(self):
        tool = st.tool_by_id(self.catalog, "kimodo")
        state = {"git": False}

        def check(pre, *args, **kwargs):
            return (state.get(pre["id"], True), "x")

        def fake_prereq(catalog, pid, *args, **kwargs):
            state[pid] = True
            return {"returncode": 0, "argv": [], "steps": [], "gitignore_added": []}

        process = mock.MagicMock()
        process.stdout = iter([])
        process.wait.return_value = 0
        with mock.patch.object(st, "check_prerequisite", side_effect=check), \
                mock.patch.object(st, "install_prerequisite", side_effect=fake_prereq) as prereq, \
                mock.patch.object(st.shutil, "which", return_value="/usr/bin/git"), \
                mock.patch.object(st.subprocess, "Popen", return_value=process):
            result = st.install(tool, self.game, True, with_prerequisites=True)
        self.assertEqual(prereq.call_args.args[1], "git")
        self.assertEqual(result["returncode"], 0)

    def test_status_reports_needs_for_install_and_use(self):
        with mock.patch.object(st, "platform_key", return_value="windows"), \
                mock.patch.object(st, "nvidia_vram_gb", return_value=None):
            rows = {row["id"]: row for row in st.status(self.catalog, self.game, "en")}
        kimodo = {row["id"]: row for row in rows["kimodo"]["prerequisites"]}
        self.assertEqual((kimodo["linux"]["for"], kimodo["linux"]["met"], kimodo["linux"]["who"]), ("use", False, "person"))
        self.assertFalse(kimodo["nvidia-gpu-17gb"]["met"])
        self.assertFalse(rows["kimodo"]["ready_to_use"])
        mixar = rows["mixar-claude"]["prerequisites"]
        self.assertIsNone(next(row for row in mixar if row["id"] == "mixar-app")["met"])
        self.assertEqual(rows["ffmpeg"]["prerequisites"], [])

    def test_unfinished_install_is_not_reported_as_installed(self):
        tool = st.tool_by_id(self.catalog, "motion2mixamorig")
        program = LicenceGateTests.fake_finished_m2mr(self)
        self.assertTrue(st.detect(tool, self.game, st.load_settings(self.game))[0])
        program.unlink()
        installed, detail = st.detect(tool, self.game, st.load_settings(self.game))
        self.assertFalse(installed)
        self.assertIn("did not finish", detail)
        process = mock.MagicMock()
        process.stdout = iter([])
        process.wait.return_value = 0
        lines = []
        with mock.patch.object(st.shutil, "which", return_value="/usr/bin/git"), \
                mock.patch.object(st, "check_prerequisite", return_value=(True, "ok")), \
                mock.patch.object(st.subprocess, "Popen", return_value=process):
            result = st.install(tool, self.game, True, on_line=lines.append, python="/py")
        self.assertEqual(result["returncode"], 1)
        self.assertIn("did not finish", lines[-1])

    def test_programs_outside_path_are_found_in_known_folders(self):
        folder = self.tools / "Blender Foundation"
        for version in ("Blender 4.5", "Blender 5.3"):
            (folder / version).mkdir(parents=True)
            (folder / version / "blender.exe").write_bytes(b"")
        pattern = str(folder / "Blender *" / "blender.exe")
        self.assertEqual(st.known_program([pattern]), str(folder / "Blender 5.3" / "blender.exe"))
        self.assertIsNone(st.known_program([str(folder / "Nope *" / "x.exe"), "%NO_SUCH_VARIABLE_X%/a.exe"]))

    def test_extensionless_file_on_path_is_not_a_program_on_windows(self):
        found = {"winget": r"C:\Windows\System32\winget",
                 "winget.EXE": r"C:\Users\u\AppData\Local\Microsoft\WindowsApps\winget.EXE"}
        with mock.patch.object(st.sys, "platform", "win32"), \
                mock.patch.dict("os.environ", {"PATHEXT": ".COM;.EXE"}), \
                mock.patch.object(st.shutil, "which", side_effect=lambda name: found.get(name)):
            self.assertEqual(st.resolve_program("winget"), found["winget.EXE"])

    def test_versions_compare_by_parts(self):
        self.assertEqual(st.version_tuple("Blender 5.3.0\nbuild date"), (5, 3, 0))
        self.assertTrue(st.at_least((5, 3, 0), "5.2"))
        self.assertFalse(st.at_least((4, 2, 1), "5.2"))
        self.assertTrue(st.at_least((18, 0, 0), "18"))


class ConsoleTests(unittest.TestCase):
    """Piped output is UTF-8 on every system, so Claude's tools read ✓, → and Cyrillic (Windows used cp1252)."""

    def test_status_prints_through_a_pipe(self):
        import os
        import subprocess
        env = {key: value for key, value in os.environ.items() if key not in {"PYTHONIOENCODING", "PYTHONUTF8"}}
        with TemporaryDirectory() as game:
            for extra in ([], ["--json"]):
                result = subprocess.run([sys.executable, str(ROOT / "scripts" / "studio_tools.py"), "--game", game,
                                         "--lang", "ru", "status", *extra], capture_output=True, env=env, timeout=120)
                with self.subTest(args=extra):
                    self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
                    text = result.stdout.decode("utf-8")
                    self.assertIn("prerequisites" if extra else "не установлено", text)


class RetryTests(unittest.TestCase):
    def test_retry_after_a_failed_step_skips_the_existing_clone(self):
        with TemporaryDirectory() as scratch:
            target = Path(scratch) / "tool"
            (target / ".git").mkdir(parents=True)
            process = mock.MagicMock()
            process.stdout = iter([])
            process.wait.return_value = 0
            lines = []
            with mock.patch.object(st.subprocess, "Popen", return_value=process) as popen, \
                    mock.patch.object(st.shutil, "which", return_value="/usr/bin/git"):
                code = st._run_steps([["git", "clone", "https://example.com/x", str(target)],
                                      ["git", "-C", str(target), "checkout", "--detach", "a" * 40]], Path(scratch), lines.append)
            self.assertEqual(code, 0)
            self.assertEqual(popen.call_count, 1)
            self.assertIn("checkout", popen.call_args.args[0])
            self.assertIn("already cloned", lines[0])
