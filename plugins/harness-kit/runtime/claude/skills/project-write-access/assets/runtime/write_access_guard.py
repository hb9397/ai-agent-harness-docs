#!/usr/bin/env python3
"""Project-owned guard for Git hooks and AI PreToolUse adapters."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


NAMESPACE = "harness-kit-project-write-access"
ROLES = {"admin", "pm-pl", "app-doc-lead"}
WRITE_SCOPES = {"admin", "app-doc", "team"}
CODEOWNERS_MARKERS = (
    "# harness-kit:write-access:start",
    "# harness-kit:write-access:end",
)
INSTRUCTION_MARKERS = (
    "<!-- harness-kit:write-access:start -->",
    "<!-- harness-kit:write-access:end -->",
)


class GuardError(RuntimeError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def managed_hash(content: bytes, markers: tuple[str, str]) -> str:
    text = content.decode("utf-8")
    start, end = markers
    if text.count(start) != 1 or text.count(end) != 1:
        raise GuardError("managed block is missing or malformed")
    left = text.index(start)
    right = text.index(end, left) + len(end)
    return sha256_bytes(text[left:right].encode("utf-8"))


def json_handler_hash(content: bytes) -> str:
    data = json.loads(content.decode("utf-8"))
    entries = data.get("hooks", {}).get("PreToolUse", [])
    managed = [entry for entry in entries if "write_access_guard.py" in json.dumps(entry, ensure_ascii=False)]
    if len(managed) != 1:
        raise GuardError("managed AI hook entry is missing or duplicated")
    return sha256_bytes(canonical_json(managed[0]))


def generated_content_hash(content: bytes, mode: str) -> str:
    if mode == "full":
        return sha256_bytes(content)
    if mode == "codeowners-block":
        return managed_hash(content, CODEOWNERS_MARKERS)
    if mode == "instruction-block":
        return managed_hash(content, INSTRUCTION_MARKERS)
    if mode == "json-handler":
        return json_handler_hash(content)
    raise GuardError(f"unknown generated-manifest mode: {mode}")


def run_git(root: Path, *args: str, check: bool = True, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        input=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise GuardError(result.stderr.decode("utf-8", errors="replace").strip() or "git command failed")
    return result


def access_dir_from_project(project_root: Path) -> Path:
    return project_root.resolve() / ".docs" / "harness" / "access-control"


def load_verified_policy(project_root: Path) -> dict[str, Any]:
    access_dir = access_dir_from_project(project_root)
    policy_path = access_dir / "policy.json"
    trust_path = access_dir / "trust.json"
    signature_path = access_dir / "policy.sig"
    manifest_path = access_dir / "generated-manifest.json"
    for path in (policy_path, trust_path, signature_path, manifest_path):
        if not path.is_file():
            raise GuardError(f"required access-control file is missing: {path}")

    policy_bytes = policy_path.read_bytes()
    policy = json.loads(policy_bytes.decode("utf-8"))
    trust = json.loads(trust_path.read_text(encoding="utf-8"))
    if policy.get("project_id") != trust.get("project_id"):
        raise GuardError("project identity does not match trust.json")

    public_key = str(trust.get("admin_public_key", "")).strip()
    if not public_key.startswith("ssh-ed25519 "):
        raise GuardError("trust.json does not contain an Ed25519 public key")
    with tempfile.TemporaryDirectory(prefix="write-access-verify-") as raw:
        allowed = Path(raw) / "allowed_signers"
        allowed.write_text(f"harness-admin {public_key}\n", encoding="utf-8", newline="\n")
        result = subprocess.run(
            [
                "ssh-keygen",
                "-Y",
                "verify",
                "-f",
                str(allowed),
                "-I",
                "harness-admin",
                "-n",
                NAMESPACE,
                "-s",
                str(signature_path),
            ],
            input=policy_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    if result.returncode != 0:
        raise GuardError("policy signature verification failed")

    core = copy.deepcopy(policy)
    declared_core = core.pop("policy_core_sha256", None)
    core.pop("generated_manifest_sha256", None)
    if declared_core != sha256_bytes(canonical_json(core)):
        raise GuardError("policy core hash does not match")
    manifest_bytes = manifest_path.read_bytes()
    if policy.get("generated_manifest_sha256") != sha256_bytes(manifest_bytes):
        raise GuardError("generated manifest hash does not match policy")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    for entry in manifest.get("files", []):
        path = (project_root / str(entry.get("path", ""))).resolve()
        try:
            path.relative_to(project_root.resolve())
        except ValueError as exc:
            raise GuardError("generated-manifest path escapes project root") from exc
        if not path.is_file():
            raise GuardError(f"generated file is missing: {entry.get('path')}")
        actual = generated_content_hash(path.read_bytes(), str(entry.get("mode", "")))
        if actual != entry.get("sha256"):
            raise GuardError(f"generated content hash does not match: {entry.get('path')}")
    return policy


def glob_regex(pattern: str) -> re.Pattern[str]:
    out = ["^"]
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "*":
            if index + 1 < len(pattern) and pattern[index + 1] == "*":
                out.append(".*")
                index += 2
            else:
                out.append("[^/]*")
                index += 1
        elif char == "?":
            out.append("[^/]")
            index += 1
        else:
            out.append(re.escape(char))
            index += 1
    out.append("$")
    return re.compile("".join(out))


def normalize_project_path(value: str, project_root: Path) -> str:
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(project_root.resolve())
        except ValueError as exc:
            raise GuardError(f"path escapes project root: {value}") from exc
    normalized = candidate.as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized or normalized == ".":
        raise GuardError("a concrete target path is required")
    if normalized == ".." or normalized.startswith("../") or "/../" in f"/{normalized}/":
        raise GuardError(f"path traversal is not allowed: {value}")
    return normalized


def principal_for(policy: dict[str, Any], provider: str, account: str) -> dict[str, Any] | None:
    wanted = account.casefold()
    for principal in policy.get("principals", []):
        actual = str(principal.get("accounts", {}).get(provider, "")).casefold()
        if actual and actual == wanted:
            return principal
    return None


def rule_for_path(policy: dict[str, Any], path: str) -> dict[str, Any] | None:
    rules = sorted(policy.get("path_rules", []), key=lambda item: int(item.get("priority", 0)), reverse=True)
    for rule in rules:
        if glob_regex(str(rule["pattern"])).match(path):
            return rule
    return None


def is_protected_path(path: str) -> bool:
    return path in {"AGENTS.md", "CLAUDE.md"} or path.startswith(".docs/")


def permits(rule: dict[str, Any], principal: dict[str, Any] | None) -> bool:
    write_scope = str(rule.get("write_scope"))
    if write_scope == "team":
        return True
    if write_scope not in WRITE_SCOPES or principal is None:
        return False
    role = str(principal.get("role"))
    if role not in ROLES:
        return False
    if write_scope == "admin":
        return role == "admin"
    application = rule.get("application")
    return role in {"admin", "pm-pl"} or (
        role == "app-doc-lead" and application in principal.get("applications", [])
    )


def authorize_paths(policy: dict[str, Any], provider: str, account: str, paths: list[str], project_root: Path) -> list[str]:
    principal = principal_for(policy, provider, account)
    denied: list[str] = []
    for raw in paths:
        path = normalize_project_path(raw, project_root)
        rule = rule_for_path(policy, path)
        if rule is None:
            if is_protected_path(path):
                denied.append(path)
            continue
        if not permits(rule, principal):
            denied.append(path)
    return sorted(set(denied))


def admin_app_confirmation_paths(
    policy: dict[str, Any], provider: str, account: str, paths: list[str], project_root: Path
) -> list[str]:
    principal = principal_for(policy, provider, account)
    if principal is None or principal.get("role") != "admin":
        return []
    required: list[str] = []
    for raw in paths:
        path = normalize_project_path(raw, project_root)
        rule = rule_for_path(policy, path)
        if rule is not None and rule.get("write_scope") == "app-doc":
            required.append(path)
    return sorted(set(required))


def git_identity(git_root: Path) -> tuple[str, str]:
    provider = run_git(git_root, "config", "--local", "--get", "harness.writeAccess.provider", check=False)
    account = run_git(git_root, "config", "--local", "--get", "harness.writeAccess.account", check=False)
    return (
        provider.stdout.decode("utf-8", errors="replace").strip(),
        account.stdout.decode("utf-8", errors="replace").strip(),
    )


def project_path_from_git(policy: dict[str, Any], git_path: str) -> str:
    prefix = str(policy.get("git_root_relative", "."))
    normalized = Path(git_path).as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized if prefix == "." else f"{prefix.strip('/')}/{normalized}"


def git_path_from_project(policy: dict[str, Any], project_path: str) -> str | None:
    prefix = str(policy.get("git_root_relative", "."))
    if prefix == ".":
        return project_path
    marker = prefix.strip("/") + "/"
    return project_path[len(marker):] if project_path.startswith(marker) else None


def verify_staged_generated_entries(
    project_root: Path, policy: dict[str, Any], git_root: Path, changed_project_paths: list[str]
) -> None:
    manifest_path = access_dir_from_project(project_root) / "generated-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    changed = set(changed_project_paths)
    for entry in manifest.get("files", []):
        project_path = str(entry.get("path", ""))
        if project_path not in changed:
            continue
        git_path = git_path_from_project(policy, project_path)
        if git_path is None:
            continue
        staged = run_git(git_root, "show", f":{git_path}", check=False)
        if staged.returncode != 0:
            raise GuardError(f"generated file may not be deleted while access control is active: {project_path}")
        actual = generated_content_hash(staged.stdout, str(entry.get("mode", "")))
        if actual != entry.get("sha256"):
            raise GuardError(f"staged generated content does not match the signed manifest: {project_path}")


def invoke_previous_hook(git_root: Path, hook_name: str, args: list[str], stdin: bytes) -> int:
    git_dir_result = run_git(git_root, "rev-parse", "--git-dir")
    git_dir = Path(git_dir_result.stdout.decode().strip())
    if not git_dir.is_absolute():
        git_dir = git_root / git_dir
    state_path = git_dir.resolve() / "harness-write-access.json"
    if not state_path.is_file():
        return 0
    state = json.loads(state_path.read_text(encoding="utf-8"))
    previous = state.get("previous_hooks", {}).get(hook_name)
    if not previous:
        return 0
    path = Path(previous)
    if not path.is_file():
        return 0
    command = [str(path), *args] if os.name != "nt" else ["sh", str(path), *args]
    result = subprocess.run(command, input=stdin, cwd=git_root, check=False)
    return result.returncode


def pre_commit(project_root: Path) -> int:
    policy = load_verified_policy(project_root)
    git_root = Path.cwd().resolve()
    provider, account = git_identity(git_root)
    changed = run_git(git_root, "diff", "--cached", "--name-only").stdout.decode().splitlines()
    paths = [project_path_from_git(policy, item) for item in changed]
    verify_staged_generated_entries(project_root, policy, git_root, paths)
    denied = authorize_paths(policy, provider, account, paths, project_root)
    if denied:
        print("project-write-access: commit denied for " + ", ".join(denied), file=sys.stderr)
        return 1
    return invoke_previous_hook(git_root, "pre-commit", [], b"")


def changed_paths_for_push(git_root: Path, remote_name: str, stdin: bytes) -> list[str]:
    paths: set[str] = set()
    for line in stdin.decode("utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) != 4:
            raise GuardError("pre-push input is malformed")
        _local_ref, local_oid, _remote_ref, remote_oid = parts
        if local_oid and set(local_oid) == {"0"}:
            continue
        if remote_oid and set(remote_oid) == {"0"}:
            commits = run_git(git_root, "rev-list", local_oid, f"--not", f"--remotes={remote_name}").stdout.decode().splitlines()
            for commit in commits:
                output = run_git(git_root, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit).stdout.decode()
                paths.update(output.splitlines())
        else:
            output = run_git(git_root, "diff", "--name-only", remote_oid, local_oid).stdout.decode()
            paths.update(output.splitlines())
    return sorted(paths)


def infer_provider(remote_url: str) -> str | None:
    lowered = remote_url.casefold()
    if "github" in lowered:
        return "github"
    if "gitlab" in lowered:
        return "gitlab"
    if "gitea" in lowered:
        return "gitea"
    return None


def pre_push(project_root: Path, remote_name: str, remote_url: str, stdin: bytes) -> int:
    policy = load_verified_policy(project_root)
    git_root = Path.cwd().resolve()
    configured_provider, account = git_identity(git_root)
    inferred_provider = infer_provider(remote_url)
    if configured_provider and inferred_provider and configured_provider != inferred_provider:
        print("project-write-access: configured provider does not match push remote", file=sys.stderr)
        return 1
    provider = configured_provider or inferred_provider or ""
    paths = [project_path_from_git(policy, item) for item in changed_paths_for_push(git_root, remote_name, stdin)]
    denied = authorize_paths(policy, provider, account, paths, project_root)
    if denied:
        print("project-write-access: push denied for " + ", ".join(denied), file=sys.stderr)
        return 1
    return invoke_previous_hook(git_root, "pre-push", [remote_name, remote_url], stdin)


PATH_KEYS = {"file_path", "path", "target_file", "target_path"}


def collect_paths(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PATH_KEYS and isinstance(child, str):
                found.append(child)
            else:
                found.extend(collect_paths(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(collect_paths(child))
    return found


def paths_from_git_command(command: str, git_root: Path, policy: dict[str, Any]) -> list[str]:
    try:
        tokens = shlex.split(command, posix=os.name != "nt")
    except ValueError:
        if ".docs" in command or "AGENTS.md" in command or "CLAUDE.md" in command:
            raise GuardError("dynamic command target could not be parsed safely")
        return []
    command_index = 0
    while command_index < len(tokens) and tokens[command_index] in {"&", "command"}:
        command_index += 1
    if command_index < len(tokens) and tokens[command_index] == "env":
        command_index += 1
        while command_index < len(tokens) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[command_index]):
            command_index += 1
    if command_index >= len(tokens):
        return []

    executable = re.split(r"[\\/]", tokens[command_index].strip("\"'"))[-1].lower()
    provider_review_commands = {
        "gh": ({"pr"}, {"checks", "diff", "list", "ls", "status", "view"}),
        "gh.exe": ({"pr"}, {"checks", "diff", "list", "ls", "status", "view"}),
        "glab": ({"mr"}, {"approvers", "diff", "issues", "list", "ls", "view"}),
        "glab.exe": ({"mr"}, {"approvers", "diff", "issues", "list", "ls", "view"}),
        "tea": ({"pr", "pull", "pulls"}, {"list", "ls", "show", "view"}),
        "tea.exe": ({"pr", "pull", "pulls"}, {"list", "ls", "show", "view"}),
    }
    review_command = provider_review_commands.get(executable)
    if review_command is not None:
        topics, read_actions = review_command
        options_with_value = {"-R", "--repo", "--hostname", "--config", "--login", "--remote"}
        positionals: list[str] = []
        arguments = tokens[command_index + 1:]
        index = 0
        while index < len(arguments):
            argument = arguments[index]
            if argument in options_with_value:
                index += 2
                continue
            if any(argument.startswith(option + "=") for option in options_with_value if option.startswith("--")):
                index += 1
                continue
            if argument.startswith("-") or argument == "--":
                index += 1
                continue
            positionals.append(argument.lower())
            index += 1
        if positionals and positionals[0] in topics:
            action = positionals[1] if len(positionals) > 1 else None
            if action is None or action in read_actions:
                return []
            raise GuardError(
                "AI provider pull/merge-request write commands require separately verified server protection and human approval"
            )
        return []

    if executable not in {"git", "git.exe"}:
        if ".docs" in command or "AGENTS.md" in command or "CLAUDE.md" in command:
            raise GuardError("non-Git command targets protected documents and cannot be proven safe")
        return []
    index = command_index + 1
    while index < len(tokens) and tokens[index].startswith("-"):
        option = tokens[index]
        index += 2 if option in {"-C", "--git-dir", "--work-tree", "--namespace", "--config-env"} and index + 1 < len(tokens) else 1
    if index >= len(tokens):
        return []
    action = tokens[index]
    action_args = tokens[index + 1:]

    def to_project_path(item: str) -> str:
        return normalize_project_path(item, project_root) if Path(item).is_absolute() else project_path_from_git(policy, item)

    if action == "add":
        candidates = [item for item in action_args if not item.startswith("-")]
        if not candidates or any(item in {".", "-A", "--all"} for item in action_args):
            output = run_git(git_root, "status", "--porcelain", "--untracked-files=all").stdout.decode()
            candidates = [line[3:] for line in output.splitlines() if len(line) > 3]
        return [to_project_path(item) for item in candidates]
    if action == "commit":
        output = run_git(git_root, "diff", "--cached", "--name-only").stdout.decode()
        return [project_path_from_git(policy, item) for item in output.splitlines()]
    if action in {"push", "merge", "rebase"}:
        raise GuardError(f"AI {action} requires the standard Git hook and a separately verified branch state")
    if ".docs" in command or "AGENTS.md" in command or "CLAUDE.md" in command:
        raise GuardError(f"Git {action} targets protected documents and cannot be proven safe")
    return []


def ai_decision(project_root: Path, payload: dict[str, Any]) -> tuple[str, str]:
    policy = load_verified_policy(project_root)
    cwd = Path(str(payload.get("cwd") or project_root)).resolve()
    docs_root = project_root / ".docs"
    docs_git = run_git(docs_root, "rev-parse", "--show-toplevel", check=False) if docs_root.is_dir() else None
    if docs_git is not None and docs_git.returncode == 0 and Path(docs_git.stdout.decode().strip()).resolve() == docs_root.resolve():
        git_root = docs_root.resolve()
    else:
        git_root_result = run_git(cwd, "rev-parse", "--show-toplevel", check=False)
        git_root = Path(git_root_result.stdout.decode().strip()).resolve() if git_root_result.returncode == 0 else project_root
    provider, account = git_identity(git_root)
    tool_input = payload.get("tool_input") or {}
    paths = collect_paths(tool_input)
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if isinstance(command, str):
        paths.extend(paths_from_git_command(command, git_root, policy))
    normalized: list[str] = []
    for path in paths:
        try:
            normalized.append(normalize_project_path(path, project_root))
        except GuardError:
            if any(token in str(path) for token in (".docs", "AGENTS.md", "CLAUDE.md")):
                raise
    denied = authorize_paths(policy, provider, account, normalized, project_root)
    if denied:
        return "deny", "write denied for: " + ", ".join(denied)
    confirmation = admin_app_confirmation_paths(policy, provider, account, normalized, project_root)
    if confirmation:
        return (
            "ask",
            "관리자가 앱 문서 소유 범위를 대신 수정합니다. 대상 앱·정확한 파일·원래 소유 범위·수정 요약과 이유를 확인한 뒤 이 변경에 한해 승인하세요: "
            + ", ".join(confirmation),
        )
    return "allow", "allowed"


def emit_ai_denial(host: str, reason: str) -> int:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"project-write-access: {reason}",
        }
    }
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0


def emit_ai_confirmation(host: str, reason: str) -> int:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"project-write-access: {reason}",
        }
    }
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("pre-commit", "pre-push"):
        item = sub.add_parser(name)
        item.add_argument("--project-root", required=True)
        if name == "pre-push":
            item.add_argument("remote_name")
            item.add_argument("remote_url")
    ai = sub.add_parser("ai")
    ai.add_argument("--host", choices=("claude", "codex"), required=True)
    ai.add_argument("--project-root", required=True)
    check = sub.add_parser("check-path")
    check.add_argument("--project-root", required=True)
    check.add_argument("--provider", choices=("github", "gitlab", "gitea"), required=True)
    check.add_argument("--account", required=True)
    check.add_argument("paths", nargs="+")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    try:
        if args.command == "pre-commit":
            return pre_commit(project_root)
        if args.command == "pre-push":
            stdin = sys.stdin.buffer.read()
            return pre_push(project_root, args.remote_name, args.remote_url, stdin)
        if args.command == "check-path":
            policy = load_verified_policy(project_root)
            denied = authorize_paths(policy, args.provider, args.account, args.paths, project_root)
            if denied:
                print(json.dumps({"decision": "deny", "paths": denied}, ensure_ascii=False))
                return 1
            confirmation = admin_app_confirmation_paths(
                policy, args.provider, args.account, args.paths, project_root
            )
            if confirmation:
                print(
                    json.dumps(
                        {
                            "decision": "confirm",
                            "paths": confirmation,
                            "reason": "admin is crossing into app-doc ownership; ask one additional access-specific question",
                        },
                        ensure_ascii=False,
                    )
                )
                return 3
            print(json.dumps({"decision": "allow", "paths": args.paths}, ensure_ascii=False))
            return 0
        payload = json.loads(sys.stdin.read())
        decision, reason = ai_decision(project_root, payload)
        if decision == "deny":
            return emit_ai_denial(args.host, reason)
        if decision == "ask":
            return emit_ai_confirmation(args.host, reason)
        return 0
    except (GuardError, json.JSONDecodeError, OSError, ValueError) as exc:
        if args.command == "ai":
            return emit_ai_denial(args.host, str(exc))
        print(f"project-write-access: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
