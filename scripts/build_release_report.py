#!/usr/bin/env python3
"""Inventory a local build ZIP and summarize browser QA as separate evidence."""

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from review_evidence import ISSUE_URL


PLATFORMS = ("playgama", "youtube-playables")
CHECK_KINDS = {"navigation", "step", "within", "no_overlap"}


def inventory(path):
    with path.open("rb") as source:
        with ZipFile(source) as archive:
            files = [
                {"path": entry.filename, "bytes": entry.file_size, "compressed_bytes": entry.compress_size}
                for entry in archive.infolist() if not entry.is_dir()
            ]
        source.seek(0)
        digest = hashlib.sha256()
        size = 0
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {
        "name": path.name,
        "archive_bytes": size,
        "sha256": digest.hexdigest(),
        "file_count": len(files),
        "uncompressed_bytes": sum(entry["bytes"] for entry in files),
        "compressed_member_bytes": sum(entry["compressed_bytes"] for entry in files),
        "files": files,
    }


def field(document, key, expected):
    if not isinstance(document, dict) or type(document.get(key)) is not expected:
        raise ValueError(f"Invalid QA summary field: {key}")
    return document[key]


def load_candidate_qa(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if field(data, "version", int) != 1:
        raise ValueError("Unsupported QA summary version")
    issue = field(data, "issue", str)
    if not ISSUE_URL.fullmatch(issue):
        raise ValueError("Expected the QA summary to link a GitHub issue")
    build = field(field(data, "builds", dict), "after", dict)
    commit = field(build, "commit", str)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected a full candidate Git commit in QA summary")
    viewports = []
    names = set()
    for viewport in field(data, "viewports", list):
        name = field(viewport, "name", str)
        if not name.strip() or name in names:
            raise ValueError("Expected unique names for QA viewports")
        names.add(name)
        after = field(field(viewport, "builds", dict), "after", dict)
        startup = after.get("ready_ms")
        if startup is not None and (type(startup) not in (int, float)
                                    or not 0 <= startup <= sys.float_info.max
                                    or not math.isfinite(startup)):
            raise ValueError(f"Invalid ready_ms for viewport {name}")
        checks = []
        for check in field(after, "checks", list):
            label = field(check, "name", str)
            kind = field(check, "type", str)
            if kind not in CHECK_KINDS or not label.strip():
                raise ValueError(f"Invalid check name or type for viewport {name}")
            checks.append({
                "name": label,
                "type": kind,
                "passed": field(check, "passed", bool),
                "detail": field(check, "detail", str),
            })
        errors = field(after, "errors", list)
        if any(not isinstance(error, str) for error in errors):
            raise ValueError(f"Invalid browser error for viewport {name}")
        viewports.append({
            "name": name,
            "ready_ms": startup,
            "scenario_passed": field(after, "scenario_passed", bool),
            "errors": errors,
            "checks": checks,
        })
    if not viewports:
        raise ValueError("QA summary must contain a viewport")
    return {"issue": issue, "candidate_commit": commit, "viewports": viewports}


def named_check(viewports, name):
    if not name:
        return {"status": "not_run"}
    observations = []
    for viewport in viewports:
        matches = [check for check in viewport["checks"]
                   if check["type"] == "step" and check["name"] == name]
        if len(matches) > 1:
            raise ValueError(f"Ambiguous step {name!r} for viewport {viewport['name']}")
        observations.append({
            "viewport": viewport["name"],
            "status": ("passed" if matches[0]["passed"] else "failed") if matches else "not_run",
        })
    statuses = {entry["status"] for entry in observations}
    if "failed" in statuses:
        status = "failed"
    elif statuses == {"passed"}:
        status = "passed"
    elif "passed" in statuses:
        status = "incomplete"
    else:
        status = "not_run"
    return {"status": status, "step": name, "observations": observations}


def build_report(archive, qa_result, platforms, limit, pause_check, save_check):
    build = inventory(archive)
    qa = load_candidate_qa(qa_result) if qa_result else None
    viewports = qa["viewports"] if qa else []
    budget = {"status": "not_run"}
    if limit is not None:
        budget = {
            "status": "passed" if build["archive_bytes"] <= limit else "failed",
            "max_archive_bytes": limit,
        }
    return {
        "version": 1,
        "archive": build,
        "archive_budget": budget,
        "candidate_browser_qa": qa,
        "archive_browser_match": {"status": "unverified"} if qa else {"status": "not_run"},
        "pause": named_check(viewports, pause_check),
        "save": named_check(viewports, save_check),
        "platforms": [{"name": platform, "status": "unverified"} for platform in dict.fromkeys(platforms)],
    }


def positive_bytes(value):
    size = int(value)
    if size <= 0:
        raise argparse.ArgumentTypeError("Expected a positive byte count")
    return size


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="The archive SHA-256 identifies the ZIP. Browser QA describes the served build recorded "
               "in the supplied summary. Matching those bytes requires separate verification.",
    )
    parser.add_argument("--archive", type=Path, required=True, help="Local ZIP to inventory")
    parser.add_argument("--out", type=Path, required=True, help="New JSON report path")
    parser.add_argument("--qa-result", type=Path, help="summary.json from capture_review.py")
    parser.add_argument("--platform", choices=PLATFORMS, action="append", default=[],
                        help="Record a target as unverified. Repeat for multiple targets.")
    parser.add_argument("--max-archive-bytes", type=positive_bytes)
    parser.add_argument("--pause-check", help="Exact name of the scenario step asserting pause behavior")
    parser.add_argument("--save-check", help="Exact name of the scenario step asserting save behavior")
    args = parser.parse_args(argv)
    if not args.qa_result and (args.pause_check or args.save_check):
        parser.error("Named checks require --qa-result")
    try:
        report = build_report(
            args.archive, args.qa_result, args.platform, args.max_archive_bytes, args.pause_check, args.save_check
        )
        with args.out.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(report, output, ensure_ascii=False, allow_nan=False, indent=2)
            output.write("\n")
    except (BadZipFile, OSError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Release report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
