# 자동 검증 실행 규칙 (run-auto)

분류된 auto 항목을 순차 실행하고 PASS/FAIL/UNKNOWN을 판정한다.

---

## 실행 전 게이트

다음 중 하나라도 해당하면 **반드시 사용자 승인**을 받는다:

- 운영(prod) 환경 URL/DB 접속 가능성
- 결제·메일·SMS·푸시 같은 외부 사이드이펙트
- 멱등성 없는 쓰기 작업 (DELETE, UPDATE 다건)
- 마이그레이션 실행 (운영 DB)
- 자격증명이 명령행에 노출되는 경우

승인 양식:

> "다음 명령은 외부 사이드이펙트가 있을 수 있습니다.
> 실행해도 될까요?
> ```
> {명령}
> ```
> 환경: {로컬 / 스테이지 / 운영}"

---

## 실행 순서

`extract-checks.md`의 우선순위를 따른다:

1. 빌드 / 타입체크 / lint → 실패 시 이후 검증 SKIP
2. 단위 테스트
3. 통합/E2E 테스트
4. HTTP 호출 (curl 등)
5. DB 검증
6. 파일/산출물 검증

빌드 실패 시 이후 항목은 "skipped — build failed"로 표시.

---

## 실행 방식

각 항목을 다음 형식으로 처리:

```
[항목 ID] {본문 요약}
  → 명령: {명령 1줄}
  → 실행 중...
  → 결과: PASS/FAIL/UNKNOWN
  → 출력 요약: {3줄 이내}
```

- 명령은 한 번에 1개씩 실행한다.
- 출력이 길면 마지막 30줄만 캡처하고 전체는 파일로 저장 (`logs/{check_id}.log`).
- 비밀번호·토큰은 마스킹 (`***`).

---

## PASS / FAIL / UNKNOWN 판정 규칙

### PASS 조건 (모두 충족)

- exit code가 `expected_exit`와 일치
- `expected_stdout_pattern`이 있으면 매칭
- 부수 조건(DB 레코드, 파일 존재)이 있으면 모두 충족

### FAIL 조건 (하나라도 해당)

- exit code 불일치
- stdout 패턴 불일치
- 부수 조건 불충족
- 예외/스택트레이스 발견 (`expected_exit`가 정상이어도 출력에 에러가 있으면 FAIL)

### UNKNOWN 조건

- 명령 실행은 됐는데 합격 조건이 모호해 판정 불가
- 출력 형식이 예상과 다름
- → 자동으로 manual로 재분류, 사용자에게 결과 보여주고 판정 요청

---

## 명령 실패 시 보강 정보 수집

FAIL이 났을 때 다음 정보를 추가 수집 (사용자에게 진단 도움):

- 명령 종료 코드
- stderr 마지막 10줄
- 관련 로그 파일 위치 (있으면)
- 최근 변경된 파일 (git status --short 1회)

```
[FAIL] BE-03.criterion: curl POST /api/sites → 201 기대했으나 500
  종료 코드: 0 (curl 자체는 성공)
  응답 상태: 500
  응답 본문: {"error":"AttributeError: 'NoneType'..."}
  관련 변경: M  api/routers/sites.py (3분 전)
  추정 원인: 라우터 핸들러 내부 NPE
  권장 액션: api/routers/sites.py의 POST 핸들러 NPE 처리 확인
```

원인 추정은 단정하지 않는다("추정 원인", "권장 액션" 표현 사용).

---

## 환경 변수 / 자격증명

- 자격증명은 환경변수로만 받는다 (`DATABASE_URL`, `API_TOKEN` 등).
- 명령 출력 캡처 시 다음 패턴은 자동 마스킹:
  - `Bearer [A-Za-z0-9-._~+/]+`
  - `password=\S+`
  - `[Aa]uth.*[Tt]oken.*[:=]\s*\S+`
- 마스킹 누락이 의심되면 사용자에게 알리고 캡처 폐기.

---

## 타임아웃

- 단위 테스트: 60초
- 통합/E2E: 300초
- HTTP 요청: 30초
- DB 쿼리: 30초

타임아웃 시 FAIL 처리하고 사유를 "timeout: {초}" 로 기록.

---

## 실행 결과 저장

다음 구조로 저장:

```
verify-output/
└── {YYYY-MM-DD-HHMM}/
    ├── summary.json          # 전체 PASS/FAIL/SKIP 카운트
    ├── per-check/
    │   ├── BE-03.criterion.json
    │   └── ...
    └── logs/
        ├── BE-03.criterion.log
        └── ...
```

이 위치는 사용자가 명시한 경로 또는 기본 `./verify-output/`.
사용자가 저장을 원치 않으면 대화창 출력만 한다.
