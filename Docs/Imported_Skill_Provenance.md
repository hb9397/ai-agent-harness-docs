# Imported Skill Provenance

This document records upstream content that is included, adapted, or packaged into the harness plugin. Reference-only sources are tracked separately in `Docs/External_Skill_References.md`.

The current audit confirms three adapted relationships from two upstream repositories.

## Current State

| Item | Status | Notes |
|---|---|---|
| Current 18 user skills | two adapted skills | `humanize-korean` is adapted from `im-not-ai`; `frontend-design` is a translated and restructured derivative of Anthropic Skills. |
| Current 3 maintainer skills | one adapted skill | `custom-skill-design` is a translated and restructured derivative of Anthropic `skill-creator`. |
| `humanize-korean` | accepted adapted | Upstream: `epoko77-ai/im-not-ai` v2.3.0, commit `82137e858763dadb99561f194c5c00465735017b`, MIT. |
| `frontend-design` | accepted adapted | Upstream: `anthropics/skills`, commit `b29e7cf65e5cb78a5ac33d582270551bc74a14eb`, Apache-2.0. |
| `custom-skill-design` | accepted adapted, manager-only | Same Anthropic Skills commit and license; it is not packaged in the user plugin. |
| Plugin NOTICE | generated | Includes packaged `im-not-ai` and Anthropic `frontend-design` license closure. |

## Accepted Adapted Sources

| Local skill | Upstream | Version | Treatment |
|---|---|---|---|
| `skills/humanize-korean` | `https://github.com/epoko77-ai/im-not-ai` | `v2.3.0` / `82137e858763dadb99561f194c5c00465735017b` | Adapted guidance and local guard script. Full upstream runtime is not vendored. |
| `skills/frontend-design` | `https://github.com/anthropics/skills/tree/main/skills/frontend-design` | `main` / `b29e7cf65e5cb78a5ac33d582270551bc74a14eb` | Korean translation, shortened design rules, project routing and verification added. Packaged in the user plugin. |
| `maintainer/skills/custom-skill-design` | `https://github.com/anthropics/skills/tree/main/skills/skill-creator` | `main` / `b29e7cf65e5cb78a5ac33d582270551bc74a14eb` | Korean translation and a repository-specific manager workflow. Manager-only; excluded from the user plugin. |

Details:

- Notice: `maintainer/upstreams/provenance/im-not-ai/NOTICE.md`
- File map: `maintainer/upstreams/provenance/im-not-ai/file-map.json`
- Promotion decision: `maintainer/upstreams/promotions/humanize-korean-im-not-ai-v2.3.0.json`
- Runtime allowlist: `maintainer/plugin/runtime-allowlist.json`
- Packaged notice: `plugins/ai-agent-harness/THIRD_PARTY_NOTICES.md`
- Packaged upstream lock: `plugins/ai-agent-harness/UPSTREAMS.lock.json`
- Anthropic notice and file map: `maintainer/upstreams/provenance/anthropic-skills/`

## Required For Future Direct Imports

Any future `vendored` or `adapted` entry must record:

- upstream repository and immutable permalink
- tag and full 40-character commit SHA
- license SPDX, license URL, and license SHA-256
- copyright and NOTICE text
- file-by-file treatment: `verbatim`, `modified`, `excluded`, or `local-only`
- protected asset impact approval
- destructive approval for deletion, move, or replacement
- validation results and rollback path

`im-not-ai` and Anthropic Skills must not be represented as reference-only for the local files
listed above. Separate conceptual references to current documentation or other design sources may
remain in `Docs/External_Skill_References.md`, but the translated/restructured relationships and
their redistribution obligations are tracked here.
