# prompts/single-app-setup.md
# 역할: 단일 애플리케이션 프로젝트의 초기 세팅 절차

---

## 전제

- SKILL.md Step 2에서 **단일 애플리케이션** 확정, Step 3에서 **초기 세팅** 판정.
- 프로젝트 루트 = 애플리케이션 루트 (같은 폴더).
- 이 프로젝트는 단일 git 레포로 관리되며, 스킬·컨텍스트·산출물이 모두 이 레포 안에서 형상관리된다.

---

## 1. 플러그인 설치 상태 안내

이 스킬은 프로젝트 local skill copy를 만들지 않는다. 사용자가 `design-doc`, `context-doc` 등 후속 스킬을 아직 사용할 수 없다면 `ai-agent-harness` 플러그인 설치·새 세션 시작을 안내한다.

---

## 2. 산출물 디렉토리 확인

`.docs/` 디렉토리가 없으면 생성한다:

```bash
mkdir -p .docs
```

> 단일 앱에서의 `.docs/` 산출물 경로 표준:
>
> | 스킬 | 경로 |
> |------|------|
> | design-doc | `.docs/context-base/DESIGN.md` |
> | context-doc | `.docs/instruction/*-instruction.md` |
> | impl-doc / impl-fe-be-doc | `.docs/impl-doc/{사용자}/{기능}.md` |
> | design-prototype-docs / create-prototype | `.docs/prototype/{사용자}/{id}/` |

---

## 2-1. `.docs/` 안내·정책 파일 생성

`.docs/`를 처음 만들 때 아래 3종을 함께 생성한다. 이미 있으면 README/.gitignore는 최신 템플릿으로 덮어쓰고, `_inbox/` 내용은 보존한다.

| 파일 | 원본 템플릿 | 역할 |
|------|------------|------|
| `.docs/README.md` | `templates/docs-readme-single.template` | `.docs/` 구조·산출물 종류·스킬별 산출 위치 안내 |
| `.docs/.gitignore` | `templates/docs-gitignore.template` | 로컬 전용(미추적) 영역 지정 |
| `.docs/_inbox/README.md` | `templates/inbox-readme.template` | `_inbox/` 용도 설명 |

```bash
# 안내 README (구조·산출물·스킬 매핑)
cp "[plugin:harness-setup]/templates/docs-readme-single.template" .docs/README.md

# 로컬 전용 영역 지정 .gitignore
cp "[plugin:harness-setup]/templates/docs-gitignore.template" .docs/.gitignore

# 에이전트 임시 입력 공간 _inbox (대표적 로컬 전용 영역)
mkdir -p .docs/_inbox
: > .docs/_inbox/.gitkeep
cp "[plugin:harness-setup]/templates/inbox-readme.template" .docs/_inbox/README.md
```

> **`_inbox/`의 의미**: 에이전트에게 읽힐 파일(스크린샷·로그·표 등)을 잠시 올려두는 공간이다.
> `.docs/.gitignore`가 `/_inbox/*`를 무시하므로 그 안의 파일은 git에 올라가지 않고, `.gitkeep`·`README.md`만 추적되어 폴더 구조만 공유된다.
> 단일 앱에서는 `.docs/`가 소스 레포에 포함되므로, 이 `.gitignore`가 해당 레포의 중첩 `.gitignore`로 동작한다.

---

## 3. 루트 컨텍스트 파일 생성

단일 앱에서 루트 `AGENTS.md`는 공통 컨텍스트 정본이다. 이미 있으면 보존하고, 없으면 `context-doc` 실행을 안내한다.

루트 `CLAUDE.md`는 `@AGENTS.md` bridge만 둔다. 없으면 `templates/claude-bridge.template`로 생성한다.

```bash
cp "[plugin:harness-setup]/templates/claude-bridge.template" CLAUDE.md
```

## 4. legacy local skill copy 읽기 전용 report

`.agents/skills/` 또는 `.claude/skills/`가 있으면 삭제·수정하지 않고 다음만 보고한다.

- 발견 경로
- 스킬 디렉토리명
- `SKILL.md` 존재 여부
- plugin 제공 스킬과 이름 충돌 가능성

제거는 별도 migration 승인 절차가 있을 때만 수행한다.

---

## 5. 결과 정리

생성된 구조를 출력용으로 정리한다:

```
{애플리케이션 루트}/
├── .docs/                  ← 산출물 저장소
│   ├── README.md           ← harness-setup 생성 (구조·산출물 안내)
│   ├── .gitignore          ← harness-setup 생성 (로컬 전용 영역 지정)
│   └── _inbox/             ← 에이전트 임시 입력 공간 (내용 git 미추적)
├── AGENTS.md               ← context-doc이 생성/관리하는 공통 정본
├── CLAUDE.md               ← @AGENTS.md bridge
└── (기존 소스코드)
```

> 📌 단일 애플리케이션에서는:
> - `AGENTS.md`는 `context-doc` 스킬이 생성·관리한다.
> - `CLAUDE.md`는 `@AGENTS.md` bridge다.
> - `.docs/` 이하 산출물은 소스코드와 함께 동일 git 레포에서 형상관리한다.
> - 사용자 스킬은 프로젝트 local copy가 아니라 `ai-agent-harness` 플러그인으로 사용한다.
