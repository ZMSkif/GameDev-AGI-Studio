#!/usr/bin/env python3
"""The studio memory as a stdio MCP server that the plugin starts with every Claude Code session.

It sits in front of the person's own Hindsight server (scripts/memory_server.py, 127.0.0.1:8888) and:
  * is always "connected", even when Hindsight is not installed or not running yet, so the person never
    sees a failed connector; the first call then says what is missing, and starts the server if it is
    installed;
  * keeps one upstream MCP endpoint per bank (contracts/v1/knowledge-policy.json, DEC-101): the
    ``studio_*`` tools reach only ``gamedev-studio::studio`` and the ``project_*`` tools only the bank of
    the studio game this session runs in (the nearest folder with the ``.gamedev-studio`` marker);
    a ``bank_id`` argument is dropped, so no call can reach another game's bank, and ``document_id`` and
    ``update_mode`` are dropped, because they make Hindsight replace (delete) earlier memories;
  * forwards only the contract's tools (retain, recall, list_memories, get_memory, get_bank): there is
    no delete or clear (DEC-138).
Stdlib only; JSON-RPC over stdin/stdout, one message per line; diagnostics go to stderr.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import threading
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_server as ms  # noqa: E402

PROTOCOL = "2025-06-18"
VERSION = "1"
MARKER = ".gamedev-studio"
PREFIXES = {"studio_": "studio", "project_": "project"}
INSTRUCTIONS = (
    "GameDev Studio memory (Hindsight), the `memory` skill's rules apply. studio_* tools use the studio bank "
    "(lessons for every game); project_* tools use only this game's bank. Memory is a pointer, never the "
    "source of truth: decisions and approved documents win (DEC-103). Every retain needs metadata with "
    "source_type, source, source_rev, recorded_by and verified; never store secrets, personal data or "
    "transcripts; never pass document_id or update_mode. Recall facts with types [\"world\", \"experience\"]."
)
# Argument schemas of Hindsight's per-bank MCP tools, recorded from the pinned version (see that file).
SCHEMAS = json.loads((Path(__file__).resolve().parent / "memory_tool_schemas.json").read_text(encoding="utf-8"))["tools"]
# Never forwarded: bank_id could reach another game's bank; document_id or update_mode replace and so delete
# earlier memories (memory skill, DEC-138).
FORBIDDEN_ARGUMENTS = {"bank_id", "document_id", "update_mode"}


def log(text):
    print(f"[gamedev-studio memory] {text}", file=sys.stderr, flush=True)


def studio_game(start=None):
    """The studio game folder this session runs in, or None outside one."""
    base = start or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    current = Path(base).resolve()
    for folder in (current, *current.parents):
        if (folder / MARKER).is_file():
            return folder
    return None


def bank_for(scope, game):
    if scope == "studio":
        return ms.STUDIO_BANK
    return ms.PROJECT_BANK.format(repository=ms.repository_name(game)) if game else None


def tool_list():
    tools = []
    for prefix, scope in PREFIXES.items():
        where = "the studio bank (every game)" if scope == "studio" else "this game's own bank"
        for name in ms.MCP_TOOLS:
            tools.append({"name": prefix + name, "description": f"Hindsight {name} in {where}.",
                          "inputSchema": SCHEMAS[name]})
    return tools


class Upstream:
    """A streamable-HTTP MCP session to one per-bank Hindsight endpoint."""

    def __init__(self, bank):
        self.url = f"{ms.URL}/mcp/{bank}/"
        self.headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
        self.next_id = 0
        self.ready = False

    def post(self, body, timeout=120):
        request = urllib.request.Request(self.url, data=json.dumps(body).encode("utf-8"), method="POST",
                                         headers=self.headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            session = response.headers.get("Mcp-Session-Id")
            kind = response.headers.get("Content-Type", "")
        if session:
            self.headers["Mcp-Session-Id"] = session
        if not raw.strip():
            return {}
        if "text/event-stream" in kind:
            for line in raw.splitlines():
                if line.startswith("data:"):
                    return json.loads(line[5:].strip())
            return {}
        return json.loads(raw)

    def call(self, method, params):
        self.next_id += 1
        return self.post({"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params})

    def open(self):
        self.headers.pop("Mcp-Session-Id", None)
        self.call("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                 "clientInfo": {"name": "gamedev-studio-memory", "version": VERSION}})
        self.post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.ready = True

    def tool(self, name, arguments):
        for attempt in (1, 2):
            try:
                if not self.ready:
                    self.open()
                answer = self.call("tools/call", {"name": name, "arguments": arguments})
                if "error" in answer and attempt == 1:
                    self.ready = False  # an expired session after a server restart: open a new one once
                    continue
                return answer
            except (urllib.error.URLError, OSError, ValueError):
                self.ready = False
                if attempt == 2:
                    raise
        return answer


class Memory:
    def __init__(self):
        self.upstreams = {}
        self.game = studio_game()

    def text(self, message, error=True):
        return {"content": [{"type": "text", "text": message}], "isError": error}

    def unavailable(self):
        state = ms.health()
        if state == "hindsight":
            return None
        if state == "other":
            return self.text(f"Memory is unavailable: port {ms.PORT} is used by another program.")
        if not ms.find_runtime():
            return self.text("Memory (Hindsight) is not installed on this computer. Offer it to the person "
                             "with /gamedev-studio:setup-tools; until then work without memory (Manual mode).")
        code = ms.start(out=lambda line: None)
        return self.text("The memory server is starting (the first start can take a few minutes). "
                         "Go on with the task and try the memory call again in about a minute."
                         if code == 0 else "The memory server did not start; see " + str(ms.log_file()))

    def call(self, name, arguments):
        prefix = next((p for p in PREFIXES if name.startswith(p)), None)
        tool = name[len(prefix):] if prefix else ""
        if not prefix or tool not in ms.MCP_TOOLS:
            return self.text(f"Unknown memory tool: {name}")
        bank = bank_for(PREFIXES[prefix], self.game)
        if not bank:
            return self.text("This session is not inside a GameDev Studio game (no .gamedev-studio marker), "
                             "so there is no project memory here; the studio_* tools still work.")
        blocked = self.unavailable()
        if blocked:
            return blocked
        arguments = {key: value for key, value in (arguments or {}).items() if key not in FORBIDDEN_ARGUMENTS}
        upstream = self.upstreams.setdefault(bank, Upstream(bank))
        try:
            answer = upstream.tool(tool, arguments)
        except (urllib.error.URLError, OSError, ValueError) as error:
            return self.text(f"Memory call failed: {error}")
        if "error" in answer:
            return self.text(f"Memory error: {answer['error'].get('message', answer['error'])}")
        return answer.get("result") or self.text("Memory returned no result.")


def warm_up():
    """Start the server when Claude starts, if it is installed and not running, so memory is ready soon."""
    try:
        if ms.find_runtime() and ms.health() is None:
            ms.start(out=lambda line: None)
    except Exception as error:  # never break the MCP session over a start attempt
        log(f"start failed: {error}")


def handle(memory, message):
    method, ident = message.get("method"), message.get("id")
    if ident is None:
        return None  # a notification
    if method == "initialize":
        result = {"protocolVersion": message.get("params", {}).get("protocolVersion") or PROTOCOL,
                  "capabilities": {"tools": {}}, "instructions": INSTRUCTIONS,
                  "serverInfo": {"name": "gamedev-studio-memory", "version": VERSION}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": tool_list()}
    elif method == "tools/call":
        params = message.get("params", {})
        result = memory.call(params.get("name", ""), params.get("arguments") or {})
    else:
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": ident, "result": result}


def serve(stdin=sys.stdin, stdout=sys.stdout):
    memory = Memory()
    threading.Thread(target=warm_up, daemon=True).start()
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            continue
        reply = handle(memory, message) if isinstance(message, dict) else None
        if reply is not None:
            stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            stdout.flush()


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout):
        stream.reconfigure(encoding="utf-8", errors="replace", newline="\n" if stream is sys.stdout else None)
    serve()
