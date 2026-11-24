---
description: Ask about each optional GameDev Studio tool with clear options, install only the chosen free ones after a yes, and open the local studio panel.
argument-hint: "[group or tool id]"
---

Apply the `studio-setup` skill, including its rule on which folder is the game (the folder Claude was started in, with or without the `.gamedev-studio` marker; never a temporary folder). Limit the questions to `$ARGUMENTS` when it names a catalog group or tool id; otherwise go through every group with tools that are not installed. Install only what the person chose, with `scripts/studio_tools.py install <id> --yes`, and finish by offering `scripts/studio_panel.py`.
