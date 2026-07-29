#!/usr/bin/env python3
"""Deterministic helper for Korean document refinement guards.

This script is intentionally conservative. It provides token protection,
small phrase-level cleanup, and change-rate gating for tests/smoke checks.
The agent still owns final writing judgment.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path


PROTECTED_PATTERNS = [
    re.compile(r"`[^`]+`"),
    re.compile(r"https?://[^\s)]+"),
    re.compile(r"(?:^|[\s(])(?:\.{1,2}/|[A-Za-z]:\\|/)[^\s)]+"),
    re.compile(r"\b[A-Z]{2,}-\d+\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?(?:%|ms|초|분|시간|KB|MB|GB|자)?\b"),
    re.compile(r"\"[^\"]*\""),
    re.compile(r"'[^']*'"),
]

REPLACEMENTS = [
    ("이에 있어서", "여기서"),
    ("~를 통해", "~로"),
    ("를 통해", "로"),
    ("을 통해", "으로"),
    ("에 의해", "가"),
    ("수행할 수 있습니다", "수행할 수 있습니다"),
    ("진행할 수 있습니다", "진행할 수 있습니다"),
    ("중요한 역할을 수행합니다", "중요한 역할을 합니다"),
    ("중요한 역할을 수행할 수 있습니다", "중요한 역할을 할 수 있습니다"),
    ("시사하는 바가 큽니다", "의미가 있습니다"),
    ("결론적으로, ", ""),
    ("결론적으로 ", ""),
]


def split_fenced_blocks(text: str) -> list[tuple[bool, str]]:
    parts: list[tuple[bool, str]] = []
    cursor = 0
    for match in re.finditer(r"```.*?```", text, flags=re.DOTALL):
        if match.start() > cursor:
            parts.append((False, text[cursor : match.start()]))
        parts.append((True, match.group(0)))
        cursor = match.end()
    if cursor < len(text):
        parts.append((False, text[cursor:]))
    return parts


def collect_protected(text: str) -> list[str]:
    found: list[str] = []
    for pattern in PROTECTED_PATTERNS:
        found.extend(m.group(0).strip() for m in pattern.finditer(text))
    return sorted(set(found), key=lambda value: (len(value), value))


def refine_plain(text: str) -> str:
    refined = text
    for src, dst in REPLACEMENTS:
        refined = refined.replace(src, dst)
    refined = re.sub(r"(합니다\.)\s+또한,\s+", r"\1 ", refined)
    refined = re.sub(r"\s{2,}", " ", refined)
    return refined


def refine(text: str) -> str:
    chunks = []
    for fenced, value in split_fenced_blocks(text):
        chunks.append(value if fenced else refine_plain(value))
    return "".join(chunks)


def change_rate(original: str, refined: str) -> float:
    if not original:
        return 0.0 if not refined else 1.0
    return 1.0 - difflib.SequenceMatcher(a=original, b=refined).ratio()


def validate_protected(original: str, refined_text: str) -> list[str]:
    missing = []
    for token in collect_protected(original):
        if token and token not in refined_text:
            missing.append(token)
    return missing


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path)
    parser.add_argument("--text")
    parser.add_argument("--profile", default="general", choices=["general", "document-refinement"])
    parser.add_argument("--mode", default="standard", choices=["fast", "standard", "redo"])
    parser.add_argument("--write-approved", action="store_true")
    args = parser.parse_args(argv)

    if bool(args.file) == bool(args.text):
        parser.error("provide exactly one of --file or --text")

    original = args.file.read_text(encoding="utf-8") if args.file else args.text
    refined_text = refine(original)
    rate = change_rate(original, refined_text)
    missing = validate_protected(original, refined_text)
    warnings = []

    if rate > 0.30:
        warnings.append("change_rate_over_30_percent")
    if rate > 0.50:
        warnings.append("change_rate_over_50_percent_stop")
    if missing:
        warnings.append("protected_token_changed")

    status = "ok"
    exit_code = 0
    if rate > 0.50 or missing:
        status = "blocked"
        exit_code = 2

    if args.profile == "document-refinement" and args.file and args.write_approved and exit_code == 0:
        args.file.write_text(refined_text, encoding="utf-8")
    elif args.profile != "document-refinement" and args.file and args.write-approved and exit_code == 0:
        args.file.write_text(refined_text, encoding="utf-8")

    result = {
        "status": status,
        "profile": args.profile,
        "mode": args.mode,
        "change_rate": round(rate, 4),
        "protected_tokens": collect_protected(original),
        "missing_protected_tokens": missing,
        "warnings": warnings,
        "proposal_only": args.profile == "document-refinement" and not args.write_approved,
        "refined_text": refined_text,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
