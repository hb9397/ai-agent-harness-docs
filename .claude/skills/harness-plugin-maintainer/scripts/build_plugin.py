#!/usr/bin/env python3
"""Build deterministic ai-agent-harness plugin runtime."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import zipfile
from pathlib import Path

from plugin_common import (
    GENERATED_BY,
    PLUGIN_ID,
    PLUGIN_ROOT_REL,
    PLUGIN_VERSION,
    copy_tree_clean,
    ensure_no_symlink,
    generated_marker,
    load_json,
    remove_dir,
    repo_root,
    tree_manifest,
    user_skills,
    write_json,
    write_text,
)


MARKDOWN_PRODUCERS = [
    "harness-setup",
    "harness-bootstrap",
    "context-doc",
    "design-doc",
    "design-prototype-docs",
    "impl-doc",
    "impl-fe-be-doc",
]
TEXT_SUFFIXES = {
    ".md",
    ".json",
    ".py",
    ".sh",
    ".template",
    ".html",
    ".txt",
    ".yml",
    ".yaml",
}


def copy_user_skills(root: Path, plugin_root: Path, capabilities: dict) -> None:
    logical = capabilities["logical_user_skills"]
    current = user_skills(root)
    if current != logical:
        raise RuntimeError(f"user skill inventory mismatch: {current} != {logical}")

    codex_skills = plugin_root / "runtime" / "codex" / "skills"
    claude_skills = plugin_root / "runtime" / "claude" / "skills"
    codex_skills.mkdir(parents=True, exist_ok=True)
    claude_skills.mkdir(parents=True, exist_ok=True)
    for skill in logical:
        copy_tree_clean(root / "skills" / skill, codex_skills / skill)
        copy_tree_clean(root / "skills" / skill, claude_skills / skill)


def add_claude_aliases(root: Path, plugin_root: Path, runtime_allowlist: dict) -> None:
    template = (root / "maintainer" / "skills" / "harness-plugin-maintainer" / "templates" / "claude-alias-skill.md").read_text(encoding="utf-8")
    aliases = {
        "humanize": "Humanize",
        "humanize-redo": "Humanize Redo",
    }
    for alias, title in aliases.items():
        write_text(
            plugin_root / "runtime" / "claude" / "skills" / alias / "SKILL.md",
            template.format(
                alias_name=alias,
                alias_title=title,
                alias_description=f"Claude compatibility alias for humanize-korean ({alias}).",
            ),
        )

    agent_template = (root / "maintainer" / "skills" / "harness-plugin-maintainer" / "templates" / "claude-agent.md").read_text(encoding="utf-8")
    for agent in runtime_allowlist["claude_runtime_agents"]:
        write_text(
            plugin_root / "runtime" / "claude" / "agents" / f"{agent}.md",
            agent_template.format(agent_name=agent),
        )


def copy_im_not_ai_root(root: Path, plugin_root: Path) -> None:
    target = plugin_root / "runtime" / "claude" / "im-not-ai-root"
    target.mkdir(parents=True, exist_ok=True)
    copy_tree_clean(root / "skills" / "humanize-korean" / "references", target / "references")
    copy_tree_clean(root / "skills" / "humanize-korean" / "scripts", target / "scripts")
    copy_tree_clean(root / "skills" / "humanize-korean" / "evals", target / "evals")


def manifest(plugin_root: Path, platform: str) -> dict:
    runtime_key = "codex" if platform == "codex" else "claude"
    payload = {
        "id": PLUGIN_ID,
        "name": "AI Agent Harness",
        "version": PLUGIN_VERSION,
        "description": "Project harness plugin for Codex and Claude Code.",
        "generated_by": GENERATED_BY,
        "skills": f"./runtime/{runtime_key}/skills",
    }
    if platform == "claude":
        payload["agents"] = "./runtime/claude/agents"
        payload["im_not_ai_root"] = "./runtime/claude/im-not-ai-root"
    return payload


def marketplace(plugin_root: Path, platform: str) -> dict:
    entry = {
        "id": PLUGIN_ID,
        "name": "AI Agent Harness",
        "description": "Install ai-agent-harness user skills without cloning the management repository.",
        "source": "./",
        "manifest": "./.codex-plugin/plugin.json" if platform == "codex" else "./.claude-plugin/plugin.json",
        "repository": "https://github.com/epoko77-ai/ai-agent-harness-docs",
        "license": "SEE LICENSE AND THIRD_PARTY_NOTICES.md",
    }
    if platform == "codex":
        entry["category"] = "developer-productivity"
        entry["policy"] = "private-git-backed"
    return {"schema_version": "1.0.0", "generated_by": GENERATED_BY, "plugins": [entry]}


def build_capabilities(root: Path, runtime_allowlist: dict, markdown_flow: dict, plugin_root: Path) -> dict:
    base = load_json(root / "maintainer" / "plugin" / "CAPABILITIES.json")
    value = copy.deepcopy(base)
    value.update({
        "generated_by": GENERATED_BY,
        "version": PLUGIN_VERSION,
        "plugin_id": PLUGIN_ID,
        "codex": {
            "physical_skills": 18,
            "physical_agents": 0,
            "skills_path": "./runtime/codex/skills",
        },
        "claude": {
            "physical_skills": 20,
            "physical_agents": 3,
            "skills_path": "./runtime/claude/skills",
            "agents_path": "./runtime/claude/agents",
            "runtime_agents": runtime_allowlist["claude_runtime_agents"],
            "aliases": runtime_allowlist["capability_aliases"],
        },
        "markdown_artifact_flow": {
            "producer_count": len(markdown_flow["producer_skills"]),
            "producers": [item["skill"] for item in markdown_flow["producer_skills"]],
            "handoff_target": "humanize-korean",
            "proposal_only": True,
        },
    })
    return value


def notices(root: Path, plugin_root: Path) -> None:
    license_template = (root / "maintainer" / "skills" / "harness-plugin-maintainer" / "templates" / "plugin-license.md").read_text(encoding="utf-8")
    write_text(plugin_root / "LICENSE", license_template)
    (plugin_root / "licenses").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / "maintainer" / "upstreams" / "provenance" / "im-not-ai" / "LICENSE", plugin_root / "licenses" / "im-not-ai-LICENSE")
    shutil.copyfile(root / "THIRD_PARTY_NOTICES.md", plugin_root / "THIRD_PARTY_NOTICES.md")


def lock(root: Path, plugin_root: Path, artifact_manifest: list[dict]) -> dict:
    upstream_lock = load_json(root / "maintainer" / "upstreams" / "lock.json")
    packaged = copy.deepcopy(upstream_lock)
    for state in packaged.get("states", []):
        if state.get("id") == "im-not-ai":
            state["packaged"] = {
                "plugin_id": PLUGIN_ID,
                "version": PLUGIN_VERSION,
                "packaged_at": "2026-07-29",
                "artifact_manifest_sha256": next(item["sha256"] for item in artifact_manifest if item["path"] == "CAPABILITIES.json"),
            }
    packaged["generated_by"] = GENERATED_BY
    packaged["released_state_preserved"] = True
    return packaged


def write_archive(plugin_root: Path) -> Path:
    archive = plugin_root.parent / f"{PLUGIN_ID}-{PLUGIN_VERSION}.zip"
    if archive.exists():
        archive.unlink()
    fixed_dt = (2026, 7, 29, 0, 0, 0)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(p for p in plugin_root.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(str(path.relative_to(plugin_root)).replace("\\", "/"), fixed_dt)
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    return archive


def normalize_text_payload(plugin_root: Path) -> None:
    for path in sorted(p for p in plugin_root.rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lines = [line.rstrip() for line in text.splitlines()]
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")


def build(root: Path) -> dict:
    plugin_root = root / PLUGIN_ROOT_REL
    remove_dir(plugin_root)
    plugin_root.mkdir(parents=True, exist_ok=True)

    capabilities = load_json(root / "maintainer" / "plugin" / "CAPABILITIES.json")
    runtime_allowlist = load_json(root / "maintainer" / "plugin" / "runtime-allowlist.json")
    markdown_flow = load_json(root / "maintainer" / "inventory" / "markdown-artifact-flow.json")

    copy_user_skills(root, plugin_root, capabilities)
    add_claude_aliases(root, plugin_root, runtime_allowlist)
    copy_im_not_ai_root(root, plugin_root)
    notices(root, plugin_root)

    write_json(plugin_root / ".codex-plugin" / "plugin.json", manifest(plugin_root, "codex"))
    write_json(plugin_root / ".claude-plugin" / "plugin.json", manifest(plugin_root, "claude"))
    write_json(plugin_root / ".agents" / "plugins" / "marketplace.json", marketplace(plugin_root, "codex"))
    write_json(plugin_root / ".claude-plugin" / "marketplace.json", marketplace(plugin_root, "claude"))
    write_json(plugin_root / "CAPABILITIES.json", build_capabilities(root, runtime_allowlist, markdown_flow, plugin_root))
    normalize_text_payload(plugin_root)

    artifact_manifest = tree_manifest(plugin_root)
    write_json(plugin_root / "UPSTREAMS.lock.json", lock(root, plugin_root, artifact_manifest))
    artifact_manifest = tree_manifest(plugin_root)
    write_json(plugin_root / "MANIFEST.sha256.json", {"generated_by": GENERATED_BY, "files": artifact_manifest})
    archive = write_archive(plugin_root)

    release = {
        "schema_version": "1.0.0",
        "generated_by": GENERATED_BY,
        "plugin_id": PLUGIN_ID,
        "version": PLUGIN_VERSION,
        "plugin_root": str(PLUGIN_ROOT_REL).replace("\\", "/"),
        "archive": str(archive.relative_to(root)).replace("\\", "/"),
        "archive_sha256": __import__("plugin_common").sha256_file(archive),
        "logical_user_skills": 18,
        "codex_physical_skills": 18,
        "codex_physical_agents": 0,
        "claude_physical_skills": 20,
        "claude_physical_agents": 3,
        "markdown_producers": MARKDOWN_PRODUCERS,
        "released_state_preserved": True,
        "push_tag_release_created": False,
    }
    write_json(root / "maintainer" / "plugin" / "release.json", release)
    ensure_no_symlink(plugin_root)
    return release


def check(root: Path) -> int:
    release_before = load_json(root / "maintainer" / "plugin" / "release.json") if (root / "maintainer" / "plugin" / "release.json").exists() else None
    build(root)
    release_after = load_json(root / "maintainer" / "plugin" / "release.json")
    if release_before and release_before != release_after:
        print("ERROR: plugin build drift detected", file=sys.stderr)
        return 1
    print("plugin build check passed")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    if args.check:
        return check(root)
    release = build(root)
    print(json.dumps(release, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
