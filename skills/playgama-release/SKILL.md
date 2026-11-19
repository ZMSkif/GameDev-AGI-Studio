---
name: playgama-release
description: Releasing an HTML5 game on Playgama with the Bridge SDK - the required Bridge steps, the moderation requirement numbers, packaging and archive checks, the release-gate coverage, and the sandbox flow through the Playgama Developer Console MCP tools with the owner's gates (sandbox, catalog and traffic only on the owner's yes, moderation only after the owner's review). Use for any Playgama build, archive, upload, sandbox, moderation, rejection or Bridge question.
---

# Playgama release

Binding: DEC-013 (#13) Playgama first; DEC-058 (#58) check the Bridge API against current docs; DEC-057 (#57) a build profile and QA matrix per platform; DEC-056 (#56) platform adapters; DEC-077 (#78) Semi-Auto release; DEC-009 (#9), DEC-092 (#93), DEC-130 (#132) no publishing or spending without the owner; DEC-016 (#16) report only what ran.

## Step 0: re-check the live rules

Facts below were read on 16–19.11.2026 and will drift. Before each release:
1. If the Playgama Developer Console MCP is connected, read `get_launch_steps` (after `create_application`, with the game's id), `get_game_checklist`, `get_bridge_sdk_docs` and `get_game_guides`. Read each tool's description before calling it: the rules live there.
2. Compare with this skill and write down every difference with its date. Without the MCP, mark platform facts `UNVERIFIED` in the release report.

## Bridge required steps (Bridge wiki "Required steps", 16.11.2026)

1. `playgama-bridge-config.json` next to `index.html` (else the automatic archive check fails).
2. The Bridge script is the **first** script in `<head>`, loaded normally (not async, not from code); `await bridge.initialize()` before the engine and assets; no SDK call before it.
3. Language from `bridge.platform.language` (ISO 639-1), read once after init.
4. Progress only through `bridge.storage.get([...])` / `.set([...],[...])`; all keys in one `get` at start; write only on meaningful changes.
5. Pause and sound: `bridge.platform.isAudioEnabled` at start (false → silent); listen to `AUDIO_STATE_CHANGED` and `PAUSE_STATE_CHANGED`.
6. `bridge.platform.sendMessage('game_ready')` when the first playable frame is on screen and the loading screen is gone.
7. An interstitial at every natural pause, **with no own timers or counters**; frequency is Bridge's and `minimumDelayBetweenInterstitial`.
8. Hide what is not supported: rewarded (`isRewardedSupported`), shop (`payments.isSupported`), leaderboards (`leaderboards.type`), sign-in, external links (`isExternalLinksAllowed`).

In Vite: `playgamaBridge({ mode: 'local' })` from `@playgama/bridge/vite` copies the SDK as a separate unmodified `playgama-bridge.js`. Every product and placement id in code must also be in the Bridge config (a review blocked a publish because three cosmetic products were missing there). Rewarded grants only in the `rewarded` state; Payments: `getPurchases()` on every start, `consumePurchase` for each consumable.

## Requirement numbers (Game Requirements, 16.11.2026; quote the number in every report)

| No. | In short |
|---|---|
| 1.1.1–1.1.2 | current Bridge; all required steps |
| 1.2.1–1.2.7 | no forced sign-in; no external analytics; no external resources; external links only when allowed; no URL binding |
| 1.3.1–1.3.3 | archive ≤ 300 MB; `index.html` at the root; Latin file names; start-up memory peak < 2 GB |
| 1.4.1–1.4.6 | mobile: full screen; keyboard on inputs; orientation (a "rotate" screen when needed); full touch control; long press selects nothing, opens no menu or iOS magnifier; no WebGL warnings |
| 1.5.1–1.5.3 | desktop: keyboard and mouse; **no Esc**; both schemes work |
| 1.6.1–1.6.8 | any screen and orientation; nothing cut off; no page scroll; no overlaps; ✕ on every popup; **one-hand control**; readable text; a 1:1 window filled |
| 1.7.1–1.7.3 | no errors or hangs (rotation, long press, minimise, ads, history); completable; Chrome, Firefox, Opera, Safari, Edge on Windows, macOS, Android, iOS |
| 1.8.1–1.8.2 | video only inside the archive, no system player |
| 2.1.1–2.1.7 | ads only via Bridge; interstitials exist; only in logical pauses; not under the finger; ad orientation = game orientation; sound and game paused during full-screen ads; the game goes on when an ad fails |
| 2.2.1–2.2.5 | rewarded: optional, clear button; can be declined; the reward is a bonus; revive at most once per attempt; reward only after a watched ad |
| 2.3.1–2.3.2 | banners only via Bridge; never over interactive elements |
| 2.4.1–2.4.6 | payments only via Bridge; prices from the catalog; grant after success; consume; restore; no double purchase |
| 2.5.1–2.5.2 | no real money or prizes; no casino or lottery |
| 3.1.1–3.1.3 | progress or interaction; rising difficulty; a tutorial without a wall of text |
| 3.2.1–3.2.3 | saves only through Bridge Storage (not localStorage, IndexedDB or cookies); progress or best result saved; survives reload, rotation and ads |
| 3.3.1–3.3.5 | music and SFX; **recorded ogg or mp3, never synthesised in code**; a mute button; sound and pause from Bridge (also after reload); silence when minimised |
| 3.4.1–3.4.4 | English by default; language only from Bridge; full translation; a clear language selector (self-names or flags, gear or globe icon) |
| 3.5.1 | the title in the game = the title in the application |
| 4.1.x–4.4.1 | forbidden content; rights to all material, no copies or foreign brands; not fully generative AI without visual rework, no emoji icons or template UI; data consent where data is processed |

Common return reasons: progress outside Bridge or written too often; no interstitial or own timers; sound during ads or in the background; cut-off UI (1:1 too); Esc; long-press selection; rewarded without a watched ad; no sound, no mute or synthesised sound; no tutorial; untranslated text; loading before Bridge or no `game_ready`; errors; title mismatch; external links or GA4; template AI look; copying.

## Packaging and archive checks

Build a production archive with a script that fails loudly, never "best effort" (Cat Challenge `tools/package-game.mjs`):
- `index.html` at the root; `playgama-bridge-config.json` and the **unmodified** `playgama-bridge.js` next to it;
- Latin file names (YouTube: only `A–Z a–z 0–9 . - _`, no spaces, ≤ 8,000 files); size ≤ 314,572,800 bytes;
- no source maps; no dev-only code (mocks, debug globals, autoplay hooks); no external URLs; fonts, sounds and decoders inside;
- licence files: the Bridge LGPL-3.0 and GPL-3.0 texts with a link to the sources of exactly the shipped version; one third-party notices file, byte-equal to what a generator builds from the installed packages; the Bridge version read from one source (`@playgama/bridge/package.json`), and the packager fails when a text names another;
- output: `<game>-<version>.zip`, its SHA-256 and a JSON report. The packager never uploads.

## Release gate coverage (production build, then dev build with a mock platform)

Production: Bridge steps and call order, network (no external hosts) and browser-storage traps, the console in a default Chrome, first boot, reload with saves, a page that boots hidden (starts silent and frozen), an unsupported language → English, unsupported payments and rewarded hide their UI, WebGL context loss and restore, one failing asset, a failing code chunk, all audio failing. Dev and mock: full matches with ads shown, skipped and failed; rewarded paths incl. decline and failure; purchases with success, cancel, error, pending restore and a slow double tap; input per scheme incl. no-Esc and long press; layout at 16:9, 9:16, 1:1, 360×640 and 640×360 in the longest languages with glyph checks; HUD overlap by painted boxes; tutorial; a soak with heap after a forced GC; save errors and corrupted saves; perf under phone emulation; a licence audit of the dist folder.

Rules from the Cat Challenge reviews: a check that cannot fail is no check (stale e2e assertions "caught nothing"); play the production archive past the first round before any publish; compare memory, warnings and movement with the previous release; label emulation as emulation (DEC-073, #74). Run the gate with the `release-qa-engineer` role, then a separate `pre-publish-reviewer`.

## The sandbox flow and the owner's gates

| Step | Tools | Who and when |
|---|---|---|
| draft app | `list_applications` first (titles are not unique), then `create_application` (title = in-game title; `agent`/`model` = your own values) | agent |
| archive | `get_game_checklist` → `start_archive_upload` → PUT → `confirm_archive_upload` → `get_archive_status` | agent, after the release gate |
| covers | 3 slots, PNG or JPEG ≤ 10,485,760 B: landscape 1920×1080, square 800×800 (also the icon), portrait 1080×1920; `start_cover_upload` → PUT → `confirm_cover_upload` | agent, after the owner has seen them (4.3) |
| form | `update_application_form`: description and how-to-play ≥ 100 chars; story 150–900 chars, 2–6 sentences, first person; languages as console codes (Ukrainian `UA`, Brazilian Portuguese `PT_BR`); only facts true in the build | agent |
| QA tool | `get_archive_qa_tool_link`, `get_local_game_qa_tool_link` | agent |
| sandbox | `publish_sandbox`: a public page without moderation, no undo | **only after the owner's explicit yes for this game and this build** |
| share | `get_sandbox_share`; take links from tool answers, never build them | agent |
| traffic | `start_sandbox_traffic` spends a bonus | **only on the owner's yes** |
| catalog | `replace_in_app_products` deletes every product left out; `send_playgama_catalog_update` changes the live game for all players | **only on the owner's yes to the exact list** |
| moderation | opens only after the sandbox reaches its targets (play time per category among them, counted daily); `get_submission_state`, `get_sandbox_state` | the owner reviews the game first; submitting, screenshots and rollback happen in the console (no MCP tool) |

Relay a tool's refusal `message` word for word. A permission one game got (Cat Challenge: sandbox publishing, a pre-approved catalog) never carries over to another game or build.

## Store texts and credits

- Credits at the legal minimum; Cat Challenge's owner also ruled: the developer credit first, others in small collapsible text, never list technologies or track titles on screens, store pages or update notes. Confirm this rule per game.
- The one technology name that must stay on screen is "Playgama Bridge … LGPL-3.0-or-later" inside the Licenses view, without "SDK" or a version (a review blocked a build showing the version).

## Other platforms through Bridge

YouTube Playables (initial download ≤ 30 MiB, recommended < 15 MiB; files < 30 MiB; pause only via its SDK, Page Visibility forbidden) is **UNVERIFIED** through Bridge 2.4.2 (see `../engine-profiles/references/web-profile.md` §8). CrazyGames requirements are **UNVERIFIED**; on 16.11.2026 the Playgama wiki said Playgama does not publish there. Partner sieves seen on 16.11.2026: MSN < 50 MB; Facebook needs two of purchases, leaderboards, multiplayer, sharing; Discord needs purchases and multiplayer; GameSnacks files < 10 MiB, start < 15 MiB, total < 100 MiB.

## Source

Cat Challenge `PLATFORM_REQUIREMENTS.md`, `release/PLAYGAMA_SUBMISSION.md` (read through the Playgama MCP on 16–17.11.2026), `tools/package-game.mjs`, `game/e2e/release/*.mjs`, the r17 release (sandbox, 19.11.2026), reviews 01, 17 and 60 of its archive, and the owner's rules in its `OWNER_DECISIONS.md`.
