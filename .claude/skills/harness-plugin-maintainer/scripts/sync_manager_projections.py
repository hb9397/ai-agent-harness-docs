#!/usr/bin/env python3
"""Sync repo-local maintainer skill projections.

The maintainer source of truth is maintainer/skills. The projections under
.agents/skills and .claude/skills are generated copies for local agent
discovery in this repository only.
"""

from __future__ import annotations

import argparse
import filecmp
import hashlib
import shutil
import sys
from pathlib import Path


MANAGER_SKILLS = (
    "custom-skill-design",
    "skill-portfolio-maintainer",
    "harness-plugin-maintainer",
)
PROJECTION_ROOTS = (
    Path(".agents") / "skills",
    Path(".claude") / "skills",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def is_generated_cache(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix == ".pyc"


def iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and not is_generated_cache(path))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relative_file_map(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)).replace("\\", "/"): digest(path) for path in iter_files(root)}


def expected_projection(source_root: Path) -> dict[str, str]:
    expected: dict[str, str] = {}
    for skill in MANAGER_SKILLS:
        skill_root = source_root / skill
        if not skill_root.is_dir():
            raise FileNotFoundError(f"Missing maintainer skill: {skill_root}")
        for rel, sha in relative_file_map(skill_root).items():
            expected[f"{skill}/{rel}"] = sha
    return expected


def check_projection(source_root: Path, projection_root: Path) -> list[str]:
    expected = expected_projection(source_root)
    actual = relative_file_map(projection_root) if projection_root.exists() else {}
    messages: list[str] = []

    for rel in sorted(expected.keys() - actual.keys()):
        messages.append(f"missing: {projection_root / rel}")
    for rel in sorted(actual.keys() - expected.keys()):
        messages.append(f"unexpected: {projection_root / rel}")
    for rel in sorted(expected.keys() & actual.keys()):
        if expected[rel] != actual[rel]:
            messages.append(f"changed: {projection_root / rel}")
    return messages


def copy_skill(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, copy_function=shutil.copy2, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def apply_projection(source_root: Path, projection_root: Path) -> None:
    projection_root.mkdir(parents=True, exist_ok=True)
    for child in projection_root.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for skill in MANAGER_SKILLS:
        copy_skill(source_root / skill, projection_root / skill)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report drift without modifying projections")
    args = parser.parse_args(argv)

    root = repo_root()
    source_root = root / "maintainer" / "skills"
    projection_roots = [root / item for item in PROJECTION_ROOTS]

    if args.check:
        messages: list[str] = []
        for projection_root in projection_roots:
            messages.extend(check_projection(source_root, projection_root))
        if messages:
            print("\n".join(messages))
            return 1
        print("manager projections are in sync")
        return 0

    for projection_root in projection_roots:
        apply_projection(source_root, projection_root)
    for projection_root in projection_roots:
        comparison = check_projection(source_root, projection_root)
        if comparison:
            print("\n".join(comparison), file=sys.stderr)
            return 1
    print("manager projections updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
