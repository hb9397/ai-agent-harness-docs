# 플러그인 릴리스 체크리스트

생성 시각: 2026-07-29T00:00:00+00:00

## 릴리스 후보

- 플러그인 ID: `ai-agent-harness`
- 버전: `0.2.0`
- 아카이브: `plugins/ai-agent-harness-0.2.0.zip`
- 아카이브 SHA-256: `a0e64c04fd1f797851d6ed656ad1da14112124e263754e1d5410dece6316f4bd`
- Codex 물리 스킬 수: 20
- Codex 물리 에이전트 수: 0
- Claude 물리 스킬 수: 20
- Claude 물리 에이전트 수: 0
- Markdown 생성 스킬 handoff 수: 9

## 자동화된 로컬 검사

| 검사 | 결과 |
|---|---|
| manifest 이름/버전 일치 | 통과 |
| 아카이브 체크섬과 릴리스 메타데이터 일치 | 통과 |
| 패키징된 adapted/vendored NOTICE-license-lock 완결성 | 통과 |
| `released` 상태 보존 | 통과 |
| `humanize-korean`이 제안만 수행 | 통과 |
| `humanize-korean`이 원본 파일을 변경하지 않음 | 통과 |
| 보호 토큰 보존 | 통과 |

## 표면별 증적

| 표면 | 상태 | 증적 |
|---|---|---|
| Codex CLI | `blocked` | CLI 스모크 증적이 불완전하거나 실패함 |
| Codex Desktop/App | `manual-required` | 대화형 Plugins UI 설치/업데이트에는 앱 표면이 필요하므로 이 셸에서 완료할 수 없음 |
| Claude Code CLI | `blocked` | CLI 스모크 증적이 불완전하거나 실패함 |
| Claude Desktop Code | `manual-required` | Desktop Code 로컬/SSH 캐시 검증에는 Claude Desktop 앱 표면이 필요함 |

## 릴리스 게이트

상태: **`not-release-ready`**

사유: 격리된 CLI 설치 증적이 불완전하며, 네 가지 CLI/App 표면 모두 직접 모델 호출 증적이 필요하다.

## 완료한 자동 설치 검사

- CLI 설치 스모크: 불완전.

## `release-ready` 전 필수 작업

- Codex 및 Claude Code CLI: 공식 CLI로 `scripts/smoke_cli_install.py`를 실행하고 통과 증적을 보존한다.
- 직접 테스트 기록: `maintainer/plugin/manual-surface-test-template.md`를 `maintainer/plugin/manual-evidence/YYYYMMDD/{surface}.md`로 복사하고 표면마다 새로운 픽스처 하나를 보존한다.
- 네 표면 모두: `harness-setup`과 `humanize-korean`을 호출하고, 제안 전용 동작과 생성된 허용 목록을 검증하며, `.agents/skills`, `.claude/skills`, `skills`가 생성되지 않았는지 확인하고 관리 블록 확장을 보존한다.
- 네 표면 모두: 새 작업/세션을 다시 열어 같은 산출물 지문을 다시 제안하지 않는지 확인하고 `.docs/.harness/humanize-handoffs.json` 이벤트를 보존한다.
- 네 표면 모두: 제안된 쓰기 전에 취소하고 원본 해시와 사용자 감시 토큰이 보존되는지 확인한다.
- Codex 앱: 후보 마켓플레이스를 설치하고 재시작/새 작업에서 표식/버전을 확인한 뒤 vN+1로 업데이트한다.
- Claude Desktop Code: 로컬 호스트의 캐시/버전을 확인하고 앱을 재시작해 새 세션을 연다. SSH를 지원 표면으로 선언한 경우에만 SSH에서도 반복한다. 지원하지 않는 클라우드/WSL 경로를 문서화한다.
- 표면 상태를 `verified`로 변경하기 전에 검토자가 승인한 직접 테스트 기록을 이 체크리스트에 연결한다.
- 레거시 이전: 읽기 전용 목록 조사를 수행하고, 명시적 승인이 있을 때만 백업/제거를 실행한 뒤 플러그인이 한 번만 탐색되는지 확인한다.
