: << 'CMDBLOCK'
@echo off
REM Cross-platform launcher for the GameDev Studio hook scripts (Python >= 3.8, stdlib only).
REM
REM Attribution: the single-file cmd/sh polyglot technique (a first line that is a no-op here-document
REM for sh and a batch label block for cmd.exe) is adapted from hooks/run-hook.cmd of the "superpowers"
REM plugin, Copyright (c) 2025 Jesse Vincent, MIT License, https://github.com/obra/superpowers.
REM Only the pattern is reused; the interpreter search, probing and exit handling are original.
REM
REM One file, two shells: cmd.exe runs this batch half; sh/bash treats the first line as a
REM no-op here-document and runs the POSIX half below.
REM Usage: run-hook.cmd <script-name>      (runs scripts\<script-name>.py, JSON payload on stdin)
REM Fail-open: no usable Python, or a Python exit code other than 0/2 -> exit 0 (hooks must never block work).
setlocal
if "%~1"=="" exit /b 0
set "SCRIPT=%~dp0scripts\%~1.py"
if not exist "%SCRIPT%" exit /b 0

python -c "import sys;sys.exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if not errorlevel 1 goto :run_python
py -3 -c "import sys;sys.exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if not errorlevel 1 goto :run_py
python3 -c "import sys;sys.exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if not errorlevel 1 goto :run_python3
exit /b 0

:run_python
python -I "%SCRIPT%"
goto :finish
:run_py
py -3 -I "%SCRIPT%"
goto :finish
:run_python3
python3 -I "%SCRIPT%"
goto :finish
:finish
if errorlevel 2 if not errorlevel 3 exit /b 2
exit /b 0
CMDBLOCK

# POSIX half (Linux, macOS, Git Bash on Windows).
case "$0" in
  */*|*\\*) HOOK_DIR="${0%[/\\]*}" ;;
  *) HOOK_DIR="." ;;
esac
name="${1:-}"
[ -n "$name" ] || exit 0
script="$HOOK_DIR/scripts/$name.py"
[ -f "$script" ] || exit 0

# Run one interpreter if it is a working Python >= 3.8. On Windows `python3` is often the Microsoft
# Store stub that fails, so each candidate is probed before use. Exit code 2 passes through; any other
# non-zero code (crash, interpreter problem) is turned into 0 so a broken hook never blocks work.
try_python() {
  "$@" -c 'import sys;sys.exit(0 if sys.version_info>=(3,8) else 1)' >/dev/null 2>&1 || return 1
  "$@" -I "$script"
  rc=$?
  [ "$rc" -eq 2 ] && exit 2
  exit 0
}

case "${OSTYPE:-}" in
  msys*|cygwin*|win32*)
    command -v python >/dev/null 2>&1 && try_python python
    command -v py >/dev/null 2>&1 && try_python py -3
    command -v python3 >/dev/null 2>&1 && try_python python3
    ;;
  *)
    command -v python3 >/dev/null 2>&1 && try_python python3
    command -v python >/dev/null 2>&1 && try_python python
    ;;
esac
exit 0
