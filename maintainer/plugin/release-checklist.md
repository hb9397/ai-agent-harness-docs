# Plugin Release Checklist

Generated at: 2026-07-29T00:00:00+00:00

## Release candidate

- Plugin ID: `ai-agent-harness`
- Version: `0.1.0`
- Archive: `plugins/ai-agent-harness-0.1.0.zip`
- Archive SHA-256: `8c576a8ed68bf0a3ea035f04afc6890fd3079b1ab5915e4aa8ff8b07e145623e`
- Codex physical skills: 18
- Codex physical agents: 0
- Claude physical skills: 18
- Claude physical agents: 0
- Markdown producer handoff count: 7

## Automated local checks

| Check | Result |
|---|---|
| Manifest name/version match | True |
| Archive checksum matches release metadata | True |
| Packaged adapted/vendored NOTICE-license-lock closure | True |
| Released state preserved | True |
| `humanize-korean` proposal-only | True |
| `humanize-korean` leaves original file unchanged | True |
| Protected tokens preserved | True |

## Surface evidence

| Surface | Status | Evidence |
|---|---|---|
| Codex CLI | install-smoke-verified | `isolated marketplace add/install/list/uninstall/remove and cache inspection passed; model invocation not tested` |
| Codex Desktop/App | manual-required | `Interactive Plugins UI install/update requires app surface and cannot be completed from this shell.` |
| Claude Code CLI | install-smoke-verified | `isolated marketplace add/install/list/uninstall/remove and cache inspection passed; model invocation not tested` |
| Claude Desktop Code | manual-required | `Desktop Code local/SSH cache verification requires Claude Desktop app surface.` |

## Release gate

Status: **not release-ready**

Reason: isolated Codex and Claude Code CLI installation smokes passed, but an installation/cache smoke is not a model invocation. Codex and Claude CLI/App all still require direct invocation, output, restart, and new-session manual evidence.

## Completed automated install checks

- Codex CLI install smoke: marketplace add/list/remove, plugin add/list/remove, installed cache 18 skills / 0 agents, including `harness-setup` and `humanize-korean` skill directories (not model invocation).
- Claude Code CLI install smoke: strict plugin/marketplace validation, marketplace add/list/remove, plugin install/list/uninstall, installed cache 18 skills / 0 agents (not model invocation).

## Required before release-ready

- Direct test record: copy `maintainer/plugin/manual-surface-test-template.md` to `maintainer/plugin/manual-evidence/YYYYMMDD/{surface}.md` and retain one fresh fixture per surface.
- All four surfaces: invoke both `harness-setup` and `humanize-korean`, verify proposal-only behavior, verify generated allowlist, verify no `.agents/skills`, `.claude/skills`, or `skills`, and preserve managed-block extensions.
- All four surfaces: reopen a new task/session and verify the same artifact fingerprint is not proposed again; retain the `.docs/.harness/humanize-handoffs.json` event.
- All four surfaces: cancel before a proposed write and verify original hashes and user sentinels are preserved.
- Codex app: install the candidate marketplace, restart/new task, verify marker/version, update to vN+1.
- Claude Desktop Code: local host cache/version verification and app restart/new session; repeat on SSH only when SSH is a declared support surface. Document unsupported cloud/WSL paths.
- Link reviewer-approved direct records from this checklist before changing any surface to `verified`.
- Legacy migration: run read-only inventory, backup/remove only with explicit approval, verify plugin single discovery.
