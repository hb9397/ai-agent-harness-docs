# Phase 10 Release Regression

Generated at: 2026-07-29T00:00:00+00:00

## Summary

- Overall status: `not-release-ready`
- Plugin: `ai-agent-harness` `0.1.0`
- Archive SHA-256: `8c576a8ed68bf0a3ea035f04afc6890fd3079b1ab5915e4aa8ff8b07e145623e`
- Release gate: `not-release-ready`
- Push/tag/release created: `false`

## Checks

| Check | Result |
|---|---|
| `source_projection_integrity` | True |
| `reproducible_build` | True |
| `static_local_links` | True |
| `upstream_modes_fixture` | True |
| `user_contract_fixture` | True |
| `failure_rollback` | True |
| `release_gate` | True |

## Release decision

This candidate remains `not-release-ready` because interactive evidence is still required for `codex-cli, codex-desktop-app, claude-code-cli, claude-desktop-code`. The isolated Codex and Claude CLI install smokes passed. The script does not update `released` lock state and does not create tags or releases.

## Rollback

Rollback is validated in isolated fixtures by restoring the previous released lock and plugin version. The live workspace is read-only for destructive scenarios.
