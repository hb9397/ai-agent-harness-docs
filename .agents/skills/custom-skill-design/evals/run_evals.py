#!/usr/bin/env python3
"""Static contract checks for the manager-only custom-skill-design skill."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    skill = read("SKILL.md")
    checklist = read("prompts/checklist.md")
    principles = read("prompts/design-principles.md")
    skill_template = read("templates/SKILL-template.md")
    optimizer = read("prompts/description-optimizer.md")
    eval_loop = read("prompts/eval-loop.md")

    require("skills/{skill-name}/" in skill, "user canonical path is missing")
    require(
        "maintainer/skills/{skill-name}/" in skill,
        "maintainer canonical path is missing",
    )
    require(
        skill.index("파일을 만들기 전에 먼저 배포 대상을 분류한다")
        < skill.index("### 3-3. 테스트 케이스 초안"),
        "canonical area must be classified before files are created",
    )
    require(
        "구조 점검만` 진입이면" in skill and "파일을 수정하지 않는다" in skill,
        "audit-only entry must remain read-only",
    )
    require(
        "Codex CLI/App" in skill and "Claude Code/Desktop Code" in skill,
        "both platform execution surfaces must be documented",
    )
    require(
        "cat [경로]/SKILL.md" not in skill and "2>/dev/null" not in skill,
        "manager workflow must not depend on POSIX-only inspection commands",
    )
    require(
        "harness-plugin-maintainer/scripts/" not in skill
        and "`harness-plugin-maintainer`를 명시 호출" in skill,
        "manager skills must hand off by public skill contract",
    )
    require(
        "제한 없는 `Bash` 사전 승인 금지" in principles,
        "skill design principles must forbid unrestricted Bash pre-approval",
    )
    require(
        "allowed-tools: Read, Write, Glob, Grep, Bash" not in principles
        and "Read, Write, Glob, Grep, Bash" not in skill_template,
        "new skill examples must not regenerate unrestricted Bash",
    )
    require(
        "2>/dev/null" not in principles
        and "2>/dev/null" not in skill_template
        and "cat package.json" not in principles,
        "skill examples must not require POSIX-only inspection commands",
    )
    require(
        "allowed-tools에 제한 없는 Bash" in checklist
        and "플랫폼별 직접 호출 예시" in checklist,
        "review checklist must cover shell permission and manual invocation",
    )
    require(
        "python -m scripts.run_loop" not in optimizer,
        "optimizer must not invoke a missing bundled module",
    )
    require(
        "자동 최적화 runner가 포함되어 있지 않다" in optimizer,
        "runner availability must be stated truthfully",
    )
    require(
        "제공하지 않는 표면에서는 `null`" in eval_loop,
        "missing telemetry must not be fabricated",
    )

    print("custom-skill-design contract evals passed")


if __name__ == "__main__":
    main()
