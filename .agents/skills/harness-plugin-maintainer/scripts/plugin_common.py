#!/usr/bin/env python3
"""Shared helpers for harness plugin build/validation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any


PLUGIN_ID = "harness-kit"
PLUGIN_VERSION = "0.5.0"
PLUGIN_ROOT_REL = Path("plugins") / PLUGIN_ID
MARKETPLACE_NAME = "hb9397"
PLUGIN_DISPLAY_NAME = "Harness Kit"
PLUGIN_DESCRIPTION = "Harness Kit plugin for Codex and Claude Code projects."
REPOSITORY_URL = "https://github.com/hb9397/harness-kit"
GENERATED_BY = "harness-plugin-maintainer"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def retry_filesystem(operation, *, attempts: int = 5, delay: float = 0.05):
    """Retry a filesystem call that Windows can fail transiently.

    A scanner or indexer holding a brief handle surfaces as OSError and makes an
    otherwise deterministic build fail at random. Retrying a bounded number of
    times keeps the verification suite trustworthy; a real error still raises
    once the attempts run out.
    """
    for attempt in range(attempts):
        try:
            return operation()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(delay * (2**attempt))
    raise AssertionError("unreachable")


def _write_atomic(path: Path, payload: str) -> None:
    """Write through a temporary file and replace the target in one step.

    Opening an existing file for truncating write is unreliable on Windows: a
    scanner or indexer holding a brief handle surfaces as OSError(EINVAL) and
    fails the build non-deterministically. os.replace is atomic and does not
    reopen the destination, so a reader either sees the old file or the new one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
        retry_filesystem(lambda: os.replace(tmp, path))
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def write_json(path: Path, value: Any) -> None:
    _write_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_text(path: Path, value: str) -> None:
    _write_atomic(path, value.rstrip() + "\n")


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
        retry_filesystem(lambda: shutil.rmtree(target))
    retry_filesystem(
        lambda: shutil.copytree(
            source,
            target,
            copy_function=shutil.copy2,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    )


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
        "source": REPOSITORY_URL,
    }
