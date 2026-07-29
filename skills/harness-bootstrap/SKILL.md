---
name: harness-bootstrap
description: >
  AI 하네스 문서가 전혀 없는 기존 코드베이스에 처음으로 하네스를 부팅할 때 사용한다.
  '하네스 부팅', '기존 코드 분석해서 문서 만들어줘', '레거시 프로젝트 문서화',
  'CLAUDE.md 없는데 생성', '설계 문서 역추출', 'AI 문서 부트스트랩',
  '기존 프로젝트에 하네스 도입' 요청이 오면 이 스킬을 사용한다.
  기존 코드베이스 → design-doc OUTPUT_V2 형식 설계 문서 + context-doc 결과물(AGENTS.md 정본 + CLAUDE.md bridge + .docs/instruction/*) 자동 도출.
  프레임워크 자동 감지. 최소 인터뷰(2회 이하)로 코드에서 추출 불가능한 도메인 맥락만 보충.
allowed-tools: Read, Glob, Grep, Bash, Write
---

# 하네스 부트스트랩 (harness-bootstrap)

기존 코드베이스만 있고 AI 하네스 문서(CLAUDE.md, AGENTS.md, 설계 문서, instruction 등)가 전혀 없을 때,
코드를 직접 분석해서 다음 두 산출물을 한 번에 도출한다.

1. **`design-doc` OUTPUT_V2 형식 설계 문서** (프로젝트 설계 스냅샷)
2. **`context-doc` 결과물** — `AGENTS.md` 정본 + `CLAUDE.md` bridge + `.docs/instruction/*-instruction.md`

생성 전 반드시 사용자 확인을 거친다. 파일을 무단으로 생성하지 않는다.

> 이 스킬은 "레거시/기존 프로젝트에 AI 하네스를 처음 도입"하는 진입점이다.
> 이후부터는 `design-doc` → `context-doc` 정규 플로우를 그대로 쓰면 된다.

> **공개 계약 재사용**: 이 스킬은 `design-doc`과 `context-doc`의 공개 산출물 계약을 한 번에 수행하는 통합 스킬이다. 다른 스킬의 내부 구현 경로에 결합하지 않고, 필요한 템플릿 구조는 이 문서의 AGENTS 정본 + CLAUDE bridge 계약을 따른다.

---

## 설계 원칙

1. **코드에서 추출 가능한 건 모두 자동 추출**. 질문하지 않는다.
2. **코드에서 알 수 없는 것만 인터뷰**. 도메인 목적·사용자·상위 비즈니스 맥락.
3. **인터뷰는 최대 2회**. 그 이상은 `미정 — [이유]` 로 남긴다.
4. **공개 산출물 계약을 재사용한다**. `design-doc` OUTPUT_V2 형식과 `context-doc`의 AGENTS 정본 + CLAUDE bridge 구조를 따른다.
5. **프레임워크 중립**. 매니페스트 파일 기반으로 자동 감지한다.

## 질문 예산

사용자 질문 총합은 **최대 3회**다.

- Step 1의 저장소 루트/프로젝트 단위 확인: 최대 1회
- Step 3의 인터뷰: 최대 2회
- Step 6의 `context-doc` 단계에서는 **새 질문을 추가하지 않는다**
- 예산이 소진되면 추가 확인 대신 `미정 — [이유]` 로 남긴다

---

## 스킬 연계

```
기존 코드베이스 (AI 문서 없음)
        │
        ▼
/harness-bootstrap
        │
        ├─ Step 1~4: 코드 스캔 + 최소 인터뷰
        │
        ├─ Step 5: design-doc OUTPUT_V2 산출
        │            └── 저장: {project}/.docs/context-base/DESIGN.md (또는 사용자 지정)
        │
        └─ Step 6~7: context-doc 파이프라인 실행
                     └── 저장: AGENTS.md + CLAUDE.md bridge + .docs/instruction/*-instruction.md
```

이후 작업은 정규 플로우를 따른다.
- 설계 변경 시 → `design-doc`로 OUTPUT 갱신 후 → `context-doc`로 하네스 갱신
- 문서-코드 괴리 검증 → `doc-audit`
- 구현 지침이 필요하면 → `impl-fe-be-doc` / `impl-doc`
- 구현 직전 공통 자산 확인 → `impl-reuse-scan` (선택)
- 단계/페이즈 종료 검증 → `impl-verify` (선택)

## 중간 산출물 재사용

- `.docs/context-base/DESIGN.md`만 먼저 저장해도, 이후에는 저장소 재스캔 없이
  `@.docs/context-base/DESIGN.md /context-doc`로 정규 컨텍스트 생성 흐름을 다시 탈 수 있다.
- 한 번 부트스트랩이 끝난 프로젝트는 구조 변경 시 `harness-bootstrap`을 반복하기보다
  `design-doc` → `context-doc` 갱신을 기본 경로로 쓴다.

---

## 워크플로우

### Step 0 — 플랫폼·실행 방식 확인 + 프로젝트 유형 확인

#### Step 0-A — 플랫폼·실행 방식 확인

사용자에게 아래를 확인한다:

> 1. 서브에이전트(병렬 처리)를 사용할 수 있는 환경인가요? (Claude Code / Codex / 기타)
> 2. 사용할 경우 병렬 실행을 원하시나요?

서브에이전트 미지원 또는 미사용 선택 시 순차 실행한다.

#### Step 0-B — 프로젝트 유형 확인 (C-1 확인 단계)

부트스트랩 범위를 확정하기 위해 **반드시** 아래를 수행한다.

1. 현재 수행 위치에서 프로젝트 구조를 탐색한다 (git repo 경계, 하위 앱 폴더 후보 스캔).
2. **단일 애플리케이션 프로젝트**인지 **복수 애플리케이션 프로젝트**인지 판정한다.
3. 판정 결과 + 적용 대상 애플리케이션(폴더)을 사용자에게 **반드시 재확인**한다.
4. 확인된 범위 밖은 건드리지 않는다.

> ✋ **확인 게이트**
>
> - 프로젝트 유형: **단일 / 복수** 애플리케이션
> - 부트스트랩 대상 애플리케이션(폴더): `{폴더명}`
>
> 맞습니까? **(승인 / 수정 / 취소)**

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

코드에서 **절대 알 수 없는 것**만 묻는다.

**필수 질문 1** — 도메인·목적·사용자
> "이 프로젝트는 어떤 사용자가, 어떤 문제를 해결하기 위해 쓰는 시스템인가요?
> 2~3줄로 설명해 주세요."

**선택 질문 2** — 상위 맥락/제약 (필요시에만)
> "이 프로젝트가 속한 상위 시스템이 있거나, 반드시 지켜야 할 운영 제약이 있으면 알려주세요.
> 없으면 '없음'이라고만 답해 주세요."

**묻지 않는 것**:
- 기술 스택 (매니페스트에서 이미 알 수 있음)
- 디렉토리 구조, API 목록, 환경 변수 목록 (코드에서 추출)
- 코딩 컨벤션 세부 (코드 스타일에서 역추론)

답변이 없거나 불충분하면 `미정 — 사용자 미제공` 으로 표시하고 진행한다.

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

`../design-doc/templates/OUTPUT_V2.md` 양식을 그대로 사용해 설계 문서 초안을 생성한다.

- 작성 지침(주석)은 제거한 상태로 출력
- 해당하지 않는 스케일 섹션은 삭제
- 불명확한 항목은 `미정 — [이유]` 로 표시
- 사용자가 별도 중단을 요청하지 않으면, **설계 초안 확인 후 바로 Step 6으로 연속 진행**한다.
- 설계 초안 단계의 확인은 **수정 포인트 수집용**이며, 최종 저장 승인은 Step 7에서 1회만 받는다.

초안을 대화창에 출력하고 확인받는다.

> "위 설계 문서를 검토해 주세요.
> 수정할 부분이 있으면 말씀해 주시고, 이상 없으면 바로 `context-doc` 단계까지 이어서 초안을 완성하겠습니다.
> 저장 경로는 `.docs/context-base/DESIGN.md` 로 하겠습니다. 변경 원하시면 알려주세요."

---

### Step 6 — context-doc 파이프라인 실행

Step 5 OUTPUT을 입력으로 삼아 `context-doc` 스킬의 워크플로우를 그대로 실행한다.

- AGENTS.md 정본에 들어갈 프로젝트 팩트 + 지침 인덱스 초안 작성
- `../context-doc/prompts/analysis-instruction.md` 기준으로 주제별 instruction 파일 분류
- AGENTS 정본 + CLAUDE bridge + 각 `*-instruction.md` 구조 활용
- 모노레포 감지 시 `.docs/instruction/` 배치 질문 (context-doc의 Step 2와 동일)

이 단계에서는 **새로운 인터뷰를 추가하지 않는다**. Step 3 답변 + Step 5 OUTPUT으로 충분하다.
또한 bootstrap 한계 때문에 아래 오버라이드를 적용한다.

- 코드/README/주석에서 **규범적 이유·대안이 확인된 금지 항목만** 삼위일체로 기록한다.
- 관찰 사실만 있고 이유·대안이 확정되지 않으면 `미정 — bootstrap 산출물에는 규범 근거 없음`으로 남긴다.
- 이 사유로는 사용자를 다시 인터뷰하지 않는다. 후속 `design-doc` → `context-doc` 보강 대상으로 넘긴다.

---

### Step 7 — 미리보기 및 일괄 저장

생성된 모든 파일 초안을 대화창에 순서대로 출력하고 승인을 요청한다.

출력 순서:

**단일 애플리케이션:**
1. `.docs/context-base/DESIGN.md` (또는 사용자 지정 경로)
2. `AGENTS.md`
3. `CLAUDE.md` (`@AGENTS.md` bridge)
4. `.docs/instruction/*-instruction.md` (해당 주제만)

**복수 애플리케이션:**
1. `.docs/{앱}/context-base/DESIGN.md`
2. `.docs/{앱}-context.md` (단일앱의 CLAUDE.md/AGENTS.md에 해당하는 내용)
3. `.docs/{앱}/instruction/*-instruction.md` (해당 주제만)
4. `.docs/root-context/AGENTS.md`, `.docs/root-context/CLAUDE.md` (루트 통합 인덱스 복사본)

(단, 설계 문서에 해당 주제가 없으면 instruction 파일은 생성하지 않는다 — context-doc 원칙 그대로)

> "위 파일들을 검토해 주세요.
> 이상 없으면 한꺼번에 저장하겠습니다. 수정 사항이 있으면 알려주세요."

승인 시 STEP 0에서 확정한 프로젝트 유형에 따라 분기한다.

**단일 애플리케이션:**
- `.docs/instruction/` 디렉토리가 없으면 생성
- 설계 문서 저장 폴더(`.docs/context-base/`)가 없으면 생성
- 모든 파일 일괄 저장
- `AGENTS.md`의 `@.docs/instruction/*` 참조가 실제 파일과 1:1 일치하는지 검증
- `CLAUDE.md`가 `@AGENTS.md` bridge인지 검증

**복수 애플리케이션:**
- `.docs/{앱}/instruction/` 디렉토리가 없으면 생성
- `.docs/{앱}/context-base/` 디렉토리가 없으면 생성
- `.docs/root-context/` 디렉토리가 없으면 생성
- 설계 문서: `.docs/{앱}/context-base/DESIGN.md` 저장
- 컨텍스트 문서: `.docs/{앱}-context.md` 저장
- instruction: `.docs/{앱}/instruction/*-instruction.md` 저장
- 루트 통합: `.docs/root-context/CLAUDE.md`, `.docs/root-context/AGENTS.md` 저장
- `.docs/{앱}-context.md`의 instruction 참조가 `.docs/{앱}/instruction/` 내 실제 파일과 1:1 일치하는지 검증
- `.docs/root-context/CLAUDE.md`가 `@AGENTS.md` bridge인지 검증

**공통:**
- 이미 존재하는 파일이 있으면 덮어쓰기 전에 사용자에게 알림

---

## 문서 개선 후처리

`DESIGN.md`, `AGENTS.md`, `CLAUDE.md` 초안 생성 후에는 `humanize-korean`의 `document-refinement` 프로필로 한국어 문장 개선안을 제안할 수 있다.

- 후처리는 proposal-only가 기본이다.
- 승인 전 파일 쓰기는 금지한다.
- 요구사항, 경로, ID, 숫자, 날짜, 코드 fence, 표 구조, 의무 수준은 변경하지 않는다.
