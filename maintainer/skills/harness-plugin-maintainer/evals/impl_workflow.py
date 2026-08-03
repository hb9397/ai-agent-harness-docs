#!/usr/bin/env python3
"""Static cross-skill checks for implementation-document handoffs."""

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
            "$impl-reuse-scan",
            "$impl-verify",
        ):
            assert needle in content, f"{name} missing integration contract: {needle}"
        assert "invocation: explicit-only" in content or 'invocation: "explicit-only"' in content, (
            f"{name} missing explicit-only invocation contract"
        )

    assert "impl-reuse-scan" in fe_be and "impl-verify" in fe_be, "FE/BE integration graph is incomplete"
    assert "impl-reuse-scan (선택)" not in bootstrap, "bootstrap still marks reuse scan optional"
    assert "impl-verify (선택)" not in bootstrap, "bootstrap still marks verify optional"
    assert "필수 preflight" in bootstrap and "명시 호출 전용" in bootstrap, "bootstrap gate wording is incomplete"
    assert "artifact-output-routing-instruction" in context
    assert "artifact-output-routing-instruction" in context_template
    print("impl workflow integration evals: PASS (roadmap, reuse, verify, routing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
