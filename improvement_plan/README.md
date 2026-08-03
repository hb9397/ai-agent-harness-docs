# improvement_plan — 리팩토링 의사결정·점검 이력

이 디렉터리는 하네스 구조 변경의 계획과 점검 기록을 보관한다. 현행 운영 기준은 루트 [README.md](../README.md), [.user-docs/Plugin_Installation_Guide.md](../.user-docs/Plugin_Installation_Guide.md), [.user-docs/Harness_Engineering.md](../.user-docs/Harness_Engineering.md)를 우선한다.

---

## 현행 계획

| 위치 | 상태 | 설명 |
|------|------|------|
| [20260803/260803-1.harness-kit-plugin-rename-and-example-removal-impl-doc.md](./20260803/260803-1.harness-kit-plugin-rename-and-example-removal-impl-doc.md) | Phase 6 완료 / Phase 7~8 대기 | plugin ID를 `harness-kit`, marketplace를 `hb9397`로 전환하고, root `example/`을 외부 저장소 없이 제거하며 산출물 routing·impl downstream 계약을 정립하는 impl-doc 계획 |
| [20260801/260801-1.user-docs-migration-and-education-removal-impl-refactor.md](./20260801/260801-1.user-docs-migration-and-education-removal-impl-refactor.md) | 구현 대기 | 루트 `.user-docs/`를 `.user-docs/`로 이전하고 `education/`을 제거한 뒤, 정본·projection·플러그인 `0.2.2` 재빌드와 Codex·Claude 기술 회귀검증을 수행하는 impl-doc 계획 |
| [20260729/플러그인 전환 및 스킬 거버넌스 리팩토링 작업 계획서.md](./20260729/플러그인%20전환%20및%20스킬%20거버넌스%20리팩토링%20작업%20계획서.md) | Phase 0~10 구현 완료 / 직접 표면 검증 대기 | 사용자 플러그인 전환, 관리자/사용자 스킬 분리, upstream governance, 문서 최신화, release gate 구현 완료. Codex CLI·Claude Code CLI의 로컬 marketplace 설치 smoke는 통과했고 Codex·Claude CLI/앱 네 표면의 실제 모델 호출 증적과 관리자 최종 승인이 남아 있음 |

---

## 역사 자료

아래 문서는 당시 기준 기록이다. 본문을 byte-preserve하기 위해 Phase 9에서는 파일 자체에 header를 추가하지 않는다.

| 문서 | 현재 기준과 다른 점 |
|------|---------------------|
| [리팩토링 작업 계획서.md](./20260627/리팩토링%20작업%20계획서.md) | clone/copy 기반 설치, `agent-sync` 존치, `rfp-ingest` 존치 등 과거 기준 포함 가능 |
| [스킬셋_리팩토링_1차_점검_보고서.md](./20260627/스킬셋_리팩토링_1차_점검_보고서.md) | 과거 점검 결과. 현행 플러그인 payload/관리자 분리 기준과 다를 수 있음 |
| [스킬셋_리팩토링_2차_점검_보고서.md](./20260627/스킬셋_리팩토링_2차_점검_보고서.md) | 과거 점검 결과. 현행 `AGENTS.md` 정본·`CLAUDE.md` bridge 기준과 다를 수 있음 |
| [스킬셋_리팩토링_3차_점검_보고서.md](./20260627/스킬셋_리팩토링_3차_점검_보고서.md) | 과거 점검 결과. 현행 사용자 18종·관리자 3종 분리 기준과 다를 수 있음 |
| [20260627/](./20260627/) | 과거 리팩토링 의사결정 디렉터리. 현행 운영 기준이 아님 |

---

## 현행 기준 요약

- 실제 프로젝트 사용자는 이 저장소를 clone하거나 `.agents/.claude` 스킬을 복사하지 않는다.
- 사용자 프로젝트는 `ai-agent-harness` 플러그인을 설치한 뒤 `harness-setup`을 실행한다.
- 사용자 스킬은 19종, 관리자 스킬은 3종이다.
- `agent-sync`와 `rfp-ingest`는 제거됐다.
- `custom-skill-design`은 관리자 스킬이다.
- `humanize-korean`은 `im-not-ai`에서 적응 반영한 직접 반입형 스킬이며, 별도 `im-not-ai` 설치 없이 플러그인에서 사용한다.
- 최종 readiness 감사는 [maintainer/plugin/final-readiness-audit.md](../maintainer/plugin/final-readiness-audit.md)와 [maintainer/plugin/final-readiness-audit.json](../maintainer/plugin/final-readiness-audit.json)에 기록한다.
- 현재 릴리스 후보는 자동 회귀 검증과 Codex CLI·Claude Code CLI의 격리 설치
  smoke를 통과했다. Codex App·Claude Desktop Code의 직접 증적이 없어
  `not-release-ready` 상태다.

과거 문서를 볼 때는 위 기준을 우선 적용한다.
