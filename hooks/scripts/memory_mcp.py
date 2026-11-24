"""Start the studio memory MCP server (scripts/memory_mcp.py) through run-hook.cmd, which finds Python.

The plugin's .claude-plugin/plugin.json starts it with every Claude Code session as the `memory` MCP server.
"""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts" / "memory_mcp.py"), run_name="__main__")
