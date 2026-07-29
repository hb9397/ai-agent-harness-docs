#!/usr/bin/env python3
"""Read-only upstream refresh checker.

By default this script prints a report and does not write files. With
--write-observed it updates lock.states[].observed only.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Any

from portfolio_common import http_json, load_json, stable_release, write_json


def github_repo_api(repository: str) -> str:
    owner_repo = repository.removeprefix("https://github.com/").strip("/")
    return f"https://api.github.com/repos/{owner_repo}"


def resolve_github_source(source: dict[str, Any], fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    sid = source["id"]
    if fixture is not None:
        if sid in fixture:
            return fixture[sid]
        return {"status": "skipped", "reason": "fixture-missing"}

    upstream = source.get("upstream", {})
    repository = upstream.get("repository")
    if not repository or "github.com/" not in repository:
        return {"status": "skipped", "reason": "non-github-source"}

    base = github_repo_api(repository)
    tracking = upstream.get("tracking")
    tag_pattern = upstream.get("tag_pattern")

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
            return {"status": "ok", "ref": tag, "sha": sha, "source_url": release.get("html_url")}

    if tracking in {"release", "branch"}:
        branch = "main"
        branches = http_json(f"{base}/branches")
        names = [item.get("name") for item in branches]
        if "main" not in names and names:
            branch = names[0]
        branch_obj = http_json(f"{base}/branches/{branch}")
        return {
            "status": "fallback",
            "ref": branch,
            "sha": branch_obj.get("commit", {}).get("sha"),
            "source_url": f"{repository}/tree/{branch}",
        }

    return {"status": "skipped", "reason": f"unsupported-tracking:{tracking}"}


def update_observed(lock: dict[str, Any], source_id: str, observed: dict[str, Any]) -> None:
    states = lock.setdefault("states", [])
    state = next((item for item in states if item.get("id") == source_id), None)
    if not state:
        state = {"id": source_id, "accepted": None, "embedded": None, "packaged": None, "released": None}
        states.append(state)
    previous = state.get("observed") or {}
    state["observed"] = {
        "source_url": observed.get("source_url") or previous.get("source_url"),
        "checked_at": dt.date.today().isoformat(),
        "ref": observed.get("ref") or previous.get("ref"),
        "sha": observed.get("sha") or previous.get("sha"),
        "note": observed.get("note") or f"Observed by check_upstreams.py with status={observed.get('status')}",
    }


def main(argv: list[str]) -> int:
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path(__file__).resolve().parents[4]
    fixture_path = Path(argv[argv.index("--fixture") + 1]) if "--fixture" in argv else None
    write_observed = "--write-observed" in argv

    registry_path = root / "maintainer" / "upstreams" / "registry.json"
    lock_path = root / "maintainer" / "upstreams" / "lock.json"
    registry = load_json(registry_path)
    lock = load_json(lock_path)
    fixture = load_json(fixture_path) if fixture_path else None

    report = {"schema_version": "1.0.0", "mode": "check", "write_observed": write_observed, "results": []}
    for source in registry.get("sources", []):
        if source.get("id") == "internal-harness-native":
            continue
        try:
            observed = resolve_github_source(source, fixture)
        except Exception as exc:  # noqa: BLE001 - report and preserve lock
            observed = {"status": "error", "error": str(exc), "note": "current pinned state preserved"}
        report["results"].append({"id": source.get("id"), "observed": observed})
        if write_observed and observed.get("status") in {"ok", "fallback"}:
            update_observed(lock, source["id"], observed)

    if write_observed:
        write_json(lock_path, lock)
    print(__import__("json").dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
