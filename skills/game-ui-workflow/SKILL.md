---
name: game-ui-workflow
description: Design and implement game HUDs, menus, icons and portrait systems from visual proposals through reusable engine assets, live game state and input checks. Use when a game interface in Godot, Three.js or PixiJS needs a coherent visual and behaviour contract.
---

# Game UI workflow

Apply the `studio-rules` skill first. Read the game's approved brief, Art Bible, target devices and the selected engine profile. The Art Director owns the visual direction, the Gameplay Engineer wires the game and an independent reviewer checks the result (DEC-065, DEC-072). Localised text follows `i18n-portal`.

Inspect the current game camera, input rules, UI framework and representative screens. Reuse the project's selected visual language and framework. Establish the information and actions the player needs before generating decorative art.

## 1. Design against real gameplay

- List the player action each control serves and the state or event that drives it. Identify the available space, input methods and the longest shipped text.
- Use a native game capture as the backdrop for a proposal, and keep it identical when comparing HUD alternatives, so a changed background cannot disguise contrast or obstruction. Agree hierarchy, layout and art on a mockup before a material visual change.
- Define shared surface, type, spacing and selection tokens. Preserve semantic colours for ownership, health, danger and accepted choices.
- Separate visual art from live data. Decide which values come from runtime state, which actions dispatch existing commands and what remains unimplemented. Show unavailable data honestly; do not invent a currency, timer or rule.
- Include hover, focus, pressed, selected, disabled, empty, error and overflow states where they apply.
- Review the actual interface scale and aspect ratios: portrait, landscape and square for portal games, plus safe areas. Corner anchors, minimum sizes, long labels and compact rosters stay usable at a narrow viewport. Test the intended selection and grouping rules; unit type and team may be independent keys, and a combined health display is different data from a range of stats.

## 2. Prepare reusable assets

- Keep approved art and source masters with stable asset IDs and a manifest of source paths, hashes and licences.
- Export icons at their intended display scale. Check alpha edges on light and dark backgrounds, shared optical weight and silhouette readability.
- For stretchable panels identify border regions explicitly and check corners at several sizes before choosing nine-slice (Godot `NinePatchRect`/`StyleBoxTexture`, Pixi `NineSliceSprite`, CSS `border-image`) or another approach.
- Static and animated portraits use the same crop and a reliable still fallback. Budget concurrent video decoders and render targets, share identical playback when appropriate and release hidden views. Portrait art is data-driven rather than a new UI branch per character.
- Preserve resource IDs and existing bindings when updating imported assets.

## 3. Integrate and prove interaction

- Use the engine's existing UI tools or an available editor bridge. State the required framework or package instead of assuming a particular MCP is installed.
- Keep layout and world-input exclusion in agreement: a click or tap over a panel must not also command the world (Godot `mouse_filter`, DOM `pointer-events`, Pixi `eventMode`).
- Verify hover, click, tap, drag, keyboard and gamepad focus, selection, minimap behaviour, orientation change, pause and return paths that the changed screen owns. Platform and game actions stay reachable after dialogs and advertisements close.
- Read current values and cooldowns from their authoritative systems; do not duplicate combat or production timers in presentation code. Reuse views, bound expensive updates and avoid per-frame texture readback for a minimap.
- Save the real assets and check them in a fresh engine session or a clean build.

## 4. Capture and verify

Use `gameplay-visual-review`: the same screen before and after under the same conditions, a clip when timing or input matters, every target size. For web builds the browser runner in `reference/browser-visual-qa.md` checks bounds and overlap at portrait, landscape and square.

Deliver the theme, the asset mapping, native captures, the tested interactions, the revision and the open decisions. A browser mockup approval is a design decision, not a claim of engine integration.

Example request: "Give the existing HUD a compact unit panel and six matching command icons." Success includes consistent icons, real selection data, working commands, overflow behaviour and no click-through.

Dependencies: the current UI sources, game captures and target-engine access for implementation.

Source: [Mr. Mak game UI](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/game-ui-workflow/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
