#!/usr/bin/env python3
"""Executable lifecycle, authorization, tamper, and rollback checks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


sys.dont_write_bytecode = True
SKILL_ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = SKILL_ROOT / "scripts" / "project_write_access.py"
GUARD_ASSET = SKILL_ROOT / "assets" / "runtime" / "write_access_guard.py"


def command(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if check and result.returncode != 0:
        raise AssertionError(f"command failed ({result.returncode}): {' '.join(args)}\n{result.stdout}\n{result.stderr}")
    return result


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return command(["git", "-C", str(root), *args], check=check)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def secure_private_key(path: Path) -> None:
    if os.name == "nt":
        user = os.environ.get("USERNAME") or os.environ.get("USER")
        assert user
        command(["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:(F)"])
    else:
        path.chmod(0o600)


def init_repo(root: Path) -> None:
    root.mkdir(parents=True)
    git(root, "init", "-q")
    git(root, "config", "user.name", "Fixture Admin")
    git(root, "config", "user.email", "fixture@example.com")


def commit_all(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)


def base_config(path: Path, repo_path: str = ".") -> Path:
    config = {
        "schema_version": "1.0.0",
        "project_id": "fixture-project",
        "applications": ["web", "api"],
        "principals": [
            {
                "id": "owner",
                "role": "admin",
                "accounts": {"github": "@owner", "gitlab": "@owner", "gitea": "@owner"},
            },
            {
                "id": "lead",
                "role": "pm-pl",
                "accounts": {"github": "@lead", "gitlab": "@lead", "gitea": "@lead"},
            },
            {
                "id": "dev-a",
                "role": "developer",
                "accounts": {"github": "@dev-a", "gitlab": "@dev-a", "gitea": "@dev-a"},
            },
            {
                "id": "dev-b",
                "role": "developer",
                "accounts": {"github": "@dev-b", "gitlab": "@dev-b", "gitea": "@dev-b"},
            },
        ],
        "repositories": [
            {"path": repo_path, "provider": "github", "protected_branches": ["main"], "server_policy": "externally-approved"}
        ],
        "local_identity": {"provider": "github", "account": "@owner"},
        "enable_git_hooks": True,
        "enable_ai_hooks": True,
    }
    write(path, json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    return path


def controller(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return command([sys.executable, str(CONTROLLER), *args], check=check)


def plan(project: Path, config: Path) -> dict:
    result = controller("plan", "--project-root", str(project), "--config", str(config))
    return json.loads(result.stdout)


def apply(project: Path, config: Path, plan_hash: str, codex_keys: Path, claude_keys: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return controller(
        "apply",
        "--project-root",
        str(project),
        "--config",
        str(config),
        "--approve-plan-hash",
        plan_hash,
        "--codex-key-dir",
        str(codex_keys),
        "--claude-key-dir",
        str(claude_keys),
        check=check,
    )


def ai_command(guard: Path, project: Path, host: str, shell_command: str) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"cwd": str(project), "tool_input": {"command": shell_command}}, ensure_ascii=False)
    return subprocess.run(
        [sys.executable, str(guard), "ai", "--host", host, "--project-root", str(project)],
        cwd=project,
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def make_single_fixture(root: Path) -> Path:
    project = root / "single"
    init_repo(project)
    write(project / "AGENTS.md", "# Agent map\n")
    write(project / "CLAUDE.md", "@AGENTS.md\n")
    for app in ("web", "api"):
        write(project / ".docs" / app / "instruction" / "agent-instruction.md", f"# {app} rules\n\nTEAM-{app}\n")
        (project / ".docs" / app / "impl-doc" / "dev-a").mkdir(parents=True)
        (project / ".docs" / app / "impl-doc" / "dev-b").mkdir(parents=True)
    write(project / ".docs" / "README.md", "# Docs\n")
    write(project / ".docs" / ".gitignore", "_inbox/*\n")
    write(project / ".github" / "CODEOWNERS", "# TEAM-RULE\n/src/ @source-owner\n")
    commit_all(project, "baseline")
    return project


def assert_skill_contract() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    openai = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in skill
    assert "allow_implicit_invocation: false" in openai
    assert "일반 파일 편집" in skill
    for path in (CONTROLLER, GUARD_ASSET):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_single_repository(root: Path) -> None:
    project = make_single_fixture(root)
    baseline_sha = git(project, "rev-parse", "HEAD").stdout.strip()
    previous_hook = project / ".git" / "hooks" / "pre-commit"
    write(previous_hook, "#!/bin/sh\ntouch \"$(git rev-parse --git-dir)/previous-hook-ran\"\n")
    os.chmod(previous_hook, 0o755)
    config = base_config(root / "single-config.json")
    codex_keys = root / "codex-keys"
    claude_keys = root / "claude-keys"
    first_plan = plan(project, config)
    assert first_plan["topology"] == "single-repository"
    result = apply(project, config, first_plan["plan_hash"], codex_keys, claude_keys)
    applied = json.loads(result.stdout)
    assert applied["status"] == "valid"
    assert applied["provider_server_rules"] == "not-applied"

    key_a = codex_keys / "fixture-project.key"
    key_b = claude_keys / "fixture-project.key"
    assert key_a.read_bytes() == key_b.read_bytes()
    assert "TEAM-RULE" in (project / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    assert "TEAM-web" in (project / ".docs" / "web" / "instruction" / "agent-instruction.md").read_text(encoding="utf-8")
    assert git(project, "config", "--local", "--get", "core.hooksPath").stdout.strip() == ".docs/harness/access-control/hooks/git"

    guard = project / ".docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
    allow_admin = command([sys.executable, str(guard), "check-path", "--project-root", str(project), "--provider", "github", "--account", "@owner", ".docs/harness/access-control/policy.json"], check=False)
    deny_admin_doc = command([sys.executable, str(guard), "check-path", "--project-root", str(project), "--provider", "github", "--account", "@dev-a", ".docs/harness/access-control/policy.json"], check=False)
    allow_own = command([sys.executable, str(guard), "check-path", "--project-root", str(project), "--provider", "github", "--account", "@dev-a", ".docs/web/impl-doc/dev-a/task.md"], check=False)
    deny_other = command([sys.executable, str(guard), "check-path", "--project-root", str(project), "--provider", "github", "--account", "@dev-a", ".docs/web/impl-doc/dev-b/task.md"], check=False)
    allow_admin_unlisted = command([sys.executable, str(guard), "check-path", "--project-root", str(project), "--provider", "github", "--account", "@owner", ".docs/new-admin-document.md"], check=False)
    deny_dev_unlisted = command([sys.executable, str(guard), "check-path", "--project-root", str(project), "--provider", "github", "--account", "@dev-a", ".docs/new-admin-document.md"], check=False)
    assert allow_admin.returncode == 0
    assert deny_admin_doc.returncode == 1
    assert allow_own.returncode == 0
    assert deny_other.returncode == 1
    assert allow_admin_unlisted.returncode == 0
    assert deny_dev_unlisted.returncode == 1

    git(project, "config", "--local", "harness.writeAccess.account", "@dev-a")
    denied_path = project / ".docs" / "web" / "impl-doc" / "dev-b" / "denied.md"
    write(denied_path, "denied\n")
    assert git(project, "add", str(denied_path)).returncode == 0
    denied_commit = git(project, "commit", "-m", "must be denied", check=False)
    assert denied_commit.returncode != 0
    assert "commit denied" in denied_commit.stderr
    git(project, "reset", "--", str(denied_path))
    denied_path.unlink()

    protected_path = project / ".docs" / "README.md"
    protected_text = protected_path.read_text(encoding="utf-8")
    protected_path.unlink()
    git(project, "add", str(protected_path))
    denied_deletion = git(project, "commit", "-m", "must deny protected deletion", check=False)
    assert denied_deletion.returncode != 0
    assert "commit denied" in denied_deletion.stderr
    protected_path.write_text(protected_text, encoding="utf-8", newline="\n")
    git(project, "add", str(protected_path))

    provider_review_commands = ("gh pr create --base main", "glab mr create --target-branch main", "tea pr create")
    provider_read_commands = ("gh pr list", "glab mr view 42", "tea pr list")
    for host in ("claude", "codex"):
        for provider_command in provider_review_commands:
            denied_ai = ai_command(guard, project, host, provider_command)
            assert denied_ai.returncode == 0, denied_ai.stderr
            decision = json.loads(denied_ai.stdout)["hookSpecificOutput"]
            assert decision["permissionDecision"] == "deny"
            assert "human approval" in decision["permissionDecisionReason"]
        for provider_command in provider_read_commands:
            allowed_review_read = ai_command(guard, project, host, provider_command)
            assert allowed_review_read.returncode == 0
            assert allowed_review_read.stdout == ""
        allowed_ai = ai_command(guard, project, host, "gh issue list")
        assert allowed_ai.returncode == 0
        assert allowed_ai.stdout == ""

    own_path = project / ".docs" / "web" / "impl-doc" / "dev-a" / "allowed.md"
    write(own_path, "allowed\n")
    git(project, "add", str(own_path))
    git(project, "commit", "-q", "-m", "developer-owned document")
    assert (project / ".git" / "previous-hook-ran").is_file()
    local_state = json.loads((project / ".git" / "harness-write-access.json").read_text(encoding="utf-8"))
    assert local_state["previous_hooks"]["pre-commit"] == str(previous_hook.resolve())
    guard = project / ".docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
    local_oid = git(project, "rev-parse", "HEAD").stdout.strip()
    push_input = f"refs/heads/main {local_oid} refs/heads/main {baseline_sha}\n"
    allowed_push = subprocess.run(
        [sys.executable, str(guard), "pre-push", "--project-root", str(project), "origin", "https://github.com/example/repo.git"],
        cwd=project,
        input=push_input,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert allowed_push.returncode == 0, allowed_push.stderr
    self_hosted_push = subprocess.run(
        [sys.executable, str(guard), "pre-push", "--project-root", str(project), "origin", "https://git.company.internal/example/repo.git"],
        cwd=project,
        input=push_input,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert self_hosted_push.returncode == 0, self_hosted_push.stderr

    git(project, "config", "--local", "harness.writeAccess.account", "@owner")
    write(denied_path, "admin-created\n")
    git(project, "add", str(denied_path))
    git(project, "commit", "-q", "-m", "admin updates another owner path")
    git(project, "config", "--local", "harness.writeAccess.account", "@dev-a")
    local_oid = git(project, "rev-parse", "HEAD").stdout.strip()
    push_input = f"refs/heads/main {local_oid} refs/heads/main {baseline_sha}\n"
    denied_push = subprocess.run(
        [sys.executable, str(guard), "pre-push", "--project-root", str(project), "origin", "https://github.com/example/repo.git"],
        cwd=project,
        input=push_input,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert denied_push.returncode == 1
    assert "push denied" in denied_push.stderr
    git(project, "config", "--local", "harness.writeAccess.account", "@owner")

    verify = controller("verify", "--project-root", str(project))
    assert json.loads(verify.stdout)["status"] == "valid"

    commit_all(project, "access policy")
    second_plan = plan(project, config)
    apply(project, config, second_plan["plan_hash"], codex_keys, claude_keys)
    assert git(project, "status", "--porcelain").stdout == ""

    signature = project / ".docs" / "harness" / "access-control" / "policy.sig"
    valid_signature = signature.read_bytes()
    signature.write_text("tampered\n", encoding="utf-8")
    failed = controller("verify", "--project-root", str(project), check=False)
    assert failed.returncode == 2
    assert "signature" in failed.stderr
    signature.write_bytes(valid_signature)
    controller("verify", "--project-root", str(project))

    old_key = root / "old-admin-backup.key"
    old_key.write_bytes((codex_keys / "fixture-project.key").read_bytes())
    secure_private_key(old_key)
    old_key_bytes = old_key.read_bytes()
    rotation_plan = json.loads(
        controller("rotate-plan", "--project-root", str(project), "--config", str(config)).stdout
    )
    rotated = controller(
        "rotate",
        "--project-root",
        str(project),
        "--config",
        str(config),
        "--approve-plan-hash",
        rotation_plan["plan_hash"],
        "--codex-key-dir",
        str(codex_keys),
        "--claude-key-dir",
        str(claude_keys),
    )
    assert json.loads(rotated.stdout)["status"] == "valid"
    assert (codex_keys / "fixture-project.key").read_bytes() == (claude_keys / "fixture-project.key").read_bytes()
    assert (codex_keys / "fixture-project.key").read_bytes() != old_key_bytes
    commit_all(project, "rotate administrator key")

    current_plan = plan(project, config)
    old_key_attempt = controller(
        "apply",
        "--project-root",
        str(project),
        "--config",
        str(config),
        "--approve-plan-hash",
        current_plan["plan_hash"],
        "--admin-key",
        str(old_key),
        "--codex-key-dir",
        str(codex_keys),
        "--claude-key-dir",
        str(claude_keys),
        check=False,
    )
    assert old_key_attempt.returncode == 2
    assert "fingerprint" in old_key_attempt.stderr, old_key_attempt.stderr

    current_claude_key = claude_keys / "fixture-project.key"
    current_claude_public = current_claude_key.with_suffix(".key.pub")
    current_claude_key_bytes = current_claude_key.read_bytes()
    current_claude_public_bytes = current_claude_public.read_bytes()
    current_claude_key.unlink()
    current_claude_public.unlink()
    missing_key_attempt = controller(
        "apply",
        "--project-root",
        str(project),
        "--config",
        str(config),
        "--approve-plan-hash",
        current_plan["plan_hash"],
        "--codex-key-dir",
        str(codex_keys),
        "--claude-key-dir",
        str(claude_keys),
        check=False,
    )
    assert missing_key_attempt.returncode == 2
    assert "both Codex and Claude" in missing_key_attempt.stderr
    current_claude_key.write_bytes(current_claude_key_bytes)
    current_claude_public.write_bytes(current_claude_public_bytes)
    secure_private_key(current_claude_key)

    removal_plan = json.loads(
        controller("remove-plan", "--project-root", str(project), "--delete-keys").stdout
    )
    removed = controller(
        "remove",
        "--project-root",
        str(project),
        "--approve-plan-hash",
        removal_plan["plan_hash"],
        "--codex-key-dir",
        str(codex_keys),
        "--claude-key-dir",
        str(claude_keys),
        "--delete-keys",
    )
    assert json.loads(removed.stdout)["status"] == "removed"
    assert not (project / ".docs" / "harness" / "access-control" / "policy.json").exists()
    assert not (codex_keys / "fixture-project.key").exists()
    assert not (claude_keys / "fixture-project.key").exists()
    assert "TEAM-RULE" in (project / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    assert "TEAM-web" in (project / ".docs" / "web" / "instruction" / "agent-instruction.md").read_text(encoding="utf-8")
    assert git(project, "config", "--local", "--get", "core.hooksPath", check=False).returncode == 1
    assert previous_hook.is_file()
    assert not (project / ".git" / "harness-write-access.json").exists()


def test_multi_repository(root: Path) -> None:
    project = root / "multi"
    docs = project / ".docs"
    project.mkdir()
    init_repo(docs)
    write(project / "AGENTS.md", "# Untracked root map\n")
    write(project / "CLAUDE.md", "@AGENTS.md\n")
    write(docs / "web" / "instruction" / "agent-instruction.md", "# Web\n")
    write(docs / "api" / "instruction" / "agent-instruction.md", "# API\n")
    write(docs / "README.md", "# Docs repo\n")
    write(docs / ".gitignore", "_inbox/*\n")
    write(docs / "CODEOWNERS", "# Existing higher-priority GitLab and Gitea file\n")
    commit_all(docs, "baseline")
    config = base_config(root / "multi-config.json", ".docs")
    codex_keys = root / "multi-codex-keys"
    claude_keys = root / "multi-claude-keys"
    current_plan = plan(project, config)
    assert current_plan["topology"] == "multi-repository"
    assert {item["provider"] for item in current_plan["conflicts"] if item["type"] == "shadowed-codeowners"} == {"gitlab", "gitea"}
    apply(project, config, current_plan["plan_hash"], codex_keys, claude_keys)
    assert (docs / ".github" / "CODEOWNERS").is_file()
    gitea_owners = (docs / ".gitea" / "CODEOWNERS").read_text(encoding="utf-8")
    assert "^web/context-base/.*$" in gitea_owners
    assert "^.*$" not in gitea_owners
    assert not (project / ".github" / "CODEOWNERS").exists()
    assert git(docs, "config", "--local", "--get", "core.hooksPath").stdout.strip() == "harness/access-control/hooks/git"
    policy = json.loads((docs / "harness" / "access-control" / "policy.json").read_text(encoding="utf-8"))
    assert policy["root_context_tracked"] is False
    assert {rule["pattern"] for rule in policy["path_rules"]} >= {"AGENTS.md", "CLAUDE.md"}
    assert "AGENTS" not in gitea_owners and "CLAUDE" not in gitea_owners


def test_failed_apply_removes_new_keys(root: Path) -> None:
    project = root / "rollback"
    init_repo(project)
    write(project / "AGENTS.md", "# Agent map\n")
    write(project / "CLAUDE.md", "@AGENTS.md\n")
    write(project / ".docs" / "web" / "instruction" / "agent-instruction.md", "# Web\n")
    write(project / ".docs" / "api" / "instruction" / "agent-instruction.md", "# API\n")
    write(project / ".docs" / "README.md", "# Docs\n")
    write(project / ".docs" / ".gitignore", "_inbox/*\n")
    write(project / ".claude" / "settings.json", "{ malformed\n")
    commit_all(project, "baseline")
    config = base_config(root / "rollback-config.json")
    codex_keys = root / "rollback-codex-keys"
    claude_keys = root / "rollback-claude-keys"
    current_plan = plan(project, config)
    failed = apply(project, config, current_plan["plan_hash"], codex_keys, claude_keys, check=False)
    assert failed.returncode == 2
    assert not (codex_keys / "fixture-project.key").exists()
    assert not (claude_keys / "fixture-project.key").exists()
    assert not (project / ".docs" / "harness" / "access-control" / "policy.json").exists()


def main() -> int:
    assert_skill_contract()
    with tempfile.TemporaryDirectory(prefix="project-write-access-evals-") as raw:
        root = Path(raw)
        test_single_repository(root)
        test_multi_repository(root)
        test_failed_apply_removes_new_keys(root)
    print("project-write-access evals: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
