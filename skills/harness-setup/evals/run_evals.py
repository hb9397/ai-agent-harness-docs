"""Contract and executable filesystem fixture checks for project setup."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
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
MARKDOWN_MARKERS = (
    "<!-- ai-agent-harness:managed:start -->",
    "<!-- ai-agent-harness:managed:end -->",
)
GITIGNORE_MARKERS = (
    "# ai-agent-harness:managed:start",
    "# ai-agent-harness:managed:end",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, needle: str, source: Path) -> None:
    if needle not in text:
        raise AssertionError(f"{source}: missing required contract: {needle}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_fingerprint(project: Path, artifacts: list[Path]) -> tuple[str, list[dict[str, str]]]:
    ledger = project / ".docs" / ".harness" / "humanize-handoffs.json"
    normalized: list[dict[str, str]] = []
    for path in artifacts:
        if path.resolve() == ledger.resolve():
            raise AssertionError("ledger must not be part of the humanize artifact bundle")
        normalized.append(
            {
                "path": path.relative_to(project).as_posix(),
                "sha256": sha256(path),
            }
        )
    normalized.sort(key=lambda item: item["path"])
    canonical = "\n".join(
        f"{item['path']}\0{item['sha256']}" for item in normalized
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest(), normalized


def append_ledger_event(
    ledger: Path,
    fingerprint: str,
    artifacts: list[dict[str, str]],
    status: str,
    supersedes_fingerprint: str | None = None,
) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.loads(ledger.read_text(encoding="utf-8"))
        if ledger.exists()
        else {"schema_version": "1.0.0", "records": []}
    )
    record = next(
        (
            item
            for item in payload["records"]
            if item["artifact_fingerprint"] == fingerprint
        ),
        None,
    )
    if record is None:
        record = {
            "artifact_fingerprint": fingerprint,
            "producer": "harness-setup",
            "artifact_bundle_id": "fixture-correlation-id",
            "profile": "document-refinement",
            "artifacts": artifacts,
            "events": [],
        }
        if supersedes_fingerprint is not None:
            record["supersedes_fingerprint"] = supersedes_fingerprint
        payload["records"].append(record)
    record["events"].append(
        {"status": status, "recorded_at": "2026-07-30T00:00:00+09:00"}
    )
    temp_path = ledger.with_name(f".{ledger.name}.tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, ledger)


def snapshot_files(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def detect_mode(project: Path) -> str:
    return "update" if (project / ".docs").exists() or (project / "AGENTS.md").exists() else "initial"


def replace_managed_block(existing: str, template: str, markers: tuple[str, str]) -> str:
    start, end = markers
    if existing.count(start) != 1 or existing.count(end) != 1:
        raise ValueError("existing file is unmanaged or has malformed markers")
    if template.count(start) != 1 or template.count(end) != 1:
        raise ValueError("template must contain exactly one managed block")
    existing_start = existing.index(start)
    existing_end = existing.index(end, existing_start) + len(end)
    template_start = template.index(start)
    template_end = template.index(end, template_start) + len(end)
    return (
        existing[:existing_start]
        + template[template_start:template_end]
        + existing[existing_end:]
    )


def render(template_name: str, replacements: dict[str, str] | None = None) -> str:
    text = read(SETUP_ROOT / "templates" / template_name)
    for key, value in (replacements or {}).items():
        text = text.replace(key, value)
    if re.search(r"\{\{[A-Z0-9_]+\}\}", text):
        raise AssertionError(f"unresolved placeholder in {template_name}")
    return text


def assert_allowed_outputs(project: Path, before: dict[str, str]) -> None:
    after = snapshot_files(project)
    changed = {
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
    }
    invalid = sorted(
        path
        for path in changed
        if not (
            path == "AGENTS.md"
            or path == "CLAUDE.md"
            or path.startswith(".docs/")
        )
    )
    if invalid:
        raise AssertionError(f"fixture wrote outside setup allowlist: {invalid}")


def materialize_single_fixture(project: Path) -> None:
    docs = project / ".docs"
    inbox = docs / "_inbox"
    inbox.mkdir(parents=True)
    (docs / "README.md").write_text(
        render("docs-readme-single.template"), encoding="utf-8", newline="\n"
    )
    (docs / ".gitignore").write_text(
        render("docs-gitignore.template"), encoding="utf-8", newline="\n"
    )
    (inbox / "README.md").write_text(
        render("inbox-readme.template"), encoding="utf-8", newline="\n"
    )
    (inbox / ".gitkeep").write_text("", encoding="utf-8")
    (project / "AGENTS.md").write_text(
        render(
            "root-context-single.template",
            {
                "{{PROJECT_NAME}}": project.name,
                "{{PROJECT_ROOT}}": str(project.resolve()),
            },
        ),
        encoding="utf-8",
        newline="\n",
    )
    (project / "CLAUDE.md").write_text(
        render("claude-bridge.template"), encoding="utf-8", newline="\n"
    )


def materialize_multi_fixture(project: Path) -> None:
    docs = project / ".docs"
    inbox = docs / "_inbox"
    root_context = docs / "root-context"
    inbox.mkdir(parents=True)
    root_context.mkdir(parents=True)
    for app in ("api", "web"):
        (docs / app / "context-base").mkdir(parents=True)
        (docs / app / "instruction").mkdir()
        (docs / app / "impl-doc").mkdir()
        (docs / f"{app}-context.md").write_text("", encoding="utf-8")
    (docs / "prototype").mkdir()
    (docs / "README.md").write_text(
        render("docs-readme-multi.template"), encoding="utf-8", newline="\n"
    )
    (docs / ".gitignore").write_text(
        render("docs-gitignore.template"), encoding="utf-8", newline="\n"
    )
    (inbox / "README.md").write_text(
        render("inbox-readme.template"), encoding="utf-8", newline="\n"
    )
    (inbox / ".gitkeep").write_text("", encoding="utf-8")
    agents = render(
        "root-context.template",
        {
            "{{PROJECT_NAME}}": project.name,
            "{{APP_LIST}}": "| API | `api/` | fixture |\n| Web | `web/` | fixture |",
            "{{APP_CONTEXT_ENTRIES}}": "- `@.docs/api-context.md`\n- `@.docs/web-context.md`",
            "{{APP_INSTRUCTION_ENTRIES}}": "- `@.docs/api/instruction/*-instruction.md`\n- `@.docs/web/instruction/*-instruction.md`",
        },
    )
    bridge = render("claude-bridge.template")
    for path, text in (
        (project / "AGENTS.md", agents),
        (project / "CLAUDE.md", bridge),
        (root_context / "AGENTS.md", agents),
        (root_context / "CLAUDE.md", bridge),
    ):
        path.write_text(text, encoding="utf-8", newline="\n")


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
    require(skill_text, "`.docs/`와 `AGENTS.md`가 모두 없음", SETUP_ROOT / "SKILL.md")
    require(skill_text, "`.docs/` 또는 `AGENTS.md` 중 하나 이상 존재", SETUP_ROOT / "SKILL.md")
    for needle in (
        "artifact_fingerprint",
        "`.docs/.harness/humanize-handoffs.json`",
        "`proposed`, `skipped`, `rejected`, `applied`, `revalidated`",
        "원자적 replace",
        "ledger는 Markdown이 아니며",
        "correlation 용도",
        "`ai-agent-harness:managed:start/end` marker",
    ):
        require(skill_text, needle, SETUP_ROOT / "SKILL.md")

    detection = read(SETUP_ROOT / "prompts" / "detection.md")
    require(detection, "`.docs/` 또는 `AGENTS.md`가 존재", SETUP_ROOT / "prompts" / "detection.md")
    require(detection, "위 조건 불충족", SETUP_ROOT / "prompts" / "detection.md")

    update = setup_texts[SETUP_ROOT / "prompts" / "update-mode.md"]
    for needle in (
        "관리 블록만",
        "앞뒤 사용자 내용을 byte-preserve",
        "동시 수정",
        "`.docs/archive/harness-setup/{timestamp}/{상대경로}`",
        "`unmanaged`",
        "`malformed`",
    ):
        require(update, needle, SETUP_ROOT / "prompts" / "update-mode.md")
    if "덮어써도 안전" in update:
        raise AssertionError("update-mode still claims unconditional overwrite is safe")

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

    for template_name in (
        "docs-readme-single.template",
        "docs-readme-multi.template",
        "root-context-single.template",
        "root-context.template",
        "claude-bridge.template",
    ):
        template = read(SETUP_ROOT / "templates" / template_name)
        for marker in MARKDOWN_MARKERS:
            require(template, marker, SETUP_ROOT / "templates" / template_name)
    gitignore = read(SETUP_ROOT / "templates" / "docs-gitignore.template")
    for marker in GITIGNORE_MARKERS:
        require(gitignore, marker, SETUP_ROOT / "templates" / "docs-gitignore.template")


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

    for needle in (
        "공개 스킬 이름 `harness-setup`",
        "handoff_owner = harness-bootstrap",
        "suppress_child_handoff = true",
        "같은 질문을 반복하지 않는다",
        "`.agents/skills/`",
        "`.claude/skills/`",
        "`skills/`는 생성·복사·동기화하지 않는다",
    ):
        require(bootstrap, needle, BOOTSTRAP_SKILL)


def check_filesystem_fixtures() -> None:
    with tempfile.TemporaryDirectory(prefix="harness-setup-fixtures-") as tmp:
        root = Path(tmp)

        single = root / "single-project"
        single.mkdir()
        before = snapshot_files(single)
        if detect_mode(single) != "initial":
            raise AssertionError("empty project must be initial mode")
        materialize_single_fixture(single)
        assert_allowed_outputs(single, before)
        artifacts = [
            single / ".docs" / "README.md",
            single / "AGENTS.md",
            single / "CLAUDE.md",
        ]
        fingerprint, artifact_manifest = artifact_fingerprint(single, artifacts)
        ledger = single / ".docs" / ".harness" / "humanize-handoffs.json"
        append_ledger_event(ledger, fingerprint, artifact_manifest, "proposed")
        stored = json.loads(ledger.read_text(encoding="utf-8"))
        if stored["records"][0]["artifact_fingerprint"] != fingerprint:
            raise AssertionError("ledger did not persist the artifact fingerprint")
        if stored["records"][0]["events"][0]["status"] != "proposed":
            raise AssertionError("ledger did not persist the proposal event")
        same_fingerprint, _ = artifact_fingerprint(single, artifacts)
        if same_fingerprint != fingerprint:
            raise AssertionError("same artifacts must produce the same fingerprint")
        (single / "AGENTS.md").write_text(
            (single / "AGENTS.md").read_text(encoding="utf-8") + "\nNEW-CONTENT\n",
            encoding="utf-8",
            newline="\n",
        )
        changed_fingerprint, changed_manifest = artifact_fingerprint(single, artifacts)
        if changed_fingerprint == fingerprint:
            raise AssertionError("content changes must produce a new fingerprint")
        append_ledger_event(
            ledger,
            changed_fingerprint,
            changed_manifest,
            "applied",
            supersedes_fingerprint=fingerprint,
        )
        append_ledger_event(
            ledger,
            changed_fingerprint,
            changed_manifest,
            "revalidated",
        )
        updated_ledger = json.loads(ledger.read_text(encoding="utf-8"))
        final_record = next(
            record
            for record in updated_ledger["records"]
            if record["artifact_fingerprint"] == changed_fingerprint
        )
        if final_record.get("supersedes_fingerprint") != fingerprint:
            raise AssertionError("post-apply fingerprint did not link proposal fingerprint")
        if [event["status"] for event in final_record["events"]] != [
            "applied",
            "revalidated",
        ]:
            raise AssertionError("post-apply final fingerprint is not terminal")
        if ledger.with_name(f".{ledger.name}.tmp").exists():
            raise AssertionError("atomic ledger temporary file was not cleaned up")
        assert_allowed_outputs(single, before)
        for rel in FORBIDDEN_LOCAL_SKILL_PATHS:
            if (single / rel.rstrip("/")).exists():
                raise AssertionError(f"single fixture created forbidden path: {rel}")

        multi = root / "multi-project"
        (multi / "api").mkdir(parents=True)
        (multi / "web").mkdir()
        before = snapshot_files(multi)
        materialize_multi_fixture(multi)
        assert_allowed_outputs(multi, before)
        for rel in FORBIDDEN_LOCAL_SKILL_PATHS:
            if (multi / rel.rstrip("/")).exists():
                raise AssertionError(f"multi fixture created forbidden path: {rel}")

        partial_docs = root / "partial-docs"
        (partial_docs / ".docs").mkdir(parents=True)
        if detect_mode(partial_docs) != "update":
            raise AssertionError(".docs-only project must use update/recovery mode")
        partial_agents = root / "partial-agents"
        partial_agents.mkdir()
        (partial_agents / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")
        if detect_mode(partial_agents) != "update":
            raise AssertionError("AGENTS-only project must use update/recovery mode")

        update = root / "update-project"
        materialize_single_fixture(update)
        custom_tokens = {
            update / ".docs" / "README.md": "TEAM-README-EXTENSION",
            update / ".docs" / ".gitignore": "team-private.cache",
            update / "AGENTS.md": "TEAM-AGENT-RULE",
            update / "CLAUDE.md": "TEAM-CLAUDE-DELTA",
        }
        for path, token in custom_tokens.items():
            path.write_text(
                path.read_text(encoding="utf-8") + f"\n{token}\n",
                encoding="utf-8",
                newline="\n",
            )

        legacy_files = [
            update / ".agents" / "skills" / "custom-skill" / "SKILL.md",
            update / ".claude" / "skills" / "legacy-skill" / "SKILL.md",
            update / "skills" / "domain-skill" / "SKILL.md",
        ]
        for path in legacy_files:
            path.parent.mkdir(parents=True)
            path.write_text("legacy sentinel\n", encoding="utf-8")
        legacy_before = {path: sha256(path) for path in legacy_files}
        before = snapshot_files(update)

        replacement_templates = {
            update / ".docs" / "README.md": (
                render("docs-readme-single.template"),
                MARKDOWN_MARKERS,
            ),
            update / ".docs" / ".gitignore": (
                render("docs-gitignore.template"),
                GITIGNORE_MARKERS,
            ),
            update / "AGENTS.md": (
                render(
                    "root-context-single.template",
                    {
                        "{{PROJECT_NAME}}": update.name,
                        "{{PROJECT_ROOT}}": str(update.resolve()),
                    },
                ),
                MARKDOWN_MARKERS,
            ),
            update / "CLAUDE.md": (
                render("claude-bridge.template"),
                MARKDOWN_MARKERS,
            ),
        }
        for path, (template, markers) in replacement_templates.items():
            current = path.read_text(encoding="utf-8")
            path.write_text(
                replace_managed_block(current, template, markers),
                encoding="utf-8",
                newline="\n",
            )
        assert_allowed_outputs(update, before)
        for path, token in custom_tokens.items():
            if token not in path.read_text(encoding="utf-8"):
                raise AssertionError(f"user extension was not preserved: {path}")
        for path, digest in legacy_before.items():
            if sha256(path) != digest:
                raise AssertionError(f"legacy local skill copy changed: {path}")


def main() -> int:
    check_setup_contract()
    check_nested_handoff_contract()
    check_filesystem_fixtures()
    print("harness setup contract and filesystem fixture evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
