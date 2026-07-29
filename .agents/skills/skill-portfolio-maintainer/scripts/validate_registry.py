#!/usr/bin/env python3
"""Validate upstream registry, lock, and Phase 3 provenance docs."""

from __future__ import annotations

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
    if len(skills) != 20:
        error(errors, f"current-skills.json must describe 20 current skills, got {len(skills)}")
    if not any(item.get("name") == "humanize-korean" for item in candidates):
        error(errors, "current-skills.json missing humanize-korean candidate")
    for item in skills + candidates:
        for sid in item.get("sources", []):
            if sid not in source_ids:
                error(errors, f"{item.get('name')}: unknown source id {sid}")


def validate_docs(root: Path, errors: list[str]) -> None:
    refs = root / "Docs" / "External_Skill_References.md"
    imports = root / "Docs" / "Imported_Skill_Provenance.md"
    policy = root / "Docs" / "Skill_Upstream_Update_Policy.md"
    for path in (refs, imports, policy):
        if not path.exists():
            error(errors, f"missing doc: {path.relative_to(root)}")

    imported_text = imports.read_text(encoding="utf-8") if imports.exists() else ""
    if "no confirmed current `vendored` or `adapted`" not in imported_text:
        error(errors, "Imported_Skill_Provenance.md must state Phase 3 has no confirmed imports")
    if "humanize-korean" not in imported_text or "pending candidate" not in imported_text:
        error(errors, "Imported_Skill_Provenance.md must keep humanize-korean pending")


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


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return self_test()

    root = repo_root()
    errors: list[str] = []
    validate_registry(root, errors)
    validate_docs(root, errors)

    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        return 1
    print("upstream registry validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
