# HTML Template — 프로토타입 기본 골격

이 파일은 프로토타입 HTML의 기본 구조를 정의한다.
모든 프로토타입은 이 골격을 기반으로 확장한다.

---

## 파일 짝 규칙

화면 1개 = 4개 파일을 반드시 함께 생성한다.

```text
display/{PREFIX}-001-{slug}.html   ← HTML 구조 + JSON 데이터 임베드
css/{PREFIX}-001-{slug}.css        ← 화면 전용 CSS
script/{PREFIX}-001-{slug}.js      ← 화면 전용 JS (renderData, 이벤트 핸들러)
data/{PREFIX}-001-{slug}-data.json ← JSON 원본 보관용
```

공통 파일 (병렬 생성 시 Phase 1에서 먼저 생성):
```text
css/{PREFIX}-001.css               ← 공통 CSS (모든 HTML이 참조)
script/{PREFIX}-001-common.js      ← 공통 JS (선택, 공유 함수가 있을 때만)
```

---

## 기본 `<head>` 구조

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{PREFIX}-001-{slug} — {프로젝트명} 화면 예시</title>

<!-- 폰트 -->
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<!-- Tailwind CSS CDN — 폰트 링크 이후, CSS 링크 이전에 배치 -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- 공통 CSS -->
<link rel="stylesheet" href="../css/{PREFIX}-001.css">
<!-- 화면별 CSS -->
<link rel="stylesheet" href="../css/{PREFIX}-001-{slug}.css">

<!-- 공통 JS (선택 — 공유 함수 없으면 이 줄 전체 제거) -->
<script src="../script/{PREFIX}-001-common.js"></script>
<!-- 화면별 JS (항상 포함) -->
<script src="../script/{PREFIX}-001-{slug}.js"></script>

<!-- <style> 블록 사용 금지 — 모든 CSS는 위 CSS 파일에 클래스로 정의 -->
<!-- 인라인 style="" 원칙적 금지 — JS 동적 주입 등 불가피한 경우만 허용 -->
</head>
```

> **JS는 모두 `<head>`에 선언한다.**
> JS 파일 내부에서 `DOMContentLoaded`를 사용하면 `<head>` 선언이어도 DOM 준비 후 실행이 보장된다.
> `<body>` 안에 `<script src>` 태그를 쓰지 않는다.

> **공통 JS가 없을 때**: `<script src="../script/{PREFIX}-001-common.js">` 줄을 완전히 제거한다.
> 존재하지 않는 파일을 참조하면 콘솔 에러가 발생한다.

---

## 필수 CSS 클래스 정의

CSS는 **공통 파일**과 **화면별 파일** 두 종류로 분리한다.

### 공통 CSS 파일 — `css/{PREFIX}-001.css`

모든 HTML이 이 파일 하나를 `<link rel="stylesheet">`로 참조한다.
병렬 생성 시 서브에이전트 실행 전에 메인 에이전트가 먼저 생성한다.

```css
/* ── CSS 변수 (color-system.md 참조) ── */
:root {
  --bg: #F4F6F9;
  --surface: #FFFFFF;
  --surface2: #EEF1F6;
  --border: #D8DDE8;
  --primary: {메인색상};
  --primary-light: {파생};
  --primary-mid: {파생};
  --nav-bg: {파생};
  --sky: #0EA5E9;
  --sky-light: #E0F2FE;
  --green: #16A34A;
  --green-light: #DCFCE7;
  --orange: #EA580C;
  --orange-light: #FFF7ED;
  --purple: #7C3AED;
  --purple-light: #F3E8FF;
  --red: #EF4444;
  --red-light: #FEE2E2;
  --amber: #F59E0B;
  --text-primary: #111827;
  --text-secondary: #4B5563;
  --text-muted: #9CA3AF;
  --sidebar-w: 260px;
  --header-h: 52px;
}

/* ── 리셋 ── */
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Noto Sans KR', sans-serif;
  background: var(--bg);
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.5;
}

/* ── 상단 내비게이션 탭 (다중 화면용) ── */
.page-nav {
  position: sticky; top: 0; z-index: 100;
  background: var(--nav-bg);
  display: flex; align-items: center; gap: 4px;
  padding: 0 20px; height: 36px;
  box-shadow: 0 2px 8px rgba(0,0,0,.18);
}
.page-nav .logo {
  font-size: 13px; font-weight: 700; color: #fff;
  margin-right: 24px; white-space: nowrap;
  display: flex; align-items: center; gap: 8px;
}
.page-nav .logo span {
  background: var(--sky); color: #fff;
  border-radius: 4px; padding: 2px 7px; font-size: 11px;
}
.tab-btn {
  border: none; background: transparent; cursor: pointer;
  color: rgba(255,255,255,.6); font-family: inherit;
  font-size: 12.5px; font-weight: 500;
  padding: 6px 14px; border-radius: 6px;
  transition: all .2s;
  text-decoration: none;
}
.tab-btn:hover { background: rgba(255,255,255,.1); color: #fff; }
.tab-btn.active { background: var(--primary); color: #fff; }

/* ── 화면 ── */
.screen {
  display: flex; flex-direction: column;
  height: calc(100vh - 36px); overflow: hidden;
}

/* ── 화면 라벨 바 ── */
.screen-label {
  background: var(--nav-bg); color: #fff;
  padding: 4px 24px;
  font-size: 11px; font-weight: 600;
  display: flex; align-items: center; gap: 12px;
  flex-shrink: 0;
}
.screen-label .badge {
  background: var(--sky); color: #fff;
  border-radius: 4px; padding: 2px 8px; font-size: 10.5px;
}
.screen-label .sub { color: rgba(255,255,255,.6); font-weight: 400; }

/* ── 앱 셸 ── */
.app-shell { display: flex; flex: 1; overflow: hidden; }

/* ── 사이드바 ── */
.sidebar {
  width: var(--sidebar-w); min-width: var(--sidebar-w);
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  overflow-y: auto;
}
.sidebar-section { padding: 8px 0; border-bottom: 1px solid var(--border); }
.sidebar-section:last-child { border-bottom: none; flex: 1; }
.sidebar-heading {
  font-size: 10.5px; font-weight: 700; letter-spacing: .05em;
  color: var(--text-muted); text-transform: uppercase;
  padding: 6px 14px 4px;
}
.sidebar-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 14px;
  font-size: 12px; color: var(--text-secondary);
  cursor: pointer; transition: background .15s;
}
.sidebar-item:hover { background: var(--primary-light); color: var(--primary); }
.sidebar-item.active { background: var(--primary-light); color: var(--primary); font-weight: 600; }

/* ── 메인 콘텐츠 ── */
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

/* ── 상단 바 ── */
.topbar {
  height: 32px; min-height: 32px;
  background: var(--surface); border-bottom: 1px solid var(--border);
  display: flex; align-items: center; padding: 0 16px; gap: 12px;
  font-size: 11.5px;
}
.topbar .meta-badge {
  background: var(--primary-light); color: var(--primary);
  border-radius: 5px; padding: 3px 8px; font-weight: 600; font-size: 11.5px;
}

/* ── 버튼 ── */
.btn {
  border: none; border-radius: 7px; cursor: pointer;
  font-family: inherit; font-size: 12px; font-weight: 600;
  padding: 7px 14px; transition: all .15s;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-primary { background: var(--primary); color: #fff; }
.btn-primary:hover { filter: brightness(0.9); }
.btn-secondary { background: var(--surface2); color: var(--text-secondary); }
.btn-secondary:hover { background: var(--border); }
.btn-green { background: var(--green); color: #fff; }
.btn-green:hover { filter: brightness(0.9); }
.btn-icon { background: var(--surface2); color: var(--text-secondary); padding: 7px 10px; }

/* ── 입력 필드 ── */
.input-field {
  width: 100%; padding: 8px 12px;
  border: 1px solid var(--border); border-radius: 6px;
  font-family: inherit; font-size: 13px;
  background: var(--surface); outline: none;
  transition: border-color .2s;
}
.input-field:focus { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-light); }

/* ── 카드 ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px; padding: 16px;
  box-shadow: 0 2px 6px rgba(0,0,0,.02);
}

/* ── 태그/뱃지 ── */
.tag { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.chip { font-size: 10px; font-weight: 600; padding: 1px 6px; border-radius: 10px; }

/* ── 데이터 테이블 ── */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left; padding: 8px 12px;
  font-size: 11px; font-weight: 600; color: var(--text-muted);
  border-bottom: 2px solid var(--border); background: var(--surface2);
}
.data-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 13px; }
.data-table tr:hover { background: var(--primary-light); }

/* ── 검색 바 ── */
.search-bar {
  width: 100%; padding: 14px 20px 14px 48px; font-size: 15px;
  border: 1px solid var(--border); border-radius: 8px;
  font-family: inherit; margin-bottom: 20px;
  background: var(--surface); outline: none;
  box-shadow: 0 2px 6px rgba(0,0,0,0.02); transition: border-color 0.2s;
}
.search-bar:focus { border-color: var(--primary); }

/* ── 목록 카드 ── */
.grid-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.list-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 24px;
  display: flex; flex-direction: column; cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
}
.list-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); border-color: var(--primary-mid); }

/* ── 스크롤바 ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

/* ── 애니메이션 ── */
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

/* ── 반응형 (최소한) ── */
@media (max-width: 900px) { .sidebar { width: 160px; min-width: 160px; } }
```

### 화면별 CSS 파일 — `css/{PREFIX}-001-{slug}.css`

해당 화면에만 쓰이는 레이아웃과 컴포넌트만 작성한다.
공통 CSS에 이미 있는 클래스(`.btn`, `.card` 등)는 재정의하지 않는다.

```css
/* ── {slug} 화면 전용 레이아웃 ── */

.split-layout {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
  flex: 1;
}

.status-running { background: var(--sky-light); color: var(--sky); }
.status-done    { background: var(--green-light); color: var(--green); }
```

---

## 필수 JavaScript

### JS 로딩 순서 규칙

```
<head> 선언 순서:
  1. Tailwind CDN          — 동기 로드
  2. 공통 JS (있을 때만)   — 동기 로드
  3. 화면별 JS             — 동기 로드

실행 순서 (DOMContentLoaded 사용 시):
  HTML 파싱 → JS 파일 로드+실행(함수 정의) → DOM 파싱 완료 → DOMContentLoaded 발생
  → 화면별 JS의 DOMContentLoaded 리스너 실행 → renderData() 호출
```

> **`DOMContentLoaded`를 반드시 사용한다.**
> `<script src>`가 `<head>`에 있으면 DOM보다 먼저 파싱된다.
> `DOMContentLoaded` 없이 즉시 `document.getElementById(...)`를 호출하면 `null`을 반환한다.

### 화면별 JS 파일 — `script/{PREFIX}-001-{slug}.js`

각 HTML에 짝지어진 JS 파일. `renderData()`와 화면 전용 이벤트 핸들러를 모두 여기에 작성한다.

```javascript
// ── {slug} 화면 JS ──
// script/{PREFIX}-001-{slug}.js

document.addEventListener('DOMContentLoaded', () => {
  // JSON 데이터 읽기 — HTML의 <script type="application/json" id="page-data">에서 가져옴
  const data = JSON.parse(document.getElementById('page-data').textContent);
  renderData(data);
});

function renderData(data) {
  const container = document.getElementById('card-container');
  container.innerHTML = data.cards.map(card => `
    <div class="list-card" onclick="alert('${card.title}')">
      <div style="font-size:28px;">${card.icon}</div>
      <h3>${card.title}</h3>
      <p>${card.desc}</p>
    </div>
  `).join('');
}

// 화면 전용 이벤트 핸들러 (필요 시)
function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) {
  if (id) document.getElementById(id).classList.remove('active');
  else document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
}
function togglePanel(name) {
  document.querySelector('[data-panel="' + name + '"]').classList.toggle('active');
}
```

### 공통 JS 파일 — `script/{PREFIX}-001-common.js` (선택)

여러 화면이 실제로 공유하는 함수가 있을 때만 생성한다.
없으면 파일 자체를 만들지 않고, HTML의 `<script src>` 참조도 제거한다.

```javascript
// ── 공통 유틸리티 ──
// script/{PREFIX}-001-common.js

// 예: 날짜 포맷 유틸 (여러 화면에서 공통 사용)
function formatDate(dateStr) {
  const d = new Date(dateStr);
  return `${d.getFullYear()}.${String(d.getMonth()+1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')}`;
}

// 예: 상태 배지 색상 매핑
function getStatusClass(status) {
  const map = { '완료': 'status-done', '처리중': 'status-running', '대기': 'status-pending' };
  return map[status] || '';
}
```

---

## 화면 유형별 body 구조

HTML `<body>` 안에는 콘텐츠 마크업과 `<script type="application/json">` 태그만 존재한다.
`<script src>` 및 로직 `<script>` 태그는 모두 `<head>`에 선언되어 있으므로 `<body>` 안에 쓰지 않는다.

### 유형 A: 다중 화면 (링크 이동)

```html
<!-- display/{PREFIX}-001-entry.html -->
<body>
  <nav class="page-nav">
    <div class="logo">{프로젝트명} <span>DEMO</span></div>
    <a class="tab-btn active" href="{PREFIX}-001-entry.html">진입화면</a>
    <a class="tab-btn" href="{PREFIX}-001-list.html">목록</a>
    <a class="tab-btn" href="{PREFIX}-001-detail.html">상세</a>
  </nav>

  <div class="screen" style="height:calc(100vh - 36px); overflow:auto;">
    <div id="card-container"><!-- script/{PREFIX}-001-entry.js 가 renderData()로 채움 --></div>
  </div>

  <!-- JSON 데이터 임베드 — body 안에서 유일하게 허용되는 <script> 태그 -->
  <script type="application/json" id="page-data">
  {
    "cards": [
      { "icon": "📩", "title": "전자민원 접수", "desc": "AI 기반 민원 분석", "count": 24 }
    ]
  }
  </script>
</body>
```

### 유형 B: 단일 화면 (앱 셸)

```html
<body>
  <div class="screen" style="height:100vh;">
    <div class="screen-label">
      <span class="badge">{PREFIX}-001</span> {화면 설명}
    </div>
    <div class="app-shell">
      <aside class="sidebar"><!-- 사이드바 --></aside>
      <main class="main">
        <div id="data-container"><!-- renderData()가 채움 --></div>
      </main>
    </div>
  </div>

  <script type="application/json" id="page-data">
  { "items": [] }
  </script>
</body>
```

### 유형 C: 단일 화면 (목록/대시보드)

```html
<body style="background: var(--bg);">
  <div style="padding: 30px 40px; max-width: 1200px; margin: 0 auto;">
    <h1 style="font-size:20px; font-weight:700; margin-bottom:20px;">{화면명}</h1>
    <div id="data-container"><!-- renderData()가 채움 --></div>
  </div>

  <script type="application/json" id="page-data">
  { "rows": [] }
  </script>
</body>
```

---

## 모달 패턴

CSS는 화면별 CSS 파일에, JS 함수는 화면별 JS 파일에 작성한다.

```css
/* css/{PREFIX}-001-{slug}.css 에 작성 */
.modal-overlay {
  display: none; position: fixed; top: 0; left: 0;
  width: 100%; height: 100%;
  background: rgba(0,0,0,0.5); z-index: 1000;
  align-items: center; justify-content: center;
}
.modal-overlay.active { display: flex; }
.modal-box { background: var(--surface); width: 600px; max-width: 90%; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
.modal-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg); }
.modal-body { padding: 24px 20px; overflow-y: auto; }
.modal-footer { padding: 16px 20px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; background: var(--bg); }
```

```html
<!-- display/{PREFIX}-001-{slug}.html body 안 -->
<div id="myModal" class="modal-overlay" onclick="if(event.target===this)closeModal()">
  <div class="modal-box">
    <div class="modal-header">
      <h3 style="font-size:16px; font-weight:700;">제목</h3>
      <button onclick="closeModal()" style="background:transparent; border:none; font-size:20px; cursor:pointer; color:var(--text-muted);">&times;</button>
    </div>
    <div class="modal-body">내용</div>
    <div class="modal-footer">
      <button class="btn btn-primary" onclick="closeModal()">확인</button>
    </div>
  </div>
</div>
```

```javascript
// script/{PREFIX}-001-{slug}.js 에 작성
function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) {
  if (id) document.getElementById(id).classList.remove('active');
  else document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
}
```

---

## 슬라이드 패널 패턴

```css
/* css/{PREFIX}-001-{slug}.css 에 작성 */
.slide-panel {
  width: 320px; min-width: 320px; background: var(--surface);
  border-left: 1px solid var(--border);
  display: none; flex-direction: column; overflow-y: auto;
}
.slide-panel.active { display: flex; }
```

```javascript
// script/{PREFIX}-001-{slug}.js 에 작성
function togglePanel(name) {
  document.querySelector('[data-panel="' + name + '"]').classList.toggle('active');
}
```

---

## 주석 컨벤션

```css
/* ── 섹션명 ─────────────────────────────── */
```

```html
<!-- ═══════ 화면 이름 ═══════ -->
```

```javascript
// ── 섹션명 ──
```
