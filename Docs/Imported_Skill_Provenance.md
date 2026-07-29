# Imported Skill Provenance

This document records upstream content that is included, adapted, or packaged into the harness plugin. Reference-only sources are tracked separately in `Docs/External_Skill_References.md`.

Phase 4 promotes one confirmed `adapted` upstream relationship into the user skill set.

## Current State

| Item | Status | Notes |
|---|---|---|
| Current 18 user skills | one adapted source | `humanize-korean` is adapted from `epoko77-ai/im-not-ai` v2.3.0. Other user skills remain native or reference-only. |
| Current 3 maintainer skills | no confirmed direct import | `custom-skill-design` has reference relationships only at Phase 3. |
| `humanize-korean` | accepted adapted | Upstream: `epoko77-ai/im-not-ai` v2.3.0, commit `82137e858763dadb99561f194c5c00465735017b`, MIT. |
| Plugin NOTICE | generated | `plugins/ai-agent-harness/THIRD_PARTY_NOTICES.md` includes the accepted `im-not-ai` notice. |

## Accepted Adapted Sources

| Local skill | Upstream | Version | Treatment |
|---|---|---|---|
| `skills/humanize-korean` | `https://github.com/epoko77-ai/im-not-ai` | `v2.3.0` / `82137e858763dadb99561f194c5c00465735017b` | Adapted guidance and local guard script. Full upstream runtime is not vendored. |

Details:

- Notice: `maintainer/upstreams/provenance/im-not-ai/NOTICE.md`
- File map: `maintainer/upstreams/provenance/im-not-ai/file-map.json`
- Promotion decision: `maintainer/upstreams/promotions/humanize-korean-im-not-ai-v2.3.0.json`
- Runtime allowlist: `maintainer/plugin/runtime-allowlist.json`
- Packaged notice: `plugins/ai-agent-harness/THIRD_PARTY_NOTICES.md`
- Packaged upstream lock: `plugins/ai-agent-harness/UPSTREAMS.lock.json`

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

`im-not-ai` must not appear in `Docs/External_Skill_References.md` as a reference-only source. It is directly tracked here because `humanize-korean` is an adapted local skill and the plugin packages the corresponding NOTICE/license closure.
