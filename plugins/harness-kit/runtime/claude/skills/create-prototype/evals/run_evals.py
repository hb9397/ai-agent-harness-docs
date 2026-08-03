#!/usr/bin/env python3
"""Static safety contract checks for the prototype template."""

from __future__ import annotations

import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def executable_lines(text: str) -> list[str]:
    """Return non-prose assignment/markup lines that could be copied as code."""
    return [
        line
        for line in text.splitlines()
        if not line.lstrip().startswith(("-", ">", "#", "<!--"))
    ]


def main() -> int:
    template = (ROOT / "references" / "html-template.md").read_text(encoding="utf-8")
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    code = "\n".join(executable_lines(template))

    assert not re.search(r"<[^>]+\sstyle\s*=", code, re.IGNORECASE), "inline style remains"
    assert not re.search(r"<[^>]+\son[a-z]+\s*=", code, re.IGNORECASE), "inline handler remains"
    assert not re.search(
        r"\.(?:innerHTML|outerHTML)\s*=|insertAdjacentHTML\s*\(|document\.write\s*\(",
        code,
    ), "unsafe HTML sink remains in copyable example"
    for required in ("textContent", "createElement", "replaceChildren", "addEventListener"):
        assert required in template, f"safe DOM primitive missing: {required}"
    for required in ("\\u003c", "innerHTML", "인라인 `on*`"):
        assert required in skill, f"SKILL safety contract missing: {required}"

    legacy = ROOT / "examples" / "SFR-018.html"
    assert legacy.exists() and legacy.stat().st_size > 0, "protected legacy example was removed"

    # Prototype output is throwaway verification material. Losing this boundary
    # would let verification HTML drift into the product source tree.
    for required in (
        "### 두 분기의 경계",
        "제품 소스로 승격하지 않는다",
        "제품 디렉터리로 복사하지 않는다",
        "승인된 디자인 결정과 화면\n  명세만** 전달한다",
        "처음부터 실제 화면 구현을 요청하면 이 스킬을 강제하지 않고",
    ):
        assert required in skill, f"branch boundary contract missing: {required!r}"

    # Motion belongs to motion-design; this skill only realises approved output.
    for required in (
        "### 선행 입력",
        "승인된 `motion-design` 결과",
        "모션은 승인된 후보만 구현한다",
        "과도한 반복이나 장식 애니메이션을 넣지 않는다",
    ):
        assert required in skill, f"preceding-input contract missing: {required!r}"

    for pattern in (r"ui-ux-pro-max/(?:scripts|data|references)/",
                    r"motion-design/(?:director|patterns|reference)/"):
        assert not re.search(pattern, skill), f"internal path coupling: {pattern}"

    print("create-prototype evals: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
