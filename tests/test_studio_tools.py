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
        self.assertTrue(argv[-1].endswith(".tools/img2threejs"))
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
        self.assertEqual(argv, st.install_command(tool, self.game))
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

    def test_virtualenv_programs_are_not_required_up_front(self):
        tool = st.tool_by_id(self.catalog, "motion2mixamorig")
        process = mock.MagicMock()
        process.stdout = iter([])
        process.wait.return_value = 0
        with mock.patch.object(st.shutil, "which", return_value="/usr/bin/git"), \
                mock.patch.object(st.subprocess, "Popen", return_value=process) as popen:
            result = st.install(tool, self.game, True, python="/py")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(popen.call_count, len(result["steps"]))
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
