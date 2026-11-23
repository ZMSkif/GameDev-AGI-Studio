---
name: game-level-design
description: Turn a game-level brief or an existing scene snapshot into a reviewable spatial plan, then apply the approved changes with coordinate, navigation and scene checks. Use for layouts, encounter placement, routes and terrain plans.
---

# Game level design

Apply the `studio-rules` skill first. Read the current design revision, the engine profile (`engine-profiles`) and the piece's acceptance lines. Use the actual movement and camera behaviour as the design constraints.

Establish the play goal, scale, camera, movement and navigation limits and the existing visual setup. Inspect the scene and the documented mechanics before proposing placements. Reuse approved lighting and material settings when making another level: a new layout does not imply permission to redesign the game's presentation.

## 1. Keep source and proposal separate

- For an existing level, capture a read-only source snapshot: scene identity and revision or hash, units, grid size, origin, axis convention, terrain, collision and navigation data and object IDs.
- For a new level, label the baseline as a proposal. Do not describe a generated map as an engine export.
- Store edits separately from the source: layer overrides, marker additions, moves and removals and design notes. Keep alternate layouts independent.
- Regeneration must not silently replace the owner's edited draft. If the source changed, keep a recovery copy and resolve the conflict instead of treating the draft as disposable.

## 2. Make the plan useful for decisions

- Show terrain, passage, obstacles, cover, objectives, entry and exit as distinct layers. Define brush and cell sizes in world units.
- Visual ground colour is not necessarily a navigation blocker; tree cover, water and a road may have different rules. Keep visual terrain separate from collision and traversal rules.
- Preserve stable marker IDs and distinguish counts, capacity and starting occupants. Unchosen prefabs, scenes or mechanics remain explicit design intent.
- Check main and alternate routes, chokepoint width, clearances, encounter order and travel distances against the real character footprint, abilities and approved speeds. Record the expected time-to-objective.
- A 2D simulation can compare strategies only within its documented assumptions. Its result does not prove native navigation, combat behaviour or final balance.

## 3. Apply only the approved plan

- Export a manifest that maps coordinates, the source revision and markers to engine assets. Reject a stale or conflicting revision before applying.
- Confirm the target scene and which objects are generated. Do not overwrite an unrelated authored scene or manual edits as a side effect of a rebuild.
- Godot: check scene ownership, transform conversion, TileMap/GridMap cell sizes and collision and navigation resources. Web: check world-to-grid and render-to-simulation scale in the actual map loader.

## 4. Traverse the saved result

Verify the saved terrain dimensions, height and axis conversion, scene and prefab references, colliders, navigable paths, spawn locations and camera bounds in the engine. With the real player size and camera, traverse the main and alternate routes and reproduce the changed encounters. Repeat on the target touch layout when applicable. Preserve unrelated gameplay values and assets.

Deliver the editable plan, the applied scene, the export manifest, measured clearances and timings, native captures and the unresolved choices through `review-evidence`.

Example request: "Plan a small valley with two routes to the objective, then apply the chosen version." Success includes a reviewable layout, measured route clearance and a verified native path through the saved scene.

Dependencies: the project's design rules and engine access or an editor bridge for scene work.

Source: [Mr. Mak level design](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/game-level-design/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
