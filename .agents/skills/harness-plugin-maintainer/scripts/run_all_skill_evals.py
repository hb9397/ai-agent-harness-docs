#!/usr/bin/env python3
"""Run every canonical skill eval runner without relying on a hand-maintained list."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def discover() -> list[Path]:
    runners: list[Path] = []
    for base in (ROOT / "skills", ROOT / "maintainer" / "skills"):
        if not base.is_dir():
            continue
        runners.extend(base.glob("*/evals/run_evals.py"))
    return sorted(runners, key=lambda path: path.relative_to(ROOT).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--list",
        action="store_true",
        help="print discovered canonical eval runners without executing them",
    )
    args = parser.parse_args()

    runners = discover()
    if not runners:
        print("ERROR: no canonical skill eval runners found", file=sys.stderr)
        return 1

    if args.list:
        for runner in runners:
            print(runner.relative_to(ROOT).as_posix())
        return 0

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    failures: list[str] = []
    for runner in runners:
        relative = runner.relative_to(ROOT).as_posix()
        print(f"==> {relative}", flush=True)
        completed = subprocess.run(
            [sys.executable, str(runner)],
            cwd=ROOT,
            env=env,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            failures.append(relative)

    if failures:
        print("ERROR: failed eval runners:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"all canonical skill evals passed ({len(runners)} runners)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
