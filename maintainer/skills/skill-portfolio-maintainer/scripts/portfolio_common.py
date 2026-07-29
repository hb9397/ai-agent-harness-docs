#!/usr/bin/env python3
"""Shared helpers for skill-portfolio-maintainer scripts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
RATE_LIMIT_STATUS = {403, 429}
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
PROTECTED_ASSET_DIRECTORIES = frozenset(
    {
        "agent",
        "agents",
        "asset",
        "assets",
        "bin",
        "command",
        "commands",
        "eval",
        "evals",
        "example",
        "examples",
        "hook",
        "hooks",
        "prompt",
        "prompts",
        "reference",
        "references",
        "script",
        "scripts",
        "template",
        "templates",
        "test",
        "tests",
    }
)
PROTECTED_ASSET_FILENAMES = frozenset({"template.md"})
PROTECTED_ASSET_FILE_PREFIXES = ("license", "notice")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def is_protected_asset_path(path: str) -> bool:
    """Classify protected assets by complete path segment or root-level filename."""
    if not isinstance(path, str) or not path.strip():
        return False
    parts = PurePosixPath(path.replace("\\", "/")).parts
    if not parts:
        return False
    directory_parts = {part.casefold() for part in parts[:-1]}
    basename = parts[-1].casefold()
    return (
        bool(directory_parts & PROTECTED_ASSET_DIRECTORIES)
        or basename in PROTECTED_ASSET_FILENAMES
        or basename.startswith(PROTECTED_ASSET_FILE_PREFIXES)
    )


def has_protected_asset_change(file_map: list[dict[str, Any]]) -> bool:
    return any(is_protected_asset_path(item.get("local_path") or "") for item in file_map)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(value, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_candidate_id(value: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value):
        raise ValueError(
            "candidate id must be 1-128 ASCII letters, digits, dots, underscores, or hyphens "
            "and must start with a letter or digit"
        )
    if value in {".", ".."} or value.rstrip(" .") != value:
        raise ValueError("candidate id contains an unsafe trailing or dot-only segment")
    if value.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
        raise ValueError("candidate id uses a reserved Windows device name")
    return value


def validate_relative_path(relative: str, *, allow_glob: bool = False) -> str:
    if not isinstance(relative, str) or not relative:
        raise ValueError("path must be a non-empty string")
    if "\x00" in relative:
        raise ValueError("path contains NUL")
    if not allow_glob and any(character in relative for character in "*?[]"):
        raise ValueError(f"glob syntax is not allowed here: {relative}")

    posix = PurePosixPath(relative.replace("\\", "/"))
    windows = PureWindowsPath(relative)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise ValueError(f"absolute path blocked: {relative}")
    if any(part in {"", ".", ".."} for part in posix.parts):
        raise ValueError(f"dot segment or traversal blocked: {relative}")
    return relative


def safe_join(root: Path, relative: str, *, reject_symlinks: bool = False) -> Path:
    validate_relative_path(relative)
    root_resolved = root.resolve()
    unresolved = root_resolved / Path(relative)
    if reject_symlinks:
        current = root_resolved
        for part in Path(relative).parts:
            current = current / part
            if current.exists() and current.is_symlink():
                raise ValueError(f"symlink path blocked: {relative}")

    path = unresolved.resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError:
        raise ValueError(f"path traversal blocked: {relative}")
    if reject_symlinks and path.exists() and path.is_symlink():
        raise ValueError(f"symlink path blocked: {relative}")
    return path


def hash_tree(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"tree path does not exist: {path}")
    if path.is_symlink():
        raise ValueError(f"symlink tree blocked: {path}")

    if path.is_file():
        files = [path]
        base = path.parent
    elif path.is_dir():
        entries = sorted(path.rglob("*"), key=lambda item: item.relative_to(path).as_posix())
        for entry in entries:
            relative = entry.relative_to(path).as_posix()
            if entry.is_symlink():
                raise ValueError(f"symlink entry blocked: {relative}")
            if ".git" in entry.relative_to(path).parts:
                raise ValueError(f"git metadata or submodule entry blocked: {relative}")
            if entry.name == ".gitmodules":
                raise ValueError(f"git submodule declaration blocked: {relative}")
        files = [entry for entry in entries if entry.is_file()]
        base = path
    else:
        raise ValueError(f"unsupported tree entry: {path}")
    if not files:
        raise ValueError(f"tree contains no files: {path}")

    digest = hashlib.sha256()
    digest.update(b"skill-portfolio-tree-v1\0")
    byte_count = 0
    for file_path in files:
        relative = file_path.relative_to(base).as_posix()
        data = file_path.read_bytes()
        if b"\x00" in data[:8192]:
            raise ValueError(f"binary file blocked: {relative}")
        if data.startswith(b"version https://git-lfs.github.com/spec/"):
            raise ValueError(f"Git LFS pointer blocked: {relative}")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"non-UTF-8 or binary file blocked: {relative}") from exc
        encoded_path = relative.encode("utf-8")
        digest.update(len(encoded_path).to_bytes(8, "big"))
        digest.update(encoded_path)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
        byte_count += len(data)

    return {
        "algorithm": "sha256-tree-v1",
        "sha256": digest.hexdigest(),
        "file_count": len(files),
        "byte_count": byte_count,
    }


def mask_token(value: str) -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        value = value.replace(token, "***")
    return value


def http_json(url: str, timeout: int = 15, retries: int = 2) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-agent-harness-skill-portfolio-maintainer",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_error: str | None = None
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason}"
            if exc.code not in RATE_LIMIT_STATUS and attempt >= retries:
                break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        if attempt < retries:
            time.sleep(min(2 ** attempt, 4))
    raise RuntimeError(mask_token(last_error or "unknown http error"))


def parse_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=repo_root())
    return parser


def stable_release(releases: list[dict[str, Any]], tag_pattern: str | None) -> dict[str, Any] | None:
    pattern = re.compile("^" + (tag_pattern or ".*").replace("*", ".*") + "$")
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        tag = release.get("tag_name") or ""
        if pattern.match(tag):
            return release
    return None


def error(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1
