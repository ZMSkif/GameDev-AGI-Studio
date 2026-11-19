"""Unit tests for scripts/hindsight_smoke.py, with a fake Hindsight server (no real server needed)."""
import contextlib
import importlib.util
import io
import json
import re
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("hindsight_smoke", REPO_ROOT / "scripts" / "hindsight_smoke.py")
hs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hs)

CONTRACT_TOOLS = set(json.loads((REPO_ROOT / "contracts/v1/knowledge-policy.json").read_text(encoding="utf-8"))
                     ["memory_backend"]["mcp_enabled_tools"])


class FakeHindsight:
    """Answers hs.request like Hindsight 1.2.2. Flags turn on one fault each."""

    def __init__(self, **faults):
        self.banks: dict[str, list[dict]] = {}
        self.tools = set(CONTRACT_TOOLS)
        self.bank_tools: dict[str, set] = {}
        self.faults = faults
        self.next_id = 0

    # -- REST -------------------------------------------------------------------------------
    def __call__(self, url, method="GET", body=None, headers=None, timeout=0):
        path = re.sub(r"^https?://[^/]+", "", url)
        if path == "/health":
            if self.faults.get("health_not_json"):
                return 200, {}, "<html>ok</html>"
            return 200, {}, json.dumps({"status": "healthy", "database": "connected"})
        if path == "/v1/version":
            return 200, {}, json.dumps({"api_version": "1.2.2"})
        if path.startswith("/v1/default/banks?"):
            query = dict(part.split("=") for part in path.split("?", 1)[1].split("&"))
            names = sorted(self.banks) + [f"filler-{i}" for i in range(self.faults.get("extra_banks", 0))]
            names.sort(key=lambda n: (not n.startswith("filler"), n))           # real banks after the fillers
            start, limit = int(query.get("offset", 0)), int(query.get("limit", 100))
            return 200, {}, json.dumps({"banks": [{"bank_id": b} for b in names[start:start + limit]]})
        match = re.match(r"^/v1/default/banks/(.+?)/memories(/recall)?$", path)
        if match and method == "POST":
            bank = match.group(1)
            if match.group(2):
                return 200, {}, json.dumps({"results": self.recall(bank, body)})
            return 200, {}, json.dumps(self.retain(bank, body["items"]))
        match = re.match(r"^/mcp/(.+?)/$", path)
        if match:
            return self.mcp(match.group(1), body)
        return 404, {}, "{}"

    def retain(self, bank, items):
        if self.faults.get("retain_fails"):
            return {"success": False, "items_count": 0}
        for item in items:
            self.next_id += 1
            meta = dict(item.get("metadata") or {})
            if self.faults.get("empty_metadata"):
                meta = {k: "" for k in meta}
            self.banks.setdefault(bank, []).append({
                "id": f"00000000-0000-0000-0000-{self.next_id:012d}", "text": item["content"], "metadata": meta,
                "tags": item.get("tags", []), "type": "world"})
        return {"success": True, "bank_id": bank, "items_count": len(items), "async": False}

    def recall(self, bank, body):
        pool = [m for b, ms in self.banks.items() for m in ms] if self.faults.get("leak_rest") \
            else list(self.banks.get(bank, []))
        tags = None if self.faults.get("tags_ignored") else body.get("tags")
        if tags:
            pool = [m for m in pool if set(tags) & set(m["tags"])]
        results = [dict(m) for m in pool]
        if "types" not in body and results:
            results.append({"text": "derived observation", "metadata": {}, "tags": [], "type": "observation"})
        return results

    # -- MCP --------------------------------------------------------------------------------
    def mcp(self, bank, body):
        method = body.get("method")
        if method == "notifications/initialized":
            return 202, {}, ""
        if method == "initialize":
            result = {"protocolVersion": "2025-06-18"}
        elif method == "tools/list":
            result = {"tools": [{"name": n} for n in sorted(self.bank_tools.get(bank, self.tools))]}
        else:
            name, args = body["params"]["name"], body["params"]["arguments"]
            target = args.get("bank_id", bank) if self.faults.get("mcp_honours_bank_id") else bank
            if name == "recall":
                payload = {"results": [] if self.faults.get("mcp_recall_empty") and "bank_id" not in args
                           else self.recall(target, {"query": args["query"]})}
            elif name == "list_memories":
                pool = [m for ms in self.banks.values() for m in ms] if self.faults.get("leak_list") \
                    else self.banks.get(bank, [])
                payload = {"items": pool, "total": len(pool)}
            elif name == "get_memory":
                payload = next((m for m in self.banks.get(bank, []) if m["id"] == args["memory_id"]), None)
                if self.faults.get("get_memory_swaps_text") and payload:
                    beta = next(m for b, ms in self.banks.items() if "beta" in b for m in ms)
                    payload = dict(payload, text=beta["text"])
            elif name == "get_bank":
                payload = {"bank_id": "someone-else" if self.faults.get("get_bank_other") else bank}
            else:
                payload = None
            result = {"content": [{"type": "text", "text": json.dumps(payload)}], "isError": payload is None,
                      "structuredContent": payload}
        answer = {"jsonrpc": "2.0", "id": body.get("id"), "result": result}
        return 200, {"Content-Type": "application/json", "mcp-session-id": "s1"}, json.dumps(answer)


class FakeServerCase(unittest.TestCase):
    def call(self, fake, *args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(hs, "request", side_effect=fake), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = hs.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def rows(self, out):
        return {line.split(":")[0].split(None, 1)[1]: line.split()[0] for line in out.splitlines()[1:]}

    def store(self, fake, run="r1"):
        code, out, err = self.call(fake, "--run", run)
        return code, self.rows(out), err


class RunTest(FakeServerCase):
    def test_clean_server_passes_and_persistence_is_manual(self):
        code, rows, _ = self.store(FakeHindsight())
        self.assertEqual(code, 0)
        self.assertEqual(rows, {"S1 health": "PASS", "S2 retain": "PASS", "S3 project isolation": "PASS",
                                "S4 MCP isolation": "PASS", "S5 task scope": "PASS", "S6 provenance": "PASS",
                                "S7 MCP allowlist": "PASS", "S8 persistence": "MANUAL", "S9 MCP read tools": "PASS"})

    def test_recall_only_needs_after_restart_for_persistence(self):
        fake = FakeHindsight()
        self.store(fake)
        code, out, _ = self.call(fake, "--run", "r1", "--recall-only")
        self.assertEqual(self.rows(out)["S8 persistence"], "MANUAL")
        code, out, _ = self.call(fake, "--run", "r1", "--recall-only", "--after-restart", "--json")
        self.assertEqual(code, 0)
        s8 = [r for r in json.loads(out)["evidence"] if r["integration_id"] == "hindsight-s8"][0]
        self.assertEqual((s8["status"], s8["recovery_test"]), ("pass", "pass"))
        self.assertIn("--recall-only --after-restart", s8["command_redacted"])
        self.assertIn("--run r1", s8["command_redacted"])
        self.assertEqual(s8["version"], "1.2.2")

    def test_persistence_needs_this_runs_studio_fact(self):
        fake = FakeHindsight()
        self.store(fake, "r1")
        fake.banks["gamedev-studio-smoke::studio-r2"] = [
            dict(fake.banks["gamedev-studio-smoke::studio-r1"][0], text="Studio rule r1: an independent reviewer.")]
        for kind in ("alpha", "beta"):
            fake.banks[f"gamedev-studio-smoke::project::{kind}-r2"] = fake.banks[f"gamedev-studio-smoke::project::{kind}-r1"]
        _, out, _ = self.call(fake, "--run", "r2", "--recall-only", "--after-restart")
        self.assertEqual(self.rows(out)["S8 persistence"], "FAIL")

    def test_each_fault_fails_its_check(self):
        cases = {"leak_rest": "S3 project isolation", "mcp_honours_bank_id": "S4 MCP isolation",
                 "empty_metadata": "S6 provenance", "retain_fails": "S2 retain", "leak_list": "S9 MCP read tools",
                 "get_memory_swaps_text": "S9 MCP read tools", "tags_ignored": "S5 task scope",
                 "get_bank_other": "S9 MCP read tools", "mcp_recall_empty": "S4 MCP isolation"}
        for fault, check in cases.items():
            with self.subTest(fault=fault):
                code, rows, _ = self.store(FakeHindsight(**{fault: True}))
                self.assertEqual(rows[check], "FAIL")
                self.assertEqual(code, 1)

    def test_provenance_of_another_run_fails(self):
        fake = FakeHindsight()
        self.store(fake, "r1")
        for memory in fake.banks["gamedev-studio-smoke::project::alpha-r1"]:
            memory["metadata"]["source_rev"] = "old"
        _, out, _ = self.call(fake, "--run", "r1", "--recall-only")
        self.assertEqual(self.rows(out)["S6 provenance"], "FAIL")

    def test_tool_set_must_equal_the_contract(self):
        for change in ({"delete_bank"}, {"reflect"}, set()):
            with self.subTest(change=change):
                fake = FakeHindsight()
                fake.tools = (CONTRACT_TOOLS | change) if change else CONTRACT_TOOLS - {"get_bank"}
                _, rows, _ = self.store(fake)
                self.assertEqual(rows["S7 MCP allowlist"], "FAIL")

    def test_every_endpoint_is_checked_for_the_tool_set(self):
        for kind in ("studio", "alpha", "beta"):
            with self.subTest(endpoint=kind):
                fake = FakeHindsight()
                name = {"studio": "gamedev-studio-smoke::studio-r1"}.get(kind, f"gamedev-studio-smoke::project::{kind}-r1")
                fake.bank_tools[name] = CONTRACT_TOOLS | {"delete_bank"}
                _, rows, _ = self.store(fake)
                self.assertEqual(rows["S7 MCP allowlist"], "FAIL")

    def test_a_used_run_id_is_found_past_the_first_page(self):
        fake = FakeHindsight(extra_banks=250)
        self.store(fake, "r1")
        code, _, err = self.call(fake, "--run", "r1")
        self.assertEqual(code, 2)
        self.assertIn("was used before", err)

    def test_a_used_run_id_is_refused(self):
        fake = FakeHindsight()
        self.store(fake, "r1")
        stored = sum(len(m) for m in fake.banks.values())
        code, _, err = self.call(fake, "--run", "r1")
        self.assertEqual(code, 2)
        self.assertIn("was used before", err)
        self.assertEqual(sum(len(m) for m in fake.banks.values()), stored)

    def test_no_document_id_or_update_mode_is_sent(self):
        sent = []
        fake = FakeHindsight()

        def spy(url, method="GET", body=None, headers=None, timeout=0):
            if url.endswith("/memories") and method == "POST":
                sent.extend(body["items"])
            return fake(url, method, body, headers, timeout)

        self.store(spy)
        self.assertEqual(len(sent), 4)
        self.assertTrue(all("document_id" not in i and "update_mode" not in i for i in sent))
        self.assertTrue(all(i["metadata"]["source_rev"] == "r1" for i in sent))

    def test_health_that_is_not_json_is_a_fail(self):
        code, out, err = self.call(FakeHindsight(health_not_json=True), "--run", "r1")
        self.assertEqual(code, 1)
        self.assertIn("FAIL    S1 health", out)
        self.assertNotIn("Traceback", err)


class PartsTest(unittest.TestCase):
    def test_tools_are_read_from_the_contract(self):
        self.assertEqual(hs.allowed_tools(), CONTRACT_TOOLS)
        self.assertNotIn("reflect", CONTRACT_TOOLS)

    def test_judge_tools_is_exact(self):
        self.assertEqual(hs.judge_tools(set(CONTRACT_TOOLS), CONTRACT_TOOLS)[0], "PASS")
        self.assertEqual(hs.judge_tools({"retain", "recall"}, CONTRACT_TOOLS)[0], "FAIL")
        result, why = hs.judge_tools(CONTRACT_TOOLS | {"delete_bank"}, CONTRACT_TOOLS)
        self.assertEqual(result, "FAIL")
        self.assertIn("delete_bank", why)

    def test_provenance_values(self):
        good = {"results": [{"metadata": hs.provenance("r1")}]}
        self.assertTrue(hs.has_provenance(good, "r1"))
        self.assertFalse(hs.has_provenance(good, "r2"))
        self.assertFalse(hs.has_provenance({"results": [{"metadata": dict(hs.provenance("r1"), source="")}]}, "r1"))
        self.assertFalse(hs.has_provenance({"results": []}, "r1"))

    def test_bank_names_carry_the_run(self):
        names = hs.banks("p", "r1")
        self.assertEqual(names["studio"], "p::studio-r1")
        self.assertTrue(all(n.endswith("-r1") for n in names.values()))
        self.assertTrue(all("::project::" in names[k] for k in ("alpha", "beta")))

    def test_facts_name_the_run_and_one_task(self):
        self.assertTrue(all("r1" in f["content"] for f in hs.facts("r1")))
        self.assertEqual([t for f in hs.facts("r1") for t in f["tags"]], ["task:T1"])

    def test_mcp_parsing(self):
        sse = 'event: message\ndata: {"jsonrpc": "2.0", "id": 2, "result": {"tools": []}}\n\n'
        self.assertEqual(hs.parse_mcp(sse, "text/event-stream")["id"], 2)
        self.assertEqual(hs.parse_mcp('{"id": 3}', "application/json")["id"], 3)
        for raw, kind in (("event: ping\n\n", "text/event-stream"), ("<html>", "application/json")):
            with self.assertRaises(hs.SmokeError):
                hs.parse_mcp(raw, kind)

    def test_evidence_rows_match_the_integration_evidence_contract(self):
        schema = json.loads((REPO_ROOT / "contracts/v1/integration-evidence.schema.json").read_text(encoding="utf-8"))
        rows = [("S1 health", "PASS", "ok"), ("S8 persistence", "MANUAL", "later"), ("S2 retain", "UNKNOWN", "n/a")]
        for row in hs.evidence(rows, "python scripts/hindsight_smoke.py --run r1", "1.2.2", "local"):
            self.assertEqual(set(schema["required"]) - set(row), set())
            self.assertEqual(set(row) - set(schema["properties"]), set())
            self.assertIn(row["status"], schema["properties"]["status"]["enum"])
            self.assertEqual(row["recovery_test"], "not_run")


class CliTest(FakeServerCase):
    def test_argument_errors(self):
        for args in (["--recall-only"], ["--after-restart", "--run", "r1"], ["--run", "Bad id"], ["--run", "x"]):
            with self.subTest(args=args):
                self.assertEqual(self.call(FakeHindsight(), *args)[0], 2)

    def test_unreachable_server_gives_exit_two(self):
        code, _, err = self.call(hs.SmokeError("GET x: refused"), "--run", "r1")
        self.assertEqual(code, 2)
        self.assertIn("refused", err)

    def test_unhealthy_server_is_a_fail(self):
        code, out, _ = self.call(lambda *a, **k: (503, {}, '{"database": "down"}'), "--run", "r1")
        self.assertEqual(code, 1)
        self.assertIn("FAIL    S1 health", out)


if __name__ == "__main__":
    unittest.main()
