---
name: fair-bots-balance
description: Fair bots and balance testing - bots that see only what the player sees, difficulty that grows with the player, a scripted casual-human tester, held-out seeds, determinism and pinned hashes, passability per control scheme, and long soaks for crowds and NPCs. Use when bots feel unfair or "know ahead", when tuning difficulty or a level, when writing balance or soak tests, or when a crowd walks in place.
---

# Fair bots and balance

Binding: DEC-069 (#70) deterministic gameplay tests in the Godot profile (the web profile's equivalent is in the `engine-profiles` skill); DEC-054 (#54) logic apart from view and input; DEC-071 (#72) long sessions; DEC-082 (#83) major design and economy changes go to the owner; DEC-016 (#16).

## 1. Bots that feel fair

From the Cat Challenge owner's playtest (16.11.2026: bots "much too hard" and "knew ahead where things would be"):
- Bots see only what the player can see, and only after the telegraph or the spawn, with a reaction delay.
- Bots are a bit slower than the player (Cat Challenge: 80–98 %), react late and make mistakes.
- Difficulty is a number from 0 to 1 that grows with the player's experience (Cat Challenge: a new player 0.25, an experienced one 0.8). The numbers are that game's; the shape is the rule.
- Hazards are telegraphed; no death is unavoidable; safe zones are labelled.

## 2. Testing balance

- A scripted **casual human** (reaction about 0.3 s, aim error, hesitation) plays the rounds. It may read only what the screen shows; check its imports and fields statically.
- **Held-out seeds** that never took part in tuning decide the pass rates. Keep tuning seeds and judging seeds apart and check that they never overlap.
- Targets: a pass rate per difficulty level, from the game's design.
- **Per control scheme:** run the same course with the keyboard, the on-screen button and the one-hand touch scheme. Cat Challenge's one-hand final was not reliably passable while keyboard runs were (review 26: 1 of 4 one-hand runs against 4 of 4 keyboard runs). Prompts must never say "wait" forever: sweep stand-back distances and assert a "jump now" appears.
- When balance or physics must change to make it fair, that is the owner's design call: ask with options (DEC-082), for example an assist in the first show or a longer input window. Do not retune on your own.
- Balance suites are slow and flaky under load: run them with other agents idle or with a larger timeout, and name the flaky test in the report.

## 3. Determinism

- Simulation on a fixed tick, seeded randomness, input as data. No `Math.random`, `Date` or `performance.now` in simulation code; a source lint test enforces it.
- A golden hash of the state after N ticks (Cat Challenge NPCs: 20 citizens over 36,000 ticks, also after a save and restore mid-run). Two runs must match; the reviewer computes it twice on the same browser. Re-pin a hash only on purpose, with the reason in the commit. Cross-browser determinism is not claimed unless measured.
- Maps and sets are looked up, never iterated for results, unless sorted first.

## 4. Crowds and NPCs: long soaks

Short tests miss slow failures. In Cat Challenge, a walking-in-place oscillation showed only after 200 s, and a face-to-face lock at one junction only at about 7.6 minutes on one seed.
- Soak for 30 minutes on several seed-clocks (seed × time of day), with and without the player.
- Measure stuck runs, total stuck time, direction flips and walking in place; bound each in the test.
- Stage a reproduction from the replay and sweep the start positions (±0.1 m) to see how often a lock happens.
- Kill mutants of the steering and holding code (an always-false "blocked ahead", a removed invalidate); a mutant that survives is a missing test.
- Check the crowd reads as a crowd in the game camera (a review blocked a plaza event that showed 5 citizens where the concept showed 14).

## Source

Cat Challenge `OWNER_DECISIONS.md` (playtest 16.11.2026 and later rulings), `docs/city/CITY_PLAN.md` CK2 card, `docs/status/RESUME_2026-11-23.md`, and reviews 26, 29, 40, 44, 50, 53, 55 and 64 of its `docs/reviews/`.
