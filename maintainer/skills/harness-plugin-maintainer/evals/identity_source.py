#!/usr/bin/env python3
"""Static checks for the harness-kit identity source migration."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "maintainer" / "skills" / "harness-plugin-maintainer" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from plugin_common import (  # noqa: E402
    MARKETPLACE_NAME,
    PLUGIN_DESCRIPTION,
    PLUGIN_DISPLAY_NAME,
    PLUGIN_ID,
    PLUGIN_ROOT_REL,
    REPOSITORY_URL,
    generated_marker,
)
import smoke_cli_install  # noqa: E402


def main() -> int:
    assert PLUGIN_ID == "harness-kit"
    assert MARKETPLACE_NAME == "hb9397"
    assert PLUGIN_DISPLAY_NAME == "Harness Kit"
    assert REPOSITORY_URL == "https://github.com/hb9397/harness-kit"
    assert PLUGIN_ROOT_REL.as_posix() == "plugins/harness-kit"
    assert smoke_cli_install.QUALIFIED_PLUGIN_ID == "harness-kit@hb9397"
    marker = generated_marker()
    assert marker["source"] == REPOSITORY_URL
    assert not Path(marker["source"]).is_absolute()

    registry = json.loads((ROOT / "maintainer" / "upstreams" / "registry.json").read_text(encoding="utf-8"))
    internal = next(item for item in registry["sources"] if item["id"] == "internal-harness-native")
    assert internal["upstream"]["source_url"] == REPOSITORY_URL
    assert internal["provenance"]["license_url"] == f"{REPOSITORY_URL}/blob/main/LICENSE"

    live_sources = [
        ROOT / "maintainer" / "skills" / "harness-plugin-maintainer" / "scripts" / "plugin_common.py",
        ROOT / "maintainer" / "skills" / "harness-plugin-maintainer" / "scripts" / "build_plugin.py",
        ROOT / "maintainer" / "skills" / "harness-plugin-maintainer" / "scripts" / "validate_plugin.py",
        ROOT / "maintainer" / "skills" / "harness-plugin-maintainer" / "scripts" / "smoke_cli_install.py",
    ]
    old_plugin_name = "ai-agent-" + "harness"
    old_marker = old_plugin_name + ":managed"
    old_checkout = "D:/Dev_Workspace/" + old_plugin_name + "-docs"
    for path in live_sources:
        text = path.read_text(encoding="utf-8")
        assert old_plugin_name not in text, f"old identity remains in live source: {path}"
        assert old_checkout not in text

    setup_templates = ROOT / "skills" / "harness-setup"
    for path in setup_templates.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".template", ".py"}:
            text = path.read_text(encoding="utf-8")
            assert old_marker not in text, f"old managed marker remains: {path}"

    print("plugin identity source evals: PASS (harness-kit, hb9397, stable marker)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
