#!/usr/bin/env python3
"""Validate generated ai-agent-harness plugin."""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

from plugin_common import (
    GENERATED_BY,
    PLUGIN_ID,
    PLUGIN_ROOT_REL,
    PLUGIN_VERSION,
    iter_files,
    load_json,
    repo_root,
    sha256_file,
    tree_manifest,
)


FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLUGIN_DISPLAY_NAME = "AI Agent Harness"
MARKETPLACE_NAME = "ai-agent-harness"
ROOT_CODEX_MARKETPLACE = Path(".agents") / "plugins" / "marketplace.json"
ROOT_CLAUDE_MARKETPLACE = Path(".claude-plugin") / "marketplace.json"
PACKAGED_INTEGRATION_MODES = {"adapted", "vendored"}
TEXT_SUFFIXES = {".md", ".json", ".py", ".sh", ".template", ".html", ".txt", ".yml", ".yaml"}
CODEX_MANIFEST_FIELDS = {
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "keywords",
    "skills",
    "interface",
}
CLAUDE_MANIFEST_FIELDS = {
    "name",
    "displayName",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "keywords",
    "skills",
}
EXPLICIT_ONLY_SKILLS = {"commit", "git-scoped-account", "impl-verify"}
MODEL_ROUTABLE_SKILLS = {"multi-review", "pre-commit"}


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def dirs(path: Path) -> list[str]:
    if not path.is_dir():
        return []
    return sorted(item.name for item in path.iterdir() if item.is_dir())


def validate_manifest(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    codex = load_json(plugin_root / ".codex-plugin" / "plugin.json")
    claude = load_json(plugin_root / ".claude-plugin" / "plugin.json")
    for name, manifest in [("codex", codex), ("claude", claude)]:
        if manifest.get("name") != PLUGIN_ID or not KEBAB_CASE_RE.fullmatch(str(manifest.get("name", ""))):
            error(errors, f"{name} manifest name must be the kebab-case plugin identifier")
        if manifest.get("version") != PLUGIN_VERSION:
            error(errors, f"{name} manifest version mismatch")
        expected_fields = CODEX_MANIFEST_FIELDS if name == "codex" else CLAUDE_MANIFEST_FIELDS
        unknown = sorted(set(manifest) - expected_fields)
        if unknown:
            error(errors, f"{name} manifest contains unsupported fields: {unknown}")
        expected_skills = f"./runtime/{name}/skills/"
        if manifest.get("skills") != expected_skills:
            error(errors, f"{name} manifest skills path mismatch")
        else:
            resolved = (plugin_root / expected_skills[2:]).resolve()
            try:
                resolved.relative_to(plugin_root.resolve())
            except ValueError:
                error(errors, f"{name} manifest skills path escapes plugin root")
            if not resolved.is_dir():
                error(errors, f"{name} manifest skills directory missing")
        if name == "codex":
            interface = manifest.get("interface")
            if not isinstance(interface, dict) or interface.get("displayName") != PLUGIN_DISPLAY_NAME:
                error(errors, "codex manifest interface.displayName mismatch")
        elif manifest.get("displayName") != PLUGIN_DISPLAY_NAME:
            error(errors, "claude manifest displayName mismatch")
        if any(key in manifest for key in {"id", "generated_by", "im_not_ai_root"}):
            error(errors, f"{name} manifest contains legacy non-schema fields")


def validate_counts(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    codex_skills = dirs(plugin_root / "runtime" / "codex" / "skills")
    claude_skills = dirs(plugin_root / "runtime" / "claude" / "skills")
    claude_agents = sorted(path.stem for path in (plugin_root / "runtime" / "claude" / "agents").glob("*.md"))
    caps = load_json(plugin_root / "CAPABILITIES.json")
    allowlist = load_json(root / "maintainer" / "plugin" / "runtime-allowlist.json")

    if len(codex_skills) != 18:
        error(errors, f"Codex physical skills must be 18, got {len(codex_skills)}")
    if len(claude_skills) != 18:
        error(errors, f"Claude physical skills must be 18, got {len(claude_skills)}")
    if claude_agents != sorted(allowlist["claude_runtime_agents"]):
        error(errors, "Claude agent allowlist mismatch")
    if claude_agents:
        error(errors, f"Claude runtime agents must be empty, got {claude_agents}")
    for legacy in ["humanize", "humanize-redo"]:
        if legacy in claude_skills:
            error(errors, f"legacy Claude alias must not be packaged: {legacy}")
    if (plugin_root / "runtime" / "claude" / "im-not-ai-root").exists():
        error(errors, "legacy Claude im-not-ai-root must not be packaged")
    if any(name in codex_skills or name in claude_skills for name in ["custom-skill-design", "harness-plugin-maintainer", "skill-portfolio-maintainer"]):
        error(errors, "maintainer skill leaked into runtime")
    if caps["claude"].get("aliases") != {} or allowlist.get("capability_aliases") != {}:
        error(errors, "Claude compatibility aliases must be empty")
    if caps["claude"].get("canonical_humanize_skill") != "humanize-korean":
        error(errors, "canonical Claude humanize skill mismatch")
    if caps["claude"].get("physical_skills") != 18 or caps["claude"].get("physical_agents") != 0:
        error(errors, "Claude capability counts must be 18 skills and 0 agents")
    producers = caps["markdown_artifact_flow"]["producers"]
    if producers != ["harness-setup", "harness-bootstrap", "context-doc", "design-doc", "design-prototype-docs", "impl-doc", "impl-fe-be-doc"]:
        error(errors, "Markdown producer inventory mismatch")


def validate_skill_files(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    for path in list((plugin_root / "runtime" / "codex" / "skills").glob("*/SKILL.md")) + list((plugin_root / "runtime" / "claude" / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        frontmatter_match = FRONTMATTER_RE.match(text)
        if not frontmatter_match:
            error(errors, f"missing SKILL frontmatter: {path}")
            continue
        frontmatter = frontmatter_match.group(0)
        if re.search(r"(?m)^model\s*:", text):
            error(errors, f"model field forbidden: {path}")
        if "agent: fork" in text:
            error(errors, f"agent: fork forbidden: {path}")
        allowed_line = next(
            (
                line.split(":", 1)[1]
                for line in frontmatter.splitlines()
                if line.startswith("allowed-tools:")
            ),
            "",
        )
        allowed_tools = {
            item.strip().strip("[]\"'")
            for item in allowed_line.split(",")
            if item.strip()
        }
        if "Bash" in allowed_tools:
            error(errors, f"unrestricted Bash pre-approval forbidden: {path}")
        if "Task" in allowed_tools:
            error(errors, f"legacy Task tool forbidden: {path}")

        skill_name = path.parent.name
        explicit_only = bool(
            re.search(
                r"(?m)^disable-model-invocation\s*:\s*true\s*$",
                frontmatter,
            )
        )
        if skill_name in EXPLICIT_ONLY_SKILLS:
            if not explicit_only:
                error(errors, f"side-effect skill must be explicit-only: {path}")
            if f"${skill_name}" not in text:
                error(errors, f"Codex direct invocation example missing: {path}")
            if f"/{PLUGIN_ID}:{skill_name}" not in text:
                error(errors, f"Claude direct invocation example missing: {path}")
        if skill_name in MODEL_ROUTABLE_SKILLS and explicit_only:
            error(errors, f"review/check skill must remain model-routable: {path}")
        if skill_name == "pre-commit" and "bash scripts/scan.sh" in text:
            error(errors, f"pre-commit script path must be bundle-relative: {path}")


def validate_source_permission_policy(root: Path, errors: list[str]) -> None:
    for base in (root / "skills", root / "maintainer" / "skills"):
        for path in sorted(base.glob("*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            frontmatter_match = FRONTMATTER_RE.match(text)
            if not frontmatter_match:
                error(errors, f"canonical SKILL frontmatter missing: {path}")
                continue
            allowed_line = next(
                (
                    line.split(":", 1)[1]
                    for line in frontmatter_match.group(0).splitlines()
                    if line.startswith("allowed-tools:")
                ),
                "",
            )
            allowed_tools = {
                item.strip().strip("[]\"'")
                for item in allowed_line.split(",")
                if item.strip()
            }
            if "Bash" in allowed_tools:
                error(errors, f"canonical skill pre-approves unrestricted Bash: {path}")
            if "Task" in allowed_tools:
                error(errors, f"canonical skill uses legacy Task tool: {path}")

    alias_template = (
        root
        / "maintainer"
        / "skills"
        / "harness-plugin-maintainer"
        / "templates"
        / "claude-alias-skill.md"
    )
    if re.search(
        r"(?m)^allowed-tools\s*:.*\bBash\b",
        alias_template.read_text(encoding="utf-8"),
    ):
        error(errors, "Claude alias template pre-approves unrestricted Bash")

    manager_skill = (
        root
        / "maintainer"
        / "skills"
        / "harness-plugin-maintainer"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    if "disable-model-invocation: true" not in manager_skill:
        error(errors, "plugin build manager must be explicit-only")
    for invocation in ("$harness-plugin-maintainer", "/harness-plugin-maintainer"):
        if invocation not in manager_skill:
            error(errors, f"plugin build manager invocation example missing: {invocation}")


def validate_manual_surface_contract(root: Path, errors: list[str]) -> None:
    template = (
        root / "maintainer" / "plugin" / "manual-surface-test-template.md"
    ).read_text(encoding="utf-8")
    required_fragments = [
        "## Codex CLI 예시",
        "## Codex 앱 예시",
        "## Claude Code CLI 예시",
        "## Claude Desktop Code 예시",
        "$harness-setup",
        "$humanize-korean",
        "/ai-agent-harness:harness-setup",
        "/ai-agent-harness:humanize-korean",
        "### A. 최초 설정",
        "### B. 갱신과 사용자 확장 보존",
        "### C. 새 session 중복 handoff 방지",
        "### D. 중단 시 원본 보존",
        ".agents/skills",
        ".claude/skills",
        "maintainer/plugin/manual-evidence/YYYYMMDD/{surface}.md",
        "자동 설치 smoke와 실제 모델 호출은 별도 증적",
        "POSIX shell 확인 예",
        "PowerShell 확인 예",
    ]
    for fragment in required_fragments:
        if fragment not in template:
            error(errors, f"manual surface test contract missing: {fragment}")
    if template.count("A·B·C·D") < 4:
        error(errors, "all four direct surfaces must execute scenarios A-D")


def validate_notices(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    required = [
        "LICENSE",
        "THIRD_PARTY_NOTICES.md",
        "UPSTREAMS.lock.json",
        "CAPABILITIES.json",
        "MANIFEST.sha256.json",
    ]
    for item in required:
        if not (plugin_root / item).exists():
            error(errors, f"missing plugin metadata: {item}")
    registry = load_json(root / "maintainer" / "upstreams" / "registry.json")
    logical = set(load_json(root / "maintainer" / "plugin" / "CAPABILITIES.json")["logical_user_skills"])
    packaged_sources = sorted(
        (
            source
            for source in registry.get("sources", [])
            if source.get("lifecycle") == "active"
            and source.get("integration_mode") in PACKAGED_INTEGRATION_MODES
            and set(source.get("target", {}).get("local_skills", [])) & logical
        ),
        key=lambda item: item["id"],
    )
    lock = load_json(plugin_root / "UPSTREAMS.lock.json")
    notices = (plugin_root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    for source in packaged_sources:
        source_id = source["id"]
        provenance = source.get("provenance", {})
        license_path = plugin_root / "licenses" / f"{source_id}-LICENSE"
        if not license_path.is_file():
            error(errors, f"{source_id}: packaged license missing")
        elif provenance.get("license_sha256") and sha256_file(license_path) != provenance["license_sha256"]:
            error(errors, f"{source_id}: packaged license hash mismatch")
        notice_path = root / str(provenance.get("notice_path", ""))
        if not provenance.get("notice_path") or not notice_path.is_file():
            error(errors, f"{source_id}: source notice missing")
        if source_id not in notices:
            error(errors, f"{source_id}: THIRD_PARTY_NOTICES entry missing")
        state = next((item for item in lock.get("states", []) if item.get("id") == source_id), None)
        if not state or not state.get("packaged"):
            error(errors, f"{source_id}: packaged lock state missing")
        elif state["packaged"].get("plugin_id") != PLUGIN_ID or state["packaged"].get("version") != PLUGIN_VERSION:
            error(errors, f"{source_id}: packaged lock plugin/version mismatch")
    release = load_json(root / "maintainer" / "plugin" / "release.json")
    if release.get("version") != PLUGIN_VERSION or release.get("plugin_id") != PLUGIN_ID:
        error(errors, "release metadata version/plugin mismatch")
    if release.get("push_tag_release_created") is not False:
        error(errors, "release metadata must not mark push/tag/release as created")
    if release.get("packaged_upstreams") != [source["id"] for source in packaged_sources]:
        error(errors, "release packaged upstream inventory mismatch")


def validate_marketplace(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    codex = load_json(root / ROOT_CODEX_MARKETPLACE)
    claude = load_json(root / ROOT_CLAUDE_MARKETPLACE)
    if (plugin_root / ".agents" / "plugins" / "marketplace.json").exists():
        error(errors, "Codex marketplace must be repo-root, not plugin-internal")
    if (plugin_root / ".claude-plugin" / "marketplace.json").exists():
        error(errors, "Claude marketplace must be repo-root, not plugin-internal")
    for name, market in [("codex", codex), ("claude", claude)]:
        if market.get("name") != MARKETPLACE_NAME or not KEBAB_CASE_RE.fullmatch(str(market.get("name", ""))):
            error(errors, f"{name} marketplace name must be kebab-case")
        plugins = market.get("plugins", [])
        if len(plugins) != 1 or plugins[0].get("name") != PLUGIN_ID:
            error(errors, f"{name} marketplace plugin entry mismatch")
            continue
        entry = plugins[0]
        source = entry.get("source")
        if name == "codex":
            if set(market) != {"name", "interface", "plugins"}:
                error(errors, "codex marketplace contains unsupported top-level fields")
            if source != {"source": "local", "path": f"./{PLUGIN_ROOT_REL.as_posix()}"}:
                error(errors, "codex marketplace local source mismatch")
            if entry.get("policy") != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
                error(errors, "codex marketplace policy mismatch")
            if not entry.get("category"):
                error(errors, "codex marketplace category missing")
            source_path = source.get("path") if isinstance(source, dict) else None
        else:
            if set(market) != {"name", "owner", "description", "plugins"}:
                error(errors, "claude marketplace contains unsupported top-level fields")
            owner = market.get("owner")
            if not isinstance(owner, dict) or not owner.get("name"):
                error(errors, "claude marketplace owner.name missing")
            if not market.get("description"):
                error(errors, "claude marketplace description missing")
            if source != f"./{PLUGIN_ROOT_REL.as_posix()}":
                error(errors, "claude marketplace local source mismatch")
            if entry.get("displayName") != PLUGIN_DISPLAY_NAME:
                error(errors, "claude marketplace displayName mismatch")
            source_path = source if isinstance(source, str) else None
        if source_path:
            resolved = (root / source_path[2:]).resolve() if source_path.startswith("./") else None
            if resolved != plugin_root.resolve():
                error(errors, f"{name} marketplace source does not resolve to plugin root")


def validate_payload_integrity(root: Path, errors: list[str]) -> None:
    plugin_root = root / PLUGIN_ROOT_REL
    manifest_path = plugin_root / "MANIFEST.sha256.json"
    manifest = load_json(manifest_path)
    expected_manifest = [
        item for item in tree_manifest(plugin_root) if item["path"] != "MANIFEST.sha256.json"
    ]
    if manifest.get("generated_by") != GENERATED_BY or manifest.get("files") != expected_manifest:
        error(errors, "MANIFEST.sha256.json does not match plugin payload")

    for path in iter_files(plugin_root):
        if path.suffix.lower() not in TEXT_SUFFIXES and path.suffix:
            continue
        try:
            payload = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        if "\r" in payload:
            error(errors, f"text payload must use LF line endings: {path.relative_to(plugin_root)}")

    release = load_json(root / "maintainer" / "plugin" / "release.json")
    archive = root / release.get("archive", "")
    if not archive.is_file():
        error(errors, "plugin archive missing")
        return
    if sha256_file(archive) != release.get("archive_sha256"):
        error(errors, "plugin archive hash does not match release metadata")
    expected_files = {
        str(path.relative_to(plugin_root)).replace("\\", "/"): path
        for path in iter_files(plugin_root)
    }
    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        names = [info.filename for info in infos]
        if names != sorted(expected_files):
            error(errors, "plugin archive file inventory/order mismatch")
        for info in infos:
            source = expected_files.get(info.filename)
            if source is None:
                continue
            if zf.read(info) != source.read_bytes():
                error(errors, f"plugin archive payload mismatch: {info.filename}")
            expected_mode = 0o755 if Path(info.filename).suffix.lower() == ".sh" else 0o644
            actual_mode = (info.external_attr >> 16) & 0o777
            if info.create_system != 3 or actual_mode != expected_mode:
                error(errors, f"plugin archive mode mismatch: {info.filename} ({oct(actual_mode)})")


def main() -> int:
    root = repo_root()
    errors: list[str] = []
    validate_source_permission_policy(root, errors)
    validate_manual_surface_contract(root, errors)
    plugin_root = root / PLUGIN_ROOT_REL
    if not plugin_root.exists():
        error(errors, "plugin root missing; run build_plugin.py first")
    else:
        validate_manifest(root, errors)
        validate_counts(root, errors)
        validate_skill_files(root, errors)
        validate_notices(root, errors)
        validate_marketplace(root, errors)
        validate_payload_integrity(root, errors)
    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        return 1
    print("plugin validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
