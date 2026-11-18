"""Small, tolerant shell-command parser for the GameDev Studio hooks (stdlib only).

It is a guard rail, not a security boundary: it understands the command shapes that
coding agents really emit (`cd X && git ...`, `git -C X -c k=v commit -m "$(cat <<'EOF' ...)"`,
`bash -c '...'`, PowerShell `;`/`&&` chains) and ignores what it cannot resolve
(variables, command substitution results), i.e. it fails open on unknowns.

`parse(command)` returns a flat, ordered list of events:
  ("cd", target)                       a directory change (target may be None = unknown)
  ("git", opts_dirs, sub, args, bad)   a git invocation: -C paths, subcommand, its args,
                                       bad=True when the git directory cannot be resolved
"""
from __future__ import annotations

import os
import re

_OP_CHARS = ";&|()`\n"
_PREFIX_WORDS = {
    "{", "}", "!", "then", "do", "else", "elif", "if", "while", "until", "time",
    "nohup", "command", "builtin", "exec", "sudo", "env", "call", "start",
}
_CD_WORDS = {"cd", "chdir", "pushd", "set-location", "sl", "push-location"}
_SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "pwsh", "powershell"}
_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_HEREDOC_RE = re.compile(r"(?<!<)<<-?\s*(?:'([^']+)'|\"([^\"]+)\"|\\?([A-Za-z0-9_.-]+))")
_REDIR_RE = re.compile(r"\d*(?:>>|>|<<<|<<|<)(?:&\d*-?|\|)?")
_ESCAPABLE = set(" \t\"'$`;&|()<>*?#\n!\\")


def strip_heredocs(text: str) -> str:
    """Remove here-document bodies (and their terminator line). Left untouched when unterminated."""
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        delims = [m.group(1) or m.group(2) or m.group(3) for m in _HEREDOC_RE.finditer(line)]
        for delim in delims:
            for j in range(i, len(lines)):
                if lines[j].strip() == delim:
                    i = j + 1
                    break
            # no terminator found: keep the following lines as they are
    return "\n".join(out)


def tokenize(text: str):
    """Split into a list of words and operator markers (None = command separator)."""
    tokens = []
    cur = []
    have = False
    quote = None
    skip_word = False  # the word after a redirection operator is a file name
    i, n = 0, len(text)

    def flush():
        nonlocal cur, have, skip_word
        if have:
            word = "".join(cur)
            if skip_word:
                skip_word = False
            elif word not in ("$",):
                tokens.append(word)
        cur, have = [], False

    def sep():
        flush()
        if tokens and tokens[-1] is not None:
            tokens.append(None)

    while i < n:
        c = text[i]
        if quote == "'":
            if c == "'":
                quote = None
            else:
                cur.append(c)
        elif quote == '"':
            if c == "\\" and i + 1 < n and text[i + 1] in '"\\$`':
                cur.append(text[i + 1])
                i += 1
            elif c == '"':
                quote = None
            else:
                cur.append(c)
        else:
            if c in " \t\r":
                flush()
            elif c in "'\"":
                quote = c
                have = True
            elif c == "\\" and i + 1 < n and text[i + 1] == "\n":
                i += 1  # line continuation
            elif c == "\\" and i + 1 < n and text[i + 1] in _ESCAPABLE:
                cur.append(text[i + 1])
                have = True
                i += 1
            elif c == "#" and not have:
                while i < n and text[i] != "\n":
                    i += 1
                continue
            elif c in "<>" or (c == "&" and i + 1 < n and text[i + 1] == ">" and not have):
                m = _REDIR_RE.match(text, i) if c in "<>" else re.compile(r"&>>?").match(text, i)
                if have and cur and "".join(cur).isdigit():
                    cur, have = [], False  # the fd number of `2>file`
                else:
                    flush()
                end = m.end() if m else i + 1
                op = text[i:end]
                if not re.search(r"&\d*-?$", op):
                    skip_word = True
                i = end
                continue
            elif c in _OP_CHARS:
                sep()
                if c in "&|" and i + 1 < n and text[i + 1] == c:
                    i += 1
            elif c == "$" and i + 1 < n and text[i + 1] == "(":
                sep()
                i += 1
            else:
                cur.append(c)
                have = True
        i += 1
    flush()
    while tokens and tokens[-1] is None:
        tokens.pop()
    return tokens


def _basename(word: str) -> str:
    base = re.split(r"[\\/]", word)[-1].lower()
    for ext in (".exe", ".cmd", ".bat"):
        if base.endswith(ext):
            base = base[: -len(ext)]
    return base


def _commands(tokens):
    cmd = []
    for tok in tokens:
        if tok is None:
            if cmd:
                yield cmd
            cmd = []
        else:
            cmd.append(tok)
    if cmd:
        yield cmd



def _parse_git(words):
    """words[0] is git. Returns (dirs, sub, args, bad) or None when there is no subcommand."""
    dirs = []
    bad = False
    i = 1
    while i < len(words):
        w = words[i]
        if not w.startswith("-"):
            return dirs, w, words[i + 1:], bad
        if w == "-C" and i + 1 < len(words):
            dirs.append(words[i + 1])
            i += 2
        elif w in ("-c", "--namespace", "--super-prefix", "--config-env", "--attr-source") and i + 1 < len(words):
            i += 2
        elif w in ("--git-dir", "--work-tree"):
            bad = True  # explicit git dir: effective repository unknown
            i += 2
        elif w.startswith(("--git-dir=", "--work-tree=")):
            bad = True
            i += 1
        else:
            i += 1
    return None


def parse(command: str, depth: int = 0):
    events = []
    if depth > 3 or not isinstance(command, str):
        return events
    tokens = tokenize(strip_heredocs(command))
    for words in _commands(tokens):
        i = 0
        prefixed = False
        while i < len(words):
            w = words[i]
            if _ASSIGN_RE.match(w):
                i += 1
            elif _basename(w) in _PREFIX_WORDS:
                prefixed = True
                i += 1
            elif prefixed and w.startswith("-"):
                i += 1
            else:
                break
        if i >= len(words):
            continue
        head = _basename(words[i])
        rest = words[i + 1:]
        if head in _CD_WORDS:
            target = None
            for w in rest:
                if not w.startswith("-") or head in ("set-location", "sl", "push-location"):
                    if w.lower() in ("-path", "-literalpath"):
                        continue
                    target = w
                    break
            events.append(("cd", target if rest else "~"))
        elif head == "git":
            parsed = _parse_git(words[i:])
            if parsed:
                events.append(("git",) + parsed)
        elif head in _SHELLS:
            for k, w in enumerate(rest[:-1]):
                low = w.lower()
                if (low.startswith("-") and not low.startswith("--") and "c" in low[1:]) or low in ("-command", "-c"):
                    events.extend(parse(rest[k + 1], depth + 1))
                    break
    return events


# ---- directory resolution -------------------------------------------------------------

_MSYS_RE = re.compile(r"^/(?:cygdrive/)?([A-Za-z])(?:/(.*))?$")


def resolve_dir(base: str, target):
    """Resolve `target` against `base`; None when unknown (variables, `cd -`, missing dir)."""
    if target is None or not isinstance(target, str):
        return None
    if any(ch in target for ch in "$`*?") or target == "-":
        return None
    if target.startswith("~"):
        target = os.path.expanduser(target)
    if os.name == "nt":
        m = _MSYS_RE.match(target)
        if m:
            target = m.group(1).upper() + ":/" + (m.group(2) or "")
    path = target if os.path.isabs(target) else os.path.join(base, target)
    path = os.path.normpath(path)
    return path if os.path.isdir(path) else None
