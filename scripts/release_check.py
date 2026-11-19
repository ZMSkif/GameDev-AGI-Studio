#!/usr/bin/env python3
"""Release checks for a `vX.Y.Z` tag: versions agree and the CHANGELOG has the notes. Stdlib only.

  * the tag is `v` + the version in both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`;
  * `CHANGELOG.md` has a `## [X.Y.Z] - YYYY-MM-DD` section with text in it;
  * with --notes-out, that section's body is written there for the release notes.

Usage: python scripts/release_check.py --tag v0.3.0 [--root .] [--notes-out notes.md]
Exit codes: 0 ok, 1 a check failed, 2 bad arguments.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"^v(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)$")
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")


def section(changelog: str, version: str) -> str | None:
    """The body of the `## [version] - date` section, without its heading; None when absent."""
    heading = re.compile(rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\s*$", re.M)
    match = heading.search(changelog)
    if not match:
        return None
    rest = changelog[match.end():]
    following = re.search(r"^## \[", rest, re.M)
    return (rest[:following.start()] if following else rest).strip()


def check(root: Path, tag: str) -> tuple[list[str], str]:
    errors: list[str] = []
    match = TAG_RE.match(tag)
    if not match:
        return [f"tag {tag!r} is not v<major>.<minor>.<patch>"], ""
    version = match.group(1)
    for rel in MANIFESTS:
        try:
            found = json.loads((root / rel).read_text(encoding="utf-8")).get("version")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{rel}: cannot read ({exc})")
            continue
        if found != version:
            errors.append(f"{rel}: version {found!r} does not match tag {tag}")
    try:
        notes = section((root / "CHANGELOG.md").read_text(encoding="utf-8"), version)
    except OSError as exc:
        return errors + [f"CHANGELOG.md: cannot read ({exc})"], ""
    if not notes:
        errors.append(f"CHANGELOG.md: no non-empty '## [{version}] - YYYY-MM-DD' section")
    return errors, notes or ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a release tag against the plugin versions and CHANGELOG.")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--notes-out")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    errors, notes = check(Path(args.root), args.tag)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    if args.notes_out:
        Path(args.notes_out).write_text(notes + "\n", encoding="utf-8", newline="\n")
    print(f"{args.tag}: versions match and CHANGELOG has the notes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
