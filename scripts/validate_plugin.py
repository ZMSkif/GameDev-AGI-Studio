#!/usr/bin/env python3
"""Read-only, dependency-free check of the Claude Code / Codex plugin scaffold.

Checks:
  * the four manifests parse as JSON objects;
  * name and version agree across the Claude and Codex plugin.json files;
  * version is set only in plugin.json (not in the Claude marketplace entry);
  * both marketplaces list the plugin with a source that resolves to the repo root;
  * every skills/*/SKILL.md has name + description frontmatter, only those keys,
    and the name matches its directory;
  * hooks/hooks.json (if present) parses and has a top-level "hooks" key;
  * agents/: every role in contracts/v1/agent-team-policy.json `minimum_roles` is present
    as agents/<role-slug>.md (extra roles are allowed), each agent has a `name` matching
    its file name, a non-empty `description`, none of the frontmatter keys Claude Code
    ignores for plugin agents, and a reference to the studio-rules skill;
  * skills/studio-team/SKILL.md names every minimum role and the role files it points to exist;
  * no manifest, agent or skill contains a secret-looking value.

Usage: python scripts/validate_plugin.py [repo_root]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

CLAUDE_PLUGIN = PurePosixPath(".claude-plugin/plugin.json")
CLAUDE_MARKETPLACE = PurePosixPath(".claude-plugin/marketplace.json")
CODEX_PLUGIN = PurePosixPath(".codex-plugin/plugin.json")
CODEX_MARKETPLACE = PurePosixPath(".agents/plugins/marketplace.json")
MANIFESTS = (CLAUDE_PLUGIN, CLAUDE_MARKETPLACE, CODEX_PLUGIN, CODEX_MARKETPLACE)

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_NUM = r"(?:0|[1-9]\d*)"  # numeric identifier without leading zeros
SEMVER_RE = re.compile(rf"^{_NUM}\.{_NUM}\.{_NUM}(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$")
ALLOWED_FRONTMATTER = {"name", "description"}
MAX_SKILL_LINES = 500
MAX_SKILL_NAME = 64
MAX_SKILL_DESCRIPTION = 1024

AGENT_POLICY = PurePosixPath("contracts/v1/agent-team-policy.json")
# Frontmatter keys that Claude Code ignores for plugin agents; declare hooks and MCP
# servers at plugin level instead.
FORBIDDEN_AGENT_KEYS = {"permissionMode", "hooks", "mcpServers", "initialPrompt"}
STUDIO_RULES_SKILL = "studio-rules"
TEAM_SKILL = PurePosixPath("skills/studio-team/SKILL.md")

SECRET_VALUE_PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("OpenAI/Anthropic-style key", re.compile(r"\bsk[_-][A-Za-z0-9_-]{16,}")),
    ("npm token", re.compile(r"\bnpm_[A-Za-z0-9]{20,}")),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("bearer credential", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    ("credentials in URL", re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@")),
]
# Matched against the key split into words (camelCase and separators become "_"), so
# `GITHUB_TOKEN` and `apiKey` match but `tokenizer` does not.
SECRET_KEY_RE = re.compile(
    r"(?:^|_)(?:password|passwd|secret|token|api_?key|access_?key|private_?key)s?(?:_|$)"
)
# A reference to an environment variable (`${GITHUB_TOKEN}`, `$TOKEN`) holds no secret.
ENV_REFERENCE_RE = re.compile(r"^\$\{?[A-Z0-9_]+\}?$")


def normalized_key(key: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    return re.sub(r"[^A-Za-z0-9]+", "_", spaced).lower()


def load_json(root: Path, rel: PurePosixPath, errors: list[str]):
    path = root / rel
    if not path.is_file():
        errors.append(f"{rel}: file is missing")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"{rel}: cannot parse JSON ({exc})")
        return None
    if not isinstance(data, dict):
        errors.append(f"{rel}: top level must be a JSON object")
        return None
    return data


def check_secrets(rel: PurePosixPath, data, errors: list[str]) -> None:
    """Flag secret-looking string values and secret-named keys that hold a value."""

    def visit(value, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else key
                if (
                    SECRET_KEY_RE.search(normalized_key(key))
                    and isinstance(child, str)
                    and child.strip()
                    and not ENV_REFERENCE_RE.match(child.strip())
                ):
                    errors.append(f"{rel}: key '{child_path}' looks like a secret and has a value")
                visit(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")
        elif isinstance(value, str):
            for label, pattern in SECRET_VALUE_PATTERNS:
                if pattern.search(value):
                    errors.append(f"{rel}: value at '{path}' looks like a secret ({label})")

    visit(data, "")


def scan_text_for_secrets(rel: PurePosixPath, text: str, errors: list[str]) -> None:
    for label, pattern in SECRET_VALUE_PATTERNS:
        if pattern.search(text):
            errors.append(f"{rel}: contains a secret-looking value ({label})")


def source_path(source) -> str | None:
    """Extract the local path from a marketplace source (string or object)."""
    if isinstance(source, str):
        return source
    if isinstance(source, dict):
        for key in ("path", "url"):
            if isinstance(source.get(key), str):
                return source[key]
    return None


def resolves_to_root(root: Path, source) -> bool:
    text = source_path(source)
    if text is None or "://" in text or Path(text).is_absolute():
        return False
    return (root / text).resolve() == root.resolve()


def check_marketplace(root: Path, rel: PurePosixPath, data, plugin_name: str, errors: list[str]) -> None:
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append(f"{rel}: 'plugins' must be a non-empty list")
        return
    entries = [p for p in plugins if isinstance(p, dict) and p.get("name") == plugin_name]
    if not entries:
        errors.append(f"{rel}: no plugin entry named '{plugin_name}'")
        return
    for entry in entries:
        if "version" in entry:
            errors.append(f"{rel}: plugin entry must not set 'version' (version lives only in plugin.json)")
        if not resolves_to_root(root, entry.get("source")):
            errors.append(f"{rel}: source {entry.get('source')!r} does not resolve to the repository root")


def parse_frontmatter(text: str):
    """Return (fields, body); fields is None without frontmatter. Simple `key: value` only."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for end in range(1, len(lines)):
        if lines[end].strip() != "---":
            continue
        fields: dict[str, str] = {}
        for line in lines[1:end]:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if ":" not in line:
                return {"__invalid__": line}, ""
            key, _, value = line.partition(":")
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            fields[key.strip()] = value
        return fields, "\n".join(lines[end + 1:])
    return None, text


def check_skills(root: Path, errors: list[str]) -> None:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        errors.append("skills/: directory is missing")
        return
    skill_dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir())
    if not skill_dirs:
        errors.append("skills/: no skill directories found")
    for directory in skill_dirs:
        rel = PurePosixPath("skills") / directory.name / "SKILL.md"
        skill_file = root / rel
        if not skill_file.is_file():
            errors.append(f"{rel}: file is missing")
            continue
        try:
            text = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{rel}: cannot read ({exc})")
            continue
        scan_text_for_secrets(rel, text, errors)
        fields, _ = parse_frontmatter(text)
        if fields is None:
            errors.append(f"{rel}: missing YAML frontmatter")
            continue
        if "__invalid__" in fields:
            errors.append(f"{rel}: invalid frontmatter line {fields['__invalid__']!r}")
            continue
        for key in ("name", "description"):
            if not fields.get(key):
                errors.append(f"{rel}: frontmatter '{key}' is missing or empty")
        if len(fields.get("name", "")) > MAX_SKILL_NAME:
            errors.append(f"{rel}: name is longer than {MAX_SKILL_NAME} characters")
        if len(fields.get("description", "")) > MAX_SKILL_DESCRIPTION:
            errors.append(f"{rel}: description is longer than {MAX_SKILL_DESCRIPTION} characters")
        extra = sorted(set(fields) - ALLOWED_FRONTMATTER)
        if extra:
            errors.append(f"{rel}: frontmatter keys outside the portable subset: {', '.join(extra)}")
        if fields.get("name") and fields["name"] != directory.name:
            errors.append(f"{rel}: name '{fields['name']}' does not match directory '{directory.name}'")
        if len(text.splitlines()) > MAX_SKILL_LINES:
            errors.append(f"{rel}: longer than {MAX_SKILL_LINES} lines")


def role_slug(role: str) -> str:
    """'Publishing & Analytics Agent' -> 'publishing-analytics-agent'."""
    return re.sub(r"[^a-z0-9]+", "-", role.lower()).strip("-")


def load_minimum_roles(root: Path, errors: list[str]) -> list[str] | None:
    """The role titles from the agent team policy; None (with an error) when unusable."""
    policy = load_json(root, AGENT_POLICY, errors)
    if policy is None:
        return None
    roles = policy.get("minimum_roles")
    if not isinstance(roles, list) or not roles or not all(isinstance(r, str) and r.strip() for r in roles):
        errors.append(f"{AGENT_POLICY}: 'minimum_roles' must be a non-empty list of role titles")
        return None
    slugs = [role_slug(r) for r in roles]
    if len(set(slugs)) != len(slugs):
        errors.append(f"{AGENT_POLICY}: 'minimum_roles' contains duplicate roles")
        return None
    return roles


def check_agents(root: Path, roles: list[str] | None, errors: list[str]) -> None:
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        errors.append("agents/: directory is missing")
        return
    # Secrets: every file under agents/, not only the Markdown ones.
    for path in sorted(p for p in agents_dir.rglob("*") if p.is_file()):
        rel = PurePosixPath(path.relative_to(root).as_posix())
        try:
            scan_text_for_secrets(rel, path.read_text(encoding="utf-8"), errors)
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{rel}: cannot read as UTF-8 text ({exc})")
    if roles is not None:
        for role in roles:
            rel = PurePosixPath("agents") / f"{role_slug(role)}.md"
            if not (root / rel).is_file():
                errors.append(f"{rel}: file is missing (required role '{role}' from {AGENT_POLICY})")
    for path in sorted(agents_dir.rglob("*.md")):
        rel = PurePosixPath(path.relative_to(root).as_posix())
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # already reported above
        fields, body = parse_frontmatter(text)
        if fields is None:
            errors.append(f"{rel}: missing YAML frontmatter")
            continue
        if "__invalid__" in fields:
            errors.append(f"{rel}: invalid frontmatter line {fields['__invalid__']!r} (use single-line `key: value`)")
            continue
        if not fields.get("name"):
            errors.append(f"{rel}: frontmatter 'name' is missing or empty")
        elif fields["name"] != path.stem:
            errors.append(f"{rel}: name '{fields['name']}' does not match file name '{path.stem}'")
        if not fields.get("description"):
            errors.append(f"{rel}: frontmatter 'description' is missing or empty")
        forbidden = sorted(set(fields) & FORBIDDEN_AGENT_KEYS)
        if forbidden:
            errors.append(f"{rel}: frontmatter keys ignored for plugin agents: {', '.join(forbidden)}")
        if STUDIO_RULES_SKILL not in body:
            errors.append(f"{rel}: body must tell the role to apply the {STUDIO_RULES_SKILL} skill first")


def check_team_skill(root: Path, roles: list[str] | None, errors: list[str]) -> None:
    """The studio-team skill is how Codex gets the roles; it must index every minimum role."""
    path = root / TEAM_SKILL
    if not path.is_file():
        errors.append(f"{TEAM_SKILL}: file is missing")
        return
    if roles is None:
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return  # reported by check_skills
    for role in roles:
        role_file = f"agents/{role_slug(role)}.md"
        if role not in text:
            errors.append(f"{TEAM_SKILL}: does not name role '{role}'")
        if role_file not in text:
            errors.append(f"{TEAM_SKILL}: does not reference '{role_file}'")
        if not (root / role_file).is_file():
            errors.append(f"{TEAM_SKILL}: referenced role file '{role_file}' does not exist")


def check_hooks(root: Path, errors: list[str]) -> None:
    rel = PurePosixPath("hooks/hooks.json")
    if not (root / rel).is_file():
        return
    data = load_json(root, rel, errors)
    if data is None:
        return
    check_secrets(rel, data, errors)
    if "hooks" not in data:
        errors.append(f"{rel}: must have a top-level 'hooks' key")
    elif not isinstance(data["hooks"], dict):
        errors.append(f"{rel}: 'hooks' must be an object")


def check_plugin_manifest(rel: PurePosixPath, data, errors: list[str]) -> None:
    name, version = data.get("name"), data.get("version")
    if not isinstance(name, str) or not NAME_RE.match(name):
        errors.append(f"{rel}: 'name' must be kebab-case")
    elif name.startswith(("claude-", "anthropic-")):
        errors.append(f"{rel}: 'name' must not start with 'claude-' or 'anthropic-'")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        errors.append(f"{rel}: 'version' must be a semver string")


def check_codex_skills_path(root: Path, ref, errors: list[str]) -> None:
    """The Codex `skills` path must be a relative directory inside the repository root."""
    if not isinstance(ref, str) or not ref.strip():
        errors.append(f"{CODEX_PLUGIN}: 'skills' must be a relative path string, got {ref!r}")
        return
    if ref.startswith(("/", "\\")) or Path(ref).is_absolute() or PureWindowsPath(ref).is_absolute():
        errors.append(f"{CODEX_PLUGIN}: 'skills' {ref!r} must be relative, not absolute")
        return
    target = (root / ref).resolve()
    if root != target and root not in target.parents:
        errors.append(f"{CODEX_PLUGIN}: 'skills' {ref!r} escapes the repository root")
    elif not target.is_dir():
        errors.append(f"{CODEX_PLUGIN}: 'skills' {ref!r} does not point to a directory")


def validate(root) -> list[str]:
    """Return a list of error strings; empty means the scaffold is valid."""
    root = Path(root).resolve()
    errors: list[str] = []
    loaded = {rel: load_json(root, rel, errors) for rel in MANIFESTS}

    for rel, data in loaded.items():
        if data is not None:
            check_secrets(rel, data, errors)

    claude, codex = loaded[CLAUDE_PLUGIN], loaded[CODEX_PLUGIN]
    if claude is not None:
        check_plugin_manifest(CLAUDE_PLUGIN, claude, errors)
    if codex is not None:
        check_plugin_manifest(CODEX_PLUGIN, codex, errors)
        if "skills" in codex:
            check_codex_skills_path(root, codex["skills"], errors)
    if claude is not None and codex is not None:
        if claude.get("name") != codex.get("name"):
            errors.append(f"name mismatch: {claude.get('name')!r} (claude) != {codex.get('name')!r} (codex)")
        if claude.get("version") != codex.get("version"):
            errors.append(
                f"version mismatch: {claude.get('version')!r} (claude) != {codex.get('version')!r} (codex)"
            )

    plugin_name = claude.get("name") if claude is not None else None
    if isinstance(plugin_name, str):
        for rel in (CLAUDE_MARKETPLACE, CODEX_MARKETPLACE):
            if loaded[rel] is not None:
                check_marketplace(root, rel, loaded[rel], plugin_name, errors)

    check_skills(root, errors)
    roles = load_minimum_roles(root, errors)
    check_agents(root, roles, errors)
    check_team_skill(root, roles, errors)
    check_hooks(root, errors)
    return errors


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"Plugin validation failed with {len(errors)} error(s)")
        return 1
    print("Plugin manifests, marketplaces, skills and agents are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
