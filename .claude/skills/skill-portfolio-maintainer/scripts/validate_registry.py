#!/usr/bin/env python3
"""Validate upstream registry, lock, and skill provenance docs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MODES = {"native", "reference", "vendored", "adapted", "unknown"}
SOURCE_CLASSES = {"internal", "official", "reputable-third-party", "community", "standard", "unknown"}
LIFECYCLES = {"candidate", "active", "blocked", "deprecated"}
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


def canonical_skill_count(root: Path) -> int:
    """Derive the expected current-skills.json entry count from canonical trees.

    current-skills.json records provenance for every canonical skill, user and
    manager alike. Deriving the number keeps the check correct when skills are
    added or removed instead of requiring a hardcoded edit.
    """
    total = 0
    for base in (root / "skills", root / "maintainer" / "skills"):
        if base.is_dir():
            total += sum(1 for path in base.iterdir() if (path / "SKILL.md").is_file())
    return total


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

    validate_relationship_groups(registry, lock, errors)

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


def validate_docs(root: Path, errors: list[str]) -> None:
    refs = root / "Docs" / "External_Skill_References.md"
    imports = root / "Docs" / "Imported_Skill_Provenance.md"
    policy = root / "Docs" / "Skill_Upstream_Update_Policy.md"
    for path in (refs, imports, policy):
        if not path.exists():
            error(errors, f"missing doc: {path.relative_to(root)}")

    imported_text = imports.read_text(encoding="utf-8") if imports.exists() else ""
    registry = load_json(root / "maintainer" / "upstreams" / "registry.json")
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
        local_skills = source.get("target", {}).get("local_skills", [])
        for skill_name in local_skills:
            if skill_name not in imported_text:
                error(
                    errors,
                    f"Imported_Skill_Provenance.md must document {sid} target {skill_name}",
                )
    if not has_accepted_adapted_status(imported_text):
        error(
            errors,
            "Imported_Skill_Provenance.md must describe accepted/adapted status identifiers",
        )


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
        "templates/plugin-license.md",
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
