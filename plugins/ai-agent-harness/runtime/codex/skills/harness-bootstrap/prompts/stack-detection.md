# 기술 스택 자동 감지 (stack-detection)

매니페스트 파일에서 언어·런타임·프레임워크·버전을 자동 추출한다.
프레임워크 이름을 스킬에 하드코딩하지 않는다 — **매니페스트에 적힌 그대로** 반영.

---

## 매니페스트 탐색 순서

루트에서 아래 파일을 Glob으로 찾는다. 여러 개가 있으면 모두 추출한다.

| 파일 | 언어/에코시스템 |
|------|----------------|
| `package.json` | Node.js / JavaScript / TypeScript |
| `requirements.txt` | Python (pip) |
| `pyproject.toml` | Python (poetry / PEP 621) |
| `Pipfile` | Python (pipenv) |
| `build.gradle`, `build.gradle.kts` | JVM (Gradle) |
| `pom.xml` | JVM (Maven) |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `composer.json` | PHP |
| `Gemfile` | Ruby |
| `*.csproj`, `*.fsproj`, `*.sln` | .NET |
| `pubspec.yaml` | Dart / Flutter |
| `mix.exs` | Elixir |
| `deno.json`, `deno.jsonc` | Deno |
| `bun.lockb`, `bun.lock` | Bun |

---

## 추출 항목

매니페스트별로 다음을 추출:

### 공통
- **프로젝트명**
- **버전**
- **런타임/언어 요구 버전** (engines, python_requires, rust-version, go 버전 등)
- **의존성 목록** (프로덕션 / 개발 / 테스트 분리)

루트에 서로 다른 에코시스템의 매니페스트가 2개 이상 공존하면
의존성을 한 프로젝트로 합치지 말고 **런타임 그룹별로 분리 유지**한다.

### package.json 특수
- `scripts` 필드 전체 (실행 명령 출처)
- `workspaces` 필드 (모노레포 판정)
- `type` 필드 (ESM/CJS)

### pyproject.toml 특수
- `[tool.poetry]` 또는 `[project]` 섹션
- `[tool.poetry.scripts]` 또는 `[project.scripts]` 진입점

### build.gradle / pom.xml 특수
- Spring Boot 플러그인 버전 (있으면)
- 자바 버전

---

## 의존성 카테고리 분류

추출된 의존성은 아래 카테고리로 자동 분류한다.
**라이브러리 이름 패턴 매칭**으로 분류하며, 스킬에 프레임워크를 하드코딩하지 않는다.

| 카테고리 | 판정 키워드 예시 |
|---------|----------------|
| HTTP 서버 / 웹 프레임워크 | `express`, `fastapi`, `flask`, `django`, `spring-boot`, `next`, `nest`, `koa`, `gin`, `echo`, `actix`, `axum`, `rails`, `sinatra`, `rocket` |
| API 클라이언트 | `axios`, `requests`, `httpx`, `ky`, `okhttp`, `reqwest` |
| DB 드라이버 | `pg`, `mysql`, `psycopg`, `asyncpg`, `pymongo`, `mongoose`, `redis` |
| ORM / 쿼리 빌더 | `sqlalchemy`, `prisma`, `typeorm`, `sequelize`, `drizzle`, `knex`, `jpa`, `hibernate`, `diesel`, `sqlx`, `gorm` |
| 데이터 검증 | `pydantic`, `zod`, `joi`, `class-validator`, `valibot` |
| 실시간 통신 | `socket.io`, `ws`, `websockets`, `sockjs`, `stomp` |
| AI/LLM | `langchain`, `langgraph`, `llama-index`, `ollama`, `openai`, `anthropic`, `transformers` |
| 브라우저 자동화 | `playwright`, `puppeteer`, `selenium`, `patchright` |
| 상태 관리 | `redux`, `zustand`, `pinia`, `mobx`, `recoil`, `jotai` |
| UI 프레임워크 | `react`, `vue`, `svelte`, `solid`, `angular`, `qwik` |
| 스타일 | `tailwindcss`, `styled-components`, `emotion`, `sass`, `less` |
| 테스트 | `jest`, `vitest`, `pytest`, `mocha`, `playwright-test`, `cypress`, `junit`, `rspec` |
| 빌드/번들 | `vite`, `webpack`, `rollup`, `esbuild`, `turbopack`, `gradle`, `maven` |
| 모니터링/로깅 | `sentry`, `winston`, `pino`, `loguru`, `log4j` |

분류 불명확한 것은 **`기타`** 로 묶는다. 지우지 않는다.

---

## 실행 환경 감지

컨테이너/배포 힌트:

- `Dockerfile` 있음 → 컨테이너 배포 환경
- `docker-compose.yml` / `podman-compose.yml` 있음 → 컴포즈 기반 멀티 서비스
- `Procfile` 있음 → Heroku 스타일
- `vercel.json` / `netlify.toml` → 서버리스 배포
- `serverless.yml` → AWS Lambda 등
- `.github/workflows/deploy*` → CI/CD 배포 힌트

---

## 출력 형식

```markdown
## 감지된 기술 스택

- **언어**: [Python 3.11 / Node.js 20 / Java 17 …]
- **주요 프레임워크**: [매니페스트에서 추출한 그대로]
- **빌드/패키지 매니저**: [npm/yarn/pnpm/pip/poetry/gradle/maven …]
- **배포 환경 힌트**: [Dockerfile / docker-compose / Podman …]
- **런타임 그룹**: [단일 / 멀티 런타임 루트면 그룹별 요약]

### 의존성 (카테고리별)

| 분류 | 라이브러리 (버전) |
|------|-------------------|
| HTTP 서버 | |
| ORM | |
| ... | |
```

OUTPUT_V2의 **07 라이브러리** 섹션에 그대로 사용 가능한 형식.
