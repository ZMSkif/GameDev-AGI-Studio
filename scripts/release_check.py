#!/usr/bin/env python3
"""Release checks for a `vX.Y.Z` tag: versions agree and the CHANGELOG has the notes. Stdlib only.

  * the tag is `v` + the version in both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`;
    a release version is plain X.Y.Z (no pre-release or build part);
  * `CHANGELOG.md` has exactly one `## [X.Y.Z] - YYYY-MM-DD` section, with a real date and at least
    one line that is not a heading;
  * with --notes-out, that section's body is written there for the release notes.

Usage: python scripts/release_check.py --tag v0.4.0 [--root .] [--notes-out notes.md]
Exit codes: 0 ok, 1 a check failed, 2 bad arguments.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"v([0-9]+\.[0-9]+\.[0-9]+)")
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")


def headings(changelog: str, version: str) -> list[re.Match]:
    pattern = re.compile(rf"^## \[{re.escape(version)}\] - ([0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})[ \t]*$", re.M)
    return list(pattern.finditer(changelog))


def section(changelog: str, version: str) -> str | None:
    """The body of the first `## [version] - date` section, without its heading; None when absent."""
    found = headings(changelog, version)
    if not found:
        return None
    rest = changelog[found[0].end():]
    following = re.search(r"^## \[", rest, re.M)
    return (rest[:following.start()] if following else rest).strip()


def check(root: Path, tag: str) -> tuple[list[str], str]:
    errors: list[str] = []
    match = TAG_RE.fullmatch(tag)
    if not match:
        return [f"tag {tag!r} is not v<major>.<minor>.<patch>"], ""
    version = match.group(1)
    for rel in MANIFESTS:
        try:
            manifest = json.loads((root / rel).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{rel}: cannot read ({exc})")
            continue
        found = manifest.get("version") if isinstance(manifest, dict) else None
        if found != version:
            errors.append(f"{rel}: version {found!r} does not match tag {tag}")
    try:
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return errors + [f"CHANGELOG.md: cannot read ({exc})"], ""
    found = headings(changelog, version)
    if len(found) > 1:
        errors.append(f"CHANGELOG.md: {len(found)} sections for {version}; keep one")
    if found:
        try:
            _dt.date.fromisoformat(found[0].group(1))
        except ValueError:
            errors.append(f"CHANGELOG.md: {found[0].group(1)} is not a real date")
    notes = section(changelog, version)
    if not notes or not any(line.strip() and not line.startswith("#") for line in notes.splitlines()):
        errors.append(f"CHANGELOG.md: no '## [{version}] - YYYY-MM-DD' section with text in it")
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
    if not errors and args.notes_out:
        try:
            Path(args.notes_out).write_text(notes + "\n", encoding="utf-8", newline="\n")
        except OSError as exc:
            errors.append(f"--notes-out: cannot write ({exc})")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"{args.tag}: versions match and CHANGELOG has the notes")
    return 0


if __name__ == "__main__":
    from console_io import prepare_console
    prepare_console()
    sys.exit(main())
