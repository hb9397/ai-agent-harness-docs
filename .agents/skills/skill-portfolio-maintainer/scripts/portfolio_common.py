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
from pathlib import Path
from typing import Any


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RATE_LIMIT_STATUS = {403, 429}


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


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_join(root: Path, relative: str) -> Path:
    if "\x00" in relative:
        raise ValueError("path contains NUL")
    path = (root / relative).resolve()
    root_resolved = root.resolve()
    if not str(path).startswith(str(root_resolved)):
        raise ValueError(f"path traversal blocked: {relative}")
    return path


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
