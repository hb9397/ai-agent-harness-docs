#!/usr/bin/env python3
"""Failure/safety evals for skill-portfolio-maintainer."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "maintainer" / "skills" / "skill-portfolio-maintainer"
SCRIPTS = SKILL / "scripts"
FIXTURES = SKILL / "evals" / "fixtures"
STAGING = ROOT / "maintainer" / "upstreams" / "staging"


def run(args: list[str], expect: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    if completed.returncode != expect:
        raise AssertionError(
            f"expected exit {expect}, got {completed.returncode}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed


def parse_json(stdout: str) -> dict:
    return json.loads(stdout)


def test_check_is_observed_only() -> None:
    completed = run([
        str(SCRIPTS / "check_upstreams.py"),
        "--fixture",
        str(FIXTURES / "check_upstreams.json")
    ])
    report = parse_json(completed.stdout)
    assert report["mode"] == "check"
    assert report["write_observed"] is False
    assert any(item["observed"]["status"] == "error" for item in report["results"])


def test_discovery_is_report_only() -> None:
    completed = run([
        str(SCRIPTS / "discover_upstreams.py"),
        "--fixture",
        str(FIXTURES / "discover_upstreams.json")
    ])
    report = parse_json(completed.stdout)
    assert report["mode"] == "discover"
    assert report["candidate_registration"] == "approval-required"
    assert all(item["state_transition"] == "report-only" for item in report["candidates"])


def test_stage_blocks_malicious_path() -> None:
    run([
        str(SCRIPTS / "stage_upstream.py"),
        "--candidate",
        str(FIXTURES / "malicious-path-candidate.json")
    ], expect=2)


def test_self_update_blocks_same_session() -> None:
    run([
        str(SCRIPTS / "stage_upstream.py"),
        "--candidate",
        str(FIXTURES / "self-update-candidate.json")
    ], expect=2)


def test_protected_asset_requires_asset_approval() -> None:
    candidate = FIXTURES / "protected-asset-candidate.json"
    run([str(SCRIPTS / "stage_upstream.py"), "--candidate", str(candidate)])
    run([
        str(SCRIPTS / "promote_upstream.py"),
        "--candidate-id",
        "protected-asset-change",
        "--approval-id",
        "APPROVAL-GENERAL"
    ], expect=2)
    run([
        str(SCRIPTS / "promote_upstream.py"),
        "--candidate-id",
        "protected-asset-change",
        "--approval-id",
        "APPROVAL-GENERAL",
        "--asset-approval-id",
        "APPROVAL-ASSET",
        "--dry-run"
    ])


def test_destructive_requires_destructive_approval() -> None:
    candidate = FIXTURES / "destructive-candidate.json"
    run([str(SCRIPTS / "stage_upstream.py"), "--candidate", str(candidate)])
    run([
        str(SCRIPTS / "promote_upstream.py"),
        "--candidate-id",
        "destructive-change",
        "--approval-id",
        "APPROVAL-GENERAL"
    ], expect=2)
    run([
        str(SCRIPTS / "promote_upstream.py"),
        "--candidate-id",
        "destructive-change",
        "--approval-id",
        "APPROVAL-GENERAL",
        "--destructive-approval-id",
        "APPROVAL-DESTRUCTIVE",
        "--dry-run"
    ])


def test_im_not_ai_dogfood_stages_and_dry_run_promotes() -> None:
    candidate = FIXTURES / "im-not-ai-same-pinned-candidate.json"
    run([str(SCRIPTS / "stage_upstream.py"), "--candidate", str(candidate)])
    completed = run([
        str(SCRIPTS / "promote_upstream.py"),
        "--candidate-id",
        "im-not-ai-v2.3.0-dogfood",
        "--approval-id",
        "APPROVAL-GENERAL",
        "--asset-approval-id",
        "APPROVAL-ASSET",
        "--dry-run"
    ])
    report = parse_json(completed.stdout)
    assert report["handoff_to"] == "harness-plugin-maintainer"
    assert report["embedded_lock_changed"] is False


def main() -> int:
    tests = [
        test_check_is_observed_only,
        test_discovery_is_report_only,
        test_stage_blocks_malicious_path,
        test_self_update_blocks_same_session,
        test_protected_asset_requires_asset_approval,
        test_destructive_requires_destructive_approval,
        test_im_not_ai_dogfood_stages_and_dry_run_promotes,
    ]
    try:
        for test in tests:
            test()
    finally:
        for candidate_id in [
            "protected-asset-change",
            "destructive-change",
            "im-not-ai-v2.3.0-dogfood",
        ]:
            shutil.rmtree(STAGING / candidate_id, ignore_errors=True)
    print("skill-portfolio-maintainer evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
