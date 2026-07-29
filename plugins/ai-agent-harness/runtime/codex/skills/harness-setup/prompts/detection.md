# prompts/detection.md
# 역할: 실행 컨텍스트·프로젝트 유형·세팅 모드를 감지하는 규칙

---

## [실행 컨텍스트 감지]

현재 스킬이 어디서 실행되고 있는지 판정한다.

### 감지 순서

1. 현재 디렉토리에서 하네스 관리 레포 식별자를 찾는다:

```bash
# 하네스 관리 레포 식별: maintainer/ 디렉토리 + 현재 계획서 공존 여부
ls maintainer/skills/harness-plugin-maintainer/SKILL.md 2>/dev/null && ls improvement_plan/20260729/플러그인\ 전환\ 및\ 스킬\ 거버넌스\ 리팩토링\ 작업\ 계획서.md 2>/dev/null

# 이전 구조 식별 fallback
ls skills/harness-setup/SKILL.md 2>/dev/null && (ls Docs/Harness_Engineering.md 2>/dev/null || ls Harness_Engineering.md 2>/dev/null)
```

2. 위 조건이 성립하면 → **하네스 관리 레포 내부**. 사용자에게 대상 프로젝트 루트 경로를 질문한다. 부모 폴더를 자동 적용하지 않는다.

3. 위 조건 불충족 시, 현재 위치에 `.docs/` 또는 `AGENTS.md`가 있는지 확인:

```bash
ls -d .docs/ 2>/dev/null || ls AGENTS.md 2>/dev/null
```

4. `.docs/` 또는 `AGENTS.md`가 존재하면 → **이미 하네스 문서가 있는 프로젝트**. 현재 위치를 프로젝트 루트로 설정.

5. 위 모두 불충족 → 사용자에게 프로젝트 루트 경로를 직접 질문.

`.claude/skills/`, `.agents/skills/` 또는 `skills/*/SKILL.md`가 존재하면
legacy/custom local skill 후보로만 기록하고, 실행 컨텍스트 판정의 주 기준으로
쓰지 않는다.

### 하네스 관리 레포에서 실행 시 추가 확인

사용자에게 대상 프로젝트 루트 경로를 확인한다:

> "하네스 관리 레포(`{현재 폴더}`) 안에서 실행 중입니다.
> `.docs`와 루트 컨텍스트를 세팅할 대상 프로젝트 루트 경로를 알려주세요."

---

## [프로젝트 유형 감지]

프로젝트 루트 확정 후, 단일/복수 애플리케이션 여부를 판정한다.

### 감지 기준

**단일 애플리케이션 시그널** — 프로젝트 루트 자체가 앱 루트:
- 루트에 빌드/의존성 매니페스트가 있음: `package.json`, `pom.xml`, `build.gradle`, `go.mod`, `requirements.txt`, `Cargo.toml`, `*.sln`, `*.csproj`, `Gemfile`, `pyproject.toml`, `composer.json`
- 루트에 소스 디렉토리가 있음: `src/`, `app/`, `lib/`, `cmd/`
- 루트에 엔트리포인트가 있음: `main.*`, `index.*`, `App.*`

**복수 애플리케이션 시그널** — 프로젝트 루트 아래에 여러 앱 루트가 존재:
- 하위 디렉토리 각각이 위 매니페스트를 보유
- 하위 디렉토리 각각이 독립 `.git/`을 보유
- 프로젝트 루트 자체에는 매니페스트가 없음 (또는 하네스 레포/`.docs` 등 인프라만 있음)

### 감지 절차

```bash
# 1. 프로젝트 루트에 매니페스트가 있는지 확인
ls package.json pom.xml build.gradle go.mod requirements.txt Cargo.toml *.sln *.csproj Gemfile pyproject.toml composer.json 2>/dev/null

# 2. 하위 1 depth 폴더에서 매니페스트 보유 디렉토리 탐색
for d in */; do
  [ -d "$d" ] || continue
  case "$d" in
    .docs/|.claude/|.agents/|node_modules/|.git/|*-ai-harness-docs/|ai-agent-harness-docs/) continue ;;
  esac
  manifests=$(ls "${d}package.json" "${d}pom.xml" "${d}build.gradle" "${d}go.mod" "${d}requirements.txt" "${d}Cargo.toml" "${d}Gemfile" "${d}pyproject.toml" "${d}composer.json" 2>/dev/null | head -1)
  gitdir=$(ls -d "${d}.git" 2>/dev/null)
  if [ -n "$manifests" ] || [ -n "$gitdir" ]; then
    echo "APP_CANDIDATE: $d (manifest: $manifests, git: $gitdir)"
  fi
done

# 3. 하네스 관리 레포 디렉토리 탐색 (제외 대상)
ls -d *-ai-harness-docs/ ai-agent-harness-docs/ 2>/dev/null
```

### 판정 규칙

| 루트 매니페스트 | 하위 앱 후보 | 판정 |
|----------------|-------------|------|
| 있음 | 0~1개 | **단일 애플리케이션** |
| 없음 | 2개 이상 | **복수 애플리케이션** |
| 있음 | 2개 이상 | 사용자에게 확인 — 모노레포일 수 있음 |
| 없음 | 0~1개 | 사용자에게 직접 질문 |

> 어떤 경우든 **판정 결과를 사용자에게 반드시 보여주고 승인받는다**.

---

## [세팅 모드 판별]

프로젝트 루트(확정)에서 기존 하네스 흔적을 탐색한다.

```bash
# 기존 .docs 구조 존재 여부
ls -d .docs/ 2>/dev/null
ls .docs/*.md .docs/*-context.md .docs/root-context/ 2>/dev/null | head -10

# 루트 컨텍스트 존재 여부
ls AGENTS.md CLAUDE.md 2>/dev/null

# legacy local skill copy 후보(읽기 전용 report 대상)
ls .claude/skills/*/SKILL.md 2>/dev/null | head -5
ls .agents/skills/*/SKILL.md 2>/dev/null | head -5
ls skills/*/SKILL.md 2>/dev/null | head -5
```

| 조건 | 모드 |
|------|------|
| `.docs/` 또는 `AGENTS.md`가 존재 | **갱신 모드** |
| 위 조건 불충족 | **초기 세팅 모드** |

> `.claude/skills/`, `.agents/skills/` 또는 `skills/*/SKILL.md`만 있는 경우:
> legacy/custom local skill 후보로 보고하되, 문서 하네스가 없으면 **초기 세팅**으로
> 분류한다. 이 경로들은 세팅 모드와 관계없이 생성·수정·동기화하지 않는다.
