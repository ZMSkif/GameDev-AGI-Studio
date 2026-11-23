#!/usr/bin/env python3
"""Real smoke test of a Hindsight server for the gamedev-studio memory layer (DEC-042, DEC-046).

It talks to a running server over HTTP (stdlib only) and prints a PASS / FAIL / MANUAL / UNKNOWN
matrix (DEC-120); with --json each row has the shape of contracts/v1/integration-evidence.schema.json.
It never deletes anything: memory is kept until the owner deletes it (DEC-138), so the test banks
it creates stay and are named `<prefix>::...-<run>` for the owner to remove. A run id is used for
one store run only, so no document is ever replaced.

Checks:
  S1 health            the server answers and its database is connected
  S2 retain            each fact is stored (the server answers success for one item)
  S3 project isolation a fact retained in one project bank is not recalled from another (DEC-101)
  S4 MCP isolation     alpha's per-bank MCP endpoint returns alpha's fact and never beta's, even when
                       the call names beta's bank_id
  S5 task scope        task memories are found by their task tag and not by another task's tag
  S6 provenance        recalled facts carry this run's provenance values, none of them empty
  S7 MCP allowlist     every per-bank endpoint exposes exactly the contract's mcp_enabled_tools, so no
                       delete, clear or unsourced reflect tool (DEC-138, provenance_required)
  S8 persistence       after a server restart (--recall-only --after-restart), this run's facts are
                       still recalled; without --after-restart it is MANUAL
  S9 MCP read tools    list_memories, get_memory and get_bank answer on the per-bank endpoint and
                       show no other bank's facts; get_memory returns the listed fact's own text

Usage:
  python scripts/hindsight_smoke.py [--url http://127.0.0.1:8888] [--prefix gamedev-studio-smoke]
                                    [--run RUN_ID] [--recall-only [--after-restart]] [--json]
Exit codes: 0 no FAIL, 1 at least one FAIL, 2 bad arguments or the server is unreachable.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

POLICY = Path(__file__).resolve().parents[1] / "contracts" / "v1" / "knowledge-policy.json"
PROVENANCE_KEYS = ("source_type", "source", "source_rev", "recorded_by", "verified")
SOURCE = "scripts/hindsight_smoke.py"
RECORDED_BY = "gamedev-studio:hindsight_smoke"
RUN_RE = re.compile(r"^[a-z0-9]{2,16}$")


class SmokeError(RuntimeError):
    """The server could not be reached or answered with something unusable."""


def allowed_tools() -> set[str]:
    """The per-bank tools the contract allows (knowledge-policy.json memory_backend.mcp_enabled_tools)."""
    return set(json.loads(POLICY.read_text(encoding="utf-8"))["memory_backend"]["mcp_enabled_tools"])


def request(url: str, method: str = "GET", body=None, headers=None, timeout: float = 180.0):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise SmokeError(f"{method} {url}: {exc}") from exc


def as_json(raw: str):
    try:
        return json.loads(raw)
    except ValueError:
        return None


def banks(prefix: str, run: str) -> dict[str, str]:
    """A studio bank and two project banks per run; tasks are tags inside a project bank (DEC-101)."""
    return {
        "studio": f"{prefix}::studio-{run}",
        "alpha": f"{prefix}::project::alpha-{run}",
        "beta": f"{prefix}::project::beta-{run}",
    }


def provenance(run: str) -> dict[str, str]:
    return {"source_type": "smoke-test", "source": SOURCE, "source_rev": run,
            "recorded_by": RECORDED_BY, "verified": "false"}


def facts(run: str) -> list[dict]:
    """Facts with unique tokens, so a recall shows where an answer came from."""
    return [
        {"bank": "studio", "content": f"Studio rule {run}: every piece of work gets an independent reviewer.",
         "tags": []},
        {"bank": "alpha", "content": f"The alpha game {run} uses the cobalt-lantern colour palette.", "tags": []},
        {"bank": "beta", "content": f"The beta game {run} uses the amber-kite colour palette.", "tags": []},
        {"bank": "alpha", "content": f"Task T1 of {run} fixed the lantern flicker by lifting the overlay 2 mm.",
         "tags": ["task:T1"]},
    ]


def texts(recall_body: dict) -> str:
    return " ".join(str(r.get("text", "")) for r in recall_body.get("results", [])).lower()


def has_provenance(recall_body: dict, run: str) -> bool:
    """Every result carries this run's provenance, with no empty value."""
    want = provenance(run)
    results = recall_body.get("results", [])
    return bool(results) and all(
        isinstance(r.get("metadata"), dict) and all(r["metadata"].get(k) == want[k] for k in PROVENANCE_KEYS)
        for r in results)


def parse_mcp(raw: str, content_type: str) -> dict:
    """A JSON-RPC answer, sent as plain JSON or as one server-sent event."""
    if "text/event-stream" in (content_type or ""):
        for line in raw.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        raise SmokeError("MCP answer had no data line")
    answer = as_json(raw)
    if not isinstance(answer, dict):
        raise SmokeError("MCP answer is not JSON")
    return answer


class McpSession:
    """A minimal streamable-HTTP MCP client for one endpoint."""

    def __init__(self, url: str):
        self.url, self.next_id = url, 1
        self.headers = {"Accept": "application/json, text/event-stream"}
        self.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "gamedev-studio-smoke", "version": "1"}}, keep_session=True)
        request(url, "POST", {"jsonrpc": "2.0", "method": "notifications/initialized"}, self.headers)

    def call(self, method: str, params: dict | None = None, keep_session: bool = False) -> dict:
        self.next_id += 1
        body = {"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params or {}}
        status, head, raw = request(self.url, "POST", body, self.headers)
        if status != 200:
            raise SmokeError(f"MCP {method} {self.url}: HTTP {status}")
        lowered = {k.lower(): v for k, v in head.items()}
        if keep_session and lowered.get("mcp-session-id"):
            self.headers["Mcp-Session-Id"] = lowered["mcp-session-id"]
        return parse_mcp(raw, lowered.get("content-type", ""))

    def tool(self, name: str, arguments: dict) -> tuple[bool, object, str]:
        """(ok, parsed payload, lower-case text of the whole answer); ok is False for an error answer."""
        answer = self.call("tools/call", {"name": name, "arguments": arguments})
        result = answer.get("result")
        ok = "error" not in answer and isinstance(result, dict) and not result.get("isError")
        payload = None
        if isinstance(result, dict):
            payload = result.get("structuredContent")
            if payload is None and result.get("content"):
                payload = as_json(str(result["content"][0].get("text", "")))
        return ok, payload, json.dumps(answer, ensure_ascii=False).lower()


def endpoint(base: str, bank: str) -> str:
    return f"{base}/mcp/{bank}/"


def judge_tools(tools: set[str], allowed: set[str]) -> tuple[str, str]:
    if tools == allowed:
        return "PASS", f"exactly the contract's tools: {sorted(tools)}"
    return "FAIL", f"missing {sorted(allowed - tools)}; outside the contract {sorted(tools - allowed)}"


def recall(base: str, bank: str, query: str, **extra) -> dict:
    body = {"query": query, "budget": "mid", "max_tokens": 2048}
    body.update(extra)
    status, _, raw = request(f"{base}/v1/default/banks/{bank}/memories/recall", "POST", body)
    answer = as_json(raw)
    if status != 200 or not isinstance(answer, dict):
        raise SmokeError(f"recall {bank}: HTTP {status}: {raw[:200]}")
    return answer


def existing_banks(base: str, page: int = 100) -> set[str]:
    """Every bank id on the server, page by page (the server returns at most `limit` at a time)."""
    found: set[str] = set()
    for offset in range(0, 1_000_000, page):
        status, _, raw = request(f"{base}/v1/default/banks?limit={page}&offset={offset}")
        answer = as_json(raw)
        if status != 200 or not isinstance(answer, dict):
            raise SmokeError(f"list banks: HTTP {status}")
        banks_page = [b.get("bank_id") for b in answer.get("banks", []) if isinstance(b, dict)]
        found.update(banks_page)
        if len(banks_page) < page:
            return found
    raise SmokeError("list banks: too many pages")


def retain_one(base: str, bank: str, item: dict) -> bool:
    status, _, raw = request(f"{base}/v1/default/banks/{bank}/memories", "POST", {"items": [item]}, timeout=600)
    answer = as_json(raw)
    return status == 200 and isinstance(answer, dict) and answer.get("success") is True \
        and answer.get("items_count") == 1


def check_mcp_isolation(base: str, names: dict, run: str, question: str) -> tuple[str, str]:
    session = McpSession(endpoint(base, names["alpha"]))
    ok, _, own = session.tool("recall", {"query": question})
    probe_ok, _, probe = session.tool("recall", {"query": question, "bank_id": names["beta"]})
    leaked = "amber" in own or "amber" in probe
    if ok and "cobalt" in own and not leaked:
        how = "returned alpha's fact" if probe_ok and "cobalt" in probe else "was refused"
        return "PASS", f"alpha's endpoint returns alpha's fact only; the call naming beta's bank_id {how}"
    return "FAIL", f"own recall ok={ok} cobalt={'cobalt' in own}; beta's fact leaked={leaked}"


def check_read_tools(base: str, names: dict) -> tuple[str, str]:
    session = McpSession(endpoint(base, names["alpha"]))
    listed_ok, listed, listed_text = session.tool("list_memories", {})
    bank_ok, bank, _ = session.tool("get_bank", {})
    items = [i for i in (listed.get("items", []) if isinstance(listed, dict) else []) if isinstance(i, dict)]
    # The stored cobalt fact itself (a fact, not an observation), so get_memory can be checked by content.
    target = next((i for i in items if i.get("id") and "cobalt" in str(i.get("text", "")).lower()
                   and i.get("fact_type", i.get("type")) in ("world", "experience")), None)
    got_ok = False
    if target:
        got_ok, got, got_text = session.tool("get_memory", {"memory_id": target["id"]})
        got_ok = (got_ok and isinstance(got, dict) and got.get("id") == target["id"]
                  and got.get("text") == target.get("text") and "amber" not in got_text)
    own_bank = isinstance(bank, dict) and bank.get("bank_id") == names["alpha"]
    clean = "amber" not in listed_text
    if listed_ok and bank_ok and got_ok and own_bank and clean:
        return "PASS", "list_memories, get_bank and get_memory answered with alpha's data only"
    return "FAIL", (f"list_memories ok={listed_ok} ({len(items)} items), get_bank ok={bank_ok} own={own_bank}, "
                    f"get_memory of alpha's fact ok={got_ok}, other bank's data absent={clean}")


def run(base: str, prefix: str, run_id: str, recall_only: bool, after_restart: bool,
        allowed: set[str]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    status, _, raw = request(f"{base}/health")
    health = as_json(raw)
    healthy = status == 200 and isinstance(health, dict) and health.get("database") == "connected"
    rows.append(("S1 health", "PASS" if healthy else "FAIL", raw[:120]))
    if not healthy:
        return rows
    names = banks(prefix, run_id)
    if recall_only:
        rows.append(("S2 retain", "UNKNOWN", "not run in --recall-only mode"))
    else:
        clash = sorted(set(names.values()) & existing_banks(base))
        if clash:
            raise SmokeError(f"run id {run_id} was used before ({', '.join(clash)}); pick a new --run, "
                             "so no stored document is replaced")
        stored = 0
        for fact in facts(run_id):
            item = {"content": fact["content"], "context": "gamedev-studio smoke test",
                    "metadata": provenance(run_id), "tags": fact["tags"]}
            stored += retain_one(base, names[fact["bank"]], item)
        rows.append(("S2 retain", "PASS" if stored == 4 else "FAIL", f"{stored}/4 retained over REST (sync)"))
    question = "Which colour palette does the game use?"
    alpha, beta = recall(base, names["alpha"], question), recall(base, names["beta"], question)
    isolated = "cobalt" in texts(alpha) and "amber" not in texts(alpha) \
        and "amber" in texts(beta) and "cobalt" not in texts(beta)
    rows.append(("S3 project isolation", "PASS" if isolated else "FAIL",
                 f"alpha={texts(alpha)[:80]!r} beta={texts(beta)[:80]!r}"))
    try:
        rows.append(("S4 MCP isolation", *check_mcp_isolation(base, names, run_id, question)))
    except SmokeError as exc:
        rows.append(("S4 MCP isolation", "FAIL", str(exc)))
    t1 = recall(base, names["alpha"], "How was the flicker fixed?", tags=["task:T1"], tags_match="any_strict")
    t2 = recall(base, names["alpha"], "How was the flicker fixed?", tags=["task:T2"], tags_match="any_strict")
    scoped = "flicker" in texts(t1) and not t2.get("results")
    rows.append(("S5 task scope", "PASS" if scoped else "FAIL",
                 f"task:T1 hits={len(t1.get('results', []))}, task:T2 hits={len(t2.get('results', []))}"))
    # Extracted facts (world, experience) keep the stored metadata; derived observations come back
    # with empty metadata, so provenance is checked on facts and the skill treats observations as hints.
    facts_only = {"types": ["world", "experience"]}
    alpha_facts = recall(base, names["alpha"], question, **facts_only)
    t1_facts = recall(base, names["alpha"], "How was the flicker fixed?", tags=["task:T1"],
                      tags_match="any_strict", **facts_only)
    observations = [r for r in alpha.get("results", []) + t1.get("results", []) if r.get("type") == "observation"]
    bare = sum(1 for r in observations if not r.get("metadata"))
    proven = has_provenance(alpha_facts, run_id) and has_provenance(t1_facts, run_id)
    rows.append(("S6 provenance", "PASS" if proven else "FAIL",
                 f"facts carry this run's {list(PROVENANCE_KEYS)}; {bare} of {len(observations)} derived "
                 "observations have no metadata (unverified hints)"))
    try:
        judged = [(kind, *judge_tools(mcp_tools(base, names[kind]), allowed)) for kind in ("studio", "alpha", "beta")]
        bad = [f"{kind}: {why}" for kind, result, why in judged if result != "PASS"]
        rows.append(("S7 MCP allowlist", "FAIL", "; ".join(bad)) if bad else
                    ("S7 MCP allowlist", "PASS", f"the studio, alpha and beta endpoints expose exactly {sorted(allowed)}"))
    except SmokeError as exc:
        rows.append(("S7 MCP allowlist", "FAIL", str(exc)))
    if recall_only and after_restart:
        studio = recall(base, names["studio"], "Who reviews each piece of work?")
        kept = f"rule {run_id}" in texts(studio) and "independent reviewer" in texts(studio) and isolated
        rows.append(("S8 persistence", "PASS" if kept else "FAIL",
                     f"run {run_id}'s facts recalled after a restart the operator confirmed (--after-restart)"))
    else:
        rows.append(("S8 persistence", "MANUAL",
                     f"restart the server, then run with --recall-only --after-restart --run {run_id}"))
    try:
        rows.append(("S9 MCP read tools", *check_read_tools(base, names)))
    except SmokeError as exc:
        rows.append(("S9 MCP read tools", "FAIL", str(exc)))
    return rows


def mcp_tools(base: str, bank: str) -> set[str]:
    answer = McpSession(endpoint(base, bank)).call("tools/list")
    return {tool["name"] for tool in answer.get("result", {}).get("tools", [])}


def server_version(base: str) -> str:
    try:
        status, _, raw = request(f"{base}/v1/version")
    except SmokeError:
        return "unknown"
    answer = as_json(raw)
    return str(answer.get("api_version")) if status == 200 and isinstance(answer, dict) else "unknown"


def evidence(rows, command: str, version: str, environment: str) -> list[dict]:
    """Rows in the shape of contracts/v1/integration-evidence.schema.json."""
    now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()
    return [{
        "integration_id": f"hindsight-{check.split()[0].lower()}",
        "capability": check.split(" ", 1)[1],
        "checked_at": now,
        "status": result.lower(),
        "version": version,
        "environment": environment,
        "command_redacted": command,
        "observed_result": observed,
        "recovery_test": "pass" if check.startswith("S8") and result == "PASS" else "not_run",
    } for check, result, observed in rows]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke test a Hindsight server (read the module docstring).")
    parser.add_argument("--url", default="http://127.0.0.1:8888")
    parser.add_argument("--prefix", default="gamedev-studio-smoke")
    parser.add_argument("--run", default=None, help="run id (2-16 lower-case letters or digits); reuse it only "
                                                    "with --recall-only")
    parser.add_argument("--recall-only", action="store_true", help="store nothing; check an earlier run's facts")
    parser.add_argument("--after-restart", action="store_true",
                        help="with --recall-only: the server was restarted since the store run (S8)")
    parser.add_argument("--json", action="store_true", help="print integration-evidence rows as JSON")
    parser.add_argument("--environment", default="local", help="environment for the evidence rows")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if args.recall_only and not args.run:
        print("ERROR: --recall-only needs the --run id of the earlier run", file=sys.stderr)
        return 2
    if args.after_restart and not args.recall_only:
        print("ERROR: --after-restart goes with --recall-only", file=sys.stderr)
        return 2
    run_id = args.run or uuid.uuid4().hex[:8]
    if not RUN_RE.match(run_id):
        print("ERROR: --run must be 2-16 lower-case letters or digits", file=sys.stderr)
        return 2
    base = args.url.rstrip("/")
    command = " ".join(["python scripts/hindsight_smoke.py", "--url", base, "--prefix", args.prefix, "--run", run_id]
                       + (["--recall-only"] if args.recall_only else [])
                       + (["--after-restart"] if args.after_restart else []))
    try:
        rows = run(base, args.prefix, run_id, args.recall_only, args.after_restart, allowed_tools())
    except SmokeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        rows_json = evidence(rows, command, server_version(base), args.environment)
        print(json.dumps({"run": run_id, "evidence": rows_json}, ensure_ascii=False, indent=2))
    else:
        print(f"run {run_id}")
        for check, result, observed in rows:
            print(f"{result:<7} {check}: {observed}")
    return 1 if any(result == "FAIL" for _, result, _ in rows) else 0


if __name__ == "__main__":
    from console_io import prepare_console
    prepare_console()
    sys.exit(main())
