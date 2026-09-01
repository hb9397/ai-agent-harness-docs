#!/usr/bin/env python3
"""Static contract checks for context-doc portable artifact routing."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = ROOT / "skills" / "context-doc"


def require(path: Path, *needles: str) -> None:
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise AssertionError(f"{path}: missing required contract: {needle}")


def main() -> int:
    require(
        SKILL_ROOT / "SKILL.md",
        ".ai-docs/harness/artifact-routing.json",
        "artifact-format-contract.json",
        "harness-kit:managed:start/end",
        ".ai-docs/_inbox/{artifact-bundle-id}/artifact-manifest.json",
        "## 선택 권한 정책 연계",
        "`admin`은 앱 문서",
        "권한을 상속하지 않는다",
        "다른 스킬이 `context-doc`을 선택한 경우에도",
        "앱 컨텍스트와 작업 지침 편집 확인",
        "루트 `AGENTS.md`/`CLAUDE.md`와 `.ai-docs/root-context/**`는 생성하지 않는다",
    )
    require(
        SKILL_ROOT / "templates" / "artifact-output-routing-instruction.md.template",
        "artifact 의미와 대상 app",
        "G12 승인",
        "artifact_bundle_id",
        "harness-kit:managed:start/end",
    )
    require(
        SKILL_ROOT / "templates" / "AGENTS.md.template",
        "Application Context",
        ".ai-docs/harness/artifact-routing.json",
        "artifact 의미와 대상 앱",
    )
    require(
        SKILL_ROOT / "templates" / "CLAUDE.md.template",
        "plugin 이름 기반 경로를 만들지 않는다",
    )
    for prompt in ("analysis-instruction.md", "parallel-setup.md"):
        require(SKILL_ROOT / "prompts" / prompt, "artifact 의미", "대상 앱")

    evals = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    ids = [case["id"] for case in evals["evals"]]
    if ids != [1, 2, 3, 4]:
        raise AssertionError(f"unexpected eval ids: {ids}")
    if "_inbox" not in evals["evals"][-1]["expected_output"]:
        raise AssertionError("external producer eval must require inbox-only proposal")
    if any("CLAUDE.md는 bridge" in case["expected_output"] for case in evals["evals"]):
        raise AssertionError("context-doc eval still assigns root bridge ownership")

    print("context-doc portable routing evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
