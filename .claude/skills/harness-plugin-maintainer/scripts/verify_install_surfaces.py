#!/usr/bin/env python3
"""Verify Phase 7 install/update surfaces and write release gate evidence.

This script does not mutate user plugin installations. It records which CLI/app
surfaces are available in the current host and validates local release-candidate
behavior that can be checked without external marketplace state.
"""

from __future__ import annotations

import argparse
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
MANUAL_SURFACE_TEMPLATE_REL = Path("maintainer/plugin/manual-surface-test-template.md")

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

    # Smoke evidence is tied to the artifact it installed. Carrying a previous
    # version's result forward would let a rebuilt archive inherit verification
    # it never received.
    smoke_versions = {
        platforms[name].get("installed_payload", {}).get("version")
        for name in required
        if name in platforms
    }
    version_matches = smoke_versions == {PLUGIN_VERSION}

    passed = (
        evidence.get("status") == "passed"
        and evidence.get("evidence_level") == "marketplace-install-and-cache-smoke"
        and evidence.get("model_invocation_verified") is False
        and required.issubset(platforms)
        and version_matches
        and all(
            platforms[name].get("status") == "passed"
            and platforms[name].get("model_invocation_verified") is False
            for name in required
        )
    )
    if passed:
        summary = "isolated marketplace add/install/list/uninstall/remove and cache inspection passed; model invocation not tested"
    elif not version_matches:
        observed = sorted(str(item) for item in smoke_versions)
        summary = (
            f"CLI smoke evidence covers plugin version(s) {observed}, not the current "
            f"candidate {PLUGIN_VERSION}; re-run smoke_cli_install.py"
        )
    else:
        summary = "CLI smoke evidence is incomplete or failed"

    return {
        **evidence,
        "status": "passed" if passed else "failed",
        "evidence_applies_to_current_version": version_matches,
        "summary": summary,
    }


def render_release_checklist(evidence: dict) -> str:
    cli_smoke_verified = all(
        evidence["surfaces"][surface]["status"] == "install-smoke-verified"
        for surface in ("codex-cli", "claude-code-cli")
    )
    if cli_smoke_verified:
        gate_reason = (
            "격리된 Codex 및 Claude Code CLI 설치 스모크 검사는 통과했지만 설치/캐시 "
            "스모크 검사는 모델 호출이 아니다. Codex와 Claude의 모든 CLI/앱 인터페이스에는 "
            "직접 호출, 출력, 재시작 및 새 세션 수동 증적이 여전히 필요하다."
        )
        # 스킬 수는 실제 설치 증적에서 읽는다. 리터럴을 두면 체크리스트가 실제와
        # 다른 숫자를 주장해도 --check가 통과한다.
        counts = sorted(
            {
                platform.get("installed_payload", {}).get("skill_count")
                for platform in evidence["cli_smoke"].get("platforms", {}).values()
            }
            - {None}
        )
        skill_count = counts[0] if len(counts) == 1 else "/".join(map(str, counts))
        completed_cli = (
            "- Codex CLI 설치 스모크: 마켓플레이스 등록/목록 확인/제거, 플러그인 등록/목록 확인/제거, "
            f"`harness-setup`과 `humanize-korean` 디렉터리를 포함한 설치 캐시의 스킬 {skill_count}개 / "
            "에이전트 0개를 확인했다(모델 호출 아님).\n"
            "- Claude Code CLI 설치 스모크: 엄격한 플러그인/마켓플레이스 검증, 마켓플레이스 "
            f"등록/목록 확인/제거, 플러그인 설치/목록 확인/제거, 설치 캐시의 스킬 {skill_count}개 / "
            "에이전트 0개를 확인했다(모델 호출 아님)."
        )
        pending_cli = ""
    else:
        gate_reason = (
            "격리된 CLI 설치 증적이 불완전하며, 네 가지 CLI/앱 인터페이스 모두 직접 모델 호출 "
            "증적이 필요하다."
        )
        completed_cli = "- CLI 설치 스모크: 불완전."
        pending_cli = (
            "- Codex 및 Claude Code CLI: 공식 CLI로 `scripts/smoke_cli_install.py`를 "
            "실행하고 통과 증적을 보존한다.\n"
        )
    def check_result(value: bool) -> str:
        return "통과" if value else "실패"

    if cli_smoke_verified:
        cli_summary = "격리된 마켓플레이스 등록/설치/목록 확인/제거 및 캐시 검사를 통과했으며, 모델 호출은 테스트하지 않음"
    elif evidence["cli_smoke"].get("evidence_applies_to_current_version") is False:
        # Say which artifact the evidence actually covers. "incomplete or failed"
        # would hide that the smoke passed for a different version.
        cli_summary = (
            "CLI 스모크 증적이 현재 릴리스 후보가 아닌 다른 플러그인 버전을 대상으로 한다. "
            "`smoke_cli_install.py`를 재실행해야 한다"
        )
    else:
        cli_summary = "CLI 스모크 증적이 불완전하거나 실패함"
    return f"""# 플러그인 릴리스 체크리스트

생성 시각: {evidence["generated_at"]}

## 릴리스 후보

- 플러그인 ID: `{evidence["plugin"]["plugin_id"]}`
- 버전: `{evidence["plugin"]["version"]}`
- 아카이브: `{evidence["plugin"]["archive"]}`
- 아카이브 SHA-256: `{evidence["plugin"]["archive_sha256"]}`
- Codex 물리 스킬 수: {evidence["plugin"]["codex_physical_skills"]}
- Codex 물리 에이전트 수: {evidence["plugin"]["codex_physical_agents"]}
- Claude 물리 스킬 수: {evidence["plugin"]["claude_physical_skills"]}
- Claude 물리 에이전트 수: {evidence["plugin"]["claude_physical_agents"]}
- Markdown 생성 스킬 handoff 수: {evidence["plugin"]["markdown_producer_count"]}

## 자동화된 로컬 검사

| 검사 | 결과 |
|---|---|
| manifest 이름/버전 일치 | {check_result(evidence["plugin"]["codex_manifest_matches_claude"])} |
| 아카이브 체크섬과 릴리스 메타데이터 일치 | {check_result(evidence["plugin"]["archive_sha256_matches_release"])} |
| 패키징된 adapted/vendored NOTICE-license-lock 완결성 | {check_result(evidence["plugin"]["packaged_upstream_closure"])} |
| `released` 상태 보존 | {check_result(evidence["plugin"]["released_state_preserved"])} |
| `humanize-korean`이 제안만 수행 | {check_result(evidence["humanize_korean"]["proposal_only"])} |
| `humanize-korean`이 원본 파일을 변경하지 않음 | {check_result(evidence["humanize_korean"]["file_unchanged"])} |
| 보호 토큰 보존 | {check_result(evidence["humanize_korean"]["protected_tokens_preserved"])} |

## 인터페이스별 증적

| 인터페이스 | 상태 | 증적 |
|---|---|---|
| Codex CLI | `{evidence["surfaces"]["codex-cli"]["status"]}` | {cli_summary} |
| Codex 앱 | `{evidence["surfaces"]["codex-desktop-app"]["status"]}` | 앱의 Plugins UI에서 직접 설치·업데이트한 증적이 필요하므로 이 셸에서 완료할 수 없음 |
| Claude Code CLI | `{evidence["surfaces"]["claude-code-cli"]["status"]}` | {cli_summary} |
| Claude 앱 | `{evidence["surfaces"]["claude-desktop-code"]["status"]}` | 앱에서 직접 설치·호출하고 local/SSH cache를 확인한 증적이 필요함 |

## 릴리스 게이트

상태: **`not-release-ready`**

사유: {gate_reason}

## 완료한 자동 설치 검사

{completed_cli}

## `release-ready` 전 필수 작업

{pending_cli}- 직접 테스트 기록: `{MANUAL_SURFACE_TEMPLATE_REL.as_posix()}`를 `maintainer/plugin/manual-evidence/YYYYMMDD/{{surface}}.md`로 복사하고 인터페이스마다 새로운 픽스처 하나를 보존한다.
- 네 인터페이스 모두: `harness-setup`과 `humanize-korean`을 호출하고, 제안 전용 동작과 생성된 허용 목록을 검증하며, `.agents/skills`, `.claude/skills`, `skills`가 생성되지 않았는지 확인하고 관리 블록 확장을 보존한다.
- 네 인터페이스 모두: 새 작업/세션을 다시 열어 같은 산출물 지문을 다시 제안하지 않는지 확인하고 `.docs/.harness/humanize-handoffs.json` 이벤트를 보존한다.
- 네 인터페이스 모두: 제안된 쓰기 전에 취소하고 원본 해시와 사용자 감시 토큰이 보존되는지 확인한다.
- Codex 앱: 후보 마켓플레이스를 설치하고 재시작/새 작업에서 표식/버전을 확인한 뒤 vN+1로 업데이트한다.
- Claude 앱: 로컬 호스트의 캐시/버전을 확인하고 앱을 재시작해 새 세션을 연다. SSH를 지원 인터페이스로 선언한 경우에만 SSH에서도 반복한다. 지원하지 않는 클라우드/WSL 경로를 문서화한다.
- 인터페이스 상태를 `verified`로 변경하기 전에 검토자가 승인한 직접 테스트 기록을 이 체크리스트에 연결한다.
- 레거시 이전: 읽기 전용 목록 조사를 수행하고, 명시적 승인이 있을 때만 백업/제거를 실행한 뒤 플러그인이 한 번만 탐색되는지 확인한다.
"""


def write_release_checklist(root: Path, evidence: dict) -> None:
    write_text(
        root / "maintainer" / "plugin" / "release-checklist.md",
        render_release_checklist(evidence),
    )


def deterministic_evidence(evidence: dict) -> dict:
    """Exclude only host-specific CLI discovery diagnostics from tracked checks."""
    return {
        key: value
        for key, value in evidence.items()
        if key != "cli_probes"
    }


def check_tracked_evidence(root: Path, evidence: dict) -> list[str]:
    errors: list[str] = []
    plugin_root = root / "maintainer" / "plugin"
    verification_path = plugin_root / "install-verification.json"
    legacy_path = plugin_root / "legacy-migration-fixture.json"
    checklist_path = plugin_root / "release-checklist.md"

    if not verification_path.is_file():
        errors.append(f"missing tracked evidence: {verification_path}")
    else:
        tracked = load_json(verification_path)
        if deterministic_evidence(tracked) != deterministic_evidence(evidence):
            errors.append("deterministic install-verification evidence is stale")

    if not legacy_path.is_file():
        errors.append(f"missing tracked evidence: {legacy_path}")
    elif load_json(legacy_path) != evidence["legacy_migration"]:
        errors.append("legacy migration fixture is stale")

    expected_checklist = render_release_checklist(evidence).rstrip() + "\n"
    if not checklist_path.is_file():
        errors.append(f"missing tracked evidence: {checklist_path}")
    elif checklist_path.read_text(encoding="utf-8") != expected_checklist:
        errors.append("release checklist is stale")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="compare deterministic evidence fields without writing tracked files",
    )
    mode.add_argument(
        "--no-write",
        action="store_true",
        help="run probes and validation without updating tracked evidence files",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    codex_help = run_probe(["codex", "--help"])
    codex_plugin = run_probe(["codex", "plugin", "--help"])
    claude_help = run_probe(["claude", "--help"])
    cli_smoke = load_cli_smoke(root)
    cli_smoke_passed = cli_smoke["status"] == "passed"
    surfaces = {
        "codex-cli": {
            "status": "install-smoke-verified" if cli_smoke_passed else "blocked",
            "summary": cli_smoke["summary"],
        },
        "codex-desktop-app": {
            "status": "manual-required",
            "summary": "Interactive Plugins UI install/update requires app surface and cannot be completed from this shell.",
        },
        "claude-code-cli": {
            "status": "install-smoke-verified" if cli_smoke_passed else "blocked",
            "summary": cli_smoke["summary"],
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
        "manual_surface_test": {
            "template": MANUAL_SURFACE_TEMPLATE_REL.as_posix(),
            "required_checks": [
                "explicit harness-setup invocation",
                "explicit humanize-korean invocation with proposal-only result",
                "setup output allowlist",
                "no local skill directories created",
                "managed-block user extensions preserved",
                "same fingerprint not re-proposed in a new task/session",
                "cancelled write leaves original hashes unchanged",
                "reviewed evidence record linked from release checklist",
            ],
        },
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
    if args.check:
        errors = check_tracked_evidence(root, evidence)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print("install surface deterministic evidence check passed")
        return 0
    if not args.no_write:
        write_json(root / "maintainer" / "plugin" / "install-verification.json", evidence)
        write_json(root / "maintainer" / "plugin" / "legacy-migration-fixture.json", evidence["legacy_migration"])
        write_release_checklist(root, evidence)
    print(json.dumps(evidence["release_gate"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
