"""Executable contract checks for the bootstrap-to-setup workflow."""

from __future__ import annotations

import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = SKILL_ROOT / "SKILL.md"
EVALS_FILE = Path(__file__).with_name("evals.json")
INTERVIEW_FILE = SKILL_ROOT / "prompts" / "interview.md"
CODE_SCAN_FILE = SKILL_ROOT / "prompts" / "code-scan.md"
EXTRACTION_FILE = SKILL_ROOT / "prompts" / "project-extraction-mapping.md"
DESIGN_SKILL_FILE = SKILL_ROOT.parent / "design-doc" / "SKILL.md"
CONTEXT_SKILL_FILE = SKILL_ROOT.parent / "context-doc" / "SKILL.md"
CONTEXT_TEMPLATE_FILE = SKILL_ROOT.parent / "context-doc" / "templates" / "AGENTS.md.template"


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
        "`.ai-docs/README.md`, `.ai-docs/.gitignore`, `.ai-docs/_inbox/`",
        "`prompts/interview.md`",
        "**단일 상세 계약**",
        "artifact_fingerprint",
        "`.ai-docs/.harness/humanize-handoffs.json`",
        "`proposed`, `skipped`, `rejected`, `applied`, `revalidated`",
        "원자적 replace",
        "`harness-kit:managed:start/end` marker",
        "## 선택 권한 정책 연계와 단계 분리",
        "`admin`만 가진 계정은 앱 문서를 저장할 수 없다",
        "하네스 단계",
        "앱 문서 단계",
        "`design-doc`과 `context-doc`이 자동 handoff된 실행에서도",
        "앱 설계·컨텍스트 문서 쓰기 확인",
        "루트 `AGENTS.md`·`CLAUDE.md`와 `.ai-docs/root-context/**`를 수정하지 않았는지 검증",
        "## 문서 루트 계약",
        "`.docs/`만 있거나 두 경로가 공존하면",
        "`harness-setup`의 명시적 문서 루트 이관·충돌 해결",
        "`.docs/`가 남지 않았다는 검증",
        "confirmed_scope = {Step 0-B에서 승인받은 범위 객체}",
        "`agent-instruction.md`",
        "@.ai-docs/instruction/artifact-output-routing-instruction.md",
        "@.ai-docs/{앱}/instruction/artifact-output-routing-instruction.md",
        "{project}/.ai-docs/{앱}/context-base/DESIGN.md",
        "PROJECT_DESIGN",
        "기능 분류는 상세 문서나 구현의 허용 목록이 아님",
        "변경 이력 없이 현재 기준 사실만 기록",
        "1~10 상세 애플리케이션 컨텍스트",
        "핵심 도메인 개념을 포함한 계층형 앱 특이사항",
        "노드명·순서·부모-자식 관계·Depth",
        "실행 profile, Git remote·branch",
        "DB 준비·migration 명령을 넣지 않는다",
        "초기 목적 골격 세트",
        "architecture·data-standard·code-style·framework·file-convention",
        "과거 값·변경 과정 없이 현재 사실·규칙만",
    ):
        require(skill, needle)

    if "저장 경로는 `.ai-docs/context-base/DESIGN.md`" in skill:
        raise AssertionError("bootstrap still presents a single-app path for every project type")

    for child_skill in (DESIGN_SKILL_FILE, CONTEXT_SKILL_FILE):
        child_text = child_skill.read_text(encoding="utf-8")
        for needle in (
            "confirmed_scope",
            "같은 질문을 반복하지",
            "대신하지 않는다",
        ):
            if needle not in child_text:
                raise AssertionError(f"{child_skill}: missing confirmed scope handoff contract: {needle}")

    context_template = CONTEXT_TEMPLATE_FILE.read_text(encoding="utf-8")
    for needle in (
        "DESIGN.md 열기",
        "양방향으로 추적",
        "AI 구현 전 읽기 순서",
        "## 1. 프로젝트 개요",
        "## 4. 실행 프로필 및 실행 방식",
        "## 5. Git 원격 저장소 및 브랜치",
        "## 6. 배포 방식",
        "## 8. 애플리케이션 사용 환경 변수 목록",
        "## 9. AI 구현 지침",
        "## 10. 구축 대상 기능 분류",
        "현재 유효한 사실만 기록",
    ):
        if needle not in context_template:
            raise AssertionError(f"{CONTEXT_TEMPLATE_FILE}: missing context contract: {needle}")

    if not INTERVIEW_FILE.is_file():
        raise AssertionError(f"missing protected interview prompt: {INTERVIEW_FILE}")
    interview = INTERVIEW_FILE.read_text(encoding="utf-8")
    for needle in (
        "최대 3회",
        "질문 1 (필수)",
        "질문 2 (필수)",
        "질문 3 (조건부)",
        "패키지·파일 구조 예시",
        "배포 환경은 비워 두겠습니다",
        "묻지 않는 것",
    ):
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
    if "context 단계에서도 새 질문 없이" in EVALS_FILE.read_text(encoding="utf-8"):
        raise AssertionError("eval contract incorrectly suppresses mandatory access approval")

    print("harness bootstrap contract evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
