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
SCHEMA_VERSION = "3.0.0"
DOCS_ROOT_NAME = ".ai-docs"
LEGACY_DOCS_ROOT_NAME = ".docs"
LEGACY_POLICY_SCHEMA_VERSIONS = {"1.1.0", "2.0.0"}
ROLES = {"admin", "pm-pl", "app-doc-lead", "developer"}
WRITE_SCOPES = {"admin", "app-doc", "team"}
PROVIDERS = ("github", "gitlab", "gitea")
PROVIDER_DEFAULT_HOSTS = {
    "github": "github.com",
    "gitlab": "gitlab.com",
    "gitea": "gitea.com",
}
GIT_SCOPED_ACCOUNT_KEYS = (
    "harness.gitScopedAccount.projectRoot",
    "harness.gitScopedAccount.configPath",
    "harness.gitScopedAccount.provider",
    "harness.gitScopedAccount.host",
    "harness.gitScopedAccount.account",
)
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

    subjects = raw.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        raise AccessError("subjects must contain at least one person or service-account entry")
    subject_ids: set[str] = set()
    provider_accounts: set[tuple[str, str, str]] = set()
    for subject in subjects:
        subject_id = str(subject.get("id", ""))
        if not SAFE_ID.fullmatch(subject_id) or subject_id in subject_ids:
            raise AccessError("subject ids must be unique safe identifiers")
        subject_ids.add(subject_id)
        accounts = subject.get("accounts")
        if not isinstance(accounts, list) or not accounts:
            raise AccessError(f"subject {subject_id} requires at least one provider account")
        for account in accounts:
            if not isinstance(account, dict):
                raise AccessError(f"provider accounts for {subject_id} must be objects")
            provider = str(account.get("provider", ""))
            host = str(account.get("host") or PROVIDER_DEFAULT_HOSTS.get(provider, "")).casefold()
            login = str(account.get("login", ""))
            account_id = account.get("account_id")
            if provider not in PROVIDERS:
                raise AccessError(f"unsupported provider account for {subject_id}: {provider}")
            if not re.fullmatch(r"[A-Za-z0-9.-]+(?::[0-9]{1,5})?", host):
                raise AccessError(f"invalid provider host for {subject_id}: {host}")
            if not re.fullmatch(r"@[A-Za-z0-9_.-]+", login):
                raise AccessError(f"invalid individual {provider} login for {subject_id}: {login}")
            if account_id is not None and (not isinstance(account_id, (str, int)) or not str(account_id).strip()):
                raise AccessError(f"invalid immutable account_id for {subject_id}: {account_id}")
            account["host"] = host
            if account_id is not None:
                account["account_id"] = str(account_id)
            account_key = (provider, host, str(account_id).casefold() if account_id is not None else login.casefold())
            if account_key in provider_accounts:
                raise AccessError(f"provider account is assigned to more than one subject: {provider}@{host}:{login}")
            provider_accounts.add(account_key)

    assignments = raw.get("role_assignments")
    if not isinstance(assignments, list) or not assignments:
        raise AccessError("role_assignments must contain at least one entry")
    assignment_keys: set[tuple[str, str]] = set()
    admin_subjects: set[str] = set()
    for assignment in assignments:
        if not isinstance(assignment, dict):
            raise AccessError("role assignments must be objects")
        subject_id = str(assignment.get("subject_id", ""))
        role = str(assignment.get("role", ""))
        if subject_id not in subject_ids:
            raise AccessError(f"role assignment references an unknown subject: {subject_id}")
        if role not in ROLES:
            raise AccessError(f"unsupported role for {subject_id}: {role}")
        key = (subject_id, role)
        if key in assignment_keys:
            raise AccessError(f"duplicate role assignment: {subject_id}/{role}")
        assignment_keys.add(key)
        scoped_applications = assignment.get("applications")
        if role == "app-doc-lead":
            if (
                not isinstance(scoped_applications, list)
                or not scoped_applications
                or any(not isinstance(app, str) for app in scoped_applications)
                or len(set(scoped_applications)) != len(scoped_applications)
                or any(app not in applications for app in scoped_applications)
            ):
                raise AccessError(
                    f"app-doc-lead {subject_id} requires unique applications from the configured application list"
                )
        elif scoped_applications is not None:
            raise AccessError(f"applications may be assigned only to app-doc-lead: {subject_id}/{role}")
        if role == "admin":
            admin_subjects.add(subject_id)
    if not admin_subjects:
        raise AccessError("at least one subject must have an explicit admin role assignment")

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
            if not isinstance(pattern, str) or not (pattern.startswith(".ai-docs/") or pattern in allowed_control_paths):
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
    repository_ids: set[str] = set()
    for repo in repositories:
        if not isinstance(repo, dict):
            raise AccessError("repository entries must be objects")
        repository_id = str(repo.get("id", ""))
        if not SAFE_ID.fullmatch(repository_id) or repository_id in repository_ids:
            raise AccessError("repository ids must be unique safe identifiers")
        repository_ids.add(repository_id)
        if repo.get("provider") not in PROVIDERS:
            raise AccessError("repository provider must be github, gitlab, or gitea")
        provider = str(repo["provider"])
        host = str(repo.get("host") or PROVIDER_DEFAULT_HOSTS[provider]).casefold()
        if not re.fullmatch(r"[A-Za-z0-9.-]+(?::[0-9]{1,5})?", host):
            raise AccessError(f"invalid repository provider host: {host}")
        repo["host"] = host
        owner = str(repo.get("owner", ""))
        name = str(repo.get("name", ""))
        if not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise AccessError(f"repository {repository_id} requires a safe owner/namespace and name")
        purpose = str(repo.get("purpose", "source"))
        if purpose not in {"docs", "source"}:
            raise AccessError(f"repository {repository_id} purpose must be docs or source")
        repo["purpose"] = purpose
        scoped_apps = repo.get("applications", [])
        if not isinstance(scoped_apps, list) or len(set(scoped_apps)) != len(scoped_apps) or any(app not in applications for app in scoped_apps):
            raise AccessError(f"repository {repository_id} applications must come from the configured application list")
        branches = repo.get("protected_branches", [])
        if not isinstance(branches, list) or any(not isinstance(item, str) or not item.strip() for item in branches):
            raise AccessError("protected_branches must be an array of non-empty strings")
        if repo.get("server_policy", "externally-approved") not in {"externally-approved", "none"}:
            raise AccessError("server_policy must be externally-approved or none")
        cli_login = repo.get("cli_login")
        if cli_login is not None and (not isinstance(cli_login, str) or not SAFE_ID.fullmatch(cli_login)):
            raise AccessError(f"repository {repository_id} cli_login must be a safe CLI profile name")

    local_identity = raw.get("local_identity")
    if not isinstance(local_identity, dict) or local_identity.get("provider") not in PROVIDERS:
        raise AccessError("local_identity with a supported provider is required")
    if not isinstance(local_identity.get("account"), str) or not re.fullmatch(r"@[A-Za-z0-9_.-]+", local_identity["account"]):
        raise AccessError("local_identity account must be an individual @login")
    provider = str(local_identity["provider"])
    local_identity.setdefault("host", PROVIDER_DEFAULT_HOSTS[provider])
    local_identity["host"] = str(local_identity["host"]).casefold()
    if not re.fullmatch(r"[A-Za-z0-9.-]+(?::[0-9]{1,5})?", local_identity["host"]):
        raise AccessError("local_identity host is invalid")
    identity_key = (provider, local_identity["host"], local_identity["account"].casefold())
    if not any(
        account["provider"] == identity_key[0]
        and account["host"] == identity_key[1]
        and account["login"].casefold() == identity_key[2]
        for subject in subjects
        for account in subject["accounts"]
    ):
        raise AccessError("local_identity must match a configured subject account")

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
    docs_root = project_root / DOCS_ROOT_NAME
    legacy_docs_root = project_root / LEGACY_DOCS_ROOT_NAME
    if docs_root.exists() and legacy_docs_root.exists():
        raise AccessError(
            ".ai-docs and legacy .docs both exist; resolve the document-root conflict with harness-setup before configuring access"
        )
    if legacy_docs_root.exists():
        legacy_policy = legacy_docs_root / "harness" / "access-control" / "policy.json"
        if legacy_policy.is_file():
            raise AccessError(
                "legacy .docs contains a signed access policy; use migrate-root-plan and migrate-root"
            )
        raise AccessError(
            "legacy .docs exists without .ai-docs; run the explicit harness-setup document-root migration before configuring access"
        )
    if docs_root.is_dir() and is_git_root(docs_root):
        git_root = docs_root
        git_root_relative = DOCS_ROOT_NAME
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


def detect_legacy_layout(project_root: Path) -> dict[str, Any]:
    """Describe the current Git boundary before an explicit .docs migration."""
    docs_root = project_root / DOCS_ROOT_NAME
    legacy_docs_root = project_root / LEGACY_DOCS_ROOT_NAME
    if docs_root.exists() and legacy_docs_root.exists():
        raise AccessError(".ai-docs and legacy .docs both exist; automatic merge is not supported")
    if docs_root.exists():
        raise AccessError(".ai-docs already exists; document-root migration is not applicable")
    if not legacy_docs_root.is_dir():
        raise AccessError("legacy .docs is missing; document-root migration is not applicable")
    if is_git_root(legacy_docs_root):
        git_root = legacy_docs_root
        topology = "multi-repository"
        post_git_root_relative = DOCS_ROOT_NAME
    elif is_git_root(project_root):
        git_root = project_root
        topology = "single-repository"
        post_git_root_relative = "."
    else:
        git_root = None
        topology = "local-only"
        post_git_root_relative = "."
    return {
        "topology": topology,
        "git_root": git_root,
        "git_root_relative": post_git_root_relative,
        "root_context_tracked": topology == "single-repository",
    }


def path_rules(config: dict[str, Any], layout: dict[str, Any]) -> list[dict[str, Any]]:
    docs = DOCS_ROOT_NAME
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
    subjects = copy.deepcopy(config["subjects"])
    for subject in subjects:
        subject["accounts"] = sorted(
            subject["accounts"],
            key=lambda item: (item["provider"], item["host"], str(item.get("account_id", "")), item["login"].casefold()),
        )
    assignments = copy.deepcopy(config["role_assignments"])
    for assignment in assignments:
        if "applications" in assignment:
            assignment["applications"] = sorted(assignment["applications"])
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": config["project_id"],
        "topology": layout["topology"],
        "git_root_relative": layout["git_root_relative"],
        "root_context_tracked": layout["root_context_tracked"],
        "remote_verification": remote_verification,
        "authorization_model": {
            "role_mode": "explicit-capabilities-no-inheritance",
            "app_scoped_role": "app-doc-lead",
            "team_access_mode": "repository-writers",
            "unregistered_team_write": True,
            "app_doc_ai_confirmation": "required-for-authorized-writes",
            "source_code_protection": "out-of-scope",
        },
        "applications": sorted(config["applications"]),
        "subjects": sorted(subjects, key=lambda item: item["id"]),
        "role_assignments": sorted(
            assignments,
            key=lambda item: (item["subject_id"], item["role"]),
        ),
        "path_rules": path_rules(config, layout),
        "repositories": sorted(copy.deepcopy(config["repositories"]), key=lambda item: item["id"]),
    }


def assignments_for(policy: dict[str, Any], subject_id: str) -> list[dict[str, Any]]:
    return [
        assignment
        for assignment in policy.get("role_assignments", [])
        if assignment.get("subject_id") == subject_id
    ]


def subject_has_role(policy: dict[str, Any], subject_id: str, role: str, application: str | None = None) -> bool:
    for assignment in assignments_for(policy, subject_id):
        if assignment.get("role") != role:
            continue
        if role != "app-doc-lead" or application in assignment.get("applications", []):
            return True
    return False


def subject_for_account(policy: dict[str, Any], provider: str, host: str, login: str) -> dict[str, Any] | None:
    wanted = (provider, host.casefold(), login.casefold())
    for subject in policy.get("subjects", []):
        for account in subject.get("accounts", []):
            actual = (str(account.get("provider", "")), str(account.get("host", "")).casefold(), str(account.get("login", "")).casefold())
            if actual == wanted:
                return subject
    return None


def legacy_admin_id_for_account(
    policy: dict[str, Any],
    provider: str,
    host: str,
    login: str,
) -> str | None:
    """Resolve one legacy admin while preserving each schema's identity boundary."""
    schema_version = policy.get("schema_version")
    if schema_version == "1.1.0":
        matches = [
            str(principal.get("id", ""))
            for principal in policy.get("principals", [])
            if principal.get("role") == "admin"
            and isinstance(principal.get("accounts"), dict)
            and str(principal["accounts"].get(provider, "")).casefold() == login.casefold()
        ]
        return matches[0] if len(matches) == 1 and matches[0] else None
    if schema_version == "2.0.0":
        subject = subject_for_account(policy, provider, host, login)
        if subject is not None and subject_has_role(policy, subject["id"], "admin"):
            return str(subject["id"])
    return None


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
    for subject in policy["subjects"]:
        subject_id = subject["id"]
        if write_scope == "admin" and not subject_has_role(policy, subject_id, "admin"):
            continue
        if write_scope == "app-doc" and not (
            subject_has_role(policy, subject_id, "pm-pl")
            or subject_has_role(policy, subject_id, "app-doc-lead", application)
        ):
            continue
        result.extend(
            account["login"]
            for account in subject.get("accounts", [])
            if account.get("provider") == provider
        )
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
        if rule["pattern"] == ".ai-docs/**" and rule["write_scope"] == "admin":
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


def instruction_targets(project_root: Path) -> list[Path]:
    """Return only session-entry maps that must point at the signed access instruction."""
    targets: list[Path] = []
    for root_file in (project_root / "AGENTS.md", project_root / "CLAUDE.md"):
        if root_file.is_file():
            targets.append(root_file)
    return targets


def render_instruction_block(policy_core_hash: str) -> str:
    start, end = INSTRUCTION_MARKERS
    return "\n".join(
        [
            start,
            "## 문서 쓰기 권한 확인",
            "",
            f"- 정책: `@.ai-docs/harness/access-control/policy.json` (`{policy_core_hash}`)",
            "- 쓰기 전에 `@.ai-docs/harness/access-control/write-access-instruction.md`를 반드시 읽고 서명 정책과 현재 Git 계정을 확인한다.",
            "- 이 블록은 `project-write-access`만 갱신한다. 블록 밖의 설계·개발 지침은 원래 소유자가 관리한다.",
            end,
            "",
        ]
    )


def render_access_instruction(policy_core_hash: str) -> bytes:
    return (
        "# 프로젝트 문서 쓰기 권한\n\n"
        f"정본 정책은 `@.ai-docs/harness/access-control/policy.json`이며 현재 정책 본문 해시는 `{policy_core_hash}`다. "
        "이 파일과 정책은 `project-write-access`만 갱신한다.\n\n"
        "## 적용 원칙\n\n"
        "- 모든 참여자는 문서를 읽을 수 있다. 앱 소스 코드와 일반 개발 파일은 이 정책의 보호 대상이 아니다.\n"
        "- 역할은 상속하지 않는다. 한 사람이 여러 역할을 맡으려면 정책에 각 역할을 명시적으로 배정한다.\n"
        "- `admin`은 루트 컨텍스트, `.ai-docs/harness/`, CODEOWNERS와 권한 설정만 관리한다.\n"
        "- `pm-pl`은 모든 앱의 `DESIGN.md`, `*-context.md`, `*-instruction.md`를 관리한다.\n"
        "- `app-doc-lead`는 배정된 앱에서만 같은 종류의 핵심 문서를 관리한다.\n"
        "- `developer`는 일반 기여자임을 명시하는 표기다. 이 역할이 없거나 등록되지 않은 저장소 작성자도 `team` 범위의 구현 지침, 프로토타입, 임시 입력 문서를 쓸 수 있다.\n"
        "- 신원, 프로젝트, 앱 또는 경로를 확정할 수 없거나 권한이 부족하면 직접 쓰지 않고 문서 소유자에게 변경안을 제안한다.\n\n"
        "## 앱 핵심 문서 AI 편집 확인\n\n"
        "권한이 있는 `pm-pl` 또는 해당 앱의 `app-doc-lead`라도 AI가 앱 핵심 문서를 만들거나 고치기 직전에 다음 정보를 보여주고 이 변경에 한해 명시적 승인을 받아야 한다. "
        "스킬이 자동으로 `design-doc` 또는 `context-doc`을 선택한 경우에도 생략하지 않는다.\n\n"
        "1. 대상 앱과 정확한 파일 경로\n"
        "2. 문서 종류와 역할: `DESIGN.md`는 설계 기준, `*-context.md`는 앱의 기술·설계 맥락, `*-instruction.md`는 해당 주제 작업 규칙\n"
        "3. 만들거나 바꿀 내용의 요약과 변경 이유\n"
        "4. 현재 Git 계정에 적용된 역할과 앱 범위\n\n"
        "승인은 다른 파일이나 후속 변경에 재사용하지 않는다. guard의 `check-path`가 `decision=confirm`을 반환하거나 "
        "PreToolUse가 `permissionDecision=ask`를 반환하면 반드시 사용자에게 확인한다.\n"
    ).encode("utf-8")


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
                "${CLAUDE_PROJECT_DIR}/.ai-docs/harness/access-control/hooks/write_access_guard.py",
                "ai",
                "--host",
                "claude",
                "--project-root",
                "${CLAUDE_PROJECT_DIR}",
            ],
        }
        matcher = "Write|Edit|Bash|PowerShell"
    else:
        guard = project_root / ".ai-docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
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


PERMISSION_RANK = {
    "none": 0,
    "guest": 5,
    "pull": 10,
    "read": 10,
    "reporter": 10,
    "triage": 15,
    "push": 20,
    "write": 20,
    "developer": 20,
    "maintain": 30,
    "maintainer": 30,
    "admin": 40,
    "owner": 40,
}


def quote_component(value: str) -> str:
    safe = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    return "".join(chr(byte) if byte in safe else f"%{byte:02X}" for byte in value.encode("utf-8"))


def cli_api_json(provider: str, repo: dict[str, Any], endpoint: str) -> Any:
    executable = {"github": "gh", "gitlab": "glab", "gitea": "tea"}[provider]
    if shutil.which(executable) is None:
        raise AccessError(f"{provider} participant discovery requires the authenticated {executable} CLI")
    if provider == "github":
        command = ["gh", "api", endpoint, "--hostname", repo["host"]]
    elif provider == "gitlab":
        command = ["glab", "api", endpoint, "--hostname", repo["host"]]
    else:
        cli_login = repo.get("cli_login")
        if not cli_login:
            raise AccessError("gitea participant discovery requires repository cli_login for an authenticated tea profile")
        command = ["tea", "--login", str(cli_login), "api", endpoint]
    result = run(command, check=False)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()[:300]
        raise AccessError(f"{provider} CLI API request failed: {detail or 'no error detail'}")
    try:
        return json.loads(result.stdout.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AccessError(f"{provider} CLI returned malformed JSON") from exc


def paged_cli_api(provider: str, repo: dict[str, Any], endpoint: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    page = 1
    while True:
        separator = "&" if "?" in endpoint else "?"
        page_endpoint = f"{endpoint}{separator}per_page=100&page={page}"
        payload = cli_api_json(provider, repo, page_endpoint)
        if not isinstance(payload, list):
            raise AccessError("participant API response must be an array")
        records.extend(item for item in payload if isinstance(item, dict))
        if len(payload) < 100:
            break
        page += 1
    return records


def permission_name(value: Any, provider: str) -> str:
    if provider == "gitlab":
        return {
            50: "owner",
            40: "maintainer",
            30: "developer",
            20: "reporter",
            10: "guest",
        }.get(int(value or 0), "none")
    text = str(value or "none").casefold()
    return text if text in PERMISSION_RANK else "none"


def merge_participant_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in records:
        provider = str(record["provider"])
        host = str(record["host"]).casefold()
        account_id = str(record.get("account_id") or "")
        login = str(record["login"])
        key = (provider, host, account_id or login.casefold())
        current = merged.setdefault(
            key,
            {
                "provider": provider,
                "host": host,
                "account_id": account_id or None,
                "login": login,
                "display_name": record.get("display_name") or login.lstrip("@"),
                "account_type": record.get("account_type", "user"),
                "active": bool(record.get("active", True)),
                "max_permission": "none",
                "repositories": [],
            },
        )
        permission = permission_name(record.get("permission"), provider)
        if PERMISSION_RANK[permission] > PERMISSION_RANK[current["max_permission"]]:
            current["max_permission"] = permission
        repository = {
            "id": record["repository_id"],
            "permission": permission,
            "source": record.get("source", "direct"),
        }
        if repository not in current["repositories"]:
            current["repositories"].append(repository)
        current["active"] = current["active"] and bool(record.get("active", True))
    for participant in merged.values():
        participant["repositories"] = sorted(
            participant["repositories"], key=lambda item: (item["id"], item["source"], item["permission"])
        )
    return sorted(merged.values(), key=lambda item: (item["provider"], item["host"], item["login"].casefold()))


def discover_repository_participants(repo: dict[str, Any]) -> list[dict[str, Any]]:
    provider = repo["provider"]
    owner = quote_component(str(repo["owner"]))
    name = quote_component(str(repo["name"]))
    records: list[dict[str, Any]] = []

    def add(account: dict[str, Any], permission: Any, source: str) -> None:
        login = str(account.get("login") or account.get("username") or "")
        if not login:
            return
        records.append(
            {
                "provider": provider,
                "host": repo["host"],
                "account_id": account.get("id"),
                "login": "@" + login.lstrip("@"),
                "display_name": account.get("name") or account.get("full_name") or login,
                "account_type": str(account.get("type") or ("bot" if login.endswith("[bot]") else "user")).casefold(),
                "active": str(account.get("state", "active")).casefold() not in {"blocked", "inactive", "deactivated"},
                "permission": permission,
                "repository_id": repo["id"],
                "source": source,
            }
        )

    if provider == "github":
        collaborators = paged_cli_api(provider, repo, f"repos/{owner}/{name}/collaborators?affiliation=all")
        for item in collaborators:
            permission = item.get("role_name")
            if not permission:
                permissions = item.get("permissions", {})
                permission = next((key for key in ("admin", "maintain", "push", "triage", "pull") if permissions.get(key)), "none")
            add(item, permission, "effective-collaborator")
    elif provider == "gitlab":
        project = quote_component(f"{repo['owner']}/{repo['name']}")
        members = paged_cli_api(provider, repo, f"projects/{project}/members/all")
        for item in members:
            add(item, item.get("access_level"), "effective-member")
    else:
        collaborators = paged_cli_api(provider, repo, f"repos/{owner}/{name}/collaborators")
        for item in collaborators:
            login = str(item.get("login") or item.get("username") or "")
            permission_payload = cli_api_json(
                provider,
                repo,
                f"repos/{owner}/{name}/collaborators/{quote_component(login)}/permission",
            )
            permission = permission_payload.get("permission") if isinstance(permission_payload, dict) else "none"
            add(item, permission, "effective-collaborator")
        teams = paged_cli_api(provider, repo, f"repos/{owner}/{name}/teams")
        for team in teams:
            team_id = team.get("id")
            if team_id is None:
                continue
            members = paged_cli_api(provider, repo, f"teams/{team_id}/members")
            for item in members:
                add(item, team.get("permission", "none"), f"team:{team_id}")
    return records


def discover_participants(config: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for repo in config["repositories"]:
        try:
            records.extend(discover_repository_participants(repo))
        except AccessError as exc:
            errors.append({"repository_id": repo["id"], "message": str(exc)})
    status = "complete" if not errors else ("partial" if records else "failed")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "repositories_checked": [repo["id"] for repo in config["repositories"]],
        "participants": merge_participant_records(records),
        "errors": errors,
        "selection_required": "admin must explicitly assign roles; discovery never grants a role",
    }


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


def one_local_git_value(git_root: Path, key: str) -> str:
    result = git(git_root, "config", "--local", "--get-all", key, check=False)
    values = result.stdout.decode().splitlines() if result.returncode == 0 else []
    if len(values) != 1 or not values[0].strip():
        raise AccessError(f"git-scoped-account local setting is missing or duplicated: {key}")
    return values[0].strip()


def normalized_config_origin(value: str) -> str:
    raw = value.removeprefix("file:").strip().replace("\\", "/")
    return raw.casefold()


def require_git_scoped_identity(project_root: Path, git_root: Path) -> dict[str, str]:
    values = {key: one_local_git_value(git_root, key) for key in GIT_SCOPED_ACCOUNT_KEYS}
    registered_root = Path(values["harness.gitScopedAccount.projectRoot"]).resolve()
    if registered_root != project_root.resolve():
        raise AccessError("git-scoped-account project root does not match this project")

    config_path = values["harness.gitScopedAccount.configPath"].replace("\\", "/")
    included = git(
        git_root,
        "config",
        "--local",
        "--fixed-value",
        "--get-all",
        "include.path",
        config_path,
        check=False,
    )
    if included.returncode != 0 or included.stdout.decode().splitlines() != [config_path]:
        raise AccessError("git-scoped-account shared config is not included exactly once")
    for key in ("user.name", "user.email"):
        origin = git(git_root, "config", "--show-origin", "--get", key, check=False)
        if origin.returncode != 0:
            raise AccessError(f"git-scoped-account did not provide {key}")
        source = origin.stdout.decode(errors="replace").split(maxsplit=1)[0]
        if normalized_config_origin(source) != normalized_config_origin(config_path):
            raise AccessError(f"{key} is not sourced from the git-scoped-account shared config")

    provider = values["harness.gitScopedAccount.provider"]
    host = values["harness.gitScopedAccount.host"].casefold()
    account = values["harness.gitScopedAccount.account"]
    if provider not in PROVIDERS:
        raise AccessError("git-scoped-account provider is unsupported")
    if not re.fullmatch(r"[A-Za-z0-9.-]+(?::[0-9]{1,5})?", host):
        raise AccessError("git-scoped-account provider host is invalid")
    if not re.fullmatch(r"@[A-Za-z0-9_.-]+", account):
        raise AccessError("git-scoped-account provider account is invalid")
    return {
        "project_root": str(project_root.resolve()),
        "config_path": config_path,
        "provider": provider,
        "host": host,
        "account": account,
    }


def git_scoped_plan_state(project_root: Path, git_root: Path | None, expected: dict[str, Any] | None = None) -> dict[str, Any]:
    if git_root is None:
        return {"status": "required", "message": "Git boundary is unavailable"}
    try:
        identity = require_git_scoped_identity(project_root, git_root)
        if expected is not None and (
            identity["provider"],
            identity["host"],
            identity["account"].casefold(),
        ) != (
            expected["provider"],
            str(expected["host"]).casefold(),
            str(expected["account"]).casefold(),
        ):
            raise AccessError("git-scoped-account identity does not match config local_identity")
        return {"status": "ready", **identity}
    except AccessError as exc:
        return {"status": "required", "message": str(exc)}


def make_plan(project_root: Path, config: dict[str, Any], operation: str = "apply") -> dict[str, Any]:
    layout = detect_layout(project_root)
    state = preflight(layout)
    remote_verification = "pending" if state["remote"] else "local-only"
    policy_core = build_policy_core(config, layout, remote_verification)
    policy_core_hash = sha256_bytes(canonical_json(policy_core))
    changes: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []
    git_root: Path | None = layout["git_root"]
    scoped_state = git_scoped_plan_state(project_root, git_root, config["local_identity"])
    if scoped_state["status"] != "ready":
        conflicts.append({"provider": "local-git", "type": "git-scoped-account-required", "path": ".git/config"})
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
        conflicts.append({"provider": "all", "type": "no-git-repository", "path": ".ai-docs"})

    block = render_instruction_block(policy_core_hash)
    desired_instruction_targets = instruction_targets(project_root)
    for target in desired_instruction_targets:
        desired = replace_managed_block(read_optional(target), block, INSTRUCTION_MARKERS)
        current = read_optional(target)
        changes.append({"path": relative(project_root, target), "action": "unchanged" if current == desired else ("create" if current is None else "modify")})
    for target, reduced in stale_instruction_outputs(project_root, desired_instruction_targets).items():
        changes.append({"path": relative(project_root, target), "action": "delete" if reduced is None else "modify"})

    access_dir = project_root / ".ai-docs" / "harness" / "access-control"
    for name in ("trust.json", "policy.json", "policy.sig", "provider-state.json", "generated-manifest.json", "write-access-instruction.md", "hooks/write_access_guard.py", "hooks/git/pre-commit", "hooks/git/pre-push"):
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
        "git_scoped_account": scoped_state,
        "participant_discovery": "required-before-role-change" if config["repositories"] else "not-applicable",
    }
    return {
        **plan_basis,
        "preflight": state,
        "plan_hash": sha256_bytes(canonical_json(plan_basis)),
        "server_changes": [
            {
                "provider": repo["provider"],
                "repository_id": repo["id"],
                "host": repo["host"],
                "repository": f"{repo['owner']}/{repo['name']}",
                "purpose": repo["purpose"],
                "protected_branches": repo.get("protected_branches", []),
                "status": (
                    "externally-managed-not-applied-by-skill"
                    if repo["purpose"] == "docs" and repo.get("server_policy") != "none"
                    else "not-configured"
                ),
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
    for provider in PROVIDERS:
        target = targets.get(provider)
        shadow = provider_shadow(git_root, provider, target) if git_root is not None and target is not None else None
        repositories = [
            {
                "id": item["id"],
                "host": item["host"],
                "repository": f"{item['owner']}/{item['name']}",
                "purpose": item["purpose"],
                "applications": item.get("applications", []),
                "protected_branches": item.get("protected_branches", []),
                "server_policy": item.get("server_policy", "externally-approved"),
            }
            for item in config["repositories"]
            if item["provider"] == provider
        ]
        states[provider] = {
            "codeowners": relative(Path(config["_project_root"]), target) if target is not None else None,
            "shadowed_by": shadow,
            "codeowners_status": "shadowed" if shadow else ("generated" if target is not None else "unavailable"),
            "server_rules_status": "external-not-queried-or-changed",
            "repositories": repositories,
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
    "harness.writeAccess.host",
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


def install_git_hooks(
    project_root: Path,
    git_root: Path,
    layout: dict[str, Any],
    config: dict[str, Any],
    *,
    legacy_root_migration: bool = False,
) -> None:
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
    ours_relative = ".ai-docs/harness/access-control/hooks/git" if layout["git_root_relative"] == "." else "harness/access-control/hooks/git"
    previous_hooks: dict[str, str] = {}
    if hook_path.resolve() != (git_root / ours_relative).resolve():
        for name in ("pre-commit", "pre-push"):
            candidate = hook_path / name
            if candidate.is_file():
                previous_hooks[name] = str(candidate.resolve())
    ours_path = (git_root / ours_relative).resolve()
    legacy_relative = ".docs/harness/access-control/hooks/git" if layout["git_root_relative"] == "." else ours_relative
    legacy_path = (git_root / legacy_relative).resolve()
    reusing_managed_state = hook_path.resolve() == ours_path or (
        legacy_root_migration and hook_path.resolve() == legacy_path
    )
    if reusing_managed_state and state_path.is_file():
        local_state = json.loads(state_path.read_text(encoding="utf-8"))
        local_state["schema_version"] = SCHEMA_VERSION
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
        git(git_root, "config", "--local", "--replace-all", "harness.writeAccess.host", identity["host"])
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


def resolve_manifest_path(project_root: Path, raw_path: str, manifest_root_name: str, actual_root_name: str) -> Path:
    parts = Path(raw_path).parts
    if not parts or Path(raw_path).is_absolute() or ".." in parts:
        raise AccessError(f"generated-manifest path escapes project root: {raw_path}")
    if parts[0] == manifest_root_name and manifest_root_name != actual_root_name:
        parts = (actual_root_name, *parts[1:])
    path = (project_root / Path(*parts)).resolve()
    try:
        path.relative_to(project_root.resolve())
    except ValueError as exc:
        raise AccessError(f"generated-manifest path escapes project root: {raw_path}") from exc
    return path


def verify_bundle_at(
    project_root: Path,
    docs_root_name: str,
    *,
    manifest_root_name: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    access_dir = project_root / docs_root_name / "harness" / "access-control"
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
    source_root = manifest_root_name or docs_root_name
    for entry in manifest.get("files", []):
        path = resolve_manifest_path(project_root, entry["path"], source_root, docs_root_name)
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
    summary = {
        "status": "valid",
        "project_id": policy["project_id"],
        "policy_core_sha256": declared_core,
        "files": len(manifest.get("files", [])),
        "schema_version": policy.get("schema_version"),
        "document_root": docs_root_name,
    }
    return summary, policy, manifest


def verify_bundle(project_root: Path) -> dict[str, Any]:
    summary, _policy, _manifest = verify_bundle_at(project_root, DOCS_ROOT_NAME)
    return summary


def make_local_enrollment_plan(project_root: Path) -> dict[str, Any]:
    verified, policy, _manifest = verify_bundle_at(project_root, DOCS_ROOT_NAME)
    layout = detect_layout(project_root)
    git_root: Path | None = layout["git_root"]
    if git_root is None:
        raise AccessError("local enrollment requires the Git boundary that tracks .ai-docs")
    identity = require_git_scoped_identity(project_root, git_root)
    subject = subject_for_account(policy, identity["provider"], identity["host"], identity["account"])
    roles = sorted(
        assignment["role"]
        for assignment in policy.get("role_assignments", [])
        if subject is not None and assignment.get("subject_id") == subject.get("id")
    )
    ours_relative = ".ai-docs/harness/access-control/hooks/git" if layout["git_root_relative"] == "." else "harness/access-control/hooks/git"
    basis = {
        "schema_version": SCHEMA_VERSION,
        "operation": "local-enroll",
        "project_root": str(project_root.resolve()),
        "project_id": policy["project_id"],
        "policy_core_sha256": verified["policy_core_sha256"],
        "git_root_relative": layout["git_root_relative"],
        "identity": identity,
        "subject_id": subject.get("id") if subject is not None else None,
        "roles": roles,
        "changes": [
            {"path": ".git/config", "action": "connect-local-identity-and-hooks"},
            {"path": str(git_local_state_path(git_root)), "action": "record-previous-hooks"},
        ],
        "core_hooks_path": ours_relative,
        "shared_policy_changes": "none",
        "provider_server_rules": "externally-managed-not-applied-by-skill",
    }
    return {**basis, "plan_hash": sha256_bytes(canonical_json(basis))}


def apply_local_enrollment(project_root: Path, approved_hash: str) -> dict[str, Any]:
    plan = make_local_enrollment_plan(project_root)
    if plan["plan_hash"] != approved_hash:
        raise AccessError("approved local enrollment plan hash does not match the current plan")
    layout = detect_layout(project_root)
    git_root: Path | None = layout["git_root"]
    if git_root is None:
        raise AccessError("local enrollment requires the Git boundary that tracks .ai-docs")
    state_path = git_local_state_path(git_root)
    file_snapshot = snapshot([state_path])
    git_snapshot = git_config_values(git_root)
    config = {
        "local_identity": {
            "provider": plan["identity"]["provider"],
            "host": plan["identity"]["host"],
            "account": plan["identity"]["account"],
        }
    }
    try:
        install_git_hooks(project_root, git_root, layout, config)
        actual = {
            "project_root": one_local_git_value(git_root, "harness.writeAccess.projectRoot"),
            "provider": one_local_git_value(git_root, "harness.writeAccess.provider"),
            "host": one_local_git_value(git_root, "harness.writeAccess.host").casefold(),
            "account": one_local_git_value(git_root, "harness.writeAccess.account"),
            "core_hooks_path": one_local_git_value(git_root, "core.hooksPath"),
        }
        expected = {
            "project_root": str(project_root.resolve()),
            "provider": plan["identity"]["provider"],
            "host": plan["identity"]["host"],
            "account": plan["identity"]["account"],
            "core_hooks_path": plan["core_hooks_path"],
        }
        if actual != expected:
            raise AccessError("local enrollment verification failed")
        verify_bundle(project_root)
    except Exception:
        restore_files(file_snapshot)
        restore_git_config(git_root, git_snapshot)
        raise
    return {
        "status": "enrolled",
        "project_id": plan["project_id"],
        "subject_id": plan["subject_id"],
        "roles": plan["roles"],
        "identity": plan["identity"],
        "shared_policy_changes": "none",
        "provider_server_rules": "externally-managed-not-applied-by-skill",
    }


def remove_managed_block(content: bytes, markers: tuple[str, str]) -> bytes:
    text = content.decode("utf-8")
    start, end = markers
    if text.count(start) != 1 or text.count(end) != 1:
        raise AccessError("managed block is missing or malformed")
    left = text.index(start)
    right = text.index(end, left) + len(end)
    return (text[:left] + text[right:]).encode("utf-8")


def stale_instruction_outputs(
    project_root: Path,
    desired_targets: list[Path],
    manifest_root_name: str | None = None,
) -> dict[Path, bytes | None]:
    """Remove v1 blocks that were copied into every app instruction during a v2 migration."""
    manifest_path = project_root / ".ai-docs" / "harness" / "access-control" / "generated-manifest.json"
    if not manifest_path.is_file():
        return {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    desired = {path.resolve() for path in desired_targets}
    outputs: dict[Path, bytes | None] = {}
    for entry in manifest.get("files", []):
        if entry.get("mode") != "instruction-block":
            continue
        path = resolve_manifest_path(
            project_root,
            str(entry.get("path", "")),
            manifest_root_name or DOCS_ROOT_NAME,
            DOCS_ROOT_NAME,
        )
        if path in desired or not path.is_file():
            continue
        reduced = remove_managed_block(path.read_bytes(), INSTRUCTION_MARKERS)
        outputs[path] = reduced if reduced.strip() else None
    return outputs


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
    access_dir = project_root / ".ai-docs" / "harness" / "access-control"
    manifest = json.loads((access_dir / "generated-manifest.json").read_text(encoding="utf-8"))
    policy = json.loads((access_dir / "policy.json").read_text(encoding="utf-8"))
    paths = sorted({entry["path"] for entry in manifest["files"]} | {
        ".ai-docs/harness/access-control/policy.json",
        ".ai-docs/harness/access-control/policy.sig",
        ".ai-docs/harness/access-control/generated-manifest.json",
    })
    basis = {
        "schema_version": SCHEMA_VERSION,
        "operation": "remove",
        "project_root": str(project_root.resolve()),
        "project_id": policy["project_id"],
        "policy_core_sha256": verified["policy_core_sha256"],
        "managed_paths": paths,
        "delete_keys": delete_keys,
        "provider_server_rules": "externally-managed-not-applied-by-skill",
    }
    return {**basis, "plan_hash": sha256_bytes(canonical_json(basis))}


def remove_access_control(project_root: Path, approved_hash: str, codex_dir: Path, claude_dir: Path, backup_key: Path | None, delete_keys: bool) -> dict[str, Any]:
    plan = make_remove_plan(project_root, delete_keys)
    if plan["plan_hash"] != approved_hash:
        raise AccessError("approved removal plan hash does not match the current plan")
    access_dir = project_root / ".ai-docs" / "harness" / "access-control"
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
                ours = ".ai-docs/harness/access-control/hooks/git" if layout["git_root_relative"] == "." else "harness/access-control/hooks/git"
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
        "provider_server_rules": "externally-managed-not-applied-by-skill",
    }


def make_root_migration_plan(project_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    layout = detect_legacy_layout(project_root)
    verified, current_policy, manifest = verify_bundle_at(project_root, LEGACY_DOCS_ROOT_NAME)
    if current_policy.get("schema_version") not in LEGACY_POLICY_SCHEMA_VERSIONS:
        raise AccessError(
            f"unsupported legacy policy schema: {current_policy.get('schema_version')}"
        )
    if current_policy.get("project_id") != config["project_id"]:
        raise AccessError("migration config project_id does not match the signed legacy policy")

    state = preflight(layout)
    scoped_state = git_scoped_plan_state(project_root, layout["git_root"], config["local_identity"])
    remote_verification = "pending" if state["remote"] else "local-only"
    desired_policy_core = build_policy_core(config, layout, remote_verification)
    desired_policy_core_hash = sha256_bytes(canonical_json(desired_policy_core))
    managed_paths = sorted(
        {
            str(entry["path"]).replace(
                f"{LEGACY_DOCS_ROOT_NAME}/",
                f"{DOCS_ROOT_NAME}/",
                1,
            )
            for entry in manifest.get("files", [])
        }
    )
    changes = [
        {
            "path": f"{LEGACY_DOCS_ROOT_NAME}/ -> {DOCS_ROOT_NAME}/",
            "action": "rename-document-root",
        },
        *({"path": path, "action": "rebind-and-regenerate"} for path in managed_paths),
    ]
    legacy_schema_version = current_policy.get("schema_version")
    basis = {
        "schema_version": SCHEMA_VERSION,
        "operation": "migrate-document-root",
        "project_root": str(project_root.resolve()),
        "project_id": config["project_id"],
        "config": config,
        "topology": layout["topology"],
        "git_root_relative": layout["git_root_relative"],
        "legacy_policy_schema_version": legacy_schema_version,
        "legacy_admin_identity_binding": (
            "provider-login-and-admin-key"
            if legacy_schema_version == "1.1.0"
            else "provider-host-login-and-admin-key"
        ),
        "legacy_policy_core_sha256": verified["policy_core_sha256"],
        "policy_core_sha256": desired_policy_core_hash,
        "changes": changes,
        "git_scoped_account": scoped_state,
        "provider_server_rules": "externally-managed-not-applied-by-skill",
    }
    return {
        **basis,
        "preflight": state,
        "plan_hash": sha256_bytes(canonical_json(basis)),
        "server_changes": [
            {
                "provider": repo["provider"],
                "repository_id": repo["id"],
                "host": repo["host"],
                "repository": f"{repo['owner']}/{repo['name']}",
                "status": "not-requested-by-document-root-migration",
            }
            for repo in config["repositories"]
        ],
    }


def migrate_document_root(
    project_root: Path,
    config: dict[str, Any],
    approved_hash: str,
    codex_dir: Path,
    claude_dir: Path,
    backup_key: Path | None,
    evidence: str | None,
) -> dict[str, Any]:
    plan = make_root_migration_plan(project_root, config)
    if plan["plan_hash"] != approved_hash:
        raise AccessError("approved migration plan hash does not match the current plan")
    state = plan["preflight"]
    if state.get("dirty"):
        raise AccessError("Git worktree is not clean")
    if state.get("behind", 0) > 0 or (
        state.get("ahead", 0) > 0 and state.get("behind", 0) > 0
    ):
        raise AccessError("Git history is behind or diverged; fast-forward it before migration")
    if state.get("remote") and not evidence:
        raise AccessError("remote repositories require provider-admin evidence before migration")
    git_root: Path | None = detect_legacy_layout(project_root)["git_root"]
    if git_root is None:
        raise AccessError("migration requires the Git boundary that tracks .docs")
    scoped_identity = require_git_scoped_identity(project_root, git_root)
    if (
        scoped_identity["provider"],
        scoped_identity["host"],
        scoped_identity["account"].casefold(),
    ) != (
        config["local_identity"]["provider"],
        config["local_identity"]["host"].casefold(),
        config["local_identity"]["account"].casefold(),
    ):
        raise AccessError("git-scoped-account identity does not match migration local_identity")

    _verified, current_policy, _manifest = verify_bundle_at(
        project_root,
        LEGACY_DOCS_ROOT_NAME,
    )
    trust_path = (
        project_root
        / LEGACY_DOCS_ROOT_NAME
        / "harness"
        / "access-control"
        / "trust.json"
    )
    trust = json.loads(trust_path.read_text(encoding="utf-8"))
    key_path = locate_admin_key(config["project_id"], codex_dir, claude_dir, backup_key)
    if fingerprint(public_key_from_private(key_path)) != trust.get("admin_key_fingerprint"):
        raise AccessError("administrator key fingerprint does not match legacy trust")
    legacy_admin_id = legacy_admin_id_for_account(
        current_policy,
        config["local_identity"]["provider"],
        config["local_identity"]["host"],
        config["local_identity"]["account"],
    )
    if legacy_admin_id is None:
        raise AccessError("the legacy document root can be migrated only by a signed-policy admin")

    legacy_root = project_root / LEGACY_DOCS_ROOT_NAME
    canonical_root = project_root / DOCS_ROOT_NAME
    moved = False
    try:
        os.replace(legacy_root, canonical_root)
        moved = True
        result = apply(
            project_root,
            config,
            approved_hash,
            codex_dir,
            claude_dir,
            backup_key,
            evidence,
            approved_plan=plan,
            allow_migration_dirty=True,
            existing_manifest_root=LEGACY_DOCS_ROOT_NAME,
        )
    except Exception:
        if moved and canonical_root.exists() and not legacy_root.exists():
            os.replace(canonical_root, legacy_root)
        raise
    return {
        **result,
        "status": "migrated",
        "document_root_before": LEGACY_DOCS_ROOT_NAME,
        "document_root_after": DOCS_ROOT_NAME,
    }


def apply(
    project_root: Path,
    config: dict[str, Any],
    approved_hash: str,
    codex_dir: Path,
    claude_dir: Path,
    backup_key: Path | None,
    evidence: str | None,
    rotate_key: bool = False,
    *,
    approved_plan: dict[str, Any] | None = None,
    allow_migration_dirty: bool = False,
    existing_manifest_root: str | None = None,
) -> dict[str, Any]:
    plan = approved_plan or make_plan(project_root, config, "rotate" if rotate_key else "apply")
    if plan["plan_hash"] != approved_hash:
        raise AccessError("approved plan hash does not match the current plan")
    state = plan["preflight"]
    if state.get("dirty") and not allow_migration_dirty:
        raise AccessError("Git worktree is not clean")
    if state.get("behind", 0) > 0 or (state.get("ahead", 0) > 0 and state.get("behind", 0) > 0):
        raise AccessError("Git history is behind or diverged; fast-forward it before Apply")
    if state.get("remote") and not evidence:
        raise AccessError("remote repositories require provider-admin evidence before Apply")

    layout = detect_layout(project_root)
    git_root: Path | None = layout["git_root"]
    if git_root is None:
        raise AccessError("Apply requires the Git boundary that tracks .ai-docs")
    scoped_identity = require_git_scoped_identity(project_root, git_root)
    if (
        scoped_identity["provider"],
        scoped_identity["host"],
        scoped_identity["account"].casefold(),
    ) != (
        config["local_identity"]["provider"],
        config["local_identity"]["host"].casefold(),
        config["local_identity"]["account"].casefold(),
    ):
        raise AccessError("git-scoped-account identity does not match config local_identity")
    remote_verification = "verified" if evidence else "local-only"
    policy_core = build_policy_core(config, layout, remote_verification)
    policy_core_hash = sha256_bytes(canonical_json(policy_core))
    access_dir = project_root / ".ai-docs" / "harness" / "access-control"
    initial = not (access_dir / "policy.json").is_file()
    if not initial:
        verify_bundle_at(
            project_root,
            DOCS_ROOT_NAME,
            manifest_root_name=existing_manifest_root,
        )
    if initial and rotate_key:
        raise AccessError("administrator key rotation requires an existing signed policy")
    caller = subject_for_account(
        policy_core,
        config["local_identity"]["provider"],
        config["local_identity"]["host"],
        config["local_identity"]["account"],
    )
    if caller is None:
        raise AccessError("local Git identity is not registered in the policy")
    if initial and not subject_has_role(policy_core, caller["id"], "admin"):
        raise AccessError("the first caller must be assigned the explicit admin role")

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
    provider_state_value = provider_state(config_with_root, layout, git_root, evidence, policy_core_hash)
    trust_value = {
        "schema_version": SCHEMA_VERSION,
        "project_id": config["project_id"],
        "admin_public_key": public_key,
        "admin_key_fingerprint": key_fingerprint,
        "admin_subjects": sorted(
            subject["id"]
            for subject in config["subjects"]
            if subject_has_role(policy_core, subject["id"], "admin")
        ),
        "signature_namespace": NAMESPACE,
    }

    full_outputs: dict[Path, bytes] = {
        access_dir / "trust.json": pretty_json(trust_value),
        access_dir / "provider-state.json": pretty_json(provider_state_value),
        access_dir / "write-access-instruction.md": render_access_instruction(policy_core_hash),
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
    desired_instruction_targets = instruction_targets(project_root)
    for target in desired_instruction_targets:
        managed_outputs[target] = (replace_managed_block(read_optional(target), instruction_block, INSTRUCTION_MARKERS), "instruction-block")
    stale_outputs = stale_instruction_outputs(
        project_root,
        desired_instruction_targets,
        manifest_root_name=existing_manifest_root,
    )

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
    transaction_paths = [*final_outputs, *key_outputs, *stale_outputs]
    if git_root is not None and config["enable_git_hooks"]:
        transaction_paths.append(git_local_state_path(git_root))
    file_snapshot = snapshot(transaction_paths)
    git_snapshot = git_config_values(git_root) if git_root is not None else None
    try:
        for path, content in final_outputs.items():
            mode = 0o755 if path.name in {"pre-commit", "pre-push", "write_access_guard.py"} else None
            atomic_write(path, content, mode)
        for path, content in stale_outputs.items():
            if content is None:
                if path.is_file():
                    path.unlink()
            else:
                atomic_write(path, content)
        for path, content in key_outputs.items():
            private = path.suffix == ".key"
            atomic_write(path, content, 0o600 if private else 0o644)
            if private:
                restrict_private_key(path)
        if config["enable_git_hooks"] and git_root is not None:
            install_git_hooks(
                project_root,
                git_root,
                layout,
                config,
                legacy_root_migration=existing_manifest_root == LEGACY_DOCS_ROOT_NAME,
            )
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
    return {
        **result,
        "plan_hash": approved_hash,
        "provider_server_rules": "externally-managed-not-applied-by-skill",
        "hosts": provider_state_value["hosts"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "apply", "rotate-plan", "rotate", "migrate-root-plan", "migrate-root"):
        item = sub.add_parser(name)
        item.add_argument("--project-root", required=True)
        item.add_argument("--config", required=True)
        if name in {"apply", "rotate", "migrate-root"}:
            item.add_argument("--approve-plan-hash", required=True)
            item.add_argument("--provider-admin-evidence")
            item.add_argument("--admin-key")
            item.add_argument("--codex-key-dir")
            item.add_argument("--claude-key-dir")
    discover = sub.add_parser("discover-participants")
    discover.add_argument("--config", required=True)
    for name in ("local-enroll-plan", "local-enroll"):
        item = sub.add_parser(name)
        item.add_argument("--project-root", required=True)
        if name == "local-enroll":
            item.add_argument("--approve-plan-hash", required=True)
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
        if args.command == "discover-participants":
            result = discover_participants(load_config(Path(args.config).resolve()))
        else:
            project_root = Path(args.project_root).resolve()
            if args.command == "verify":
                result = verify_bundle(project_root)
            elif args.command == "local-enroll-plan":
                result = make_local_enrollment_plan(project_root)
            elif args.command == "local-enroll":
                result = apply_local_enrollment(project_root, args.approve_plan_hash)
            elif args.command == "remove-plan":
                result = make_remove_plan(project_root, args.delete_keys)
            elif args.command == "remove":
                policy = json.loads((project_root / ".ai-docs" / "harness" / "access-control" / "policy.json").read_text(encoding="utf-8"))
                codex_dir = Path(args.codex_key_dir).resolve() if args.codex_key_dir else Path.home() / ".codex" / "harness-kit" / "admin-keys"
                claude_dir = Path(args.claude_key_dir).resolve() if args.claude_key_dir else Path.home() / ".claude" / "harness-kit" / "admin-keys"
                backup = Path(args.admin_key).resolve() if args.admin_key else None
                result = remove_access_control(project_root, args.approve_plan_hash, codex_dir, claude_dir, backup, args.delete_keys)
            else:
                config = load_config(Path(args.config).resolve())
                if args.command == "migrate-root-plan":
                    result = make_root_migration_plan(project_root, config)
                elif args.command in {"plan", "rotate-plan"}:
                    result = make_plan(project_root, config, "rotate" if args.command == "rotate-plan" else "apply")
                else:
                    codex_dir = Path(args.codex_key_dir).resolve() if args.codex_key_dir else Path.home() / ".codex" / "harness-kit" / "admin-keys"
                    claude_dir = Path(args.claude_key_dir).resolve() if args.claude_key_dir else Path.home() / ".claude" / "harness-kit" / "admin-keys"
                    backup = Path(args.admin_key).resolve() if args.admin_key else None
                    if args.command == "migrate-root":
                        result = migrate_document_root(
                            project_root,
                            config,
                            args.approve_plan_hash,
                            codex_dir,
                            claude_dir,
                            backup,
                            args.provider_admin_evidence,
                        )
                    else:
                        result = apply(project_root, config, args.approve_plan_hash, codex_dir, claude_dir, backup, args.provider_admin_evidence, args.command == "rotate")
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (AccessError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
