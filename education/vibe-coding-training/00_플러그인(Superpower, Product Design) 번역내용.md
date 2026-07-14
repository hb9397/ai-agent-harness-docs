## Superpower

아래 내용은 Superpowers 6.1.1에 포함된 각 `SKILL.md` 원문의 한글 번역이다. 스킬명과 frontmatter의 원문 표기는 유지한다.

#### 플러그인: Superpowers · 스킬명: `dispatching-parallel-agents` — 병렬 에이전트 분배

````markdown
**설명:** 공유 상태나 순차 의존성 없이 처리할 수 있는 독립 작업이 두 개 이상일 때 사용한다.

# 병렬 에이전트 분배

## 개요

격리된 컨텍스트를 가진 전문 에이전트에게 작업을 위임한다. 지시와 컨텍스트를 정확하게 작성하면 에이전트가 작업에 집중하여 성공하도록 만들 수 있다. 에이전트는 현재 세션의 컨텍스트나 이력을 상속하면 안 된다. 에이전트에 필요한 내용만 정확히 구성해 제공한다. 이렇게 하면 조정 작업을 위한 자신의 컨텍스트도 보존된다.

서로 관계없는 실패가 여러 개일 때(서로 다른 테스트 파일, 하위 시스템, 버그), 이를 순차로 조사하면 시간이 낭비된다. 각 조사는 독립적이므로 병렬로 진행할 수 있다.

**핵심 원칙:** 독립적인 문제 영역마다 에이전트 한 명을 배정한다. 동시에 작업하게 한다.

## 사용할 때

- 근본 원인이 서로 다른 테스트 파일이 3개 이상 실패할 때
- 여러 하위 시스템이 독립적으로 고장 났을 때
- 각 문제를 다른 문제의 컨텍스트 없이 이해할 수 있을 때
- 조사 사이에 공유 상태가 없을 때

## 사용하지 않을 때

- 실패들이 서로 연관되어 있을 때(하나를 고치면 다른 것도 고쳐질 수 있음)
- 전체 시스템 상태를 이해해야 할 때
- 에이전트가 서로 간섭할 때

## 패턴

### 1. 독립 영역 식별

무엇이 고장 났는지에 따라 실패를 묶는다.

- 파일 A 테스트: 도구 승인 흐름
- 파일 B 테스트: 배치 완료 동작
- 파일 C 테스트: 중단 기능

각 영역이 독립적이면 도구 승인을 고쳐도 중단 테스트에는 영향을 주지 않는다.

### 2. 집중된 에이전트 작업 만들기

각 에이전트에는 다음을 제공한다.

- **구체적 범위:** 테스트 파일 하나 또는 하위 시스템 하나
- **명확한 목표:** 해당 테스트를 통과시킬 것
- **제약:** 다른 코드는 변경하지 말 것
- **기대 출력:** 찾은 내용과 수정 사항의 요약

### 3. 병렬 분배

세 하위 에이전트 분배를 같은 응답에서 모두 실행하면 병렬로 동작한다.

```text
하위 에이전트(범용): "agent-tool-abort.test.ts 실패를 수정"
하위 에이전트(범용): "batch-completion-behavior.test.ts 실패를 수정"
하위 에이전트(범용): "tool-approval-race-conditions.test.ts 실패를 수정"
# 세 작업은 모두 동시에 실행된다.
```

한 응답 안의 여러 분배 호출은 병렬 실행이다. 응답을 나누어 하나씩 분배하면 순차 실행이다.

### 4. 검토 및 통합

에이전트가 돌아오면 다음을 수행한다.

- 각 요약을 읽는다.
- 수정 사항끼리 충돌하지 않는지 확인한다.
- 전체 테스트 모음을 실행한다.
- 모든 변경을 통합한다.

## 에이전트 프롬프트 구조

좋은 에이전트 프롬프트는 다음 조건을 갖는다.

1. **집중됨:** 하나의 명확한 문제 영역
2. **자급자족:** 문제를 이해하는 데 필요한 모든 컨텍스트
3. **출력이 구체적:** 에이전트가 무엇을 반환해야 하는가

```markdown
src/agents/agent-tool-abort.test.ts의 실패한 테스트 3개를 수정하세요.

1. "부분 출력 캡처와 함께 도구를 중단해야 함" — 메시지에 'interrupted at'가 있어야 합니다.
2. "완료된 도구와 중단된 도구가 섞인 경우를 처리해야 함" — 빠른 도구가 완료되는 대신 중단됩니다.
3. "pendingToolCount를 올바르게 추적해야 함" — 결과 3개를 기대하지만 0개를 받습니다.

이것들은 타이밍/경쟁 조건 문제입니다. 수행할 작업:

1. 테스트 파일을 읽고 각 테스트가 무엇을 검증하는지 이해합니다.
2. 근본 원인이 타이밍 문제인지 실제 버그인지 식별합니다.
3. 다음 방식으로 수정합니다.
   - 임의의 시간 초과를 이벤트 기반 대기로 교체합니다.
   - 발견되면 중단 구현의 버그를 수정합니다.
   - 동작이 바뀐 것을 테스트한다면 기대값을 조정합니다.

단순히 시간 초과를 늘리지 마세요. 실제 문제를 찾으세요.

반환: 찾은 내용과 수정한 내용의 요약.
```

## 흔한 실수

- ❌ 너무 넓음: “모든 테스트를 고쳐라” — 에이전트가 길을 잃는다.
- ✅ 구체적: “agent-tool-abort.test.ts를 고쳐라” — 범위가 집중된다.
- ❌ 컨텍스트 없음: “경쟁 조건을 고쳐라” — 에이전트가 위치를 모른다.
- ✅ 컨텍스트 제공: 오류 메시지와 테스트 이름을 붙여 넣는다.
- ❌ 제약 없음: 에이전트가 모든 것을 리팩터링할 수 있다.
- ✅ 제약 제공: “운영 코드는 변경하지 말 것” 또는 “테스트만 수정할 것”이라고 명시한다.
- ❌ 모호한 출력: “고쳐라” — 무엇이 바뀌었는지 알 수 없다.
- ✅ 구체적 출력: “근본 원인과 변경 사항의 요약을 반환하라.”

## 사용하지 말아야 할 때

**관련된 실패:** 하나를 고치면 다른 것도 고쳐질 수 있으므로 먼저 함께 조사한다.  
**전체 컨텍스트 필요:** 전체 시스템을 보아야 이해할 수 있다.  
**탐색적 디버깅:** 무엇이 고장 났는지 아직 모른다.  
**공유 상태:** 같은 파일 수정, 같은 리소스 사용 등으로 에이전트가 간섭한다.

## 주요 이점

1. **병렬화:** 여러 조사가 동시에 진행된다.
2. **집중:** 각 에이전트의 범위가 좁아 추적할 컨텍스트가 적다.
3. **독립성:** 에이전트가 서로 간섭하지 않는다.
4. **속도:** 문제 3개를 문제 1개에 가까운 시간에 해결한다.

## 검증

에이전트가 돌아온 뒤 다음을 수행한다.

1. **각 요약 검토:** 무엇이 바뀌었는지 이해한다.
2. **충돌 확인:** 에이전트가 같은 코드를 수정했는가?
3. **전체 모음 실행:** 모든 수정이 함께 동작하는지 확인한다.
4. **표본 점검:** 에이전트도 체계적인 오류를 낼 수 있다.
````

#### 플러그인: Superpowers · 스킬명: `executing-plans` — 계획 실행

````markdown
**설명:** 별도 세션에서 검토 지점을 두고 서면 구현 계획을 실행할 때 사용한다.

# 계획 실행

## 개요

계획을 불러오고, 비판적으로 검토하고, 모든 작업을 실행한 뒤, 완료 시 보고한다.

**시작 시 알림:** “이 계획을 구현하기 위해 executing-plans 스킬을 사용하겠습니다.”

**참고:** 하위 에이전트에 접근할 수 있으면 Superpowers가 훨씬 더 잘 동작한다고 협업자에게 알린다. 하위 에이전트를 지원하는 플랫폼에서는 품질이 크게 높아진다. 하위 에이전트를 쓸 수 있으면 이 스킬 대신 `superpowers:subagent-driven-development`를 사용한다.

## 절차

### 1단계: 계획 불러오기 및 검토

1. 계획 파일을 읽는다.
2. 계획을 비판적으로 검토하고, 질문 또는 우려 사항을 식별한다.
3. 우려가 있으면 시작하기 전에 협업자에게 제기한다.
4. 우려가 없으면 계획 항목의 할 일을 만들고 진행한다.

### 2단계: 작업 실행

각 작업에서 다음을 수행한다.

1. 진행 중으로 표시한다.
2. 각 단계를 정확히 따른다(계획에는 작은 단위 단계가 있다).
3. 지정된 검증을 실행한다.
4. 완료로 표시한다.

### 3단계: 개발 완료

모든 작업을 완료하고 검증한 뒤:

- “이 작업을 마무리하기 위해 finishing-a-development-branch 스킬을 사용하겠습니다.”라고 알린다.
- **필수 하위 스킬:** `superpowers:finishing-a-development-branch`를 사용한다.
- 해당 스킬에 따라 테스트를 검증하고, 선택지를 제시하고, 선택을 실행한다.

## 멈추고 도움을 요청할 때

다음 상황에서는 **즉시 실행을 멈춘다.**

- 막힘을 만났을 때(누락된 의존성, 테스트 실패, 불명확한 지시)
- 계획에 시작을 막는 치명적인 공백이 있을 때
- 지시를 이해하지 못할 때
- 검증이 반복해서 실패할 때

추측하는 대신 설명을 요청한다.

## 이전 단계로 돌아갈 때

다음 경우 검토(1단계)로 돌아간다.

- 협업자가 피드백을 반영해 계획을 업데이트했을 때
- 기본 접근 방식을 다시 생각해야 할 때

막힘을 억지로 통과하지 말고, 멈추고 질문한다.

## 기억할 점

- 먼저 계획을 비판적으로 검토한다.
- 계획 단계를 정확히 따른다.
- 검증을 건너뛰지 않는다.
- 계획이 지시할 때 스킬을 참조한다.
- 막히면 멈추고 추측하지 않는다.
- 명시적 동의 없이 main/master 브랜치에서 구현을 시작하지 않는다.
````

#### 플러그인: Superpowers · 스킬명: `requesting-code-review` — 코드 리뷰 요청

````markdown
**설명:** 작업 완료, 주요 기능 구현, 병합 전 요구사항 충족 여부를 검증할 때 사용한다.

# 코드 리뷰 요청

문제가 커지기 전에 잡기 위해 코드 리뷰어 하위 에이전트를 분배한다. 리뷰어에게는 평가에 필요한 컨텍스트만 정밀하게 제공하며, 현재 세션의 이력은 제공하지 않는다. 그러면 리뷰어가 사고 과정이 아닌 작업 결과물에 집중하고, 자신의 컨텍스트도 보존할 수 있다.

**핵심 원칙:** 일찍 리뷰하고, 자주 리뷰한다.

## 리뷰를 요청할 때

**필수:**

- 하위 에이전트 기반 개발에서 각 작업 뒤
- 주요 기능을 완료한 뒤
- main 브랜치에 병합하기 전

**선택 사항이지만 가치 있음:**

- 막혔을 때(새로운 관점)
- 리팩터링 전(기준선 확인)
- 복잡한 버그 수정 뒤

## 요청 방법

**1. Git SHA 가져오기:**

```bash
BASE_SHA=$(git rev-parse HEAD~1)  # 또는 origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. 코드 리뷰어 하위 에이전트 분배:**

`general-purpose` 하위 에이전트를 분배하고, [code-reviewer.md](code-reviewer.md)의 템플릿을 채운다.

**자리표시자:**

- `{DESCRIPTION}` — 만든 것의 짧은 요약
- `{PLAN_OR_REQUIREMENTS}` — 해야 하는 일
- `{BASE_SHA}` — 시작 커밋
- `{HEAD_SHA}` — 종료 커밋

**3. 피드백 처리:**

- 심각한 문제는 즉시 수정한다.
- 중요한 문제는 진행 전에 수정한다.
- 경미한 문제는 나중을 위해 기록한다.
- 리뷰어가 틀리면 근거를 들어 이의를 제기한다.

## 워크플로우와의 통합

**하위 에이전트 기반 개발:** 각 작업 뒤 리뷰하고, 문제가 누적되기 전에 잡으며, 다음 작업으로 가기 전에 수정한다.  
**계획 실행:** 각 작업 뒤 또는 자연스러운 점검 지점에서 리뷰하고, 피드백을 적용한 뒤 계속한다.  
**임시 개발:** 병합 전 또는 막혔을 때 리뷰한다.

## 위험 신호

다음을 해서는 안 된다.

- “간단하다”는 이유로 리뷰를 건너뛴다.
- 심각한 문제를 무시한다.
- 중요한 문제를 수정하지 않고 진행한다.
- 타당한 기술 피드백에 감정적으로 반박한다.

리뷰어가 틀렸다면 기술적 근거를 제시하고, 동작을 증명하는 코드·테스트를 보이며, 설명을 요청한다.

템플릿은 [code-reviewer.md](code-reviewer.md)를 참조한다.
````

#### 플러그인: Superpowers · 스킬명: `using-superpowers` — Superpowers 사용

````markdown
**설명:** 모든 대화의 시작에서 사용한다. 질문을 포함한 어떤 응답이나 작업보다 먼저 관련 스킬을 호출하도록 정한다.

`<SUBAGENT-STOP>`  
특정 작업을 수행하도록 하위 에이전트로 분배되었다면 이 스킬을 무시한다.  
`</SUBAGENT-STOP>`

`<EXTREMELY-IMPORTANT>`  
수행하려는 작업에 스킬이 적용될 가능성이 1%라도 있다고 생각되면 반드시 그 스킬을 호출해야 한다.

작업에 스킬이 적용된다면 선택권은 없다. 반드시 사용해야 한다.

협상할 수 없으며, 이를 피해 갈 이유를 합리화해서는 안 된다.  
`</EXTREMELY-IMPORTANT>`

## 규칙

질문, 코드베이스 탐색, 파일 확인을 포함한 어떤 응답이나 행동보다 **먼저 관련 있거나 요청된 스킬을 호출한다.** 나중에 그 스킬이 상황에 맞지 않는다고 밝혀지면 계속 사용할 필요는 없다.

계획 모드로 들어가기 전에는, 아직 브레인스토밍하지 않았다면 먼저 `brainstorming` 스킬을 호출한다.

그다음 “`[목적]을 위해 [스킬]을 사용합니다.`”라고 알리고 스킬을 정확하게 따른다. 체크리스트가 있으면 각 항목의 할 일을 만든다.

## 스킬 우선순위

여러 스킬이 적용되면 프로세스 스킬을 먼저 사용한다. 프로세스 스킬이 접근 방식을 정하고, 그다음 구현 스킬(예: frontend-design)을 사용한다. `brainstorming`과 `systematic-debugging`은 Superpowers에서 가장 흔한 프로세스 스킬이지만, 이 원칙은 모든 스킬에 적용된다.

- “X를 만들자” → 먼저 `superpowers:brainstorming`, 그다음 구현 스킬
- “이 버그를 고쳐라” → 먼저 `superpowers:systematic-debugging`, 그다음 도메인 스킬

## 위험 신호

다음 생각이 들면 멈춘다. 이는 합리화의 신호다.

| 생각 | 실제 상황 |
| --- | --- |
| “그냥 간단한 질문이다.” | 질문도 작업이다. 스킬을 확인한다. |
| “먼저 컨텍스트가 더 필요하다.” | 설명을 묻기 전에 스킬을 확인한다. |
| “코드베이스를 먼저 탐색하겠다.” | 스킬은 탐색 방법을 알려 준다. 먼저 확인한다. |
| “Git이나 파일을 빨리 확인할 수 있다.” | 파일에는 대화 컨텍스트가 없다. 먼저 스킬을 확인한다. |
| “정보부터 모으겠다.” | 스킬은 정보를 모으는 방법을 알려 준다. 먼저 확인한다. |
| “형식적인 스킬은 필요 없다.” | 스킬이 있다면 사용한다. |
| “이 스킬이 무엇인지 기억한다.” | 스킬은 바뀐다. 현재 버전을 읽는다. |
| “이건 작업으로 치지 않는다.” | 행동은 작업이다. 먼저 확인한다. |
| “이 정도에는 스킬이 과하다.” | 단순한 일도 복잡해질 수 있다. 스킬을 사용한다. |
| “이 한 가지만 먼저 하겠다.” | 어떤 행동 전에도 먼저 확인한다. |
| “생산적으로 느껴진다.” | 규율 없는 행동은 시간을 낭비한다. 스킬이 이를 막는다. |
| “무슨 뜻인지 안다.” | 의미를 아는 것과 스킬을 사용하는 것은 다르다. 호출한다. |

## 플랫폼 적응

현재 하네스가 아래에 있으면 특별 지침을 담은 참조 파일을 읽는다.

- Codex: `references/codex-tools.md`
- Pi: `references/pi-tools.md`
- Antigravity: `references/antigravity-tools.md`

## 사용자 지시

사용자 지시(`CLAUDE.md`, `AGENTS.md`, `GEMINI.md` 등 직접 요청)는 스킬보다 우선하며, 스킬은 기본 지침보다 우선한다. 사람이 명시적으로 지시한 경우에만 스킬 워크플로 또는 지침을 건너뛴다.
````

#### 플러그인: Superpowers · 스킬명: `verification-before-completion` — 완료 전 검증

````markdown
**설명:** 완료·수정·통과라고 주장하기 전, 커밋 또는 PR 생성 전에 사용한다. 검증 명령을 실행하고 출력을 확인해야 하며, 주장이 아닌 증거를 항상 우선한다.

# 완료 전 검증

## 개요

검증 없이 작업이 완료되었다고 주장하는 것은 효율이 아니라 부정직이다.

**핵심 원칙:** 항상 주장보다 증거를 먼저 둔다.

이 규칙의 문구만 지키고 정신을 어기는 것도 규칙을 어기는 것이다.

## 철칙

```text
새로운 검증 증거 없이는 완료를 주장하지 않는다.
```

이 메시지에서 검증 명령을 실행하지 않았다면 통과했다고 주장할 수 없다.

## 게이트 함수

```text
어떤 상태를 주장하거나 만족을 표현하기 전:

1. 식별: 이 주장을 증명하는 명령은 무엇인가?
2. 실행: 완전한 명령을 새로 실행한다.
3. 읽기: 전체 출력을 읽고, 종료 코드와 실패 수를 확인한다.
4. 검증: 출력이 주장을 확인하는가?
   - 아니오: 증거와 함께 실제 상태를 말한다.
   - 예: 증거와 함께 주장을 말한다.
5. 그때에만 주장을 한다.

어느 한 단계라도 건너뛰면 검증하지 않은 것이며, 거짓말이다.
```

## 흔한 실패

| 주장 | 필요한 것 | 충분하지 않은 것 |
| --- | --- | --- |
| 테스트 통과 | 테스트 명령 출력: 실패 0건 | 이전 실행, “통과할 것임” |
| 린터 정상 | 린터 출력: 오류 0건 | 부분 검사, 추정 |
| 빌드 성공 | 빌드 명령: 종료 코드 0 | 린터 통과, 로그가 좋아 보임 |
| 버그 수정 | 원래 증상을 테스트하여 통과 | 코드를 바꿈, 수정됐다고 가정 |
| 회귀 테스트 동작 | red-green 주기를 검증 | 테스트가 한 번 통과 |
| 에이전트 완료 | VCS diff가 변경을 보임 | 에이전트의 “성공” 보고 |
| 요구사항 충족 | 항목별 체크리스트 | 테스트 통과 |

## 위험 신호 — 멈춤

- “~일 것이다”, “아마도”, “~처럼 보인다”를 사용한다.
- 검증 전에 만족을 표현한다(“좋아!”, “완벽해!”, “끝났다!” 등).
- 검증 없이 커밋·푸시·PR을 하려 한다.
- 에이전트 성공 보고를 신뢰한다.
- 부분 검증에 의존한다.
- “이번 한 번만”이라고 생각한다.
- 피곤해서 작업을 끝내고 싶다.
- 검증 없이 성공을 암시하는 어떤 표현이든 사용한다.

## 합리화 방지

| 변명 | 실제 |
| --- | --- |
| “이제 동작할 것이다.” | 검증을 실행한다. |
| “확신한다.” | 확신은 증거가 아니다. |
| “이번 한 번만.” | 예외는 없다. |
| “린터가 통과했다.” | 린터는 컴파일러가 아니다. |
| “에이전트가 성공했다고 했다.” | 독립적으로 검증한다. |
| “피곤하다.” | 피곤함은 변명이 아니다. |
| “부분 검사면 충분하다.” | 부분 검사는 아무것도 증명하지 않는다. |
| “다른 말로 표현했으니 규칙이 적용되지 않는다.” | 문구보다 정신이 우선한다. |

## 주요 패턴

**테스트:**

```text
✅ [테스트 명령 실행] [34/34 통과 확인] “모든 테스트가 통과합니다.”
❌ “이제 통과할 것입니다.” / “정확해 보입니다.”
```

**회귀 테스트(TDD red-green):**

```text
✅ 작성 → 실행(통과) → 수정 되돌림 → 실행(반드시 실패) → 복원 → 실행(통과)
❌ red-green 검증 없이 “회귀 테스트를 작성했습니다.”라고 말함
```

**빌드:**

```text
✅ [빌드 실행] [종료 코드 0 확인] “빌드가 통과합니다.”
❌ “린터가 통과했습니다.”(린터는 컴파일을 확인하지 않음)
```

**요구사항:**

```text
✅ 계획을 다시 읽기 → 체크리스트 만들기 → 각각 검증 → 공백 또는 완료 보고
❌ “테스트가 통과했으니 단계가 완료됐다.”
```

**에이전트 위임:**

```text
✅ 에이전트 성공 보고 → VCS diff 확인 → 변경 검증 → 실제 상태 보고
❌ 에이전트 보고를 신뢰함
```

## 중요한 이유

실패 기억 24건에서 확인된 결과:

- 협업자가 “믿을 수 없다”고 말해 신뢰가 깨졌다.
- 정의되지 않은 함수가 배포되어 충돌할 수 있었다.
- 요구사항 누락 상태로 배포되어 기능이 불완전했다.
- 잘못된 완료 보고 뒤에 재지시와 재작업으로 시간이 낭비됐다.
- “정직은 핵심 가치다. 거짓말하면 대체될 것이다.”라는 원칙을 위반한다.

## 적용 시점

**항상 다음 전에 적용한다.**

- 성공·완료 주장의 모든 변형
- 만족을 나타내는 모든 표현
- 작업 상태에 대한 모든 긍정적 표현
- 커밋, PR 생성, 작업 완료
- 다음 작업으로 이동
- 에이전트에게 위임

이 규칙은 정확한 문구, 바꿔 말한 표현과 동의어, 성공·정확성을 암시하는 표현 모두에 적용된다.

## 결론

**검증에 지름길은 없다.**

명령을 실행하고, 출력을 읽고, 그다음 주장한다.

이는 협상할 수 없다.
````

## Product Design

아래 내용은 OpenAI `role-specific-plugins` 공개 저장소의 Product Design 0.1.50에 포함된 각 `SKILL.md` 원문의 한글 번역이다. 스킬명과 frontmatter의 `name` 값은 원문 표기를 유지한다.

#### 플러그인: Product Design · 스킬명: `index` — 스킬 라우터

````markdown
---
name: index
description: "Product Design 플러그인의 특정 스킬을 찾을 때, Product Design이 직접 언급되었을 때, 또는 관련 가능성이 있는 작업이 언급될 때 사용한다. 여기에는 UX 리서치, 제품·화면·흐름 감사, 시각 아이데이션, 아이디어·URL·이미지·Figma·코드에서 앱 또는 인터페이스를 디자인·리디자인·복제·프로토타이핑·구현하는 작업, 디자인 QA, 프로토타입 공유 또는 배포가 포함된다."
---

# 스킬 목적

Product Design 요청을 적절한 Product Design 스킬로 라우팅한다.

`@Product Design` 언급, Product Design 직접 호출, 또는 "이 앱을 디자인해줘", "프로토타입을 만들어줘", "이 흐름을 감사해줘", "이 제품을 조사해줘", "이 프로토타입을 공유해줘" 같은 넓은 요청은 이 플러그인을 사용하려는 의도로 취급한다.

# 플러그인 목적

Product Design 플러그인은 디자이너와 기타 비코더가 제품 아이디어와 작동하는 소프트웨어 사이의 간극을 줄이도록 돕는다.

Product Design 플러그인은 다음을 수행할 수 있는 스킬 세트를 제공한다.

- 제품과 관련된 아이디어와 문제 지점을 조사한다.
- 제품 흐름 감사를 수행한다.
- ImageGen으로 제품에 대한 뚜렷하게 새로운 아이디어를 생성한다.
- 기존 제품 앱을 가벼운 프로토타입으로 복제한다.
- 팀과 공유할 가벼운 또는 상호작용형 프로토타입을 만든다.

## 커뮤니케이션 스타일

따뜻하고 재미있으며 협업적인 방식으로 사용자에게 말하되, 긴 텍스트 덩어리와 많은 bullet보다 짧고 핵심적인 설명을 우선한다.

Product Design 플러그인 진행 업데이트와 인계는 [communication-protocol](../../references/communication-protocol.md)을 참조한다.

## 중요 오버라이드

- [$critical-overrides](../../references/critical-overrides.md)를 따른다.

## 라우터 전용

이 index는 Product Design 요청을 라우팅한다. focused workflow 자체를 충족하지 않는다.

요청이 `$user-context`, `$get-context`, `$research`, `$ideate`, `$prototype`, `$image-to-code`, `$url-to-code`, `$audit`, `$design-qa`, `$share`와 일치하면 해당 focused skill을 불러와 따른다.

시각 아이데이션 요청은 먼저 `$get-context`를 불러온 뒤 `$ideate`를 불러온다.

## 시각 대상 없이는 빌드하지 않음

URL, 스크린샷, Figma 프레임, 목업, 소스 이미지, 기존 코드 대상이 없는 새 앱·프로토타입·리디자인·UI 빌드 요청에서는 다음을 수행한다.

- `$get-context`를 실행한다.
- 브리프가 승인되면 `$ideate`로 라우팅한다.
- 정확히 세 가지 시각 옵션을 보여주고 사용자가 하나를 선택할 때까지 기다린다.
- 시각 옵션이 선택되기 전에는 스캐폴딩, 파일 편집, 서버 시작을 하지 않는다.

`Full working version`, `no refs`, `go for it`, `make an assumption`, 확인된 브리프는 이 규칙을 면제하지 않는다.

## 사용자 컨텍스트

사용자가 다음을 요청하면 [$user-context](../user-context/SKILL.md)를 사용한다.

- Product Design 설정
- Product Design 시작
- Product Design 온보딩
- 제품 또는 디자인 소스 저장
- Product Design이 기억하는 내용 확인
- 저장된 제품 또는 디자인 컨텍스트 업데이트
- Product Design 선호 사항 기억
- 플러그인 설정

컨텍스트 수집 요청은 사용자의 요청에 맞게 조정한다. 최초 설정은 기존 컨텍스트 업데이트와 다르다.

설정 전용 요청에서는 워크스페이스를 검사하거나, 의존성을 설치하거나, 프로토타입을 스캐폴딩하거나, 이미지를 생성하거나, 감사를 실행하거나, 구현을 시작하지 않는다.

"무엇을 할 수 있나?", "어떻게 시작하나?" 같은 넓은 Product Design 질문에 답할 때는 저장 컨텍스트를 설정할지 묻는 것으로 끝낸다.

다음 문구로 마무리한다.

```text
Want to onboard Product Design with your context? Send product URLs, Figma files, screenshots, codebase paths, Storybook links, tokens, brand assets, or preferred share targets, and I'll save them for future work.
```

Product Design 워크플로로 라우팅하기 전에 [$user-context](../user-context/SKILL.md)를 불러오고, 로컬 셸 접근이 가능하면 preflight 스크립트를 실행한다.

## 브라우저 주석 업데이트

주석은 현재 프로토타입에 한정된 편집으로 취급한다.

코드를 변경하기 전에 주석, 대상, 주변 화면을 읽는다. 기본적으로 기존 프로토타입을 보존한다. 주석이 변경을 요청하지 않는 한 레이아웃, 스타일, 콘텐츠, 라우트, 에셋, 상호작용, 작동 동작을 유지한다.

주석이 해당 영역에 닿았다는 이유만으로 주변 UI를 리디자인하거나 프로토타입을 다시 만들지 않는다. 주석이 모호하고 선택이 프로토타입을 실질적으로 바꾼다면 먼저 질문한다.

## 스킬

Product Design 플러그인 작업의 루트 라우팅 지침으로 사용한다. 여러 focused skill이 적용되면 가장 유용한 디자인 워크플로가 되는 순서로 배열한다. 이 index는 라우터로 유지하며, focused workflow 로직을 여기서 수행하지 않는다.

### $user-context

Product Design 설정 컨텍스트를 preflight, 저장, 또는 답변에 사용한다.

Product Design 워크플로 전에 저장된 제품·디자인 소스를 불러오기 위해 라우팅한다. 직접 설정, 시작, 온보딩, 저장, 기억, 회상, 검사, 맞춤화 요청에도 사용한다. 이 스킬은 Product Design 플러그인 범위의 컨텍스트와 선호 정책을 담당한다.

### $get-context

디자인, 빌드, 프로토타입, 리디자인, 확장, UI 탐색 작업에서는 먼저 여기로 라우팅한다.

세부 정보가 빠졌다면 누락된 제품·시각·상호작용 컨텍스트만 질문한다. 세부 정보가 이미 있으면 진행 전에 브리프를 되짚어 말한다. Product Design 아이데이션 또는 구현 전에 디자인 브리프를 사용자에게 확인한다.

### $research

지정된 디지털 제품의 현재 사용자 문제를 빠르고 출처 기반으로 조사한다.

사용자 고통, UX 마찰, 온보딩 문제, 문서·도움말 문제, 개발자 경험 마찰, 지원 고통, 제품 워크플로 문제, 현재 사용자 불만 조사를 요청하면 여기로 라우팅한다.

### $audit

제품 흐름, 여정, 화면, 다단계 제품 경험을 스크린샷으로 캡처하고 검토한다.

사용자 대상 감사, 비평, 리뷰, 검사, 평가, UI 평가 요청은 여기로 라우팅한다. 캡처한 근거에 연결된 UX, 디자인, 접근성 findings를 보고한다. 사용자 대상 감사에는 `design-qa`를 사용하지 않는다.

### $ideate

컴포넌트, 화면, 기능, 워크플로, 제품 아이디어에 대해 이미지 기반 시각 대안, 리믹스, 컨셉 방향을 생성한다.

`get-context`가 디자인 브리프를 확인했고, 사용자가 시각 탐색, 디자인 변형, 기존 디자인의 대안, 시각 대상 선택 전 아이디어 탐색을 필요로 하면 여기로 라우팅한다. 사용자가 prose를 요청하지 않는 한 prose-only 아이데이션보다 이 방식을 선호한다.

### $prototype

코딩된 프로토타입, 리디자인, 복제, UI 빌드 요청을 적절한 Product Design 워크플로로 라우팅한다.

`get-context`가 브리프를 확인했고, 사용자가 URL, 이미지, 목업, Figma 소스, 기존 코드베이스, 제품 아이디어로부터 빌드해 달라고 요청하면 여기로 라우팅한다.

### $url-to-code

Browser 또는 Chrome 소스 근거를 사용해 라이브 URL을 실행 가능한 프론트엔드 전용 로컬 앱으로 복제한다.

`get-context`가 브리프를 확인했고, 사용자가 충실한 로컬 프로토타입 또는 복제를 위해 프로덕션 URL을 제공하면 여기로 라우팅한다. 프로덕션 코드는 수정하면 안 된다. 소스 선택이 아직 불명확하면 먼저 `prototype`을 사용한다.

### $image-to-code

선택된 시각 대상을 충실하고 반응형이며 상호작용 가능한 프론트엔드로 구현한다.

`get-context`가 브리프를 확인했고, 사용자가 ImageGen 목업, 스크린샷, Figma 프레임, 목업, 참조 이미지 또는 기타 시각 소스를 선택했을 때 여기로 라우팅한다. 선택된 시각 대상이 없으면 여기서 시작하지 않는다. 먼저 `get-context`와 `ideate`를 사용한다.

### $share

사용 가능한 기본 공유 대상이 있으면 그 대상을 사용해 실행 가능한 프로토타입을 배포하고 공유 가능한 URL을 반환한다.

사용자가 `@Sites`, `@Vercel`, 또는 다른 배포 도구로 공유, 배포, 게시, 호스팅, 링크 생성, 프로토타입 공유 가능화를 요청하면 여기로 라우팅한다.

### $design-qa

전달 전에 코딩된 Product Design 프로토타입을 소스 시각 대상과 비교한다.

프로토타입, URL-to-code 빌드, image-to-code 빌드가 소스 시각 자료와 렌더링된 구현을 모두 갖춘 뒤 내부 helper로만 라우팅한다. 넓은 UX 비평, 감사, 제품 흐름 리뷰는 여기로 라우팅하지 말고 `audit`을 사용한다.
````

#### 플러그인: Product Design · 스킬명: `user-context` — 사용자 컨텍스트

````markdown
---
name: user-context
description: Product Design의 저장된 사용자 컨텍스트를 불러오거나 관리한다. 사용자가 Product Design 설정, 시작, 온보딩, 제품 또는 디자인 소스 저장, Product Design이 기억하는 내용 확인, 저장된 컨텍스트 업데이트, Product Design 선호 사항 기억을 요청할 때 사용한다. 예시에는 제품 URL, Figma 파일, 스크린샷, 참조 이미지, 코드베이스 경로, Storybook, 토큰, 디자인 시스템, 브랜드 에셋, 일반 제품·디자인 노트가 포함된다.
---

# 사용자 컨텍스트

User Context는 디자이너가 자주 사용하는 제품과 디자인 참조를 저장하여, 이후 Product Design 작업이 올바른 소스에서 시작되도록 한다.

이 스킬은 사용자가 다음을 요청할 때 사용한다.

- Product Design 설정
- Product Design 시작
- Product Design 온보딩
- 제품 또는 디자인 소스 저장
- Product Design이 기억하는 내용 확인
- 저장된 제품 또는 디자인 컨텍스트 업데이트
- Product Design 선호 사항 기억
- 플러그인 설정

## 중요 오버라이드

- 진행하기 전에 Plugin router [$index](../index/SKILL.md)를 참조한다.
- [$critical-overrides](../../references/critical-overrides.md)를 따른다.

## 저장된 사용자 컨텍스트

`user-context.md`가 있으면 기본적으로 사용한다. 저장된 제품 URL, Figma 파일, 스크린샷, 참조 이미지, 코드베이스 경로, Storybook, 토큰, 디자인 시스템, 브랜드 에셋, 컴포넌트 참조, 브라우저 선호, 공유 대상을 사용해 Product Design 작업의 근거로 삼는다.

아이데이션, 프로토타입, 감사, 복제, 비평은 사용자가 다르게 요청하지 않는 한 저장된 제품 컨텍스트와 맞아야 한다.

워크플로에 시각적 grounding이 필요하면 관련 저장 스크린샷, 참조 이미지, 토큰, 디자인 언어, 컴포넌트 참조를 ImageGen, 아이데이션, 프로토타입, 감사, 비평 작업에 첨부하거나 포함한다.

## 상태 파일

저장된 컨텍스트는 여기에 있다.

```text
$CODEX_HOME/state/plugins/product-design/user-context.md
```

저장된 스크린샷과 참조 이미지는 그 옆에 있다.

```text
$CODEX_HOME/state/plugins/product-design/assets/
```

파일이 없으면 사용자가 Product Design 설정, 컨텍스트 저장을 요청했거나 현재 작업이 제품·디자인 컨텍스트 부족으로 막힌 경우가 아니면 정상적으로 계속한다.

## Preflight

Product Design 워크플로가 저장된 컨텍스트를 필요로 하면 다음을 실행한다.

```bash
python3 scripts/user_context_preflight.py
```

반환된 저장 항목을 작업의 시작 컨텍스트로 사용한다. 스크립트가 저장된 컨텍스트가 없다고 보고하면, 설정 컨텍스트가 필요한 경우가 아니면 현재 사용자 프롬프트에서 계속한다.

preflight 중 저장된 모든 참조를 탐색하거나 열거나 검사하지 않는다. 현재 작업에 필요한 저장 참조만 검사한다.

## 설정

사용자가 Product Design 설정, Product Design이 기억할 수 있는 내용, Product Design이 제품에 대해 알고 있는 내용에 대해 묻거나 저장할 제품·디자인 참조를 제공하면 [references/onboarding.md](references/onboarding.md)를 사용한다.

설정 전용 요청에서는 Product Design이 무엇을 기억할 수 있는지 설명하고 유용한 소스를 요청한다. 컨텍스트 수집 요청은 사용자의 요청에 맞게 조정한다. 최초 설정은 기존 컨텍스트 업데이트와 다르다.

설정 중에는 워크스페이스 검사, 의존성 설치, 프로토타입 스캐폴딩, 이미지 생성, 감사 실행, 구현 시작을 하지 않는다.

사용자가 저장할 참조를 제공하면 다음을 실행한다.

```bash
python3 scripts/init_user_context.py
```

그런 다음 생성된 `user-context.md`에 참조를 추가한다.

## 저장

유용하고 지속 가능한 Product Design 컨텍스트를 저장한다.

- 제품 URL
- Figma 파일
- 스크린샷과 참조 이미지
- 코드베이스 경로
- Storybook과 컴포넌트 문서
- 디자인 토큰과 테마 소스
- 브랜드, 로고, 아이콘, 일러스트레이션, 이미지, 에셋 소스
- 선호 브라우저, 캡처 도구, 공유 대상
- 향후 Product Design 작업을 더 정확하게 만드는 팀 규칙

사용자가 저장할 스크린샷 또는 참조 이미지를 제공하면 `user-context.md` 옆의 `assets/`로 복사하고 저장 항목에서 링크한다.

각 저장 이미지에는 이미지가 무엇을 보여주는지 설명하는 명확한 파일명을 붙인다. 향후 Product Design 실행이 파일을 열지 않고도 이해할 수 있는 이름을 사용한다.

좋은 이미지 이름:

```text
assets/chatgpt-settings-modal-dark-mode.png
assets/payment-sheet-mobile-error-state.png
assets/product-dashboard-sidebar-navigation.png
assets/storybook-primary-button-states.png
assets/brand-logo-lockup-purple-gradient.png
assets/onboarding-flow-welcome-step.png
assets/checkout-confirmation-screen.png
assets/account-menu-open-state.png
```

비밀, 자격 증명, API 키, private token, 복사된 고객 데이터, 지속 저장하면 안 되는 것은 저장하지 않는다.

다음 구조를 사용한다.

```md
# {Category}

- Description: {이 카테고리가 무엇이며 향후 Product Design 실행이 언제 사용해야 하는지}

## Saved Links And Context

{저장된 참조 또는 사실}

- Date Added: YYYY-MM-DD.
- File: assets/{clear-descriptive-name}.png
- Useful Context: {이 참조가 무엇을 나타내는지}
- Future Use: {향후 Product Design 작업이 이 참조를 어떻게 사용해야 하는지}
```

저장 항목에 로컬 이미지 파일이 있을 때만 `File:`을 포함한다.

카테고리에 저장된 참조가 아직 없으면 정확히 다음을 사용한다.

```md
status: not provided
```

저장 컨텍스트를 잘 선별한다. 가능한 모든 URL이나 파일을 덤프하기보다 가치가 높은 참조 몇 개를 선호한다.

## 읽기

- `status: not provided`를 사실로 취급하지 않는다.
- 로컬 셸 접근이 가능하면 `scripts/user_context_preflight.py`를 읽어본다.
- 저장된 컨텍스트를 기본 grounding으로 사용한 뒤, 현재 작업에 필요한 것만 검사한다.
````

#### 플러그인: Product Design · 스킬명: `get-context` — 컨텍스트 확인

````markdown
---
name: get-context
description: "Product Design 빌드와 디자인 워크플로의 필수 디자인 브리프 게이트. 아이데이션, 프로토타이핑, image-to-code 빌드, 리디자인, 제품 UI 작업 전에 사용하여 누락된 제품·시각·상호작용 컨텍스트를 명확히 하거나, 제공된 브리프를 되짚어 말한 뒤 진행한다."
---

# 컨텍스트 확인

다음 디자인 작업에 필요한 컨텍스트만 수집한다. 이 스킬은 디자인 브리프를 해결하거나 확인한다. UI를 구현하거나 지속적인 디자인 산출물을 만들지 않는다.

사용자가 제품 UI 방향을 디자인, 빌드, 프로토타입, 복제, 리디자인, 확장, 생성해 달라고 요청할 때 Product Design 요청 시작 시 이 스킬을 실행한다.

다음 중 하나라도 불명확하면 질문 모드를 사용한다.

- 어떤 제품, 사이트, 기능, 워크플로, 컴포넌트, 화면을 디자인하는지
- 어떤 시각 소스가 외형을 결정해야 하는지
- 소스가 없을 때 어떤 구체적 선호 또는 회피 사항이 시각 탐색을 형성해야 하는지
- 사용자가 기대하는 상호작용 수준

사용자가 필요한 세부 정보를 이미 제공했다면 playback 모드를 사용한다.

playback 모드에서는 이미 답한 질문을 다시 묻지 않는다. 간결한 형식으로 브리프를 되짚어 말하고 다음 워크플로를 명명한다.

경계: 컨텍스트가 아직 누락되어 있으면 UI 구현, 프로토타입 스캐폴딩, 서버 시작, 파일 생성을 하지 않는다.

## 중요 오버라이드

- 진행하기 전에 Plugin router [$index](../index/SKILL.md)를 참조한다.
- [$critical-overrides](../../references/critical-overrides.md)를 따른다.

## 사용자 컨텍스트

시작 전에 [$user-context](../user-context/SKILL.md)를 불러오고, 로컬 셸 접근이 가능하면 preflight 스크립트를 실행한다.

관련이 있으면 저장된 제품 URL, Figma 파일, 스크린샷, 참조 이미지, 코드베이스 경로, Storybook, 토큰, 디자인 시스템, 브랜드 에셋, 컴포넌트 참조, 브라우저 선호, 공유 대상을 grounding material로 사용한다.

저장된 모든 참조를 검사하지 않는다. 현재 작업에 필요한 것만 검사한다.

## 컨텍스트 확인 스크립트

다음 세 질문은 사용자가 답해야 한다. 사용자가 지금까지 제공한 내용에 맞게 질문을 조정한다. 일부 또는 전체 필드가 이미 알려져 있으면 질문을 건너뛰고 자신의 말로 디자인 브리프를 요약한다.

답해야 할 질문:

> 만들 대상이 무엇을 해야 하나?

> 어떤 기존 제품, 디자인 시스템, Figma 파일, 스크린샷, URL, 이미지 또는 기타 시각 소스와 맞아야 하나? 없으면 어떤 look을 원하는가? user-context에 기존 디자인 시스템이 있으면 언급한다.

> 상호작용 수준은 어느 정도여야 하나?

다음 중 하나:

- 전체 상호작용: 모든 컨트롤과 상태가 완전히 기능하고 구현된다.
- 정적: 속도를 우선하여 컨트롤과 상태가 최소한으로 상호작용한다.

질문 뒤에는 탐색할 내용을 요약한 간결한 디자인 브리프로 답한다. 긴 텍스트를 반드시 피한다. 명확하고 간결하게 쓴다.

따를 예시 스크립트:

```text
Before I build, the Product Design workflow needs a quick design brief.

What should the login page do? Email/password only, magic link, SSO, sign-up link, forgot password?
Do you have an existing design system, app, Figma, or screenshot to match? If not, what look are you going for?
Interactivity level: full working form states, or a faster mostly-static mock?
```

## 최종 메시지

1. `$ideate`, `$prototype`, `$url-to-code`, `$image-to-code`로 진행하기 전에 `final` 메시지로 디자인 브리프를 간결하게 되짚어 사용자에게 확인한다.
2. 현재 스레드에 정확히 그 브리프에 대한 확인이 이미 있지 않다면, 사용자가 디자인 브리프를 확인한 뒤에만 진행한다. 사용자가 피드백을 제공하면 함께 브리프를 계속 다듬는다.
3. 사용자가 디자인 브리프를 확인한 뒤, 관련 앱·프로토타입·복제·리디자인·빌드를 시작하기 전에 짧은 기대 설정 메모를 하나 보낸다.

기대 설정이 포함된 확인 메시지 예시:

```text
Lovely, brief locked.

This kind of build usually takes about 10-15 minutes, and ambitious ones can take longer. Good moment to grab coffee or tend to something else; I'll keep moving and bring the prototype back when it is ready.
```

작은 정적 변경, 빠른 감사, 단순 리서치, 설정 전용, 공유 전용 요청에는 이 메모를 보내지 않는다.

완료란 사용자가 디자인 브리프를 확인한 상태를 뜻한다.
````

#### 플러그인: Product Design · 스킬명: `research` — 리서치

````markdown
---
name: research
description: "사용자가 지정한 디지털 제품에서 사용자가 겪는 가장 높은 신호의 문제를 빠르고 출처 기반으로 UX 리서치한다. 사용자가 명명된 제품에 대해 사용자 고통, UX 마찰, 온보딩 문제, 문서·도움말 문제, 개발자 경험 마찰, 지원 고통, 제품 워크플로 문제, 현재 사용자 불만 조사를 요청할 때 사용한다."
---

# 리서치

사용자가 지정한 제품에 대해 최신 UX 리서치 스캔을 실행한다. 현재의 근거 있는 사용자 문제에 집중한다.

로그인된 제품 경험, 셀프서비스 흐름, 온보딩, 문서·도움말, 개발자 경험, 지원 마찰, 제품 워크플로를 우선한다.

## 중요 오버라이드

- 진행하기 전에 Plugin router [$index](../index/SKILL.md)를 참조한다.
- [$critical-overrides](../../references/critical-overrides.md)를 따른다.

## 사용자 컨텍스트

시작 전에 [$user-context](../user-context/SKILL.md)를 불러오고, 로컬 셸 접근이 가능하면 preflight 스크립트를 실행한다.

관련이 있으면 저장된 제품 URL, Figma 파일, 스크린샷, 참조 이미지, 코드베이스 경로, Storybook, 토큰, 디자인 시스템, 브랜드 에셋, 컴포넌트 참조, 브라우저 선호, 공유 대상을 grounding material로 사용한다.

저장된 모든 참조를 검사하지 않는다. 현재 작업에 필요한 것만 검사한다.

## 계약

- 스캔하기 전에 제품, 대상 사용자, 시간 범위, 리서치 범위를 다시 말한다.
- 기본적으로 공개 출처를 사용한다.
- 커넥터를 사용할 수 있고 사용자 요청이 허용하면 내부 출처를 사용한다.
- 가능한 곳마다 출처를 인용한다.
- 관찰된 근거와 추론을 분리한다.
- 일화에서 과도하게 주장하지 않는다.
- 불만 목록 덤프를 반환하지 않는다. 명확한 제품 스토리를 말한다.
- 출처 접근이 없거나 약하면 명확히 말한다.

## 워크플로

1. 리서치 범위를 다시 말한다.
2. 공개 출처를 검색한다.
   - Reddit
   - X/Twitter
   - Hacker News
   - Stack Overflow
   - GitHub issues/discussions
   - 관련성이 있는 포럼, 블로그, 리뷰, YouTube 댓글, 개발자 커뮤니티
3. 사용할 수 있으면 내부 출처를 검색한다.
   - Slack
   - Gong
   - Notion
   - Google Drive/docs
   - Linear/Jira/GitHub
   - 지원 또는 CRM 노트
4. 근거를 가장 높은 신호의 UX 문제로 클러스터링한다.
5. 다음을 분리한다.
   - 제품 UI·워크플로 마찰
   - 문서·도움말 마찰
   - 온보딩 마찰
   - 계정, 결제, 권한, 설정 마찰
   - 개발자/API/SDK 마찰
   - 신뢰성·성능 문제
   - 기능 요청
6. 심각도, 빈도, 확신도, 제품 레버리지로 문제의 순위를 매긴다.
7. 명확한 제품 스토리를 말한다.

## 출력

사용자가 다른 형식을 요청하지 않으면 기본적으로 채팅 안의 리서치 브리프로 작성한다.

다음을 포함한다.

- Executive read: 핵심 스토리를 5~7문장으로 요약한다.
- Ranked UX problems: 각 문제마다 문제, 사용자 목표, 표면, 무엇이 깨지는지, 근거, 심각도, 빈도 신호, 확신도, 권장 제품 조치를 포함한다.
- Source map: 무엇을 검색했는지, 각 출처가 어떤 신호를 제공했는지, 어디에서 신호가 약했는지.
- Opportunity map: 이번 주에 고칠 것, 이번 분기에 고칠 것, 더 깊은 리서치가 필요한 것으로 권장 사항을 묶는다.

## 규칙

- 가능한 곳마다 출처를 인용한다.
- 일화에서 과도하게 주장하지 않는다.
- 목소리 큰 불만과 빈번한 문제를 분리한다.
- UX 마찰과 누락된 기능을 분리한다.
- 신뢰성·성능 문제와 UX 워크플로 문제를 분리한다.
- 내부 전용 근거는 별도로 표시한다.
- 브리프는 날카롭고 구체적이며 쉽게 소비할 수 있게 유지한다.
````

#### 플러그인: Product Design · 스킬명: `audit` — 감사

````markdown
---
name: audit
description: "제품 흐름, 여정, 워크플로, 퍼널, 온보딩 경로, checkout 경로, 설정 경로, 화면 또는 다단계 제품 경험을 감사하거나 비평한다. 먼저 스크린샷을 캡처하고, Figma 또는 로컬 폴더에 배치한 뒤, 그 근거를 바탕으로 UX, 디자인, 접근성 findings를 보고한다. 사용자가 제품 경험을 감사, 비평, 리뷰, 검사, 평가해 달라고 요청할 때 사용한다."
---

# 감사

사용자가 제품 흐름, 여정, 퍼널, 온보딩 경로, checkout 경로, 설정 경로, 화면 또는 기타 제품 경험을 감사하거나 비평하려 할 때 이 스킬을 사용한다.

출력은 느슨한 의견이 아니다.

출력은 다음이다.

- 흐름의 스크린샷
- 선택한 대상에 배치된 스크린샷
- 번호가 매겨진 단계 목록
- 단계 또는 스크린샷에 연결된 UX 및 디자인 findings
- 단계 또는 스크린샷에 연결된 접근성 risks
- 스크린샷만으로 확인할 수 없었던 사항의 명확한 한계

## 중요 오버라이드

- 진행하기 전에 Plugin router [$index](../index/SKILL.md)를 참조한다.
- [$critical-overrides](../../references/critical-overrides.md)를 따른다.

## 사용자 컨텍스트

시작 전에 [$user-context](../user-context/SKILL.md)를 불러오고, 로컬 셸 접근이 가능하면 preflight 스크립트를 실행한다.

관련이 있으면 저장된 제품 URL, Figma 파일, 스크린샷, 참조 이미지, 코드베이스 경로, Storybook, 토큰, 디자인 시스템, 브랜드 에셋, 컴포넌트 참조, 브라우저 선호, 공유 대상을 grounding material로 사용한다.

저장된 모든 참조를 검사하지 않는다. 현재 작업에 필요한 것만 검사한다.

## 경로

감사 전에:

1. 제품 또는 표면을 식별한다.
2. 흐름 또는 작업을 식별한다.
3. 목적지를 식별한다.
4. 캡처 도구를 선택한다.
5. 흐름을 캡처한다.
6. 각 스크린샷을 저장, 검사, 배치, 주석 처리한다.

목적지 규칙:

- 사용자가 Figma를 명명하면 Figma를 사용한다.
- 사용자가 로컬 폴더를 명명하면 해당 폴더를 사용한다.
- 목적지가 없으면 한 가지 질문만 한다. "Should I put this in Figma or a local folder?"

캡처 규칙:

- 먼저 Codex in-app Browser를 사용한다.
- Browser가 대상에 접근, 제어, 스크린샷 캡처를 할 수 없으면 Chrome [Internal]을 사용한다.
- Browser와 Chrome이 캡처를 완료할 수 없으면 fallback으로 Playwright를 사용하기 전에 질문한다.
- 어떤 도구도 유효한 스크린샷을 캡처하거나 흐름을 제어할 수 없으면 멈추고 blocker를 보고한다.

Browser 캡처 순서:

1. 브라우저 작업 전에 Browser skill을 불러온다.
2. 브라우저에 연결하고 현재 탭이 이미 대상을 보여주면 현재 탭을 사용한다.
3. 감사에 fresh start가 필요한 경우가 아니라면 reload하거나 다른 곳으로 이동하지 않는다.
4. 행동하기 전에 보이는 상태를 관찰한다.
5. 각 클릭, 입력, 키 입력 전에 최신 DOM snapshot을 사용해 하나의 명확한 컨트롤을 대상으로 삼는다.
6. 각 행동 뒤 변경을 증명하는 가장 저렴한 새 확인을 수행한다. 구조는 DOM, 시각 상태는 screenshot을 사용한다.
7. accepted screenshot을 감사 근거로 사용하기 전에 저장하고 검사한다.

Figma 규칙:

- 목적지가 Figma이면 파일 생성 또는 편집 전에 필요한 Figma skill을 불러온다.
- Figma가 성공하더라도 모든 스크린샷의 로컬 사본을 유지한다.
- 저장된 로컬 파일을 검사하고 승인하기 전에는 스크린샷을 Figma에 업로드하지 않는다.
- 스크린샷이 Figma 출력에 시각적으로 배치되기 전까지 Figma 작업은 끝난 것이 아니다.
- Figma에 스크린샷을 배치한 뒤 board를 render 또는 inspect하고 모든 흐름 단계가 올바른 카드에 올바른 스크린샷으로 보이는지 확인한다.
- 이미지가 없거나, 잘못 배치되었거나, 비어 있거나, 사용되지 않은 asset으로만 업로드되었으면 handoff 전에 수정한다.
- Figma 도구가 파일을 만들거나 이미지를 배치할 수 없으면 감사를 로컬에 저장하고 누락된 Figma capability를 설명한다.

근거 규칙:

- 현재 감사 실행에서 캡처한 근거만 사용한다.
- 사용자가 명시적으로 제공하지 않은 한 memory, 이전 채팅, 오래된 trace, cached screenshot, 이전 generated artifact를 감사 근거로 사용하지 않는다.
- 제품, 흐름, 목적지, 캡처 도구가 알려지기 전에는 감사하지 않는다.
- 스크린샷만으로 완전한 접근성 준수를 주장하지 않는다.

## 흐름 캡처 및 감사

전문 디자인, UX, 접근성 auditor로 행동한다.

흐름의 각 단계에서 사용자가 보는 것을 캡처하고, 화면이 어떻게 동작하는지 관찰하고, 스크린샷을 검사하고, 다음으로 이동하기 전에 audit notes를 작성한다.

강점, UX 문제, 접근성 risks, 한계, 권장 사항을 무엇을 검사하고 어떻게 설명할지 결정할 때 [references/design-audit-framework.md](references/design-audit-framework.md)를 따른다.

스크린샷 소스 규칙:

- 실제로 본 스크린샷을 사용한다.
- 그 정확한 스크린샷을 로컬 audit folder에 저장한다.
- 저장된 파일을 승인하기 전에 열거나 검사한다.
- 저장된 파일이 잘못된 창, 잘못된 상태, 빈 페이지, crop, loading screen을 보여주면 reject하고 다시 캡처한다.
- 목적지가 Figma이면 승인된 로컬 파일을 업로드한다.
- 업로드 뒤 Figma board가 같은 단계를 보여주는지 확인한다.
- Browser, Chrome, Computer Use 스크린샷을 OS screenshot으로 대체하지 않는다. 대체하려면 먼저 저장된 파일이 같은 창과 상태를 보여준다는 것을 증명해야 한다.

모든 단계에서:

1. 요청된 흐름의 다음 단계로 이동한다.
2. 화면이 로드되고 시각적으로 안정될 때까지 기다린다.
3. loading spinner, 빈 영역, login wall, error page, blocked state, cookie dialog, half-rendered content를 확인한다.
4. 스크린샷을 캡처한다.
5. 승인하기 전에 스크린샷을 검사한다.
6. 비어 있거나, loading 중이거나, crop되었거나, blocked이거나, 잘못된 상태를 보여주면 reject한다.
7. navigation, focus, loading, validation, error handling, empty state, motion, 다음 action의 명확성처럼 감사에 중요한 동작을 관찰한다.
8. 해당 단계의 notes를 작성한다.
9. notes에는 강점, UX 문제, 접근성 risks, 해당 단계를 감사하기 어렵게 만든 한계를 보고한다.
10. `01-start.png`, `02-form-filled.png`, `03-confirmation.png`처럼 번호가 매겨진 이름으로 accepted screenshot을 저장한다.
11. 업로드 또는 handoff 전에 저장된 screenshot file을 검사한다.
12. 각 accepted screenshot을 선택한 목적지에 즉시 추가한다.
13. 해당 단계의 notes를 선택한 목적지에 즉시 추가한다.

목적지가 로컬 폴더이면:

- 해당 폴더에 스크린샷을 저장한다.
- 끝에서 공유할 수 있는 파일에 notes를 저장한다.

목적지가 Figma이면:

- 스크린샷을 순서대로 같은 행에 왼쪽에서 오른쪽으로 배치하고, 각 스크린샷 사이를 200px 둔다. 15개마다 새 행으로 이동하고 행 사이를 600px 둔다.
- 스크린샷 아래에 단계 번호와 이름, notes를 담은 텍스트를 추가한다.
- Figma가 성공해도 로컬 폴더 사본을 유지한다.
- 완료되면 추가한 모든 asset을 Section으로 감싸고 section 제목을 지정한다.

Acceptance checks:

- 요청된 흐름의 모든 중요한 단계에 유효한 스크린샷 또는 명명된 blocker가 있다.
- 스크린샷이 순서대로 저장된다.
- 스크린샷은 캡처되는 대로 선택한 목적지에 배치된다.
- notes는 작성되는 대로 선택한 목적지에 배치된다.
- 모든 note는 설명하는 스크린샷 또는 단계를 가리킨다.
- notes는 해당될 때 강점, UX 문제, 접근성 risks, 근거 한계를 설명한다.
- 접근성 risks는 스크린샷에서 볼 수 있는 것과 여전히 테스트가 필요한 것을 말한다.
- 최종 스크린샷 세트와 notes는 요청된 감사를 뒷받침하기에 충분하다.

Blockers:

- 흐름을 완료할 수 없다.
- 필수 단계를 스크린샷으로 캡처할 수 없다.
- 소스가 흐름을 불명확하게 만드는 방식으로 변경된다.
- 스크린샷을 저장하거나 목적지에 배치할 수 없다.
- notes를 작성하거나 목적지에 배치할 수 없다.
- 요청된 주장이 스크린샷으로 제공할 수 없는 근거를 요구한다.

## 최종 응답

흐름을 캡처하고 notes를 작성한 뒤 최종 응답에 모든 단계를 나열한다.

최종 단계 목록에는 반드시 다음이 포함되어야 한다.

- 단계 번호
- 단계의 짧은 설명
- 해당 단계의 일반적인 상태

전체 출력이 저장되거나 배치된 위치도 포함한다.

언어는 직접적으로 유지한다. 평이한 표현으로 충분할 때 넓은 디자인 jargon을 사용하지 않는다.
````

#### 플러그인: Product Design · 스킬명: `ideate` — 아이데이션

````markdown
---
name: ideate
description: "Product Design get-context가 디자인 브리프를 확인한 뒤 이미지 기반 시각 대안, 리믹스, 컨셉 방향을 생성한다. 사용자가 제공된 컨텍스트에서 디자인 변형, 시각 탐색, 리믹스, 이미지 생성 접근을 요청할 때 사용한다."
---

# 아이데이션

사용자의 아이디어에 대한 디자인 컨셉 생성을 맡는다. [$index](../index/SKILL.md)의 공유 Product Design routing guidance를 따른다.

## 중요 오버라이드

- 진행하기 전에 Plugin router [$index](../index/SKILL.md)를 참조한다.
- [$critical-overrides](../../references/critical-overrides.md)를 따른다.

## 사용자 컨텍스트

시작 전에 [$user-context](../user-context/SKILL.md)를 불러오고, 로컬 셸 접근이 가능하면 preflight 스크립트를 실행한다.

제공된 제품 URL, Figma 파일, 스크린샷, 참조 이미지, 코드베이스 경로, Storybook, 토큰, 디자인 시스템, 브랜드 에셋, 컴포넌트 참조, 브라우저 선호, 공유 대상을 Image Gen generation에 첨부하여 디자인 브리프에 맞춘다.

저장된 모든 참조를 검사하지 않는다. 현재 작업에 필요한 것만 검사한다.

## 워크플로

`$get-context`가 이 정확한 요청에 대한 디자인 브리프를 되짚어 말하고 확인하기 전에는 이미지를 생성하지 않는다.

이 스킬이 직접 호출되었고 현재 thread에 확인된 브리프가 아직 없으면 먼저 [$get-context](../get-context/SKILL.md)로 라우팅한다.

이미지 생성 전에:

1. 브리프를 이해한다.
   - 대상이 컴포넌트, 화면, 기능·워크플로, 넓은 제품 아이디어인지 식별한다.
   - 의도된 사용자, 제품 표면, 목표를 식별한다.
   - 사용자의 hard constraints를 보존한다.
   - 브리프가 아직 되짚어지고 확인되지 않았으면 `get-context`를 실행한다.
2. 컨텍스트를 해결한다.
   - 제공된 파일, 스크린샷, 링크, 보이는 참조를 사용한다.
   - 로컬 워크스페이스에서는 가까운 디자인 문서와 다른 로컬 시각 컨텍스트를 찾는다.
   - `user-context`, `storybook/`, `.storybook/`, `design-system/`, `design-systems/`, `tokens/`, `components/`, `app/`, generated prototype roots 같은 가능성 높은 디자인 컨텍스트 폴더를 확인한다.
   - 기존 프로젝트에서는 생성 전에 기존 제품 스크린샷, 유사 흐름, Storybook 캡처, 디자인 토큰, 컴포넌트 참조를 찾는다.
   - 기존 앱에 접근할 수 없으면 사용자가 만드는 화면과 유사한 예시 화면을 제공할 수 있는지 묻는다.
   - Image Gen prompt에 디자인 언어와 토큰을 반드시 추가한다.
3. 참조를 직접 검사한다.
   - 생성 전에 스크린샷, 이미지, Figma frame, 앱 표면 또는 기타 시각 참조를 본다.
   - 파일명만 보고 추론하지 않는다.
   - 명명된 로컬 경로나 참조가 보이지 않으면 멈추고 사용자에게 경로 확인, 파일 업로드, 로컬 앱 시작, 올바른 워크스페이스 지정을 요청한다.
4. variation mode를 결정한다.
   - 유용한 로컬 디자인 컨텍스트가 있고 사용자가 새 스타일을 요청하지 않았으면 기존 방향 안에 머문다.
   - 유용한 디자인 컨텍스트가 없거나 사용자가 넓은 탐색을 요청하면 concept과 visual system을 모두 변화시킨다.
   - 특정 컴포넌트나 기존 표면에서는 브랜드 스타일을 바꾸기 전에 구조, 상호작용, 위계, 강조를 변화시킨다.
   - 넓은 제품 아이디어에서는 의미 있게 다른 세 가지 제품 방향을 탐색한다.
5. Image Gen 전에 대상 dimensions를 선택한다.
   - 사용자의 요청과 제공된 시각 참조에 가장 잘 맞는 dimensions를 선택한다.
   - Mobile app: `390 x 844`.
   - Tablet app: `834 x 1194`.
   - Desktop app, dashboard, admin, SaaS: `1440 x 1024`.
   - Landing 또는 marketing page: `1440` wide and scrollable.
   - Modal, panel, widget, component: 자연스러운 container size.
   - 제공된 screenshot, Figma frame, mockup, reference image: 사용자가 그 visual에서 이어가려는 경우 dimensions와 aspect ratio를 맞춘다.
   - 혼잡함을 피한다. 선택한 dimensions에 깨끗하게 맞고, 현실적인 spacing, 읽기 쉬운 type, clipped content가 없게 만든다.
   - 모든 Image Gen prompt에 선택한 dimensions를 포함한다.
6. 접근 gaps를 확인한다.
   - connector, reference, file에 auth, permissions, expired login, missing scope, 비정상적으로 빈 결과, unavailable local state 때문에 접근할 수 없으면 멈춘다.
   - gap을 명확히 말하고 접근 문제를 해결할지, 해당 소스 없이 계속할지 묻는다.
   - 명명된 참조를 조용히 무시한 채 이미지를 생성하지 않는다.
7. 컨텍스트가 너무 얇을 때만 질문한다.
   - 유용한 directions를 생성하기에 컨텍스트가 부족할 때만 targeted question 하나를 묻는다.
   - 스타일 방향, 대상 사용자, 참조 표면에 대해 묻는 것을 선호한다.
8. 사용자가 제공한 이미지와 mock을 디자인 브리프와 함께 Image Gen call에 첨부한다.
9. 정보 위계, 레이아웃 전략, 상호작용 모델, 제품 framing이 다른 독립 옵션 3개를 생성한다.

반드시 따라야 할 규칙:

- 아래 Image Gen prompt를 사용한다.
- built-in Image Gen tool을 사용한다.
- 사용자가 count를 override하지 않는 한 정확히 세 개의 독립 이미지를 생성한다.
- 가능하면 옵션을 병렬로 생성한다.
- 각 옵션은 자체 Image Gen result여야 한다. 여러 아이디어를 한 이미지에 넣지 않는다.
- 제공된 스크린샷, 파일, 앱 캡처, Figma 참조, 시각 소스 자료를 가능하면 moodboard inspiration으로 첨부한다.
- 기존 제품 스크린샷, 유사 흐름, Storybook 캡처, 디자인 토큰, 컴포넌트 참조를 가능하면 grounding material로 첨부한다.
- screenshot, image, visual file을 사용할 수 있으면 실제 이미지를 Image Gen call에 첨부한다. 텍스트 설명에 의존하지 않는다.
- Image Gen call이 실제로 이미지 또는 읽을 수 있는 로컬 이미지 경로를 받았을 때만 시각 참조를 첨부했다고 주장한다.
- 이미지를 첨부할 수 없으면 명확히 말하고 text-only direction으로 계속할지 묻는다.
- 모든 이미지에서 브리프의 hard constraints를 보존한다.
- 옵션을 생성한 뒤에는 어떤 build work도 시작하기 전에 사용자의 선택을 기다린다.
- 선택된 옵션이 `$image-to-code`의 visual target이다.

## 피드백 루프

사용자가 옵션을 본 뒤 피드백을 주면 그 피드백을 반영한 revised options를 생성한다.

사용자가 옵션을 선택하고 피드백을 주면 build 전에 해당 피드백으로 revised option을 생성한다.

사용자가 여러 옵션의 일부를 좋아하면 그 선택을 조합한 새 Image Gen design을 만들고 build 전에 보여준다.

## Image Gen Prompt

확인된 디자인 브리프에 맞게 이 prompt를 조정하고, 사용 가능한 image references를 첨부한 뒤 Image Gen으로 보낸다.

```text
Create realistic, production-quality UI designs with clear hierarchy, strong typography, intentional imagery, and purposeful spacing. Keep the design simple. Avoid busy interfaces. Every section should have a clear purpose, and every element should earn its place. Prioritize clarity, whitespace, and usability over decorative complexity.

### Target Dimensions
Pick the dimensions that best match the user's request and any provided visual reference.
- Mobile app: `390 x 844`
- Tablet app: `834 x 1194`
- Desktop app, dashboard, admin, or SaaS: `1440 x 1024`
- Landing or marketing page: `1440` wide and scrollable
- Modal, panel, widget, or component: natural container size
- Provided screenshot, Figma frame, mockup, or reference image: match its dimensions and aspect ratio when the user wants to continue from that visual

Avoid crowding. Make the design fit the chosen dimensions cleanly, with realistic spacing, readable type, and no clipped content.

### Layout
When deciding how to lay elements out on the page, this should be your priority order for tools to differentiate sections:
1. Use spacing, grouping, alignment, typography, and hierarchy on the same product surface.
2. Use simple dividers or row separators.
3. Use a subtle surface tint only when the base surface is not enough.
4. Use borders only when separation still is not clear.
5. Use shadows/elevation last, and sparingly.

Don'ts:
- Do not default to a centered "app card" (the whole UI is in a card on the page) on top of a contrasting page background. Use the base page surface first unless the source product or user explicitly asks for a contained app panel.
- Do not put cards inside cards. Do not make every major section a card. Do not make each list item its own card unless each item is truly a standalone object. A normal list should usually read as one grouped surface with lightweight row separation.
- Do not make up extraneous features. Add only the things essential to accomplish what the prototype's goal is. Don't make up more features just to fill out a UI.

### Typography
- Anchor UI typography to readable product sizes. Body text should usually sit between 14px and 16px, with the rest of the type scale built around that baseline.
- Keep long-form text to a comfortable line length, generally no more than 65 characters per line.
- Use no more than 2 fonts in a UI. You can use any font available in the project, or fonts provided free on Google Fonts. Pick the font that is best for the goal of the product and that matches with its intended look and feel.

### Presentation
- Do not add browser or device chrome around the mockup.
- Do not put multiple ideas into a single image generation.
- Vary each idea as much as possible while adhering to the constraints given entirely.
```

## 출력

생성 뒤 다음을 제공한다.

1. 각 컨셉의 선택을 압축해 보여주는 짧고 기억하기 쉬운 이름.
2. 더 탐색할지, 하나의 방향을 선택해 계속할지 묻는 짧은 closing question.

이미지 도구가 생성된 이미지를 이미 thread에 표시했다면 final message에 같은 이미지를 다시 embed하지 않는다.

이미지 도구가 생성된 이미지를 표시하지 않았다면 option마다 하나의 이미지를 포함한다. 같은 생성 이미지를 두 번 보여주지 않는다.

closing question 예시:

> Want to explore more directions, or should I build one of these? If one works, tell me 1, 2, or 3.

완료란 요청된 수의 독립 이미지가 생성되었고, 사용자에게 하나를 선택하도록 요청한 상태를 뜻한다.
````

#### 플러그인: Product Design · 스킬명: `image-to-code` — 이미지에서 코드로

````markdown
---
name: image-to-code
description: "Product Design get-context가 디자인 브리프를 확인한 뒤, 선택된 이미지, 스크린샷, 목업 또는 Image Gen 참조를 충실한 반응형 프론트엔드로 구현한다."
---

# 이미지에서 코드로

시각 대상 이미지를 고품질의 상호작용형 웹사이트 또는 웹앱으로 변환하는 일을 맡는다.

## 중요 오버라이드

- 진행하기 전에 Plugin router [$index](../index/SKILL.md)를 참조한다.
- [$critical-overrides](../../references/critical-overrides.md)를 따른다.

## 사용자 컨텍스트

시작 전에 [$user-context](../user-context/SKILL.md)를 불러오고, 로컬 셸 접근이 가능하면 preflight 스크립트를 실행한다.

관련이 있으면 저장된 제품 URL, Figma 파일, 스크린샷, 참조 이미지, 코드베이스 경로, Storybook, 토큰, 디자인 시스템, 브랜드 에셋, 컴포넌트 참조, 브라우저 선호, 공유 대상을 grounding material로 사용한다.

저장된 모든 참조를 검사하지 않는다. 현재 작업에 필요한 것만 검사한다.

## 워크플로

중요: 이것은 안내가 아니다. 완료해야 하는 체크리스트다.

0. `$get-context`가 이 정확한 요청에 대한 디자인 브리프를 되짚어 말하고 확인하기 전에는 시작하지 않는다. 이 스킬이 명확한 시각 대상 없이 직접 at-mention되었거나 현재 thread에 확인된 브리프가 아직 없으면 먼저 [$get-context](../get-context/SKILL.md)로 라우팅한다.
1. 재현할 선택된 이미지, 스크린샷, 목업, Image Gen result가 없으면 시작하지 않는다. written brief만으로는 충분하지 않다.
2. 제공된 이미지를 재현할 디자인으로 취급한다.
3. 제공된 디자인이 mobile viewport이면 mobile app을 만든다. 불명확하면 desktop으로 기본 설정한다.
4. reference design을 검토하고, 디자인 안의 모든 image asset을 catalog한 뒤, Image Gen tool을 사용해 각각의 individual image를 만든다. 생성해야 할 모든 asset을 놓치지 않도록 확대해서 본다.

예시:

- full bleed image background를 포함한 hero image
- featured article imagery
- thumbnail
- decorative illustration
- texture와 background motif
- logo
- product image
- avatar

규칙:

- 중요 규칙: real icon과 image asset 대신 custom div art, CSS art, inline SVG, handcrafted SVG, HTML element drawing, div/span shape, CSS drawing, gradient, emoji, text glyph를 절대 만들지 않는다.
- 이미지에는 built-in Image Gen tool을 사용하고, icon에는 가장 잘 맞는 icon library를 사용한다.
- 텍스트가 image asset의 일부이면 그 텍스트를 image asset 안에 유지한다. 예시는 full bleed hero image, sign, poster, packaging, storefront, article art, type이 visual 자체에 속한 illustration이다.
- source가 image 위에 editable UI text가 놓여 있음을 명확히 보여주지 않는 한, background image를 crop하고 그 텍스트를 transparent text box, HTML, CSS, separate overlay layer로 다시 만들지 않는다.
- reference가 custom visual content를 암시하면 generic placeholder를 사용하지 않는다.
- 생성된 asset은 reference mockup과 같은 art direction, palette, rendering style, design language를 공유해야 한다.
- built-in Image Gen tool은 transparent image를 지원하지 않는다. transparency가 필요하면 generated asset을 post-process한다.

5. 페이지의 모든 section을 정의한다. 각 section마다 layout, element 간 spacing, element 자체의 size와 space를 꼼꼼히 측정한다.
6. target design과 맞는 자유 사용 가능한 font를 찾는다.
7. target design과 맞는 자유 사용 가능한 icon library를 찾는다. Lucide icon을 기본값으로 두지 않는다. 가장 잘 맞는 것을 검색한다.

규칙:

- 중요 규칙: custom inline SVG, handcrafted SVG, HTML element drawing, div/span shape, CSS drawing, gradient, emoji, text glyph를 만들지 않는다. built-in Image Gen tool로 asset을 생성하고, icon에는 가장 잘 맞는 icon library를 사용한다.

8. [local-prototype-preflight](../../references/local-prototype-preflight.md)로 시작해 앱을 빌드한다. 모든 interaction을 만들고 앱이 완전하고 기능적이며 상호작용 가능하도록 한다. 모든 control과 state가 활성화되고 기능해야 한다.

예시:

- header, sidebar, tooltip, modal interaction
- hover와 focus state
- responsive navigation
- clickable card와 button
- design이 암시하는 animated affordance
- mockup에 보이는 newsletter form, tag, filter, navigation element
- 대상을 살아 있게 만든다. static site를 전달하지 않는다. 덜 할수록 designer가 더 많이 추가해야 한다.

규칙:

- 계속하기 전에 생성한 모든 image asset을 해당 위치에 배치한다. 반복한다. 계속하기 전에 CSS/SVG placeholder를 포함한 모든 placeholder를 대체한다.
- visible control을 static chrome으로 남기지 않는다.
- 사용자가 요청하지 않는 한 새 page나 route를 만들지 않는다.

9. 로컬 앱을 실행한다.
10. [browser-order](../../references/browser-order.md)를 사용해 로컬 앱을 캡처한다.
11. [design-qa](../design-qa/SKILL.md)를 blocking build gate로 실행한다.

단계:

- QA report를 작성하기 전에 reference image와 최신 prototype screenshot을 연다.
- 같은 viewport와 같은 interaction state를 비교한다. 일치하지 않으면 먼저 누락된 view를 캡처한다.
- QA report를 project root의 `design-qa.md`로 저장한다.
- P0/P1/P2 이슈를 수정하고 앱을 다시 캡처하며, QA report가 `final result: passed`라고 말할 때까지 반복한다.
- P3 polish에 대해 계속 loop하지 않는다. 남은 P3는 follow-up iteration notes에 포함한다.
- source capture, prototype capture, visual comparison이 막히면 멈춘다. `design-qa.md`는 `final result: blocked`라고 말해야 한다.
- `design-qa.md`가 존재하고 `final result: passed`라고 말하지 않는 한 handoff하지 않는다.

12. 앱 또는 웹사이트를 handoff한다.

- [design-qa](../design-qa/SKILL.md)가 통과한 뒤에만 handoff한다.
- 프로토타입은 로컬에서 계속 실행되게 둔다.
- 클릭 가능한 로컬 URL을 제공한다.
- 디자이너가 설명하듯 작업을 간단히 설명한다.
- [critical-overrides](../../references/critical-overrides.md#build-handoff)의 post-build iteration과 share nudge를 포함한다.
````

#### 플러그인: Product Design · 스킬명: `url-to-code` — URL에서 코드로

````markdown
---
name: url-to-code
description: "Product Design get-context가 디자인 브리프를 확인한 뒤 Browser/Chrome 소스 근거를 사용해 라이브 URL을 실행 가능한 프론트엔드 전용 로컬 앱으로 복제한다."
---

# URL에서 코드로

``를 실제 상호작용형 프론트엔드 전용 로컬 앱 또는 웹사이트로 복제한다. 복제본은 소스처럼 보이고 상호작용해야 한다.

## 중요 오버라이드

- 진행하기 전에 Plugin router [$index](../index/SKILL.md)를 참조한다.
- [$critical-overrides](../../references/critical-overrides.md)를 따른다.

## 사용자 컨텍스트

시작 전에 [$user-context](../user-context/SKILL.md)를 불러오고, 로컬 셸 접근이 가능하면 preflight 스크립트를 실행한다.

관련이 있으면 저장된 제품 URL, Figma 파일, 스크린샷, 참조 이미지, 코드베이스 경로, Storybook, 토큰, 디자인 시스템, 브랜드 에셋, 컴포넌트 참조, 브라우저 선호, 공유 대상을 grounding material로 사용한다.

저장된 모든 참조를 검사하지 않는다. 현재 작업에 필요한 것만 검사한다.

## 워크플로

0. `$get-context`가 이 정확한 요청에 대한 디자인 브리프를 되짚어 말하고 확인하기 전에는 시작하지 않는다. 이 스킬이 직접 호출되었고 현재 thread에 확인된 브리프가 아직 없으면 먼저 [$get-context](../get-context/SKILL.md)로 라우팅한다.
1. 중요 단계: 진행하기 전에 사용자가 대상 웹사이트의 약관을 따라야 한다고 경고한다. 이 워크플로는 사용자가 소유했거나 재현 권한이 있는 앱과 웹사이트에만 사용한다.
2. [browser-order](../../references/browser-order.md)를 사용해 source URL을 연다.
3. 페이지가 올바른지 확인한다.
   - wrong page, blocked page, login page, promo page, loading screen, error page, app-install page, unrelated redirect가 보이면 계속하지 않는다.
   - 페이지가 잘못되었으면 다른 사용 가능한 browser로 다시 시도한다.
   - 모든 browser가 wrong page를 보여주면 멈추고 무엇이 보이는지 사용자에게 말한다.
4. source page를 신중하게 캡처한다.
   - 페이지 맨 위에서 시작한다.
   - 작은 단계로 아래로 scroll한다.
   - 각 단계에서 보이는 것을 캡처한다.
   - 새 section, control, sticky element, animation, lazy-loaded asset을 기록한다.
   - 전체 page를 볼 때까지 계속한다.
   - 맨 위로 돌아와 무언가 바뀌었는지 확인한다.
   - mobile `390 x 844`에서도 반복한다.
5. 브라우저 DOM 도구를 사용해 source를 재현하는 데 필요한 모든 것을 수집한다.
   - element
   - component
   - text
   - link
   - button과 control
   - state
   - image
   - icon
   - font
   - video
   - SVG
   - style sheet
   - color
   - spacing
   - layout size
   - responsive behavior
6. page interaction을 찾고 테스트한다.
   - screenshot과 browser DOM tool을 사용해 visible control을 찾는다.
   - navigation, button, link, input, menu, drawer, modal, tab, carousel, hover state, sticky element, 그 밖에 사용자가 상호작용할 수 있는 모든 것을 포함한다.
   - control 하나씩 테스트한다.
   - 다음 control을 테스트하기 전에 시작 상태로 돌아간다.
   - 페이지가 시각적으로 바뀌거나 browser tool이 state change를 보여주면 결과를 저장한다.
7. source page의 real asset을 복사한다.
   - page가 asset을 load하면 browser가 접근하거나 저장할 수 없는 경우를 제외하고 available로 취급한다.
   - image, logo, icon, font, video, SVG, sprite, mask, cursor, background image가 page에서 사용되면 local로 복사한다.
   - image asset을 복사할 수 없으면 원본 screenshot을 사용해 ImageGen으로 대체물을 생성한다.
   - font file을 복사할 수 없으면 가장 가까운 open source font match를 사용한다.
   - icon 또는 glyph를 복사할 수 없으면 가장 가까운 matching open source icon set을 사용한다. 가장 가까운 match가 아닌 한 Lucide를 기본값으로 사용하지 않는다.
   - 대체한 asset, font, icon이 있으면 무엇을 왜 대체했는지 간단히 기록한다.
8. [local-prototype-preflight](../../references/local-prototype-preflight.md)로 local app을 만든다.
9. 캡처, 복사, source에서 수집한 것만으로 빌드한다.
   - 새 visual idea를 추가하지 않는다.
   - hotlinked source asset을 사용하지 않는다.
   - source proof가 있을 때 추측하지 않는다.
10. 로컬 앱을 실행한다.
11. 로컬 앱을 original과 비교한다.
   - desktop을 확인한다.
   - mobile을 확인한다.
   - 캡처한 모든 interaction을 확인한다.
   - final QA를 실행하기 전에 명확한 mismatch를 수정한다.
12. [design-qa](../design-qa/SKILL.md)를 blocking build gate로 실행한다.
   - QA report를 project root의 `design-qa.md`로 저장한다.
   - P0/P1/P2 이슈를 수정하고 앱을 다시 캡처하며, QA report가 `final result: passed`라고 말할 때까지 반복한다.
   - P3 polish에 대해 계속 loop하지 않는다. 남은 P3는 follow-up iteration notes에 포함한다.
   - source capture, prototype capture, visual comparison이 막히면 멈춘다. `design-qa.md`는 `final result: blocked`라고 말해야 한다.
   - `design-qa.md`가 존재하고 `final result: passed`라고 말하지 않는 한 handoff하지 않는다.
13. 앱 또는 웹사이트를 handoff한다.
   - [design-qa](../design-qa/SKILL.md)가 통과한 뒤에만 handoff한다.
   - 프로토타입은 로컬에서 계속 실행되게 둔다.
   - 클릭 가능한 로컬 URL을 제공한다.
   - 디자이너가 설명하듯 작업을 간단히 설명한다.
   - [critical-overrides](../../references/critical-overrides.md#build-handoff)의 post-build iteration과 share nudge를 포함한다.

## 강한 규칙

- 먼저 source evidence를 캡처한다. desktop capture, mobile capture, key states, 모든 required asset, icon, control mark, font가 캡처되거나 대체되기 전에는 scaffold, app code 작성, server 시작, local prototype 생성을 하지 않는다.
- 모든 interaction과 state가 target에서 캡처되기 전에는 handoff하지 않는다.
- memory, screenshot alone, guessed CSS, generic asset, prior chat에서 빌드하지 않는다.
- saved state는 source screenshot과 해당 state의 사용 가능한 DOM/style/layout evidence 없이는 구현하지 않는다.
- final app에서 hotlinked source asset을 사용하지 않는다.
- asset을 해결하기를 기다리는 동안에도 temporary CSS icon, text glyph, emoji mark, placeholder block, handmade SVG를 만들지 않는다. 먼저 asset을 해결하고 그다음 빌드한다.
- Browser와 Chrome이 실패하면 Playwright를 사용하기 전에 질문한다. 승인된 도구가 유효한 source와 prototype evidence를 캡처할 수 없으면 멈추고 design-qa blocker를 보고한다.
````

#### 플러그인: Product Design · 스킬명: `design-qa` — 디자인 QA

````markdown
---
name: design-qa
description: "내부 prototype QA helper. Product Design prototype, URL-to-code build, image-to-code build에 handoff 전 비교할 source visual target과 rendered implementation이 있을 때만 사용한다. broad UX critique, design critique, product audit, flow review에는 사용하지 않는다. 그런 사용자 대상 요청은 audit으로 라우팅한다."
---

# 디자인 QA

handoff 전에 prototype의 source design을 rendered implementation과 비교할 때 이 internal helper를 사용한다.

broad UX critique, design critique, product audit, flow review에는 이 스킬을 사용하지 않는다. 그런 사용자 대상 요청에는 [audit](../audit/SKILL.md)을 사용한다.

모든 Product Design build handoff 전에 이 스킬을 사용한다.

통과하는 QA run에는 다음 둘이 모두 필요하다.

- source visual target: Figma node, image, screenshot, mockup, source capture
- rendered implementation: local URL, deployed URL, app screen, component, screenshot

둘 중 하나라도 열거나, 캡처하거나, 비교할 수 없으면 `design-qa.md`에 `final result: blocked`를 쓰고 blocker를 명명한다. build skill이 done으로 handoff하게 두지 않는다.

## 중요 오버라이드

[critical-overrides](../../references/critical-overrides.md)를 따른다.

## 워크플로

generic aesthetic critic가 아니라 product-quality reviewer로 intended design과 implementation을 비교한다.

출력은 두 artifact의 근거에 기반한 prioritized fix list여야 한다.

memory, code, file path만으로 QA review를 작성하지 않는다. 먼저 source design과 implementation을 열거나 캡처한 뒤 실제로 보이는 것을 비교한다.

분리된 image view를 side-by-side comparison인 것처럼 가장하지 않는다.

source image와 implementation screenshot을 같은 comparison input에 함께 넣은 뒤, 그 combined input에서 보이는 차이를 판단한다.

1. comparison target을 식별한다.
   - source design을 결정한다: Figma node, image, design board, screenshot, spec, mockup.
   - implementation을 결정한다: local URL, deployed URL, app screen, component, screenshot, code-rendered view.
   - 판단 전에 같은 viewport, state, theme, device density, route, content, auth state, interaction state를 맞춘다.
   - artifact가 같은 state를 나타내지 않으면 먼저 그 점을 말하고 false precision을 피한다.
2. 근거를 캡처한다.
   - Figma에는 사용할 수 있으면 design context와 screenshot tool을 사용한다.
   - web/app implementation은 target을 browser에서 열고 intended viewport로 screenshot을 캡처한다.
   - 관련 있으면 mobile/desktop, hover/focus/active, empty/loading/error, dark/light, key responsive breakpoint 같은 추가 state를 캡처한다.
   - findings가 evidence를 인용할 수 있도록 가능한 경우 screenshot path 또는 URL을 저장한다.
   - screenshot 캡처만으로는 충분하지 않다. 판단 전에 source image와 implementation screenshot을 같은 comparison input에 넣는다.
3. 비교 전에 normalize한다.
   - crop, viewport size, scale, device frame을 정렬한다.
   - framed mockup과 unframed page를 비교할 때는 mismatch를 기록하지 않고 넘어가지 않는다.
   - full browser chrome 또는 surrounding canvas보다 content region 비교를 선호한다.
4. 적절한 detail level에서 비교한다.
   - full-view comparison으로 전체 composition, hierarchy, layout, density, responsive structure를 판단한다.
   - 중요한 detail이 full-view comparison에서 너무 작아 판단하기 어려우면 focused region comparison을 사용한다.
   - 실제 source와 implementation에서 focused region을 선택한다.
   - fidelity가 precise typography, alignment, imagery, assets, icons, logos, controls, forms, navigation, tables, dense UI, visible interaction state에 의존할 때 focused region을 사용한다.
   - focused region이 필요 없으면 `design-qa.md`에 이유를 쓴다.
   - 중요한 detail이 명확히 읽히지 않으면 full-view comparison만으로 QA를 통과시키지 않는다.
5. 체계적으로 리뷰한다.
   - QA pass가 quick visual check보다 넓으면 [qa-rubric](./references/qa-rubric.md)을 읽는다.
   - information architecture, layout, spacing, typography/fonts, color, imagery/image quality, icons, copy, affordances, interaction states, responsiveness, accessibility, polish를 확인한다.
   - 항상 다섯 가지 required fidelity surface를 구체적으로 점검한다: fonts/typography, spacing/layout rhythm, colors/tokens, image quality, copy/content. 사용자가 해당 영역을 명시하지 않아도 수행한다.
   - mock이 보고 있는 issue를 다루지 않는다면, 예를 들어 null state, 이를 해결해야 할 mock의 shortcoming으로 별도 finding에 기록한다.
   - 또 다른 목표는 implementation이 mock만큼 좋아 보이는지 결정하는 것이다. stylistic problem이 있으면 지적한다. 사용자의 prompt가 implementation에 새고 있다면, 앱 자체가 서도록 두지 못한 점도 지적한다.
   - design drift와 의도된 product/code constraint를 구분한다. deviation이 의도된 것일 수 있으면 question 또는 assumption으로 표현한다.
6. fix-oriented QA report를 만든다.
   - findings를 먼저 제시하고, severity와 user impact 순으로 정렬한다.
   - 각 finding에는 severity, location, 무엇이 다른지, evidence, 왜 중요한지, 구체적 fix를 포함한다.
   - implementation context가 있으면 정확한 CSS/component/token 제안을 포함한다.
   - objective mismatch와 subjective polish recommendation을 분리한다.
   - required fidelity surface가 확인되고, 남은 차이가 acceptable, expected, still actionable로 명시적으로 분류되기 전에는 design이 match한다, done이다, 가능한 만큼 좋다고 말하지 않는다.
   - concise implementation checklist로 끝낸다.

## 필수 Fidelity Surface

모든 QA report는 다음 surface를 명시적으로 평가해야 한다.

- Fonts and typography: family, fallback, weight, size, line height, letter spacing, antialiasing, hierarchy, wrapping, truncation, display text와 small UI text가 적절한 optical weight를 쓰는지. font fidelity를 신중하게 확인하는 것이 매우 중요하며, 유사 typeface를 찾아보거나 image analysis로 font difference를 찾는 것도 포함한다.
- Spacing and layout rhythm: frame size, crop, alignment, margins, padding, grid tracks, section gaps, component spacing, radii, shadows/elevation, vertical rhythm.
- Colors and visual tokens: sampled 또는 inferred palette, gradients, opacity, contrast, semantic state colors, foreground/background balance, CSS token이 source design과 mapping되는지.
- Image quality and asset fidelity: subject correctness, crop, scale, sharpness, compression, transparency halo, masking, background treatment, raster-vs-vector appropriateness, generated asset이 source art direction과 맞는지.
- 시각 target의 logo, illustration, decorative mark, product imagery, non-standard icon, 기타 visible image asset이 custom inline SVG, handcrafted SVG, HTML element, div/span shape, CSS drawing, gradient, emoji, text glyph, placeholder shape, code-native approximation으로 대체되면 QA를 실패시킨다.
- Copy and content of app-specific text.

## Severity

- `P0`: 핵심 사용을 막거나, 심각한 접근성 실패, 깨진 layout, 불가능한 task.
- `P1`: 사용자가 알아차릴 가능성이 높은 major design mismatch 또는 usability regression.
- `P2`: moderate visual drift, inconsistent state, responsive issue, fixable polish gap.
- `P3`: acceptance를 막지는 않지만 fidelity를 개선하는 minor refinement.

## 출력 형식

사용자가 달리 요청하지 않으면 다음 구조를 사용한다.

```markdown
**Findings**

- [P1] Short issue title
  Location: screen/component/selector/file if known.
  Evidence: design does X, implementation does Y.
  Impact: why this matters.
  Fix: concrete change.

**Open Questions**

- Any ambiguity about intentional deviations, unavailable states, or missing artifacts.

**Implementation Checklist**

- Ordered fixes that can be executed directly.

**Follow-up Polish**

- P3 refinements that can improve fidelity after handoff.
```

실질적 mismatch가 없으면 그 점을 명확히 말하고 남은 test gap을 나열한다.

이 스킬을 handoff 전에 사용할 때는 최신 QA report를 project-root `design-qa.md`로 저장한다.

`design-qa.md`에는 다음이 포함되어야 한다.

- source visual truth path
- implementation screenshot path
- viewport
- state
- full-view comparison evidence
- focused region comparison evidence 또는 필요 없었던 이유
- findings
- 이전 QA pass 이후 적용된 patch
- final result

`final result`는 정확히 `passed` 또는 `blocked`여야 한다.

actionable P0/P1/P2 finding이 없으면 `passed`를 사용한다. P3 finding은 follow-up polish로 남을 수 있다.

actionable P0/P1/P2 finding이 남아 있으면 `blocked`를 사용하고 blocker를 명명한다.

QA report의 file path를 반환한다.
````

#### 플러그인: Product Design · 스킬명: `share` — 공유

````markdown
---
name: share
description: "사용자의 선호 배포 도구를 사용해 실행 가능한 프로토타입을 공유한다."
---

# 공유

사용자가 다른 사람과 공유할 수 있도록 실행 가능한 프로토타입을 배포한다.

## 중요 오버라이드

- 진행하기 전에 Plugin router [$index](../index/SKILL.md)를 참조한다.
- [$critical-overrides](../../references/critical-overrides.md)를 따른다.

## 사용자 컨텍스트

시작 전에 [$user-context](../user-context/SKILL.md)를 불러오고, 로컬 셸 접근이 가능하면 preflight 스크립트를 실행한다.

관련이 있으면 저장된 제품 URL, Figma 파일, 스크린샷, 참조 이미지, 코드베이스 경로, Storybook, 토큰, 디자인 시스템, 브랜드 에셋, 컴포넌트 참조, 브라우저 선호, 공유 대상을 grounding material로 사용한다.

저장된 모든 참조를 검사하지 않는다. 현재 작업에 필요한 것만 검사한다.

## 워크플로

1. prototype directory와 사용자의 preferred deployment target을 확인한다.
2. 사용자가 Product Design을 @Sites, @Vercel 또는 다른 deployment tool과 함께 호출하면 이를 선택된 hosting target으로 취급한다.
3. 사용자가 target을 선택하지 않았으면 한 가지 질문만 한다.

> Where should I deploy this: @Sites, @Vercel, or another target?

4. 사용할 수 있으면 선택된 deployment tool을 사용한다.
5. 선택된 tool을 사용할 수 없으면 명확히 말하고 다른 target을 사용할지 묻는다.
6. 가능하면 deployment를 실행한다. 직접 deployment를 완료할 수 있다면 setup instruction을 주지 않는다.
7. shareable URL을 반환한다.
8. 아직 사용자가 해야 하는 누락 사항 또는 manual follow-up을 말한다.

## 규칙

- 사용자가 target을 선택하거나 확인하기 전에는 deploy하지 않는다.
- working URL이 없으면 prototype이 공유되었다고 주장하지 않는다.
- 선택된 tool을 사용할 수 없으면 명확히 말하고 다른 target을 사용할지 묻는다.
````
