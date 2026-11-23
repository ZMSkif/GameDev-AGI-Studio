---
name: game-animation-integration
description: Integrate approved game animation clips into locomotion, turns and actions with verified contact markers, pose continuity and interruption behavior.
---

# Game animation integration

Read `studio-rules`, `engine-profiles` and the approved movement and combat specification. Start with the editable animation source, the engine import and the controller that actually drives the character.

1. **Map the clips.** Verify rig and bone paths, axes, scale, bind pose and animation lengths in the imported build. Record clip IDs, loop flags and contact/release markers measured from the selected source. Include seconds and frame rate for frame-based references. Document which clips are missing or substituted.
2. **Assign motion authority.** Record whether the controller or clip supplies translation and facing, and which clock drives each. If the controller owns yaw, remove or compensate an equivalent authored rotation before blending. Keep player input, movement speed and action cadence within the approved spec. Godot may use AnimationTree and the project's character controller. Three.js may use AnimationMixer and the game state machine. For PixiJS, use the approved sprite timeline and verify the equivalent events against gameplay ticks.
3. **Prove continuous poses.** Capture turns entering and leaving walk and run in both directions. Inspect partial and reversed turns, stopping and turn-to-action. If a long blend hides a foot swap, compare the last evaluated pose with candidate gait phases in body-local space and preserve the supporting foot or paw. Cache reusable samples outside the frame loop when needed.
4. **Test event delivery.** Verify that the project's chosen playback route actually dispatches the markers it relies on and that no marker fires twice during a transition. Check a canceled windup, pause/resume and a replayed action. Bind audible and visible cues to the correct gameplay confirmation when a visual marker alone cannot establish a hit.
5. **Hand over a runnable proof.** Provide the bone/clip/marker mapping and normal-speed captures from the real game camera. Record boundary times, expected and observed event counts, remaining gaps and the tested revision in `review-evidence`. Send to independent review before acceptance.

[Mr. Mak runtime animation integration](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/game-animation-integration/SKILL.md).
