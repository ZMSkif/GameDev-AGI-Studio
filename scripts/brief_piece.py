#!/usr/bin/env python3
"""Assemble one brief for a worker agent from a piece card (Context Intelligence, light; DEC-102).

It only reads and writes one brief file; it never changes code. Stdlib only.

Inputs:
  --card FILE         the piece card (Markdown, e.g. a GitHub Issue body saved by /brief-piece) with
                      "Goal:", "Acceptance:" (numbered, each "Test:" or "Shot:"), "Owns:", "Depends:",
                      "Reviewer gate:" and an optional "Piece: <ID>" line
  --card-source TEXT  where the card came from, such as "issue #42 updated 2026-11-19T10:00Z"
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
  * a port range that overlaps one in use, even by one port (the brief is refused, exit 3);
  * a backticked name in the card that nothing in the repository defines or imports any more
    (a stale recipe); a mention in a comment does not count;
  * notes that earlier reviews left for this piece are pulled in verbatim: whole "For <ID>:" blocks,
    and every line of another piece's review that names the piece;
  * done means every acceptance line in the built game; a mockup is not done.
The brief records the revision of everything it was built from (DEC-102).
Exit codes: 0 brief written, 2 bad input, 3 refused (port clash).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("Goal", "Acceptance", "Owns", "Depends", "Reviewer gate", "Piece")
FIELD_RE = re.compile(r"^\s*(?:[-*]\s*)?\**(" + "|".join(FIELDS) + r")\**\s*:\s*\**\s*(.*)$", re.I)
# A second field on the same line, such as "**Depends:** CK2. **Reviewer gate:** the video".
EMBEDDED_RE = re.compile(r"\*\*(" + "|".join(FIELDS) + r")(?::\*\*|\*\*\s*:)\s*", re.I)
ACCEPTANCE_LINE_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+(.*\S)")
EVIDENCE_RE = re.compile(r"^\s*(Test|Shot)\b[^:]{0,40}:", re.I)
SYMBOL_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]{2,})(?:\(\))?`")
TICKED_RE = re.compile(r"`([^`]+)`")
IMPORT_RES = (
    re.compile(r"""(?:from|import)\s*\(?\s*['"](\.{1,2}/[^'"]+)['"]"""),      # JS/TS relative imports
    re.compile(r"""require\(\s*['"](\.{1,2}/[^'"]+)['"]\s*\)"""),
    re.compile(r"""(?:preload|load)\(\s*["']res://([^"']+)["']\s*\)"""),        # GDScript
)
CODE_SUFFIXES = {".ts", ".tsx", ".js", ".mjs", ".jsx", ".py", ".gd", ".cs", ".json", ".css"}
SKIP_DIRS = {".git", "node_modules", "dist", "build", "coverage", ".venv", "__pycache__", ".godot"}
MAX_SOURCE_BYTES = 2_000_000   # bigger files are generated bundles or captures, not source
STOPWORDS = set("the a an and or of to in on for with by from is are be this that it its at as into only "
                "each every one two any all not no new piece game games player players".split())
CORE_DECISIONS = (1, 16, 40)   # branch + PR, no invented results, independent review (issue numbers)
REQUIRED_MEMORY_METADATA = ("source_type", "source", "source_rev", "recorded_by", "verified")
DONE_RULE = ("Done means every acceptance line below is met in the built game and shown by its own "
             "evidence (test output or a screenshot of the build). A mockup, concept or plan is not done.")


class BriefError(Exception):
    """Bad input: the card or a file cannot be used."""


class Refused(Exception):
    """The brief must not be issued (for example a port clash)."""


def split_fields(line: str) -> list[str]:
    """One card line, cut where a second **Field:** starts on the same line."""
    match = FIELD_RE.match(line)
    if not match:
        return [line]
    rest = match.group(2)
    inner = EMBEDDED_RE.search(rest)
    if not inner:
        return [line]
    head = line[:match.start(2)] + rest[:inner.start()].rstrip()
    return [head] + split_fields("- **" + inner.group(1) + ":** " + rest[inner.end():])


def owned_paths(text: str) -> list[tuple[str, bool]]:
    """(path, new) pairs from an Owns line; backticked paths win, the word "new" before one marks it."""
    ticked = list(TICKED_RE.finditer(text))
    if ticked:
        return [(m.group(1).strip(), bool(re.search(r"\bnew\s*$", text[:m.start()], re.I))) for m in ticked
                if "/" in m.group(1) or "." in m.group(1)]
    pairs = []
    for part in re.split(r"[,;]", text):
        part = part.strip(" `.")
        new = bool(re.match(r"new\s+", part, re.I))
        part = re.sub(r"^new\s+", "", part, flags=re.I).strip(" `.")
        if part:
            pairs.append((part, new))
    return pairs


def parse_card(text: str) -> dict:
    card = {"goal": [], "acceptance": [], "owns": [], "new": [], "depends": [], "reviewer_gate": [], "piece": "",
            "title": ""}
    names = {"goal": "goal", "acceptance": "acceptance", "owns": "owns", "depends": "depends",
             "reviewer gate": "reviewer_gate", "piece": "piece"}
    current = None
    for raw in text.splitlines():
        for line in split_fields(raw):
            if not card["title"] and line.startswith("#"):
                card["title"] = line.lstrip("#").strip()
                continue
            field = FIELD_RE.match(line)
            if field:
                current = names[field.group(1).lower()]
                rest = field.group(2).strip()
                if current == "piece":
                    card["piece"] = rest.strip("* `")
                elif current == "owns":
                    for path, new in owned_paths(rest):
                        card["owns"].append(path)
                        if new:
                            card["new"].append(path)
                elif rest:
                    card[current].append(rest)
                continue
            item = ACCEPTANCE_LINE_RE.match(line)
            if current == "acceptance" and item:
                card["acceptance"].append(item.group(1))
            elif current == "owns" and item:
                for path, new in owned_paths(item.group(1)):
                    card["owns"].append(path)
                    if new:
                        card["new"].append(path)
            elif current in ("goal", "depends", "reviewer_gate") and line.strip():
                card[current].append(line.rstrip())
            elif line.startswith("#"):
                current = None
    if not card["goal"] or not card["acceptance"] or not card["owns"]:
        raise BriefError("the card needs Goal, numbered Acceptance lines and an Owns list")
    if not card["piece"]:
        match = re.match(r"\[?([A-Z][A-Z0-9-]*\d[A-Z]?)\]?", card["title"])
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
    """Refuse a range that shares even one port with a range in use; return notes otherwise."""
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


def walk_files(root: Path):
    """Every file under root, never entering .git, node_modules or build output."""
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            yield Path(folder) / name


def expand_owned(root: Path, owns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in owns:
        pattern = pattern.replace("\\", "/").rstrip("/")
        if pattern.endswith("/**"):
            base = root / pattern[:-3]
            files += sorted(walk_files(base)) if base.is_dir() else []
        elif any(ch in pattern for ch in "*?["):
            files += sorted(p for p in root.glob(pattern) if p.is_file())
        elif (root / pattern).is_file():
            files.append(root / pattern)
        elif (root / pattern).is_dir():
            files += sorted(walk_files(root / pattern))
    seen, unique = set(), []
    for path in files:
        if path not in seen and not SKIP_DIRS & set(path.relative_to(root).parts):
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


def strip_comments(text: str, suffix: str) -> str:
    """Code without its comments, so a comment that names a removed function does not keep it alive."""
    if suffix in (".py", ".gd"):
        return re.sub(r"#[^\n]*", "", text)
    if suffix == ".json":
        return text
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?<![:\"'\\])//[^\n]*", "", text)


def definition_re(name: str) -> re.Pattern:
    """Where code defines, exports or imports `name` (JS/TS, Python, GDScript, C#, JSON keys)."""
    n = re.escape(name)
    return re.compile("|".join([
        rf"\b(?:function\*?|def|func|class|interface|type|enum|struct|signal|class_name|const|let|var)\s+{n}\b",
        rf"\bexport\s*\{{[^}}]*\b{n}\b[^}}]*\}}",
        rf"\bimport\s*\{{[^}}]*\b{n}\b[^}}]*\}}\s*from\b",
        rf"\bimport\s+(?:\*\s+as\s+)?{n}\b",
        rf"\bfrom\s+\S+\s+import\s+[^\n]*\b{n}\b",
        rf"^\s*(?:export\s+)?(?:public\s+|private\s+|protected\s+|static\s+|readonly\s+|async\s+|get\s+|set\s+)*"
        rf"{n}\??\s*(?:[:=]|\([^)]*\)\s*(?::[^{{;]+)?\{{)",
        rf"\b{n}\s*:\s*(?:async\s+)?(?:function\b|\()",
        rf"\"{n}\"\s*:",
        rf"\b\w+(?:<[^>]*>)?\s+{n}\s*\([^)]*\)\s*\{{",
    ]), re.M)


def source_files(root: Path) -> list[Path]:
    """The code files of the repository: git's tracked files when it is a git repository (so other
    worktrees, captures and build output inside it do not count), else every file outside SKIP_DIRS."""
    listed = git(root, "ls-files", "-z")
    if listed is not None:
        names = [n for n in listed.split("\0") if n]
        paths = [root / n for n in names if not SKIP_DIRS & set(Path(n).parts)]
    else:
        paths = list(walk_files(root))
    keep = []
    for path in paths:
        try:
            if path.suffix in CODE_SUFFIXES and path.is_file() and path.stat().st_size <= MAX_SOURCE_BYTES:
                keep.append(path)
        except OSError:
            pass
    return keep


def stale_symbols(root: Path, card_text: str) -> list[str]:
    """Backticked identifiers in the card that no source file defines, exports or imports."""
    missing = set(SYMBOL_RE.findall(card_text))
    if not missing:
        return []
    patterns = {s: definition_re(s) for s in missing}
    for path in source_files(root):
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        here = [s for s in missing if s in raw]
        if not here:
            continue
        code = strip_comments(raw, path.suffix)
        missing -= {s for s in here if patterns[s].search(code)}
        if not missing:
            break
    return sorted(missing)


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def note_block(lines: list[str], index: int) -> list[str]:
    """The "For <ID>:" line and what belongs to it: deeper-indented lines, up to a blank line,
    a heading or the next item at the same level."""
    block = [lines[index].rstrip()]
    level = indent_of(lines[index])
    for follow in lines[index + 1:]:
        if not follow.strip() or follow.startswith("#"):
            break
        if indent_of(follow) <= level and re.match(r"^\s*(?:[-*]|\d+[.)])\s", follow):
            break
        if indent_of(follow) <= level and re.match(r"^\s*\*\*For [A-Z]", follow):
            break
        block.append(follow.rstrip())
    return block


def review_title(text: str) -> str:
    match = re.search(r'^# Review: Agent "(.+?)"', text, re.M)
    return match.group(1) if match else ""


def review_notes(reviews: Path, piece: str, owned_paths_: list[str]) -> list[tuple[str, list[str]]]:
    """Verbatim notes: "For <ID>:" blocks, lines in other pieces' reviews naming the piece, and
    must / block / fix lines about owned files. Each note is (file name, its lines)."""
    notes: list[tuple[str, list[str]]] = []
    if not reviews.is_dir():
        return notes
    tails = {p.rsplit("/", 1)[-1] for p in owned_paths_ if "." in p.rsplit("/", 1)[-1] and "*" not in p}
    word = re.compile(rf"(?<![A-Za-z0-9]){re.escape(piece)}(?![A-Za-z0-9])") if piece else None
    for path in sorted(reviews.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        own_review = bool(word and word.search(review_title(text)))
        taken: set[int] = set()
        for index, line in enumerate(lines):
            if index in taken:
                continue
            if piece and re.search(rf"\*{{0,2}}For {re.escape(piece)}\b", line):
                block = note_block(lines, index)
                taken.update(range(index, index + len(block)))
                notes.append((path.name, block))
            elif word and not own_review and word.search(line) and not line.startswith("# Review:"):
                block = note_block(lines, index)
                taken.update(range(index, index + len(block)))
                notes.append((path.name, block))
            elif tails and any(t in line for t in tails) and re.search(r"must|block|fix", line, re.I):
                notes.append((path.name, [line.rstrip()]))
    return notes


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
    """Recalled facts with every provenance field filled; observations and bare facts are dropped."""
    keep = []
    for result in (answer or {}).get("results", []):
        meta = result.get("metadata") or {}
        if result.get("type") in ("world", "experience") and all(
                isinstance(meta.get(k), str) and meta[k].strip() for k in REQUIRED_MEMORY_METADATA):
            keep.append(result)
    return keep


def git(root: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.rstrip("\r\n") if done.returncode == 0 else None  # porcelain lines start with a space


def sha256_of(path: str | None) -> str:
    if not path:
        return "(none)"
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def revisions(args, root: Path, owned: list[Path], reads: list[str]) -> list[str]:
    """What the brief was built from, with a revision for each source (DEC-102)."""
    head = git(root, "rev-parse", "HEAD")
    status = git(root, "status", "--porcelain") or ""
    touched = {line[3:].strip().strip('"') for line in status.splitlines() if len(line) > 3}
    mine = sorted(p for p in [o.relative_to(root).as_posix() for o in owned] + reads if p in touched)
    plugin = Path(args.plugin_root)
    try:
        plugin_version = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        plugin_version = "unknown"
    reviews = Path(args.reviews) if args.reviews else root / "docs" / "reviews"
    archive = sorted(p.name for p in reviews.glob("*.md")) if reviews.is_dir() else []
    lines = [
        f"- Game repository HEAD: `{head or 'not a git repository'}`"
        + (f"; uncommitted changes in {', '.join(f'`{m}`' for m in mine)}" if mine else
           ("; other uncommitted changes exist" if touched else "; clean")),
        f"- Card: sha256 `{sha256_of(args.card)}`" + (f", from {args.card_source}" if args.card_source else ""),
        f"- Decisions: sha256 `{sha256_of(args.decisions)}`",
        f"- Memories: sha256 `{sha256_of(args.memories)}`",
        f"- Review archive: {len(archive)} files" + (f", last `{archive[-1]}`" if archive else ""),
        f"- Plugin gamedev-studio {plugin_version}" + (f" at `{git(plugin, 'rev-parse', 'HEAD')}`"
                                                       if git(plugin, "rev-parse", "HEAD") else ""),
    ]
    return lines


def render(card, decisions, skills, owned, reads, stale, notes, memories, port_notes, root: Path,
           revision_lines: list[str]) -> str:
    out = [f"# Brief: {card['title'] or card['piece']}", ""]
    out += ["## Goal", *card["goal"], ""]
    out += ["## Rules", "- Apply the `studio-rules` skill first; decisions bind (DEC-003).",
            "- Work only in your own worktree and branch; commit as you go (a restart loses uncommitted work);"
            " never push.", *[f"- {n}" for n in port_notes],
            "- Ask the coordinator in one message when blocked; never guess an owner decision (DEC-004).", ""]
    out += ["## Definition of done", DONE_RULE]
    for number, line in enumerate(card["acceptance"], 1):
        flag = ""
        if not EVIDENCE_RE.match(line):
            flag = "  ⚠ no Test:/Shot: evidence named"
        elif re.search(r"\b(mockup|mock-up|concept|plan)\b", line, re.I):
            flag = "  ⚠ points at a mockup or concept; done needs the built game"
        out.append(f"{number}. {line}{flag}")
    existing = {p.relative_to(root).as_posix() for p in owned}
    owned_lines = [f"- `{p}`" for p in sorted(existing)]
    owned_lines += [f"- `{p}` (new: it does not exist yet)" if p in card["new"] else f"- `{p}` (not found)"
                    for p in card["owns"] if not any(e == p or e.startswith(p.rstrip("*").rstrip("/") + "/")
                                                     for e in existing)]
    out += ["", "## Owns (change only these)", *owned_lines]
    out += ["", "## Reads (do not change)", *([f"- `{r}`" for r in reads] or ["- (no imports found)"])]
    if card["depends"]:
        out += ["", "## Depends", *card["depends"]]
    if card["reviewer_gate"]:
        out += ["", "## Reviewer gate", *card["reviewer_gate"]]
    out += ["", "## Decisions", *[f"- #{d.get('number')} {d.get('title')} {d.get('url', '')}".rstrip()
                                  for d in decisions]]
    out += ["", "## Skills", *[f"- `{name}`: {text}" for name, text in skills]]
    if stale:
        out += ["", "## ⚠ Stale references", "Nothing in the repository at HEAD defines, exports or imports these "
                "names from the card. Do not apply a recipe that uses them; ask the coordinator:",
                *[f"- `{s}`" for s in stale]]
    if notes:
        out += ["", "## Notes from earlier reviews (verbatim)"]
        last = None
        for name, block in notes:
            if name != last:
                out += ["", f"From `{name}`:", ""]
                last = name
            out += block
    if memories:
        out += ["", "## Memories (verify before use; the source wins, DEC-103)",
                *[f"- {m.get('text')} — source: {m['metadata'].get('source')} @ {m['metadata'].get('source_rev')}"
                  f" (verified: {m['metadata'].get('verified')}, by {m['metadata'].get('recorded_by')})"
                  for m in memories]]
    out += ["", "## Built from", *revision_lines]
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
    words = keywords(card["title"], " ".join(card["goal"]), " ".join(card["acceptance"]),
                     " ".join(card["reviewer_gate"]))
    decisions = pick_decisions(load_json(args.decisions, "--decisions") or [], words)
    skills = pick_skills(Path(args.plugin_root), words)
    owned = expand_owned(root, card["owns"])
    reads = reads_of(root, owned)
    stale = stale_symbols(root, card_text)
    reviews = Path(args.reviews) if args.reviews else root / "docs" / "reviews"
    notes = review_notes(reviews, card["piece"], [p.relative_to(root).as_posix() for p in owned] + card["owns"])
    memories = usable_memories(load_json(args.memories, "--memories"))
    return render(card, decisions, skills, owned, reads, stale, notes, memories, port_notes, root,
                  revisions(args, root, owned, reads))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble a worker brief from a piece card (read the docstring).")
    parser.add_argument("--card", required=True)
    parser.add_argument("--card-source")
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
