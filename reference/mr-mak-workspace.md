# Mr. Mak with GameDev Studio

Mr. Mak Desktop can open your installed Claude Code or Codex in the current game folder. GameDev Studio supplies the game-production skills and roles. The game repository's GitHub Issues and pull requests hold tasks and acceptance.

1. Install GameDev Studio using [its installation guide](../INSTALL.md) and confirm that it loads in your CLI from the game's root. The game should be marked with `.gamedev-studio` according to step 8. The plugin's `python scripts/doctor.py` command checks local prerequisites.
2. If you want the desktop view, install [Mr. Mak v0.6.6](https://github.com/witnesstodark/mr-mak-workspace/releases/tag/v0.6.6) separately. In **Chats → New chat**, choose your installed CLI and select the existing game root or the worktree assigned to the piece. Start a chat and confirm that the CLI can find the studio skills and current Issue before it edits files.
3. Keep project and report links in the optional Workspace view. For an art or gameplay piece, the `review-evidence` skill records the playable result, captures and verdict on the Issue or PR. The [Gallery card editor](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/docs/editable-cards.md) can display selected evidence as a reference. Add only media approved for that view.
4. When moving to a fresh chat, use the `studio-handoff` skill to record or prepare the checkpoint. Open the new chat in the assigned worktree and point it to the Issue or PR. It verifies the revision and ownership before resuming.
5. For phone access, the owner can opt in using [Mr. Mak's Tailscale and pairing instructions](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/docs/mobile-access.md). The computer keeps the running CLI and its sign-in. Pairing and compatibility with the owner's local CLI versions should be checked on that installation.

[Upstream attribution and license](mr-mak-notices.md).
