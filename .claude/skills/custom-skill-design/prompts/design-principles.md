# prompts/design-principles.md
# 역할: 스킬 파일 작성 시 적용할 설계 원칙

---

## 라우팅 표

| 작성 단계 | 읽을 섹션 |
|----------|----------|
| SKILL.md 초안 작성 | [SKILL.md 작성 규칙] |
| prompts 파일 작성 | [prompts 작성 규칙] |
| templates 파일 작성 | [templates 작성 규칙] |
| 구조 결정 | [구조 원칙] |
| 지침 자유도 결정 | [지침 자유도] |
| Codex 메타데이터 결정 | [Codex 메타데이터] |
| 병렬 처리 설계 | [병렬 처리 규칙] |

---

## [구조 원칙]

### 파일별 책임

```
SKILL.md       → 흐름(What & When)만. 규칙(How)은 prompts에.
prompts/*.md   → 파일 하나 = 역할 하나. 두 역할 혼재 금지.
templates/*.md → 출력 구조만. 예시 데이터 금지.
references/*.md → 필요할 때만 읽을 상세 지식. 한 단계 깊이로 직접 연결.
scripts/*       → 결정론적 반복 작업. 대표 입력으로 실제 실행 검증.
assets/*        → 결과물에 복사·사용할 정적 자산.
agents/openai.yaml → 필요한 경우의 Codex UI 메타데이터.
```

### 점진적 공개와 컨텍스트 예산

1. 탐색 단계에는 frontmatter의 `name`과 `description`만 보이도록 핵심 트리거를
   간결하게 쓴다.
2. 호출 후에는 `SKILL.md`만으로 전체 흐름과 필요한 자산 경로를 파악할 수 있어야 한다.
3. `prompts/`, `references/`, `templates/`는 해당 Step에서 필요한 파일만 읽게 한다.
   `assets/`는 결과물에 복사·사용하고, 시각·형식 검사가 필요한 때만 읽는다.
   reference가 다른 reference를 다시 따라가게 하는 깊은 연결은 만들지 않는다.
4. `SKILL.md`는 가능하면 500줄 이하로 유지하고, 모델이 이미 아는 일반 설명보다
   이 워크플로에만 필요한 비자명한 제약과 짧은 예시를 우선한다.
5. 실행에 필요하지 않은 `README.md`, `INSTALL.md`, `CHANGELOG.md` 같은 보조 문서는
   스킬 폴더 안에 새로 만들지 않는다.

### 보조 자산 선택

- 같은 결정론적 코드를 세 번 이상 다시 쓰게 되면 `scripts/` 후보로 분리한다.
- 길거나 특정 도메인에만 필요한 지식은 `references/`에 두고 읽는 조건을 명시한다.
- 최종 결과물에 복사하거나 렌더링할 파일은 `assets/`에 둔다.
- 기존 `prompts/`, `templates/`, `scripts/`, `assets/`, `evals/`를 다른 구조로
  옮기거나 교체하는 일은 별도 보호 자산 영향으로 분리하고 승인 없이 수행하지 않는다.

### 연계 스킬이 있을 때 SKILL.md 상단 형식

```markdown
## 스킬 연계

upstream-skill OUTPUT
    ↓
this-skill
    ↓
downstream-skill 입력으로 사용 가능

| 업스트림 OUTPUT 섹션 | 이 스킬에서의 사용 위치 |
|---------------------|------------------------|
| [섹션명]            | [사용 위치]             |
```

---

## [SKILL.md 작성 규칙]

### 헤더 필수 항목

```yaml
---
name: skill-name                          # kebab-case
description: "트리거 상황 명시 — 언제, 어떤 키워드에 호출되는지"
allowed-tools: Read, Write, Glob, Grep     # 실제 사용하는 안전한 공통 도구만
disable-model-invocation: true            # 외부 상태 변경·명령 실행·재귀 위험으로 명시 호출만 허용할 때
---
```

- `name`은 64자 이하의 kebab-case로 쓰고, 가능하면 수행 동작이 드러나는 동사형을
  사용한다. 도구별 동명이인 충돌 가능성이 있으면 짧은 namespace를 붙인다.

### 헤더 금지 항목

- **`model:` 필드 금지** — 모델 선택은 사용자·환경에 위임한다. frontmatter에 하드코딩하지 않는다.
- **`agent: fork` 하드코딩 금지** — 서브에이전트/병렬 사용 여부는 STEP 0에서 사용자에게 질문하는 게이트로 처리한다. frontmatter로 강제하지 않는다.
- **제한 없는 `Bash` 사전 승인 금지** — shell이 필요해도 `allowed-tools`에
  무제한 `Bash`를 넣지 않는다. 실행은 플랫폼의 일반 permission mode로 넘기고
  Windows·POSIX 절차 또는 수동 fallback을 함께 쓴다.
- **부작용 스킬 자동 호출 금지** — 커밋, Git 설정, 작업지침 명령 실행처럼 외부
  상태를 바꾸거나 임의 명령을 실행하는 스킬은 `disable-model-invocation: true`와
  플랫폼별 직접 호출 예시를 함께 둔다.

### 플랫폼 중립 원칙 (C-3)

- frontmatter는 Codex가 무시해도 안전하고 Claude Code가 해석할 수 있는 공통 최소
  필드(`name`, `description`, `allowed-tools`)를 사용한다.
- 본문은 **Codex 등 타 플랫폼에서도 해석 가능한 중립 서술**로 작성한다.
- 플랫폼 전용 기능(sub-agent/Agent, 앱 전용 UI 등)은 STEP 0에서 지원 여부를 감지하고
  미지원 환경의 순차 fallback을 제공한다.

### description 작성 기준

- "~할 때", "~을 요청할 때" 형식으로 트리거 상황을 구체적으로 나열
- 트리거 키워드 3개 이상 포함 (Agent가 undertrigger하는 경향 보정)
- 무엇을 하는지(What) + 언제 쓰는지(When) 모두 포함

---

## [지침 자유도]

작업의 변동성과 실패 비용에 따라 지침의 구체성을 정한다.

| 자유도 | 적용 대상 | 작성 방식 |
|---|---|---|
| 높음 | 창의적·탐색적이며 여러 해법이 유효한 작업 | 목표·품질 기준·금지선 중심 |
| 중간 | 선호 패턴은 있지만 프로젝트별 차이가 있는 작업 | 의사코드·선택 기준·검증 예시 |
| 낮음 | 순서 오류가 위험하거나 결과가 결정론적이어야 하는 작업 | 정확한 순서·스크립트·실패 처리 |

모든 작업을 세세한 명령으로 고정하거나, 취약 절차를 모호한 원칙만으로 남기지 않는다.

---

## [Codex 메타데이터]

- Codex에서 목록 표시, 기본 프롬프트, 도구 연결 같은 UI 메타데이터가 실제로 필요할
  때만 `agents/openai.yaml`을 생성한다.
- 메타데이터는 SKILL.md의 `name`, `description`, 공개 동작 계약과 일치시킨다.
- 최소 UI schema는 다음처럼 작성한다. 문자열 값은 모두 따옴표로 감싸고 key는
  따옴표로 감싸지 않는다.

```yaml
interface:
  display_name: "사용자에게 보일 이름"
  short_description: "25~64자의 짧은 설명"
  default_prompt: "Use $skill-name to perform the intended workflow."

policy:
  allow_implicit_invocation: true
```

- `interface.default_prompt`는 짧은 한 문장으로 쓰고 실제 `$skill-name`을 명시한다.
- 아이콘이 필요할 때만 `icon_small`·`icon_large`를 `./assets/...` 상대경로로 추가하고
  해당 자산의 존재를 확인한다. MCP 의존성이 실제로 있을 때만 `dependencies.tools`를
  추가하며 현재 지원 타입은 `mcp`로 제한한다.
- 외부 상태 변경·명시 호출 전용 스킬은 `policy.allow_implicit_invocation: false`를
  사용한다. 그 외에는 실제 호출 정책에 맞춰 결정한다.
- 플랫폼이 공개한 생성기·validator가 현재 환경에 있으면 공개 스킬 계약으로 조건부
  사용한다. 특정 사용자 홈이나 다른 스킬의 내부 스크립트 절대경로는 기록하지 않는다.
- 공개 validator가 없으면 위 schema, 따옴표, 글자 수, `$skill-name`, 상대경로를
  수동 검사하고 검증 상태를 `수동 점검`으로 보고한다. 검증하지 않은 파일을
  `validator 통과`로 표시하지 않는다.
- Claude 대상에서는 `agents/openai.yaml`이 없어도 핵심 workflow가 완전해야 한다.

### Step 서술 규칙

- Step별로 "어느 prompts 파일의 어느 섹션을 참조하라"만 명시
- 규칙 내용을 SKILL.md에 직접 쓰지 않는다 → 이중 명세 금지
- 사용자 확인 게이트 위치를 명시한다

### 조건부 파일 로드 명시 방법

```markdown
# 좋은 예
Step 2에서 감지된 언어에 해당하는 섹션만 `prompts/style-guide.md`에서 참조한다.

# 나쁜 예
`prompts/style-guide.md`를 참조하여 주석을 작성한다.
```

### 진입 분기가 있을 때

SKILL.md 상단에 분기표를 둔다:

```markdown
## 진입 분기

| 상황 | 이동할 Step |
|------|------------|
| [상황 A] | Step X → Y → Z |
| [상황 B] | Step X → Z (Y 건너뜀) |
```

---

## [prompts 작성 규칙]

### 단일 책임 원칙

- 파일 하나 = 역할 하나
- 두 역할이 섞이면 반드시 분리

```
❌ analysis.md에 인터뷰 질문 + 출력 형식 규칙 혼재
✅ interview.md (질문만) / output-rules.md (형식만) 분리
```

### 라우팅 표 (조건 분기가 있는 파일 필수)

파일 상단에 라우팅 표를 둔다:

```markdown
## 라우팅 표

| 조건 | 읽을 섹션 |
|------|----------|
| [조건 A] | ## [섹션명] |
| [조건 B] | ## [다른 섹션명] |
```

### 질문 우선순위 규칙

```
🔴 필수 확인 (최대 2개): 추론 불가능한 것만
🟡 선택 확인 (최대 1개): 필수 답변 후에도 불명확한 것만
한 번에 최대 3개 초과 금지
```

### 외부 명령 작성 규칙 (외부 명령 사용 스킬)

- 먼저 `Glob`·`Read` 등 공통 도구로 대상 존재 여부와 범위를 확인한다.
- 외부 명령은 감지된 대상에만 실행하고 종료 코드와 stderr를 판정한다.
- 대용량 출력은 파일·줄·결과 수를 제한하고, 변경이 없으면 즉시 종료한다.
- 플랫폼 중립 스크립트를 우선하며 Windows와 POSIX 호출 예 또는 수동 fallback을
  함께 둔다.
- `allowed-tools`에서 제한 없는 shell을 사전 승인하지 않는다.

### 병렬 처리 규칙 (해당 스킬만)

참조: [병렬 처리 규칙] 섹션

---

## [templates 작성 규칙]

### 핵심 규칙

- **구조(열 이름, 섹션 헤더)만** 작성
- 예시 데이터 절대 금지 → HTML 주석으로 대체

```markdown
# 나쁜 예
| 1 | auth/CLAUDE.md | JWT → Session | 보안 취약점 |

# 좋은 예
| # | 대상 파일 | 현재 내용 | 제안 내용 | 이유 |
|---|-----------|-----------|-----------|------|
<!-- 예시: | 1 | auth/CLAUDE.md | JWT 방식 | Session 방식 | 보안 취약점 발견 | -->
```

새 `scripts/` 파일을 추가했다면 도움말 출력만 보지 말고 정상 입력, 실패 입력,
경계 입력 가운데 대표 사례를 실제로 실행해 종료 코드와 산출물을 확인한다.

---

## [병렬 처리 규칙]

### 병렬 적합 여부 판단

```
적합: 독립적, 결과가 서로 영향 없음, 3~6개 관점
부적합: 선행 결과 필요, 동일 파일 동시 수정, 2개 이하 관점
```

### 병렬 sub-agent 수 기준

```
2개 이하 → 순차 실행
3~6개    → 병렬 sub-agent
7개 이상 → 재설계 (관점 과다)
```

### SKILL.md 내 병렬 구조 표기법

```markdown
아래 N개 관점을 독립 sub-agent로 병렬 실행한다.
sub-agent 미지원 환경이면 순차로 직접 수행한다.

├── 작업 A: [관점명] → `prompts/a.md` 참조
├── 작업 B: [관점명] → `prompts/b.md` 참조
└── 작업 C: [관점명] → `prompts/c.md` 참조
```
