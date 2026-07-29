#!/usr/bin/env python3
"""Verify Phase 7 install/update surfaces and write release gate evidence.

This script does not mutate user plugin installations. It records which CLI/app
surfaces are available in the current host and validates local release-candidate
behavior that can be checked without external marketplace state.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from plugin_common import PLUGIN_ID, PLUGIN_ROOT_REL, PLUGIN_VERSION, load_json, repo_root, sha256_file, write_json, write_text


SURFACES = [
    "codex-cli",
    "codex-desktop-app",
    "claude-code-cli",
    "claude-desktop-code",
]

DEFAULT_GENERATED_AT = "2026-07-29T00:00:00+00:00"


def generated_at() -> str:
    return os.environ.get("HARNESS_VERIFY_GENERATED_AT", DEFAULT_GENERATED_AT)


def run_probe(command: list[str]) -> dict:
    exe = shutil.which(command[0])
    if not exe:
        return {
            "command": command,
            "available": False,
            "status": "missing",
            "exit_code": None,
            "stdout_excerpt": "",
            "stderr_excerpt": "",
        }
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        completed = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=20,
            env=env,
        )
        return {
            "command": command,
            "available": True,
            "status": "ok" if completed.returncode == 0 else "failed",
            "exit_code": completed.returncode,
            "stdout_excerpt": completed.stdout[:1000],
            "stderr_excerpt": completed.stderr[:1000],
        }
    except Exception as exc:  # noqa: BLE001 - probe report must preserve host failure
        return {
            "command": command,
            "available": True,
            "status": "failed-to-start",
            "exit_code": None,
            "stdout_excerpt": "",
            "stderr_excerpt": str(exc)[:1000],
        }


def validate_plugin_metadata(root: Path) -> dict:
    plugin_root = root / PLUGIN_ROOT_REL
    codex = load_json(plugin_root / ".codex-plugin" / "plugin.json")
    claude = load_json(plugin_root / ".claude-plugin" / "plugin.json")
    caps = load_json(plugin_root / "CAPABILITIES.json")
    lock = load_json(plugin_root / "UPSTREAMS.lock.json")
    release = load_json(root / "maintainer" / "plugin" / "release.json")
    archive = root / release["archive"]
    im_not_ai = next(item for item in lock["states"] if item["id"] == "im-not-ai")
    return {
        "plugin_root": str(PLUGIN_ROOT_REL).replace("\\", "/"),
        "plugin_id": codex["id"],
        "version": codex["version"],
        "codex_manifest_matches_claude": codex["id"] == claude["id"] and codex["version"] == claude["version"],
        "archive": release["archive"],
        "archive_sha256": sha256_file(archive),
        "archive_sha256_matches_release": sha256_file(archive) == release["archive_sha256"],
        "logical_user_skills": len(caps["logical_user_skills"]),
        "codex_physical_skills": caps["codex"]["physical_skills"],
        "claude_physical_skills": caps["claude"]["physical_skills"],
        "claude_physical_agents": caps["claude"]["physical_agents"],
        "markdown_producer_count": caps["markdown_artifact_flow"]["producer_count"],
        "humanize_aliases": caps["claude"]["aliases"],
        "im_not_ai_packaged": bool(im_not_ai.get("packaged")),
        "released_state_preserved": im_not_ai.get("released") is None,
    }


def verify_humanize_proposal(root: Path) -> dict:
    script = root / "plugins" / PLUGIN_ID / "runtime" / "codex" / "skills" / "humanize-korean" / "scripts" / "humanize_korean.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    with tempfile.TemporaryDirectory() as tmp:
        sample = Path(tmp) / "sample.md"
        original = "결론적으로, SFR-021은 2026-07-29에 .docs/api/SFR-021.md를 통해 관리될 수 있습니다."
        sample.write_text(original, encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(script), "--file", str(sample), "--profile", "document-refinement"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=True,
            env=env,
        )
        result = json.loads(completed.stdout)
        return {
            "proposal_only": result["proposal_only"],
            "file_unchanged": sample.read_text(encoding="utf-8") == original,
            "protected_tokens_preserved": all(token in result["refined_text"] for token in ["SFR-021", "2026-07-29", ".docs/api/SFR-021.md"]),
            "change_rate": result["change_rate"],
        }


def legacy_migration_readonly_fixture() -> dict:
    return {
        "mode": "read-only-inventory",
        "fixture_cases": [
            {
                "case": "known-old-harness-copy",
                "active_path": ".agents/skills/harness-setup",
                "classification": "known legacy local skill copy",
                "default_action": "report-only",
                "destructive_action_requires": "explicit backup/remove approval",
            },
            {
                "case": "user-modified-old-copy",
                "active_path": ".claude/skills/harness-setup",
                "classification": "modified legacy copy",
                "default_action": "preserve and report hash",
                "destructive_action_requires": "explicit backup/remove approval",
            },
            {
                "case": "unknown-custom-skill",
                "active_path": ".agents/skills/custom-domain-skill",
                "classification": "custom skill",
                "default_action": "preserve",
                "destructive_action_requires": "not eligible for automatic removal",
            },
        ],
        "backup_target": ".docs/archive/legacy-agent-skills/{timestamp}/",
        "rollback": "restore archived active root after user approval",
    }


def write_release_checklist(root: Path, evidence: dict) -> None:
    checklist = f"""# Plugin Release Checklist

Generated at: {evidence["generated_at"]}

## Release candidate

- Plugin ID: `{evidence["plugin"]["plugin_id"]}`
- Version: `{evidence["plugin"]["version"]}`
- Archive: `{evidence["plugin"]["archive"]}`
- Archive SHA-256: `{evidence["plugin"]["archive_sha256"]}`
- Codex physical skills: {evidence["plugin"]["codex_physical_skills"]}
- Claude physical skills: {evidence["plugin"]["claude_physical_skills"]}
- Claude physical agents: {evidence["plugin"]["claude_physical_agents"]}
- Markdown producer handoff count: {evidence["plugin"]["markdown_producer_count"]}

## Automated local checks

| Check | Result |
|---|---|
| Manifest ID/version match | {evidence["plugin"]["codex_manifest_matches_claude"]} |
| Archive checksum matches release metadata | {evidence["plugin"]["archive_sha256_matches_release"]} |
| `im-not-ai` packaged lock exists | {evidence["plugin"]["im_not_ai_packaged"]} |
| Released state preserved | {evidence["plugin"]["released_state_preserved"]} |
| `humanize-korean` proposal-only | {evidence["humanize_korean"]["proposal_only"]} |
| `humanize-korean` leaves original file unchanged | {evidence["humanize_korean"]["file_unchanged"]} |
| Protected tokens preserved | {evidence["humanize_korean"]["protected_tokens_preserved"]} |

## Surface evidence

| Surface | Status | Evidence |
|---|---|---|
| Codex CLI | {evidence["surfaces"]["codex-cli"]["status"]} | `{evidence["surfaces"]["codex-cli"]["summary"]}` |
| Codex Desktop/App | {evidence["surfaces"]["codex-desktop-app"]["status"]} | `{evidence["surfaces"]["codex-desktop-app"]["summary"]}` |
| Claude Code CLI | {evidence["surfaces"]["claude-code-cli"]["status"]} | `{evidence["surfaces"]["claude-code-cli"]["summary"]}` |
| Claude Desktop Code | {evidence["surfaces"]["claude-desktop-code"]["status"]} | `{evidence["surfaces"]["claude-desktop-code"]["summary"]}` |

## Release gate

Status: **not release-ready**

Reason: Phase 7 requires evidence from four core surfaces: Codex CLI, Codex app, Claude Code CLI, and Claude Desktop Code. This host could not execute Codex CLI because WindowsApps denied process start, and Claude CLI is not installed. Desktop/app installation and update checks require interactive app surfaces.

## Required before release-ready

- Codex CLI: marketplace add/list/upgrade/remove, plugin add/list/remove, install vN, verify `harness-setup` and `humanize-korean`, update to vN+1 or reinstall stale cache.
- Codex app: install from Git-backed marketplace, restart/new task, verify marker/version, update to vN+1.
- Claude Code CLI: marketplace add/update, plugin install/list/update/uninstall, `/reload-plugins`, verify `harness-setup` and `humanize-korean`.
- Claude Desktop Code: local and SSH host cache/version verification, app restart/new session, unsupported cloud/WSL path documented.
- Legacy migration: run read-only inventory, backup/remove only with explicit approval, verify plugin single discovery.
"""
    write_text(root / "maintainer" / "plugin" / "release-checklist.md", checklist)


def main() -> int:
    root = repo_root()
    codex_help = run_probe(["codex", "--help"])
    codex_plugin = run_probe(["codex", "plugin", "--help"])
    claude_help = run_probe(["claude", "--help"])
    evidence = {
        "schema_version": "1.0.0",
        "generated_at": generated_at(),
        "plugin": validate_plugin_metadata(root),
        "humanize_korean": verify_humanize_proposal(root),
        "legacy_migration": legacy_migration_readonly_fixture(),
        "cli_probes": {
            "codex_help": codex_help,
            "codex_plugin_help": codex_plugin,
            "claude_help": claude_help,
        },
        "surfaces": {
            "codex-cli": {
                "status": "blocked" if codex_help["status"] != "ok" else "needs-install-smoke",
                "summary": codex_help["stderr_excerpt"] or codex_help["stdout_excerpt"] or codex_help["status"],
            },
            "codex-desktop-app": {
                "status": "manual-required",
                "summary": "Interactive Plugins UI install/update requires app surface and cannot be completed from this shell.",
            },
            "claude-code-cli": {
                "status": "blocked" if claude_help["status"] != "ok" else "needs-install-smoke",
                "summary": claude_help["stderr_excerpt"] or claude_help["stdout_excerpt"] or claude_help["status"],
            },
            "claude-desktop-code": {
                "status": "manual-required",
                "summary": "Desktop Code local/SSH cache verification requires Claude Desktop app surface.",
            },
        },
        "release_gate": {
            "status": "not-release-ready",
            "missing_required_surfaces": SURFACES,
            "push_tag_release_created": False,
        },
    }
    write_json(root / "maintainer" / "plugin" / "install-verification.json", evidence)
    write_json(root / "maintainer" / "plugin" / "legacy-migration-fixture.json", evidence["legacy_migration"])
    write_release_checklist(root, evidence)
    print(json.dumps(evidence["release_gate"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
