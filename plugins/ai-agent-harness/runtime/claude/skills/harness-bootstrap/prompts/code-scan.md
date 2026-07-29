# 코드베이스 스캔 기준 (code-scan)

기존 코드베이스에서 인벤토리를 자동 추출하는 기준.
모든 추출은 **실제 파일 내용 기반**이며 추측·상상 금지.

---

## 스캔 원칙

1. **관찰 기반 서술**. "현재 이렇게 돼 있다"만 쓰고 "이렇게 해야 한다"는 쓰지 않는다.
2. **역할 없는 파일·폴더는 무시**. `node_modules/`, `.git/`, `dist/`, `build/`, `venv/`, `__pycache__/`, `target/`, `.next/`, `.turbo/`, `coverage/` 등은 트리에서 제외.
3. **읽을 수 없는 대용량/바이너리는 스킵**. 이미지·모델 가중치·아카이브 등.
4. **불확실하면 `미정 — 코드에서 확인 불가`**. 추론하지 않는다.

---

## 추출 항목

### 1. 디렉토리 트리

- 루트에서 Glob으로 전체 트리 수집
- 제외 디렉토리 필터링 (위 무시 목록)
- **역할 있는 폴더만** 남긴다:
  - 소스 코드 폴더 (`src/`, `app/`, `lib/`, `pkg/` 등)
  - 도메인 모듈 폴더 (`api/`, `services/`, `models/`, `components/` 등)
  - 설정 폴더 (`config/`, `scripts/`)
- 각 폴더 옆에 **한 줄 역할 주석** — 내부 파일명에서 추론

### 2. 엔트리포인트

- 관례 파일명 검색: `main.*`, `app.*`, `index.*`, `server.*`, `__main__.py`, `cmd/**/main.go`, `Application.java`, `Program.cs`
- 매니페스트의 `main`/`scripts.start`/`entry-point` 필드 확인
- Dockerfile의 `CMD`/`ENTRYPOINT` 확인
- 관례 파일명이 없으면 **실행 스크립트가 가리키는 파일**과 **서버/CLI 부트스트랩 코드**를 후보로 수집한다.
- 후보가 여러 개면 모두 나열하고, 이후 동작 흐름 추적은 **확정 가능한 후보**에서만 시작한다.

### 3. 라우터/엔드포인트

다음 패턴 grep. 언어/프레임워크 별 대표 패턴:

| 언어/프레임워크 | 패턴 |
|---------------|------|
| FastAPI/Flask | `@app.(get\|post\|put\|delete)`, `@router.(get\|post\|put\|delete)`, `add_url_rule` |
| Express/Koa | `app\.(get\|post\|put\|delete\|patch)`, `router\.(get\|post\|put\|delete)` |
| NestJS | `@(Get\|Post\|Put\|Delete\|Patch)` |
| Spring | `@(Get\|Post\|Put\|Delete\|Request)Mapping`, `@RestController` |
| Next.js | `app/**/route.(ts\|js)`, `pages/api/**` |
| Rails/Sinatra | `resources :`, `get '/'` 등 |
| Go | `http\.HandleFunc`, `mux.HandleFunc`, `r\.(GET\|POST)` |
| ASP.NET | `\[Http(Get\|Post\|Put\|Delete)\]` |

결과 형식: `METHOD PATH → 파일:라인`

### 4. WebSocket / 실시간 통신

grep 키워드: `websocket`, `WebSocket`, `\.on\(['\"]message`, `@WebSocketGateway`, `stomp`, `socket\.io`, `SockJS`, `/ws`

메시지 타입은 `type` 필드·이벤트명 기반으로 후보 목록 구성.
불명확하면 `미정 — 메시지 타입 코드에서 확인 필요`.

### 5. DB 모델/테이블

| ORM/드라이버 | 소스 |
|------------|------|
| SQLAlchemy | `Base` 상속 클래스 |
| Django ORM | `models.Model` 상속 |
| TypeORM/Prisma | `@Entity`, `schema.prisma` |
| JPA | `@Entity` |
| Sequelize/Mongoose | `Model.init`, `mongoose.Schema` |
| Drizzle/Knex | 테이블 정의 파일 |

추출: 테이블명, 핵심 컬럼, 관계(FK).

### 6. 환경 변수

- `.env*` 파일 전체 (단, 값은 마스킹하고 키만 노출)
- 코드에서 `os.getenv`, `process.env.`, `System.getenv`, `env::var`, `os.Getenv` grep
- 키 + 사용 위치 + 기본값(코드에 있으면) 추출

### 7. 실행 스크립트·배포 구성

- `package.json` scripts
- `Makefile`, `justfile`, `taskfile.yml`
- `Dockerfile`, `docker-compose*`, `Containerfile`, `podman-compose*`
- CI 파일 (`.github/workflows/*`, `.gitlab-ci.yml`) — 빌드·테스트 명령만 참고

### 8. 외부 서비스/라이브러리

- 매니페스트에서 의존성 목록 추출
- 카테고리 분류 후보: HTTP 서버, DB 드라이버, ORM, 캐시, 큐, AI/LLM, 테스트, 빌드 도구, 모니터링
- 카테고리 불명은 `기타`로 묶는다

### 9. TODO/FIXME/NOTE 주석

- grep: `TODO`, `FIXME`, `XXX`, `HACK`, `NOTE`
- OUTPUT_V2의 **12 열린 결정 사항** 섹션 후보로 사용

---

## 모노레포 감지

루트에 매니페스트가 **없고** 하위에 여러 매니페스트가 있으면 모노레포.

감지 패턴:
- `package.json` with `workspaces` 필드
- `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`
- `apps/`, `packages/`, `services/`, `frontend/`+`backend/`, `fe/`+`be/`, `client/`+`server/` 디렉토리

모노레포면 각 하위 프로젝트를 **독립 단위로 스캔**하고, 최종 산출물도 프로젝트별로 분리 저장.

---

## 멀티 런타임 루트 감지

루트에 `package.json` + `pyproject.toml`처럼
**서로 다른 에코시스템 매니페스트가 2개 이상** 공존하면 단일 프로젝트로 단정하지 않는다.

- 이 경우 `멀티 런타임 루트`로 표시하고 deployable unit 후보를 분리한다.
- 후보 분리 기준: 매니페스트 경로, Dockerfile, 실행 스크립트, 엔트리포인트 묶음
- 저장 단위가 불명확하면 사용자에게 **1회만** 확인한다.

---

## 출력 형식 (Step 2 요약 보고서)

사용자에게 보여줄 요약은 아래 형식:

```markdown
## 스캔 결과 요약

- 프로젝트 유형: [단일 / 모노레포 / 멀티 런타임 루트]
- 언어/프레임워크: [자동 감지 결과]
- 엔트리포인트: [파일 경로]
- API 엔드포인트: [N개 발견]
- WebSocket: [있음/없음]
- DB: [ORM / 테이블 수]
- 환경 변수: [N개 발견]

확인 필요:
- [불명확한 항목 리스트]
```

사용자가 수정하거나 "OK"하면 Step 3으로 진행.
