"""The studio memory: its own local Hindsight server per person, and the always-connected MCP in front of it."""

import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import memory_server as ms  # noqa: E402
import memory_mcp as mm  # noqa: E402

POLICY = json.loads((ROOT / "contracts" / "v1" / "knowledge-policy.json").read_text(encoding="utf-8"))["memory_backend"]


class ServerTests(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.home = Path(scratch.name)
        patcher = mock.patch.dict("os.environ", {"GAMEDEV_STUDIO_HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_tools_and_binding_follow_the_contract(self):
        self.assertEqual(ms.MCP_TOOLS, POLICY["mcp_enabled_tools"])
        self.assertEqual(ms.HOST, "127.0.0.1")
        env = ms.server_environment()
        self.assertEqual(env["HINDSIGHT_API_HOST"], "127.0.0.1")
        self.assertEqual(env["HINDSIGHT_API_LLM_PROVIDER"], "claude-code")  # the person's subscription, no paid API
        self.assertEqual(env["HINDSIGHT_API_MCP_ENABLED_TOOLS"].split(","), POLICY["mcp_enabled_tools"])
        self.assertNotIn("HINDSIGHT_API_DATABASE_URL", env)  # the default pg0 instance, where memory already is
        self.assertEqual(ms.server_argv(Path("/r"))[1:], ["--host", "127.0.0.1", "--port", "8888"])
        self.assertEqual(ms.STUDIO_BANK, POLICY["bank_naming"]["studio"])
        self.assertEqual(ms.PROJECT_BANK, POLICY["bank_naming"]["project"])

    def test_no_command_deletes_memory(self):
        parser_text = (ROOT / "scripts" / "memory_server.py").read_text(encoding="utf-8").lower()
        for word in ("delete", "clear", "reset", "drop"):
            self.assertNotIn(f'add_parser("{word}', parser_text)
        self.assertNotIn("DELETE", (ROOT / "scripts" / "memory_mcp.py").read_text(encoding="utf-8").replace("delete or clear", ""))

    def test_start_never_spawns_twice_or_over_another_program(self):
        with mock.patch.object(ms.subprocess, "Popen") as popen:
            with mock.patch.object(ms, "health", return_value="hindsight"):
                self.assertEqual(ms.start(out=lambda line: None), 0)
            with mock.patch.object(ms, "health", return_value="other"):
                self.assertEqual(ms.start(out=lambda line: None), 3)
            with mock.patch.object(ms, "health", return_value=None), \
                    mock.patch.object(ms, "recorded_server", return_value=4242):
                self.assertEqual(ms.start(out=lambda line: None), 0)
            with mock.patch.object(ms, "health", return_value=None), \
                    mock.patch.object(ms, "recorded_server", return_value=None), \
                    mock.patch.object(ms, "find_runtime", return_value=None):
                self.assertEqual(ms.start(out=lambda line: None), 2)
        popen.assert_not_called()

    def test_start_runs_the_server_detached_on_loopback(self):
        runtime = self.home / "rt"
        exe = ms.program(runtime)
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b"")
        process = mock.MagicMock(pid=77)
        with mock.patch.object(ms, "health", return_value=None), \
                mock.patch.object(ms, "recorded_server", return_value=None), \
                mock.patch.object(ms, "find_runtime", return_value=runtime), \
                mock.patch.object(ms.subprocess, "Popen", return_value=process) as popen:
            self.assertEqual(ms.start(out=lambda line: None), 0)
        argv = popen.call_args.args[0]
        self.assertEqual(argv, [str(exe), "--host", "127.0.0.1", "--port", "8888"])
        self.assertEqual(popen.call_args.kwargs["env"]["HINDSIGHT_API_HOST"], "127.0.0.1")
        self.assertEqual(ms.pid_file().read_text(encoding="ascii"), "77")

    def test_stop_only_stops_its_own_hindsight_process(self):
        ms.state_dir().mkdir(parents=True)
        ms.pid_file().write_text("99", encoding="ascii")
        with mock.patch.object(ms, "process_image", return_value="notepad.exe"), \
                mock.patch.object(ms.subprocess, "run") as run, mock.patch.object(ms.os, "kill") as kill:
            self.assertEqual(ms.stop(out=lambda line: None), 0)
        run.assert_not_called()
        kill.assert_not_called()

    def test_autostart_runs_a_copy_outside_the_plugin(self):
        with mock.patch.object(ms.sys, "platform", "win32"), \
                mock.patch.object(ms.subprocess, "run", return_value=mock.MagicMock(returncode=0, stdout=b"ok", stderr=b"")) as run:
            self.assertEqual(ms.autostart(True, out=lambda line: None), 0)
        argv = run.call_args.args[0]
        self.assertEqual(argv[:4], ["schtasks", "/Create", "/TN", ms.TASK_NAME])
        self.assertIn("ONLOGON", argv)
        self.assertIn("LIMITED", argv)  # no administrator rights
        launcher = ms.state_dir() / "memory_server.py"
        self.assertTrue(launcher.is_file())
        self.assertIn(str(launcher), argv[-1])
        self.assertTrue(argv[-1].endswith(" start"))

    def test_repository_names(self):
        cases = {"https://github.com/acme/space-game.git": "space-game", "git@github.com:acme/space-game.git": "space-game",
                 "https://github.com/acme/space-game/": "space-game"}
        for remote, name in cases.items():
            with self.subTest(remote=remote), mock.patch.object(
                    ms.subprocess, "run", return_value=mock.MagicMock(stdout=remote.encode())):
                self.assertEqual(ms.repository_name(Path("/x/folder")), name)
        with mock.patch.object(ms.subprocess, "run", return_value=mock.MagicMock(stdout=b"")):
            self.assertEqual(ms.repository_name(self.home), self.home.resolve().name)


class McpTests(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.game = Path(scratch.name) / "my-game"
        (self.game / "src").mkdir(parents=True)
        (self.game / ".gamedev-studio").write_text("", encoding="utf-8")

    def test_tools_are_the_contracts_per_bank_without_bank_id(self):
        names = [tool["name"] for tool in mm.tool_list()]
        self.assertEqual(names, [f"{p}{t}" for p in ("studio_", "project_") for t in POLICY["mcp_enabled_tools"]])
        for tool in mm.tool_list():
            for forbidden in ("bank_id", "document_id", "update_mode"):
                self.assertNotIn(forbidden, tool["inputSchema"].get("properties", {}))
            self.assertNotRegex(tool["name"], "delete|clear|reflect")

    def test_project_bank_is_the_game_of_this_session(self):
        with mock.patch.object(ms.subprocess, "run", return_value=mock.MagicMock(stdout=b"")):
            self.assertEqual(mm.studio_game(str(self.game / "src")), self.game.resolve())
            self.assertEqual(mm.bank_for("project", self.game), "gamedev-studio::project::my-game")
        self.assertEqual(mm.bank_for("studio", None), "gamedev-studio::studio")
        self.assertIsNone(mm.bank_for("project", None))
        self.assertIsNone(mm.studio_game(str(Path(self.game).parent)))

    def memory(self, game):
        with mock.patch.object(mm, "studio_game", return_value=game):
            return mm.Memory()

    def test_calls_route_to_one_bank_and_drop_bank_id(self):
        memory = self.memory(self.game)
        upstream = mock.MagicMock()
        upstream.tool.return_value = {"result": {"content": [{"type": "text", "text": "ok"}]}}
        with mock.patch.object(ms, "health", return_value="hindsight"), \
                mock.patch.object(ms.subprocess, "run", return_value=mock.MagicMock(stdout=b"")), \
                mock.patch.object(mm, "Upstream", return_value=upstream) as made:
            result = memory.call("project_recall", {"query": "q", "bank_id": "gamedev-studio::project::other",
                                                    "document_id": "d", "update_mode": "replace"})
        self.assertEqual(result, {"content": [{"type": "text", "text": "ok"}]})
        self.assertEqual(made.call_args.args[0], "gamedev-studio::project::my-game")
        self.assertEqual(upstream.tool.call_args.args, ("recall", {"query": "q"}))

    def test_refusals_and_missing_server_are_answers_not_failures(self):
        outside = self.memory(None)
        self.assertTrue(outside.call("project_recall", {"query": "q"})["isError"])
        self.assertIn("Unknown", outside.call("studio_delete_bank", {})["content"][0]["text"])
        self.assertIn("Unknown", outside.call("recall", {})["content"][0]["text"])
        with mock.patch.object(ms, "health", return_value=None), mock.patch.object(ms, "find_runtime", return_value=None):
            text = outside.call("studio_recall", {"query": "q"})["content"][0]["text"]
        self.assertIn("setup-tools", text)
        with mock.patch.object(ms, "health", return_value=None), \
                mock.patch.object(ms, "find_runtime", return_value=Path("/rt")), \
                mock.patch.object(ms, "start", return_value=0) as start:
            text = outside.call("studio_recall", {"query": "q"})["content"][0]["text"]
        start.assert_called_once()
        self.assertIn("starting", text)
        with mock.patch.object(ms, "health", return_value="other"):
            self.assertIn("another program", outside.call("studio_get_bank", {})["content"][0]["text"])

    def test_protocol_over_stdio(self):
        lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                 {"jsonrpc": "2.0", "method": "notifications/initialized"},
                 {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                 {"jsonrpc": "2.0", "id": 3, "method": "nope"}]
        out = io.StringIO()
        with mock.patch.object(mm, "warm_up"), mock.patch.object(mm, "studio_game", return_value=None):
            mm.serve(io.StringIO("\n".join(json.dumps(line) for line in lines) + "\n"), out)
        replies = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual([reply["id"] for reply in replies], [1, 2, 3])
        self.assertIn("DEC-103", replies[0]["result"]["instructions"])
        self.assertEqual(len(replies[1]["result"]["tools"]), 10)
        self.assertEqual(replies[2]["error"]["code"], -32601)


class SchemaTests(unittest.TestCase):
    def test_schemas_are_the_pinned_versions_tools(self):
        doc = json.loads((ROOT / "scripts" / "memory_tool_schemas.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["hindsight_version"], POLICY["capability"]["version"])
        self.assertEqual(sorted(doc["tools"]), sorted(POLICY["mcp_enabled_tools"]))
        self.assertEqual(doc["tools"]["recall"]["required"], ["query"])
        self.assertEqual(doc["tools"]["retain"]["required"], ["content"])


class PluginWiringTests(unittest.TestCase):
    def test_plugin_starts_the_memory_mcp_with_every_session(self):
        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        server = manifest["mcpServers"]["memory"]
        self.assertEqual(server["command"], "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd")
        self.assertEqual(server["args"], ["memory_mcp"])
        self.assertTrue((ROOT / "hooks" / "scripts" / "memory_mcp.py").is_file())

    def test_catalog_installs_memory_for_everyone(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import studio_tools as st
        tool = st.tool_by_id(st.load_catalog(), "hindsight")
        self.assertEqual((tool["who"], tool["scope"], tool["cost"]["kind"]), ("claude_yes", "machine", "free"))
        steps = st.install_steps(tool, Path("/g"), python="/py")
        self.assertEqual(steps[-1][-1], f"hindsight-api=={POLICY['capability']['version']}")


if __name__ == "__main__":
    unittest.main()
