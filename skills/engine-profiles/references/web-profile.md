# Web profile: stack, versions, subsystems, physics, startup, bench

> **Status: DEC-145, not yet registered.** The owner chose both engine profiles on 19.11.2026. Until the DEC-145 issue exists, the binding contract names only the Godot profile, so the web-profile text here is information, not a rule.

This file is the single source of the web stack tables. Other skills link here instead of copying them.

Source: Cat Challenge `STACK_PLAYBOOK.md`, agreed by Claude, Codex (round 8 «ПОДТВЕРЖДАЮ») and an advisor on 16.11.2026. Labels: **shipped** = imported by the Cat Challenge r17 build (checked in its code on 19.11.2026); **decided** = agreed but not imported by a shipped build. All timings are emulation, not devices.

## 1. Criteria, in this order

- **Licence is a gate, not a score.** MIT, Apache-2.0, BSD, Zlib, CC0 without conditions; LGPL only as a separate unmodified file; own licences (GSAP, Spine) only by a separate owner decision.
1. **Quality for the player:** picture, smoothness, response, sound, time to the first controllable match, memory, heat.
2. **Maintenance:** a live repository that answers bugs. A fresh release is not required (tween.js 2024 and Howler 2023 are fine).
3. **Weight of the start-up path only.** Heavy, high-quality content is allowed; load it after `game_ready` (per round, in the menu, during the tutorial). Moving it past `game_ready` does not make it free: it still costs time to the first match, memory and heat.

The owner's rule (Cat Challenge, 16.11.2026): never cut quality to save kilobytes; weight limits apply only to what is needed before the first interactive frame.

## 2. Renderer by game type

| Game type | Renderer | When something else |
|---|---|---|
| 3D | Three.js `WebGLRenderer` (WebGL2), exact version (r187 shipped) | Babylon.js when the built-ins (Havok, Inspector, GUI, NME) matter more than the start-up path on weak phones, e.g. desktop-first |
| 2.5D (isometric, ortho camera, 3D models) | Three.js, same stack | an isometric game made of sprites is 2D |
| Light 2D: puzzles, match-3, merge, cards, quizzes, runners, clickers; tens to hundreds of objects; UI in DOM | Three.js + `OrthographicCamera` + DOM UI (decided, not shipped) | — |
| Rich 2D: thousands of different sprites, Tiled/LDtk, 9-slice in WebGL, Spine, filters and masks | PixiJS v8 (decided, not shipped by any studio game) | Phaser 4 only for an all-in-one framework, after a trial build on iOS and HiDPI (347 KiB, slower repository) |

- The 2D line is a recommendation, not an automatic rule. One mask or a small map does not need a renderer change. When unsure, prototype the key scene on both and measure (§6).
- Three can draw thousands of sprites only through an own batcher (`InstancedMesh` + atlas + shader): 20,000 sprites took 10.3 ms of JS against 29.4 ms for Pixi `Sprite` and 7.3 ms for Pixi `ParticleContainer` (CPU ×4). One `THREE.Sprite` per object is unusable (5,000 → 71 ms).
- "Not found" is not "does not exist": the official `@esotericsoftware/spine-threejs` 4.3.13 exists (Spine licence; its peer range `three <0.185` does not cover r187, untested).
- Why not Babylon by default for 3D: on the reference scene Three was ready faster than every Babylon build tested (phone emulation 0.49 s against 1.57 s; weak phone 1.37 s against 5.36 s; 155 KiB against 526–871 KiB). The gap for a full game on real devices is not measured. Babylon also calls a CDN for decoders and the Inspector by default, which portals forbid.
- Do not take: Babylon Lite (WebGPU only); TSL / `WebGPURenderer` 2D layers for Three (`three-flatland`, `three-2d`: alpha, no r187; `WebGPURenderer` is 222 KB gzip against 136 KB for `WebGLRenderer`); `cannon-es` (unmaintained since 2022).

## 3. Version policy

- `three` at an exact version, no `^`. Upgrade only when the `peerDependencies` of every dependency cover the new version (`postprocessing` was capped at `<0.188`).
- Every dependency at an exact version in the lockfile; `npm ls three` shows exactly one copy.
- Check current library docs (context7 or the vendor site) before you rely on an API; re-check platform rules before each release (DEC-058, #58).

## 4. Subsystems: ready-made or own

Weights are gzip deltas of a separate build on top of the Three core (`research/bench/libsize.mjs`): an estimate, not the exact addition to a game.

| # | Subsystem | Choice | Status in Cat Challenge r17 | Weight | Own work on top |
|---|---|---|---|---:|---|
| 1 | Characters and animation | ready CC0 clips + own or reworked models, offline retarget in Blender, `AnimationMixer` | shipped | — | the 10-step character process (`art-acceptance` skill); procedural ears, tail, gaze, squash and stretch |
| 2 | Tweens | `@tweenjs/tween.js`; CSS and WAAPI for DOM | **decided, not shipped**: installed but never imported; the shipped game tweens with its own `@gamekit/fx` pool | 3.8 KiB | tween time only from the game loop (pause, hit-stop) |
| 3 | Particles and VFX | `three.quarks` for confetti, flashes, dust; simple geometry for rings, lasers, waves | **decided, not shipped**: the shipped game uses its own `@gamekit/fx` particles | 38.9 KiB | choose by picture and frame time, not weight |
| 4 | Physics | own arcade physics for limited mechanics; fallback §5 | shipped (`@gamekit/arcade-physics`, 120 Hz, deterministic) | own code | gate P1 |
| 5 | Camera | own, `MathUtils.damp`, shake from "trauma" | shipped | ~0 | — |
| 6 | Input | own action layer on Pointer Events + keyboard + Gamepad API | shipped (`@gamekit/input`); `nipplejs` not used | — | one-hand scheme and gestures are always own (Playgama 1.6.6) |
| 7 | Audio engine | Howler + own platform audio gate and buses (music / SFX / UI) | shipped (Howler 2.2.4) | 10.3 KiB | real iOS test: unlock, return from background, ads (`web-audio-lifecycle` skill) |
| 8 | Post-processing | `UnrealBloomPass` from `three/addons` on the high profile | shipped; `postprocessing` (Zlib) not used | 4.9 KiB | the base picture reads without bloom |
| 9 | UI | Preact for menus, shop, settings, tutorial; hot HUD by direct DOM updates | shipped | 6.1 KiB | — |
| 10 | App states | XState v5 for the app life cycle; own per-tick FSM for bots | **decided, not shipped**: installed, never imported | 12.7 KiB | — |
| 11 | Localisation | i18next with local resources + `Intl` | shipped | 16.5 KiB | language source per platform profile; English fallback (`i18n-portal` skill) |
| 12 | Saves | valibot + own format versions, migrations, write queue | shipped (`@gamekit/save`) | 1.6 KiB | storage per platform profile (Playgama: Bridge Storage only) |
| 13 | Debugging | `lil-gui`, `stats-gl`, Spector.js, dev only, cut by `import.meta.env.DEV` | not in the release build (verify the build) | 0 | own collider and bot debug layer |
| 14 | Tests and build | Vite, Vitest, Playwright, `@gltf-transform/cli`, glTF Validator, meshoptimizer, KTX-Software | Vite 8, Vitest, `playwright-core`, the meshopt decoder from `three/examples` shipped; KTX2 not verified in shipped code | tools 0; shipped decoders are not 0 | own checks: network audit, platform limits |
| 15 | Text in 3D | DOM overlay by default; `troika-three-text` only with a local font and a CSP check of its worker | not used | 41–46 KiB | — |
| 16 | 2D physics (2D games) | `planck` (47 KB) or `matter-js` (28 KB); Rapier2D only when needed (0.9–1.3 MB) | not used | — | — |

**Own and reusable core** (in the Cat Challenge repo as `gamekit`; see the `gamekit` skill): the platform adapter and platform profiles; shared time, pause and resume; a loader with retry, abort and disposal; WebGL context-loss handling; data version, seed and input log for bug replay; the asset provenance registry and a Credits screen generated from it; accessibility (safe areas, contrast, reduced motion); the packaging script with network and platform-limit audits.

Game physics, render-object disposal and context-loss recovery are modules behind shared interfaces, not one shared implementation. Reuse is confirmed only by a second game of another type.

## 5. Physics fallback procedure

1. Own arcade physics must pass **P1**: automatic scenarios plus an **independent audit** of the spec and the tests (not the author). Expected values come from formulas, not from the code's output. The visual part is the "feel" gate.
2. Budget: the first run plus **2 fix iterations**. Only the reviewer or the owner resets the counter, never the author.
3. If a required scenario is still red, use the failed cases to pick a candidate quickly, in the order Jolt (`CharacterVirtual`) → Rapier (separate wasm) → Babylon + Havok. **Before acceptance the candidate passes the whole required set**, regressions and feel included. Rank by: all required items, then control quality, then measured performance.
4. A parallel prototype on a ready engine is not required while P1 passes.
5. Start-up cost (weak-phone emulation): Jolt 1,023 KiB, 6.36 s; Rapier wasm 1,351 KiB, 8.82 s; Babylon + Havok 1,195–1,541 KiB, 7.78–9.32 s. Controller quality was not compared by these numbers.
6. Measure physics performance only under constant full load: every participant active for the whole interval, the counter checked at the end.

Cat Challenge result: P1 closed at iteration 2 of 2, 83/83 tests, audited by Codex; 20 active participants cost about 0.06 ms per tick in Chrome.

## 6. Start-up metrics and the bench

Measure both, always:
- time to **`game_ready`** (interactive menu or first playable frame);
- time to the **first controllable match**, including lazily loaded physics and round assets.

The bench (`research/bench/` in the Cat Challenge repo, reusable):
- Vite 8 and headless Chrome through `playwright-core`;
- CDP profiles "phone" (CPU ×4, 10 Mbit/s, RTT 80 ms) and "weak phone" (CPU ×6, 1.6 Mbit/s, RTT 150 ms);
- one readiness protocol, `__bench.readyAt`; an error makes the run FAILED;
- SHA snapshots of every build; a new scene is a folder `src/<name>/`, and the suffix `-1chunk` builds it as one file.

Limits: emulation, not a device; HTTP/1.1; the GPU is not slowed; reference-scene results do not carry over to a game, so measure the game itself. Readiness marks must match across compared scenes (Pixi/Phaser fire on the second tick, Three after the first render; align them before comparing).

A bench or device profile in Chrome is never a physical-device pass (DEC-073, #74). The real-phone gate is a human with the device.

## 7. Quality gates of the web profile

| Gate | What | Who |
|---|---|---|
| P1 | own physics: automatic scenarios + independent audit of spec and tests | author, then another agent or Codex |
| Feel | recordings of game situations **watched by a human**; a recording alone is no proof | the agent records, the owner watches and decides |
| P2 | real Android and iPhone: start-up, sustained FPS, controls, life cycle | a human |
| Sound | a human listens to all sound in the game | a human |
| Visual (Playgama 4.3) | style, cover and icon are not template AI | a human; owner review does not prove 4.3 compliance |
| Release gate | platform requirements by number | an agent plus the platform QA tool (`playgama-release` skill) |

## 8. Platforms

- Each platform has its own build profile and QA matrix (DEC-057, #57). Gameplay never calls a platform SDK directly; adapters isolate ads, payments, identity and storage (DEC-056, #56).
- **Playgama profile:** Playgama Bridge (`@playgama/bridge`, exact version; 2.4.2 shipped; LGPL-3.0-or-later) through `@playgama/bridge/vite` with `mode: 'local'`, so the SDK is a separate unmodified file next to `index.html`. Steps and requirement numbers: `playgama-release` skill.
- **YouTube Playables profile:** its own packaging and life-cycle rules (DEC-059, #59). Through Bridge 2.4.2 it is **UNVERIFIED**: the storage module always subscribes to `visibilitychange` and `pagehide` and wraps `localStorage`, both of which YouTube forbids. Find a confirmed configuration, an SDK fix or a separate adapter first.
- **CrazyGames:** Bridge has a `crazy_games` platform; CrazyGames' own requirements are **UNVERIFIED** until written down before a release there.
