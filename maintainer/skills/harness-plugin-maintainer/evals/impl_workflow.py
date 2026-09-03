#!/usr/bin/env python3
"""Static cross-skill checks for tool-neutral implementation contracts."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    impl = read("skills/impl-doc/SKILL.md")
    fe_be = read("skills/impl-fe-be-doc/SKILL.md")
    bootstrap = read("skills/harness-bootstrap/SKILL.md")
    context = read("skills/context-doc/SKILL.md")
    context_template = read("skills/context-doc/templates/artifact-output-routing-instruction.md.template")

    for name, content in (("impl-doc", impl), ("impl-fe-be-doc", fe_be)):
        for needle in (
            "Step 0-C",
            "design-roadmap",
            "*-roadmap-impl-index.md",
            "impl-reuse-scan",
            "impl-verify",
            "downstream:",
            "not-applicable",
            "selected",
            "특정 스킬",
            "다른 도구·Agent",
        ):
            assert needle in content, f"{name} missing integration contract: {needle}"
        assert "$impl-reuse-scan" not in content, f"{name} still mandates impl-reuse-scan"
        assert "$impl-verify" not in content, f"{name} still mandates impl-verify"

    assert "필수 preflight" not in bootstrap and "종료 게이트" not in bootstrap
    assert "제공되는 참조 구현" in bootstrap and "필수 조건으로 만들지 않는다" in bootstrap
    assert "artifact-output-routing-instruction" in context
    assert "artifact-output-routing-instruction" in context_template
    assert "특정 스킬 호출을 완료 조건으로 삼지 않는다" in context_template
    assert "다른 스킬·플러그인·일반 Agent" in context_template
    print("impl workflow integration evals: PASS (roadmap, tool-neutral reuse/verify, routing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
