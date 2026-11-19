"""Unit tests for the pure parts of scripts/hindsight_smoke.py (no server needed)."""
import contextlib
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("hindsight_smoke", REPO_ROOT / "scripts" / "hindsight_smoke.py")
hs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hs)

FACT_META = {"source_type": "x", "source": "y", "source_rev": "z", "recorded_by": "w", "verified": "false"}


class ToolsTest(unittest.TestCase):
    allowed = set(hs.ALLOWED_TOOLS)

    def test_exact_allowlist_passes(self):
        self.assertEqual(hs.judge_tools(set(hs.ALLOWED_TOOLS), self.allowed)[0], "PASS")

    def test_any_tool_outside_the_allowlist_fails(self):
        for extra in ("delete_bank", "reflect", "some_new_tool"):
            with self.subTest(tool=extra):
                result, why = hs.judge_tools(set(hs.ALLOWED_TOOLS) | {extra}, self.allowed)
                self.assertEqual(result, "FAIL")
                self.assertIn(extra, why)

    def test_missing_required_tool_fails(self):
        self.assertEqual(hs.judge_tools({"recall"}, self.allowed)[0], "FAIL")

    def test_reflect_is_not_allowed_by_default(self):
        self.assertNotIn("reflect", hs.ALLOWED_TOOLS)


class ProvenanceTest(unittest.TestCase):
    def test_all_facts_with_keys_pass(self):
        self.assertTrue(hs.has_provenance({"results": [{"metadata": dict(FACT_META)}]}))

    def test_missing_key_or_empty_metadata_fails(self):
        partial = dict(FACT_META)
        partial.pop("source_rev")
        self.assertFalse(hs.has_provenance({"results": [{"metadata": partial}]}))
        self.assertFalse(hs.has_provenance({"results": [{"metadata": dict(FACT_META)}, {"metadata": {}}]}))

    def test_no_results_is_no_proof(self):
        self.assertFalse(hs.has_provenance({"results": []}))


class McpParseTest(unittest.TestCase):
    def test_event_stream_and_json(self):
        sse = 'event: message\ndata: {"jsonrpc": "2.0", "id": 2, "result": {"tools": []}}\n\n'
        self.assertEqual(hs.parse_mcp(sse, "text/event-stream")["id"], 2)
        self.assertEqual(hs.parse_mcp('{"id": 3}', "application/json")["id"], 3)

    def test_event_stream_without_data_is_an_error(self):
        with self.assertRaises(hs.SmokeError):
            hs.parse_mcp("event: ping\n\n", "text/event-stream")


class ShapeTest(unittest.TestCase):
    def test_bank_names_keep_scopes_apart(self):
        names = hs.banks("p", "r1")
        self.assertEqual(names["studio"], "p::studio")
        self.assertNotEqual(names["alpha"], names["beta"])
        self.assertTrue(all("::project::" in names[k] for k in ("alpha", "beta")))

    def test_facts_carry_scope_tags_and_one_task_tag(self):
        tags = [t for f in hs.facts("r1") for t in f["tags"]]
        self.assertIn("task:T1", tags)
        self.assertTrue(all(any(t.startswith("scope:") for t in f["tags"]) for f in hs.facts("r1")))

    def test_evidence_rows_match_the_integration_evidence_contract(self):
        schema = json.loads((REPO_ROOT / "contracts/v1/integration-evidence.schema.json").read_text(encoding="utf-8"))
        rows = [("S1 health", "PASS", "ok"), ("S8 persistence", "MANUAL", "later"), ("S2 retain", "UNKNOWN", "n/a")]
        for row in hs.evidence(rows, "http://127.0.0.1:8888", "hindsight-api 1.2.2", "local"):
            self.assertEqual(set(schema["required"]) - set(row), set())
            self.assertEqual(set(row) - set(schema["properties"]), set())
            self.assertIn(row["status"], schema["properties"]["status"]["enum"])
            self.assertIn(row["recovery_test"], schema["properties"]["recovery_test"]["enum"])


class CliTest(unittest.TestCase):
    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = hs.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_recall_only_needs_a_run_id(self):
        code, _, err = self.call("--recall-only")
        self.assertEqual(code, 2)
        self.assertIn("--run", err)

    def test_unreachable_server_gives_exit_two(self):
        with mock.patch.object(hs, "request", side_effect=hs.SmokeError("GET x: refused")):
            code, _, err = self.call("--url", "http://127.0.0.1:1")
        self.assertEqual(code, 2)
        self.assertIn("refused", err)

    def test_unhealthy_server_is_a_fail(self):
        with mock.patch.object(hs, "request", return_value=(503, {}, '{"database": "down"}')):
            code, out, _ = self.call()
        self.assertEqual(code, 1)
        self.assertIn("FAIL    S1 health", out)


if __name__ == "__main__":
    unittest.main()
