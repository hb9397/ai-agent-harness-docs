# Harness Plugin Maintainer Fixtures

Phase 6 evals build from the live repository source because the plugin payload is
the source-of-truth user skill set. An isolated output-root fixture injects
plugin drift and verifies that `build_plugin.py --check` detects it without
rewriting the drifted canonical file. `validate_plugin.py` covers manifest,
repo-root marketplace, LF normalization, archive mode, checksum, and packaged
upstream closure failures.

`smoke_cli_install.py --self-test` validates both generated runtime payloads
without network access. CI separately runs the full isolated Codex and Claude
marketplace add/install/list/remove lifecycle with the official CLIs.
