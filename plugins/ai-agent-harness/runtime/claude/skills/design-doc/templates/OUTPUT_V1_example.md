# 🚄 Acro — 범용 예약 매크로 + AI 자동 적응 시스템

> **사용자가 1회 예약 행위를 시연하면 AI가 매크로를 설정하고, 사이트 변경 시 자동 복구까지 처리하는 범용 자동화 플랫폼**
> `Playwright · BeautifulSoup4 · LangChain · LangGraph · Ollama · FastAPI · React · PostgreSQL · Docker`

---

## 01. 개요

스케일: **프로젝트 전체**

예약 사이트마다 DOM 구조가 달라 기존엔 수동으로 예약해야 했다. 이 시스템은 **사용자가 1회 시연하고 요소별 힌트를 주면 AI가 매크로 설정을 자동 생성**하고, 이후엔 완전 자동으로 예약을 실행한다. 사이트 구조가 변경되면 크롤러가 감지하고 LangGraph 에이전트가 자동 복구를 시도한다. **어떤 예약 사이트든 `site_name` 기준으로 독립적으로 관리**할 수 있는 범용 구조를 목표로 하되, 코레일·SRT 2개 사이트로 먼저 검증한다.

핵심 설계 결정:
- **사용자 힌트 방식 온보딩** — AI가 클릭 요소의 역할을 추론하고, 사용자가 확인/수정. 요소 이름을 하드코딩하지 않아 어떤 사이트든 동일한 플로우로 처리
- **크롤링 선행 + 매크로 분리** — 매크로 실행 전 BeautifulSoup4로 DOM 변경을 먼저 확인. 이상 없으면 바로 실행, 변경 감지 시 LangGraph 에이전트로 에스컬레이션
- **AI 심각도 이중 분기** — 셀렉터 값만 바뀐 경우 자동 수정 / 예약 플로우 자체가 바뀐 경우 운영자에게 재온보딩 요청
- **LLM 교체 가능 구조** — 현재 Ollama(로컬)이지만 클라우드 모델로 전환 가능하도록 `chain.py`에서 추상화

---

## 02. 핵심 흐름

### 🟦 흐름 A — 온보딩 (사이트 최초 1회)

### STEP A-1 · 사이트 등록
**운영자가 Web UI에서 사이트명 + URL을 입력하고 브라우저 열기**
`FastAPI` · `React`

`sites` 테이블에 저장되고 온보딩 화면으로 진입.

```
사이트 이름 : [ korail ]
사이트 URL  : [ https://korail.com ]  [ 브라우저 열기 → ]
```

↓

### STEP A-2 · 가상 브라우저 열기 + 직접 로그인
**Playwright가 Xvfb 가상 화면에 브라우저를 띄우고 noVNC로 스트리밍**
`Playwright (headless=False)` · `Xvfb` · `noVNC`

사용자는 `:6080`에 접속해 평소처럼 직접 로그인 → 예약 화면까지 이동. 로그인 자동화 불필요, 세션(쿠키)만 `{site_name}_session.json`으로 자동 저장.

↓

### STEP A-3 · 요소 클릭 + HTML 수집
**"셀렉터 등록 시작" 클릭 후 예약에 필요한 요소를 순서대로 클릭**
`Playwright` · `capture.py`

클릭마다 HTML 정보(tag, id, class, placeholder, 주변 텍스트, selector)를 자동 수집. 몇 개를 클릭할지 사전에 정하지 않음 — 사용자가 필요한 만큼 클릭하고 "등록 완료" 클릭.

↓

### STEP A-4 · AI 역할 추론 + 사용자 확인
**LangChain + Ollama가 HTML 맥락 보고 역할명 추론 → WebSocket으로 실시간 전달**
`LangChain` · `Ollama` · `WebSocket`

| ✅ 추론 성공 | ⚠️ 추론 불확실 |
|---|---|
| 역할명 자동 제안 → 사용자 확인 | "확인 필요" 표시 → 사용자 직접 입력 |

추론 결과 UI 예시:

| # | AI 추론 이름 | 셀렉터 | 상태 |
|---|---|---|---|
| 1 | 출발역 입력칸 | `#dpt_stn_nm` | ✅ 확인 |
| 2 | 도착역 입력칸 | `#arv_stn_nm` | ✅ 확인 |
| 3 | 여행 날짜 | `.date-picker` | ✏️ 수정중 |
| 4 | 조회 버튼 | `#search_btn` | ✅ 확인 |

↓

### STEP A-5 · 저장 완료
**확정된 요소 이름 + 셀렉터 + 실행 순서를 DB에 저장**
`FastAPI` · `SQLAlchemy`

`sites.is_onboarded = true`로 갱신. 이후 매크로 자동 실행 가능 상태.

---

### 🟩 흐름 B — 매크로 실행

### STEP B-1 · 크롤링 + DOM 변경 확인
**매크로 실행 전 예약 페이지 HTML 수집 → 이전 스냅샷과 비교**
`requests` · `BeautifulSoup4` · `difflib` · `SQLAlchemy`

`dom_snapshots` 테이블의 `page_hash`(MD5)와 현재 HTML을 비교. 변경 없으면 바로 매크로 실행, 변경 감지 시 LangGraph 에이전트 호출.

| ✅ 이상 없음 | ❌ 변경 감지 |
|---|---|
| 매크로 바로 실행 (STEP B-2) | AI 복구 에이전트 호출 (흐름 C) |

↓

### STEP B-2 · 매크로 자동 실행
**저장된 세션 + 셀렉터로 Playwright가 순서대로 예약 수행**
`Playwright` · `playwright-stealth` · `macro/engine.py`

`selectors.element_order` 순서대로 요소를 찾아 클릭/입력. 세션 만료 감지 시 운영자에게 재로그인 알림.

↓

### STEP B-3 · 결과 전달
**예약 성공/실패, 변경 감지 로그, AI 수정 내역을 대시보드에 실시간 표시**
`FastAPI` · `WebSocket` · `React`

---

### 🟥 흐름 C — 변경 감지 + AI 자동 복구

### STEP C-1 · 심각도 판단
**LangGraph 에이전트가 변경된 HTML을 분석하고 심각도를 판단**
`LangGraph` · `LangChain` · `Ollama` · `ai/agent.py`

| 🔧 자동 수정 (셀렉터 값만 변경) | ⚠️ 재온보딩 요청 (플로우 자체 변경) |
|---|---|
| AI가 새 셀렉터 찾아서 DB 업데이트 → 매크로 자동 재시도 → 운영자에게 변경 내역 알림 | 예약 단계 자체가 바뀐 경우 → 운영자 알림 + 재온보딩 요청 플래그 설정 |

↓

### STEP C-2 · 복구 시도 (자동 수정 경로)
**에이전트가 새 DOM에서 기존 역할에 맞는 셀렉터를 반복 추론 + 검증**
`LangGraph` · `Playwright`

최대 시도 횟수(기본 3회) 초과 시 재온보딩 경로로 에스컬레이션.

↓

### STEP C-3 · 결과 처리
**복구 성공 → DB 업데이트 + 운영자 알림 / 복구 실패 → 운영자 알림 + 재온보딩**
`FastAPI` · `SQLAlchemy`

알림 방식: 미정 (이메일 / Slack / 앱 내 알림)

---

## 03. 집중 로직

### 3-A. 온보딩 — 클릭 감지 → AI 역할 추론 → 실시간 전달

Playwright 이벤트 리스너가 클릭마다 HTML 정보를 수집하고, FastAPI WebSocket을 통해 LangChain 추론 결과를 프론트에 실시간으로 전달한다. 사용자는 추론 결과를 확인하거나 수정 후 저장.

```python
# capture.py — 클릭 요소 HTML 정보 수집
element_info = {
    "tag": "input",
    "id": "dpt_stn_nm",
    "class": "station-input",
    "placeholder": "출발지",
    "nearby_text": "출발",   # el.closest('label')?.innerText
    "selector": "#dpt_stn_nm"
}

# chain.py — LangChain 프롬프트 + LLM 추상화
prompt = f"""
아래는 사용자가 클릭한 HTML 요소 정보입니다.
{element_info}

이 요소의 역할을 한국어로 간단하게 추론해주세요.
예시: 출발역 입력칸, 날짜 선택, 조회 버튼
한 줄로만 답하세요. 확실하지 않으면 "확인 필요"라고 답하세요.
"""
# → AI 응답 예시: "출발역 입력칸"

# main.py — WebSocket으로 추론 결과 실시간 전달
@app.websocket("/ws/onboarding/{site_name}")
async def onboarding_ws(websocket: WebSocket, site_name: str):
    await websocket.accept()
    async for click_data in receive_clicks(websocket):
        element_name = await llm_chain.ainvoke(build_prompt(click_data))
        await websocket.send_json({
            "element": click_data,
            "suggested_name": element_name,
            "status": "confirmed" if element_name != "확인 필요" else "needs_review"
        })
```

---

### 3-B. 크롤링 → DOM 변경 감지

매크로 실행 전 매번 수행. MD5 해시로 빠르게 변경 여부를 1차 판단. 해시가 다르면 `difflib`로 상세 비교하여 어떤 셀렉터가 사라졌는지 파악.

```python
# crawler/crawler.py — HTML 수집
import requests, hashlib
from bs4 import BeautifulSoup

def fetch_page(url: str, session_cookies: dict) -> tuple[str, str]:
    response = requests.get(url, cookies=session_cookies)
    html = response.text
    page_hash = hashlib.md5(html.encode()).hexdigest()
    return html, page_hash

# ai/detector.py — 이전 스냅샷과 비교
import difflib

def detect_changes(old_html: str, new_html: str, stored_selectors: list[str]) -> dict:
    diff = list(difflib.unified_diff(
        old_html.splitlines(), new_html.splitlines(), lineterm=""
    ))
    missing = [sel for sel in stored_selectors if sel not in new_html]
    return {
        "has_change": bool(diff),
        "missing_selectors": missing,
        "severity": "minor" if missing else "major"  # 에이전트에서 재판단
    }
```

---

### 3-C. LangGraph 복구 에이전트 — 심각도 판단 + 자동 수정

변경 감지 이후 핵심 로직. 에이전트가 현재 DOM을 분석해 심각도를 판단하고, 자동 수정 가능하면 새 셀렉터를 추론·검증·저장한다. 불가능하면 운영자에게 에스컬레이션.

**⚠️ DOM 토큰 절약 필수** — 전체 HTML을 그대로 LLM에 넘기면 토큰 초과. `missing_selectors` 주변 영역만 추출하거나 3,000자로 잘라서 전달.

```python
# ai/agent.py — LangGraph 복구 에이전트
from langgraph.graph import StateGraph
from typing import TypedDict

class RecoveryState(TypedDict):
    site_name: str
    dom_snapshot: str          # 현재 페이지 HTML (3,000자 제한)
    missing_selectors: list    # [{element_name, old_selector}]
    severity: str              # "minor" | "major"
    candidates: list           # LLM 제안 후보
    recovered: list
    failed: list
    attempt_count: int

def judge_severity(state: RecoveryState):
    """LLM이 DOM을 보고 플로우 변경 여부 판단"""
    prompt = f"""
    기존 셀렉터가 사라짐: {state['missing_selectors']}
    현재 DOM(일부): {state['dom_snapshot'][:3000]}
    판단: 셀렉터 값만 바뀐 것(minor) vs 예약 플로우 자체 변경(major)?
    JSON으로만: {{"severity": "minor" or "major", "reason": "..."}}
    """
    parsed = parse_json(llm.invoke(prompt))
    return {**state, "severity": parsed["severity"]}

def find_new_selectors(state: RecoveryState):
    """LLM이 새 DOM에서 기존 역할에 맞는 셀렉터 후보 제안"""
    prompt = f"""
    현재 DOM(일부): {state['dom_snapshot'][:3000]}
    역할에 맞는 CSS 셀렉터를 찾아주세요: {state['missing_selectors']}
    JSON으로만: [{{"element_name": "...", "selector": "..."}}]
    """
    return {**state, "candidates": parse_json(llm.invoke(prompt))}

def verify_selectors(state: RecoveryState):
    """Playwright로 후보 셀렉터 실존 여부 검증"""
    recovered, failed = [], []
    for c in state["candidates"]:
        exists = page.locator(c["selector"]).count() > 0
        (recovered if exists else failed).append(c)
    return {**state, "recovered": recovered, "failed": failed,
            "attempt_count": state["attempt_count"] + 1}

def route_after_verify(state: RecoveryState):
    if state["severity"] == "major":    return "escalate"
    if not state["failed"]:             return "save"
    if state["attempt_count"] >= 3:     return "escalate"
    return "retry"

# 그래프 구성
graph = StateGraph(RecoveryState)
graph.add_node("judge",   judge_severity)
graph.add_node("find",    find_new_selectors)
graph.add_node("verify",  verify_selectors)
graph.add_node("save",    save_and_notify)    # DB 업데이트 + 운영자 알림
graph.add_node("escalate", alert_and_flag)   # 운영자 알림 + is_onboarded=false

graph.set_entry_point("judge")
graph.add_edge("judge", "find")
graph.add_edge("find",  "verify")
graph.add_conditional_edges("verify", route_after_verify, {
    "retry":    "find",
    "save":     "save",
    "escalate": "escalate"
})
```

복구 성공: `selectors` 업데이트 + `last_verified` 갱신 + 운영자 알림
복구 실패 / major: 운영자 알림 + `sites.is_onboarded = false` 플래그

---

## 04. 프로젝트 구조

```
acro/
├── be/
│   ├── main.py                   # FastAPI 진입점
│   ├── .env                      # 환경변수 (커밋 금지)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── start.sh                  # Xvfb → x11vnc → noVNC → uvicorn 기동
│   │
│   ├── onboarding/
│   │   ├── browser.py            # Playwright headless=False + Xvfb 실행
│   │   ├── capture.py            # 클릭 요소 HTML 정보 수집 + 셀렉터 추출
│   │   └── session.py            # 세션(쿠키) 저장/로드
│   │
│   ├── crawler/
│   │   ├── crawler.py            # HTML 수집 (requests + bs4)
│   │   └── parser.py             # 셀렉터 파싱
│   │
│   ├── macro/
│   │   ├── engine.py             # Playwright 실행, 예약 흐름
│   │   └── selector.py           # DB에서 셀렉터 로드
│   │
│   ├── ai/
│   │   ├── agent.py              # LangGraph 복구 에이전트 (핵심)
│   │   ├── detector.py           # difflib DOM 변경 비교
│   │   └── chain.py              # LangChain + Ollama 체인 (LLM 추상화)
│   │
│   └── db/
│       ├── database.py           # SQLAlchemy + asyncpg 연결
│       └── models.py             # 테이블 모델 정의
│
├── fe/
│   ├── Dockerfile
│   └── src/pages/
│       ├── Dashboard.jsx         # 메인 대시보드 + 실시간 로그
│       ├── Onboarding.jsx        # 사이트 등록 온보딩
│       ├── Reservation.jsx       # 예약 조건 설정
│       └── Sites.jsx             # 등록된 사이트 관리
│
└── docker-compose.yml
```

---

## 05. 데이터 구조

### `sites` — 등록된 사이트 관리

| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | SERIAL PK | |
| site_name | VARCHAR UNIQUE | korail / srt 등 |
| site_url | VARCHAR | 예약 시작 URL |
| is_onboarded | BOOLEAN | 온보딩 완료 여부 |
| last_crawled | TIMESTAMPTZ | 마지막 크롤링 시각 |
| created_at | TIMESTAMPTZ | |

### `selectors` — 요소 셀렉터 + 역할명

| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | SERIAL PK | |
| site_name | VARCHAR | FK → sites.site_name |
| element_name | VARCHAR | AI 추론 결과 (사용자 수정 가능) |
| selector | VARCHAR | CSS / XPath |
| element_order | INTEGER | 매크로 실행 순서 |
| element_type | VARCHAR | input / button / select |
| last_verified | TIMESTAMPTZ | 복구 성공 시 갱신 |
| is_active | BOOLEAN | 변경 감지 후 비활성화 가능 |

### `sessions` — 로그인 세션

| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | SERIAL PK | |
| site_name | VARCHAR | FK → sites.site_name |
| session_path | VARCHAR | 쿠키 파일 경로 |
| expires_at | TIMESTAMPTZ | 만료 시 재로그인 알림 트리거 |
| is_valid | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

### `dom_snapshots` — DOM 변경 감지용 스냅샷

| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | SERIAL PK | |
| site_name | VARCHAR | FK → sites.site_name |
| page_hash | VARCHAR | MD5 — 빠른 변경 1차 감지 |
| snapshot_html | TEXT | 전체 HTML 저장 |
| created_at | TIMESTAMPTZ | |

### `reservations` — 예약 조건 설정

| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | SERIAL PK | |
| site_name | VARCHAR | FK → sites.site_name |
| departure | VARCHAR | 출발지 |
| destination | VARCHAR | 도착지 |
| travel_date | VARCHAR | |
| seat_type | VARCHAR | |
| is_active | BOOLEAN | |

---

## 06. 라이브러리 및 외부 구성

### 05-A · 백엔드

#### 크롤링
| 라이브러리 | 설명 | 비고 |
|------------|------|------|
| `requests` | HTTP 요청, HTML 수집 | Playwright와 역할 분리 — 가볍게 DOM 수집만 |
| `beautifulsoup4` | HTML 파싱, 요소 추출 | |
| `lxml` | 빠른 HTML 파서 | bs4 백엔드 |
| `difflib` | DOM 변경 비교 | Python 내장 |

#### 브라우저 자동화
| 라이브러리 | 설명 | 비고 |
|------------|------|------|
| `playwright` | 온보딩 + 매크로 실행 | 온보딩: headless=False, 매크로: headless=True |
| `playwright-stealth` | 봇 감지 우회 | 코레일 필수 — 없으면 차단 |

#### AI / 에이전트
| 라이브러리 | 설명 | 비고 |
|------------|------|------|
| `langchain` | 프롬프트 체인 구성 | |
| `langgraph` | 복구 에이전트 상태 그래프 | 반복 시도 + 분기 처리 |
| `langchain-community` | Ollama 연동 | |
| `ollama` | 로컬 LLM 클라이언트 | 클라우드 전환 대비 chain.py에서 추상화 |

#### API / DB
| 라이브러리 | 설명 | 비고 |
|------------|------|------|
| `fastapi` | REST API + WebSocket | |
| `uvicorn` | ASGI 서버 | |
| `pydantic` | 데이터 검증 | |
| `python-dotenv` | 환경변수 관리 | |
| `sqlalchemy` | ORM (async) | |
| `asyncpg` | 비동기 PostgreSQL 드라이버 | |
| `psycopg2-binary` | 동기 드라이버 | Alembic 마이그레이션용 |

---

### 05-B · 프론트엔드

#### UI / 통신
| 라이브러리 | 설명 | 비고 |
|------------|------|------|
| `react + vite` | UI + 빌드 도구 | |
| `axios` | API 통신 | |
| `react-router-dom` | 페이지 라우팅 | |
| `tailwindcss` | 스타일링 | 비개발자도 쓰는 UI — 단순하게 |

---

### 05-C · 외부 구성 요소

| 이름 | 종류 | 역할 | 비고 |
|------|------|------|------|
| `postgres:16` | Docker 이미지 | 메인 DB | |
| `ollama/ollama` | Docker 이미지 | 로컬 LLM 서버 | 최초 1회 `ollama pull llama3.2` 필요 (~2GB) |
| `Xvfb` | OS 패키지 (apt) | 가상 모니터 생성 | 컨테이너 내 GUI 온보딩 핵심 |
| `x11vnc` | OS 패키지 (apt) | 가상 화면 VNC 공유 | |
| `noVNC` | 외부 프로그램 (git clone) | 웹브라우저로 VNC 접속 | pip websockify와 함께 사용 |
| `websockify` | OS 패키지 / pip | noVNC ↔ VNC 프록시 | |

---

## 07. 주의사항

> ⚠️ **법적 주의** — 코레일·SRT는 이용약관에서 자동화 프로그램을 금지합니다. 개인 학습 목적, 본인 계정에서만 사용할 것. 상업적 이용·티켓 재판매는 형사처벌 대상.

> 🛡️ **playwright-stealth 필수** — 코레일은 봇 감지를 하고 있음. `playwright-stealth` 없이 실행하면 차단될 수 있음.

> 🛡️ **세션 파일 관리** — 쿠키 파일(`{site_name}_session.json`)은 `.gitignore`에 반드시 포함. 유출 시 계정 탈취 가능.

> ⚠️ **noVNC 보안** — `:6080` 포트는 온보딩 구간에만 열 것. 완료 후 `headless=True`로 전환하고 noVNC 연결 종료. 운영 환경에서는 비밀번호 설정 또는 로컬호스트 전용으로 제한.

> ⚠️ **LLM 토큰 한도** — DOM 전체를 LLM에 넘기면 토큰 초과. 복구 에이전트에서 DOM을 3,000자 이내로 자르거나 `missing_selectors` 주변 영역만 추출하는 전처리 필수.

> 💡 **세션 만료 처리** — 저장된 세션이 만료되면 FastAPI + WebSocket으로 운영자에게 재로그인 알림을 실시간 전송.

> 💡 **LLM 교체 가능성** — `chain.py`에서 LLM 클라이언트를 추상화. `OllamaLLM`을 직접 호출하지 말고 래퍼 레이어를 둘 것. Ollama → 클라우드 전환 시 `chain.py`만 수정하면 됨.

> 💡 **dom_snapshots 용량** — `snapshot_html`이 TEXT라 장기 운영 시 용량 증가. 최신 N개만 보존하는 정리 로직 필요.

---

## 08. 부가 정보

### 🐳 배포 환경 (Docker)

| 컨테이너 | 역할 | 포트 |
|----------|------|------|
| `acro-frontend` | React + Vite Web UI | `5173` |
| `acro-backend` | FastAPI + Playwright + Xvfb + noVNC | `8000`, `6080` |
| `acro-ai` | Ollama (Llama 3.2) | `11434` |
| `acro-db` | PostgreSQL 16 | 내부 `5432` |

주요 환경변수:
```
DISPLAY                  : Xvfb 가상 디스플레이 번호 (:99)
OLLAMA_HOST              : http://acro-ai:11434
DATABASE_URL             : postgresql+asyncpg://acro:secret@acro-db:5432/acrodb
MAX_RECOVERY_ATTEMPTS    : LangGraph 복구 최대 시도 횟수 (기본값: 3)
```

가상 디스플레이 스택 (`acro-backend` 내부):
```
Xvfb   → 가상 모니터 생성 (:99)
x11vnc → 화면을 VNC로 공유 (5900)
noVNC  → 웹브라우저로 VNC 접속 (6080)
```

최초 실행:
```bash
docker compose up -d
docker compose exec acro-ai ollama pull llama3.2   # 최초 1회, 약 2GB
# Web UI  : http://localhost:5173
# FastAPI : http://localhost:8000
# noVNC   : http://localhost:6080
```

### DB

SQLAlchemy + Alembic으로 마이그레이션 관리.
`selectors.last_verified`로 복구 이력 추적.
`dom_snapshots`는 주기적으로 오래된 데이터 정리 필요 (`snapshot_html`이 TEXT라 용량 주의).

### VSCode 익스텐션

| 익스텐션 | 이유 |
|----------|------|
| Python + Pylance | 타입 힌트, 자동완성 |
| Python Debugger | 중단점, 변수 추적 |
| indent-rainbow | 들여쓰기 색상 구분 |
| ES7+ React Snippets | React 단축 코드 |
| Tailwind IntelliSense | 클래스 자동완성 |
| Thunder Client | FastAPI 엔드포인트 테스트 |
| SQLite Viewer | DB 내용 GUI 확인 |
| Prettier | 코드 자동 정렬 |
| GitLens | Git 히스토리 추적 |

---

## 09. 열린 결정 사항

| 항목 | 옵션 | 우선순위 |
|------|------|----------|
| 운영자 알림 방식 | 이메일 / Slack / 앱 내 알림 | 결정 필요 |
| 매크로 실행 트리거 | 수동 실행 / 스케줄(cron) 자동 실행 | 결정 필요 |
| AI 추론 실패 fallback | 빈칸 vs "확인 필요" 표시 후 사용자 입력 | 결정 필요 (현재 후자 권장) |
| DOM 전처리 전략 | 3,000자 cut vs missing_selectors 주변 영역만 추출 | 결정 필요 |
| dom_snapshots 보존 기간 | 최신 N개만 유지 vs 전체 보존 | 나중에 |
| Ollama 모델 선택 | llama3.2 / mistral / qwen2.5 | 나중에 |
| 요소 클릭 취소 / 순서 변경 UX | 드래그 vs 삭제 후 재클릭 | 나중에 |
