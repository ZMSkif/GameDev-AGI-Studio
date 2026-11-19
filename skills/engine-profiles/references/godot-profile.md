# Godot profile

The binding entry is `engine_profiles.profiles.godot` in `contracts/v1/game-production-policy.json`. It keeps DEC-012 (#12): Godot 4.x. Nothing in this profile changed when the web profile was proposed.

## Decisions that name Godot

| Decision | What it requires |
|---|---|
| DEC-012 (#12) | the engine is Godot 4.x |
| DEC-047 (#47) | Godot games are modular whatever their size |
| DEC-069 (#70) | QA includes Godot integration tests and deterministic gameplay-state tests |
| DEC-116 (#118) | never edit the working Godot project directly over network WebDAV |
| DEC-129 (#131) | quality claims need real Godot, Blender, browser and device evidence |

## Core decisions applied the Godot way

- **DEC-064 (#65) character pipeline:** crisp pixel concept as proportion and colour blueprint → smooth stylized 2D concept → stylized PBR 3D → rig → animation → in-engine validation. In this profile "in-engine" means inside the Godot project, not only after import (DEC-065, #66). Pixelation does not leak into the final smooth 3D without owner approval (DEC-133, #135).
- **DEC-054 (#54):** gameplay logic stays apart from view and input (scenes and nodes for view, plain logic for rules).
- **DEC-056 (#56), DEC-057 (#57):** platform adapters and a build profile plus QA matrix per platform. A Godot web export for Playgama still follows the `playgama-release` skill (Bridge, packaging, owner gates).
- **DEC-068 (#69), DEC-070 to DEC-075 (#71 to #76):** static checks, contracts, resource import and unit tests; touch, browser and orientation checks; long sessions, saves and performance; physical devices with emulation labelled; evidence with environment, date and hash; the bug workflow.

## Tooling notes

- Godot MCP connector selection is task PLUGIN-04 (#151); until it is done, report editor and export steps you could not run as `not_run`.
- The installed `godot-prompter` plugin has Godot skills and agents (architecture, GDScript, shaders, UI, testing). Use them for engine craft; this plugin keeps the studio rules.
- Web export of a Godot game: check the size and start-up path against the platform limits (Playgama: archive ≤ 300 MB, start-up memory under 2 GB; YouTube: initial download ≤ 30 MiB) before choosing Godot for a portal game. The owner's choice of a web profile for portal games waits for its decision issue (see `../SKILL.md`, Status).
