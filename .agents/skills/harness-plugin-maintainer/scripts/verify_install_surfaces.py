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
CLI_SMOKE_REL = Path("maintainer/plugin/cli-smoke.json")

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
    source_lock = load_json(root / "maintainer" / "upstreams" / "lock.json")
    release = load_json(root / "maintainer" / "plugin" / "release.json")
    archive = root / release["archive"]
    packaged_ids = release.get("packaged_upstreams", [])
    packaged_states = {item["id"]: item for item in lock["states"] if item["id"] in packaged_ids}
    source_states = {item["id"]: item for item in source_lock["states"] if item["id"] in packaged_ids}
    return {
        "plugin_root": str(PLUGIN_ROOT_REL).replace("\\", "/"),
        "plugin_id": codex["name"],
        "version": codex["version"],
        "codex_manifest_matches_claude": codex["name"] == claude["name"] and codex["version"] == claude["version"],
        "archive": release["archive"],
        "archive_sha256": sha256_file(archive),
        "archive_sha256_matches_release": sha256_file(archive) == release["archive_sha256"],
        "logical_user_skills": len(caps["logical_user_skills"]),
        "codex_physical_skills": caps["codex"]["physical_skills"],
        "codex_physical_agents": caps["codex"]["physical_agents"],
        "claude_physical_skills": caps["claude"]["physical_skills"],
        "claude_physical_agents": caps["claude"]["physical_agents"],
        "markdown_producer_count": caps["markdown_artifact_flow"]["producer_count"],
        "humanize_aliases": caps["claude"]["aliases"],
        "packaged_upstreams": packaged_ids,
        "packaged_upstream_closure": sorted(packaged_states) == sorted(packaged_ids)
        and all(packaged_states[source_id].get("packaged") for source_id in packaged_ids),
        "released_state_preserved": release.get("released_state_preserved") is True
        and all(
            packaged_states[source_id].get("released") == source_states[source_id].get("released")
            for source_id in packaged_ids
            if source_id in packaged_states and source_id in source_states
        ),
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


def load_cli_smoke(root: Path) -> dict:
    path = root / CLI_SMOKE_REL
    if not path.is_file():
        return {
            "status": "missing",
            "platforms": {},
            "summary": f"missing {CLI_SMOKE_REL.as_posix()}",
        }
    evidence = load_json(path)
    platforms = evidence.get("platforms", {})
    required = {"codex", "claude"}
    passed = (
        evidence.get("status") == "passed"
        and required.issubset(platforms)
        and all(platforms[name].get("status") == "passed" for name in required)
    )
    return {
        **evidence,
        "status": "passed" if passed else "failed",
        "summary": (
            "isolated marketplace add/install/list/uninstall/remove passed"
            if passed
            else "CLI smoke evidence is incomplete or failed"
        ),
    }


def write_release_checklist(root: Path, evidence: dict) -> None:
    cli_verified = all(
        evidence["surfaces"][surface]["status"] == "verified"
        for surface in ("codex-cli", "claude-code-cli")
    )
    if cli_verified:
        gate_reason = (
            "isolated Codex and Claude Code CLI installation smokes passed. Codex "
            "Desktop/App and Claude Desktop Code installation, restart, and new-session "
            "discovery still require interactive manual evidence."
        )
        completed_cli = (
            "- Codex CLI: marketplace add/list/remove, plugin add/list/remove, installed "
            "cache 18 skills / 0 agents, `harness-setup` and `humanize-korean`.\n"
            "- Claude Code CLI: strict plugin/marketplace validation, marketplace "
            "add/list/remove, plugin install/list/uninstall, installed cache 18 skills / "
            "0 agents."
        )
        pending_cli = ""
    else:
        gate_reason = (
            "isolated CLI installation evidence is incomplete, and both interactive app "
            "surfaces still require manual evidence."
        )
        completed_cli = "- CLI install smoke: incomplete."
        pending_cli = (
            "- Codex and Claude Code CLI: run `scripts/smoke_cli_install.py` with the "
            "official CLIs and retain passing evidence.\n"
        )
    checklist = f"""# Plugin Release Checklist

Generated at: {evidence["generated_at"]}

## Release candidate

- Plugin ID: `{evidence["plugin"]["plugin_id"]}`
- Version: `{evidence["plugin"]["version"]}`
- Archive: `{evidence["plugin"]["archive"]}`
- Archive SHA-256: `{evidence["plugin"]["archive_sha256"]}`
- Codex physical skills: {evidence["plugin"]["codex_physical_skills"]}
- Codex physical agents: {evidence["plugin"]["codex_physical_agents"]}
- Claude physical skills: {evidence["plugin"]["claude_physical_skills"]}
- Claude physical agents: {evidence["plugin"]["claude_physical_agents"]}
- Markdown producer handoff count: {evidence["plugin"]["markdown_producer_count"]}

## Automated local checks

| Check | Result |
|---|---|
| Manifest name/version match | {evidence["plugin"]["codex_manifest_matches_claude"]} |
| Archive checksum matches release metadata | {evidence["plugin"]["archive_sha256_matches_release"]} |
| Packaged adapted/vendored NOTICE-license-lock closure | {evidence["plugin"]["packaged_upstream_closure"]} |
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

Reason: {gate_reason}

## Completed automated install checks

{completed_cli}

## Required before release-ready

{pending_cli}- Codex app: install from Git-backed marketplace, restart/new task, verify marker/version, update to vN+1.
- Claude Desktop Code: local and SSH host cache/version verification, app restart/new session, unsupported cloud/WSL path documented.
- Legacy migration: run read-only inventory, backup/remove only with explicit approval, verify plugin single discovery.
"""
    write_text(root / "maintainer" / "plugin" / "release-checklist.md", checklist)


def main() -> int:
    root = repo_root()
    codex_help = run_probe(["codex", "--help"])
    codex_plugin = run_probe(["codex", "plugin", "--help"])
    claude_help = run_probe(["claude", "--help"])
    cli_smoke = load_cli_smoke(root)
    cli_smoke_passed = cli_smoke["status"] == "passed"
    surfaces = {
        "codex-cli": {
            "status": "verified" if cli_smoke_passed else "blocked",
            "summary": (
                cli_smoke["summary"]
                if cli_smoke_passed
                else codex_help["stderr_excerpt"]
                or codex_help["stdout_excerpt"]
                or cli_smoke["summary"]
            ),
        },
        "codex-desktop-app": {
            "status": "manual-required",
            "summary": "Interactive Plugins UI install/update requires app surface and cannot be completed from this shell.",
        },
        "claude-code-cli": {
            "status": "verified" if cli_smoke_passed else "blocked",
            "summary": (
                cli_smoke["summary"]
                if cli_smoke_passed
                else claude_help["stderr_excerpt"]
                or claude_help["stdout_excerpt"]
                or cli_smoke["summary"]
            ),
        },
        "claude-desktop-code": {
            "status": "manual-required",
            "summary": "Desktop Code local/SSH cache verification requires Claude Desktop app surface.",
        },
    }
    missing_surfaces = [
        name for name, surface in surfaces.items() if surface["status"] != "verified"
    ]
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
        "cli_smoke": cli_smoke,
        "surfaces": surfaces,
        "release_gate": {
            "status": "not-release-ready",
            "missing_required_surfaces": missing_surfaces,
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
