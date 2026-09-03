---
name: design-doc
description: >
  프로젝트 전체의 확장 가능한 앱 기준 문서 또는 새 기능·화면·컴포넌트의 상세 설계를
  구조화할 때 사용한다.
  '설계해줘', '어떻게 만들지 정리해줘', '기획 문서 작성', '요구사항 정리',
  '스펙 작성', 'PRD 만들어줘', 'RFP 분석해서 설계해줘', 'SFR 설계' 요청이 오면 이 스킬로 처리한다.
  인터뷰 또는 RFP/SFR 원문 기반으로 구조화된 설계 문서를 자동 도출한다.
  create-prototype 입력용 화면 배치·컴포넌트 목업 문서만 필요하면
  design-prototype-docs를 사용한다.
allowed-tools: Read, Glob, Write, Agent
---

## 문서 루트 계약

이 스킬이 하네스 문서를 읽거나 쓸 때 사용하는 정본은 `.ai-docs/`뿐이다. 작업 전에
`.ai-docs/`와 이전 `.docs/`의 존재를 확인한다. `.docs/`만 있거나 두 경로가 함께
있으면 하네스 문서를 읽거나 쓰지 않고 `harness-setup`의 명시적 문서 루트 이관·충돌
해결을 먼저 요청한다. 이전 경로를 호환 별칭으로 추측하지 않는다. 애플리케이션 소스
작업 자체의 권한과 가능 여부는 이 문서 루트 판정으로 제한하지 않는다.


# 설계 문서 도출 (design-doc)

이 스킬이 호출되면 아래 워크플로우를 순서대로 실행한다.
결과 문서는 대화창에 바로 출력한다. (별도 .md 파일 생성 금지 — 사용자가 요청할 때만 저장)

파일 저장이 승인되면 산출물 위치·소유권·인계는
`@.ai-docs/instruction/artifact-output-routing-instruction.md`를 따른다.
복수 앱은 `@.ai-docs/{앱}/instruction/artifact-output-routing-instruction.md`를
읽고 대상 앱 범위를 유지한다.

> 이 스킬의 OUTPUT은 AI Agent가 개발에 활용하는 Context 문서 / Instruction / Rule / PRD가 될 수 있음을 항상 염두에 두고 작성한다.
> 따라서 모호한 표현, 미결 항목 방치, 중복 서술을 피하고 Agent가 오해 없이 읽을 수 있는 정밀한 문서를 목표로 한다.

---

## 다운스트림 연계

이 스킬의 OUTPUT은 기반 `context-doc` 또는 아래 선택 작업의 입력으로 사용할 수 있다.
비기반 스킬 이름은 Harness Kit가 제공하는 참조 구현이며 동등한 다른 도구·Agent를
배제하지 않는다.

```
design-doc OUTPUT
    ├─→ context-doc                         → 앱 context + instruction (기반 흐름)
    ├─→ 구현 계획 도구                     → FE/BE·화면·범용 작업지침서
    ├─→ 재사용 검토 도구                   → 공통 자산 발견·보고
    └─→ 구현 검증 도구                     → 검증 결과와 evidence
```

OUTPUT 문서를 저장했다면 해당 파일을 그대로 선택한 다음 도구에 넘기면 된다.
제공 선택지로 `impl-fe-be-doc`, `impl-doc`, `impl-reuse-scan`, `impl-verify`가 있지만
특정 호출을 완료 조건으로 만들지 않는다.

---

## 저장 위치 원칙

- 설계 문서를 파일로 저장할 때는 반드시 대상 프로젝트 루트를 먼저 확정한다.
- **단일 애플리케이션**: `{project}/.ai-docs/context-base/DESIGN.md`
- **복수 애플리케이션**: `{project}/.ai-docs/{앱 디렉토리명}/context-base/DESIGN.md` (예: `.ai-docs/fe-acro-portal/context-base/DESIGN.md`)
- 사용자가 다른 파일명을 지정해도 위 `context-base/` 하위에 저장한다.
- 상위 워크스페이스 루트에서 실행 중이어도, 대상 프로젝트가 따로 있으면 상위 루트에 저장하지 않는다.

프로젝트 전체 스케일의 `DESIGN.md`는 `templates/PROJECT_DESIGN.md`를 사용한다. 이 문서는
앱의 현재 개요와 상위 기능 분류를 공유하는 기준 문서이지 상세 기능의 허용 목록이 아니다.
`02. 구축 대상 기능 분류`에 아직 없는 기능도 상세 설계·구현 문서로 만들 수 있으며,
필요하면 다음 `design-doc` 갱신에서 분류에 추가한다.

화면·기능·컴포넌트·로직 단위는 기존 `templates/OUTPUT_V2.md`로 상세 설계를 작성한다.
프로젝트 전체 `DESIGN.md`의 대분류가 상세 설계의 깊이, 인터페이스 또는 구현 방식을
미리 제한하지 않게 두 산출물의 역할을 구분한다. 아키텍처의 패키지·파일 트리도
상위 패턴을 설명하는 예시이며 별도 파일 규칙이나 허용 목록으로 사용하지 않는다.
프로젝트 전체 `DESIGN.md`는 현재 기준 사실만 담는 스냅샷이다. 변경 전 값, 삭제·이동·
이름 변경 기록, 날짜별 경과와 과거 대안은 저장하지 않는다. 변경 요약은 Step 4의
검토·승인 정보로만 보여주고 문서 본문과 분리한다.

---

## 선택 권한 정책 연계

`.ai-docs/harness/access-control/policy.json`이 없으면 기존 설계·저장 흐름을 그대로
수행한다. `project-write-access`는 선택 기능이며 이 스킬이 자동 호출하거나 권한
설정을 요구하지 않는다.

서명 정책이 있으면 Step 0-1에서 대상 앱과 `DESIGN.md` 경로를 확정한 직후 다음을
수행한다.

1. `.ai-docs/harness/access-control/write-access-instruction.md`를 읽는다.
2. `.ai-docs`를 추적하는 Git 경계의 `harness.writeAccess.provider`,
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
3. 상위 공개 workflow가 `confirmed_scope`를 전달했다면 프로젝트 루트, 단일·복수 앱
   판정, 대상 앱, `DESIGN.md` 경로가 현재 탐색 결과와 모두 일치하는지 확인한다.
4. 일치하는 `confirmed_scope`에는 이미 받은 범위 승인을 재사용하고 같은 질문을 반복하지
   않는다. 값이 없거나 하나라도 다르면 판정 결과와 적용 대상 애플리케이션을 사용자에게
   **반드시 재확인**한다.
5. 확인된 범위 밖은 건드리지 않는다.

`confirmed_scope`는 아래 필드를 모두 가진 공개 handoff 계약이다. 이 계약은 범위 확인만
재사용하며 Step 4의 일반 저장 승인과 권한 정책의 앱 핵심 문서 별도 승인을 대신하지 않는다.

```text
confirmed_scope.project_root = {정규화한 프로젝트 루트}
confirmed_scope.project_type = single-app | multi-app
confirmed_scope.target_app = {애플리케이션 식별자}
confirmed_scope.design_path = {.ai-docs 아래 정규화 상대경로}
confirmed_scope.instruction_root = {.ai-docs 아래 정규화 상대경로}
confirmed_scope.user_approved = true
```

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
> 1) 프로젝트 전체  2) 화면 단위  3) 기능 단위  4) 컴포넌트 / 로직 단위"

스케일 확인 후, 참고할 기존 설계 문서(PRD, 기획서, DB 설계서, 관련 코드, RFP/SFR 원문 등)가 있는지 묻는다.

> "참고할 기존 문서나 코드가 있으면 파일 또는 텍스트로 공유해 주세요. RFP/SFR 원문, 사용자가 정리한 요구사항, DB 설계가 있으면 함께 주시면 좋겠습니다. 없으면 바로 인터뷰를 시작합니다."

RFP/SFR 원문이 제공되면 별도 사전 스킬을 요구하지 않고 이 스킬 안에서 최소한으로 해석한다.
프로젝트 전체 스케일에서는 앱 목적, 사용자·환경, 구축 대상 기능의 대분류, 기술·운영
제약만 추출한다. 세부 요구사항을 처음부터 앱 정본의 확정 범위로 만들지 않는다.

아래 상세 추출은 화면·기능·컴포넌트·로직 단위에서만 수행한다.

- 요구사항 ID, 요구사항 명칭, 원문 범위, 필수 기능, 제약, 사용자 역할을 추출한다.
- 화면 후보가 필요한 경우 확정안이 아니라 후보로 표시하고 사용자 확인을 받는다.
- 불명확한 항목은 추측하지 않고 Step 2 인터뷰 질문에 포함한다.
- 삭제된 별도 RFP 처리 스킬의 전체 로직을 복제하지 않는다.

스케일별 양식 매핑은 `prompts/scale-routing.md` 참조.
프로젝트 전체이고 기존 `DESIGN.md`가 있으면 반드시 전체 내용을 입력에 포함해 갱신
경로로 들어간다. 직접 재호출과 상위 스킬의 자동 호출을 구분하지 않는다.

상세 설계 인터뷰 진행 시 입력 양식이 필요하면 `templates/INPUT_V2.md`를 사용자에게 제공한다.
(사용자가 직접 채워서 제출하는 경우에만. 일반적으로는 Step 2 인터뷰로 대체)

---

### Step 2 — 설계 인터뷰

프로젝트 전체 스케일은 `prompts/project-design.md`에서 기존 문서 유무에 맞는 섹션만
읽고 최소 확인 절차를 진행한다. 개요와 구축 대상 기능을 상세 명세 수준으로 확정하려고
묻지 않는다. 기술 스택을 확인한 뒤에는 적합한 아키텍처 패턴의 권장안과 대안, 각
패턴의 패키지·파일 구조 예시를 먼저 보여주고 사용자의 선택을 받는다. 상위 workflow가
같은 후보·근거·구조 예시와 사용자의 선택을 전달했다면 재사용하고 다시 묻지 않는다. 배포 환경은
로컬 개발·개발 서버·운영 환경별 서버 형태, 운영체제와 배포·실행 방식을 한 번에
확인하며, 사용자가 모르면 비워 둔다.

화면·기능·컴포넌트·로직 단위는 `prompts/interview.md`의 질문 목록을 순서대로 진행한다.

아래 인터뷰 규칙은 이 상세 설계 분기에 적용한다.

- 섹션 순서대로 **한 번에 하나씩** 질문한다.
- 답변이 모호하면 반박하거나 더 파고든다. 넘어가지 않는다.
- H섹션(뒤집기 확인)은 D섹션 직후에 진행한다. 범위가 확정되기 전에 뒤집는 것이 실효성 있다.
- 기존 문서가 있으면 답변과 교차 검증하여 불일치를 짚어낸다.

---

### Step 3 — OUTPUT 문서 작성

인터뷰 완료 후 스케일에 따라 양식을 선택한다.

- 프로젝트 전체: `templates/PROJECT_DESIGN.md`
- 화면·기능·컴포넌트·로직: `templates/OUTPUT_V2.md` (V1은 deprecated)

- 스케일별 OUTPUT 양식은 `prompts/scale-routing.md` 참조.
- 프로젝트 전체는 제목·요약과 `01 개요`부터 `07 VSCode 익스텐션 추천`까지 고정
  순서를 유지한다. 기존 `주의사항` 내용 중 앱 고유 사실은 `05 애플리케이션
  특이사항`으로 옮기고 `주의사항` 제목은 만들지 않는다.
- 프로젝트 전체의 배포 환경은 모르는 경우 제목만 남기고 본문을 비운다. 그 밖의
  확인되지 않은 사실을 임의로 확정하지 않는다.
- 상세 설계에서 확실하지 않은 항목은 비우지 않고 `미정 — [이유]`로 표시한다.
- 양식의 작성 지침(주석)은 읽고 반영한 뒤 최종 출력에서 제거한다.
- `OUTPUT_V2` 상세 설계에서 해당하지 않는 스케일의 섹션은 소제목째 삭제한다.

기존 프로젝트 전체 `DESIGN.md`를 갱신할 때는 새 양식으로 단순 덮어쓰지 않는다.
`prompts/project-design.md`의 기존 문서 갱신 절차에 따라 현재 유효한 내용만 의미 기준으로
재배치한다. 기존 문서는 현재 사실 후보일 뿐이므로 현재 코드·설정·운영 문서나 이번 사용자
확인과 충돌하는 내용, 현재성을 확인할 수 없는 내용은 정본에서 제거한다. 그 변경 이력은
Step 4 미리보기에는 표시하되 `DESIGN.md` 본문에는 남기지 않는다.

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
> - 문서 역할: `DESIGN.md`는 앱의 개요, 상위 기능 분류, 기술 스택, 아키텍처와
>   앱 고유 운영 맥락을 공유하는 설계 기준 문서입니다. 기능 분류는 상세 설계나
>   구현을 제한하는 허용 목록이 아닙니다.
> - 현재 권한: `{pm-pl / app-doc-lead와 앱 범위}`
> - 변경 내용과 이유: `{신규 작성 또는 갱신 요약}`
>
> 위 변경을 이 파일에 반영할까요? **(승인 / 수정 / 취소)**

대상 경로·내용 요약·현재 역할이 달라지면 이전 답변을 재사용하지 않는다. AI 훅의
`permissionDecision=ask`도 같은 확인을 요구하므로 생략하지 않는다.

저장 승인 시:
- **단일 앱**: 기본 경로 `{project}/.ai-docs/context-base/DESIGN.md`
- **복수 앱**: 기본 경로 `{project}/.ai-docs/{앱 디렉토리명}/context-base/DESIGN.md`
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
`artifact_bundle_fingerprint`를 계산한다. `.ai-docs/.harness/humanize-handoffs.json`
원자적 ledger에 같은 fingerprint의 `proposed`, `skipped`, `rejected`, `applied`,
`revalidated` 완료 기록이 있으면 새 session에서도 다시 제안하지 않는다. 결정 시
bundle ID, owner, 파일 hash, 시각을 기록하고 승인 반영 뒤에는 `applied`와
`revalidated`를 순서대로 갱신한다. ledger 파일은 개선 대상 bundle에서 제외한다.
ledger를 기록할 수 없으면 현재 session 한정 상태로 보고한다.

직접 호출에서도 사용자가 이번 요청에서 한국어 Markdown 문체 개선까지 명시한 경우에만,
Step 4에서 스케일별 필수 섹션, 현재 사실만 유지했는지, 내부 링크와 저장 경로를 먼저
검증한 후 다음 조건을 모두 만족할 때 bundle 전체를 `humanize-korean`의
`document-refinement` 프로필로 한 번만 제안한다.

- `user_requested_document_refinement == true`
- `handoff_owner == design-doc`
- `suppress_child_handoff == false`
- `handoff_completed == false`

기본은 proposal-only이며 승인 전에는 `DESIGN.md`를 수정하지 않는다. 요구사항 ID,
API 경로, 파일 경로, 표 구조, 숫자, 날짜, 의무 수준 표현은 보존한다. 제안·건너뛰기·
거절 중 하나로 결정되면 `handoff_completed = true`와 ledger 상태를 함께 기록한다.

승인된 변경을 반영한 경우 Step 4의 스케일별 필수 섹션, 현재 사실만 유지했는지, 내부 링크와 저장 경로
검증을 다시 통과해야 최종 완료로 보고한다. downstream에는 이 재검증을 통과한
최종 Markdown만 전달한다.
