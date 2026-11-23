---
name: game-ui-workflow
description: Take a game HUD, menu or overlay from approved visual references to live game state, responsive input, and evidence from the running game. Use when designing or implementing game UI in Godot, Three.js or PixiJS.
---

# Game UI workflow

Apply the `studio-rules` skill and read the game's approved brief, Art Bible, target devices and selected engine profile. The Art Director owns the visual direction, the Gameplay Engineer wires the game, and an independent reviewer checks the result (DEC-065 and DEC-072).

1. **Start with the real screen.** List the player action each control serves and the state or event that drives it. Capture the current implementation and identify the available space, input methods and text lengths. Use a mockup to agree on hierarchy, layout and art before a material visual change.
2. **Prepare reusable pieces.** List fonts, textures, icons and nine-slice margins with sources. Approve a representative set and document the layout constraints. Define idle, focus, pressed, unavailable and error states only where applicable.
3. **Wire real behavior.** Connect the approved design to live state and actions. Match flow under touch, mouse and keyboard where supported. Check focus, safe area, orientation changes, longest shipped translations and natural pause/resume cases relevant to the screen. Keep platform and game actions accessible after dialogs close.
4. **Capture and verify.** Use the `gameplay-visual-review` skill. Show the actual screen before and after under the same conditions, with a clip if timing or input matters. Check the build on the relevant target sizes and record the tested revision.

Report the visual decision, player actions checked, revision, captures and any gaps. Use vocabulary and thresholds from the approved game and platform contracts. Source for the workflow: [Mr. Mak game UI](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/game-ui-workflow/SKILL.md).
