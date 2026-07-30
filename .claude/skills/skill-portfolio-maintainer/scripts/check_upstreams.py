#!/usr/bin/env python3
"""Read-only upstream refresh checker.

By default this script prints a report and does not write files. With
--write-observed it updates lock.states[].observed only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from portfolio_common import http_json, load_json, safe_join, stable_release, write_json


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


def update_observed(lock: dict[str, Any], source_id: str, observed: dict[str, Any]) -> None:
    states = lock.setdefault("states", [])
    state = next((item for item in states if item.get("id") == source_id), None)
    if not state:
        state = {"id": source_id, "accepted": None, "embedded": None, "packaged": None, "released": None}
        states.append(state)
    previous = state.get("observed") or {}
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
        "note": note,
    }
    if watched_paths_complete:
        state["observed"]["watched_paths"] = watched_paths
    elif "watched_paths" in previous:
        state["observed"]["watched_paths"] = previous["watched_paths"]


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
    registry = load_json(registry_path)
    lock = load_json(lock_path)
    fixture = load_json(args.fixture) if args.fixture else None

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
        "schema_version": "1.0.0",
        "mode": "check",
        "write_observed": args.write_observed,
        "verify_watched_paths": args.verify_watched_paths,
        "requested_sources": sorted(requested),
        "results": [],
    }
    for source in sources:
        try:
            observed = resolve_github_source(
                source,
                fixture,
                verify_watched_paths=args.verify_watched_paths,
            )
        except Exception as exc:  # noqa: BLE001 - report and preserve lock
            observed = {"status": "error", "error": str(exc), "note": "current pinned state preserved"}
        report["results"].append({"id": source.get("id"), "observed": observed})
        if args.write_observed and observed.get("status") in {"ok", "fallback"}:
            update_observed(lock, source["id"], observed)

    if args.write_observed:
        write_json(lock_path, lock)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
