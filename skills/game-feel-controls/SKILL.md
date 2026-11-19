---
name: game-feel-controls
description: Game feel and teaching controls for portal games - juice (hit-stop, squash and stretch, pickup flights, camera trauma), the human-watched feel gate, one-hand touch control, keyboard rules without Esc, a visible pause, a zero-click first minute and in-match teaching that shows where and how. Use when a hit "does not feel", controls are awkward or misfire, players do not understand what to do, or when designing touch controls or a tutorial.
---

# Game feel and controls

Binding: DEC-070 (#71) QA checks controls, browser, touch and orientation; DEC-072 (#73) an independent gameplay review; DEC-082 (#83) major design changes go to the owner. Platform: Playgama 1.4.x, 1.5.x, 1.6.6 (one hand), 3.1.3 (a tutorial without a wall of text).

## 1. Juice

- Hit-stop through the simulation time scale: the strongest request wins (max, never a sum), with a cooldown so it does not stutter, easing back to 1.
- Squash and stretch, dust, debris, a "poof" on elimination; a pickup flies to its HUD counter.
- Camera shake from "trauma" that decays, damped follow.
- Tweens and effects run on the game clock, so pause and hit-stop stop them.
- No allocation per frame in effects (pools, struct-of-arrays particles); quality tiers where low is the cheapest.
- Effect colours come from the theme.

## 2. The feel gate

The agent records game situations (platforms and jumps from them, hits, sliding contact, crowds, frame drops). **A human watches the recordings and decides**; a recording alone is no proof. The Cat Challenge owner's playtests found what tests did not: "the hit does not feel", "everything is plasticine", "cardboard stands", "the run carry is too long" after tiny steering touches.

## 3. One-hand touch control

What the Cat Challenge owner settled after three playtests (18.11.2026); treat it as the proven default, and confirm per game:
- A floating joystick appears where the thumb lands and **stays there**; only the knob moves.
- A quick tap jumps; a jump keeps the run direction (release the stick and tap at once → jump forward); a second finger also jumps.
- The push is automatic on contact; no double-tap dash.
- An upward swipe as "jump" was removed: it fired by accident.
- An optional explicit jump button sits in the settings, off by default.
- Long press selects nothing, opens no context menu and no iOS magnifier; pinch does not zoom the page.

Check one-hand passability of every level with the `fair-bots-balance` procedure.

## 4. Keyboard and pause

- WASD and arrows move, Space jumps, P pauses. **Esc does nothing** (Playgama 1.5.2). Read `KeyboardEvent.code` so AZERTY works.
- Any pause (platform, after an ad, a hidden tab, lost focus) shows a clear "Paused, tap to continue" screen; the game never just stands still. During the ad itself the ad covers the screen. Focus the card so Space or Enter resumes.
- Popups have a ✕; every press has a sound; controls are at least 44 px (primary 48).

## 5. The first minute and teaching

- **Play leads straight into the game:** no choices, no sign-in. Cat Challenge: a fresh player is in the first show right after `game_ready`; a returning player sees the menu (or the hub).
- Teach inside the first match: a pictogram card with 2–4 words and a short demo with the game's real effects (the tile turns red and falls; the hammer hits), skippable, not affecting the match.
- Teach **where and how**: hints before the places that need a jump, and a short lesson with practice right before the round that first needs it.
- Hints advance on the real action; separate desktop (keys) and touch hints; the "seen" flag is saved.
- A separate training mode lives behind a settings button.

## Source

Cat Challenge `OWNER_DECISIONS.md` (playtests 16.11, 17.11 and 18.11.2026), `gamekit/packages/fx/README.md`, `gamekit/packages/input/README.md`, `game/e2e/release/dev-input.mjs`, `docs/design/MASTER_PLAN.md` §6.1, and reviews 07, 08, 10, 26 and 56 of its `docs/reviews/`.
