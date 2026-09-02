# 변경 이력

이 문서는 `harness-kit` 사용자 플러그인의 주요 변경 사항을 기록한다.

## [0.6.1] - 2026-09-02

### 변경

- `design-doc`의 `DESIGN.md` 구조를 개요, 구축 대상 기능 분류, 기술 스택, 아키텍처,
  애플리케이션 특이사항, 배포 환경, VSCode 익스텐션 추천 순서로 정규화했다.
- 최초 설계는 기능 대분류만 잡고, 재실행 시 개발자가 선택한 기능 분류 Depth를 현재
  사실 기준으로 반영하도록 했다.
- `context-doc`의 앱 컨텍스트를 10개 섹션으로 정리하고 `DESIGN.md`와 개요·아키텍처·
  특이사항·기능 분류를 양방향 추적하도록 했다.
- 최초 instruction을 목적 중심 골격으로 생성하고, 현재 규칙으로 갱신하거나 불필요한
  파일을 승인 후 제거하는 생명주기를 추가했다.
- 앱 컨텍스트와 instruction 본문에는 변경 이력을 쌓지 않고 현재 사실만 유지하도록 했다.

### 배포 상태

- `0.6.1`은 로컬 배포 후보다. tag, GitHub Release와 push는 아직 수행하지 않았다.
- `0.6.1` 아카이브 SHA-256은 `aa681b5996e0a28f2484780620897f104afc81d19bab2a71066ee1d50aff4900`이다.

## [0.5.0] - 2026-08-28

### 추가

- 명시 호출 전용 `project-write-access`를 사용자 runtime에 추가했다. 검증된 관리자가 서명 정책을 만들고 GitHub·GitLab·Gitea용 CODEOWNERS, 로컬 Git 훅, Codex·Claude 쓰기 가드를 같은 문서 권한 모델로 설정한다.
- `admin`, `pm-pl`, 앱별 `app-doc-lead`, 일반 기여자의 `team` 범위를 구분했다. `admin`이 앱 핵심 문서를 대신 수정할 때는 권한 전용 추가 확인을 요구한다.

### 변경

- 사용자 스킬 정본, capability inventory와 Codex·Claude runtime을 모두 20종으로 맞췄다.
- `harness-setup`과 Git 계정 확인 뒤 권한 정책을 먼저 설정하고, 허용된 역할·앱 범위에서 `design-doc`, `context-doc`, `harness-bootstrap`을 사용하는 흐름을 문서화했다.
- 플러그인·산출물 라우팅·실행 파일·평가 범위·upstream provenance 기준선을 `0.5.0`에 맞췄다.
- Windows에서도 권한 스킬의 한글 JSON 회귀검사가 UTF-8로 일관되게 동작하도록 평가 실행기의 자식 프로세스 인코딩을 고정했다.
- CLI 설치 smoke 결과를 `maintainer/plugin/cli-smoke.json`에 명시적으로 기록해 다음 릴리스 검사가 이전 버전 증적을 재사용하지 않도록 관리자 검증 명령을 바로잡았다.
- 확장자 없는 `pre-commit`·`pre-push` 셸 자산도 실행 정책 검사 대상에 포함해 권한 스킬의 전체 실행 표면을 검증한다.

### 배포 상태

- `0.5.0`은 main 배포 후보다. tag와 GitHub Release는 아직 만들지 않았으며 게시된 최신 stable은 `v0.4.3`이다.
- `0.5.0` 아카이브 SHA-256은 `3d9c244c5f8788eb0bd010bc37098ae1910b4dd1a0b960afe01059af3dad1b62`이다.
- Codex CLI와 Claude Code CLI의 격리 marketplace 등록, 설치, 캐시 확인과 제거 smoke를 통과했다.
- Codex·Claude CLI·앱의 실제 모델 호출 수동 증적은 별도 릴리스 게이트로 남는다.

## [0.4.3] - 2026-08-11

### 호환성 변경

- 플러그인 ID와 패키지 경로를 `ai-agent-harness`에서 `harness-kit`으로 변경했다. 기존 marketplace 설치는 제거한 뒤 `harness-kit@hb9397`을 설치해야 한다.
- 독립 `pre-commit` 스킬과 scanner를 제거했다. 커밋은 명시 호출 전용 `commit` 스킬과 프로젝트의 기존 hook·검증 명령을 사용한다.
- 프로젝트에 복사해 둔 `.agents/skills/**`, `.claude/skills/**`, `skills/**`는 자동으로 삭제하지 않는다. 먼저 읽기 전용으로 분류하고 백업·삭제는 사용자가 승인한 경우에만 수행한다.

### 추가

- 단일 앱과 복수 앱 모두에서 프로젝트가 소유하는 artifact routing 계약을 추가했다. Markdown producer는 각각 `.docs/instruction/artifact-output-routing-instruction.md` 또는 `.docs/{앱}/instruction/artifact-output-routing-instruction.md`를 기준으로 산출물의 위치·소유권·인계를 결정한다.
- 선택형 host-local write guard와 외부 artifact 정규화 흐름을 추가했다. 외부 텍스트는 `normalize-artifact.ps1 -Plan` 제안을 확인하고 명시적으로 승인한 뒤에만 정본에 반영한다.
- `ui-ux-pro-max` runtime과 provenance를 upstream `v2.13.0` 기준으로 갱신했다.

### 변경

- Codex와 Claude runtime을 사용자 스킬 19종, 에이전트 0개로 맞췄다.
- `motion-design`의 역할을 사용자 작업 흐름에 명시하고 디자인 시스템의 모션 명세 경로와 reduced-motion 기준을 정리했다.
- Markdown producer를 고정 7종과 조건부 2종, 총 9종으로 명시하고 승인형 `humanize-korean` handoff를 정리했다.
- `create-prototype`은 project-owned `.docs/prototype/**` 또는 `.docs/{앱}/prototype/**`에 폐기 가능한 검증 시안을 만들고, `frontend-design`은 승인된 제품 소스에 실제 UI를 구현하도록 책임 경계를 분리했다.
- 하네스 설치·설계·구현·검증·문서·커밋 흐름과 단일/복수 앱 산출물 위치를 사용자 문서에 맞춰 정리했다.

### 검증 범위와 알려진 제한

- `0.4.3` 아카이브 SHA-256은 `0385680650cca7827b8f71445a9e7aa6e1d630997e0167a6f4094e38f14e2d76`이며, 정본은 [`maintainer/plugin/release.json`](./maintainer/plugin/release.json)이다.
- Codex CLI와 Claude Code CLI의 격리 marketplace 등록, 설치, 목록·cache 확인, 제거 smoke는 통과했다.
- 위 smoke는 실제 모델 호출 검증이 아니다. Codex CLI·Codex 앱·Claude Code CLI·Claude 앱 네 인터페이스의 직접 호출, 산출물, 재시작과 새 세션 수동 증적은 아직 남아 있다.
- 정식 태그 게시와 별개로, 위 수동 증적이 없으므로 저장소 내부 릴리스 게이트 상태는 `not-release-ready`다.
- host-local write guard는 관찰 가능한 쓰기 요청만 점검한다. 동적 shell 경로, hosted tool, 외부 process를 완전히 차단하지 못하며 해당 경우는 bypass evidence로 기록한다.

자세한 설치 및 마이그레이션 방법은 [`v0.4.3` 릴리스 노트](./maintainer/plugin/release-notes/v0.4.3.md)를 참고한다.

[0.4.3]: https://github.com/hb9397/harness-kit/releases/tag/v0.4.3
