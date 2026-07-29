# example — 하네스 산출물 예시

각 스킬을 실행했을 때 생성되는 산출물 형식을 보여주는 예시 문서다. 소재는 **ACRO(범용 예약 매크로)** 프로젝트로 통일했다.

현행 기준:

- 실제 프로젝트는 `ai-agent-harness` 플러그인을 설치한 뒤 `harness-setup`으로 시작한다.
- `AGENTS.md`가 프로젝트 컨텍스트 정본이다.
- `CLAUDE.md`는 `AGENTS.md`를 읽는 bridge 예제로 둔다.
- `.md` 산출물 생성 후에는 `humanize-korean` 개선안을 확인할 수 있다.
- 제거된 `agent-sync`, `rfp-ingest`, 스킬 copy 설치 모델은 예제 흐름에 포함하지 않는다.

| 파일 | 생성/참조 스킬 | 대표 산출 경로 |
|------|----------------|----------------|
| [design-doc--ACRO.md](./design-doc--ACRO.md) | `design-doc` | `.docs/context-base/DESIGN.md` |
| [design-doc--ACRO-BE.md](./design-doc--ACRO-BE.md) | `design-doc` | `.docs/acro-be/context-base/DESIGN.md` |
| [design-doc--ACRO-FE.md](./design-doc--ACRO-FE.md) | `design-doc` | `.docs/acro-fe/context-base/DESIGN.md` |
| [context-doc--AGENTS.md](./context-doc--AGENTS.md) | `context-doc` | 루트 `AGENTS.md` |
| [context-doc--CLAUDE.md](./context-doc--CLAUDE.md) | `harness-setup` bridge | 루트 `CLAUDE.md` |
| [context-doc--architecture-instruction.md](./context-doc--architecture-instruction.md) | `context-doc` | `.docs/instruction/architecture-instruction.md` |
| [impl-fe-be-doc--ACRO.md](./impl-fe-be-doc--ACRO.md) | `impl-fe-be-doc` | `.docs/impl-doc/{사용자}/acro.md` |
| [impl-doc--selector-recovery.md](./impl-doc--selector-recovery.md) | `impl-doc` | `.docs/impl-doc/{사용자}/selector-recovery.md` |
| [design-prototype-docs--onboarding.md](./design-prototype-docs--onboarding.md) | `design-prototype-docs` | `.docs/prototype/{사용자}/onboarding/design-doc.md` |
| [markdown-refinement-flow.md](./markdown-refinement-flow.md) | `humanize-korean` | 산출물 개선안·승인·재검증 예시 |

리포트형 스킬(`impl-verify`, `multi-review`, `pre-commit`, `doc-audit`)과 코드/커밋 적용 스킬(`frontend-design`, `code-comment`, `commit`, `create-prototype`, `git-scoped-account`)은 별도 예제 산출물을 두지 않는다. 전체 흐름은 [Docs/Harness_Engineering.md](../Docs/Harness_Engineering.md)를 따른다.
