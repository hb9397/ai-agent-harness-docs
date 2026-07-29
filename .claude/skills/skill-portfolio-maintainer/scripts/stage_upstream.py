#!/usr/bin/env python3
"""Stage an upstream candidate without touching canonical skill sources."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

from portfolio_common import (
    has_protected_asset_change,
    hash_tree,
    load_json,
    safe_join,
    sha256_path,
    validate_candidate_id,
    validate_relative_path,
    write_json,
)


def has_protected_change(file_map: list[dict]) -> bool:
    return has_protected_asset_change(file_map)


def tree_path(candidate: dict, name: str) -> str | None:
    trees = candidate.get("trees") or {}
    if not isinstance(trees, dict):
        return None
    return trees.get(name) or candidate.get(f"{name}_tree")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage one reviewed upstream candidate without changing canonical skills or plugin runtime.",
        epilog="Candidate JSON must declare repository-relative trees.source and trees.runtime paths to actual text trees.",
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4], help="harness repository root")
    parser.add_argument("--candidate", type=Path, required=True, help="reviewed candidate JSON file")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    candidate_file = args.candidate
    try:
        candidate = load_json(candidate_file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read candidate JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(candidate, dict):
        print("ERROR: candidate JSON must be an object", file=sys.stderr)
        return 2
    promotion = candidate.get("promotion") if isinstance(candidate.get("promotion"), dict) else {}
    candidate_id = candidate.get("id") or promotion.get("target_skill") or candidate_file.stem

    try:
        validate_candidate_id(candidate_id)
    except ValueError as exc:
        print(f"ERROR: unsafe candidate id: {exc}", file=sys.stderr)
        return 2

    if candidate.get("self_update_same_session"):
        print("ERROR: self-update same-session stage/promote is blocked", file=sys.stderr)
        return 2

    file_map = candidate.get("file_map") or promotion.get("file_map") or []
    destructive_changes = candidate.get("destructive_changes") or []
    if not isinstance(file_map, list) or any(not isinstance(item, dict) for item in file_map):
        print("ERROR: candidate file_map must be an array of objects", file=sys.stderr)
        return 2
    if not isinstance(destructive_changes, list) or any(not isinstance(item, dict) for item in destructive_changes):
        print("ERROR: candidate destructive_changes must be an array of objects", file=sys.stderr)
        return 2
    try:
        for item in file_map:
            for key in ("local_path", "upstream_path"):
                value = item.get(key)
                if value:
                    validate_relative_path(value, allow_glob=True)
        for item in destructive_changes:
            if item.get("path"):
                validate_relative_path(item["path"], allow_glob=True)
    except ValueError as exc:
        print(f"ERROR: path safety check failed: {exc}", file=sys.stderr)
        return 2

    source_relative = tree_path(candidate, "source")
    runtime_relative = tree_path(candidate, "runtime")
    if not source_relative or not runtime_relative:
        print(
            "ERROR: candidate must declare actual trees.source and trees.runtime repository-relative paths",
            file=sys.stderr,
        )
        return 2

    try:
        source_path = safe_join(root, source_relative, reject_symlinks=True)
        runtime_path = safe_join(root, runtime_relative, reject_symlinks=True)
        source_manifest = hash_tree(source_path)
        runtime_manifest = hash_tree(runtime_path)
        staging_base = safe_join(root, "maintainer/upstreams/staging", reject_symlinks=True)
        staging_root = safe_join(staging_base, candidate_id, reject_symlinks=True)
    except ValueError as exc:
        print(f"ERROR: candidate tree safety check failed: {exc}", file=sys.stderr)
        return 2

    staging_root.mkdir(parents=True, exist_ok=True)
    try:
        staged_candidate = safe_join(staging_root, "candidate.json", reject_symlinks=True)
        stage_report_path = safe_join(staging_root, "stage-report.json", reject_symlinks=True)
    except ValueError as exc:
        print(f"ERROR: staging output path safety check failed: {exc}", file=sys.stderr)
        return 2
    shutil.copyfile(candidate_file, staged_candidate)
    report = {
        "schema_version": "1.0.0",
        "candidate_id": candidate_id,
        "staged_at": dt.date.today().isoformat(),
        "staging_dir": str(staging_root.relative_to(root)).replace("\\", "/"),
        "canonical_source_changed": False,
        "embedded_lock_changed": False,
        "protected_asset_change": has_protected_change(file_map),
        "candidate_sha256": sha256_path(staged_candidate),
        "source_tree": {
            "path": source_relative.replace("\\", "/"),
            **source_manifest,
        },
        "runtime_tree": {
            "path": runtime_relative.replace("\\", "/"),
            **runtime_manifest,
        },
        "status": "staged"
    }
    write_json(stage_report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
