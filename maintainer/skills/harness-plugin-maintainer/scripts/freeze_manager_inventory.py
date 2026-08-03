#!/usr/bin/env python3
"""Freeze maintainer skill file inventory and hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from plugin_common import GENERATED_BY, repo_root, write_json


MANAGER_SKILLS = [
    "custom-skill-design",
    "harness-plugin-maintainer",
    "skill-portfolio-maintainer",
]


def portable_sha256(path: Path) -> str:
    """Hash UTF-8 text with LF newlines and binary files byte-for-byte."""
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        normalized = data
    else:
        normalized = text.replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def iter_files(root: Path) -> list[Path]:
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    ]
    return sorted(
        files,
        key=lambda path: (
            path.relative_to(root).as_posix().casefold(),
            path.relative_to(root).as_posix(),
        ),
    )


def build_inventory(root: Path) -> dict:
    source_root = root / "maintainer" / "skills"
    inventory = []
    for skill in MANAGER_SKILLS:
        skill_root = source_root / skill
        files = []
        for path in iter_files(skill_root):
            files.append({
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "sha256": portable_sha256(path),
            })
        inventory.append({
            "skill": skill,
            "file_count": len(files),
            "files": files,
        })
    out = {
        "schema_version": "1.0.0",
        "generated_by": GENERATED_BY,
        "generated_at": "2026-08-03",
        "scope": "Phase 1 manager skill freeze after commit-workflow and upstream governance validation updates",
        "manager_skill_count": len(MANAGER_SKILLS),
        "skills": inventory,
    }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the portable inventory with the tracked freeze without writing",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    out = build_inventory(root)
    target = root / "maintainer" / "plugin" / "manager-skill-freeze.json"
    if args.check:
        expected = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
        if not target.is_file() or target.read_text(encoding="utf-8") != expected:
            print(
                "ERROR: manager skill freeze is stale; run freeze_manager_inventory.py",
                file=sys.stderr,
            )
            return 1
        print("manager skill freeze check passed")
        return 0

    write_json(target, out)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
