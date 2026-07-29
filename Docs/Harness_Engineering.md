# Harness Engineering Guide

> 기준일: 2026-07-29
> 이 문서는 `ai-agent-harness` 플러그인 전환 이후의 현행 운영 정본이다.

---

## 1. 목적

AI Agent Harness는 Codex, Claude Code 등 여러 에이전트가 같은 프로젝트에서 같은 품질 기준으로 일하도록 만드는 스킬·문서·검증 체계다.

핵심 원칙:

1. 실제 프로젝트 사용자는 플러그인을 설치한다.
2. 프로젝트 수행자가 `.docs`, `AGENTS.md`, `CLAUDE.md`를 만든다.
3. 스킬 복사와 양쪽 플랫폼 동기화는 사용자가 하지 않는다.
4. 관리자만 이 저장소에서 사용자 스킬, upstream, 플러그인 릴리스 후보를 관리한다.

---

## 2. 현재 구성

| 구분 | 수 | 위치 | 설명 |
|------|---:|------|------|
| 사용자 스킬 정본 | 18 | `skills/` | 플러그인 payload에 포함 |
| 관리자 스킬 정본 | 3 | `maintainer/skills/` | 이 저장소에서만 사용 |
| Codex runtime projection | 18 skills, 0 agents | `plugins/ai-agent-harness/runtime/codex/skills/` | 사용자 플러그인 산출물 |
| Claude runtime projection | 18 skills, 0 agents | `plugins/ai-agent-harness/runtime/claude/` | Codex와 같은 canonical 사용자 스킬만 포함 |
| 관리자 projection | 3 | `.agents/skills/`, `.claude/skills/` | repo-local 관리자 사용용 |

사용자 플러그인에는 관리자 스킬을 포함하지 않는다.
공유 runtime의 `allowed-tools`에는 제한 없는 `Bash`를 넣지 않는다. shell 명령은
플랫폼의 일반 permission mode에서 승인받고, 커밋·Git 설정·작업지침 명령 실행은
명시 호출 전용으로 제한한다.

---

## 3. 사용자 스킬 맵

| 계열 | 스킬 | 역할 |
|------|------|------|
| 설치·기반 | `harness-setup` | 프로젝트 유형 확인 후 `.docs`, `AGENTS.md`, `CLAUDE.md` 생성·갱신 |
| 설치·기반 | `harness-bootstrap` | 문서 없는 기존 코드베이스에서 설계·컨텍스트 역추출 |
| 설치·기반 | `git-scoped-account` | 프로젝트 트리 하위 repo의 git 계정 범위 지정 |
| 설계 | `design-doc` | 요구사항·아이디어·RFP 입력을 구조화한 설계 문서 생성 |
| 설계 | `context-doc` | 설계 문서를 에이전트 컨텍스트와 instruction 문서로 분리 |
| 설계 | `design-prototype-docs` | 프로토타입 입력용 화면 설계 문서 생성 |
| 설계 | `create-prototype` | HTML/CSS 기반 프로토타입 생성 |
| UI | `frontend-design` | 실제 UI 구현 품질 기준 제공 |
| 구현 계획 | `impl-doc` | 단일·소규모 기능 구현 계획 |
| 구현 계획 | `impl-fe-be-doc` | FE/BE 페어 또는 다중 화면 구현 계획 |
| 구현 점검 | `impl-reuse-scan` | 구현 전 기존 자산 발견·보고 |
| 구현 검증 | `impl-verify` | Phase/태스크 검증 매트릭스 산출 |
| 품질 | `multi-review` | 보안·성능·유지보수·테스트 관점 리뷰 |
| 품질 | `pre-commit` | 커밋 전 규칙 검사 |
| 품질 | `commit` | Conventional Commits 커밋 작성·실행 |
| 품질 | `code-comment` | 변경 코드 한글 주석 작성·갱신 |
| 문서 감사 | `doc-audit` | 코드와 문서 괴리 분석 |
| 문서 개선 | `humanize-korean` | Markdown 산출물의 한국어 문서 개선안 제시 |

제거된 스킬:

- `agent-sync`: 플랫폼별 스킬 복사/동기화 모델 제거
- `rfp-ingest`: RFP는 후속 설계·구현 스킬에 직접 입력

---

## 4. 관리자 스킬 맵

| 스킬 | 위치 | 역할 |
|------|------|------|
| `custom-skill-design` | `maintainer/skills/custom-skill-design` | 반복 업무를 새 스킬로 설계·생성·검증 |
| `skill-portfolio-maintainer` | `maintainer/skills/skill-portfolio-maintainer` | 외부 공식·유명 스킬 참고/반입 후보 탐색, provenance 관리 |
| `harness-plugin-maintainer` | `maintainer/skills/harness-plugin-maintainer` | 플러그인 build, validate, release gate, 설치 표면 증적 관리 |

관리자 스킬은 `.agents/skills`와 `.claude/skills`에 repo-local projection으로만 둔다.
별도의 관리자 플러그인은 만들지 않는다. 관리자는 정본 유지보수에는 repo-local
projection을 사용하고, 사용자 경험 검증에는 일반 사용자용 `ai-agent-harness`
플러그인을 격리된 CLI/App 설정에 설치해 사용한다.

---

## 5. 현행 사용자 흐름

```text
plugin 설치
→ harness-setup
→ 요구사항/RFP 또는 코드베이스 입력
→ 설계·prototype·구현계획 Markdown 생성
→ 원 producer 검증
→ humanize-korean 개선안·diff
→ 승인된 변경 반영·재검증
→ 승인된 최종 Markdown을 다음 구현·검증 스킬에 입력
```

사용자는 관리자 저장소를 clone하지 않는다. 플러그인 설치와 프로젝트 문서 생성만 수행한다.

`harness-setup`의 사용자 프로젝트 출력 allowlist는 `.docs/**`, 루트 `AGENTS.md`,
`CLAUDE.md`다. `.agents/skills/**`, `.claude/skills/**`, `skills/**`를 생성·복사·
동기화하는 동작은 금지한다. 기존 local skill copy는 읽기 전용으로 보고하고 승인
없는 이동·삭제를 하지 않는다.

---

## 6. `.docs`, `AGENTS.md`, `CLAUDE.md` 계약

### 단일 앱

- `.docs`는 앱 repo 안에서 관리한다.
- `AGENTS.md`는 공용 에이전트 컨텍스트 정본이다.
- `CLAUDE.md`는 Claude가 `AGENTS.md`를 읽도록 연결하는 bridge로 둔다.

### 복수 앱

- 프로젝트 최상위 폴더는 git으로 관리하지 않는다.
- `.docs`는 별도 git repo로 관리하는 것을 권장한다.
- `.docs/root-context/AGENTS.md`가 루트 컨텍스트 관리 원본이다.
- 루트 `AGENTS.md`, `CLAUDE.md`는 실행용 파일이며 `harness-setup`이 갱신한다.

---

## 7. Markdown producer와 `humanize-korean` 후처리

Markdown 산출물을 만드는 스킬 7종:

- `harness-setup`
- `harness-bootstrap`
- `context-doc`
- `design-doc`
- `design-prototype-docs`
- `impl-doc`
- `impl-fe-be-doc`

후처리 계약:

1. 최외곽 producer가 안정적인 `artifact_bundle_id`와 `handoff_owner`를 만든다.
2. 중첩 producer에는 같은 ID와 owner, `suppress_child_handoff=true`를 전달한다.
3. 원 producer가 산출물 구조와 링크를 검증한다.
4. owner만 bundle 전체를 `humanize-korean`의 `document-refinement` profile에 한 번 넘긴다.
5. `humanize-korean`은 개선안과 diff만 제시한다.
6. 보호 token, 경로, 코드블록, 표, 링크, 식별자를 보존한다.
7. 사용자가 승인한 변경만 원자적으로 반영한다.
8. 원 producer가 index, bridge, 구조, link를 다시 검증한다.
9. downstream 스킬은 승인·재검증된 최종 Markdown만 입력으로 사용한다.

제안, 건너뛰기, 거절, 적용, 재검증 상태는 실행 중
`handoff_completed=true`로 두고, 최종 Markdown 상대경로·내용 SHA-256·profile로
계산한 fingerprint를 `.docs/.harness/humanize-handoffs.json`에 원자적으로
기록한다. 같은 fingerprint가 완료 상태이면 새 session에서도 다시 제안하지 않는다.
ledger 자체는 문서 개선 대상에서 제외한다.

사용자가 문서 개선을 건너뛰거나 거절해도 원본 하네스 흐름은 계속 가능해야 한다.

---

## 8. 외부 upstream lifecycle

외부 스킬 관계는 두 종류다.

| 유형 | 의미 | 문서 |
|------|------|------|
| 참고형 | 공식·유명 스킬의 아이디어만 참고 | `Docs/External_Skill_References.md` |
| 직접 반입형 | 코드·프롬프트·템플릿을 포함하거나 변형 | `Docs/Imported_Skill_Provenance.md` |

관리자는 `skill-portfolio-maintainer`로 후보를 탐색하고, 산출물·스크립트·템플릿 삭제가 포함될 때는 반드시 사용자 확인 후 반영한다.

---

## 9. Plugin release lifecycle

관리자 흐름:

```text
skills/ 사용자 정본 수정
→ upstream registry/lock/provenance 갱신
→ harness-plugin-maintainer build
→ validate
→ install surface verification
→ release checklist 확인
→ 별도 승인 후 tag/push/release
```

공식 manifest·marketplace, 결정적 archive, 격리된 Codex/Claude CLI 설치 smoke는
자동 검증 대상으로 둔다. 설치 smoke는 실제 모델 호출 성공을 의미하지 않는다.
Codex/Claude CLI·앱 네 표면의 설치·명시 호출·산출물·재시작·새 세션 증적이
부족하면 릴리스 후보는 `not-release-ready`다.

---

## 10. Legacy local copy migration

기존 프로젝트의 `.agents/skills`, `.claude/skills` 복사본은 즉시 삭제하지 않는다.

기본 순서:

```text
read-only inventory
→ known old copy / modified old copy / custom skill 분류
→ backup target 확인
→ 사용자 승인
→ backup/remove
→ plugin 단일 discovery 확인
→ 필요 시 rollback
```

산출물, 스크립트, 템플릿을 가진 스킬은 자동 제거하지 않는다.

---

## 11. 검증 계약

| 영역 | 검증 |
|------|------|
| source/projection | 사용자 18종, 관리자 3종, 관리자 projection sync |
| plugin | Codex 18 skills, Claude 18 skills, 양쪽 agents 0, 관리자 0 |
| Markdown | producer 검증, humanize proposal-only, 승인 후 재검증 |
| upstream | registry schema, lock, provenance, license/NOTICE |
| setup | 사용자 프로젝트 skill 디렉터리 미생성, `.docs/**`·AGENTS·CLAUDE output allowlist |
| release | archive checksum, official manifest/catalog, isolated CLI install, app 수동 증적 |

대표 명령:

```text
python maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/validate_plugin.py
python maintainer/skills/harness-plugin-maintainer/scripts/smoke_cli_install.py
python maintainer/skills/harness-plugin-maintainer/scripts/verify_install_surfaces.py
python skills/harness-setup/evals/run_evals.py
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py --check
python maintainer/skills/skill-portfolio-maintainer/scripts/validate_registry.py
```

---

## 12. 한 줄 결론

현행 하네스는 “저장소를 clone해서 스킬을 복사하는 구조”가 아니라, **사용자는 플러그인을 설치하고 프로젝트 문서를 만들며, 관리자는 이 저장소에서 스킬·upstream·플러그인 릴리스를 관리하는 구조**다.
