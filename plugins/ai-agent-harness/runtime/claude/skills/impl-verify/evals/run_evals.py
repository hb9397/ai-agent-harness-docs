#!/usr/bin/env python3
"""Static trust-boundary regression checks for impl-verify."""

from __future__ import annotations

import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    skill = read("SKILL.md")
    safe = read("references/safe-execution.md")
    classify = read("prompts/classify-checks.md")
    run_auto = read("prompts/run-auto.md")
    combined = "\n".join((skill, safe, classify, run_auto))

    for required in (
        "신뢰하지 않는 데이터",
        "실행 파일",
        "스크립트 본문",
        "사용자 승인도 이 금지를 해제하지 않는다",
        "downloader-to-shell",
        "auto candidate",
    ):
        assert required in combined, f"trust-boundary contract missing: {required}"
    assert "## 자유롭게 실행 가능" not in safe
    assert "기본 `./verify-output/`" not in run_auto
    assert "allowed-tools: Read, Glob, Grep, Agent" in skill
    assert "disable-model-invocation: true" in skill

    # UI and motion checks are easy to drop during later edits because they only
    # apply to screen work. Pin them so the matrix cannot quietly shrink.
    for required in (
        "### UI 검증 항목",
        "해당 없으면\n항목을 생략하고 생략 사유를 리포트에 남긴다",
        "raw hex·매직 넘버를 직접 쓰지 않음",
        "대비 4.5:1 이상",
        "focus 표시가 보임",
        "44×44px",
        "가로 스크롤 없음",
        "loading·empty·error·success",
        "prefers-reduced-motion: reduce",
        "승인된 명세 범위 안에 있고",
        "목적 없이 계속 돌지 않음",
        "layout thrashing",
        "`.docs/prototype/**` 코드가 제품 소스로 복사되지 않음",
    ):
        assert required in skill, f"UI verification item missing: {required!r}"

    print("impl-verify evals: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
