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
| 병렬 처리 설계 | [병렬 처리 규칙] |

---

## [구조 원칙]

### 파일별 책임

```
SKILL.md       → 흐름(What & When)만. 규칙(How)은 prompts에.
prompts/*.md   → 파일 하나 = 역할 하나. 두 역할 혼재 금지.
templates/*.md → 출력 구조만. 예시 데이터 금지.
```

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
