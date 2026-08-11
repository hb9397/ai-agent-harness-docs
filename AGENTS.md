# Harness Kit — Agent 운영 가이드

> AI 에이전트 스킬·운영 문서와 사용자 플러그인 원본을 관리하는 하네스 저장소

이 저장소는 실제 프로젝트에 직접 복사해서 쓰는 저장소가 아니다. 실제 프로젝트 수행자는 생성된 사용자 플러그인 `harness-kit`을 설치해서 사용한다. 이 저장소는 관리자가 사용자 스킬, 관리자 스킬, 외부 upstream, 플러그인 packaging 산출물을 관리하는 원본 저장소다.

## 현재 전환 상태

- 기준 계획서: `improvement_plan/20260729/플러그인 전환 및 스킬 거버넌스 리팩토링 작업 계획서.md`
- `harness-kit` `0.4.3`은 annotated tag와 stable GitHub Release로 게시됐다.
- inventory, upstream provenance, license/NOTICE, plugin build, 설치 인터페이스와 회귀검증 기준선은 `maintainer/` 아래에서 관리한다.
- CLI 자동 설치 검증과 Codex·Claude 앱 수동 증적이 모두 충족되기 전에는 `release-ready`로 표시하지 않는다.
- `0.4.3` stable 게시에는 관리자의 명시적 예외 승인이 적용됐다. 게시 결과는 `maintainer/plugin/publish.json`에 기록하고, 미완료 수동 증적은 `maintainer/plugin/release-exceptions/v0.4.3.md`에 알려진 제한으로 남긴다.

## 정본 경로

| 영역 | 정본 | 생성물 또는 대상 |
|---|---|---|
| 사용자 스킬 원본 | `skills/` | `plugins/harness-kit/**` 사용자 payload |
| 관리자 스킬 원본 | `maintainer/skills/` | `.agents/skills/`, `.claude/skills/` repo-local projection |
| 관리자 upstream·provenance | `maintainer/upstreams/` | 외부 공식·유명 스킬 조사 및 반영 증적 |
| 관리자 inventory·plugin metadata | `maintainer/inventory/`, `maintainer/plugin/` | machine-readable 기준선과 릴리스 증적 |
| 운영 문서 | `README.md`, `.user-docs/` | 사용자 설치·하네스 흐름 설명 |

## 사용자 스킬과 관리자 스킬

- `skills/`는 사용자 플러그인에 들어갈 스킬의 정본이다.
- `maintainer/skills/`는 이 저장소 관리자만 사용하는 repo-local 스킬의 정본이다.
- 관리자 스킬은 사용자 플러그인 payload에 포함하지 않는다.
- 사용자 스킬은 `.agents/skills/` 또는 `.claude/skills/` repo-local projection에 포함하지 않는다.
- 실제 사용자 프로젝트에서도 `harness-setup`은 `.agents/skills/`, `.claude/skills/`, `skills/`를 생성·복사·동기화하지 않는다. 사용자 스킬은 설치된 플러그인에서만 제공한다.
- `custom-skill-design`은 관리자 스킬이며 `maintainer/skills/custom-skill-design/`에서만 편집한다.
- `skill-portfolio-maintainer`는 사용자 스킬 포트폴리오, 외부 upstream, provenance, protected asset 영향 관리를 담당한다.
- `harness-plugin-maintainer`는 Codex·Claude 사용자 플러그인 생성, 검증, 릴리스를 담당한다.

## Projection 규칙

`.agents/skills/`와 `.claude/skills/`는 직접 편집하지 않는다. 다음 생성기로만 갱신한다.

```bash
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py --check
```

projection에는 관리자 3종만 있어야 한다.

- `custom-skill-design`
- `skill-portfolio-maintainer`
- `harness-plugin-maintainer`

`harness-setup`을 포함한 사용자 스킬은 projection에서 제거한다.

## 스킬 편집 규칙

1. 사용자 스킬은 `skills/{skill-name}/`에서만 편집한다.
2. 관리자 스킬은 `maintainer/skills/{skill-name}/`에서만 편집한다.
3. projection 경로의 파일은 생성물로 취급하고 직접 수정하지 않는다.
4. `SKILL.md` frontmatter는 플랫폼 중립적으로 유지한다. `model:` 필드와 특정 agent fork 하드코딩은 금지한다.
5. 산출물·적용범위 스킬의 초기 단계에는 프로젝트 유형과 적용 범위를 확인하는 절차를 둔다.
6. 다른 스킬의 내부 파일, 상대경로, 구현 세부사항에 결합하지 않는다.
7. 같은 사용자 플러그인 안에서 공개 skill 이름으로 수행하는 승인형 workflow handoff는 허용한다.
8. 공유 스킬 frontmatter에서 제한 없는 `Bash`를 사전 승인하지 않는다. shell 실행은
   플랫폼의 일반 permission mode로 넘기며, 커밋·Git 설정·작업지침 명령 실행처럼
   부작용 가능성이 있는 스킬은 명시 호출 전용으로 둔다.

## 문서 동반 갱신

스킬 구조, 사용자 플러그인 설치 방식, 하네스 흐름이 바뀌면 다음 문서를 함께 갱신한다.

- `README.md`
- `.user-docs/Harness_Engineering.md`
- `.user-docs/Harness_Engineering_Intro.md`
- 관련 `.user-docs/**`

실제 사용자 프로젝트에서 산출물을 만드는 경우에는 생성된
`@.docs/instruction/artifact-output-routing-instruction.md`를 단일 앱의
경로·소유권·인계 정본으로 사용한다. 복수 앱은 각 앱의
`@.docs/{앱}/instruction/artifact-output-routing-instruction.md`를 사용하며,
이 관리자 저장소 자체의 `maintainer/**` 산출물과 교차 쓰지 않는다.

역사 문서인 `improvement_plan/20260627/**`는 byte-preserve 대상이다. 수정하지 않고 현행 문서에서 새 기준을 설명한다.

## 보호 자산 규칙

`template.md`, `templates/`, `script/`, `scripts/`, `asset/`, `assets/`,
`skills/**/example/`, `skills/**/examples/`, `evals/`에 있는 산출물은 보호 자산으로
취급한다. 내용
보완은 영향 범위를 분리해 기록하고, 삭제·이동·교체는 별도 파괴적 변경 승인
항목으로 분리한다.

## 커밋 규칙

- 커밋 메시지는 Conventional Commits 규격을 따른다.
- Phase 단위 작업은 구현, 검증, 커밋을 한 묶음으로 완료한다.
- 사용자가 명시한 Phase 범위를 넘어서는 구현은 다음 Phase로 넘긴다.

## 참조 문서

- `improvement_plan/20260729/플러그인 전환 및 스킬 거버넌스 리팩토링 작업 계획서.md`
- `.user-docs/Skill_Upstream_Governance.md`
- `.user-docs/Harness_Engineering.md`
- `.user-docs/Harness_Engineering_Intro.md`
- `.user-docs/Agent_Skills_Repo_Structure_Analysis.md`
