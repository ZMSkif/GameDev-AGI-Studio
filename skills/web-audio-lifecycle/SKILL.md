---
name: web-audio-lifecycle
description: Browser game audio across its life cycle - the platform audio gate, music that must come back after a tab switch, minimise, focus loss, an ad or a platform pause, the Howler streamed-music volume trap, iOS unlock and play-never-starts protection, and tests that read real volume instead of trusting a mock. Use when sound or music is missing, doubled or plays at the wrong time, when wiring audio to ads and pause, or when reviewing audio code.
---

# Web audio life cycle

Binding: DEC-070 (#71) browser and device checks; DEC-071 (#72) long sessions; DEC-073 (#74) emulation is labelled; DEC-075 (#76) reproduce, root cause, regression test, review; DEC-141 (#143) unique audio. Platform: Playgama 2.1.6 (sound and game paused during full-screen ads), 3.3.1–3.3.5.

## 1. The gate

Sound plays only when the platform allows it (`isAudioEnabled`, pause events, full-screen ads) **and** the player has not muted it. If the page boots hidden or Bridge reports audio off, start silent and frozen. Silence in the background. Buses: music, SFX, UI.

The Cat Challenge owner's rule (P0, 18.11.2026): after any pause (tab switch, minimise, focus loss, an ad, a platform pause) the music comes back, the same track at the same volume; if the platform muted the sound, silence until the platform unmutes it.

## 2. The Howler streamed-music trap (Howler 2.2.4)

For streamed (html5) music, `play()` followed at once by `fade()` or `volume()` queues the fade while Howler waits for the browser to confirm playback (its internal play lock). When playback starts, Howler runs only a queued `play` step, so the fade never runs and a track created at volume 0 stays at 0 while `currentTime` advances. Every pause cycle adds another stuck entry.
- Set the volume after playback has really started (or apply it without a queued fade), and do the same for loops and any streamed sound effect.
- Test the real element: after the first start, after a crossfade and after each blur, visibility, mute and ad cycle, assert `node.volume > 0` and an empty queue.
- A new regression test must fail on the old code (the Cat Challenge fix: 6 of 8 new tests failed before, 8 of 8 passed after).
- iOS Safari ignores `element.volume`, so this mechanism does not explain an iPhone report; test iOS separately.

## 3. iOS and "play never starts"

- Unlock audio on the first gesture; Howler's `unlock` event fires once per page.
- A watchdog for "play never started" doubled the music in Cat Challenge: Howler waits in a `loading` state while a stream buffers, so a watchdog that fires on "data available, paused, play pending" restarts a voice that later starts too. If you build one: fire only in the `loaded` state, check only this voice's element, stop that sound before retrying, and test with `readyState` 3 during the wait and a late start. Unrequested hardening is a regression risk; a reviewer must see it.

## 4. Ads and platform pause

- Bridge reports one combined pause. On Playgama a stale "focus lost" pause after an ad could be ignored, but on platforms that send their own pause or mute (the QA tool, CrazyGames, Yandex and others), ignoring it lost the platform's next pause. Ignore a stale pause only on the platform classes that never send their own.
- A timeout that ends an ad must not un-pause or un-mute the game when the host page took the focus; leave the platform's pause and show the pause card.
- Do not let a 20 s "no answer" backstop fire under a normal long ad: derive it from the ad-open cap.

## 5. Loading and mixing

- Recorded files only (ogg + mp3), no synthesis (Playgama 3.3.2).
- Keep the start-up audio set small; load a sound before the moment it is needed. Do not download variants that are never chosen.
- Stop the same short sound from stacking on itself (two applause copies 0.8 s apart).
- YouTube Playables: pause and resume only through its SDK; Page Visibility is forbidden (see the `engine-profiles` web reference, §8).

## 6. Tests that catch these bugs

Mocks hid both big bugs: the Howler mock completed fades instantly and had no play lock, and the e2e checks meant only "`play()` was called". Read the actual volume in a real browser, on the production build with the real Bridge in its local fallback, through hidden→visible and blur→focus on the menu, in an intro and in a round. A headless page stays "visible", so a real tab switch and a real iPhone remain human checks; report them as `not_run`.

## Source

Cat Challenge `gamekit/packages/audio/README.md`, `game/e2e/release/prod-audio-start.mjs`, its `OWNER_DECISIONS.md` (18.11.2026), and reviews 08, 11, 15, 22, 35, 48 and 52 of its `docs/reviews/`.
