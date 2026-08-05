# NOTICE — UI/UX Pro Max

- Upstream: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- Accepted ref: `v2.13.0`
- Accepted commit: `4d140cf8ff6842de13213c7214eff3810371beb2`
- License: MIT
- Copyright: Copyright (c) 2024 Next Level Builder
- License text: `maintainer/upstreams/provenance/ui-ux-pro-max/LICENSE`
- License SHA-256: `738f69dfa83db5c347c678fb9d90e560877059f0de93a327c39001bff92dc014`

## Relationship group

This upstream is tracked through two relationships that must stay pinned to the
same commit.

| Source id | Mode | Local target | Packaged |
|---|---|---|---|
| `ui-ux-pro-max-runtime` | `adapted` | `skills/ui-ux-pro-max` | yes |
| `ui-ux-pro-max-principles` | `reference` | existing design and verification skills | no |

## Import scope

The upstream ships two parallel trees. `src/ui-ux-pro-max/` is generator input
and contains no `SKILL.md`. `.claude/skills/ui-ux-pro-max/` is the generated,
complete skill. The local import target is the generated tree.

Imported: `SKILL.md`, `data/**` (35 CSV files), `references/**` (2 files),
`scripts/**` (4 modules and 2 test modules).

Not imported: the sibling skills `banner-design`, `brand`, `design`,
`design-system`, `slides` and `ui-styling`; the TypeScript install-and-sync CLI
under `cli/`; repository tooling and generator templates.

## Local modification summary

The local `SKILL.md` is rewritten for this harness. It is platform neutral,
removes Claude-only assumptions, adds project-scope confirmation, adds an
approval gate before any file write, and routes implementation, prototype and
motion work through public skill names.

Upstream data, references and scripts are preserved. Upstream scripts already
resolve their own location with `Path(__file__)` and require no path rewriting.
Any local change to those files is recorded in `file-map.json`.
