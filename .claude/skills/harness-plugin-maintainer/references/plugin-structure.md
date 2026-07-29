# ai-agent-harness Plugin Structure

The generated plugin is a one-root, dual-manifest bundle.

## Root

`plugins/ai-agent-harness/`

## Codex runtime

- manifest: `.codex-plugin/plugin.json`
- skills: `runtime/codex/skills`
- physical skill count: 18
- agents: none

## Claude runtime

- manifest: `.claude-plugin/plugin.json`
- skills: `runtime/claude/skills`
- physical skill count: 20
  - 18 logical user skills
  - `humanize`
  - `humanize-redo`
- agents: `runtime/claude/agents`
- physical agent count: 3, from `maintainer/plugin/runtime-allowlist.json`

## Direct import closure

Every runtime direct import must be closed by:

- `licenses/{upstream-id}-LICENSE`
- `THIRD_PARTY_NOTICES.md`
- `UPSTREAMS.lock.json`
- source registry file-map

## Generated marker

Every generated manifest and metadata file includes `generated_by: harness-plugin-maintainer`. Runtime skill files are copied from source and are not rewritten except Claude alias wrappers.
