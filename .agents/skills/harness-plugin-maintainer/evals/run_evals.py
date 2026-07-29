#!/usr/bin/env python3
"""Build/validation evals for harness-plugin-maintainer."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "maintainer" / "skills" / "harness-plugin-maintainer"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_plugin  # noqa: E402


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
    )
    if completed.returncode != 0:
        raise AssertionError(f"command failed: {args}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return completed


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="harness-plugin-text-eval-") as tmp:
        payload_root = Path(tmp)
        extensionless = payload_root / "LICENSE"
        extensionless.write_bytes(b"line with protected spaces  \r\nsecond line\r\n")
        build_plugin.normalize_text_payload(payload_root)
        if extensionless.read_bytes() != b"line with protected spaces  \nsecond line\n":
            raise AssertionError("extensionless text LF normalization changed protected content")

    build = run([str(SCRIPTS / "build_plugin.py")])
    release = json.loads(build.stdout)
    if release["logical_user_skills"] != 18:
        raise AssertionError("logical user skill count mismatch")
    if release["codex_physical_skills"] != 18 or release["claude_physical_skills"] != 18:
        raise AssertionError("physical skill count mismatch")
    if release["codex_physical_agents"] != 0 or release["claude_physical_agents"] != 0:
        raise AssertionError("physical agent count mismatch")
    run([str(SCRIPTS / "validate_plugin.py")])
    run([str(SCRIPTS / "build_plugin.py"), "--check"])
    run([str(SCRIPTS / "validate_plugin.py")])

    with tempfile.TemporaryDirectory(prefix="harness-plugin-check-eval-") as tmp:
        fixture_root = Path(tmp)
        build_plugin.build(ROOT, output_root=fixture_root)
        drifted = fixture_root / "plugins" / "ai-agent-harness" / ".codex-plugin" / "plugin.json"
        drifted.write_text('{"name":"drift-must-survive-check"}\n', encoding="utf-8", newline="\n")
        before = drifted.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = build_plugin.check(ROOT, canonical_root=fixture_root)
        if result == 0:
            raise AssertionError("--check did not detect plugin tree drift")
        if drifted.read_bytes() != before:
            raise AssertionError("--check mutated the canonical plugin tree")

    run([str(SCRIPTS / "freeze_manager_inventory.py")])
    run([str(SCRIPTS / "smoke_cli_install.py"), "--self-test"])
    run([str(SCRIPTS / "verify_install_surfaces.py")])
    run([str(SCRIPTS / "run_release_regression.py")])
    print("harness-plugin-maintainer evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
