# GameDev AGI Studio — agent rules

1. Before starting work, run `gh issue list --label decision --limit 1000`, review **all relevant approved decisions** and their cited sources; decisions are binding and agents must not modify, bypass or supersede them.
2. Read `contracts/v1/` before designing interfaces. Decisions live in GitHub Issues, tasks in GitHub Issues/Projects; do not create duplicate Markdown trackers.
3. Implement in separate branches/worktrees via pull requests. Never push directly to `main` (except the empty-repository bootstrap already performed).
4. Do not invent tests, integrations, permissions, subscription entitlements or approvals. Record observed evidence.
5. Never commit secrets, spend money, publish games, change approved design/architecture or perform destructive actions without explicit owner approval.
6. If a required tool is unavailable, stop only the affected task; do not silently replace it with an inferior tool. Preserve quality and request recovery.
7. Begin with repository/decision/contract audit, then create your own phased GitHub Issues and Projects from the binding decisions; start with feasibility tests, not production claims.
8. For each PR: link decisions and tasks, tests and actual results, rollback, risks, licensing and independent review.
9. Treat the 2026-11-14 architecture baseline as a **consolidated source**, not a verbatim transcript of all 142 historical answers; never fabricate original dialogue citations.

10. On first setup, create the **Decision Register** GitHub Project with `Area` and `Phase` fields, attach all `decision` Issues (script: `scripts/setup_decision_register.sh`); never recreate existing decisions.
11. Validate `contracts/v1/manifest.json` and run `python scripts/validate_contracts.py` before creating implementation plans.
12. Plugin structure (DEC-143, #146): the repository root is a Claude Code and Codex plugin named `gamedev-studio` (`.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/marketplace.json`, `skills/`, `agents/`, `hooks/`). Version lives only in the two `plugin.json` files and must match. Run `python scripts/validate_plugin.py` and `claude plugin validate . --strict` when changing it.
