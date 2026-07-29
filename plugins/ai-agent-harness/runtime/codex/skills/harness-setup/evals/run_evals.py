"""Static contract checks for plugin-based project setup."""

from __future__ import annotations

import re
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[2]
SETUP_ROOT = SKILLS_ROOT / "harness-setup"
BOOTSTRAP_SKILL = SKILLS_ROOT / "harness-bootstrap" / "SKILL.md"
CONTEXT_SKILL = SKILLS_ROOT / "context-doc" / "SKILL.md"

FORBIDDEN_LOCAL_SKILL_PATHS = (
    ".agents/skills",
    ".claude/skills",
    "skills/",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, needle: str, source: Path) -> None:
    if needle not in text:
        raise AssertionError(f"{source}: missing required contract: {needle}")


def check_setup_contract() -> None:
    setup_files = [
        SETUP_ROOT / "SKILL.md",
        SETUP_ROOT / "prompts" / "single-app-setup.md",
        SETUP_ROOT / "prompts" / "multi-app-setup.md",
        SETUP_ROOT / "prompts" / "update-mode.md",
    ]
    setup_texts = {path: read(path) for path in setup_files}

    for path, text in setup_texts.items():
        for forbidden_path in FORBIDDEN_LOCAL_SKILL_PATHS:
            require(text, forbidden_path, path)

    skill_text = setup_texts[SETUP_ROOT / "SKILL.md"]
    require(skill_text, "허용되는 생성·갱신 범위는 `.docs/**`, 루트 `AGENTS.md`, 루트 `CLAUDE.md`뿐이다.", SETUP_ROOT / "SKILL.md")
    require(skill_text, "플러그인 리소스 해석 계약", SETUP_ROOT / "SKILL.md")

    command_pattern = re.compile(
        r"^\s*(?:mkdir|cp|copy|touch|new-item|set-content|write-output)\b.*"
        r"(?:\.agents[/\\]skills|\.claude[/\\]skills|(?:^|\s)skills[/\\])",
        re.IGNORECASE | re.MULTILINE,
    )
    for path, text in setup_texts.items():
        if command_pattern.search(text):
            raise AssertionError(f"{path}: command writes a local skill directory")

    combined = "\n".join(setup_texts.values())
    if 'cp "[plugin:harness-setup]' in combined:
        raise AssertionError("unresolvable plugin pseudo-path remains in a copy command")

    referenced_templates = set(
        re.findall(r"`templates/([A-Za-z0-9_.-]+)`", combined)
    )
    for template_name in referenced_templates:
        template_path = SETUP_ROOT / "templates" / template_name
        if not template_path.is_file():
            raise AssertionError(f"missing bundled template: {template_path}")

    single_template = read(SETUP_ROOT / "templates" / "root-context-single.template")
    require(single_template, "{{PROJECT_NAME}}", SETUP_ROOT / "templates" / "root-context-single.template")
    require(single_template, "{{PROJECT_ROOT}}", SETUP_ROOT / "templates" / "root-context-single.template")

    multi_template = read(SETUP_ROOT / "templates" / "root-context.template")
    if "HARNESS_REPO_NAME" in multi_template:
        raise AssertionError("removed clone-era HARNESS_REPO_NAME remains")


def check_nested_handoff_contract() -> None:
    bootstrap = read(BOOTSTRAP_SKILL)
    context = read(CONTEXT_SKILL)

    for stale_path in ("../design-doc/", "../context-doc/"):
        if stale_path in bootstrap:
            raise AssertionError(f"{BOOTSTRAP_SKILL}: private cross-skill path remains")

    for needle in (
        "artifact_bundle_id",
        "handoff_owner = harness-bootstrap",
        "suppress_child_handoff = true",
        "공개 스킬 이름 `design-doc`",
        "공개 스킬 이름 `context-doc`",
        "handoff_completed = true",
    ):
        require(bootstrap, needle, BOOTSTRAP_SKILL)

    for needle in (
        "artifact_bundle_id",
        "handoff_owner = context-doc",
        "suppress_child_handoff = true",
        "handoff_completed = true",
    ):
        require(context, needle, CONTEXT_SKILL)


def main() -> int:
    check_setup_contract()
    check_nested_handoff_contract()
    print("harness setup contract evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
