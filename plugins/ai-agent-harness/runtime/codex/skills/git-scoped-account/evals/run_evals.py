#!/usr/bin/env python3
"""Behavioral safety checks for exact include handling and rollback."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import re
from pathlib import Path


sys.dont_write_bytecode = True
SKILL_ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def values(repo: Path) -> list[str]:
    result = git(repo, "config", "--local", "--get-all", "include.path", check=False)
    return result.stdout.splitlines() if result.returncode == 0 else []


def normalize(repo: Path, target: str) -> None:
    matches = git(
        repo,
        "config",
        "--local",
        "--fixed-value",
        "--get-all",
        "include.path",
        target,
        check=False,
    )
    assert matches.returncode in (0, 1), matches.stderr
    count = len(matches.stdout.splitlines()) if matches.returncode == 0 else 0
    if count == 0:
        git(repo, "config", "--local", "--add", "include.path", target)
    elif count > 1:
        git(
            repo,
            "config",
            "--local",
            "--fixed-value",
            "--unset-all",
            "include.path",
            target,
        )
        git(repo, "config", "--local", "--add", "include.path", target)


def test_exact_value_preserves_unrelated(tmp: Path) -> None:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    unrelated_a = "C:/other/[literal].gitconfig"
    target = "C:/dev/project-a/.gitconfig-scoped"
    unrelated_b = "../team.gitconfig"
    for value in (unrelated_a, target, unrelated_b, target):
        git(repo, "config", "--local", "--add", "include.path", value)

    normalize(repo, target)
    actual = values(repo)
    assert actual.count(target) == 1, actual
    assert [item for item in actual if item != target] == [unrelated_a, unrelated_b], actual
    before = (repo / ".git" / "config").read_bytes()
    normalize(repo, target)
    assert (repo / ".git" / "config").read_bytes() == before


def test_byte_exact_rollback(tmp: Path) -> None:
    repo = tmp / "rollback"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "--local", "--add", "include.path", "../keep.gitconfig")
    local_config = repo / ".git" / "config"
    original = local_config.read_bytes()
    normalize(repo, "C:/temporary/.gitconfig-scoped")
    assert local_config.read_bytes() != original
    local_config.write_bytes(original)
    assert local_config.read_bytes() == original
    assert values(repo) == ["../keep.gitconfig"]


def test_document_contract() -> None:
    commands = (SKILL_ROOT / "prompts" / "commands.md").read_text(encoding="utf-8")
    assert "--fixed-value" in commands
    assert "byte" in commands
    assert "롤백" in commands
    unsafe_line = re.compile(
        r"^\s*(?![-`>]).*\bconfig\b.*--local\s+--unset-all\s+include\.path(?:\s*$|[\"'`])",
        re.MULTILINE,
    )
    assert not unsafe_line.search(commands), "unsafe value-less include removal command remains"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="git-scoped-account-eval-") as raw:
        tmp = Path(raw)
        test_exact_value_preserves_unrelated(tmp)
        test_byte_exact_rollback(tmp)
    test_document_contract()
    print("git-scoped-account evals: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
