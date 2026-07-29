#!/usr/bin/env python3
"""Static safety contract checks for the prototype template."""

from __future__ import annotations

import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def executable_lines(text: str) -> list[str]:
    """Return non-prose assignment/markup lines that could be copied as code."""
    return [
        line
        for line in text.splitlines()
        if not line.lstrip().startswith(("-", ">", "#", "<!--"))
    ]


def main() -> int:
    template = (ROOT / "references" / "html-template.md").read_text(encoding="utf-8")
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    code = "\n".join(executable_lines(template))

    assert not re.search(r"<[^>]+\sstyle\s*=", code, re.IGNORECASE), "inline style remains"
    assert not re.search(r"<[^>]+\son[a-z]+\s*=", code, re.IGNORECASE), "inline handler remains"
    assert not re.search(
        r"\.(?:innerHTML|outerHTML)\s*=|insertAdjacentHTML\s*\(|document\.write\s*\(",
        code,
    ), "unsafe HTML sink remains in copyable example"
    for required in ("textContent", "createElement", "replaceChildren", "addEventListener"):
        assert required in template, f"safe DOM primitive missing: {required}"
    for required in ("\\u003c", "innerHTML", "인라인 `on*`"):
        assert required in skill, f"SKILL safety contract missing: {required}"

    legacy = ROOT / "examples" / "SFR-018.html"
    assert legacy.exists() and legacy.stat().st_size > 0, "protected legacy example was removed"
    print("create-prototype evals: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
