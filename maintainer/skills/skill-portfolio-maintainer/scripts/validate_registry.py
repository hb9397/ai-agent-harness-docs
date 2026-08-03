#!/usr/bin/env python3
"""Validate upstream registry, lock, and skill provenance docs."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MODES = {"native", "reference", "vendored", "adapted", "unknown"}
SOURCE_CLASSES = {"internal", "official", "reputable-third-party", "community", "standard", "unknown"}
LIFECYCLES = {"candidate", "active", "blocked", "deprecated"}
CLAIM_CLASSES = {"official-documented", "local-policy", "runtime-observation"}
BEHAVIOR_EVIDENCE_STATUSES = {"fresh", "stale", "unverified"}
STALE_FALLBACK = "preserve-last-accepted-mark-stale"
SCHEMA_VERSION = "1.1.0"
GOVERNANCE_MERGE_MANIFEST = "maintainer/inventory/upstream-governance-doc-merge.json"
EXPECTED_GOVERNANCE_SOURCE_DOCUMENTS = {
    ".user-docs/Skill_Upstream_Update_Policy.md": {
        "source_sha256": "4ed6fc34f525b8a8c557fdde52984e5af7eed98a0e6eccd7473a7ff227dc60cb",
        "title": "스킬 업스트림 업데이트 정책",
        "line_count": 105,
        "byte_count": 5520,
    },
    ".user-docs/Imported_Skill_Provenance.md": {
        "source_sha256": "0394cd4358efd4071d183166dc1ea5cb162f4452d948b9b7aa66aaa71e475376",
        "title": "반입 스킬 출처 추적",
        "line_count": 125,
        "byte_count": 10142,
    },
    ".user-docs/External_Skill_References.md": {
        "source_sha256": "7058a8e2d8ff11dc7d4ab71400f2edf781e3742f6306a3dccf38cbd6bb9b5f64",
        "title": "외부 스킬 참조",
        "line_count": 118,
        "byte_count": 11541,
    },
}
GOVERNANCE_DISPOSITIONS = {"merged", "deduplicated", "historical", "superseded"}
PROTECTED_REQUIRED = {
    "**/scripts/**",
    "**/templates/**",
    "LICENSE*",
    "NOTICE*",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def canonical_skill_counts(root: Path) -> dict[str, int]:
    return {
        "user_skills": sum(
            1 for path in (root / "skills").iterdir() if (path / "SKILL.md").is_file()
        ) if (root / "skills").is_dir() else 0,
        "maintainer_skills": sum(
            1 for path in (root / "maintainer" / "skills").iterdir() if (path / "SKILL.md").is_file()
        ) if (root / "maintainer" / "skills").is_dir() else 0,
    }


def canonical_skill_count(root: Path) -> int:
    """Derive the expected current-skills.json entry count from canonical trees.

    current-skills.json records provenance for every canonical skill, user and
    manager alike. Deriving the number keeps the check correct when skills are
    added or removed instead of requiring a hardcoded edit.
    """
    return sum(canonical_skill_counts(root).values())


def validate_promotion_evidence(root: Path, registry: dict, errors: list[str]) -> None:
    """An active external relationship must carry a promotion record.

    Implementing and packaging a source without recording the approvals leaves
    no evidence that the governance procedure was followed. The code alone
    cannot show that upstream selection, asset impact and licence were approved.
    """
    promotions = root / "maintainer" / "upstreams" / "promotions"
    recorded: set[str] = set()
    for path in sorted(promotions.glob("*.json")):
        data = load_json(path)
        promotion = data.get("promotion", {})
        ids = promotion.get("source_ids") or [promotion.get("source_id")]
        recorded.update(item for item in ids if item)

    for source in registry.get("sources", []):
        sid = source.get("id")
        if not sid or sid == "internal-harness-native":
            continue
        if source.get("lifecycle") != "active":
            continue
        if source.get("integration_mode") not in {"adapted", "vendored"}:
            continue
        if sid not in recorded:
            error(errors, f"{sid}: active direct-import source has no promotion record")

    # A candidate bundle must not still claim work is pending once its sources
    # are active and its skill exists.
    for path in sorted((root / "maintainer" / "upstreams" / "candidates").glob("*/candidate.json")):
        data = load_json(path)
        ids = {item.get("source_id") for item in data.get("candidate_sources", [])}
        lifecycles = {
            source.get("lifecycle")
            for source in registry.get("sources", [])
            if source.get("id") in ids
        }
        if not lifecycles or lifecycles != {"active"}:
            continue
        # Status vocabulary varies across historical bundles, so judge by what
        # the bundle still claims is outstanding rather than by an exact string.
        rel = path.relative_to(root).as_posix()
        status = str(data.get("status", ""))
        if "pending" in status:
            error(errors, f"{rel}: sources are active but candidate status is {status!r}")
        if data.get("pending_approvals"):
            error(errors, f"{rel}: sources are active but approvals are still pending")


def validate_relationship_groups(registry: dict, lock: dict, errors: list[str]) -> None:
    """Keep every relationship derived from one upstream pinned to one commit.

    A single upstream can be tracked as a direct import and as a reference at the
    same time. Those relationships must not drift apart, so the group shares a
    repository, a license determination and a pinned commit.
    """
    lock_by_id = {state.get("id"): state for state in lock.get("states", [])}
    groups: dict[str, list[dict]] = {}
    for source in registry.get("sources", []):
        group = source.get("relationship_group")
        if group:
            groups.setdefault(group, []).append(source)

    for group, sources in sorted(groups.items()):
        if len(sources) < 2:
            error(errors, f"relationship group {group}: needs at least two relationships")
            continue

        for field, label in (("repository", "upstream.repository"), ("source_url", "upstream.source_url")):
            values = {source.get("upstream", {}).get(field) for source in sources}
            if len(values) != 1:
                error(errors, f"relationship group {group}: {label} must match across the group, got {sorted(map(str, values))}")

        licenses = {source.get("provenance", {}).get("license_spdx") for source in sources}
        if len(licenses) != 1:
            error(errors, f"relationship group {group}: license_spdx must match across the group, got {sorted(map(str, licenses))}")

        lifecycles = {source.get("lifecycle") for source in sources}
        if len(lifecycles) != 1:
            error(errors, f"relationship group {group}: lifecycle must be promoted atomically, got {sorted(map(str, lifecycles))}")

        for key in ("observed", "accepted"):
            shas = set()
            for source in sources:
                state = lock_by_id.get(source.get("id"))
                entry = (state or {}).get(key)
                shas.add(entry.get("sha") if isinstance(entry, dict) else None)
            if len(shas) != 1:
                error(errors, f"relationship group {group}: {key} sha must match across the group, got {sorted(map(str, shas))}")

        modes = [source.get("integration_mode") for source in sources]
        if "reference" not in modes:
            error(errors, f"relationship group {group}: expected at least one reference relationship")
        for source in sources:
            if source.get("integration_mode") != "reference":
                continue
            provenance = source.get("provenance", {})
            if provenance.get("notice_path"):
                error(errors, f"{source.get('id')}: reference relationship must not claim a packaged notice_path")
            for entry in provenance.get("file_map", []):
                if entry.get("treatment") != "reference-only":
                    error(errors, f"{source.get('id')}: reference relationship file_map must stay reference-only")


def validate_behavior_candidates(
    root: Path,
    registry: dict,
    errors: list[str],
    lock: dict | None = None,
) -> None:
    """Behavior references stay in vendor-specific, non-importing review bundles."""
    sources = {
        source.get("id"): source
        for source in registry.get("sources", [])
        if source.get("target", {}).get("behavior_contracts")
    }
    candidate_by_source: dict[str, Path] = {}
    for source_id, source in sources.items():
        evidence = source.get("provenance", {}).get("classification_evidence_url", "")
        if not isinstance(evidence, str) or not evidence.startswith("maintainer/upstreams/candidates/"):
            continue
        path = root / evidence
        if not path.is_file():
            error(errors, f"{source_id}: behavior candidate evidence is missing: {evidence}")
            continue
        data = load_json(path)
        candidate_sources = data.get("candidate_sources", []) if isinstance(data, dict) else []
        ids = [item.get("source_id") for item in candidate_sources if isinstance(item, dict)]
        if ids != [source_id]:
            error(errors, f"{path.relative_to(root).as_posix()}: behavior candidate must contain only {source_id}, got {ids}")
        if data.get("auto_import") is not False or data.get("file_import_allowed") is not False:
            error(errors, f"{source_id}: behavior candidate must explicitly prohibit automatic and file import")
        if data.get("relationship_group") is not None:
            error(errors, f"{source_id}: behavior candidate must not join a relationship_group")
        if data.get("stale_fallback") != STALE_FALLBACK:
            error(errors, f"{source_id}: behavior candidate missing stale fallback {STALE_FALLBACK}")
        if data.get("runtime_fixture_status") != "planned" or data.get("runtime_fixture_evidence") is not None:
            error(errors, f"{source_id}: Phase 1 behavior candidate must keep product fixture evidence planned and empty")
        if not candidate_sources or not candidate_sources[0].get("runtime_observation_scope"):
            error(errors, f"{source_id}: candidate must scope runtime observation to available evidence")
        declared_surface_ids = {
            item.get("id") for item in source.get("upstream", {}).get("watched_surfaces", [])
            if isinstance(item, dict)
        }
        candidate_surfaces = {
            item.get("id"): item.get("normalized_sha256")
            for item in data.get("watched_surfaces", [])
            if isinstance(item, dict) and item.get("id")
        }
        if set(candidate_surfaces) != declared_surface_ids:
            error(errors, f"{source_id}: candidate watched surfaces do not match registry declarations")
        for surface_id, content_hash in candidate_surfaces.items():
            if not SHA256_RE.match(str(content_hash or "")):
                error(errors, f"{source_id}/{surface_id}: candidate surface hash must be 64 lowercase hex chars")
        if isinstance(lock, dict):
            state = next((item for item in lock.get("states", []) if item.get("id") == source_id), {})
            accepted_surfaces = {
                item.get("id"): item.get("content_sha256")
                for item in (state.get("accepted") or {}).get("watched_surfaces", [])
                if isinstance(item, dict) and item.get("id")
            }
            if candidate_surfaces != accepted_surfaces:
                error(errors, f"{source_id}: candidate hashes do not match accepted lock evidence")
        candidate_by_source[source_id] = path

    openai_id = "openai-codex-commit-behavior"
    anthropic_id = "anthropic-claude-code-commit-behavior"
    if openai_id in sources and anthropic_id in sources:
        if candidate_by_source.get(openai_id) == candidate_by_source.get(anthropic_id):
            error(errors, "OpenAI and Anthropic commit behavior sources must use separate candidates")
        groups = {sources[openai_id].get("relationship_group"), sources[anthropic_id].get("relationship_group")}
        groups.discard(None)
        if groups:
            error(errors, "OpenAI and Anthropic commit behavior sources must not share a relationship_group")


def validate_behavior_contracts(
    root: Path,
    registry: dict,
    lock: dict,
    current: dict,
    errors: list[str],
) -> None:
    source_by_id = {
        source.get("id"): source
        for source in registry.get("sources", [])
        if isinstance(source, dict) and source.get("id")
    }
    lock_by_id = {
        state.get("id"): state
        for state in lock.get("states", [])
        if isinstance(state, dict) and state.get("id")
    }
    current_by_name = {
        item.get("name"): item
        for item in current.get("skills", [])
        if isinstance(item, dict) and item.get("name")
    }
    contract_lock_by_id = {
        state.get("id"): state
        for state in lock.get("behavior_contracts", [])
        if isinstance(state, dict) and state.get("id")
    }

    contracts: dict[str, dict] = {}
    for contract in registry.get("behavior_contracts", []):
        contract_id = contract.get("id") if isinstance(contract, dict) else None
        if not contract_id:
            error(errors, "behavior contract missing id")
            continue
        if contract_id in contracts:
            error(errors, f"duplicate behavior contract id: {contract_id}")
            continue
        contracts[contract_id] = contract

    behavior_sources_by_contract: dict[str, set[str]] = {contract_id: set() for contract_id in contracts}
    behavior_source_status: dict[str, str] = {}
    for source_id, source in source_by_id.items():
        target = source.get("target", {})
        contract_ids = target.get("behavior_contracts", [])
        if not contract_ids:
            continue
        if target.get("local_skills"):
            error(errors, f"{source_id}: behavior-only source must not map through target.local_skills")
        if source.get("integration_mode") != "reference":
            error(errors, f"{source_id}: behavior-only source must remain reference mode")
        provenance = source.get("provenance", {})
        for file_map in provenance.get("file_map", []):
            if file_map.get("treatment") != "reference-only" or file_map.get("local_path") is not None:
                error(errors, f"{source_id}: behavior-only source must not map an upstream file to a local path")
        refresh = source.get("refresh_policy", {})
        if refresh.get("strategy") != "observe-and-review":
            error(errors, f"{source_id}: behavior source refresh strategy must be observe-and-review")
        if refresh.get("auto_import") is not False or refresh.get("review_on_change") is not True:
            error(errors, f"{source_id}: behavior source changes must require review and never auto-import")
        if refresh.get("stale_fallback") != STALE_FALLBACK:
            error(errors, f"{source_id}: behavior source stale fallback must be {STALE_FALLBACK}")
        if not isinstance(refresh.get("stale_after_days"), int) or refresh.get("stale_after_days", 0) < 1:
            error(errors, f"{source_id}: behavior source stale_after_days must be positive")

        watched_surfaces = source.get("upstream", {}).get("watched_surfaces", [])
        surface_ids = [item.get("id") for item in watched_surfaces if isinstance(item, dict)]
        if not surface_ids or len(surface_ids) != len(set(surface_ids)):
            error(errors, f"{source_id}: behavior source watched surfaces must be non-empty and unique")
        for surface in watched_surfaces:
            if not isinstance(surface, dict):
                error(errors, f"{source_id}: watched surface entries must be objects")
                continue
            if not str(surface.get("url", "")).startswith("https://") or not surface.get("change_signals"):
                error(errors, f"{source_id}/{surface.get('id')}: watched surface needs an https URL and change signals")
        declared_paths = set(source.get("upstream", {}).get("watched_paths", []))
        state = lock_by_id.get(source_id)
        if not isinstance(state, dict):
            error(errors, f"{source_id}: behavior source missing lock state")
        else:
            observed = state.get("observed")
            accepted = state.get("accepted")
            if not isinstance(accepted, dict):
                error(errors, f"{source_id}: behavior source requires a last accepted observation for stale fallback")
            if not isinstance(observed, dict):
                error(errors, f"{source_id}: behavior source requires an observed lock entry")
            else:
                evidence_status = observed.get("evidence_status")
                behavior_source_status[source_id] = evidence_status
                if evidence_status not in BEHAVIOR_EVIDENCE_STATUSES:
                    error(errors, f"{source_id}: invalid behavior evidence_status {evidence_status}")
                if not observed.get("checked_at") or not observed.get("ref"):
                    error(errors, f"{source_id}: observed behavior evidence requires checked_at and ref")
                expected_version = refresh.get("observed_product_version")
                if expected_version is not None and observed.get("product_version") != expected_version:
                    error(errors, f"{source_id}: observed product version does not match registry refresh metadata")
                observed_surface_ids = {
                    item.get("id") for item in observed.get("watched_surfaces", []) if isinstance(item, dict)
                }
                if set(surface_ids) != observed_surface_ids:
                    error(errors, f"{source_id}: observed watched surfaces do not match registry declarations")
                observed_paths = {
                    item.get("path") for item in observed.get("watched_paths", []) if isinstance(item, dict)
                }
                if declared_paths != observed_paths:
                    error(errors, f"{source_id}: observed watched paths do not match registry declarations")
                if evidence_status == "stale":
                    fallback = observed.get("stale_fallback", {})
                    if fallback.get("strategy") != STALE_FALLBACK or not observed.get("last_check_attempt_at"):
                        error(errors, f"{source_id}: stale evidence must preserve accepted state and record the failed check")
                else:
                    for surface in observed.get("watched_surfaces", []):
                        if surface.get("status") != "ok" or not SHA256_RE.match(str(surface.get("content_sha256", ""))):
                            error(errors, f"{source_id}: fresh watched surface evidence requires an ok 64-hex content hash")
            if isinstance(accepted, dict):
                if accepted.get("evidence_status") not in {"fresh", "unverified"}:
                    error(errors, f"{source_id}: accepted behavior evidence has invalid status")
                accepted_surface_ids = {
                    item.get("id") for item in accepted.get("watched_surfaces", []) if isinstance(item, dict)
                }
                if set(surface_ids) != accepted_surface_ids:
                    error(errors, f"{source_id}: accepted watched surfaces do not match registry declarations")
                for surface in accepted.get("watched_surfaces", []):
                    if not SHA256_RE.match(str(surface.get("content_sha256", ""))):
                        error(errors, f"{source_id}: accepted watched surface evidence requires a 64-hex content hash")
                accepted_paths = {
                    item.get("path") for item in accepted.get("watched_paths", []) if isinstance(item, dict)
                }
                if declared_paths != accepted_paths:
                    error(errors, f"{source_id}: accepted watched paths do not match registry declarations")
            for evidence_state in ("embedded", "packaged", "released"):
                if state.get(evidence_state) is not None:
                    error(errors, f"{source_id}: behavior-only source must not claim {evidence_state} content")

        for contract_id in contract_ids:
            if contract_id not in contracts:
                error(errors, f"{source_id}: unknown target behavior contract {contract_id}")
                continue
            behavior_sources_by_contract[contract_id].add(source_id)

    for contract_id, contract in contracts.items():
        if contract.get("lifecycle") not in LIFECYCLES:
            error(errors, f"{contract_id}: invalid behavior contract lifecycle {contract.get('lifecycle')}")
        consumers = contract.get("consumers", {})
        consumer_skills = consumers.get("skills", [])
        if not consumer_skills:
            error(errors, f"{contract_id}: behavior contract requires at least one skill consumer")
        for skill_name in consumer_skills:
            item = current_by_name.get(skill_name)
            if item is None:
                error(errors, f"{contract_id}: consumer skill missing from current-skills.json: {skill_name}")
            elif contract_id not in item.get("behaviors", []):
                error(errors, f"{contract_id}: consumer {skill_name} does not declare the behavior contract")
        if not consumers.get("docs") or not consumers.get("validators"):
            error(errors, f"{contract_id}: behavior contract requires doc and validator consumers")

        claim_ids: set[str] = set()
        claim_classes: set[str] = set()
        claimed_source_ids: set[str] = set()
        runtime_fixtures = contract.get("validation", {}).get("runtime_fixtures", [])
        observed_fixture_evidence = [
            fixture for fixture in runtime_fixtures
            if isinstance(fixture, dict)
            and fixture.get("status") == "observed"
            and isinstance(fixture.get("evidence_path"), str)
            and fixture.get("evidence_path")
        ]
        for claim in contract.get("claims", []):
            claim_id = claim.get("id")
            claim_class = claim.get("claim_class")
            source_ids = claim.get("source_ids", [])
            if not claim_id or claim_id in claim_ids:
                error(errors, f"{contract_id}: behavior claim ids must be present and unique")
            if claim_id:
                claim_ids.add(claim_id)
            if claim_class not in CLAIM_CLASSES:
                error(errors, f"{contract_id}/{claim_id}: invalid claim class {claim_class}")
                continue
            claim_classes.add(claim_class)
            if claim_class == "local-policy" and source_ids:
                error(errors, f"{contract_id}/{claim_id}: local-policy claims must not cite an upstream source")
            if claim_class in {"official-documented", "runtime-observation"} and not source_ids:
                error(errors, f"{contract_id}/{claim_id}: {claim_class} claims require source evidence")
            observation_kind = claim.get("observation_kind")
            if claim_class == "runtime-observation":
                if observation_kind not in {"product-version", "fixture-result"}:
                    error(errors, f"{contract_id}/{claim_id}: runtime observation requires a supported observation_kind")
                if observation_kind == "fixture-result" and not observed_fixture_evidence:
                    error(errors, f"{contract_id}/{claim_id}: fixture-result claim requires observed fixture evidence")
            elif observation_kind is not None:
                error(errors, f"{contract_id}/{claim_id}: only runtime-observation claims may set observation_kind")
            for source_id in source_ids:
                source = source_by_id.get(source_id)
                if source is None:
                    error(errors, f"{contract_id}/{claim_id}: unknown source id {source_id}")
                    continue
                if contract_id not in source.get("target", {}).get("behavior_contracts", []):
                    error(errors, f"{contract_id}/{claim_id}: source {source_id} does not target the contract")
                if claim_class == "official-documented" and source.get("source_class") not in {"official", "standard"}:
                    error(errors, f"{contract_id}/{claim_id}: official-documented claim cites non-official source {source_id}")
                if claim_class == "runtime-observation":
                    observed = (lock_by_id.get(source_id) or {}).get("observed", {})
                    if not observed.get("product_version"):
                        error(errors, f"{contract_id}/{claim_id}: runtime observation source {source_id} lacks product version")
                claimed_source_ids.add(source_id)
        if claim_classes != CLAIM_CLASSES:
            error(errors, f"{contract_id}: claims must cover exactly {sorted(CLAIM_CLASSES)}, got {sorted(claim_classes)}")
        missing_claim_sources = behavior_sources_by_contract.get(contract_id, set()) - claimed_source_ids
        if missing_claim_sources:
            error(errors, f"{contract_id}: behavior sources lack a contract claim: {sorted(missing_claim_sources)}")

        unsupported_ids: set[str] = set()
        for guarantee in contract.get("unsupported_guarantees", []):
            guarantee_id = guarantee.get("id")
            if not guarantee_id or guarantee_id in unsupported_ids:
                error(errors, f"{contract_id}: unsupported guarantee ids must be present and unique")
            if guarantee_id:
                unsupported_ids.add(guarantee_id)
            if guarantee.get("status") != "unsupported" or not guarantee.get("summary"):
                error(errors, f"{contract_id}/{guarantee_id}: unsupported guarantee must stay explicitly unsupported")
        if not unsupported_ids:
            error(errors, f"{contract_id}: contract must enumerate unsupported guarantees")

        refresh = contract.get("refresh_policy", {})
        if refresh.get("strategy") != "manual-semantic-review" or refresh.get("auto_import") is not False:
            error(errors, f"{contract_id}: contract refresh must be manual and non-importing")
        if refresh.get("stale_fallback") != STALE_FALLBACK:
            error(errors, f"{contract_id}: contract stale fallback must be {STALE_FALLBACK}")
        if not refresh.get("review_triggers"):
            error(errors, f"{contract_id}: contract refresh requires review triggers")

        fixture_ids: set[str] = set()
        for fixture in runtime_fixtures:
            if not isinstance(fixture, dict):
                error(errors, f"{contract_id}: runtime fixture entries must be objects")
                continue
            fixture_id = fixture.get("id")
            status = fixture.get("status")
            evidence_path = fixture.get("evidence_path")
            if not fixture_id or fixture_id in fixture_ids:
                error(errors, f"{contract_id}: runtime fixture ids must be present and unique")
            if fixture_id:
                fixture_ids.add(fixture_id)
            if status not in {"planned", "observed"}:
                error(errors, f"{contract_id}/{fixture_id}: invalid runtime fixture status {status}")
            if status == "planned" and evidence_path is not None:
                error(errors, f"{contract_id}/{fixture_id}: planned fixture must not claim evidence")
            if status == "observed":
                if not isinstance(evidence_path, str) or not evidence_path or not (root / evidence_path).is_file():
                    error(errors, f"{contract_id}/{fixture_id}: observed fixture requires an existing evidence file")
            if not fixture.get("platforms") or not fixture.get("claim_scope"):
                error(errors, f"{contract_id}/{fixture_id}: runtime fixture needs platforms and claim scope")

        contract_state = contract_lock_by_id.get(contract_id)
        expected_sources = behavior_sources_by_contract.get(contract_id, set())
        if not isinstance(contract_state, dict):
            error(errors, f"{contract_id}: behavior contract missing lock state")
        else:
            if set(contract_state.get("source_ids", [])) != expected_sources:
                error(errors, f"{contract_id}: lock source_ids do not match source-to-contract targets")
            if set(contract_state.get("consumer_skills", [])) != set(consumer_skills):
                error(errors, f"{contract_id}: lock consumers do not match contract consumers")
            if contract_state.get("evidence_status") not in BEHAVIOR_EVIDENCE_STATUSES:
                error(errors, f"{contract_id}: lock evidence status is invalid")
            source_statuses = {
                behavior_source_status.get(source_id, "unverified")
                for source_id in expected_sources
            }
            expected_contract_status = (
                "stale" if "stale" in source_statuses
                else "fresh" if source_statuses == {"fresh"}
                else "unverified"
            )
            if contract_state.get("evidence_status") != expected_contract_status:
                error(errors, f"{contract_id}: lock evidence status must derive as {expected_contract_status}")
            if contract_state.get("unsupported_guarantees_verified") is not True:
                error(errors, f"{contract_id}: lock must record unsupported-guarantee verification")
            locked_fixtures = {
                item.get("id"): (item.get("status"), item.get("evidence_path"))
                for item in contract_state.get("runtime_fixtures", [])
                if isinstance(item, dict) and item.get("id")
            }
            declared_fixtures = {
                item.get("id"): (item.get("status"), item.get("evidence_path"))
                for item in runtime_fixtures
                if isinstance(item, dict) and item.get("id")
            }
            if locked_fixtures != declared_fixtures:
                error(errors, f"{contract_id}: lock runtime fixture status does not match the contract")

    for skill_name, item in current_by_name.items():
        for contract_id in item.get("behaviors", []):
            contract = contracts.get(contract_id)
            if contract is None:
                error(errors, f"{skill_name}: unknown behavior contract {contract_id}")
            elif skill_name not in contract.get("consumers", {}).get("skills", []):
                error(errors, f"{skill_name}: behavior contract {contract_id} does not declare the skill as a consumer")

    validate_behavior_candidates(root, registry, errors, lock)


def validate_registry(root: Path, errors: list[str]) -> None:
    registry_path = root / "maintainer" / "upstreams" / "registry.json"
    lock_path = root / "maintainer" / "upstreams" / "lock.json"
    current_path = root / "maintainer" / "upstreams" / "provenance" / "current-skills.json"

    registry = load_json(registry_path)
    lock = load_json(lock_path)
    current = load_json(current_path)

    if not isinstance(registry, dict) or not isinstance(registry.get("sources"), list):
        error(errors, "registry.json must contain sources[]")
        return
    for label, value in (("registry.json", registry), ("lock.json", lock), ("current-skills.json", current)):
        if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
            actual = value.get("schema_version") if isinstance(value, dict) else None
            error(errors, f"{label} schema_version must be {SCHEMA_VERSION}, got {actual}")
    if not isinstance(registry.get("behavior_contracts"), list) or not registry.get("behavior_contracts"):
        error(errors, "registry.json must contain behavior_contracts[]")

    source_ids: set[str] = set()
    for source in registry["sources"]:
        sid = source.get("id")
        if not sid:
            error(errors, "source missing id")
            continue
        if sid in source_ids:
            error(errors, f"duplicate source id: {sid}")
        source_ids.add(sid)

        if source.get("source_class") not in SOURCE_CLASSES:
            error(errors, f"{sid}: invalid source_class {source.get('source_class')}")
        mode = source.get("integration_mode")
        if mode not in MODES:
            error(errors, f"{sid}: invalid integration_mode {mode}")
        if source.get("lifecycle") not in LIFECYCLES:
            error(errors, f"{sid}: invalid lifecycle {source.get('lifecycle')}")

        policy = source.get("policy", {})
        for key in ("channel", "pin", "apply", "deletion", "license_change"):
            if key not in policy:
                error(errors, f"{sid}: policy missing {key}")

        protected = set(source.get("protection", {}).get("protected_globs", []))
        if not protected:
            error(errors, f"{sid}: protection.protected_globs missing")
        if mode in {"vendored", "adapted"} and not PROTECTED_REQUIRED.issubset(protected):
            error(errors, f"{sid}: vendored/adapted source missing required protected globs")

        provenance = source.get("provenance", {})
        if not provenance.get("classification_evidence_url"):
            error(errors, f"{sid}: missing classification evidence")
        if not provenance.get("classification_checked_at"):
            error(errors, f"{sid}: missing classification checked date")

        if mode in {"vendored", "adapted"}:
            if not provenance.get("license_spdx"):
                error(errors, f"{sid}: direct import missing license_spdx")
            if not provenance.get("license_url"):
                error(errors, f"{sid}: direct import missing license_url")
            license_sha = provenance.get("license_sha256")
            if not isinstance(license_sha, str) or not SHA256_RE.match(license_sha):
                error(errors, f"{sid}: direct import license_sha256 must be 64 lowercase hex chars")
            if not provenance.get("notice_path"):
                error(errors, f"{sid}: direct import missing notice_path")

    if not isinstance(lock, dict) or not isinstance(lock.get("states"), list):
        error(errors, "lock.json must contain states[]")
        return
    lock_ids = {state.get("id") for state in lock["states"]}
    for sid in source_ids:
        if sid != "internal-harness-native" and sid not in lock_ids:
            error(errors, f"{sid}: missing lock state")
    for state in lock["states"]:
        observed = state.get("observed")
        if observed and observed.get("sha") is not None and not SHA_RE.match(observed["sha"]):
            error(errors, f"{state.get('id')}: observed sha must be 40 lowercase hex chars")

    skills = current.get("skills", []) if isinstance(current, dict) else []
    candidates = current.get("candidates", []) if isinstance(current, dict) else []
    expected_skills = canonical_skill_count(root)
    if len(skills) != expected_skills:
        error(
            errors,
            f"current-skills.json must describe {expected_skills} current skills "
            f"(user + manager canonical directories), got {len(skills)}",
        )
    expected_counts = canonical_skill_counts(root)
    recorded_counts = current.get("counts", {}) if isinstance(current, dict) else {}
    for field, expected in expected_counts.items():
        if recorded_counts.get(field) != expected:
            error(errors, f"current-skills.json counts.{field} must be derived as {expected}, got {recorded_counts.get(field)}")
    if recorded_counts.get("candidate_skills") != len(candidates):
        error(errors, "current-skills.json counts.candidate_skills must match candidates[]")
    if candidates:
        error(errors, f"current-skills.json must not keep candidates after Phase 4 promotion, got {len(candidates)}")
    humanize = next((item for item in skills if item.get("name") == "humanize-korean"), None)
    if not humanize:
        error(errors, "current-skills.json missing promoted humanize-korean skill")
    elif humanize.get("mode") != "adapted" or "im-not-ai" not in humanize.get("sources", []):
        error(errors, "humanize-korean must be adapted from im-not-ai")
    for item in skills + candidates:
        for sid in item.get("sources", []):
            if sid not in source_ids:
                error(errors, f"{item.get('name')}: unknown source id {sid}")
            else:
                source = next((entry for entry in registry["sources"] if entry.get("id") == sid), {})
                if source.get("target", {}).get("behavior_contracts"):
                    error(errors, f"{item.get('name')}: behavior-only source {sid} must not appear in current-skills sources")

    # External relationships are declared twice for different consumers:
    # registry.json routes an upstream to local targets, while current-skills.json
    # explains each local skill's provenance. Keep both views exact. The local
    # internal-harness-native authorship record is intentionally excluded because
    # current-skills records the strongest external relationship for a skill.
    current_by_name = {
        item.get("name"): item
        for item in skills
        if isinstance(item, dict) and item.get("name")
    }
    # Candidate sources describe planned relationships. Their targets may not
    # exist as canonical skills yet, and existing skills must not claim them
    # before promotion, so candidates are checked against a candidate bundle
    # instead of the current-skills provenance view.
    targets_by_source: dict[str, set[str]] = {}
    candidate_ids: set[str] = set()
    for source in registry["sources"]:
        sid = source.get("id")
        if not sid or sid == "internal-harness-native":
            continue
        targets = set(source.get("target", {}).get("local_skills", []))
        if source.get("lifecycle") == "candidate":
            candidate_ids.add(sid)
            evidence = source.get("provenance", {}).get("classification_evidence_url", "")
            bundle = root / evidence if evidence and not evidence.startswith("http") else None
            if bundle is None or not bundle.is_file():
                error(errors, f"{sid}: candidate source must point to a candidate or provenance bundle")
            # A skill being built from this candidate may record it, but only
            # while the skill itself is still marked candidate. An established
            # skill claiming an unpromoted source would misreport provenance.
            for skill_name in targets:
                item = current_by_name.get(skill_name)
                if item is None or sid not in item.get("sources", []):
                    continue
                if item.get("lifecycle") != "candidate":
                    error(
                        errors,
                        f"{sid}: established skill {skill_name} must not declare an unpromoted candidate source",
                    )
            continue
        targets_by_source[sid] = targets
        for skill_name in targets:
            item = current_by_name.get(skill_name)
            if item is None:
                error(errors, f"{sid}: target skill missing from current-skills.json: {skill_name}")
            elif sid not in item.get("sources", []):
                error(
                    errors,
                    f"{sid}: target {skill_name} does not declare the source in current-skills.json",
                )

    for skill_name, item in current_by_name.items():
        for sid in item.get("sources", []):
            if sid == "internal-harness-native":
                continue
            if sid in candidate_ids:
                continue
            if skill_name not in targets_by_source.get(sid, set()):
                error(
                    errors,
                    f"{skill_name}: source {sid} does not target the skill in registry.json",
                )

    validate_behavior_contracts(root, registry, lock, current, errors)
    validate_relationship_groups(registry, lock, errors)
    validate_promotion_evidence(root, registry, errors)

    for sid in ("superpowers", "gstack", "openai-codex-skill-creator"):
        source = next((item for item in registry["sources"] if item.get("id") == sid), None)
        if source is None:
            continue
        validation = source.get("validation", {})
        for field in ("behavior_fixtures", "codex_smoke_prompts", "claude_smoke_prompts"):
            if not validation.get(field):
                error(errors, f"{sid}: validation.{field} must declare semantic behavior coverage")


def has_accepted_adapted_status(text: str) -> bool:
    return bool(
        re.search(
            r"(?:`accepted`|accepted)\s+(?:`adapted`|adapted)",
            text,
            flags=re.IGNORECASE,
        )
    )


def _source_document_bytes_from_worktree_or_history(
    root: Path,
    relative: str,
    expected_sha256: str,
) -> bytes | None:
    """Read a migration source without requiring its deleted path to stay live.

    Before consolidation, the working-tree file is authoritative. After the
    approved deletion, Git history is the evidence carrier. A fixed manifest
    hash remains the final baseline when a shallow/source archive has no old
    blob, so absence alone is not an error.
    """
    path = root / relative
    if path.is_file():
        return path.read_bytes()

    revisions: list[str] = ["HEAD"]
    try:
        completed = subprocess.run(
            ["git", "log", "--all", "--format=%H", "--", relative],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError:
        return None
    if completed.returncode == 0:
        revisions.extend(line.strip() for line in completed.stdout.splitlines() if line.strip())

    seen: set[str] = set()
    for revision in revisions:
        if revision in seen:
            continue
        seen.add(revision)
        try:
            blob = subprocess.run(
                ["git", "show", f"{revision}:{relative}"],
                cwd=root,
                check=False,
                capture_output=True,
            )
        except OSError:
            return None
        if blob.returncode == 0 and hashlib.sha256(blob.stdout).hexdigest() == expected_sha256:
            return blob.stdout
    return None


def _validate_live_governance_referrers(
    root: Path,
    source_paths: set[str],
    destination_path: str,
    errors: list[str],
) -> None:
    """Reject live references to the three superseded governance documents."""
    excluded = {
        *source_paths,
        destination_path,
        GOVERNANCE_MERGE_MANIFEST,
        "maintainer/skills/skill-portfolio-maintainer/scripts/validate_registry.py",
    }
    searchable_suffixes = {".md", ".json", ".py", ".txt", ".yaml", ".yml"}
    tokens = source_paths | {Path(path).name for path in source_paths}
    candidates = [root / "README.md", root / "AGENTS.md"]
    for relative_root in (".user-docs", "skills", "maintainer", "example"):
        base = root / relative_root
        if base.is_dir():
            candidates.extend(base.rglob("*"))

    for path in candidates:
        if not path.is_file() or path.suffix.lower() not in searchable_suffixes:
            continue
        relative = path.relative_to(root).as_posix()
        parts = Path(relative).parts
        is_eval_fixture = "evals" in parts and "fixtures" in parts
        is_historical_audit = relative.startswith(
            (
                "maintainer/upstreams/promotions/",
                "maintainer/upstreams/staging/",
                "maintainer/upstreams/archive/",
                "maintainer/upstreams/archives/",
                "maintainer/inventory/baselines/",
                "maintainer/inventory/snapshots/",
            )
        ) or any(part in {"historical", "history", "archive", "archives"} for part in parts)
        if relative in excluded or is_eval_fixture or is_historical_audit:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        hits = sorted(token for token in tokens if token in text)
        if hits:
            error(
                errors,
                f"{relative}: live referrer still names superseded governance source(s): {', '.join(hits)}",
            )


def validate_governance_merge_data(
    root: Path,
    manifest: dict,
    errors: list[str],
    *,
    verify_source_bytes: bool = True,
    check_live_referrers: bool = True,
) -> None:
    """Validate the lossless three-document consolidation evidence."""
    prefix = GOVERNANCE_MERGE_MANIFEST
    if manifest.get("schema_version") != "1.0.0":
        error(errors, f"{prefix}: schema_version must be 1.0.0")

    unitization_policy = manifest.get("unitization_policy")
    required_unitization_rules = {
        "headings",
        "table_rows",
        "normative_rules",
        "command_blocks",
        "evidence_paths",
    }
    if not isinstance(unitization_policy, dict) or set(unitization_policy) != required_unitization_rules:
        error(errors, f"{prefix}: unitization_policy must define every semantic source-unit class")
    elif any(not isinstance(value, str) or not value for value in unitization_policy.values()):
        error(errors, f"{prefix}: unitization_policy rules must be non-empty strings")

    destination_path = manifest.get("destination_path")
    if not isinstance(destination_path, str) or not destination_path:
        error(errors, f"{prefix}: destination_path is required")
        return
    destination = root / destination_path
    if not destination.is_file():
        error(errors, f"{prefix}: destination document does not exist: {destination_path}")
        return
    destination_text = destination.read_text(encoding="utf-8")

    allowed = manifest.get("allowed_dispositions")
    if not isinstance(allowed, list) or set(allowed) != GOVERNANCE_DISPOSITIONS or len(allowed) != len(GOVERNANCE_DISPOSITIONS):
        error(
            errors,
            f"{prefix}: allowed_dispositions must be exactly {sorted(GOVERNANCE_DISPOSITIONS)}",
        )
        allowed_set = GOVERNANCE_DISPOSITIONS
    else:
        allowed_set = set(allowed)

    documents = manifest.get("source_documents")
    if not isinstance(documents, list):
        error(errors, f"{prefix}: source_documents must be a list")
        documents = []
    documents_by_path: dict[str, dict] = {}
    source_lines_by_path: dict[str, list[str]] = {}
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            error(errors, f"{prefix}: source_documents[{index}] must be an object")
            continue
        source_path = document.get("source_path")
        if not isinstance(source_path, str) or not source_path:
            error(errors, f"{prefix}: source_documents[{index}].source_path is required")
            continue
        if source_path in documents_by_path:
            error(errors, f"{prefix}: duplicate source document {source_path}")
            continue
        documents_by_path[source_path] = document

    expected_paths = set(EXPECTED_GOVERNANCE_SOURCE_DOCUMENTS)
    if set(documents_by_path) != expected_paths or len(documents) != len(expected_paths):
        error(errors, f"{prefix}: source_documents must contain exactly the three migration baselines")

    for source_path, expected in EXPECTED_GOVERNANCE_SOURCE_DOCUMENTS.items():
        document = documents_by_path.get(source_path)
        if document is None:
            continue
        for field, expected_value in expected.items():
            if document.get(field) != expected_value:
                error(
                    errors,
                    f"{prefix}: {source_path} {field} must be {expected_value!r}",
                )
        recorded_hash = document.get("source_sha256")
        if not isinstance(recorded_hash, str) or not SHA256_RE.fullmatch(recorded_hash):
            error(errors, f"{prefix}: {source_path} has invalid source_sha256")
            continue
        payload = _source_document_bytes_from_worktree_or_history(root, source_path, recorded_hash)
        if payload is None:
            # A source archive may intentionally omit Git history. The fixed
            # expected metadata above remains the immutable migration baseline.
            continue
        try:
            source_lines = payload.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            error(errors, f"{prefix}: {source_path} baseline is not UTF-8")
            continue
        source_lines_by_path[source_path] = source_lines
        if not verify_source_bytes:
            continue
        actual_hash = hashlib.sha256(payload).hexdigest()
        actual_lines = len(source_lines)
        if actual_hash != recorded_hash:
            error(errors, f"{prefix}: {source_path} source_sha256 does not match baseline bytes")
        if len(payload) != document.get("byte_count"):
            error(errors, f"{prefix}: {source_path} byte_count does not match baseline bytes")
        if actual_lines != document.get("line_count"):
            error(errors, f"{prefix}: {source_path} line_count does not match baseline bytes")

    coverage = manifest.get("coverage")
    if not isinstance(coverage, list):
        error(errors, f"{prefix}: coverage must be a list")
        coverage = []
    summary = manifest.get("coverage_summary")
    if not isinstance(summary, dict):
        error(errors, f"{prefix}: coverage_summary must be an object")
        summary = {}

    by_source: Counter[str] = Counter()
    by_disposition: Counter[str] = Counter()
    by_unit_type: Counter[str] = Counter()
    unit_ids: set[tuple[str, str]] = set()
    structural_units: Counter[tuple[str, str, int]] = Counter()
    evidence_units: Counter[tuple[str, int, str]] = Counter()
    expected_evidence_units: set[tuple[str, int, str]] = set()
    legacy_document_names = {
        Path(source_path).name for source_path in EXPECTED_GOVERNANCE_SOURCE_DOCUMENTS
    }
    for source_path, source_lines in source_lines_by_path.items():
        for source_line, raw_source_line in enumerate(source_lines, start=1):
            for match in re.finditer(r"`([^`]+)`", raw_source_line):
                token = match.group(1)
                is_legacy_document = any(name in token for name in legacy_document_names)
                is_machine_file = token.startswith(("maintainer/", "plugins/")) and bool(
                    re.search(r"\.[A-Za-z0-9][A-Za-z0-9._-]*$", token)
                )
                is_evidence_directory = (
                    raw_source_line.lstrip().startswith("- ")
                    and token.startswith(("maintainer/", "plugins/"))
                    and token.endswith("/")
                )
                if is_legacy_document or is_machine_file or is_evidence_directory:
                    expected_evidence_units.add((source_path, source_line, token))
            command_match = re.match(r"\s*python\s+([^\s\\]+)", raw_source_line)
            if command_match:
                expected_evidence_units.add((source_path, source_line, command_match.group(1)))
    unmapped_units = 0

    for index, unit in enumerate(coverage):
        label = f"{prefix}: coverage[{index}]"
        if not isinstance(unit, dict):
            error(errors, f"{label} must be an object")
            unmapped_units += 1
            continue
        source_path = unit.get("source_path")
        disposition = unit.get("disposition")
        unit_type = unit.get("unit_type")
        if isinstance(source_path, str):
            by_source[source_path] += 1
        if isinstance(disposition, str):
            by_disposition[disposition] += 1
        if isinstance(unit_type, str):
            by_unit_type[unit_type] += 1

        mapping_valid = True
        source_document = documents_by_path.get(source_path)
        if source_document is None:
            error(errors, f"{label} names unknown source_path {source_path!r}")
            mapping_valid = False
        elif unit.get("source_sha256") != source_document.get("source_sha256"):
            error(errors, f"{label} source_sha256 does not match source_documents")
            mapping_valid = False

        row_id = unit.get("source_row_or_rule_id")
        if not isinstance(row_id, str) or not row_id:
            error(errors, f"{label} source_row_or_rule_id is required")
            mapping_valid = False
        elif isinstance(source_path, str):
            unit_key = (source_path, row_id)
            if unit_key in unit_ids:
                error(errors, f"{label} duplicates source unit {source_path}#{row_id}")
                mapping_valid = False
            unit_ids.add(unit_key)

        for field in ("source_heading", "source_excerpt", "unit_type", "reason", "evidence_source"):
            if not isinstance(unit.get(field), str) or not unit.get(field):
                error(errors, f"{label} {field} is required")
                mapping_valid = False
        source_line = unit.get("source_line")
        source_limit = source_document.get("line_count") if source_document else None
        if not isinstance(source_line, int) or source_line < 1 or (
            isinstance(source_limit, int) and source_line > source_limit
        ):
            error(errors, f"{label} source_line is outside the source document")
            mapping_valid = False

        source_lines = source_lines_by_path.get(source_path, [])
        if isinstance(source_line, int) and 1 <= source_line <= len(source_lines):
            raw_source_line = source_lines[source_line - 1]
            containing_heading = next(
                (
                    match.group(1)
                    for index in range(source_line - 1, -1, -1)
                    if (match := re.fullmatch(r"#{1,6}\s+(.+?)\s*", source_lines[index]))
                ),
                None,
            )
            if containing_heading is None or unit.get("source_heading") != containing_heading:
                error(errors, f"{label} source_heading must equal the containing baseline heading")
                mapping_valid = False
            if unit_type == "heading":
                structural_units[(source_path, "heading", source_line)] += 1
                heading_match = re.fullmatch(r"#{1,6}\s+(.+?)\s*", raw_source_line)
                if heading_match is None:
                    error(errors, f"{label} heading locator does not point to a Markdown heading")
                    mapping_valid = False
                else:
                    if unit.get("source_excerpt") != raw_source_line:
                        error(errors, f"{label} heading source_excerpt must equal the baseline heading")
                        mapping_valid = False
            elif unit_type == "table_row":
                structural_units[(source_path, "table_row", source_line)] += 1
                cells = [cell.strip() for cell in raw_source_line.strip().strip("|").split("|")]
                is_separator = bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)
                if not raw_source_line.startswith("|") or is_separator:
                    error(errors, f"{label} table_row locator does not point to a header or data row")
                    mapping_valid = False
                elif unit.get("source_excerpt") != raw_source_line:
                    error(errors, f"{label} table_row source_excerpt must equal the baseline row")
                    mapping_valid = False
            elif unit_type == "list_rule":
                structural_units[(source_path, "list_rule", source_line)] += 1
                if re.match(r"^\s*-\s+\S", raw_source_line) is None:
                    error(errors, f"{label} list_rule locator does not point to a Markdown list item")
                    mapping_valid = False
            elif unit_type == "command_block":
                structural_units[(source_path, "command_block", source_line)] += 1
                if re.fullmatch(r"```(?:bash|sh|shell)", raw_source_line) is None:
                    error(errors, f"{label} command_block locator does not point to a shell fence")
                    mapping_valid = False
                else:
                    closing_index = next(
                        (
                            index
                            for index in range(source_line, len(source_lines))
                            if source_lines[index] == "```"
                        ),
                        None,
                    )
                    if closing_index is None:
                        error(errors, f"{label} command_block has no closing fence")
                        mapping_valid = False
                    else:
                        baseline_block = "\n".join(source_lines[source_line - 1 : closing_index + 1])
                        if unit.get("source_excerpt") != baseline_block:
                            error(errors, f"{label} command_block source_excerpt must equal the baseline block")
                            mapping_valid = False
            elif unit_type == "evidence_path":
                source_excerpt = unit.get("source_excerpt")
                if isinstance(source_excerpt, str):
                    evidence_units[(source_path, source_line, source_excerpt)] += 1

        if unit.get("destination_path") != destination_path:
            error(errors, f"{label} destination_path must be {destination_path}")
            mapping_valid = False
        anchor = unit.get("destination_anchor")
        if not isinstance(anchor, str) or not anchor:
            error(errors, f"{label} destination_anchor is required")
            mapping_valid = False
        elif f'id="{anchor}"' not in destination_text:
            error(errors, f"{label} destination anchor #{anchor} does not exist")
            mapping_valid = False
        if disposition not in allowed_set:
            error(errors, f"{label} disposition {disposition!r} is not allowed")
            mapping_valid = False
        evidence_source = unit.get("evidence_source")
        if isinstance(evidence_source, str) and evidence_source and not (root / evidence_source).exists():
            error(errors, f"{label} evidence_source does not exist: {evidence_source}")
            mapping_valid = False
        if not mapping_valid:
            unmapped_units += 1

    for source_path, source_lines in source_lines_by_path.items():
        for source_line, raw_source_line in enumerate(source_lines, start=1):
            expected_type = None
            if re.fullmatch(r"#{1,6}\s+.+?\s*", raw_source_line):
                expected_type = "heading"
            elif raw_source_line.startswith("|"):
                cells = [cell.strip() for cell in raw_source_line.strip().strip("|").split("|")]
                if not (cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)):
                    expected_type = "table_row"
            elif re.match(r"^\s*-\s+\S", raw_source_line):
                expected_type = "list_rule"
            elif re.fullmatch(r"```(?:bash|sh|shell)", raw_source_line):
                expected_type = "command_block"
            if expected_type is None:
                continue
            count = structural_units[(source_path, expected_type, source_line)]
            if count != 1:
                error(
                    errors,
                    f"{prefix}: {source_path}:{source_line} must have exactly one {expected_type} coverage unit; found {count}",
                )
                unmapped_units += 1

    for evidence_key in sorted(expected_evidence_units):
        count = evidence_units[evidence_key]
        if count != 1:
            source_path, source_line, source_excerpt = evidence_key
            error(
                errors,
                f"{prefix}: {source_path}:{source_line} evidence path {source_excerpt!r} "
                f"must have exactly one coverage unit; found {count}",
            )
            unmapped_units += 1
    for evidence_key, count in evidence_units.items():
        if evidence_key not in expected_evidence_units:
            source_path, source_line, source_excerpt = evidence_key
            error(
                errors,
                f"{prefix}: {source_path}:{source_line} evidence path {source_excerpt!r} "
                "does not match the baseline unitization policy",
            )
            unmapped_units += count

    if summary.get("source_units") != len(coverage):
        error(errors, f"{prefix}: coverage_summary.source_units must equal len(coverage)")
    if summary.get("unmapped_units") != unmapped_units:
        error(errors, f"{prefix}: coverage_summary.unmapped_units does not match invalid mappings")
    if unmapped_units != 0 or summary.get("unmapped_units") != 0:
        error(errors, f"{prefix}: unmapped_units must be zero")

    aggregates = {
        "by_source": dict(by_source),
        "by_disposition": dict(by_disposition),
        "by_unit_type": dict(by_unit_type),
    }
    for field, actual in aggregates.items():
        if summary.get(field) != actual:
            error(errors, f"{prefix}: coverage_summary.{field} does not match coverage")

    if check_live_referrers:
        _validate_live_governance_referrers(root, expected_paths, destination_path, errors)


def validate_governance_merge_manifest(root: Path, errors: list[str]) -> None:
    path = root / GOVERNANCE_MERGE_MANIFEST
    if not path.is_file():
        error(errors, f"missing governance merge manifest: {GOVERNANCE_MERGE_MANIFEST}")
        return
    manifest = load_json(path)
    if not isinstance(manifest, dict):
        error(errors, f"{GOVERNANCE_MERGE_MANIFEST}: root must be an object")
        return
    validate_governance_merge_data(root, manifest, errors)


def validate_docs(root: Path, errors: list[str]) -> None:
    registry = load_json(root / "maintainer" / "upstreams" / "registry.json")
    governance = registry.get("governance", {})
    relative = governance.get("canonical_document")
    if not isinstance(relative, str) or not relative:
        error(errors, "registry governance.canonical_document is missing")
        return
    path = root / relative
    if not path.is_file():
        error(errors, f"missing canonical governance doc: {relative}")
        return
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for anchor in governance.get("required_anchors", []):
        if f'id="{anchor}"' not in text:
            error(errors, f"{relative}: missing required policy anchor #{anchor}")

    validate_governance_merge_manifest(root, errors)

    def rows_for(identifier: str) -> list[str]:
        token = f"`{identifier}`"
        return [line for line in lines if token in line]

    for source in registry.get("sources", []):
        if source.get("lifecycle") != "active" or source.get("id") == "internal-harness-native":
            continue
        source_id = source.get("id")
        rows = rows_for(source_id)
        if not rows:
            error(errors, f"{relative}: active source {source_id} is not documented")
            continue
        mode = source.get("integration_mode")
        lifecycle = source.get("lifecycle")
        summary_rows = [line for line in rows if mode in line and lifecycle in line]
        if not summary_rows:
            error(errors, f"{relative}: source {source_id} summary must match mode={mode} and lifecycle={lifecycle}")
            summary_rows = rows
        targets = source.get("target", {})
        for skill_name in targets.get("local_skills", []):
            if not any(skill_name in line for line in summary_rows):
                error(errors, f"{relative}: source {source_id} summary missing target {skill_name}")
        for contract_id in targets.get("behavior_contracts", []):
            if not any(f"`{contract_id}`" in line for line in summary_rows):
                error(errors, f"{relative}: behavior source {source_id} summary missing contract {contract_id}")
        group = source.get("relationship_group")
        if group and not any(group in line for line in summary_rows):
            error(errors, f"{relative}: source {source_id} summary missing relationship_group {group}")

    direct_sources = [
        source
        for source in registry.get("sources", [])
        if source.get("lifecycle") == "active"
        and source.get("integration_mode") in {"vendored", "adapted"}
    ]
    if not direct_sources:
        error(errors, "registry must retain at least one active vendored/adapted source")
    for source in direct_sources:
        sid = source.get("id", "<missing-id>")
        provenance = source.get("provenance", {})
        for field in ("license_spdx", "license_url", "license_sha256", "notice_path", "file_map"):
            if not provenance.get(field):
                error(errors, f"{sid}: active direct source missing legal/provenance field {field}")

    for contract in registry.get("behavior_contracts", []):
        contract_id = contract.get("id")
        rows = rows_for(contract_id)
        if not rows:
            error(errors, f"{relative}: behavior contract {contract_id} is not documented")
            continue
        for skill_name in contract.get("consumers", {}).get("skills", []):
            if not any(skill_name in line for line in rows):
                error(errors, f"{relative}: behavior contract {contract_id} summary missing consumer {skill_name}")


def validate_phase5_skill_files(root: Path, errors: list[str]) -> None:
    base = root / "maintainer" / "skills" / "skill-portfolio-maintainer"
    required = [
        "scripts/build_plugin.py",
        "scripts/validate_plugin.py",
        "scripts/freeze_manager_inventory.py",
        "scripts/smoke_cli_install.py",
        "scripts/verify_install_surfaces.py",
        "scripts/run_release_regression.py",
        "scripts/plugin_common.py",
        "references/plugin-structure.md",
        "evals/run_evals.py",
    ]
    plugin_base = root / "maintainer" / "skills" / "harness-plugin-maintainer"
    for item in required:
        if not (plugin_base / item).exists():
            error(errors, f"harness-plugin-maintainer missing Phase 6 file: {item}")

    required = [
        "scripts/check_upstreams.py",
        "scripts/discover_upstreams.py",
        "scripts/stage_upstream.py",
        "scripts/promote_upstream.py",
        "scripts/rollback_upstream.py",
        "scripts/portfolio_common.py",
        "references/reference-mode.md",
        "references/vendored-mode.md",
        "references/adapted-mode.md",
        "templates/upstream-review-report.md",
        "templates/asset-impact-report.md",
        "evals/run_evals.py",
    ]
    for item in required:
        if not (base / item).exists():
            error(errors, f"skill-portfolio-maintainer missing Phase 5 file: {item}")


def self_test() -> int:
    checks: list[tuple[str, bool]] = [
        ("invalid integration mode", "copied" not in MODES),
        ("invalid short sha", not SHA_RE.match("abc123")),
        ("invalid uppercase sha", not SHA_RE.match("A" * 40)),
        ("valid lowercase sha", bool(SHA_RE.match("a" * 40))),
        ("invalid sha256", not SHA256_RE.match("b" * 63)),
        ("required protected policy detects missing templates", not PROTECTED_REQUIRED.issubset({"**/scripts/**", "LICENSE*", "NOTICE*"})),
        ("claim classes stay separated", CLAIM_CLASSES == {"official-documented", "local-policy", "runtime-observation"}),
        ("stale fallback preserves accepted evidence", STALE_FALLBACK == "preserve-last-accepted-mark-stale"),
    ]
    failed = [name for name, passed in checks if not passed]
    if failed:
        for name in failed:
            print(f"ERROR: self-test failed: {name}", file=sys.stderr)
        return 1
    print("upstream registry validator self-test passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the upstream registry, lock state, provenance, and portfolio skill files."
    )
    parser.add_argument("--root", type=Path, default=repo_root(), help="harness repository root")
    parser.add_argument("--self-test", action="store_true", help="run validator fixture self-tests")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        return self_test()

    root = args.root.resolve()
    errors: list[str] = []
    validate_registry(root, errors)
    validate_docs(root, errors)
    validate_phase5_skill_files(root, errors)

    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        return 1
    print("upstream registry validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
