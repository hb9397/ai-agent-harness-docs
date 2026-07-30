# 반입 스킬 출처 추적

이 문서는 하네스 플러그인에 포함·변형·패키징되는 업스트림 콘텐츠를 기록한다. 참조 전용 출처는 `Docs/External_Skill_References.md`에서 별도로 추적한다.

현재 감사 결과, 업스트림 저장소 2개와의 `adapted` 관계 3건이 확인되었다.
활성 `vendored` 관계는 없다.

## 현재 상태

| 항목 | 상태 | 비고 |
|---|---|---|
| 현재 사용자 스킬 18개 | `adapted` 스킬 2개 | `humanize-korean`은 `im-not-ai`에서 변형되었으며, `frontend-design`은 Anthropic Skills를 번역하고 재구성한 파생물이다. |
| 현재 관리자 스킬 3개 | `adapted` 스킬 1개 | `custom-skill-design`은 Anthropic `skill-creator`를 번역하고 재구성한 파생물이다. |
| `humanize-korean` | `accepted` `adapted` | 업스트림: `epoko77-ai/im-not-ai` v2.3.0, 커밋 `82137e858763dadb99561f194c5c00465735017b`, MIT. |
| `frontend-design` | `accepted` `adapted` | 업스트림: `anthropics/skills`, 커밋 `b29e7cf65e5cb78a5ac33d582270551bc74a14eb`, Apache-2.0. |
| `custom-skill-design` | `accepted` `adapted`, 관리자 전용 | 동일한 Anthropic Skills 커밋과 라이선스를 사용하며, 사용자 플러그인에는 패키징하지 않는다. |
| `custom-skill-design` 이중 upstream | `adapted` + `reference` | Anthropic `skill-creator`는 번역·재구성 원본으로, OpenAI Codex `skill-creator`는 공식 설계 원칙 참조로 각각 최신성을 확인한다. |
| 최신본 확인 | 2026-07-30 일치 | Anthropic Skills `main`과 im-not-ai 최신 안정 릴리스의 `observed`가 세 adapted 관계의 `accepted` 기준과 일치한다. OpenAI Codex reference도 별도 `observed`와 감시 경로를 확인했다. 어느 관계도 자동 승격·자동 반영하지 않는다. |
| 플러그인 NOTICE | 생성됨 | 패키징된 `im-not-ai`와 Anthropic `frontend-design`의 라이선스 충족 사항을 포함한다. |

## 승인된 `adapted` 출처

| 로컬 스킬 | 업스트림 | 버전 | 처리 방식 |
|---|---|---|---|
| `skills/humanize-korean` | `https://github.com/epoko77-ai/im-not-ai` | `v2.3.0` / `82137e858763dadb99561f194c5c00465735017b` | 변형된 지침과 로컬 보호 스크립트. 전체 업스트림 런타임을 `vendored`로 반입하지 않는다. |
| `skills/frontend-design` | `https://github.com/anthropics/skills/tree/main/skills/frontend-design` | `main` / `b29e7cf65e5cb78a5ac33d582270551bc74a14eb` | 한국어 번역, 축약한 디자인 규칙, 프로젝트 라우팅 및 검증을 추가했다. 사용자 플러그인에 패키징한다. |
| `maintainer/skills/custom-skill-design` | `https://github.com/anthropics/skills/tree/main/skills/skill-creator` | `main` / `b29e7cf65e5cb78a5ac33d582270551bc74a14eb` | 한국어 번역과 저장소 전용 관리자 워크플로. 관리자 전용이며 사용자 플러그인에서 제외한다. |

`custom-skill-design`은 이 직접 반입 관계와 별도로
[`openai/codex`의 공식 `skill-creator`](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md)를
참조한다. OpenAI 관계는 간결성, 지침 자유도, 점진적 공개, 검증 무결성,
`agents/openai.yaml` 같은 개념만 독자적으로 반영한 `reference`이며 OpenAI 파일이나
내부 helper script를 반입하지 않는다. 따라서 Anthropic 관계의 전체 분류는 계속
`adapted`이고 OpenAI 관계를 별도 reference source로 함께 기록한다.

## `custom-skill-design` 이중 upstream 최신화 정책

`Imported_Skill_Provenance.md`의 승인된 반입 표에 Anthropic만 있는 것은 Anthropic
`skill-creator`가 실제 번역·재구성 원본인 `adapted` 관계이기 때문이다. 이것이
`custom-skill-design`의 최신화 대상을 Anthropic 하나로 제한한다는 뜻은 아니다.
관리자는 다음 두 출처를 한 번의 점검 범위에 포함한다.

| 역할 | source ID | 감시 대상 | 새 변경 발견 시 처리 |
|---|---|---|---|
| 번역·재구성 원본 | `skill-creator-guides` | Anthropic `skills/skill-creator/SKILL.md`, `LICENSE.txt` | 로컬 patch와 의미 diff, 라이선스, 보호 자산 영향을 검토하고 승인된 변경만 `accepted`와 `embedded`로 승격한다. |
| 공식 설계 원칙 참조 | `openai-codex-skill-creator` | OpenAI Codex `skill-creator/SKILL.md`, `references/openai_yaml.md` | 간결성, 자유도, 점진적 공개, 자산 역할, 검증 및 Codex 메타데이터 원칙의 차이를 분석해 반영 후보를 만든다. 원본 파일을 복사하거나 `accepted`·`embedded` 상태로 자동 승격하지 않는다. |

두 출처의 최신성은 다음처럼 함께 확인한다.

```bash
python maintainer/skills/skill-portfolio-maintainer/scripts/check_upstreams.py \
  --source skill-creator-guides \
  --source openai-codex-skill-creator \
  --verify-watched-paths
```

이 명령은 읽기 전용 관찰이다. `--write-observed`를 추가해도 `observed`만 갱신하며,
`custom-skill-design` 정본 수정은 두 출처의 차이와 충돌을 관리자가 검토하고 명시적으로
승인한 뒤 별도 작업으로 수행한다. OpenAI reference의 세부 최신 관찰값과 동작 동등성
한계는 `Docs/External_Skill_References.md`에서 추적한다.

## 동작 검증 해석

- `adapted`는 원본과 문장·파일·runtime이 동일하다는 뜻이 아니다. 고정한 accepted
  기준의 핵심 목적과 로컬 변경 목적을 회귀검증한다.
- `humanize-korean`에는 실행형 회귀 테스트가 있다.
- `frontend-design`과 `custom-skill-design`은 현재 정적 계약 eval 중심이므로,
  Codex·Claude의 실제 격리 실행 증적 없이 원본과 동일 동작한다고 주장하지 않는다.
- 새 observed SHA가 accepted와 다르면 최신본을 자동 복사하지 않고 의미 diff,
  라이선스, 보호 자산 영향을 검토한 뒤 별도 승격한다.

세부 자료:

- NOTICE: `maintainer/upstreams/provenance/im-not-ai/NOTICE.md`
- 파일 매핑: `maintainer/upstreams/provenance/im-not-ai/file-map.json`
- 승격 결정: `maintainer/upstreams/promotions/humanize-korean-im-not-ai-v2.3.0.json`
- 런타임 허용 목록: `maintainer/plugin/runtime-allowlist.json`
- 패키징된 NOTICE: `plugins/ai-agent-harness/THIRD_PARTY_NOTICES.md`
- 패키징된 업스트림 잠금: `plugins/ai-agent-harness/UPSTREAMS.lock.json`
- Anthropic NOTICE 및 파일 매핑: `maintainer/upstreams/provenance/anthropic-skills/`

## 향후 직접 반입 필수 항목

향후 모든 `vendored` 또는 `adapted` 항목에는 다음을 기록해야 한다.

- 업스트림 저장소와 변경 불가능한 고정 링크
- 태그와 전체 40자 커밋 SHA
- 라이선스 SPDX, 라이선스 URL 및 라이선스 SHA-256
- 저작권 및 NOTICE 문구
- 파일별 처리 방식: `verbatim`, `modified`, `excluded` 또는 `local-only`
- 보호 자산 영향 승인
- 삭제·이동·교체에 대한 파괴적 변경 승인
- 검증 결과와 롤백 경로

위에 열거한 로컬 파일에 대해 `im-not-ai`와 Anthropic Skills를 참조 전용으로 표시해서는
안 된다. 현행 문서 또는 다른 디자인 출처에 대한 별도의 개념적 참조는
`Docs/External_Skill_References.md`에 남길 수 있지만, 번역·재구성 관계와 그에 따른
재배포 의무는 이 문서에서 추적한다.
