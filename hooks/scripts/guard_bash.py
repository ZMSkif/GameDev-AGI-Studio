#!/usr/bin/env python3
"""PreToolUse hook (Claude Code Bash/PowerShell tools, Codex Bash tool) for GameDev Studio projects.

Rule 1 (decision #1): no direct commits or pushes to main/master. Open a branch + PR.
Rule 2 (decision #9): never stage or commit credential-like files.

Reads the hook JSON from stdin. Allowed -> exit 0 with no output. Blocked -> prints a
`permissionDecision: "deny"` JSON (accepted by Claude Code and Codex) and exits 0.
Outside a GameDev Studio project, or on malformed input or any internal error, it
exits 0 silently (fail open).
"""
import fnmatch
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import studio_scope as scope  # noqa: E402
import studio_shell as shell  # noqa: E402

SECRET_GLOBS = ("*.pem", "*.key", "id_rsa*", "id_ed25519*", "id_ecdsa*", "id_dsa*", "*.p12", "*.pfx", "*.ppk",
                "*.jks", "*.keystore")
ENV_TEMPLATE_SUFFIXES = ("example", "sample", "template")

BRANCH_HELP = (
    "Create a branch (for example `git switch -c feat/<TASK>-<slug>`) or a worktree, commit there "
    "and open a pull request. Never write directly to main/master."
)


def is_credential_path(path: str) -> bool:
    base = os.path.basename(str(path).replace("\\", "/")).lower()
    if not base or base.endswith(".pub"):  # public keys are not secrets
        return False
    if base == ".env":
        return True
    if base.startswith(".env."):
        return base.rsplit(".", 1)[-1] not in ENV_TEMPLATE_SUFFIXES
    return any(fnmatch.fnmatchcase(base, pattern) for pattern in SECRET_GLOBS)


def deny(reason: str) -> None:
    scope.emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })
    sys.exit(0)


# ---- rule 1 ---------------------------------------------------------------------------

_PUSH_VALUE_OPTS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
_RECURSE_VALUES = {"check", "on-demand", "only", "no"}


_FORCE_FLAGS = {"-f", "--force", "--force-if-includes"}


def remote_lacks_branch(directory: str, remote, branch: str):
    """True only when `git ls-remote --exit-code --heads` proves the remote has no such branch (exit 2)."""
    args = ["ls-remote", "--exit-code", "--heads", remote or "origin", branch]
    done = scope.run_git(directory, args, timeout=5.0)
    return done is not None and done.returncode == 2


def check_push(directory: str, head_branch, args):
    """Return a deny reason if this `git push` would update main/master.

    Decision #1 allows the initial commit into an empty repository, so a plain (non-force) push of
    main/master is allowed when the remote has no such branch yet.
    """
    positional = []
    flags = set()
    repo_opt = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            positional.extend(args[i + 1:])
            break
        if a in _PUSH_VALUE_OPTS:
            if a == "--repo" and i + 1 < len(args):
                repo_opt = args[i + 1]
            i += 2
            continue
        if a == "--recurse-submodules" and i + 1 < len(args) and args[i + 1] in _RECURSE_VALUES:
            i += 2
            continue
        if a.startswith("--repo="):
            repo_opt = a[len("--repo="):]
        if a.startswith("-") and len(a) > 1:
            flags.add(a)
            if not a.startswith("--") and len(a) > 2:  # clustered short flags such as -fu / -nv
                flags.update("-" + ch for ch in a[1:])
        else:
            positional.append(a)
        i += 1

    if flags & {"-n", "--dry-run"}:
        return None
    if flags & {"--all", "--mirror"}:
        which = "--all" if "--all" in flags else "--mirror"
        return "`git push %s` would update main/master." % which

    remote = repo_opt if repo_opt else (positional[0] if positional else None)
    refspecs = positional if repo_opt else positional[1:]
    forced = (bool(flags & _FORCE_FLAGS) or any(f.startswith("--force") for f in flags)
              or any(spec.startswith("+") for spec in refspecs))
    deleting = bool(flags & {"-d", "--delete"})

    targets = []
    if not refspecs:
        if "--tags" in flags:
            return None  # tags only; no branch is updated
        targets.append(head_branch())  # implicit push of the current branch
    for spec in refspecs:
        spec = spec[1:] if spec.startswith("+") else spec
        src, sep, dst = spec.partition(":")
        if not sep:
            dst = src
        elif not dst:
            continue
        elif not src:
            deleting = True  # `:main` deletes the remote branch
        if dst == "HEAD":
            dst = head_branch() or ""
        if dst.startswith("refs/heads/"):
            dst = dst[len("refs/heads/"):]
        targets.append(dst)
    for dst in targets:
        if not dst or not any(fnmatch.fnmatchcase(p, dst) for p in scope.PROTECTED_BRANCHES):
            continue
        if forced or deleting or dst not in scope.PROTECTED_BRANCHES:
            return "`git push` would update %s on the remote." % dst
        if not remote_lacks_branch(directory, remote, dst):
            return ("`git push` of %s is only allowed as the initial push into an empty remote, and `git ls-remote` "
                    "did not confirm that %s is absent (it exists, or the check failed or timed out)." % (dst, dst))
    return None


# ---- rule 2 ---------------------------------------------------------------------------

_COMMIT_VALUE_SHORT = set("mFCct")
_COMMIT_VALUE_LONG = {"--message", "--file", "--author", "--date", "--reuse-message", "--reedit-message",
                      "--fixup", "--squash", "--template", "--cleanup", "--pathspec-from-file", "--trailer"}


def commit_args(args):
    """Return (stage_all, paths) from `git commit` arguments."""
    stage_all = False
    paths = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            paths.extend(args[i + 1:])
            break
        if a.startswith("--"):
            if a in ("--all",):
                stage_all = True
            if a in _COMMIT_VALUE_LONG:
                i += 1
        elif a.startswith("-") and len(a) > 1:
            for k, ch in enumerate(a[1:], 1):
                if ch == "a":
                    stage_all = True
                elif ch in _COMMIT_VALUE_SHORT:
                    if k == len(a) - 1:
                        i += 1  # value is the next argument
                    break
        else:
            paths.append(a)
        i += 1
    return stage_all, paths


def _names(done):
    if done is None or done.returncode != 0:
        return []
    return [n.decode("utf-8", errors="replace") for n in done.stdout.split(b"\0") if n]


def credential_hits(paths):
    return sorted({p for p in paths if is_credential_path(p)})


def check_add(directory: str, args):
    flags = {a for a in args if a.startswith("-")}
    if flags & {"-n", "--dry-run"}:
        return None
    positional = [a for a in args if not a.startswith("-") or a == "-"]
    hits = credential_hits(positional)
    if not hits and not (flags & {"-p", "--patch", "-i", "--interactive", "-e", "--edit"}):
        done = scope.run_git(directory, ["-c", "core.quotepath=false", "add", "--dry-run"] + list(args), timeout=8)
        if done is not None and done.returncode == 0:
            staged = []
            for line in done.stdout.decode("utf-8", errors="replace").splitlines():
                if line.startswith("add '") and line.endswith("'"):
                    staged.append(line[5:-1])
            hits = credential_hits(staged)
    if hits:
        return "`git add` would stage credential-like file(s): %s." % ", ".join(hits)
    return None


def check_commit(directory: str, args):
    flags = {a for a in args if a.startswith("--")}
    if "--dry-run" in flags:
        return None
    stage_all, paths = commit_args(args)
    candidates = list(paths)
    candidates += _names(scope.run_git(directory, ["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]))
    if stage_all:
        candidates += _names(scope.run_git(directory, ["diff", "--name-only", "--diff-filter=ACMR", "-z"]))
    hits = credential_hits(candidates)
    if hits:
        return "`git commit` would include credential-like file(s): %s." % ", ".join(hits)
    return None


# ---- branch tracking inside one command line --------------------------------------------
# `git checkout -b feat/x && git commit` is legitimate: the branch at hook time is not the branch
# the commit lands on, so branch-changing commands earlier in the same line are simulated.

_SWITCH_CREATE = {"-b", "-B", "-c", "-C", "--create", "--force-create", "--orphan"}


def simulated_branch(directory: str, sub: str, args, current):
    """Return (known, branch) after `git checkout|switch ...`; known=False when unchanged/unknown."""
    if "--" in args:
        cut = args.index("--")
        if cut < len(args) - 1:  # `git checkout <tree-ish> -- <paths>` restores files, it does not switch
            return False, current
        args = args[:cut]
    i = 0
    positional = []
    while i < len(args):
        a = args[i]
        if a in _SWITCH_CREATE and i + 1 < len(args):
            return True, args[i + 1]
        if a.startswith(("-b", "-B")) and len(a) > 2 and sub == "checkout":
            return True, a[2:]
        if a in ("-d", "--detach"):
            return True, None
        if not a.startswith("-"):
            positional.append(a)
        i += 1
    if len(positional) == 1:
        name = positional[0]
        done = scope.run_git(directory, ["show-ref", "--verify", "--quiet", "refs/heads/" + name])
        if done is not None and done.returncode == 0:
            return True, name
        if sub == "switch":
            return True, name
    return False, current


# ---- driver ---------------------------------------------------------------------------

_WATCHED = {"commit", "push", "add", "checkout", "switch", "merge", "cherry-pick", "revert", "rebase"}
_HISTORY_REWRITERS = {"merge", "cherry-pick", "revert", "rebase"}
_HISTORY_ESCAPES = {"--abort", "--continue", "--quit", "--skip"}


def evaluate(command: str, session_cwd: str, powershell: bool = False):
    """Return (rule, reason) for the first violating git invocation in `command`, else None.

    rule is "branch" (decision #1) or "credentials" (decision #9).
    """
    cur = session_cwd
    simulated = {}  # normalised directory -> simulated branch name (None = detached)

    def branch_of(directory):
        key = os.path.normcase(os.path.abspath(directory))
        if key in simulated:
            return simulated[key]
        return scope.current_branch(directory)

    for event in shell.parse(command, powershell=powershell):
        if event[0] == "cd":
            # unknown target (variable, command substitution, missing dir) -> None: the following git
            # commands cannot be placed in a repository, so they are skipped (fail open)
            cur = shell.resolve_dir(cur, event[1])
            continue
        _, dirs, sub, args, bad = event
        if bad or sub not in _WATCHED:
            continue
        target = cur
        for d in dirs:
            target = shell.resolve_dir(target, d)
            if target is None:
                break
        if cur is None and not dirs:
            continue
        if target is None or not scope.is_studio_dir(target):
            continue
        if sub in ("checkout", "switch"):
            known, name = simulated_branch(target, sub, args, None)
            if known:
                simulated[os.path.normcase(os.path.abspath(target))] = name
            continue
        if sub == "add":
            found = ("credentials", check_add(target, args))
        elif sub == "push":
            found = ("branch", check_push(target, lambda t=target: branch_of(t), args))
        elif sub in _HISTORY_REWRITERS:
            branch = branch_of(target)
            reason = None
            if branch in scope.PROTECTED_BRANCHES and not (set(args) & _HISTORY_ESCAPES):
                reason = "`git %s` while `%s` is checked out would change %s directly." % (sub, branch, branch)
            found = ("branch", reason)
        else:
            branch = branch_of(target)
            reason = None
            # Decision #1 allows the initial commit into an empty repository: HEAD is unborn there.
            if (branch in scope.PROTECTED_BRANCHES and "--dry-run" not in args
                    and scope.head_exists(target) is not False):
                reason = "`git commit` while `%s` is checked out is a direct commit to %s." % (branch, branch)
            found = ("branch", reason) if reason else ("credentials", check_commit(target, args))
        if found[1]:
            return found
    return None


def main() -> None:
    payload = scope.read_payload()
    if payload is None:
        return
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if isinstance(command, list):  # Codex may pass argv
        command = " ".join(str(x) if " " not in str(x) else '"%s"' % x for x in command)
    if not isinstance(command, str) or "git" not in command.lower():
        return
    # No session-level scope gate: only the directory a git command targets decides (is_studio_dir), so
    # `git -C <studio> commit` / `cd <studio> && git commit` from another project is still guarded.
    # `cwd` is a common input field of every hook event. A missing, non-string or non-existent value is
    # malformed input: fail open. Never fall back to the process cwd, which is unrelated to the session.
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd or not os.path.isdir(cwd):
        return
    found = evaluate(command, cwd, payload.get("tool_name") == "PowerShell")
    if found:
        rule, reason = found
        scope.debug("deny: " + reason)
        if rule == "credentials":
            deny("GameDev Studio hook: blocked (decision #9). %s Credentials must never be committed. Remove them "
                 "from the change, keep them in an untracked/ignored file or a secret store, and commit a "
                 "`.env.example` instead." % reason)
        deny("GameDev Studio hook: blocked (decision #1). %s %s" % (reason, BRANCH_HELP))


if __name__ == "__main__":
    scope.fail_open(main)
