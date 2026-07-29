#!/usr/bin/env python3
"""Failure/safety evals for skill-portfolio-maintainer."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "maintainer" / "skills" / "skill-portfolio-maintainer"
SCRIPTS = SKILL / "scripts"
FIXTURES = SKILL / "evals" / "fixtures"
STAGING = ROOT / "maintainer" / "upstreams" / "staging"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))

import check_upstreams  # noqa: E402
from portfolio_common import hash_tree, safe_join, sha256_path  # noqa: E402


def run(args: list[str], expect: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
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
        str(FIXTURES / "discover_upstreams.json"),
        "--no-default-catalog",
        "--search-query",
        "agent skill korean",
    ])
    report = parse_json(completed.stdout)
    assert report["mode"] == "discover"
    assert report["candidate_registration"] == "approval-required"
    assert report["discovery_inputs"]["fixed_seed_only"] is False
    assert report["discovery_inputs"]["search_queries"] == ["agent skill korean"]
    assert report["input_errors"] == []
    assert any(item["provenance_url"] == "https://github.com/example/korean-agent-skill" for item in report["candidates"])
    assert all(item["state_transition"] == "report-only" for item in report["candidates"])


def test_stage_blocks_malicious_path() -> None:
    run([
        str(SCRIPTS / "stage_upstream.py"),
        "--candidate",
        str(FIXTURES / "malicious-path-candidate.json")
    ], expect=2)


def test_stage_blocks_candidate_id_traversal() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        run([
            str(SCRIPTS / "stage_upstream.py"),
            "--root",
            str(temporary_root),
            "--candidate",
            str(FIXTURES / "malicious-id-candidate.json"),
        ], expect=2)
        run([
            str(SCRIPTS / "promote_upstream.py"),
            "--root",
            str(temporary_root),
            "--candidate-id",
            "../../escaped-candidate",
            "--approval-id",
            "APPROVAL-GENERAL",
        ], expect=2)
        run([
            str(SCRIPTS / "rollback_upstream.py"),
            "--root",
            str(temporary_root),
            "--candidate-id",
            "../../escaped-candidate",
        ], expect=2)
        assert not (temporary_root / "maintainer" / "escaped-candidate").exists()


def test_safe_join_rejects_sibling_prefix_and_absolute_paths() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary) / "root"
        temporary_root.mkdir()
        for unsafe in ("../root-sibling/file.txt", "/absolute.txt", "C:\\outside.txt"):
            try:
                safe_join(temporary_root, unsafe)
            except ValueError:
                continue
            raise AssertionError(f"safe_join accepted unsafe path: {unsafe}")


def test_tree_hash_blocks_binary_content() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        tree = Path(temporary) / "tree"
        tree.mkdir()
        (tree / "payload.bin").write_bytes(b"\x89PNG\r\n\x1a\n\x00binary")
        try:
            hash_tree(tree)
        except ValueError as exc:
            assert "binary" in str(exc)
            return
        raise AssertionError("hash_tree accepted binary content")


def test_check_uses_exact_default_branch() -> None:
    base = "https://api.github.com/repos/example/no-main"
    calls: list[str] = []
    original_http_json = check_upstreams.http_json

    def fake_http_json(url: str):
        calls.append(url)
        if url == f"{base}/releases":
            return []
        if url == base:
            return {"default_branch": "trunk"}
        if url == f"{base}/branches/trunk":
            return {"commit": {"sha": "f" * 40}}
        raise AssertionError(f"unexpected GitHub API call: {url}")

    check_upstreams.http_json = fake_http_json
    try:
        observed = check_upstreams.resolve_github_source({
            "id": "default-branch-fixture",
            "upstream": {
                "repository": "https://github.com/example/no-main",
                "tracking": "release",
                "tag_pattern": "v*",
            },
        })
    finally:
        check_upstreams.http_json = original_http_json

    assert observed["status"] == "fallback"
    assert observed["ref"] == "trunk"
    assert calls == [f"{base}/releases", base, f"{base}/branches/trunk"]
    assert f"{base}/branches" not in calls


def test_check_date_override_is_deterministic() -> None:
    original = os.environ.get("HARNESS_UPSTREAM_CHECKED_AT")
    try:
        os.environ["HARNESS_UPSTREAM_CHECKED_AT"] = "2026-07-29"
        lock = {"states": []}
        check_upstreams.update_observed(
            lock,
            "date-fixture",
            {
                "status": "ok",
                "ref": "main",
                "sha": "a" * 40,
                "source_url": "https://github.com/example/date-fixture/tree/main",
            },
        )
        assert lock["states"][0]["observed"]["checked_at"] == "2026-07-29"
        os.environ["HARNESS_UPSTREAM_CHECKED_AT"] = "not-a-date"
        try:
            check_upstreams.checked_at()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid upstream check date override was accepted")
    finally:
        if original is None:
            os.environ.pop("HARNESS_UPSTREAM_CHECKED_AT", None)
        else:
            os.environ["HARNESS_UPSTREAM_CHECKED_AT"] = original


def test_actual_tree_hashes_and_post_stage_mutation_block() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        source = temporary_root / "candidate-source"
        runtime = temporary_root / "runtime-preview"
        source.mkdir()
        runtime.mkdir()
        (source / "SKILL.md").write_text("# Candidate\n", encoding="utf-8")
        (runtime / "adapter.py").write_text("print('safe')\n", encoding="utf-8")
        candidate = {
            "id": "actual-tree-hash",
            "upstream": {"source_id": "fixture", "ref": "v1.0.0", "sha": "a" * 40},
            "trees": {"source": "candidate-source", "runtime": "runtime-preview"},
            "file_map": [{"upstream_path": "SKILL.md", "local_path": "skills/example/SKILL.md"}],
            "validation": {"fixture": "actual tree hashes"},
        }
        candidate_file = temporary_root / "candidate.json"
        candidate_file.write_text(json.dumps(candidate), encoding="utf-8")

        staged = parse_json(run([
            str(SCRIPTS / "stage_upstream.py"),
            "--root",
            str(temporary_root),
            "--candidate",
            str(candidate_file),
        ]).stdout)
        source_hash = hash_tree(source)["sha256"]
        runtime_hash = hash_tree(runtime)["sha256"]
        assert staged["source_tree"]["sha256"] == source_hash
        assert staged["runtime_tree"]["sha256"] == runtime_hash
        assert source_hash != sha256_path(candidate_file)

        promoted = parse_json(run([
            str(SCRIPTS / "promote_upstream.py"),
            "--root",
            str(temporary_root),
            "--candidate-id",
            "actual-tree-hash",
            "--approval-id",
            "APPROVAL-GENERAL",
            "--dry-run",
        ]).stdout)
        assert promoted["source_hash"] == source_hash
        assert promoted["runtime_hash"] == runtime_hash

        (runtime / "adapter.py").write_text("print('changed')\n", encoding="utf-8")
        run([
            str(SCRIPTS / "promote_upstream.py"),
            "--root",
            str(temporary_root),
            "--candidate-id",
            "actual-tree-hash",
            "--approval-id",
            "APPROVAL-GENERAL",
            "--dry-run",
        ], expect=2)


def test_public_scripts_have_real_help() -> None:
    for script_name in [
        "check_upstreams.py",
        "discover_upstreams.py",
        "stage_upstream.py",
        "promote_upstream.py",
        "rollback_upstream.py",
        "validate_registry.py",
    ]:
        completed = run([str(SCRIPTS / script_name), "--help"])
        assert "usage:" in completed.stdout.lower()


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
        test_stage_blocks_candidate_id_traversal,
        test_safe_join_rejects_sibling_prefix_and_absolute_paths,
        test_tree_hash_blocks_binary_content,
        test_check_uses_exact_default_branch,
        test_check_date_override_is_deterministic,
        test_actual_tree_hashes_and_post_stage_mutation_block,
        test_public_scripts_have_real_help,
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
