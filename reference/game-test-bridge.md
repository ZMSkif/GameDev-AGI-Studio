# Game test bridge

Canvas games draw their state into pixels, so the browser runner cannot read a score or a pause flag from the page. A game exposes a small test bridge instead, and scenarios check it declaratively. The runner only calls the two functions below; scenarios never carry code.

```js
// Only in development and QA builds, never in the release build.
if (import.meta.env.DEV || new URLSearchParams(location.search).has("qa")) {
  window.__gameTest = {
    // A plain, JSON-serialisable snapshot of what the scenarios check.
    state: () => ({
      scene: game.scene.name,
      score: game.score,
      paused: game.paused,
      player: { lives: game.player.lives, x: Math.round(game.player.x) },
    }),
    // Named commands the scenarios may call. Unknown names throw.
    command: (name, args) => {
      if (name === "pause") return game.pause();
      if (name === "add-coins") return game.wallet.add(args.n);
      throw new Error(`Unknown test command ${name}`);
    },
  };
}
```

Keep the bridge out of the shipped archive: gate it behind a development flag and check the release ZIP in `build_release_report.py` and the `playgama-release` audit.

## Scenario steps

| Step | Fields | What it does |
| --- | --- | --- |
| `state` | `path` and exactly one of `equals`, `not_equals`, `at_least`, `at_most`, `includes`, `exists` | Reads `window.__gameTest.state()` at the dotted `path` (for example `player.lives`) and waits up to `timeout_ms` for the condition. A failure records the expected and actual values. |
| `command` | `name`, optional `args` (JSON, under 2 KB) | Calls `window.__gameTest.command(name, args)` and records its result. |
| `tap_at` | `selector`, `x`, `y` (fractions 0–1 of the element) | Taps (touch profiles) or clicks (mouse profiles) a point on a canvas or any element. |
| `wait` | `ms` (0–10000) | Waits, for example for a transition to finish. Prefer a `state` check when the game exposes the state. |
| `frame` | — | Saves a checkpoint frame without doing anything. |

The existing steps (`click`, `tap`, `press`, `visible`, `text`, `reload`) keep working.

## Profiles

```json
"profiles": {
  "phone-uk": {"width": 360, "height": 780, "dpr": 2, "locale": "uk-UA", "timezone": "Europe/Kyiv", "label": "Phone · uk"},
  "desktop":  {"width": 1280, "height": 720, "input": "mouse", "label": "Desktop"}
},
"viewports": ["phone-uk", "desktop", "square"]
```

Fields: `width`, `height` (200–4096 CSS px), `dpr` (1–4), `locale`, `timezone`, `input` (`touch` or `mouse`, default `touch`), `color_scheme`, `mobile`, `label`. `viewports` lists the profiles to run, from the scenario's own profiles and the built-in `portrait`, `landscape` and `square`. `--profiles a,b` runs a subset.

## Step frames

`"step_frames": true` in the scenario, or `--step-frames`, saves a frame after the ready check and after every step; a failed step always gets a frame. The check inspector links each check to its frame, and the report adds a step-by-step strip with the baseline and candidate side by side.
