---
name: img2threejs
description: Rebuild an object or character from a reference image as a quality-gated, procedural Three.js model written in code, using the upstream img2threejs pipeline (Apache-2.0) under studio rules. Use for image-to-3D reconstruction of props, game objects and stylized characters for a Three.js web game.
---

# img2threejs — image to procedural Three.js

Apply the `studio-rules`, `art-acceptance` and `asset-licensing` skills first, and the web engine profile. DEC-133 governs any move from a pixel concept to smooth 3D; DEC-139 asks for non-template art.

img2threejs rebuilds the object in a reference image as a **code-only** procedural Three.js model through a staged sculpting pipeline (blockout → structure → form → material → lighting → interaction → optimization) with a visual self-review after each pass. It is reconstruction-by-code, not photogrammetry, mesh extraction or downloaded art packs. The core is pure Python 3.10+ standard library.

## Install (once per game, from upstream)

The upstream project is not copied into this plugin. It is installed from its own source at a pinned release, as for every third-party tool:

```text
git clone --depth 1 --branch v2.0.0 https://github.com/img2threejs/img2threejs <game>/.tools/img2threejs
git -C <game>/.tools/img2threejs rev-parse HEAD   # expect a669e9a97cea4452b1c2310c5cca6aa0f6657c1f
```

v2.0.0 is the release Mr. Mak Workspace v0.6.6 bundled. A newer release is an upgrade the owner approves. Add `.tools/` to the game's `.gitignore`, or record the tool as a submodule if the owner prefers. Keep its `LICENSE` (Apache-2.0) with it. The generated model code is the game's own work; record the tool and version in the asset's provenance (DEC-094).

Then read `<game>/.tools/img2threejs/SKILL.md` completely and follow it. It is the authority for the pipeline; this skill adds the studio's gates around it. Run its scripts from that directory.

## Studio gates around the pipeline

1. **Brief.** Before intake, record on the piece Issue: the approved reference and its licence, the intended use (prop, playable object, destructible, animation rig), the target camera and play distance, and the budget for draw calls, triangles and materials on the target device class (portal web games run on low-end phones).
2. **State file.** img2threejs keeps its checklist in `.img2threejs/state.json` and stops hard when its gate says so (`forge/next.py` exit code 3). Obey the stop and bring the reason to the owner; never reconstruct progress from chat history. The state file is a resumability index, not evidence.
3. **Honesty.** A single image cannot reveal hidden sides. State when the result is approximate, stylized or low-poly, and list what was inferred.
4. **Optional adapters.** Vision adapters (SAM2, MediaPipe, Depth Anything) and any paid vision API are optional; install or call them only when the owner agrees. Monocular depth is relative only.
5. **Integration.** The model enters the game through the game's own module structure: one factory per asset, shared geometries and materials reused, `dispose()` on retirement. Check it in the actual game scene, lighting and camera, not only in the img2threejs preview.
6. **Animation.** If the model must move, choose the profile that includes the animation readiness gates, and hand clips to `game-animation-integration`.
7. **Evidence.** Attach the reference, per-pass screenshots, the final in-game capture at play distance, measured triangle, draw-call and material counts and the img2threejs review history through `review-evidence`. An independent art reviewer gives the verdict.

Source: [img2threejs](https://github.com/img2threejs/img2threejs) (Apache-2.0), as distributed with [Mr. Mak Workspace v0.6.6](https://github.com/witnesstodark/mr-mak-workspace/tree/v0.6.6/.agents/skills/img2threejs).
