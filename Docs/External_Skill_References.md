# External Skill References

This document records external official or reputable sources used as references only. It does not mean upstream files have been copied into this repository.

## Reference Sources

| Source | Class | Internal skills | Reference use | Tracking | Checked |
|---|---|---|---|---|---|
| [OpenAI Product Design](https://github.com/openai/role-specific-plugins/tree/main/plugins/product-design) | official | `frontend-design`, `design-prototype-docs`, `create-prototype` | Product design, prototype, critique and handoff ideas only | branch + observed commit | 2026-07-29 |
| [Superpowers](https://github.com/obra/superpowers) | reputable-third-party | `design-doc`, `impl-doc`, `impl-fe-be-doc`, `impl-verify`, `multi-review`, `pre-commit`, `custom-skill-design` | Planning, execution, verification and review concepts only | latest stable release | 2026-07-29 |
| [gstack](https://github.com/garrytan/gstack) | reputable-third-party | `design-doc`, `impl-fe-be-doc`, `multi-review`, `frontend-design` | Role-based design, QA and release concepts only | default branch commit | 2026-07-29 |
| [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | standard | `commit` | Commit message structure | documentation version | 2026-07-29 |
| [OpenAI AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | official | `context-doc`, `harness-setup`, `doc-audit` | `AGENTS.md` canonical project guidance | current documentation | 2026-07-29 |
| [Claude Code memory documentation](https://code.claude.com/docs/en/memory) | official | `context-doc`, `harness-setup`, `doc-audit` | `CLAUDE.md` importing `AGENTS.md` with `@AGENTS.md` | current documentation | 2026-07-29 |
| [Claude Agent Skills documentation](https://claude.com/skills) | official | `custom-skill-design` | Current skill folder and invocation model; no file copy under this relationship | current documentation | 2026-07-29 |

## Rules

- Reference entries may influence workflow, terminology, or validation ideas.
- Reference entries must not include upstream files, translated text, assets, scripts, tests, or templates.
- If an update requires copying or translating upstream content, reclassify the source as `adapted` and run the imported provenance gates.
- Adapted direct-import relationships are excluded from this reference-only document. See `Docs/Imported_Skill_Provenance.md`.

`frontend-design`의 Anthropic 원본 관계와 `custom-skill-design`의 Anthropic
`skill-creator` 관계는 번역·축약·재구성된 adapted 관계이므로 이 표가 아니라
`Docs/Imported_Skill_Provenance.md`에서 라이선스·고정 ref·변경 범위를 추적한다.

Machine-readable source records live in `maintainer/upstreams/registry.json`, `maintainer/upstreams/lock.json`, and `maintainer/upstreams/provenance/current-skills.json`.
