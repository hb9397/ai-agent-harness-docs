#!/usr/bin/env python3
"""Validate generated ai-agent-harness plugin."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from plugin_common import GENERATED_BY, PLUGIN_ID, PLUGIN_ROOT_REL, PLUGIN_VERSION, load_json, repo_root


FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def dirs(path: Path) -> list[str]:
    return sorted(item.name for item in path.iterdir() if item.is_dir())


def validate_manifest(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    codex = load_json(plugin_root / ".codex-plugin" / "plugin.json")
    claude = load_json(plugin_root / ".claude-plugin" / "plugin.json")
    for name, manifest in [("codex", codex), ("claude", claude)]:
        if manifest.get("id") != PLUGIN_ID:
            error(errors, f"{name} manifest id mismatch")
        if manifest.get("version") != PLUGIN_VERSION:
            error(errors, f"{name} manifest version mismatch")
        if manifest.get("generated_by") != GENERATED_BY:
            error(errors, f"{name} manifest generated marker missing")
        for key, value in manifest.items():
            if key.endswith("path") or key in {"skills", "agents", "im_not_ai_root"}:
                if isinstance(value, str) and not value.startswith("./"):
                    error(errors, f"{name} manifest path must start with ./: {key}={value}")


def validate_counts(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    codex_skills = dirs(plugin_root / "runtime" / "codex" / "skills")
    claude_skills = dirs(plugin_root / "runtime" / "claude" / "skills")
    claude_agents = sorted(path.stem for path in (plugin_root / "runtime" / "claude" / "agents").glob("*.md"))
    caps = load_json(plugin_root / "CAPABILITIES.json")
    allowlist = load_json(root / "maintainer" / "plugin" / "runtime-allowlist.json")

    if len(codex_skills) != 18:
        error(errors, f"Codex physical skills must be 18, got {len(codex_skills)}")
    if len(claude_skills) != 20:
        error(errors, f"Claude physical skills must be 20, got {len(claude_skills)}")
    if claude_agents != sorted(allowlist["claude_runtime_agents"]):
        error(errors, "Claude agent allowlist mismatch")
    if any(name in codex_skills or name in claude_skills for name in ["custom-skill-design", "harness-plugin-maintainer", "skill-portfolio-maintainer"]):
        error(errors, "maintainer skill leaked into runtime")
    if caps["claude"]["aliases"].get("humanize") != "humanize-korean" or caps["claude"]["aliases"].get("humanize-redo") != "humanize-korean":
        error(errors, "humanize aliases missing")
    producers = caps["markdown_artifact_flow"]["producers"]
    if producers != ["harness-setup", "harness-bootstrap", "context-doc", "design-doc", "design-prototype-docs", "impl-doc", "impl-fe-be-doc"]:
        error(errors, "Markdown producer inventory mismatch")


def validate_skill_files(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    for path in list((plugin_root / "runtime" / "codex" / "skills").glob("*/SKILL.md")) + list((plugin_root / "runtime" / "claude" / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        if not FRONTMATTER_RE.match(text):
            error(errors, f"missing SKILL frontmatter: {path}")
        if re.search(r"(?m)^model\s*:", text):
            error(errors, f"model field forbidden: {path}")
        if "agent: fork" in text:
            error(errors, f"agent: fork forbidden: {path}")


def validate_notices(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    required = [
        "LICENSE",
        "licenses/im-not-ai-LICENSE",
        "THIRD_PARTY_NOTICES.md",
        "UPSTREAMS.lock.json",
        "CAPABILITIES.json",
        "MANIFEST.sha256.json",
    ]
    for item in required:
        if not (plugin_root / item).exists():
            error(errors, f"missing plugin metadata: {item}")
    lock = load_json(plugin_root / "UPSTREAMS.lock.json")
    im_not_ai = next((item for item in lock.get("states", []) if item.get("id") == "im-not-ai"), None)
    if not im_not_ai or not im_not_ai.get("packaged"):
        error(errors, "im-not-ai packaged state missing")
    if im_not_ai and im_not_ai.get("released") is not None:
        error(errors, "released state must remain unset")
    release = load_json(root / "maintainer" / "plugin" / "release.json")
    if release.get("version") != PLUGIN_VERSION or release.get("plugin_id") != PLUGIN_ID:
        error(errors, "release metadata version/plugin mismatch")
    if release.get("push_tag_release_created") is not False:
        error(errors, "release metadata must not mark push/tag/release as created")


def validate_marketplace(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    codex = load_json(plugin_root / ".agents" / "plugins" / "marketplace.json")
    claude = load_json(plugin_root / ".claude-plugin" / "marketplace.json")
    for name, market in [("codex", codex), ("claude", claude)]:
        if market.get("generated_by") != GENERATED_BY:
            error(errors, f"{name} marketplace generated marker missing")
        plugins = market.get("plugins", [])
        if len(plugins) != 1 or plugins[0].get("id") != PLUGIN_ID:
            error(errors, f"{name} marketplace plugin entry mismatch")


def main() -> int:
    root = repo_root()
    errors: list[str] = []
    plugin_root = root / PLUGIN_ROOT_REL
    if not plugin_root.exists():
        error(errors, "plugin root missing; run build_plugin.py first")
    else:
        validate_manifest(root, errors)
        validate_counts(root, errors)
        validate_skill_files(root, errors)
        validate_notices(root, errors)
        validate_marketplace(root, errors)
    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        return 1
    print("plugin validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
