#!/usr/bin/env python3
"""Failure/safety evals for skill-portfolio-maintainer."""

from __future__ import annotations

import copy
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
    assert report["behavior_contract_validation"] == "passed"
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


def _behavior_fixture() -> tuple[dict, dict, dict]:
    registry = json.loads((ROOT / "maintainer" / "upstreams" / "registry.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "maintainer" / "upstreams" / "lock.json").read_text(encoding="utf-8"))
    current = json.loads((ROOT / "maintainer" / "upstreams" / "provenance" / "current-skills.json").read_text(encoding="utf-8"))
    return registry, lock, current


def test_behavior_sources_route_only_through_contracts() -> None:
    registry, lock, current = _behavior_fixture()
    source = next(
        item for item in registry["sources"]
        if item["id"] == "openai-codex-commit-behavior"
    )
    source["target"]["local_skills"] = ["commit"]
    errors: list[str] = []
    validate_registry.validate_behavior_contracts(ROOT, registry, lock, current, errors)
    assert any("must not map through target.local_skills" in item for item in errors), errors


def test_behavior_claim_classes_cannot_be_collapsed() -> None:
    registry, lock, current = _behavior_fixture()
    contract = next(item for item in registry["behavior_contracts"] if item["id"] == "commit-workflow")
    contract["claims"] = [
        claim for claim in contract["claims"]
        if claim["claim_class"] != "runtime-observation"
    ]
    errors: list[str] = []
    validate_registry.validate_behavior_contracts(ROOT, registry, lock, current, errors)
    assert any("claims must cover exactly" in item for item in errors), errors


def test_unsupported_product_guarantee_is_blocked() -> None:
    registry, lock, current = _behavior_fixture()
    contract = next(item for item in registry["behavior_contracts"] if item["id"] == "commit-workflow")
    contract["unsupported_guarantees"][0]["status"] = "guaranteed"
    errors: list[str] = []
    validate_registry.validate_behavior_contracts(ROOT, registry, lock, current, errors)
    assert any("must stay explicitly unsupported" in item for item in errors), errors


def test_planned_fixture_cannot_support_a_runtime_result_claim() -> None:
    registry, lock, current = _behavior_fixture()
    contract = next(item for item in registry["behavior_contracts"] if item["id"] == "commit-workflow")
    claim = next(item for item in contract["claims"] if item["claim_class"] == "runtime-observation")
    claim["observation_kind"] = "fixture-result"
    errors: list[str] = []
    validate_registry.validate_behavior_contracts(ROOT, registry, lock, current, errors)
    assert any("fixture-result claim requires observed fixture evidence" in item for item in errors), errors


def test_stale_behavior_evidence_requires_accepted_fallback() -> None:
    registry, lock, current = _behavior_fixture()
    state = next(item for item in lock["states"] if item["id"] == "anthropic-claude-code-commit-behavior")
    state["observed"]["evidence_status"] = "stale"
    state["observed"].pop("stale_fallback", None)
    state["observed"].pop("last_check_attempt_at", None)
    errors: list[str] = []
    validate_registry.validate_behavior_contracts(ROOT, registry, lock, current, errors)
    assert any("stale evidence must preserve accepted state" in item for item in errors), errors


def test_refresh_failure_preserves_accepted_and_marks_stale() -> None:
    registry, lock, _current = _behavior_fixture()
    source = next(
        item for item in registry["sources"]
        if item["id"] == "anthropic-claude-code-commit-behavior"
    )
    state = next(item for item in lock["states"] if item["id"] == source["id"])
    accepted_before = copy.deepcopy(state["accepted"])
    stale = check_upstreams.apply_behavior_refresh_policy(
        source,
        {"status": "error", "error": "fixture timeout"},
        state,
    )
    assert stale["evidence_status"] == "stale"
    assert stale["stale_fallback"]["strategy"] == "preserve-last-accepted-mark-stale"
    check_upstreams.update_observed(lock, source["id"], stale)
    assert state["accepted"] == accepted_before
    assert state["observed"]["evidence_status"] == "stale"
    assert state["observed"]["ref"]
    assert state["observed"]["last_check_attempt_at"]


def test_unchanged_behavior_surfaces_do_not_require_review() -> None:
    registry, lock, _current = _behavior_fixture()
    source = next(
        item for item in registry["sources"]
        if item["id"] == "openai-codex-commit-behavior"
    )
    state = next(item for item in lock["states"] if item["id"] == source["id"])
    observed = copy.deepcopy(state["observed"])
    observed["status"] = "ok"
    result = check_upstreams.apply_behavior_refresh_policy(source, observed, state)
    assert result["evidence_status"] == "fresh"
    assert result["auto_import"] is False
    assert result["semantic_review_required"] is False


def test_behavior_candidates_are_vendor_separated_and_non_importing() -> None:
    registry, _lock, _current = _behavior_fixture()
    errors: list[str] = []
    validate_registry.validate_behavior_candidates(ROOT, registry, errors)
    assert errors == [], "\n".join(errors)
    candidate_paths = []
    for source_id in ("openai-codex-commit-behavior", "anthropic-claude-code-commit-behavior"):
        source = next(item for item in registry["sources"] if item["id"] == source_id)
        path = ROOT / source["provenance"]["classification_evidence_url"]
        candidate = json.loads(path.read_text(encoding="utf-8"))
        candidate_paths.append(path)
        assert candidate["auto_import"] is False
        assert candidate["file_import_allowed"] is False
        assert candidate["runtime_fixture_status"] == "planned"
        assert candidate["runtime_fixture_evidence"] is None
        assert [item["source_id"] for item in candidate["candidate_sources"]] == [source_id]
    assert candidate_paths[0] != candidate_paths[1]


def test_current_commit_consumes_contract_not_behavior_sources() -> None:
    registry, _lock, current = _behavior_fixture()
    commit = next(item for item in current["skills"] if item["name"] == "commit")
    behavior_source_ids = {
        source["id"] for source in registry["sources"]
        if source.get("target", {}).get("behavior_contracts")
    }
    assert commit["behaviors"] == ["commit-workflow"]
    assert behavior_source_ids.isdisjoint(commit.get("sources", []))
    contract = next(item for item in registry["behavior_contracts"] if item["id"] == "commit-workflow")
    runtime_claim = next(item for item in contract["claims"] if item["claim_class"] == "runtime-observation")
    assert runtime_claim["id"] == "runtime-version-observation"
    assert runtime_claim["observation_kind"] == "product-version"
    assert contract["validation"]["runtime_fixtures"][0]["status"] == "planned"
    assert contract["validation"]["runtime_fixtures"][0]["evidence_path"] is None


def test_registry_schema_exposes_behavior_v11() -> None:
    schema = json.loads((ROOT / "maintainer" / "upstreams" / "schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema_version"]["pattern"] == r"^1\.1\.0$"
    assert "behavior_contracts" in schema["properties"]
    assert "behavior_contracts" in schema["$defs"]["source"]["properties"]["target"]["properties"]
    claim_classes = set(schema["$defs"]["behavior_claim"]["properties"]["claim_class"]["enum"])
    assert claim_classes == {"official-documented", "local-policy", "runtime-observation"}


def test_governance_merge_manifest_is_semantically_complete() -> None:
    errors: list[str] = []
    validate_registry.validate_governance_merge_manifest(ROOT, errors)
    assert errors == [], "\n".join(errors)


def test_governance_merge_manifest_rejects_coverage_and_metadata_drift() -> None:
    manifest_path = ROOT / validate_registry.GOVERNANCE_MERGE_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["coverage_summary"]["source_units"] -= 1
    manifest["coverage"][0]["destination_anchor"] = "missing-governance-anchor"
    manifest["source_documents"][0]["byte_count"] += 1
    errors: list[str] = []
    validate_registry.validate_governance_merge_data(
        ROOT,
        manifest,
        errors,
        verify_source_bytes=False,
        check_live_referrers=False,
    )
    assert any("source_units must equal len(coverage)" in item for item in errors), errors
    assert any("destination anchor #missing-governance-anchor does not exist" in item for item in errors), errors
    assert any("byte_count must be" in item for item in errors), errors
    assert any("unmapped_units must be zero" in item for item in errors), errors


def test_governance_merge_manifest_rejects_placeholder_heading_and_missing_table_header() -> None:
    manifest_path = ROOT / validate_registry.GOVERNANCE_MERGE_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    heading = next(unit for unit in manifest["coverage"] if unit["unit_type"] == "heading")
    heading["source_excerpt"] = heading["source_row_or_rule_id"]
    table_row = next(unit for unit in manifest["coverage"] if unit["unit_type"] == "table_row")
    table_row["source_heading"] = "wrong containing heading"
    command = next(unit for unit in manifest["coverage"] if unit["unit_type"] == "command_block")
    command["source_excerpt"] = "command summary placeholder"
    list_rule = next(unit for unit in manifest["coverage"] if unit["unit_type"] == "list_rule")
    evidence_path = next(
        unit
        for unit in manifest["coverage"]
        if unit["source_row_or_rule_id"] == "evidence-path-L015-capabilities"
    )
    manifest["coverage"] = [
        unit
        for unit in manifest["coverage"]
        if unit["source_row_or_rule_id"]
        not in {
            "table-header-L007-mode",
            list_rule["source_row_or_rule_id"],
            evidence_path["source_row_or_rule_id"],
        }
    ]
    manifest["coverage_summary"]["source_units"] = len(manifest["coverage"])
    errors: list[str] = []
    validate_registry.validate_governance_merge_data(
        ROOT,
        manifest,
        errors,
        verify_source_bytes=False,
        check_live_referrers=False,
    )
    assert any("heading source_excerpt must equal the baseline heading" in item for item in errors), errors
    assert any("source_heading must equal the containing baseline heading" in item for item in errors), errors
    assert any("command_block source_excerpt must equal the baseline block" in item for item in errors), errors
    source_path = manifest["source_documents"][0]["source_path"]
    assert any(
        f"{source_path}:7 must have exactly one table_row coverage unit; found 0" in item
        for item in errors
    ), errors
    assert any(
        f"{list_rule['source_path']}:{list_rule['source_line']} must have exactly one list_rule coverage unit; found 0"
        in item
        for item in errors
    ), errors
    assert any(
        f"{evidence_path['source_path']}:{evidence_path['source_line']} evidence path " in item
        and "must have exactly one coverage unit; found 0" in item
        for item in errors
    ), errors


def test_generated_governance_hits_are_allowed_but_canonical_hits_fail() -> None:
    source_path = next(iter(validate_registry.EXPECTED_GOVERNANCE_SOURCE_DOCUMENTS))
    source_name = Path(source_path).name
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / ".user-docs").mkdir()
        destination_path = ".user-docs/Skill_Upstream_Governance.md"
        (root / destination_path).write_text(
            '<a id="migration-appendix"></a>\n',
            encoding="utf-8",
        )
        generated = root / ".agents" / "skills" / "generated.md"
        generated.parent.mkdir(parents=True)
        generated.write_text(f"historical input: {source_name}\n", encoding="utf-8")

        clean_errors: list[str] = []
        validate_registry._validate_live_governance_referrers(
            root,
            {source_path},
            destination_path,
            clean_errors,
        )
        assert clean_errors == [], clean_errors

        (root / "README.md").write_text(f"live policy: {source_name}\n", encoding="utf-8")
        live_errors: list[str] = []
        validate_registry._validate_live_governance_referrers(
            root,
            {source_path},
            destination_path,
            live_errors,
        )
        assert any("live referrer still names" in item for item in live_errors), live_errors


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
    """An in-progress skill may record its candidate source; a promoted one may not.

    Zero candidates is a valid steady state, so this checks the rule rather than
    asserting the repository is mid-integration.
    """
    registry = json.loads((ROOT / "maintainer" / "upstreams" / "registry.json").read_text(encoding="utf-8"))
    current = json.loads((ROOT / "maintainer" / "upstreams" / "provenance" / "current-skills.json").read_text(encoding="utf-8"))
    candidate_ids = {
        source["id"] for source in registry["sources"] if source.get("lifecycle") == "candidate"
    }
    for item in current["skills"]:
        overlap = candidate_ids & set(item.get("sources", []))
        if overlap:
            assert item.get("lifecycle") == "candidate", (
                f"established skill {item['name']} claims unpromoted sources {sorted(overlap)}"
            )


def test_established_skill_claiming_candidate_source_is_blocked() -> None:
    """Demote one active relationship and confirm the guard fires.

    Building the violation instead of relying on live repository state keeps the
    check meaningful once every relationship is promoted.
    """
    registry_path = ROOT / "maintainer" / "upstreams" / "registry.json"
    registry_backup = registry_path.read_bytes()
    try:
        registry = json.loads(registry_backup.decode("utf-8"))
        target = next(
            source for source in registry["sources"]
            if source.get("integration_mode") == "reference"
            and source.get("relationship_group")
            and source.get("lifecycle") == "active"
        )
        group = target["relationship_group"]
        for source in registry["sources"]:
            if source.get("relationship_group") == group:
                source["lifecycle"] = "candidate"
        registry_path.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        errors: list[str] = []
        validate_registry.validate_registry(ROOT, errors)
        assert any("must not declare an unpromoted candidate source" in item for item in errors), errors
    finally:
        registry_path.write_bytes(registry_backup)
    errors = []
    validate_registry.validate_registry(ROOT, errors)
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
    contract_eval = subprocess.run(
        [sys.executable, str(SKILL / "evals" / "artifact_output_contract.py")],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    if contract_eval.returncode != 0:
        raise AssertionError(
            f"artifact output contract eval failed\nSTDOUT:\n{contract_eval.stdout}\nSTDERR:\n{contract_eval.stderr}"
        )
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
        test_behavior_sources_route_only_through_contracts,
        test_behavior_claim_classes_cannot_be_collapsed,
        test_unsupported_product_guarantee_is_blocked,
        test_planned_fixture_cannot_support_a_runtime_result_claim,
        test_stale_behavior_evidence_requires_accepted_fallback,
        test_refresh_failure_preserves_accepted_and_marks_stale,
        test_unchanged_behavior_surfaces_do_not_require_review,
        test_behavior_candidates_are_vendor_separated_and_non_importing,
        test_current_commit_consumes_contract_not_behavior_sources,
        test_registry_schema_exposes_behavior_v11,
        test_governance_merge_manifest_is_semantically_complete,
        test_governance_merge_manifest_rejects_coverage_and_metadata_drift,
        test_governance_merge_manifest_rejects_placeholder_heading_and_missing_table_header,
        test_generated_governance_hits_are_allowed_but_canonical_hits_fail,
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
