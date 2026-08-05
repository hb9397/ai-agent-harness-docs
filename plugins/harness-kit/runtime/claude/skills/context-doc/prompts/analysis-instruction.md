# instruction 분석 및 주제 분류 기준 (analysis-instruction)

설계 문서에서 **코딩 규칙/제약/금지사항**을 추출한 뒤, 아래 주제별로 분류한다.
각 주제에 해당하는 내용이 있을 때만 파일을 생성한다. 없는 주제는 파일을 만들지 않는다.

> 핵심: 프레임워크 이름으로 분기하지 않는다. 설계 문서에 등장한 라이브러리·주제를 그대로 반영한다.

---

## 공통 추출 원칙

### 금지 목록 — 반드시 삼위일체로 추출

각 금지 항목은 아래 세 가지를 반드시 함께 추출한다.
하나라도 빠지면 Agent가 왜 금지인지 모르고 우회 코드를 생성한다.

```
금지 패턴  →  금지 이유  →  대안
```

예시:
- `axios 직접 import` → API 호출 분산 시 유지보수 불가 → `src/api/client.js` 함수 사용
- `sync def 라우터` → uvicorn ASGI에서 블로킹 발생 → `async def` 사용

누락 시 **Step 3-B의 단일 질문 할당분 안에서만** 사용자에게 확인한다.
이미 질문 예산이 소진되었다면 추측하지 말고 `미정 — 금지 이유/대안 확인 필요`로 남긴다.

---

## 경계가 겹치는 규칙 처리

한 규칙이 여러 파일 후보에 걸쳐 보이면 **가장 구체적인 1개 파일에만** 넣는다.
같은 내용을 두 파일에 복제하지 않는다.

| 규칙 유형 | 우선 배치 파일 | 메모 |
|-----------|----------------|------|
| 레이어 경계, 책임 분리, 의존 방향 | `architecture-instruction.md` | 구조 규칙 |
| 언어 레벨 async/await, 예외 전파, 네이밍, 타입, 로그 | `code-style-instruction.md` | 프레임워크 비특정 규칙 |
| 특정 라이브러리 API 사용법, 훅/DI/세션 패턴, 재시도 옵션 | `framework-instruction.md` | 라이브러리 명이 규칙의 핵심일 때 |
| HTTP 엔드포인트, 요청/응답 스키마, 인증/인가, 버전 | `api-instruction.md` | HTTP 규약 |
| WebSocket/MQ/RPC 메시지 포맷, 이벤트 순서, 재연결 | `comm-instruction.md` | 비-HTTP 통신 |
| 파일 위치, 네이밍, 진입점 파일에 넣으면 안 되는 코드 | `file-convention-instruction.md` | 저장 위치/배치 규칙 |
| Agent의 응답 방식, 승인 절차, 자동 실행 금지 | `agent-instruction.md` | AI 행동 규칙 |

예시:
- 일반적인 `async` 에러 전파 규칙 → `code-style-instruction.md`
- `React Query`의 `retry`/`queryClient` 사용 규칙 → `framework-instruction.md`
- `FastAPI` 라우터는 항상 `async def`여야 함 → 라이브러리 결합이 강하면 `framework-instruction.md`, 그렇지 않으면 `code-style-instruction.md`

---

## 주제별 분류 가이드

### 1. `architecture-instruction.md` — 아키텍처 제약

생성 조건: 모듈/레이어/책임 분리 규칙이 있을 때

- 레이어 간 의존 방향 (어디서 어디를 호출할 수 있는가 / 금지되는가)
- 집중 관리 모듈 (API 클라이언트, 공통 훅, DB 접근 레이어 등)
- 모듈별 책임과 금지 책임 (표 형태 권장)
- 위반 시 처리 방식 (어떤 파일/레이어로 옮길 것인가)

### 2. `code-style-instruction.md` — 코드 스타일

생성 조건: 언어 레벨 스타일·컨벤션이 있을 때

- 네이밍 컨벤션
- 타입 힌트 / 타입 선언 규칙
- 함수 길이·복잡도 기준
- 비동기 처리 방식 (try/catch, 에러 전파)
- 주석 스타일 (사람이 작성하는 주석 기준)
- 로그/예외 처리 방식
- 하드코딩 금지 목록 (URL, 비밀번호, 포트 등)

### 3. `framework-instruction.md` — 프레임워크/라이브러리 사용 규칙

생성 조건: 특정 라이브러리의 사용 규칙/금지 패턴이 있을 때

설계 문서 `07 라이브러리` 섹션을 읽고, **각 라이브러리마다** 다음을 추출한다.

- 사용 규칙 (반드시 이렇게 쓴다)
- 금지 패턴 + 이유 + 대안
- 핵심 예시 스니펫 (완성 코드 X, 패턴만)

라이브러리마다 별도 하위 섹션으로 전개한다. 프레임워크 이름으로 파일을 나누지 않는다.

### 4. `api-instruction.md` — API 설계 규약

생성 조건: API 엔드포인트/스키마 규약이 있을 때

- 엔드포인트 네이밍 규칙
- 요청/응답 스키마 규약 (dict 금지, Pydantic 필수 등)
- 에러 처리 규약 (HTTPException, 에러 응답 포맷)
- 인증/인가 규칙
- 버전 관리 방식
- (선택) 엔드포인트 카탈로그 — AGENTS.md에 없다면 여기에

### 5. `comm-instruction.md` — 통신 프로토콜 규약

생성 조건: WebSocket/MQ/RPC/pub-sub 등 비-HTTP 통신이 있을 때

- 메시지 포맷 규약 (type 필드 필수 등)
- 메시지 타입 목록과 의미
- 이벤트 트리거 조건
- 재연결/실패 처리 규칙
- 순서 고정 플로우 (온보딩, 결제 등 Step별 트리거 + 액션 매핑)

### 6. `file-convention-instruction.md` — 파일 생성 규칙

생성 조건: 파일 배치/네이밍 규칙이 있을 때

- 새 파일을 어느 폴더에 만드는가 (폴더별 기준)
- 파일 네이밍 컨벤션
- 한 파일에 담을 수 있는 것 / 담으면 안 되는 것
- 특정 진입점 파일(main.py, app.ts 등)에 쓰면 안 되는 코드

### 7. `agent-instruction.md` — AI Agent 전용 규칙 (항상 생성)

생성 조건: **항상 생성**. 항목이 없어도 뼈대는 둔다.

- Agent가 코드 작성 시 반드시 지켜야 할 것 (예: 기존 주석 보존)
- Agent가 해서는 안 되는 것 (예: 새 주석 추가 금지, 테스트 자동 실행 금지)
- Agent의 응답 스타일 규칙
- 구현 승인 절차 (예: 파일 생성 전 사용자 확인)

---

## 분류 후 산출물

분류가 끝나면 다음 정보를 갖고 Step 4로 넘어간다.

```
생성할 파일 목록:
- architecture-instruction.md (있음/없음)
- code-style-instruction.md (있음/없음)
- framework-instruction.md (있음/없음)
- api-instruction.md (있음/없음)
- comm-instruction.md (있음/없음)
- file-convention-instruction.md (있음/없음)
- agent-instruction.md (항상 있음)

각 파일별 주제 본문 + 금지 삼위일체 목록
```

---

## 관찰 기반 bootstrap 입력 예외

입력 문서가 `harness-bootstrap`처럼 **관찰 기반으로 역추출된 설계 문서**라면,
규범적 이유와 대안이 문서/코드/README에 없을 수 있다.

- 이 경우 금지 이유·대안을 **추정해서 채우지 않는다**.
- 관찰 사실만 있고 규범 근거가 없으면 `미정 — bootstrap 산출물에는 규범 근거 없음`으로 남긴다.
- 필요하면 `12 열린 결정 사항` 또는 각 파일의 `미정` 항목으로 올려 후속 `design-doc` 보강 대상으로 표시한다.

---

## 누락 항목 처리

- 주제별 규칙 본문이 없으면 해당 파일 **생성하지 않음** (빈 파일 금지)
- 금지 항목의 이유/대안이 없으면 질문 예산 안에서만 확인, 아니면 `미정` 처리
- 항목이 부분적으로 있으면 `미정 — [이유]` 로 표시하고 파일은 생성
- analysis-claude에서 이미 질문했으면 이 단계에서는 질문 금지 (금지 삼위일체 누락 제외)

## 산출물 라우팅 분류

instruction을 생성·갱신하기 전 producer 이름이 아니라 **artifact 의미**와 **대상 앱**을
결정한다. `.docs/harness/artifact-routing.json`과 format contract가 있으면 그 required
field를 사용한다. 기존 project instruction의 managed marker 밖 규칙과 충돌하면 기존
규칙을 보존하고 diff proposal만 만든다.
