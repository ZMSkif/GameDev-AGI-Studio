#!/usr/bin/env python3
"""Mine the verbatim review archive for recurring failure classes (Learning & Improvement, light).

DEC-105: improvement comes from real QA failures. A class becomes a lesson only past the noise guard:
at least 2 independent occurrences (different pieces; a re-review of the same piece counts once), or
one severe occurrence (inside a blocker or must-fix section). Stdlib only; it reads the archive and
writes one report. With --retain it also stores each lesson in a Hindsight bank with provenance,
after the same secret and --forbid check the review archiver uses.

Usage:
  python scripts/mine_lessons.py --reviews docs/reviews [--since N] [--out report.md] [--json]
                                 [--retain http://127.0.0.1:8888 --bank gamedev-studio::studio]
                                 [--forbid REGEX ...]
Exit codes: 0 ok, 2 bad input, 3 some lessons were not retained (see the report).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d+)_(.+?)_([a-z-]+)\.md$")
HEADER_END = "\n---\n\n"
SEVERE_HEADING = re.compile(r"^#{1,4}\s.*\b(blockers?|must-fix|must fix)\b", re.I)
OTHER_HEADING = re.compile(r"^#{1,4}\s")
MIN_INDEPENDENT = 2

# (class id, pattern, what to change in the plugin)
CLASSES = [
    ("primitive-or-mangled-asset", r"\bprimitive\b|faceted|lumpy|sawtooth|slivers?\b|blotch",
     "art-acceptance §1-§4 and the art-reviewer checklist"),
    ("collider-mismatch", r"collider|overhang|walked through|walk through|no physics body",
     "art-acceptance §2: measure collider against mesh at character height"),
    ("stepped-gate-rule", r"\bstep rule\b|stepped where|jumps? by|flip(?:s|ped)? results|never jumps|continuous rule",
     "art-acceptance §6: one continuous rule with a test that it never jumps"),
    ("check-that-cannot-fail", r"stale (?:assertion|check|test|e2e)|catch(?:es)? nothing|cannot fail|loops? over zero"
                               r"|false pass|mutants? \S*\s*surviv|survived",
     "orchestration-playbook §3: mutants and known-bad controls in every review"),
    ("audio-lifecycle", r"\bmusic\b|volume (?:stuck|at 0)|play ?lock|watchdog",
     "web-audio-lifecycle: test real element volume after every pause path"),
    ("text-clipping", r"cut off|clipp(?:ed|ing)|overflow|run(?:s)? off the|mid-word",
     "i18n-portal §3: length and layout lint at small viewports"),
    ("licence-registry", r"licen[cs]e rows?|drops? the licen|uncovered|merge-licenses",
     "asset-licensing §3: registry checks that cannot false-pass"),
    ("context-loss", r"context (?:loss|restore|lost)|webglcontextrestored|lose_context",
     "playgama-release: WebGL context loss and restore in the release gate"),
    ("platform-pause", r"leftover pause|un-?pauses?\b|un-?mutes?\b|pause or mute .{0,40}lost",
     "web-audio-lifecycle §4: platform pause and ad timeouts"),
    ("unrequested-change", r"unrequested|not requested",
     "orchestration-playbook §3: unrequested changes are a regression risk"),
    ("long-run-only-failure", r"\bsoaks?\b.{0,60}(?:longer|minute|30-minute)|walk(?:ing)? in place|oscillat|nose to nose",
     "fair-bots-balance §4: soaks longer than the tests' own windows"),
    ("passability", r"not reliably passable|wait forever|can't reliably pass",
     "fair-bots-balance §2: passability per control scheme"),
]


def _guard():
    """blocked_reason from archive_reviews.py, so lessons pass the same secret and --forbid check."""
    path = Path(__file__).resolve().parent / "archive_reviews.py"
    spec = importlib.util.spec_from_file_location("_archive_reviews_guard", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.blocked_reason


def review_files(folder: Path, since: int) -> list[tuple[int, str, Path]]:
    found = []
    for path in sorted(folder.glob("*.md")):
        match = NAME_RE.match(path.name)
        if match and int(match.group(2)) > since:
            found.append((int(match.group(2)), match.group(3), path))
    return sorted(found)


def sections(body: str):
    """Yield (line, severe) for every line, severe when it sits under a blocker or must-fix heading."""
    severe = False
    for line in body.splitlines():
        if SEVERE_HEADING.match(line):
            severe = True
        elif OTHER_HEADING.match(line):
            severe = False
        yield line, severe


def mine(folder: Path, since: int = 0) -> dict:
    occurrences: dict[str, list[dict]] = {cid: [] for cid, _, _ in CLASSES}
    files = review_files(folder, since)
    for number, piece, path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        body = text.split(HEADER_END, 1)[1] if HEADER_END in text else text
        for cid, pattern, _ in CLASSES:
            hits = [(line.strip(), severe) for line, severe in sections(body) if re.search(pattern, line, re.I)]
            if hits:
                occurrences[cid].append({"file": path.name, "number": number, "piece": piece,
                                         "severe": any(s for _, s in hits), "example": hits[0][0][:200]})
    lessons, dropped = [], []
    for cid, _, proposal in CLASSES:
        found = occurrences[cid]
        pieces = sorted({o["piece"] for o in found})
        severe = any(o["severe"] for o in found)
        if not found:
            continue
        entry = {"class": cid, "pieces": pieces, "files": [o["file"] for o in found], "severe": severe,
                 "independent_occurrences": len(pieces), "examples": [o["example"] for o in found[:2]],
                 "proposal": proposal}
        if len(pieces) >= MIN_INDEPENDENT or severe:
            lessons.append(entry)
        else:
            dropped.append({"class": cid, "reason": "one occurrence, not severe", "files": entry["files"]})
    last = max((n for n, _, _ in files), default=since)
    return {"since": since, "last": last, "files": len(files), "lessons": lessons, "dropped": dropped}


def lesson_text(lesson: dict) -> str:
    return (f"Lesson ({lesson['class']}): seen in {lesson['independent_occurrences']} independent pieces"
            f"{' with a blocker' if lesson['severe'] else ''}. Change: {lesson['proposal']}.")


def render(report: dict) -> str:
    out = [f"# Lessons from reviews {report['since'] + 1}–{report['last']} ({report['files']} files)", ""]
    for lesson in report["lessons"]:
        out += [f"## {lesson['class']}", lesson_text(lesson),
                f"- pieces: {', '.join(lesson['pieces'])}",
                f"- files: {', '.join(lesson['files'][:8])}{' …' if len(lesson['files']) > 8 else ''}",
                *[f"- example: {e}" for e in lesson["examples"]], ""]
    if report["dropped"]:
        out += ["## Below the noise guard", *[f"- {d['class']}: {d['reason']} ({', '.join(d['files'])})"
                                             for d in report["dropped"]], ""]
    out.append(f"Next run: --since {report['last']}")
    return "\n".join(out) + "\n"


def retain(report: dict, base: str, bank: str, forbid: list[re.Pattern]) -> list[tuple[str, str]]:
    """Store each lesson; return (class, reason) for every lesson not stored."""
    blocked_reason = _guard()
    refused = []
    for lesson in report["lessons"]:
        content = lesson_text(lesson)
        reason = blocked_reason(content, forbid)
        if reason:
            refused.append((lesson["class"], reason))
            continue
        item = {"content": content, "context": "review archive lessons",
                "metadata": {"source_type": "review-archive", "source": ", ".join(lesson["files"])[:900],
                             "source_rev": f"reviews {report['since'] + 1}-{report['last']}",
                             "recorded_by": "gamedev-studio:lessons", "verified": "false"},
                "tags": ["scope:studio", f"lesson:{lesson['class']}"],
                "document_id": f"lesson-{lesson['class']}-{report['last']}"}
        data = json.dumps({"items": [item]}).encode("utf-8")
        req = urllib.request.Request(f"{base.rstrip('/')}/v1/default/banks/{bank}/memories", data=data, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                if resp.status != 200:
                    refused.append((lesson["class"], f"HTTP {resp.status}"))
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            refused.append((lesson["class"], str(exc)))
    return refused


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mine the review archive for recurring failure classes.")
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--since", type=int, default=0, help="only files numbered above this")
    parser.add_argument("--out", help="write the Markdown report here (outside the repository)")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--retain", metavar="URL", help="Hindsight base URL to store the lessons in")
    parser.add_argument("--bank", default="gamedev-studio::studio")
    parser.add_argument("--forbid", action="append", default=[])
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    folder = Path(args.reviews)
    if not folder.is_dir():
        print(f"ERROR: no review folder at {folder}", file=sys.stderr)
        return 2
    try:
        forbid = [re.compile(p) for p in args.forbid]
    except re.error as exc:
        print(f"ERROR: bad --forbid: {exc}", file=sys.stderr)
        return 2
    report = mine(folder, args.since)
    text = render(report)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else text)
    if args.retain:
        refused = retain(report, args.retain, args.bank, forbid)
        for cid, reason in refused:
            print(f"NOT RETAINED {cid}: {reason}", file=sys.stderr)
        return 3 if refused else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
