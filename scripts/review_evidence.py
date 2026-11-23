#!/usr/bin/env python3
"""Build or verify a local review evidence manifest using the standard library."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath


ISSUE_URL = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/issues/[1-9][0-9]*", re.ASCII)
DECISION_URL = re.compile(
    r"https://github\.com/[\w.-]+/[\w.-]+/(?:issues|pull)/[1-9][0-9]*"
    r"(?:#issuecomment-[1-9][0-9]*)?",
    re.ASCII,
)
IMAGE_SUFFIXES = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
ROLES = {"before", "after", "clip", "build", "test", "source", "export", "reference", "step"}


def require_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{label} must contain exactly: {', '.join(sorted(expected))}")


def load_document(path, manifest):
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    keys = {"issue", "commit", "files"}
    require_keys(document, keys | {"version"} if manifest else keys, "Document")
    if manifest and (type(document["version"]) is not int or document["version"] != 1):
        raise ValueError("Unsupported manifest version")
    issue, commit, files = document["issue"], document["commit"], document["files"]
    if not isinstance(issue, str) or not ISSUE_URL.fullmatch(issue):
        raise ValueError("Expected the full GitHub Issue URL")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected a full, lowercase Git commit SHA")
    if not isinstance(files, list) or not files:
        raise ValueError("List at least one evidence file")

    paths = set()
    for index, entry in enumerate(files, 1):
        keys = {"path", "role"}
        if isinstance(entry, dict) and "decision_url" in entry:
            keys.add("decision_url")
        require_keys(entry, keys | {"sha256", "bytes"} if manifest else keys, f"File {index}")
        role = entry["role"]
        if not isinstance(role, str) or role not in ROLES:
            raise ValueError(f"File {index} has an unsupported role")
        name = entry["path"]
        if not isinstance(name, str) or re.search(r'[\\:*?"<>|\x00-\x1f]', name):
            raise ValueError(f"File {index} must use a relative path with forward slashes")
        parts = name.split("/")
        if any(not part or part.endswith((".", " ")) for part in parts):
            raise ValueError(f"File {index} must use a normalized relative path")
        if name.casefold() in paths:
            raise ValueError(f"Duplicate evidence path: {name}")
        paths.add(name.casefold())
        if role == "reference" and PurePosixPath(name).suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError(f"File {index} must be a raster image for a reference")
        if "decision_url" in entry:
            url = entry["decision_url"]
            if role != "reference" or not isinstance(url, str) or not DECISION_URL.fullmatch(url):
                raise ValueError(f"File {index} decision_url must link a reference to a GitHub issue or pull request")
        if manifest:
            sha, size = entry["sha256"], entry["bytes"]
            if (not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha)
                    or type(size) is not int or size < 0):
                raise ValueError(f"File {index} has an invalid hash or byte count")
    if all(entry["role"] in {"source", "reference"} for entry in files):
        raise ValueError("Include at least one output or capture")
    return document


def measure(root, entry):
    path = (root / PurePosixPath(entry["path"])).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Expected a regular file inside the evidence root")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"sha256": digest.hexdigest(), "bytes": size}


def build(root, plan, out):
    document = load_document(plan, manifest=False)
    files = [{**entry, **measure(root, entry)} for entry in document["files"]]
    rendered = json.dumps({"version": 1, **document, "files": files}, ensure_ascii=False, indent=2) + "\n"
    if out is None:
        print(rendered, end="")
        return
    with out.open("x", encoding="utf-8", newline="\n") as file:
        file.write(rendered)


def verify(root, manifest):
    document = load_document(manifest, manifest=True)
    failures = []
    for entry in document["files"]:
        name = entry["path"]
        try:
            actual = measure(root, entry)
        except (ValueError, OSError, RuntimeError) as error:
            failures.append(f"{name}: {error}")
            continue
        if actual != {key: entry[key] for key in actual}:
            failures.append(f"{name}: bytes or SHA-256 changed")
    if failures:
        raise ValueError("\n".join(failures))
    print(f"Verified {len(document['files'])} evidence file(s)")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    create = actions.add_parser("build")
    create.add_argument("--root", type=Path, required=True)
    create.add_argument("--plan", type=Path, required=True)
    create.add_argument("--out", type=Path)
    check = actions.add_parser("verify")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("The evidence root must be a directory")
        if args.action == "build":
            build(root, args.plan, args.out)
        else:
            verify(root, args.manifest)
    except (ValueError, OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    from console_io import prepare_console
    prepare_console()
    raise SystemExit(main())
