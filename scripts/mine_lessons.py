#!/usr/bin/env python3
"""Mine the verbatim review archive for recurring failure classes (Learning & Improvement, light).

DEC-105: improvement comes from real QA failures. A class becomes a lesson only past the noise guard:
at least 2 independent occurrences (different pieces; a re-review of the same piece counts once), or
one severe occurrence (a defect line inside a blocker or must-fix section). The whole archive is
always counted, so repeats spread over several runs still add up; --since only limits the report to
lessons with an occurrence newer than that file number.

Stdlib only. It reads the archive and writes one report. With --retain it also stores each kept
lesson in a Hindsight bank, with provenance and a document id that is new for every run, so a later
run never replaces an earlier one (DEC-138). Every payload passes the review archiver's secret and
--forbid check first.

Usage:
  python scripts/mine_lessons.py --reviews docs/reviews [--since N] [--drop CLASS ...] [--out FILE] [--json]
                                 [--retain http://127.0.0.1:8888 --bank gamedev-studio::studio
                                  --repository owner/name] [--forbid REGEX ...]
Exit codes: 0 ok, 2 bad input, 3 some lessons were not retained (see stderr).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d+)_(.+?)_([a-z-]+)\.md$")
TITLE_RE = re.compile(r'^# Review: Agent "(.+?)"', re.M)
HEADER_END = "\n---\n\n"
SEVERE_HEADING = re.compile(r"^#{1,4}\s.*\b(blockers?|must-fix|must fix)\b", re.I)
NEGATED_HEADING = re.compile(r"\b(no|zero|none|0)\s+(\w+\s+)?(blockers?|must-fix|must fix)\b"
                             r"|\b(blockers?|must-fix|must fix)\s*:?\s*(none|no|0)\b", re.I)
OTHER_HEADING = re.compile(r"^#{1,4}\s")
# A line that only reports a pass is not an occurrence, unless it also names a defect.
PASS_CUE = re.compile(r"\b(pass(?:es|ed)?|holds?|confirmed|ok|fine|works?)\b", re.I)
DEFECT_CUE = re.compile(r"\b(fail\w*|broken|missing|wrong|bugs?|crash\w*|leak\w*|stuck|lost|regress\w*|not|never"
                        r"|cannot|can't|doesn't|clipp\w*|cut off|block\w*|must|surviv\w*)\b", re.I)
# A piece code such as cn1, wp0, wa-0, ca1b, r17b; review words are not codes.
PIECE_CODE = re.compile(r"(?<![a-z0-9])([a-z]{1,4})-?(\d{1,3})([a-z]?)(?![a-z0-9])")
REVIEW_WORDS = {"agent", "independent", "review", "re", "second", "third", "fourth", "final", "again", "fix",
                "fixes", "round", "follow", "up", "finished", "finish", "finishe", "fi", "of", "the", "pass"}
MIN_INDEPENDENT = 2
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

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
CLASS_IDS = [cid for cid, _, _ in CLASSES]


def _guard():
    """blocked_reason from archive_reviews.py, so lessons pass the same secret and --forbid check."""
    path = Path(__file__).resolve().parent / "archive_reviews.py"
    spec = importlib.util.spec_from_file_location("_archive_reviews_guard", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.blocked_reason


def piece_key(title: str) -> str:
    """One key per piece: its code (cn1, wp0, wa0) when the title has one, else the title without review words."""
    text = title.lower()
    for match in PIECE_CODE.finditer(text):
        if match.group(1) not in REVIEW_WORDS:
            return "".join(match.groups())
    words = [w for w in re.findall(r"[a-z0-9]+", text) if w not in REVIEW_WORDS and not w.isdigit()]
    return "-".join(words) or text


def review_files(folder: Path) -> list[tuple[int, Path]]:
    found = []
    for path in sorted(folder.glob("*.md")):
        match = NAME_RE.match(path.name)
        if match:
            found.append((int(match.group(2)), path))
    return sorted(found)


def lines_with_severity(body: str):
    """Yield (line, severe) for every line, severe when it sits under a blocker or must-fix heading."""
    severe = False
    for line in body.splitlines():
        if OTHER_HEADING.match(line):
            severe = bool(SEVERE_HEADING.match(line)) and not NEGATED_HEADING.search(line)
        yield line, severe


def is_pass_only(line: str) -> bool:
    return bool(PASS_CUE.search(line)) and not DEFECT_CUE.search(line)


def mine(folder: Path, since: int = 0, drop: tuple[str, ...] = ()) -> dict:
    occurrences: dict[str, list[dict]] = {cid: [] for cid in CLASS_IDS}
    files = review_files(folder)
    for number, path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        title_match = TITLE_RE.search(text)
        piece = piece_key(title_match.group(1) if title_match else NAME_RE.match(path.name).group(3))
        body = text.split(HEADER_END, 1)[1] if HEADER_END in text else text
        lines = [(line.strip(), severe) for line, severe in lines_with_severity(body)
                 if line.strip() and not OTHER_HEADING.match(line) and not is_pass_only(line)]
        for cid, pattern, _ in CLASSES:
            hits = [(line, severe) for line, severe in lines if re.search(pattern, line, re.I)]
            if hits:
                occurrences[cid].append({"file": path.name, "number": number, "piece": piece,
                                         "severe": any(s for _, s in hits), "example": hits[0][0][:200]})
    lessons, dropped, removed = [], [], []
    for cid, _, proposal in CLASSES:
        found = occurrences[cid]
        if not found or all(o["number"] <= since for o in found):
            continue
        pieces = sorted({o["piece"] for o in found})
        severe = any(o["severe"] for o in found)
        entry = {"class": cid, "pieces": pieces, "files": [o["file"] for o in found], "severe": severe,
                 "independent_occurrences": len(pieces),
                 "new_files": [o["file"] for o in found if o["number"] > since],
                 "examples": [o["example"] for o in found[:2]], "proposal": proposal}
        if cid in drop:
            removed.append({"class": cid, "reason": "dropped by --drop", "files": entry["files"]})
        elif len(pieces) >= MIN_INDEPENDENT or severe:
            lessons.append(entry)
        else:
            dropped.append({"class": cid, "reason": "one piece, not severe", "files": entry["files"]})
    numbers = [n for n, _ in files]
    return {"since": since, "first": min(numbers, default=0), "last": max(numbers, default=since),
            "files": len(files), "new_files": sum(1 for n in numbers if n > since),
            "lessons": lessons, "dropped": dropped, "removed": removed}


def lesson_text(lesson: dict) -> str:
    return (f"Lesson ({lesson['class']}): seen in {lesson['independent_occurrences']} independent pieces"
            f"{' with a blocker' if lesson['severe'] else ''}. Change: {lesson['proposal']}.")


def render(report: dict) -> str:
    out = [f"# Lessons from reviews {report['first']}–{report['last']} ({report['files']} files, "
           f"{report['new_files']} after --since {report['since']})", ""]
    for lesson in report["lessons"]:
        out += [f"## {lesson['class']}", lesson_text(lesson),
                f"- pieces: {', '.join(lesson['pieces'])}",
                f"- files: {', '.join(lesson['files'][:8])}{' …' if len(lesson['files']) > 8 else ''}",
                f"- new since {report['since']}: {', '.join(lesson['new_files'])}",
                *[f"- example: {e}" for e in lesson["examples"]], ""]
    if report["dropped"]:
        out += ["## Below the noise guard", *[f"- {d['class']}: {d['reason']} ({', '.join(d['files'])})"
                                             for d in report["dropped"]], ""]
    if report["removed"]:
        out += ["## Dropped as false hits", *[f"- {d['class']}: {d['reason']}" for d in report["removed"]], ""]
    out.append(f"Next run: --since {report['last']}")
    return "\n".join(out) + "\n"


def items_for(report: dict, repository: str, token: str) -> list[dict]:
    """The Hindsight items: one per lesson, then one run marker. Document ids are new for every run."""
    span = f"{report['first']}-{report['last']}"
    items = []
    for lesson in report["lessons"]:
        items.append({
            "content": lesson_text(lesson), "context": "review archive lessons",
            "metadata": {"source_type": "review-archive",
                         "source": f"{repository}: " + ", ".join(lesson["files"])[:900],
                         "source_rev": f"{repository} reviews {span}",
                         "recorded_by": "gamedev-studio:lessons", "verified": "false",
                         "archive_last": str(report["last"])},
            "tags": ["lesson", f"lesson:{lesson['class']}", f"repo:{repository}"],
            "document_id": f"lesson::{repository}::{lesson['class']}::{span}::{token}"})
    items.append({
        "content": (f"Lessons run for {repository}: review archive files {span} mined, "
                    f"{len(report['lessons'])} lessons kept. Next run: --since {report['last']}."),
        "context": "review archive lessons run marker",
        "metadata": {"source_type": "review-archive", "source": f"{repository}: review archive",
                     "source_rev": f"{repository} reviews {span}", "recorded_by": "gamedev-studio:lessons",
                     "verified": "true", "archive_last": str(report["last"])},
        "tags": ["lessons-run", f"repo:{repository}"],
        "document_id": f"lessons-run::{repository}::{span}::{token}"})
    return items


def post(base: str, bank: str, item: dict) -> str | None:
    """Store one item; return None on success, else the reason."""
    data = json.dumps({"items": [item]}).encode("utf-8")
    req = urllib.request.Request(f"{base.rstrip('/')}/v1/default/banks/{bank}/memories", data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        return f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
        return str(exc)
    except ValueError:
        return "answer is not JSON"
    if body.get("success") is not True or body.get("items_count") != 1:
        return f"not stored: {json.dumps(body)[:200]}"
    return None


def retain(report: dict, base: str, bank: str, repository: str, forbid: list[re.Pattern],
           token: str | None = None) -> list[tuple[str, str]]:
    """Store each kept lesson and the run marker; return (document id, reason) for every item not stored."""
    blocked_reason = _guard()
    token = token or uuid.uuid4().hex[:12]
    refused = []
    for item in items_for(report, repository, token):
        reason = blocked_reason(json.dumps(item, ensure_ascii=False), forbid)
        if not reason:
            reason = post(base, bank, item)
        if reason:
            refused.append((item["document_id"], reason))
    return refused


def repository_of(folder: Path) -> Path | None:
    """The top of the git repository that holds the review archive, or None."""
    try:
        top = subprocess.run(["git", "-C", str(folder), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return Path(top.stdout.strip()).resolve() if top.returncode == 0 and top.stdout.strip() else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mine the review archive for recurring failure classes.")
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--since", type=int, default=0, help="report only lessons with a file numbered above this")
    parser.add_argument("--drop", action="append", default=[], metavar="CLASS",
                        help="a false hit to leave out of the report and out of --retain; repeatable")
    parser.add_argument("--out", help="write the Markdown report here (outside the game repository)")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--retain", metavar="URL", help="Hindsight base URL to store the lessons in")
    parser.add_argument("--bank", default="gamedev-studio::studio")
    parser.add_argument("--repository", help="owner/name of the game repository the archive belongs to")
    parser.add_argument("--forbid", action="append", default=[])
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    folder = Path(args.reviews)
    if not folder.is_dir():
        print(f"ERROR: no review folder at {folder}", file=sys.stderr)
        return 2
    unknown = sorted(set(args.drop) - set(CLASS_IDS))
    if unknown:
        print(f"ERROR: unknown --drop class {', '.join(unknown)}; known: {', '.join(CLASS_IDS)}", file=sys.stderr)
        return 2
    if args.retain and not (args.repository and REPO_RE.match(args.repository)):
        print("ERROR: --retain needs --repository owner/name", file=sys.stderr)
        return 2
    root = repository_of(folder)
    if args.out and root and (root == Path(args.out).resolve() or root in Path(args.out).resolve().parents):
        print("ERROR: --out must be outside the game repository (DEC-002: no tracked report files)", file=sys.stderr)
        return 2
    try:
        forbid = [re.compile(p) for p in args.forbid]
    except re.error as exc:
        print(f"ERROR: bad --forbid: {exc}", file=sys.stderr)
        return 2
    report = mine(folder, args.since, tuple(args.drop))
    text = render(report)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")  # a cp1251 console cannot print every character
    print(json.dumps(report, indent=2) if args.json else text)
    if args.retain:
        refused = retain(report, args.retain, args.bank, args.repository, forbid)
        for doc, reason in refused:
            print(f"NOT RETAINED {doc}: {reason}", file=sys.stderr)
        return 3 if refused else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
