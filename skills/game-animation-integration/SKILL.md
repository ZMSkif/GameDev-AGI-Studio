---
name: game-animation-integration
description: Integrate approved character clips into a game's movement and combat systems, including motion authority, turn compensation, gait phase, event timing and interruptions. Use after animation authoring or to repair runtime transitions in Godot, Three.js or PixiJS.
---

# Game animation integration

Apply the `studio-rules` skill first. Read `engine-profiles`, the approved movement and combat specification and the piece's acceptance lines. Animation authoring is covered by `blender-game-animation`; evidence goes through `gameplay-visual-review` and `review-evidence`.

Start with the approved rig, the runtime export and its clip manifest. Inspect the existing animation player and the controller that actually drives the character before replacing anything. Confirm forward/up axes, scale, bone paths, import type, bind pose, clips, loop flags and event times in the imported build. Keep **source animation approval**, **import verification** and **in-game visual acceptance** as separate states.

## 1. Map the clips

Record clip IDs, durations, loop flags and contact/release markers measured from the selected source, in seconds and in frames with the frame rate. Document which clips are missing or substituted; mark a missing clip explicitly instead of reusing a similar one silently.

## 2. Separate movement, facing and authored motion

- Choose which system owns translation and which owns yaw, and which clock drives each. Applying controller rotation and the same authored turn twice produces a false turn. If the controller owns yaw, remove or compensate the equivalent authored rotation before blending.
- Keep uncompensated source clips for pure previews where useful; document the compensated gameplay route.
- Record heading samples and their frame/time origin. Derive sample spacing from the actual count and duration, not from a presumed integer or quarter-frame step.
- Do not change base movement speed, attack cadence or navigation responsiveness incidentally. A character need not finish a whole turn clip before obeying a new movement or combat order. Keep visual stepping speed, gameplay facing and speed recovery independently configurable.

Engine routes: Godot uses AnimationPlayer/AnimationTree with the project's CharacterBody controller; Three.js uses AnimationMixer and the game's state machine; PixiJS uses the approved sprite timeline, and its frame events must be checked against gameplay ticks.

## 3. Match the pose at a transition

- If leaving a partial turn causes a foot swap, a longer crossfade alone may not fix it. Compare the last evaluated pose with sampled gait phases in a shared body-local space, excluding world placement and controller yaw. Select a nearby phase at the handoff, then advance normally. Preserve an already better phase.
- Build the mapping for the actual anatomy. Two feet and knees can be enough for a biped; four-legged rigs need all relevant paws and support joints. Do not prescribe one sample count, stride or blend duration for every rig.
- Bake reusable pose tables at import or update time; cache bones and avoid allocating or searching each frame. Rebuild when the rig, clips or coordinate convention changes.
- Verify intermediate transforms during a finite transition, including upper-body settling. A correct mixer weight does not prove a continuous visible pose. Keep straight and steering variants phase-compatible. Document any root-motion or contact-IK system separately from phase selection.

## 4. Bind events and validate

- Use the actual contact and release markers and the game's authoritative clock. Some players do not dispatch imported animation events; verify the chosen route instead of assuming it, and make sure no marker fires twice during a transition.
- Cancellation must suppress events that have not happened yet. Bind audible and visible cues to the gameplay confirmation when a visual marker alone cannot establish a hit.
- Exercise left/right, small/large and reversed turns; Walk and Run exits; stop and arrival; turn-to-attack; attack variants; death; pause/resume; repeated commands; disable/re-enable and any storage flow.
- Review at normal speed from the game camera as well as in isolated clip playback.
- Preserve material and team bindings, existing scene and resource IDs (Godot UIDs, prefab or asset GUIDs) and unchanged gameplay values.

## 5. Hand over a runnable proof

Deliver the bone/clip/marker mapping, the runtime configuration, source contact times, the verified interruption cases with expected and observed event counts, the remaining gaps and native normal-speed captures for the tested revision through `review-evidence`. Send it to independent review before acceptance.

Example: integrate a robot's quarter-turns without changing its movement speed, and prove that a partial turn can enter Run without swapping the supporting foot.

Dependencies: approved clips, their editable source and manifest, and engine access.

Source: [Mr. Mak runtime animation integration](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/game-animation-integration/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
