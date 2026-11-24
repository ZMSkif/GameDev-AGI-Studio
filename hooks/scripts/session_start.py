#!/usr/bin/env python3
"""SessionStart hook for GameDev Studio projects (Claude Code and Codex).

Rule 3 (decisions #62, #129): preflight of the mandatory tools `git`, `gh` and a working
`gh auth status`. A missing tool never blocks the session: it is reported to the agent
(additionalContext) and to the user (systemMessage) so only the affected task stops.
Rule 4 (decisions #16, #34, #40): a short evidence/review reminder.

Outside a GameDev Studio project, on malformed input or on any internal error this
exits 0 and prints nothing.
"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import studio_scope as scope  # noqa: E402

GH_AUTH_TIMEOUT = 8

REMINDER = (
    "GameDev Studio project. Before any planning or implementation load the `gamedev-studio:studio-rules` skill "
    "(the plugin carries the studio's rules; with access to the studio repository it also reads the owner's decisions "
    "with gh, and without access it works from the plugin alone, DEC-147). Report only commands you actually ran "
    "and their real results; never present invented tests or stubs as done (#16, #34). Work is not accepted "
    "without an independent review (#40). Hooks block direct commits/pushes to main (#1) and committing "
    "credential files (#9)."
)


def preflight():
    """Return a list of problem descriptions (empty when everything is fine)."""
    problems = []
    if not shutil.which("git"):
        problems.append("`git` was not found on PATH")
    gh = shutil.which("gh")
    if not gh:
        problems.append("`gh` (GitHub CLI) was not found on PATH")
    else:
        try:
            done = subprocess.run(
                [gh, "auth", "status", "--hostname", "github.com"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=GH_AUTH_TIMEOUT,
                env=dict(os.environ, GH_PROMPT_DISABLED="1", NO_COLOR="1"),
            )
            if done.returncode != 0:
                problems.append("`gh auth status` failed (exit %d): gh authentication failed or could not be verified "
                                "(possibly a network error)" % done.returncode)
        except subprocess.TimeoutExpired:
            problems.append("`gh auth status` did not finish within %ds, so gh authentication could not be verified"
                            % GH_AUTH_TIMEOUT)
        except OSError as exc:
            problems.append("`gh` could not be run (%s)" % exc.__class__.__name__)
    return problems


def main() -> None:
    payload = scope.read_payload()
    if payload is None or not scope.session_in_scope(payload):
        return
    context = REMINDER
    out = {}
    problems = preflight()
    if problems:
        warning = (
            "GameDev Studio tool preflight FAILED: %s. Only a task that needs it waits (#62, #129); everything else goes on. "
            "git and gh serve the game's own repository: its branches, Issues and pull requests, under the person's "
            "own GitHub account. The studio's rules are in the plugin, so never ask for access to the studio "
            "repository (DEC-147). Do not silently substitute another tool or fake a result; say what waits and why, "
            "and ask the person once." % "; ".join(problems)
        )
        context = warning + "\n" + context
        out["systemMessage"] = warning
    out["hookSpecificOutput"] = {"hookEventName": "SessionStart", "additionalContext": context}
    scope.emit(out)


if __name__ == "__main__":
    scope.fail_open(main)
