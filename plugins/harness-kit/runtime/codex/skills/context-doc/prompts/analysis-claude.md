# AGENTS.md 추출 기준 (analysis-claude)

AGENTS.md는 **얇은 프로젝트 팩트 + 지침 인덱스** 정본이다.
CLAUDE.md는 `@AGENTS.md` bridge이므로 이 분석 결과를 복제하지 않는다.
설계 문서에서 아래 항목만 추출한다. 규칙/금지사항은 여기 넣지 않는다.

---

## 추출 항목 (프로젝트 팩트만)

### 1. 프로젝트 개요
- 프로젝트명 및 부제 (한 줄 설명)
- 무엇을 하는 시스템인가 (도메인, 목적)
- 어떤 사용자가 쓰는가
- 상위 구조 (예: FE / BE / AI 분리 여부)

### 2. 기술 스택
- 레이어별 라이브러리 + 버전
- 패키지 매니저
- 실행 환경 (로컬 / 컨테이너 / 클라우드)

### 3. 아키텍처 (디렉토리 트리)
- 폴더 트리 (역할이 있는 파일만, 전체 나열 금지)
- 각 폴더/파일 옆에 **한 줄 역할 주석**만 단다.
- 레이어 간 의존성 **규칙**은 여기 쓰지 않는다 → `architecture-instruction.md`로.

### 4. 핵심 도메인 개념
- 프로젝트 고유 용어 및 정의
- 핵심 식별자 (예: site_name, user_id)

### 5. 실행 방법
- 개발 환경 실행 명령
- 배포 환경 실행 명령
- 초기 세팅 명령 (최초 1회)

### 6. 환경 변수
- 개발/배포 환경 분리 여부
- 환경변수 목록 (변수명, 설명, 예시값)
- 환경별 동작 차이

### 7. 주의사항 (프로젝트 고유)
- "이 프로젝트에서만 해당되는" 함정/제약만.
- 일반적인 코딩 규칙·금지 패턴은 instruction 파일로.

### 8. 지침 인덱스 (Instruction Index)
Step 3-B에서 생성하기로 확정된 `.docs/instruction/*-instruction.md` 파일 목록을
**표 형태 인덱스**로 삽입한다. 생성하지 않는 파일은 인덱스에 넣지 않는다.

---

## 추출하지 않는 항목

아래 항목은 **AGENTS.md에 넣지 않는다**. instruction 파일로 넘긴다.

- 레이어 간 의존 방향 규칙 → `architecture-instruction.md`
- 코딩 컨벤션·네이밍 → `code-style-instruction.md`
- 라이브러리 사용 규칙·금지 패턴 → `framework-instruction.md`
- API 스키마 규약·에러 처리 규칙 → `api-instruction.md`
- WebSocket/메시지큐 프로토콜 규약 → `comm-instruction.md`
- 파일 생성 위치·네이밍 규칙 → `file-convention-instruction.md`
- AI Agent 전용 행동 규칙 → `agent-instruction.md`

단, **API 엔드포인트 카탈로그 자체**와 **WebSocket 엔드포인트 목록**은
사실 목록으로서 AGENTS.md에 실어도 되고, `api-instruction.md` / `comm-instruction.md`에
실어도 된다. 본 스킬은 **규약(규칙)은 instruction에, 팩트(목록)만 AGENTS.md 가능**을 기본으로 한다.

---

## 누락 항목 처리

항목이 설계 문서에 없으면 `미정 — [이유]` 로 표시한다.
사용자에게 확인이 필요한 경우 아래 우선순위로 최대 1개만 묻는다.

🔴 최대 1개만 확인 (Step 3-B에서도 질문 가능하므로 합산 2개 이내로 제한):
기술 스택 버전 / 환경변수 분리 여부 / 실행 방법 중 가장 불명확한 하나만
