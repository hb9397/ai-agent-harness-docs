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


def commit_all_without_hooks(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-q", "--no-verify", "-m", message)


def base_config(path: Path, repo_path: str = ".", applications: list[str] | None = None) -> Path:
    application_ids = applications or ["web", "api"]
    config = {
        "schema_version": "3.0.0",
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


def prepare_git_scoped_identity(project: Path, config: Path) -> Path:
    data = json.loads(config.read_text(encoding="utf-8"))
    git_root = project
    if not (git_root / ".git").exists():
        for name in (".ai-docs", ".docs"):
            candidate = project / name
            if (candidate / ".git").exists():
                git_root = candidate
                break
        else:
            raise AssertionError("fixture has no Git boundary")

    shared = project.parent / f".{project.name}-gitconfig-scoped"
    write(shared, "[user]\n\tname = Fixture Admin\n\temail = fixture@example.com\n")
    shared_value = shared.resolve().as_posix()
    existing = git(git_root, "config", "--local", "--fixed-value", "--get-all", "include.path", shared_value, check=False)
    if existing.returncode != 0:
        git(git_root, "config", "--local", "--add", "include.path", shared_value)
    elif len(existing.stdout.splitlines()) > 1:
        git(git_root, "config", "--local", "--fixed-value", "--unset-all", "include.path", shared_value)
        git(git_root, "config", "--local", "--add", "include.path", shared_value)

    identity = data["local_identity"]
    values = {
        "harness.gitScopedAccount.projectRoot": str(project.resolve()),
        "harness.gitScopedAccount.configPath": shared_value,
        "harness.gitScopedAccount.provider": identity["provider"],
        "harness.gitScopedAccount.host": identity["host"],
        "harness.gitScopedAccount.account": identity["account"],
    }
    for key, value in values.items():
        git(git_root, "config", "--local", "--replace-all", key, value)
    return git_root


def set_local_account(git_root: Path, account: str) -> None:
    git(git_root, "config", "--local", "--replace-all", "harness.gitScopedAccount.account", account)
    git(git_root, "config", "--local", "--replace-all", "harness.writeAccess.account", account)


def plan(project: Path, config: Path) -> dict:
    prepare_git_scoped_identity(project, config)
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


def migration_plan(project: Path, config: Path) -> dict:
    result = controller(
        "migrate-root-plan",
        "--project-root",
        str(project),
        "--config",
        str(config),
    )
    return json.loads(result.stdout)


def migrate_root(
    project: Path,
    config: Path,
    plan_hash: str,
    codex_keys: Path,
    claude_keys: Path,
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return controller(
        "migrate-root",
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


def load_controller_module():
    spec = importlib.util.spec_from_file_location("project_write_access_controller", CONTROLLER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_legacy_values(value, schema_version: str):
    if isinstance(value, dict):
        return {key: replace_legacy_values(item, schema_version) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_legacy_values(item, schema_version) for item in value]
    if isinstance(value, str):
        return value.replace(".ai-docs", ".docs").replace("3.0.0", schema_version)
    return value


def legacy_policy_core(policy: dict, schema_version: str) -> dict:
    if schema_version == "2.0.0":
        result = replace_legacy_values(policy, schema_version)
        result.pop("policy_core_sha256", None)
        result.pop("generated_manifest_sha256", None)
        return result
    if schema_version != "1.1.0":
        raise AssertionError(f"unsupported legacy fixture schema: {schema_version}")

    subjects = {subject["id"]: subject for subject in policy["subjects"]}
    principals = []
    for assignment in policy["role_assignments"]:
        role = assignment["role"]
        if role == "developer":
            continue
        subject = subjects[assignment["subject_id"]]
        principal = {
            "id": subject["id"],
            "role": role,
            "accounts": {
                account["provider"]: account["login"]
                for account in subject.get("accounts", [])
            },
        }
        if role == "app-doc-lead":
            principal["applications"] = assignment["applications"]
        principals.append(principal)

    return {
        "schema_version": schema_version,
        "project_id": policy["project_id"],
        "topology": policy["topology"],
        "git_root_relative": policy["git_root_relative"],
        "root_context_tracked": policy["root_context_tracked"],
        "remote_verification": policy["remote_verification"],
        "role_inheritance": {"admin": ["pm-pl"], "pm-pl": [], "app-doc-lead": []},
        "authorization_model": {
            "app_scoped_role": "app-doc-lead",
            "unregistered_team_write": True,
            "admin_app_doc_confirmation": "required-by-ai-instruction",
        },
        "applications": policy["applications"],
        "principals": sorted(principals, key=lambda item: item["id"]),
        "path_rules": replace_legacy_values(policy["path_rules"], schema_version),
        "repositories": [
            {
                "provider": repository["provider"],
                "path": ".",
                "protected_branches": repository.get("protected_branches", []),
                "server_policy": repository.get("server_policy", "externally-approved"),
            }
            for repository in policy["repositories"]
        ],
    }


def convert_current_policy_to_legacy(
    project: Path,
    codex_keys: Path,
    schema_version: str = "2.0.0",
) -> Path:
    """Turn a valid current fixture into a correctly signed legacy .docs fixture."""
    module = load_controller_module()
    current_root = project / ".ai-docs"
    access = current_root / "harness" / "access-control"
    policy = json.loads((access / "policy.json").read_text(encoding="utf-8"))
    current_core_hash = policy["policy_core_sha256"]
    legacy_core = legacy_policy_core(policy, schema_version)
    legacy_core_hash = module.sha256_bytes(module.canonical_json(legacy_core))
    manifest = json.loads((access / "generated-manifest.json").read_text(encoding="utf-8"))

    for entry in manifest["files"]:
        target = project / entry["path"]
        content = target.read_bytes()
        content = content.replace(b".ai-docs", b".docs")
        content = content.replace(b"3.0.0", schema_version.encode("ascii"))
        content = content.replace(current_core_hash.encode("ascii"), legacy_core_hash.encode("ascii"))
        target.write_bytes(content)

    legacy_entries = []
    for entry in manifest["files"]:
        legacy_entry = dict(entry)
        legacy_entry["path"] = entry["path"].replace(".ai-docs/", ".docs/", 1)
        current_path = project / entry["path"]
        if entry["mode"] == "full":
            digest = module.sha256_bytes(current_path.read_bytes())
        elif entry["mode"] == "codeowners-block":
            digest = module.managed_hash(current_path.read_bytes(), module.CODEOWNERS_MARKERS)
        elif entry["mode"] == "instruction-block":
            digest = module.managed_hash(current_path.read_bytes(), module.INSTRUCTION_MARKERS)
        elif entry["mode"] == "json-handler":
            digest = module.json_handler_hash(current_path)
        else:
            raise AssertionError(f"unknown fixture manifest mode: {entry['mode']}")
        legacy_entry["sha256"] = digest
        legacy_entries.append(legacy_entry)

    legacy_manifest = {
        "schema_version": schema_version,
        "policy_core_sha256": legacy_core_hash,
        "files": sorted(legacy_entries, key=lambda item: item["path"]),
    }
    manifest_bytes = module.pretty_json(legacy_manifest)
    legacy_policy = {
        **legacy_core,
        "policy_core_sha256": legacy_core_hash,
        "generated_manifest_sha256": module.sha256_bytes(manifest_bytes),
    }
    policy_bytes = module.canonical_json(legacy_policy)
    key_path = codex_keys / "fixture-project.key"
    (access / "generated-manifest.json").write_bytes(manifest_bytes)
    (access / "policy.json").write_bytes(policy_bytes)
    (access / "policy.sig").write_bytes(module.sign_policy(policy_bytes, key_path))

    git_root = current_root if module.is_git_root(current_root) else project
    state_path = module.git_local_state_path(git_root)
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["schema_version"] = schema_version
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    legacy_root = project / ".docs"
    os.replace(current_root, legacy_root)
    if git_root == project:
        git(project, "config", "--local", "--replace-all", "core.hooksPath", ".docs/harness/access-control/hooks/git")
        return project
    return legacy_root


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
        write(project / ".ai-docs" / app / "instruction" / "agent-instruction.md", f"# {app} rules\n\nTEAM-{app}\n")
        (project / ".ai-docs" / app / "impl-doc").mkdir(parents=True)
    write(project / ".ai-docs" / "README.md", "# Docs\n")
    write(project / ".ai-docs" / ".gitignore", "_inbox/*\n")
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
    assert '"migrate-root-plan"' in controller
    assert '"migrate-root"' in controller
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
    assert first_plan["git_scoped_account"]["status"] == "ready"
    result = apply(project, config, first_plan["plan_hash"], codex_keys, claude_keys)
    applied = json.loads(result.stdout)
    assert applied["status"] == "valid"
    assert applied["provider_server_rules"] == "not-applied"

    key_a = codex_keys / "fixture-project.key"
    key_b = claude_keys / "fixture-project.key"
    assert key_a.read_bytes() == key_b.read_bytes()
    codeowners = (project / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    assert "TEAM-RULE" in codeowners
    assert "/.ai-docs/web/context-base/** @lead @web-doc-lead" in codeowners
    assert "/.ai-docs/api/context-base/** @lead" in codeowners
    assert "/.ai-docs/web/impl-doc/**" not in codeowners
    assert "/.ai-docs/ @owner" not in codeowners
    instruction = (project / ".ai-docs" / "web" / "instruction" / "agent-instruction.md").read_text(encoding="utf-8")
    assert "TEAM-web" in instruction
    assert "harness-kit:write-access" not in instruction
    root_map = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "write-access-instruction.md" in root_map
    access_instruction = (project / ".ai-docs" / "harness" / "access-control" / "write-access-instruction.md").read_text(encoding="utf-8")
    assert "역할은 상속하지 않는다" in access_instruction
    assert "설계 기준" in access_instruction
    assert git(project, "config", "--local", "--get", "core.hooksPath").stdout.strip() == ".ai-docs/harness/access-control/hooks/git"
    assert git(project, "config", "--local", "--get", "harness.writeAccess.host").stdout.strip() == "github.com"
    provider_state = json.loads((project / ".ai-docs" / "harness" / "access-control" / "provider-state.json").read_text(encoding="utf-8"))
    assert {item["id"] for item in provider_state["providers"]["github"]["repositories"]} == {"docs-repo", "web-source"}

    guard = project / ".ai-docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
    policy_before_enrollment = (project / ".ai-docs" / "harness" / "access-control" / "policy.json").read_bytes()
    for key in ("core.hooksPath", "harness.writeAccess.projectRoot", "harness.writeAccess.provider", "harness.writeAccess.host", "harness.writeAccess.account"):
        git(project, "config", "--local", "--unset-all", key, check=False)
    enrollment_plan = json.loads(
        controller("local-enroll-plan", "--project-root", str(project)).stdout
    )
    assert enrollment_plan["shared_policy_changes"] == "none"
    assert enrollment_plan["roles"] == ["admin"]
    enrolled = json.loads(
        controller(
            "local-enroll",
            "--project-root",
            str(project),
            "--approve-plan-hash",
            enrollment_plan["plan_hash"],
        ).stdout
    )
    assert enrolled["status"] == "enrolled"
    assert (project / ".ai-docs" / "harness" / "access-control" / "policy.json").read_bytes() == policy_before_enrollment

    git(project, "config", "--local", "--unset-all", "harness.gitScopedAccount.account")
    missing_enrollment_doc = ai_file_write(guard, project, "codex", project / ".ai-docs" / "README.md")
    missing_enrollment_source = ai_file_write(guard, project, "codex", project / "src" / "app.py")
    assert json.loads(missing_enrollment_doc.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert missing_enrollment_source.returncode == 0 and missing_enrollment_source.stdout == ""
    set_local_account(project, "@owner")

    common = [sys.executable, str(guard), "check-path", "--project-root", str(project), "--provider", "github", "--provider-host", "github.com", "--account"]
    allow_admin = command([*common, "@owner", ".ai-docs/harness/access-control/policy.json"], check=False)
    deny_admin_app = command([*common, "@owner", ".ai-docs/web/context-base/DESIGN.md"], check=False)
    deny_admin_doc = command([*common, "@dev-a", ".ai-docs/harness/access-control/policy.json"], check=False)
    allow_team_a = command([*common, "@dev-a", ".ai-docs/web/impl-doc/dev-a/task.md"], check=False)
    allow_team_b = command([*common, "@dev-a", ".ai-docs/web/impl-doc/dev-b/task.md"], check=False)
    confirm_pm_pl_all_apps = command([*common, "@lead", ".ai-docs/api/context-base/DESIGN.md"], check=False)
    confirm_app_lead = command([*common, "@web-doc-lead", ".ai-docs/web/instruction/agent-instruction.md"], check=False)
    deny_other_app = command([*common, "@web-doc-lead", ".ai-docs/api/context-base/DESIGN.md"], check=False)
    deny_app_lead_admin = command([*common, "@web-doc-lead", ".ai-docs/README.md"], check=False)
    allow_admin_unlisted = command([*common, "@owner", ".ai-docs/new-admin-document.md"], check=False)
    deny_dev_unlisted = command([*common, "@dev-a", ".ai-docs/new-admin-document.md"], check=False)
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

    set_local_account(project, "@lead")
    for host in ("claude", "codex"):
        app_prompt = ai_file_write(
            guard, project, host, project / ".ai-docs" / "web" / "context-base" / "DESIGN.md"
        )
        assert app_prompt.returncode == 0
        prompt_decision = json.loads(app_prompt.stdout)["hookSpecificOutput"]
        assert prompt_decision["permissionDecision"] == "ask"
        assert "설계 기준" in prompt_decision["permissionDecisionReason"]

    set_local_account(project, "@owner")
    instruction_path = project / ".ai-docs" / "harness" / "access-control" / "write-access-instruction.md"
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

    set_local_account(project, "@dev-a")
    team_path = project / ".ai-docs" / "web" / "impl-doc" / "dev-b" / "team.md"
    write(team_path, "team\n")
    assert git(project, "add", str(team_path)).returncode == 0
    git(project, "commit", "-q", "-m", "unregistered contributor team document")
    assert (project / ".git" / "previous-hook-ran").is_file()

    protected_path = project / ".ai-docs" / "README.md"
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
    guard = project / ".ai-docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
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

    set_local_account(project, "@owner")
    write(protected_path, protected_text + "admin update\n")
    git(project, "add", str(protected_path))
    git(project, "commit", "-q", "-m", "admin updates admin document")
    set_local_account(project, "@dev-a")
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
    set_local_account(project, "@owner")

    verify = controller("verify", "--project-root", str(project))
    assert json.loads(verify.stdout)["status"] == "valid"

    commit_all(project, "access policy")
    second_plan = plan(project, config)
    apply(project, config, second_plan["plan_hash"], codex_keys, claude_keys)
    assert git(project, "status", "--porcelain").stdout == ""

    signature = project / ".ai-docs" / "harness" / "access-control" / "policy.sig"
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
    updated_guard = project / ".ai-docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
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
            ".ai-docs/api/context-base/DESIGN.md",
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
    assert not (project / ".ai-docs" / "harness" / "access-control" / "policy.json").exists()
    assert not (codex_keys / "fixture-project.key").exists()
    assert not (claude_keys / "fixture-project.key").exists()
    assert "TEAM-RULE" in (project / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    assert "TEAM-web" in (project / ".ai-docs" / "web" / "instruction" / "agent-instruction.md").read_text(encoding="utf-8")
    assert git(project, "config", "--local", "--get", "core.hooksPath", check=False).returncode == 1
    assert previous_hook.is_file()
    assert not (project / ".git" / "harness-write-access.json").exists()


def test_single_application_defaults(root: Path) -> None:
    project = root / "single-application"
    init_repo(project)
    write(project / "AGENTS.md", "# Agent map\n")
    write(project / "CLAUDE.md", "@AGENTS.md\n")
    write(project / ".ai-docs" / "instruction" / "agent-instruction.md", "# App rules\n")
    write(project / ".ai-docs" / "README.md", "# Docs\n")
    commit_all(project, "baseline")
    config = base_config(root / "single-application-config.json", applications=["solo"])
    codex_keys = root / "single-application-codex-keys"
    claude_keys = root / "single-application-claude-keys"
    current_plan = plan(project, config)
    apply(project, config, current_plan["plan_hash"], codex_keys, claude_keys)

    policy = json.loads(
        (project / ".ai-docs" / "harness" / "access-control" / "policy.json").read_text(encoding="utf-8")
    )
    rules = {rule["pattern"]: rule for rule in policy["path_rules"]}
    assert rules[".ai-docs/context-base/**"] == {
        "application": "solo",
        "pattern": ".ai-docs/context-base/**",
        "priority": 90,
        "write_scope": "app-doc",
    }
    assert rules[".ai-docs/instruction/**"]["write_scope"] == "app-doc"
    assert rules[".ai-docs/impl-doc/**"]["write_scope"] == "team"

    guard = project / ".ai-docs" / "harness" / "access-control" / "hooks" / "write_access_guard.py"
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
            ".ai-docs/impl-doc/anyone/task.md",
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
            ".ai-docs/context-base/DESIGN.md",
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
    assert current_plan["schema_version"] == "3.0.0"
    assert current_plan["participant_discovery"] == "required-before-role-change"


def test_signed_legacy_root_migration(root: Path) -> None:
    single = root / "signed-legacy-single"
    init_repo(single)
    write(single / "AGENTS.md", "# Agent map\n")
    write(single / "CLAUDE.md", "@AGENTS.md\n")
    for app in ("web", "api"):
        write(single / ".ai-docs" / app / "instruction" / "agent-instruction.md", f"# {app}\n")
    write(single / ".ai-docs" / "README.md", "# Docs\n")
    write(single / ".ai-docs" / ".gitignore", "_inbox/*\n")
    commit_all(single, "baseline")
    single_config = base_config(root / "signed-legacy-single-config.json")
    single_codex = root / "signed-legacy-single-codex"
    single_claude = root / "signed-legacy-single-claude"
    current = plan(single, single_config)
    apply(single, single_config, current["plan_hash"], single_codex, single_claude)
    legacy_git_root = convert_current_policy_to_legacy(single, single_codex, "1.1.0")
    commit_all_without_hooks(legacy_git_root, "legacy signed policy")

    rejected_general_plan = controller(
        "plan",
        "--project-root",
        str(single),
        "--config",
        str(single_config),
        check=False,
    )
    assert rejected_general_plan.returncode == 2
    assert "use migrate-root-plan and migrate-root" in rejected_general_plan.stderr
    migration = migration_plan(single, single_config)
    assert migration["operation"] == "migrate-document-root"
    assert migration["legacy_policy_schema_version"] == "1.1.0"
    assert migration["legacy_admin_identity_binding"] == "provider-login-and-admin-key"

    non_admin_config = root / "signed-legacy-single-non-admin-config.json"
    non_admin_value = json.loads(single_config.read_text(encoding="utf-8"))
    non_admin_value["local_identity"]["account"] = "@lead"
    write(non_admin_config, json.dumps(non_admin_value, ensure_ascii=False, indent=2) + "\n")
    set_local_account(legacy_git_root, "@lead")
    non_admin_plan = migration_plan(single, non_admin_config)
    rejected_non_admin = migrate_root(
        single,
        non_admin_config,
        non_admin_plan["plan_hash"],
        single_codex,
        single_claude,
        check=False,
    )
    assert rejected_non_admin.returncode == 2
    assert "signed-policy admin" in rejected_non_admin.stderr
    set_local_account(legacy_git_root, "@owner")

    migrated = json.loads(
        migrate_root(
            single,
            single_config,
            migration["plan_hash"],
            single_codex,
            single_claude,
        ).stdout
    )
    assert migrated["status"] == "migrated"
    assert not (single / ".docs").exists()
    assert (single / ".ai-docs").is_dir()
    assert git(single, "config", "--local", "--get", "core.hooksPath").stdout.strip() == ".ai-docs/harness/access-control/hooks/git"
    state = json.loads((single / ".git" / "harness-write-access.json").read_text(encoding="utf-8"))
    assert state["previous_core_hooks_path"] is None
    verified = json.loads(controller("verify", "--project-root", str(single)).stdout)
    assert verified["schema_version"] == "3.0.0"
    assert verified["document_root"] == ".ai-docs"

    multi = root / "signed-legacy-multi"
    docs = multi / ".ai-docs"
    multi.mkdir()
    init_repo(docs)
    write(multi / "AGENTS.md", "# Root map\n")
    write(multi / "CLAUDE.md", "@AGENTS.md\n")
    for app in ("web", "api"):
        write(docs / app / "instruction" / "agent-instruction.md", f"# {app}\n")
    write(docs / "README.md", "# Docs\n")
    write(docs / ".gitignore", "_inbox/*\n")
    commit_all(docs, "baseline")
    multi_config = base_config(root / "signed-legacy-multi-config.json")
    multi_codex = root / "signed-legacy-multi-codex"
    multi_claude = root / "signed-legacy-multi-claude"
    current = plan(multi, multi_config)
    apply(multi, multi_config, current["plan_hash"], multi_codex, multi_claude)
    legacy_git_root = convert_current_policy_to_legacy(multi, multi_codex)
    commit_all_without_hooks(legacy_git_root, "legacy signed policy")
    migration = migration_plan(multi, multi_config)
    assert migration["legacy_policy_schema_version"] == "2.0.0"
    assert migration["legacy_admin_identity_binding"] == "provider-host-login-and-admin-key"
    migrated = json.loads(
        migrate_root(
            multi,
            multi_config,
            migration["plan_hash"],
            multi_codex,
            multi_claude,
        ).stdout
    )
    assert migrated["status"] == "migrated"
    assert not (multi / ".docs").exists()
    assert git(multi / ".ai-docs", "config", "--local", "--get", "core.hooksPath").stdout.strip() == "harness/access-control/hooks/git"
    assert json.loads(controller("verify", "--project-root", str(multi)).stdout)["status"] == "valid"


def test_legacy_root_migration_rolls_back(root: Path) -> None:
    project = root / "legacy-migration-rollback"
    init_repo(project)
    write(project / "AGENTS.md", "# Agent map\n")
    write(project / "CLAUDE.md", "@AGENTS.md\n")
    write(project / ".ai-docs" / "web" / "instruction" / "agent-instruction.md", "# Web\n")
    write(project / ".ai-docs" / "api" / "instruction" / "agent-instruction.md", "# API\n")
    write(project / ".ai-docs" / "README.md", "# Docs\n")
    commit_all(project, "baseline")
    config = base_config(root / "legacy-migration-rollback-config.json")
    config_value = json.loads(config.read_text(encoding="utf-8"))
    config_value["enable_ai_hooks"] = False
    write(config, json.dumps(config_value, ensure_ascii=False, indent=2) + "\n")
    codex_keys = root / "legacy-migration-rollback-codex"
    claude_keys = root / "legacy-migration-rollback-claude"
    current = plan(project, config)
    apply(project, config, current["plan_hash"], codex_keys, claude_keys)
    legacy_git_root = convert_current_policy_to_legacy(project, codex_keys)
    write(project / ".codex" / "hooks.json", "{ malformed\n")
    commit_all_without_hooks(legacy_git_root, "legacy signed policy with unmanaged host file")

    config_value["enable_ai_hooks"] = True
    write(config, json.dumps(config_value, ensure_ascii=False, indent=2) + "\n")
    migration = migration_plan(project, config)
    failed = migrate_root(
        project,
        config,
        migration["plan_hash"],
        codex_keys,
        claude_keys,
        check=False,
    )
    assert failed.returncode == 2
    assert (project / ".docs").is_dir()
    assert not (project / ".ai-docs").exists()
    assert git(project, "config", "--local", "--get", "core.hooksPath").stdout.strip() == ".docs/harness/access-control/hooks/git"


def test_legacy_document_roots_are_rejected(root: Path) -> None:
    legacy = root / "legacy-docs-root"
    init_repo(legacy)
    write(legacy / ".docs" / "README.md", "# Legacy docs\n")
    legacy_config = base_config(root / "legacy-docs-root-config.json")
    rejected_legacy = controller(
        "plan", "--project-root", str(legacy), "--config", str(legacy_config), check=False
    )
    assert rejected_legacy.returncode == 2
    assert "legacy .docs exists without .ai-docs" in rejected_legacy.stderr

    both = root / "conflicting-docs-roots"
    init_repo(both)
    write(both / ".docs" / "README.md", "# Legacy docs\n")
    write(both / ".ai-docs" / "README.md", "# Canonical docs\n")
    both_config = base_config(root / "conflicting-docs-roots-config.json")
    rejected_both = controller(
        "plan", "--project-root", str(both), "--config", str(both_config), check=False
    )
    assert rejected_both.returncode == 2
    assert ".ai-docs and legacy .docs both exist" in rejected_both.stderr


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
    docs = project / ".ai-docs"
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
    config = base_config(root / "multi-config.json", ".ai-docs")
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
    write(project / ".ai-docs" / "web" / "instruction" / "agent-instruction.md", "# Web\n")
    write(project / ".ai-docs" / "api" / "instruction" / "agent-instruction.md", "# API\n")
    write(project / ".ai-docs" / "README.md", "# Docs\n")
    write(project / ".ai-docs" / ".gitignore", "_inbox/*\n")
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
    assert not (project / ".ai-docs" / "harness" / "access-control" / "policy.json").exists()


def main() -> int:
    assert_skill_contract()
    eval_tmp = os.environ.get("HARNESS_EVAL_TMPDIR")
    with tempfile.TemporaryDirectory(prefix="project-write-access-evals-", dir=eval_tmp) as raw:
        root = Path(raw)
        test_single_repository(root)
        test_single_application_defaults(root)
        test_explicit_developer_and_multiple_roles(root)
        test_signed_legacy_root_migration(root)
        test_legacy_root_migration_rolls_back(root)
        test_legacy_document_roots_are_rejected(root)
        test_participant_merge()
        test_multi_repository(root)
        test_failed_apply_removes_new_keys(root)
    print("project-write-access evals: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
