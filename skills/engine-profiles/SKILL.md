---
name: engine-profiles
description: Which engine profile a GameDev Studio game uses (web for HTML5 portal games, Godot 4.x for heavy or desktop games) and which studio decisions bind in each. Use when starting a game, choosing or questioning the engine, planning architecture or tests, or when a rule mentions Godot and the game is a web game.
---

# Engine profiles

> **Status: DEC-145, not yet registered.** The owner chose both engine profiles on 19.11.2026. Until the DEC-145 issue exists, the binding contract names only the Godot profile, so the web-profile text here is information, not a rule.

The studio core is engine-neutral: decisions, quality gates, QA, assets, platforms, review and release rules apply to every game. A **profile** adds only what depends on the engine: renderer, language, build, test tools and the engine-scoped decisions.

| Profile | For | Engine and tools | Details |
|---|---|---|---|
| `godot` | heavy or desktop games | Godot 4.x (DEC-012, #12) | `references/godot-profile.md` |
| `web` | HTML5 games for portals: Playgama, CrazyGames, YouTube Playables | Three.js for 3D, 2.5D and light 2D; PixiJS v8 for rich 2D; TypeScript, Vite | `references/web-profile.md` (the single source of the web stack tables) |

The binding contract is `contracts/v1/game-production-policy.json` (`engine_profiles`). Read it; this skill explains it and does not replace it.

## Choose the profile

1. Ask what the game is for at preproduction (the adaptive interview, DEC-078, #79). Portal HTML5 first → `web`. A large 3D world, a desktop store release or editor-heavy content → `godot`. Until the DEC-145 issue exists only the Godot profile may be proposed; for a portal game, ask the owner to register DEC-145 first.
2. Propose the profile with the reason in the architecture document (DEC-080, #81). The owner approves it; never switch a game's profile on your own (DEC-017, #17).
3. Inside the web profile, pick the renderer and libraries with the `web-stack-choice` skill.
4. Record the choice in the game repository (its architecture or ADR), not in this plugin.

## Which decisions bind where

| Decision | Godot profile | Web profile |
|---|---|---|
| DEC-047 (#47) modular architecture | binding (it names Godot games) | same intent, proposed in DEC-145: packages with fixed contracts, no monolith |
| DEC-069 (#70) Godot integration and deterministic tests | binding | proposed in DEC-145: deterministic Vitest tests of game logic and Playwright checks of the production build |
| DEC-116 (#118) no WebDAV editing of the Godot project | binding | not applicable |
| DEC-129 (#131) real Godot, Blender, browser and device evidence | binding | browser, device and Blender evidence bind; DEC-145 proposes the built web game in the browser in place of Godot evidence |
| DEC-064 (#65) 3D character pipeline, in-engine validation | binding for new 3D characters | binding for new 3D characters; not for 2D assets or static props. An exception for portal games would need its own owner decision |
| DEC-054 (#54), DEC-056 (#56) logic apart from view and input; platform adapters | binding | binding |
| DEC-057 (#57), DEC-058 (#58), DEC-059 (#59) platform build profiles, Bridge docs, YouTube rules | binding | binding; Playgama Bridge belongs to the Playgama platform profile, not to every web game |
| DEC-068 (#69), DEC-070 to DEC-075 (#71 to #76) QA | binding | binding |
| DEC-139 (#141), DEC-065 (#66), DEC-094 (#95), DEC-141 (#143) art, licences, audio | binding | binding |

## Evidence words

- **shipped**: present in the code of a build that players can open (Cat Challenge r17, published to the Playgama sandbox on 19.11.2026; not yet through moderation).
- **decided, not shipped**: agreed in a playbook but never imported by a shipped build. Say so when you recommend it.
- **emulation**: a bench or a browser device profile. It is never a physical-device result (DEC-073, #74).

## Source

Cat Challenge project, `STACK_PLAYBOOK.md` and `ENGINE_DECISION.md` (agreed by Claude, Codex and an advisor, 16.11.2026); the owner's answer «Оба профиля» (19.11.2026), recorded in that project's `OWNER_DECISIONS.md`; shipped imports checked in the game's code on 19.11.2026.
