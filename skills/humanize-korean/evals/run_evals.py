#!/usr/bin/env python3
"""Regression evals for the deterministic humanize-korean helper."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "humanize_korean.py"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPT.parent))

import humanize_korean  # noqa: E402


def run(args: list[str], *, cwd: Path = ROOT, expect: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    if completed.returncode != expect:
        raise AssertionError(
            f"expected exit {expect}, got {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed


def parse_json(stdout: str) -> dict:
    return json.loads(stdout)


def test_general_file_defaults_to_proposal_without_crash() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        source = Path(temporary) / "artifact.md"
        original = "결론적으로, 이 기능은 중요한 역할을 수행할 수 있습니다.\n"
        source.write_text(original, encoding="utf-8")
        report = parse_json(run([str(SCRIPT), "--file", str(source)]).stdout)
        assert report["status"] == "ok"
        assert report["proposal_only"] is True
        assert report["written"] is False
        assert report["contextual_rewrites_applied"] is False
        assert [item["rule_id"] for item in report["diagnostics"]] == [
            "D-context-conclusion"
        ]
        assert source.read_text(encoding="utf-8") == original


def test_approved_file_write_is_atomic_and_preserves_newlines() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        source = Path(temporary) / "artifact.md"
        source.write_bytes(
            "결론적으로, 이 기능은 중요한 역할을 수행할 수 있습니다.\r\n두 번째 줄입니다.\r\n".encode("utf-8")
        )
        report = parse_json(
            run([str(SCRIPT), "--file", str(source), "--write-approved"]).stdout
        )
        assert report["proposal_only"] is False
        assert report["write_approved"] is True
        assert report["written"] is True
        written = source.read_bytes()
        assert b"\r\n" in written
        decoded = written.decode("utf-8")
        assert "결론적으로" in decoded
        assert "중요한 역할을 할 수 있습니다" in decoded

        replace_calls: list[tuple[Path, Path]] = []
        original_replace: Callable[[str | bytes | Path, str | bytes | Path], None] = humanize_korean.os.replace

        def observe_replace(source_path, destination_path):
            source_temp = Path(source_path)
            destination = Path(destination_path)
            assert source_temp.parent == destination.parent
            replace_calls.append((source_temp, destination))
            original_replace(source_path, destination_path)

        humanize_korean.os.replace = observe_replace
        try:
            humanize_korean.atomic_write_text(source, "원자적 교체 결과\r\n")
        finally:
            humanize_korean.os.replace = original_replace
        assert replace_calls and replace_calls[0][1] == source
        assert source.read_bytes() == "원자적 교체 결과\r\n".encode("utf-8")
        assert not replace_calls[0][0].exists()


def test_fast_standard_and_redo_are_distinct() -> None:
    original = (
        "결론적으로, 이 기능은 중요한 역할을 수행할 수 있습니다.\n"
        "이에 있어서 두 번째 작업은 도구를 통해 진행할 수 있습니다.\n"
    )
    fast = humanize_korean.refine(original, mode="fast")
    standard = humanize_korean.refine(original, mode="standard")
    redo = humanize_korean.refine(original, mode="redo", redo_range=(2, 2))

    assert fast != standard
    assert "결론적으로" in fast
    assert "결론적으로" in standard
    assert "도구를 통해" in standard
    assert "이에 있어서" in fast
    assert "이에 있어서" not in standard
    assert redo.splitlines(keepends=True)[0] == original.splitlines(keepends=True)[0]
    assert redo.splitlines(keepends=True)[1] == standard.splitlines(keepends=True)[1]


def test_protected_tokens_code_quotes_and_tables_are_preserved() -> None:
    original = (
        "SFR-021은 2026-07-29에 .ai-docs/api/SFR-021.md와 `결론적으로, 실행`을 사용합니다.\n"
        "\"결론적으로, 인용을 통해 수행할 수 있습니다\"와 https://example.com/a?q=30을 보존합니다.\n"
        "| ID | 설명 |\n"
        "| --- | --- |\n"
        "| SFR-021 | 결론적으로, 표를 통해 관리합니다. |\n"
        "```python\n"
        "print('결론적으로, 코드를 통해 수행할 수 있습니다')\n"
        "```\n"
        "결론적으로, 본문은 중요한 역할을 수행할 수 있습니다.\n"
    )
    refined = humanize_korean.refine(original, mode="standard")

    assert humanize_korean.validate_protected(original, refined) == []
    for token in humanize_korean.collect_protected(original):
        assert refined.count(token) >= original.count(token)
    assert "| SFR-021 | 결론적으로, 표를 통해 관리합니다. |" in refined
    assert "print('결론적으로, 코드를 통해 수행할 수 있습니다')" in refined
    assert "\"결론적으로, 인용을 통해 수행할 수 있습니다\"" in refined
    assert "결론적으로, 본문은 중요한 역할을 할 수 있습니다." in refined

    diagnostics = humanize_korean.diagnose_contextual(original)
    assert [(item["rule_id"], item["line"]) for item in diagnostics] == [
        ("D-context-conclusion", 9)
    ]


def test_context_sensitive_phrases_are_diagnosed_without_rewrite() -> None:
    original = (
        "사용자는 터널을 통해 이동합니다.\n"
        "결과는 시스템에 의해 생성됩니다.\n"
        "결론적으로, 이 문단은 앞선 근거를 요약합니다.\n"
    )
    report = parse_json(run([str(SCRIPT), "--text", original]).stdout)

    assert report["refined_text"] == original
    assert report["contextual_rewrites_applied"] is False
    assert "contextual_review_required" in report["warnings"]
    assert [
        (item["rule_id"], item["line"], item["column"], item["span"], item["action"])
        for item in report["diagnostics"]
    ] == [
        ("A-context-through", 1, 8, "을 통해", "review-and-propose"),
        ("A-context-passive-agent", 2, 8, "에 의해", "review-and-propose"),
        ("D-context-conclusion", 3, 1, "결론적으로,", "review-and-propose"),
    ]
    assert all(item["reason"] for item in report["diagnostics"])
    assert all(len(item["suggestions"]) >= 2 for item in report["diagnostics"])
    assert humanize_korean.diagnose_contextual("소결론적으로 구분한 표제입니다.") == []


def test_redo_diagnostics_stay_inside_selected_range() -> None:
    original = (
        "결론적으로, 첫 번째 문장입니다.\n"
        "두 번째 작업은 도구를 통해 진행합니다.\n"
    )
    report = parse_json(
        run(
            [
                str(SCRIPT),
                "--text",
                original,
                "--mode",
                "redo",
                "--redo-range",
                "2:2",
            ]
        ).stdout
    )

    assert [(item["rule_id"], item["line"]) for item in report["diagnostics"]] == [
        ("A-context-through", 2)
    ]


def test_installed_skill_has_no_manager_repo_path_dependency() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        installed_skill = temporary_root / "plugin-cache" / "humanize-korean"
        unrelated_cwd = temporary_root / "project"
        target = unrelated_cwd / "artifact.md"
        shutil.copytree(SKILL, installed_skill)
        unrelated_cwd.mkdir()
        original = "결론적으로, 설치된 스킬은 중요한 역할을 수행할 수 있습니다.\n"
        target.write_text(original, encoding="utf-8")

        report = parse_json(
            run(
                [
                    str(installed_skill / "scripts" / "humanize_korean.py"),
                    "--file",
                    str(target),
                    "--profile",
                    "document-refinement",
                ],
                cwd=unrelated_cwd,
            ).stdout
        )
        assert report["proposal_only"] is True
        assert report["written"] is False
        assert report["diagnostics"][0]["rule_id"] == "D-context-conclusion"
        assert target.read_text(encoding="utf-8") == original


def main() -> int:
    tests = [
        test_general_file_defaults_to_proposal_without_crash,
        test_approved_file_write_is_atomic_and_preserves_newlines,
        test_fast_standard_and_redo_are_distinct,
        test_protected_tokens_code_quotes_and_tables_are_preserved,
        test_context_sensitive_phrases_are_diagnosed_without_rewrite,
        test_redo_diagnostics_stay_inside_selected_range,
        test_installed_skill_has_no_manager_repo_path_dependency,
    ]
    for test in tests:
        test()
    print("humanize-korean evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
