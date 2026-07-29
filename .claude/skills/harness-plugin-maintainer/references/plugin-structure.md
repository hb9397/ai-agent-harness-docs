# ai-agent-harness Plugin Structure

The generated plugin is a one-root, dual-manifest bundle. Marketplace catalogs
live at the management repository root because Codex and Claude resolve local
plugin sources relative to the marketplace root.

## Repository marketplace catalogs

- Codex: `.agents/plugins/marketplace.json`
- Claude: `.claude-plugin/marketplace.json`
- local source: `./plugins/ai-agent-harness`

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
- physical skill count: 18
- canonical document refinement skill: `humanize-korean`
- agents: none

## Direct import closure

Every runtime direct import must be closed by:

- `licenses/{upstream-id}-LICENSE`
- `THIRD_PARTY_NOTICES.md`
- `UPSTREAMS.lock.json`
- source registry file-map

## Generated metadata

Official plugin manifests and marketplace catalogs contain only recognized
schema fields. Harness-owned metadata such as `CAPABILITIES.json`,
`UPSTREAMS.lock.json`, `MANIFEST.sha256.json`, and `release.json` carries the
`generated_by` marker. Runtime skill files are copied from source; build-time
normalization changes line endings only and preserves other text.

## Isolated CLI install smoke

Run `scripts/smoke_cli_install.py` only after the deterministic build and local
validator pass. It uses temporary platform configuration directories and must
verify, for both Codex and Claude Code:

1. repo-root marketplace registration,
2. `ai-agent-harness@ai-agent-harness` installation,
3. enabled plugin listing,
4. installed runtime equality with 18 logical skills and 0 agents,
5. presence of `harness-setup` and `humanize-korean`,
6. absence of nested marketplace catalogs,
7. uninstall and marketplace cleanup.

Desktop/App installation remains a manual release gate because a headless CLI
smoke cannot prove UI discovery, restart behavior, or a newly opened task.
