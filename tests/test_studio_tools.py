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
