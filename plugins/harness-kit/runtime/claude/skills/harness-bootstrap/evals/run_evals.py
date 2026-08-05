"""Executable contract checks for the bootstrap-to-setup workflow."""

from __future__ import annotations

import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = SKILL_ROOT / "SKILL.md"
EVALS_FILE = Path(__file__).with_name("evals.json")
INTERVIEW_FILE = SKILL_ROOT / "prompts" / "interview.md"
CODE_SCAN_FILE = SKILL_ROOT / "prompts" / "code-scan.md"
EXTRACTION_FILE = SKILL_ROOT / "prompts" / "extraction-mapping.md"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"{SKILL_FILE}: missing required contract: {needle}")


def main() -> int:
    skill = SKILL_FILE.read_text(encoding="utf-8")
    evals = json.loads(EVALS_FILE.read_text(encoding="utf-8"))

    for needle in (
        "공개 스킬 이름 `harness-setup`",
        "handoff_owner = harness-bootstrap",
        "suppress_child_handoff = true",
        "같은 질문을 반복하지 않는다",
        "`.agents/skills/`",
        "`.claude/skills/`",
        "`skills/`는 생성·복사·동기화하지 않는다",
        "private 템플릿을 흉내 내거나 프로젝트에 스킬을 복사해",
        "`.docs/README.md`, `.docs/.gitignore`, `.docs/_inbox/`",
        "`prompts/interview.md`",
        "**단일 상세 계약**",
        "artifact_fingerprint",
        "`.docs/.harness/humanize-handoffs.json`",
        "`proposed`, `skipped`, `rejected`, `applied`, `revalidated`",
        "원자적 replace",
        "`harness-kit:managed:start/end` marker",
    ):
        require(skill, needle)

    if not INTERVIEW_FILE.is_file():
        raise AssertionError(f"missing protected interview prompt: {INTERVIEW_FILE}")
    interview = INTERVIEW_FILE.read_text(encoding="utf-8")
    for needle in ("최대 2회", "질문 1 (필수)", "질문 2 (선택)", "묻지 않는 것"):
        if needle not in interview:
            raise AssertionError(f"{INTERVIEW_FILE}: missing contract: {needle}")

    for prompt_file in (CODE_SCAN_FILE, EXTRACTION_FILE, INTERVIEW_FILE):
        text = prompt_file.read_text(encoding="utf-8")
        if "artifact 의미" not in text or "대상 앱" not in text:
            raise AssertionError(f"{prompt_file}: missing portable routing decision rule")

    if "../harness-setup/" in skill:
        raise AssertionError("bootstrap must not couple to harness-setup private paths")

    ids = [case["id"] for case in evals["evals"]]
    if ids != [1, 2, 3, 4, 5]:
        raise AssertionError(f"unexpected eval ids: {ids}")
    if "/harness-bootstrap" in EVALS_FILE.read_text(encoding="utf-8"):
        raise AssertionError("platform-specific standalone slash invocation remains")

    print("harness bootstrap contract evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
