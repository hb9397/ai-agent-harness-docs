# Docs — 문서 인덱스

이 디렉토리는 실제 프로젝트 사용자와 하네스 관리자가 현재 적용할 운영 기준을 보관한다.

현재 운영 기준은 루트 [README.md](../README.md), [Harness_Engineering.md](./Harness_Engineering.md), [Plugin_Installation_Guide.md](./Plugin_Installation_Guide.md), 루트 [AGENTS.md](../AGENTS.md)를 우선한다.

---

## 현행 사용자·관리자 운영 문서

| 문서 | 역할 |
|------|------|
| [Plugin_Installation_Guide.md](./Plugin_Installation_Guide.md) | Codex CLI·앱, Claude Code CLI·앱 설치·확인·업데이트·제거 기준과 예시 화면 |
| [Harness_Engineering.md](./Harness_Engineering.md) | 사용자 스킬 정본과 현재 main `0.5.0` runtime 20종, 관리자 3종, 플러그인 흐름, `.ai-docs`·컨텍스트·권한·Markdown 후처리 운영 정본 |
| [Harness_Engineering_Intro.md](./Harness_Engineering_Intro.md) | 플러그인 기반 하네스 도입 배경과 실제 프로젝트 사용·권한 분기 예시 |
| [Multi_App_Doc_Flow_And_Ownership.md](./Multi_App_Doc_Flow_And_Ownership.md) | 복수 앱 프로젝트의 AI 문서 흐름, 문서 소유권, 선택형 3계층 쓰기 권한 제어 |

---

## 현재 프로젝트 시작 기준

```text
모든 참여자: harness-setup을 작업 환경별 최초 1회 수행
→ 단일·복수 repo: 모든 참여자가 git-scoped-account를 자기 PC에서 최초 1회 수행
→ 문서 쓰기 권한을 분리하면 원격 Git provider·저장소·참여자 계정을 먼저 준비
→ 관리자: project-write-access 공유 정책 설정
→ 정책 생성 뒤 모든 참여자: 자기 PC의 로컬 Git·AI 가드 등록
→ 권한 정책이 있으면 역할·앱 범위에 맞게 design-doc·context-doc 사용
→ 권한 정책이 없으면 기존 설계·컨텍스트 흐름을 그대로 사용
```

`harness-setup`은 플러그인 공지가 하네스 갱신을 요구하거나 앱 경계가 바뀌거나 골격 복구가 필요할 때 다시 실행한다. `project-write-access`는 `0.5.0` runtime에 포함되지만 자동 실행되지 않는다. 공유 정책은 관리자가 명시적으로 설정하고, 참여자 PC의 로컬 등록은 관리자 키 없이 각 참여자가 수행한다. 정책이 있는데 현재 PC의 `git-scoped-account` 또는 로컬 등록이 없거나 계정이 다르면 지원되는 AI 가드는 `.ai-docs/**` 쓰기를 거부하며, 애플리케이션 소스코드 권한은 그대로 둔다.

---

## 외부 스킬 관계·거버넌스 문서

| 문서 | 역할 |
|------|------|
| [Skill_Upstream_Governance.md](./Skill_Upstream_Governance.md) | 직접 반입·개념·행동 참조, provenance, license/NOTICE, 최신화·승인·동등성 정책의 사람용 단일 정본 |

---

## 이미지 자료

| 자료 | 비고 |
|------|------|
| [Codex 앱 플러그인 추가 화면](./assets/plugin-install/codex-app-add-marketplace.png) | Codex 앱의 플러그인 마켓플레이스 추가 예시 |
| [Claude 앱 플러그인 추가 화면](./assets/plugin-install/claude-app-add-marketplace.png) | Claude 앱의 마켓플레이스 추가 예시 |

---
