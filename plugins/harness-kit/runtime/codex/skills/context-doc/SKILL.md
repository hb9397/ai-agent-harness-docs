---
name: context-doc
description: >
  설계 문서나 PRD가 완성된 후 AI Agent용 컨텍스트 파일을 만들 때 사용한다.
  'AGENTS.md 만들어줘', 'CLAUDE.md 만들어줘', '컨텍스트 문서 생성', 'instruction 작성',
  '.ai-docs/instruction 생성', '규칙 문서 생성', '프로젝트 규칙 파일',
  '에이전트 가이드 만들어줘' 요청이 오면 반드시 이 스킬을 쓴다.
  앱별 DESIGN.md와 현재 코드·설정·Git 정보를 동기화해 *-context.md의 개요·기술 스택·
  아키텍처·실행 profile·Git·배포·계층형 앱 특이사항·환경 변수·AI 구현 지침·기능 분류와 주제별
  .ai-docs/instruction/*-instruction.md를 생성한다.
  산출물 위치·소유권·인계 기준인 `@.ai-docs/instruction/artifact-output-routing-instruction.md`
  (복수 앱은 `@.ai-docs/{앱}/instruction/artifact-output-routing-instruction.md`)를 단일 앱·복수 앱
  모두에서 항상 생성한다.
  최초 instruction 목적 골격과 이후 현재 규칙 갱신·불필요 파일 삭제 생명주기를 관리한다.
allowed-tools: Read, Glob, Grep, Write, Agent
---

## 문서 루트 계약

이 스킬이 하네스 문서를 읽거나 쓸 때 사용하는 정본은 `.ai-docs/`뿐이다. 작업 전에
`.ai-docs/`와 이전 `.docs/`의 존재를 확인한다. `.docs/`만 있거나 두 경로가 함께
있으면 하네스 문서를 읽거나 쓰지 않고 `harness-setup`의 명시적 문서 루트 이관·충돌
해결을 먼저 요청한다. 이전 경로를 호환 별칭으로 추측하지 않는다. 애플리케이션 소스
작업 자체의 권한과 가능 여부는 이 문서 루트 판정으로 제한하지 않는다.


# Context 문서 생성 (context-doc)

---

## 책임 경계

이 스킬은 애플리케이션의 설계 원칙, 기술 스택, 아키텍처, 실행 profile, Git remote·
branch, 배포, 환경 변수와 주제별 작업 규칙을 앱 context·instruction으로 만든다.
AI가 프로젝트 전체를 어떻게 읽을지 정하는
루트 `AGENTS.md`·`CLAUDE.md`, `.ai-docs/root-context/**`와 `.ai-docs/harness/**`는
`harness-setup`의 관리 범위이며 이 스킬이 만들거나 갱신하지 않는다.

단일 앱도 권한과 소유권을 분리하기 위해 프로젝트 팩트를 루트 `AGENTS.md`에 직접
쓰지 않고 `.ai-docs/{앱}-context.md`에 쓴다. 루트 읽기 지도 반영은 admin이
`harness-setup`으로 수행한다.

## 선택 권한 정책 연계

`.ai-docs/harness/access-control/policy.json`이 없으면 기존 앱 문서 생성 흐름을 유지한다.
이 스킬은 선택 기능인 `project-write-access`를 자동 호출하거나 권한 설정을 요구하지
않는다.

서명 정책이 있으면 STEP 0-B에서 대상 앱을 확정하고 STEP 3-B에서 실제 변경 파일
목록을 확정한 뒤 다음을 수행한다.

1. `.ai-docs/harness/access-control/write-access-instruction.md`를 읽는다.
2. `.ai-docs`를 추적하는 Git 경계의 `harness.writeAccess.provider`,
   `harness.writeAccess.host`, `harness.writeAccess.account`를 현재 신원으로 읽는다.
3. 프로젝트에 설치된 `write_access_guard.py check-path`로 앱 context와 생성·갱신·삭제할 모든
   `*-instruction.md`의 정확한 경로를 한꺼번에 검사한다. 정책·서명·변경 목록을
   검증하지 못하면 쓰지 않는다.
4. `pm-pl`은 모든 앱, `app-doc-lead`는 배정된 앱에서만 진행한다. `admin`은 앱 문서
   권한을 상속하지 않는다. 같은 사람이 두 범위를 맡으면 정책에 역할을 각각 배정한다.
5. 권한이 없으면 역할·정책을 추측해 고치지 않고 초안과 필요한 역할만 보고한다.

guard의 `decision=confirm`은 권한은 있으나 앱 핵심 문서 쓰기 전에 별도 승인이
필요하다는 뜻이다. 다른 스킬이 `context-doc`을 선택한 경우에도 STEP 5의 권한 확인을
생략하지 않는다.

---

## STEP 0 — 플랫폼·실행 방식 확인 + 프로젝트 유형 확인

### STEP 0-0 — 상위 산출물 bundle 확인

상위 producer가 전달한 실행 컨텍스트가 있는지 먼저 확인한다.

- `artifact_bundle_id`가 있으면 그 값과 `handoff_owner`를 그대로 보존한다.
- `handoff_owner != context-doc`이면 `suppress_child_handoff = true`로 유지한다.
- 상위 공개 workflow가 `confirmed_scope`를 전달했다면 값을 바꾸지 않고 STEP 0-B의
  현재 탐색 결과와 대조한다.
- 전달된 컨텍스트가 없으면 직접 호출로 표시하고, STEP 0-B에서 프로젝트 루트를
  확정한 직후 다음 값을 만든다.

```text
artifact_bundle_id = context-doc:{정규화한 프로젝트 루트}:{이번 실행의 고유 ID}
handoff_owner = context-doc
suppress_child_handoff = false
handoff_completed = false
```

같은 `artifact_bundle_id`로 초안 재생성이나 승인 반영을 반복해도 새 bundle로
취급하지 않는다.

### STEP 0-A — 플랫폼·실행 방식 확인

`prompts/parallel-setup.md`의 능력 기반 절차를 따른다. 현재 호스트의 병렬 작업 능력은
노출된 도구로 판단하고, 관찰 가능한 플랫폼 이름을 사용자에게 다시 묻지 않는다.
병렬 미지원 또는 미사용 선택 시 순차 실행한다.

### STEP 0-B — 프로젝트 유형 확인 (C-1 확인 단계)

컨텍스트 문서 생성 범위를 확정하기 위해 **반드시** 아래를 수행한다.

1. 현재 수행 위치에서 프로젝트 구조를 탐색한다 (git repo 경계, 하위 앱 폴더 후보 스캔).
2. **단일 애플리케이션 프로젝트**인지 **복수 애플리케이션 프로젝트**인지 판정한다.
3. 설계 문서(`.ai-docs/context-base/DESIGN.md` 또는
   `.ai-docs/{앱}/context-base/DESIGN.md`)와 instruction 루트 위치를 확인한다.
4. 상위 공개 workflow가 `confirmed_scope`를 전달했다면 프로젝트 루트, 단일·복수 앱
   판정, 대상 앱, 설계 경로와 instruction 루트가 현재 탐색 결과와 모두 일치하는지
   확인한다.
5. 일치하는 `confirmed_scope`에는 이미 받은 범위 승인을 재사용하고 같은 질문을 반복하지
   않는다. 값이 없거나 하나라도 다르면 판정 결과와 적용 대상 애플리케이션을 사용자에게
   **반드시 재확인**한다.
6. 확인된 범위 밖은 건드리지 않는다.
7. `.ai-docs/harness/artifact-routing.json`과 `artifact-format-contract.json`이 있으면 함께
   읽어 artifact 의미·대상 앱·필수 형식을 결정한다. 없으면 경로를 추정 생성하지 않고
   `harness-setup` 실행을 안내한다.

`confirmed_scope`는 `design-doc`과 같은 공개 handoff 계약을 사용한다. 이 계약은 범위
확인만 재사용하며 Step 5의 일반 저장 승인과 권한 정책의 앱 핵심 문서 별도 승인을
대신하지 않는다.

> ✋ **확인 게이트**
>
> - 프로젝트 유형: **단일 / 복수** 애플리케이션
> - 적용 대상 애플리케이션(폴더): `{폴더명}`
> - 참조 설계 문서: `{DESIGN 경로}`
>
> 맞습니까? **(승인 / 수정 / 취소)**

### STEP 0-C — 병렬 작업 후보 안내 (STEP 0-A에서 병렬 선호 시에만)

`prompts/parallel-setup.md`의 [플랫폼 확인] → [모델 목록 표시] → [실행 방식 선택 — 선호도만 저장] 절차를 따른다.

병렬 선호 시 아래 작업 후보 목록을 미리 안내한다.
실제 생성할 파일은 Step 3-B 분석 후 확정되며, 확정 시점에 `prompts/parallel-setup.md`의 [모델 확정] 절차를 실행한다.

| # | 작업 (instruction 파일) | 생성 조건 |
|---|------------------------|----------|
| 1 | `architecture-instruction.md` | 최초 목적 골격; 이후 현재 구조 규칙으로 갱신 |
| 2 | `data-standard-instruction.md` | 최초 목적 골격; 이후 현재 데이터 표준으로 갱신 |
| 3 | `code-style-instruction.md` | 최초 목적 골격; 이후 현재 코드 규칙으로 갱신 |
| 4 | `framework-instruction.md` | 최초 목적 골격; 이후 현재 라이브러리 규칙으로 갱신 |
| 5 | `api-instruction.md` | API 엔드포인트·요청/응답 규약이 있을 때 |
| 6 | `comm-instruction.md` | WebSocket·메시지큐 등 통신 규약이 있을 때 |
| 7 | `file-convention-instruction.md` | 최초 목적 골격; 이후 현재 파일 규칙으로 갱신 |
| 8 | `agent-instruction.md` | 항상 생성 |
| 9 | `artifact-output-routing-instruction.md` | 항상 생성; 산출물 경로·owner·handoff 정본 |

순차 선택 시 Step 1로 직접 진행한다.

---

대상 앱의 `DESIGN.md`와 현재 코드·설정·Git 정보를 입력받아 AI Agent가 개발에
활용할 수 있는 Context 문서 세트를 생성한다. 상세 설계·PRD는 보조 입력으로만 사용한다.

- `.ai-docs/{앱}-context.md` — `DESIGN.md`와 양방향 추적하는 애플리케이션의
  **상세 실행 팩트 + AI 구현 지침 인덱스 + 기능 분류 추적** 정본
- `.ai-docs/instruction/*-instruction.md` — 최초 목적 골격에서 현재 적용 규칙으로 갱신되는 주제별 지침
- `artifact-output-routing-instruction.md` — 단일/복수 앱 산출물 위치·소유권·승인·인계 정본 (항상 생성)

생성 전 반드시 사용자 확인을 거친다. 파일을 무단으로 수정하지 않는다.

> 이 문서들은 AI Agent가 코드를 작성할 때 매 요청마다 참조하는 핵심 컨텍스트다.
> 모호한 서술, 중복, 미결 항목 방치는 Agent의 잘못된 코드 생성으로 직결된다.
> 정밀하고 오해 없는 표현을 최우선으로 한다.

## 질문 예산

사용자 질문 총합은 **최대 3회**다.

- **필수 확인 최대 2개**: 설계 문서만으로 확정 불가능한 핵심 사실만 묻는다.
- **선택 확인 최대 1개**: 모노레포 배치나 저장 위치처럼 운영상 결정이 필요할 때만 묻는다.
- Step 2의 모노레포 배치 질문도 이 예산에 포함한다.
- Step 3-B의 금지 삼위일체 확인은 **추가 질문이 아니라 Step 3-B 할당분을 소비**한다.
- 예산이 소진되면 앱 context는 `미정 — [이유]` 또는 설계 보강으로, instruction의
  미확정 후보는 본문 밖 검토 항목으로 처리한다.

## 설계 원칙

1. **앱 context는 구현에 필요한 상세 사실만 유지한다.** 개요·기술 스택·아키텍처·
   실행 profile·Git·배포·계층형 앱 특이사항·환경 변수·instruction 인덱스와 기능 분류
   추적을 두되 DB 절차와 세부 규칙은 해당 섹션·instruction으로 분리한다.
2. **루트 컨텍스트를 수정하지 않는다.** 루트 `AGENTS.md`·`CLAUDE.md`와 `.ai-docs/root-context/**`는 harness-setup에 맡긴다.
3. **규칙은 주제별로 분리한다.** Agent가 필요한 주제만 찾아 참조할 수 있게 한다.
4. **프레임워크를 하드코딩하지 않는다.** 설계 문서에 등장한 라이브러리·주제를 그대로 반영한다.
5. **instruction 생명주기를 관리한다.** 최초 목적 골격, 이후 현재 규칙 갱신과 불필요
   파일 삭제 기준은 `prompts/instruction-lifecycle.md`를 따른다.
6. **금지 항목은 삼위일체(패턴·이유·대안)로 작성한다.**

## 스킬 연계

```
design-doc (앱별 PROJECT_DESIGN 정본)
    ↓ DESIGN.md + 현재 앱 코드·설정·Git 정보
context-doc → 앱별 *-context.md 정본 + .ai-docs/{앱}/instruction/*-instruction.md
    ↘ 상위 설계 drift 발견 시 공개 design-doc 갱신 제안
```

`DESIGN.md`와 앱 context의 역할·양방향 최신화 규칙은 `prompts/design-sync.md`를 따른다.
PROJECT_DESIGN과 현재 앱 자료는 다음처럼 매핑한다.

| 입력 | 앱 context 또는 instruction |
|---|---|
| 제목·요약, 01 개요 | 제목·요약, 1 프로젝트 개요 |
| 02 구축 대상 기능 분류 | 10 구축 대상 기능 분류 |
| 03 기술 스택 | 2 기술 스택 + framework-instruction.md 후보 |
| 04 아키텍처 | 3 아키텍처 + architecture/file-convention instruction 후보 |
| 실행 설정·명령·엔트리포인트 | 4 실행 프로필 및 실행 방식 |
| Git config·HEAD·refs | 5 Git 원격 저장소 및 브랜치 |
| 06 배포 환경 + 배포 설정 | 6 배포 방식 |
| 05 애플리케이션 특이사항 + 현재 앱 고유 사실·핵심 도메인 개념 | 7 계층형 애플리케이션 특이사항 + 주제별 instruction 후보 |
| 환경 설정·코드의 환경 변수 참조 | 8 애플리케이션 사용 환경 변수 목록 |
| 실제 instruction 파일 | 9 AI 구현 지침 |

화면·기능 단위 `OUTPUT_V2`, 기존 PRD와 `harness-bootstrap` 코드 인벤토리는 보조 입력으로
사용할 수 있지만 대상 앱의 `DESIGN.md`를 대체하지 않는다.

---

## 분할 파일 카탈로그

최초 생성·조건부 확장·항상 유지·후속 삭제 판정은 `prompts/instruction-lifecycle.md`를
따른다. 아래 표는 주제 분류 카탈로그다.

| 파일 | 생성 조건 |
|------|----------|
| `architecture-instruction.md` | 모듈·레이어 경계, 의존성 방향, 책임 분리 규칙이 있을 때 |
| `data-standard-instruction.md` | 앱 고유 용어·식별자·코드 표준이 있을 때 |
| `code-style-instruction.md` | 네이밍·타입힌트·예외 처리·주석 스타일 규칙이 있을 때 |
| `framework-instruction.md` | 라이브러리별 사용 규칙/금지 패턴이 있을 때 |
| `api-instruction.md` | API 엔드포인트·요청/응답 스키마 규약이 있을 때 |
| `comm-instruction.md` | WebSocket·메시지큐·RPC 등 통신 프로토콜 규약이 있을 때 |
| `file-convention-instruction.md` | 파일 위치·네이밍·디렉토리 추가 기준이 있을 때 |
| `agent-instruction.md` | 항상 생성 (AI가 사람과 다르게 행동해야 할 규칙 집합) |
| `artifact-output-routing-instruction.md` | 항상 생성 (산출물 위치·소유권·승인·인계 정본) |

---

## 워크플로우

### Step 1 — 입력 문서 수집

대상 앱과 대응하는 `DESIGN.md`를 먼저 찾고, 현재 앱 source root의 매니페스트·실행
설정·배포 파일·환경 변수 참조와 Git metadata를 함께 수집한다. 기존 `{앱}-context.md`와
instruction root가 있으면 전체를 현재 사실 후보로 읽는다.

`DESIGN.md`가 없으면 앱 context를 독립 정본으로 만들지 않고 요청한다.

> "대상 앱의 `DESIGN.md`가 필요합니다. 먼저 `design-doc`으로 앱 설계 정본을 만들거나
> 현재 DESIGN.md 경로를 알려주세요. 기존 PRD와 상세 설계는 보조 자료로 함께 사용할 수 있습니다."

`prompts/design-sync.md`의 현재 상태에 맞는 분기를 적용해 공통 주제와 상세 운영 사실을
구분한다.

---

### Step 2 — 구조 판정

확정한 앱 source root와 `DESIGN.md`의 아키텍처, 현재 디렉토리 구조를 읽어 아래를 판정한다.

- **모노레포 여부**: `frontend/`·`backend/`·`fe/`·`be/`·`client/`·`server/` 등 **명시적 분리**가 보이는가
- **분할 대상 파일**: 위 카탈로그에서 어떤 파일을 생성할지 결정
- **실행·Git·배포 근거**: profile 설정, 실행 명령, Git remote·branch, Kubernetes·
  컨테이너·빌드 결과물과 환경 변수를 어디서 확인할지 결정

모노레포로 감지되면 사용자에게 1회 확인한다.
이 질문은 전체 질문 예산에 포함된다.

> "디렉토리 트리에 프론트/백엔드 디렉토리 분리가 보입니다.
> `.ai-docs/instruction/`을 프로젝트별로 분리할까요, 루트에 통합할까요?"

---

### Step 3-A — 앱 context 분석

`prompts/analysis-claude.md`와 `prompts/design-sync.md` 기준으로 `DESIGN.md`, 현재 앱 자료와
기존 context를 분석하여 **애플리케이션 팩트**만 추출한다.
추출한 본문은 `.ai-docs/{앱}-context.md` 정본에 사용한다. 루트 컨텍스트에는 복제하지 않는다.
**질문은 0~1개만** 한다. (전체 질문 예산 최대 3회 안에서만 허용)
누락한 앱 context 항목은 `미정 — [이유]`로 표시한다.

---

### Step 3-B — instruction 분석 및 주제 분류

`prompts/analysis-instruction.md` 기준으로 설계 문서를 분석하여
**주제별로 규칙을 분류**한다. 각 주제마다 다음을 모은다.

- 규칙 본문
- 금지 패턴 + 이유 + 대안 (삼위일체)
- 예시 스니펫 (핵심 패턴만)

**질문은 0~1개만** 한다. Step 3-A에서 이미 질문했다면 기본적으로 질문하지 않는다.
예외가 필요한 경우에도 **전체 질문 예산 안에서만** 허용하며, 이 단계의 질문은 금지 삼위일체 확인까지 포함한 **단 1회**다.
미확정 규칙은 instruction 본문에 `미정`으로 넣지 않고 검토 화면의 보강 후보로 둔다.

주제별 분류 뒤 `prompts/instruction-lifecycle.md`로 각 파일을 `항상 유지 / 최초 목적
골격 / 적용 중 / 삭제 후보` 중 하나로 판정하고 생성·갱신·삭제 목록을 확정한다.

---

### Step 3-C — 문서 충분성 게이트

`DESIGN.md`의 `01 개요 / 03 기술 스택 / 04 아키텍처 / 05 애플리케이션 특이사항 /
06 배포 환경`과 현재 앱의 실행·Git·환경 설정을 확인한다. 이 중 **구체적인 현재 사실을
확인할 수 있는 묶음이 3개 미만**이면 바로 Step 4로 넘어가지 않는다.

- 이 경우 대부분의 결과물이 `미정` 위주 뼈대가 되므로,
  **컨텍스트 고정 문서로 저장하지 않고** 설계 보강을 요청한다.
- 열린 결정이 많아도 핵심 현재 사실이 빈약하면 충분한 입력으로 간주하지 않는다.

> "핵심 설계 정보가 부족해 현재 상태로는 앱 context와 instruction 문서를 고정 맥락으로 저장하기 어렵습니다.
> 우선 DESIGN.md의 개요·기술 스택·아키텍처·앱 특이사항·배포 환경과 현재 앱의
> 실행·Git·환경 설정 중 확인 가능한 내용을 보강해 주세요."

---

### Step 3-D — 병렬 모델 확정 (STEP 0에서 병렬 선호 시에만)

STEP 0에서 병렬을 선택한 경우, Step 3-B에서 확정된 생성 파일 목록을 사용하여
`prompts/parallel-setup.md`의 [모델 확정] 절차를 실행한다.

순차를 선택했거나 병렬 실행 능력이 없는 경우 이 Step을 건너뛴다.

---

### Step 4 — 문서 초안 생성

`templates/` 하위 템플릿을 참조하여 각 파일 초안을 작성한다.

- `templates/AGENTS.md.template` — 파일명은 호환성을 위해 유지하며 앱 context 본문으로 사용
- `templates/architecture-instruction.md.template`
- `templates/data-standard-instruction.md.template`
- `templates/code-style-instruction.md.template`
- `templates/framework-instruction.md.template`
- `templates/api-instruction.md.template`
- `templates/comm-instruction.md.template`
- `templates/file-convention-instruction.md.template`
- `templates/agent-instruction.md.template`
- `templates/artifact-output-routing-instruction.md.template` — 산출물 routing·owner·handoff 템플릿 (항상 사용)

작성 원칙:
- 제목 바로 아래에 대응 `DESIGN.md`의 `@` 경로·Markdown 링크, 문서 역할과 양방향
  최신화 원칙을 적고 기존 개요 요약을 유지한다.
- 최상단과 `9. AI 구현 지침`에 루트 컨텍스트 → 앱 context → 작업 관련 instruction
  필독 순서를 적는다.
- 앱 context의 확실하지 않은 항목은 `미정 — [이유]` 로 표시한다. profile·branch에
  별도 지시가 없으면 `dev/qa/prod`를 기본 기준으로 제시하되 실제 존재를 단정하지 않는다.
- `4. 실행 프로필 및 실행 방식`과 `6. 배포 방식`에는 DB 생성·migration·seed·접속
  명령을 넣지 않는다.
- 코드 예시는 핵심 패턴만, 완성 코드는 포함하지 않는다.
- **앱 context의 9번 인덱스와 실제 적용되는 instruction 파일이 1:1로 일치**해야 한다.
  기존 팀 고유 instruction도 실제 존재하고 적용되면 보존한다.
- 각 instruction 행에는 `@` 참조와 현재 context 기준 Markdown 링크를 함께 둔다.
- `artifact-output-routing-instruction.md`는 앱 context의 참조·링크와 실제 경로가
  1:1로 일치해야 한다.
- existing instruction의 `harness-kit:managed:start/end` marker 밖 규칙은 보존한다. 갱신은
  managed block diff만 보여주고 사용자 승인 뒤에 적용한다.
- 외부 fixed-format bundle은 `.ai-docs/_inbox/{artifact-bundle-id}/artifact-manifest.json`에
  proposal로 기록하며 G12 승인 전 canonical instruction에 병합하지 않는다.
- 루트 `AGENTS.md`·`CLAUDE.md`와 `.ai-docs/root-context/**`는 생성 목록에 넣지 않는다.
- 각 instruction 파일은 자신의 주제에만 집중한다. 주제 간 중복 금지.
- 앱 context와 모든 instruction 본문은 변경 이력 없이 현재 사실·규칙만 유지한다.
  최초 골격과 후속 갱신·삭제 표현은 `prompts/instruction-lifecycle.md`를 따른다.
- 7번은 `### 핵심 도메인 개념`을 포함하고 `###` → `####` 계층형 하위 노드로
  구성한다. 개념 의미·관계는 7번에 두고 명명·약어·식별자 표현·코드값 규범은
  `data-standard-instruction.md`로 분리한다.
- 10번은 DESIGN.md 02와 노드명·순서·부모-자식 관계·Depth를 양방향 추적하고 현재
  구현 연결을 별도 표로 기록한다. 기능 분류를 구현 허용 목록으로 사용하지 않는다.
- 앱 context 본문은 변경 이력을 누적하지 않고 현재 유효한 사실만 남긴다.

---

### Step 5 — 미리보기 및 사용자 확인

앱 context와 instruction의 생성·갱신 초안, 삭제 후보를 대화창에 순서대로 출력하고
승인을 요청한다. 삭제 후보는 파일 경로·현재 불필요한 근거·9번에서 제거할 행을 함께
보여준다.

> "위 문서들을 검토해 주세요.
> 수정할 부분이 있으면 말씀해 주시고, 이상 없으면 저장 경로를 확인해 드릴게요."

저장 경로 안내:

**단일 애플리케이션:**
- `.ai-docs/{앱}-context.md` → DESIGN.md와 양방향 추적하는 앱의 1~10 상세 컨텍스트와
  AI 구현 지침 인덱스
- `.ai-docs/instruction/*-instruction.md` → 프로젝트 루트 하위 `.ai-docs/instruction/` 폴더

**복수 애플리케이션:**
- `.ai-docs/{앱}-context.md` → DESIGN.md와 양방향 추적하는 앱의 1~10 상세 컨텍스트와
  AI 구현 지침 인덱스
- `.ai-docs/{앱}/instruction/*-instruction.md` → 앱별 instruction 폴더에 작성
- 루트 `AGENTS.md`/`CLAUDE.md`와 `.ai-docs/root-context/**`는 생성하지 않는다. admin이
  `harness-setup`으로 앱 context·instruction 위치를 읽기 지도에 반영한다.

권한 정책이 활성화되어 guard가 `decision=confirm`을 반환했다면 일반 초안 검토·저장
승인과 별도로, 파일 저장 도구를 호출하기 직전에 다음 내용을 보여주고 이 변경에 한해
승인받는다.

> **앱 컨텍스트와 작업 지침 편집 확인**
>
> - 대상 앱: `{애플리케이션}`
> - 대상 파일: `{정확한 *-context.md와 모든 *-instruction.md 경로}`
> - 문서 역할:
>   - `*-context.md`: 대응 DESIGN.md와 양방향 추적하는 앱의 개요·기술 스택·아키텍처·
>     실행 profile·Git·배포·계층형 앱 특이사항·환경 변수·AI 구현 지침 인덱스와 기능 분류
>   - `architecture-instruction.md`: 모듈·레이어 경계와 의존성 규칙
>   - `data-standard-instruction.md`: 앱 고유 용어·식별자·코드 표준
>   - `code-style-instruction.md`: 네이밍·타입·예외 처리·주석 규칙
>   - `framework-instruction.md`: 프레임워크·라이브러리 사용 및 금지 규칙
>   - `api-instruction.md`: API 요청·응답과 엔드포인트 규약
>   - `comm-instruction.md`: WebSocket·메시지큐·RPC 통신 규약
>   - `file-convention-instruction.md`: 파일 위치·이름·디렉토리 추가 규칙
>   - `agent-instruction.md`: AI가 사람과 다르게 지켜야 할 작업 규칙
>   - `artifact-output-routing-instruction.md`: 산출물 위치·소유자·승인·인계 정본
> - 현재 권한: `{pm-pl / app-doc-lead와 앱 범위}`
> - 변경 내용과 이유: `{신규 작성·갱신·삭제 요약}`
>
> 위 변경을 이 파일들에 반영할까요? **(승인 / 수정 / 취소)**

삭제 후보도 정확한 대상 파일에 포함한다. 대상 파일·내용 요약·현재 역할이 달라지면
이전 답변을 재사용하지 않는다. AI 훅의 `permissionDecision=ask`도 같은 확인을
요구하므로 생략하지 않는다.

---

### Step 6 — 파일 저장

STEP 0에서 확정한 프로젝트 유형에 따라 저장 경로와 검증 범위를 분기한다.

#### 단일 애플리케이션

1. `.ai-docs/instruction/` 디렉토리가 없으면 생성한다.
2. `.ai-docs/{앱}-context.md`, `.ai-docs/instruction/*-instruction.md` 파일을 저장한다.
3. `agent-instruction.md`와 `artifact-output-routing-instruction.md`를 설계 주제 유무와
   관계없이 저장한다.
4. 승인된 삭제 후보는 파일과 9번 인덱스 행을 같은 변경에서 제거한다.
5. 검증:
   - `.ai-docs/{앱}-context.md` 제목 아래 DESIGN.md `@` 참조·상대 링크가 정확한지 확인
   - `1`부터 `10`까지 고정 목차와 최상단 구현 전 읽기 순서가 있는지 확인
   - 9번 인덱스의 `@.ai-docs/instruction/*-instruction.md` 참조·Markdown 링크가
     실제 적용 파일과 1:1 일치
   - 7번이 핵심 도메인 개념을 포함한 계층형 노드인지, 10번 기능 분류가 DESIGN.md 02의
     노드명·순서·부모-자식 관계·Depth와 일치하는지 확인
   - 앱 context와 instruction 본문에 과거 값·변경 이력·폐기 규칙이 없는지 확인
   - 루트 `AGENTS.md`·`CLAUDE.md`와 `.ai-docs/root-context/**`를 수정하지 않았는지 확인
   - 불일치 시 사용자에게 보고하고 수정

#### 복수 애플리케이션

1. `.ai-docs/{앱}/instruction/` 디렉토리가 없으면 생성한다.
2. 아래 파일을 저장한다:
   - `.ai-docs/{앱}-context.md`
   - `.ai-docs/{앱}/instruction/*-instruction.md` (artifact-output-routing 포함)
3. 승인된 삭제 후보는 파일과 9번 인덱스 행을 같은 변경에서 제거한다.
4. 검증:
   - `.ai-docs/{앱}-context.md` 제목 아래 DESIGN.md `@` 참조·상대 링크가 정확한지 확인
   - `1`부터 `10`까지 고정 목차와 최상단 구현 전 읽기 순서가 있는지 확인
   - 9번 인덱스의 instruction `@` 참조·Markdown 링크가
     `.ai-docs/{앱}/instruction/` 내 실제 적용 파일과 1:1 일치
   - 7번이 핵심 도메인 개념을 포함한 계층형 노드인지, 10번 기능 분류가 DESIGN.md 02의
     노드명·순서·부모-자식 관계·Depth와 일치하는지 확인
   - 앱 context와 instruction 본문에 과거 값·변경 이력·폐기 규칙이 없는지 확인
   - 루트 `AGENTS.md`·`CLAUDE.md`와 `.ai-docs/root-context/**`를 수정하지 않았는지 확인
   - 불일치 시 사용자에게 보고하고 수정

저장과 검증이 끝나면 루트 읽기 지도 갱신이 필요한지 보고한다. 필요하면 admin이
`harness-setup`을 명시적으로 실행할 후속 작업으로 남긴다. 현재 호출자가 admin인지
추측해 자동 실행하지 않는다.

> 이미 존재하는 파일이 있으면 덮어쓰기 전에 사용자에게 알린다.

---

## 문서 개선 후처리

전체 앱 context와 생성된 instruction 파일의 경로·참조 검증을
마친 뒤 다음 조건을 전부 만족할 때만 bundle 전체를 `humanize-korean`의
`document-refinement` 프로필로 한 번 넘긴다.

- `handoff_owner == context-doc`
- `suppress_child_handoff == false`
- `handoff_completed == false`

상위 `harness-bootstrap` 등에서 전달된 실행이면 초안과 검증 결과만 반환하고
후처리를 제안하지 않는다. 직접 호출에서 handoff를 제안하거나 실행한 뒤에는
`handoff_completed = true`로 기록한다.

새 session·재시도에서도 중복을 막기 위해 최종 검증된 Markdown의 정규화 상대경로와
각 파일 SHA-256, profile 이름을 정렬해 `artifact_bundle_fingerprint`를 계산한다.
`.ai-docs/.harness/humanize-handoffs.json`을 fingerprint 키의 원자적 ledger로 사용한다.
같은 fingerprint에 `proposed`, `skipped`, `rejected`, `applied`, `revalidated` 중
완료 기록이 있으면 다시 제안하지 않는다. 새 결정은 bundle ID, owner, 파일 hash,
결정 시각과 함께 원자적으로 기록하고 승인 반영 후에는 `applied`와 `revalidated`
상태를 순서대로 갱신한다. ledger 자체는 개선 대상 bundle에서 제외한다. ledger를
기록할 수 없으면 bundle당 1회를 보장했다고 보고하지 않고 현재 session 한정임을
알린다.

기본은 개선안 제안이며 승인 없이 파일을 덮어쓰지 않는다. 스킬명, 명령어, 경로,
환경 변수, 정책 문구의 의무 수준은 보존한다. 승인 적용 후 Step 6의 참조
검증을 다시 수행해야 최종 완료로 보고한다.
