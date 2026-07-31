#!/usr/bin/env python3
"""Contract evals for frontend-design.

This skill implements product code. The checks keep two things apart that are
easy to conflate: the routing table that picks an owner by final deliverable,
and the preceding-input contract that decides what the implementation is based
on. Motion is conditional here rather than self-decided.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def skill_text() -> str:
    return (ROOT / "SKILL.md").read_text(encoding="utf-8")


def test_routing_table_still_selects_by_final_deliverable() -> None:
    skill = skill_text()
    assert "## 진입 라우팅" in skill
    for owner in ("`design-prototype-docs`", "`create-prototype`", "`frontend-design`"):
        assert owner in skill, f"routing owner missing: {owner}"
    assert "요청에 “화면”, “UI”, “프로토타입”이라는 단어가 있다는 이유만으로 선택하지 않는다" in skill


def test_preceding_input_is_a_separate_two_axis_contract() -> None:
    skill = skill_text()
    assert "## 선행 입력" in skill, "preceding-input section missing"
    assert "축이 다르다" in skill, "the section must explain why it is not merged into routing"
    for axis in ("| 디자인 |", "| 모션 |"):
        assert axis in skill, f"input axis missing: {axis}"
    for required in (
        "기존 제품의 디자인 시스템·컴포넌트·토큰",
        "승인된 `ui-ux-pro-max` 결정",
        "기존 제품의 모션 언어",
        "승인된 `motion-design` 명세",
        "접근 가능한 최소 상태 피드백",
        "구현하지 말고** 차이와 근거를 보고한다",
    ):
        assert required in skill, f"preceding-input contract missing: {required!r}"


def test_motion_is_conditional_not_self_decided() -> None:
    skill = skill_text()
    assert "`motion-design` 명세가 있을 때만 해당 모션을 구현한다" in skill
    assert "장식 애니메이션을 추가하지 않는다" in skill
    # The pre-integration wording let this skill pick motion on its own.
    assert "의미 있는 1~2개의 핵심 애니메이션에 집중" not in skill


def test_prototype_code_is_not_promoted() -> None:
    skill = skill_text()
    assert "프로토타입 코드는 재사용하지 않는다" in skill
    assert ".docs/prototype/**" in skill


def test_permissions_and_source_notice_stay_bounded() -> None:
    skill = skill_text()
    frontmatter = skill.split("---")[1]
    assert "allowed-tools: Read, Write, Glob, Grep" in frontmatter
    assert "Bash" not in frontmatter, "unrestricted shell must not be pre-approved"
    assert "model:" not in frontmatter, "frontmatter must stay model-neutral"

    # Source lists live in the central provenance docs. Duplicating them here
    # only creates drift between the skill text and the registry.
    assert "Docs/External_Skill_References.md" in skill
    assert "이 파일에 출처 목록을 중복해" in skill
    for pattern in (r"\$\{CLAUDE_PLUGIN_ROOT\}", r"\.claude/skills", r"\.agents/skills"):
        assert not re.search(pattern, skill), f"platform-specific path leaked: {pattern}"


def main() -> int:
    tests = [
        test_routing_table_still_selects_by_final_deliverable,
        test_preceding_input_is_a_separate_two_axis_contract,
        test_motion_is_conditional_not_self_decided,
        test_prototype_code_is_not_promoted,
        test_permissions_and_source_notice_stay_bounded,
    ]
    for test in tests:
        test()
    print(f"frontend-design evals: PASS ({len(tests)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
