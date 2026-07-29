# Imported Skill Provenance

Phase 3 found no confirmed current `vendored` or `adapted` upstream skill files in the repository.

## Current State

| Item | Status | Notes |
|---|---|---|
| Current 17 user skills | no confirmed direct import | Some skills have `reference` relationships; see `Docs/External_Skill_References.md`. |
| Current 3 maintainer skills | no confirmed direct import | `custom-skill-design` has reference relationships only at Phase 3. |
| `humanize-korean` | pending candidate | No `skills/humanize-korean/**` files exist yet. Phase 4 must verify and record `im-not-ai` provenance before any source promotion. |

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

`THIRD_PARTY_NOTICES.md` is intentionally not generated in Phase 3 because there is no accepted imported payload yet.
