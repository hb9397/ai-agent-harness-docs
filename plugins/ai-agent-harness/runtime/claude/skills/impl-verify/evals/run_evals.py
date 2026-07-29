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
    print("impl-verify evals: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
