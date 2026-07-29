#!/usr/bin/env python3
"""Promote a staged candidate only after explicit approval gates."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

from portfolio_common import load_json, sha256_path, write_json


def arg_value(argv: list[str], name: str) -> str | None:
    return argv[argv.index(name) + 1] if name in argv else None


def main(argv: list[str]) -> int:
    root = Path(arg_value(argv, "--root") or Path(__file__).resolve().parents[4])
    candidate_id = arg_value(argv, "--candidate-id")
    general_approval = arg_value(argv, "--approval-id")
    asset_approval = arg_value(argv, "--asset-approval-id")
    destructive_approval = arg_value(argv, "--destructive-approval-id")
    dry_run = "--dry-run" in argv

    if not candidate_id:
        print("ERROR: --candidate-id is required", file=sys.stderr)
        return 1
    if not general_approval:
        print("ERROR: general approval is required", file=sys.stderr)
        return 2

    staging_root = root / "maintainer" / "upstreams" / "staging" / candidate_id
    candidate_file = staging_root / "candidate.json"
    stage_report_file = staging_root / "stage-report.json"
    if not candidate_file.exists() or not stage_report_file.exists():
        print("ERROR: staged candidate not found", file=sys.stderr)
        return 2

    candidate = load_json(candidate_file)
    stage_report = load_json(stage_report_file)
    if candidate.get("self_update_same_session"):
        print("ERROR: self-update same-session promote is blocked", file=sys.stderr)
        return 2

    destructive = candidate.get("destructive_changes", [])
    if stage_report.get("protected_asset_change") and not asset_approval:
        print("ERROR: protected asset approval is required", file=sys.stderr)
        return 2
    if destructive and not destructive_approval:
        print("ERROR: destructive approval is required", file=sys.stderr)
        return 2
    if candidate.get("license_change") == "block" or candidate.get("security_risk") == "block":
        print("ERROR: license/security risk blocks promotion", file=sys.stderr)
        return 2

    handoff = {
        "schema_version": "1.0.0",
        "candidate_id": candidate_id,
        "promoted_at": dt.date.today().isoformat(),
        "dry_run": dry_run,
        "approval_ids": {
            "general": general_approval,
            "asset_impact": asset_approval,
            "destructive": destructive_approval
        },
        "upstream": candidate.get("upstream") or candidate.get("promotion", {}),
        "source_hash": sha256_path(candidate_file),
        "runtime_hash": sha256_path(stage_report_file),
        "validation": candidate.get("validation", {}),
        "embedded_lock_changed": False,
        "plugin_release_created": False,
        "handoff_to": "harness-plugin-maintainer",
        "status": "promoted-dry-run" if dry_run else "promoted-handoff"
    }
    if not dry_run:
        write_json(root / "maintainer" / "upstreams" / "promotions" / f"{candidate_id}.json", handoff)
    print(json.dumps(handoff, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
