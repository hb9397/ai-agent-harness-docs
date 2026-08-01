# 외부 스킬 참조

이 문서는 외부 공식·신뢰 출처에서 **개념만 참고하는 `reference` 관계**를 기록한다.
업스트림 파일을 복사·번역·패키징했다는 뜻이 아니며, 원본 runtime과 동일하게
동작한다는 보증도 아니다. 번역·재구성한 `adapted` 관계는
`.user-docs/Imported_Skill_Provenance.md`에서 별도로 추적한다.

## 참조 출처

| 출처 | 분류 | 내부 스킬 | 참조 용도 | 추적 방식 | 확인일 |
|---|---|---|---|---|---|
| [OpenAI Product Design](https://github.com/openai/role-specific-plugins/tree/main/plugins/product-design) | 공식(`official`) | `frontend-design`, `design-prototype-docs`, `create-prototype` | 제품 디자인, 프로토타입, 비평 및 인계 개념 | 브랜치 + 확인된 커밋 | 2026-07-30 |
| [Superpowers v6.2.0](https://github.com/obra/superpowers/releases/tag/v6.2.0) | 신뢰할 수 있는 서드파티(`reputable-third-party`) | `design-doc`, `impl-doc`, `impl-fe-be-doc`, `impl-reuse-scan`(제한적), `impl-verify`, `multi-review`, `pre-commit`, `custom-skill-design` | 브레인스토밍, 계획, TDD, 기존 패턴 우선, 완료 전 검증, 병렬 리뷰 및 스킬 작성 원칙 | 최신 안정 릴리스 | 2026-07-30 |
| [gstack](https://github.com/garrytan/gstack) | 신뢰할 수 있는 서드파티(`reputable-third-party`) | `create-prototype`(제한적), `design-doc`, `design-prototype-docs`, `impl-doc`, `impl-fe-be-doc`, `impl-reuse-scan`(제한적), `impl-verify`, `multi-review` | 역할 기반 명세·계획·디자인·`qa-only`·리뷰 개념 | 기본 브랜치 커밋 | 2026-07-30 |
| [OpenAI Codex `skill-creator`](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md) | 공식(`official`) | `custom-skill-design` | 간결성, 작업별 지침 자유도, 점진적 공개, 보조 자산 역할, 검증 무결성, 선택적 `agents/openai.yaml` | 기본 브랜치 + 파일 커밋 | 2026-07-30 |
| [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | 표준(`standard`) | `commit` | 커밋 메시지 구조 | 문서 버전 | 2026-07-29 |
| [OpenAI AGENTS.md documentation](https://github.com/openai/codex/blob/main/docs/agents_md.md) | 공식(`official`) | `context-doc`, `harness-bootstrap`, `harness-setup`, `doc-audit` | Codex의 `AGENTS.md` 프로젝트 지침 계약 | 현행 문서 | 2026-07-30 |
| [Claude Code memory documentation](https://code.claude.com/docs/en/memory) | 공식(`official`) | `context-doc`, `harness-bootstrap`, `harness-setup`, `doc-audit` | `CLAUDE.md`에서 `@AGENTS.md`를 불러오는 브리지 | 현행 문서 | 2026-07-30 |
| [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 신뢰할 수 있는 서드파티(`reputable-third-party`) | `design-prototype-docs`, `create-prototype`, `frontend-design`, `impl-verify` | 디자인 시스템을 입력으로 받는 계약, 기존 제품 토큰 우선, 대비·focus·터치 대상·상태 검증 관점 | 안정 릴리스 `v2.11.3` 고정 | 2026-07-31 |
| [Motion Design](https://github.com/LottieFiles/motion-design-skill) | 신뢰할 수 있는 서드파티(`reputable-third-party`) | `design-prototype-docs`, `create-prototype`, `frontend-design`, `impl-verify` | 모션 목적 분류, 승인된 명세만 구현, reduced-motion 대체안과 반복·성능 검증 관점 | 브랜치 head 고정 | 2026-07-31 |

위 두 출처는 같은 저장소를 **직접 반입 관계와 동시에** 추적한다.
`skills/ui-ux-pro-max`와 `skills/motion-design`은 `adapted`이며
`.user-docs/Imported_Skill_Provenance.md`에서 다룬다. 이 표의 참고 관계는 기존 스킬 4종에
**개념만** 반영한 것으로, 업스트림 파일·번역문·요약문을 반입하지 않는다. 두 관계는
하나의 `relationship_group`으로 묶여 같은 고정 SHA를 가리킨다.

`frontend-design`의 Anthropic 원본 관계와 `custom-skill-design`의 Anthropic
`skill-creator` 관계는 번역·축약·재구성된 `adapted` 관계다. 위 표의 참조 관계와
혼동하지 않고 `.user-docs/Imported_Skill_Provenance.md`에서 라이선스·고정 ref·파일
대응표를 추적한다.

## impl 계열 재분류

모든 `impl-*` 스킬은 Superpowers와 gstack의 일부 정책을 참고할 수 있다. 다만
참조 강도와 채택 범위가 서로 다르며 두 외부 workflow 전체를 합치는 것은 아니다.

| 로컬 스킬 | Superpowers에서 참고할 수 있는 정책 | gstack에서 참고할 수 있는 정책 | 현재 반영 상태와 후속 후보 |
|---|---|---|---|
| `impl-doc` | `writing-plans`, test-first 순서, 계획 자체검토 | `/spec`, `/plan-eng-review` | 정확한 범위·파일·의존·검증 게이트는 현재 반영. test-first 순서와 계획 자체검토는 **후속 반영 후보**다. 완성 코드 전체는 계획서에 넣지 않는다. |
| `impl-fe-be-doc` | 계획 원칙 + 인접 태스크 계약·실행 인계 | `/spec`, `/plan-eng-review`, `/plan-design-review` | FE↔API↔BE↔DB 추적성과 Phase 검증은 현재 반영. 태스크별 명시적 consumes/produces와 실행 인계는 **후속 반영 후보**다. |
| `impl-reuse-scan` | 기존 구조·패턴 우선, working-example 비교 | Search Before Building, Existing Code Leverage | 기존 자산 발견·분류·사용자 결정·무수정 게이트가 현재 반영된 **제한적 참조**다. |
| `impl-verify` | `verification-before-completion`, 원 증상 재현, 증거와 추정 분리 | 수정 없는 `/qa-only` 보고 방식 | fresh 명령 증거·`UNKNOWN`·보고 전용 경계는 현재 반영. 원 증상 재현 절차는 **후속 반영 후보**다. gstack 자동 수정 runtime은 가져오지 않는다. |

관련 비 impl 항목은 `design-doc`이 브레인스토밍·요구 구체화, `multi-review`가 병렬
전문 리뷰·증거·중복 제거, `pre-commit`이 완료 전 기계적 검사 일부를 참조한다.
gstack의 `/design-review`는 구현 후 시각 QA 성격이므로 현재 로컬
`frontend-design`의 직접 참조로 분류하지 않는다.

## 2026-07-30 최신본 관찰 결과

| 출처 | 최신 관찰값 | 로컬 상태 | 판정 |
|---|---|---|---|
| Superpowers | `v6.2.0`, `3dcbd5c4b48e02263fbf4a3c01e3fe4f81d584d9` | lock과 일치 | 최신 안정 릴리스 메타데이터 일치 |
| gstack | `main`, `a3259400a366593e0c909dd9ac3e59752efd2488`, 내부 버전 `1.60.1.0` | lock과 일치 | 최신 기본 브랜치 메타데이터 일치 |
| OpenAI Codex `skill-creator` | Codex `main` `b1ccaa0e080f59cfd71a136f6fcc60a4f2d60fba`; `SKILL.md` 마지막 변경 `59533a2c26e349c59417e4773b930c26211d7bdd` | `SKILL.md`와 `references/openai_yaml.md` reference lock 등록 | 두 공식 파일과 로컬 설치본의 줄바꿈 정규화 내용 일치 확인. 보조 스키마 파일은 API rate limit으로 마지막 변경 커밋을 주장하지 않고 내용 hash만 기록 |
| Anthropic Skills | `main`, `b29e7cf65e5cb78a5ac33d582270551bc74a14eb` | `frontend-design`, `custom-skill-design`의 accepted/embedded와 일치 | 최신 관찰값과 현재 승인 기준 일치 |
| im-not-ai | `v2.3.0`, `82137e858763dadb99561f194c5c00465735017b` | `humanize-korean` accepted/embedded와 일치 | 최신 안정 릴리스와 현재 승인 기준 일치 |
| OpenAI Product Design | `main`, `fe5608d2512a7d6a7b9821ce8a88c48464ecd6e4` | reference lock과 일치 | 최신 기본 브랜치 메타데이터 일치 |

Superpowers는 관련 exact skill 경로의 마지막 변경 커밋까지 lock에 기록했다. gstack은
기본 브랜치 SHA와 경로 존재를 확인했지만 exact 경로별 마지막 변경 조회 도중 GitHub
rate limit이 발생해 불완전한 path 결과를 lock에 저장하지 않았다. 따라서 gstack은
현재 main 기준 수동 의미 감사 결과를 사용하되 path-level 자동 증적은 `부분 미검증`이다.
OpenAI Codex `skill-creator`의 보조 `references/openai_yaml.md`도 같은 제한 때문에
마지막 변경 커밋은 미확인으로 남기되, 공식 raw 파일과 로컬 시스템 파일의 정규화
SHA-256 일치값을 lock에 기록했다.

`check_upstreams.py`의 성공은 최신 ref·SHA를 **관찰**했다는 뜻이다. `reference`
출처의 파일을 내려받거나, `adapted` 스킬에 변경사항을 자동 적용하거나, 원본 행동을
재현했다는 뜻은 아니다. 새 `observed` 값이 생기면 관리자가 의미 차이·라이선스·보호
자산 영향을 검토한 뒤에만 `accepted`와 `embedded`를 승격한다.

## 동작 동등성 판정 기준

| 관계 | 기대하는 동등성 | 검사 방법 |
|---|---|---|
| `reference` | 선택한 개념의 **의미적 행동 불변 조건**만 일치 | 같은 fixture에서 트리거, 승인 게이트, 보고 전용 여부, 산출물 구조, 검증 증거를 비교 |
| `adapted` | 승인한 upstream 기준과 로컬 변경 목적을 함께 만족 | accepted SHA 확인 + 파일 대응표 + 로컬 회귀 eval + 필요 시 upstream 원본과 differential smoke |
| `vendored` | 고정한 원본 파일·runtime의 재현성 | 파일 hash·라이선스·원본 테스트·Codex/Claude 설치 smoke를 모두 확인 |

현재 활성 `vendored` 관계는 없다. 따라서 이 저장소가 외부 Superpowers나 gstack
runtime을 그대로 제공하거나 원본과 동일하게 동작한다고 주장해서는 안 된다.
`humanize-korean`은 실행형 회귀 테스트가 있지만, `frontend-design`과
`custom-skill-design`은 주로 정적 계약 eval이다. Superpowers·gstack 매핑에는 이번에
Codex/Claude smoke prompt와 의미 불변 조건 **선언**을 등록했지만, 문자열 선언 자체는
실행 증적이 아니다. 실제 격리 실행 기록이 없으면 동작 검증은 `미검증`으로 남긴다.

관리자 검증 명령:

```bash
python maintainer/skills/skill-portfolio-maintainer/scripts/check_upstreams.py
python maintainer/skills/skill-portfolio-maintainer/scripts/check_upstreams.py --source openai-codex-skill-creator --verify-watched-paths
python maintainer/skills/skill-portfolio-maintainer/scripts/validate_registry.py
python maintainer/skills/skill-portfolio-maintainer/evals/run_evals.py
python maintainer/skills/custom-skill-design/evals/run_evals.py
python maintainer/upstreams/provenance/im-not-ai/tests/test_humanize_korean.py
```

실제 행동 비교는 원본과 로컬을 각각 격리된 home 또는 새 task에 설치하고 같은 fixture를
여러 번 실행한다. 결과 문장 자체가 아니라 위 표의 행동 불변 조건을 비교하며, 원본
runtime이 자동 수정·telemetry·브라우저 daemon을 요구하면 로컬의 보고 전용·승인형
경계와 별도 항목으로 기록한다.

## 정책 규칙

- 참조 항목에는 업스트림 파일, 번역문, 자산, 스크립트, 테스트 또는 템플릿을
  포함하지 않는다.
- 업데이트에 업스트림 콘텐츠 복사 또는 번역이 필요하면 `adapted`로 재분류하고
  provenance·라이선스·보호 자산 게이트를 수행한다.
- 원본을 수정 없이 포함하려면 `vendored`로 분류하고 파일 hash와 원본 테스트를
  고정한다.
- 템플릿·스크립트·자산·eval의 삭제·이동·교체는 최신화 작업과 분리해 사용자 승인을
  받는다.

기계 판독용 기록은 `maintainer/upstreams/registry.json`,
`maintainer/upstreams/lock.json`,
`maintainer/upstreams/provenance/current-skills.json`에서 관리한다.
