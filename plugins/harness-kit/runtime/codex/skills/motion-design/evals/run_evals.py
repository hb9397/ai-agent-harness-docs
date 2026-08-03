#!/usr/bin/env python3
"""Contract evals for motion-design.

The runtime carries no executable asset, so these are static contract checks:
the harness safety defaults must survive future edits, the imported upstream
knowledge tree must stay whole, and its internal links must keep resolving once
the skill is packaged and installed somewhere else.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT.parents[1] / "maintainer" / "upstreams" / "provenance" / "lottiefiles-motion-design"

UPSTREAM_TREES = {"director": 8, "patterns": 4, "reference": 4}


def skill_text() -> str:
    return (ROOT / "SKILL.md").read_text(encoding="utf-8")


def test_purpose_first_contract() -> None:
    skill = skill_text()
    for required in (
        "STEP 0 — 모션이 필요한지 먼저 판단",
        "어디에도 해당하지 않으면 모션을 넣지 않는다",
        "목적 분류 없이 모션을 설계하지 않는다",
    ):
        assert required in skill, f"purpose-first contract missing: {required!r}"
    for purpose in ("정보 전달", "상태 변화", "공간 관계", "피드백", "브랜드 표현"):
        assert purpose in skill, f"motion purpose category missing: {purpose}"


def test_motion_is_optional_and_low_density_by_default() -> None:
    skill = skill_text()
    for required in (
        "정적 화면이나 기존 디자인 시스템만으로 목적이 충분한 경우",
        "공공·의료·금융·엔터프라이즈",
        "3계층을 강제하지 않는다",
        "모든 화면에 3계층 모션을 강제하지 않는다",
    ):
        assert required in skill, f"low-density default missing: {required!r}"


def test_accessibility_is_mandatory() -> None:
    skill = skill_text()
    for required in (
        "prefers-reduced-motion",
        "reduced-motion 대체안",
        "정지 상태",
        "핵심 정보가 모션에만 실려 있지 않을 것",
        "모션이 유일한 전달 수단이면 그 설계는 통과시키지 않는다",
        "reduced-motion 대체안 없이 명세를 완료하지 않는다",
    ):
        assert required in skill, f"accessibility contract missing: {required!r}"


def test_performance_contract_requires_evidence() -> None:
    skill = skill_text()
    for required in (
        "transform과 opacity를 우선한다",
        "근거 없이 레이아웃 유발 속성을 쓰지 않는다",
        "성능 검증 방법",
    ):
        assert required in skill, f"performance contract missing: {required!r}"


def test_existing_product_language_wins() -> None:
    skill = skill_text()
    for required in (
        "기존 제품의 모션 언어를 먼저 조사한다",
        "이 스킬의 기본값보다 **우선**한다",
        "구현 프레임워크를 임의로 바꾸지 않는다",
    ):
        assert required in skill, f"existing-language precedence missing: {required!r}"


def test_output_contract_is_approval_gated() -> None:
    skill = skill_text()
    for required in (
        ".docs/design-system/{project-slug}/motion/{screen-or-component}.md",
        "승인 전에는 덮어쓰지 않는다",
        "사용자 승인 없이 프로젝트 파일을 만들지 않는다",
        "최외곽 산출물 생성자",
    ):
        assert required in skill, f"output contract missing: {required!r}"
    for field in ("목적", "trigger와 상태", "duration·delay·easing", "반복 조건",
                  "성능 위험", "검증 기준"):
        assert field in skill, f"required motion spec field missing: {field}"


def test_public_handoff_names_only() -> None:
    skill = skill_text()
    for public_name in ("ui-ux-pro-max", "design-prototype-docs", "create-prototype",
                        "frontend-design", "impl-verify"):
        assert f"`{public_name}`" in skill, f"public handoff name missing: {public_name}"
    for banned in ("${CLAUDE_PLUGIN_ROOT}", ".claude/skills", ".agents/skills"):
        assert banned not in skill, f"platform-specific path leaked: {banned}"
    frontmatter = skill.split("---")[1]
    assert "model:" not in frontmatter, "frontmatter must stay model-neutral"
    assert "allowed-tools: Read, Write, Glob, Grep" in frontmatter


def test_upstream_knowledge_tree_is_complete() -> None:
    for tree, expected in UPSTREAM_TREES.items():
        files = sorted((ROOT / tree).glob("*.md"))
        assert len(files) == expected, f"{tree}/ expected {expected} files, found {len(files)}"


def test_upstream_files_match_the_pinned_manifest() -> None:
    import hashlib

    file_map = json.loads((PROVENANCE / "file-map.json").read_text(encoding="utf-8"))
    checked = 0
    for entry in file_map["files"]:
        if entry["treatment"] != "verbatim":
            continue
        local = ROOT.parents[1] / entry["local_path"]
        assert local.is_file(), f"missing imported file: {entry['local_path']}"
        digest = hashlib.sha256(local.read_bytes()).hexdigest()
        assert digest == entry["upstream_sha256"], f"drift from pinned upstream: {entry['local_path']}"
        checked += 1
    assert checked == 16, f"expected 16 verbatim upstream files, checked {checked}"


def test_internal_links_resolve() -> None:
    """Relative links must keep working once the skill is installed elsewhere."""
    pattern = re.compile(r"\[[^\]]+\]\((?!https?://)([^)#]+)")
    broken: list[str] = []
    for path in sorted(ROOT.rglob("*.md")):
        for target in pattern.findall(path.read_text(encoding="utf-8")):
            if target.startswith("/"):
                broken.append(f"{path.name} -> absolute link {target}")
                continue
            if not (path.parent / target).resolve().is_file():
                broken.append(f"{path.relative_to(ROOT).as_posix()} -> {target}")
    assert not broken, "unresolved internal links:\n" + "\n".join(broken)


def main() -> int:
    tests = [
        test_purpose_first_contract,
        test_motion_is_optional_and_low_density_by_default,
        test_accessibility_is_mandatory,
        test_performance_contract_requires_evidence,
        test_existing_product_language_wins,
        test_output_contract_is_approval_gated,
        test_public_handoff_names_only,
        test_upstream_knowledge_tree_is_complete,
        test_upstream_files_match_the_pinned_manifest,
        test_internal_links_resolve,
    ]
    for test in tests:
        test()
    print(f"motion-design evals: PASS ({len(tests)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
