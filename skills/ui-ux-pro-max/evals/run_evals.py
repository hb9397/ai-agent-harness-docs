#!/usr/bin/env python3
"""Contract and behaviour evals for ui-ux-pro-max.

Contract checks guard the wording this skill must keep. Behaviour checks run the
imported upstream scripts for real, because a Markdown-only check cannot tell
whether the search tool still resolves its own data directory, refuses to
overwrite prior decisions, or reaches the network.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SEARCH = ROOT / "scripts" / "search.py"

NETWORK_MODULES = {
    "socket", "urllib", "urllib.request", "http", "http.client", "ftplib",
    "requests", "httpx", "aiohttp", "telnetlib", "smtplib", "xmlrpc",
}
PROCESS_CALLS = {"system", "popen", "spawn", "spawnl", "spawnv", "execv", "execl"}


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SEARCH), *args],
        cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True,
    )


def test_skill_contract_wording() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for required in (
        "allowed-tools: Read, Write, Glob, Grep",
        "STEP 0 — 적용 범위 확인",
        "기존 시스템이 있으면 그 규칙이 이 스킬의 추천보다 **우선**한다",
        "사용자 승인 없이\n프로젝트 파일을 만들지 않는다",
        ".ai-docs/design-system/{project-slug}/MASTER.md",
        "승인 전에는 덮어쓰지 않는다",
        "스택을 **임의로 가정하지 않는다.**",
        "0건 검색을 데이터가 나온 것처럼 제시하지 않는다",
        "Python을 package manager로 자동 설치하지 않는다",
        "네트워크에서 디자인 데이터를 내려받지 않는다",
        "최외곽 산출물 생성자",
    ):
        assert required in skill, f"contract wording missing: {required!r}"

    for public_name in ("design-prototype-docs", "create-prototype", "frontend-design",
                        "motion-design", "impl-verify"):
        assert f"`{public_name}`" in skill, f"public handoff name missing: {public_name}"


def test_skill_has_no_platform_specific_paths() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for banned in ("${CLAUDE_PLUGIN_ROOT}", ".claude/skills", ".agents/skills", "CLAUDE_PLUGIN_ROOT"):
        assert banned not in skill, f"platform-specific path leaked into SKILL.md: {banned}"
    assert "{skill_dir}" in skill, "SKILL.md must resolve scripts relative to its own directory"
    assert "model:" not in skill.split("---")[1], "frontmatter must stay model-neutral"


def test_scripts_declare_no_network_or_process_surface() -> None:
    for path in sorted(ROOT.glob("scripts/**/*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in NETWORK_MODULES, f"{path.name}: network import {alias.name}"
                    assert alias.name != "subprocess", f"{path.name}: subprocess import"
            elif isinstance(node, ast.ImportFrom):
                root_mod = (node.module or "").split(".")[0]
                assert root_mod not in NETWORK_MODULES, f"{path.name}: network import {node.module}"
                assert root_mod != "subprocess", f"{path.name}: subprocess import"
            elif isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                assert name not in {"eval", "exec", "compile"}, f"{path.name}: dynamic execution {name}"
                assert name not in PROCESS_CALLS, f"{path.name}: process call {name}"


def test_data_and_reference_assets_are_present() -> None:
    assert (ROOT / "references" / "quick-reference.md").is_file()
    assert (ROOT / "references" / "pro-rules.md").is_file()
    csvs = list(ROOT.glob("data/**/*.csv"))
    assert len(csvs) >= 35, f"expected the full imported dataset, found {len(csvs)}"
    assert (ROOT / "data" / "stacks").is_dir()


def test_search_resolves_assets_from_unrelated_cwd() -> None:
    """The tool must find its own data no matter where it is invoked from."""
    with tempfile.TemporaryDirectory() as tmp:
        completed = run(["saas dashboard analytics", "--domain", "style", "-n", "2"], Path(tmp))
        assert completed.returncode == 0, completed.stderr
        assert "Found:" in completed.stdout
        assert "0 results" not in completed.stdout


def test_zero_result_search_refuses_to_fabricate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        completed = run(["zzzqqqxxx-no-such-domain-term", "--domain", "style"], Path(tmp))
        assert completed.returncode == 0, completed.stderr
        assert "0 results" in completed.stdout
        assert "No matches" in completed.stdout


def test_persist_writes_only_under_requested_output_dir() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / ".ai-docs").mkdir()
        completed = run(
            ["medical booking accessibility", "--design-system", "--persist",
             "-p", "Clinic", "--output-dir", ".ai-docs"],
            base,
        )
        assert completed.returncode == 0, completed.stderr
        master = base / ".ai-docs" / "design-system" / "clinic" / "MASTER.md"
        assert master.is_file(), "persist must follow the .ai-docs/design-system contract path"
        outside = [p for p in base.rglob("*") if p.is_file() and ".ai-docs" not in p.parts]
        assert not outside, f"persist wrote outside the requested output dir: {outside}"


def test_persist_does_not_silently_overwrite_prior_decisions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / ".ai-docs").mkdir()
        args = ["medical booking accessibility", "--design-system", "--persist",
                "-p", "Clinic", "--output-dir", ".ai-docs"]
        assert run(args, base).returncode == 0
        master = base / ".ai-docs" / "design-system" / "clinic" / "MASTER.md"
        before = master.read_bytes()
        second = run(["fintech trading terminal dense", "--design-system", "--persist",
                      "-p", "Clinic", "--output-dir", ".ai-docs"], base)
        assert second.returncode == 0, second.stderr
        assert master.read_bytes() == before, "existing MASTER.md must survive an unforced rerun"
        assert "already exists" in second.stdout


def test_project_slug_cannot_escape_the_output_dir() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        target = base / "workspace"
        (target / ".ai-docs").mkdir(parents=True)
        completed = run(
            ["test", "--design-system", "--persist", "-p", "../../escaped", "--output-dir", ".ai-docs"],
            target,
        )
        assert completed.returncode == 0, completed.stderr
        escaped = [p for p in base.rglob("*") if p.is_file() and "workspace" not in p.parts]
        assert not escaped, f"slug escaped the workspace: {escaped}"


def main() -> int:
    tests = [
        test_skill_contract_wording,
        test_skill_has_no_platform_specific_paths,
        test_scripts_declare_no_network_or_process_surface,
        test_data_and_reference_assets_are_present,
        test_search_resolves_assets_from_unrelated_cwd,
        test_zero_result_search_refuses_to_fabricate,
        test_persist_writes_only_under_requested_output_dir,
        test_persist_does_not_silently_overwrite_prior_decisions,
        test_project_slug_cannot_escape_the_output_dir,
    ]
    for test in tests:
        test()
    print(f"ui-ux-pro-max evals: PASS ({len(tests)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
