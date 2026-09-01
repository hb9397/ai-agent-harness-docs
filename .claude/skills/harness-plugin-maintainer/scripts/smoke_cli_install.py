#!/usr/bin/env python3
"""Run isolated Codex and Claude Code local-marketplace install smokes.

The smoke uses temporary platform configuration directories, installs the plugin
from this repository, verifies the installed payload, then uninstalls everything.
It never reads or writes the user's normal Codex or Claude configuration.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from plugin_common import MARKETPLACE_NAME, PLUGIN_ID, PLUGIN_ROOT_REL, load_json, repo_root, write_json


QUALIFIED_PLUGIN_ID = f"{PLUGIN_ID}@{MARKETPLACE_NAME}"


class SmokeFailure(RuntimeError):
    """Raised when an isolated CLI smoke does not satisfy its contract."""


def command_from_json(raw: str, label: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"{label} command must be a JSON string array: {exc}") from exc
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise SmokeFailure(f"{label} command must be a non-empty JSON string array")
    return resolve_executable(value)


def resolve_executable(command: list[str]) -> list[str]:
    """Resolve a bare command name to a full path before spawning it.

    npm global installs put `codex.CMD` and `claude.CMD` on PATH. Windows shell
    lookup finds those, but subprocess without a shell does not, so a bare name
    fails with WinError 2 even though the CLI is installed. shutil.which applies
    PATHEXT the same way the shell does.
    """
    head, *rest = command
    if os.sep in head or (os.altsep and os.altsep in head):
        return command
    resolved = shutil.which(head)
    return [resolved, *rest] if resolved else command


def run(
    prefix: list[str],
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    command = [*prefix, *args]
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SmokeFailure(f"failed to run {command!r}: {exc}") from exc
    if check and completed.returncode != 0:
        stdout = completed.stdout[-2000:]
        stderr = completed.stderr[-2000:]
        raise SmokeFailure(
            f"command failed ({completed.returncode}): {command!r}\n"
            f"stdout:\n{stdout}\nstderr:\n{stderr}"
        )
    return completed


def parse_json_stdout(completed: subprocess.CompletedProcess[str], label: str) -> Any:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeFailure(
            f"{label} did not return JSON: {completed.stdout[-2000:]!r}"
        ) from exc


def installed_payload_contract(install_root: Path, platform: str) -> dict[str, Any]:
    capabilities_path = install_root / "CAPABILITIES.json"
    if not capabilities_path.is_file():
        raise SmokeFailure(f"installed payload missing {capabilities_path}")
    capabilities = load_json(capabilities_path)
    platform_caps = capabilities.get(platform, {})
    skills_rel = str(platform_caps.get("skills_path", "")).removeprefix("./")
    skills_root = install_root / skills_rel
    if not skills_root.is_dir():
        raise SmokeFailure(f"installed {platform} skills directory missing: {skills_root}")

    skill_names = sorted(
        child.name
        for child in skills_root.iterdir()
        if child.is_dir() and (child / "SKILL.md").is_file()
    )
    expected_names = sorted(capabilities.get("logical_user_skills", []))
    if skill_names != expected_names:
        raise SmokeFailure(
            f"installed {platform} skills differ: expected {expected_names}, got {skill_names}"
        )

    agent_roots = [
        install_root / "agents",
        install_root / "runtime" / platform / "agents",
    ]
    agent_files = sorted(
        path.relative_to(install_root).as_posix()
        for agent_root in agent_roots
        if agent_root.exists()
        for path in agent_root.rglob("*")
        if path.is_file()
    )
    if agent_files:
        raise SmokeFailure(f"installed {platform} payload contains agents: {agent_files}")

    forbidden_catalogs = [
        install_root / ".agents" / "plugins" / "marketplace.json",
        install_root / ".claude-plugin" / "marketplace.json",
    ]
    nested_catalogs = [
        path.relative_to(install_root).as_posix()
        for path in forbidden_catalogs
        if path.exists()
    ]
    if nested_catalogs:
        raise SmokeFailure(f"plugin payload contains nested marketplace catalogs: {nested_catalogs}")

    for required in ("harness-setup", "humanize-korean"):
        if required not in skill_names:
            raise SmokeFailure(f"installed {platform} payload missing required skill {required}")

    expected_count = platform_caps.get("physical_skills")
    if expected_count != len(skill_names):
        raise SmokeFailure(
            f"{platform} capability count {expected_count!r} does not match {len(skill_names)}"
        )
    if platform_caps.get("physical_agents") != 0:
        raise SmokeFailure(f"{platform} physical_agents must be 0")

    return {
        "version": capabilities.get("version"),
        "skill_count": len(skill_names),
        "agent_count": 0,
        "required_skills": ["harness-setup", "humanize-korean"],
        "evidence_level": "installed-cache-payload",
        "model_invocation_verified": False,
        "nested_marketplaces": 0,
    }


def codex_smoke(root: Path, command: list[str]) -> dict[str, Any]:
    marketplace_added = False
    plugin_installed = False
    cleanup_errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="harness-kit-codex-") as temp_dir:
        env = os.environ.copy()
        codex_home = Path(temp_dir) / "codex-home"
        codex_home.mkdir()
        env["CODEX_HOME"] = str(codex_home)
        try:
            version = run(command, ["--version"], cwd=root, env=env).stdout.strip()
            added = parse_json_stdout(
                run(
                    command,
                    ["plugin", "marketplace", "add", str(root), "--json"],
                    cwd=root,
                    env=env,
                ),
                "Codex marketplace add",
            )
            marketplace_added = True
            if added.get("marketplaceName") != MARKETPLACE_NAME:
                raise SmokeFailure(f"unexpected Codex marketplace: {added!r}")

            marketplaces = parse_json_stdout(
                run(
                    command,
                    ["plugin", "marketplace", "list", "--json"],
                    cwd=root,
                    env=env,
                ),
                "Codex marketplace list",
            )
            if MARKETPLACE_NAME not in {
                item.get("name") for item in marketplaces.get("marketplaces", [])
            }:
                raise SmokeFailure("Codex marketplace list does not contain harness-kit")

            installed = parse_json_stdout(
                run(
                    command,
                    ["plugin", "add", QUALIFIED_PLUGIN_ID, "--json"],
                    cwd=root,
                    env=env,
                ),
                "Codex plugin add",
            )
            plugin_installed = True
            if installed.get("pluginId") != QUALIFIED_PLUGIN_ID:
                raise SmokeFailure(f"unexpected Codex plugin install result: {installed!r}")
            payload = installed_payload_contract(Path(installed["installedPath"]), "codex")

            listed = parse_json_stdout(
                run(command, ["plugin", "list", "--json"], cwd=root, env=env),
                "Codex plugin list",
            )
            matching = [
                item
                for item in listed.get("installed", [])
                if item.get("pluginId") == QUALIFIED_PLUGIN_ID
            ]
            if len(matching) != 1 or not matching[0].get("enabled"):
                raise SmokeFailure(f"Codex installed plugin not enabled exactly once: {matching!r}")
        finally:
            if plugin_installed:
                removed = run(
                    command,
                    ["plugin", "remove", QUALIFIED_PLUGIN_ID, "--json"],
                    cwd=root,
                    env=env,
                    check=False,
                )
                if removed.returncode != 0:
                    cleanup_errors.append("Codex plugin remove failed")
            if marketplace_added:
                removed_marketplace = run(
                    command,
                    ["plugin", "marketplace", "remove", MARKETPLACE_NAME, "--json"],
                    cwd=root,
                    env=env,
                    check=False,
                )
                if removed_marketplace.returncode != 0:
                    cleanup_errors.append("Codex marketplace remove failed")
        if cleanup_errors:
            raise SmokeFailure("; ".join(cleanup_errors))

    return {
        "status": "passed",
        "cli_version": version,
        "marketplace": MARKETPLACE_NAME,
        "plugin_id": QUALIFIED_PLUGIN_ID,
        "evidence_level": "marketplace-install-and-cache-smoke",
        "model_invocation_verified": False,
        "installed_payload": payload,
        "cleanup": "passed",
    }


def claude_smoke(root: Path, command: list[str]) -> dict[str, Any]:
    marketplace_added = False
    plugin_installed = False
    cleanup_errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="harness-kit-claude-") as temp_dir:
        temp_root = Path(temp_dir)
        env = os.environ.copy()
        claude_config = temp_root / "config"
        claude_cache = temp_root / "plugin-cache"
        claude_config.mkdir()
        claude_cache.mkdir()
        env["CLAUDE_CONFIG_DIR"] = str(claude_config)
        env["CLAUDE_CODE_PLUGIN_CACHE_DIR"] = str(claude_cache)
        try:
            version = run(command, ["--version"], cwd=root, env=env).stdout.strip()
            run(
                command,
                ["plugin", "validate", str(root / PLUGIN_ROOT_REL)],
                cwd=root,
                env=env,
            )
            run(
                command,
                ["plugin", "validate", str(root)],
                cwd=root,
                env=env,
            )
            run(
                command,
                ["plugin", "marketplace", "add", f"./{root.name}"],
                cwd=root.parent,
                env=env,
            )
            marketplace_added = True

            marketplaces = parse_json_stdout(
                run(
                    command,
                    ["plugin", "marketplace", "list", "--json"],
                    cwd=root,
                    env=env,
                ),
                "Claude marketplace list",
            )
            if MARKETPLACE_NAME not in {item.get("name") for item in marketplaces}:
                raise SmokeFailure("Claude marketplace list does not contain harness-kit")

            run(
                command,
                ["plugin", "install", QUALIFIED_PLUGIN_ID, "--scope", "user"],
                cwd=root,
                env=env,
            )
            plugin_installed = True

            listed = parse_json_stdout(
                run(command, ["plugin", "list", "--json"], cwd=root, env=env),
                "Claude plugin list",
            )
            matching = [
                item
                for item in listed
                if item.get("id") == QUALIFIED_PLUGIN_ID and item.get("scope") == "user"
            ]
            if len(matching) != 1 or not matching[0].get("enabled"):
                raise SmokeFailure(f"Claude installed plugin not enabled exactly once: {matching!r}")
            payload = installed_payload_contract(Path(matching[0]["installPath"]), "claude")
        finally:
            if plugin_installed:
                removed = run(
                    command,
                    [
                        "plugin",
                        "uninstall",
                        QUALIFIED_PLUGIN_ID,
                        "--scope",
                        "user",
                    ],
                    cwd=root,
                    env=env,
                    check=False,
                )
                if removed.returncode != 0:
                    cleanup_errors.append("Claude plugin uninstall failed")
            if marketplace_added:
                removed_marketplace = run(
                    command,
                    ["plugin", "marketplace", "remove", MARKETPLACE_NAME],
                    cwd=root,
                    env=env,
                    check=False,
                )
                if removed_marketplace.returncode != 0:
                    cleanup_errors.append("Claude marketplace remove failed")
        if cleanup_errors:
            raise SmokeFailure("; ".join(cleanup_errors))

    return {
        "status": "passed",
        "cli_version": version,
        "marketplace": MARKETPLACE_NAME,
        "plugin_id": QUALIFIED_PLUGIN_ID,
        "evidence_level": "marketplace-install-and-cache-smoke",
        "model_invocation_verified": False,
        "installed_payload": payload,
        "cleanup": "passed",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Install harness-kit from the local repository in isolated Codex and "
            "Claude configuration directories, verify it, then uninstall it."
        )
    )
    parser.add_argument(
        "--platform",
        choices=("all", "codex", "claude"),
        default="all",
        help="platform smoke to run (default: all)",
    )
    parser.add_argument(
        "--codex-command-json",
        default='["codex"]',
        help='Codex command prefix as JSON, for example ["codex"]',
    )
    parser.add_argument(
        "--claude-command-json",
        default='["claude"]',
        help='Claude command prefix as JSON, for example ["claude"]',
    )
    parser.add_argument("--root", type=Path, default=repo_root(), help="repository root")
    parser.add_argument("--output", type=Path, help="optional JSON evidence output path")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="validate command parsing and both local payload contracts without invoking CLIs",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.self_test:
        command_from_json('["codex"]', "Codex")
        try:
            command_from_json('"codex"', "Codex")
        except SmokeFailure:
            pass
        else:
            raise SmokeFailure("command parser accepted a non-array command")
        plugin_root = root / PLUGIN_ROOT_REL
        codex = installed_payload_contract(plugin_root, "codex")
        claude = installed_payload_contract(plugin_root, "claude")
        print(
            json.dumps(
                {
                    "status": "passed",
                    "codex_skills": codex["skill_count"],
                    "claude_skills": claude["skill_count"],
                    "agents": codex["agent_count"] + claude["agent_count"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    results: dict[str, Any] = {
        "schema_version": "1.0.0",
        "verified_at": os.environ.get(
            "HARNESS_CLI_SMOKE_VERIFIED_AT", "2026-07-29T00:00:00+09:00"
        ),
        "plugin_id": PLUGIN_ID,
        "qualified_plugin_id": QUALIFIED_PLUGIN_ID,
        "marketplace_source": ".",
        "evidence_level": "marketplace-install-and-cache-smoke",
        "model_invocation_verified": False,
        "platforms": {},
    }
    try:
        if args.platform in {"all", "codex"}:
            results["platforms"]["codex"] = codex_smoke(
                root, command_from_json(args.codex_command_json, "Codex")
            )
        if args.platform in {"all", "claude"}:
            results["platforms"]["claude"] = claude_smoke(
                root, command_from_json(args.claude_command_json, "Claude")
            )
        results["status"] = "passed"
    except SmokeFailure as exc:
        results["status"] = "failed"
        results["error"] = str(exc)

    if args.output:
        write_json(args.output.resolve(), results)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if results["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
