# 외부 스킬 참조

이 문서는 참조 목적으로만 사용한 외부 공식 출처 또는 신뢰할 수 있는 출처를 기록한다. 업스트림 파일을 이 저장소에 복사했다는 뜻은 아니다.

## 참조 출처

| 출처 | 분류 | 내부 스킬 | 참조 용도 | 추적 방식 | 확인일 |
|---|---|---|---|---|---|
| [OpenAI Product Design](https://github.com/openai/role-specific-plugins/tree/main/plugins/product-design) | 공식(`official`) | `frontend-design`, `design-prototype-docs`, `create-prototype` | 제품 디자인, 프로토타입, 비평 및 인계 아이디어만 참조 | 브랜치 + 확인된 커밋 | 2026-07-29 |
| [Superpowers](https://github.com/obra/superpowers) | 신뢰할 수 있는 서드파티(`reputable-third-party`) | `design-doc`, `impl-doc`, `impl-fe-be-doc`, `impl-verify`, `multi-review`, `pre-commit`, `custom-skill-design` | 계획, 실행, 검증 및 리뷰 개념만 참조 | 최신 안정 릴리스 | 2026-07-29 |
| [gstack](https://github.com/garrytan/gstack) | 신뢰할 수 있는 서드파티(`reputable-third-party`) | `design-doc`, `impl-fe-be-doc`, `multi-review`, `frontend-design` | 역할 기반 디자인, QA 및 릴리스 개념만 참조 | 기본 브랜치 커밋 | 2026-07-29 |
| [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | 표준(`standard`) | `commit` | 커밋 메시지 구조 | 문서 버전 | 2026-07-29 |
| [OpenAI AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | 공식(`official`) | `context-doc`, `harness-setup`, `doc-audit` | `AGENTS.md` 정본 프로젝트 지침 | 현행 문서 | 2026-07-29 |
| [Claude Code memory documentation](https://code.claude.com/docs/en/memory) | 공식(`official`) | `context-doc`, `harness-setup`, `doc-audit` | `CLAUDE.md`가 `@AGENTS.md`로 `AGENTS.md`를 불러오는 방식 | 현행 문서 | 2026-07-29 |
| [Claude Agent Skills documentation](https://claude.com/skills) | 공식(`official`) | `custom-skill-design` | 현행 스킬 폴더와 호출 모델. 이 관계에서는 파일을 복사하지 않음 | 현행 문서 | 2026-07-29 |

## 규칙

- 참조 항목은 워크플로, 용어 또는 검증 아이디어에 영향을 줄 수 있다.
- 참조 항목에는 업스트림 파일, 번역문, 자산, 스크립트, 테스트 또는 템플릿을 포함해서는 안 된다.
- 업데이트에 업스트림 콘텐츠 복사 또는 번역이 필요하면 출처를 `adapted`로 재분류하고 반입 출처 추적 게이트를 수행한다.
- `adapted` 직접 반입 관계는 이 참조 전용 문서에서 제외한다. `Docs/Imported_Skill_Provenance.md`를 참조한다.

`frontend-design`의 Anthropic 원본 관계와 `custom-skill-design`의 Anthropic
`skill-creator` 관계는 번역·축약·재구성된 adapted 관계이므로 이 표가 아니라
`Docs/Imported_Skill_Provenance.md`에서 라이선스·고정 ref·변경 범위를 추적한다.

기계 판독용 출처 기록은 `maintainer/upstreams/registry.json`, `maintainer/upstreams/lock.json`, `maintainer/upstreams/provenance/current-skills.json`에서 관리한다.
