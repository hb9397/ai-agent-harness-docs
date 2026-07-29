#!/usr/bin/env python3
"""Create rollback report for a promoted upstream candidate."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from portfolio_common import load_json, safe_join, validate_candidate_id, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a non-destructive rollback report for one promotion handoff."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4], help="harness repository root")
    parser.add_argument("--candidate-id", required=True, help="promoted candidate identifier")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    candidate_id = args.candidate_id
    try:
        validate_candidate_id(candidate_id)
        promotions = safe_join(root, "maintainer/upstreams/promotions", reject_symlinks=True)
        promotion_file = safe_join(promotions, f"{candidate_id}.json", reject_symlinks=True)
    except ValueError as exc:
        print(f"ERROR: unsafe candidate id or promotion path: {exc}", file=sys.stderr)
        return 2

    if not promotion_file.exists():
        print("ERROR: promotion handoff not found", file=sys.stderr)
        return 2

    try:
        promotion = load_json(promotion_file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read promotion handoff: {exc}", file=sys.stderr)
        return 2
    if not isinstance(promotion, dict):
        print("ERROR: promotion handoff must be a JSON object", file=sys.stderr)
        return 2
    report = {
        "schema_version": "1.0.0",
        "candidate_id": candidate_id,
        "created_at": dt.date.today().isoformat(),
        "source_promotion": str(promotion_file.relative_to(root)).replace("\\", "/"),
        "automatic_destructive_action": False,
        "rollback_basis": promotion.get("previous_lock") or "current lock state; no previous lock snapshot recorded",
        "required_manual_steps": [
            "Review promotion handoff and current lock state.",
            "Revert source changes with normal git review if needed.",
            "Regenerate plugin runtime in Phase 6 tooling if the promoted source was packaged."
        ]
    }
    rollback_dir = safe_join(root, "maintainer/upstreams/rollback", reject_symlinks=True)
    out = safe_join(rollback_dir, f"{candidate_id}.json", reject_symlinks=True)
    write_json(out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
