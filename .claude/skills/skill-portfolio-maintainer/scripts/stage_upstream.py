#!/usr/bin/env python3
"""Stage an upstream candidate without touching canonical skill sources."""

from __future__ import annotations

import datetime as dt
import json
import shutil
import sys
from pathlib import Path

from portfolio_common import load_json, safe_join, sha256_path, write_json


PROTECTED_MARKERS = ("scripts/", "templates/", "references/", "prompts/", "agents/", "commands/", "evals/", "tests/", "LICENSE", "NOTICE")


def has_protected_change(file_map: list[dict]) -> bool:
    for item in file_map:
        local = item.get("local_path") or ""
        if any(marker in local.replace("\\", "/") for marker in PROTECTED_MARKERS):
            return True
    return False


def main(argv: list[str]) -> int:
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path(__file__).resolve().parents[4]
    candidate_file = Path(argv[argv.index("--candidate") + 1]) if "--candidate" in argv else None
    if not candidate_file:
        print("ERROR: --candidate is required", file=sys.stderr)
        return 1
    candidate = load_json(candidate_file)
    candidate_id = candidate.get("id") or candidate.get("promotion", {}).get("target_skill") or candidate_file.stem

    if candidate.get("self_update_same_session"):
        print("ERROR: self-update same-session stage/promote is blocked", file=sys.stderr)
        return 2

    file_map = candidate.get("file_map") or candidate.get("promotion", {}).get("file_map") or []
    for item in file_map:
        for key in ("local_path", "upstream_path"):
            value = item.get(key)
            if value and (".." in Path(value).parts or value.startswith(("/", "\\"))):
                print(f"ERROR: path traversal blocked: {value}", file=sys.stderr)
                return 2

    staging_root = root / "maintainer" / "upstreams" / "staging" / candidate_id
    staging_root.mkdir(parents=True, exist_ok=True)
    staged_candidate = staging_root / "candidate.json"
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
        "status": "staged"
    }
    write_json(staging_root / "stage-report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
