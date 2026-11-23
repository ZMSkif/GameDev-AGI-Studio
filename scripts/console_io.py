"""Console text for the studio scripts on every operating system.

On Windows a pipe (Claude's Bash tool, a log file, ``subprocess`` with ``capture_output``) gets the ANSI
code page (cp1252 or cp1251). Printing ✓, → or Cyrillic there either crashes with ``'charmap' codec can't
encode`` or arrives as broken text, and Windows' own error messages (``[WinError 2] ...``) come out in
cp1251, which a reader expecting UTF-8 cannot decode. ``prepare_console()`` makes piped stdout and stderr
UTF-8 unless ``PYTHONIOENCODING`` says otherwise; a real console keeps its encoding but never crashes on a
character. Each script calls it from its ``if __name__ == "__main__":`` block only, so importing a script
in a test changes nothing.
"""
from __future__ import annotations

import os
import sys


def prepare_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        piped = not (hasattr(stream, "isatty") and stream.isatty())
        if piped and not os.environ.get("PYTHONIOENCODING"):
            stream.reconfigure(encoding="utf-8", errors="replace")
        else:
            stream.reconfigure(errors="replace")
