---
description: Start the local GameDev Studio panel for this game to manage tools, keys and browser QA runs.
argument-hint: "[--lang ru|en]"
---

Apply the `studio-setup` skill, section 5, and its rule on which folder is the game: the folder Claude was started in is the game, with or without the `.gamedev-studio` marker; never a temporary folder. Run `scripts/studio_panel.py --game <the game folder>` with `$ARGUMENTS`, in the background, and give the person the one-time address it prints. Remind them that it serves this computer only and stops with its button or Ctrl+C.
