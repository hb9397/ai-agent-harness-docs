#!/usr/bin/env python3
"""Behavioral regression checks for the pre-commit scanner."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import re
import shutil
from pathlib import Path


sys.dont_write_bytecode = True
SKILL_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SCRIPT = SKILL_ROOT / "scripts" / "scan.py"
SHELL_SCRIPT = SKILL_ROOT / "scripts" / "scan.sh"


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        list(args),
        cwd=cwd,
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )


def init_repo(root: Path) -> None:
    run("git", "init", "-q", cwd=root)
    run("git", "config", "user.name", "Eval", cwd=root)
    run("git", "config", "user.email", "eval@example.invalid", cwd=root)


def build_git_fixture(tmp: Path) -> Path:
    repo = tmp / "repo with spaces"
    (repo / "app-a" / "nested").mkdir(parents=True)
    (repo / "app-b").mkdir()
    tracked = repo / "app-a" / "nested" / "tracked.py"
    tracked.write_text("print('initial')\n", encoding="utf-8")
    (repo / "app-b" / "outside.py").write_text("print('initial')\n", encoding="utf-8")
    init_repo(repo)
    run("git", "add", ".", cwd=repo)
    run("git", "commit", "-qm", "initial", cwd=repo)

    tracked.write_text("print('changed')  # TODO\n", encoding="utf-8")
    untracked = repo / "app-a" / "nested" / "new file.py"
    untracked.write_text("token = 'not-a-real-token'\n", encoding="utf-8")
    staged = repo / "app-a" / "nested" / "staged file.py"
    staged.write_text("requests.get('https://example.invalid')\n", encoding="utf-8")
    run("git", "add", str(staged.relative_to(repo)), cwd=repo)
    (repo / "app-b" / "outside.py").write_text("print('outside changed')\n", encoding="utf-8")
    return repo


def test_git_changes_and_scope(tmp: Path) -> None:
    repo = build_git_fixture(tmp)

    result = run(sys.executable, str(PYTHON_SCRIPT), str(repo / "app-a"), cwd=tmp)
    output = result.stdout
    assert "app-a/nested/tracked.py" in output, output
    assert "app-a/nested/new file.py" in output, output
    assert "app-a/nested/staged file.py" in output, output
    assert "app-b/outside.py" not in output, output
    assert "TODO" in output, output
    assert "requests.get" in output, output


def test_non_git_recursive(tmp: Path) -> None:
    root = tmp / "plain"
    nested = root / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "unsafe.py").write_text("try:\n    pass\nexcept Exception:\n    pass\n# TODO\n", encoding="utf-8")
    (nested / "test_unsafe.py").write_text("def test_it():\n    pass\n", encoding="utf-8")
    result = run(sys.executable, str(PYTHON_SCRIPT), str(root), cwd=tmp)
    output = result.stdout
    assert "비-git 재귀 전체 스캔" in output, output
    assert "unsafe.py" in output, output
    assert "TODO" in output, output
    assert "test_unsafe.py" in output, output


def test_no_changes_and_invalid_target(tmp: Path) -> None:
    repo = tmp / "clean"
    repo.mkdir()
    (repo / "clean.py").write_text("print('clean')\n", encoding="utf-8")
    init_repo(repo)
    run("git", "add", ".", cwd=repo)
    run("git", "commit", "-qm", "initial", cwd=repo)

    clean = run(sys.executable, str(PYTHON_SCRIPT), str(repo), cwd=tmp)
    assert "변경된 파일이 없습니다" in clean.stdout, clean.stdout

    missing = run(
        sys.executable,
        str(PYTHON_SCRIPT),
        str(tmp / "missing"),
        cwd=tmp,
        check=False,
    )
    assert missing.returncode == 2, missing.stdout
    assert "검사 대상 디렉토리가 없거나" in missing.stdout, missing.stdout


def test_shell_parity_when_available(tmp: Path) -> None:
    if shutil.which("bash") is None:
        return

    repo = build_git_fixture(tmp)
    python_result = run(
        sys.executable,
        str(PYTHON_SCRIPT),
        str(repo / "app-a"),
        cwd=tmp,
    )
    shell_result = run(
        "bash",
        str(SHELL_SCRIPT),
        str(repo / "app-a"),
        cwd=tmp,
        check=False,
    )
    if shell_result.returncode != 0:
        # A discovered bash may be WSL and unable to resolve a Windows path.
        if sys.platform == "win32":
            return
        raise AssertionError(shell_result.stdout)

    for marker in (
        "app-a/nested/tracked.py",
        "app-a/nested/new file.py",
        "app-a/nested/staged file.py",
        "## 1. 에러 처리",
        "## 2. 외부 호출",
        "## 3. 민감 정보",
        "## 4. TODO 주석",
        "## 5. 테스트 존재 여부",
        "=== 스캔 완료 ===",
    ):
        assert marker in python_result.stdout, python_result.stdout
        assert marker in shell_result.stdout, shell_result.stdout


def verbatim_upstream_paths(root: Path) -> set[str]:
    """Repo-relative paths imported unchanged from a pinned upstream commit."""
    provenance = root / "maintainer" / "upstreams" / "provenance"
    paths: set[str] = set()
    for file_map in sorted(provenance.glob("*/file-map.json")):
        data = json.loads(file_map.read_text(encoding="utf-8"))
        for entry in data.get("files", []):
            if entry.get("treatment") == "verbatim" and entry.get("local_path"):
                paths.add(entry["local_path"])
    return paths


def test_user_skill_frontmatter_contract() -> None:
    skills_root = SKILL_ROOT.parent
    for skill_file in sorted(skills_root.glob("*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        allowed = next(
            (line for line in frontmatter.splitlines() if line.startswith("allowed-tools:")),
            "",
        )
        assert "Bash" not in allowed, f"unrestricted Bash permission: {skill_file}"
        assert not re.search(r"(?:^|,\s*)Task(?:\s*,|$)", allowed), (
            f"legacy Task permission: {skill_file}"
        )

    # Verbatim upstream imports are governed by the pinned provenance manifest
    # and cannot be edited, so they are excluded here. The English word "Task"
    # appears in upstream prose without referring to the legacy tool.
    vendored = verbatim_upstream_paths(skills_root.parent)
    for markdown in sorted(skills_root.glob("**/*.md")):
        if markdown.relative_to(skills_root.parent).as_posix() in vendored:
            continue
        text = markdown.read_text(encoding="utf-8")
        assert not re.search(r"\bTask\b", text), f"legacy Task wording: {markdown}"

    for name in ("commit", "git-scoped-account", "impl-verify"):
        text = (skills_root / name / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        assert re.search(
            r"^disable-model-invocation:\s*true\s*$",
            frontmatter,
            re.MULTILINE,
        ), (
            f"side-effect skill must be explicit-only: {name}"
        )
        assert f"${name}" in text, f"Codex direct invocation example missing: {name}"
        assert f"/ai-agent-harness:{name}" in text, (
            f"Claude direct invocation example missing: {name}"
        )

    design = (skills_root / "design-doc" / "SKILL.md").read_text(encoding="utf-8")
    prototype_design = (
        skills_root / "design-prototype-docs" / "SKILL.md"
    ).read_text(encoding="utf-8")
    review = (skills_root / "multi-review" / "SKILL.md").read_text(encoding="utf-8")
    pre_commit = (skills_root / "pre-commit" / "SKILL.md").read_text(encoding="utf-8")
    assert "create-prototype 입력용" in design and "design-prototype-docs" in design
    assert "create-prototype" in prototype_design
    assert "pre-commit을 사용" in review
    assert "multi-review를 사용" in pre_commit


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="pre-commit-eval-") as raw:
        tmp = Path(raw)
        test_git_changes_and_scope(tmp)
        test_non_git_recursive(tmp)
        test_no_changes_and_invalid_target(tmp)
    with tempfile.TemporaryDirectory(prefix="pre-commit-parity-") as raw:
        test_shell_parity_when_available(Path(raw))
    test_user_skill_frontmatter_contract()
    print("pre-commit evals: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
