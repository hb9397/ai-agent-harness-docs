#!/usr/bin/env python3
"""Regression tests for the local humanize-korean adapter."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / "skills" / "humanize-korean" / "scripts" / "humanize_korean.py"


def run_script(*args: str) -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return json.loads(completed.stdout)


def test_preserves_tokens() -> None:
    text = "SFR-021은 2026-07-29에 .docs/api/SFR-021.md를 통해 관리됩니다.\n```bash\nnpm run build\n```"
    result = run_script("--text", text)
    assert result["status"] == "ok"
    for token in ["SFR-021", "2026-07-29", ".docs/api/SFR-021.md", "```bash\nnpm run build\n```"]:
        assert token in result["refined_text"]


def test_contextual_phrases_are_diagnostic_only() -> None:
    text = "도구를 통해 확인하고 시스템에 의해 기록합니다. 결론적으로, 결과를 요약합니다."
    result = run_script("--text", text)
    assert result["refined_text"] == text
    assert result["contextual_rewrites_applied"] is False
    assert [item["rule_id"] for item in result["diagnostics"]] == [
        "A-context-through",
        "A-context-passive-agent",
        "D-context-conclusion",
    ]


def test_document_refinement_is_proposal_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.md"
        original = "결론적으로, 이 기능은 중요한 역할을 수행할 수 있습니다."
        path.write_text(original, encoding="utf-8")
        result = run_script("--file", str(path), "--profile", "document-refinement")
        assert result["proposal_only"] is True
        assert path.read_text(encoding="utf-8") == original


def test_write_requires_explicit_approval_flag() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.md"
        original = "결론적으로, 이 기능은 중요한 역할을 수행할 수 있습니다."
        path.write_text(original, encoding="utf-8")
        result = run_script("--file", str(path), "--profile", "document-refinement", "--write-approved")
        assert result["status"] == "ok"
        assert path.read_text(encoding="utf-8") == result["refined_text"]


if __name__ == "__main__":
    test_preserves_tokens()
    test_contextual_phrases_are_diagnostic_only()
    test_document_refinement_is_proposal_only()
    test_write_requires_explicit_approval_flag()
    print("humanize-korean adapter tests passed")
