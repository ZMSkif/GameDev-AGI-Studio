---
name: gameplay-visual-review
description: Independently review game UI, scenes, animation and feel from comparable before-and-after captures taken inside the running game. Use to prepare or assess playable visual evidence.
---

# Gameplay visual review

Apply the `studio-rules` skill. Use the piece's acceptance lines and the `art-acceptance` or `game-feel-controls` skill when relevant. An independent reviewer is responsible for the verdict (DEC-040, DEC-072).

1. **Choose a repeatable setup.** Record the commit, engine and build, scene and saved state or seed, camera, viewport, input method and the steps to reproduce the shot. Pick one view at actual play distance. Add a close-up if the asset requires one.
2. **Capture comparable views.** Keep camera, viewport, lighting and action consistent across revisions unless one of them is the change. For timing and input, capture a short clip with the action and the state change. Keep concept art and isolated previews explicitly labelled.
3. **Check appearance and behavior.** Compare to the accepted reference and test the relevant input or state changes in the running game. Inspect both narrow and wide supported screens when layout is affected. Record external blockers, missing test devices and any differences between the review build and release build.
4. **Attach evidence.** Use the `review-evidence` skill for the Issue, exact revision, captures and verbatim reviewer verdict. A screenshot only establishes a visual state. Timing, interaction and sustained performance need their own evidence.

## Browser QA

For a web build, use [browser visual QA](../../reference/browser-visual-qa.md) when a project has a reproducible scenario. Run it at the two revisions and report failures, captures and the tested widths. Use real device evidence when the acceptance line calls for a physical device or platform integration.

Source for the workflow: [Mr. Mak gameplay visual review](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/gameplay-visual-review/SKILL.md).
