---
name: memory
description: Long-term studio and project memory through Hindsight over MCP (DEC-024) - which bank and tags to use for the studio, project and task scopes, what to store and never store, provenance on every memory, the four retrieval modes, why approved decisions and documents always win over memory, and how to start, connect and verify the server. Use before storing or recalling a lesson, a recurring failure or a decision's provenance, when wiring Hindsight into a game repository, or when a memory contradicts a source.
---

# Memory (Hindsight)

Binding: DEC-024 (#24) memory is retrievable, never authoritative; DEC-101 (#102) studio, project and task levels; DEC-102 (#103) only relevant sources, with revision and provenance; DEC-103 (#104) the approved source of truth wins over memory; DEC-104 (#106) Auto, Always Verify, Memory First and Manual; DEC-138 (#140) memory stays until the owner deletes it; DEC-019 (#19), DEC-085 (#86) no paid API; DEC-090 (#91) no secrets in prompts or stores. The contract is `contracts/v1/knowledge-policy.json`.

**Status (19.11.2026):** Hindsight 1.2.2 passed a local smoke test on the owner's PC (`scripts/hindsight_smoke.py`). Where the server finally runs, this PC or a server, is the owner's choice (task #150). Until then use the local server, and never change another machine.

## 1. Banks and scopes

| Scope | Where | Example |
|---|---|---|
| studio | bank `gamedev-studio::studio` | "Every piece gets its own reviewer; mutants catch tests that cannot fail." |
| project | bank `gamedev-studio::project::<repository>` | "In cat-challenge the round-3 lesson runs inside the first show." |
| task | the project bank, tag `task:<issue number>` | "Issue 42: the collar spike came from an unbisected border." |

- Add a scope tag to every memory (`scope:studio`, `scope:project`, `scope:task`).
- **One MCP endpoint per bank.** The multi-bank endpoint `/mcp/` accepts any `bank_id`, so a session there can read other games. The smoke test showed it. Wire only per-bank endpoints into a game.

## 2. Connect a game repository (each step needs the owner's yes)

The owner gives the base URL (`<base>`; the local smoke server is `http://127.0.0.1:8888`).

- **Claude Code**, in the game repository:
  - `claude mcp add --transport http --scope project hindsight-project <base>/mcp/gamedev-studio::project::<repository>/`
  - `claude mcp add --transport http --scope project hindsight-studio <base>/mcp/gamedev-studio::studio/`
- **Codex**, in the trusted project's `.codex/config.toml`:
  - `[mcp_servers.hindsight-project]` with `url = "<base>/mcp/gamedev-studio::project::<repository>/"`
  - the same for `hindsight-studio`.
- **Do not use** the `@vectorize-io/hindsight-coding-agents` installer. Its default stores whole session transcripts, which breaks the never-store list below.
- If the server is down, Claude Code marks the server "failed" and the session goes on. Say so in the result; do not work around it.

## 3. Store (retain)

Store only what helps later work and is backed by a source:
- a verified lesson, with the review files and commits that show it;
- a pointer to a decision's provenance: the issue number and the line that matters, never a copy that could drift;
- a recurring failure class (`lessons` skill);
- a piece's outcome, with its review verdict file.

Every retain carries `metadata` with `source_type`, `source` (file, issue or commit), `source_rev` (commit or date), `recorded_by` (role) and `verified` (`"false"` unless a reviewer confirmed it). It also carries the scope tags. A memory without provenance is not stored.

**Never store:**
- secrets, tokens, keys or passwords;
- personal data, such as names, e-mail addresses or local user paths;
- unverified claims written as facts;
- whole transcripts;
- copyrighted text.

Before a retain, check the content as `scripts/archive_reviews.py` checks a verdict: secret patterns and the project's `--forbid` patterns. Retain over MCP is asynchronous, so a recall right after it can come back empty; recall again after about 20 s.

## 4. Recall and the four modes

| Mode | When | What to do |
|---|---|---|
| **Auto** (default) | normal work | Recall, then check every memory you act on against its source before relying on it. |
| **Always Verify** | decisions, money, publishing, anything risky | Recall only as a pointer; read the source (issue, file, commit) itself; act only on the source. |
| **Memory First** | low-risk recall of studio practice | Use the memory directly, still showing its provenance, and say it is from memory. |
| **Manual** | the owner asked for it, or no memory server is wired | Do not recall; ask the owner. |

- Recall facts with `types: ["world", "experience"]`. Derived observations come back without provenance, so they are hints, never evidence.
- `reflect` is not used: its answers carry no sources, and the server's MCP allowlist leaves it out.
- **The approved source of truth always wins** (DEC-103). That means the decision issues, then the approved GDD, Art Bible and architecture, then memory. When a memory contradicts a source, follow the source. Report the stale memory to the owner; never delete or "fix" it yourself.

## 5. Running the server (local)

```
HINDSIGHT_API_LLM_PROVIDER=claude-code HINDSIGHT_API_HOST=127.0.0.1 HINDSIGHT_API_PORT=8888 \
HINDSIGHT_API_MODEL_INIT_TIMEOUT=900 \
HINDSIGHT_API_MCP_ENABLED_TOOLS=retain,recall,list_memories,get_memory,get_bank \
~/.hindsight-runtime/Scripts/hindsight-api --host 127.0.0.1 --port 8888
```

- Bind to 127.0.0.1. The default is 0.0.0.0 with an unauthenticated MCP endpoint.
- The `claude-code` provider uses the owner's Claude subscription (no API key). The `openai-codex` provider or a local Ollama model are the other no-paid-API options.
- The first start downloads the search models from Hugging Face. It can take longer than the default 300 s init timeout.
- After any change, run `python scripts/hindsight_smoke.py`. With `--json` it prints rows for `contracts/v1/integration-evidence.schema.json`.

## 6. Deleting

Only the owner deletes memory, from the control plane or the admin CLI (DEC-138). Agents never call delete or clear tools, even on smoke banks, and never send DELETE to the REST API, which is open on localhost. If memory must go, ask the owner and name the bank and the memories.

## Source

Hindsight docs at hindsight.vectorize.io (installation, models, MCP server, configuration, memories API; read 19.11.2026). Smoke test on the owner's PC, 19.11.2026, `scripts/hindsight_smoke.py`: S1–S8 PASS, Claude Code and Codex both read and write one bank over MCP, the multi-bank endpoint crosses banks, observations and reflect carry no sources.
