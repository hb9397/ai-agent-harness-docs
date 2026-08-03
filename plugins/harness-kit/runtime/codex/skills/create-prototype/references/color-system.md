# Color System — 메인 색상에서 전체 팔레트 파생

사용자가 메인 색상 하나를 제공하면, 이 문서의 규칙에 따라 전체 CSS 변수 팔레트를 생성한다.

---

## CSS 변수 전체 목록

```css
:root {
  /* ── 배경 & 서피스 (항상 고정) ── */
  --bg:             #F4F6F9;
  --surface:        #FFFFFF;
  --surface2:       #EEF1F6;
  --border:         #D8DDE8;

  /* ── 메인 색상 (사용자 지정에서 파생) ── */
  --primary:        {메인색상};           /* 사용자가 준 값 그대로 */
  --primary-light:  {메인색상 밝은 변형};   /* HSL lightness 95~97% */
  --primary-mid:    {메인색상 중간 변형};   /* HSL lightness 75~85% */

  /* ── 내비게이션 바 (메인색상의 어두운 변형) ── */
  --nav-bg:         {메인색상 어두운 변형}; /* HSL sat 30~50%, lightness 15~25% */

  /* ── 보조 색상 (항상 고정 — 상태 표시용) ── */
  --sky:            #0EA5E9;
  --sky-light:      #E0F2FE;
  --green:          #16A34A;
  --green-light:    #DCFCE7;
  --orange:         #EA580C;
  --orange-light:   #FFF7ED;
  --purple:         #7C3AED;
  --purple-light:   #F3E8FF;
  --red:            #EF4444;
  --red-light:      #FEE2E2;
  --amber:          #F59E0B;

  /* ── 텍스트 (항상 고정) ── */
  --text-primary:   #111827;
  --text-secondary: #4B5563;
  --text-muted:     #9CA3AF;

  /* ── 레이아웃 (필요에 따라 조정) ── */
  --sidebar-w:      260px;
  --header-h:       52px;
}
```

---

## 메인 색상별 파생값 레퍼런스

사용자가 제공할 수 있는 주요 색상과 그에 맞는 파생값 예시:

### 파랑 (Blue) 계열
```css
--primary:       #2563EB;
--primary-light: #EFF6FF;
--primary-mid:   #BFDBFE;
--nav-bg:        #1E3A5F;
```

### 네이비 (Navy) 계열
```css
--primary:       #1E40AF;
--primary-light: #EFF6FF;
--primary-mid:   #93C5FD;
--nav-bg:        #0F1D3D;
```

### 초록 (Green) 계열
```css
--primary:       #16A34A;
--primary-light: #F0FDF4;
--primary-mid:   #BBF7D0;
--nav-bg:        #14532D;
```

### 빨강 (Red) 계열
```css
--primary:       #DC2626;
--primary-light: #FEF2F2;
--primary-mid:   #FECACA;
--nav-bg:        #450A0A;
```

### 보라 (Purple) 계열
```css
--primary:       #7C3AED;
--primary-light: #F5F3FF;
--primary-mid:   #DDD6FE;
--nav-bg:        #2E1065;
```

### 주황 (Orange) 계열
```css
--primary:       #EA580C;
--primary-light: #FFF7ED;
--primary-mid:   #FED7AA;
--nav-bg:        #431407;
```

### 틸 (Teal) 계열
```css
--primary:       #0D9488;
--primary-light: #F0FDFA;
--primary-mid:   #99F6E4;
--nav-bg:        #134E4A;
```

### 인디고 (Indigo) 계열
```css
--primary:       #4F46E5;
--primary-light: #EEF2FF;
--primary-mid:   #C7D2FE;
--nav-bg:        #1E1B4B;
```

---

## 파생 알고리즘

메인 색상의 HEX → HSL 변환 후:
1. **--primary-light**: H 유지, S를 60~80%로 낮추고, L을 95~97%로 올림
2. **--primary-mid**: H 유지, S를 50~70%로 낮추고, L을 75~85%로 올림
3. **--nav-bg**: H 유지(±10도 허용), S를 30~50%로 낮추고, L을 15~25%로 낮춤

위 레퍼런스 표에 없는 색상은 이 알고리즘으로 직접 계산한다.

---

## 색상명 → HEX 변환 가이드

사용자가 색상명으로 줄 때의 기본 매핑:

| 색상명 | HEX |
|---|---|
| 파란색, 파랑, 블루 | #2563EB |
| 네이비 | #1E40AF |
| 하늘색, 스카이 | #0EA5E9 |
| 초록, 그린 | #16A34A |
| 빨강, 레드 | #DC2626 |
| 보라, 퍼플 | #7C3AED |
| 주황, 오렌지 | #EA580C |
| 틸, 청록 | #0D9488 |
| 인디고, 남색 | #4F46E5 |
| 핑크, 분홍 | #EC4899 |
| 노랑, 옐로우 | #EAB308 |
| 검정, 블랙 | #1F2937 |

---

## 버튼 색상 체계

버튼 CSS 클래스(`.btn-primary`, `.btn-secondary`, `.btn-green` 등)는 `html-template.md`에 정의되어 있다. 색상은 항상 CSS 변수를 사용하며, hover는 `filter: brightness(0.9)`로 처리한다.
