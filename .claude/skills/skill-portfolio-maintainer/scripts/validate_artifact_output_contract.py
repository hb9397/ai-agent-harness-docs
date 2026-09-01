#!/usr/bin/env python3
"""Validate the canonical artifact-output routing manifest against live skills."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MANIFEST = ROOT / "maintainer" / "inventory" / "artifact-output-contract.json"
ALLOWED_CLASSES = {
    "managed-project-output",
    "source-mutation",
    "report-only",
    "chat-only",
    "manager-repository-output",
}
REQUIRED_FIELDS = {
    "skill",
    "scope",
    "artifact_class",
    "persistence",
    "single_app_path",
    "multi_app_path",
    "owner",
    "approval",
    "handoff",
    "routing_profile",
    "evidence",
}
ROUTING_REQUIRED = {
    "context-doc",
    "create-prototype",
    "design-doc",
    "design-prototype-docs",
    "frontend-design",
    "harness-bootstrap",
    "harness-setup",
    "impl-doc",
    "impl-fe-be-doc",
    "motion-design",
    "ui-ux-pro-max",
}


def live_skills(root_name: str) -> set[str]:
    root = ROOT / root_name
    return {p.parent.name for p in root.glob("*/SKILL.md")}


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = data["skills"]
    routing_profiles = data["routing_profiles"]
    names = [entry.get("skill") for entry in entries]
    assert len(names) == len(set(names)), "duplicate skill in artifact-output contract"
    assert set(names) == live_skills("skills") | live_skills("maintainer/skills"), "manifest/live skill set mismatch"

    user = {entry["skill"] for entry in entries if entry["scope"] == "user"}
    manager = {entry["skill"] for entry in entries if entry["scope"] == "manager"}
    assert len(user) == data["discovery"]["expected_user_skill_count"], "user skill count mismatch"
    assert len(manager) == data["discovery"]["expected_manager_skill_count"], "manager skill count mismatch"
    assert user == live_skills("skills"), "user skill manifest mismatch"
    assert manager == live_skills("maintainer/skills"), "manager skill manifest mismatch"

    instruction = data["instruction"]
    assert instruction["single_app_path"] == ".ai-docs/instruction/artifact-output-routing-instruction.md"
    assert instruction["multi_app_path"] == ".ai-docs/{앱}/instruction/artifact-output-routing-instruction.md"
    assert instruction["single_app_ref"] == "@.ai-docs/instruction/artifact-output-routing-instruction.md"
    assert instruction["multi_app_ref"] == "@.ai-docs/{앱}/instruction/artifact-output-routing-instruction.md"

    for entry in entries:
        assert set(entry) >= REQUIRED_FIELDS, f"{entry.get('skill')} missing manifest fields"
        assert entry["artifact_class"] in ALLOWED_CLASSES, f"invalid artifact class: {entry['skill']}"
        assert all(str(entry[field]).strip() for field in REQUIRED_FIELDS), f"blank manifest field: {entry['skill']}"
        profile = routing_profiles.get(entry["routing_profile"])
        assert profile is not None, f"unknown routing profile: {entry['skill']}"
        assert set(profile) >= {"media_type", "required_format", "unknown_write_capability"}, (
            f"incomplete routing profile: {entry['routing_profile']}"
        )
        assert profile["unknown_write_capability"] is False, (
            f"unknown write capability is not allowed: {entry['skill']}"
        )
        if entry["skill"] in {"impl-doc", "impl-fe-be-doc"}:
            assert "roadmap" in entry["evidence"] and "{사용자}" in entry["single_app_path"]
            assert ".ai-docs/{앱}/" in entry["multi_app_path"]
        if entry["skill"] in {"design-prototype-docs", "create-prototype", "ui-ux-pro-max", "motion-design"}:
            assert ".ai-docs/{앱}/" in entry["multi_app_path"], f"multi-app path is not app-scoped: {entry['skill']}"
        if entry["artifact_class"] in {"report-only", "chat-only"}:
            assert "no file" in entry["persistence"].lower() or "chat" in entry["single_app_path"].lower()
        if entry["scope"] == "manager":
            assert "maintainer" in entry["single_app_path"] or "plugins" in entry["single_app_path"]
            assert ".ai-docs" not in entry["single_app_path"] and ".ai-docs" not in entry["multi_app_path"]

    for skill in ROUTING_REQUIRED:
        skill_text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "artifact-output-routing-instruction" in skill_text, (
            f"output-producing skill does not consume routing instruction: {skill}"
        )
        assert "@.ai-docs/instruction/artifact-output-routing-instruction.md" in skill_text
        assert "@.ai-docs/{앱}/instruction/artifact-output-routing-instruction.md" in skill_text

    # A live skill that gained a write-capable surface must be added to the manifest.
    # The exact set assertion above is the primary guard; this scan provides a useful
    # diagnostic for accidental path-bearing files outside the declared roots.
    for skill_root in (ROOT / "skills", ROOT / "maintainer" / "skills"):
        for skill_file in skill_root.glob("*/SKILL.md"):
            text = skill_file.read_text(encoding="utf-8")
            if re.search(r"(?:Write|write|저장|생성|수정|삭제|commit|push)", text):
                assert skill_file.parent.name in names, f"write-capable skill absent from manifest: {skill_file}"

    print("artifact output contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
