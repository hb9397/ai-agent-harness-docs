#!/usr/bin/env python3
"""Build/validation evals for harness-plugin-maintainer."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "maintainer" / "skills" / "harness-plugin-maintainer"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_plugin  # noqa: E402
import freeze_manager_inventory  # noqa: E402
import verify_install_surfaces  # noqa: E402


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
    )
    if completed.returncode != 0:
        raise AssertionError(f"command failed: {args}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return completed


def test_invalid_inventory_does_not_destroy_the_plugin_tree() -> None:
    """A failed build must not leave the repository without a plugin tree.

    The builder resets its output directory before writing. If that reset ran
    before input validation, any invalid input would delete the tracked plugin
    and leave nothing behind.
    """
    with tempfile.TemporaryDirectory(prefix="harness-plugin-reset-eval-") as tmp:
        fixture_root = Path(tmp)
        build_plugin.build(ROOT, output_root=fixture_root)
        plugin_root = fixture_root / "plugins" / "ai-agent-harness"
        before = sorted(p.relative_to(fixture_root).as_posix() for p in plugin_root.rglob("*"))
        assert before, "fixture build produced no plugin tree"

        capabilities_path = ROOT / "maintainer" / "plugin" / "CAPABILITIES.json"
        backup = capabilities_path.read_bytes()
        try:
            broken = json.loads(backup.decode("utf-8"))
            broken["logical_user_skills"] = broken["logical_user_skills"][:-1]
            capabilities_path.write_text(
                json.dumps(broken, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
            )
            try:
                build_plugin.build(ROOT, output_root=fixture_root)
            except RuntimeError as exc:
                assert "user skill inventory mismatch" in str(exc)
            else:
                raise AssertionError("build accepted a mismatched inventory")
        finally:
            capabilities_path.write_bytes(backup)

        after = sorted(p.relative_to(fixture_root).as_posix() for p in plugin_root.rglob("*"))
        assert after == before, "failed build deleted or altered the existing plugin tree"


def test_pending_candidate_skill_is_canonical_but_not_packaged() -> None:
    """A skill may exist canonically while its upstream group is unpromoted."""
    pending = build_plugin.pending_user_skills(ROOT)
    if not pending:
        return
    capabilities = json.loads((ROOT / "maintainer" / "plugin" / "CAPABILITIES.json").read_text(encoding="utf-8"))
    for skill in pending:
        assert (ROOT / "skills" / skill / "SKILL.md").is_file(), f"pending skill {skill} is not canonical"
        assert skill not in capabilities["logical_user_skills"], f"pending skill {skill} leaked into capabilities"
        for platform in ("codex", "claude"):
            packaged = ROOT / "plugins" / "ai-agent-harness" / "runtime" / platform / "skills" / skill
            assert not packaged.exists(), f"pending skill {skill} leaked into the {platform} runtime"


def main() -> int:
    test_invalid_inventory_does_not_destroy_the_plugin_tree()
    test_pending_candidate_skill_is_canonical_but_not_packaged()

    with tempfile.TemporaryDirectory(prefix="harness-plugin-text-eval-") as tmp:
        payload_root = Path(tmp)
        extensionless = payload_root / "LICENSE"
        extensionless.write_bytes(b"line with protected spaces  \r\nsecond line\r\n")
        build_plugin.normalize_text_payload(payload_root)
        if extensionless.read_bytes() != b"line with protected spaces  \nsecond line\n":
            raise AssertionError("extensionless text LF normalization changed protected content")

    build = run([str(SCRIPTS / "build_plugin.py")])
    release = json.loads(build.stdout)
    if release["logical_user_skills"] != 18:
        raise AssertionError("logical user skill count mismatch")
    if release["codex_physical_skills"] != 18 or release["claude_physical_skills"] != 18:
        raise AssertionError("physical skill count mismatch")
    if release["codex_physical_agents"] != 0 or release["claude_physical_agents"] != 0:
        raise AssertionError("physical agent count mismatch")
    run([str(SCRIPTS / "validate_plugin.py")])
    run([str(SCRIPTS / "build_plugin.py"), "--check"])
    run([str(SCRIPTS / "validate_plugin.py")])

    with tempfile.TemporaryDirectory(prefix="harness-plugin-check-eval-") as tmp:
        fixture_root = Path(tmp)
        build_plugin.build(ROOT, output_root=fixture_root)
        drifted = fixture_root / "plugins" / "ai-agent-harness" / ".codex-plugin" / "plugin.json"
        drifted.write_text('{"name":"drift-must-survive-check"}\n', encoding="utf-8", newline="\n")
        before = drifted.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = build_plugin.check(ROOT, canonical_root=fixture_root)
        if result == 0:
            raise AssertionError("--check did not detect plugin tree drift")
        if drifted.read_bytes() != before:
            raise AssertionError("--check mutated the canonical plugin tree")

    with tempfile.TemporaryDirectory(prefix="harness-manager-freeze-eval-") as tmp:
        fixture_root = Path(tmp)
        for skill in freeze_manager_inventory.MANAGER_SKILLS:
            (fixture_root / "maintainer" / "skills" / skill).mkdir(parents=True)
        crlf_file = (
            fixture_root
            / "maintainer"
            / "skills"
            / "custom-skill-design"
            / "SKILL.md"
        )
        crlf_file.write_bytes(b"first line\r\nsecond line\r\n")
        nested = crlf_file.parent / "evals" / "run.py"
        nested.parent.mkdir()
        nested.write_bytes(b"print('ok')\r\n")
        crlf_inventory = freeze_manager_inventory.build_inventory(fixture_root)
        crlf_file.write_bytes(b"first line\nsecond line\n")
        nested.write_bytes(b"print('ok')\n")
        lf_inventory = freeze_manager_inventory.build_inventory(fixture_root)
        if crlf_inventory != lf_inventory:
            raise AssertionError("manager freeze differs between CRLF and LF text")
        paths = [
            item["path"]
            for item in crlf_inventory["skills"][0]["files"]
        ]
        expected_paths = sorted(paths, key=lambda path: (path.casefold(), path))
        if paths != expected_paths:
            raise AssertionError("manager freeze path order is platform-dependent")

    run([str(SCRIPTS / "freeze_manager_inventory.py"), "--check"])
    run([str(SCRIPTS / "smoke_cli_install.py"), "--self-test"])
    evidence_paths = [
        ROOT / "maintainer" / "plugin" / "install-verification.json",
        ROOT / "maintainer" / "plugin" / "legacy-migration-fixture.json",
        ROOT / "maintainer" / "plugin" / "release-checklist.md",
    ]
    evidence_before = {
        path: path.read_bytes()
        for path in evidence_paths
    }
    run([str(SCRIPTS / "verify_install_surfaces.py"), "--check"])
    if any(path.read_bytes() != evidence_before[path] for path in evidence_paths):
        raise AssertionError("install surface check mutated tracked evidence")

    with tempfile.TemporaryDirectory(prefix="harness-install-evidence-eval-") as tmp:
        fixture_root = Path(tmp)
        fixture_plugin = fixture_root / "maintainer" / "plugin"
        fixture_plugin.mkdir(parents=True)
        for source in evidence_paths:
            (fixture_plugin / source.name).write_bytes(source.read_bytes())
        baseline = json.loads(evidence_paths[0].read_text(encoding="utf-8"))
        probe_only_change = copy.deepcopy(baseline)
        probe_only_change["cli_probes"]["codex_help"]["status"] = "fixture-host-difference"
        if verify_install_surfaces.check_tracked_evidence(
            fixture_root, probe_only_change
        ):
            raise AssertionError("host-specific CLI probe drift failed deterministic check")
        core_drift = copy.deepcopy(baseline)
        core_drift["plugin"]["version"] = "9.9.9"
        if not verify_install_surfaces.check_tracked_evidence(
            fixture_root, core_drift
        ):
            raise AssertionError("deterministic install evidence drift was not detected")
    run([str(SCRIPTS / "run_release_regression.py")])
    print("harness-plugin-maintainer evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
