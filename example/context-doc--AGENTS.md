<!-- 산출물 예시 메타 -->
> 📂 **산출물 예시 — `context-doc` 스킬 (AGENTS.md)**  
> 산출 경로: 프로젝트 루트 `AGENTS.md` (복수 앱은 루트 통합 인덱스)  
> 현행 기준에서 `AGENTS.md`는 프로젝트 컨텍스트 정본입니다. Claude용 `CLAUDE.md`는 같은 본문을 중복하지 않고 `@AGENTS.md` bridge로 연결합니다.

---

# ACRO Backend — Agent Guide (AGENTS.md)

> Adaptive Crawler RObot | Backend Context  
> Python + FastAPI + PostgreSQL 기반 Agent 참조용 문서 (Codex·공용 Agent 진입점, CLAUDE.md와 동일 내용)

---

## 1️⃣ Context (프로젝트 맥락)

### 프로젝트 개요
- ACRO는 열차 예약 사이트(코레일, SRT 등)를 자동 예약하는 매크로 시스템의 **백엔드**
- FastAPI 서버이며 크롤링 / 온보딩 / 매크로 / AI 4개 모듈을 포함
- 사용자 직접 로그인 세션을 저장하고 Playwright가 이를 이어받아 자동 예약 수행
- 사이트 구조 변경 시 LangGraph 에이전트가 셀렉터를 자동 수정
- Podman Compose 환경에서 `localhost:8000`(API), `localhost:6080`(noVNC) 으로 접근

### 기술 스택

| 분류 | 라이브러리 | 버전 |
|---|---|---|
| API 프레임워크 | fastapi | 최신 |
| ASGI 서버 | uvicorn | 최신 |
| 실시간 통신 | websockets | 최신 |
| 매크로 | playwright | 최신 |
| CDP 탐지 우회 | patchright | 최신 |
| 봇 감지 우회 | playwright-stealth | 최신 |
| HTTP 클라이언트 | requests | 최신 |
| HTML 파싱 | beautifulsoup4 | 최신 |
| HTML 파서 | lxml | 최신 |
| AI 체인 | langchain | 최신 |
| AI 에이전트 | langgraph | 최신 |
| Ollama 연동 | langchain-ollama | 최신 |
| LLM 클라이언트 | ollama | 최신 |
| ORM | sqlalchemy | 최신 |
| 비동기 DB 드라이버 | asyncpg | 최신 |
| 동기 DB 드라이버 | psycopg2-binary | 최신 |
| 데이터 검증 | pydantic | 최신 |
| 환경변수 | python-dotenv | 최신 |

### 아키텍처

```
acro/
└── be/
    ├── main.py                  # FastAPI 진입점, 라우터 등록, WebSocket
    ├── .env.development         # 개발 환경변수 (노출 금지)
    ├── .env.production          # 배포 환경변수 (노출 금지)
    ├── requirements.txt
    ├── Dockerfile
    ├── start.sh                 # Xvfb → x11vnc → noVNC → uvicorn 기동 스크립트
    │
    ├── routers/                 # 도메인별 API 라우터 분리
    │   ├── __init__.py
    │   ├── site.py              # /sites 엔드포인트
    │   ├── onboarding.py        # /onboarding, /selectors 엔드포인트
    │   ├── reservation.py       # /reservations 매크로 예약 CRUD
    │   └── settings.py          # /settings/human-mode 런타임 토글
    │
    ├── onboarding/              # 온보딩 모듈 — 사이트 최초 등록
    │   ├── browser.py           # patchright headless=False + Xvfb(:99) 실행 (CDP 탐지 우회)
    │   ├── capture.py           # 클릭 요소 HTML 정보 수집 + 셀렉터 추출
    │   └── session.py           # 세션(쿠키) 저장 / 로드
    │
    ├── crawler/                 # 크롤링 모듈 — 변경 감지용
    │   ├── crawler.py           # requests로 HTML 수집
    │   └── parser.py            # BeautifulSoup 셀렉터 파싱
    │
    ├── macro/                   # 매크로 엔진
    │   ├── engine.py            # patchright 자동 예약 실행
    │   ├── selector.py          # DB에서 셀렉터 로드 / 저장
    │   └── human_behavior.py    # 인간형 행동 모듈 (랜덤딩레이·타이핑·스크롤)
    │
    ├── ai/                      # AI 모듈
    │   ├── agent.py             # LangGraph 에이전트 (핵심)
    │   ├── detector.py          # difflib DOM 변경 비교
    │   └── chain.py             # LangChain + Ollama 체인
    │
    └── db/
        ├── database.py          # SQLAlchemy + asyncpg 비동기 연결 설정
        └── models.py            # 테이블 모델 정의
```

### 메인 로직 흐름

```
[STEP 1] 온보딩 (최초 1회)
  사용자가 직접 브라우저에서 로그인 + 예약 화면 이동
  → 세션(쿠키) 자동 저장
  → 사용자가 요소들을 클릭
  → AI(LangChain)가 각 요소 이름 추론
  → 사용자가 확인 or 수정
  → DB에 셀렉터 + 이름 저장

[STEP 2] 크롤링
  매크로 실행 전 예약 페이지 HTML 수집
  → dom_snapshots 테이블과 MD5 해시 비교

[STEP 3] DB 비교
  변경 없음 → STEP 4 (매크로 실행)
  변경 감지 → AI 에이전트 호출 (LangGraph)
    셀렉터만 변경 → DB 자동 수정 → 재시도
    구조 변경  → FE에 WebSocket 알림 → 사용자 재온보딩

[STEP 4] 매크로 실행
  저장된 세션으로 예약 화면 진입
  → DB 셀렉터로 자동 예약 수행
  → 세션 만료 시 FE에 SESSION_EXPIRED 알림

[STEP 5] 결과 전달
  FastAPI WebSocket (`/ws`, `/ws/onboarding`)으로 FE에 실시간 상태 및 요소 전달
```

### 온보딩 상세 흐름

온보딩은 새 사이트를 최초 등록할 때 1회만 수행한다.  
로그인은 사용자가 직접 하므로 로그인 관련 셀렉터 등록은 불필요하다.

```
1. FE에서 사이트 이름 + URL 입력 → POST /onboarding/start
2. browser.py : Playwright headless=False로 Xvfb 가상 화면에 브라우저 실행
   → 배포: 컨테이너 내 Xvfb(:99) 가상 모니터에 브라우저가 뜸
            사용자는 http://localhost:6080 (noVNC) 접속 or FE iframe으로 조작
   → 개발: 로컬 PC 모니터에 직접 브라우저 창이 열림
3. 사용자가 직접 로그인 + 예약 화면까지 이동
4. session.py : 세션(쿠키) 저장 → {site_name}_session.json
5. FE에서 "셀렉터 등록 시작" 클릭 → POST /onboarding/capture/start
6. capture.py : 사용자가 클릭하는 요소마다 HTML 정보 수집
   수집 항목: tag, id, class, placeholder, name, nearby_text, selector
7. chain.py : LangChain + Ollama로 요소 이름 추론
   프롬프트 예시: "이 HTML 요소의 역할을 한국어로 한 줄로 답하세요"
   응답 예시: "출발역 입력칸"
8. FE에 추론 결과 전송 → 사용자 확인 or 수정
9. 확정된 이름 + 셀렉터 → selectors 테이블에 저장
10. sites 테이블 is_onboarded = True 업데이트
```

> 💡 **browser.py — HEADLESS 환경변수로 분기**: `headless` 값을 코드에 하드코딩하지 않고 환경변수 `HEADLESS`로 읽어 처리한다. 개발 환경(`HEADLESS=false`)에서는 로컬 PC 모니터에 창이 직접 열리고, 배포 환경(`HEADLESS=false` + Xvfb)에서는 가상 모니터에 창이 열린다.
> ```python
> # onboarding/browser.py
> import os
> headless = os.getenv("HEADLESS", "false").lower() == "true"
> browser = await playwright.chromium.launch(headless=headless)
> ```

### AI 에이전트 역할 (LangGraph)

AI는 이 프로젝트에서 두 가지 역할을 한다.

**역할 1 — 온보딩: 요소 이름 추론**
- 담당 파일: `ai/chain.py`
- 입력: 클릭한 요소의 HTML 정보 (tag, id, class, placeholder, nearby_text 등)
- 출력: 요소 역할 이름 (한국어, 한 줄)
- 모델: Ollama (llama3.2, 로컬 실행)

**역할 2 — 운영 중: 셀렉터 자동 수정**
- 담당 파일: `ai/agent.py` (LangGraph), `ai/detector.py`, `ai/chain.py`
- LangGraph 노드: `detect_change` → `analyze_html` → `judge_severity` → `auto_fix` / `notify_human`
- 셀렉터 변경 → 자동 수정 후 DB 업데이트 / 구조 변경 → FE에 알림 → 재온보딩 요청

> ⚠️ **토큰 한도 주의**: DOM 전체를 LLM에 넘기면 토큰 초과. 3,000자 이내 컷팅 또는 `missing_selectors` 주변부 영역만 추출하는 전처리 필수.  
> 🔄 **복구 시도 제한**: `MAX_RECOVERY_ATTEMPTS` 환경변수(기본값 3)로 무한 루프 방지.

### API 엔드포인트 목록

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/sites` | 새 사이트 등록 |
| GET | `/sites` | 등록된 사이트 목록 |
| DELETE | `/sites/{site_name}` | 사이트 삭제 (CASCADE) |
| POST | `/onboarding/start` | 온보딩 브라우저 실행 |
| POST | `/onboarding/reset` | 온보딩 초기화 (셀렉터/세션 전체 삭제) |
| POST | `/onboarding/capture/start` | 셀렉터 캡처 시작 |
| POST | `/onboarding/capture/confirm` | AI 추론 결과 확인/수정 저장 |
| POST | `/reservations` | 매크로 예약 등록 (macro_name + priority) |
| GET | `/reservations` | 매크로 예약 목록 (`?site_name=korail`) |
| DELETE | `/reservations/{id}` | 매크로 예약 삭제 |
| PATCH | `/reservations/{id}/done` | 매크로 예약 성공 완료 처리 |
| GET | `/settings/human-mode` | 인간형 행동 모드 상태 조회 |
| POST | `/settings/human-mode` | 인간형 행동 모드 런타임 변경 |
| POST | `/macro/run` | 매크로 실행 |
| POST | `/macro/stop` | 매크로 중지 |
| GET | `/macro/status` | 매크로 현재 상태 |
| GET | `/selectors/{site_name}` | 특정 사이트 셀렉터 목록 |
| WS | `/ws/onboarding/{site_name}` | 온보딩 요소 실시간 스트리밍 |
| WS | `/ws` | 매크로 실시간 상태 추적 및 로그 스트림 |

### DB 테이블 (PostgreSQL)

| 테이블 | 용도 | 핵심 컬럼 |
|---|---|---|
| `sites` | 등록된 사이트 원장 | `site_name UNIQUE`, `is_onboarded (DEFAULT FALSE)`, `created_at` |
| `selectors` | 사이트별 CSS 셀렉터 | `site_name` (FK CASCADE), `element_name`, `element_order` (UNIQUE with site_name), `element_type` (action/available_indicator/success_indicator) |
| `sessions` | 로그인 세션(쿠키) | `site_name` (FK CASCADE), `session_path`, `is_valid (DEFAULT TRUE)` |
| `dom_snapshots` | HTML 스냅샷 (변경 감지) | `site_name` (FK CASCADE), `page_hash`, `snapshot_html`, `created_at` |
| `reservations` | 매크로 예약 (BE-M1 범용) | `site_name` (FK CASCADE), `macro_name`, `fill_overrides JSONB`, `priority`, `is_done (DEFAULT FALSE)`, `success_url_pattern` |

- 모든 테이블은 `site_name`으로 사이트별 데이터를 격리 (멀티 사이트 지원)
- PK: `SERIAL`, 문자열: `VARCHAR`, 시각: `TIMESTAMPTZ`
- 성능 최적화 인덱스: `dom_snapshots` (최신순 복합 인덱스), `selectors`/`reservations` (활성 상태 부분 인덱스)

---

## 2️⃣ Instruction
코드 작성에 있어서는 늘 아래 주제별 지침들을 준수한다.
@.docs/instruction/architecture-instruction.md
@.docs/instruction/code-style-instruction.md
@.docs/instruction/framework-instruction.md
@.docs/instruction/api-instruction.md
@.docs/instruction/agent-instruction.md

---

## 3️⃣ 실행 방법

### 방법 A — Podman Compose (배포 테스트)

```bash
# 전체 환경 한 번에 기동
podman compose up -d

# 접속 주소
# Web UI  : http://localhost:5173
# FastAPI  : http://localhost:8000
# noVNC    : http://localhost:6080  ← 온보딩 브라우저 화면
```

### 방법 B — 로컬 직접 실행 (개발 환경 권장)

> 💡 개발 환경에서는 `start.sh`를 사용하지 않는다. Xvfb · noVNC 없이 `uvicorn`만 실행하며, Playwright는 로컬 PC 모니터에 직접 브라우저 창을 띄운다. DB · Ollama는 Podman 컨테이너로 별도 실행한다.

```bash
# 1. 가상환경 생성
python -m venv venv
venv\Scripts\activate         # Windows
source venv/bin/activate      # Mac/Linux

# 2. 라이브러리 설치
pip install -r requirements.txt

# 3. Playwright 브라우저 설치 (patchright — CDP 탐지 우회 패치 적용 Chromium)
patchright install chromium

# 4. .env.development 파일 기준으로 서버 실행
uvicorn main:app --reload --port 8000
```

### 환경변수

환경변수는 개발/배포 환경을 분리하여 2개의 프로필로 관리한다.

#### `.env.development` — 개발 환경

```bash
DATABASE_URL=postgresql+asyncpg://acro_user:acro_password@localhost:55432/acro_db
OLLAMA_HOST=http://localhost:11434
# DISPLAY=:99  # 배포 전용 — 개발 환경에서는 불필요
HEADLESS=false
SESSION_DIR=./sessions
MAX_RECOVERY_ATTEMPTS=3
HUMAN_MODE=false  # 개발 시 속도 우선
LOG_LEVEL=debug
CORS_ORIGINS=http://localhost:5173  # CORS 허용 출처
```

#### `.env.production` — 배포 환경 (Podman 컨테이너)

```bash
DATABASE_URL=postgresql+asyncpg://acro_user:acro_password@host.containers.internal:55432/acro_db
OLLAMA_HOST=http://host.containers.internal:11434
DISPLAY=:99
HEADLESS=false
SESSION_DIR=./sessions
MAX_RECOVERY_ATTEMPTS=3
HUMAN_MODE=true  # 배포 시 인간형 행동 활성화
LOG_LEVEL=warning
CORS_ORIGINS=http://localhost:5173  # CORS 허용 출처
```

---

## 4️⃣ 주의사항

- **`patchright` + `playwright-stealth` 필수**: 코레일은 CDP 연결 자체를 탐지하므로 `browser.py`에서 `playwright.async_api` 대신 `patchright.async_api`를 import해야 한다. 둘 다 빠지면 차단된다.
- 세션 만료 시 FE에 WebSocket으로 알림을 전송해야 한다.
- `capture.py`는 `page.expose_function()` + `page.evaluate()`로 JS 클릭 이벤트를 브라우저에 주입해 수집한다. `page.on("click")`은 DOM 이벤트를 감지할 수 없어 사용하지 않는다.
- 개인 학습 목적, 본인 계정에서만 사용할 것. 상업적 이용 금지.
- `.env.development` · `.env.production` 파일은 절대 커밋하지 않는다.
