#!/usr/bin/env python3
"""Plan, apply, and verify project document write-access artifacts."""

from __future__ import annotations

import atexit
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = SKILL_ROOT / "assets" / "runtime"
NAMESPACE = "harness-kit-project-write-access"
SCHEMA_VERSION = "1.1.0"
ROLES = {"admin", "pm-pl", "app-doc-lead"}
WRITE_SCOPES = {"admin", "app-doc", "team"}
PROVIDERS = ("github", "gitlab", "gitea")
CODEOWNERS_MARKERS = (
    "# harness-kit:write-access:start",
    "# harness-kit:write-access:end",
)
INSTRUCTION_MARKERS = (
    "<!-- harness-kit:write-access:start -->",
    "<!-- harness-kit:write-access:end -->",
)
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")


class AccessError(RuntimeError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: Path, content: bytes, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(raw)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def run(command: list[str], *, cwd: Path | None = None, stdin: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(command, cwd=cwd, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if check and result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise AccessError(message or f"command failed: {command[0]}")
    return result


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return run(["git", "-C", str(root), *args], check=check)


def validate_config(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise AccessError(f"config schema_version must be {SCHEMA_VERSION}")
    project_id = str(raw.get("project_id", ""))
    if not SAFE_ID.fullmatch(project_id):
        raise AccessError("project_id must be a safe 1-63 character identifier")

    applications = raw.get("applications")
    if not isinstance(applications, list) or not applications:
        raise AccessError("applications must contain at least one application id")
    if len(set(applications)) != len(applications) or any(not isinstance(item, str) or not SAFE_ID.fullmatch(item) for item in applications):
        raise AccessError("application ids must be unique safe identifiers")

    principals = raw.get("principals")
    if not isinstance(principals, list) or not principals:
        raise AccessError("principals must contain at least one entry")
    ids: set[str] = set()
    provider_accounts: set[tuple[str, str]] = set()
    admin_count = 0
    for principal in principals:
        principal_id = str(principal.get("id", ""))
        role = str(principal.get("role", ""))
        if not SAFE_ID.fullmatch(principal_id) or principal_id in ids:
            raise AccessError("principal ids must be unique safe identifiers")
        if role not in ROLES:
            raise AccessError(f"unsupported role for {principal_id}: {role}")
        ids.add(principal_id)
        admin_count += int(role == "admin")
        scoped_applications = principal.get("applications")
        if role == "app-doc-lead":
            if (
                not isinstance(scoped_applications, list)
                or not scoped_applications
                or any(not isinstance(app, str) for app in scoped_applications)
                or len(set(scoped_applications)) != len(scoped_applications)
                or any(app not in applications for app in scoped_applications)
            ):
                raise AccessError(
                    f"app-doc-lead {principal_id} requires unique applications from the configured application list"
                )
        elif scoped_applications is not None:
            raise AccessError(f"applications may be assigned only to app-doc-lead principals: {principal_id}")
        accounts = principal.get("accounts", {})
        if not isinstance(accounts, dict):
            raise AccessError(f"accounts for {principal_id} must be an object")
        for provider, account in accounts.items():
            if provider not in PROVIDERS:
                raise AccessError(f"unsupported provider account: {provider}")
            if not isinstance(account, str) or not re.fullmatch(r"@[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?", account):
                raise AccessError(f"invalid {provider} account for {principal_id}")
            account_key = (provider, account.casefold())
            if account_key in provider_accounts:
                raise AccessError(f"{provider} account is assigned to more than one principal: {account}")
            provider_accounts.add(account_key)
    if admin_count < 1:
        raise AccessError("at least one admin principal is required")

    configured_rules = raw.get("path_rules")
    if configured_rules is not None:
        if not isinstance(configured_rules, list) or not configured_rules:
            raise AccessError("path_rules must be a non-empty array when provided")
        for rule in configured_rules:
            pattern = rule.get("pattern")
            write_scope = rule.get("write_scope")
            application = rule.get("application")
            allowed_control_paths = {
                "AGENTS.md",
                "CLAUDE.md",
                ".github/CODEOWNERS",
                ".gitlab/CODEOWNERS",
                ".gitea/CODEOWNERS",
                ".claude/settings.json",
                ".codex/hooks.json",
            }
            if not isinstance(pattern, str) or not (pattern.startswith(".docs/") or pattern in allowed_control_paths):
                raise AccessError("path_rules may protect only document-harness and write-access control paths")
            if "\\" in pattern or any(part == ".." for part in pattern.split("/")):
                raise AccessError("path_rules may not contain backslashes or parent traversal")
            if write_scope not in WRITE_SCOPES or not isinstance(rule.get("priority"), int):
                raise AccessError("each path rule requires a valid write_scope and integer priority")
            if write_scope == "app-doc":
                if application not in applications:
                    raise AccessError("app-doc path rules require a configured application")
            elif application is not None:
                raise AccessError("application may be set only on app-doc path rules")

    repositories = raw.get("repositories", [])
    if not isinstance(repositories, list):
        raise AccessError("repositories must be an array")
    for repo in repositories:
        if repo.get("provider") not in PROVIDERS:
            raise AccessError("repository provider must be github, gitlab, or gitea")
        branches = repo.get("protected_branches", [])
        if not isinstance(branches, list) or any(not isinstance(item, str) or not item.strip() for item in branches):
            raise AccessError("protected_branches must be an array of non-empty strings")
        if repo.get("server_policy", "externally-approved") not in {"externally-approved", "none"}:
            raise AccessError("server_policy must be externally-approved or none")

    local_identity = raw.get("local_identity")
    if local_identity is not None:
        if not isinstance(local_identity, dict) or local_identity.get("provider") not in PROVIDERS:
            raise AccessError("local_identity provider is invalid")
        if not isinstance(local_identity.get("account"), str):
            raise AccessError("local_identity account is required")

    for flag in ("enable_git_hooks", "enable_ai_hooks"):
        if flag in raw and not isinstance(raw[flag], bool):
            raise AccessError(f"{flag} must be a boolean")

    result = copy.deepcopy(raw)
    result.setdefault("repositories", [])
    result.setdefault("enable_git_hooks", True)
    result.setdefault("enable_ai_hooks", True)
    return result


def load_config(path: Path) -> dict[str, Any]:
    try:
        return validate_config(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise AccessError(f"invalid config JSON: {exc}") from exc


def is_git_root(path: Path) -> bool:
    result = git(path, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        return False
    try:
        return Path(result.stdout.decode().strip()).resolve() == path.resolve()
    except OSError:
        return False


def detect_layout(project_root: Path) -> dict[str, Any]:
    docs_root = project_root / ".docs"
    if docs_root.is_dir() and is_git_root(docs_root):
        git_root = docs_root
        git_root_relative = ".docs"
        topology = "multi-repository"
    elif is_git_root(project_root):
        git_root = project_root
        git_root_relative = "."
        topology = "single-repository"
    else:
        git_root = None
        git_root_relative = "."
        topology = "local-only"
    return {
        "topology": topology,
        "git_root": git_root,
        "git_root_relative": git_root_relative,
        "root_context_tracked": topology == "single-repository",
    }


def path_rules(config: dict[str, Any], layout: dict[str, Any]) -> list[dict[str, Any]]:
    docs = ".docs"
    rules: list[dict[str, Any]] = []

    def add(pattern: str, write_scope: str, priority: int, application: str | None = None) -> None:
        item: dict[str, Any] = {"pattern": pattern, "write_scope": write_scope, "priority": priority}
        if application is not None:
            item["application"] = application
        rules.append(item)

    def add_control_plane() -> None:
        add("AGENTS.md", "admin", 120)
        add("CLAUDE.md", "admin", 120)
        add(".claude/settings.json", "admin", 120)
        add(".codex/hooks.json", "admin", 120)
        codeowners_prefix = "" if layout["git_root_relative"] == "." else f"{docs}/"
        for provider_dir in (".github", ".gitlab", ".gitea"):
            add(f"{codeowners_prefix}{provider_dir}/CODEOWNERS", "admin", 120)

    add_control_plane()
    add(f"{docs}/**", "admin", 0)

    if config.get("path_rules"):
        configured_patterns = {item["pattern"] for item in config["path_rules"]}
        rules = [item for item in rules if item["pattern"] not in configured_patterns]
        rules.extend(copy.deepcopy(config["path_rules"]))
        return rules

    add(f"{docs}/README.md", "admin", 110)
    add(f"{docs}/.gitignore", "admin", 110)
    add(f"{docs}/root-context/**", "admin", 110)
    add(f"{docs}/harness/**", "admin", 110)
    add(f"{docs}/.harness/**", "admin", 110)
    add(f"{docs}/_inbox/**", "team", 100)
    add(f"{docs}/prototype/**", "team", 100)
    if len(config["applications"]) == 1:
        application = config["applications"][0]
        add(f"{docs}/context-base/**", "app-doc", 90, application)
        add(f"{docs}/instruction/**", "app-doc", 90, application)
        add(f"{docs}/impl-doc/**", "team", 100)
    for app in config["applications"]:
        add(f"{docs}/{app}-context.md", "app-doc", 90, app)
        add(f"{docs}/{app}/context-base/**", "app-doc", 90, app)
        add(f"{docs}/{app}/instruction/**", "app-doc", 90, app)
        add(f"{docs}/{app}/impl-doc/**", "team", 100)
        add(f"{docs}/{app}/prototype/**", "team", 100)
    return rules


def build_policy_core(config: dict[str, Any], layout: dict[str, Any], remote_verification: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": config["project_id"],
        "topology": layout["topology"],
        "git_root_relative": layout["git_root_relative"],
        "root_context_tracked": layout["root_context_tracked"],
        "remote_verification": remote_verification,
        "role_inheritance": {"admin": ["pm-pl"], "pm-pl": [], "app-doc-lead": []},
        "authorization_model": {
            "app_scoped_role": "app-doc-lead",
            "unregistered_team_write": True,
            "admin_app_doc_confirmation": "required-by-ai-instruction",
        },
        "applications": sorted(config["applications"]),
        "principals": sorted(config["principals"], key=lambda item: item["id"]),
        "path_rules": path_rules(config, layout),
        "repositories": config["repositories"],
    }


def path_in_git(rule_path: str, layout: dict[str, Any]) -> str | None:
    prefix = layout["git_root_relative"]
    if prefix == ".":
        return rule_path
    if rule_path == prefix:
        return ""
    marker = prefix.rstrip("/") + "/"
    return rule_path[len(marker):] if rule_path.startswith(marker) else None


def eligible_owners(policy: dict[str, Any], rule: dict[str, Any], provider: str) -> list[str]:
    write_scope = rule["write_scope"]
    if write_scope == "team":
        return []
    application = rule.get("application")
    result: list[str] = []
    for principal in policy["principals"]:
        role = principal["role"]
        account = principal.get("accounts", {}).get(provider)
        if not account:
            continue
        if write_scope == "admin" and role != "admin":
            continue
        if write_scope == "app-doc" and not (
            role == "pm-pl" or (role == "app-doc-lead" and application in principal.get("applications", []))
        ):
            continue
        result.append(account)
    return sorted(set(result), key=str.casefold)


def glob_to_gitea(pattern: str) -> str:
    result = ["^"]
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "*":
            if index + 1 < len(pattern) and pattern[index + 1] == "*":
                result.append(".*")
                index += 2
            else:
                result.append("[^/]*")
                index += 1
        elif char == "?":
            result.append("[^/]")
            index += 1
        else:
            result.append("\\" + char if char in ".+*?()|[]{}^$\\" else char)
            index += 1
    result.append("$")
    return "".join(result)


def render_codeowners_block(policy: dict[str, Any], provider: str, layout: dict[str, Any], policy_core_hash: str) -> str:
    start, end = CODEOWNERS_MARKERS
    lines = [start, f"# policy_core_sha256: {policy_core_hash}"]
    lines.append("# coverage: explicit owner paths only; team-write paths intentionally have no CODEOWNERS rule")
    rendered = 0
    for rule in sorted(policy["path_rules"], key=lambda item: int(item["priority"])):
        if rule["pattern"] == ".docs/**" and rule["write_scope"] == "admin":
            continue
        relative = path_in_git(rule["pattern"], layout)
        if relative is None:
            continue
        owners = eligible_owners(policy, rule, provider)
        if not owners:
            continue
        pattern = glob_to_gitea(relative) if provider == "gitea" else "/" + relative.lstrip("/")
        lines.append(f"{pattern} {' '.join(owners)}")
        rendered += 1
    if rendered == 0:
        lines.append(f"# inactive: no valid {provider} owner account is registered")
    lines.append(end)
    return "\n".join(lines) + "\n"


def replace_managed_block(existing: bytes | None, block: str, markers: tuple[str, str]) -> bytes:
    text = existing.decode("utf-8") if existing is not None else ""
    start, end = markers
    start_count = text.count(start)
    end_count = text.count(end)
    if start_count != end_count or start_count > 1:
        raise AccessError("managed block markers are malformed or duplicated")
    if start_count == 1:
        left = text.index(start)
        right = text.index(end, left) + len(end)
        merged = text[:left] + block.rstrip("\n") + text[right:]
    else:
        separator = "" if not text else ("\n" if text.endswith("\n") else "\n\n")
        merged = text + separator + block
    if not merged.endswith("\n"):
        merged += "\n"
    return merged.encode("utf-8")


def codeowners_targets(git_root: Path) -> dict[str, Path]:
    return {
        "github": git_root / ".github" / "CODEOWNERS",
        "gitlab": git_root / ".gitlab" / "CODEOWNERS",
        "gitea": git_root / ".gitea" / "CODEOWNERS",
    }


def provider_shadow(git_root: Path, provider: str, managed_target: Path) -> str | None:
    order = {
        "github": [git_root / ".github" / "CODEOWNERS", git_root / "CODEOWNERS", git_root / "docs" / "CODEOWNERS"],
        "gitlab": [git_root / "CODEOWNERS", git_root / "docs" / "CODEOWNERS", git_root / ".gitlab" / "CODEOWNERS"],
        "gitea": [git_root / "CODEOWNERS", git_root / "docs" / "CODEOWNERS", git_root / ".gitea" / "CODEOWNERS"],
    }[provider]
    for candidate in order:
        if candidate.resolve() == managed_target.resolve():
            return None
        if candidate.is_file():
            return candidate.relative_to(git_root).as_posix()
    return None


def instruction_targets(project_root: Path, applications: list[str]) -> list[Path]:
    targets: set[Path] = set()
    for root_file in (project_root / "AGENTS.md", project_root / "CLAUDE.md"):
        if root_file.is_file():
            targets.add(root_file)
    roots = [project_root / ".docs" / "instruction"] + [project_root / ".docs" / app / "instruction" for app in applications]
    for directory in roots:
        if not directory.is_dir():
            continue
        found = sorted(path for path in directory.glob("*-instruction.md") if path.is_file())
        agent = directory / "agent-instruction.md"
        if agent.is_file() and agent not in found:
            found.append(agent)
        if found:
            targets.update(found)
        elif directory.parent.name in applications:
            targets.add(directory / "write-access-instruction.md")
    return sorted(targets)


def render_instruction_block(policy_core_hash: str) -> str:
    start, end = INSTRUCTION_MARKERS
    return "\n".join(
        [
            start,
            "## 문서 쓰기 권한 확인",
            "",
            f"- 정책: `@.docs/harness/access-control/policy.json` (`{policy_core_hash}`)",
            "- 읽기는 모두 허용한다. 파일 생성·편집과 AI가 실행하는 Git 명령 전에 서명 정책의 현재 계정·역할·대상 앱·쓰기 범위를 확인한다.",
            "- `admin`은 관리 문서와 제어 설정을, `pm-pl`은 모든 앱의 핵심 문서를, `app-doc-lead`는 배정된 앱의 핵심 문서만 쓸 수 있다.",
            "- 등록되지 않은 일반 기여자도 `team` 범위의 구현 지침·프로토타입·임시 입력 경로에는 쓸 수 있다. 개발자를 개인별 principal로 등록하지 않는다.",
            "- `admin`이 `app-doc` 범위를 대신 수정할 때는 일반 내용 승인과 별도로 대상 앱·파일·원래 소유 범위·수정 이유를 보여주고 한 번 더 확인받는다. 그 승인을 다른 변경에 재사용하지 않는다.",
            "- guard의 `check-path`가 `decision=confirm`을 반환하거나 `PreToolUse`가 `permissionDecision=ask`를 반환하면 그 확인을 생략하지 않는다.",
            "- 신원·프로젝트·앱·경로를 확정할 수 없거나 권한이 부족하면 직접 쓰지 말고 해당 문서 소유자에게 변경안을 제안한다.",
            "- 이 블록은 `project-write-access`만 갱신한다. 블록 밖의 설계·개발 지침은 원래 소유자가 관리한다.",
            end,
            "",
        ]
    )


def merge_hook_config(path: Path, host: str, project_root: Path) -> tuple[bytes, dict[str, Any]]:
    if path.is_file():
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AccessError(f"cannot merge malformed JSON: {path}") from exc
    else:
        config = {}
    hooks = config.setdefault("hooks", {})
    entries = hooks.setdefault("PreToolUse", [])
    if not isinstance(entries, list):
        raise AccessError(f"PreToolUse must be an array: {path}")
    if host == "claude":
        handler = {
            "type": "command",
            "command": "python",
            "args": [
                "${CLAUDE_PROJECT_DIR}/.docs/harness/access-control/hooks/write_access_guard.py",
                "ai",
                "--host",
                "claude",
                "--project-root",
                "${CLAUDE_PROJECT_DIR}",
            ],
        }
        matcher = "Write|Edit|Bash|PowerShell"
    else:
        guard = project_root / ".docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
        command = f'python "{guard}" ai --host codex --project-root "{project_root}"'
        handler = {"type": "command", "command": command, "commandWindows": command}
        matcher = "apply_patch|Edit|Write|Bash|PowerShell|MCP|.*"

    def managed(entry: Any) -> bool:
        if not isinstance(entry, dict):
            return False
        return "write_access_guard.py" in json.dumps(entry, ensure_ascii=False)

    entries[:] = [entry for entry in entries if not managed(entry)]
    managed_entry = {"matcher": matcher, "hooks": [handler]}
    entries.append(managed_entry)
    return pretty_json(config), managed_entry


def relative(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def read_optional(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def preflight(layout: dict[str, Any]) -> dict[str, Any]:
    git_root: Path | None = layout["git_root"]
    if git_root is None:
        return {"git": "not-initialized", "dirty": False, "remote": False, "upstream": "none"}
    status = git(git_root, "status", "--porcelain").stdout.decode().splitlines()
    remotes = git(git_root, "remote", check=False).stdout.decode().splitlines()
    upstream_result = git(git_root, "rev-parse", "--abbrev-ref", "@{upstream}", check=False)
    state: dict[str, Any] = {"git": "ready", "dirty": bool(status), "remote": bool(remotes), "upstream": "none"}
    if upstream_result.returncode == 0:
        upstream = upstream_result.stdout.decode().strip()
        counts = git(git_root, "rev-list", "--left-right", "--count", f"HEAD...{upstream}").stdout.decode().split()
        state.update({"upstream": upstream, "ahead": int(counts[0]), "behind": int(counts[1])})
    return state


def make_plan(project_root: Path, config: dict[str, Any], operation: str = "apply") -> dict[str, Any]:
    layout = detect_layout(project_root)
    state = preflight(layout)
    remote_verification = "pending" if state["remote"] else "local-only"
    policy_core = build_policy_core(config, layout, remote_verification)
    policy_core_hash = sha256_bytes(canonical_json(policy_core))
    changes: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []
    git_root: Path | None = layout["git_root"]
    if git_root is not None:
        for provider, target in codeowners_targets(git_root).items():
            block = render_codeowners_block(policy_core, provider, layout, policy_core_hash)
            desired = replace_managed_block(read_optional(target), block, CODEOWNERS_MARKERS)
            current = read_optional(target)
            changes.append({"path": relative(project_root, target), "action": "unchanged" if current == desired else ("create" if current is None else "modify")})
            shadow = provider_shadow(git_root, provider, target)
            if shadow:
                conflicts.append({"provider": provider, "type": "shadowed-codeowners", "path": shadow})
    else:
        conflicts.append({"provider": "all", "type": "no-git-repository", "path": ".docs"})

    block = render_instruction_block(policy_core_hash)
    for target in instruction_targets(project_root, config["applications"]):
        desired = replace_managed_block(read_optional(target), block, INSTRUCTION_MARKERS)
        current = read_optional(target)
        changes.append({"path": relative(project_root, target), "action": "unchanged" if current == desired else ("create" if current is None else "modify")})

    access_dir = project_root / ".docs" / "harness" / "access-control"
    for name in ("trust.json", "policy.json", "policy.sig", "provider-state.json", "generated-manifest.json", "hooks/write_access_guard.py", "hooks/git/pre-commit", "hooks/git/pre-push"):
        target = access_dir / name
        changes.append({"path": relative(project_root, target), "action": "modify" if target.exists() else "create"})
    if config["enable_ai_hooks"]:
        for target in (project_root / ".claude" / "settings.json", project_root / ".codex" / "hooks.json"):
            changes.append({"path": relative(project_root, target), "action": "modify" if target.exists() else "create"})
    if config["enable_git_hooks"] and git_root is None:
        conflicts.append({"provider": "local-git", "type": "hooks-unavailable", "path": ".git/config"})

    plan_basis = {
        "schema_version": SCHEMA_VERSION,
        "operation": operation,
        "project_root": str(project_root.resolve()),
        "config": config,
        "topology": layout["topology"],
        "git_root_relative": layout["git_root_relative"],
        "policy_core_sha256": policy_core_hash,
        "changes": sorted(changes, key=lambda item: item["path"]),
        "conflicts": conflicts,
    }
    return {
        **plan_basis,
        "preflight": state,
        "plan_hash": sha256_bytes(canonical_json(plan_basis)),
        "server_changes": [
            {
                "provider": repo["provider"],
                "repository_path": repo.get("path", "."),
                "protected_branches": repo.get("protected_branches", []),
                "status": "requires-separate-provider-admin-approval" if repo.get("server_policy") != "none" else "not-requested",
            }
            for repo in config["repositories"]
        ],
    }


def public_key_from_private(key_path: Path) -> str:
    result = run(["ssh-keygen", "-y", "-f", str(key_path)])
    parts = result.stdout.decode().strip().split()
    if len(parts) < 2 or parts[0] != "ssh-ed25519":
        raise AccessError("administrator key is not an OpenSSH Ed25519 key")
    return f"{parts[0]} {parts[1]}"


def fingerprint(public_key: str) -> str:
    with tempfile.TemporaryDirectory(prefix="write-access-fingerprint-") as raw:
        path = Path(raw) / "key.pub"
        path.write_text(public_key + "\n", encoding="utf-8", newline="\n")
        result = run(["ssh-keygen", "-lf", str(path), "-E", "sha256"])
    parts = result.stdout.decode().split()
    if len(parts) < 2:
        raise AccessError("could not calculate administrator key fingerprint")
    return parts[1]


def restrict_private_key(path: Path) -> None:
    os.chmod(path, 0o600)
    if os.name == "nt":
        user = os.environ.get("USERNAME")
        if not user:
            raise AccessError("USERNAME is required to restrict a Windows private key")
        result = run(["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:(F)"], check=False)
        if result.returncode != 0:
            raise AccessError("failed to restrict Windows administrator-key ACL")


def create_admin_key(project_id: str, codex_dir: Path, claude_dir: Path) -> tuple[Path, list[Path]]:
    targets = [codex_dir / f"{project_id}.key", claude_dir / f"{project_id}.key"]
    if any(path.exists() or path.with_suffix(path.suffix + ".pub").exists() for path in targets):
        raise AccessError("administrator key path already exists; use verified recovery or rotation")
    created = [item for target in targets for item in (target, target.with_suffix(target.suffix + ".pub"))]
    try:
        with tempfile.TemporaryDirectory(prefix="write-access-key-") as raw:
            source = Path(raw) / "admin.key"
            run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", f"harness-kit:{project_id}", "-f", str(source)])
            private_bytes = source.read_bytes()
            public_bytes = source.with_suffix(".key.pub").read_bytes()
            for target in targets:
                atomic_write(target, private_bytes, 0o600)
                restrict_private_key(target)
                atomic_write(target.with_suffix(target.suffix + ".pub"), public_bytes, 0o644)
        if targets[0].read_bytes() != targets[1].read_bytes():
            raise AccessError("Codex and Claude administrator-key copies differ")
    except Exception:
        cleanup_created_keys(created)
        raise
    return targets[0], created


def generate_admin_key_material(project_id: str) -> tuple[bytes, bytes]:
    with tempfile.TemporaryDirectory(prefix="write-access-rotate-key-") as raw:
        source = Path(raw) / "admin.key"
        run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", f"harness-kit:{project_id}", "-f", str(source)])
        return source.read_bytes(), source.with_suffix(".key.pub").read_bytes()


def public_key_from_public_bytes(value: bytes) -> str:
    parts = value.decode("utf-8").strip().split()
    if len(parts) < 2 or parts[0] != "ssh-ed25519":
        raise AccessError("generated administrator public key is invalid")
    return f"{parts[0]} {parts[1]}"


def cleanup_created_keys(paths: list[Path]) -> None:
    parents: set[Path] = set()
    for path in paths:
        parents.add(path.parent)
        if path.is_file():
            path.unlink()
    for parent in sorted(parents, key=lambda item: len(item.parts), reverse=True):
        try:
            parent.rmdir()
        except OSError:
            pass


def locate_admin_key(project_id: str, codex_dir: Path, claude_dir: Path, backup: Path | None) -> Path:
    if backup is not None:
        if not backup.is_file():
            raise AccessError("backup administrator key does not exist")
        return backup
    codex = codex_dir / f"{project_id}.key"
    claude = claude_dir / f"{project_id}.key"
    if not codex.is_file() or not claude.is_file():
        raise AccessError("both Codex and Claude administrator-key copies are required, or provide --admin-key")
    if codex.read_bytes() != claude.read_bytes():
        raise AccessError("Codex and Claude administrator-key copies differ")
    return codex


def sign_policy(policy_bytes: bytes, key_path: Path) -> bytes:
    with tempfile.TemporaryDirectory(prefix="write-access-sign-") as raw:
        payload = Path(raw) / "policy.json"
        payload.write_bytes(policy_bytes)
        run(["ssh-keygen", "-Y", "sign", "-f", str(key_path), "-n", NAMESPACE, str(payload)])
        return payload.with_suffix(".json.sig").read_bytes()


def sign_policy_with_material(policy_bytes: bytes, private_key: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="write-access-rotate-sign-") as raw:
        key_path = Path(raw) / "admin.key"
        atomic_write(key_path, private_key, 0o600)
        restrict_private_key(key_path)
        return sign_policy(policy_bytes, key_path)


def managed_hash(content: bytes, markers: tuple[str, str]) -> str:
    text = content.decode("utf-8")
    start, end = markers
    if text.count(start) != 1 or text.count(end) != 1:
        raise AccessError("managed block is missing or malformed")
    left = text.index(start)
    right = text.index(end, left) + len(end)
    return sha256_bytes(text[left:right].encode("utf-8"))


def provider_state(config: dict[str, Any], layout: dict[str, Any], git_root: Path | None, evidence: str | None, policy_core_hash: str) -> dict[str, Any]:
    states: dict[str, Any] = {}
    targets = codeowners_targets(git_root) if git_root is not None else {}
    configured_repos = {item["provider"]: item for item in config["repositories"]}
    for provider in PROVIDERS:
        target = targets.get(provider)
        shadow = provider_shadow(git_root, provider, target) if git_root is not None and target is not None else None
        repo = configured_repos.get(provider, {})
        states[provider] = {
            "codeowners": relative(Path(config["_project_root"]), target) if target is not None else None,
            "shadowed_by": shadow,
            "codeowners_status": "shadowed" if shadow else ("generated" if target is not None else "unavailable"),
            "server_rules_status": "not-applied",
            "protected_branches": repo.get("protected_branches", []),
            "coverage": "known-signed-policy-paths" if provider == "gitea" else "all-docs-with-ordered-overrides",
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_core_sha256": policy_core_hash,
        "provider_admin_evidence_sha256": sha256_bytes(evidence.encode("utf-8")) if evidence else None,
        "providers": states,
        "hosts": {
            "claude": "pending-trust" if config["enable_ai_hooks"] else "not-installed",
            "codex": "pending-trust" if config["enable_ai_hooks"] else "not-installed",
        },
    }


def snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
    return {path: read_optional(path) for path in paths}


def restore_files(values: dict[Path, bytes | None]) -> None:
    for path, content in values.items():
        if content is None:
            if path.is_file():
                path.unlink()
        else:
            atomic_write(path, content)


GIT_CONFIG_KEYS = (
    "core.hooksPath",
    "harness.writeAccess.projectRoot",
    "harness.writeAccess.provider",
    "harness.writeAccess.account",
)


def git_config_values(git_root: Path) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for key in GIT_CONFIG_KEYS:
        result = git(git_root, "config", "--local", "--get-all", key, check=False)
        values[key] = result.stdout.decode().splitlines() if result.returncode == 0 else []
    return values


def restore_git_config(git_root: Path, values: dict[str, list[str]]) -> None:
    for key, original in values.items():
        git(git_root, "config", "--local", "--unset-all", key, check=False)
        for value in original:
            git(git_root, "config", "--local", "--add", key, value)


def git_local_state_path(git_root: Path) -> Path:
    raw = git(git_root, "rev-parse", "--git-dir").stdout.decode().strip()
    path = Path(raw)
    if not path.is_absolute():
        path = git_root / path
    return path.resolve() / "harness-write-access.json"


def install_git_hooks(project_root: Path, git_root: Path, layout: dict[str, Any], config: dict[str, Any]) -> None:
    git_dir_raw = git(git_root, "rev-parse", "--git-dir").stdout.decode().strip()
    git_dir = Path(git_dir_raw)
    if not git_dir.is_absolute():
        git_dir = git_root / git_dir
    state_path = git_dir.resolve() / "harness-write-access.json"
    previous_value = git(git_root, "config", "--local", "--get", "core.hooksPath", check=False)
    previous_hooks_path = previous_value.stdout.decode().strip() if previous_value.returncode == 0 else str(git_dir.resolve() / "hooks")
    hook_path = Path(previous_hooks_path)
    if not hook_path.is_absolute():
        hook_path = git_root / hook_path
    ours_relative = ".docs/harness/access-control/hooks/git" if layout["git_root_relative"] == "." else "harness/access-control/hooks/git"
    previous_hooks: dict[str, str] = {}
    if hook_path.resolve() != (git_root / ours_relative).resolve():
        for name in ("pre-commit", "pre-push"):
            candidate = hook_path / name
            if candidate.is_file():
                previous_hooks[name] = str(candidate.resolve())
    ours_path = (git_root / ours_relative).resolve()
    if hook_path.resolve() == ours_path and state_path.is_file():
        local_state = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        local_state = {
            "schema_version": SCHEMA_VERSION,
            "previous_core_hooks_path": previous_value.stdout.decode().strip() if previous_value.returncode == 0 else None,
            "previous_hooks": previous_hooks,
        }
    atomic_write(state_path, pretty_json(local_state))
    git(git_root, "config", "--local", "--replace-all", "core.hooksPath", ours_relative)
    git(git_root, "config", "--local", "--replace-all", "harness.writeAccess.projectRoot", str(project_root.resolve()))
    identity = config.get("local_identity")
    if identity:
        git(git_root, "config", "--local", "--replace-all", "harness.writeAccess.provider", identity["provider"])
        git(git_root, "config", "--local", "--replace-all", "harness.writeAccess.account", identity["account"])


def verify_signature(policy_path: Path, trust_path: Path, signature_path: Path) -> dict[str, Any]:
    policy_bytes = policy_path.read_bytes()
    policy = json.loads(policy_bytes.decode("utf-8"))
    trust = json.loads(trust_path.read_text(encoding="utf-8"))
    public_key = str(trust.get("admin_public_key", "")).strip()
    with tempfile.TemporaryDirectory(prefix="write-access-verify-") as raw:
        allowed = Path(raw) / "allowed_signers"
        allowed.write_text(f"harness-admin {public_key}\n", encoding="utf-8", newline="\n")
        result = run(
            ["ssh-keygen", "-Y", "verify", "-f", str(allowed), "-I", "harness-admin", "-n", NAMESPACE, "-s", str(signature_path)],
            stdin=policy_bytes,
            check=False,
        )
    if result.returncode != 0:
        raise AccessError("policy signature verification failed")
    return policy


def json_handler_hash(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("hooks", {}).get("PreToolUse", [])
    managed = [entry for entry in entries if "write_access_guard.py" in json.dumps(entry, ensure_ascii=False)]
    if len(managed) != 1:
        raise AccessError(f"managed AI hook entry is missing or duplicated: {path}")
    return sha256_bytes(canonical_json(managed[0]))


def verify_bundle(project_root: Path) -> dict[str, Any]:
    access_dir = project_root / ".docs" / "harness" / "access-control"
    required = {name: access_dir / name for name in ("policy.json", "trust.json", "policy.sig", "generated-manifest.json")}
    for name, path in required.items():
        if not path.is_file():
            raise AccessError(f"missing {name}")
    policy = verify_signature(required["policy.json"], required["trust.json"], required["policy.sig"])
    core = copy.deepcopy(policy)
    declared_core = core.pop("policy_core_sha256", None)
    core.pop("generated_manifest_sha256", None)
    if declared_core != sha256_bytes(canonical_json(core)):
        raise AccessError("policy core hash mismatch")
    manifest_bytes = required["generated-manifest.json"].read_bytes()
    if policy.get("generated_manifest_sha256") != sha256_bytes(manifest_bytes):
        raise AccessError("generated manifest hash mismatch")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    for entry in manifest.get("files", []):
        path = project_root / entry["path"]
        if not path.is_file():
            raise AccessError(f"generated file is missing: {entry['path']}")
        mode = entry["mode"]
        if mode == "full":
            actual = sha256_bytes(path.read_bytes())
        elif mode == "codeowners-block":
            actual = managed_hash(path.read_bytes(), CODEOWNERS_MARKERS)
        elif mode == "instruction-block":
            actual = managed_hash(path.read_bytes(), INSTRUCTION_MARKERS)
        elif mode == "json-handler":
            actual = json_handler_hash(path)
        else:
            raise AccessError(f"unknown manifest mode: {mode}")
        if actual != entry["sha256"]:
            raise AccessError(f"generated content hash mismatch: {entry['path']}")
    return {"status": "valid", "project_id": policy["project_id"], "policy_core_sha256": declared_core, "files": len(manifest.get("files", []))}


def remove_managed_block(content: bytes, markers: tuple[str, str]) -> bytes:
    text = content.decode("utf-8")
    start, end = markers
    if text.count(start) != 1 or text.count(end) != 1:
        raise AccessError("managed block is missing or malformed")
    left = text.index(start)
    right = text.index(end, left) + len(end)
    return (text[:left] + text[right:]).encode("utf-8")


def remove_json_handler(content: bytes) -> bytes:
    data = json.loads(content.decode("utf-8"))
    entries = data.get("hooks", {}).get("PreToolUse", [])
    if not isinstance(entries, list):
        raise AccessError("PreToolUse must be an array")
    managed = [entry for entry in entries if "write_access_guard.py" in json.dumps(entry, ensure_ascii=False)]
    if len(managed) != 1:
        raise AccessError("managed AI hook entry is missing or duplicated")
    data["hooks"]["PreToolUse"] = [entry for entry in entries if entry is not managed[0]]
    return pretty_json(data)


def make_remove_plan(project_root: Path, delete_keys: bool) -> dict[str, Any]:
    verified = verify_bundle(project_root)
    access_dir = project_root / ".docs" / "harness" / "access-control"
    manifest = json.loads((access_dir / "generated-manifest.json").read_text(encoding="utf-8"))
    policy = json.loads((access_dir / "policy.json").read_text(encoding="utf-8"))
    paths = sorted({entry["path"] for entry in manifest["files"]} | {
        ".docs/harness/access-control/policy.json",
        ".docs/harness/access-control/policy.sig",
        ".docs/harness/access-control/generated-manifest.json",
    })
    basis = {
        "schema_version": SCHEMA_VERSION,
        "operation": "remove",
        "project_root": str(project_root.resolve()),
        "project_id": policy["project_id"],
        "policy_core_sha256": verified["policy_core_sha256"],
        "managed_paths": paths,
        "delete_keys": delete_keys,
        "provider_server_rules": "left-unchanged; requires separate provider-admin approval",
    }
    return {**basis, "plan_hash": sha256_bytes(canonical_json(basis))}


def remove_access_control(project_root: Path, approved_hash: str, codex_dir: Path, claude_dir: Path, backup_key: Path | None, delete_keys: bool) -> dict[str, Any]:
    plan = make_remove_plan(project_root, delete_keys)
    if plan["plan_hash"] != approved_hash:
        raise AccessError("approved removal plan hash does not match the current plan")
    access_dir = project_root / ".docs" / "harness" / "access-control"
    policy = json.loads((access_dir / "policy.json").read_text(encoding="utf-8"))
    trust = json.loads((access_dir / "trust.json").read_text(encoding="utf-8"))
    key_path = locate_admin_key(policy["project_id"], codex_dir, claude_dir, backup_key)
    if fingerprint(public_key_from_private(key_path)) != trust.get("admin_key_fingerprint"):
        raise AccessError("administrator key fingerprint does not match current trust")
    manifest = json.loads((access_dir / "generated-manifest.json").read_text(encoding="utf-8"))
    layout = detect_layout(project_root)
    git_root: Path | None = layout["git_root"]
    state_path = git_local_state_path(git_root) if git_root is not None else None
    key_paths = [
        codex_dir / f"{policy['project_id']}.key",
        codex_dir / f"{policy['project_id']}.key.pub",
        claude_dir / f"{policy['project_id']}.key",
        claude_dir / f"{policy['project_id']}.key.pub",
    ]
    target_paths = [project_root / entry["path"] for entry in manifest["files"]]
    target_paths.extend([access_dir / "policy.json", access_dir / "policy.sig", access_dir / "generated-manifest.json"])
    if state_path is not None:
        target_paths.append(state_path)
    if delete_keys:
        target_paths.extend(key_paths)
    file_snapshot = snapshot(list(dict.fromkeys(target_paths)))
    git_snapshot = git_config_values(git_root) if git_root is not None else None
    try:
        for entry in manifest["files"]:
            path = project_root / entry["path"]
            if not path.is_file():
                raise AccessError(f"managed file disappeared during removal: {entry['path']}")
            mode = entry["mode"]
            if mode == "codeowners-block":
                reduced = remove_managed_block(path.read_bytes(), CODEOWNERS_MARKERS)
                if reduced.strip():
                    atomic_write(path, reduced)
                else:
                    path.unlink()
            elif mode == "instruction-block":
                reduced = remove_managed_block(path.read_bytes(), INSTRUCTION_MARKERS)
                if reduced.strip():
                    atomic_write(path, reduced)
                else:
                    path.unlink()
            elif mode == "json-handler":
                atomic_write(path, remove_json_handler(path.read_bytes()))

        if git_root is not None:
            local_state = json.loads(state_path.read_text(encoding="utf-8")) if state_path is not None and state_path.is_file() else None
            if local_state is not None:
                previous = local_state.get("previous_core_hooks_path")
                git(git_root, "config", "--local", "--unset-all", "core.hooksPath", check=False)
                if previous is not None:
                    git(git_root, "config", "--local", "--add", "core.hooksPath", previous)
                for key in GIT_CONFIG_KEYS[1:]:
                    git(git_root, "config", "--local", "--unset-all", key, check=False)
                state_path.unlink()
            else:
                current = git(git_root, "config", "--local", "--get", "core.hooksPath", check=False)
                ours = ".docs/harness/access-control/hooks/git" if layout["git_root_relative"] == "." else "harness/access-control/hooks/git"
                if current.returncode == 0 and current.stdout.decode().strip() == ours:
                    raise AccessError("local Git hook recovery state is missing")

        for entry in manifest["files"]:
            if entry["mode"] == "full":
                path = project_root / entry["path"]
                if path.is_file():
                    path.unlink()
        for path in (access_dir / "policy.json", access_dir / "policy.sig", access_dir / "generated-manifest.json"):
            if path.is_file():
                path.unlink()
        if delete_keys:
            for path in key_paths:
                if path.is_file():
                    path.unlink()
    except Exception:
        restore_files(file_snapshot)
        if git_root is not None and git_snapshot is not None:
            restore_git_config(git_root, git_snapshot)
        for path in key_paths:
            if path.suffix == ".key" and path.is_file():
                restrict_private_key(path)
        raise
    remaining = sorted(relative(project_root, path) for path in access_dir.rglob("*") if path.is_file()) if access_dir.is_dir() else []
    return {
        "status": "removed",
        "project_id": policy["project_id"],
        "keys": "deleted" if delete_keys else "preserved",
        "remaining_access_control_files": remaining,
        "provider_server_rules": "left-unchanged",
    }


def apply(project_root: Path, config: dict[str, Any], approved_hash: str, codex_dir: Path, claude_dir: Path, backup_key: Path | None, evidence: str | None, rotate_key: bool = False) -> dict[str, Any]:
    plan = make_plan(project_root, config, "rotate" if rotate_key else "apply")
    if plan["plan_hash"] != approved_hash:
        raise AccessError("approved plan hash does not match the current plan")
    state = plan["preflight"]
    if state.get("dirty"):
        raise AccessError("Git worktree is not clean")
    if state.get("behind", 0) > 0 or (state.get("ahead", 0) > 0 and state.get("behind", 0) > 0):
        raise AccessError("Git history is behind or diverged; fast-forward it before Apply")
    if state.get("remote") and not evidence:
        raise AccessError("remote repositories require provider-admin evidence before Apply")

    layout = detect_layout(project_root)
    remote_verification = "verified" if evidence else "local-only"
    policy_core = build_policy_core(config, layout, remote_verification)
    policy_core_hash = sha256_bytes(canonical_json(policy_core))
    access_dir = project_root / ".docs" / "harness" / "access-control"
    initial = not (access_dir / "policy.json").is_file()
    if not initial:
        verify_bundle(project_root)
    if initial and rotate_key:
        raise AccessError("administrator key rotation requires an existing signed policy")

    created_keys: list[Path] = []
    key_outputs: dict[Path, bytes] = {}
    rotation_private: bytes | None = None
    if initial:
        key_path, created_keys = create_admin_key(config["project_id"], codex_dir, claude_dir)
        atexit.register(cleanup_created_keys, created_keys)
        public_key = public_key_from_private(key_path)
        key_fingerprint = fingerprint(public_key)
    else:
        current_key = locate_admin_key(config["project_id"], codex_dir, claude_dir, backup_key)
        current_public_key = public_key_from_private(current_key)
        current_fingerprint = fingerprint(current_public_key)
        trust = json.loads((access_dir / "trust.json").read_text(encoding="utf-8"))
        if trust.get("admin_key_fingerprint") != current_fingerprint:
            raise AccessError("administrator key fingerprint does not match current trust")
        if rotate_key:
            rotation_private, rotation_public = generate_admin_key_material(config["project_id"])
            public_key = public_key_from_public_bytes(rotation_public)
            key_fingerprint = fingerprint(public_key)
            for target in (codex_dir / f"{config['project_id']}.key", claude_dir / f"{config['project_id']}.key"):
                key_outputs[target] = rotation_private
                key_outputs[target.with_suffix(target.suffix + ".pub")] = rotation_public
            key_path = current_key
        else:
            key_path = current_key
            public_key = current_public_key
            key_fingerprint = current_fingerprint

    config_with_root = copy.deepcopy(config)
    config_with_root["_project_root"] = str(project_root.resolve())
    git_root: Path | None = layout["git_root"]
    provider_state_value = provider_state(config_with_root, layout, git_root, evidence, policy_core_hash)
    trust_value = {
        "schema_version": SCHEMA_VERSION,
        "project_id": config["project_id"],
        "admin_public_key": public_key,
        "admin_key_fingerprint": key_fingerprint,
        "admin_principals": sorted(principal["id"] for principal in config["principals"] if principal["role"] == "admin"),
        "signature_namespace": NAMESPACE,
    }

    full_outputs: dict[Path, bytes] = {
        access_dir / "trust.json": pretty_json(trust_value),
        access_dir / "provider-state.json": pretty_json(provider_state_value),
        access_dir / "hooks" / "write_access_guard.py": (RUNTIME_ROOT / "write_access_guard.py").read_bytes(),
        access_dir / "hooks" / "git" / "pre-commit": (RUNTIME_ROOT / "pre-commit").read_bytes(),
        access_dir / "hooks" / "git" / "pre-push": (RUNTIME_ROOT / "pre-push").read_bytes(),
    }
    managed_outputs: dict[Path, tuple[bytes, str]] = {}
    if git_root is not None:
        for provider, target in codeowners_targets(git_root).items():
            block = render_codeowners_block(policy_core, provider, layout, policy_core_hash)
            managed_outputs[target] = (replace_managed_block(read_optional(target), block, CODEOWNERS_MARKERS), "codeowners-block")
    instruction_block = render_instruction_block(policy_core_hash)
    for target in instruction_targets(project_root, config["applications"]):
        managed_outputs[target] = (replace_managed_block(read_optional(target), instruction_block, INSTRUCTION_MARKERS), "instruction-block")

    json_outputs: dict[Path, tuple[bytes, dict[str, Any]]] = {}
    if config["enable_ai_hooks"]:
        json_outputs[project_root / ".claude" / "settings.json"] = merge_hook_config(project_root / ".claude" / "settings.json", "claude", project_root)
        json_outputs[project_root / ".codex" / "hooks.json"] = merge_hook_config(project_root / ".codex" / "hooks.json", "codex", project_root)

    manifest_entries: list[dict[str, str]] = []
    for path, content in full_outputs.items():
        manifest_entries.append({"path": relative(project_root, path), "mode": "full", "sha256": sha256_bytes(content)})
    for path, (content, mode) in managed_outputs.items():
        markers = CODEOWNERS_MARKERS if mode == "codeowners-block" else INSTRUCTION_MARKERS
        manifest_entries.append({"path": relative(project_root, path), "mode": mode, "sha256": managed_hash(content, markers)})
    for path, (_content, handler) in json_outputs.items():
        manifest_entries.append({"path": relative(project_root, path), "mode": "json-handler", "sha256": sha256_bytes(canonical_json(handler))})
    manifest = {"schema_version": SCHEMA_VERSION, "policy_core_sha256": policy_core_hash, "files": sorted(manifest_entries, key=lambda item: item["path"])}
    manifest_bytes = pretty_json(manifest)
    policy = {**policy_core, "policy_core_sha256": policy_core_hash, "generated_manifest_sha256": sha256_bytes(manifest_bytes)}
    policy_bytes = canonical_json(policy)
    signature_bytes = sign_policy_with_material(policy_bytes, rotation_private) if rotation_private is not None else sign_policy(policy_bytes, key_path)

    final_outputs = {
        **full_outputs,
        **{path: content for path, (content, _mode) in managed_outputs.items()},
        **{path: content for path, (content, _handler) in json_outputs.items()},
        access_dir / "generated-manifest.json": manifest_bytes,
        access_dir / "policy.json": policy_bytes,
        access_dir / "policy.sig": signature_bytes,
    }
    transaction_paths = [*final_outputs, *key_outputs]
    if git_root is not None and config["enable_git_hooks"]:
        transaction_paths.append(git_local_state_path(git_root))
    file_snapshot = snapshot(transaction_paths)
    git_snapshot = git_config_values(git_root) if git_root is not None else None
    try:
        for path, content in final_outputs.items():
            mode = 0o755 if path.name in {"pre-commit", "pre-push", "write_access_guard.py"} else None
            atomic_write(path, content, mode)
        for path, content in key_outputs.items():
            private = path.suffix == ".key"
            atomic_write(path, content, 0o600 if private else 0o644)
            if private:
                restrict_private_key(path)
        if config["enable_git_hooks"] and git_root is not None:
            install_git_hooks(project_root, git_root, layout, config)
        result = verify_bundle(project_root)
    except Exception:
        restore_files(file_snapshot)
        if git_root is not None and git_snapshot is not None:
            restore_git_config(git_root, git_snapshot)
        for path in key_outputs:
            if path.suffix == ".key" and path.is_file():
                restrict_private_key(path)
        cleanup_created_keys(created_keys)
        raise
    if created_keys:
        atexit.unregister(cleanup_created_keys)
    return {**result, "plan_hash": approved_hash, "provider_server_rules": "not-applied", "hosts": provider_state_value["hosts"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "apply", "rotate-plan", "rotate"):
        item = sub.add_parser(name)
        item.add_argument("--project-root", required=True)
        item.add_argument("--config", required=True)
        if name in {"apply", "rotate"}:
            item.add_argument("--approve-plan-hash", required=True)
            item.add_argument("--provider-admin-evidence")
            item.add_argument("--admin-key")
            item.add_argument("--codex-key-dir")
            item.add_argument("--claude-key-dir")
    for name in ("remove-plan", "remove"):
        item = sub.add_parser(name)
        item.add_argument("--project-root", required=True)
        item.add_argument("--delete-keys", action="store_true")
        if name == "remove":
            item.add_argument("--approve-plan-hash", required=True)
            item.add_argument("--admin-key")
            item.add_argument("--codex-key-dir")
            item.add_argument("--claude-key-dir")
    verify = sub.add_parser("verify")
    verify.add_argument("--project-root", required=True)
    args = parser.parse_args()

    try:
        project_root = Path(args.project_root).resolve()
        if args.command == "verify":
            result = verify_bundle(project_root)
        elif args.command == "remove-plan":
            result = make_remove_plan(project_root, args.delete_keys)
        elif args.command == "remove":
            policy = json.loads((project_root / ".docs" / "harness" / "access-control" / "policy.json").read_text(encoding="utf-8"))
            codex_dir = Path(args.codex_key_dir).resolve() if args.codex_key_dir else Path.home() / ".codex" / "harness-kit" / "admin-keys"
            claude_dir = Path(args.claude_key_dir).resolve() if args.claude_key_dir else Path.home() / ".claude" / "harness-kit" / "admin-keys"
            backup = Path(args.admin_key).resolve() if args.admin_key else None
            result = remove_access_control(project_root, args.approve_plan_hash, codex_dir, claude_dir, backup, args.delete_keys)
        else:
            config = load_config(Path(args.config).resolve())
            if args.command in {"plan", "rotate-plan"}:
                result = make_plan(project_root, config, "rotate" if args.command == "rotate-plan" else "apply")
            else:
                codex_dir = Path(args.codex_key_dir).resolve() if args.codex_key_dir else Path.home() / ".codex" / "harness-kit" / "admin-keys"
                claude_dir = Path(args.claude_key_dir).resolve() if args.claude_key_dir else Path.home() / ".claude" / "harness-kit" / "admin-keys"
                backup = Path(args.admin_key).resolve() if args.admin_key else None
                result = apply(project_root, config, args.approve_plan_hash, codex_dir, claude_dir, backup, args.provider_admin_evidence, args.command == "rotate")
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (AccessError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
