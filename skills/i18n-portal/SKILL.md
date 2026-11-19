---
name: i18n-portal
description: Localisation of portal games in many languages (Cat Challenge shipped 8 - EN, RU, UK, ES, PT, DE, FR, TR) - language from the platform, the validator, length lints at 360 px and small landscapes, font glyph checks, and a language review of Russian and Ukrainian that is honest about not being a human native read. Use when adding or changing in-game text, adding a language, fixing clipped or untranslated text, or reviewing a translation.
---

# Portal localisation

Binding: DEC-068 (#69) static checks; DEC-070 (#71) browser, touch and orientation checks; DEC-016 (#16) report only what was done; DEC-074 (#75) evidence with environment and date. Platform: Playgama 3.4.1–3.4.4 and 1.6.x (`playgama-release` skill).

## 1. Language set and source

- The owner chooses the languages per game. Cat Challenge: 8, English default, then RU, UK, ES, PT (Brazilian), DE, FR, TR.
- On Playgama the language comes only from `bridge.platform.language`, read once; unknown languages fall back to English. The language selector shows self-names (or flags) behind a gear or globe icon.
- Text inside the 3D scene: only numbers, `$` and the title, or it must be translated too.
- The Playgama form codes differ from ISO: Ukrainian is `UA`, Brazilian Portuguese is `PT_BR`.

## 2. The validator (run on every text change)

- every key of the master language exists in every file; no extra keys;
- plurals, placeholders and allowed formats match the master;
- keys that must be identical in all languages (the game title, Playgama 3.5.1) are identical;
- a value equal to English is an error unless it is on an allow-list;
- a length lint against the master (Cat Challenge used ×1.3);
- scan keys built by helper functions as well as literal keys (a review found a sign key built by a `name('…')` helper that the literal scan missed);
- code defaults must not carry stale wording: they show when a language file fails to load.

Keep one glossary of the game's terms per language and write every wording change into it, not into a report that is not in the repository. Keep design documents in sync with the shipped strings, so the owner reads what ships.

## 3. Layout on small screens

Capture every touched state in the longest languages (de, fr, ru, uk; tr for glyphs) at 1280×720, 405×720, **360×640**, 640×360 and a 1:1 window; for anything shown in landscape, also 568×320, 667×375, 740×360 and 844×390. Measure where the letters themselves end, not the pill behind them. Fail on any clip, mid-word break, overlap, page scroll or control outside the viewport. Watch the smallest font size (a 360×640 card dropped to 8 px in r17, against 10.8 px before).

Seen in Cat Challenge: countdown words (READY / SET / GO) ran off the right edge in landscape in six languages while portrait was fine; a German compound overflowed a 64 px tile by 4 px on each side.

## 4. Fonts and glyphs

- Draw the risky characters on a canvas with the UI font stack and compare with the `.notdef` (tofu) bitmap of an unassigned code point: Ukrainian і ї є ґ, Turkish ğ ş ı İ.
- Check characters that `Intl` and translators add: French numbers from `Intl` use U+202F (narrow no-break space), and the shipped Nunito files had neither U+202F nor U+2030, so the browser fell back to a system font for them. Include them in the font subset or avoid them.
- Build the font subset from the actual character set of all language files.

## 5. Language review of ru and uk

An AI reviewer reads Russian and Ukrainian for: wrong meaning; address that assumes the player's gender; Russian calques and surzhyk in Ukrainian; register and tone; clashes with the game's glossary; case forms of the game's names. It also writes notes for native readers of the other languages, marked as uncertain.

This is an **AI language review, not a human native-speaker read** (DEC-016). Say so in the report, list what a human native speaker should confirm, and never mark "native-checked" without a person. Wording the owner chose in the plan stays unless the owner changes it.

## Source

Cat Challenge `game/i18n/_tools/validate-i18n.mjs` and `GLOSSARY.md`, `game/e2e/release/dev-layout.mjs` and `hud-boxes.mjs`, reviews 24, 35, 59, 61 and 62 of its `docs/reviews/`, `docs/status/RESUME_2026-11-23.md` (I18N-C follow-ups), and its `OWNER_DECISIONS.md` (8 languages, 16.11.2026).
