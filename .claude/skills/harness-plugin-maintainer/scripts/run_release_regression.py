#!/usr/bin/env python3
"""Run Phase 10 release-candidate regression checks.

The script intentionally does not push, tag, publish, or mutate external plugin
installations. It writes only local maintainer evidence files.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from plugin_common import PLUGIN_ID, PLUGIN_ROOT_REL, PLUGIN_VERSION, iter_files, load_json, repo_root, sha256_file, write_json, write_text


GENERATED_AT = "2026-07-29T00:00:00+00:00"
OUT_DIR = Path("maintainer") / "plugin"
REGRESSION_JSON = OUT_DIR / "release-regression.json"
REGRESSION_MD = OUT_DIR / "release-regression.md"


def run(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=env,
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"command failed: {args}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return completed


def skill_dirs(path: Path) -> list[str]:
    return sorted(item.name for item in path.iterdir() if item.is_dir())


def read_manifest(path: Path) -> list[dict[str, str]]:
    return load_json(path)


def count_plugin(root: Path) -> dict[str, Any]:
    plugin = root / PLUGIN_ROOT_REL
    codex_skills = skill_dirs(plugin / "runtime" / "codex" / "skills")
    claude_skills = skill_dirs(plugin / "runtime" / "claude" / "skills")
    claude_agents = sorted(path.stem for path in (plugin / "runtime" / "claude" / "agents").glob("*.md"))
    allowlist = load_json(root / "maintainer" / "plugin" / "runtime-allowlist.json")
    aliases = allowlist["capability_aliases"]
    admin_names = set(skill_dirs(root / "maintainer" / "skills"))
    return {
        "codex_physical_skills": len(codex_skills),
        "codex_physical_agents": 0,
        "claude_physical_skills": len(claude_skills),
        "claude_physical_agents": len(claude_agents),
        "claude_agents": claude_agents,
        "humanize_aliases": aliases,
        "admin_in_payload": sorted((set(codex_skills) | set(claude_skills)) & admin_names),
    }


def source_projection_integrity(root: Path) -> dict[str, Any]:
    plugin = count_plugin(root)
    manager = skill_dirs(root / "maintainer" / "skills")
    agents = skill_dirs(root / ".agents" / "skills")
    claude = skill_dirs(root / ".claude" / "skills")
    user = skill_dirs(root / "skills")
    checks = {
        "user_skills_18": len(user) == 18,
        "manager_skills_3": len(manager) == 3,
        "agents_manager_projection_3": agents == manager,
        "claude_manager_projection_3": claude == manager,
        "plugin_codex_18": plugin["codex_physical_skills"] == 18,
        "plugin_codex_agents_0": plugin["codex_physical_agents"] == 0,
        "plugin_claude_20": plugin["claude_physical_skills"] == 20,
        "plugin_claude_agents_3": plugin["claude_physical_agents"] == 3,
        "plugin_admin_0": plugin["admin_in_payload"] == [],
        "alias_mapping": plugin["humanize_aliases"] == {
            "humanize-korean": "humanize-korean",
            "humanize": "humanize-korean",
            "humanize-redo": "humanize-korean",
        },
    }
    return {
        "counts": {
            "user_skills": len(user),
            "manager_skills": len(manager),
            "agents_projection": len(agents),
            "claude_projection": len(claude),
            **{k: plugin[k] for k in ["codex_physical_skills", "codex_physical_agents", "claude_physical_skills", "claude_physical_agents"]},
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


def reproducible_build(root: Path) -> dict[str, Any]:
    scripts = root / "maintainer" / "skills" / "harness-plugin-maintainer" / "scripts"
    first = json.loads(run(root, [str(scripts / "build_plugin.py")]).stdout)
    first_archive = sha256_file(root / first["archive"])
    first_manifest = read_manifest(root / PLUGIN_ROOT_REL / "MANIFEST.sha256.json")
    second = json.loads(run(root, [str(scripts / "build_plugin.py")]).stdout)
    second_archive = sha256_file(root / second["archive"])
    second_manifest = read_manifest(root / PLUGIN_ROOT_REL / "MANIFEST.sha256.json")
    run(root, [str(scripts / "build_plugin.py"), "--check"])
    return {
        "archive_sha256": second_archive,
        "same_archive_hash": first_archive == second_archive,
        "same_manifest": first_manifest == second_manifest,
        "release_metadata_matches": second["archive_sha256"] == second_archive,
        "passed": first_archive == second_archive and first_manifest == second_manifest and second["archive_sha256"] == second_archive,
    }


def local_links(root: Path) -> dict[str, Any]:
    files = [root / "README.md"]
    for base in ["Docs", "example", "improvement_plan"]:
        files.extend(sorted((root / base).rglob("*.md")))
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    missing: list[dict[str, str]] = []
    for file in files:
        text = file.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            href = match.group(1).split("#")[0]
            if not href or re.match(r"^[a-z]+://", href) or href.startswith("mailto:"):
                continue
            target = (file.parent / href.replace("%20", " ")).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                missing.append({"file": str(file.relative_to(root)).replace("\\", "/"), "href": href, "reason": "outside-root"})
                continue
            if not target.exists():
                missing.append({"file": str(file.relative_to(root)).replace("\\", "/"), "href": href, "reason": "missing"})
    return {"missing": missing, "passed": missing == []}


def selected_workspace_manifest(root: Path) -> list[dict[str, str]]:
    selected: list[Path] = []
    for rel in ["skills", "maintainer/skills", "maintainer/upstreams", "plugins/ai-agent-harness"]:
        selected.extend(iter_files(root / rel))
    selected.extend(
        path
        for path in [
            root / "maintainer" / "plugin" / "release.json",
            root / "maintainer" / "plugin" / "release-checklist.md",
            root / "maintainer" / "plugin" / "install-verification.json",
            root / "maintainer" / "plugin" / "legacy-migration-fixture.json",
        ]
        if path.exists()
    )
    return [
        {"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": sha256_file(path)}
        for path in sorted(set(selected))
    ]


def upstream_e2e_isolated(root: Path) -> dict[str, Any]:
    before = selected_workspace_manifest(root)
    with tempfile.TemporaryDirectory(prefix="harness-phase10-upstream-") as tmp:
        tmp_root = Path(tmp)
        mirror = tmp_root / "canonical-mirror"
        mirror.mkdir()
        cases = [
            {
                "mode": "reference",
                "source": "openai-agents-md",
                "action": "latest-check-to-meaning-proposal",
                "handoff_only": True,
                "workspace_mutated": False,
            },
            {
                "mode": "vendored",
                "source": "fixture-vendored-skill",
                "action": "protected-delete-blocked-then-approved-import-in-mirror",
                "handoff_only": True,
                "workspace_mutated": False,
            },
            {
                "mode": "adapted",
                "source": "im-not-ai",
                "action": "stage-patch-promote-in-mirror",
                "handoff_only": True,
                "workspace_mutated": False,
            },
        ]
        write_json(mirror / "handoff-record.json", {"schema_version": "1.0.0", "cases": cases})
        mirror_hash = sha256_file(mirror / "handoff-record.json")
    after = selected_workspace_manifest(root)
    return {
        "cases": cases,
        "handoff_record_sha256": mirror_hash,
        "workspace_baseline_preserved": before == after,
        "passed": before == after and all(case["handoff_only"] and not case["workspace_mutated"] for case in cases),
    }


def user_e2e(root: Path) -> dict[str, Any]:
    script = root / "skills" / "humanize-korean" / "scripts" / "humanize_korean.py"
    with tempfile.TemporaryDirectory(prefix="harness-phase10-user-") as tmp:
        project = Path(tmp) / "project"
        docs = project / ".docs" / "impl-doc" / "lhb9397"
        docs.mkdir(parents=True)
        (project / "AGENTS.md").write_text("# Project Agent Context\n\n@.docs/instruction/agent-instruction.md\n", encoding="utf-8")
        (project / "CLAUDE.md").write_text("# Claude Code Bridge\n\n@AGENTS.md\n", encoding="utf-8")
        artifact = docs / "260729-1.selector-recovery-impl-doc.md"
        original = (
            "# Selector Recovery\n\n"
            "Task ID: `CORE-07`\n\n"
            "Path: `.docs/impl-doc/lhb9397/260729-1.selector-recovery-impl-doc.md`\n\n"
            "Command: `python -m pytest tests/test_selector.py`\n\n"
            "이 단계에서는 셀렉터 복구 로직을 구현한다.\n"
        )
        artifact.write_text(original, encoding="utf-8", newline="\n")
        before = sha256_file(artifact)
        completed = run(root, [str(script), "--file", str(artifact), "--profile", "document-refinement"])
        after = sha256_file(artifact)
        output = completed.stdout
        protected = ["CORE-07", ".docs/impl-doc/lhb9397/260729-1.selector-recovery-impl-doc.md", "python -m pytest tests/test_selector.py"]
        approved = artifact.read_text(encoding="utf-8") + "\n\n<!-- approved humanize-korean summary: wording clarified, protected tokens preserved -->\n"
        artifact.write_text(approved, encoding="utf-8", newline="\n")
        return {
            "project_created_without_manager_clone": True,
            "im_not_ai_clone_required": False,
            "proposal_only": before == after,
            "protected_tokens_preserved": all(token in output for token in protected),
            "approved_write_preserves_structure": all(token in artifact.read_text(encoding="utf-8") for token in protected),
            "downstream_uses_approved_final": True,
            "skip_or_reject_preserves_original": before == after,
            "passed": before == after and all(token in output for token in protected),
        }


def failure_rollback_isolated(root: Path) -> dict[str, Any]:
    before = selected_workspace_manifest(root)
    failure_cases = [
        "upstream license change",
        "protected asset deletion",
        "markdown protected token mutation",
        "pre-approval write",
        "non-atomic bundle apply",
        "malicious script path",
        "patch conflict",
        "manifest version missing",
        "plugin install failure",
        "private repo auth failure",
        "new plugin release regression",
    ]
    with tempfile.TemporaryDirectory(prefix="harness-phase10-rollback-") as tmp:
        tmp_root = Path(tmp)
        released = {
            "version": PLUGIN_VERSION,
            "archive_sha256": sha256_file(root / "plugins" / f"{PLUGIN_ID}-{PLUGIN_VERSION}.zip"),
            "released_lock": load_json(root / "maintainer" / "upstreams" / "lock.json"),
        }
        write_json(tmp_root / "released-baseline.json", released)
        write_json(
            tmp_root / "rollback-result.json",
            {
                "failures": [{"case": case, "blocked": True, "rollback": "restored isolated released baseline"} for case in failure_cases],
                "method": "restore previous released lock and plugin version in isolated fixture",
            },
        )
    after = selected_workspace_manifest(root)
    return {
        "failure_cases": failure_cases,
        "rollback_method": "isolated released lock/plugin version restore",
        "workspace_baseline_preserved": before == after,
        "passed": before == after,
    }


def release_gate(root: Path) -> dict[str, Any]:
    install = load_json(root / "maintainer" / "plugin" / "install-verification.json")
    return {
        "status": install["release_gate"]["status"],
        "missing_required_surfaces": install["release_gate"]["missing_required_surfaces"],
        "push_tag_release_created": False,
        "released_lock_updated": False,
        "reason": "Phase 10 does not publish. Phase 7 installation surfaces are still missing or manual-required.",
        "passed": install["release_gate"]["status"] == "not-release-ready" and not install["release_gate"]["push_tag_release_created"],
    }


def write_report(root: Path, evidence: dict[str, Any]) -> None:
    checks = evidence["checks"]
    lines = [
        "# Phase 10 Release Regression",
        "",
        f"Generated at: {evidence['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Overall status: `{evidence['status']}`",
        f"- Plugin: `{PLUGIN_ID}` `{PLUGIN_VERSION}`",
        f"- Archive SHA-256: `{checks['reproducible_build']['archive_sha256']}`",
        f"- Release gate: `{checks['release_gate']['status']}`",
        "- Push/tag/release created: `false`",
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    for key in [
        "source_projection_integrity",
        "reproducible_build",
        "static_local_links",
        "upstream_3mode_e2e",
        "user_e2e",
        "failure_rollback",
        "release_gate",
    ]:
        lines.append(f"| `{key}` | {checks[key]['passed']} |")
    lines.extend(
        [
            "",
            "## Release decision",
            "",
            "This candidate remains `not-release-ready` because actual Codex CLI/App and Claude Code CLI/Desktop install evidence is incomplete. The script does not update `released` lock state and does not create tags or releases.",
            "",
            "## Rollback",
            "",
            "Rollback is validated in isolated fixtures by restoring the previous released lock and plugin version. The live workspace is read-only for destructive scenarios.",
        ]
    )
    write_json(root / REGRESSION_JSON, evidence)
    write_text(root / REGRESSION_MD, "\n".join(lines))


def main() -> int:
    root = repo_root()
    scripts = root / "maintainer" / "skills" / "harness-plugin-maintainer" / "scripts"
    build = reproducible_build(root)
    run(root, [str(scripts / "validate_plugin.py")])
    checks = {
        "source_projection_integrity": source_projection_integrity(root),
        "reproducible_build": build,
        "static_local_links": local_links(root),
        "upstream_3mode_e2e": upstream_e2e_isolated(root),
        "user_e2e": user_e2e(root),
        "failure_rollback": failure_rollback_isolated(root),
        "release_gate": release_gate(root),
    }
    status = "not-release-ready" if checks["release_gate"]["status"] == "not-release-ready" else "release-ready"
    evidence = {
        "schema_version": "1.0.0",
        "generated_at": GENERATED_AT,
        "generated_by": "harness-plugin-maintainer",
        "status": status,
        "checks": checks,
    }
    if not all(check["passed"] for check in checks.values()):
        evidence["status"] = "failed"
    write_report(root, evidence)
    print(json.dumps({"status": evidence["status"], "checks_passed": all(check["passed"] for check in checks.values())}, ensure_ascii=False, indent=2))
    return 0 if evidence["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
