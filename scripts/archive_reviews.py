#!/usr/bin/env python3
"""Archive independent reviewer verdicts verbatim from Claude Code session transcripts.

Generalised from the coordinator script of the Cat Challenge project, which saved 66
verdicts to docs/reviews/ (orchestration-playbook skill). Stdlib only.

What it does:
  * reads one or more session transcripts (JSONL; a directory means every *.jsonl in it,
    oldest first);
  * finds <task-notification> blocks in message text (never in tool results) whose
    <result> contains a verdict line such as "VERDICT: BLOCKED" or
    "VERDICT (round 2): CONFIRMED";
  * de-duplicates by content: the SHA-256 of the normalised body, within this run and
    against every file already in the archive (a re-run writes nothing new);
  * numbers new files after the highest number already in the archive, so existing names
    never shift: <YYYY-MM-DD>_<NN>_<slug>_<verdict>.md;
  * writes the body verbatim under a small header: only the notification's XML escaping
    (&lt; &gt; &amp;) is undone, and a final newline is added when the body has none;
  * never writes a body that looks like it holds a secret (patterns shared with
    scripts/validate_plugin.py) or that matches a --forbid pattern (for example the
    owner's e-mail or a local path); such bodies are reported and the exit code is 3.

Usage:
  python scripts/archive_reviews.py --transcript <file-or-dir> [--transcript ...]
                                    --out docs/reviews [--dry-run] [--forbid REGEX ...]
Exit codes: 0 ok, 2 bad arguments, 3 some verdicts were skipped for review by a human.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

NOTIFICATION_RE = re.compile(r"<task-notification>(.*?)</task-notification>", re.S)
RESULT_RE = re.compile(r"<result>(.*)</result>", re.S)
SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.S)
VERDICT_RE = re.compile(r"VERDICT[^:\n]{0,30}:\s*\**\s*([A-Z][A-Z_]*)")
ARCHIVE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_(\d+)_")
HASH_LINE_RE = re.compile(r"^- Body SHA-256: ([0-9a-f]{64})\s*$", re.M)
HEADER_END = "\n---\n\n"
SLUG_MAX = 50


def _load_secret_patterns():
    """The secret patterns of validate_plugin.py, so both tools flag the same values."""
    path = Path(__file__).resolve().parent / "validate_plugin.py"
    spec = importlib.util.spec_from_file_location("_validate_plugin_patterns", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SECRET_VALUE_PATTERNS


SECRET_PATTERNS = _load_secret_patterns()


class Verdict:
    """One reviewer verdict: when it arrived, the task summary, its label and the body."""

    def __init__(self, timestamp: str, summary: str, label: str, body: str):
        self.timestamp, self.summary, self.label, self.body = timestamp, summary, label, body

    @property
    def digest(self) -> str:
        return body_digest(self.body)


def unescape(text: str) -> str:
    """Undo the XML escaping of a notification; &amp; last, so "&amp;lt;" stays "&lt;"."""
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def normalise(body: str) -> str:
    return body.replace("\r\n", "\n").strip()


def body_digest(body: str) -> str:
    return hashlib.sha256(normalise(body).encode("utf-8")).hexdigest()


def verdict_label(body: str) -> str | None:
    """One verdict -> its name; several different ones -> the last two joined."""
    found = VERDICT_RE.findall(body)
    if not found:
        return None
    unique = list(dict.fromkeys(found))
    if len(unique) == 1:
        return unique[0]
    return "-".join(found[-2:])


def texts_of(record: dict) -> list[str]:
    """The message text of a transcript record.

    Tool results are not read: background agents report in message text, and a tool result
    can quote a notification-shaped block (a `cat` of a test fixture) that is no report.
    On the Cat Challenge coordinator transcript all 68 verdicts were in message text.
    """
    message = record.get("message") or {}
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [p["text"] for p in content if isinstance(p, dict) and p.get("type") == "text" and isinstance(p.get("text"), str)]
    return []


def transcript_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files += sorted(path.glob("*.jsonl"), key=lambda p: (p.stat().st_mtime, p.name))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f"transcript not found: {raw}")
    return files


def extract(files: list[Path]) -> list[Verdict]:
    """Verdicts in transcript order, without repeats of the same body."""
    seen: set[str] = set()
    verdicts: list[Verdict] = []
    for file in files:
        with file.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict):
                    continue
                stamp = record.get("timestamp") if isinstance(record.get("timestamp"), str) else ""
                for text in texts_of(record):
                    for block in NOTIFICATION_RE.finditer(text):
                        result = RESULT_RE.search(block.group(1))
                        if not result:
                            continue
                        # Verbatim: only the transport escaping is undone. Normalising is for
                        # the de-duplication key alone (body_digest).
                        body = unescape(result.group(1))
                        label = verdict_label(body)
                        if label is None:
                            continue
                        digest = body_digest(body)
                        if digest in seen:
                            continue
                        seen.add(digest)
                        summary = SUMMARY_RE.search(block.group(1))
                        verdicts.append(Verdict(stamp, unescape(summary.group(1)).strip() if summary else "", label, body))
    return verdicts


def archived_digests(out: Path) -> tuple[set[str], int]:
    """Digests of the bodies already archived and the highest file number in use."""
    digests: set[str] = set()
    highest = 0
    if not out.is_dir():
        return digests, highest
    for path in out.glob("*.md"):
        match = ARCHIVE_NAME_RE.match(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
        text = path.read_text(encoding="utf-8", errors="replace")
        recorded = HASH_LINE_RE.search(text.split(HEADER_END, 1)[0])
        if recorded:
            digests.add(recorded.group(1))
        if HEADER_END in text:
            digests.add(body_digest(text.split(HEADER_END, 1)[1]))
    return digests, highest


def slugify(summary: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", summary.lower()).strip("-")[:SLUG_MAX].strip("-")
    return slug or "review"


def blocked_reason(body: str, forbid: list[re.Pattern]) -> str | None:
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(body):
            return f"secret-looking value ({label})"
    for pattern in forbid:
        if pattern.search(body):
            return f"matches --forbid {pattern.pattern!r}"
    return None


def render(verdict: Verdict) -> str:
    return (
        f"# Review: {verdict.summary or 'reviewer report'}\n\n"
        f"- Received: {verdict.timestamp or 'n/a'}\n"
        f"- Verdict: {verdict.label}\n"
        f"- Body SHA-256: {verdict.digest}\n"
        "- Source: independent reviewer agent report, saved verbatim by the coordinator.\n"
        f"{HEADER_END}{verdict.body}"
        f"{'' if verdict.body.endswith(chr(10)) else chr(10)}"
    )


def archive(files: list[Path], out: Path, *, dry_run: bool = False, forbid=(), today: str | None = None):
    """Write new verdicts; return (written file names, skipped (summary, reason) pairs)."""
    known, highest = archived_digests(out)
    fallback_day = today or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    written: list[str] = []
    skipped: list[tuple[str, str]] = []
    for verdict in extract(files):
        if verdict.digest in known:
            continue
        reason = blocked_reason(verdict.body, list(forbid))
        if reason:
            skipped.append((verdict.summary or verdict.label, reason))
            continue
        highest += 1
        day = verdict.timestamp[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", verdict.timestamp) else fallback_day
        name = f"{day}_{highest:02d}_{slugify(verdict.summary)}_{verdict.label.lower()}.md"
        if not dry_run:
            out.mkdir(parents=True, exist_ok=True)
            (out / name).write_text(render(verdict), encoding="utf-8", newline="\n")
        known.add(verdict.digest)
        written.append(name)
    return written, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--transcript", action="append", required=True, help="a session .jsonl file or a folder of them")
    parser.add_argument("--out", required=True, help="the archive folder, for example docs/reviews")
    parser.add_argument("--dry-run", action="store_true", help="list what would be written, write nothing")
    parser.add_argument("--forbid", action="append", default=[], help="regex; a body that matches is not written")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        forbid = [re.compile(p) for p in args.forbid]
        files = transcript_files(args.transcript)
    except (re.error, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    written, skipped = archive(files, Path(args.out), dry_run=args.dry_run, forbid=forbid)
    verb = "would write" if args.dry_run else "wrote"
    for name in written:
        print(f"{verb} {name}")
    for summary, reason in skipped:
        print(f"SKIPPED {summary!r}: {reason}; check it by hand", file=sys.stderr)
    print(f"{len(written)} new verdict(s), {len(skipped)} skipped")
    return 3 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
