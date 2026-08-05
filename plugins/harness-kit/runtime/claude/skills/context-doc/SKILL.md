---
name: context-doc
description: >
  설계 문서나 PRD가 완성된 후 AI Agent용 컨텍스트 파일을 만들 때 사용한다.
  'AGENTS.md 만들어줘', 'CLAUDE.md 만들어줘', '컨텍스트 문서 생성', 'instruction 작성',
  '.docs/instruction 생성', '규칙 문서 생성', '프로젝트 규칙 파일',
  '에이전트 가이드 만들어줘' 요청이 오면 반드시 이 스킬을 쓴다.
  설계 문서 → 얇은 AGENTS.md 정본(프로젝트 팩트 + 인덱스) + CLAUDE.md bridge + 주제별 .docs/instruction/*-instruction.md 자동 생성.
  산출물 위치·소유권·인계 기준인 `@.docs/instruction/artifact-output-routing-instruction.md`
  (복수 앱은 `@.docs/{앱}/instruction/artifact-output-routing-instruction.md`)를 단일 앱·복수 앱
  모두에서 항상 생성한다.
  프레임워크 종속성이 없으며, 설계 문서에 등장한 주제만 분할 파일로 생성한다.
allowed-tools: Read, Glob, Grep, Write, Agent
---

# Context 문서 생성 (context-doc)

---

## STEP 0 — 플랫폼·실행 방식 확인 + 프로젝트 유형 확인

### STEP 0-0 — 상위 산출물 bundle 확인

상위 producer가 전달한 실행 컨텍스트가 있는지 먼저 확인한다.

- `artifact_bundle_id`가 있으면 그 값과 `handoff_owner`를 그대로 보존한다.
- `handoff_owner != context-doc`이면 `suppress_child_handoff = true`로 유지한다.
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
3. 판정 결과 + 적용 대상 애플리케이션(폴더)을 사용자에게 **반드시 재확인**한다.
4. 설계 문서(`.docs/context-base/DESIGN.md` 또는 `.docs/{앱}/context-base/DESIGN.md`) 위치를 확인하여 참조 설정을 명시한다.
5. 확인된 범위 밖은 건드리지 않는다.
6. `.docs/harness/artifact-routing.json`과 `artifact-format-contract.json`이 있으면 함께
   읽어 artifact 의미·대상 앱·필수 형식을 결정한다. 없으면 경로를 추정 생성하지 않고
   `harness-setup` 실행을 안내한다.

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
| 1 | `architecture-instruction.md` | 모듈·레이어 경계·의존성 규칙이 있을 때 |
| 2 | `code-style-instruction.md` | 네이밍·예외처리·주석 규칙이 있을 때 |
| 3 | `framework-instruction.md` | 라이브러리별 사용 규칙이 있을 때 |
| 4 | `api-instruction.md` | API 엔드포인트·요청/응답 규약이 있을 때 |
| 5 | `comm-instruction.md` | WebSocket·메시지큐 등 통신 규약이 있을 때 |
| 6 | `file-convention-instruction.md` | 파일 위치·네이밍 규칙이 있을 때 |
| 7 | `agent-instruction.md` | 항상 생성 |
| 8 | `artifact-output-routing-instruction.md` | 항상 생성; 산출물 경로·owner·handoff 정본 |

순차 선택 시 Step 1로 직접 진행한다.

---

design-doc 스킬의 OUTPUT 또는 별도 설계 문서를 입력받아
AI Agent가 개발에 활용할 수 있는 Context 문서 세트를 생성한다.

- `AGENTS.md` — 프로젝트 루트에 위치하는 **얇은 프로젝트 팩트 + 지침 인덱스** 정본
- `CLAUDE.md` — `@AGENTS.md` bridge와 Claude 전용 차이만 담는 파일
- `.docs/instruction/*-instruction.md` — 주제별로 분리된 코딩 지침 (설계 문서에 등장한 주제만 생성)
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
- 예산이 소진되면 더 묻지 않고 `미정 — [이유]` 또는 설계 보강 요청으로 처리한다.

## 설계 원칙

1. **AGENTS.md는 얇게 유지한다.** 프로젝트 팩트(기술 스택·아키텍처·실행 방법·환경 변수·주의사항)와 인덱스만 둔다.
2. **CLAUDE.md는 bridge로 유지한다.** 공통 본문을 복제하지 않고 `@AGENTS.md`와 Claude 전용 차이만 둔다.
3. **규칙은 주제별로 분리한다.** Agent가 필요한 주제만 찾아 참조할 수 있게 한다.
4. **프레임워크를 하드코딩하지 않는다.** 설계 문서에 등장한 라이브러리·주제를 그대로 반영한다.
5. **설계 문서에 없는 주제는 파일을 만들지 않는다.** 단,
   `artifact-output-routing-instruction.md`는 산출물 경계 정본이므로 이 원칙의
   유일한 항상 생성 예외다. 빈 주제 파일·추측 규칙은 금지한다.
6. **금지 항목은 삼위일체(패턴·이유·대안)로 작성한다.**

## 스킬 연계

```
design-doc (설계 인터뷰 → OUTPUT 문서)
    ↓ OUTPUT 문서를 그대로 이 스킬에 입력
context-doc → AGENTS.md 정본 + CLAUDE.md bridge + .docs/instruction/*-instruction.md
```

> 아래 섹션 번호는 `design-doc`의 **OUTPUT_V2 기준**이다. V1 OUTPUT은 번호 체계가 다르므로 비권장.

design-doc OUTPUT의 각 섹션은 아래와 같이 매핑된다.

| design-doc OUTPUT 섹션 | 생성 대상 |
|------------------------|----------|
| 01 개요, 05 데이터, 07 라이브러리 | AGENTS.md — 프로젝트 팩트 |
| 06 파일 구성 | AGENTS.md(트리) + architecture-instruction.md + file-convention-instruction.md |
| 02 동작 흐름 | comm-instruction.md |
| 03 집중 로직 | architecture-instruction.md + framework-instruction.md |
| 04 인터페이스 | api-instruction.md + comm-instruction.md |
| 07 라이브러리 | framework-instruction.md |
| 11 부가 정보 | AGENTS.md — 실행 방법 + 환경 변수 + 배포 힌트 |
| 10 주의사항 | code-style-instruction.md / agent-instruction.md / 각 주제 금지 목록 |
| 12 열린 결정 | 해당 주제 파일의 `미정` 섹션 |

---

## 분할 파일 카탈로그

설계 문서에서 해당 내용이 발견될 때만 생성한다. 없으면 만들지 않는다.

| 파일 | 생성 조건 |
|------|----------|
| `architecture-instruction.md` | 모듈·레이어 경계, 의존성 방향, 책임 분리 규칙이 있을 때 |
| `code-style-instruction.md` | 네이밍·타입힌트·예외 처리·주석 스타일 규칙이 있을 때 |
| `framework-instruction.md` | 라이브러리별 사용 규칙/금지 패턴이 있을 때 |
| `api-instruction.md` | API 엔드포인트·요청/응답 스키마 규약이 있을 때 |
| `comm-instruction.md` | WebSocket·메시지큐·RPC 등 통신 프로토콜 규약이 있을 때 |
| `file-convention-instruction.md` | 파일 위치·네이밍·디렉토리 추가 기준이 있을 때 |
| `agent-instruction.md` | 항상 생성 (AI가 사람과 다르게 행동해야 할 규칙 집합) |

---

## 워크플로우

### Step 1 — 입력 문서 수집

설계 문서가 제공되지 않은 경우 요청한다.

> "AGENTS.md, CLAUDE.md bridge와 instruction 문서를 생성할 설계 문서를 공유해 주세요.
> design-doc 스킬의 결과물이나 기존 PRD/설계서 모두 가능합니다."

---

### Step 2 — 구조 판정

설계 문서 `06 파일 구성`의 디렉토리 트리를 읽어 아래를 판정한다.

- **모노레포 여부**: `frontend/`·`backend/`·`fe/`·`be/`·`client/`·`server/` 등 **명시적 분리**가 보이는가
- **분할 대상 파일**: 위 카탈로그에서 어떤 파일을 생성할지 결정

모노레포로 감지되면 사용자에게 1회 확인한다.
이 질문은 전체 질문 예산에 포함된다.

> "디렉토리 트리에 프론트/백엔드 디렉토리 분리가 보입니다.
> `.docs/instruction/`을 프로젝트별로 분리할까요, 루트에 통합할까요?"

---

### Step 3-A — AGENTS.md 분석

`prompts/analysis-claude.md` 기준으로 설계 문서를 분석하여 **프로젝트 팩트**만 추출한다.
추출한 본문은 `AGENTS.md` 정본에 사용한다. `CLAUDE.md`에는 공통 본문을 복제하지 않는다.
**질문은 0~1개만** 한다. (전체 질문 예산 최대 3회 안에서만 허용)
누락 항목은 `미정 — [이유]` 로 표시한다.

---

### Step 3-B — instruction 분석 및 주제 분류

`prompts/analysis-instruction.md` 기준으로 설계 문서를 분석하여
**주제별로 규칙을 분류**한다. 각 주제마다 다음을 모은다.

- 규칙 본문
- 금지 패턴 + 이유 + 대안 (삼위일체)
- 예시 스니펫 (핵심 패턴만)

**질문은 0~1개만** 한다. Step 3-A에서 이미 질문했다면 기본적으로 질문하지 않는다.
예외가 필요한 경우에도 **전체 질문 예산 안에서만** 허용하며, 이 단계의 질문은 금지 삼위일체 확인까지 포함한 **단 1회**다.
누락 항목은 `미정 — [이유]` 로 표시한다.

주제별 분류가 끝나면 **어떤 파일을 생성할지 목록을 확정**한다.

---

### Step 3-C — 문서 충분성 게이트

아래 핵심 섹션 `01 / 03 / 06 / 07 / 10 / 11` 중
**구체적 사실이나 규칙이 있는 섹션이 3개 미만**이면 바로 Step 4로 넘어가지 않는다.

- 이 경우 대부분의 결과물이 `미정` 위주 뼈대가 되므로,
  **컨텍스트 고정 문서로 저장하지 않고** 설계 보강을 요청한다.
- `12 열린 결정 사항`이 풍부해도 핵심 섹션이 빈약하면 충분한 입력으로 간주하지 않는다.

> "핵심 설계 정보가 부족해 현재 상태로는 `CLAUDE.md`, `AGENTS.md`와 instruction 문서를 고정 맥락으로 저장하기 어렵습니다.
> 우선 01/03/06/07/10/11 중 비어 있는 섹션을 보강해 주세요."

---

### Step 3-D — 병렬 모델 확정 (STEP 0에서 병렬 선호 시에만)

STEP 0에서 병렬을 선택한 경우, Step 3-B에서 확정된 생성 파일 목록을 사용하여
`prompts/parallel-setup.md`의 [모델 확정] 절차를 실행한다.

순차를 선택했거나 병렬 실행 능력이 없는 경우 이 Step을 건너뛴다.

---

### Step 4 — 문서 초안 생성

`templates/` 하위 템플릿을 참조하여 각 파일 초안을 작성한다.

- `templates/AGENTS.md.template` — `AGENTS.md` 정본 본문으로 사용
- `templates/CLAUDE.md.template` — `@AGENTS.md` bridge로 사용
- `templates/architecture-instruction.md.template`
- `templates/code-style-instruction.md.template`
- `templates/framework-instruction.md.template`
- `templates/api-instruction.md.template`
- `templates/comm-instruction.md.template`
- `templates/file-convention-instruction.md.template`
- `templates/agent-instruction.md.template`
- `templates/artifact-output-routing-instruction.md.template` — 산출물 routing·owner·handoff 템플릿 (항상 사용)

작성 원칙:
- 확실하지 않은 항목은 `미정 — [이유]` 로 표시하고 생략하지 않는다.
- 설계 문서의 "열린 결정 사항"은 그대로 전달한다.
- `OUTPUT_V2`의 `11 부가 정보`에 있는 실행/배포/env 정보는 `AGENTS.md`의 `5. 실행 방법`, `6. 환경 변수`에 우선 반영한다.
- 코드 예시는 핵심 패턴만, 완성 코드는 포함하지 않는다.
- **AGENTS.md의 인덱스와 실제 생성 파일 목록이 1:1로 일치**해야 한다.
- `artifact-output-routing-instruction.md`는 AGENTS/앱 context의 `@` 참조와 실제 경로가 1:1로 일치해야 한다.
- existing instruction의 `harness-kit:managed:start/end` marker 밖 규칙은 보존한다. 갱신은
  managed block diff만 보여주고 사용자 승인 뒤에 적용한다.
- 외부 fixed-format bundle은 `.docs/_inbox/{artifact-bundle-id}/artifact-manifest.json`에
  proposal로 기록하며 G12 승인 전 canonical instruction에 병합하지 않는다.
- **CLAUDE.md는 `@AGENTS.md` bridge 구조여야 한다.**
- 각 instruction 파일은 자신의 주제에만 집중한다. 주제 간 중복 금지.

---

### Step 5 — 미리보기 및 사용자 확인

AGENTS.md 정본, CLAUDE.md bridge, 각 instruction 파일 초안을 대화창에 순서대로 출력하고 승인을 요청한다.

> "위 문서들을 검토해 주세요.
> 수정할 부분이 있으면 말씀해 주시고, 이상 없으면 저장 경로를 확인해 드릴게요."

저장 경로 안내:

**단일 애플리케이션:**
- `AGENTS.md` → 프로젝트(애플리케이션) 루트
- `CLAUDE.md` → 프로젝트(애플리케이션) 루트 (`@AGENTS.md` bridge)
- `.docs/instruction/*-instruction.md` → 프로젝트 루트 하위 `.docs/instruction/` 폴더

**복수 애플리케이션:**
- `.docs/{앱}-context.md` → 단일앱의 `AGENTS.md`에 들어갈 내용을 앱별로 작성
- `.docs/{앱}/instruction/*-instruction.md` → 앱별 instruction 폴더에 작성
- 루트 `AGENTS.md`/`CLAUDE.md` → 각 앱의 context 문서와 instruction 위치 정보 및 참조 안내만 관리 (**이 파일은 harness-setup이 최종 갱신**, 이 스킬은 `.docs/root-context/AGENTS.md`, `.docs/root-context/CLAUDE.md` 에 복사본을 갱신)
- `.docs` 하위 폴더 및 문서의 위치·정보 요약을 루트 컨텍스트에 포함

---

### Step 6 — 파일 저장

STEP 0에서 확정한 프로젝트 유형에 따라 저장 경로와 검증 범위를 분기한다.

#### 단일 애플리케이션

1. `.docs/instruction/` 디렉토리가 없으면 생성한다.
2. `AGENTS.md`, `CLAUDE.md`, `.docs/instruction/*-instruction.md` 파일을 저장한다.
3. `artifact-output-routing-instruction.md`를 설계 주제 유무와 관계없이 저장한다.
4. 검증:
   - `AGENTS.md` 인덱스의 `@.docs/instruction/*-instruction.md` 참조가 실제 파일과 1:1 일치
   - `CLAUDE.md`가 `@AGENTS.md` bridge인지 확인
   - 불일치 시 사용자에게 보고하고 수정

#### 복수 애플리케이션

1. `.docs/{앱}/instruction/` 디렉토리가 없으면 생성한다.
2. `.docs/root-context/` 디렉토리가 없으면 생성한다.
3. 아래 파일을 저장한다:
   - `.docs/{앱}-context.md`
   - `.docs/{앱}/instruction/*-instruction.md` (artifact-output-routing 포함)
   - `.docs/root-context/AGENTS.md`, `.docs/root-context/CLAUDE.md`
4. 검증:
   - `.docs/{앱}-context.md`의 instruction 참조가 `.docs/{앱}/instruction/` 내 실제 파일과 1:1 일치
   - `.docs/root-context/CLAUDE.md`가 `@AGENTS.md` bridge인지 확인
   - `.docs/root-context/AGENTS.md`가 각 앱의 context 문서 위치를 올바르게 참조
   - 불일치 시 사용자에게 보고하고 수정

> 이미 존재하는 파일이 있으면 덮어쓰기 전에 사용자에게 알린다.

---

## 문서 개선 후처리

전체 `AGENTS.md`, `CLAUDE.md`, 생성된 instruction 파일의 경로·참조·bridge 검증을
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
`.docs/.harness/humanize-handoffs.json`을 fingerprint 키의 원자적 ledger로 사용한다.
같은 fingerprint에 `proposed`, `skipped`, `rejected`, `applied`, `revalidated` 중
완료 기록이 있으면 다시 제안하지 않는다. 새 결정은 bundle ID, owner, 파일 hash,
결정 시각과 함께 원자적으로 기록하고 승인 반영 후에는 `applied`와 `revalidated`
상태를 순서대로 갱신한다. ledger 자체는 개선 대상 bundle에서 제외한다. ledger를
기록할 수 없으면 bundle당 1회를 보장했다고 보고하지 않고 현재 session 한정임을
알린다.

기본은 개선안 제안이며 승인 없이 파일을 덮어쓰지 않는다. 스킬명, 명령어, 경로,
환경 변수, 정책 문구의 의무 수준은 보존한다. 승인 적용 후 Step 6의 참조·bridge
검증을 다시 수행해야 최종 완료로 보고한다.
