#!/usr/bin/env python3
"""Mine the verbatim review archive for recurring failure classes (Learning & Improvement, light).

DEC-105: improvement comes from real QA failures. A class is a candidate lesson only past the noise
guard: at least 2 independent occurrences (different pieces; reviews whose titles share a piece code
are one piece) or one severe occurrence (a line under a blocker or must-fix heading whose section does
not say "None"). The whole archive is always counted; --since only limits the report to classes with a
hit newer than that file number.

The text rules only annotate: a hit that reports a pass or says a defect is absent is shown as doubtful,
never dropped. The report lists every hit with its file and line. Nothing is stored unless the agent names
the class with --keep after reading the hits, because a stored memory can only be removed by the owner
(DEC-138). With --retain and --keep, each kept lesson is stored with provenance and without a document_id;
storing stops at the first failure, and the run marker that moves the next --since forward is stored only
after every kept lesson was. Every payload passes the review archiver's secret and --forbid check first.

Usage:
  python scripts/mine_lessons.py --reviews docs/reviews [--since N] [--out FILE] [--json]
         [--retain http://127.0.0.1:8888 --bank gamedev-studio::studio --repository owner/name --keep CLASS ...]
         [--forbid REGEX ...]
Exit codes: 0 ok, 2 bad input, 3 some kept lessons were not stored (see stderr).
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
# "No blockers", "Zero must-fix items", "Blockers: none" - but not "Must-fix: no music after resume".
NEGATED_HEADING = re.compile(r"\b(no|zero|none|0)\s+(\w+\s+)?(blockers?|must-fix|must fix)\b"
                             r"|\b(blockers?|must-fix|must fix)(\s+list)?\s*:?\s*(none|no|0|nothing)\s*[.!]?\s*$",
                             re.I)
OTHER_HEADING = re.compile(r"^#{1,4}\s")
# The archive's own way of saying a blocker section is empty: "## BLOCKER" then "None." on the next line.
NONE_LINE = re.compile(r"^\W*(?:none|nothing|n/?a)\W*$|^\W*(?:none|nothing)\s*[.!]\s", re.I)
# A line that only reports a pass, or only says a defect is absent ("music is not stuck"), is not an
# occurrence unless it also names a defect.
# Doubt cues: they mark a hit for the agent to check; they never remove it.
PASS_CUE = re.compile(r"\b(pass(?:es|ed)|(?:checks?|tests?|suite) pass|confirmed|works as expected)\b", re.I)
DEFECT_CUE = re.compile(r"\b(fail\w*|broken|missing|wrong|bugs?|crash\w*|leak\w*|stuck|lost|regress\w*|not|never"
                        r"|cannot|can't|doesn't|clipp\w*|cut off|block\w*|must|surviv\w*|gone|silent|stops?|freez\w*)\b",
                        re.I)
DEFECT_WORDS = (r"fail\w*|broken|missing|wrong|bugs?|crash\w*|leak\w*|stuck|lost|regress\w*|clipp\w*|cut off"
                r"|block\w*")
NEGATED_DEFECT = re.compile(r"\b(?:not(?!\s+only\b)|no|never|without|doesn't|does not|didn't|isn't|is not(?!\s+only\b)"
                            r"|won't|nothing)\s+"
                            r"(?:\w+\s+){0,2}?(?:" + DEFECT_WORDS + r")\b", re.I)
# Piece codes in review titles, matched in any case: CN1, WP0, WA-0, CA1b, I18N, r17 (see piece_codes).
PIECE_CODE = re.compile(r"(?<![a-z0-9])([a-z]{1,4})-?(\d{1,3})([a-z]?)(?![a-z0-9])")
REVIEW_WORDS = {"agent", "independent", "review", "re", "second", "third", "fourth", "final", "again", "fix",
                "fixes", "round", "follow", "up", "finished", "finish", "finishe", "fi", "of", "the", "pass", "v",
                "piece", "check", "recheck"}
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


def review_files(folder: Path) -> list[tuple[int, Path]]:
    found = []
    for path in sorted(folder.glob("*.md")):
        match = NAME_RE.match(path.name)
        if match:
            found.append((int(match.group(2)), path))
    return sorted(found)


def piece_codes(title: str) -> set[str]:
    """The codes a review title names, in any case. Codes with two or more letters (CN1, WP0, WA-0, CA1b,
    LOD1) are the pieces; a review item such as B1, M3 or R2, or a fix round such as r17, counts only when
    the title names nothing else. Without a code, the title's words minus review words stand for it."""
    found = [m for m in PIECE_CODE.finditer(title.lower()) if m.group(1) not in REVIEW_WORDS]
    strong = {"".join(m.groups()) for m in found if len(m.group(1)) >= 2}
    if strong:
        return strong
    weak = {"".join(m.groups()) for m in found}
    if weak:
        return weak
    words = [w for w in re.findall(r"[a-z0-9]+", title.lower())
             if w not in REVIEW_WORDS and not w.isdigit() and not re.fullmatch(r"v\d+", w)]
    return {"-".join(words) or title.lower()}


def piece_groups(titles: dict[int, str]) -> dict[int, str]:
    """Key -> piece group. Reviews whose titles share a code are one piece, transitively. Titles that share
    no code stay apart, so the report prints the groups for the agent to check."""
    parent = {n: n for n in titles}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    owner: dict = {}
    codes = {n: piece_codes(t) for n, t in titles.items()}
    worded = {n: set(next(iter(cs)).split("-")) for n, cs in codes.items()
              if len(cs) == 1 and not PIECE_CODE.fullmatch(next(iter(cs)))}
    for a in worded:
        for b in worded:
            if a != b and len(worded[a]) >= 2 and worded[a] <= worded[b]:
                parent[find(a)] = find(b)
    for n, cs in codes.items():
        for code in cs:
            if code in owner:
                parent[find(n)] = find(owner[code])
            else:
                owner[code] = n
    members: dict[int, set[str]] = {}
    for n in titles:
        members.setdefault(find(n), set()).update(codes[n])
    return {n: "/".join(sorted(members[find(n)])) for n in titles}


def piece_key(title: str) -> str:
    """The group name a single title gets on its own (its codes, sorted)."""
    return "/".join(sorted(piece_codes(title)))


def lines_with_severity(body: str):
    """Yield (line number in the body, line, severe, section note) for every line. A line is severe under
    a blocker or must-fix heading, unless the heading or the section's first line says there is none."""
    severe, first, note = False, False, ""
    for number, line in enumerate(body.splitlines(), 1):
        if OTHER_HEADING.match(line):
            blocker = bool(SEVERE_HEADING.match(line))
            negated = blocker and bool(NEGATED_HEADING.search(line))
            severe, first = blocker and not negated, blocker and not negated
            note = "the heading says there is none" if negated else ""
        elif first and line.strip():
            first = False
            if NONE_LINE.match(line):
                severe, note = False, "the section says None"
        yield number, line, severe, note


def doubts(line: str, note: str) -> list[str]:
    """Why a hit may be a false one. Doubts never remove a hit; they are shown, and the agent decides."""
    found = [note] if note else []
    rest = NEGATED_DEFECT.sub(" ", line)
    if not DEFECT_CUE.search(rest):
        if PASS_CUE.search(line):
            found.append("the line reports a pass")
        if rest != line:
            found.append("the line says a defect is absent")
    return found


def mine(folder: Path, since: int = 0) -> dict:
    files = review_files(folder)
    texts = {path: path.read_text(encoding="utf-8", errors="replace") for _, path in files}
    titles = {}
    for number, path in files:
        match = TITLE_RE.search(texts[path])
        titles[path] = match.group(1) if match else NAME_RE.match(path.name).group(3)
    groups = piece_groups(titles)
    hits: dict[str, list[dict]] = {cid: [] for cid in CLASS_IDS}
    for number, path in files:
        text = texts[path]
        cut = text.index(HEADER_END) + len(HEADER_END) if HEADER_END in text else 0
        head_lines, body = text[:cut].count("\n"), text[cut:]
        for line_no, line, severe, note in lines_with_severity(body):
            if not line.strip():
                continue
            for cid, pattern, _ in CLASSES:
                if re.search(pattern, line, re.I):
                    hits[cid].append({"file": path.name, "number": number, "line": head_lines + line_no,
                                      "piece": groups[path], "severe": severe, "doubts": doubts(line, note),
                                      "text": line.strip()})
    lessons, doubtful, below = [], [], []
    for cid, _, proposal in CLASSES:
        found = hits[cid]
        if not found or all(h["number"] <= since for h in found):
            continue
        solid = [h for h in found if not h["doubts"]]
        entry = {"class": cid, "proposal": proposal, "hits": found,
                 "pieces": sorted({h["piece"] for h in found}),
                 "solid_pieces": sorted({h["piece"] for h in solid}),
                 "severe": any(h["severe"] for h in solid),
                 "new_files": sorted({h["file"] for h in found if h["number"] > since})}
        if len(entry["solid_pieces"]) >= MIN_INDEPENDENT or entry["severe"]:
            lessons.append(entry)
        elif len(entry["pieces"]) >= MIN_INDEPENDENT or any(h["severe"] for h in found):
            doubtful.append(entry)
        else:
            below.append(entry)
    numbers = [n for n, _ in files]
    return {"since": since, "first": min(numbers, default=0), "last": max(numbers, default=since),
            "files": len(files), "new_files": sum(1 for n in numbers if n > since),
            "lessons": lessons, "doubtful": doubtful, "below": below}


def lesson_text(lesson: dict) -> str:
    pieces = lesson["solid_pieces"] or lesson["pieces"]
    return (f"Lesson ({lesson['class']}): seen in {len(pieces)} independent pieces"
            f"{' with a blocker' if lesson['severe'] else ''}. Change: {lesson['proposal']}.")


def render_hits(entry: dict) -> list[str]:
    out = []
    for h in entry["hits"]:
        marks = (["severe"] if h["severe"] else []) + [f"doubt: {d}" for d in h["doubts"]]
        out.append(f"- `{h['file']}:{h['line']}` [{h['piece']}]{' (' + '; '.join(marks) + ')' if marks else ''}: "
                   f"{h['text']}")
    return out


def render(report: dict) -> str:
    out = [f"# Lessons from reviews {report['first']}–{report['last']} ({report['files']} files, "
           f"{report['new_files']} after --since {report['since']})", "",
           "Nothing is stored unless you name it: read every hit, then run again with "
           "`--retain … --keep <class>` for each class that is a real recurring failure.", ""]
    sections = (("Lessons", "lessons", "past the noise guard without the doubtful hits"),
                ("Doubtful", "doubtful", "past the guard only with doubtful hits: read them before you keep one"),
                ("Below the noise guard", "below", "one piece, not severe: listed, never stored"))
    for title, key, why in sections:
        if not report[key]:
            continue
        out += [f"## {title} ({why})", ""]
        for entry in report[key]:
            out += [f"### {entry['class']}", lesson_text(entry),
                    f"- pieces: {', '.join(entry['pieces'])}",
                    f"- new since {report['since']}: {', '.join(entry['new_files'])}", *render_hits(entry), ""]
    out.append(f"Next run: --since {report['last']}")
    return "\n".join(out) + "\n"


def items_for(report: dict, keep: list[str], repository: str, token: str) -> list[dict]:
    """The Hindsight items: one per lesson, then one run marker. No item names a document_id or an
    update_mode, so Hindsight makes a new document for each and nothing stored is replaced (DEC-138)."""
    span = f"{report['first']}-{report['last']}"
    items = []
    chosen = [e for e in report["lessons"] + report["doubtful"] if e["class"] in keep]
    for lesson in chosen:
        files = sorted({h["file"] for h in lesson["hits"]})
        items.append({
            "content": lesson_text(lesson), "context": "review archive lessons",
            "metadata": {"source_type": "review-archive",
                         "source": f"{repository}: " + ", ".join(files)[:900],
                         "source_rev": f"{repository} reviews {span}",
                         "recorded_by": "gamedev-studio:lessons", "verified": "false",
                         "archive_last": str(report["last"]), "lessons_run": token},
            "tags": ["lesson", f"lesson:{lesson['class']}", f"repo:{repository}"]})
    items.append({
        "content": (f"Lessons run for {repository}: review archive files {span} mined. "
                    f"Next run: --since {report['last']}."),
        "context": "review archive lessons run marker",
        "metadata": {"source_type": "review-archive", "source": f"{repository}: review archive",
                     "source_rev": f"{repository} reviews {span}", "recorded_by": "gamedev-studio:lessons",
                     "verified": "false", "archive_last": str(report["last"]), "lessons_run": token},
        "tags": ["lessons-run", f"repo:{repository}"]})
    return items


def post(base: str, bank: str, item: dict) -> tuple[str, str]:
    """Store one item. Returns ("stored", ""); ("refused", why) only when the item was surely not stored:
    the server could not be reached, answered 4xx, or answered "success": false; or ("unknown", why) for
    every other outcome (a timeout, a dropped connection, a 5xx such as a proxy's 502 or 504, an empty or
    unreadable answer), because the server may have stored the item before it failed to answer."""
    data = json.dumps({"items": [item]}).encode("utf-8")
    req = urllib.request.Request(f"{base.rstrip('/')}/v1/default/banks/{bank}/memories", data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return ("refused" if 400 <= exc.code < 500 else "unknown"), f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ConnectionRefusedError):
            return "refused", f"connection refused ({exc.reason})"
        return "unknown", str(exc)
    except (TimeoutError, ConnectionError, OSError) as exc:
        return "unknown", f"{type(exc).__name__}: {exc}"
    except ValueError:
        return "unknown", "the answer is not JSON"
    if not isinstance(body, dict):
        return "unknown", "the answer is not a JSON object"
    if body.get("success") is False:
        return "refused", f"not stored: {json.dumps(body)[:200]}"
    if body.get("success") is not True or body.get("items_count") != 1:
        return "unknown", f"the answer does not confirm one stored item: {json.dumps(body)[:200]}"
    return "stored", ""


def item_name(item: dict) -> str:
    return next((t for t in item["tags"] if t.startswith("lesson:")), item["tags"][0])


def retain(report: dict, keep: list[str], base: str, bank: str, repository: str, forbid: list[re.Pattern],
           token: str | None = None, marker_only: bool = False) -> dict:
    """Store each kept lesson, then the run marker, stopping at the first item that is not stored for
    sure. Returns {"token", "stored", "refused": [(item, why)], "unknown": [(item, why)], "skipped": [item]}.
    An unknown item may be in the bank: the caller must check the bank before storing anything again."""
    blocked_reason = _guard()
    token = token or uuid.uuid4().hex[:12]
    items = items_for(report, keep, repository, token)
    if marker_only:
        items = items[-1:]
    result = {"token": token, "stored": [], "refused": [], "unknown": [], "skipped": []}
    for position, item in enumerate(items):
        blocked = blocked_reason(json.dumps(item, ensure_ascii=False), forbid)
        status, why = ("refused", blocked) if blocked else post(base, bank, item)
        if status == "stored":
            result["stored"].append(item_name(item))
            continue
        result[status].append((item_name(item), why))
        result["skipped"] = [item_name(i) for i in items[position + 1:]]
        break
    return result


def repository_of(folder: Path) -> Path | None:
    """The top of the git repository that holds the review archive, or None."""
    try:
        top = subprocess.run(["git", "-C", str(folder), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return Path(top.stdout.strip()).resolve() if top.returncode == 0 and top.stdout.strip() else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mine the review archive for recurring failure classes.")
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--since", type=int, default=0, help="report only lessons with a file numbered above this")
    parser.add_argument("--keep", action="append", default=[], metavar="CLASS",
                        help="with --retain: a class to store, named after reading its hits; repeatable")
    parser.add_argument("--mark-run", action="store_true",
                        help="with --retain and --run-token: store only the marker of that run, after every kept "
                             "lesson of it was stored")
    parser.add_argument("--run-token", help="the RUN TOKEN an earlier, unfinished run printed; a retry reuses it")
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
    unknown = sorted(set(args.keep) - set(CLASS_IDS))
    if unknown:
        print(f"ERROR: unknown --keep class {', '.join(unknown)}; known: {', '.join(CLASS_IDS)}", file=sys.stderr)
        return 2
    if args.keep and not args.retain:
        print("ERROR: --keep goes with --retain", file=sys.stderr)
        return 2
    if args.retain and not (args.repository and REPO_RE.match(args.repository)):
        print("ERROR: --retain needs --repository owner/name", file=sys.stderr)
        return 2
    if args.mark_run and (args.keep or not args.retain or not args.run_token):
        print("ERROR: --mark-run goes with --retain and the --run-token of the unfinished run, without --keep",
              file=sys.stderr)
        return 2
    if args.run_token and not re.fullmatch(r"[0-9a-f]{12}", args.run_token):
        print("ERROR: --run-token is the 12-character RUN TOKEN a run printed", file=sys.stderr)
        return 2
    if args.retain and not args.keep and not args.mark_run:
        print("ERROR: --retain stores only the classes you name: read the report, then add --keep CLASS "
              "for each real lesson", file=sys.stderr)
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
    report = mine(folder, args.since)
    candidates = {e["class"] for e in report["lessons"] + report["doubtful"]}
    not_candidates = sorted(set(args.keep) - candidates)
    if not_candidates:
        print(f"ERROR: --keep {', '.join(not_candidates)} is not past the noise guard in this report "
              f"(candidates: {', '.join(sorted(candidates)) or 'none'})", file=sys.stderr)
        return 2
    text = render(report)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")  # a cp1251 console cannot print every character
    print(json.dumps(report, indent=2) if args.json else text)
    if args.retain:
        result = retain(report, args.keep, args.retain, args.bank, args.repository, forbid,
                        token=args.run_token, marker_only=args.mark_run)
        print(f"RUN TOKEN: {result['token']}", file=sys.stderr)
        print(f"STORED: {', '.join(result['stored']) or 'nothing'}", file=sys.stderr)
        for name, reason in result["refused"]:
            print(f"NOT STORED {name}: {reason}", file=sys.stderr)
        for name, reason in result["unknown"]:
            print(f"UNKNOWN {name}: {reason}. The server may have stored it.", file=sys.stderr)
        for name in result["skipped"]:
            print(f"NOT SENT {name}: an earlier item was not stored for sure", file=sys.stderr)
        if result["unknown"]:
            print(f"Do not run the store again yet. First recall from the bank with the tags of the unknown item "
                  f"and look for metadata lessons_run = {result['token']}: if it is there, it was stored. Then "
                  f"store only what is still missing, with --run-token {result['token']} and --keep for lessons, "
                  f"or --mark-run for the marker.", file=sys.stderr)
        elif result["refused"]:
            left = [n.split(":", 1)[1] for n in [result["refused"][0][0], *result["skipped"]] if n.startswith("lesson:")]
            retry = (f"--run-token {result['token']} --keep {' --keep '.join(left)}" if left else
                     f"--run-token {result['token']} --mark-run (every kept lesson is stored)")
            print(f"The run marker was not stored. After fixing the cause, run again with the same --since and "
                  f"{retry}.", file=sys.stderr)
        return 3 if result["refused"] or result["unknown"] else 0
    return 0


if __name__ == "__main__":
    from console_io import prepare_console
    prepare_console()
    sys.exit(main())
