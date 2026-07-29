# Plugin Release Checklist

Generated at: 2026-07-29T00:00:00+00:00

## Release candidate

- Plugin ID: `ai-agent-harness`
- Version: `0.1.0`
- Archive: `plugins/ai-agent-harness-0.1.0.zip`
- Archive SHA-256: `aafd14e888fc2d3efa9615df6b2f68eef913f3863bef3d0316566ebadb6765aa`
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
| Codex CLI | verified | `isolated marketplace add/install/list/uninstall/remove passed` |
| Codex Desktop/App | manual-required | `Interactive Plugins UI install/update requires app surface and cannot be completed from this shell.` |
| Claude Code CLI | verified | `isolated marketplace add/install/list/uninstall/remove passed` |
| Claude Desktop Code | manual-required | `Desktop Code local/SSH cache verification requires Claude Desktop app surface.` |

## Release gate

Status: **not release-ready**

Reason: isolated Codex and Claude Code CLI installation smokes passed. Codex Desktop/App and Claude Desktop Code installation, restart, and new-session discovery still require interactive manual evidence.

## Completed automated install checks

- Codex CLI: marketplace add/list/remove, plugin add/list/remove, installed cache 18 skills / 0 agents, `harness-setup` and `humanize-korean`.
- Claude Code CLI: strict plugin/marketplace validation, marketplace add/list/remove, plugin install/list/uninstall, installed cache 18 skills / 0 agents.

## Required before release-ready

- Codex app: install from Git-backed marketplace, restart/new task, verify marker/version, update to vN+1.
- Claude Desktop Code: local and SSH host cache/version verification, app restart/new session, unsupported cloud/WSL path documented.
- Legacy migration: run read-only inventory, backup/remove only with explicit approval, verify plugin single discovery.
