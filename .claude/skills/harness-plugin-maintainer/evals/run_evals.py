#!/usr/bin/env python3
"""Build/validation evals for harness-plugin-maintainer."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "maintainer" / "skills" / "harness-plugin-maintainer"
SCRIPTS = SKILL / "scripts"


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
    build = run([str(SCRIPTS / "build_plugin.py")])
    release = json.loads(build.stdout)
    if release["logical_user_skills"] != 18:
        raise AssertionError("logical user skill count mismatch")
    if release["codex_physical_skills"] != 18 or release["claude_physical_skills"] != 20:
        raise AssertionError("physical skill count mismatch")
    run([str(SCRIPTS / "validate_plugin.py")])
    run([str(SCRIPTS / "build_plugin.py"), "--check"])
    run([str(SCRIPTS / "validate_plugin.py")])
    run([str(SCRIPTS / "freeze_manager_inventory.py")])
    run([str(SCRIPTS / "verify_install_surfaces.py")])
    print("harness-plugin-maintainer evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
