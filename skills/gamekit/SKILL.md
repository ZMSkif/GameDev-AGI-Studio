---
name: gamekit
description: How to use gamekit, the reusable TypeScript game packages built for Cat Challenge (platform facade over Playgama Bridge, save, audio, input, theme, fx, arcade-physics, hub, prompts, npc, quests, dialogue, three-batch) - the package map, the start-up order, the contract rules and their current status, plus the extraction spec for moving them to their own versioned repository. Use when a web-profile game needs a platform adapter, saves, audio, input, effects, physics, a hub, quests, dialogue or NPCs, or when planning the gamekit extraction.
---

# gamekit

> **Status: DEC-145, not yet registered.** The owner chose both engine profiles on 19.11.2026. Until the DEC-145 issue exists, the binding contract names only the Godot profile, so the web-profile text here is information, not a rule.

**Where it is (19.11.2026):** `gamekit/packages/*` inside the Cat Challenge repository. Every package is `0.1.0`, `private: true`, scope `@gamekit`, and exports raw `src/*.ts` (no build step), so only a Vite consumer in the same workspace can use it. **Do not move or copy the code now:** the game is still changing these packages. The extraction is specified in `references/extraction-spec.md`.

## Package map

| Package | What it gives | Notes |
|---|---|---|
| `platform` | a typed `Platform` facade over Playgama Bridge 2.4.2 and a deterministic mock; leaderboards, remote config, a purchase guard | game code never touches `window.bridge`; no browser storage or Page Visibility in the package |
| `save` | versioned saves over the platform key/value store; valibot schemas, migrations, debounced single-flight writes | all keys read in one `get` at start (Bridge step 4) |
| `audio` | Howler 2.2.4, three buses, manifest events, music crossfade, the platform audio gate | static no-synthesis test; see the `web-audio-lifecycle` skill |
| `input` | actions `move`, `jump`, `dash`, `pause` from keyboard, one-hand and two-hand touch, gamepad | the action set is fixed today |
| `theme` | themes as lazily loaded data; apply order and failure handling; CSS adapter; WCAG contrast helpers | engine-neutral |
| `fx` | particle pool, hit-stop, tween pool, easing, DOM popups, seeded cosmetic RNG; `/three` adapters (sticker atlas, batches) | `three` is a peer dependency |
| `arcade-physics` | deterministic 120 Hz arcade physics; P1 spec and result | **no README yet** (`P1_SPEC.md`, `P1_RESULT.md`) |
| `hub` | scene-module contract (`load/enter/update/exit/dispose/stats`), place registry, spawn points, chunk loader with abort and prefetch | **no README yet** |
| `prompts` | zone prompts: nearest wins, hysteresis, stand-to-enter countdown, E / Enter / gamepad A | **no README yet** |
| `npc` | deterministic citizens on a waypoint graph; schedules as pure functions of seed, day, tick and id | needs `arcade-physics` |
| `quests` | data-driven quests, rewards granted once, UTC daily and weekly cycles, story chapters by day | valibot + `save` |
| `dialogue` | dialogue graphs, facts, actions, day-seeded variants, a validator CLI | no dependencies |
| `three-batch` | instanced batching for Three.js | **no README yet** |

## Start-up order (Playgama)

Bridge script first in `<head>` → `await bridge.initialize()` → create the platform → read **all** save keys in one call → restore purchases → read the pause and audio state and subscribe → load the engine and the first scene → `game_ready` → load round assets, packs and music after it.

## Rules while it lives in the game repository

- Each package's contract is its `src/api.ts`; change it only through the game's coordinator, and say it in the PR.
- Engine-neutral packages have no Three.js, DOM, clocks or `Math.random`; keep it that way (a source lint test enforces it in `npc`).
- Pin external versions exactly (`howler` 2.2.4, `@playgama/bridge` 2.4.2, `valibot` 1.5.0); `three` as a peer with a tested range.
- Keep game-specific bits (rounds, the `__game` debug global, `?round=`) out of packages, behind small adapters, so extraction stays cheap.

## Using it in a new game today

There is no registry and no approved starter template yet, and DEC-132 (#134) allows new games only from verified templates without hidden project assumptions. So:
1. Tell the owner that gamekit is not extracted; propose the extraction (`references/extraction-spec.md`) or a workspace copy as a stopgap. Vendoring is an emergency path only.
2. Never copy Cat Challenge's game code (rounds, bots, host, data, layouts); only packages.
3. A package counts as reusable only after a **second game of another type** uses it without changes to its contract.

## Source

Cat Challenge `gamekit/packages/*/README.md` and `package.json` files (read 19.11.2026), `docs/city/CITY_PLAN.md` §5 and §11, `docs/stack-plugin/PLUGIN_PLAN.md` §3 and §11, `STACK_PLAYBOOK.md` §4, the stack-plugin hand-over note (17.11.2026).
