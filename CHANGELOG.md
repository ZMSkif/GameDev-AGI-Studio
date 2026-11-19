# Changelog

All notable changes to the `gamedev-studio` plugin. The version lives only in `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`, and a release tag `vX.Y.Z` must match it. From the next release on, each section is the release notes for its tag (see "Releases" in `README.md`). 0.1.0 and 0.2.0 were not tagged. The v0.3.0 release notes were written by hand, in Russian and English, before this file existed.

## [0.4.0] - 2026-11-20

### Added
- **Memory** over Hindsight 1.2.2 (MIT) through MCP: the `memory` skill and `scripts/hindsight_smoke.py` ([DEC-024](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/24), DEC-101–DEC-104, [DEC-138](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/140)).
  - A studio bank and a bank per project; task memories are tagged `task:<n>` in the project bank. Each bank gets its own MCP endpoint, because the multi-bank endpoint crosses banks.
  - Provenance on every memory; facts only as evidence, observations as hints.
  - The four retrieval modes, with Auto as default.
  - Agents never pass `document_id` or `update_mode`, because a repeated id replaces memory.
  - Only the owner deletes memory.
  - The smoke test (S1–S9) prints integration-evidence rows. Persistence counts only after a restart.
- **Context Intelligence, light** ([DEC-102](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/103)): the `context-brief` skill, `/gamedev-studio:brief-piece` and `scripts/brief_piece.py`. One worker brief per piece card, with:
  - the decisions, skills, owned files and the files they read;
  - the earlier review notes, verbatim;
  - memories with full provenance;
  - the revision of every source.

  It refuses a clashing port range, flags names that nothing defines any more (and lists where it found the others), and says that a mockup is not done.
- **Learning and Improvement, light** ([DEC-105](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/107), [DEC-106](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/108)): the `lessons` skill, `/gamedev-studio:mine-lessons` and `scripts/mine_lessons.py`.
  - It mines the review archive for recurring failure classes behind a noise guard: 2 independent pieces or 1 blocker.
  - The report shows every hit with its file and line; doubtful wording is marked, never dropped.
  - Nothing is stored unless the agent names the class with `--keep` after reading the hits.
  - It stores lessons with provenance and without a `document_id`. The run marker is stored only after every lesson was.
  - It proposes plugin changes on a local branch. Push and PR need the owner's yes.
- Contracts v1.4.0: `knowledge-policy.json` 1.1.0, checked by `validate_contracts.py`, with the backend verified by the smoke evidence on [#150](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/150). It covers the memory backend, bank naming, storage rules, learning rules with their sources, and the known limits.
- `validate_plugin.py`: a command may not have a skill's name.
- [DEC-146](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/164): the platform parts DEC-143 deferred stay deferred for good. `system-boundaries.json` 1.3.0, `orchestration-policy.json` and `coordinator.openapi.json` link it, and `studio-rules` rule (h) says so.
- `CHANGELOG.md`, `scripts/release_check.py` and the `Release` workflow: a pushed `vX.Y.Z` tag is checked against both `plugin.json` versions and this file, and the GitHub release is created from its section. README "Releases" lists the steps.

## [0.3.0] - 2026-11-19

### Added
- Two engine profiles ([DEC-145](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/161), the owner's answer «Оба профиля»): **web** for HTML5 portal games (Three.js for 3D, 2.5D and light 2D; PixiJS v8 for rich 2D) and **Godot 4.x** for heavy or desktop games. DEC-012 is refined, not cancelled.
- 12 skills built from what the "$1,000,000 Cat Challenge" web game proved: `engine-profiles`, `web-stack-choice`, `playgama-release`, `web-monetization`, `art-acceptance`, `asset-licensing`, `i18n-portal`, `fair-bots-balance`, `game-feel-controls`, `web-audio-lifecycle`, `orchestration-playbook`, `gamekit`.
- 5 on-demand specialist roles: `release-qa-engineer`, `pre-publish-reviewer`, `art-reviewer`, `i18n-language-reviewer`, `crowd-soak-reviewer`.
- 5 Claude Code commands: `new-web-game`, `release-gate`, `package-playgama`, `review-piece`, `archive-reviews`.
- `scripts/archive_reviews.py`: saves reviewer verdicts verbatim from a session transcript.
- Validator checks for the engine profiles, the commands, the studio-team role index and every skill, role, agent, command and local file reference.

### Changed
- Contracts v1.2.0. `game-production-policy.json` 2.0.0 is **breaking**: the top-level `engine` key moved to `engine_profiles.profiles.<id>.engine`, with a migration note in the file. `system-boundaries.json` 1.2.0 adds the `web-game` module.
- Base roles follow the engine profile the contract and the game's approved architecture name.

## [0.2.0] - 2026-11-19

### Added
- The nine base Agent Team roles as Claude Code subagents, and the `studio-team` skill that indexes them for Codex (PLUGIN-02, #158).
- Quality-gate hooks scoped to studio projects: no commit or push to `main`, no commit of credential-like files such as `.env`, `*.pem` and `*.key`, and a git and gh preflight (PLUGIN-05, #159).

### Fixed
- Hooks fail open on an invalid working directory; tests no longer depend on the runner's branch (#160).

## [0.1.0] - 2026-11-17

### Added
- The repository as a Claude Code and Codex plugin and marketplace, with the `studio-rules` skill ([DEC-143](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/146); PLUGIN-01, #157).
- Contracts v1.1.0: the self-hosted platform modules are marked deferred under DEC-143 (PLUGIN-07, #156).
