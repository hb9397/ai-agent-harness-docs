#!/usr/bin/env python3
"""Executable lifecycle, authorization, tamper, and rollback checks."""

from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path


sys.dont_write_bytecode = True
SKILL_ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = SKILL_ROOT / "scripts" / "project_write_access.py"
GUARD_ASSET = SKILL_ROOT / "assets" / "runtime" / "write_access_guard.py"
CHILD_ENV = os.environ.copy()
CHILD_ENV["PYTHONIOENCODING"] = "utf-8"


def command(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        env=CHILD_ENV,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
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


def base_config(path: Path, repo_path: str = ".", applications: list[str] | None = None) -> Path:
    application_ids = applications or ["web", "api"]
    config = {
        "schema_version": "2.0.0",
        "project_id": "fixture-project",
        "applications": application_ids,
        "subjects": [
            {
                "id": "owner",
                "accounts": [
                    {"provider": "github", "host": "github.com", "account_id": "1", "login": "@owner"},
                    {"provider": "gitlab", "host": "gitlab.com", "account_id": "1", "login": "@owner"},
                    {"provider": "gitea", "host": "gitea.com", "account_id": "1", "login": "@owner"},
                ],
            },
            {
                "id": "lead",
                "accounts": [
                    {"provider": "github", "host": "github.com", "account_id": "2", "login": "@lead"},
                    {"provider": "gitlab", "host": "gitlab.com", "account_id": "2", "login": "@lead"},
                    {"provider": "gitea", "host": "gitea.com", "account_id": "2", "login": "@lead"},
                ],
            },
            {
                "id": "web-doc-lead",
                "accounts": [
                    {"provider": "github", "host": "github.com", "account_id": "3", "login": "@web-doc-lead"},
                    {"provider": "gitlab", "host": "gitlab.com", "account_id": "3", "login": "@web-doc-lead"},
                    {"provider": "gitea", "host": "gitea.com", "account_id": "3", "login": "@web-doc-lead"},
                ],
            },
            {
                "id": "developer-a",
                "accounts": [
                    {"provider": "github", "host": "github.com", "account_id": "4", "login": "@dev-a"}
                ],
            },
        ],
        "role_assignments": [
            {"subject_id": "owner", "role": "admin"},
            {"subject_id": "lead", "role": "pm-pl"},
            {"subject_id": "web-doc-lead", "role": "app-doc-lead", "applications": [application_ids[0]]},
            {"subject_id": "developer-a", "role": "developer"},
        ],
        "repositories": [
            {
                "id": "docs-repo",
                "provider": "github",
                "host": "github.com",
                "owner": "example",
                "name": "docs",
                "purpose": "docs",
                "applications": application_ids,
                "protected_branches": ["main"],
                "server_policy": "externally-approved",
            },
            {
                "id": "web-source",
                "provider": "github",
                "host": "github.com",
                "owner": "example",
                "name": "web",
                "purpose": "source",
                "applications": [application_ids[0]],
                "protected_branches": [],
                "server_policy": "none",
            },
        ],
        "local_identity": {"provider": "github", "host": "github.com", "account": "@owner"},
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
        env=CHILD_ENV,
        input=payload,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def ai_file_write(guard: Path, project: Path, host: str, path: Path) -> subprocess.CompletedProcess[str]:
    payload = json.dumps(
        {"cwd": str(project), "tool_input": {"file_path": str(path), "content": "proposed"}},
        ensure_ascii=False,
    )
    return subprocess.run(
        [sys.executable, str(guard), "ai", "--host", host, "--project-root", str(project)],
        cwd=project,
        env=CHILD_ENV,
        input=payload,
        text=True,
        encoding="utf-8",
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
        (project / ".docs" / app / "impl-doc").mkdir(parents=True)
    write(project / ".docs" / "README.md", "# Docs\n")
    write(project / ".docs" / ".gitignore", "_inbox/*\n")
    write(project / ".github" / "CODEOWNERS", "# TEAM-RULE\n/src/ @source-owner\n")
    commit_all(project, "baseline")
    return project


def assert_skill_contract() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    openai = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in skill
    assert "allow_implicit_invocation: false" in openai
    assert "일반 파일 편집" in skill
    assert "import urllib" not in controller
    assert '"gh", "api"' in controller
    assert '"glab", "api"' in controller
    assert '"tea", "--login"' in controller
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
    codeowners = (project / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    assert "TEAM-RULE" in codeowners
    assert "/.docs/web/context-base/** @lead @web-doc-lead" in codeowners
    assert "/.docs/api/context-base/** @lead" in codeowners
    assert "/.docs/web/impl-doc/**" not in codeowners
    assert "/.docs/ @owner" not in codeowners
    instruction = (project / ".docs" / "web" / "instruction" / "agent-instruction.md").read_text(encoding="utf-8")
    assert "TEAM-web" in instruction
    assert "harness-kit:write-access" not in instruction
    root_map = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "write-access-instruction.md" in root_map
    access_instruction = (project / ".docs" / "harness" / "access-control" / "write-access-instruction.md").read_text(encoding="utf-8")
    assert "역할은 상속하지 않는다" in access_instruction
    assert "설계 기준" in access_instruction
    assert git(project, "config", "--local", "--get", "core.hooksPath").stdout.strip() == ".docs/harness/access-control/hooks/git"
    assert git(project, "config", "--local", "--get", "harness.writeAccess.host").stdout.strip() == "github.com"
    provider_state = json.loads((project / ".docs" / "harness" / "access-control" / "provider-state.json").read_text(encoding="utf-8"))
    assert {item["id"] for item in provider_state["providers"]["github"]["repositories"]} == {"docs-repo", "web-source"}

    guard = project / ".docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
    common = [sys.executable, str(guard), "check-path", "--project-root", str(project), "--provider", "github", "--provider-host", "github.com", "--account"]
    allow_admin = command([*common, "@owner", ".docs/harness/access-control/policy.json"], check=False)
    deny_admin_app = command([*common, "@owner", ".docs/web/context-base/DESIGN.md"], check=False)
    deny_admin_doc = command([*common, "@dev-a", ".docs/harness/access-control/policy.json"], check=False)
    allow_team_a = command([*common, "@dev-a", ".docs/web/impl-doc/dev-a/task.md"], check=False)
    allow_team_b = command([*common, "@dev-a", ".docs/web/impl-doc/dev-b/task.md"], check=False)
    confirm_pm_pl_all_apps = command([*common, "@lead", ".docs/api/context-base/DESIGN.md"], check=False)
    confirm_app_lead = command([*common, "@web-doc-lead", ".docs/web/instruction/agent-instruction.md"], check=False)
    deny_other_app = command([*common, "@web-doc-lead", ".docs/api/context-base/DESIGN.md"], check=False)
    deny_app_lead_admin = command([*common, "@web-doc-lead", ".docs/README.md"], check=False)
    allow_admin_unlisted = command([*common, "@owner", ".docs/new-admin-document.md"], check=False)
    deny_dev_unlisted = command([*common, "@dev-a", ".docs/new-admin-document.md"], check=False)
    allow_source_without_role = command([*common, "@unregistered", "src/app.py"], check=False)
    assert allow_admin.returncode == 0
    assert deny_admin_app.returncode == 1
    assert deny_admin_doc.returncode == 1
    assert allow_team_a.returncode == 0
    assert allow_team_b.returncode == 0
    assert confirm_pm_pl_all_apps.returncode == 3
    assert confirm_app_lead.returncode == 3
    assert deny_other_app.returncode == 1
    assert deny_app_lead_admin.returncode == 1
    assert allow_admin_unlisted.returncode == 0
    assert deny_dev_unlisted.returncode == 1
    assert allow_source_without_role.returncode == 0

    git(project, "config", "--local", "harness.writeAccess.account", "@lead")
    for host in ("claude", "codex"):
        app_prompt = ai_file_write(
            guard, project, host, project / ".docs" / "web" / "context-base" / "DESIGN.md"
        )
        assert app_prompt.returncode == 0
        prompt_decision = json.loads(app_prompt.stdout)["hookSpecificOutput"]
        assert prompt_decision["permissionDecision"] == "ask"
        assert "설계 기준" in prompt_decision["permissionDecisionReason"]

    git(project, "config", "--local", "harness.writeAccess.account", "@owner")
    instruction_path = project / ".docs" / "harness" / "access-control" / "write-access-instruction.md"
    original_instruction = instruction_path.read_text(encoding="utf-8")
    staged_tamper = original_instruction.replace("역할은 상속하지 않는다", "역할을 상속한다")
    assert staged_tamper != original_instruction
    write(instruction_path, staged_tamper)
    git(project, "add", str(instruction_path))
    write(instruction_path, original_instruction)
    denied_managed_block = git(project, "commit", "-m", "must deny staged managed-block tamper", check=False)
    assert denied_managed_block.returncode != 0
    assert "staged generated content" in denied_managed_block.stderr
    git(project, "reset", "--", str(instruction_path))

    git(project, "config", "--local", "harness.writeAccess.account", "@dev-a")
    team_path = project / ".docs" / "web" / "impl-doc" / "dev-b" / "team.md"
    write(team_path, "team\n")
    assert git(project, "add", str(team_path)).returncode == 0
    git(project, "commit", "-q", "-m", "unregistered contributor team document")
    assert (project / ".git" / "previous-hook-ran").is_file()

    protected_path = project / ".docs" / "README.md"
    protected_text = protected_path.read_text(encoding="utf-8")
    write(protected_path, protected_text + "blocked\n")
    git(project, "add", str(protected_path))
    denied_admin_edit = git(project, "commit", "-m", "must deny admin document", check=False)
    assert denied_admin_edit.returncode != 0
    assert "commit denied" in denied_admin_edit.stderr
    git(project, "reset", "--", str(protected_path))
    protected_path.write_text(protected_text, encoding="utf-8", newline="\n")

    protected_path.unlink()
    git(project, "add", str(protected_path))
    denied_deletion = git(project, "commit", "-m", "must deny protected deletion", check=False)
    assert denied_deletion.returncode != 0
    assert "commit denied" in denied_deletion.stderr
    git(project, "reset", "--", str(protected_path))
    protected_path.write_text(protected_text, encoding="utf-8", newline="\n")

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

    local_state = json.loads((project / ".git" / "harness-write-access.json").read_text(encoding="utf-8"))
    assert local_state["previous_hooks"]["pre-commit"] == str(previous_hook.resolve())
    guard = project / ".docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
    local_oid = git(project, "rev-parse", "HEAD").stdout.strip()
    push_input = f"refs/heads/main {local_oid} refs/heads/main {baseline_sha}\n"
    allowed_push = subprocess.run(
        [sys.executable, str(guard), "pre-push", "--project-root", str(project), "origin", "https://github.com/example/repo.git"],
        cwd=project,
        env=CHILD_ENV,
        input=push_input,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert allowed_push.returncode == 0, allowed_push.stderr
    self_hosted_push = subprocess.run(
        [sys.executable, str(guard), "pre-push", "--project-root", str(project), "origin", "https://git.company.internal/example/repo.git"],
        cwd=project,
        env=CHILD_ENV,
        input=push_input,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert self_hosted_push.returncode == 1
    assert "provider host" in self_hosted_push.stderr

    git(project, "config", "--local", "harness.writeAccess.account", "@owner")
    write(protected_path, protected_text + "admin update\n")
    git(project, "add", str(protected_path))
    git(project, "commit", "-q", "-m", "admin updates admin document")
    git(project, "config", "--local", "harness.writeAccess.account", "@dev-a")
    local_oid = git(project, "rev-parse", "HEAD").stdout.strip()
    push_input = f"refs/heads/main {local_oid} refs/heads/main {baseline_sha}\n"
    denied_push = subprocess.run(
        [sys.executable, str(guard), "pre-push", "--project-root", str(project), "origin", "https://github.com/example/repo.git"],
        cwd=project,
        env=CHILD_ENV,
        input=push_input,
        text=True,
        encoding="utf-8",
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

    updated_config = json.loads(config.read_text(encoding="utf-8"))
    app_lead = next(item for item in updated_config["role_assignments"] if item["role"] == "app-doc-lead")
    app_lead["applications"].append("api")
    write(config, json.dumps(updated_config, ensure_ascii=False, indent=2) + "\n")
    policy_update_plan = plan(project, config)
    apply(project, config, policy_update_plan["plan_hash"], codex_keys, claude_keys)
    updated_guard = project / ".docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
    newly_allowed_app = command(
        [
            sys.executable,
            str(updated_guard),
            "check-path",
            "--project-root",
            str(project),
            "--provider",
            "github",
            "--provider-host",
            "github.com",
            "--account",
            "@web-doc-lead",
            ".docs/api/context-base/DESIGN.md",
        ],
        check=False,
    )
    assert newly_allowed_app.returncode == 3
    commit_all(project, "assign second application to document lead")

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


def test_single_application_defaults(root: Path) -> None:
    project = root / "single-application"
    init_repo(project)
    write(project / "AGENTS.md", "# Agent map\n")
    write(project / "CLAUDE.md", "@AGENTS.md\n")
    write(project / ".docs" / "instruction" / "agent-instruction.md", "# App rules\n")
    write(project / ".docs" / "README.md", "# Docs\n")
    commit_all(project, "baseline")
    config = base_config(root / "single-application-config.json", applications=["solo"])
    codex_keys = root / "single-application-codex-keys"
    claude_keys = root / "single-application-claude-keys"
    current_plan = plan(project, config)
    apply(project, config, current_plan["plan_hash"], codex_keys, claude_keys)

    policy = json.loads(
        (project / ".docs" / "harness" / "access-control" / "policy.json").read_text(encoding="utf-8")
    )
    rules = {rule["pattern"]: rule for rule in policy["path_rules"]}
    assert rules[".docs/context-base/**"] == {
        "application": "solo",
        "pattern": ".docs/context-base/**",
        "priority": 90,
        "write_scope": "app-doc",
    }
    assert rules[".docs/instruction/**"]["write_scope"] == "app-doc"
    assert rules[".docs/impl-doc/**"]["write_scope"] == "team"

    guard = project / ".docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
    allow_unregistered_team = command(
        [
            sys.executable,
            str(guard),
            "check-path",
            "--project-root",
            str(project),
            "--provider",
            "github",
            "--provider-host",
            "github.com",
            "--account",
            "@unregistered",
            ".docs/impl-doc/anyone/task.md",
        ],
        check=False,
    )
    allow_scoped_lead = command(
        [
            sys.executable,
            str(guard),
            "check-path",
            "--project-root",
            str(project),
            "--provider",
            "github",
            "--provider-host",
            "github.com",
            "--account",
            "@web-doc-lead",
            ".docs/context-base/DESIGN.md",
        ],
        check=False,
    )
    assert allow_unregistered_team.returncode == 0
    assert allow_scoped_lead.returncode == 3


def test_explicit_developer_and_multiple_roles(root: Path) -> None:
    project = root / "role-model"
    init_repo(project)
    write(project / "AGENTS.md", "# Agent map\n")
    write(project / "CLAUDE.md", "@AGENTS.md\n")
    config = base_config(root / "role-model-config.json")
    value = json.loads(config.read_text(encoding="utf-8"))
    value["role_assignments"].append({"subject_id": "owner", "role": "pm-pl"})
    write(config, json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    current_plan = plan(project, config)
    assert current_plan["schema_version"] == "2.0.0"
    assert current_plan["participant_discovery"] == "required-before-role-change"


def test_participant_merge() -> None:
    spec = importlib.util.spec_from_file_location("project_write_access_controller", CONTROLLER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    records = [
        {"provider": "github", "host": "github.com", "account_id": "7", "login": "@alice", "permission": "pull", "repository_id": "repo-a", "source": "team"},
        {"provider": "github", "host": "github.com", "account_id": "7", "login": "@alice", "permission": "admin", "repository_id": "repo-b", "source": "direct"},
        {"provider": "github", "host": "git.example.com", "account_id": "7", "login": "@alice", "permission": "write", "repository_id": "repo-c", "source": "direct"},
    ]
    merged = module.merge_participant_records(records)
    assert len(merged) == 2
    public = next(item for item in merged if item["host"] == "github.com")
    assert public["max_permission"] == "admin"
    assert {item["id"] for item in public["repositories"]} == {"repo-a", "repo-b"}


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
        test_single_application_defaults(root)
        test_explicit_developer_and_multiple_roles(root)
        test_participant_merge()
        test_multi_repository(root)
        test_failed_apply_removes_new_keys(root)
    print("project-write-access evals: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
