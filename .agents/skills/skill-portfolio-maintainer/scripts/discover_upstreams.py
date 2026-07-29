#!/usr/bin/env python3
"""Discover new official/reputable skill sources without changing registry."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from portfolio_common import load_json


DEFAULT_SEEDS = [
    {
      "id": "openai-role-specific-plugins",
      "class": "official",
      "url": "https://github.com/openai/role-specific-plugins",
      "maintainer": "openai",
      "license": "MIT",
      "fit": ["frontend-design", "prototype", "product-design"],
      "security_surface": ["skills", "assets", "plugin manifest"]
    },
    {
      "id": "anthropic-claude-code-plugins",
      "class": "official",
      "url": "https://github.com/anthropics/claude-code",
      "maintainer": "anthropics",
      "license": "unknown",
      "fit": ["frontend-design", "claude-code runtime"],
      "security_surface": ["skills", "agents", "commands"]
    },
    {
      "id": "superpowers",
      "class": "reputable-third-party",
      "url": "https://github.com/obra/superpowers",
      "maintainer": "obra",
      "license": "MIT",
      "fit": ["planning", "review", "verification"],
      "security_surface": ["skills", "scripts", "hooks"]
    }
]


def duplicate_score(seed: dict[str, Any], registry: dict[str, Any]) -> str:
    urls = {item.get("upstream", {}).get("repository") or item.get("upstream", {}).get("source_url") for item in registry.get("sources", [])}
    return "registered" if seed["url"] in urls else "new"


def main(argv: list[str]) -> int:
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path(__file__).resolve().parents[4]
    fixture_path = Path(argv[argv.index("--fixture") + 1]) if "--fixture" in argv else None
    registry = load_json(root / "maintainer" / "upstreams" / "registry.json")
    seeds = load_json(fixture_path).get("seeds", DEFAULT_SEEDS) if fixture_path else DEFAULT_SEEDS

    candidates = []
    for seed in seeds:
        candidates.append({
            "id": seed["id"],
            "source_class": seed["class"],
            "provenance_url": seed["url"],
            "checked_at": dt.date.today().isoformat(),
            "maintainer": seed.get("maintainer"),
            "activity": seed.get("activity", "unknown"),
            "license": seed.get("license", "unknown"),
            "security_surface": seed.get("security_surface", []),
            "functional_fit": seed.get("fit", []),
            "duplicate_status": duplicate_score(seed, registry),
            "state_transition": "report-only",
            "note": "Candidate registration requires explicit maintainer approval; no files imported."
        })

    print(json.dumps({
        "schema_version": "1.0.0",
        "mode": "discover",
        "known_refresh_state": "not-used",
        "candidate_registration": "approval-required",
        "candidates": candidates
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
