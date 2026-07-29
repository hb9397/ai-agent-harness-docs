---
name: harness-setup
description: >
  프로젝트에 AI 하네스를 설치·설정·갱신한다.
  '하네스 설정', '하네스 세팅', '프로젝트 세팅', '스킬 설치',
  '하네스 설치', 'setup', '초기 설정', '프로젝트 초기화',
  '하네스 갱신', '하네스 업데이트',
  'harness setup', 'harness init' 요청이 오면 이 스킬을 사용한다.
  단일/복수 애플리케이션 프로젝트를 판별하여 .docs 구조와 루트 Agent 컨텍스트를 세팅한다.
  사용자 스킬 설치·갱신은 ai-agent-harness 플러그인이 담당하며, 이 스킬은 프로젝트 local skill copy를 만들거나 덮어쓰지 않는다.
allowed-tools: Read, Write, Glob, Grep, Bash
---

## 스킬 연계

```
ai-agent-harness plugin
    ↓
harness-setup  ← 지금 여기
    ↓
프로젝트 .docs/ 구조 + AGENTS.md 정본 + CLAUDE.md bridge 세팅
    ↓
design-doc, context-doc 등 후속 스킬 사용 가능
```

---

## 책임 경계

이 스킬은 프로젝트 문서 하네스만 관리한다.

| 영역 | 처리 |
|------|------|
| 사용자 스킬 설치·업데이트 | `ai-agent-harness` 플러그인 설치·업데이트가 담당 |
| 프로젝트 `.docs/` 구조 | harness-setup이 생성·갱신 |
| 루트 `AGENTS.md` | harness-setup이 공통 컨텍스트 정본으로 생성·갱신 |
| 루트 `CLAUDE.md` | harness-setup이 `@AGENTS.md` bridge와 Claude 전용 delta만 생성 |
| 기존 `.agents/skills`, `.claude/skills` local copy | 읽기 전용으로 보고하고, 명시 승인 전에는 변경 금지 |

---

## Step 0 — 플랫폼 및 실행 방식 확인

사용자에게 아래를 확인한다:

> 1. 서브에이전트(병렬 처리)를 사용할 수 있는 환경인가요? (Claude Code / Codex / 기타)
> 2. 사용할 경우 병렬 실행을 원하시나요?

서브에이전트 미지원 또는 미사용 선택 시 순차 실행한다.

---

## Step 1 — 실행 컨텍스트 감지

`prompts/detection.md`의 [실행 컨텍스트 감지] 섹션을 참조하여 아래를 판정한다:

| 감지 결과 | 의미 | 다음 동작 |
|-----------|------|-----------|
| 사용자 프로젝트 내부에서 실행 중 | 최초 세팅 또는 갱신 | **현재 위치**를 프로젝트 루트 후보로 설정 → Step 2 |
| 하네스 관리 레포 내부에서 실행 중 | 관리자 작업 위치 | 사용자에게 대상 프로젝트 루트 경로 질문 → Step 2 |
| 판별 불가 | — | 사용자에게 프로젝트 루트 경로를 직접 질문 |

감지 결과를 사용자에게 보여주고 **반드시 확인**받는다:

> "현재 `{감지된 경로}`를 프로젝트 루트로 인식했습니다. 맞습니까?"

---

## Step 2 — 프로젝트 유형 감지 (단일/복수 애플리케이션)

`prompts/detection.md`의 [프로젝트 유형 감지] 섹션을 참조한다.

판정 후 사용자에게 결과를 보여주고 **반드시 확인**한다:

> ✋ **확인 게이트 (C-1)**
>
> 탐색 결과:
> - 프로젝트 유형: **단일 애플리케이션** / **복수 애플리케이션**
> - 프로젝트 루트: `{경로}`
> - (복수인 경우) 감지된 애플리케이션 폴더:
>   - `{앱1 폴더명}` — {근거: package.json / pom.xml / ...}
>   - `{앱2 폴더명}` — {근거}
>   - ...
>
> 맞습니까? **(승인 / 수정 / 취소)**

---

## Step 3 — 초기 세팅 / 갱신 판별

`prompts/detection.md`의 [세팅 모드 판별] 섹션을 참조한다.

| 조건 | 모드 | 다음 |
|------|------|------|
| `.docs/` 또는 `AGENTS.md`가 없음 | **초기 세팅** | Step 4 |
| `.docs/`와 `AGENTS.md`가 존재 | **갱신** | Step 5 |

판별 결과를 사용자에게 알린다:

> "기존 하네스가 **감지되지 않았습니다** / **감지되었습니다**. 초기 세팅 / 갱신을 진행합니다."

`.claude/skills/` 또는 `.agents/skills/`가 발견되면 legacy local skill copy 후보로만 기록한다. 이 단계에서 생성·수정·삭제하지 않는다.

---

## Step 4 — 초기 세팅

Step 2 확인 결과에 따라 분기한다.

### Step 4-A — 단일 애플리케이션 세팅

`prompts/single-app-setup.md` 참조.

핵심 작업:
1. `.docs/` 안내·정책 파일 생성: `.docs/README.md`(구조·산출물 안내), `.docs/.gitignore`(로컬 전용 영역 지정), `.docs/_inbox/`(에이전트 임시 입력 공간, 내용 git 미추적)
2. 루트 `AGENTS.md`가 없으면 공통 컨텍스트 정본 생성 안내
3. 루트 `CLAUDE.md`가 없으면 `@AGENTS.md` bridge 생성
4. 기존 local skill copy가 있으면 읽기 전용 migration report만 출력

### Step 4-B — 복수 애플리케이션 세팅

`prompts/multi-app-setup.md` 참조.

핵심 작업:
1. 프로젝트 최상위 폴더에 구조 생성 (**이 폴더는 `git init` 하지 않는다**)
2. `.docs/` 디렉토리 생성 (별도 git 레포로 관리 예정)
3. 앱별 빈 컨텍스트 파일 생성: `.docs/{앱}-context.md`
4. 앱별 하위 구조 생성: `.docs/{앱}/instruction/`
5. `.docs/root-context/` 생성 (루트 컨텍스트 파일 복사본 보관용)
6. 루트 `AGENTS.md` 생성 (git 미관리, 이 스킬이 단독 관리)
7. 루트 `CLAUDE.md` bridge 생성 (git 미관리, 이 스킬이 단독 관리)
8. `.docs/root-context/AGENTS.md`, `.docs/root-context/CLAUDE.md` 복사본 생성
9. `.docs/` 안내·정책 파일 생성: `.docs/README.md`(구조·산출물 안내), `.docs/.gitignore`(로컬 전용 영역 지정), `.docs/_inbox/`(에이전트 임시 입력 공간, 내용 git 미추적)

루트 `CLAUDE.md`/`AGENTS.md` 작성 시 `templates/root-context.template` 참조.

### Step 4 완료 보고

생성된 구조를 트리 형태로 사용자에게 보여준다.

> **세팅 완료!**
>
> 생성된 구조:
> ```
> {프로젝트 루트}/
> ├── .docs/
> │   ├── README.md           ← 구조·산출물 안내
> │   ├── .gitignore          ← 로컬 전용 영역 지정
> │   ├── _inbox/             ← 에이전트 임시 입력 공간 (내용 git 미추적)
> │   └── ...
> ├── CLAUDE.md
> └── AGENTS.md
> ```
>
> 📌 멀티플랫폼 안내:
> - 스킬은 프로젝트 local copy가 아니라 `ai-agent-harness` 플러그인으로 사용합니다.
> - `AGENTS.md`는 공통 정본, `CLAUDE.md`는 `@AGENTS.md` bridge입니다.

→ Step 6으로 이동.

---

## Step 5 — 갱신 모드

`prompts/update-mode.md` 참조.

핵심 작업:
1. `.docs/` 안내·정책 파일을 최신 템플릿 기준으로 갱신
2. 루트 `AGENTS.md`와 `CLAUDE.md` bridge를 확인·갱신
3. 기존 local skill copy가 있으면 읽기 전용 migration report를 출력
4. 복수앱인 경우 추가로:
   - `.docs/root-context/CLAUDE.md`, `.docs/root-context/AGENTS.md` 갱신
   - 루트 `CLAUDE.md`, `AGENTS.md` 를 `.docs/root-context/` 기준으로 갱신
5. 갱신 전 사용자 확인

> ✋ **확인 게이트**
>
> 갱신 대상:
> - `.docs` 안내·정책: {갱신 필요 / 변경 없음}
> - 루트 컨텍스트: {AGENTS 갱신 필요 / CLAUDE bridge 갱신 필요 / 변경 없음}
> - legacy local skill copy: {읽기 전용 report N건 / 없음}
> - (복수앱) 루트 컨텍스트: {갱신 필요 / 변경 없음}
>
> 진행하시겠습니까? **(승인 / 취소)**

→ Step 6으로 이동.

---

## Step 6 — 최종 결과 보고

세팅 또는 갱신 결과를 요약하여 대화창에 출력한다.
별도 `.md` 파일을 생성하지 않는다.

보고 항목:
1. 프로젝트 유형 (단일/복수)
2. 프로젝트 루트 경로
3. 생성·갱신된 파일 목록 (`.docs/README.md`, `.docs/.gitignore`, `.docs/_inbox/` 포함)
4. (복수앱) 감지된 애플리케이션 폴더 목록
5. `.docs/_inbox/`는 에이전트에게 읽힐 파일을 잠시 올려두는 로컬 전용 공간이며 내용은 git에 올라가지 않는다는 안내
6. 기존 local skill copy가 있으면 승인 전에는 변경하지 않았다는 안내
7. 다음 단계 안내

> **다음 단계:**
> - 설계 시작: `/design-doc`
> - 기존 코드 분석: `/harness-bootstrap`
> - 컨텍스트 문서 생성: `/context-doc`
> - 스킬 최신화 재실행: `/harness-setup`

---

## 문서 개선 후처리

이 스킬이 `AGENTS.md`, `CLAUDE.md`, `.docs/README.md` 같은 Markdown 산출물을 만든 뒤에는 `humanize-korean`의 `document-refinement` 프로필을 선택적으로 제안한다.

- 기본은 개선안 제안만 수행한다.
- 사용자 승인 전에는 생성된 파일을 직접 덮어쓰지 않는다.
- 제목, 표, 경로, 명령어, ID, 숫자, 날짜, 의무 수준 표현은 원문 그대로 보존한다.
