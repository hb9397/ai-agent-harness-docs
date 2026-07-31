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
import validate_registry  # noqa: E402
from portfolio_common import (  # noqa: E402
    hash_tree,
    is_protected_asset_path,
    safe_join,
    sha256_path,
    stable_release,
)


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


def test_check_observes_only_exact_watched_paths() -> None:
    base = "https://api.github.com/repos/example/watched"
    calls: list[str] = []
    original_http_json = check_upstreams.http_json

    def fake_http_json(url: str):
        calls.append(url)
        if url == base:
            return {"default_branch": "main"}
        if url == f"{base}/branches/main":
            return {"commit": {"sha": "a" * 40}}
        if url == f"{base}/commits?sha=main&path=skills%2Fdemo%2FSKILL.md&per_page=1":
            return [{
                "sha": "b" * 40,
                "html_url": f"https://github.com/example/watched/commit/{'b' * 40}",
            }]
        raise AssertionError(f"unexpected GitHub API call: {url}")

    check_upstreams.http_json = fake_http_json
    try:
        observed = check_upstreams.resolve_github_source(
            {
                "id": "watched-path-fixture",
                "upstream": {
                    "repository": "https://github.com/example/watched",
                    "tracking": "branch",
                    "watched_paths": ["skills/demo/SKILL.md", "scripts/**"],
                },
            },
            verify_watched_paths=True,
        )
    finally:
        check_upstreams.http_json = original_http_json

    assert observed["watched_paths"] == [{
        "path": "skills/demo/SKILL.md",
        "status": "ok",
        "latest_commit_sha": "b" * 40,
        "latest_commit_url": f"https://github.com/example/watched/commit/{'b' * 40}",
    }]
    assert all("scripts" not in call for call in calls)


def test_check_source_filter_is_exact() -> None:
    completed = run([
        str(SCRIPTS / "check_upstreams.py"),
        "--fixture",
        str(FIXTURES / "check_upstreams.json"),
        "--source",
        "im-not-ai",
    ])
    report = parse_json(completed.stdout)
    assert report["requested_sources"] == ["im-not-ai"]
    assert [item["id"] for item in report["results"]] == ["im-not-ai"]


def test_latest_stable_release_does_not_depend_on_api_order() -> None:
    releases = [
        {
            "tag_name": "v1.0.0",
            "draft": False,
            "prerelease": False,
            "published_at": "2026-01-01T00:00:00Z",
        },
        {
            "tag_name": "v3.0.0-rc.1",
            "draft": False,
            "prerelease": True,
            "published_at": "2026-03-01T00:00:00Z",
        },
        {
            "tag_name": "v2.0.0",
            "draft": False,
            "prerelease": False,
            "published_at": "2026-02-01T00:00:00Z",
        },
    ]
    assert stable_release(releases, "v*")["tag_name"] == "v2.0.0"


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


def test_partial_watched_path_errors_preserve_previous_observations() -> None:
    lock = {
        "states": [{
            "id": "partial-path-fixture",
            "observed": {
                "source_url": "https://github.com/example/repo/tree/main",
                "checked_at": "2026-07-29",
                "ref": "main",
                "sha": "a" * 40,
                "note": "previous",
                "watched_paths": [{
                    "path": "SKILL.md",
                    "status": "ok",
                    "latest_commit_sha": "b" * 40,
                }],
            },
            "accepted": None,
            "embedded": None,
            "packaged": None,
            "released": None,
        }]
    }
    check_upstreams.update_observed(
        lock,
        "partial-path-fixture",
        {
            "status": "ok",
            "ref": "main",
            "sha": "c" * 40,
            "source_url": "https://github.com/example/repo/tree/main",
            "note": "No matching stable release; default branch observed.",
            "watched_paths": [{
                "path": "SKILL.md",
                "status": "error",
                "error": "HTTP 403: rate limit exceeded",
            }],
        },
    )
    observed = lock["states"][0]["observed"]
    assert observed["sha"] == "c" * 40
    assert observed["watched_paths"][0]["latest_commit_sha"] == "b" * 40
    assert "incomplete" in observed["note"].lower()
    assert "No matching stable release" in observed["note"]


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
            "file_map": [{"upstream_path": "SKILL.md", "local_path": "skills/sample/SKILL.md"}],
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


def test_imported_status_check_is_prose_language_neutral() -> None:
    assert validate_registry.has_accepted_adapted_status("accepted adapted")
    assert validate_registry.has_accepted_adapted_status("`accepted` `adapted`")
    assert not validate_registry.has_accepted_adapted_status("승인된 변형 출처")


def test_external_relationships_and_behavior_contracts_are_consistent() -> None:
    errors: list[str] = []
    validate_registry.validate_registry(ROOT, errors)
    assert errors == [], "\n".join(errors)


def _group_fixture() -> tuple[dict, dict]:
    """Minimal registry/lock pair for one upstream tracked twice."""
    registry = {
        "sources": [
            {
                "id": "demo-runtime",
                "integration_mode": "adapted",
                "relationship_group": "demo",
                "lifecycle": "candidate",
                "upstream": {"repository": "https://example.invalid/demo", "source_url": "https://example.invalid/demo"},
                "provenance": {"license_spdx": "MIT", "notice_path": "maintainer/upstreams/provenance/demo/NOTICE.md", "file_map": []},
            },
            {
                "id": "demo-principles",
                "integration_mode": "reference",
                "relationship_group": "demo",
                "lifecycle": "candidate",
                "upstream": {"repository": "https://example.invalid/demo", "source_url": "https://example.invalid/demo"},
                "provenance": {"license_spdx": "MIT", "notice_path": None,
                               "file_map": [{"treatment": "reference-only"}]},
            },
        ]
    }
    lock = {
        "states": [
            {"id": "demo-runtime", "observed": {"sha": "a" * 40}, "accepted": {"sha": "a" * 40}},
            {"id": "demo-principles", "observed": {"sha": "a" * 40}, "accepted": {"sha": "a" * 40}},
        ]
    }
    return registry, lock


def test_relationship_group_accepts_matched_pair() -> None:
    registry, lock = _group_fixture()
    errors: list[str] = []
    validate_registry.validate_relationship_groups(registry, lock, errors)
    assert errors == [], "\n".join(errors)


def test_relationship_group_blocks_sha_drift() -> None:
    registry, lock = _group_fixture()
    lock["states"][1]["accepted"]["sha"] = "b" * 40
    errors: list[str] = []
    validate_registry.validate_relationship_groups(registry, lock, errors)
    assert any("accepted sha must match" in item for item in errors), errors


def test_relationship_group_blocks_partial_promotion() -> None:
    registry, lock = _group_fixture()
    registry["sources"][0]["lifecycle"] = "active"
    errors: list[str] = []
    validate_registry.validate_relationship_groups(registry, lock, errors)
    assert any("promoted atomically" in item for item in errors), errors


def test_relationship_group_blocks_license_and_repository_split() -> None:
    registry, lock = _group_fixture()
    registry["sources"][1]["provenance"]["license_spdx"] = "Apache-2.0"
    registry["sources"][1]["upstream"]["repository"] = "https://example.invalid/other"
    errors: list[str] = []
    validate_registry.validate_relationship_groups(registry, lock, errors)
    assert any("license_spdx must match" in item for item in errors), errors
    assert any("upstream.repository must match" in item for item in errors), errors


def test_reference_relationship_stays_out_of_packaging() -> None:
    registry, lock = _group_fixture()
    registry["sources"][1]["provenance"]["notice_path"] = "maintainer/upstreams/provenance/demo/NOTICE.md"
    registry["sources"][1]["provenance"]["file_map"] = [{"treatment": "verbatim"}]
    errors: list[str] = []
    validate_registry.validate_relationship_groups(registry, lock, errors)
    assert any("must not claim a packaged notice_path" in item for item in errors), errors
    assert any("file_map must stay reference-only" in item for item in errors), errors


def test_canonical_skill_count_is_derived_not_hardcoded() -> None:
    expected = sum(
        1
        for base in (ROOT / "skills", ROOT / "maintainer" / "skills")
        for path in base.iterdir()
        if (path / "SKILL.md").is_file()
    )
    assert validate_registry.canonical_skill_count(ROOT) == expected
    current = json.loads((ROOT / "maintainer" / "upstreams" / "provenance" / "current-skills.json").read_text(encoding="utf-8"))
    assert len(current["skills"]) == expected


def test_candidate_sources_are_not_claimed_by_established_skills() -> None:
    """An in-progress skill may record its candidate source; a promoted one may not."""
    registry = json.loads((ROOT / "maintainer" / "upstreams" / "registry.json").read_text(encoding="utf-8"))
    current = json.loads((ROOT / "maintainer" / "upstreams" / "provenance" / "current-skills.json").read_text(encoding="utf-8"))
    candidate_ids = {
        source["id"] for source in registry["sources"] if source.get("lifecycle") == "candidate"
    }
    assert candidate_ids, "expected candidate relationships during integration phases"
    for item in current["skills"]:
        overlap = candidate_ids & set(item.get("sources", []))
        if overlap:
            assert item.get("lifecycle") == "candidate", (
                f"established skill {item['name']} claims unpromoted sources {sorted(overlap)}"
            )


def test_established_skill_claiming_candidate_source_is_blocked() -> None:
    root = ROOT
    current_path = root / "maintainer" / "upstreams" / "provenance" / "current-skills.json"
    backup = current_path.read_bytes()
    try:
        doc = json.loads(backup.decode("utf-8"))
        for item in doc["skills"]:
            if item["name"] == "ui-ux-pro-max":
                item.pop("lifecycle", None)
        current_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        errors: list[str] = []
        validate_registry.validate_registry(root, errors)
        assert any("must not declare an unpromoted candidate source" in item for item in errors), errors
    finally:
        current_path.write_bytes(backup)
    errors = []
    validate_registry.validate_registry(root, errors)
    assert errors == [], "\n".join(errors)


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


def test_protected_asset_path_variants_are_classified() -> None:
    protected_paths = [
        "skills/demo/assets/icon.svg",
        "skills\\demo\\ASSETS\\icon.svg",
        "skills/demo/asset/icon.svg",
        "skills/demo/examples/sample.md",
        "skills/demo/example/sample.md",
        "skills/demo/templates/report.md",
        "skills/demo/template/report.md",
        "skills/demo/scripts/check.py",
        "skills/demo/script/check.py",
        "skills/demo/evals/evals.json",
        "skills/demo/eval/evals.json",
        "skills/demo/template.md",
        "template.md",
        "skills/demo/LICENSE",
        "skills/demo/NOTICE.txt",
    ]
    for path in protected_paths:
        assert is_protected_asset_path(path), path

    ordinary_paths = [
        "skills/demo/SKILL.md",
        "skills/demo/references.md",
        "skills/demo/template.md.bak",
        "skills/demo/assets-old/icon.svg",
        "skills/demo/examples-old/sample.md",
    ]
    for path in ordinary_paths:
        assert not is_protected_asset_path(path), path


def test_destructive_requires_destructive_approval() -> None:
    candidate = FIXTURES / "destructive-candidate.json"
    run([str(SCRIPTS / "stage_upstream.py"), "--candidate", str(candidate)])
    run([
        str(SCRIPTS / "promote_upstream.py"),
        "--candidate-id",
        "destructive-change",
        "--approval-id",
        "APPROVAL-GENERAL",
        "--asset-approval-id",
        "APPROVAL-ASSET",
    ], expect=2)
    run([
        str(SCRIPTS / "promote_upstream.py"),
        "--candidate-id",
        "destructive-change",
        "--approval-id",
        "APPROVAL-GENERAL",
        "--asset-approval-id",
        "APPROVAL-ASSET",
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
        test_check_observes_only_exact_watched_paths,
        test_check_source_filter_is_exact,
        test_latest_stable_release_does_not_depend_on_api_order,
        test_check_date_override_is_deterministic,
        test_partial_watched_path_errors_preserve_previous_observations,
        test_actual_tree_hashes_and_post_stage_mutation_block,
        test_public_scripts_have_real_help,
        test_imported_status_check_is_prose_language_neutral,
        test_external_relationships_and_behavior_contracts_are_consistent,
        test_relationship_group_accepts_matched_pair,
        test_relationship_group_blocks_sha_drift,
        test_relationship_group_blocks_partial_promotion,
        test_relationship_group_blocks_license_and_repository_split,
        test_reference_relationship_stays_out_of_packaging,
        test_canonical_skill_count_is_derived_not_hardcoded,
        test_candidate_sources_are_not_claimed_by_established_skills,
        test_established_skill_claiming_candidate_source_is_blocked,
        test_self_update_blocks_same_session,
        test_protected_asset_requires_asset_approval,
        test_protected_asset_path_variants_are_classified,
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
