#!/usr/bin/env python3
"""Cross-platform project rule scanner for the pre-commit skill.

Usage:
    python scan.py [target-directory]

Inside a Git worktree, only staged, unstaged, and untracked files within the
requested target boundary are scanned. Outside Git, code files below the target
directory are scanned recursively.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Iterable, Pattern, Sequence


CODE_SUFFIXES = {".java", ".kt", ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"}
EXCLUDED_DIRS = {".git", "node_modules"}
MAX_TEXT_FILE_BYTES = 2_000_000

EMPTY_CATCH = re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}")
EXCEPT_LINE = re.compile(r"except([^:]*)?:\s*$")
CATCH_OPEN = re.compile(r"catch\s*(\([^)]*\))?\s*\{")
IGNORE_COMMENT = re.compile(r"//\s*ignore|#\s*ignore|#\s*noqa", re.IGNORECASE)
EXTERNAL_CALL = re.compile(r"fetch\(|axios\.|requests\.|HttpClient|http\.Get|http\.Post")
SECRET_ASSIGNMENT = re.compile(
    r"""(password|apikey|api_key|secret|token)\s*[:=]\s*["']""",
    re.IGNORECASE,
)
SECRET_EXCLUSION = re.compile(r"test|mock|example|placeholder|TODO|env\.", re.IGNORECASE)
TODO_MARKER = re.compile(r"TODO|FIXME|HACK|XXX")
TODO = re.compile(r"TODO")
TODO_METADATA = re.compile(r"TODO@|TODO\(|#[0-9]")
SENSITIVE_PATH = re.compile(r"\.env|credential|secret|application\.yml|application\.properties")
BUSINESS_EXCLUSION = re.compile(r"test|spec|mock|fixture|\.env|\.md$|\.json$|\.ya?ml$")


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    command = ["git", "-C", os.fspath(root), *args]
    try:
        return subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        # Match the shell implementation: if Git is unavailable, treat the
        # target as a regular directory and use the recursive fallback.
        return subprocess.CompletedProcess(command, 127, b"", b"")


def _git_text(root: Path, *args: str) -> str | None:
    result = _run_git(root, *args)
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="surrogateescape").strip()


def _nul_paths(result: subprocess.CompletedProcess[bytes]) -> list[str]:
    if result.returncode != 0:
        return []
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    ]


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _git_context(target: Path) -> tuple[Path, str] | None:
    inside = _git_text(target, "rev-parse", "--is-inside-work-tree")
    if inside != "true":
        return None
    raw_root = _git_text(target, "rev-parse", "--show-toplevel")
    if not raw_root:
        return None
    repo_root = Path(raw_root).resolve()
    relative = os.path.relpath(target, repo_root)
    pathspec = "." if relative == "." else Path(relative).as_posix()
    return repo_root, pathspec


def _git_changed_files(repo_root: Path, pathspec: str) -> list[str]:
    commands = (
        ("diff", "--name-only", "-z", "--diff-filter=ACMRD", "--", pathspec),
        ("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMRD", "--", pathspec),
        ("ls-files", "--others", "--exclude-standard", "-z", "--", pathspec),
    )
    return _dedupe(
        path
        for command in commands
        for path in _nul_paths(_run_git(repo_root, *command))
    )


def _repo_file(repo_root: Path, git_path: str) -> Path:
    return repo_root.joinpath(*PurePosixPath(git_path).parts)


def _is_safe_file(path: Path, boundary: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    try:
        path.resolve(strict=True).relative_to(boundary.resolve(strict=True))
    except (OSError, ValueError):
        return False
    return True


def _iter_code_files(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*")
            if _is_safe_file(path, root)
            and path.suffix.lower() in CODE_SUFFIXES
            and not EXCLUDED_DIRS.intersection(path.relative_to(root).parts)
        ),
        key=lambda path: path.as_posix(),
    )


def _display_name(path: Path, display: str | None) -> str:
    return display if display is not None else os.fspath(path)


def _matching_lines(
    files: Sequence[tuple[Path, str | None]],
    pattern: Pattern[str],
    *,
    exclude: Pattern[str] | None = None,
    limit: int | None = None,
) -> list[str]:
    matches: list[str] = []
    for path, display in files:
        try:
            if path.stat().st_size > MAX_TEXT_FILE_BYTES:
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            if pattern.search(line) and not (exclude and exclude.search(line)):
                matches.append(f"{_display_name(path, display)}:{line_number}:{line}")
                if limit is not None and len(matches) >= limit:
                    return matches
    return matches


def _print_matches(matches: Sequence[str], *, empty: str | None = None) -> None:
    if matches:
        print("\n".join(matches))
    elif empty is not None:
        print(empty)


def _is_test_file(path: Path) -> bool:
    name = path.name
    return (
        bool(re.match(r".*Test\..*", name))
        or bool(re.match(r".*Spec\..*", name))
        or ".test." in name
        or ".spec." in name
        or name.startswith("test_")
    )


def _test_files(target: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in target.rglob("*")
            if _is_safe_file(path, target)
            and _is_test_file(path)
            and not EXCLUDED_DIRS.intersection(path.relative_to(target).parts)
        ),
        key=lambda path: path.as_posix(),
    )[:20]


def scan(target_input: str) -> int:
    target = Path(target_input).expanduser()
    if not target.is_dir():
        print(
            f"오류: 검사 대상 디렉토리가 없거나 디렉토리가 아닙니다: {target_input}",
            file=sys.stderr,
        )
        return 2

    try:
        target = target.resolve(strict=True)
    except OSError:
        print(f"오류: 검사 대상 경로를 해석할 수 없습니다: {target_input}", file=sys.stderr)
        return 2

    print("=== 프로젝트 룰 검사 스캔 ===")

    git_context = _git_context(target)
    changed_files: list[str] = []
    if git_context is not None:
        repo_root, pathspec = git_context
        changed_files = _git_changed_files(repo_root, pathspec)
        print("## 변경 파일 목록")
        if not changed_files:
            print("확인된 대상 경계에 변경된 파일이 없습니다. 검사를 종료합니다.")
            return 0
        print("\n".join(changed_files))
        print()

        code_files = [
            (_repo_file(repo_root, git_path), git_path)
            for git_path in changed_files
            if _is_safe_file(_repo_file(repo_root, git_path), target)
            and _repo_file(repo_root, git_path).suffix.lower() in CODE_SUFFIXES
        ]
        if not code_files:
            print("변경된 코드 파일이 없습니다 (md/yml/json 등 비코드 파일만 변경됨). 검사를 종료합니다.")
            return 0

        print(f"대상 코드 파일 ({len(code_files)}개):")
        for _, display in code_files:
            print(f"  {display}")
        print()
    else:
        print(f"대상: {target} (비-git 재귀 전체 스캔)")
        print()
        code_files = [(path, None) for path in _iter_code_files(target)]

    print("## 1. 에러 처리")
    print()
    print("### 빈 catch/except 블록")
    _print_matches(_matching_lines(code_files, EMPTY_CATCH))
    _print_matches(_matching_lines(code_files, EXCEPT_LINE))
    _print_matches(_matching_lines(code_files, CATCH_OPEN, limit=20))
    print("(위 결과 중 빈 블록 확인 필요)")
    print()

    print("### 에러 무시 주석 (// ignore, # noqa 등)")
    _print_matches(_matching_lines(code_files, IGNORE_COMMENT), empty="(없음)")
    print()

    print("## 2. 외부 호출 (타임아웃 확인 필요)")
    print()
    _print_matches(_matching_lines(code_files, EXTERNAL_CALL, limit=20), empty="(없음)")
    print()

    print("## 3. 민감 정보")
    print()
    print("### 하드코딩된 비밀번호/키/토큰")
    _print_matches(
        _matching_lines(
            code_files,
            SECRET_ASSIGNMENT,
            exclude=SECRET_EXCLUSION,
            limit=20,
        ),
        empty="(없음)",
    )
    print()

    print("### .env / 설정 파일 변경")
    if git_context is not None:
        sensitive = [path for path in changed_files if SENSITIVE_PATH.search(path)]
        _print_matches(sensitive, empty="(없음)")
    else:
        print("(git 변경 목록 없음)")
    print()

    print("## 4. TODO 주석")
    print()
    print("### 모든 TODO/FIXME/HACK")
    _print_matches(_matching_lines(code_files, TODO_MARKER, limit=20), empty="(없음)")
    print()

    print("### 기한 없는 TODO")
    _print_matches(
        _matching_lines(code_files, TODO, exclude=TODO_METADATA, limit=20),
        empty="(없음)",
    )
    print()

    print("## 5. 테스트 존재 여부")
    print()
    print("### 변경된 비즈니스 로직 파일")
    if git_context is not None:
        business = [path for path in changed_files if not BUSINESS_EXCLUSION.search(path)]
        _print_matches(business, empty="(없음)")
    else:
        print("(git 변경 목록 없음)")
    print()

    print("### 테스트 파일 목록")
    _print_matches([os.fspath(path) for path in _test_files(target)], empty="(없음)")
    print()

    print("=== 스캔 완료 ===")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        print("사용: python scan.py [대상 디렉토리]", file=sys.stderr)
        return 2
    return scan(args[0] if args else ".")


if __name__ == "__main__":
    raise SystemExit(main())
