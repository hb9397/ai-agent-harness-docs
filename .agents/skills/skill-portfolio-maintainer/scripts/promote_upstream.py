#!/usr/bin/env python3
"""Promote a staged candidate only after explicit approval gates."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from portfolio_common import (
    has_protected_asset_change,
    hash_tree,
    load_json,
    safe_join,
    sha256_path,
    validate_candidate_id,
    write_json,
)


def has_protected_change(file_map: list[dict]) -> bool:
    return has_protected_asset_change(file_map)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create one approval-gated promotion handoff from an unchanged staged candidate.",
        epilog="The staged candidate must retain its candidate hash and actual source/runtime tree hashes.",
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4], help="harness repository root")
    parser.add_argument("--candidate-id", required=True, help="staged candidate identifier")
    parser.add_argument("--approval-id", required=True, help="general maintainer approval identifier")
    parser.add_argument("--asset-approval-id", help="approval for protected asset additions or modifications")
    parser.add_argument("--destructive-approval-id", help="approval for deletions, moves, or replacements")
    parser.add_argument("--dry-run", action="store_true", help="validate and print the handoff without writing it")
    return parser


def verify_tree(root: Path, recorded: dict, label: str) -> dict:
    relative = recorded.get("path")
    if not relative:
        raise ValueError(f"stage report missing {label}_tree.path")
    current = hash_tree(safe_join(root, relative, reject_symlinks=True))
    for key in ("algorithm", "sha256", "file_count", "byte_count"):
        if current.get(key) != recorded.get(key):
            raise ValueError(f"{label} tree changed after staging ({key} mismatch)")
    return current


def candidate_tree_path(candidate: dict, name: str) -> str | None:
    trees = candidate.get("trees") or {}
    if not isinstance(trees, dict):
        return None
    return trees.get(name) or candidate.get(f"{name}_tree")


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    candidate_id = args.candidate_id
    try:
        validate_candidate_id(candidate_id)
        staging_base = safe_join(root, "maintainer/upstreams/staging", reject_symlinks=True)
        staging_root = safe_join(staging_base, candidate_id, reject_symlinks=True)
    except ValueError as exc:
        print(f"ERROR: unsafe candidate id or staging path: {exc}", file=sys.stderr)
        return 2

    try:
        candidate_file = safe_join(staging_root, "candidate.json", reject_symlinks=True)
        stage_report_file = safe_join(staging_root, "stage-report.json", reject_symlinks=True)
    except ValueError as exc:
        print(f"ERROR: staged file safety check failed: {exc}", file=sys.stderr)
        return 2
    if not candidate_file.exists() or not stage_report_file.exists():
        print("ERROR: staged candidate not found", file=sys.stderr)
        return 2

    try:
        candidate = load_json(candidate_file)
        stage_report = load_json(stage_report_file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read staged JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(candidate, dict) or not isinstance(stage_report, dict):
        print("ERROR: staged candidate and report must be JSON objects", file=sys.stderr)
        return 2
    promotion = candidate.get("promotion") if isinstance(candidate.get("promotion"), dict) else {}
    staged_id = candidate.get("id") or promotion.get("target_skill") or candidate_file.stem
    if staged_id != candidate_id or stage_report.get("candidate_id") != candidate_id:
        print("ERROR: staged candidate id does not match --candidate-id", file=sys.stderr)
        return 2
    if stage_report.get("candidate_sha256") != sha256_path(candidate_file):
        print("ERROR: staged candidate changed after staging", file=sys.stderr)
        return 2
    for tree_name in ("source", "runtime"):
        candidate_path = candidate_tree_path(candidate, tree_name)
        recorded_path = (stage_report.get(f"{tree_name}_tree") or {}).get("path")
        if not candidate_path or candidate_path.replace("\\", "/") != recorded_path:
            print(f"ERROR: staged {tree_name} tree path does not match candidate", file=sys.stderr)
            return 2
    if candidate.get("self_update_same_session"):
        print("ERROR: self-update same-session promote is blocked", file=sys.stderr)
        return 2

    destructive = candidate.get("destructive_changes", [])
    protected_asset_change = has_protected_change(
        candidate.get("file_map") or promotion.get("file_map") or []
    )
    if protected_asset_change and not args.asset_approval_id:
        print("ERROR: protected asset approval is required", file=sys.stderr)
        return 2
    if destructive and not args.destructive_approval_id:
        print("ERROR: destructive approval is required", file=sys.stderr)
        return 2
    if candidate.get("license_change") == "block" or candidate.get("security_risk") == "block":
        print("ERROR: license/security risk blocks promotion", file=sys.stderr)
        return 2
    if not args.approval_id.strip():
        print("ERROR: general approval is required", file=sys.stderr)
        return 2
    if args.asset_approval_id is not None and not args.asset_approval_id.strip():
        print("ERROR: protected asset approval id must not be blank", file=sys.stderr)
        return 2
    if args.destructive_approval_id is not None and not args.destructive_approval_id.strip():
        print("ERROR: destructive approval id must not be blank", file=sys.stderr)
        return 2

    try:
        source_manifest = verify_tree(root, stage_report.get("source_tree") or {}, "source")
        runtime_manifest = verify_tree(root, stage_report.get("runtime_tree") or {}, "runtime")
    except ValueError as exc:
        print(f"ERROR: staged tree verification failed: {exc}", file=sys.stderr)
        return 2

    handoff = {
        "schema_version": "1.0.0",
        "candidate_id": candidate_id,
        "promoted_at": dt.date.today().isoformat(),
        "dry_run": args.dry_run,
        "approval_ids": {
            "general": args.approval_id,
            "asset_impact": args.asset_approval_id,
            "destructive": args.destructive_approval_id
        },
        "upstream": candidate.get("upstream") or promotion,
        "source_hash": source_manifest["sha256"],
        "runtime_hash": runtime_manifest["sha256"],
        "source_tree": {
            "path": stage_report["source_tree"]["path"],
            **source_manifest,
        },
        "runtime_tree": {
            "path": stage_report["runtime_tree"]["path"],
            **runtime_manifest,
        },
        "validation": candidate.get("validation", {}),
        "embedded_lock_changed": False,
        "plugin_release_created": False,
        "handoff_to": "harness-plugin-maintainer",
        "status": "promoted-dry-run" if args.dry_run else "promoted-handoff"
    }
    if not args.dry_run:
        promotions = safe_join(root, "maintainer/upstreams/promotions", reject_symlinks=True)
        write_json(safe_join(promotions, f"{candidate_id}.json", reject_symlinks=True), handoff)
    print(json.dumps(handoff, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
