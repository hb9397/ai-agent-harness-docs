# Docs — 문서 인덱스

이 디렉토리는 실제 프로젝트 사용자와 하네스 관리자가 현재 적용할 운영 기준을 보관한다.

현재 운영 기준은 루트 [README.md](../README.md), [Harness_Engineering.md](./Harness_Engineering.md), [Plugin_Installation_Guide.md](./Plugin_Installation_Guide.md), 루트 [AGENTS.md](../AGENTS.md)를 우선한다.

---

## 현행 사용자·관리자 운영 문서

| 문서 | 역할 |
|------|------|
| [Plugin_Installation_Guide.md](./Plugin_Installation_Guide.md) | Codex CLI·앱, Claude Code CLI·앱 설치·확인·업데이트·제거 기준과 예시 화면 |
| [Harness_Engineering.md](./Harness_Engineering.md) | 사용자 스킬 정본 20종, stable `0.4.3` runtime 19종, 관리자 3종, 플러그인 흐름, `.docs`·컨텍스트·권한·Markdown 후처리 운영 정본 |
| [Harness_Engineering_Intro.md](./Harness_Engineering_Intro.md) | 플러그인 기반 하네스 도입 배경과 실제 프로젝트 사용·권한 분기 예시 |
| [Multi_App_Doc_Flow_And_Ownership.md](./Multi_App_Doc_Flow_And_Ownership.md) | 복수 앱 프로젝트의 AI 문서 흐름, 문서 소유권, 선택형 3계층 쓰기 권한 제어 |

---

## 현재 프로젝트 시작 기준

```text
모든 참여자: harness-setup을 작업 환경별 최초 1회 수행
→ 복수 repo: 모든 참여자가 git-scoped-account를 로컬 컨테이너별 최초 1회 수행
  단일 repo: 현재 유효한 Git 작성자 계정의 값과 출처를 최초 1회 확인
→ 문서 쓰기 권한을 분리하면 관리자: project-write-access 설정
→ 권한 정책이 있으면 역할·앱 범위에 맞게 design-doc·context-doc 사용
→ 권한 정책이 없으면 기존 설계·컨텍스트 흐름을 그대로 사용
```

`harness-setup`은 플러그인 공지가 하네스 갱신을 요구하거나 앱 경계가 바뀌거나 골격 복구가 필요할 때 다시 실행한다. `project-write-access`는 관리 저장소 정본에는 있지만 stable `0.4.3` runtime에는 포함되지 않는다.

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
