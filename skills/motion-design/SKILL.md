---
name: motion-design
description: "화면의 진입·퇴장·페이지 전환·모달 전환을 설계하거나 loading·success·error·hover·press 같은 상태 피드백이 필요할 때 사용한다. 여러 요소의 등장 순서와 시선을 설계하거나, 브랜드 모션 언어를 만들거나, 기존 애니메이션의 속도·이징·피로감·접근성을 리뷰할 때 쓴다. 목적·타이밍·이징·속성·안무·접근성·성능을 결정한다."
allowed-tools: Read, Write, Glob, Grep
---

# Motion Design

모션의 **목적**을 먼저 정하고 타이밍, 이징, 속성, 안무, 접근성, 성능을
결정하는 스킬이다.

이 스킬은 **모션 명세**를 만든다. 제품 소스코드 구현은 하지 않는다.

## STEP 0 — 모션이 필요한지 먼저 판단

모션을 설계하기 전에 **모션이 필요한지** 판단한다. 이 단계를 건너뛰지 않는다.

먼저 목적을 다음 중 하나로 분류한다.

| 목적 | 예시 |
|---|---|
| 정보 전달 | 진행률, 데이터 변화, 개수 증감 |
| 상태 변화 | loading → success → error |
| 공간 관계 | 어디서 열렸고 어디로 닫히는지 |
| 피드백 | 눌렸음, 실패했음, 저장됐음 |
| 브랜드 표현 | 제품 성격을 드러내는 서명 모션 |

**어디에도 해당하지 않으면 모션을 넣지 않는다.** 장식 목적만 있는 모션은
제안하지 않는다.

다음 경우에는 모션을 생략하고 그 이유를 보고한다.

- 정적 화면이나 기존 디자인 시스템만으로 목적이 충분한 경우
- 요구사항에 모션이 없고 추가 효과가 오히려 방해되는 경우
- 기존 제품 모션 명세를 그대로 적용하면 되는 단순 구현

## STEP 1 — 적용 범위와 기존 자산 확인

1. 대상 화면 또는 컴포넌트를 사용자에게 재확인한다.
2. **기존 제품의 모션 언어를 먼저 조사한다.** 모션 토큰, transition 유틸리티,
   애니메이션 라이브러리, 기존 컴포넌트의 duration·easing 값을 찾는다.
3. 기존 모션 언어가 있으면 그 규칙이 이 스킬의 기본값보다 **우선**한다.
   충돌하면 구현하지 말고 차이와 근거를 보고한다.
4. 구현 프레임워크를 임의로 바꾸지 않는다. CSS, Framer Motion, GSAP, Lottie,
   Spring 중 프로젝트가 이미 쓰는 것을 따른다.

### 모션 밀도 기본값

| 제품 성격 | 기본 밀도 |
|---|---|
| 공공·의료·금융·엔터프라이즈 | **낮음** — 상태 피드백에 필요한 최소 전환만 |
| 일반 업무·생산성 도구 | 중간 |
| 마케팅·엔터테인먼트·브랜드 표현 | 사용자가 요청한 수준까지 |

낮은 밀도가 기본인 화면에 primary·secondary·ambient 3계층을 강제하지 않는다.

## STEP 2 — 모션 결정

### 지속 시간

| 요소 유형 | 지속 시간 | 근거 |
|---|---|---|
| 툴팁·마이크로 피드백 | 80-120ms | 즉각적으로 느껴져야 함 |
| 버튼 press·토글 | 120-180ms | 반응성 |
| 아이콘 전환 | 150-250ms | 상태 변화 명확성 |
| 카드 진입·퇴장 | 200-350ms | 공간 인지 |
| 모달·다이얼로그 | 300-400ms | 초점 이동 |
| 페이지 전환 | 400-600ms | 맥락 전환 |

거리가 늘면 지속 시간도 늘린다. 100px 기준, 200px는 1.3배, 400px는 1.6배.
진입은 퇴장보다 30-50% 길게 둔다. 사용자는 나타나는 것에 더 주의한다.

상호작용 피드백은 hover 100ms 미만, press 150ms 미만, 안정화 200-300ms다.

### 이징

- **진입** → 감속. 빠르게 시작해 부드럽게 안착 (ease-out 계열)
- **퇴장** → 가속. 부드럽게 시작해 빠르게 이탈 (ease-in 계열)
- **화면 내 이동** → 양끝 부드럽게 (ease-in-out 계열)
- **반복 ambient** → 이음매 없이 (sine 기반 ease-in-out)

업계 표준값은 `reference/timing-easing-tables.md`에 있다. 이 표에는 Material
Design 3와 Apple HIG의 공개 easing 값이 비교 목적으로 인용되어 있다. 값 자체를
참고하되 원 가이드라인 문서를 복제하지 않는다.

### 속성 선택

**transform과 opacity를 우선한다.** 두 속성은 합성 단계에서 처리되어 레이아웃과
페인트를 다시 유발하지 않는다.

`width`, `height`, `top`, `left`, `margin`처럼 레이아웃을 다시 계산시키는 속성을
쓰려면 다음을 모두 보고한다.

1. transform·opacity로 같은 의미를 만들 수 없는 이유
2. 영향받는 요소 수와 예상 리플로우 범위
3. 대상 기기·브라우저에서의 성능 검증 방법

근거 없이 레이아웃 유발 속성을 쓰지 않는다.

| 효과 목적 | 주 속성 | 보조 속성 |
|---|---|---|
| 진입·퇴장 | position | opacity, scale |
| 강조 | scale | rotation(미세), opacity |
| 상태 변화 | opacity, color | scale |
| 방향·흐름 | position | rotation |
| 로딩·진행 | rotation | scale, opacity |
| 성공 | scale | color |
| 오류 | position(shake) | color |

최소한의 속성만 쓴다. 하나면 직접적, 둘이면 정돈됨, 셋 이상이면 산만해질 수 있다.

### 안무

여러 요소를 함께 움직일 때만 적용한다.

- 주 요소가 먼저 또는 가장 뚜렷하게 진입한다.
- 같은 방향에서 진입해 공간 일관성을 유지한다.
- 3개 이상일 때 동시에 움직이는 요소를 1/3 이내로 둔다.
- stagger 총합은 500ms를 넘기지 않는다.

| 패턴 | 지연 | 총 예산 |
|---|---|---|
| 마이크로 캐스케이드 | 20-40ms | 200ms 미만 |
| 표준 | 50-100ms | 400ms 미만 |
| 극적 | 100-200ms | 600ms 미만 |

### 반복

무한 반복은 목적이 있을 때만 쓴다. 로딩 표시처럼 **진행 중임을 알리는** 용도가
아니면 반복하지 않는다. 사용자가 오래 머무는 화면에서 계속 움직이는 ambient
루프는 피로를 만든다.

## STEP 3 — 접근성과 정지 상태

모든 모션 명세는 다음을 **반드시** 포함한다.

1. **reduced-motion 대체안.** `prefers-reduced-motion: reduce` 환경에서 어떻게
   동작하는지 적는다. 단순히 "애니메이션 제거"로 끝내지 않고, 모션이 전달하던
   정보를 무엇이 대신 전달하는지 명시한다.
2. **정지 상태.** 애니메이션이 끝난 뒤 또는 실행되지 않을 때의 최종 화면.
3. **핵심 정보가 모션에만 실려 있지 않을 것.** 상태·순서·관계를 모션 없이도
   알 수 있어야 한다.

모션이 유일한 전달 수단이면 그 설계는 통과시키지 않는다.

## STEP 4 — 산출물

기본 동작은 **대화창 보고**다. 모션 결정표와 구현·검증 기준을 제시하고 끝낸다.
사용자 승인 없이 프로젝트 파일을 만들지 않는다.

사용자가 명시적으로 저장을 요청하면 다음 경로에만 저장한다.

```text
.docs/design-system/{project-slug}/motion/{screen-or-component}.md
```

`{project-slug}`와 `{screen-or-component}`는 소문자, 숫자, 하이픈만 쓴다. `..`,
절대경로, 경로 구분자를 포함하면 거부한다. 기존 파일이 있으면 diff를 제시하고
승인 전에는 덮어쓰지 않는다.

필수 항목:

- 목적
- trigger와 상태
- 대상 요소
- duration·delay·easing
- 사용할 속성
- 반복 조건
- reduced-motion 대체안
- 성능 위험
- 검증 기준

duration, delay, easing curve, 속성 이름, trigger, reduced-motion 조건, 성능
budget은 문서 개선 단계의 보호 토큰이다. 개선으로 값이 바뀌면 안 된다.

이 스킬이 Markdown을 만들고 **이번 작업의 최외곽 산출물 생성자**일 때만
`humanize-korean` 개선안을 한 번 제안한다. 상위 workflow 안에서 호출되면 제안을
억제한다.

## STEP 5 — 다음 단계 연결

이후 작업은 **공개 스킬 이름으로** 넘긴다. 상대 스킬의 내부 파일이나 경로를
직접 읽도록 요구하지 않는다.

| 다음 목적 | 넘길 스킬 |
|---|---|
| 디자인 시스템·토큰 결정이 먼저 필요할 때 | `ui-ux-pro-max` |
| 화면 구조·상태 명세 문서 | `design-prototype-docs` |
| 폐기 가능한 검증 시안 | `create-prototype` |
| 실제 제품 소스코드 구현 | `frontend-design` |
| 구현 결과 검증 | `impl-verify` |

## 상세 자료

필요할 때만 읽는다.

**철학** (`director/`) — `core-philosophy.md`, `decision-framework.md`,
`disney-principles.md`, `motion-personality.md`, `emotion-mapping.md`,
`choreography.md`, `narrative-structure.md`, `context-adaptation.md`

**참조** (`reference/`) — `timing-easing-tables.md`, `property-selection.md`,
`troubleshooting.md`, `quality-checklist.md`

**패턴** (`patterns/`) — `entrance-exit.md`, `state-feedback.md`,
`ambient-continuous.md`, `multi-element.md`

이 자료들은 upstream 원본이며 영문이다. 여기에는 모든 화면에 primary·secondary·
ambient 3계층을 요구하는 서술이 있으나, 이 하네스에서는 STEP 0과 모션 밀도
기본값이 우선한다. 원본 자료는 참고 지식으로 쓰고 강제 규칙으로 적용하지 않는다.

## 금지 사항

- 목적 분류 없이 모션을 설계하지 않는다.
- 모든 화면에 3계층 모션을 강제하지 않는다.
- reduced-motion 대체안 없이 명세를 완료하지 않는다.
- 근거 없이 레이아웃 유발 속성을 쓰지 않는다.
- 목적 없는 무한 ambient 루프를 제안하지 않는다.
- 기존 제품 모션 언어를 무시하고 새 규칙을 덮어쓰지 않는다.
- 구현 프레임워크를 임의로 교체하지 않는다.
- 사용자 승인 없이 프로젝트 파일을 만들거나 덮어쓰지 않는다.
- 제품 소스코드를 이 스킬에서 직접 수정하지 않는다.

## 출처와 변경 고지

이 스킬은 [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill)
커밋 `f9a8a041`을 하네스에 맞게 반입한 파생 작업이다. 원본은 MIT 라이선스로
제공된다. `director/`, `patterns/`, `reference/`는 원본을 보존하고 이 `SKILL.md`는
목적 우선 분류, 모션 생략 허용, 저밀도 기본값, 접근성 필수 검토, 성능 근거 요구,
승인형 저장 계약, 공개 스킬 handoff에 맞게 다시 작성했다.

원본 참조 자료에는 Material Design 3, Apple Human Interface Guidelines, Disney
애니메이션 원칙이 인용되어 있다. 해당 제3자 자료의 권리는 각 원 저작자에게 있다.

정확한 upstream 커밋, 파일 대응표, 라이선스는
`.user-docs/Skill_Upstream_Governance.md#direct-import-provenance`와 플러그인의
`THIRD_PARTY_NOTICES.md`에서 추적한다.
