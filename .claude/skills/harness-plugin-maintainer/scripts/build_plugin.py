#!/usr/bin/env python3
"""Build deterministic ai-agent-harness plugin runtime."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

from plugin_common import (
    GENERATED_BY,
    PLUGIN_ID,
    PLUGIN_ROOT_REL,
    PLUGIN_VERSION,
    copy_tree_clean,
    ensure_no_symlink,
    load_json,
    repo_root,
    sha256_file,
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
    ".csv",
    ".py",
    ".sh",
    ".template",
    ".html",
    ".txt",
    ".yml",
    ".yaml",
}
PLUGIN_DISPLAY_NAME = "AI Agent Harness"
PLUGIN_DESCRIPTION = "Project harness plugin for Codex and Claude Code."
MARKETPLACE_NAME = "ai-agent-harness"
MAINTAINER_NAME = "AI Agent Harness Maintainers"
REPOSITORY_URL = "https://github.com/epoko77-ai/ai-agent-harness-docs"
ROOT_CODEX_MARKETPLACE = Path(".agents") / "plugins" / "marketplace.json"
ROOT_CLAUDE_MARKETPLACE = Path(".claude-plugin") / "marketplace.json"
EXECUTABLE_SUFFIXES = {".sh"}
PACKAGED_INTEGRATION_MODES = {"adapted", "vendored"}


def pending_user_skills(root: Path) -> list[str]:
    """Canonical user skills that are intentionally not shipped yet.

    Packaging inclusion is declared explicitly rather than inferred from upstream
    lifecycle. A relationship can be promoted to active — so the skill records
    real provenance and existing skills may reference it — while the packaging
    phase has not happened yet.
    """
    capabilities = load_json(root / "maintainer" / "plugin" / "CAPABILITIES.json")
    pending = sorted(capabilities.get("pending_packaging", []))
    logical = set(capabilities.get("logical_user_skills", []))
    overlap = sorted(set(pending) & logical)
    if overlap:
        raise RuntimeError(f"pending_packaging must not overlap logical_user_skills: {overlap}")
    missing = [name for name in pending if not (root / "skills" / name / "SKILL.md").is_file()]
    if missing:
        raise RuntimeError(f"pending_packaging lists non-canonical skills: {missing}")
    return pending


def check_user_skill_inventory(root: Path, capabilities: dict) -> None:
    logical = capabilities["logical_user_skills"]
    pending = pending_user_skills(root)
    packageable = [skill for skill in user_skills(root) if skill not in pending]
    if packageable != logical:
        raise RuntimeError(
            f"user skill inventory mismatch: {packageable} != {logical} (pending: {pending})"
        )


def copy_user_skills(root: Path, plugin_root: Path, capabilities: dict) -> None:
    logical = capabilities["logical_user_skills"]

    codex_skills = plugin_root / "runtime" / "codex" / "skills"
    claude_skills = plugin_root / "runtime" / "claude" / "skills"
    codex_skills.mkdir(parents=True, exist_ok=True)
    claude_skills.mkdir(parents=True, exist_ok=True)
    for skill in logical:
        copy_tree_clean(root / "skills" / skill, codex_skills / skill)
        copy_tree_clean(root / "skills" / skill, claude_skills / skill)


def manifest(platform: str) -> dict:
    runtime_key = "codex" if platform == "codex" else "claude"
    payload = {
        "name": PLUGIN_ID,
        "version": PLUGIN_VERSION,
        "description": PLUGIN_DESCRIPTION,
        "author": {
            "name": MAINTAINER_NAME,
            "url": REPOSITORY_URL,
        },
        "homepage": REPOSITORY_URL,
        "repository": REPOSITORY_URL,
        "keywords": ["agent-harness", "skills", "codex", "claude-code"],
        "skills": f"./runtime/{runtime_key}/skills/",
    }
    if platform == "codex":
        payload["interface"] = {
            "displayName": PLUGIN_DISPLAY_NAME,
            "shortDescription": "Reusable project harness skills for Codex and Claude Code.",
            "longDescription": "Install the shared project setup, documentation, implementation, review, and Korean document refinement workflows.",
            "developerName": MAINTAINER_NAME,
            "category": "Productivity",
            "capabilities": ["Read", "Write"],
            "websiteURL": REPOSITORY_URL,
        }
    else:
        payload["displayName"] = PLUGIN_DISPLAY_NAME
    return payload


def marketplace(platform: str) -> dict:
    if platform == "codex":
        return {
            "name": MARKETPLACE_NAME,
            "interface": {"displayName": PLUGIN_DISPLAY_NAME},
            "plugins": [
                {
                    "name": PLUGIN_ID,
                    "source": {
                        "source": "local",
                        "path": f"./{PLUGIN_ROOT_REL.as_posix()}",
                    },
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": "Productivity",
                }
            ],
        }
    return {
        "name": MARKETPLACE_NAME,
        "owner": {
            "name": MAINTAINER_NAME,
            "url": REPOSITORY_URL,
        },
        "description": "AI Agent Harness user skills for Codex and Claude Code projects.",
        "plugins": [
            {
                "name": PLUGIN_ID,
                "source": f"./{PLUGIN_ROOT_REL.as_posix()}",
                "displayName": PLUGIN_DISPLAY_NAME,
                "description": PLUGIN_DESCRIPTION,
                "version": PLUGIN_VERSION,
            }
        ],
    }


def build_capabilities(root: Path, runtime_allowlist: dict, markdown_flow: dict) -> dict:
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
            "physical_skills": 18,
            "physical_agents": 0,
            "skills_path": "./runtime/claude/skills",
            "runtime_agents": runtime_allowlist["claude_runtime_agents"],
            "aliases": runtime_allowlist["capability_aliases"],
            "canonical_humanize_skill": "humanize-korean",
        },
        "markdown_artifact_flow": {
            "producer_count": len(markdown_flow["producer_skills"]),
            "producers": [item["skill"] for item in markdown_flow["producer_skills"]],
            "handoff_target": "humanize-korean",
            "proposal_only": True,
        },
    })
    return value


def packaged_sources(root: Path) -> list[dict]:
    registry = load_json(root / "maintainer" / "upstreams" / "registry.json")
    logical_skills = set(load_json(root / "maintainer" / "plugin" / "CAPABILITIES.json")["logical_user_skills"])
    sources: list[dict] = []
    for source in registry.get("sources", []):
        if source.get("lifecycle") != "active" or source.get("integration_mode") not in PACKAGED_INTEGRATION_MODES:
            continue
        target_skills = set(source.get("target", {}).get("local_skills", []))
        if not target_skills & logical_skills:
            continue
        sources.append(source)
    return sorted(sources, key=lambda item: item["id"])


def notices(root: Path, plugin_root: Path, sources: list[dict]) -> None:
    license_template = (root / "maintainer" / "skills" / "harness-plugin-maintainer" / "templates" / "plugin-license.md").read_text(encoding="utf-8")
    write_text(plugin_root / "LICENSE", license_template)
    (plugin_root / "licenses").mkdir(parents=True, exist_ok=True)
    for source in sources:
        source_id = source["id"]
        provenance = source.get("provenance", {})
        required = ["license_spdx", "license_url", "license_sha256", "notice_path"]
        missing = [field for field in required if not provenance.get(field)]
        if missing:
            raise RuntimeError(f"{source_id}: packaged source provenance missing {missing}")
        notice_source = root / provenance["notice_path"]
        license_source = notice_source.parent / "LICENSE"
        if not license_source.is_file():
            raise RuntimeError(f"{source_id}: packaged source license missing: {license_source}")
        if not notice_source.is_file():
            raise RuntimeError(f"{source_id}: packaged source notice missing: {notice_source}")
        shutil.copyfile(license_source, plugin_root / "licenses" / f"{source_id}-LICENSE")
    shutil.copyfile(root / "THIRD_PARTY_NOTICES.md", plugin_root / "THIRD_PARTY_NOTICES.md")


def lock(root: Path, artifact_manifest: list[dict], sources: list[dict]) -> dict:
    upstream_lock = load_json(root / "maintainer" / "upstreams" / "lock.json")
    packaged = copy.deepcopy(upstream_lock)

    # Candidate relationships describe planned work, not shipped content. Keeping
    # their lock states out of the packaged lock stops an accepted-but-unbuilt
    # upstream from churning the archive hash of an already-built version.
    registry = load_json(root / "maintainer" / "upstreams" / "registry.json")
    candidate_ids = {
        source["id"]
        for source in registry.get("sources", [])
        if source.get("lifecycle") == "candidate" and source.get("id")
    }
    packaged["states"] = [
        state for state in packaged.get("states", []) if state.get("id") not in candidate_ids
    ]

    packaged_ids = {source["id"] for source in sources}
    matched: set[str] = set()
    for state in packaged.get("states", []):
        if state.get("id") in packaged_ids:
            matched.add(state["id"])
            state["packaged"] = {
                "plugin_id": PLUGIN_ID,
                "version": PLUGIN_VERSION,
                "packaged_at": "2026-07-29",
                "artifact_manifest_sha256": next(item["sha256"] for item in artifact_manifest if item["path"] == "CAPABILITIES.json"),
            }
    if matched != packaged_ids:
        raise RuntimeError(f"packaged sources missing lock state: {sorted(packaged_ids - matched)}")

    # Derive the packaged timestamp from the packaged states themselves. Copying
    # the source lock's document-level generated_at would rebuild the archive
    # whenever any unrelated relationship is touched.
    dates = [
        entry[field]
        for state in packaged["states"]
        for key in ("observed", "accepted", "embedded")
        if isinstance((entry := state.get(key)), dict)
        for field in ("checked_at", "accepted_at", "embedded_at")
        if entry.get(field)
    ]
    if dates:
        packaged["generated_at"] = max(dates)

    packaged["generated_by"] = GENERATED_BY
    packaged["released_state_preserved"] = True
    return packaged


def write_archive(plugin_root: Path) -> Path:
    archive = plugin_root.parent / f"{PLUGIN_ID}-{PLUGIN_VERSION}.zip"
    if archive.exists():
        archive.unlink()
    fixed_dt = (2026, 7, 29, 0, 0, 0)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        files = sorted(
            (path for path in plugin_root.rglob("*") if path.is_file()),
            key=lambda path: path.relative_to(plugin_root).as_posix(),
        )
        for path in files:
            info = zipfile.ZipInfo(str(path.relative_to(plugin_root)).replace("\\", "/"), fixed_dt)
            mode = 0o755 if path.suffix.lower() in EXECUTABLE_SUFFIXES else 0o644
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            info._compresslevel = 9
            zf.writestr(info, path.read_bytes())
    return archive


def normalize_text_payload(plugin_root: Path) -> None:
    for path in sorted(
        p
        for p in plugin_root.rglob("*")
        if p.is_file() and (p.suffix.lower() in TEXT_SUFFIXES or not p.suffix)
    ):
        try:
            original = path.read_bytes()
            text = original.decode("utf-8")
        except UnicodeDecodeError:
            continue
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized_bytes = normalized.encode("utf-8")
        if normalized_bytes != original:
            path.write_bytes(normalized_bytes)


def reset_plugin_output(plugin_root: Path, output_root: Path) -> None:
    resolved_root = output_root.resolve()
    resolved_plugin = plugin_root.resolve()
    try:
        resolved_plugin.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"refusing to reset plugin outside output root: {plugin_root}") from exc
    if resolved_plugin == resolved_root:
        raise RuntimeError(f"refusing to reset output root itself: {plugin_root}")
    if plugin_root.exists():
        shutil.rmtree(plugin_root)


def build(root: Path, output_root: Path | None = None) -> dict:
    target_root = output_root if output_root is not None else root
    plugin_root = target_root / PLUGIN_ROOT_REL

    # Read and validate inputs before deleting anything. Resetting first would
    # leave the repository without a plugin tree whenever an input is invalid.
    capabilities = load_json(root / "maintainer" / "plugin" / "CAPABILITIES.json")
    runtime_allowlist = load_json(root / "maintainer" / "plugin" / "runtime-allowlist.json")
    markdown_flow = load_json(root / "maintainer" / "inventory" / "markdown-artifact-flow.json")
    sources = packaged_sources(root)
    check_user_skill_inventory(root, capabilities)

    reset_plugin_output(plugin_root, target_root)
    plugin_root.mkdir(parents=True, exist_ok=True)

    copy_user_skills(root, plugin_root, capabilities)
    notices(root, plugin_root, sources)

    write_json(plugin_root / ".codex-plugin" / "plugin.json", manifest("codex"))
    write_json(plugin_root / ".claude-plugin" / "plugin.json", manifest("claude"))
    write_json(target_root / ROOT_CODEX_MARKETPLACE, marketplace("codex"))
    write_json(target_root / ROOT_CLAUDE_MARKETPLACE, marketplace("claude"))
    write_json(plugin_root / "CAPABILITIES.json", build_capabilities(root, runtime_allowlist, markdown_flow))
    normalize_text_payload(plugin_root)

    artifact_manifest = tree_manifest(plugin_root)
    write_json(plugin_root / "UPSTREAMS.lock.json", lock(root, artifact_manifest, sources))
    artifact_manifest = tree_manifest(plugin_root)
    write_json(plugin_root / "MANIFEST.sha256.json", {"generated_by": GENERATED_BY, "files": artifact_manifest})
    archive = write_archive(plugin_root)

    release = {
        "schema_version": "1.0.0",
        "generated_by": GENERATED_BY,
        "plugin_id": PLUGIN_ID,
        "version": PLUGIN_VERSION,
        "plugin_root": str(PLUGIN_ROOT_REL).replace("\\", "/"),
        "archive": str(archive.relative_to(target_root)).replace("\\", "/"),
        "archive_sha256": sha256_file(archive),
        "marketplaces": {
            "codex": str(ROOT_CODEX_MARKETPLACE).replace("\\", "/"),
            "claude": str(ROOT_CLAUDE_MARKETPLACE).replace("\\", "/"),
        },
        "packaged_upstreams": [source["id"] for source in sources],
        "logical_user_skills": 18,
        "codex_physical_skills": 18,
        "codex_physical_agents": 0,
        "claude_physical_skills": 18,
        "claude_physical_agents": 0,
        "markdown_producers": MARKDOWN_PRODUCERS,
        "released_state_preserved": True,
        "push_tag_release_created": False,
    }
    write_json(target_root / "maintainer" / "plugin" / "release.json", release)
    ensure_no_symlink(plugin_root)
    return release


def compare_tree(expected_root: Path, actual_root: Path) -> list[str]:
    expected = {item["path"]: item["sha256"] for item in tree_manifest(expected_root)}
    actual = {item["path"]: item["sha256"] for item in tree_manifest(actual_root)} if actual_root.is_dir() else {}
    messages: list[str] = []
    for path in sorted(expected.keys() - actual.keys()):
        messages.append(f"missing generated plugin file: {path}")
    for path in sorted(actual.keys() - expected.keys()):
        messages.append(f"unexpected generated plugin file: {path}")
    for path in sorted(expected.keys() & actual.keys()):
        if expected[path] != actual[path]:
            messages.append(f"changed generated plugin file: {path}")
    return messages


def compare_file(expected: Path, actual: Path, label: str) -> list[str]:
    if not actual.is_file():
        return [f"missing generated {label}: {actual}"]
    if expected.read_bytes() != actual.read_bytes():
        return [f"changed generated {label}: {actual}"]
    return []


def check(root: Path, canonical_root: Path | None = None) -> int:
    actual_root = canonical_root if canonical_root is not None else root
    messages: list[str] = []
    with tempfile.TemporaryDirectory(prefix="ai-agent-harness-build-check-") as tmp:
        expected_root = Path(tmp)
        release = build(root, output_root=expected_root)
        messages.extend(compare_tree(expected_root / PLUGIN_ROOT_REL, actual_root / PLUGIN_ROOT_REL))
        messages.extend(
            compare_file(
                expected_root / release["archive"],
                actual_root / release["archive"],
                "plugin archive",
            )
        )
        messages.extend(
            compare_file(
                expected_root / "maintainer" / "plugin" / "release.json",
                actual_root / "maintainer" / "plugin" / "release.json",
                "release metadata",
            )
        )
        for label, rel in [
            ("Codex marketplace", ROOT_CODEX_MARKETPLACE),
            ("Claude marketplace", ROOT_CLAUDE_MARKETPLACE),
        ]:
            messages.extend(compare_file(expected_root / rel, actual_root / rel, label))
    if messages:
        for message in messages:
            print(f"ERROR: {message}", file=sys.stderr)
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
