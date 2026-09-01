---
name: harness-bootstrap
description: >
  AI 하네스 문서가 전혀 없는 기존 코드베이스에 처음으로 하네스를 부팅할 때 사용한다.
  '하네스 부팅', '기존 코드 분석해서 문서 만들어줘', '레거시 프로젝트 문서화',
  'CLAUDE.md 없는데 생성', '설계 문서 역추출', 'AI 문서 부트스트랩',
  '기존 프로젝트에 하네스 도입' 요청이 오면 이 스킬을 사용한다.
  기존 코드베이스에 harness-setup의 프로젝트 문서 골격을 먼저 적용한 뒤 design-doc OUTPUT_V2 형식 설계 문서 + context-doc 결과물(앱별 *-context.md + .ai-docs/instruction/*)을 자동 도출한다.
  프레임워크 자동 감지. 최소 인터뷰(2회 이하)로 코드에서 추출 불가능한 도메인 맥락만 보충.
allowed-tools: Read, Glob, Grep, Write
---

# 하네스 부트스트랩 (harness-bootstrap)

기존 코드베이스만 있고 AI 하네스 문서(CLAUDE.md, AGENTS.md, 설계 문서, instruction 등)가 전혀 없을 때,
코드를 직접 분석해서 다음 두 산출물을 한 번에 도출한다.

1. **`design-doc` OUTPUT_V2 형식 설계 문서** (프로젝트 설계 스냅샷)
2. **`context-doc` 결과물** — 앱별 `*-context.md` + `.ai-docs/instruction/*-instruction.md`

생성 전 반드시 사용자 확인을 거친다. 파일을 무단으로 생성하지 않는다.
사용자 스킬은 설치된 `harness-kit` 플러그인에서 제공하며 프로젝트에
`.agents/skills/`, `.claude/skills/`, `skills/`를 만들거나 동기화하지 않는다.

> 이 스킬은 "레거시/기존 프로젝트에 AI 하네스를 처음 도입"하는 진입점이다.
> 이후부터는 `design-doc` → `context-doc` 정규 플로우를 그대로 쓰면 된다.

> **공개 계약 재사용**: 이 스킬은 `design-doc`과 `context-doc`의 공개 산출물 계약을 한 번에 수행하는 통합 스킬이다. 다른 스킬의 내부 구현 경로에 결합하지 않고, 루트 컨텍스트는 `harness-setup`, 앱 설계·컨텍스트는 각 앱 문서 스킬의 공개 계약을 따른다.

## 문서 루트 계약

부트스트랩 문서의 유일한 루트는 `.ai-docs/`다. Step 0에서 `.ai-docs/`와 이전
`.docs/`를 함께 확인한다. `.docs/`만 있거나 두 경로가 공존하면 코드 분석이나 문서
생성을 시작하지 않고 `harness-setup`의 명시적 문서 루트 이관·충돌 해결로 넘긴다.
이전 경로를 읽어 새 경로에 일부 산출물만 만드는 혼합 상태를 허용하지 않는다.

---

## 설계 원칙

1. **코드에서 추출 가능한 건 모두 자동 추출**. 질문하지 않는다.
2. **코드에서 알 수 없는 것만 인터뷰**. 도메인 목적·사용자·상위 비즈니스 맥락.
3. **인터뷰는 최대 2회**. 그 이상은 `미정 — [이유]` 로 남긴다.
4. **공개 산출물 계약을 재사용한다**. `design-doc` OUTPUT_V2 형식과 `context-doc`의 앱 context + instruction 구조를 따른다.
5. **프레임워크 중립**. 매니페스트 파일 기반으로 자동 감지한다.

## 선택 권한 정책 연계와 단계 분리

`.ai-docs/harness/access-control/policy.json`이 없으면 기존 통합 부트스트랩 흐름을 그대로
수행한다. 이 스킬은 선택 기능인 `project-write-access`를 자동 호출하거나 권한을
자동 설정하지 않는다. 초기 `harness-setup` 뒤부터 권한을 적용하려는 사용자는
부트스트랩을 잠시 멈추고 관리자가 `project-write-access`를 명시적으로 실행한 다음
재개한다.

서명 정책이 있으면 `.ai-docs/harness/access-control/write-access-instruction.md`를 읽고,
`.ai-docs` Git 경계의 provider·host·account와 프로젝트의 `write_access_guard.py
check-path`로 단계별 정확한 파일을 검사한다.

```text
[하네스 단계]
admin
  └─ 루트 AGENTS.md·CLAUDE.md, .ai-docs/root-context/**, .ai-docs/harness/**

[앱 문서 단계]
pm-pl 또는 해당 앱 app-doc-lead
  └─ DESIGN.md, *-context.md, *-instruction.md
```

- 역할은 상속하지 않는다. `admin`만 가진 계정은 앱 문서를 저장할 수 없다.
- 한 사람이 전체 부트스트랩을 이어서 수행하려면 `admin`과 `pm-pl` 또는 대상 앱의
  `app-doc-lead`가 정책에 각각 배정돼 있어야 한다.
- 하네스가 이미 최신이면 admin 쓰기 단계를 생략하고 앱 문서 권한자 세션에서 코드
  분석과 앱 문서 생성을 진행할 수 있다.
- 하네스 갱신이 필요하지만 현재 계정에 admin이 없으면 변경 계획과 checkpoint를
  반환하고 admin 단계가 끝난 뒤 재개한다.
- 앱 문서 권한이 없으면 코드 분석·초안까지만 반환하고 저장하지 않는다.
- 권한 부족을 역할 변경으로 우회하거나 정책을 자동 수정하지 않는다.

권한 정책의 앱 문서 승인 질문은 도메인 인터뷰 예산과 별개인 필수 쓰기 게이트다.
`design-doc`·`context-doc`을 자동 handoff한 경우에도 Step 7에서 문서 종류·대상·변경
요약을 설명하고 별도 승인을 받는다.

## 산출물 bundle과 후처리 소유권

`harness-bootstrap`은 이 통합 실행의 최외곽 producer다. Step 0에서 다음 컨텍스트를
한 번 만든다.

```text
artifact_bundle_id = harness-bootstrap:{정규화한 프로젝트 루트}:{이번 실행의 고유 ID}
handoff_owner = harness-bootstrap
suppress_child_handoff = false
handoff_completed = false
```

고유 실행 ID는 부모·자식 workflow correlation에만 사용한다. 새 task/session에서
같은 최종 산출물을 다시 제안하는 것을 막는 키는 아래 영속
`artifact_fingerprint`다.

Step 5의 `design-doc`, Step 6의 `context-doc` 공개 skill-name handoff에는 같은
`artifact_bundle_id`와 `handoff_owner`를 전달하고
`suppress_child_handoff = true`를 명시한다. 자식 workflow는 자신의
`humanize-korean` 후처리를 실행하지 않고 초안과 검증 결과만 반환해야 한다.
따라서 이 bundle의 문서 개선 handoff는 Step 7 이후
`harness-bootstrap`이 한 번만 소유한다.

### 영속 handoff fingerprint와 ledger

Step 7 검증을 마친 최종 Markdown 산출물을 프로젝트 루트 상대경로로 정규화하고
정렬한다. 각 파일의 내용 SHA-256을 계산한 뒤
`상대경로 + NUL + 내용 SHA-256` 행으로 만든 canonical manifest 전체의
SHA-256을 `artifact_fingerprint`로 사용한다.

`.ai-docs/.harness/humanize-handoffs.json`에 다음을 영속 기록한다.

```text
schema_version
artifact_fingerprint
producer = harness-bootstrap
artifact_bundle_id
profile = document-refinement
artifacts[] = {path, sha256}
events[] = {status, recorded_at}
```

ledger 자체는 fingerprint 산출물 목록과 `humanize-korean` 대상에서 제외한다.
status는 `proposed`, `skipped`, `rejected`, `applied`, `revalidated`다. 같은
fingerprint에 이들 status 중 하나라도 있으면 새 제안을 만들지 않는다.
`proposed`는 기존 제안이 있음을 보고하고, `skipped`/`rejected`는 결정을
존중한다. `applied` 후 `revalidated`가 없으면 재제안 없이 Step 7의 구조·참조
검증만 이어서 수행한다. 경로나 내용 hash가 달라지면 새 fingerprint로 처리한다.

ledger는 sibling 임시 파일에 전체 JSON을 쓴 뒤 flush하고 원자적 replace한다.
쓰기 직전 ledger hash가 달라졌으면 다시 읽고 fingerprint별 event를 merge한다.
ledger를 안전하게 기록할 수 없으면 새 proposal을 보여주지 않고 중단한다.
이 JSON ledger는 Markdown 후처리 대상이 아니며 local skill 디렉터리와 무관한
허용 경로 `.ai-docs/**` 안에만 둔다.

## 질문 예산

사용자 질문 총합은 **최대 3회**다.

- Step 1의 저장소 루트/프로젝트 단위 확인: 최대 1회
- Step 3의 인터뷰: 최대 2회
- Step 6의 `context-doc` 단계에서는 **새 도메인 인터뷰를 추가하지 않는다**
- 예산이 소진되면 추가 확인 대신 `미정 — [이유]` 로 남긴다

프로젝트 범위 확인, 권한 단계 전환, 파일 덮어쓰기, 앱 핵심 문서 쓰기 승인은
인터뷰가 아니라 안전·쓰기 게이트이므로 이 예산으로 생략하지 않는다.

---

## 스킬 연계

```
기존 코드베이스 (AI 문서 없음)
        │
        ▼
harness-bootstrap 스킬
        │
        ├─ Step 0-C: harness-setup 공개 workflow로 문서 골격 설정
        │
        ├─ Step 1~4: 코드 스캔 + 최소 인터뷰
        │
        ├─ Step 5: design-doc OUTPUT_V2 산출
        │            ├── 단일 앱: {project}/.ai-docs/context-base/DESIGN.md
        │            └── 복수 앱: {project}/.ai-docs/{앱}/context-base/DESIGN.md
        │
        └─ Step 6~7: context-doc 파이프라인 실행
                     ├── 단일 앱: *-context.md + .ai-docs/instruction/*-instruction.md
                     └── 복수 앱: *-context.md + .ai-docs/{앱}/instruction/*-instruction.md
```

이후 작업은 정규 플로우를 따른다.
- 설계 변경 시 → `design-doc`로 OUTPUT 갱신 후 → `context-doc`로 하네스 갱신
- 문서-코드 괴리 검증 → `doc-audit`
- 구현 지침이 필요하면 → `impl-fe-be-doc` / `impl-doc`
- 구현 직전 공통 자산 확인 → `impl-reuse-scan` (재사용 불가 판정 포함 필수 preflight)
- 단계/페이즈 종료 검증 → `impl-verify` (명시 호출 전용 종료 게이트)

## 중간 산출물 재사용

- `.ai-docs/context-base/DESIGN.md`만 먼저 저장해도, 이후에는 저장소 재스캔 없이
  `@.ai-docs/context-base/DESIGN.md`를 입력으로 `context-doc` 스킬의 정규 컨텍스트
  생성 흐름을 다시 탈 수 있다.
- 한 번 부트스트랩이 끝난 프로젝트는 구조 변경 시 `harness-bootstrap`을 반복하기보다
  `design-doc` → `context-doc` 갱신을 기본 경로로 쓴다.

---

## 워크플로우

### Step 0 — 플랫폼·실행 방식 확인 + 프로젝트 유형 확인

#### Step 0-A — 플랫폼·실행 방식 확인

현재 플랫폼과 사용 가능한 실행 도구는 먼저 자동 감지한다. deployable unit이
여러 개여서 독립 스캔을 병렬화할 이점이 있고 현재 플랫폼이 지원할 때만
병렬 실행 여부를 사용자에게 묻는다. 그 외에는 순차 실행하며 플랫폼 이름을
사용자가 직접 맞히도록 요구하지 않는다.

#### Step 0-B — 프로젝트 유형 확인 (C-1 확인 단계)

부트스트랩 범위를 확정하기 위해 **반드시** 아래를 수행한다.

1. 현재 수행 위치에서 프로젝트 구조를 탐색한다 (git repo 경계, 하위 앱 폴더 후보 스캔).
2. **단일 애플리케이션 프로젝트**인지 **복수 애플리케이션 프로젝트**인지 판정한다.
3. 판정 결과 + 적용 대상 애플리케이션(폴더)을 사용자에게 **반드시 재확인**한다.
4. 확인된 범위 밖은 건드리지 않는다.
5. `.docs/`와 `.ai-docs/`의 존재 조합을 확인한다. 이전 경로가 감지되면 앱 문서
   단계로 진행하지 않고 `harness-setup`의 문서 루트 전환 결과를 기다린다.
6. 승인된 프로젝트 루트·프로젝트 유형·대상 앱에 따라 `DESIGN.md`와 instruction
   루트를 확정하고 아래 `confirmed_scope`를 만든다.

```text
confirmed_scope.project_root = {정규화한 프로젝트 루트}
confirmed_scope.project_type = single-app | multi-app
confirmed_scope.target_app = {애플리케이션 식별자}
confirmed_scope.design_path = {.ai-docs 아래 정규화 상대경로}
confirmed_scope.instruction_root = {.ai-docs 아래 정규화 상대경로}
confirmed_scope.user_approved = true
```

이 값은 공개 child workflow의 범위 재확인만 생략한다. 파일 덮어쓰기와 Step 7의 앱
핵심 문서 쓰기 승인은 별도 게이트이므로 재사용하지 않는다.

> ✋ **확인 게이트**
>
> - 프로젝트 유형: **단일 / 복수** 애플리케이션
> - 부트스트랩 대상 애플리케이션(폴더): `{폴더명}`
> - 문서 하네스 골격 상태: `{없음 / 부분 존재 / 설정됨}`
> - `harness-setup` 적용 예정 경로: `.ai-docs/**`, 루트 `AGENTS.md`, `CLAUDE.md`
> - 사용자 local skill 디렉터리 생성: **없음**
>
> 맞습니까? **(승인 / 수정 / 취소)**

---

#### Step 0-C — 프로젝트 문서 골격 설정

Step 0-B 승인 뒤 다음 기준으로 공개 스킬 이름 `harness-setup`에 handoff한다.

먼저 **선택 권한 정책 연계와 단계 분리**를 적용한다. 정책이 활성화돼 있고 하네스
변경이 필요하면 현재 계정의 admin 범위를 검증한 뒤에만 handoff한다. admin이 없으면
필요한 변경과 코드 스캔 재개 지점을 checkpoint로 남기고 파일을 쓰지 않는다. 하네스가
최신이면 읽기 전용 확인만 하고 앱 문서 권한 단계로 진행한다.

이전 `.docs/`가 감지되면 권한·코드 분석 단계보다 먼저 `harness-setup`에 문서 루트
이관 판정을 요청한다. 이관이 승인·완료되고 `.docs/`가 남지 않았다는 검증을 받기 전에는
부트스트랩 산출물을 만들지 않는다. 이전 경로에 서명 권한 정책이 있으면 관리자용
별도 이관이 필요하다는 중단 결과를 그대로 사용자에게 전달한다.

- `.ai-docs/`, `AGENTS.md`, `CLAUDE.md` 중 하나라도 없으면 초기 설정 또는
  복구 workflow를 실행한다.
- 모두 있어도 `.ai-docs/README.md`, `.ai-docs/.gitignore`, `@AGENTS.md` bridge의
  계약을 읽기 전용으로 확인하고, 갱신이 필요하면 관리 블록 diff를 반환받는다.
- Step 0-B에서 확정한 프로젝트 루트·단일/복수 앱 판정·적용 경로 승인을
  전달하므로 같은 질문을 반복하지 않는다. 새 overwrite 또는 backup 판단이
  필요한 경우에만 `harness-setup`이 추가 승인을 요청한다.

handoff에는 같은 bundle 컨텍스트를 전달한다.

```text
artifact_bundle_id = {Step 0에서 만든 값}
handoff_owner = harness-bootstrap
suppress_child_handoff = true
```

`harness-setup`은 `.ai-docs/**`, 루트 `AGENTS.md`, `CLAUDE.md`만 생성·갱신하고
변경 목록과 금지 경로 불변조건 검증을 반환해야 한다. `.agents/skills/`,
`.claude/skills/`, `skills/`는 생성·복사·동기화하지 않는다. 기존 local skill
copy는 읽기 전용 report만 반환한다.

`harness-setup`을 찾을 수 없으면 플러그인 설치가 불완전한 상태로 보고 쓰기를
중단한다. bootstrap이 private 템플릿을 흉내 내거나 프로젝트에 스킬을 복사해
우회하지 않는다.

권한 정책이 활성화된 경우 이 handoff의 쓰기 범위는 admin 문서에 한정한다. 앱의
`DESIGN.md`, `*-context.md`, `*-instruction.md`는 만들지 않는다.

---

### Step 1 — 저장소 스캔 및 매니페스트 감지

`prompts/code-scan.md`·`prompts/stack-detection.md` 기준으로 저장소를 스캔한다.

- 루트의 매니페스트 파일 자동 탐색 (`package.json`, `requirements.txt`, `pyproject.toml`, `build.gradle*`, `pom.xml`, `Cargo.toml`, `go.mod`, `composer.json`, `Gemfile` 등)
- 매니페스트에서 **기술 스택 + 버전** 추출
- 모노레포/멀티 프로젝트 여부 판정 (루트에 매니페스트 없고 하위 디렉토리에 있음)
- 루트에 **서로 다른 에코시스템 매니페스트가 2개 이상** 있으면 `멀티 런타임 루트` 후보로 본다.

매니페스트를 찾지 못하면 사용자에게 확인한다.
루트에 여러 런타임이 섞여 있고 배포 단위가 불명확해도 사용자에게 1회 확인한다.
이 질문은 전체 질문 예산에 포함된다.

> "루트에서 매니페스트 파일을 찾지 못했습니다.
> 기술 스택 정보가 있는 파일 경로를 알려주시거나, 루트를 지정해 주세요."

> "루트에 여러 런타임 매니페스트가 함께 있습니다.
> 하나의 제품 문서로 묶을까요, deployable unit별로 분리할까요?"

---

### Step 2 — 코드베이스 인벤토리 추출

다음을 자동 추출한다. 전부 **코드·설정 파일 기반**이며 추측 금지.

| 항목 | 추출 소스 |
|------|----------|
| 디렉토리 트리 | 루트 스캔, 역할 있는 폴더만 |
| 엔트리포인트 | `main.*`, `app.*`, `index.*`, `server.*` 등 |
| 라우터/엔드포인트 목록 | 라우트 정의 패턴 grep (FastAPI `@router`, Express `app.get`, Spring `@GetMapping` 등) |
| WebSocket/통신 채널 | `websocket`, `ws`, `socket.io`, `stomp` 등 키워드 grep |
| DB 테이블/모델 | ORM 모델 파일 (`models.py`, `entity/*.ts`, `@Entity` 등) |
| 환경 변수 | `.env*`, `os.getenv`, `process.env`, `System.getenv` grep |
| 실행 스크립트 | `scripts` 필드, `Makefile`, `start.sh`, `Dockerfile`, `docker-compose*` |
| 외부 서비스/라이브러리 | 매니페스트 의존성 분류 |

추출 결과는 **요약 보고서**로 사용자에게 먼저 보여준다. 잘못 읽은 것이 있으면 수정받는다.

---

### Step 3 — 최소 인터뷰 (최대 2회)

`prompts/interview.md`를 이 단계의 **단일 상세 계약**으로 사용한다. 질문 문구,
질문 2를 사용할 조건, 한 번만 허용하는 재질문, 묻지 않을 항목, 답변 거부·
`모름` 처리 규칙은 그 파일을 따른다. 이 본문이나 다른 prompt에 별도 인터뷰
질문을 중복 정의하지 않는다.

오케스트레이션 상의 불변조건은 다음뿐이다.

- 코드에서 알 수 없는 도메인 목적·사용자와 필요한 경우의 상위 운영 제약만 묻는다.
- 최대 2회이며 질문 예산이 소진되면 `미정 — [이유]`로 진행한다.
- Step 6의 자식 workflow는 새 인터뷰를 추가하지 않는다.

---

### Step 4 — OUTPUT_V2 섹션 매핑

`prompts/extraction-mapping.md` 기준으로 Step 2 인벤토리 + Step 3 인터뷰 답변을
`design-doc`의 `OUTPUT_V2.md` 섹션에 매핑한다.

| OUTPUT_V2 섹션 | 채우는 소스 |
|----------------|------------|
| 01 개요 | 인터뷰 + 매니페스트 프로젝트명·버전 |
| 02 동작 흐름 | 엔트리포인트 → 라우터/핸들러 체인 역추적 |
| 03 집중 로직 | 엔트리포인트 주변 핵심 모듈 분석 |
| 04 인터페이스 | 추출된 API/WebSocket 목록 |
| 05 데이터 | ORM 모델 / 스키마 파일 |
| 06 파일 구성 | 디렉토리 트리 |
| 07 라이브러리 | 매니페스트 의존성 |
| 10 주의사항 | 위험한 환경 분기·Dockerfile·README 패턴 |
| 11 부가 정보 | 실행 스크립트·배포 힌트·환경 변수·DB/외부 구성 |
| 12 열린 결정 | 코드에서 TODO/FIXME/주석 추출 |

코드에서 역추출한 정보는 **관찰 기반**이므로, 설계 의도를 추측하지 않는다.
"현재 코드는 이렇게 구성돼 있다"로만 서술한다.

---

### Step 5 — design-doc OUTPUT 초안 생성 및 확인

공개 스킬 이름 `design-doc`으로 handoff하여 OUTPUT_V2 설계 문서 초안을
생성한다. 다른 스킬의 `templates/**` 경로나 구현 파일을 직접 읽지 않는다.

handoff 입력에는 Step 2 인벤토리, Step 3 답변, Step 4 매핑 결과와 다음 실행
컨텍스트를 함께 전달한다.

```text
artifact_bundle_id = {Step 0에서 만든 값}
handoff_owner = harness-bootstrap
suppress_child_handoff = true
confirmed_scope = {Step 0-B에서 승인받은 범위 객체}
```

이 handoff에서는 준비된 관찰·답변을 입력으로 사용하고 추가 인터뷰나 자식
`humanize-korean` 후처리를 요청하지 않는다.

권한 정책이 활성화돼 있으면 대상 `DESIGN.md`에 `pm-pl` 또는 해당 앱
`app-doc-lead` 권한이 있는지 검증한다. 이 단계는 초안 생성이므로 아직 파일을 쓰지
않으며, guard의 `decision=confirm`은 Step 7의 별도 앱 문서 승인으로 넘긴다.

- 작성 지침(주석)은 제거한 상태로 출력
- 해당하지 않는 스케일 섹션은 삭제
- 불명확한 항목은 `미정 — [이유]` 로 표시
- 사용자가 별도 중단을 요청하지 않으면, **설계 초안 확인 후 바로 Step 6으로 연속 진행**한다.
- 설계 초안 단계의 확인은 **수정 포인트 수집용**이며, 최종 저장 승인은 Step 7에서 1회만 받는다.

초안을 대화창에 출력하고 확인받는다.

> "위 설계 문서를 검토해 주세요.
> 수정할 부분이 있으면 말씀해 주시고, 이상 없으면 바로 `context-doc` 단계까지 이어서 초안을 완성하겠습니다.
> 저장 경로는 `{confirmed_scope.design_path}`로 하겠습니다. 변경 원하시면 알려주세요."

---

### Step 6 — context-doc 파이프라인 실행

Step 5 OUTPUT을 입력으로 삼아 공개 스킬 이름 `context-doc`으로 handoff한다.
다른 스킬의 `prompts/**` 또는 `templates/**` 내부 경로를 직접 참조하지 않는다.

handoff에는 다음 실행 컨텍스트를 전달한다.

```text
artifact_bundle_id = {Step 0에서 만든 값}
handoff_owner = harness-bootstrap
suppress_child_handoff = true
confirmed_scope = {Step 0-B에서 승인받은 범위 객체}
```

- `.ai-docs/{앱}-context.md`에 들어갈 애플리케이션 팩트 + 지침 인덱스 초안 작성
- `context-doc`의 공개 workflow로 주제별 instruction 파일 분류
- 앱 context + 각 `*-instruction.md` 구조 활용
- `confirmed_scope.instruction_root`에 따라 instruction 배치를 확정하고 같은 배치 질문을
  반복하지 않는다. 현재 구조가 승인값과 달라졌으면 자동 보정하지 않고 Step 0-B로
  돌아가 범위를 다시 확인한다.

이 단계에서는 **새로운 인터뷰를 추가하지 않는다**. Step 3 답변 + Step 5 OUTPUT으로 충분하다.
단, 활성 권한 정책의 쓰기 승인 질문은 인터뷰가 아니므로 Step 7에서 반드시 수행한다.
또한 bootstrap 한계 때문에 아래 오버라이드를 적용한다.

- 코드/README/주석에서 **규범적 이유·대안이 확인된 금지 항목만** 삼위일체로 기록한다.
- 관찰 사실만 있고 이유·대안이 확정되지 않으면 `미정 — bootstrap 산출물에는 규범 근거 없음`으로 남긴다.
- 이 사유로는 사용자를 다시 인터뷰하지 않는다. 후속 `design-doc` → `context-doc` 보강 대상으로 넘긴다.

---

### Step 7 — 미리보기 및 일괄 저장

생성된 모든 파일 초안을 대화창에 순서대로 출력하고 승인을 요청한다.

출력 순서:

**단일 애플리케이션:**
1. `.ai-docs/context-base/DESIGN.md` (또는 사용자 지정 경로)
2. `.ai-docs/{앱}-context.md`
3. `.ai-docs/instruction/*-instruction.md` (해당 주제와 항상 생성되는
   `agent-instruction.md`, `@.ai-docs/instruction/artifact-output-routing-instruction.md` 포함)

**복수 애플리케이션:**
1. `.ai-docs/{앱}/context-base/DESIGN.md`
2. `.ai-docs/{앱}-context.md`
3. `.ai-docs/{앱}/instruction/*-instruction.md` (해당 주제와 항상 생성되는
   `agent-instruction.md`, `@.ai-docs/{앱}/instruction/artifact-output-routing-instruction.md` 포함)

(단, 설계 문서에 해당 주제가 없으면 일반 주제 instruction 파일은 생성하지 않는다.
`agent-instruction.md`와 `artifact-output-routing-instruction.md`는 각각 AI 동작 규칙과
산출물 경계의 기본 정본이므로 항상 생성한다.)

bootstrap이 `DESIGN.md`와 context 초안을 만든 뒤에는 installer나 host 설정을 복제하지
않는다. `.ai-docs/harness/artifact-routing.json`이 있으면 이를 읽고, 없으면 공개 스킬 이름
`harness-setup`에 portable bundle 생성·갱신을 명시 handoff한다. 이후 `context-doc`도
같은 routing manifest·format contract와 앱별 instruction을 소비하며 prototype 기본 경로를
별도로 만들지 않는다. 외부 fixed-format bundle은 `.ai-docs/_inbox/{artifact-bundle-id}/`에
proposal만 기록하고 G12 승인 전 canonical artifact를 만들지 않는다.

> "위 파일들을 검토해 주세요.
> 이상 없으면 한꺼번에 저장하겠습니다. 수정 사항이 있으면 알려주세요."

권한 정책이 활성화된 경우 일반 검토·저장 승인과 별도로, 실제 저장 직전에 guard로
위의 정확한 파일 전체를 다시 검사한다. `decision=confirm`이면 다음 정보를 한 번에
보여주되 문서 종류별 역할을 빠뜨리지 않는다.

> **앱 설계·컨텍스트 문서 쓰기 확인**
>
> - 대상 앱과 정확한 파일 전체
> - `DESIGN.md`: 요구사항, 범위, 아키텍처, 데이터와 인수 기준을 정하는 설계 기준
> - `*-context.md`: 앱의 설계 원칙, 기술 스택, 아키텍처, 실행 방법과 지침 인덱스
> - 각 `*-instruction.md`: 파일명별 주제 규칙
> - `artifact-output-routing-instruction.md`: 산출물 위치·소유자·승인·인계 정본
> - 현재 `pm-pl` 또는 `app-doc-lead` 역할과 앱 범위
> - 신규 작성·갱신 파일별 변경 요약과 이유
>
> 위 변경을 이 파일들에 반영할까요? **(승인 / 수정 / 취소)**

`design-doc`과 `context-doc`이 자동 handoff된 실행에서도 생략하지 않는다. 대상 경로,
내용 요약 또는 역할이 달라지면 이전 승인을 재사용하지 않는다. `admin`만 가진 계정은
질문으로 우회하지 않고 거부한다.

승인 시 STEP 0에서 확정한 프로젝트 유형에 따라 분기한다.

**단일 애플리케이션:**
- `.ai-docs/instruction/` 디렉토리가 없으면 생성
- 설계 문서 저장 폴더(`.ai-docs/context-base/`)가 없으면 생성
- `DESIGN.md`, `.ai-docs/{앱}-context.md`, instruction 파일 일괄 저장
- 앱 context의 `@.ai-docs/instruction/*` 참조가 실제 파일과 1:1 일치하는지 검증
- 루트 `AGENTS.md`·`CLAUDE.md`와 `.ai-docs/root-context/**`를 수정하지 않았는지 검증

**복수 애플리케이션:**
- `.ai-docs/{앱}/instruction/` 디렉토리가 없으면 생성
- `.ai-docs/{앱}/context-base/` 디렉토리가 없으면 생성
- 설계 문서: `.ai-docs/{앱}/context-base/DESIGN.md` 저장
- 컨텍스트 문서: `.ai-docs/{앱}-context.md` 저장
- instruction: `.ai-docs/{앱}/instruction/*-instruction.md` 저장
- `.ai-docs/{앱}-context.md`의 instruction 참조가 `.ai-docs/{앱}/instruction/` 내 실제 파일과 1:1 일치하는지 검증
- 루트 `AGENTS.md`·`CLAUDE.md`와 `.ai-docs/root-context/**`를 수정하지 않았는지 검증

**공통:**
- 이미 존재하는 파일이 있으면 덮어쓰기 전에 사용자에게 알림
- Step 0-C가 만든 `.ai-docs/README.md`, `.ai-docs/.gitignore`, `.ai-docs/_inbox/`와
  그 사용자 확장을 보존
- 실행 전후 `.agents/skills/`, `.claude/skills/`, `skills/`의 존재·hash가
  동일하고 새 local skill 디렉터리가 생기지 않았는지 검증
- 앱 문서 저장 뒤 루트 읽기 지도 갱신이 필요하면 admin의 `harness-setup` 후속 작업으로
  남긴다. 같은 계정에 admin 역할도 명시돼 있으면 별도 admin 경로 검사와 승인을 거쳐
  공개 `harness-setup` workflow로 이어갈 수 있다.

---

## 문서 개선 후처리

Step 7의 전체 산출물과 구조 검증이 끝난 뒤 다음 조건을 전부 만족할 때만
`artifact_bundle_id` 전체를 `humanize-korean`의 `document-refinement` 프로필로
한 번 넘긴다.

- `handoff_owner == harness-bootstrap`
- `suppress_child_handoff == false`
- `handoff_completed == false`
- 같은 `artifact_fingerprint`의 ledger event가 없음

제안이 생성되면 사용자에게 보여주기 전에 ledger에 `proposed`를 원자적으로
기록한다. 건너뜀·거절·승인 적용·재검증 결과는 각각 `skipped`, `rejected`,
`applied`, `revalidated` event로 추가한다. 승인 적용으로 내용이 바뀌면 최종
파일 hash로 fingerprint를 다시 계산하고 `supersedes_fingerprint`로 제안 시점
fingerprint를 연결한다. `applied`와 Step 7 재검증의 `revalidated`는 적용 후
최종 fingerprint에도 기록해 다음 session의 재제안을 막는다. handoff를 제안하거나 기존 ledger
결정을 재사용한 뒤 `handoff_completed = true`로 기록한다.
`design-doc`과 `context-doc` 자식 workflow가 반환한 문서는 별도 handoff하지 않는다.
후처리는 proposal-only가 기본이며 승인 전 파일 쓰기는 금지한다. 요구사항, 경로,
ID, 숫자, 날짜, 코드 fence, 표 구조, 의무 수준은 변경하지 않는다. 승인 적용 후에는
Step 7의 경로·참조 검증을 다시 수행한다.
`harness-kit:managed:start/end` marker는 변경하거나 제거하지 않는다.
