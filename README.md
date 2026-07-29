# AI Agent Harness — 관리 저장소

이 저장소는 실제 프로젝트에서 직접 clone해서 쓰는 하네스가 아니라, **Codex와 Claude에서 함께 사용할 사용자용 `ai-agent-harness` 플러그인을 만들고 관리하는 원본 저장소**다.

실제 프로젝트 수행자는 이 저장소를 프로젝트 옆에 복사하거나 `.agents/skills`, `.claude/skills`를 직접 동기화하지 않는다. 먼저 플러그인을 설치한 뒤 프로젝트 안에서 `harness-setup`을 실행한다.

현재 릴리스 후보:

- Plugin ID: `ai-agent-harness`
- Version: `0.1.0`
- Archive: `plugins/ai-agent-harness-0.1.0.zip`
- 사용자 스킬: 18종
- Codex runtime: 18 skills / 0 agents
- Claude runtime: 18 skills / 0 agents
- 관리자 스킬: 3종, 이 저장소 안에서만 사용
- 릴리스 상태: `not release-ready` — 공식 패키지·CLI 자동 검증 후에도 Codex/Claude 앱 수동 증적이 모두 필요함

상세 설치 절차는 [Docs/Plugin_Installation_Guide.md](./Docs/Plugin_Installation_Guide.md)를 먼저 본다.

---

## 플러그인 적용 요약

### Codex

- CLI: `codex plugin marketplace add <이 저장소 URL 또는 루트 경로>` 후
  `codex plugin add ai-agent-harness@ai-agent-harness`로 설치한다.
- Codex Desktop/App: Plugins UI에서 Git-backed marketplace repository 또는 local marketplace root를 추가하고 새 task/session에서 스킬 노출을 확인한다.
- IDE extension: Phase 8 기준 별도 플러그인 설치 표면으로 보지 않는다. Codex CLI/App 플러그인 설치를 우선한다.

### Claude

- Claude Code CLI: `claude plugin marketplace add <이 저장소 URL 또는 루트 경로>` 후
  `claude plugin install ai-agent-harness@ai-agent-harness`로 설치하고 `/reload-plugins`를 수행한다.
- Claude Desktop Code 탭: local 또는 SSH host cache 기준으로 설치·재시작·새 session 확인이 필요하다.
- Claude Chat/Cowork: Code 플러그인과 별도 구성으로 취급한다. 같은 스킬셋을 쓰더라도 설치·권한·캐시 검증은 별도 문서화한다.

시스템 PATH의 Codex/Claude 명령 상태와 무관하게 임시 플랫폼 설정만 사용하는 공식 CLI
패키지로 설치 smoke를 수행한다. 현재 증적은 Codex CLI `0.146.0`과 Claude Code
`2.1.220`에서 marketplace 등록, plugin 설치, 18 skills / 0 agents 확인, 제거까지
통과했다. CI가 같은 흐름을 반복하며 앱 설치·재시작·새 세션 확인은 수동 증적으로
별도 유지한다.

---

## 관리자 저장소와 사용자 프로젝트 역할

| 영역 | 역할 | 사용 주체 |
|------|------|-----------|
| 이 저장소 `skills/` | 사용자 플러그인에 들어갈 사용자 스킬 정본 18종 | 하네스 관리자 |
| 이 저장소 `maintainer/skills/` | 플러그인 빌드, upstream 최신화, custom skill 설계 관리자 스킬 3종 | 하네스 관리자 |
| 이 저장소 `.agents/skills`, `.claude/skills` | 관리자 스킬 repo-local projection | 하네스 관리자 |
| `plugins/ai-agent-harness/` | 사용자 플러그인 릴리스 후보 | 하네스 관리자 |
| 실제 프로젝트 | 플러그인 설치 후 `harness-setup`으로 `.docs`, `AGENTS.md`, `CLAUDE.md`만 생성·갱신 | 프로젝트 수행자 |

관리자는 이 저장소에서 사용자 스킬과 플러그인 산출물을 관리한다. 사용자는 프로젝트에서 플러그인을 설치하고 스킬을 호출한다.

---

## 실제 프로젝트 시작 흐름

```text
플러그인 설치
→ 새 session/task 또는 /reload-plugins
→ harness-setup
→ 사용자 프로젝트 출력 allowlist 확인(.docs/**, AGENTS.md, CLAUDE.md)
→ 요구사항/RFP 직접 입력 또는 기존 코드베이스 분석
→ design-doc / context-doc / harness-bootstrap
→ impl-doc 또는 impl-fe-be-doc
→ 원 producer 검증
→ 최외곽 producer가 bundle당 한 번만 humanize-korean 개선안·diff 제안
→ 승인된 변경만 반영
→ 원 producer의 link·index·bridge·구조 재검증
→ 승인된 최종 Markdown을 다음 구현·검증 스킬에 입력
```

RFP는 더 이상 `rfp-ingest` 스킬로 받지 않는다. 사용자는 RFP 파일이나 요구사항 내용을 `design-doc`, `design-prototype-docs`, `impl-*` 요청에 직접 첨부하거나 대화 컨텍스트로 제공한다.

---

## 단일/복수 앱과 `.docs` 기준

### 단일 애플리케이션

애플리케이션 repo 안에서 소스코드와 하네스 산출물을 함께 관리한다.

```text
my-app/
├── .docs/
├── AGENTS.md
├── CLAUDE.md
└── src/
```

### 복수 애플리케이션

프로젝트 최상위 폴더는 git으로 관리하지 않고, 앱 repo와 `.docs` repo를 분리한다.

```text
my-project/
├── app-frontend/
├── app-backend/
├── .docs/              ← 별도 git repo 권장
├── AGENTS.md           ← 실행용, 보통 git 미관리
└── CLAUDE.md           ← AGENTS.md를 읽는 bridge
```

복수 앱에서 `.docs/root-context/AGENTS.md`가 루트 컨텍스트의 관리 원본이다. `CLAUDE.md`는 중복 정본이 아니라 `AGENTS.md`를 읽도록 안내하는 bridge로 둔다.

---

## 사용자 스킬 18종

| 계열 | 스킬 |
|------|------|
| 설치·기반 | `harness-setup`, `harness-bootstrap`, `git-scoped-account` |
| 설계·컨텍스트 | `design-doc`, `context-doc`, `design-prototype-docs`, `create-prototype`, `frontend-design` |
| 구현 계획·검증 | `impl-doc`, `impl-fe-be-doc`, `impl-reuse-scan`, `impl-verify` |
| 품질·운영 | `multi-review`, `pre-commit`, `commit`, `code-comment`, `doc-audit` |
| 문서 개선 | `humanize-korean` |

`agent-sync`와 `rfp-ingest`는 제거됐다. `.agents/skills`와 `.claude/skills`를 직접 맞추는 작업은 더 이상 사용자 프로젝트 흐름이 아니다.

`harness-setup`은 사용자 프로젝트에 `.agents/skills/`, `.claude/skills/` 또는
`skills/`를 새로 만들지 않으며, 그 아래로 스킬을 복사·동기화하지도 않는다.
프로젝트에 이미 같은 경로가 있으면 읽기 전용으로 분류·보고하고 승인 없이 변경하지
않는다.

---

## 관리자 스킬 3종

| 스킬 | 위치 | 역할 |
|------|------|------|
| `custom-skill-design` | `maintainer/skills/custom-skill-design` | 새 스킬 설계·생성·검증 |
| `skill-portfolio-maintainer` | `maintainer/skills/skill-portfolio-maintainer` | 외부 공식·유명 스킬 참고/반입 후보 탐색, provenance, 안전한 최신화 |
| `harness-plugin-maintainer` | `maintainer/skills/harness-plugin-maintainer` | 사용자 플러그인 build, validate, release gate 관리 |

관리자 스킬은 사용자 플러그인 payload에 포함하지 않는다.

---

## `humanize-korean`과 upstream 관계

`humanize-korean`은 `epoko77-ai/im-not-ai`의 주요 아이디어와 일부 자산을 하네스 문서 후처리용으로 반영한 사용자 스킬이다.

- 별도 `im-not-ai` clone 없이 플러그인 안에서 사용한다.
- Codex와 Claude 모두 canonical `humanize-korean` 한 종을 사용하며 별도 alias·보조 agent 복사본을 배포하지 않는다.
- `.md` 산출물을 직접 덮어쓰지 않고 개선안과 diff를 먼저 제시한다.
- 보호 token, 경로, 코드블록, 링크, 표 구조를 보존해야 한다.
- 사용자가 승인한 파일만 반영한다.

외부 스킬 관계는 두 가지로 문서화한다.

- 참고형: 좋은 아이디어나 설계 원칙을 참고하되 그대로 포함하지 않음 — [Docs/External_Skill_References.md](./Docs/External_Skill_References.md)
- 직접 반입형: 코드·프롬프트·템플릿을 포함하거나 변형해 배포함 — [Docs/Imported_Skill_Provenance.md](./Docs/Imported_Skill_Provenance.md)

업데이트 정책은 [Docs/Skill_Upstream_Update_Policy.md](./Docs/Skill_Upstream_Update_Policy.md)를 따른다.

---

## 기존 프로젝트의 local skill copy 전환

기존 프로젝트에 `.agents/skills` 또는 `.claude/skills` 복사본이 남아 있다면 바로 삭제하지 않는다.

1. 플러그인을 설치한다.
2. 기존 local copy를 읽기 전용으로 inventory한다.
3. 하네스 구버전 복사본, 사용자 수정 복사본, 프로젝트 custom skill을 분류한다.
4. 백업 위치를 확인한다.
5. 사용자가 승인한 항목만 backup/remove 한다.
6. 문제가 있으면 백업본을 복원한다.

기본 정책은 보존과 보고다. 산출물, 스크립트, 템플릿을 가진 스킬은 삭제 전에 반드시 확인한다.

---

## 상세 문서

- [Plugin Installation Guide](./Docs/Plugin_Installation_Guide.md) — Codex/Claude 설치·업데이트·제거와 Phase 7 증적
- [Harness Engineering](./Docs/Harness_Engineering.md) — 현행 운영 정본
- [Harness Engineering Intro](./Docs/Harness_Engineering_Intro.md) — 도입 배경과 사용 예시
- [Docs Index](./Docs/README.md) — 문서 역할 인덱스
- [External Skill References](./Docs/External_Skill_References.md) — 외부 참고형 스킬 관계
- [Imported Skill Provenance](./Docs/Imported_Skill_Provenance.md) — 직접 반입형 provenance
- [Skill Upstream Update Policy](./Docs/Skill_Upstream_Update_Policy.md) — 관리자 최신화 정책
- [Plugin Release Checklist](./maintainer/plugin/release-checklist.md) — 현재 릴리스 게이트
