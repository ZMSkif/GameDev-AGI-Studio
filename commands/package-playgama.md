---
description: Build the production archive of a game for Playgama and check it - index.html at the root, Bridge config and the unmodified SDK beside it, Latin names, size, no source maps, dev code or external URLs, licence texts - then write the zip, its SHA-256 and a report. Never uploads.
argument-hint: "[version, e.g. 0.1.18] [--dry-run]"
---

Package the current game for Playgama: `$ARGUMENTS`.

1. Apply the `playgama-release` skill, section "Packaging and archive checks". Use the game's own packaging script if it has one (for example `node tools/package-game.mjs`); otherwise write one in the game repository that fails loudly on every check below, and have it reviewed like any piece.
2. Make a clean production build of the commit you name.
3. Check, and stop on the first failure with the reason:
   - `index.html` at the archive root; `playgama-bridge-config.json` and the unmodified `playgama-bridge.js` next to it; every product and placement id used by the code present in the config;
   - Latin file names; total size ≤ 314,572,800 bytes;
   - no source maps, no mock platform or debug globals, no external URLs; fonts, sounds and decoders inside;
   - the Bridge LGPL and GPL texts with the link to the exact version's sources; one third-party notices file equal to what the generator builds from the installed packages; the Bridge version from one source;
   - every shipped file has a licence row (`asset-licensing` skill).
4. Write `<game>-<version>.zip`, its SHA-256 and a JSON report of the checks into the game's release folder. With `--dry-run`, build and check but write no zip.
5. Do not upload. Uploading and publishing are separate steps of the `playgama-release` skill, and publishing needs the owner's yes.
