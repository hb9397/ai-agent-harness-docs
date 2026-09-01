# prompts/single-app-setup.md
# 역할: 단일 애플리케이션 프로젝트의 초기 세팅 절차

---

## 전제

- SKILL.md Step 2에서 **단일 애플리케이션** 확정, Step 3에서 **초기 세팅** 판정.
- 프로젝트 루트 = 애플리케이션 루트 (같은 폴더).
- 이 프로젝트는 단일 git 레포로 관리되며, 프로젝트 컨텍스트와 산출물은 이
  레포 안에서 형상관리된다. 사용자 스킬은 프로젝트에 복사하지 않고 설치된
  플러그인에서 제공한다.

---

## 1. 플러그인 설치 상태 안내

이 스킬은 프로젝트 local skill copy를 만들지 않는다. `.agents/skills/`,
`.claude/skills/`, `skills/`는 생성·동기화 대상이 아니다. 사용자가 `design-doc`,
`context-doc` 등 후속 스킬을 아직 사용할 수 없다면 `harness-kit` 플러그인
설치·새 세션 시작을 안내한다.

---

## 2. 산출물 디렉토리 확인

`.docs/` 디렉토리가 없으면 현재 플랫폼의 파일 도구로 생성한다. 특정 shell의
명령 문법을 전제로 하지 않는다.

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

`.docs/`를 처음 만들 때 아래 3종을 함께 생성한다. 대상 파일이 이미 하나라도
있으면 초기 세팅에서 덮어쓰지 않고 갱신 모드의 관리 블록 비교 절차로 넘긴다.
`_inbox/` 내용은 항상 보존한다.

| 파일 | 원본 템플릿 | 역할 |
|------|------------|------|
| `.docs/README.md` | `templates/docs-readme-single.template` | `.docs/` 구조·산출물 종류·스킬별 산출 위치 안내 |
| `.docs/.gitignore` | `templates/docs-gitignore.template` | 로컬 전용(미추적) 영역 지정 |
| `.docs/_inbox/README.md` | `templates/inbox-readme.template` | `_inbox/` 용도 설명 |

템플릿은 `SKILL.md`의 **플러그인 리소스 해석 계약**으로 읽고 다음 대상에 쓴다.

| 번들 리소스 | 대상 |
|-------------|------|
| `templates/docs-readme-single.template` | `.docs/README.md` |
| `templates/docs-gitignore.template` | `.docs/.gitignore` |
| `templates/inbox-readme.template` | `.docs/_inbox/README.md` |

`.docs/_inbox/`가 없으면 디렉토리와 빈 `.gitkeep`을 만든다. 기존
`.docs/_inbox/` 안의 파일은 읽거나 덮어쓰거나 삭제하지 않는다.

> **`_inbox/`의 의미**: 에이전트에게 읽힐 파일(스크린샷·로그·표 등)을 잠시 올려두는 공간이다.
> `.docs/.gitignore`가 `/_inbox/*`를 무시하므로 그 안의 파일은 git에 올라가지 않고, `.gitkeep`·`README.md`만 추적되어 폴더 구조만 공유된다.
> 단일 앱에서는 `.docs/`가 소스 레포에 포함되므로, 이 `.gitignore`가 해당 레포의 중첩 `.gitignore`로 동작한다.

---

## 3. 루트 컨텍스트 파일 생성

단일 앱에서 루트 `AGENTS.md`는 공통 컨텍스트 정본이다.

- 없으면 번들 리소스 `templates/root-context-single.template`을 읽고
  `{{PROJECT_NAME}}`, `{{PROJECT_ROOT}}`를 확정값으로 치환해 생성한다.
- 이미 있으면 사용자 내용을 보존한다. setup 관리 뼈대가 누락됐다는 이유로 기존
  프로젝트 규칙을 덮어쓰지 않으며, `context-doc` 보강 후보로 보고한다.

루트 `CLAUDE.md`는 `@AGENTS.md` bridge만 둔다. 없으면 번들 리소스
`templates/claude-bridge.template`을 읽어 생성한다. 이미 존재하지만 bridge가
아니면 차이를 먼저 보여주고 사용자 승인 후 갱신한다.

## 4. legacy local skill copy 읽기 전용 report

`.agents/skills/`, `.claude/skills/` 또는 `skills/*/SKILL.md`가 있으면
삭제·수정하지 않고 다음만 보고한다.

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
├── AGENTS.md               ← harness-setup이 뼈대 생성, context-doc이 보강
├── CLAUDE.md               ← @AGENTS.md bridge
└── (기존 소스코드)
```

> 📌 단일 애플리케이션에서는:
> - `AGENTS.md` 뼈대는 `harness-setup`이 만들고, 프로젝트 팩트와 instruction
>   인덱스는 `context-doc`이 보강한다.
> - `CLAUDE.md`는 `@AGENTS.md` bridge다.
> - `.docs/` 이하 산출물은 소스코드와 함께 동일 git 레포에서 형상관리한다.
> - 사용자 스킬은 프로젝트 local copy가 아니라 `harness-kit` 플러그인으로 사용한다.
> - `.agents/skills/`, `.claude/skills/`, `skills/`에는 사용자 스킬을 생성하거나
>   동기화하지 않는다.

## 6. 실행 후 불변조건 검증

이번 실행의 생성·변경 목록을 확인한다.

- 허용 경로: `.docs/**`, `AGENTS.md`, `CLAUDE.md`
- 금지 경로: `.agents/skills/**`, `.claude/skills/**`, `skills/**`
- 모든 템플릿 placeholder가 치환됐고 `CLAUDE.md`가 `@AGENTS.md` bridge인지 확인

금지 경로가 변경됐거나 placeholder가 남아 있으면 세팅 성공으로 보고하지 않는다.

## 7. Portable routing bundle

`.docs/harness/`에 routing/format contract, README, installer와 shared hook core를
생성한다. Layer 1은 routing manifest를 참조하고 Layer 2의
`.docs/instruction/artifact-output-routing-instruction.md`를 상세 정본으로 둔다.
현재 앱과 `.docs`의 Git 경계·remote를 읽어 repository id, provider, host,
owner/namespace, 저장소 이름, docs/source 용도와 앱 매핑을
`artifact-routing.json.repositories[]`에 기록한다. remote가 없는 `git init` 상태면
빈 목록과 확인 필요 상태를 사용하고 provider를 추측하지 않는다.
Claude·Codex host-local config와 adapter는 `install-routing.ps1 -Plan`에만 제안하며,
G10 승인 전에는 생성하지 않는다.
