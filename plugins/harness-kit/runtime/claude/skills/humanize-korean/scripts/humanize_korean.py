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
import os
import re
import stat
import sys
import tempfile
from collections import Counter
from pathlib import Path


PROTECTED_PATTERNS = [
    re.compile(r"`[^`]+`"),
    re.compile(r"https?://[^\s)]+"),
    re.compile(r"(?<![\w./\\-])(?:\.{1,2}/|[A-Za-z]:\\|/)[^\s)]+"),
    re.compile(r"\b[A-Z]{2,}-\d+\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?(?:%|ms|초|분|시간|KB|MB|GB|자)?\b"),
    re.compile(r"\"[^\"]*\""),
    re.compile(r"'[^']*'"),
]

FAST_REPLACEMENTS = [
    ("중요한 역할을 수행할 수 있습니다", "중요한 역할을 할 수 있습니다"),
    ("중요한 역할을 수행합니다", "중요한 역할을 합니다"),
    ("시사하는 바가 큽니다", "의미가 있습니다"),
]

STANDARD_REPLACEMENTS = [
    *FAST_REPLACEMENTS,
    ("이에 있어서", "여기서"),
]

CONTEXTUAL_RULES = (
    {
        "rule_id": "A-context-through",
        "category": "A",
        "pattern": re.compile(r"~?[를을] 통해"),
        "reason": "수단·경로·매개 의미에 따라 자연스러운 서술이 달라져 문맥 확인이 필요합니다.",
        "suggestions": [
            "수단이면 `로/으로`를 검토합니다.",
            "경로나 매개가 핵심이면 원문을 유지합니다.",
            "행위 주체가 분명하면 능동형 동사 문장으로 다시 씁니다.",
        ],
    },
    {
        "rule_id": "A-context-passive-agent",
        "category": "A",
        "pattern": re.compile(r"에 의해"),
        "reason": "행위 주체와 피동 관계를 확인하지 않고 조사만 바꾸면 문법이나 의미가 달라질 수 있습니다.",
        "suggestions": [
            "실제 행위 주체를 확인한 뒤 능동문을 제안합니다.",
            "법률·학술 문맥의 정확한 피동 표현이면 원문을 유지합니다.",
        ],
    },
    {
        "rule_id": "D-context-conclusion",
        "category": "D",
        "pattern": re.compile(r"(?<![가-힣A-Za-z0-9_])결론적으로(?:,)?"),
        "reason": "빈 결말 관용구인지 실제 논리적 요약 표지인지 문단 관계를 확인해야 합니다.",
        "suggestions": [
            "새 정보 없이 결말만 예고하면 삭제를 제안합니다.",
            "앞선 근거를 요약하는 기능이 있으면 원문을 유지하거나 문맥에 맞는 연결어를 제안합니다.",
        ],
    },
)


def collect_protected(text: str) -> list[str]:
    found: list[str] = []
    for pattern in PROTECTED_PATTERNS:
        found.extend(m.group(0) for m in pattern.finditer(text))
    return sorted(set(found), key=lambda value: (len(value), value))


def protected_spans(text: str) -> list[tuple[int, int]]:
    spans = sorted(
        (match.start(), match.end())
        for pattern in PROTECTED_PATTERNS
        for match in pattern.finditer(text)
    )
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def mask_protected(text: str) -> tuple[str, dict[str, str]]:
    chunks: list[str] = []
    replacements: dict[str, str] = {}
    cursor = 0
    for index, (start, end) in enumerate(protected_spans(text)):
        marker = f"\ue000HK{index:X}\ue001"
        chunks.extend((text[cursor:start], marker))
        replacements[marker] = text[start:end]
        cursor = end
    chunks.append(text[cursor:])
    return "".join(chunks), replacements


def restore_protected(text: str, replacements: dict[str, str]) -> str:
    restored = text
    for marker, original in replacements.items():
        restored = restored.replace(marker, original)
    return restored


def refine_plain(text: str, mode: str) -> str:
    refined, protected = mask_protected(text)
    replacements = FAST_REPLACEMENTS if mode == "fast" else STANDARD_REPLACEMENTS
    for src, dst in replacements:
        refined = refined.replace(src, dst)
    if mode != "fast":
        refined = re.sub(r"(합니다\.)[ \t]+또한,[ \t]+", r"\1 ", refined)
    return restore_protected(refined, protected)


def diagnose_contextual(
    text: str,
    line_range: tuple[int, int] | None = None,
) -> list[dict[str, object]]:
    """Return context-sensitive findings without rewriting their spans."""
    diagnostics: list[dict[str, object]] = []
    fence_marker: str | None = None
    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        fence_match = re.match(r"^\s*(```|~~~)", line)
        if fence_match:
            marker = fence_match.group(1)
            if fence_marker is None:
                fence_marker = marker
            elif fence_marker == marker:
                fence_marker = None
            continue

        selected = line_range is None or line_range[0] <= line_number <= line_range[1]
        is_structural = fence_marker is not None or "|" in line or line.lstrip().startswith(">")
        if not selected or is_structural:
            continue

        spans = protected_spans(line)
        for rule in CONTEXTUAL_RULES:
            pattern = rule["pattern"]
            assert isinstance(pattern, re.Pattern)
            for match in pattern.finditer(line):
                if any(match.start() < end and start < match.end() for start, end in spans):
                    continue
                diagnostics.append(
                    {
                        "rule_id": rule["rule_id"],
                        "category": rule["category"],
                        "line": line_number,
                        "column": match.start() + 1,
                        "span": match.group(0),
                        "reason": rule["reason"],
                        "suggestions": list(rule["suggestions"]),
                        "action": "review-and-propose",
                    }
                )
    return diagnostics


def parse_redo_range(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)(?::|-)(\d+)", value)
    if not match:
        raise argparse.ArgumentTypeError("redo range must use START:END with 1-based line numbers")
    start, end = (int(part) for part in match.groups())
    if start < 1 or end < start:
        raise argparse.ArgumentTypeError("redo range must satisfy 1 <= START <= END")
    return start, end


def refine(text: str, mode: str = "standard", redo_range: tuple[int, int] | None = None) -> str:
    if mode not in {"fast", "standard", "redo"}:
        raise ValueError(f"unsupported mode: {mode}")
    if mode == "redo" and redo_range is None:
        raise ValueError("redo mode requires a line range")
    if mode != "redo" and redo_range is not None:
        raise ValueError("redo range is only valid in redo mode")

    lines = text.splitlines(keepends=True)
    if not lines and text == "":
        lines = []
    if mode == "redo" and redo_range and redo_range[1] > len(lines):
        raise ValueError(f"redo range ends at line {redo_range[1]}, but input has {len(lines)} lines")

    refined: list[str] = []
    fence_marker: str | None = None
    for line_number, line in enumerate(lines, start=1):
        fence_match = re.match(r"^\s*(```|~~~)", line)
        if fence_match:
            marker = fence_match.group(1)
            if fence_marker is None:
                fence_marker = marker
            elif fence_marker == marker:
                fence_marker = None
            refined.append(line)
            continue

        selected = redo_range is None or redo_range[0] <= line_number <= redo_range[1]
        is_structural = fence_marker is not None or "|" in line or line.lstrip().startswith(">")
        if not selected or is_structural:
            refined.append(line)
            continue
        effective_mode = "standard" if mode == "redo" else mode
        refined.append(refine_plain(line, effective_mode))

    return "".join(refined)


def change_rate(original: str, refined: str) -> float:
    if not original:
        return 0.0 if not refined else 1.0
    return 1.0 - difflib.SequenceMatcher(a=original, b=refined).ratio()


def validate_protected(original: str, refined_text: str) -> list[str]:
    original_counts = Counter(
        match.group(0)
        for pattern in PROTECTED_PATTERNS
        for match in pattern.finditer(original)
    )
    refined_counts = Counter(
        match.group(0)
        for pattern in PROTECTED_PATTERNS
        for match in pattern.finditer(refined_text)
    )
    missing: list[str] = []
    for token, count in original_counts.items():
        if token and refined_counts[token] < count:
            missing.append(token)
    return sorted(set(missing), key=lambda value: (len(value), value))


def read_text_exact(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def atomic_write_text(path: Path, text: str) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing to replace symlink: {path}")

    original_mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, original_mode)
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Conservative Korean prose refinement with protected-token and write-approval gates."
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--file", type=Path, help="UTF-8 input file; proposal-only unless --write-approved is set")
    input_group.add_argument("--text", help="inline text to refine without file writes")
    parser.add_argument(
        "--profile",
        default="general",
        choices=["general", "document-refinement"],
        help="document-refinement keeps the stricter artifact-refinement contract",
    )
    parser.add_argument(
        "--mode",
        default="standard",
        choices=["fast", "standard", "redo"],
        help="fast=minimal cleanup, standard=full cleanup, redo=standard cleanup in --redo-range only",
    )
    parser.add_argument(
        "--redo-range",
        type=parse_redo_range,
        metavar="START:END",
        help="1-based inclusive line range required by redo mode",
    )
    parser.add_argument(
        "--write-approved",
        action="store_true",
        help="record that the user approved replacing --file after validation",
    )
    args = parser.parse_args(argv)

    if args.write_approved and not args.file:
        parser.error("--write-approved requires --file")
    if args.mode == "redo" and args.redo_range is None:
        parser.error("--mode redo requires --redo-range START:END")
    if args.mode != "redo" and args.redo_range is not None:
        parser.error("--redo-range is only valid with --mode redo")

    original = read_text_exact(args.file) if args.file else args.text
    try:
        refined_text = refine(original, mode=args.mode, redo_range=args.redo_range)
    except ValueError as exc:
        parser.error(str(exc))
    diagnostics = diagnose_contextual(
        original,
        line_range=args.redo_range if args.mode == "redo" else None,
    )
    rate = change_rate(original, refined_text)
    missing = validate_protected(original, refined_text)
    warnings = []

    if rate > 0.30:
        warnings.append("change_rate_over_30_percent")
    if rate > 0.50:
        warnings.append("change_rate_over_50_percent_stop")
    if missing:
        warnings.append("protected_token_changed")
    if diagnostics:
        warnings.append("contextual_review_required")

    status = "ok"
    exit_code = 0
    if rate > 0.50 or missing:
        status = "blocked"
        exit_code = 2

    written = False
    write_error = None
    if args.file and args.write_approved and exit_code == 0:
        try:
            atomic_write_text(args.file, refined_text)
            written = True
        except (OSError, ValueError) as exc:
            status = "blocked"
            exit_code = 2
            write_error = str(exc)
            warnings.append("atomic_write_failed")

    result = {
        "status": status,
        "profile": args.profile,
        "mode": args.mode,
        "change_rate": round(rate, 4),
        "protected_tokens": collect_protected(original),
        "missing_protected_tokens": missing,
        "warnings": warnings,
        "diagnostics": diagnostics,
        "contextual_rewrites_applied": False,
        "proposal_only": bool(args.file and not args.write_approved),
        "write_approved": args.write_approved,
        "written": written,
        "write_error": write_error,
        "redo_range": list(args.redo_range) if args.redo_range else None,
        "refined_text": refined_text,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
