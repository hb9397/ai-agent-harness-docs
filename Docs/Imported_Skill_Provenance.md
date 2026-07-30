# 반입 스킬 출처 추적

이 문서는 하네스 플러그인에 포함·변형·패키징되는 업스트림 콘텐츠를 기록한다. 참조 전용 출처는 `Docs/External_Skill_References.md`에서 별도로 추적한다.

현재 감사 결과, 업스트림 저장소 2개와의 `adapted` 관계 3건이 확인되었다.

## 현재 상태

| 항목 | 상태 | 비고 |
|---|---|---|
| 현재 사용자 스킬 18개 | `adapted` 스킬 2개 | `humanize-korean`은 `im-not-ai`에서 변형되었으며, `frontend-design`은 Anthropic Skills를 번역하고 재구성한 파생물이다. |
| 현재 관리자 스킬 3개 | `adapted` 스킬 1개 | `custom-skill-design`은 Anthropic `skill-creator`를 번역하고 재구성한 파생물이다. |
| `humanize-korean` | `accepted` `adapted` | 업스트림: `epoko77-ai/im-not-ai` v2.3.0, 커밋 `82137e858763dadb99561f194c5c00465735017b`, MIT. |
| `frontend-design` | `accepted` `adapted` | 업스트림: `anthropics/skills`, 커밋 `b29e7cf65e5cb78a5ac33d582270551bc74a14eb`, Apache-2.0. |
| `custom-skill-design` | `accepted` `adapted`, 관리자 전용 | 동일한 Anthropic Skills 커밋과 라이선스를 사용하며, 사용자 플러그인에는 패키징하지 않는다. |
| 플러그인 NOTICE | 생성됨 | 패키징된 `im-not-ai`와 Anthropic `frontend-design`의 라이선스 충족 사항을 포함한다. |

## 승인된 `adapted` 출처

| 로컬 스킬 | 업스트림 | 버전 | 처리 방식 |
|---|---|---|---|
| `skills/humanize-korean` | `https://github.com/epoko77-ai/im-not-ai` | `v2.3.0` / `82137e858763dadb99561f194c5c00465735017b` | 변형된 지침과 로컬 보호 스크립트. 전체 업스트림 런타임을 `vendored`로 반입하지 않는다. |
| `skills/frontend-design` | `https://github.com/anthropics/skills/tree/main/skills/frontend-design` | `main` / `b29e7cf65e5cb78a5ac33d582270551bc74a14eb` | 한국어 번역, 축약한 디자인 규칙, 프로젝트 라우팅 및 검증을 추가했다. 사용자 플러그인에 패키징한다. |
| `maintainer/skills/custom-skill-design` | `https://github.com/anthropics/skills/tree/main/skills/skill-creator` | `main` / `b29e7cf65e5cb78a5ac33d582270551bc74a14eb` | 한국어 번역과 저장소 전용 관리자 워크플로. 관리자 전용이며 사용자 플러그인에서 제외한다. |

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
