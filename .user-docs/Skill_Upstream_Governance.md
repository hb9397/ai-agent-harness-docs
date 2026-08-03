# 스킬 업스트림 거버넌스

이 문서는 외부 출처의 분류·관찰·승인·반입·패키징·행동 참조를 함께 설명하는
사람용 단일 정본이다.

**읽는 방향: `로컬 대상 ← 외부 출처`.** 왼쪽의 로컬 대상이 오른쪽의 외부
upstream을 반입·변형하거나 개념·행동만 참고한다는 뜻이다. 화살표를 반대로 읽거나
`reference`를 파일 반입으로 해석하지 않는다.

<a id="direct-import-provenance"></a>
## 직접 반입·변형 관계 요약

| 로컬 대상 ← 외부 upstream | source ID | mode / lifecycle | accepted ref / 40자 SHA | observed / 확인일 | 반영·변형 범위 | 포함·제외 자산 | 사용자 payload | license / NOTICE / file-map |
|---|---|---|---|---|---|---|---|---|
| `skills/humanize-korean` ← [im-not-ai](https://github.com/epoko77-ai/im-not-ai) | `im-not-ai` | `adapted` / `active`; accepted·embedded | `v2.3.0` / `82137e858763dadb99561f194c5c00465735017b` | accepted와 일치 / 2026-07-30 | 핵심 지침을 한국어 문서 후처리와 승인형 workflow에 맞게 변형하고 로컬 보호 스크립트를 둔다. | 전체 upstream runtime은 제외하며 `vendored`로 주장하지 않는다. | 포함; 패키징 source | MIT / `maintainer/upstreams/provenance/im-not-ai/NOTICE.md` / `maintainer/upstreams/provenance/im-not-ai/file-map.json` |
| `skills/frontend-design` ← [Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | `anthropic-frontend-design` | `adapted` / `active`; accepted·embedded | `main` / `b29e7cf65e5cb78a5ac33d582270551bc74a14eb` | accepted와 일치 / 2026-07-30 | 한국어 번역·축약, 프로젝트 라우팅, 디자인 규칙과 검증 흐름을 추가했다. | 원문 그대로가 아닌 수정 파생물이며 라이선스 전문과 변경 고지를 보존한다. | 포함; 패키징 source | Apache-2.0 / `maintainer/upstreams/provenance/anthropic-skills/NOTICE.md` / `maintainer/upstreams/provenance/anthropic-skills/file-map.json` |
| `maintainer/skills/custom-skill-design` ← [Anthropic skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) | `skill-creator-guides` | `adapted` / `active`; accepted·embedded | `main` / `b29e7cf65e5cb78a5ac33d582270551bc74a14eb` | accepted와 일치 / 2026-07-30 | 한국어 번역·재구성과 이 관리 저장소 전용 설계 workflow를 추가했다. | 관리자 정본에만 두고 사용자 runtime·payload에서 제외한다. | 미포함; 관리자 전용 | Apache-2.0 / `maintainer/upstreams/provenance/anthropic-skills/NOTICE.md` / `maintainer/upstreams/provenance/anthropic-skills/file-map.json` |
| `skills/ui-ux-pro-max` ← [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | `ui-ux-pro-max-runtime` | `adapted` / `active`; accepted·embedded; group `ui-ux-pro-max` | `v2.11.3` / `4857a2c5ef989794751a0f66b8545a4a49566286` | accepted와 일치 / 2026-07-31 | 생성된 스킬 트리 43개 파일을 반입했다. `data/`, `references/`, `scripts/`는 보존하고 `SKILL.md`는 플랫폼 중립 경로·범위 확인·승인형 저장 계약으로 수정했다. | 생성기 `src/`, CLI `cli/`, 형제 스킬 6종은 제외한다. | 포함; 패키징 source | MIT / `maintainer/upstreams/provenance/ui-ux-pro-max/NOTICE.md` / `maintainer/upstreams/provenance/ui-ux-pro-max/file-map.json` |
| `skills/**motion-design**` ← [LottieFiles Motion Design](https://github.com/LottieFiles/motion-design-skill) | `lottiefiles-motion-design-runtime` | `adapted` / `active`; accepted·embedded; group `lottiefiles-motion-design` | `main` / `f9a8a041b85185ee4881b3471d3415e939aac772` | accepted와 일치 / 2026-07-31 | `director/`, `patterns/`, `reference/` 16개 파일을 보존하고 `SKILL.md`는 목적 우선 분류·모션 생략 허용·저밀도·접근성·성능·승인형 저장 계약으로 수정했다. | upstream의 생성·개발용 파일은 file-map의 `excluded`에 따른다. | 포함; 패키징 source | MIT / `maintainer/upstreams/provenance/lottiefiles-motion-design/NOTICE.md` / `maintainer/upstreams/provenance/lottiefiles-motion-design/file-map.json` |

현재 사용자 스킬 정본은 19개이고, 관리자 스킬은 3개다. 직접 반입 관계는
upstream 저장소 4개에 `adapted` 5건이다. 이 중 사용자 스킬은 4개, 관리자 전용
스킬은 `custom-skill-design` 1개이며 활성
`vendored` 관계는 0건이다. UI/UX Pro Max와 Motion Design은 이미 사용자 payload와
패키징 NOTICE에 포함된다.

<a id="concept-behavior-references"></a>
## 개념·행동 참조 관계 요약

아래 관계는 외부 파일·번역문·요약문·runtime을 반입하지 않는다. 선택한 개념 또는
공식 문서로 확인한 행동 사실만 로컬 계약에 연결하며, 원본 제품·스킬과의 파일
동일성이나 실행 동등성을 보증하지 않는다.

| 로컬 소비자 ← 외부 출처 | source / contract ID · 분류 | 참조 목적과 반영된 행동·불변조건 | 비반입 범위 | observed ref / 확인일 / 증적 상태 | stale 처리 |
|---|---|---|---|---|---|
| `frontend-design`, `design-prototype-docs`, `create-prototype` ← [OpenAI Product Design](https://github.com/openai/role-specific-plugins/tree/main/plugins/product-design) | `openai-product-design`; `official` | 제품 디자인, 프로토타입, 비평, 인계 개념; `reference` / `active` | 외부 skill·template·runtime 전부 | `main` / `fe5608d2512a7d6a7b9821ce8a88c48464ecd6e4` / 2026-07-30 / source-level 관찰 완료 | 마지막 완전 관찰을 보존하고 수동 의미 diff |
| `design-doc`, `impl-doc`, `impl-fe-be-doc`, `impl-reuse-scan`(제한적), `impl-verify`, `multi-review`, `custom-skill-design` ← [Superpowers v6.2.0](https://github.com/obra/superpowers/releases/tag/v6.2.0) | `superpowers`; `reputable-third-party` | 브레인스토밍, 계획, TDD, 기존 패턴 우선, 완료 전 검증, 병렬 리뷰, 스킬 작성 원칙; `reference` / `active` | Superpowers runtime·원문 skill·hook·agent 전부 | `v6.2.0` / `3dcbd5c4b48e02263fbf4a3c01e3fe4f81d584d9` / 2026-07-30 / exact watched paths 완료 | 마지막 완전 path 묶음을 보존하고 수동 의미 diff |
| `create-prototype`(제한적), `design-doc`, `design-prototype-docs`, `impl-doc`, `impl-fe-be-doc`, `impl-reuse-scan`(제한적), `impl-verify`, `multi-review` ← [gstack](https://github.com/garrytan/gstack) | `gstack`; `reputable-third-party` | 역할 기반 명세·계획·디자인·`qa-only`·리뷰 개념; `reference` / `active` | gstack runtime, 자동 수정, browser daemon, telemetry | `main` / `a3259400a366593e0c909dd9ac3e59752efd2488`; 내부 version `1.60.1.0` / 2026-07-30 / source-level 완료·path-level 부분 미검증 | rate limit 해소 후 전체 exact-path 묶음을 다시 관찰 |
| `custom-skill-design` ← [OpenAI Codex skill-creator](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md) | `openai-codex-skill-creator`; `official` | 간결성, 지침 자유도, 점진적 공개, 보조 자산 역할, 검증 무결성, 선택적 `agents/openai.yaml`; `reference` / `active` | 공식 파일·helper script·schema의 로컬 반입 | `main` / `b1ccaa0e080f59cfd71a136f6fcc60a4f2d60fba`; `SKILL.md` 마지막 변경 `59533a2c26e349c59417e4773b930c26211d7bdd` / 2026-07-30 / 보조 파일은 content hash만 완료 | 미확인 path commit을 추정하지 않고 전체 묶음 재검증 |
| `commit` ← [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | `conventional-commits` / `commit-workflow`; `standard` | 커밋 제목·본문 구조의 표준 참조; `reference` / `active` | 외부 도구·hook·commit skill | `1.0.0` / 2026-08-03 / `fresh`; normalized SHA-256 `1f02d0f99e4a830daafa4cc75d92e1fe4aef50984c6c398aabd50d7c1214091f` | 새 문서 버전을 자동 채택하지 않고 메시지 계약 검토 |
| `context-doc`, `harness-bootstrap`, `harness-setup`, `doc-audit` ← [OpenAI AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | `openai-agents-md`; `official` | Codex의 `AGENTS.md` 프로젝트 지침 계약; `reference` / `active` | Codex runtime·문서 원문 | `documentation` / 2026-07-29 / 공식 문서 관찰 | 문서 surface 변경 시 stale로 표시하고 계약 재검토 |
| `context-doc`, `harness-bootstrap`, `harness-setup`, `doc-audit` ← [Claude Code memory documentation](https://code.claude.com/docs/en/memory) | `claude-memory`; `official` | `CLAUDE.md`에서 `@AGENTS.md`를 불러오는 브리지; `reference` / `active` | Claude runtime·문서 원문 | `documentation` / 2026-07-29 / 공식 문서 관찰 | 문서 surface 변경 시 stale로 표시하고 계약 재검토 |
| `design-prototype-docs`, `create-prototype`, `frontend-design`, `impl-verify` ← [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | `ui-ux-pro-max-principles` / group `ui-ux-pro-max`; `reputable-third-party` | 디자인 시스템 입력 계약, 기존 제품 token 우선, 대비·focus·터치 대상·상태 검증; `reference` / `active` | reference 관계로는 파일을 반입하지 않음; 별도 runtime 관계만 패키징 | `v2.11.3` / `4857a2c5ef989794751a0f66b8545a4a49566286` / 2026-07-31 / accepted·embedded reference | 같은 group의 runtime 관계와 원자적으로 재검토 |
| `design-prototype-docs`, `create-prototype`, `frontend-design`, `impl-verify` ← [LottieFiles Motion Design](https://github.com/LottieFiles/motion-design-skill) | `lottiefiles-motion-design-principles` / group `lottiefiles-motion-design`; `reputable-third-party` | 모션 목적 분류, 승인된 명세만 구현, reduced-motion 대안, 반복·성능 검증; `reference` / `active` | reference 관계로는 파일을 반입하지 않음; 별도 runtime 관계만 패키징 | `main` / `f9a8a041b85185ee4881b3471d3415e939aac772` / 2026-07-31 / accepted·embedded reference | 같은 group의 runtime 관계와 원자적으로 재검토 |
| `commit` ← [OpenAI Codex 공식 base instruction](https://github.com/openai/codex/blob/2cf2a6a844f1fc2ddd489c8a67fa8bc2f59a6f3d/codex-rs/protocol/src/prompts/base_instructions/default.md) | `openai-codex-commit-behavior` / `commit-workflow`; `official` | 공식 문서로 확인한 Codex Git 행동 사실을 local commit 정책과 구분; `reference` / `active` | 특정 외부 commit skill, prompt, runtime 파일 | observed `main` / `bb5054fe47abe73ecbbd454751066a28c89f4bb9`; accepted watched path `2cf2a6a844f1fc2ddd489c8a67fa8bc2f59a6f3d`; `codex-cli 0.146.0` / 2026-08-03 / `fresh` | 마지막 accepted 관찰을 보존하고 stale·수동 semantic review |
| `commit` ← [Anthropic Claude Code 공식 commit 문서](https://code.claude.com/docs/en/headless#create-a-commit) | `anthropic-claude-code-commit-behavior` / `commit-workflow`; `official` | 공식 문서로 확인한 Claude Code Git 행동 사실을 local commit 정책과 구분; `reference` / `active` | 특정 외부 commit skill, prompt, runtime 파일 | accepted `documentation@2026-08-03`; 5개 공식 surface normalized hash(대표 headless `94bdf2c41c2cc85eaecfb0c6e03f4839a8a3121b5a020a0e0f0d7be27ec4ebaa`); `Claude Code 2.1.220` / 2026-08-03 / `fresh` | 마지막 accepted 관찰을 보존하고 stale·수동 semantic review |

<a id="machine-readable-sources"></a>
## Machine-readable 정본과 우선순위

사람용 설명과 기계 기록이 충돌하면 다음 순서로 사실을 확인한 뒤 이 문서를 고친다.

1. `maintainer/upstreams/registry.json`: 관계, source ID, behavior contract, mode,
   lifecycle, target과 정책의 정본
2. `maintainer/upstreams/lock.json`: source별 observed·accepted·embedded·packaged·
   released ref, 확인일과 증적 상태의 정본
3. `maintainer/upstreams/provenance/current-skills.json`: 사용자·관리자 skill의
   source·behavior 소비 관계 정본
4. `maintainer/plugin/CAPABILITIES.json`: 현행 사용자 skill inventory와 payload
   포함 범위의 정본
5. `maintainer/plugin/release.json`: 특정 plugin artifact의 skill 수, 패키징
   upstream과 release 상태의 정본
6. `maintainer/upstreams/provenance/**`: license, NOTICE, file-map, 제3자 권리
   판정과 promotion evidence의 정본

문서에 숫자나 날짜를 독립적으로 고정해 machine source를 대체하지 않는다. 현재
정본에서 `pre-commit`이 제거된 뒤 사용자 skill과 `0.3.0` payload는 19개다. 이전
`0.2.2` artifact의 20개 inventory는 historical immutable archive 증적이지 현행
source inventory가 아니다.

<a id="source-and-evidence-model"></a>
## 출처 mode, lifecycle, evidence state

| mode | 의미 | 필수 처리 |
|---|---|---|
| `native` | 로컬에서 작성했고 활성 외부 출처 관계가 없다. | 일반 저장소 review |
| `reference` | 외부 출처가 개념 또는 행동 사실에만 영향을 준다. | 출처 URL, 로컬 소비자·contract, 채택 범위와 비반입 범위 기록 |
| `vendored` | upstream 파일을 원문 그대로 복사한다. | license, NOTICE, hash, file-map, 원본 test와 승인 |
| `adapted` | upstream 콘텐츠를 번역·수정·재구성한다. | `vendored` 필수 항목에 local patch·처리·검증 목적 추가 |
| `unknown` | 관계나 권리 증거가 불충분하다. | 해결될 때까지 반입·패키징·release 금지 |

`lifecycle`은 조사 후보 `candidate`, 정본에 적용 중인 `active`, 위험 또는 증거
부족으로 차단된 `blocked`, 더 이상 새 반영을 하지 않는 `deprecated`를 구분한다.
mode와 lifecycle은 서로 다른 축이며 `reference/active`처럼 함께 기록한다.

| evidence state | 의미 |
|---|---|
| `observed` | 읽기 전용 검토에서 본 최신 release, tag, branch, 문서 또는 행동 surface |
| `accepted` | 관리자가 통합 기준으로 승인한 변경 불가능 ref 또는 문서 관찰 |
| `embedded` | 승인한 출처가 사용자 정본 `skills/`, 관리자 정본 `maintainer/skills/` 또는 behavior contract에 반영된 상태 |
| `packaged` | 검증된 plugin artifact에 직접 반입 대상과 법적 고지가 포함된 상태 |
| `released` | release된 plugin version을 통해 사용자에게 제공되는 상태 |

`observed`는 최신성을 본 사실일 뿐 승인·반영·패키징·동작 보장이 아니다. 직접
반입은 `accepted` 전에 immutable 40자 SHA와 file hash가 필요하다. 문서·행동
reference는 확인일, 선택적 ref·content hash, claim class와 증적 상태를 사용한다.

<a id="approval-gates"></a>
## 승인 게이트 G0~G8

| 게이트 | 요구 사항 |
|---|---|
| G0 | 출처 등록과 의도한 mode 승인 |
| G1 | 관리자 신원, release, tag와 전체 SHA 검증 |
| G2 | license와 third-party 콘텐츠 검토 |
| G3 | script, hook, MCP, network, binary, symlink, submodule과 권한 검토 |
| G4 | 보호 자산 영향을 포함한 개념 또는 파일 범위 승인 |
| G5 | 삭제·이동·교체에 대한 별도 파괴적 변경 승인 |
| G6 | 승격 전 임시 staging에만 적용 |
| G7 | Codex, Claude, 회귀와 license 검증 |
| G8 | 정본 출처로 승격하고 plugin release workflow에 인계 |

“최신 버전으로 업데이트”는 G4 또는 G5 승인이 아니다. 일반 승인, protected-asset
approval, destructive approval을 필요한 범위별로 분리한다.

<a id="direct-import-details"></a>
## 직접 반입·변형 provenance와 패키징 의무

상단 직접 관계표의 다섯 관계에는 immutable source URL·ref·40자 SHA, license SPDX·
URL·SHA-256, copyright·NOTICE, file별 `verbatim`·`modified`·`excluded`·
`local-only`, 보호 자산 승인, 파괴적 변경 승인, 검증 결과와 rollback 경로를
기록한다. 새 `vendored` 또는 `adapted` 관계에도 같은 필드를 요구한다.

- `humanize-korean`은 실행형 회귀 test를 가지지만 전체 im-not-ai runtime을
  재현한다고 주장하지 않는다.
- `frontend-design`과 `custom-skill-design`은 같은 Anthropic commit을 사용하되
  전자는 사용자 payload에, 후자는 관리자 정본에만 들어간다.
- `ui-ux-pro-max`와 `motion-design`은 보존 자산과 수정 `SKILL.md`를 file-map에서
  파일별로 구분한다. 두 runtime source는 이미 plugin NOTICE와 license bundle에
  포함된다.
- `reference` 관계는 파일을 복사하지 않으므로 그 관계 자체가 license payload를
  만들지 않는다. 같은 upstream의 별도 `adapted` runtime 관계가 있으면 그 관계의
  재배포 의무만 적용한다.

현재 `0.3.0` artifact의 `packaged_upstreams`는
`anthropic-frontend-design`, `im-not-ai`, `ui-ux-pro-max-runtime`,
`lottiefiles-motion-design-runtime` 네 source다. `THIRD_PARTY_NOTICES.md`와
`licenses/`는 네 source를 모두 닫는다. 관리자 전용 `skill-creator-guides`와
concept/behavior-only `reference`는 사용자 payload에 넣지 않는다.

Motion Design의 upstream 참조 자료에는 Material Design 3, Apple Human Interface
Guidelines와 Disney 애니메이션 원칙이 언급된다. upstream 최상위 MIT license는
upstream 저작자가 보유하지 않은 제3자 권리를 허가하지 못한다.
`maintainer/upstreams/provenance/lottiefiles-motion-design/NOTICE.md`의 파일별
판정을 유지하며 외부 지침의 설명문이나 표 전체로 반입 범위를 확대하지 않는다.

<a id="reference-adoption-details"></a>
## 개념 reference의 스킬별 채택 범위

모든 `impl-*` 스킬이 Superpowers와 gstack 전체 workflow를 합치는 것은 아니다.

| 로컬 스킬 | Superpowers에서 참고하는 정책 | gstack에서 참고하는 정책 | 현행 반영과 후속 후보 |
|---|---|---|---|
| `impl-doc` | `writing-plans`, test-first 순서, 계획 자체검토 | `/spec`, `/plan-eng-review` | 정확한 범위·파일·의존·검증 gate는 반영했다. test-first 순서와 계획 자체검토는 후속 후보이며 완성 code 전체를 계획서에 넣지 않는다. |
| `impl-fe-be-doc` | 계획 원칙, 인접 task 계약·실행 인계 | `/spec`, `/plan-eng-review`, `/plan-design-review` | FE↔API↔BE↔DB 추적성과 Phase 검증은 반영했다. task별 consumes/produces와 실행 인계는 후속 후보다. |
| `impl-reuse-scan` | 기존 구조·pattern 우선, working-example 비교 | Search Before Building, Existing Code Leverage | 기존 자산 발견·분류·사용자 결정·무수정 gate만 반영한 제한적 reference다. |
| `impl-verify` | `verification-before-completion`, 원 증상 재현, 증거와 추정 분리 | 수정 없는 `/qa-only` 보고 | fresh command 증거·`UNKNOWN`·보고 전용 경계는 반영했다. 원 증상 재현은 후속 후보이며 gstack 자동 수정 runtime은 가져오지 않는다. |

`design-doc`은 브레인스토밍·요구 구체화, `multi-review`는 병렬 전문 review·증거·
중복 제거를 참고한다. gstack `/design-review`는 구현 후 시각 QA이므로
`frontend-design`의 직접 reference로 분류하지 않는다.

삭제된 `pre-commit`이 Superpowers의 완료 전 기계 검사 일부를 참고했던 관계는
역사 기록으로만 보존한다. 그 reference는 `commit`에 자동 승계되지 않는다.
`commit`의 live 외부 관계는 상단 표와 `commit-workflow` contract에 명시한 세
behavior-only source뿐이다.

<a id="behavior-contracts"></a>
## Behavior contract: `commit-workflow`

행동 관계의 방향은 `공식 behavior source → commit-workflow → commit consumer`다.
OpenAI·Anthropic source를 서로 하나의 upstream, candidate 또는
`relationship_group`으로 합치지 않으며 특정 외부 commit skill을 import하지 않는다.
`maintainer/upstreams/provenance/current-skills.json`의 `commit` consumer는
`behaviors: ["commit-workflow"]`만 가지며 behavior source를 `sources`에 직접
매핑하지 않는다.

공식 출처가 뒷받침하는 claim은 다음 범위로 한정한다.

| claim ID | class | source | 허용하는 사실 |
|---|---|---|---|
| `codex-explicit-commit-request` | `official-documented` | `openai-codex-commit-behavior` | 관찰한 Codex base instruction은 명시 요청 없이 commit이나 branch를 만들지 말라고 지시한다. |
| `claude-staged-commit-example` | `official-documented` | `anthropic-claude-code-commit-behavior` | Claude Code 공식 headless 예시는 staged 변경을 `git diff`, log, status와 commit permission으로 검토한다. |
| `claude-configurable-git-instructions` | `official-documented` | `anthropic-claude-code-commit-behavior` | 공식 문서는 built-in commit/PR instruction, Git status snapshot, attribution, permission과 hook 설정 surface를 설명한다. |
| `conventional-message-structure` | `official-documented` | `conventional-commits` | 1.0.0은 type, 선택 scope, description, 선택 body와 footer 구조를 정의한다. |
| `runtime-version-observation` | `runtime-observation`; `observation_kind=product-version` | 로컬 `codex --version`, `claude --version` | 2026-08-03에 `codex-cli 0.146.0`과 `Claude Code 2.1.220` version 문자열만 관찰했다. Phase 1 product workflow 실행 결과는 없다. |

`commit-workflow`의 local policy 불변조건은 다음과 같다.

1. 명시적인 commit 실행 또는 commit-message 요청에서만 시작한다. message-only
   요청은 index, worktree, HEAD를 바꾸지 않는다.
2. 적용되는 `AGENTS.md`·`CLAUDE.md`, repository root, staged·unstaged·untracked
   상태, staged·unstaged diff, 의도한 untracked 내용과 최근 log를 확인한다.
3. 기존 또는 범위 밖 staged 변경을 보존하고 명시한 경로만 stage한다. 서로 다른
   concern은 분리 commit을 제안하며 범위 모호성이나 빈 stage에서는 중단한다.
4. 실제 diff와 검증 증거에 근거한 Conventional Commit 제목·본문에 변경 이유와
   중요한 결정을 기록한다.
5. 정상 hook을 실행한다. 별도 요청 없이 `--no-verify`, amend, push, tag, branch
   생성을 수행하지 않으며 hook 실패를 우회하지 않는다.
6. attribution은 agent 설정과 repository policy를 따르고 `Co-Authored-By`를
   강제하지 않는다.
7. 성공 후 SHA, `git show`, status와 남은 변경을 다시 확인해 보고한다.

<a id="claim-classes"></a>
### Claim class와 금지 주장

| claim class | 허용 범위 |
|---|---|
| `official-documented` | 고정 URL·ref·content hash와 확인일로 직접 뒷받침되는 공식 문서의 사실 |
| `local-policy` | 이 저장소가 `commit-workflow`와 `commit`에 독자적으로 정한 안전·scope·검증 규칙 |
| `runtime-observation` | 실제 실행 evidence가 있는 version command 또는 fixture 결과만 기록하며 다른 version·환경으로 일반화하지 않음 |

하나의 문장에 서로 다른 claim class를 섞어 공식 제품 보장처럼 표현하지 않는다.
공식 문서 관찰, local policy 채택, runtime 관찰은 각각 별도 evidence를 가진다.
외부 source와 로컬 `commit`의 prompt·파일·runtime 동등성, 모든 Codex·Claude
version의 동일 행동, hook·push·attribution의 제품 차원 보장은 지원하지 않는다.

<a id="relationship-groups"></a>
## 다중 upstream과 `relationship_group`

UI/UX Pro Max와 Motion Design은 각각 direct `adapted`와 concept `reference`
관계를 한 group으로 묶는다.

| relationship group | 직접 관계 | 참고 관계 |
|---|---|---|
| `ui-ux-pro-max` | `ui-ux-pro-max-runtime` | `ui-ux-pro-max-principles` |
| `lottiefiles-motion-design` | `lottiefiles-motion-design-runtime` | `lottiefiles-motion-design-principles` |

한 group 안의 repository URL, `source_url`, `license_spdx`, lifecycle,
observed·accepted SHA는 일치해야 한다. 한쪽만 새 SHA 또는 `active`로 바꿀 수 없고
하나의 candidate로 원자 승인·승격한다. 보고서는 direct 관계의 file diff·hash·
license와 reference 관계의 의미 diff, protected asset 영향과 destructive diff를
관계별·파일별로 나눈다. 조사와 staging은 여전히 GitHub upstream 하나씩 수행하며
서로 다른 upstream은 한 candidate나 group에 섞지 않는다.

`custom-skill-design`은 group이 아니라 서로 다른 두 upstream을 독립 추적한다.
`skill-creator-guides`는 Anthropic 번역·재구성 원본인 `adapted`이고,
`openai-codex-skill-creator`는 공식 설계 원칙만 독자 채택한 `reference`다. 두
출처의 차이와 충돌을 함께 검토하되 한쪽 상태를 다른 쪽에 복제하지 않는다.

<a id="refresh-and-stale-fallback"></a>
## 최신화, watched path와 stale fallback

GitHub default branch SHA 변경은 감시 대상 skill 파일 변경과 같지 않다. exact
`watched_paths`는 source-level branch/release와 각 path의 마지막 변경을 함께
확인한다. glob은 GitHub API에서 path 단위로 해석하지 않고 source-level SHA와
후속 semantic diff로 판정한다.

```bash
python maintainer/skills/skill-portfolio-maintainer/scripts/check_upstreams.py --source openai-codex-skill-creator --verify-watched-paths
```

`--write-observed` 없이 실행하면 읽기 전용이다. 옵션을 붙여도 `observed`만
갱신하며 `accepted`·`embedded`를 자동 승격하지 않는다.

exact watched path 하나라도 rate limit·network·API 오류가 나면 새 path 관찰
묶음 전체를 lock에 저장하지 않는다. 직전의 완전한 묶음이 있으면 보존하고, 없으면
source-level ref·SHA와 불완전 사유만 기록한다. 일부 성공 결과를 섞어 “path 검증
완료”로 표시하지 않는다. gstack과 OpenAI Codex `openai_yaml`의 2026-07-30
부분 미검증은 이 원칙을 따른다.

OpenAI Codex `skill-creator/SKILL.md`와 `references/openai_yaml.md`는 공식 raw
파일과 로컬 설치본의 줄바꿈 정규화 content hash가 일치했다. 다만 API rate limit로
보조 파일의 마지막 변경 commit을 확인하지 못했으므로 content match를 path-level
commit 검증으로 확대 해석하지 않는다.

behavior source refresh 실패, 공식 문서·watched surface 변경 또는 증거 만료가
생기면 마지막 accepted observation을 보존하고 evidence를 `stale`로 표시한다.
semantic/manual review가 끝나기 전에는 claim, source 파일, contract 또는 consumer를
자동 import·자동 update하지 않는다. stale는 “거짓” 판정이 아니라 현재성을 다시
확인해야 한다는 상태이며 unsupported claim으로 fallback하지 않는다.

두 skill-creator 출처는 다음의 서로 다른 감시·반영 계약을 유지한다.

- `skill-creator-guides`는 Anthropic의 `skills/skill-creator/SKILL.md`와
  `LICENSE.txt`를 감시한다. 새 변경은 local patch와 semantic diff, license,
  protected-asset 영향을 검토하고 승인된 변경만 `accepted`와 `embedded`로
  승격한다.
- `openai-codex-skill-creator`는 OpenAI Codex의 `skill-creator/SKILL.md`와
  `references/openai_yaml.md`를 감시한다. 간결성, 지침 자유도, 점진적 공개,
  자산 역할, 검증과 Codex metadata 원칙의 차이를 반영 후보로 만들되 원본 파일을
  복사하거나 `accepted`·`embedded`로 자동 승격하지 않는다.

두 출처는 다음처럼 함께 읽기 전용 확인할 수 있다.

```bash
python maintainer/skills/skill-portfolio-maintainer/scripts/check_upstreams.py \
  --source skill-creator-guides \
  --source openai-codex-skill-creator \
  --verify-watched-paths
```

<a id="equivalence-and-evidence"></a>
## 동작 동등성과 증적 해석

| 관계 | 허용하는 동등성 주장 | 검사 |
|---|---|---|
| `reference` | 선택한 개념의 의미적 행동 불변조건만 비교 | 같은 fixture에서 trigger, 승인 gate, 보고 전용 여부, 산출물 구조와 검증 증거 비교 |
| `adapted` | accepted upstream 기준과 승인한 local 변경 목적을 함께 만족 | accepted SHA, file-map, local regression eval, 필요 시 upstream differential smoke |
| `vendored` | 고정 원본 파일·runtime의 재현성 | file hash, license, 원본 test, Codex·Claude 설치 smoke |

현재 활성 `vendored`는 없다. `frontend-design`과 `custom-skill-design`은 정적 계약
eval 중심이므로 실제 격리 실행 없이 원본과 동일하게 동작한다고 주장하지 않는다.
behavior invariant 선언이나 문자열 검사는 실행 증적이 아니다.

Phase 1의 behavior runtime evidence는 로컬 `codex --version`과 `claude --version`
관찰뿐이다. 같은 격리 repository fixture의 Codex·Claude product smoke는 Phase 7
fixture `cross-product-commit-workflow`로 `planned` 상태이고 `evidence_path=null`이다.
각 product를 같은 fixture에서 별도로 실행할 계획일 뿐 현재 실행 evidence가 없다.
따라서 version 관찰이나 계획된 fixture를 commit 행동 검증 또는 cross-product
동등성으로 해석하지 않는다.

향후 실제 비교는 upstream과 local을 서로 격리된 home 또는 새 task에 설치하고 같은
fixture를 여러 번 실행한다. 결과 문구가 아니라 trigger, 승인 gate, mutation 경계,
산출물·검증 evidence를 비교한다. upstream runtime이 자동 수정, telemetry 또는
browser daemon을 요구하면 local의 보고 전용·승인형 경계와 별도 항목으로 기록한다.

<a id="protected-assets"></a>
## 보호 자산과 파괴적 변경

보호 대상은 다음과 같다.

- `scripts/`
- `templates/`
- `assets/`
- `references/`
- `prompts/`
- `agents/`
- `commands/`
- `hooks/`
- `bin/`
- `skills/**/example/`, `skills/**/examples/`
- `evals/`, `tests/`
- plugin manifest와 MCP/LSP 설정
- `LICENSE*`, `NOTICE*`

추가·내용 수정·보완에는 asset-impact 기록과 승인이 필요하다. 삭제·이동·교체에는
별도의 destructive approval이 필요하며 일반 최신화 승인으로 대체하지 않는다.
reference에서 파일·번역문·자산·script·test·template을 가져와야 하면
`adapted`로 재분류해 provenance·license·보호 자산 gate를 다시 수행한다. 수정 없는
원본 반입은 `vendored`로 분류하고 file hash와 원본 test를 고정한다.

<a id="maintainer-responsibilities"></a>
## 관리자 책임 경계

`skill-portfolio-maintainer`는 upstream 탐색, mode·lifecycle 분류, registry와
관찰 evidence, 의미 diff, provenance와 보호 자산 영향을 담당한다. 출처를 분류하거나
promotion handoff를 만들 뿐 plugin artifact를 생성하지 않는다.

`harness-plugin-maintainer`는 승인된 사용자 정본에서 Codex·Claude runtime,
manifest, NOTICE·license closure, build·smoke·release artifact를 생성·검증한다.
승인되지 않았거나 blocked인 upstream 파일을 payload에 넣지 않는다. 출처 분류와
패키징은 독립 gate다.

<a id="validation-and-rollback"></a>
## 검증 명령, 증적 위치와 rollback

관리자 검증 명령:

```bash
python maintainer/skills/skill-portfolio-maintainer/scripts/check_upstreams.py
python maintainer/skills/skill-portfolio-maintainer/scripts/check_upstreams.py --source openai-codex-skill-creator --verify-watched-paths
python maintainer/skills/skill-portfolio-maintainer/scripts/validate_registry.py
python maintainer/skills/skill-portfolio-maintainer/evals/run_evals.py
python maintainer/skills/custom-skill-design/evals/run_evals.py
python maintainer/upstreams/provenance/im-not-ai/tests/test_humanize_korean.py
```

주요 evidence:

- 관계·정책: `maintainer/upstreams/registry.json`
- 상태·관찰: `maintainer/upstreams/lock.json`
- local consumer: `maintainer/upstreams/provenance/current-skills.json`
- humanize NOTICE: `maintainer/upstreams/provenance/im-not-ai/NOTICE.md`
- humanize file-map: `maintainer/upstreams/provenance/im-not-ai/file-map.json`
- humanize promotion: `maintainer/upstreams/promotions/humanize-korean-im-not-ai-v2.3.0.json`
- Anthropic NOTICE·file-map: `maintainer/upstreams/provenance/anthropic-skills/`
- UI/UX NOTICE·file-map: `maintainer/upstreams/provenance/ui-ux-pro-max/`
- Motion NOTICE·file-map·제3자 판정: `maintainer/upstreams/provenance/lottiefiles-motion-design/`
- runtime allowlist: `maintainer/plugin/runtime-allowlist.json`
- capability inventory: `maintainer/plugin/CAPABILITIES.json`
- release artifact facts: `maintainer/plugin/release.json`
- 패키징 NOTICE: `plugins/harness-kit/THIRD_PARTY_NOTICES.md`
- 패키징 lock: `plugins/harness-kit/UPSTREAMS.lock.json`
- 문서 merge coverage: `maintainer/inventory/upstream-governance-doc-merge.json`

모든 direct promotion은 이전 lock snapshot, 승인 ref, file-map, 생성 hash와 검증
결과를 기록한다. rollback은 해당 snapshot과 승격 파일을 복원한 뒤 registry,
provenance, skill eval과 plugin 검사를 다시 수행한다. 자동 파괴 명령으로 rollback을
대체하지 않는다.

<a id="migration-appendix"></a>
## Migration과 superseded 기록

다음 세 문서의 규범과 현황은 이 문서로 통합되었고 redirect stub 없이 제거한다.
원문 SHA-256과 모든 heading·table row·list rule·command block·evidence path의
destination/disposition은
`maintainer/inventory/upstream-governance-doc-merge.json`에 보존한다.

| 제거한 원본 | SHA-256 | 처리 |
|---|---|---|
| `.user-docs/Skill_Upstream_Update_Policy.md` | `4ed6fc34f525b8a8c557fdde52984e5af7eed98a0e6eccd7473a7ff227dc60cb` | 정책 규칙을 병합·중복 제거 |
| `.user-docs/Imported_Skill_Provenance.md` | `0394cd4358efd4071d183166dc1ea5cb162f4452d948b9b7aa66aaa71e475376` | direct provenance를 현행 machine facts로 교정해 병합 |
| `.user-docs/External_Skill_References.md` | `7058a8e2d8ff11dc7d4ab71400f2edf781e3742f6306a3dccf38cbd6bb9b5f64` | concept·behavior reference와 동등성 한계를 병합 |

명시적으로 superseded 또는 historical 처리한 사실:

- “사용자 skill 20개”는 Phase 1 정본 19개로 superseded했다.
- UI/UX Pro Max와 Motion Design의 “패키징 대기/예정”은 payload·NOTICE 포함 완료로
  superseded했다.
- 패키징 NOTICE가 im-not-ai와 Anthropic만 포함한다는 설명은 UI/UX·Motion을 포함한
  모든 패키징 direct source 고지로 superseded했다.
- 모든 출처를 2026-07-30 하나의 확인일로 묶지 않고 lock의 source별 확인일을 쓴다.
- 삭제된 `pre-commit`의 Superpowers reference는 historical이며 `commit`에
  승계하지 않는다.

과거 `improvement_plan/**`의 경로와 당시 상태는 historical evidence이므로 수정하지
않는다. 복구가 필요하면 이 appendix, coverage manifest와 Git history를 함께 사용한다.
