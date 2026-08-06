# 최종 준비 상태 감사

생성 시각: 2026-07-29T00:00:00+09:00

> 역사 기록. 이 감사는 릴리스 후보 `0.1.0`을 설명한다. 현재 후보는
> `harness-kit` `0.4.2`이며 최신 상태는 `release-checklist.md`와
> `install-verification.json`을 따른다. `0.1.0`의 CLI 설치 smoke 증적은 현재
> 후보에 적용되지 않는다.

## 요약

`improvement_plan/20260729/플러그인 전환 및 스킬 거버넌스 리팩토링 작업 계획서.md`의 구현 계획은 Phase 0부터 Phase 10까지다. 현재 계획에 Phase 11은 없다.

이 저장소에서 Phase 0부터 Phase 10까지의 구현 작업은 완료했다. 격리된 Codex 및 Claude Code CLI 설치·캐시 스모크 검사는 통과했다. 이 스모크 검사는 모델을 호출하지 않는다. 네 가지 CLI/App 표면 모두에서 직접 스킬 호출, 출력, 재시작, 새 세션 증적이 아직 필요하므로 현재 릴리스 후보는 **`not-release-ready`** 상태다.

push, tag, GitHub release 생성 또는 `released` lock 갱신은 수행하지 않았다.

## 릴리스 후보

| 항목 | 값 |
|---|---|
| 플러그인 ID | `ai-agent-harness` |
| 버전 | `0.1.0` |
| 아카이브 | `plugins/ai-agent-harness-0.1.0.zip` |
| 아카이브 SHA-256 | `f15060671deaedcd195760e738ba491be29a4e25c19e5e0d32336409311efd47` |
| 논리 사용자 스킬 수 | 18 |
| 관리자 스킬 수 | 3 |
| Codex 물리 스킬 / agent 수 | 18 / 0 |
| Claude 물리 스킬 / agent 수 | 18 / 0 |
| Markdown 생성 스킬 handoff 수 | 7 |

## 자동화 증적

| 증적 | 결과 |
|---|---|
| 소스/projection 무결성 | 통과 |
| 재현 가능한 빌드 | 통과 |
| 정적 로컬 링크 | 통과 |
| upstream 3-mode 격리 계약 fixture | 통과, 실제 stage/promote는 미수행 |
| 사용자 파일시스템/스크립트 계약 fixture | 통과, 실제 agent 스킬 호출은 미수행 |
| 실패 rollback fixture | 통과, 실제 표면 취소/rollback은 미수행 |
| 정본 스킬 eval runner | 통과(자동 탐색된 runner 10개) |
| Codex CLI 격리 설치/캐시 스모크 | 통과(`0.146.0`, 스킬 18개 / agent 0개), 모델 호출은 미수행 |
| Claude Code 격리 설치/캐시 스모크 | 통과(`2.1.220`, 스킬 18개 / agent 0개), 모델 호출은 미수행 |
| 릴리스 회귀 gate | `not-release-ready` 상태로 통과 |

## 릴리스 표면 증적

| 표면 | 상태 | 근거 |
|---|---|---|
| Codex CLI | `install-smoke-verified` | marketplace 등록, plugin 등록/목록 확인, 캐시 검사, 제거 및 정리를 통과했으며 직접 모델 호출은 대기 중이다. |
| Codex Desktop/App | `manual-required` | 대화형 앱의 plugin 설치/업데이트 증적은 이 shell에서 완료할 수 없다. |
| Claude Code CLI | `install-smoke-verified` | strict 검증, marketplace 등록, plugin 설치/목록 확인, 캐시 검사, 제거 및 정리를 통과했으며 직접 모델 호출은 대기 중이다. |
| Claude Desktop Code | `manual-required` | Desktop Code 로컬/SSH 캐시 검증에는 Claude Desktop 앱 표면이 필요하다. |

## 릴리스 전 남은 작업

1. Codex CLI와 Claude Code CLI에서 `harness-setup` 및 `humanize-korean`을 직접 호출하고 시나리오 A-D를 수행한 뒤, 검토자가 승인한 기록을 수집한다.
2. Codex Desktop/App에서 직접 호출, 재시작/새 작업, marker/version 및 시나리오 A-D 증적을 수집한다.
3. Claude Desktop Code 로컬 호스트에서 직접 호출, 재시작/새 세션 및 시나리오 A-D 증적을 수집한다. SSH를 지원 표면으로 선언한 경우에만 SSH에서도 반복한다.
4. 각 표면의 상태를 `verified`로 바꾸기 전에 검토를 마친 네 개 기록을 릴리스 체크리스트에 연결한다.

## 릴리스 통제

- 릴리스 준비 완료: 아니요
- push 생성: 아니요
- tag 생성: 아니요
- GitHub release 생성: 아니요
- `released` lock 갱신: 아니요
- 배포 전 명시적인 관리자 승인 필요: 예
