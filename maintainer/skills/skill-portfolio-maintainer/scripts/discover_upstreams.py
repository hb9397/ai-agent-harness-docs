#!/usr/bin/env python3
"""Discover new official/reputable skill sources without changing registry."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from portfolio_common import http_json, load_json, safe_join


DEFAULT_CATALOG = [
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


def load_catalog(path: Path) -> list[dict[str, Any]]:
    value = load_json(path)
    if isinstance(value, list):
        candidates = value
    elif isinstance(value, dict):
        candidates = value.get("candidates") or value.get("seeds") or []
    else:
        raise ValueError(f"catalog must be a JSON array or object: {path}")
    if not isinstance(candidates, list):
        raise ValueError(f"catalog candidates must be an array: {path}")
    return candidates


def search_result_seed(item: dict[str, Any], query: str) -> dict[str, Any]:
    full_name = item.get("full_name") or ""
    owner = (item.get("owner") or {}).get("login") or full_name.partition("/")[0] or "unknown"
    fallback_id = hashlib.sha256(str(item.get("html_url", "")).encode("utf-8")).hexdigest()[:12]
    identifier = re.sub(r"[^A-Za-z0-9._-]+", "-", full_name).strip("-") or f"github-search-{fallback_id}"
    license_value = item.get("license")
    if isinstance(license_value, dict):
        license_value = license_value.get("spdx_id") or license_value.get("name")
    source_class = "official" if owner.lower() in {"openai", "anthropics"} else "community"
    return {
        "id": identifier,
        "class": source_class,
        "url": item.get("html_url"),
        "maintainer": owner,
        "license": license_value or "unknown",
        "activity": item.get("updated_at") or "unknown",
        "fit": [f"github-search:{query}"],
        "security_surface": ["repository contents require script/hook/network review"],
        "discovery_origin": "github-search",
    }


def github_search(query: str, limit: int, fixture: dict[str, Any] | None) -> list[dict[str, Any]]:
    if fixture is not None:
        search_results = fixture.get("search_results") or {}
        if query not in search_results:
            raise ValueError(f"fixture has no search_results entry for query: {query}")
        value = search_results[query]
        if isinstance(value, dict):
            value = value.get("items", [])
        if not isinstance(value, list):
            raise ValueError(f"fixture search result must be an array: {query}")
        return value[:limit]

    query_string = urlencode(
        {
            "q": query,
            "sort": "updated",
            "order": "desc",
            "per_page": limit,
        }
    )
    response = http_json(f"https://api.github.com/search/repositories?{query_string}")
    return (response.get("items") or [])[:limit]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Discover report-only upstream candidates from the built-in catalog, explicit JSON catalogs, "
            "and explicit GitHub repository searches."
        )
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4], help="harness repository root")
    parser.add_argument(
        "--fixture",
        type=Path,
        help="offline JSON containing seeds/candidates and optional search_results keyed by query",
    )
    parser.add_argument("--catalog", type=Path, action="append", default=[], help="additional candidate catalog JSON")
    parser.add_argument("--search-query", action="append", default=[], help="explicit GitHub repository search query")
    parser.add_argument("--search-limit", type=int, default=10, help="maximum results per search query (1-50)")
    parser.add_argument(
        "--no-default-catalog",
        action="store_true",
        help="exclude the built-in starter catalog",
    )
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not 1 <= args.search_limit <= 50:
        parser.error("--search-limit must be between 1 and 50")

    root = args.root.resolve()
    registry = load_json(safe_join(root, "maintainer/upstreams/registry.json", reject_symlinks=True))
    fixture = load_json(args.fixture) if args.fixture else None
    seeds: list[dict[str, Any]] = []
    catalog_inputs: list[str] = []
    input_errors: list[dict[str, str]] = []

    if not args.no_default_catalog:
        seeds.extend(DEFAULT_CATALOG)
        catalog_inputs.append("built-in")
    if fixture is not None:
        fixture_candidates = fixture.get("candidates") or fixture.get("seeds") or []
        if not isinstance(fixture_candidates, list):
            parser.error("--fixture candidates/seeds must be an array")
        seeds.extend(fixture_candidates)
        catalog_inputs.append(str(args.fixture))
    for catalog_path in args.catalog:
        try:
            seeds.extend(load_catalog(catalog_path))
            catalog_inputs.append(str(catalog_path))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            input_errors.append({"input": str(catalog_path), "error": str(exc)})

    search_inputs: list[str] = []
    for query in args.search_query:
        search_inputs.append(query)
        try:
            seeds.extend(search_result_seed(item, query) for item in github_search(query, args.search_limit, fixture))
        except Exception as exc:  # noqa: BLE001 - discovery reports failures without mutating state
            input_errors.append({"input": f"github-search:{query}", "error": str(exc)})

    candidates = []
    seen_urls: set[str] = set()
    for seed in seeds:
        if not isinstance(seed, dict) or not seed.get("id") or not seed.get("url"):
            input_errors.append({"input": "catalog-entry", "error": "candidate requires non-empty id and url"})
            continue
        if seed["url"] in seen_urls:
            continue
        seen_urls.add(seed["url"])
        candidates.append({
            "id": seed["id"],
            "source_class": seed.get("class", "unknown"),
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
        "discovery_inputs": {
            "catalogs": catalog_inputs,
            "search_queries": search_inputs,
            "fixed_seed_only": False,
        },
        "input_errors": input_errors,
        "candidates": candidates
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
