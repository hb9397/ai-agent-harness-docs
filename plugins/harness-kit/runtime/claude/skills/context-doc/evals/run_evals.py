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
        "`agent-instruction.md`와 `artifact-output-routing-instruction.md`",
        "confirmed_scope",
        "prompts/design-sync.md",
        "prompts/instruction-lifecycle.md",
        "1~10 상세 컨텍스트",
        "data-standard-instruction.md",
        "Git 원격 저장소 및 브랜치",
        "DB 생성·migration·seed·접속",
        "`플러그인 스킬만 사용` 또는 비기반 공개 스킬의 필수 호출 체인을 만들지 않는다",
        "다른 설치 스킬·플러그인·",
        "사용자가 이번 요청에서 한국어 Markdown 문체 개선까지 명시한 경우에만",
    )
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    if "유일한 항상 생성 예외" in skill_text:
        raise AssertionError("context-doc still contradicts the two always-generated instructions")
    require(
        SKILL_ROOT / "templates" / "artifact-output-routing-instruction.md.template",
        "artifact 의미와 대상 app",
        "G12 승인",
        "artifact_bundle_id",
        "harness-kit:managed:start/end",
        "특정 producer 이름을 사용 조건으로 삼지 않는다",
        "다른 스킬·플러그인·일반 Agent",
        "특정 스킬 호출을 완료 조건으로 삼지 않는다",
    )
    routing_template = (SKILL_ROOT / "templates" / "artifact-output-routing-instruction.md.template").read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "Phase 시작에\n  `impl-reuse-scan`",
        "Phase 종료에 명시 호출 `impl-verify`",
    ):
        if forbidden in routing_template:
            raise AssertionError(f"routing template still mandates a downstream skill: {forbidden}")
    require(
        SKILL_ROOT / "templates" / "agent-instruction.md.template",
        "project-local skill copy 금지",
        "다른 설치 스킬",
        "필수 실행 체인으로 쓰지 않는다",
    )
    require(
        SKILL_ROOT / "prompts" / "analysis-instruction.md",
        "필수 실행 체인으로",
        "다른 설치 스킬·플러그인·일반 Agent",
        "선택 가능한",
    )
    require(
        SKILL_ROOT / "templates" / "AGENTS.md.template",
        "AI Agent Guide",
        "DESIGN.md 열기",
        "양방향으로 추적",
        "AI 구현 전 읽기 순서",
        "## 1. 프로젝트 개요",
        "## 2. 기술 스택",
        "## 3. 아키텍처",
        "## 4. 실행 프로필 및 실행 방식",
        "## 5. Git 원격 저장소 및 브랜치",
        "## 6. 배포 방식",
        "## 7. 애플리케이션 특이사항",
        "## 8. 애플리케이션 사용 환경 변수 목록",
        "## 9. AI 구현 지침",
        "## 10. 구축 대상 기능 분류",
        "### 핵심 도메인 개념",
        "#### [도메인 개념 또는 식별자 묶음]",
        "### 기능 분류 트리",
        "### 현재 구현 연결",
        "| local |",
        "| dev | dev |",
        "| prod | main |",
        "`@` 참조",
        "문서 링크",
        "현재 상태",
        "목적만 정의됨",
        ".ai-docs/harness/artifact-routing.json",
        "artifact 의미와 대상 앱",
    )
    context_template = (SKILL_ROOT / "templates" / "AGENTS.md.template").read_text(
        encoding="utf-8"
    )
    if "## 4. 핵심 도메인 개념" in context_template:
        raise AssertionError("app context template still contains core-domain section")
    if "| qa |" in context_template or "dev/qa/prod" in context_template:
        raise AssertionError("app context template still contains the removed qa default")
    require(
        SKILL_ROOT / "templates" / "data-standard-instruction.md.template",
        "# 데이터 명칭·용어·약어·코드 표준 지침",
        "논리명·물리명",
        "최초에는 위 목적 설명만 둔다",
        "변경 이력은 남기지 않는다",
    )
    require(
        SKILL_ROOT / "prompts" / "instruction-lifecycle.md",
        "## 현재 사실 전용 계약",
        "## 초기 기본 세트",
        "architecture-instruction.md",
        "data-standard-instruction.md",
        "code-style-instruction.md",
        "framework-instruction.md",
        "file-convention-instruction.md",
        "## 불필요 파일 삭제",
        "해당 통신 방식의 존재만으로 만들지",
        "실제 앱 이름과 현재 기술 스택",
        "앱 context 9번",
        "파일과 인덱스 행",
        "`agent-instruction.md`와 `artifact-output-routing-instruction.md`는 삭제 후보가 아니다",
    )
    skeleton_templates = {
        "agent-instruction.md.template": "# AI Agent 구현 지침",
        "architecture-instruction.md.template": "# 아키텍처 제약 지침",
        "data-standard-instruction.md.template": "# 데이터 명칭·용어·약어·코드 표준 지침",
        "code-style-instruction.md.template": "# 코드 스타일 지침",
        "framework-instruction.md.template": "# 프레임워크·라이브러리 사용 지침",
        "file-convention-instruction.md.template": "# 파일 구성 지침",
        "api-instruction.md.template": "# API 설계 지침",
        "comm-instruction.md.template": "# 비-HTTP 통신 지침",
    }
    for name, title in skeleton_templates.items():
        template = (SKILL_ROOT / "templates" / name).read_text(encoding="utf-8")
        if title not in template:
            raise AssertionError(f"{name}: missing universal purpose title")
        if "최초에는 위 목적 설명만" not in template:
            raise AssertionError(f"{name}: missing purpose-only initial state")
        if "변경 이력" not in template:
            raise AssertionError(f"{name}: missing current-facts-only contract")
        if "- [규칙]" in template or "| | |" in template:
            raise AssertionError(f"{name}: initial skeleton contains placeholder rule data")
    require(
        SKILL_ROOT / "prompts" / "design-sync.md",
        "양방향",
        "구축 대상 기능 분류 양방향 추적",
        "노드명·순서·부모-자식 관계·",
        "Depth로 재구성",
        "공개 `design-doc` workflow",
        "변경 전 값",
    )
    require(
        SKILL_ROOT / "prompts" / "analysis-claude.md",
        "`local`, `dev`, `prod`",
        "`dev`, `main` branch",
        "Git 원격 저장소 및 브랜치",
        "핵심 도메인 개념`을 독립된 최상위 섹션으로 만들지 않고",
        "## 10. 구축 대상 기능 분류",
        "Markdown 상대 링크",
    )
    require(
        SKILL_ROOT / "templates" / "CLAUDE.md.template",
        "plugin 이름 기반 경로를 만들지 않는다",
    )
    for prompt in ("analysis-instruction.md", "parallel-setup.md"):
        require(SKILL_ROOT / "prompts" / prompt, "artifact 의미", "대상 앱")

    evals = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    ids = [case["id"] for case in evals["evals"]]
    if ids != [1, 2, 3, 4, 5, 6, 7, 8]:
        raise AssertionError(f"unexpected eval ids: {ids}")
    if "_inbox" not in evals["evals"][3]["expected_output"]:
        raise AssertionError("external producer eval must require inbox-only proposal")
    if any("CLAUDE.md는 bridge" in case["expected_output"] for case in evals["evals"]):
        raise AssertionError("context-doc eval still assigns root bridge ownership")

    print("context-doc portable routing evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
