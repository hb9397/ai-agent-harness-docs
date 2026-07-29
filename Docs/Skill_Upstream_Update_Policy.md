# Skill Upstream Update Policy

This repository separates reference-only learning from direct upstream import.

## Source Classes And Modes

| Mode | Meaning | Required handling |
|---|---|---|
| `native` | Locally authored, no active external source relationship | Normal repository review |
| `reference` | External source influenced concepts only | Record source URL and internal reflection point |
| `vendored` | Upstream file copied verbatim | License, NOTICE, hash, file map, approvals |
| `adapted` | Upstream content translated, modified, or restructured | Same as vendored plus local patch/treatment record |
| `unknown` | Evidence is insufficient | Do not import or release until resolved |

## State Model

| State | Meaning |
|---|---|
| `observed` | Latest release, tag, branch, or documentation state found during read-only review |
| `accepted` | Maintainer-approved upstream ref for possible integration |
| `embedded` | Source is present in canonical `skills/` |
| `packaged` | Source is present in a verified plugin artifact |
| `released` | Source is available to users through a released plugin version |

Reference sources use review dates and optional refs. Direct imports require immutable SHAs and file hashes before `accepted`.

## Approval Gates

| Gate | Requirement |
|---|---|
| G0 | Source registration and intended mode approval |
| G1 | Maintainer identity, release, tag, and full SHA verification |
| G2 | License and third-party content review |
| G3 | Scripts, hooks, MCP, network, binary, symlink, submodule, and permission review |
| G4 | Concept or file scope approval, including protected asset impact |
| G5 | Separate destructive approval for deletion, move, or replacement |
| G6 | Apply only in temporary staging before promotion |
| G7 | Codex, Claude, regression, and license validation |
| G8 | Promote to canonical source and hand off to plugin release flow |

The phrase “update to latest” is not approval for G4 or G5.

## Protected Assets

Protected paths include:

- `scripts/`
- `templates/`
- `assets/`
- `references/`
- `prompts/`
- `agents/`
- `commands/`
- `hooks/`
- `bin/`
- `example/`, `examples/`
- `evals/`, `tests/`
- plugin manifests and MCP/LSP config
- `LICENSE*`, `NOTICE*`

Adding or modifying protected assets requires an asset-impact record. Deleting, moving, or replacing protected assets requires a separate destructive approval.

## Maintainer Skill Boundary

`skill-portfolio-maintainer` owns upstream discovery, source classification, registry updates, and protected asset impact analysis.

`harness-plugin-maintainer` owns Codex and Claude plugin runtime generation, manifest generation, packaging, smoke tests, and release artifacts.

The two responsibilities must stay separate. A source can be classified without being packaged, and a plugin package must not include unaccepted or blocked upstream files.

## Rollback

Every direct import promotion must include the previous lock state, accepted ref, file map, generated hashes, and validation result. Rollback means restoring the previous lock and promoted files, then rerunning registry and plugin checks.
