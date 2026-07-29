# Plugin Release Checklist

Generated at: 2026-07-29T00:00:00+00:00

## Release candidate

- Plugin ID: `ai-agent-harness`
- Version: `0.1.0`
- Archive: `plugins/ai-agent-harness-0.1.0.zip`
- Archive SHA-256: `10233c461833265a4d061d218e7d1800102569c27c2a927222a2dd5151f8dd7a`
- Codex physical skills: 18
- Claude physical skills: 20
- Claude physical agents: 3
- Markdown producer handoff count: 7

## Automated local checks

| Check | Result |
|---|---|
| Manifest ID/version match | True |
| Archive checksum matches release metadata | True |
| `im-not-ai` packaged lock exists | True |
| Released state preserved | True |
| `humanize-korean` proposal-only | True |
| `humanize-korean` leaves original file unchanged | True |
| Protected tokens preserved | True |

## Surface evidence

| Surface | Status | Evidence |
|---|---|---|
| Codex CLI | blocked | `[WinError 5] 액세스가 거부되었습니다` |
| Codex Desktop/App | manual-required | `Interactive Plugins UI install/update requires app surface and cannot be completed from this shell.` |
| Claude Code CLI | blocked | `missing` |
| Claude Desktop Code | manual-required | `Desktop Code local/SSH cache verification requires Claude Desktop app surface.` |

## Release gate

Status: **not release-ready**

Reason: Phase 7 requires evidence from four core surfaces: Codex CLI, Codex app, Claude Code CLI, and Claude Desktop Code. This host could not execute Codex CLI because WindowsApps denied process start, and Claude CLI is not installed. Desktop/app installation and update checks require interactive app surfaces.

## Required before release-ready

- Codex CLI: marketplace add/list/upgrade/remove, plugin add/list/remove, install vN, verify `harness-setup` and `humanize-korean`, update to vN+1 or reinstall stale cache.
- Codex app: install from Git-backed marketplace, restart/new task, verify marker/version, update to vN+1.
- Claude Code CLI: marketplace add/update, plugin install/list/update/uninstall, `/reload-plugins`, verify `harness-setup` and `humanize-korean`.
- Claude Desktop Code: local and SSH host cache/version verification, app restart/new session, unsupported cloud/WSL path documented.
- Legacy migration: run read-only inventory, backup/remove only with explicit approval, verify plugin single discovery.
