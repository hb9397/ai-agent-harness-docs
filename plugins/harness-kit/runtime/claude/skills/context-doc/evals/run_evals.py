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
        ".docs/harness/artifact-routing.json",
        "artifact-format-contract.json",
        "harness-kit:managed:start/end",
        ".docs/_inbox/{artifact-bundle-id}/artifact-manifest.json",
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
        ".docs/harness/artifact-routing.json",
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

    print("context-doc portable routing evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
