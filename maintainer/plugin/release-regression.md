# Phase 10 Release Regression

Generated at: 2026-07-29T00:00:00+00:00

## Summary

- Overall status: `not-release-ready`
- Plugin: `ai-agent-harness` `0.1.0`
- Archive SHA-256: `aafd14e888fc2d3efa9615df6b2f68eef913f3863bef3d0316566ebadb6765aa`
- Release gate: `not-release-ready`
- Push/tag/release created: `false`

## Checks

| Check | Result |
|---|---|
| `source_projection_integrity` | True |
| `reproducible_build` | True |
| `static_local_links` | True |
| `upstream_3mode_e2e` | True |
| `user_e2e` | True |
| `failure_rollback` | True |
| `release_gate` | True |

## Release decision

This candidate remains `not-release-ready` because interactive evidence is still required for `codex-desktop-app, claude-desktop-code`. The isolated Codex and Claude CLI install smokes passed. The script does not update `released` lock state and does not create tags or releases.

## Rollback

Rollback is validated in isolated fixtures by restoring the previous released lock and plugin version. The live workspace is read-only for destructive scenarios.
