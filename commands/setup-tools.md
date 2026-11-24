---
description: Set up GameDev Studio's tools in a friendly way - one short question with the free recommended set, more tools only on request - install only what is chosen after a yes, and open the local studio panel.
argument-hint: "[all | group or tool id]"
---

Apply the `studio-setup` skill, including its rule on which folder is the game (the folder Claude was started in, with or without the `.gamedev-studio` marker; never a temporary folder).

- **No `$ARGUMENTS`:** do only the skill's first setup (section 2): `studio_tools.py first-setup --json`, then one short question about that set. If it is empty, say in one line that everything recommended is installed. Do not list other tools, their prices or their conditions; end with the single line about asking for all tools.
- **`$ARGUMENTS` is `all`, a catalog group or a tool id:** go through those tools, as in the skill's "Later, only on request" part, naming a tool's conditions only when the person picks it.

Install only what the person chose, with `scripts/studio_tools.py install <id> --yes`, and finish by offering `scripts/studio_panel.py`.
