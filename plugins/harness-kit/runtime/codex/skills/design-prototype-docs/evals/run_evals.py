#!/usr/bin/env python3
"""Contract evals for design-prototype-docs.

This skill sits between design decisions and prototype code. The checks below
keep that boundary: it consumes design-system input rather than inventing it,
identifies motion candidates rather than specifying motion, and never binds to
another skill's internal files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def skill_text() -> str:
    return (ROOT / "SKILL.md").read_text(encoding="utf-8")


def test_design_system_input_is_checked_first() -> None:
    skill = skill_text()
    for required in (
        "STEP 0-E — 디자인 시스템 입력 확인",
        ".docs/design-system/**",
        "색·타이포그래피·간격 체계를 새로 발명하지 않는다",
        "기존 제품 디자인 시스템 → 승인된 `ui-ux-pro-max` 결정",
    ):
        assert required in skill, f"design-system input contract missing: {required!r}"


def test_motion_is_candidate_only_and_optional() -> None:
    skill = skill_text()
    for required in (
        "이 문서는 모션을 **설계하지 않는다.**",
        "후보와 목적만** 식별한다",
        "정적 화면으로 목적이 충분하면 이 섹션을 비워 둔다",
        "빈 섹션은 결함이 아니다",
        "duration, easing, 속성 같은 구체값을 이 문서에서 정하지 않는다",
    ):
        assert required in skill, f"motion candidate contract missing: {required!r}"


def test_handoff_uses_public_skill_names_only() -> None:
    skill = skill_text()
    for public_name in ("ui-ux-pro-max", "motion-design", "create-prototype"):
        assert f"`{public_name}`" in skill, f"public handoff name missing: {public_name}"

    # Binding to another skill's internals would break when that skill is
    # refactored, and would not resolve at all in an installed plugin.
    forbidden = [
        r"ui-ux-pro-max/(?:scripts|data|references)/",
        r"motion-design/(?:director|patterns|reference)/",
        r"\$\{CLAUDE_PLUGIN_ROOT\}",
        r"\.claude/skills",
        r"\.agents/skills",
    ]
    for pattern in forbidden:
        assert not re.search(pattern, skill), f"internal path coupling: {pattern}"


def test_producer_handoff_contract_survives() -> None:
    skill = skill_text()
    for required in (
        "artifact_bundle_id",
        "suppress_child_handoff",
        "humanize-korean",
        "artifact_bundle_fingerprint",
    ):
        assert required in skill, f"markdown producer contract missing: {required!r}"


def main() -> int:
    tests = [
        test_design_system_input_is_checked_first,
        test_motion_is_candidate_only_and_optional,
        test_handoff_uses_public_skill_names_only,
        test_producer_handoff_contract_survives,
    ]
    for test in tests:
        test()
    print(f"design-prototype-docs evals: PASS ({len(tests)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
