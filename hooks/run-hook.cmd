: << 'CMDBLOCK'
@echo off
REM Cross-platform launcher for the GameDev Studio hook scripts (Python 3, stdlib only).
REM One file, two shells: cmd.exe runs this batch half; sh/bash treats the first line as a
REM no-op here-document and runs the POSIX half below.
REM Usage: run-hook.cmd <script-name>      (runs scripts\<script-name>.py, JSON payload on stdin)
REM Fail-open: no usable Python 3 -> exit 0 and print nothing (the hooks must never block work).
setlocal
if "%~1"=="" exit /b 0
set "SCRIPT=%~dp0scripts\%~1.py"
if not exist "%SCRIPT%" exit /b 0

python -c "import sys;sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>&1
if not errorlevel 1 goto :run_python
py -3 -c "import sys;sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>&1
if not errorlevel 1 goto :run_py
python3 -c "import sys;sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>&1
if not errorlevel 1 goto :run_python3
exit /b 0

:run_python
python -I "%SCRIPT%"
exit /b 0
:run_py
py -3 -I "%SCRIPT%"
exit /b 0
:run_python3
python3 -I "%SCRIPT%"
exit /b 0
CMDBLOCK

# POSIX half (Linux, macOS, Git Bash on Windows).
case "$0" in
  */*|*\*) HOOK_DIR="${0%[/\]*}" ;;
  *) HOOK_DIR="." ;;
esac
name="${1:-}"
[ -n "$name" ] || exit 0
script="$HOOK_DIR/scripts/$name.py"
[ -f "$script" ] || exit 0

# Run one interpreter if it is a working Python 3. On Windows `python3` is often the Microsoft
# Store stub that fails, so each candidate is probed before use.
try_python() {
  "$@" -c 'import sys;sys.exit(0 if sys.version_info[0]==3 else 1)' >/dev/null 2>&1 || return 1
  exec "$@" -I "$script"
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
