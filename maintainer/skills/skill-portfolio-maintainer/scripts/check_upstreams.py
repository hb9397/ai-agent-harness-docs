#!/usr/bin/env python3
"""Read-only upstream refresh checker.

By default this script prints a report and does not write files. With
--write-observed it updates lock.states[].observed only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from portfolio_common import http_json, load_json, mask_token, safe_join, stable_release, write_json
from validate_registry import validate_behavior_contracts


FRESH_STATUSES = {"ok", "fallback"}
STALE_FALLBACK = "preserve-last-accepted-mark-stale"


def github_repo_api(repository: str) -> str:
    parsed = urlparse(repository)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {"github.com", "www.github.com"}:
        raise ValueError("repository must be an https://github.com/OWNER/REPO URL")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise ValueError("repository URL must identify exactly one GitHub owner/repository")
    owner, repository_name = parts
    repository_name = repository_name.removesuffix(".git")
    if not owner or not repository_name:
        raise ValueError("repository URL is missing owner or repository")
    return f"https://api.github.com/repos/{quote(owner, safe='')}/{quote(repository_name, safe='')}"


def exact_watched_paths(source: dict[str, Any]) -> list[str]:
    paths = source.get("upstream", {}).get("watched_paths", [])
    wildcard_chars = {"*", "?", "[", "]"}
    return [
        path
        for path in paths
        if isinstance(path, str)
        and path
        and not any(char in path for char in wildcard_chars)
    ]


def http_text(url: str, timeout: int = 15, retries: int = 2) -> str:
    """Read a public documentation surface without storing or executing it."""
    headers = {
        "Accept": "text/markdown,text/plain,text/html;q=0.8,*/*;q=0.1",
        "User-Agent": "ai-agent-harness-skill-portfolio-maintainer",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and urlparse(url).hostname in {"github.com", "api.github.com", "raw.githubusercontent.com"}:
        headers["Authorization"] = f"Bearer {token}"

    last_error: str | None = None
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset)
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason}"
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as exc:
            last_error = str(exc)
        if attempt < retries:
            time.sleep(min(2 ** attempt, 4))
    raise RuntimeError(mask_token(last_error or "unknown http error"))


def normalized_content_sha256(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def resolve_watched_surfaces(source: dict[str, Any]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for surface in source.get("upstream", {}).get("watched_surfaces", []):
        surface_id = surface.get("id")
        url = surface.get("url")
        if not isinstance(surface_id, str) or not surface_id or not isinstance(url, str) or not url:
            observations.append({"id": surface_id, "url": url, "status": "error", "error": "invalid watched surface"})
            continue
        try:
            content = http_text(url)
            observations.append({
                "id": surface_id,
                "url": url,
                "checked_at": checked_at(),
                "status": "ok",
                "content_sha256": normalized_content_sha256(content),
            })
        except Exception as exc:  # noqa: BLE001 - preserve source-level observation
            observations.append({
                "id": surface_id,
                "url": url,
                "checked_at": checked_at(),
                "status": "error",
                "error": str(exc),
            })
    return observations


def resolve_watched_paths(base: str, ref: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for path in exact_watched_paths(source):
        url = (
            f"{base}/commits?sha={quote(ref, safe='')}"
            f"&path={quote(path, safe='')}&per_page=1"
        )
        try:
            commits = http_json(url)
            if isinstance(commits, list) and commits:
                commit = commits[0]
                observations.append({
                    "path": path,
                    "status": "ok",
                    "latest_commit_sha": commit.get("sha"),
                    "latest_commit_url": commit.get("html_url"),
                })
            else:
                observations.append({"path": path, "status": "not-found"})
        except Exception as exc:  # noqa: BLE001 - preserve the source-level observation
            observations.append({"path": path, "status": "error", "error": str(exc)})
    return observations


def resolve_github_source(
    source: dict[str, Any],
    fixture: dict[str, Any] | None = None,
    *,
    verify_watched_paths: bool = False,
) -> dict[str, Any]:
    sid = source["id"]
    if fixture is not None:
        if sid in fixture:
            return fixture[sid]
        return {"status": "skipped", "reason": "fixture-missing"}

    upstream = source.get("upstream", {})
    repository = upstream.get("repository")
    if not repository:
        return {"status": "skipped", "reason": "non-github-source"}

    try:
        base = github_repo_api(repository)
    except ValueError as exc:
        return {"status": "skipped", "reason": f"invalid-github-source:{exc}"}
    tracking = upstream.get("tracking")
    tag_pattern = upstream.get("tag_pattern")
    release_fallback = False

    if tracking == "release":
        releases = http_json(f"{base}/releases")
        release = stable_release(releases, tag_pattern)
        if release:
            tag = release["tag_name"]
            commit = http_json(f"{base}/git/ref/tags/{tag}")
            obj = commit.get("object", {})
            sha = obj.get("sha")
            if obj.get("type") == "tag":
                tag_obj = http_json(obj["url"])
                sha = tag_obj.get("object", {}).get("sha")
            result = {"status": "ok", "ref": tag, "sha": sha, "source_url": release.get("html_url")}
            if verify_watched_paths:
                result["watched_paths"] = resolve_watched_paths(base, tag, source)
            return result
        release_fallback = True

    if tracking in {"release", "branch"}:
        branch = upstream.get("branch")
        if not branch:
            repository_metadata = http_json(base)
            branch = repository_metadata.get("default_branch")
        if not branch:
            return {"status": "error", "reason": "github-default-branch-missing"}
        branch_obj = http_json(f"{base}/branches/{quote(branch, safe='')}")
        result = {
            "status": "fallback" if release_fallback else "ok",
            "ref": branch,
            "sha": branch_obj.get("commit", {}).get("sha"),
            "source_url": f"{repository.rstrip('/')}/tree/{quote(branch, safe='')}",
        }
        if release_fallback:
            result["note"] = "No matching stable release; exact repository default branch observed."
        if verify_watched_paths:
            result["watched_paths"] = resolve_watched_paths(base, branch, source)
        return result

    return {"status": "skipped", "reason": f"unsupported-tracking:{tracking}"}


def checked_at() -> str:
    value = os.environ.get("HARNESS_UPSTREAM_CHECKED_AT", dt.date.today().isoformat())
    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("HARNESS_UPSTREAM_CHECKED_AT must be YYYY-MM-DD") from exc
    return value


def behavior_contract_ids(source: dict[str, Any]) -> list[str]:
    contracts = source.get("target", {}).get("behavior_contracts", [])
    return [item for item in contracts if isinstance(item, str) and item]


def resolve_source(
    source: dict[str, Any],
    fixture: dict[str, Any] | None = None,
    *,
    verify_watched_paths: bool = False,
) -> dict[str, Any]:
    """Observe repository state and any declared behavior documentation surfaces."""
    observed = resolve_github_source(
        source,
        fixture,
        verify_watched_paths=verify_watched_paths,
    )
    if fixture is not None:
        return observed

    surface_definitions = source.get("upstream", {}).get("watched_surfaces", [])
    if not surface_definitions:
        return observed

    surfaces = resolve_watched_surfaces(source)
    surface_errors = [item for item in surfaces if item.get("status") != "ok"]
    refresh_policy = source.get("refresh_policy", {})
    if observed.get("status") == "skipped" and observed.get("reason") == "non-github-source":
        observed = {
            "status": "ok",
            "ref": refresh_policy.get("observed_ref") or source.get("upstream", {}).get("tracking"),
            "sha": None,
            "source_url": source.get("upstream", {}).get("source_url"),
        }
    observed["watched_surfaces"] = surfaces
    observed["product_version"] = refresh_policy.get("observed_product_version")
    if surface_errors:
        observed["status"] = "error"
        observed["error"] = "one or more watched documentation surfaces could not be verified"
    return observed


def _surface_hashes(entry: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(entry, dict):
        return {}
    return {
        item.get("id"): item.get("content_sha256")
        for item in entry.get("watched_surfaces", [])
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("content_sha256"), str)
    }


def _watched_path_shas(entry: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(entry, dict):
        return {}
    return {
        item.get("path"): item.get("latest_commit_sha")
        for item in entry.get("watched_paths", [])
        if isinstance(item, dict)
        and isinstance(item.get("path"), str)
        and isinstance(item.get("latest_commit_sha"), str)
    }


def apply_behavior_refresh_policy(
    source: dict[str, Any],
    observed: dict[str, Any],
    state: dict[str, Any] | None,
) -> dict[str, Any]:
    """Classify behavior evidence without ever applying upstream content."""
    if not behavior_contract_ids(source):
        return observed

    result = dict(observed)
    result["auto_import"] = False
    result["behavior_contracts"] = behavior_contract_ids(source)
    policy = source.get("refresh_policy", {})
    accepted = (state or {}).get("accepted")
    surfaces = result.get("watched_surfaces", [])
    surfaces_complete = (
        isinstance(surfaces, list)
        and bool(surfaces)
        and all(isinstance(item, dict) and item.get("status") == "ok" for item in surfaces)
    )
    watched_paths = result.get("watched_paths")
    paths_complete = (
        watched_paths is None
        or (
            isinstance(watched_paths, list)
            and bool(watched_paths)
            and all(isinstance(item, dict) and item.get("status") == "ok" for item in watched_paths)
        )
    )
    if result.get("status") not in FRESH_STATUSES or not surfaces_complete or not paths_complete:
        result["evidence_status"] = "stale"
        result["stale_fallback"] = {
            "strategy": policy.get("stale_fallback") or STALE_FALLBACK,
            "accepted_ref": accepted.get("ref") if isinstance(accepted, dict) else None,
            "accepted_sha": accepted.get("sha") if isinstance(accepted, dict) else None,
        }
        result["semantic_review_required"] = True
        result["note"] = "Behavior refresh incomplete; last accepted observation is preserved and marked stale."
        return result

    result["evidence_status"] = "fresh"
    accepted_surface_hashes = _surface_hashes(accepted)
    accepted_path_shas = _watched_path_shas(accepted)
    current_surface_hashes = _surface_hashes(result)
    current_path_shas = _watched_path_shas(result)
    result["semantic_review_required"] = bool(
        not isinstance(accepted, dict)
        or current_surface_hashes != accepted_surface_hashes
        or (current_path_shas and current_path_shas != accepted_path_shas)
        or result.get("product_version") != accepted.get("product_version")
    )
    return result


def update_observed(lock: dict[str, Any], source_id: str, observed: dict[str, Any]) -> None:
    states = lock.setdefault("states", [])
    state = next((item for item in states if item.get("id") == source_id), None)
    if not state:
        state = {"id": source_id, "accepted": None, "embedded": None, "packaged": None, "released": None}
        states.append(state)
    previous = state.get("observed") or {}
    if observed.get("evidence_status") == "stale":
        fallback = previous or state.get("accepted") or {}
        preserved = dict(fallback)
        preserved["evidence_status"] = "stale"
        preserved["last_check_attempt_at"] = checked_at()
        preserved["note"] = observed.get("note") or "Behavior refresh incomplete; last accepted observation preserved."
        preserved["stale_fallback"] = observed.get("stale_fallback", {
            "strategy": STALE_FALLBACK,
            "accepted_ref": (state.get("accepted") or {}).get("ref"),
            "accepted_sha": (state.get("accepted") or {}).get("sha"),
        })
        state["observed"] = preserved
        return
    watched_paths = observed.get("watched_paths")
    watched_paths_complete = (
        isinstance(watched_paths, list)
        and bool(watched_paths)
        and all(item.get("status") != "error" for item in watched_paths)
    )
    incomplete_note = (
        "Watched path verification incomplete; previous path observations preserved."
        if isinstance(watched_paths, list) and bool(watched_paths) and not watched_paths_complete
        else None
    )
    note_parts = [
        note
        for note in (observed.get("note"), incomplete_note)
        if note
    ]
    note = " ".join(note_parts) or (
        f"Observed by check_upstreams.py with status={observed.get('status')}"
    )
    state["observed"] = {
        "source_url": observed.get("source_url") or previous.get("source_url"),
        "checked_at": checked_at(),
        "ref": observed.get("ref") or previous.get("ref"),
        "sha": observed.get("sha") or previous.get("sha"),
        "evidence_status": observed.get("evidence_status") or previous.get("evidence_status"),
        "product_version": observed.get("product_version") or previous.get("product_version"),
        "note": note,
    }
    if watched_paths_complete:
        state["observed"]["watched_paths"] = watched_paths
    elif "watched_paths" in previous:
        state["observed"]["watched_paths"] = previous["watched_paths"]
    watched_surfaces = observed.get("watched_surfaces")
    surfaces_complete = (
        isinstance(watched_surfaces, list)
        and bool(watched_surfaces)
        and all(item.get("status") == "ok" for item in watched_surfaces)
    )
    if surfaces_complete:
        state["observed"]["watched_surfaces"] = watched_surfaces
    elif "watched_surfaces" in previous:
        state["observed"]["watched_surfaces"] = previous["watched_surfaces"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read registered upstream versions without changing accepted or packaged lock state."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4], help="harness repository root")
    parser.add_argument("--fixture", type=Path, help="offline source-id-to-observation JSON fixture")
    parser.add_argument(
        "--write-observed",
        action="store_true",
        help="write only lock.states[].observed after successful checks",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="check only this registered source id; repeat for multiple sources",
    )
    parser.add_argument(
        "--verify-watched-paths",
        action="store_true",
        help="also query the latest commit for each exact watched path; glob paths remain source-level only",
    )
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()

    registry_path = safe_join(root, "maintainer/upstreams/registry.json", reject_symlinks=True)
    lock_path = safe_join(root, "maintainer/upstreams/lock.json", reject_symlinks=True)
    current_path = safe_join(root, "maintainer/upstreams/provenance/current-skills.json", reject_symlinks=True)
    registry = load_json(registry_path)
    lock = load_json(lock_path)
    current = load_json(current_path)
    fixture = load_json(args.fixture) if args.fixture else None

    behavior_errors: list[str] = []
    validate_behavior_contracts(root, registry, lock, current, behavior_errors)
    if behavior_errors:
        parser.error("invalid behavior registry: " + "; ".join(behavior_errors))

    sources = [
        source
        for source in registry.get("sources", [])
        if source.get("id") != "internal-harness-native"
    ]
    requested = set(args.source)
    known = {source.get("id") for source in sources}
    unknown = sorted(requested - known)
    if unknown:
        parser.error(f"unknown source id(s): {', '.join(unknown)}")
    if requested:
        sources = [source for source in sources if source.get("id") in requested]

    report = {
        "schema_version": "1.1.0",
        "mode": "check",
        "write_observed": args.write_observed,
        "verify_watched_paths": args.verify_watched_paths,
        "behavior_contract_validation": "passed",
        "requested_sources": sorted(requested),
        "results": [],
    }
    states_by_id = {state.get("id"): state for state in lock.get("states", [])}
    for source in sources:
        try:
            observed = resolve_source(
                source,
                fixture,
                verify_watched_paths=(args.verify_watched_paths or bool(behavior_contract_ids(source))),
            )
        except Exception as exc:  # noqa: BLE001 - report and preserve lock
            observed = {"status": "error", "error": str(exc), "note": "current pinned state preserved"}
        observed = apply_behavior_refresh_policy(source, observed, states_by_id.get(source.get("id")))
        report["results"].append({"id": source.get("id"), "observed": observed})
        if args.write_observed and (
            observed.get("status") in FRESH_STATUSES
            or observed.get("evidence_status") == "stale"
        ):
            update_observed(lock, source["id"], observed)

    if args.write_observed:
        write_json(lock_path, lock)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
