#!/usr/bin/env python3
"""Freeze maintainer skill file inventory and hashes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from plugin_common import GENERATED_BY, repo_root, sha256_file, write_json


MANAGER_SKILLS = [
    "custom-skill-design",
    "harness-plugin-maintainer",
    "skill-portfolio-maintainer",
]


def iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc")


def main() -> int:
    root = repo_root()
    source_root = root / "maintainer" / "skills"
    inventory = []
    for skill in MANAGER_SKILLS:
        skill_root = source_root / skill
        files = []
        for path in iter_files(skill_root):
            files.append({
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "sha256": sha256_file(path),
            })
        inventory.append({
            "skill": skill,
            "file_count": len(files),
            "files": files,
        })
    out = {
        "schema_version": "1.0.0",
        "generated_by": GENERATED_BY,
        "generated_at": "2026-07-29",
        "scope": "Phase 6 manager skill freeze after skill-portfolio-maintainer and harness-plugin-maintainer implementation",
        "manager_skill_count": len(MANAGER_SKILLS),
        "skills": inventory,
    }
    write_json(root / "maintainer" / "plugin" / "manager-skill-freeze.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
