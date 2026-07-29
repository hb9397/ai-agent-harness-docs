# External Skill References

This document records external official or reputable sources used as references only. It does not mean upstream files have been copied into this repository.

## Reference Sources

| Source | Class | Internal skills | Reference use | Checked |
|---|---|---|---|---|
| Anthropic Frontend Design | official | `frontend-design`, `design-prototype-docs`, `create-prototype` | Distinctive production frontend design principles | 2026-07-29 |
| OpenAI Product Design | official | `frontend-design`, `design-prototype-docs`, `create-prototype` | Product design, prototype, critique, handoff workflow ideas | 2026-07-29 |
| Superpowers | reputable-third-party | `design-doc`, `impl-doc`, `impl-fe-be-doc`, `impl-verify`, `multi-review`, `pre-commit`, `custom-skill-design` | Planning, execution, verification, code review, skill writing workflow concepts | 2026-07-29 |
| gstack | reputable-third-party | `design-doc`, `impl-fe-be-doc`, `multi-review`, `frontend-design` | Role-based design, review, QA, release workflow concepts | 2026-07-29 |
| Conventional Commits 1.0.0 | standard | `commit` | Commit message structure | 2026-07-29 |
| OpenAI AGENTS.md documentation | official | `context-doc`, `harness-setup`, `doc-audit` | AGENTS.md canonical project guidance | 2026-07-29 |
| Claude Code memory documentation | official | `context-doc`, `harness-setup`, `doc-audit` | `CLAUDE.md` importing `AGENTS.md` with `@AGENTS.md` | 2026-07-29 |
| Claude Skills / skill creator guidance | official | `custom-skill-design` | Skill folder and SKILL.md authoring model | 2026-07-29 |

## Rules

- Reference entries may influence workflow, terminology, or validation ideas.
- Reference entries must not include upstream files, translated text, assets, scripts, tests, or templates.
- If an update requires copying or translating upstream content, reclassify the source as `adapted` and run the imported provenance gates.
- `humanize-korean` is not listed here as an active reference because it is a Phase 4 candidate for possible adapted integration.

Machine-readable source records live in `maintainer/upstreams/registry.json`, `maintainer/upstreams/lock.json`, and `maintainer/upstreams/provenance/current-skills.json`.
