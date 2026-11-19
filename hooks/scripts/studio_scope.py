"""Scope guard and small helpers shared by the GameDev Studio hooks.

Python 3 standard library only. Every hook calls `is_studio_dir()` first and
exits silently when it is False, so the plugin is a no-op in every project that
is not a GameDev Studio project.

A directory belongs to a GameDev Studio project when the nearest ancestor that
holds either a `.gamedev-studio` marker file or a `.git` entry

  * has the marker file `.gamedev-studio` (game repositories carry it), or
  * is a git repository whose `origin` remote is github.com/ZMSkif/GameDev-AGI-Studio.

The check reads files only (no subprocess) and understands linked worktrees
(`.git` file with `gitdir:` plus `commondir`), so it also works when `git` is
missing and costs well under a millisecond outside a studio project.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

MARKER = ".gamedev-studio"
STUDIO_SLUG = "ZMSkif/GameDev-AGI-Studio"
PROTECTED_BRANCHES = ("main", "master")

# https://github.com/ZMSkif/GameDev-AGI-Studio(.git), ssh://git@github.com/...,
# git@github.com:ZMSkif/..., git://github.com/...; exact match, case-insensitive.
_ORIGIN_RE = re.compile(
    r"^(?:https?://(?:[^/@]+@)?github\.com(?::\d+)?/"
    r"|ssh://(?:[^/@]+@)?github\.com(?::\d+)?/"
    r"|git://github\.com/"
    r"|(?:[^/@:\s]+@)?github\.com:)"
    + re.escape(STUDIO_SLUG)
    + r"(?:\.git)?/?$",
    re.IGNORECASE,
)


def debug(msg: str) -> None:
    if os.environ.get("GAMEDEV_STUDIO_HOOK_DEBUG"):
        sys.stderr.write("gamedev-studio hook: %s\n" % msg)


def is_studio_origin(url: str) -> bool:
    return bool(_ORIGIN_RE.match((url or "").strip()))


def find_project(start: str):
    """Return (root, git_entry_or_None) of the nearest marker/.git ancestor, or None."""
    try:
        cur = os.path.abspath(start)
    except (OSError, ValueError, TypeError):
        return None
    while True:
        if os.path.isfile(os.path.join(cur, MARKER)):
            git = os.path.join(cur, ".git")
            return cur, (git if os.path.exists(git) else None)
        git = os.path.join(cur, ".git")
        if os.path.exists(git):
            return cur, git
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def git_dirs(root: str, git_entry: str):
    """Return (gitdir, commondir) for a repository root, following worktree links."""
    gitdir = git_entry
    if os.path.isfile(git_entry):
        text = _read(git_entry).strip()
        if not text.startswith("gitdir:"):
            return None
        gitdir = text[len("gitdir:"):].strip()
        if not os.path.isabs(gitdir):
            gitdir = os.path.normpath(os.path.join(root, gitdir))
    common = gitdir
    common_file = os.path.join(gitdir, "commondir")
    if os.path.isfile(common_file):
        value = _read(common_file).strip()
        common = value if os.path.isabs(value) else os.path.normpath(os.path.join(gitdir, value))
    return gitdir, common


_SECTION_RE = re.compile(r"^\s*\[\s*([A-Za-z0-9.-]+)(?:\s+\"((?:[^\"\\]|\\.)*)\")?\s*\]")
_URL_RE = re.compile(r"^\s*url\s*=\s*(.*?)\s*$", re.IGNORECASE)


def read_origin_url(root: str, git_entry: str):
    dirs = git_dirs(root, git_entry)
    if not dirs:
        return None
    config = os.path.join(dirs[1], "config")
    if not os.path.isfile(config):
        return None
    in_origin = False
    for line in _read(config).splitlines():
        header = _SECTION_RE.match(line)
        if header:
            in_origin = header.group(1).lower() == "remote" and header.group(2) == "origin"
            continue
        if in_origin:
            match = _URL_RE.match(line)
            if match:
                return match.group(1).strip().strip('"')
    return None


def is_studio_dir(path) -> bool:
    """True when `path` lies inside a GameDev Studio project. Never raises."""
    try:
        if not path or not os.path.isdir(path):
            return False
        project = find_project(path)
        if not project:
            return False
        root, git_entry = project
        if os.path.isfile(os.path.join(root, MARKER)):
            return True
        if not git_entry:
            return False
        return is_studio_origin(read_origin_url(root, git_entry) or "")
    except Exception as exc:  # fail closed on scope = silent no-op
        debug("scope check failed: %r" % (exc,))
        return False


def session_dirs(payload) -> list:
    """Directories that define the session's project: the payload cwd and CLAUDE_PROJECT_DIR.

    A missing, non-string or non-existent payload cwd is malformed input and yields no directories
    (the hook then stays silent); the process cwd is never used.
    """
    cwd = payload.get("cwd") if isinstance(payload, dict) else None
    if not isinstance(cwd, str) or not cwd or not os.path.isdir(cwd):
        return []
    dirs = [cwd]
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    if isinstance(project, str) and project and project not in dirs:
        dirs.append(project)
    return dirs


def session_in_scope(payload) -> bool:
    return any(is_studio_dir(d) for d in session_dirs(payload))


def read_payload():
    """Parse the hook JSON from stdin. Returns a dict, or None if absent/malformed."""
    try:
        raw = sys.stdin.buffer.read()
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception as exc:
        debug("no/invalid JSON payload: %r" % (exc,))
        return None
    return data if isinstance(data, dict) else None


def emit(obj) -> None:
    # ASCII-only JSON, LF line ending, written as bytes: identical on every console code page.
    sys.stdout.buffer.write((json.dumps(obj) + "\n").encode("ascii"))
    sys.stdout.buffer.flush()


def run_git(directory: str, args, timeout: float = 5.0):
    """Run git in `directory`; return CompletedProcess(bytes) or None when git is unusable."""
    try:
        return subprocess.run(
            ["git", "-C", directory] + list(args),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            env=dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0"),
        )
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        debug("git %s failed: %r" % (args, exc))
        return None


def current_branch(directory: str):
    """Short name of the checked-out branch (works on an unborn branch); None if detached/unknown."""
    done = run_git(directory, ["symbolic-ref", "--short", "-q", "HEAD"])
    if done is not None:
        if done.returncode == 0:
            name = done.stdout.decode("utf-8", errors="replace").strip()
            return name or None
        if done.returncode == 1:  # not a symbolic ref: detached HEAD
            return None
    # git unavailable or refused: read HEAD directly (files backend only)
    try:
        project = find_project(directory)
        if not project or not project[1]:
            return None
        dirs = git_dirs(*project)
        head = _read(os.path.join(dirs[0], "HEAD")).strip()
        if head.startswith("ref: refs/heads/"):
            return head[len("ref: refs/heads/"):]
    except Exception as exc:
        debug("HEAD read failed: %r" % (exc,))
    return None


def head_exists(directory: str):
    """True if HEAD resolves to a commit, False if it is unborn (empty repository), None if unknown."""
    done = run_git(directory, ["rev-parse", "--verify", "-q", "HEAD"])
    if done is None:
        return None
    if done.returncode == 0:
        return True
    return False if done.returncode == 1 else None


def fail_open(func):
    """Run a hook main(); any internal error exits 0 silently (a crashed hook must not block work)."""
    try:
        func()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001
        debug("internal error: %r" % (exc,))
    sys.exit(0)
