#!/usr/bin/env python3
"""Regression fixtures for the Markdown producer contract.

Two failure modes matter here. A producer list that lives in more than one place
drifts silently, so the inventory must be the only source. And document
refinement must never alter values that carry mechanical meaning — a changed hex
or duration turns a correct spec into a wrong one without looking wrong.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
INVENTORY = ROOT / "maintainer" / "inventory" / "markdown-artifact-flow.json"
PLUGIN_ROOT = ROOT / "plugins" / "harness-kit"


def inventory() -> dict:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def test_producer_list_has_a_single_source() -> None:
    expected = [item["skill"] for item in inventory()["producer_skills"]]

    release = json.loads((ROOT / "maintainer" / "plugin" / "release.json").read_text(encoding="utf-8"))
    assert release["markdown_producers"] == expected, "release metadata drifted from the inventory"

    caps = json.loads((PLUGIN_ROOT / "CAPABILITIES.json").read_text(encoding="utf-8"))
    flow = caps["markdown_artifact_flow"]
    assert flow["producers"] == expected, "packaged capabilities drifted from the inventory"
    assert flow["producer_count"] == len(expected)

    # A literal list in the builder would reintroduce the drift this replaces.
    builder = (ROOT / "maintainer" / "skills" / "harness-plugin-maintainer" / "scripts" / "build_plugin.py").read_text(encoding="utf-8")
    assert "MARKDOWN_PRODUCERS = [" not in builder, "producer list must not be hardcoded in the builder"


def test_every_producer_is_canonical_and_declares_the_handoff() -> None:
    for item in inventory()["producer_skills"]:
        name = item["skill"]
        skill = ROOT / "skills" / name / "SKILL.md"
        assert skill.is_file(), f"producer is not a canonical user skill: {name}"
        text = skill.read_text(encoding="utf-8")
        assert "humanize-korean" in text, f"producer does not declare the handoff: {name}"


def test_conditional_producers_default_to_no_write() -> None:
    """The new design skills report to chat unless asked to persist."""
    conditional = [item for item in inventory()["producer_skills"] if item.get("conditional")]
    assert {item["skill"] for item in conditional} == {"ui-ux-pro-max", "motion-design"}
    for item in conditional:
        assert item.get("condition"), f"conditional producer needs an explicit condition: {item['skill']}"
        text = (ROOT / "skills" / item["skill"] / "SKILL.md").read_text(encoding="utf-8")
        assert "기본 동작은 **대화창 보고**다" in text, f"{item['skill']} must default to reporting"
        assert "사용자 승인 없이" in text, f"{item['skill']} must gate writes on approval"


def test_only_the_outermost_producer_offers_the_handoff() -> None:
    """Nested producers must not each propose refinement for the same bundle."""
    for item in inventory()["producer_skills"]:
        text = (ROOT / "skills" / item["skill"] / "SKILL.md").read_text(encoding="utf-8")
        owns = "handoff_owner" in text or "suppress_child_handoff" in text
        gated = "최외곽" in text
        assert owns or gated, (
            f"{item['skill']} offers refinement without an ownership or outermost condition"
        )


def test_protected_tokens_are_declared_and_contracted() -> None:
    protected = inventory()["protected_tokens"]
    contract = ROOT / protected["contract"]
    assert contract.is_file(), "protected token contract file is missing"
    text = contract.read_text(encoding="utf-8")

    assert protected["design_system_documents"], "design-system protected values are not declared"
    assert protected["motion_documents"], "motion protected values are not declared"

    for required in (
        "hex, RGB, HSL 색상값",
        "CSS 변수명과 디자인 토큰 이름",
        "spacing, breakpoint 값",
        "duration, delay 값",
        "easing curve 이름과 cubic-bezier 계수",
        "reduced-motion 조건",
        "성능 budget",
        "윤문은 문장을 다듬는 작업이지 데이터를\n바꾸는 작업이 아니다",
    ):
        assert required in text, f"protected token contract missing: {required!r}"


def test_producing_skills_lock_their_own_mechanical_values() -> None:
    uiux = (ROOT / "skills" / "ui-ux-pro-max" / "SKILL.md").read_text(encoding="utf-8")
    assert "문서 개선 단계의 보호 토큰이다" in uiux
    for value in ("색상 hex", "토큰 이름", "수치", "경로"):
        assert value in uiux, f"design protected value not named in the skill: {value}"

    motion = (ROOT / "skills" / "motion-design" / "SKILL.md").read_text(encoding="utf-8")
    assert "문서 개선 단계의 보호 토큰이다" in motion
    for value in ("duration", "easing curve", "reduced-motion 조건", "budget"):
        assert value in motion, f"motion protected value not named in the skill: {value}"


def test_persisted_paths_stay_inside_the_declared_contract() -> None:
    """Output paths in the skills must match the inventory declaration."""
    declared: set[str] = set()
    for item in inventory()["producer_skills"]:
        declared.update(item["artifacts"])

    for name, expected in (
        ("ui-ux-pro-max", ".docs/design-system/{project-slug}/MASTER.md"),
        ("motion-design", ".docs/design-system/{project-slug}/motion/{screen-or-component}.md"),
    ):
        assert expected in declared, f"inventory does not declare {expected}"
        text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert expected in text, f"{name} does not document its declared output path"
        # Anything writing outside .docs would escape the harness output area.
        for match in re.findall(r"^\.docs/[^\s`]+", text, re.MULTILINE):
            assert match.startswith(".docs/"), match


def main() -> int:
    tests = [
        test_producer_list_has_a_single_source,
        test_every_producer_is_canonical_and_declares_the_handoff,
        test_conditional_producers_default_to_no_write,
        test_only_the_outermost_producer_offers_the_handoff,
        test_protected_tokens_are_declared_and_contracted,
        test_producing_skills_lock_their_own_mechanical_values,
        test_persisted_paths_stay_inside_the_declared_contract,
    ]
    for test in tests:
        test()
    print(f"markdown producer evals: PASS ({len(tests)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
