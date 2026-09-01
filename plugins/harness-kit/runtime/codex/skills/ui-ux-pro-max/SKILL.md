---
name: ui-ux-pro-max
description: "새 화면이나 제품의 디자인 방향, 색상, 타이포그래피, 간격, 레이아웃, 컴포넌트 밀도를 정할 때 사용한다. 제품 유형·업종에 맞는 디자인 시스템 후보가 필요하거나, 기존 화면의 UX·접근성·일관성을 리뷰하거나, React·Vue·Flutter 등 스택별 UI 원칙이 필요할 때 쓴다. 검색 가능한 로컬 디자인 데이터베이스로 근거 있는 결정을 만든다."
allowed-tools: Read, Write, Glob, Grep
---

## 문서 루트 계약

이 스킬이 하네스 문서를 읽거나 쓸 때 사용하는 정본은 `.ai-docs/`뿐이다. 작업 전에
`.ai-docs/`와 이전 `.docs/`의 존재를 확인한다. `.docs/`만 있거나 두 경로가 함께
있으면 하네스 문서를 읽거나 쓰지 않고 `harness-setup`의 명시적 문서 루트 이관·충돌
해결을 먼저 요청한다. 이전 경로를 호환 별칭으로 추측하지 않는다. 애플리케이션 소스
작업 자체의 권한과 가능 여부는 이 문서 루트 판정으로 제한하지 않는다.


# UI/UX Pro Max

제품 유형, 스타일, 색상, 타이포그래피, 레이아웃, UX, 접근성, 차트, 기술 스택에
대한 로컬 검색 데이터베이스로 디자인 결정과 그 근거를 만드는 스킬이다.

이 스킬은 **디자인 결정**을 담당한다. 제품 소스코드 구현은 하지 않는다.

디자인 시스템 저장 경로·소유권·인계는 단일 앱의
`@.ai-docs/instruction/artifact-output-routing-instruction.md` 또는 복수 앱의
`@.ai-docs/{앱}/instruction/artifact-output-routing-instruction.md`를 따른다.

## 적용 범위

사용한다.

- 새 제품·화면의 디자인 방향을 정할 때
- 색상, 타이포그래피, 간격, 레이아웃, 컴포넌트 밀도를 정할 때
- 제품 유형이나 업종에 맞는 디자인 시스템 후보가 필요할 때
- 기존 화면의 UX·접근성·일관성을 리뷰할 때
- 스택별 UI 구현 원칙이 필요할 때

사용하지 않는다.

- 백엔드 전용 작업, API·데이터베이스 설계, 인프라 작업
- 기존 디자인 시스템과 화면 명세가 확정되어 단순 구현만 남은 경우
- 디자인 판단 없이 문구나 데이터만 수정하는 경우

## STEP 0 — 적용 범위 확인

작업을 시작하기 전에 **반드시** 다음을 확인한다.

1. 현재 위치에서 프로젝트 구조를 탐색한다. git repo 경계와 하위 앱 폴더를 본다.
2. 단일 애플리케이션인지 복수 애플리케이션 프로젝트인지 판정한다.
3. 판정 결과와 대상 애플리케이션을 사용자에게 재확인한다.
4. **기존 디자인 시스템을 먼저 조사한다.** 디자인 토큰, 테마 파일, 컴포넌트
   라이브러리, `.ai-docs/design-system/**`, Tailwind·CSS 변수 설정을 찾는다.
5. 기존 시스템이 있으면 그 규칙이 이 스킬의 추천보다 **우선**한다. 충돌하는
   추천은 제시하되 기존값을 기본으로 두고 차이와 근거를 보고한다.
6. 확인된 범위 밖은 건드리지 않는다.

## STEP 1 — 요구사항 분해

사용자 요청에서 다음을 추출한다. 불명확하면 묻는다.

- **제품 유형**: SaaS, 이커머스, 포트폴리오, 대시보드, 엔터테인먼트, 도구,
  생산성 또는 혼합
- **대상 사용자와 사용 맥락**: 연령대, 사용 환경, 사용 빈도
- **스타일 키워드**: 미니멀, 활기찬, 다크, 콘텐츠 중심, 몰입형 등
- **접근성 요구 수준**: 공공·의료·금융·엔터프라이즈는 접근성을 최우선으로 둔다
- **기술 스택**: 프로젝트에서 탐지한다. `package.json` 의존성(react/next/vue/
  svelte/nuxt/@angular), `pubspec.yaml`(Flutter), `*.xcodeproj`·`Package.swift`
  (SwiftUI), `composer.json`(Laravel), React Native 표식(`app.json` +
  `react-native`)을 확인한다.

스택을 **임의로 가정하지 않는다.** 탐지되지 않으면 사용자에게 묻는다. 하드코딩된
기본값은 모든 추천을 조용히 잘못된 방향으로 보낸다.

## STEP 2 — 검색 실행

검색 스크립트는 이 스킬 디렉터리 안에 있다. 현재 로드한 `SKILL.md`의 부모
디렉터리를 `{skill_dir}`로 두고 호출한다. 관리 저장소의 `skills/...` 상대경로나
특정 플랫폼의 설치 경로를 가정하지 않는다.

```bash
python "{skill_dir}/scripts/search.py" "<query>" --design-system -p "Project Name"
```

`python`이 없으면 `python3`, `py -3` 순으로 시도한다. Python 3.x 표준 라이브러리만
사용하며 외부 패키지 의존성이 없다. Python이 없으면 **설치를 자동으로 시도하지
말고** 사용자에게 설치를 안내한 뒤, 아래 우선순위 표를 근거로 한 축소된 추천을
제공하고 그 사실을 명시한다.

### 도메인별 검색

```bash
python "{skill_dir}/scripts/search.py" "<keyword>" --domain <domain> [-n <max>]
python "{skill_dir}/scripts/search.py" "<keyword>" --stack <stack>
```

| 필요 | 도메인 |
|---|---|
| 제품 유형 패턴 | `product` |
| 스타일 후보 | `style` |
| 색상 팔레트 | `color` |
| 폰트 조합 | `typography` |
| 개별 Google Fonts | `google-fonts` |
| 차트 추천 | `chart` |
| UX 모범 사례 | `ux` |
| 랜딩 페이지 구조 | `landing` |
| 아이콘 추천 | `icons` |
| 모션 프리셋 | `gsap` |
| React·Next.js 성능 | `react` |
| 앱·네이티브 인터페이스 지침 | `web` |

`--domain`을 생략하면 질의에서 자동 추론하지만 겹치는 용어는 잘못 라우팅될 수
있다. 결과가 주제에서 벗어나면 `--domain`을 명시한다.

**사용 가능한 스택**: `react`, `nextjs`, `vue`, `svelte`, `astro`, `nuxtjs`,
`nuxt-ui`, `angular`, `laravel`, `swiftui`, `react-native`, `flutter`,
`jetpack-compose`, `html-tailwind`, `shadcn`, `threejs`, `javafx`, `wpf`,
`winui`, `avalonia`, `uno`, `uwp`.

### 조절 다이얼

```bash
python "{skill_dir}/scripts/search.py" "<query>" --design-system --variance <1-10> --motion <1-10> --density <1-10>
```

| 다이얼 | 낮음 (1-3) | 중간 (4-7) | 높음 (8-10) |
|---|---|---|---|
| `--variance` | 정돈·미니멀 | 균형·모던 | 대담·비대칭 |
| `--motion` | 미세한 마이크로 인터랙션 | 표준 스크롤·스태거 | 복합 안무 |
| `--density` | 여유 (24-96px) | 표준 (16-64px) | 조밀·대시보드 (8-32px) |

공공·의료·금융·엔터프라이즈 화면은 `--motion`을 낮게 두는 것을 기본으로 한다.

### 검색 결과가 0건일 때

결과를 지어내지 않는다.

1. 더 넓거나 다르게 표현한 키워드로 한 번 재시도한다. 제품과 스타일을 합치지
   말고 나눠서 검색해 본다.
2. 그래도 비면 아래 우선순위 표를 근거로 추천하고, 이 추천이 데이터베이스
   매칭이 아니라 기본 원칙에서 나왔음을 **사용자에게 명시한다.**
3. 0건 검색을 데이터가 나온 것처럼 제시하지 않는다.

## STEP 3 — 우선순위 판단

카테고리 충돌 시 1→10 순서로 결정한다. 전체 규칙은 `references/quick-reference.md`
에 있고 필요할 때만 읽는다.

| 우선순위 | 카테고리 | 영향 | 도메인 | 필수 확인 |
|---|---|---|---|---|
| 1 | 접근성 | CRITICAL | `ux` | 대비 4.5:1, 대체 텍스트, 키보드 내비게이션, aria-label |
| 2 | 터치·인터랙션 | CRITICAL | `ux` | 최소 44×44px, 8px 이상 간격, 로딩 피드백 |
| 3 | 성능 | HIGH | `ux` | WebP·AVIF, 지연 로딩, 공간 예약 (CLS < 0.1) |
| 4 | 스타일 선택 | HIGH | `style`, `product` | 제품 유형 일치, 일관성, SVG 아이콘 |
| 5 | 레이아웃·반응형 | HIGH | `ux` | 모바일 우선 breakpoint, viewport meta, 가로 스크롤 없음 |
| 6 | 타이포그래피·색상 | MEDIUM | `typography`, `color` | 본문 16px, 행간 1.5, 시맨틱 색상 토큰 |
| 7 | 애니메이션 | MEDIUM | `ux`, `gsap` | 150-300ms, 의미 전달, 공간 연속성 |
| 8 | 폼·피드백 | MEDIUM | `ux` | 보이는 레이블, 필드 근처 오류, 점진적 공개 |
| 9 | 내비게이션 | HIGH | `ux` | 예측 가능한 뒤로가기, 하단 탭 5개 이하, 딥링크 |
| 10 | 차트·데이터 | LOW | `chart` | 범례, 툴팁, 접근 가능한 색상 |

네이티브·모바일 앱 UI를 전달하기 전에는 `references/pro-rules.md`의 사전 전달
체크리스트를 확인한다.

## STEP 4 — 산출물 결정

기본 동작은 **대화창 보고**다. 후보와 근거를 제시하고 끝낸다. 사용자 승인 없이
프로젝트 파일을 만들지 않는다.

사용자가 명시적으로 저장을 요청하면 다음 경로에만 저장한다.

```text
# 단일 앱
.ai-docs/design-system/{project-slug}/MASTER.md
.ai-docs/design-system/{project-slug}/pages/{page-slug}.md

# 복수 앱 — {앱}은 Step 0에서 확인한 대상 앱
.ai-docs/{앱}/design-system/{project-slug}/MASTER.md
.ai-docs/{앱}/design-system/{project-slug}/pages/{page-slug}.md
```

저장 규칙:

1. `{project-slug}`와 `{page-slug}`는 소문자, 숫자, 하이픈만 쓴다. `..`, 절대경로,
   경로 구분자를 포함하면 거부한다.
2. 기존 파일이 있으면 **읽고 diff를 제시한 뒤** 승인 전에는 덮어쓰지 않는다.
   이전 결정을 조용히 버리지 않는다.
3. 화면별 override 문서에는 MASTER와 **다른 값만** 적는다.
4. 저장 후 구조 검증을 수행한다. 필수 섹션, 토큰 표, 경로, 링크를 확인한다.

스크립트의 `--persist`는 `--output-dir` 기준 `design-system/` 아래에 쓴다.
`--output-dir`를 `.ai-docs`로 지정해 위 계약 경로에 맞춘다. `--output-dir` 없이
`--persist`를 실행하지 않는다. 실행 디렉터리에 따라 위치가 달라진다.
복수 앱에서는 `--output-dir`를 해당 앱의 `.ai-docs/{앱}` 루트로 지정한다.

### 문서 개선 handoff

이 스킬이 Markdown을 만들고 **이번 작업의 최외곽 산출물 생성자**일 때만
`humanize-korean` 개선안을 한 번 제안한다. 상위 workflow 안에서 호출되면 제안을
억제하고 초안과 검증 결과만 반환한다.

색상 hex, 토큰 이름, 수치, 경로, 표는 문서 개선 단계의 보호 토큰이다. 개선으로
값이 바뀌면 안 된다.

## STEP 5 — 다음 단계 연결

이 스킬은 디자인 결정에서 끝난다. 이후 작업은 **공개 스킬 이름으로** 넘긴다.
상대 스킬의 내부 파일이나 경로를 직접 읽도록 요구하지 않는다.

| 사용자의 다음 목적 | 넘길 스킬 |
|---|---|
| 화면 구조·상태·반응형 명세 문서 | `design-prototype-docs` |
| 폐기 가능한 HTML 검증 시안 | `create-prototype` |
| 실제 제품 소스코드 구현 | `frontend-design` |
| 모션 설계가 필요할 때 | `motion-design` |
| 구현 결과 검증 | `impl-verify` |

모션은 **필요할 때만** 제안한다. 정적 화면으로 목적이 충분하거나 요구사항에
모션이 없으면 넘기지 않는다.

## 금지 사항

- 사용자 승인 없이 프로젝트 파일을 만들거나 덮어쓰지 않는다.
- 검색 결과 0건을 데이터가 나온 것처럼 제시하지 않는다.
- 스택을 임의로 가정하지 않는다.
- Python을 package manager로 자동 설치하지 않는다.
- 네트워크에서 디자인 데이터를 내려받지 않는다. 데이터는 로컬 `data/`가 전부다.
- 제품 소스코드를 이 스킬에서 직접 수정하지 않는다.

## 출처와 변경 고지

이 스킬은 [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
`v2.11.3`을 하네스에 맞게 반입한 파생 작업이다. 원본은 MIT 라이선스로 제공된다.
`data/`, `references/`, `scripts/`는 원본을 보존하고 이 `SKILL.md`는 플랫폼 중립
경로, 적용 범위 확인, 승인형 저장 계약, 공개 스킬 handoff에 맞게 다시 작성했다.

정확한 upstream 커밋, 파일 대응표, 라이선스는
`.user-docs/Skill_Upstream_Governance.md#direct-import-provenance`와 플러그인의
`THIRD_PARTY_NOTICES.md`에서 추적한다.
