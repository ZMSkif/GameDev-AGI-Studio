# gamekit extraction spec

A specification, not a tracker: it says what the extraction must achieve and how it is accepted. The steps become GitHub Issues in a Project once the owner says yes (DEC-002, #2; DEC-008, #8). Nothing here is started.

Binding: DEC-066 (#67) a shared component library uses quality certification and semantic versioning; DEC-132 (#134) new games start from verified templates with no hidden project assumptions; DEC-001 (#1) branches and PRs; DEC-009 (#9) no paid actions or publishing without the owner; DEC-090 (#91) no secrets in repositories or prompts.

## 1. Own versioned repository

- A private repository (name and owner account: the owner decides), a workspace of packages, one folder per package with `src/`, `tests/`, `README.md`, `CHANGELOG.md`.
- **Build step:** `tsc -b` to `dist/*.js` + `*.d.ts`; `exports` with a `types` condition; `files: ["dist", "README.md"]`. Raw TypeScript in `node_modules` works only for Vite consumers and is fragile.
- **Distribution, for the owner to choose:** GitHub Packages (a real npm registry with a version per package; installing needs a classic token with `read:packages` in the user's `~/.npmrc`, never in a repository; the npm scope must match the owner account, so `@gamekit/*` is renamed); or one package from a git tag (no token, but one version for everything); vendoring only as an emergency path. Creating repositories, tokens and pushes needs the owner's yes.
- Move by copying, keeping `arcade-physics/history/` (the P1 iteration snapshots) as process documentation.

## 2. Semantic versions per package

- The public contract is the package's `src/api.ts`. A breaking contract change is a major bump (a minor while at `0.x`) with a migration note in the CHANGELOG; an addition is a minor; a fix is a patch.
- Start every package at `0.1.0`. **`1.0.0` only after a second game of another type uses it** without contract changes (the reuse rule of `STACK_PLAYBOOK.md` §4).
- Internal dependencies (`save`, `audio` → `platform`; `quests` → `save`; `npc` → `arcade-physics`) use `^` ranges inside the workspace; external ones are exact (`howler` 2.2.4, `@playgama/bridge` 2.4.2, `valibot` 1.5.0); `three` is a peer with the tested range narrowed from today's `>=0.170.0`.
- One copy of `three` in every consumer (`npm ls three` in CI).

## 3. Quality certification (DEC-066)

A package version is certified only when all of these pass in CI and an independent reviewer confirms them:
1. typecheck and the package's own tests; a mutant spot-check on the contract (a reviewer's mutants must die);
2. the README states the contract, the platform requirements it covers (by number) and the known traps;
3. determinism where claimed: a golden hash computed twice (npc, arcade-physics, quests);
4. no engine, DOM, clock or `Math.random` in engine-neutral packages (source lint);
5. a consumer test: the first game's build switched to the published version passes its full suite and e2e, and its archive differs only in import paths;
6. for a style-bearing package (theme, fx), a visual check that reuse does not carry one game's look into another (the reason DEC-066 exists).

## 4. Starter template (DEC-132)

- Variants: `three-3d` (proven by a shipped game), `three-2d-lite` (Three + `OrthographicCamera` + DOM UI; experimental until a game ships on it), and `pixi-2d` only after the first rich-2D game.
- Common parts: the `platform → save → audio → input` skeleton on the mock platform behind the platform adapter (DEC-056, #56); per platform profile its own wiring (DEC-057, #57), e.g. for Playgama: Bridge first in `index.html`, `playgama-bridge-config.json` and `vite.config.ts` with `playgamaBridge({ mode: 'local' })`; a Credits screen generated from the licence registry, language files for the owner's language set, a no-synthesis test, a smoke e2e, and empty game documents (requirements, stack decision, licence registry).
- **No assets in the template** (Sonniss and similar may never be published; fonts are fetched by the setup step), no names, rounds, palettes, texts or balance numbers of any existing game: anything game-specific appears only as a neutral example marked `example`.
- Acceptance: a tiny 2D game and a tiny 3D game are generated from the template non-interactively, built, packaged with a dry run, and pass the smoke e2e and a quick release gate in a clean folder on Linux CI or WSL2. Then a human runs `/gamedev-studio:new-web-game` once in a clean folder.

## 5. The four packages without a README

`arcade-physics`, `hub`, `prompts` and `three-batch` need a README before certification: purpose, the `api.ts` contract, a quick start, determinism and performance notes (for `arcade-physics`: the model, parameters, tick rate, the P1 gate and its independent audit), tests, and the platform requirements covered. Write them in the game repository first, reviewed like any piece, so the extraction copies documented code.

## 6. Candidates and limits

- Strongest new candidate: the game's render layer rule (`game/src/world/layers.ts`, 79 lines), which closes a whole class of z-fighting bugs.
- Theme service, FX recipes, UI kit, match flow, meta, FTUE and balance harnesses go to the template as examples, not packages, until a second game needs them.
- Before extraction, re-inventory the packages against this spec: the game added save v4, leaderboards and remote config after the first plan.

## Source

The plugin plan and stack playbook of the studio's first shipped web game (17.11.2026) and the gamekit READMEs and `package.json` files (19.11.2026).
