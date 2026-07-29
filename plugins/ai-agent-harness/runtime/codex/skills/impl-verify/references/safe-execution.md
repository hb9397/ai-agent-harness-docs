# 안전 실행 가이드 (safe-execution)

자동 검증 명령이 운영 환경이나 외부 시스템에 의도치 않은 사이드이펙트를 일으키지 않도록
실행 전 거치는 게이트.

---

## 절대 자동 실행 금지

다음 명령은 사용자가 직접 실행해야 한다. impl-verify는 명령을 제시만 한다.

- 운영(prod) DB에 대한 INSERT/UPDATE/DELETE
- 운영 환경 마이그레이션 (`alembic upgrade head`, `prisma migrate deploy`)
- 결제 게이트웨이 호출 (실거래)
- 메일/SMS/푸시 발송 (실수신자)
- 외부 결제·정산·환불 API
- 공개 채널 알림 (Slack channel, 공개 Discord)
- 운영 자격증명 회수/재발급
- 운영 서버 재시작/배포

자동 검증이 필요해도 위 명령은 dry-run 또는 스테이지 환경에서만 실행.

---

## 사용자 승인 필요

다음은 사용자에게 명령을 보여주고 승인을 받은 뒤에만 실행:

- 멱등성이 보장되지 않는 쓰기 (`DELETE FROM`, 다수 row UPDATE)
- 파일 시스템 삭제 (`rm -rf`, `git clean -fd`)
- 컨테이너/프로세스 종료
- 환경 초기화 (DB reset, cache flush)
- 외부 API 호출 중 quota 큰 것
- 5초 이상 걸릴 가능성이 있는 쿼리

승인 요청 형식:

```
다음 명령을 실행하려고 합니다:

  {명령}

영향:
  - {예상 사이드이펙트 1}
  - {예상 사이드이펙트 2}

환경: {로컬 / 도커 / 스테이지}
실행해도 될까요? (yes / no / 보류)
```

---

## 자유롭게 실행 가능

다음은 승인 없이 실행해도 된다:

- read-only 명령 (`SELECT`, `curl GET`, `ls`, `cat`)
- 단위 테스트 (`pytest`, `npm test`)
- lint / typecheck (`eslint`, `tsc`, `mypy`)
- 빌드 (`npm run build` — 로컬 산출물만)
- HTTP GET (외부 영향 없는 idempotent)
- 로컬 DB의 SELECT
- 로컬 파일 read

---

## 자격증명 보호

### 입력
- API_TOKEN / DATABASE_URL / SECRET_KEY 등은 환경변수로만 받는다.
- 명령행 인자(`--token=xxx`)나 평문 입력 금지.
- 환경변수가 없으면 사용자에게 `.env` 경로를 묻거나 명령 스킵.

### 출력 마스킹
다음 패턴은 캡처 시 자동 마스킹:

```
Bearer [A-Za-z0-9._\-+/]+        → Bearer ***
password=\S+                     → password=***
[Aa]uth.*[Tt]oken.*[:=]\s*\S+    → AuthToken: ***
postgres://[^:]+:[^@]+@          → postgres://***:***@
mysql://[^:]+:[^@]+@             → mysql://***:***@
"api_key":\s*"[^"]+"            → "api_key":"***"
```

마스킹 누락이 의심되면 출력 캡처 폐기.

### 저장
- 로그 파일에 평문 저장 금지.
- 마스킹 후에도 길이로 토큰 길이 유추 가능한 경우 길이도 가린다.

---

## 환경 감지

명령 실행 전 환경을 식별한다:

```
환경 감지 신호:
  - DATABASE_URL의 호스트가 prod / production 포함 → prod 의심
  - URL이 *.com / *.io / *.app 등 외부 도메인 → 외부 시스템 의심
  - .env 파일이 .env.production / .env.prod → prod 의심
  - kubeconfig context가 prod 포함 → prod 의심
```

prod 의심이면 자동 실행 절대 금지. 사용자에게 환경 확인 요청.

---

## 부수효과 추정

다음 명령 패턴은 사이드이펙트 의심으로 분류:

| 패턴 | 분류 |
|------|------|
| `POST /api/.*` | 쓰기 (확인 필요) |
| `PUT/PATCH/DELETE` | 쓰기 (확인 필요) |
| `INSERT/UPDATE/DELETE/DROP/TRUNCATE` | 쓰기 (확인 필요) |
| `migrate`, `deploy`, `publish` | 환경 변경 (승인 필요) |
| `mail`, `send`, `notify` | 외부 발송 (절대 금지) |
| `pay`, `charge`, `refund` | 결제 (절대 금지) |

분류 결과에 따라 위 게이트 적용.

---

## 실행 중단

다음 신호가 보이면 즉시 실행 중단:

- 응답에 운영 데이터로 보이는 PII (이메일·전화번호 다수)
- 예상보다 많은 영향 (1건 기대했는데 100건 변경)
- 자격증명이 stdout/stderr에 노출

중단 후 사용자에게 즉시 보고하고 후속 명령 일시 정지.
