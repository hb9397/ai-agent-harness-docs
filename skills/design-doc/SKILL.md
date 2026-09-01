---
name: design-doc
description: >
  새 기능·프로젝트의 도메인 요구사항, 범위, 아키텍처, 데이터와 인수 기준을
  구조화된 설계/PRD로 만들 때 사용한다.
  '설계해줘', '어떻게 만들지 정리해줘', '기획 문서 작성', '요구사항 정리',
  '스펙 작성', 'PRD 만들어줘', 'RFP 분석해서 설계해줘', 'SFR 설계' 요청이 오면 이 스킬로 처리한다.
  인터뷰 또는 RFP/SFR 원문 기반으로 구조화된 설계 문서를 자동 도출한다.
  create-prototype 입력용 화면 배치·컴포넌트 목업 문서만 필요하면
  design-prototype-docs를 사용한다.
allowed-tools: Read, Glob, Write, Agent
---

# 설계 문서 도출 (design-doc)

이 스킬이 호출되면 아래 워크플로우를 순서대로 실행한다.
결과 문서는 대화창에 바로 출력한다. (별도 .md 파일 생성 금지 — 사용자가 요청할 때만 저장)

파일 저장이 승인되면 산출물 위치·소유권·인계는
`@.docs/instruction/artifact-output-routing-instruction.md`를 따른다.
복수 앱은 `@.docs/{앱}/instruction/artifact-output-routing-instruction.md`를
읽고 대상 앱 범위를 유지한다.

> 이 스킬의 OUTPUT은 AI Agent가 개발에 활용하는 Context 문서 / Instruction / Rule / PRD가 될 수 있음을 항상 염두에 두고 작성한다.
> 따라서 모호한 표현, 미결 항목 방치, 중복 서술을 피하고 Agent가 오해 없이 읽을 수 있는 정밀한 문서를 목표로 한다.

---

## 다운스트림 스킬 연계

이 스킬의 OUTPUT은 아래 스킬의 입력으로 바로 사용할 수 있다.

```
design-doc OUTPUT
    ├─→ context-doc      →  앱 context + .docs/{앱}/instruction/*-instruction.md
    ├─→ impl-fe-be-doc   →  FE/BE 페어 또는 화면 중심 작업지침서
    ├─→ impl-doc         →  범용 단계별 구현 지침서
    ├─→ impl-reuse-scan  →  Phase/태스크 시작 직전 공통 자산 발견·보고(자동 반영 금지)
    └─→ impl-verify      →  태스크·Phase 종료 시 검증 매트릭스(코드/지침서 수정 금지)
```

OUTPUT 문서를 저장했다면 해당 파일을 그대로 다음 스킬에 넘기면 된다.
각 스킬의 섹션 매핑은 해당 스킬의 SKILL.md 참조.

---

## 저장 위치 원칙

- 설계 문서를 파일로 저장할 때는 반드시 대상 프로젝트 루트를 먼저 확정한다.
- **단일 애플리케이션**: `{project}/.docs/context-base/DESIGN.md`
- **복수 애플리케이션**: `{project}/.docs/{앱 디렉토리명}/context-base/DESIGN.md` (예: `.docs/fe-acro-portal/context-base/DESIGN.md`)
- 사용자가 다른 파일명을 지정해도 위 `context-base/` 하위에 저장한다.
- 상위 워크스페이스 루트에서 실행 중이어도, 대상 프로젝트가 따로 있으면 상위 루트에 저장하지 않는다.

---

## 선택 권한 정책 연계

`.docs/harness/access-control/policy.json`이 없으면 기존 설계·저장 흐름을 그대로
수행한다. `project-write-access`는 선택 기능이며 이 스킬이 자동 호출하거나 권한
설정을 요구하지 않는다.

서명 정책이 있으면 Step 0-1에서 대상 앱과 `DESIGN.md` 경로를 확정한 직후 다음을
수행한다.

1. `.docs/harness/access-control/write-access-instruction.md`를 읽는다.
2. `.docs`를 추적하는 Git 경계의 `harness.writeAccess.provider`,
   `harness.writeAccess.host`, `harness.writeAccess.account`를 현재 신원으로 읽는다.
3. 프로젝트에 설치된 `write_access_guard.py check-path`에 대상 `DESIGN.md`의 정확한
   경로와 현재 provider·host·account를 전달한다. guard가 정책 서명과 생성 목록까지
   검증하지 못하면 저장하지 않는다.
4. `pm-pl`은 모든 앱, `app-doc-lead`는 정책에 배정된 앱에서만 진행한다. `admin`은
   앱 문서 권한을 상속하지 않으므로 `admin`만 가진 계정은 거부한다. 같은 사람이
   `pm-pl`도 맡는다면 두 역할이 정책에 각각 있어야 한다.
5. 권한이 없으면 정책을 고치거나 역할을 추측하지 않고, 대상 앱·파일과 필요한 역할을
   알려준 뒤 초안만 대화창에 반환한다.

guard의 `decision=confirm`은 권한은 있으나 앱 핵심 문서 쓰기 전에 별도 승인이
필요하다는 뜻이다. 이 승인은 Step 4의 일반 문서 검토·저장 질문과 합치지 않는다.

---
## 워크플로우

### Step 0 — 플랫폼·실행 방식 확인

현재 호스트가 독립 작업을 병렬 실행할 수 있는지는 노출된 도구로 확인한다.
관찰 가능한 플랫폼 이름을 사용자에게 다시 묻지 않는다. 작업이 서로 독립적이고
병렬 실행이 실질적으로 유리할 때만 선호를 확인하며, 미지원 또는 미사용 시 순차 실행한다.

---

### Step 0-1 — 프로젝트 유형 확인 (C-1 확인 단계)

설계 작업 범위를 확정하기 위해 **반드시** 아래를 수행한다.

1. 현재 수행 위치에서 프로젝트 구조를 탐색한다 (git repo 경계, 하위 앱 폴더 후보 스캔).
2. **단일 애플리케이션 프로젝트**인지 **복수 애플리케이션 프로젝트**인지 판정한다.
3. 판정 결과 + 적용 대상 애플리케이션(폴더)을 사용자에게 **반드시 재확인**한다.
4. 확인된 범위 밖은 건드리지 않는다.

> ✋ **확인 게이트**
>
> 탐색 결과:
> - 프로젝트 유형: **단일 / 복수** 애플리케이션
> - 설계 대상 애플리케이션(폴더): `{폴더명}`
> - (복수인 경우) DESIGN 문서 참조 설정: `{DESIGN 경로}`
>
> 맞습니까? **(승인 / 수정 / 취소)**

> 복수 애플리케이션인 경우 기존 `{앱}/context-base/DESIGN.md` 파일 존재 여부도 확인하여, 신규 작성인지 갱신인지 판단한다.

---

### Step 1 — 스케일 확인 및 기존 설계 문서 수집

스킬 호출 시 스케일이 명시되지 않은 경우 사용자에게 묻는다.

> "설계할 대상의 스케일을 알려주세요.
> 1) 화면 단위  2) 기능 단위  3) 컴포넌트 / 로직 단위"

스케일 확인 후, 참고할 기존 설계 문서(PRD, 기획서, DB 설계서, 관련 코드, RFP/SFR 원문 등)가 있는지 묻는다.

> "참고할 기존 문서나 코드가 있으면 파일 또는 텍스트로 공유해 주세요. RFP/SFR 원문, 사용자가 정리한 요구사항, DB 설계가 있으면 함께 주시면 좋겠습니다. 없으면 바로 인터뷰를 시작합니다."

RFP/SFR 원문이 제공되면 별도 사전 스킬을 요구하지 않고 이 스킬 안에서 최소한으로 해석한다.

- 요구사항 ID, 요구사항 명칭, 원문 범위, 필수 기능, 제약, 사용자 역할을 추출한다.
- 화면 후보가 필요한 경우 확정안이 아니라 후보로 표시하고 사용자 확인을 받는다.
- 불명확한 항목은 추측하지 않고 Step 2 인터뷰 질문에 포함한다.
- 삭제된 별도 RFP 처리 스킬의 전체 로직을 복제하지 않는다.

스케일별 양식 매핑은 `prompts/scale-routing.md` 참조.
인터뷰 진행 시 입력 양식이 필요하면 `templates/INPUT_V2.md`를 사용자에게 제공한다.
(사용자가 직접 채워서 제출하는 경우에만. 일반적으로는 Step 2 인터뷰로 대체)

---

### Step 2 — 설계 인터뷰

`prompts/interview.md` 의 질문 목록을 스케일에 맞게 순서대로 진행한다.

- 섹션 순서대로 **한 번에 하나씩** 질문한다.
- 답변이 모호하면 반박하거나 더 파고든다. 넘어가지 않는다.
- H섹션(뒤집기 확인)은 D섹션 직후에 진행한다. 범위가 확정되기 전에 뒤집는 것이 실효성 있다.
- 기존 문서가 있으면 답변과 교차 검증하여 불일치를 짚어낸다.

---

### Step 3 — OUTPUT 문서 작성

인터뷰 완료 후 `templates/OUTPUT_V2.md` 양식을 사용해 문서를 작성한다. (V1은 deprecated)

- 스케일별 OUTPUT 양식은 `prompts/scale-routing.md` 참조.
- 확실하지 않은 항목은 비우지 않고 `미정 — [이유]` 로 표시한다.
- 양식의 작성 지침(주석)은 읽고 반영한 뒤 최종 출력에서 제거한다.
- 해당하지 않는 스케일의 섹션은 소제목째 삭제한다.

프로젝트 스케일의 경우, 07 부가 정보 작성 전에 사용자에게 확인한다.

> "배포 환경, DB 상세, VSCode 익스텐션 추천을 포함할까요?"

---

### Step 4 — 검토 및 확정

OUTPUT 초안을 대화창에 출력하고 사용자에게 확인을 요청한다.

> "위 설계 문서를 검토해 주세요. 수정할 부분이 있으면 말씀해 주세요. 파일로 저장할까요?"

수정 요청 시 해당 섹션만 재작성한다. 파일 저장은 승인 후 진행한다.
권한 정책이 활성화되어 guard가 `decision=confirm`을 반환했다면 저장 도구를 호출하기
직전에 다음 내용을 보여주고 이 변경에 한해 별도 승인을 받는다. 직접 호출뿐 아니라
다른 스킬이 `design-doc`을 선택한 경우에도 생략하지 않는다.

> **앱 설계 기준 문서 편집 확인**
>
> - 대상 앱: `{애플리케이션}`
> - 대상 파일: `{정확한 DESIGN.md 경로}`
> - 문서 역할: `DESIGN.md`는 앱의 요구사항, 범위, 아키텍처, 데이터와 인수 기준을
>   정하는 설계 기준 문서입니다.
> - 현재 권한: `{pm-pl / app-doc-lead와 앱 범위}`
> - 변경 내용과 이유: `{신규 작성 또는 갱신 요약}`
>
> 위 변경을 이 파일에 반영할까요? **(승인 / 수정 / 취소)**

대상 경로·내용 요약·현재 역할이 달라지면 이전 답변을 재사용하지 않는다. AI 훅의
`permissionDecision=ask`도 같은 확인을 요구하므로 생략하지 않는다.

저장 승인 시:
- **단일 앱**: 기본 경로 `{project}/.docs/context-base/DESIGN.md`
- **복수 앱**: 기본 경로 `{project}/.docs/{앱 디렉토리명}/context-base/DESIGN.md`
- `context-base/` 디렉토리가 없으면 생성한다.
- 동일 경로에 파일이 이미 있으면 **갱신**(덮어쓰기 전 사용자 확인)한다.

---

## 문서 개선 후처리와 완료 게이트

직접 호출에서는 다음 실행 컨텍스트를 만들고, 상위 producer가 전달한 값이 있으면
새로 만들지 않고 그대로 보존한다.

```text
artifact_bundle_id = design-doc:{정규화한 프로젝트 루트}:{이번 실행의 고유 ID}
handoff_owner = design-doc
suppress_child_handoff = false
handoff_completed = false
```

상위 producer의 `handoff_owner`가 `design-doc`이 아니면
`suppress_child_handoff = true`로 유지하고 초안과 Step 4 검증 결과만 반환한다.

최종 검증된 Markdown의 정규화 상대경로와 각 파일 SHA-256, profile 이름을 정렬해
`artifact_bundle_fingerprint`를 계산한다. `.docs/.harness/humanize-handoffs.json`
원자적 ledger에 같은 fingerprint의 `proposed`, `skipped`, `rejected`, `applied`,
`revalidated` 완료 기록이 있으면 새 session에서도 다시 제안하지 않는다. 결정 시
bundle ID, owner, 파일 hash, 시각을 기록하고 승인 반영 뒤에는 `applied`와
`revalidated`를 순서대로 갱신한다. ledger 파일은 개선 대상 bundle에서 제외한다.
ledger를 기록할 수 없으면 현재 session 한정 상태로 보고한다.

직접 호출에서는 Step 4에서 필수 섹션, 요구사항 추적, 내부 링크와 저장 경로를 먼저
검증한 후 다음 조건을 모두 만족할 때 bundle 전체를 `humanize-korean`의
`document-refinement` 프로필로 한 번만 제안한다.

- `handoff_owner == design-doc`
- `suppress_child_handoff == false`
- `handoff_completed == false`

기본은 proposal-only이며 승인 전에는 `DESIGN.md`를 수정하지 않는다. 요구사항 ID,
API 경로, 파일 경로, 표 구조, 숫자, 날짜, 의무 수준 표현은 보존한다. 제안·건너뛰기·
거절 중 하나로 결정되면 `handoff_completed = true`와 ledger 상태를 함께 기록한다.

승인된 변경을 반영한 경우 Step 4의 필수 섹션, 요구사항 추적, 내부 링크와 저장 경로
검증을 다시 통과해야 최종 완료로 보고한다. downstream에는 이 재검증을 통과한
최종 Markdown만 전달한다.
