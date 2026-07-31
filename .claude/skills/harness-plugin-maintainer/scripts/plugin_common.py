#!/usr/bin/env python3
"""Shared helpers for harness plugin build/validation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any


PLUGIN_ID = "ai-agent-harness"
PLUGIN_VERSION = "0.2.0"
PLUGIN_ROOT_REL = Path("plugins") / PLUGIN_ID
GENERATED_BY = "harness-plugin-maintainer"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(value, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def tree_manifest(root: Path) -> list[dict[str, str]]:
    return [
        {
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "sha256": sha256_file(path),
        }
        for path in iter_files(root)
    ]


def copy_tree_clean(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, copy_function=shutil.copy2, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def remove_dir(path: Path) -> None:
    root = repo_root().resolve()
    resolved = path.resolve()
    if not str(resolved).startswith(str(root)):
        raise RuntimeError(f"refusing to remove outside repository: {path}")
    if path.exists():
        shutil.rmtree(path)


def ensure_no_symlink(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"symlink not allowed in plugin payload: {path}")


def semantic_version(version: str) -> bool:
    parts = version.split(".")
    return len(parts) == 3 and all(part.isdigit() for part in parts)


def user_skills(root: Path) -> list[str]:
    return sorted(path.name for path in (root / "skills").iterdir() if path.is_dir())


def generated_marker() -> dict[str, str]:
    return {
        "generated_by": GENERATED_BY,
        "source": "D:/Dev_Workspace/ai-agent-harness-docs",
    }
