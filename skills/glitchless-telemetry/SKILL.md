---
name: glitchless-telemetry
description: Set up and use Glitchless performance telemetry for a Godot game — frame times and hitches on players' devices, grouped errors and drop-off points, read by the agent over MCP to fix the next build. Use when a Godot game needs data from real play sessions.
---

# Glitchless telemetry (Godot)

Apply `studio-rules` and `engine-profiles` first. Glitchless is an MIT addon for Godot 4.5+ with a hosted service (free up to 5,000 sessions a month) or a self-hosted MIT server. It is for the Godot profile (DEC-145). For HTML5 games on the web profile it is **not verified**; use the studio's browser QA (`gameplay-visual-review`, `capture_review.py`) there.

## Who does what

| Step | Who |
| --- | --- |
| Install the addon from the Godot Asset Library in the editor | the person |
| Create the Glitchless project and its key, choose hosted or self-hosted | the person |
| Put the key in the game's `.env`: `python3 scripts/studio_tools.py set-secret glitchless GLITCHLESS_KEY` (or the panel) | the person types it; Claude never sees or prints it |
| Decide that player sessions are sent, and where (privacy policy, platform rules, consent for the EU) | the owner, as a GitHub decision recorded with `studio_tools.py enable glitchless --decision <url>` |
| Connect the MCP server for the agent, following the addon's own instructions | the person; Claude may edit the project's MCP config after a yes |
| Read the data and turn it into fixes | Claude |

The studio stores the key as `GLITCHLESS_KEY` in the game's `.env`; copy it to wherever the addon expects it. The exact MCP command and endpoint come from the addon's README in the installed `addons/` folder; read it there rather than guessing. If it is not installed yet, ask the person to install it first.

## Working loop

1. Before the first release with telemetry, check that it is off in debug builds that testers did not agree to, and that the session cap fits the plan.
2. After a playtest or release, pull over MCP: worst frame-time percentiles by device class, hitch moments with their scene and likely cause, grouped errors, and the points where players quit.
3. Write findings as review evidence (`review-evidence`) with the build commit, the session count and the time window. Few sessions are a hint, not a measurement.
4. Fix in a branch; confirm with a local profile (Godot profiler) and with the next build's data. Do not call a fix confirmed from one player's sessions.

## Limits

- No telemetry is sent from a game until the owner's decision exists; without it the addon stays disabled.
- No personal data beyond what the decision covers; do not add user identifiers.
- Paid plans above the free tier are spending: only with the owner's yes (DEC-130).
