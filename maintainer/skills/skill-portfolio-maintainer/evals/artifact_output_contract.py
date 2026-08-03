#!/usr/bin/env python3
"""Eval entry point for the shared artifact-output contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
VALIDATOR = ROOT / "maintainer" / "skills" / "skill-portfolio-maintainer" / "scripts" / "validate_artifact_output_contract.py"


def main() -> int:
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    if completed.returncode != 0:
        print(completed.stdout, end="")
        print(completed.stderr, end="", file=sys.stderr)
        return completed.returncode
    print("artifact output contract evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
