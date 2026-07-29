# Phase 10 Release Regression

Generated at: 2026-07-29T00:00:00+00:00

## Summary

- Overall status: `not-release-ready`
- Plugin: `ai-agent-harness` `0.1.0`
- Archive SHA-256: `10233c461833265a4d061d218e7d1800102569c27c2a927222a2dd5151f8dd7a`
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

This candidate remains `not-release-ready` because actual Codex CLI/App and Claude Code CLI/Desktop install evidence is incomplete. The script does not update `released` lock state and does not create tags or releases.

## Rollback

Rollback is validated in isolated fixtures by restoring the previous released lock and plugin version. The live workspace is read-only for destructive scenarios.
