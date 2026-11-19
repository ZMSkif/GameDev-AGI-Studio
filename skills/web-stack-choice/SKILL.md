---
name: web-stack-choice
description: Procedure for choosing the renderer and libraries of a web-profile game for 2D, 2.5D or 3D (Three.js, PixiJS v8, Babylon.js, Phaser and the subsystem libraries), with the licence gate, the quality-first criteria order and the prototype-both rule. Use when a new HTML5 or portal game needs a stack, when someone asks "Three or Pixi or Babylon", or before adding a library to a web game.
---

# Web stack choice

> **Decided by DEC-145 (#161):** the web profile for HTML5 portal games and the Godot 4.x profile for heavy and desktop games; the owner approves each game's profile with its architecture.

The tables (renderer by game type, versions, the 16 subsystems, physics fallback, start-up metrics, bench) live in one place: `../engine-profiles/references/web-profile.md`. This skill is the procedure. Use `engine-profiles` first to confirm the game is in the web profile at all.

## Procedure

1. **Write the game's facts first:** genre and type (3D, 2.5D, light 2D, rich 2D), object counts on screen, special 2D needs (Tiled or LDtk maps, 9-slice, Spine, many filters and masks), target platforms and minimum devices (the owner names them; Cat Challenge used Android 2021–22 low-mid, Snapdragon 680 / Helio G85 with 4 GB, and iPhone 11).
2. **Licence gate** for every candidate (web profile §1). A library that fails it is out, however good.
3. **Pick the renderer** from the game-type table. Rich 2D leans to PixiJS v8; one mask or a small map does not.
4. **If you are unsure, build the key scene on both candidates** and measure it with the bench: both start-up metrics on the "phone" and "weak phone" profiles, frame time under the scene's real load. Report emulation as emulation.
5. **Pick each subsystem** from the subsystem table. Say for each whether it was shipped in a released game or only decided. Before you rely on an API, read its current docs (context7 or the vendor site); "not found" is not "does not exist".
6. **Rank by quality first**, then maintenance, then the start-up path weight. If an option is clearly better for the player, take it and move its cost after `game_ready`; do not drop it to save kilobytes.
7. **Pin versions:** exact versions, one copy of `three` (`npm ls three`), upgrades only when every peer range covers them.
8. **Physics:** for limited mechanics, own arcade physics through gate P1; if P1 stays red after 2 fix iterations, run the fallback order. Never skip the independent audit.
9. **Write it down** in the game repository as its stack decision (part of the architecture, DEC-080, #81) with: the choice per subsystem, the reason, shipped or decided, the risks, and what the owner must approve. Big or contested choices go through a three-way discussion (`orchestration-playbook` skill), and the owner approves the architecture (DEC-017, #17).

## Traps seen in Cat Challenge

- Libraries can be installed and never imported (XState, tween.js and three.quarks in r17). Check imports in the shipped code before you call something "the stack".
- A bench result on a reference scene does not carry over to the game; measure the game.
- Default CDN calls (Babylon decoders and Inspector) break the portal rule "no external resources" (Playgama 1.2.5).
- The ready-made Spine runtime for Three had a peer range that excluded the shipped Three version; check peer ranges before you plan on a library.

## Source

Cat Challenge `STACK_PLAYBOOK.md`, `ENGINE_DECISION.md`, `STACK_DECISIONS.md` (16.11.2026, agreed by Claude, Codex and an advisor); the game's imports checked on 19.11.2026; owner rule "quality first" (16.11.2026).
