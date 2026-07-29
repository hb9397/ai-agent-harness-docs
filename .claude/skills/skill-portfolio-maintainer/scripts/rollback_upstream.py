#!/usr/bin/env python3
"""Create rollback report for a promoted upstream candidate."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

from portfolio_common import load_json, write_json


def main(argv: list[str]) -> int:
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path(__file__).resolve().parents[4]
    candidate_id = argv[argv.index("--candidate-id") + 1] if "--candidate-id" in argv else None
    if not candidate_id:
        print("ERROR: --candidate-id is required", file=sys.stderr)
        return 1

    promotion_file = root / "maintainer" / "upstreams" / "promotions" / f"{candidate_id}.json"
    if not promotion_file.exists():
        print("ERROR: promotion handoff not found", file=sys.stderr)
        return 2

    promotion = load_json(promotion_file)
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
    out = root / "maintainer" / "upstreams" / "rollback" / f"{candidate_id}.json"
    write_json(out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
