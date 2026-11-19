#!/usr/bin/env python3
"""Assemble one brief for a worker agent from a piece card (Context Intelligence, light; DEC-102).

It only reads and writes one brief file; it never changes code. Stdlib only.

Inputs:
  --card FILE         the piece card (Markdown, e.g. a GitHub Issue body saved by /brief-piece) with
                      "Goal:", "Acceptance:" (numbered, each "Test:" or "Shot:"), "Owns:", "Depends:",
                      "Reviewer gate:" and an optional "Piece: <ID>" line
  --repo-root DIR     the game repository: owned files, the files they read, the review archive
  --decisions FILE    JSON list of decision issues ({number, title, url, body}) from
                      `gh issue list -R ZMSkif/GameDev-AGI-Studio --label decision --json number,title,url,body`
  --memories FILE     optional JSON recall answer from the project's Hindsight bank (memory skill)
  --ports FILE        optional JSON {"stream": [first, last], ...} of port ranges already in use
  --port-range A-B    the range this piece's agent will use
  --reviews DIR       the verbatim review archive (default <repo-root>/docs/reviews)
  --out FILE          where to write the brief; it must be outside --repo-root (DEC-002: no
                      tracked brief or status files)

It warns, in the brief, about what Cat Challenge learned the hard way:
  * a port range that overlaps one in use (the brief is refused, exit 3);
  * a backticked symbol in the card that no longer exists in the repository (a stale recipe);
  * notes that earlier reviews left for this piece ("For <ID>:" lines) are pulled in verbatim;
  * done means every acceptance line in the built game; a mockup is not done.
Exit codes: 0 brief written, 2 bad input, 3 refused (port clash).
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIELD_RE = re.compile(r"^\s*(?:[-*]\s*)?\**(Goal|Acceptance|Owns|Depends|Reviewer gate|Piece)\**\s*:\s*\**\s*(.*)$", re.I)
ACCEPTANCE_LINE_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+(.*\S)")
SYMBOL_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]{2,})(?:\(\))?`")
IMPORT_RES = (
    re.compile(r"""(?:from|import)\s*\(?\s*['"](\.{1,2}/[^'"]+)['"]"""),      # JS/TS relative imports
    re.compile(r"""require\(\s*['"](\.{1,2}/[^'"]+)['"]\s*\)"""),
    re.compile(r"""(?:preload|load)\(\s*["']res://([^"']+)["']\s*\)"""),        # GDScript
)
CODE_SUFFIXES = {".ts", ".tsx", ".js", ".mjs", ".jsx", ".py", ".gd", ".cs", ".json", ".css"}
STOPWORDS = set("the a an and or of to in on for with by from is are be this that it its at as into only "
                "each every one two any all not no new piece game games player players".split())
CORE_DECISIONS = (1, 16, 40)   # branch + PR, no invented results, independent review (issue numbers)
DONE_RULE = ("Done means every acceptance line below is met in the built game and shown by its own "
             "evidence (test output or a screenshot of the build). A mockup, concept or plan is not done.")


class BriefError(Exception):
    """Bad input: the card or a file cannot be used."""


class Refused(Exception):
    """The brief must not be issued (for example a port clash)."""


def parse_card(text: str) -> dict:
    card = {"goal": "", "acceptance": [], "owns": [], "depends": "", "reviewer_gate": "", "piece": "",
            "title": ""}
    current = None
    for line in text.splitlines():
        if not card["title"] and line.startswith("#"):
            card["title"] = line.lstrip("#").strip()
            continue
        field = FIELD_RE.match(line)
        if field:
            name, rest = field.group(1).lower(), field.group(2).strip()
            current = {"goal": "goal", "acceptance": "acceptance", "owns": "owns", "depends": "depends",
                       "reviewer gate": "reviewer_gate", "piece": "piece"}[name]
            if current == "owns" and rest:
                card["owns"] += [p.strip(" `.") for p in re.split(r"[,;]", rest) if p.strip(" `.")]
            elif current == "acceptance" and rest:
                card["acceptance"].append(rest)
            elif current in ("goal", "depends", "reviewer_gate", "piece"):
                card[current] = rest
            continue
        item = ACCEPTANCE_LINE_RE.match(line)
        if current == "acceptance" and item:
            card["acceptance"].append(item.group(1))
        elif current == "owns" and item:
            card["owns"] += [p.strip(" `.") for p in re.split(r"[,;]", item.group(1)) if p.strip(" `.")]
        elif current in ("goal", "reviewer_gate") and line.strip():
            card[current] = (card[current] + " " + line.strip()).strip()
    if not card["goal"] or not card["acceptance"] or not card["owns"]:
        raise BriefError("the card needs Goal, numbered Acceptance lines and an Owns list")
    if not card["piece"]:
        match = re.match(r"\[?([A-Z][A-Z0-9-]*\d)\]?", card["title"])
        card["piece"] = match.group(1) if match else ""
    return card


def keywords(*texts: str) -> set[str]:
    words = set()
    for text in texts:
        for word in re.findall(r"[a-zа-яё][a-zа-яё0-9-]{2,}", text.lower()):
            if word not in STOPWORDS:
                words.add(word)
    return words


def check_ports(requested: str | None, registry: dict | None, piece: str) -> list[str]:
    """Refuse a range that overlaps one already in use; return notes otherwise."""
    if not requested:
        return ["No port range given: ask the coordinator for one before starting any server."]
    match = re.fullmatch(r"(\d{2,5})-(\d{2,5})", requested)
    if not match:
        raise BriefError(f"--port-range must look like 5300-5302, got {requested!r}")
    first, last = int(match.group(1)), int(match.group(2))
    if first > last:
        raise BriefError("--port-range: first port is above the last")
    for stream, span in (registry or {}).items():
        lo, hi = int(span[0]), int(span[1])
        if stream != piece and first <= hi and lo <= last:
            raise Refused(f"port range {first}-{last} overlaps {stream} ({lo}-{hi}); pick a free range")
    return [f"Use only ports {first}-{last}; stop every server you start before you report."]


def expand_owned(root: Path, owns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in owns:
        pattern = pattern.replace("\\", "/").rstrip("/")
        if pattern.endswith("/**"):
            base = root / pattern[:-3]
            files += sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []
        elif any(ch in pattern for ch in "*?["):
            files += sorted(p for p in root.glob(pattern) if p.is_file())
        elif (root / pattern).is_file():
            files.append(root / pattern)
        elif (root / pattern).is_dir():
            files += sorted(p for p in (root / pattern).rglob("*") if p.is_file())
    seen, unique = set(), []
    for path in files:
        if path not in seen and ".git" not in path.parts and "node_modules" not in path.parts:
            seen.add(path)
            unique.append(path)
    return unique


def reads_of(root: Path, files: list[Path]) -> list[str]:
    """Files the owned files import (relative imports and Godot res:// loads)."""
    found: set[str] = set()
    owned = {p.resolve() for p in files}
    for path in files:
        if path.suffix not in CODE_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern in IMPORT_RES:
            for target in pattern.findall(text):
                base = root if pattern is IMPORT_RES[2] else path.parent
                candidate = (base / target).resolve()
                options = [candidate] + [candidate.with_name(candidate.name + s) for s in (".ts", ".tsx", ".js", ".mjs")]
                options += [candidate / f"index{s}" for s in (".ts", ".js")]
                for option in options:
                    if option.is_file() and option not in owned:
                        try:
                            found.add(option.relative_to(root.resolve()).as_posix())
                        except ValueError:
                            pass
                        break
    return sorted(found)


def stale_symbols(root: Path, card_text: str) -> list[str]:
    """Backticked identifiers in the card that no source file contains any more."""
    symbols = sorted(set(SYMBOL_RE.findall(card_text)))
    if not symbols:
        return []
    corpus: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in CODE_SUFFIXES and ".git" not in path.parts \
                and "node_modules" not in path.parts:
            try:
                corpus.append(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    text = "\n".join(corpus)
    return [s for s in symbols if not re.search(rf"\b{re.escape(s)}\b", text)]


def review_notes(reviews: Path, piece: str, owned_paths: list[str]) -> list[tuple[str, str]]:
    """Lines earlier verdicts addressed to this piece ("For <ID>:") or to its owned files."""
    notes: list[tuple[str, str]] = []
    if not reviews.is_dir():
        return notes
    tails = {p.rsplit("/", 1)[-1] for p in owned_paths if "." in p.rsplit("/", 1)[-1]}
    for path in sorted(reviews.glob("*.md")):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            addressed = piece and re.search(rf"\*{{0,2}}For {re.escape(piece)}\b", line)
            if addressed:
                block = [line.strip()]
                for follow in lines[index + 1:index + 12]:
                    if not follow.strip() or re.match(r"^\s*(?:-\s+)?\*\*For [A-Z]", follow) or follow.startswith("#"):
                        break
                    block.append(follow.strip())
                notes.append((path.name, " ".join(block)))
            elif tails and any(t in line for t in tails) and re.search(r"must|block|fix", line, re.I):
                notes.append((path.name, line.strip()))
    return notes[:40]


def pick_decisions(decisions: list[dict], words: set[str], limit: int = 12) -> list[dict]:
    scored = []
    for issue in decisions:
        title_words = keywords(issue.get("title", ""))
        score = len(words & title_words) * 3 + len(words & keywords(issue.get("body", "")[:600]))
        if issue.get("number") in CORE_DECISIONS:
            score += 100
        if score:
            scored.append((score, issue.get("number", 0), issue))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [issue for _, _, issue in scored[:limit]]


def pick_skills(plugin_root: Path, words: set[str], limit: int = 5) -> list[tuple[str, str]]:
    scored = []
    for skill in sorted((plugin_root / "skills").glob("*/SKILL.md")):
        head = skill.read_text(encoding="utf-8").split("---", 2)
        description = head[1] if len(head) > 2 else ""
        match = re.search(r"description:\s*(.*)", description)
        text = match.group(1) if match else ""
        score = len(words & keywords(text))
        if skill.parent.name == "studio-rules":
            score += 100
        if score:
            scored.append((score, skill.parent.name, text))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [(name, text[:140]) for _, name, text in scored[:limit]]


def usable_memories(answer: dict | None) -> list[dict]:
    """Recalled facts that carry provenance; observations and bare facts are dropped."""
    keep = []
    for result in (answer or {}).get("results", []):
        meta = result.get("metadata") or {}
        if result.get("type") in ("world", "experience") and meta.get("source") and meta.get("source_rev"):
            keep.append(result)
    return keep


def render(card, decisions, skills, owned, reads, stale, notes, memories, port_notes, root: Path) -> str:
    out = [f"# Brief: {card['title'] or card['piece']}", ""]
    out += ["## Goal", card["goal"], ""]
    out += ["## Rules", "- Apply the `studio-rules` skill first; decisions bind (DEC-003).",
            "- Work only in your own worktree and branch; commit as you go (a restart loses uncommitted work);"
            " never push.", *[f"- {n}" for n in port_notes],
            "- Ask the coordinator in one message when blocked; never guess an owner decision (DEC-004).", ""]
    out += ["## Definition of done", DONE_RULE]
    for number, line in enumerate(card["acceptance"], 1):
        flag = ""
        if not re.match(r"\s*(Test|Shot)\s*:", line, re.I):
            flag = "  ⚠ no Test:/Shot: evidence named"
        elif re.search(r"\b(mockup|mock-up|concept|plan)\b", line, re.I):
            flag = "  ⚠ points at a mockup or concept; done needs the built game"
        out.append(f"{number}. {line}{flag}")
    owned_lines = [f"- `{p.relative_to(root).as_posix()}`" for p in owned] \
        or [f"- `{p}` (does not exist yet)" for p in card["owns"]]
    out += ["", "## Owns (change only these)", *owned_lines]
    out += ["", "## Reads (do not change)", *([f"- `{r}`" for r in reads] or ["- (no imports found)"])]
    if card["depends"]:
        out += ["", "## Depends", card["depends"]]
    if card["reviewer_gate"]:
        out += ["", "## Reviewer gate", card["reviewer_gate"]]
    out += ["", "## Decisions", *[f"- #{d.get('number')} {d.get('title')} {d.get('url', '')}".rstrip()
                                  for d in decisions]]
    out += ["", "## Skills", *[f"- `{name}`: {text}" for name, text in skills]]
    if stale:
        out += ["", "## ⚠ Stale references", "These names from the card exist nowhere in the repository at HEAD."
                " Do not apply a recipe that uses them; ask the coordinator:", *[f"- `{s}`" for s in stale]]
    if notes:
        out += ["", "## Notes from earlier reviews (verbatim)", *[f"- {line} ({name})" for name, line in notes]]
    if memories:
        out += ["", "## Memories (verify before use; the source wins, DEC-103)",
                *[f"- {m.get('text')} — source: {m['metadata'].get('source')} @ {m['metadata'].get('source_rev')}"
                  f" (verified: {m['metadata'].get('verified', 'false')})" for m in memories]]
    out += ["", "## Report", "The first 400 characters say what was done and where (branch, commit); then files,"
            " numbers, evidence paths, what you could not check."]
    return "\n".join(out) + "\n"


def load_json(path: str | None, what: str):
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BriefError(f"{what}: cannot read {path}: {exc}") from exc


def build(args) -> str:
    root = Path(args.repo_root).resolve()
    if not root.is_dir():
        raise BriefError(f"--repo-root {root} is not a folder")
    out = Path(args.out).resolve()
    if root == out or root in out.parents:
        raise BriefError("--out must be outside the game repository (DEC-002: no tracked brief files)")
    card_text = Path(args.card).read_text(encoding="utf-8")
    card = parse_card(card_text)
    port_notes = check_ports(args.port_range, load_json(args.ports, "--ports"), card["piece"])
    words = keywords(card["title"], card["goal"], " ".join(card["acceptance"]), card["reviewer_gate"])
    decisions = pick_decisions(load_json(args.decisions, "--decisions") or [], words)
    skills = pick_skills(Path(args.plugin_root), words)
    owned = expand_owned(root, card["owns"])
    reads = reads_of(root, owned)
    stale = stale_symbols(root, card_text)
    reviews = Path(args.reviews) if args.reviews else root / "docs" / "reviews"
    notes = review_notes(reviews, card["piece"], [p.relative_to(root).as_posix() for p in owned] + card["owns"])
    memories = usable_memories(load_json(args.memories, "--memories"))
    return render(card, decisions, skills, owned, reads, stale, notes, memories, port_notes, root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble a worker brief from a piece card (read the docstring).")
    parser.add_argument("--card", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--decisions")
    parser.add_argument("--memories")
    parser.add_argument("--ports")
    parser.add_argument("--port-range")
    parser.add_argument("--reviews")
    parser.add_argument("--plugin-root", default=str(PLUGIN_ROOT))
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        brief = build(args)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    except (BriefError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(brief, encoding="utf-8", newline="\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
