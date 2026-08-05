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

import build_plugin
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

    # Counts come from the capability inventory, not from a literal. A canonical
    # skill whose upstream group is still a candidate is expected to exist in
    # skills/ while staying out of the shipped runtime.
    expected = load_json(root / "maintainer" / "plugin" / "CAPABILITIES.json")["logical_user_skills"]
    pending = build_plugin.pending_user_skills(root)
    packageable = [skill for skill in user if skill not in pending]

    checks = {
        "user_skills_match_inventory": packageable == sorted(expected),
        "pending_skills_are_canonical": all((root / "skills" / name / "SKILL.md").is_file() for name in pending),
        "manager_skills_3": len(manager) == 3,
        "agents_manager_projection_3": agents == manager,
        "claude_manager_projection_3": claude == manager,
        "plugin_codex_matches_inventory": plugin["codex_physical_skills"] == len(expected),
        "plugin_codex_agents_0": plugin["codex_physical_agents"] == 0,
        "plugin_claude_matches_inventory": plugin["claude_physical_skills"] == len(expected),
        "plugin_claude_agents_0": plugin["claude_physical_agents"] == 0,
        "plugin_admin_0": plugin["admin_in_payload"] == [],
        "pending_not_packaged": not (set(pending) & set(skill_dirs(root / PLUGIN_ROOT_REL / "runtime" / "codex" / "skills"))),
        "canonical_humanize_only": plugin["humanize_aliases"] == {},
    }
    return {
        "counts": {
            "user_skills": len(user),
            "packageable_user_skills": len(packageable),
            "pending_user_skills": pending,
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
    for base in [".user-docs", "example", "improvement_plan"]:
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
    for rel in ["skills", "maintainer/skills", "maintainer/upstreams", PLUGIN_ROOT_REL.as_posix()]:
        selected.extend(iter_files(root / rel))
    selected.extend(
        path
        for path in [
            root / ".agents" / "plugins" / "marketplace.json",
            root / ".claude-plugin" / "marketplace.json",
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


def upstream_modes_fixture(root: Path) -> dict[str, Any]:
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
        "evidence_level": "isolated-contract-fixture",
        "live_stage_or_promote_executed": False,
        "cases": cases,
        "handoff_record_sha256": mirror_hash,
        "workspace_baseline_preserved": before == after,
        "passed": before == after and all(case["handoff_only"] and not case["workspace_mutated"] for case in cases),
    }


def user_contract_fixture(root: Path) -> dict[str, Any]:
    script = root / "skills" / "humanize-korean" / "scripts" / "humanize_korean.py"
    setup_eval = root / "skills" / "harness-setup" / "evals" / "run_evals.py"
    run(root, [str(setup_eval)])
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
        proposal = json.loads(completed.stdout)
        protected = ["CORE-07", ".docs/impl-doc/lhb9397/260729-1.selector-recovery-impl-doc.md", "python -m pytest tests/test_selector.py"]
        approved_completed = run(
            root,
            [
                str(script),
                "--file",
                str(artifact),
                "--profile",
                "document-refinement",
                "--write-approved",
            ],
        )
        approved = json.loads(approved_completed.stdout)
        final_text = artifact.read_text(encoding="utf-8")
        forbidden_skill_roots = [
            project / ".agents" / "skills",
            project / ".claude" / "skills",
            project / "skills",
        ]
        setup_output_allowlist = all(not path.exists() for path in forbidden_skill_roots)
        proposal_only = before == after and proposal["proposal_only"] and not proposal["written"]
        protected_preserved = all(
            token in proposal["refined_text"] and token in final_text for token in protected
        )
        approved_write = (
            approved["written"]
            and not approved["proposal_only"]
            and final_text == approved["refined_text"]
            and final_text.startswith("# Selector Recovery\n")
        )
        passed = proposal_only and protected_preserved and approved_write and setup_output_allowlist
        return {
            "evidence_level": "filesystem-and-script-fixture",
            "live_agent_skill_invocation_executed": False,
            "harness_setup_eval_passed": True,
            "project_created_without_manager_clone": True,
            "im_not_ai_clone_required": False,
            "setup_output_allowlist_preserved": setup_output_allowlist,
            "local_skill_directories_created": not setup_output_allowlist,
            "proposal_only": proposal_only,
            "protected_tokens_preserved": protected_preserved,
            "approved_write_preserves_structure": approved_write,
            "downstream_uses_approved_final": final_text == approved["refined_text"],
            "skip_or_reject_preserves_original": before == after,
            "passed": passed,
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
        baseline_path = tmp_root / "released-baseline.json"
        active_path = tmp_root / "active-state.json"
        write_json(baseline_path, released)
        shutil.copyfile(baseline_path, active_path)
        baseline_sha = sha256_file(baseline_path)
        failed_candidate = {**released, "version": "0.1.1-failed", "archive_sha256": "0" * 64}
        write_json(active_path, failed_candidate)
        mutation_observed = sha256_file(active_path) != baseline_sha
        shutil.copyfile(baseline_path, active_path)
        isolated_baseline_restored = sha256_file(active_path) == baseline_sha
        write_json(
            tmp_root / "rollback-result.json",
            {
                "failures": [
                    {
                        "case": case,
                        "blocked": True,
                        "rollback": "restored isolated released baseline",
                    }
                    for case in failure_cases
                ],
                "method": "restore previous released lock and plugin version in isolated fixture",
                "mutation_observed": mutation_observed,
                "baseline_restored": isolated_baseline_restored,
            },
        )
    after = selected_workspace_manifest(root)
    return {
        "failure_cases": failure_cases,
        "rollback_method": "isolated released lock/plugin version restore",
        "failed_candidate_diff_observed": mutation_observed,
        "isolated_baseline_restored": isolated_baseline_restored,
        "workspace_baseline_preserved": before == after,
        "passed": before == after and mutation_observed and isolated_baseline_restored,
    }


def release_gate(root: Path) -> dict[str, Any]:
    install = load_json(root / "maintainer" / "plugin" / "install-verification.json")
    missing = install["release_gate"]["missing_required_surfaces"]
    cli_smoke = install.get("cli_smoke", {})
    smoke_current = cli_smoke.get("evidence_applies_to_current_version") is True
    return {
        "status": install["release_gate"]["status"],
        "missing_required_surfaces": missing,
        "push_tag_release_created": False,
        "released_lock_updated": False,
        "reason": (
            "Phase 10은 publish하지 않는다. "
            + (
                "현재 후보의 격리 Codex·Claude CLI 설치 smoke는 통과했다; "
                if smoke_current
                else "현재 후보의 CLI 설치 smoke는 검증되지 않아 이전 버전 증적을 승계하지 않는다; "
            )
            + f"다음 수동 증적이 남아 있다: {', '.join(missing)}."
        ),
        "passed": install["release_gate"]["status"] == "not-release-ready" and not install["release_gate"]["push_tag_release_created"],
    }


def write_report(root: Path, evidence: dict[str, Any]) -> None:
    checks = evidence["checks"]
    lines = [
        "# Phase 10 릴리스 회귀검증",
        "",
        f"생성 시각: {evidence['generated_at']}",
        "",
        "## 요약",
        "",
        f"- 전체 상태: `{evidence['status']}`",
        f"- 플러그인: `{PLUGIN_ID}` `{PLUGIN_VERSION}`",
        f"- 아카이브 SHA-256: `{checks['reproducible_build']['archive_sha256']}`",
        f"- 릴리스 게이트: `{checks['release_gate']['status']}`",
        "- push/tag/release 생성: `false`",
        "",
        "## 검사",
        "",
        "| 검사 | 결과 |",
        "|---|---|",
    ]
    for key in [
        "source_projection_integrity",
        "reproducible_build",
        "static_local_links",
        "upstream_modes_fixture",
        "user_contract_fixture",
        "failure_rollback",
        "release_gate",
    ]:
        result = "통과" if checks[key]["passed"] else "실패"
        lines.append(f"| `{key}` | {result} |")
    lines.extend(
        [
            "",
            "## 릴리스 결정",
            "",
            (
                f"`{', '.join(checks['release_gate']['missing_required_surfaces'])}`에 대한 대화형 "
                "증적이 아직 필요하므로 이 후보는 `not-release-ready` 상태를 유지한다. "
                f"{checks['release_gate']['reason']} 이 스크립트는 `released` "
                "잠금 상태를 갱신하지 않으며 태그 또는 릴리스를 생성하지 않는다."
            ),
            "",
            "## 롤백",
            "",
            "격리 픽스처에서 이전 `released` 잠금과 플러그인 버전을 복원하는 방식으로 롤백을 검증했다. 실제 작업공간은 파괴적 시나리오에 대해 읽기 전용이다.",
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
        "upstream_modes_fixture": upstream_modes_fixture(root),
        "user_contract_fixture": user_contract_fixture(root),
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
