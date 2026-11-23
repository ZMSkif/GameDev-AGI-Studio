---
name: game-level-design
description: Turn an approved gameplay brief into a reviewable layout proposal and validate the applied level for scale, traversal and encounter flow in its engine.
---

# Game level design

Read `studio-rules`, the current design revision and the engine profile. Use actual movement and camera behavior to establish the design constraints.

1. **Capture a baseline.** For a current scene, record scene identity and revision, units, grid size, origin, axes, collision/navigation surfaces and existing objects with stable IDs. For a proposed new level, identify the dataset as a draft. Keep the in-game baseline accessible for visual comparisons.
2. **Make the layout reviewable.** Provide an annotated view showing entry, objective, main and alternate routes, obstacles, encounter order and exit. Distinguish visual terrain from collision and traversal rules. Record clearances against the real character footprint, jumping or movement abilities, and the time-to-objective expected at approved speed.
3. **Apply the selected layout.** Keep proposed deltas separate from the source capture and identify which scene, coordinates, markers and resource IDs each delta targets. Check the base revision before writing. Reconcile a stale layout with the edited scene before applying. In Godot verify scene ownership, transform conversion and collision/navigation resources. In web verify world-to-grid and render-to-simulation scale in the actual map loader.
4. **Traverse the saved result.** Start with the real player size and camera, visit the main and alternate routes and reproduce the changed encounters. Check spawn placement, bounds, bottleneck clearance and target controls. Repeat on the target touch layout when applicable. Report measured clearances and timings and link the native screenshots or clips through `review-evidence`.

[Mr. Mak level design](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/game-level-design/SKILL.md).
