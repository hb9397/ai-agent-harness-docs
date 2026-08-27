---
name: project-write-access
description: "사용자가 프로젝트 문서 쓰기 권한 설정·변경·검증·제거·관리자 교체를 명시적으로 요청할 때만 사용한다. `.docs/**`와 루트 AGENTS.md·CLAUDE.md를 `admin > pm-pl > developer` 역할에 연결하고 GitHub·GitLab·Gitea CODEOWNERS, 표준 Git 훅, Codex·Claude 쓰기 가드를 하나의 서명 정책에서 계획·적용한다. 일반 문서 생성·편집·커밋 요청에는 사용하지 않는다."
allowed-tools: Read, Write, Glob, Grep
disable-model-invocation: true
---

# project-write-access

이 스킬은 문서 하네스를 만들거나 설계·구현 문서를 작성하지 않는다. 이미 존재하는
문서 경로에 쓰기 권한만 연결하는 선택 기능이다. 읽기는 막지 않는다.

명시 호출 예:

- Codex: `$project-write-access 프로젝트 문서 권한을 처음 설정해줘`
- Claude Code: `/harness-kit:project-write-access 현재 권한 정책을 검증해줘`

일반 파일 편집, 문서 생성, 구현, 커밋에서 이 스킬을 자동으로 연결하지 않는다.

## 스킬 리소스 해석

`scripts/`, `assets/`, `prompts/`, `references/`는 현재 로드된
`project-write-access` 스킬 번들을 기준으로 찾는다. 관리 저장소나 사용자 홈의 설치
경로를 추측하지 않는다. 번들 리소스를 읽을 수 없으면 기억으로 재구성하지 말고
적용을 중단한다.

## 진입 분기

| 요청 | 흐름 |
|---|---|
| 최초 설정 | Step 0 → 1 → 2 → 3 → 4 → 5 |
| 계정·역할·경로 정책 변경 | Step 0 → 1 → 2 → 3 → 4 → 5 |
| 상태 확인·괴리 검사 | Step 0 → 1 → 5. 읽기 전용으로 종료 |
| 제거 | Step 0 → 1 → 2 → 제거 계획 → 별도 승인 → 5 |
| 관리자 교체 | Step 0 → 1 → 2 → 교체 계획 → 기존 키 승인 → 별도 승인 → 5 |
| 키 분실 | Step 0 → 1 → 2. 백업 키가 없으면 변경 없이 종료 |

## Step 0 — 범위와 실행 환경 확인

현재 위치에서 저장소 지시문과 Git 경계를 먼저 읽는다. 프로젝트 유형은 다음 중 하나로
판정한다.

- 단일 앱·단일 저장소
- 복수 앱·단일 저장소
- 복수 앱·복수 저장소: `.docs`가 별도 저장소이고 컨테이너 루트는 Git 밖

프로젝트 루트, `.docs` 저장소 경계, 애플리케이션 목록, 보호할 루트
`AGENTS.md`·`CLAUDE.md`의 Git 포함 여부를 보여주고 확인받는다. 소스코드는 보호
범위에 넣지 않는다.

프로젝트 파일을 만드는 작업이므로 이 확인을 생략하지 않는다.

## Step 1 — 읽기 전용 사전 점검

`prompts/workflow.md`의 **사전 점검**을 따른다.

다음을 읽기 전용으로 확인한다.

1. 기존 `.docs/harness/access-control/` 정책·서명·생성 목록
2. Git 작업 폴더, upstream, 앞섬·뒤처짐·분기 상태
3. 세 서비스의 CODEOWNERS 탐색 우선순위와 기존 파일
4. `core.hooksPath`와 기존 `pre-commit`·`pre-push`
5. `.claude/settings.json`, `.codex/hooks.json`, 기존 쓰기 훅
6. 현재 호출자가 제시한 Git 서비스 계정과 관리자 권한 증적

원격이 있으면 인증 정보를 저장하지 않은 채 서비스 API 또는 공식 CLI로 현재 로그인
계정과 저장소 관리자 권한을 확인한다. 구체적인 지원 조건은 요청한 서비스에 해당하는
부분만 `references/provider-capabilities.md`에서 읽는다.

정책 변경 전에 원격 확인이 필요하면 먼저 fetch 계획을 보여주고 별도 승인을 받는다.
작업 폴더가 깨끗하고 fast-forward만 가능한 경우에만 갱신한다. 강제 reset, rebase,
로컬 변경 폐기는 하지 않는다. 뒤처졌거나 이력이 갈라지면 중단한다.

## Step 2 — 신뢰 상태 확인

`references/security-contract.md`의 **관리자 신뢰와 복구**를 따른다.

- 서명 정책이 없으면 최초 설정 후보로 분류한다.
- 정책이 있으면 정책 서명, 프로젝트 식별자, 생성 목록의 관리 영역 해시부터 검증한다.
- Codex와 Claude 전역 키 사본은 같은 공개키 지문이어야 한다.
- 로컬 키가 없어도 사용자가 명시적으로 제시한 백업 키의 지문이 일치하면 사용할 수 있다.
- 정책 파일 삭제만으로 최초 설정으로 되돌리지 않는다.
- 서명·생성 목록·관리 블록이 변조됐으면 어떤 파일도 고치지 않는다.

원격 저장소가 있는 최초 설정은 호출자의 관리자·소유자 권한을 검증한 경우에만
허용한다. 로컬 `git init`뿐인 프로젝트는 첫 호출자를 임시 관리자로 등록하고 정책에
`remote_verification=pending`을 남긴다.

## Step 3 — Plan 생성

읽기 전용 Plan을 먼저 만든다. `prompts/workflow.md`의 **Plan**과
`references/policy-schema.md`를 따른다.

Plan에는 최소한 다음을 포함한다.

- 프로젝트 식별자와 현재·제안 관리자 지문
- 역할별 사용자 식별자와 GitHub·GitLab·Gitea 계정 연결
- 경로별 최소 쓰기 역할과 개발자 개인 경로
- 생성·수정·유지·충돌 파일 목록
- CODEOWNERS가 더 높은 우선순위 파일 때문에 무시되는지 여부
- 기존 Git 훅 연결·복구 계획
- Claude·Codex 설정의 관리 항목 병합 계획과 host 신뢰 상태
- 사용자가 정한 브랜치 규칙의 서버 적용 계획 또는 `미적용`
- 되돌릴 수 없는 외부 상태와 남은 우회 가능성

프로젝트가 정하지 않은 `dev`·`main` 규칙을 새로 만들지 않는다.

번들의 `scripts/project_write_access.py plan`을 사용해 결정론적 파일 Plan과
`plan_hash`를 만든다. 명령 인자와 설정 파일에는 토큰·개인키를 넣지 않는다.

## Step 4 — 적용 승인과 Apply

Plan을 사람에게 보여준 뒤 다음 범위를 나눠 승인받는다.

1. 공유 정책·세 CODEOWNERS·instruction 관리 블록
2. 로컬 `core.hooksPath`와 Git 훅 연결
3. Claude·Codex 프로젝트 훅 설정
4. Git 서비스 API의 브랜치·검토 규칙
5. 최초 키 생성, 관리자 교체 또는 키 폐기

한 번의 포괄 승인으로 다른 범위를 추론하지 않는다. 서버 API 변경에는 해당 저장소의
관리자 권한과 별도 승인이 필요하다.

승인된 로컬 파일 범위는 `scripts/project_write_access.py apply`에 Plan에서 받은
`plan_hash`를 그대로 전달해 적용한다. 다른 해시이면 중단하고 새 Plan을 만든다.
서버 설정은 provider별 현재 값을 다시 읽은 뒤 승인된 필드만 바꾸며, 인증 토큰은
환경이나 공식 CLI 자격 증명 저장소에서만 읽고 출력·파일·로그에 남기지 않는다.

일부 적용이 실패하면 이번 실행이 바꾼 로컬 파일과 Git 설정을 가능한 범위에서
스냅샷으로 복구한다. 이미 바뀐 원격 상태를 되돌리지 못하면 성공으로 보고하지 말고
정확한 차이를 제시한다.

## Step 5 — 재검증과 보고

`scripts/project_write_access.py verify`를 실행하고 다음을 대조한다.

- `policy.json` 서명과 `generated-manifest.json` 해시
- 세 CODEOWNERS 관리 블록과 서비스별 활성 파일 우선순위
- 로컬 Git 훅의 설치 상태와 기존 훅 연결 상태
- AI instruction 관리 블록과 Claude·Codex host 훅 상태
- 세 계층이 같은 `policy_core_sha256`을 가리키는지
- 원격 브랜치·검토 규칙의 실제 상태

최종 보고는 `적용`, `미적용`, `충돌`, `검증 불가`, `복구 필요`를 구분한다.
CODEOWNERS만 생성된 상태나 로컬 훅만 설치된 상태를 완전한 권한 강제로 표현하지
않는다.

## 제거·관리자 교체

제거와 교체도 Plan과 Apply를 나눈다. 세부 흐름은 `prompts/workflow.md`의 해당
섹션을 따른다.

- 제거는 관리 블록과 이 스킬이 설치한 연결만 대상으로 한다.
- 기존 사용자 본문, 다른 CODEOWNERS 규칙, 기존 훅 파일은 보존한다.
- `core.hooksPath`는 설치 전에 기록한 값으로만 복구한다.
- 관리자 교체는 기존 또는 백업 관리자 키로 현재 정책을 검증한 뒤 수행한다.
- 키를 모두 잃으면 정책 변경·삭제·관리자 초기화를 허용하지 않는다. Git 이력과
  저장소 운영자가 정한 별도 복구 절차로 넘긴다.

## 실제 강제력의 경계

- CODEOWNERS는 서버 보호 규칙과 결합해야 승인 없는 병합을 막는다.
- 로컬 훅은 `--no-verify`, 설정 변경, 다른 PC로 우회할 수 있다.
- Claude `PreToolUse`는 지원 도구 호출을 막지만 사람의 편집과 별도 프로세스는 못 막는다.
- Codex 프로젝트 훅은 설치 후 사용자가 host의 훅 목록과 신뢰 상태를 확인하기 전까지
  `pending-trust`다.
- 복수 저장소 구조에서 Git 밖의 루트 `AGENTS.md`·`CLAUDE.md`는 CODEOWNERS와 Git
  훅으로 보호할 수 없다. AI 훅·운영체제 파일 권한·형상관리 구조 변경이 필요하다.

이 한계를 바꾸거나 축소해 설명하지 않는다.
