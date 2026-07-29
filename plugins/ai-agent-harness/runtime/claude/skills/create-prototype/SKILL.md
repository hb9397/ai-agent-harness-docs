---
name: create-prototype
description: >
  폐기 가능한 HTML UI 검증 프로토타입 생성 스킬. 요구사항 번호(SFR, REQ, UC 등
  프로젝트별 prefix) 기반 화면 프로토타입을 HTML 파일로 생성한다.
  Tailwind CSS CDN + Noto Sans KR 기반이며, 실제 서비스 수준의 인터랙티브 프로토타입을 만든다.
  "검증용 프로토타입", "UI 프로토타입", "HTML 목업", "SFR 화면 시안",
  "REQ 화면 시안" 요청에 사용한다. Markdown 화면 설계 문서는 design-prototype-docs,
  실제 앱 소스 구현은 frontend-design이 담당한다.
allowed-tools: Read, Write, Glob, Grep, Agent
---

# Create Prototype — HTML UI 프로토타입 생성기

요구사항 번호(기본 PREFIX: `SFR`, 커스텀 PREFIX 허용)를 기반으로 인터랙티브 UI 프로토타입을 생성하는 스킬이다.
Tailwind CSS CDN과 Noto Sans KR 폰트를 사용하며, `file://` 직접 열기로 확인 가능하다.

> **산출물 구조 원칙**: 모든 HTML은 `display/`, CSS는 `css/`, JSON은 `data/`, JS는 `script/`, 문서는 `docs/`에만 존재한다.
> 각 HTML은 반드시 CSS 1개 + JS 1개 + JSON 1개와 짝을 이룬다.
> `<style>` 블록과 HTML 내부 `<script>` 블록(JSON embed 제외)은 사용하지 않는다.
> 모든 `<script src>` 태그는 반드시 `<head>`에 선언한다.
> 데이터는 `fetch()` 없이 HTML에 직접 임베드한다.

---

## 진입 라우팅

| 최종 산출물 | 담당 스킬 |
|---|---|
| 화면 요구사항·흐름·컴포넌트 배치를 설명하는 Markdown | `design-prototype-docs` |
| `.docs/prototype/` 아래 검증용 HTML/CSS/JS/JSON | `create-prototype` |
| 실제 앱 디렉터리에 반영할 제품 코드 | `frontend-design` |

프로토타입은 요구사항 검증을 위한 폐기 가능한 산출물이다. 사용자가 실제 앱 적용을
요청하면 이 스킬로 비슷한 코드를 만든 뒤 복사하지 말고 `frontend-design`으로
handoff한다.

---

## 워크플로우

직접 호출할 때는 Codex에서 `$create-prototype`, Claude Code에서
`/ai-agent-harness:create-prototype`를 사용한다. 스킬이 호출되면 먼저 사용자
메시지에서 아래 4가지를 사전 추출한다.

| 항목 | 추출 기준 |
|---|---|
| PREFIX | `[A-Z]+-NNN` 패턴 포함 여부 (예: `SFR-018`, `REQ-005`, `UC-012`) — 없으면 기본값 `SFR` |
| 번호 | PREFIX와 결합된 숫자 부분 |
| 기능 설명 | 메시지에 화면 기능 설명이 있는가 |
| 메인 색상 | HEX 코드 또는 색상명 포함 여부 |

추출된 항목은 해당 STEP을 건너뛴다.
**4개가 모두 추출되면 STEP 1~3을 건너뛰고 STEP 4로 진입한다. STEP 4는 항상 실행한다.**

> PREFIX는 사용자가 명시한 값을 그대로 사용한다. 이후 모든 파일명, 디렉토리명, HTML title에 `{PREFIX}-{번호}` 형태로 반영한다.

---

### STEP 0 — 플랫폼·실행 방식 확인 + 프로젝트 유형 확인

#### STEP 0-A — 플랫폼·실행 방식 확인

`prompts/parallel-setup.md`의 [플랫폼 확인] → [모델 목록 표시] → [실행 방식 선택 — 선호도만 저장] 절차를 따른다.

병렬 선호 시: 화면 목록은 STEP 2에서 확정된다.
화면 목록 확정 후 STEP 4에서 작업 목록을 제시하고 `prompts/parallel-setup.md`의 [모델 확정] 절차를 실행한다.

순차 선택 시 STEP 1로 직접 진행한다.

#### STEP 0-B — 프로젝트 유형 확인 (C-1 확인 단계)

프로토타입 산출물 저장 위치를 확정하기 위해 **반드시** 아래를 수행한다.

1. 현재 수행 위치에서 프로젝트 구조를 탐색한다 (git repo 경계, 하위 앱 폴더 후보 스캔).
2. **단일 애플리케이션 프로젝트**인지 **복수 애플리케이션 프로젝트**인지 판정한다.
3. 판정 결과 + 적용 대상을 사용자에게 **반드시 재확인**한다.

#### STEP 0-C — 사용자 이름 확인

`git config user.name`으로 현재 git 계정을 탐색하고, **반드시** 사용자에게 확인한다.

---

### STEP 1 — 요구사항 번호 수집 (미제공 시에만 질문)

사용자에게 해당 화면의 **요구사항 번호**를 물어본다.

- 기본 PREFIX: `SFR` — 사용자가 다른 prefix를 사용하면 그것을 그대로 따른다
- 형식 규칙: `{PREFIX}-001` (영어 대문자 + 하이픈 + 숫자, 자릿수는 프로젝트 관례 따름)
- 복수 화면: `{PREFIX}-001&002` 형태로 `&`로 결합
- HTML `<title>`에도 반영: `{PREFIX}-001 — {프로젝트명} 화면 예시`

> "이 화면의 요구사항 번호를 알려주세요. (예: SFR-001, REQ-005, UC-012 등 프로젝트에서 쓰는 번호로 알려주세요. 복수이면 & 로 결합: SFR-001&002)"

---

### STEP 2 — 화면 기능구성 + 와이어프레임 수집 (미제공 시에만 질문)

1. **화면의 기능구성** — 텍스트로 설명 (어떤 기능이 있는지, 주요 영역이 뭔지)
2. **와이어프레임 또는 화면 영역 구분** — PPT, 이미지, 손그림 사진 등 무엇이든 OK

이미지가 첨부되면 레이아웃 구조, 영역 배치, 주요 컴포넌트를 파악한다.

> "화면의 기능구성을 설명해주세요. 그리고 대략적인 와이어프레임이나 화면 영역 구분 이미지(PPT, 스크린샷, 손그림 등)가 있으면 함께 첨부해주세요."

---

### STEP 3 — 메인 색상 수집 (미제공 시에만 질문)

- HEX 코드(`#2563EB`) 또는 색상명("네이비", "초록") 모두 OK
- 나머지 팔레트는 `references/color-system.md`를 읽고 자동 생성

> "디자인의 메인 색상을 알려주세요. (예: #2563EB, 또는 '네이비', '초록' 등)"

---

### STEP 4 — 병렬 분할 단위 및 모델 확정 (항상 실행)

STEP 0에서 선호도를 저장했으면 그 결과를 사용한다. 그렇지 않으면 여기서 실행 방식을 묻는다.

**병렬 선택 시** 아래 작업 목록을 제시한다:

| # | 작업 | 담당 |
|---|------|------|
| 1 | screen-{슬러그} | 화면명-HTML+CSS+JS+JSON 일체 |
| … | … | … (화면 수만큼 행 추가) |

분할 단위를 먼저 확인한다:

> "화면이 여러 개면 화면 단위로 병렬화할까요?
> 화면 1개를 한 작업 단위로 묶어 HTML+CSS+JS+JSON을 함께 생성합니다."

HTML 구조, 화면별 CSS, JS, JSON은 서로 의존하므로 파일 종류별로 나누지 않는다.

이후 `prompts/parallel-setup.md`의 [모델 확정] 절차를 따른다.

**순차 선택 시** 메인 에이전트가 화면을 하나씩 순서대로 생성한다.

---

### STEP 5 — HTML 프로토타입 생성

수집한 정보를 종합하여 프로토타입 파일을 생성한다.

**생성 전 반드시 아래 파일들을 읽는다:**
1. `references/html-template.md` — HTML 골격, CSS/JS 파일 분리 구조, 데이터 임베드 패턴
2. `references/color-system.md` — 메인 색상에서 전체 팔레트 파생 규칙
3. `examples/SFR-018.html` — 디자인 품질 기준 (상위 ~35줄 색상 변수 + 필요한 영역만 선택 읽기)

#### 산출물 디렉토리 구조

```text
{PREFIX}-001/
├── display/                              ← 모든 HTML
│   ├── {PREFIX}-001-entry.html
│   ├── {PREFIX}-001-list.html
│   └── {PREFIX}-001-detail.html
├── data/                                 ← 모든 JSON (원본 보관용)
│   ├── {PREFIX}-001-entry-data.json
│   ├── {PREFIX}-001-list-data.json
│   └── {PREFIX}-001-detail-data.json
├── css/                                  ← 공통 CSS + 화면별 CSS
│   ├── {PREFIX}-001.css                  ← 공통 (모든 HTML이 참조)
│   ├── {PREFIX}-001-entry.css            ← 진입화면 전용
│   ├── {PREFIX}-001-list.css             ← 목록화면 전용
│   └── {PREFIX}-001-detail.css           ← 상세화면 전용
├── script/                               ← 공통 JS + 화면별 JS
│   ├── {PREFIX}-001-common.js            ← 공통 (선택, 공유 함수가 있을 때만)
│   ├── {PREFIX}-001-entry.js             ← 진입화면 전용 (HTML과 1:1 짝)
│   ├── {PREFIX}-001-list.js              ← 목록화면 전용 (HTML과 1:1 짝)
│   └── {PREFIX}-001-detail.js            ← 상세화면 전용 (HTML과 1:1 짝)
└── docs/                                 ← reverse design, 목업 문서 등
```

> **HTML-파일 짝 규칙**: 화면 1개는 반드시 아래 4개 파일을 함께 생성한다.
> - `display/{PREFIX}-001-{slug}.html`
> - `css/{PREFIX}-001-{slug}.css`
> - `script/{PREFIX}-001-{slug}.js`
> - `data/{PREFIX}-001-{slug}-data.json`

#### CSS 분리 규칙

| 종류 | 경로 | 내용 |
|---|---|---|
| 공통 CSS | `css/{PREFIX}-001.css` | `:root` 변수, 리셋, `.btn`, `.card`, `.page-nav` 등 전체 공통 스타일 |
| 화면별 CSS | `css/{PREFIX}-001-{slug}.css` | 해당 화면 전용 레이아웃만, 화면마다 1개 필수 |

- **`<style>` 블록 전면 금지**: HTML 내부에 `<style>` 태그를 작성하지 않는다
- **인라인 `style=""` 원칙적 금지**: 모든 스타일은 CSS 파일에 클래스로 정의한다. `style=""` 속성은 JS로 동적으로 값을 주입하는 경우처럼 CSS 파일로 표현이 불가능한 경우에만 허용한다

#### JS 분리 규칙

| 종류 | 경로 | 내용 |
|---|---|---|
| 공통 JS | `script/{PREFIX}-001-common.js` | 여러 화면이 공유하는 함수·유틸리티 (선택, 필요할 때만) |
| 화면별 JS | `script/{PREFIX}-001-{slug}.js` | `renderData()`, 이벤트 핸들러 등 해당 화면 전용 로직 |

- **HTML 내부 `<script>` 블록 금지**: `<script type="application/json" id="page-data">` 태그 하나만 허용
- 모든 JS 로직은 `script/` 폴더의 파일에 작성
- **모든 `<script src>` 태그는 반드시 `<head>`에 선언** — body 끝 또는 body 중간 배치 금지

#### 자산 참조 경로

`display/` 기준 상대경로를 사용한다:

```html
<head>
  <!-- 공통 CSS -->
  <link rel="stylesheet" href="../css/{PREFIX}-001.css">
  <!-- 화면별 CSS -->
  <link rel="stylesheet" href="../css/{PREFIX}-001-{slug}.css">
  <!-- 공통 JS (선택 — 없으면 이 줄 전체 제거) -->
  <script src="../script/{PREFIX}-001-common.js"></script>
  <!-- 화면별 JS (항상) -->
  <script src="../script/{PREFIX}-001-{slug}.js"></script>
</head>
```

> **`DOMContentLoaded` 필수**: 모든 화면별 JS 파일은 반드시 `document.addEventListener('DOMContentLoaded', ...)` 안에서 DOM을 조작한다.
> `<script src>`가 `<head>`에 있어 DOM보다 먼저 선언되므로, `DOMContentLoaded` 없이 즉시 실행하면 DOM이 아직 없어 에러가 발생한다.

#### 네비게이션 링크

`display/` 안의 파일끼리 이동이므로 파일명만 쓴다:

```html
<nav class="page-nav">
  <div class="logo">{프로젝트명} <span>DEMO</span></div>
  <a class="tab-btn active" href="{PREFIX}-001-entry.html">진입화면</a>
  <a class="tab-btn" href="{PREFIX}-001-list.html">목록</a>
  <a class="tab-btn" href="{PREFIX}-001-detail.html">상세</a>
</nav>
```

#### 데이터 — JSON 임베드 방식 (fetch 금지)

더미 데이터는 `<script type="application/json" id="page-data">` 태그로 HTML에 직접 임베드한다.
`fetch()`를 사용하지 않으므로 `file://` 직접 열기가 가능하다.

**HTML 내 JSON 임베드 (`display/{PREFIX}-001-entry.html`):**
```html
<body>
  <!-- 콘텐츠 영역 -->
  <div id="card-container"></div>

  <!-- JSON 데이터 임베드 — 유일하게 허용되는 <script> 태그 -->
  <script type="application/json" id="page-data">
  {
    "cards": [
      { "icon": "📩", "title": "전자민원 접수·응대", "count": 24, "badge": "신규 5건" },
      { "icon": "📝", "title": "서면민원 답변 생성", "count": 12, "badge": "" }
    ]
  }
  </script>
</body>
```

**화면별 JS 파일 (`script/{PREFIX}-001-entry.js`):**
```javascript
// ── 진입화면 JS ──
document.addEventListener('DOMContentLoaded', () => {
  const data = JSON.parse(document.getElementById('page-data').textContent);
  renderData(data);
});

function renderData(data) {
  const container = document.getElementById('card-container');
  const fragment = document.createDocumentFragment();

  for (const card of Array.isArray(data.cards) ? data.cards : []) {
    const item = document.createElement('button');
    item.type = 'button';
    item.className = 'list-card';

    const icon = document.createElement('span');
    icon.className = 'list-card__icon';
    icon.textContent = String(card.icon ?? '');

    const title = document.createElement('h3');
    title.textContent = String(card.title ?? '');

    item.append(icon, title);
    item.addEventListener('click', () => alert(String(card.title ?? '')));
    fragment.append(item);
  }

  container.replaceChildren(fragment);
}
```

위 예시의 `.list-card__icon` 시각 속성은 화면별 CSS 파일에 정의한다.
임베드한 JSON을 포함한 모든 데이터는 신뢰하지 않는다. 동적 DOM은 `createElement`,
`textContent`, `replaceChildren`, `addEventListener`로 구성하며 `innerHTML`,
`outerHTML`, `insertAdjacentHTML`, `document.write`, 인라인 `on*` 핸들러를 쓰지 않는다.

> **data/ 폴더 JSON 유지**: HTML에 임베드하더라도 `data/{PREFIX}-001-{slug}-data.json`은 삭제하지 않는다.
> 원본 보관·diff 검토·재구성 목적으로 항상 유지한다.

---

#### 병렬 생성 (서브에이전트 사용 시)

**반드시 아래 순서를 따른다.**

##### Phase 1 — 공통 파일 먼저 생성 (메인 에이전트 담당)

서브에이전트 실행 전에 메인 에이전트가 먼저 생성한다:

1. `css/{PREFIX}-001.css` — 공통 CSS (`:root` 변수, 모든 공통 컴포넌트)
2. `script/{PREFIX}-001-common.js` — 공통 JS (공유 함수가 있을 때만)

> 공통 CSS의 `:root` 변수가 확정되어야 각 서브에이전트가 화면별 CSS를 올바르게 작성할 수 있다.
> Phase 1 완료 전에 서브에이전트를 실행하지 않는다.

##### Phase 2 — 화면별 파일 병렬 생성 (서브에이전트 담당)

**분할 단위: 화면 단위 (권장)**

서브에이전트 1개 = 화면 1개 담당:
- `display/{PREFIX}-001-{slug}.html`
- `css/{PREFIX}-001-{slug}.css`
- `script/{PREFIX}-001-{slug}.js`
- `data/{PREFIX}-001-{slug}-data.json`

각 서브에이전트에 전달하는 정보:
- 담당 화면의 기능 설명
- 4개 파일명 (HTML / CSS / JS / JSON)
- Phase 1에서 생성된 공통 CSS의 `:root` 변수 전체 (텍스트로 전달)
- nav 구조 (파일명 목록, active 탭 위치)
- `references/html-template.md` 경로
- 이 문서의 "HTML 생성 핵심 규칙" 섹션 요약

**분할 단위: 파일 종류별**

사용자가 선택한 경우에만:
- HTML·JS 담당 에이전트: `display/{slug}.html` + `script/{slug}.js`
- CSS 담당 에이전트: `css/{slug}.css`
- JSON 담당 에이전트: `data/{slug}-data.json`

> 파일 종류별 분할 시 에이전트 간 의존성에 주의: HTML·JS 에이전트가 CSS 클래스명을 먼저 확정하고, CSS 에이전트에 전달해야 한다.

##### Phase 3 — Self-check (메인 에이전트)

모든 서브에이전트 완료 후 메인 에이전트가 STEP 6 Self-check를 수행한다.

---

### 파일 저장

프로젝트 유형(STEP 0-B)과 사용자(STEP 0-C)에 따라 산출물 디렉토리 위치를 결정한다:

- **단일 앱**: `.docs/prototype/{사용자}/{PREFIX}-{번호}/` 하위에 생성
- **복수 앱**: `.docs/prototype/{사용자}/{PREFIX}-{번호}/` 하위에 생성 (앱 구분 없이 프로젝트 공통)

예시 (단일앱):
```
.docs/prototype/developer/SFR-019/
├── display/
├── data/
├── css/
├── script/
└── docs/
```

- 같은 경로에 디렉토리가 이미 존재하면 **갱신 여부를 사용자에게 확인**한다.
- 저장 디렉토리가 없으면 생성한다.

---

## HTML 생성 핵심 규칙

### 파일 기본 설정

- `lang="ko"`, 한글 UI
- Google Fonts: `Noto Sans KR` (본문) + `JetBrains Mono` (코드/숫자)
- **Tailwind CSS CDN**: `<script src="https://cdn.tailwindcss.com"></script>` — `<head>` 맨 앞에 배치
- CSS 변수(`:root`)로 색상 체계 관리 — Tailwind 유틸리티는 **보조**로만 사용
- **CSS-first 원칙** — 모든 스타일은 `css/` 폴더의 파일에 클래스로 정의한다. `<style>` 블록과 인라인 `style` 속성, 인라인 `on*` 이벤트 속성을 금지한다.
- **HTML 내 `<script>` 블록 금지** — `<script type="application/json" id="page-data">` 하나만 허용
- **모든 `<script src>` 는 `<head>`에 선언** — `<head>` 선언 순서: Tailwind CDN → 공통 CSS → 화면별 CSS → 공통 JS (선택) → 화면별 JS
- **동적 상태도 클래스 우선** — 상태는 검증된 클래스 allowlist로 전환한다. 불가피한 수치형 값은 범위·형식을 검증한 뒤 미리 정의한 CSS custom property 하나에만 `style.setProperty`로 설정한다.
- **JSON 임베드 안전성** — JSON 직렬화 결과의 `<`를 `\u003c`로 이스케이프해 `</script>` 종료를 막고, 읽을 때는 `textContent` + `JSON.parse`만 사용한다.

### Tailwind 사용 원칙

- 레이아웃 보조: `flex`, `gap-*`, `p-*`, `mt-*`, `grid`, `w-full` 등
- 텍스트 보조: `text-sm`, `font-bold`, `truncate` 등
- **색상은 항상 CSS 변수와 CSS 클래스 사용** — 예: `.status-primary { color: var(--primary); }`
- Tailwind의 색상 유틸리티(text-blue-500 등)는 사용하지 않는다
- 핵심 컴포넌트(.btn, .card, .sidebar 등)는 CSS 파일에 커스텀 CSS로 정의

### 디자인 시스템

- CSS 변수(`:root`)로 전체 색상 관리 (color-system.md 참조)
- 13px 기본 폰트, `line-height: 1.5`
- 카드/패널: `border-radius: 8~12px`, 미세한 `box-shadow`
- 버튼 클래스: `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-green`
- 스크롤바 커스텀, fadeIn 애니메이션, hover 트랜지션

### 레이아웃 패턴

| 패턴 | 용도 | 구조 |
|---|---|---|
| 앱 셸 | 업무 화면 | 사이드바 + 메인 + 우측패널 |
| 목록 화면 | 데이터 조회 | 검색바 + 그리드/테이블 |
| 대시보드 | 현황 요약 | 상단 카드 + 하단 차트/테이블 |
| 진입 화면 | 메뉴 선택 | 중앙 정렬 카드 버튼 |
| 폼 화면 | 데이터 입력 | 라벨 + 입력필드 + 제출 |

### 인터랙션

- 화면 이동: `<a href="파일명.html">` 상대경로 링크 (다중 화면)
- 화면 내 탭: `showScreen(id, btn)` 함수 — 화면별 JS 파일에 작성
- 모달: `.modal-overlay` + `.modal-box` — CSS는 화면별 CSS에, 함수는 화면별 JS에
- 사이드 패널: `.slide-panel` — CSS는 화면별 CSS에, `togglePanel()`은 화면별 JS에
- 호버 효과: `transition: all .2s`
- 더미 데이터: `<script type="application/json" id="page-data">` 임베드, 한국어, 사실적으로
- 미구현 기능: `alert('XX 기능은 준비중입니다.')`

---

## 참조 파일

| 파일 | 내용 | 언제 읽는가 |
|---|---|---|
| `references/html-template.md` | HTML 골격, CSS/JS 파일 분리 구조, 데이터 임베드 패턴 | STEP 5 시작 시 반드시 |
| `references/color-system.md` | 메인 색상 → 전체 팔레트 파생 규칙 | STEP 3에서 색상 확정 후 |
| `examples/SFR-018.html` | 디자인 품질 기준 (화면 구성, 레이아웃, 색상 활용) | STEP 5에서 디자인 참고 |

> **레거시 예제 주의**: 보호 자산 `examples/SFR-018.html`은 구 방식의 단일 파일이며
> 인라인 스타일·이벤트 핸들러·문자열 기반 DOM 생성이 남아 있을 수 있다.
> 화면 구성과 시각 품질만 참고하고 코드 구조나 DOM 작성법은 복사하지 않는다.
> 생성 시 항상 `--primary`, `--primary-light`, `--primary-mid`, `--nav-bg` 변수명을 사용한다.

---

## STEP 6 — Self-check (생성 직후 필수)

모든 파일에 대해 아래 항목을 순서대로 확인하고, 문제가 있으면 즉시 수정한다.

| 확인 항목 | 기준 |
|---|---|
| 디렉토리 구조 | `display/`, `data/`, `css/`, `script/`, `docs/` 5개 서브디렉토리가 존재하는가 |
| HTML-파일 짝 완비 | 각 HTML에 대응하는 `css/{slug}.css`, `script/{slug}.js`, `data/{slug}-data.json` 4종이 모두 존재하는가 |
| Tailwind CDN | 모든 HTML의 `<head>` 맨 앞에 Tailwind CDN `<script>`가 있는가 |
| JS head 선언 | 모든 `<script src>` 태그가 `<head>` 안에 있는가 (body 안에 `<script src>` 없는가) |
| CSS 선언 순서 | `<head>` 내 CSS 순서: Tailwind CDN → 공통 CSS → 화면별 CSS |
| JS 선언 순서 | `<head>` 내 JS 순서: 공통 JS (선택) → 화면별 JS (CSS 뒤에 위치) |
| `<style>` 블록 없음 | 모든 HTML에 `<style>` 태그가 없는가 |
| 인라인 속성 없음 | `style` 속성과 `onclick` 등 인라인 `on*` 이벤트 속성이 모두 없는가 |
| HTML 내 `<script>` | `<body>` 안에 `<script type="application/json" id="page-data">` 외 다른 `<script>` 태그가 없는가 |
| DOMContentLoaded | 모든 화면별 JS 파일이 `document.addEventListener('DOMContentLoaded', ...)` 안에서 DOM을 조작하는가 |
| XSS sink 없음 | 데이터로 `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`를 호출하지 않는가 |
| 안전한 DOM 생성 | 동적 텍스트는 `textContent`, 이벤트는 `addEventListener`, 노드 교체는 `replaceChildren`을 사용하는가 |
| 안전한 JSON 임베드 | JSON 직렬화 시 `<`가 `\u003c`로 이스케이프되고 `textContent`로만 읽는가 |
| fetch() 없음 | 모든 파일에 `fetch(` 문자열이 없는가 |
| 데이터 임베드 | 각 HTML에 `<script type="application/json" id="page-data">` 가 존재하는가 |
| JSON 원본 보관 | `data/` 폴더에 각 화면에 대응하는 JSON 파일이 존재하는가 |
| CSS 경로 형식 | 모든 CSS `href`가 `../css/...` 형태인가 |
| JS 경로 형식 | 모든 JS `src`가 `../script/...` 형태인가 |
| 공통 JS 미사용 시 | 공통 JS가 없으면 `<script src="../script/{PREFIX}-001-common.js">` 줄이 HTML에 없는가 |
| CSS 변수 완비 | 공통 CSS의 `:root`에 `--primary`, `--primary-light`, `--primary-mid`, `--nav-bg` 4개 정의 |
| 변수 이름 오염 | `--blue`, `--blue-light` 같은 색상명 변수가 없는가 |
| 네비게이션 링크 | 다중 화면: 모든 `<a class="tab-btn">` href가 실제 존재하는 파일명과 일치하는가 |
| 현재 페이지 표시 | 각 HTML에서 자기 자신에 해당하는 탭에 `active` 클래스가 있는가 |
| 하드코딩 색상 | HEX 직접 입력 대신 CSS 변수 사용. hover에는 `filter: brightness(0.9)` |
| 모달 (해당 시) | 모달 `z-index`가 nav(100)보다 높은가. 닫기 함수가 연결돼 있는가 |

---

## 품질 기준

1. **실제 서비스처럼 보인다** — SFR-018.html 수준의 완성도
2. **더미 데이터가 사실적이다** — 한국어, 실제 업무 맥락에 맞는 이름/날짜/내용
3. **데스크탑에서 깨지지 않는다** — 최소 1280px 이상에서 정상 표시
4. **코드가 정리되어 있다** — `/* ── 섹션명 ── */` 주석으로 영역 구분
5. **인터랙티브하다** — 화면 이동, 모달, 호버, 패널 토글 등 동작
6. **file://에서 바로 열린다** — fetch() 없이 임베드 방식
7. **Live Server에서 완벽 동작** — 링크 이동, JSON 로드, 모든 JS가 정상 실행
