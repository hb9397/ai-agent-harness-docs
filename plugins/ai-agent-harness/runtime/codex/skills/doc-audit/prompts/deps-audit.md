# Task A — 의존성 분석 (deps-audit)

**역할**: 실제 의존성 파일과 AI Agent 문서 간의 라이브러리/버전 괴리를 찾는 전담 에이전트.

---

## 1. 언어 자동 감지

먼저 프로젝트에 어떤 의존성 파일이 존재하는지 확인한다.

```bash
ls requirements.txt requirements-dev.txt requirements-prod.txt pyproject.toml Pipfile \
   package.json yarn.lock pnpm-lock.yaml \
   pom.xml build.gradle build.gradle.kts \
   go.mod Cargo.toml 2>/dev/null
```

위 결과를 기반으로 **감지된 언어 블록만** 아래에서 선택적으로 실행한다.

---

## 2. 의존성 파일 수집 (감지된 언어만 실행)

### Python — `requirements.txt` / `pyproject.toml` / `Pipfile` 존재 시

```bash
cat requirements.txt 2>/dev/null
cat requirements-dev.txt 2>/dev/null
cat requirements-prod.txt 2>/dev/null
cat pyproject.toml 2>/dev/null
cat Pipfile 2>/dev/null
pip list --format=freeze 2>/dev/null | head -50
```

### Node.js — `package.json` 존재 시

```bash
cat package.json 2>/dev/null
```

### Next.js — `package.json`에 `next` 의존성이 있는 경우 추가 확인

```bash
cat next.config.js 2>/dev/null
cat next.config.mjs 2>/dev/null
ls app/ src/app/ pages/ src/pages/ 2>/dev/null
```

### Java / Spring Boot — `pom.xml` / `build.gradle` 존재 시

```bash
cat pom.xml 2>/dev/null
cat build.gradle 2>/dev/null
cat build.gradle.kts 2>/dev/null
grep -i "spring-boot\|springframework" pom.xml build.gradle 2>/dev/null | head -20
grep "<artifactId>\|implementation\|compile\|runtimeOnly\|testImplementation" \
  pom.xml build.gradle 2>/dev/null | head -40
```

### Go — `go.mod` 존재 시

```bash
cat go.mod 2>/dev/null
cat go.sum 2>/dev/null | head -30
```

### Rust — `Cargo.toml` 존재 시

```bash
cat Cargo.toml 2>/dev/null
```

---

## 3. 런타임/프레임워크 버전 확인 (감지된 언어만 실행)

감지된 언어에 한해 아래 명령을 조건부 실행한다.

| 감지 언어 | 런타임 확인 | 프레임워크 확인 |
|-----------|------------|----------------|
| Python    | `python --version` | `pip show fastapi django flask` |
| Node.js   | `node --version` | `node -e "try{console.log('next:',require('./node_modules/next/package.json').version)}catch(e){}"` 등 |
| Java      | `java -version` | `grep` 으로 Spring Boot 버전 확인 (2단계에서 수행) |
| Go        | `go version` | `go.mod` 에서 확인 (2단계에서 수행) |
| Rust      | `rustc --version` | `Cargo.toml` 에서 확인 (2단계에서 수행) |

---

## 4. 문서와 비교

| 확인 항목 | 방법 |
|-----------|------|
| 라이브러리 추가 | 의존성 파일에 있지만 문서에 언급 없는 항목 |
| 라이브러리 제거 | 문서에 있지만 의존성 파일에서 사라진 항목 |
| 버전 불일치 | 문서 기재 버전 ≠ 실제 설치/명시 버전 |
| 프레임워크 메이저 업그레이드 | Next.js 13→14, Spring Boot 2→3 등 주요 변경점 |
