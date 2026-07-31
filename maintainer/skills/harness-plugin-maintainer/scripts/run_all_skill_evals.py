#!/usr/bin/env python3
"""Run every canonical skill eval runner and enforce declared runner coverage."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
COVERAGE = ROOT / "maintainer" / "inventory" / "skill-eval-coverage.json"


def discover() -> list[Path]:
    runners: list[Path] = []
    for base in (ROOT / "skills", ROOT / "maintainer" / "skills"):
        if not base.is_dir():
            continue
        runners.extend(base.glob("*/evals/run_evals.py"))
    return sorted(runners, key=lambda path: path.relative_to(ROOT).as_posix())


def check_coverage(runners: list[Path]) -> tuple[list[str], list[str]]:
    """Compare discovered runners against the declared coverage manifest.

    Glob discovery alone cannot tell a deliberate omission from an accidental
    one, so a skill without a runner would disappear from the run while the log
    still claims everything passed. Returns (failures, reports).
    """
    if not COVERAGE.is_file():
        return ([f"missing eval coverage manifest: {COVERAGE.relative_to(ROOT).as_posix()}"], [])

    manifest = json.loads(COVERAGE.read_text(encoding="utf-8"))
    present = {(path.relative_to(ROOT).parts[0], path.relative_to(ROOT).parts[-3]) for path in runners}
    present_user = {name for root, name in present if root == "skills"}
    present_mgr = {name for root, name in present if root == "maintainer"}

    required = manifest.get("required", {})
    failures = [
        f"required eval runner missing: skills/{name}/evals/run_evals.py"
        for name in sorted(required.get("skills", []))
        if name not in present_user
    ]
    failures += [
        f"required eval runner missing: maintainer/skills/{name}/evals/run_evals.py"
        for name in sorted(required.get("maintainer_skills", []))
        if name not in present_mgr
    ]

    reports = []
    for entry in manifest.get("planned", []):
        name = entry.get("skill")
        root = entry.get("canonical_root", "skills")
        pool = present_user if root == "skills" else present_mgr
        if name not in pool:
            reports.append(f"planned runner not yet present: {root}/{name} (due in {entry.get('required_from_phase')})")

    declared = set(required.get("skills", [])) | {e["skill"] for e in manifest.get("planned", []) if e.get("canonical_root", "skills") == "skills"}
    declared |= set(manifest.get("not_required", {}).get("skills", []))
    for name in sorted(present_user - declared):
        reports.append(f"runner present but not listed in coverage manifest: skills/{name}")

    return (failures, reports)


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

    coverage_failures, coverage_reports = check_coverage(runners)
    for line in coverage_reports:
        print(f"NOTE: {line}", flush=True)
    if coverage_failures:
        print("ERROR: eval runner coverage failed:", file=sys.stderr)
        for line in coverage_failures:
            print(f"- {line}", file=sys.stderr)
        return 1

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
