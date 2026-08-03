"""Deterministic static contract checks for the commit workflow skill."""

from __future__ import annotations

import re
from pathlib import Path


COMMIT_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = COMMIT_ROOT / "SKILL.md"
EXAMPLES_PATH = COMMIT_ROOT / "examples" / "commit-messages.md"
MULTI_REVIEW_PATH = COMMIT_ROOT.parent / "multi-review" / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_all(text: str, source: Path, needles: tuple[str, ...]) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{source}: missing required contract markers: {missing}")


def reject_all(text: str, source: Path, needles: tuple[str, ...]) -> None:
    present = [needle for needle in needles if needle in text]
    if present:
        raise AssertionError(f"{source}: forbidden workflow markers remain: {present}")


def check_frontmatter(skill: str) -> None:
    if not skill.startswith("---\n"):
        raise AssertionError("commit SKILL.md must start with YAML frontmatter")
    frontmatter = skill.split("---\n", 2)[1]
    keys = re.findall(r"^([a-z][a-z0-9_-]*):", frontmatter, re.MULTILINE)
    if keys != ["name", "description", "disable-model-invocation"]:
        raise AssertionError(
            f"commit frontmatter must keep the explicit-only invocation gate: {keys}"
        )
    require_all(
        frontmatter,
        SKILL_PATH,
        ("명시적으로 요청할 때만", "커밋 메시지 작성을", "커밋 의도를 추론하지 않는다"),
    )
    require_all(frontmatter, SKILL_PATH, ("disable-model-invocation: true",))


def check_explicit_request_gate(skill: str) -> None:
    require_all(
        skill,
        SKILL_PATH,
        (
            "커밋 메시지만 요청하면 메시지만 제안하고",
            "index, worktree, `HEAD`를 변경하지 말라",
            "실제 커밋 요청이 있을 때만 stage와 `git commit`을 실행하라",
            "범위가 모호하면 먼저 질문하라",
            "`$commit <범위>`",
            "`/harness-kit:commit <범위>`",
        ),
    )


def check_inspection_and_scope(skill: str) -> None:
    require_all(
        skill,
        SKILL_PATH,
        (
            "git rev-parse --show-toplevel",
            "`AGENTS.md`",
            "`CLAUDE.md`",
            "git status --short --branch",
            "git diff --staged --stat",
            "git diff --staged",
            "git diff --stat",
            "git diff",
            "git ls-files --others --exclude-standard",
            "git log -5 --oneline",
            "staged, unstaged, untracked",
            "기존 staged 변경 중 범위 밖 항목",
            "임의로 unstage하거나 함께 커밋하지 말라",
            "reset, restore, checkout, stash, drop하지 말라",
            "분리 커밋을 제안하라",
            "git add -- <path...>",
            "의도하지 않은 파일이나 hunk를 일괄 stage하지 말라",
            "staged diff가 비었거나 범위가 다르면 커밋하지 말고",
        ),
    )
    reject_all(skill, SKILL_PATH, ("git add -A", "git add ."))


def check_message_contract(skill: str, examples: str) -> None:
    require_all(
        skill,
        SKILL_PATH,
        (
            "Conventional Commits",
            "<type>(<scope>)!: <subject>",
            "<body>",
            "변경 이유, 주요 결정과 영향",
            "실제로 실행한 검증 결과",
            "실행하지 않은 테스트",
            "diff에 없는 효과를 주장하지 말라",
        ),
    )
    require_all(
        examples,
        EXAMPLES_PATH,
        (
            "저장소 지침과 최근 log",
            "실제 추가·수정·제거 사항과 이유를 bullet로 구체화",
            "검증:",
            "body와 결정 근거가 없음",
            "실행하지 않은 검증을 성공으로 주장",
            "서로 다른 관심사를 한 커밋으로 숨김",
        ),
    )


def check_side_effect_and_hook_guards(skill: str) -> None:
    require_all(
        skill,
        SKILL_PATH,
        (
            "`--no-verify`, `--amend`, push, tag, branch 생성",
            "각각 별도의 명시적 요청 없이는 수행하지 말라",
            "저장소 hook을 그대로 통과시켜라",
            "hook 실패 시 종료 코드와 핵심 출력을 보고하고",
            "`--no-verify`로 우회하지 말라",
            "실패 후 자동으로 `--amend`하거나",
            "`Co-Authored-By` trailer를 강제하거나 자동 삽입하지 말라",
        ),
    )


def check_post_commit_evidence(skill: str) -> None:
    require_all(
        skill,
        SKILL_PATH,
        (
            "before_sha",
            "git rev-parse --verify HEAD",
            "`initial commit` 상태로",
            "git show --format=fuller --stat --summary <commit-sha>",
            "git status --short --branch",
            "새 SHA가 `before_sha`와 다른지",
            "새 `HEAD`가 생성됐는지",
            "commit SHA, 제목과 body 요약, 포함 파일, hook·검증 결과",
            "남은 staged, unstaged, untracked 변경을 구분해 보고하라",
        ),
    )


def check_removed_handoff(multi_review: str) -> None:
    removed_skill = "pre" + "-commit"
    if removed_skill in multi_review.casefold():
        raise AssertionError(f"{MULTI_REVIEW_PATH}: removed scanner handoff remains")
    if re.search(r"commit.{0,40}(?:스킬|skill).{0,40}(?:호출|사용|handoff)", multi_review, re.I):
        raise AssertionError(f"{MULTI_REVIEW_PATH}: implicit commit handoff was introduced")


def main() -> int:
    skill = read(SKILL_PATH)
    examples = read(EXAMPLES_PATH)
    multi_review = read(MULTI_REVIEW_PATH)
    check_frontmatter(skill)
    check_explicit_request_gate(skill)
    check_inspection_and_scope(skill)
    check_message_contract(skill, examples)
    check_side_effect_and_hook_guards(skill)
    check_post_commit_evidence(skill)
    check_removed_handoff(multi_review)
    print("commit workflow static contract evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
