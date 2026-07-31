# Phase 10 릴리스 회귀검증

생성 시각: 2026-07-29T00:00:00+00:00

## 요약

- 전체 상태: `not-release-ready`
- 플러그인: `ai-agent-harness` `0.2.1`
- 아카이브 SHA-256: `ed5d08a52b99955b1b1d488ef3311161f011e8188d6e33253a9aa9c05e8b99cb`
- 릴리스 게이트: `not-release-ready`
- push/tag/release 생성: `false`

## 검사

| 검사 | 결과 |
|---|---|
| `source_projection_integrity` | 통과 |
| `reproducible_build` | 통과 |
| `static_local_links` | 통과 |
| `upstream_modes_fixture` | 통과 |
| `user_contract_fixture` | 통과 |
| `failure_rollback` | 통과 |
| `release_gate` | 통과 |

## 릴리스 결정

`codex-cli, codex-desktop-app, claude-code-cli, claude-desktop-code`에 대한 대화형 증적이 아직 필요하므로 이 후보는 `not-release-ready` 상태를 유지한다. 격리된 Codex 및 Claude CLI 설치 스모크 검사는 통과했다. 이 스크립트는 `released` 잠금 상태를 갱신하지 않으며 태그 또는 릴리스를 생성하지 않는다.

## 롤백

격리 픽스처에서 이전 `released` 잠금과 플러그인 버전을 복원하는 방식으로 롤백을 검증했다. 실제 작업공간은 파괴적 시나리오에 대해 읽기 전용이다.
