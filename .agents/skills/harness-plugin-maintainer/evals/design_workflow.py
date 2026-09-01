#!/usr/bin/env python3
"""Cross-skill integration fixtures for the design workflow.

Individual skill runners guard their own contract wording. Nothing there can see
whether the branches fit together: that a design decision reaches implementation
only through public names, that prototype output never becomes product source,
and that exactly one Markdown producer owns the humanize handoff. Those are
properties of the set, so they live here instead of in any single skill.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
SKILLS = ROOT / "skills"

DESIGN_FLOW = ["ui-ux-pro-max", "motion-design", "design-prototype-docs",
               "create-prototype", "frontend-design", "impl-verify"]


def read(skill: str) -> str:
    return (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")


def test_design_flow_skills_exist() -> None:
    for skill in DESIGN_FLOW:
        assert (SKILLS / skill / "SKILL.md").is_file(), f"design flow skill missing: {skill}"


def test_skills_never_bind_to_another_skills_internals() -> None:
    """Handoff must go through public names, not through file paths.

    An internal path breaks when the other skill is refactored, and it does not
    resolve at all once each skill is installed as a separate plugin entry.
    """
    internals = {
        "ui-ux-pro-max": ("scripts", "data", "references"),
        "motion-design": ("director", "patterns", "reference"),
        "create-prototype": ("references", "prompts", "examples"),
        "design-prototype-docs": ("example",),
        "impl-verify": ("prompts", "references", "templates"),
    }
    for skill in DESIGN_FLOW:
        text = read(skill)
        for other, subdirs in internals.items():
            if other == skill:
                continue
            for subdir in subdirs:
                pattern = rf"{re.escape(other)}/{subdir}/"
                assert not re.search(pattern, text), f"{skill} binds to {other}/{subdir}/"


def test_prototype_output_is_never_promoted_to_product_source() -> None:
    prototype = read("create-prototype")
    assert "제품 소스로 승격하지 않는다" in prototype
    assert "제품 디렉터리로 복사하지 않는다" in prototype

    frontend = read("frontend-design")
    assert "프로토타입 코드는 재사용하지 않는다" in frontend

    verify = read("impl-verify")
    assert "`.ai-docs/prototype/**` 코드가 제품 소스로 복사되지 않음" in verify


def test_both_branches_end_in_verification() -> None:
    for skill in ("create-prototype", "frontend-design", "ui-ux-pro-max", "motion-design"):
        assert "impl-verify" in read(skill), f"{skill} does not route to verification"


def test_real_screen_branch_does_not_require_a_prototype_first() -> None:
    prototype = read("create-prototype")
    assert "처음부터 실제 화면 구현을 요청하면 이 스킬을 강제하지 않고" in prototype


def test_motion_stays_conditional_across_the_flow() -> None:
    assert "정적 화면으로 목적이 충분하면 이 섹션을 비워 둔다" in read("design-prototype-docs")
    assert "어디에도 해당하지 않으면 모션을 넣지 않는다" in read("motion-design")
    assert "`motion-design` 명세가 있을 때만 해당 모션을 구현한다" in read("frontend-design")
    assert "모션은 승인된 후보만 구현한다" in read("create-prototype")


def test_existing_product_assets_outrank_generated_suggestions() -> None:
    assert "기존 시스템이 있으면 그 규칙이 이 스킬의 추천보다 **우선**한다" in read("ui-ux-pro-max")
    assert "이 스킬의 기본값보다 **우선**한다" in read("motion-design")
    assert "기존 제품 디자인 시스템 → 승인된 `ui-ux-pro-max` 결정" in read("design-prototype-docs")
    assert "1순위와 2순위가 충돌하면 **구현하지 말고**" in read("frontend-design")


def test_single_humanize_owner_per_bundle() -> None:
    """Only declared producers may offer the refinement handoff, and only once."""
    flow = json.loads((ROOT / "maintainer" / "inventory" / "markdown-artifact-flow.json").read_text(encoding="utf-8"))
    declared = {item["skill"] for item in flow["producer_skills"]}
    for skill in DESIGN_FLOW:
        text = read(skill)
        if "humanize-korean" not in text:
            continue
        if skill in declared:
            assert "suppress_child_handoff" in text or "억제" in text, (
                f"{skill} is a declared producer but does not suppress nested handoffs"
            )
        else:
            assert "최외곽 산출물 생성자" in text, (
                f"{skill} offers humanize handoff without an outermost-owner condition"
            )


def test_new_skills_are_canonical_but_not_yet_packaged() -> None:
    capabilities = json.loads((ROOT / "maintainer" / "plugin" / "CAPABILITIES.json").read_text(encoding="utf-8"))
    pending = set(capabilities.get("pending_packaging", []))
    for skill in ("ui-ux-pro-max", "motion-design"):
        assert (SKILLS / skill / "SKILL.md").is_file()
        if skill in pending:
            assert skill not in capabilities["logical_user_skills"]


def test_reference_relationships_import_no_files() -> None:
    """Reference mode adopts concepts; copying would make it an adapted source."""
    registry = json.loads((ROOT / "maintainer" / "upstreams" / "registry.json").read_text(encoding="utf-8"))
    for source in registry["sources"]:
        if source.get("integration_mode") != "reference":
            continue
        provenance = source.get("provenance", {})
        assert not provenance.get("notice_path"), f"{source['id']}: reference claims a packaged notice"
        for entry in provenance.get("file_map", []):
            assert entry.get("treatment") == "reference-only", (
                f"{source['id']}: reference file_map must stay reference-only"
            )


def main() -> int:
    tests = [
        test_design_flow_skills_exist,
        test_skills_never_bind_to_another_skills_internals,
        test_prototype_output_is_never_promoted_to_product_source,
        test_both_branches_end_in_verification,
        test_real_screen_branch_does_not_require_a_prototype_first,
        test_motion_stays_conditional_across_the_flow,
        test_existing_product_assets_outrank_generated_suggestions,
        test_single_humanize_owner_per_bundle,
        test_new_skills_are_canonical_but_not_yet_packaged,
        test_reference_relationships_import_no_files,
    ]
    for test in tests:
        test()
    print(f"design workflow integration evals: PASS ({len(tests)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
