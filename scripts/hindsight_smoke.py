#!/usr/bin/env python3
"""Real smoke test of a Hindsight server for the gamedev-studio memory layer (DEC-042, DEC-046).

It talks to a running server over HTTP (stdlib only) and prints a PASS / FAIL / MANUAL / UNKNOWN
matrix (DEC-120); with --json each row has the shape of contracts/v1/integration-evidence.schema.json.
It never deletes anything: memory is kept until the owner deletes it (DEC-138), so the test banks
it creates stay and are named `<prefix>::...` for the owner to remove.

Checks:
  S1 health            the server answers and its database is connected
  S2 retain            facts are stored with provenance metadata and scope tags
  S3 project isolation a fact retained in one project bank is not recalled from another (DEC-101)
  S4 MCP isolation     the per-bank MCP endpoint of one project cannot reach another project's facts
  S5 task scope        task memories are found by their task tag and not by another task's tag
  S6 provenance        recalled facts carry the provenance metadata they were stored with
  S7 MCP allowlist     the per-bank MCP endpoint exposes exactly the allowed tools, so no delete,
                       clear or unsourced reflect tool (DEC-138, provenance_required)
  S8 persistence       with --recall-only after a server restart, the facts are still recalled

Usage:
  python scripts/hindsight_smoke.py [--url http://127.0.0.1:8888] [--prefix gamedev-studio-smoke]
                                    [--run RUN_ID] [--recall-only] [--json]
                                    [--allow-tools retain,recall,list_memories,get_memory,get_bank]
Exit codes: 0 no FAIL, 1 at least one FAIL, 2 bad arguments or the server is unreachable.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import urllib.error
import urllib.request
import uuid

# The per-bank tools the plugin allows (contracts/v1/knowledge-policy.json memory_backend.mcp_enabled_tools).
# `reflect` is left out: its answers come back without sources (based_on is null), against
# provenance_required. Any tool outside this set on the endpoint is a FAIL, not only known delete names.
ALLOWED_TOOLS = ("retain", "recall", "list_memories", "get_memory", "get_bank")
REQUIRED_TOOLS = {"retain", "recall"}
PROVENANCE_KEYS = ("source_type", "source", "source_rev", "recorded_by", "verified")


class SmokeError(RuntimeError):
    """The server could not be reached or answered with something unusable."""


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


def banks(prefix: str, run: str) -> dict[str, str]:
    """Studio bank, two project banks; tasks are tags inside a project bank (DEC-101)."""
    return {
        "studio": f"{prefix}::studio",
        "alpha": f"{prefix}::project::alpha-{run}",
        "beta": f"{prefix}::project::beta-{run}",
    }


def provenance(source: str, rev: str) -> dict[str, str]:
    return {"source_type": "smoke-test", "source": source, "source_rev": rev,
            "recorded_by": "gamedev-studio:hindsight_smoke", "verified": "false"}


def facts(run: str) -> list[dict]:
    """Facts with unique tokens, so a recall shows where an answer came from."""
    return [
        {"bank": "studio", "content": f"Studio rule {run}: every piece of work gets an independent reviewer.",
         "tags": ["scope:studio"]},
        {"bank": "alpha", "content": f"The alpha game {run} uses the cobalt-lantern colour palette.",
         "tags": ["scope:project"]},
        {"bank": "beta", "content": f"The beta game {run} uses the amber-kite colour palette.",
         "tags": ["scope:project"]},
        {"bank": "alpha", "content": f"Task T1 of {run} fixed the lantern flicker by lifting the overlay 2 mm.",
         "tags": ["scope:task", "task:T1"]},
    ]


def texts(recall_body: dict) -> str:
    return " ".join(str(r.get("text", "")) for r in recall_body.get("results", [])).lower()


def has_provenance(recall_body: dict) -> bool:
    results = recall_body.get("results", [])
    return bool(results) and all(
        isinstance(r.get("metadata"), dict) and all(k in r["metadata"] for k in PROVENANCE_KEYS)
        for r in results)


def parse_mcp(raw: str, content_type: str) -> dict:
    """A JSON-RPC answer, sent as plain JSON or as one server-sent event."""
    if "text/event-stream" in (content_type or ""):
        for line in raw.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        raise SmokeError("MCP answer had no data line")
    return json.loads(raw)


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


def mcp_tools(base: str, bank: str) -> set[str]:
    answer = McpSession(f"{base}/mcp/{bank}/").call("tools/list")
    return {tool["name"] for tool in answer.get("result", {}).get("tools", [])}


def mcp_recall_text(base: str, bank: str, query: str) -> str:
    """What a per-bank MCP endpoint returns for a recall, as lower-case text."""
    answer = McpSession(f"{base}/mcp/{bank}/").call("tools/call", {"name": "recall", "arguments": {"query": query}})
    return json.dumps(answer.get("result", {}), ensure_ascii=False).lower()


def judge_tools(tools: set[str], allowed: set[str]) -> tuple[str, str]:
    missing = sorted(REQUIRED_TOOLS - tools)
    extra = sorted(tools - allowed)
    if missing or extra:
        return "FAIL", f"missing {missing}; outside the allowlist {extra}"
    return "PASS", f"exactly the allowed tools: {sorted(tools)}"


def recall(base: str, bank: str, query: str, **extra) -> dict:
    body = {"query": query, "budget": "mid", "max_tokens": 2048}
    body.update(extra)
    status, _, raw = request(f"{base}/v1/default/banks/{bank}/memories/recall", "POST", body)
    if status != 200:
        raise SmokeError(f"recall {bank}: HTTP {status}: {raw[:200]}")
    return json.loads(raw)


def run(base: str, prefix: str, run_id: str, recall_only: bool, allowed: set[str]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    status, _, raw = request(f"{base}/health")
    healthy = status == 200 and json.loads(raw).get("database") == "connected"
    rows.append(("S1 health", "PASS" if healthy else "FAIL", raw[:120]))
    if not healthy:
        return rows
    names = banks(prefix, run_id)
    if recall_only:
        rows.append(("S2 retain", "UNKNOWN", "not run in --recall-only mode"))
    else:
        stored = 0
        for index, fact in enumerate(facts(run_id)):
            item = {"content": fact["content"], "context": "gamedev-studio smoke test",
                    "metadata": provenance("scripts/hindsight_smoke.py", run_id), "tags": fact["tags"],
                    "document_id": f"smoke-{run_id}-{index}"}
            status, _, _ = request(f"{base}/v1/default/banks/{names[fact['bank']]}/memories", "POST",
                                   {"items": [item]}, timeout=600)
            stored += status == 200
        rows.append(("S2 retain", "PASS" if stored == 4 else "FAIL", f"{stored}/4 retained over REST (sync)"))
    question = "Which colour palette does the game use?"
    alpha, beta = recall(base, names["alpha"], question), recall(base, names["beta"], question)
    isolated = "cobalt" in texts(alpha) and "amber" not in texts(alpha) \
        and "amber" in texts(beta) and "cobalt" not in texts(beta)
    rows.append(("S3 project isolation", "PASS" if isolated else "FAIL",
                 f"alpha={texts(alpha)[:80]!r} beta={texts(beta)[:80]!r}"))
    try:
        via_mcp = mcp_recall_text(base, names["alpha"], question)
        mcp_isolated = "cobalt" in via_mcp and "amber" not in via_mcp
        rows.append(("S4 MCP isolation", "PASS" if mcp_isolated else "FAIL",
                     "the alpha per-bank endpoint returns alpha facts only (the multi-bank /mcp/ endpoint "
                     "takes any bank_id, so the plugin wires one endpoint per bank)"))
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
    rows.append(("S6 provenance", "PASS" if has_provenance(alpha_facts) and has_provenance(t1_facts) else "FAIL",
                 f"facts carry {list(PROVENANCE_KEYS)}; {bare} of {len(observations)} derived observations "
                 "have no metadata (unverified hints)"))
    try:
        rows.append(("S7 MCP allowlist", *judge_tools(mcp_tools(base, names["studio"]), allowed)))
    except SmokeError as exc:
        rows.append(("S7 MCP allowlist", "FAIL", str(exc)))
    if recall_only:
        studio = recall(base, names["studio"], "Who reviews each piece of work?")
        kept = "independent reviewer" in texts(studio) and isolated
        rows.append(("S8 persistence", "PASS" if kept else "FAIL",
                     f"facts of run {run_id} recalled by a later run; this proves persistence only if the "
                     "server was restarted in between"))
    else:
        rows.append(("S8 persistence", "MANUAL", f"restart the server, then run with --recall-only --run {run_id}"))
    return rows


def evidence(rows, base: str, version: str, environment: str) -> list[dict]:
    """Rows in the shape of contracts/v1/integration-evidence.schema.json."""
    now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()
    return [{
        "integration_id": f"hindsight-{check.split()[0].lower()}",
        "capability": check.split(" ", 1)[1],
        "checked_at": now,
        "status": result.lower(),
        "version": version,
        "environment": environment,
        "command_redacted": f"python scripts/hindsight_smoke.py --url {base}",
        "observed_result": observed,
        "recovery_test": "pass" if check.startswith("S8") and result == "PASS" else "not_run",
    } for check, result, observed in rows]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke test a Hindsight server (read the module docstring).")
    parser.add_argument("--url", default="http://127.0.0.1:8888")
    parser.add_argument("--prefix", default="gamedev-studio-smoke")
    parser.add_argument("--run", default=None, help="run id; reuse it with --recall-only")
    parser.add_argument("--recall-only", action="store_true", help="store nothing; check earlier facts")
    parser.add_argument("--allow-tools", default=",".join(ALLOWED_TOOLS), help="comma-separated MCP allowlist")
    parser.add_argument("--json", action="store_true", help="print integration-evidence rows as JSON")
    parser.add_argument("--version", default="hindsight-api", help="server version for the evidence rows")
    parser.add_argument("--environment", default="local", help="environment for the evidence rows")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if args.recall_only and not args.run:
        print("ERROR: --recall-only needs the --run id of the earlier run", file=sys.stderr)
        return 2
    run_id = args.run or uuid.uuid4().hex[:8]
    allowed = {t.strip() for t in args.allow_tools.split(",") if t.strip()}
    base = args.url.rstrip("/")
    try:
        rows = run(base, args.prefix, run_id, args.recall_only, allowed)
    except SmokeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"run": run_id, "evidence": evidence(rows, base, args.version, args.environment)},
                         ensure_ascii=False, indent=2))
    else:
        print(f"run {run_id}")
        for check, result, observed in rows:
            print(f"{result:<7} {check}: {observed}")
    return 1 if any(result == "FAIL" for _, result, _ in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
