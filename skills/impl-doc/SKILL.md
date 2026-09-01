---
name: impl-doc
description: >
  한 애플리케이션 안의 단일 기능·모듈·스크립트·CLI·BE 엔드포인트·FE 컴포넌트처럼
  독립된 소규모 작업의 단계별 구현 지침서를 생성한다.
  '범용 구현 지침', '단일 기능 작업 순서', '소규모 구현 계획', '자동화 구현 가이드',
  '스크립트 구현 지침', '도구 구현 계획', '단일 기능 구현 계획',
  'BE 단일 기능', '백엔드 단일 기능 구현', '백엔드 API 1개 추가',
  'FE 단일 기능', '프론트 단일 기능 구현', '컴포넌트 1개 추가',
  '훅 추가', '화면 1개 수정', 'UI 리팩터' 요청이 오면 이 스킬을 사용한다.
  CLI, 자동화 스크립트, 라이브러리, 단독 백엔드 서비스,
  단일 BE 엔드포인트/도메인 로직, 단일 FE 컴포넌트/훅/화면 등
  단일·소규모 범용 작업의 Phase별 구현 지침을 만든다. FE와 BE를 함께 연결하거나
  여러 화면을 한 로드맵으로 계획하는 요청은 impl-fe-be-doc을 사용한다.
allowed-tools: Read, Write, Glob, Grep, Agent
---

## 문서 루트 계약

이 스킬이 하네스 문서를 읽거나 쓸 때 사용하는 정본은 `.ai-docs/`뿐이다. 작업 전에
`.ai-docs/`와 이전 `.docs/`의 존재를 확인한다. `.docs/`만 있거나 두 경로가 함께
있으면 하네스 문서를 읽거나 쓰지 않고 `harness-setup`의 명시적 문서 루트 이관·충돌
해결을 먼저 요청한다. 이전 경로를 호환 별칭으로 추측하지 않는다. 애플리케이션 소스
작업 자체의 권한과 가능 여부는 이 문서 루트 판정으로 제한하지 않는다.


# 범용 구현 지침서 (impl-doc)

design-doc 스킬의 OUTPUT 또는 설계 문서를 입력받아
**기능 단위**로 Phase별 구현 지침서를 생성한다.

단일·소규모 범용 작업의 폴백 스킬이다.
FE/BE 페어 다중 기능 또는 화면 다중 RFP가 아니면 이 스킬을 사용한다.

생성 전 반드시 사용자 확인을 거친다. 파일을 무단으로 생성하지 않는다.

계획서·roadmap index 저장 경로·소유권·인계는 단일 앱의
`@.ai-docs/instruction/artifact-output-routing-instruction.md` 또는 복수 앱의
`@.ai-docs/{앱}/instruction/artifact-output-routing-instruction.md`를 따른다.

> impl-fe-be-doc은 **FE/BE 페어 다중 기능** 또는
> **RFP/SFR 기반 다중 화면** 구현에 특화된 스킬이다.
> 이 스킬(impl-doc)은 그 외 모든 단일·소규모 범용 작업을 받는다.
> 내부 도구, 자동화 스크립트, CLI, 라이브러리, 단독 백엔드 서비스,
> 데이터 파이프라인, **BE 단일 기능(엔드포인트 1~수개 또는 단일 도메인 로직)**,
> **FE 단일 기능(컴포넌트/훅/화면 1개 신규·수정)** 등이 대상이다.

## 스킬 연계

```
design-doc OUTPUT (설계문서.md)
    ↓
impl-doc  ← 지금 여기
    ↓
(단일앱) .ai-docs/impl-doc/{사용자}/{YYMMDD}-{seq}.{slug}-impl-{kind}.md
(복수앱) .ai-docs/{앱}/impl-doc/{사용자}/{YYMMDD}-{seq}.{slug}-impl-{kind}.md
        예: .ai-docs/app-backend/impl-doc/developer/260630-1.user-auth-impl-api.md
    ├─→ 같은 디렉토리의 로드맵 인덱스 문서
    │   {YYMMDD}-0.{앱이름}-roadmap-impl-index.md 생성/갱신 (Step 8)
    ├─→ 실제 구현
    ├─→ impl-reuse-scan  →  Phase 시작 전 공통 자산 확인
    ├─→ impl-verify      →  Phase 종료 검증
    ├─→ multi-review     →  코드 리뷰
    └─→ doc-audit        →  문서 괴리 점검
```

### 구현 지침 스킬 선택 기준

분기 기준은 **FE/BE 분리 여부가 아니라 "다중 화면·페어 다중 기능인가"** 다.

| 스킬 | 선택 조건 |
|------|----------|
| `impl-fe-be-doc` | FE/BE 페어 **다중 기능** 풀스택 프로젝트, 또는 RFP/SFR 기반 **다중 화면** 구현 |
| **`impl-doc`** | **그 외 모든 단일·소규모 범용 작업** ← 이 스킬 |

판단 가이드:
- 화면 1개 또는 컴포넌트/훅 단독 → **impl-doc**
- API 엔드포인트 1~수개 또는 단일 도메인 로직 → **impl-doc**
- FE 화면 여러 개 + BE API 여러 개를 페어로 묶는 풀스택 → **impl-fe-be-doc**
- RFP/SFR/화면정의서 기반 다중 화면 명세 → **impl-fe-be-doc**

---

## 대상 프로젝트 유형

```
✅ 이 스킬이 적합한 경우
  - CLI 도구 / 커맨드라인 유틸리티
  - 자동화 스크립트 (크롤러, 배치 처리, 데이터 변환)
  - 라이브러리 / SDK / 패키지
  - 단독 백엔드 서비스 (API 서버이나 FE가 없는 경우)
  - BE 단일 기능 (엔드포인트 1~수개, 단일 도메인 로직, 마이그레이션 1건)
  - FE 단일 기능 (컴포넌트 1개, 훅 1개, 화면 1개 신규/수정, UI 리팩터)
  - 데이터 파이프라인 / ETL
  - AI Agent / LLM 기반 도구
  - 인프라 자동화 (Terraform, Ansible 등)
  - 테스트 자동화 프레임워크

❌ 다른 스킬을 쓰는 경우
  - FE/BE 페어 다중 기능 풀스택 신규 프로젝트 → impl-fe-be-doc
  - RFP/SFR 기반 다중 화면 명세 → impl-fe-be-doc 화면 중심 모드
```

---

## 워크플로우

### Step 0 — 플랫폼·실행 방식 확인 + 프로젝트 유형 확인

#### Step 0-A — 플랫폼·실행 방식 확인

현재 호스트가 독립 작업을 병렬 실행할 수 있는지는 노출된 도구로 확인한다.
관찰 가능한 플랫폼 이름을 사용자에게 다시 묻지 않는다. 작업이 서로 독립적이고
병렬 실행이 실질적으로 유리할 때만 선호를 확인하며, 미지원 또는 미사용 시 순차 실행한다.

#### Step 0-B — 프로젝트 유형 확인 (C-1 확인 단계)

작업지침서 생성 범위를 확정하기 위해 **반드시** 아래를 수행한다.

1. 현재 수행 위치에서 프로젝트 구조를 탐색한다 (git repo 경계, 하위 앱 폴더 후보 스캔).
2. **단일 애플리케이션 프로젝트**인지 **복수 애플리케이션 프로젝트**인지 판정한다.
3. 판정 결과 + 적용 대상 애플리케이션(폴더)을 사용자에게 **반드시 재확인**한다.
4. 확인된 범위 밖은 건드리지 않는다.

> ✋ **확인 게이트**
>
> - 프로젝트 유형: **단일 / 복수** 애플리케이션
> - 적용 대상 애플리케이션(폴더): `{폴더명}`
>
> 맞습니까? **(승인 / 수정 / 취소)**

---

### Step 0-C — design-roadmap·roadmap index preflight

구현계획서 초안을 만들기 전에 반드시 수행한다. Step 8의 사후 갱신만으로는 계획서가
인덱스 없이 저장될 수 있으므로, 이 단계에서 scope를 확정하고 index를 예약한다.

1. 사용자 식별자, 단일/복수 앱 유형, 앱 식별자·source root, repository root, `.ai-docs`
   root를 확인한다.
2. `../impl-doc/{사용자 식별}/` 아래의 실제 `design-roadmap` 위치와 접근 가능한
   `*-roadmap-impl-index.md`를 탐색한다. 단일 앱은 `.ai-docs/impl-doc/{사용자}/`,
   복수 앱은 `.ai-docs/{앱}/impl-doc/{사용자}/`를 계획서 scope로 사용한다.
3. 대상 scope에 index가 없으면 계획서를 쓰기 **전에**
   `{YYMMDD}-0.{앱이름}-roadmap-impl-index.md`를 만들고 `implementation plan pending`,
   사용자·앱·예정 slug/kind·design-roadmap 경로·preflight 시각을 예약 행으로 기록한다.
4. index가 둘 이상이면 임의 선택하지 않고 후보 scope·hash·최근 상태를 사용자에게
   보여준 뒤 선택 전까지 파일을 만들지 않는다. 기존 impl 문서가 index 없이 있으면
   기존 문서를 backfill한 뒤 진행한다.
5. 이 단계에서는 구현·reuse scan·verify 명령을 실행하지 않는다. 경로가 없거나
   앱 식별자가 모호하면 `handoff=blocked`로 보고하고 사용자 확인을 기다린다.

---

### Step 1 — 입력 문서 수집 및 프로젝트 분석

설계 문서가 제공되지 않은 경우 요청한다.

> "구현 지침을 만들 설계 문서를 공유해 주세요.
> design-doc 결과물이나 기존 PRD/설계서 모두 가능합니다."

문서를 받으면 `prompts/analysis.md` 기준으로 분석한다.

추출 항목:
- 프로젝트 유형 (CLI / 라이브러리 / 서비스 / 스크립트 / 파이프라인)
- 모듈 목록 (파일/폴더 단위)
- 외부 의존성 (라이브러리, API, 시스템)
- 핵심 로직 식별
- 입출력 인터페이스 (CLI args, stdin/stdout, API, 파일 I/O)
- 테스트 전략 (단위, 통합, E2E)

분석 후 불명확한 항목 중 최대 3개만 골라 한 번에 묻는다.

---

### Step 2 — Phase 분할

`prompts/phase-design.md`의 분할 기준으로 Phase를 설계한다.

프로젝트 유형별 Phase 패턴과 분할 원칙은 `prompts/phase-design.md` 참조.

Phase 설계 초안을 대화창에 출력한다:

> "Phase 구성을 아래와 같이 제안합니다:
> Phase 0: {내용} — {검증 기준}
> Phase 1: {내용} — {검증 기준}
> ...
> 조정할 부분이 있으면 말씀해 주세요."

---

### Step 3 — 태스크 작성

`prompts/task-rules.md`의 규칙에 따라 각 Phase의 태스크를 작성한다.
산출물의 전체 섹션·필드 순서는 bundled 보호 자산인 `templates/output.md`를 정식
output contract로 사용한다. 템플릿의 placeholder와 주석은 실제 값으로 채우거나
최종 출력에서 제거하되, 템플릿 파일 자체를 삭제·이동·대체하지 않는다.

**범용 태스크 ID 체계**:

```
INIT-XX : 초기화 (프로젝트 구조, 설정, 의존성)
CORE-XX : 핵심 로직 (비즈니스 로직, 알고리즘)
IO-XX   : 입출력 (CLI 파싱, 파일 I/O, API 클라이언트)
API-XX  : BE 엔드포인트 / 라우터 / DTO (BE 단일 기능에서 사용)
DB-XX   : DB 스키마 / 모델 / 마이그레이션 (BE 단일 기능에서 사용)
UI-XX   : FE 컴포넌트 / 화면 / 라우팅 (FE 단일 기능에서 사용)
STATE-XX: FE 상태 / 훅 / 클라이언트 캐시 (FE 단일 기능에서 사용)
TEST-XX : 테스트 (단위 테스트, 통합 테스트)
PKG-XX  : 패키징 (빌드, 배포, 문서화)
```

작업 성격에 맞는 계열만 골라 쓴다. 모두 쓸 필요 없다.

번호는 Phase 내 순서가 아닌 **전체 문서 통합 일련번호**로 부여한다.

각 태스크 필수 항목:
- 태스크 ID + 이름 + 파일 경로
- 의존 태스크
- 구현 내용 (무엇을 왜)
- Agent 지시 (핵심 시그니처 / 주의 분기 — 선택)
- 검증 기준

---

### Step 4 — 검증 시나리오 작성

각 Phase의 통합 검증을 `prompts/verification.md` 형식으로 작성한다.

범용 프로젝트 검증 특징:
- CLI: 명령 실행 → stdout/stderr 확인 → 종료 코드 확인
- 라이브러리: 단위 테스트 실행 → 커버리지 확인
- 서비스: 프로세스 기동 → 헬스체크 → 기능 호출 → 로그 확인
- 스크립트: 입력 파일 → 실행 → 출력 파일 대조

---

### Step 5 — 함정 체크

`prompts/pitfall-checklist.md`의 체크리스트를 실행하여 누락 항목을 검토한다.

---

### Step 6 — 초안 출력 및 사용자 확인

작업지침서 초안을 대화창에 출력하고 승인을 요청한다.

> "위 작업지침서를 검토해 주세요.
> Phase 구성이나 태스크 내용 중 수정할 부분이 있으면 말씀해 주세요."

수정 요청 시 해당 Phase / 태스크만 재작성한다.

---

### Step 7 — 기능 이름 · 구현 종류 · 저장 위치 결정 · 파일 저장

승인 후에만 진행한다. 파일을 무단으로 생성하지 않는다.

**① 기능 이름(slug) 질문** — 파일명에 들어갈 이번 기능 이름을 사용자에게 묻는다.

> "이번에 작성하는 작업지침서의 기능 이름을 알려주세요. (예: log-analyzer, user-auth)"

받은 이름은 kebab-case로 정규화하여 `{slug}`로 쓴다.

**② 구현 종류(kind) 질문** — 이 문서가 다루는 작업 성격을 한 단어로 묻는다.

> "이 작업지침서가 다루는 구현 종류를 한 단어로 알려주세요.
> (예: api, db, ui, screen, cli, lib, script, pipeline, refactor — 자유롭게 한 단어)"

받은 값은 소문자 kebab-case 한 단어로 정규화하여 `{kind}`로 쓴다.

**③ 사용자(`{사용자}`) 확인** — 다음 순서로 정한다.

1. `git config user.name`으로 현재 git 계정을 탐색한다.
2. 탐색되면 사용자에게 **반드시** 확인받는다.
   > "현재 git 계정은 `{git_user}`입니다. 이 이름으로 저장할까요? 다른 이름을 원하면 알려주세요."
3. git 계정이 없거나 사용자가 다른 이름을 원하면 직접 입력받는다.

**④ 저장 디렉토리 결정** — 프로젝트 유형에 따라 분기한다.

- **단일 앱**: `.ai-docs/impl-doc/{사용자}/`
- **복수 앱**: `.ai-docs/{앱}/impl-doc/{사용자}/` (예: `.ai-docs/app-backend/impl-doc/developer/`)

디렉토리가 없으면 생성한다.

**⑤ 파일명 산정 (날짜 + 순번)**

파일명 포맷:
```
{YYMMDD}-{seq}.{slug}-impl-{kind}.md
```

- `{YYMMDD}` — 작성/갱신 시점 오늘 날짜를 2자리 연/월/일로 (예: 2026-06-30 → `260630`).
- `{seq}` — **저장 디렉토리 안에서 `{YYMMDD}-` 접두 파일들의 최대 순번 + 1** (없으면 `1`). 디렉토리를 `ls`로 스캔하여 같은 날짜의 가장 큰 `-N` 을 찾아 산정한다.
- `{slug}` — ①에서 받은 기능명(kebab-case).
- `{kind}` — ②에서 받은 구현 종류 한 단어.

예시:
- `.ai-docs/app-backend/impl-doc/developer/260630-1.user-auth-impl-api.md`
- `.ai-docs/app-backend/impl-doc/developer/260630-2.user-auth-impl-db.md`
- `.ai-docs/app-frontend/impl-doc/developer/260630-3.search-result-impl-ui.md`

**⑥ 중복 검사 및 갱신 처리**

새로 쓰기 전에 같은 저장 디렉토리에서 **`{slug}-impl-{kind}.md` 로 끝나는 기존 파일**을 모두 찾는다.

| 상황 | 처리 |
|------|------|
| 동일 `{slug}-impl-{kind}` 파일 없음 | 신규 생성 (⑤ 파일명 그대로) |
| 동일 `{slug}-impl-{kind}` 파일 1개 이상 존재 | 사용자에게 "**기존 파일을 갱신할지 / 새 버전으로 신규 생성할지**"를 묻는다 |
| 비슷하지만 slug/kind가 다른 후보 | 화면에 나열하고 "동일 작업인지" 확인 |

**갱신을 선택한 경우**:
- 갱신 대상 기존 파일을 **⑤에서 산정한 새 파일명(현재 날짜·순번)으로 rename** 한다.
- 내용은 새로 작성한 본문으로 덮어쓴다.
- 문서 머리말에 **갱신일자**를 갱신/추가한다.
- 다른 사용자/git 계정이 작성한 파일을 갱신하는 경우, 머리말에 **갱신자(사용자 이름 또는 git 계정)를 추가 표기**한다.

**신규 생성을 선택한 경우**:
- ⑤ 파일명 그대로 새 파일을 만든다 (기존 파일은 손대지 않는다).

**⑦ 공통 규칙**

- 파일명은 스킬별로 구분하지 않는다. **어떤 스킬로 만들었는지는 문서 머리말의 `생성 스킬: impl-doc` 표기로만 구분**한다.
- 저장 직전에 `{slug}`, `{kind}`, 최종 파일명을 사용자에게 한 번 더 확인한다.
  > "다음 파일명으로 저장합니다: `{YYMMDD}-{seq}.{slug}-impl-{kind}.md`. 맞나요?"

---

### Step 8 — 로드맵 인덱스 문서 생성·갱신

Step 7 저장이 끝난 뒤 **반드시** 수행한다. 대상은 Step 7 ④에서 정한 저장 디렉토리
(`.ai-docs/impl-doc/{사용자}/` 또는 `.ai-docs/{앱}/impl-doc/{사용자}/`) 안의
**로드맵 인덱스 문서 1개**다. 이 문서는 impl-doc/impl-fe-be-doc이 함께 쓰는 공용 산출물이며,
"이 디렉토리에 어떤 impl 문서들이 있고, 지금 어디까지 왔는가"를 한 곳에서 보여준다.

**① 인덱스 파일 탐색** — 저장 디렉토리를 스캔해 `*-roadmap-impl-index.md`로 끝나는 파일을 찾는다.

**② 최초 사용 (인덱스 파일 없음)** — 이 스킬로 해당 디렉토리에 생성하는 **첫 문서**라면,
Step 7에서 방금 저장한 문서와 같은 자리에 인덱스 문서를 새로 만든다.

파일명 포맷 (일반 impl 문서와 순번 체계를 분리하기 위해 `{seq}`를 항상 `0`으로 고정):
```
{YYMMDD}-0.{앱이름}-roadmap-impl-index.md
```
- `{YYMMDD}` — 인덱스 문서를 처음 만드는 시점의 날짜. 이후 문서 내용이 갱신되어도 파일명은 **바꾸지 않는다** (일반 impl 문서처럼 최신 날짜로 rename하지 않음).
- `{앱이름}` — 단일앱은 프로젝트명, 복수앱은 대상 애플리케이션 폴더명(예: `collector`, `portal`).

구조는 현재 프로젝트의 기존 `*-roadmap-impl-index.md`가 있으면 그 사용자 확장을
보존해 따르고, 없으면 아래의 일반 섹션 계약으로 새로 만든다:
- 머리말: 생성 스킬, 작성일자, 갱신일자, 작성/갱신 계정, 목적, 현재 진행 위치
- `impl-doc 분할 구조` 표: 문서 목록(순서/문서명/상태/범위)
- 전체 페이즈·단계 경계(있다면) 또는 기능 로드맵 개요
- 단계별 상세(진행 중/예정 단계는 방향만, 착수 시 구체화한다고 명시)
- 미래 단계 공통 원칙

**③ 이미 사용 중 (인덱스 파일 있음)** — Step 7에서 신규 문서를 만들었거나 기존 문서를 갱신했다면,
그 변화를 인덱스 문서에 **바로 반영**한다:
- 신규 문서 추가 시: 분할 구조 표에 새 행 추가, 상태를 진행 상황에 맞게 표기
- 기존 문서 갱신 시: 해당 행의 상태·범위 설명을 갱신
- 머리말의 `갱신일자`와 `현재 진행 위치`를 항상 최신 상태로 갱신
- 갱신자가 원작성자와 다르면 머리말에 갱신 계정을 추가 표기 (Step 7 ⑥과 동일 규칙)

**④ 인덱스 파일이 없는데 impl 문서가 이미 존재하는 경우** — 이번이 이 스킬로 만드는 첫 문서가 아니더라도
인덱스 파일 자체가 없으면 ②의 규칙으로 새로 만들되, 디렉토리를 스캔해 기존 impl 문서들을 분할 구조 표에 **소급 반영**한다.

**⑤ 저장 전 확인** — 인덱스 문서의 신규 생성/갱신 내용을 요약해 사용자에게 보여주고 저장한다. 별도 승인 게이트 없이 Step 7 승인에 포함된 것으로 간주하되, 인덱스 문서만 크게 구조가 바뀌는 경우(최초 생성, 스테이지 경계 변경 등)에는 저장 직전 한 번 더 확인한다.

## downstream 구현·검증 handoff

계획서와 index를 저장한 뒤 실제 구현 흐름은 모든 Phase/태스크에서 다음 블록을 따른다.
이 route는 자동 하위 스킬 실행이 아니라 사용자가 실행할 명시적 handoff다.

```yaml
downstream:
  roadmap_index: <verified index path>
  phase: <phase id>
  reuse_scan:
    skill: impl-reuse-scan
    trigger: phase-start
    status: required | not-applicable | passed | pending
    input: <plan path + task/asset scope + source root>
    decision: reuse | extend | new | deferred | pending
    evidence: <report reference or reason>
  verify:
    skill: impl-verify
    trigger: phase-end
    invocation: explicit-only
    status: required | passed | failed | skipped | pending
    input: <plan path + task/phase/full scope + implementation root>
    evidence: <verification report reference>
```

Phase 시작에는 `$impl-reuse-scan`을 호출해 후보를 보고하고 사용자 결정 전에는 패치하지
않는다. Phase 종료에는 `$impl-verify`를 명시 호출한다. `impl-verify`는
`disable-model-invocation: true`를 유지하므로 route가 자동 실행을 의미하지 않는다.
FAIL은 다음 Phase 진입 불가 권고로 index/evidence에 전달한다.

---

## impl-fe-be-doc과의 차이

| 관점 | impl-fe-be-doc | impl-doc (이 스킬) |
|------|---------------|-------------------|
| **중심 축** | FE/BE 페어 또는 다중 화면 | 단일 기능 / 모듈 단위 |
| **Phase 단위** | BE+FE 페어 기능 또는 화면 1개당 1 Phase | 입출력 파이프라인 또는 단일 기능 |
| **태스크 ID** | INF/BE/FE 계열 | INIT/CORE/IO/API/DB/UI/STATE/TEST/PKG-XX |
| **검증 방식** | FE→API→DB E2E, 화면 렌더링+API | 작업 성격별 (CLI/단위 테스트/API curl/컴포넌트 렌더링) |
| **적합 대상** | 풀스택 다중 기능, RFP 화면 기반 | 단일 BE 기능, 단일 FE 기능, 도구, 스크립트, 라이브러리 |
| **규모 감각** | 다중 화면/다중 기능 | 단일 화면/단일 기능/단일 모듈 |

---

## 문서 개선 후처리와 완료 게이트

직접 호출에서는 구현 계획서와 로드맵 인덱스를 하나의 bundle로 묶는다. 상위
producer가 전달한 실행 컨텍스트가 있으면 새 ID나 owner를 만들지 않는다.

```text
artifact_bundle_id = impl-doc:{정규화한 프로젝트 루트}:{이번 실행의 고유 ID}
handoff_owner = impl-doc
suppress_child_handoff = false
handoff_completed = false
```

Step 7의 계획서 저장 검증과 Step 8의 인덱스 링크·분할 구조 검증을 모두 마친 뒤,
owner이고 억제되지 않았으며 아직 완료되지 않은 bundle에 대해서만
`humanize-korean`의 `document-refinement` 프로필을 한 번 제안한다. 상위
producer가 owner이면 초안과 검증 결과만 반환한다.

최종 검증된 계획서·인덱스의 정규화 상대경로와 각 파일 SHA-256, profile 이름을
정렬해 `artifact_bundle_fingerprint`를 계산한다. `.ai-docs/.harness/
humanize-handoffs.json` 원자적 ledger에 같은 fingerprint의 `proposed`, `skipped`,
`rejected`, `applied`, `revalidated` 완료 기록이 있으면 새 session에서도
재제안하지 않는다. 새 결정은 bundle ID, owner, 파일 hash, 시각과 함께 기록하고
승인 반영 후에는 `applied`와 `revalidated`를 순서대로 갱신한다. ledger 자체는
개선 대상에서 제외하며 기록할 수 없으면 현재 session 한정 상태로 보고한다.

기본은 proposal-only이며 사용자 승인 전 파일 반영은 금지한다. 단계 번호, 파일
경로, 명령어, API/요구사항 ID, 숫자, 날짜, 의무 수준 표현은 보존한다.
제안·건너뛰기·거절 중 하나가 결정되면 `handoff_completed = true`와 ledger 상태를
함께 기록한다.

승인된 변경을 반영한 경우 태스크 ID, 파일 경로, 명령어, 검증 시나리오와 Step 8
인덱스 링크를 다시 검증한다. 재검증된 구현 계획서와 인덱스만 downstream 구현·
검증 스킬의 입력으로 사용한다.
