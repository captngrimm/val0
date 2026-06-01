#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLAYBOOK = ROOT / "docs" / "ops" / "ROUTER_05_SHADOW_OBSERVATION_PLAYBOOK.md"
HELPER = ROOT / "scripts" / "ops" / "router_shadow_mode.sh"
ARCH_DOC = ROOT / "docs" / "architecture" / "INTENT_ROUTER_V2_MARCHING_ORDER.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def test_playbook_content() -> None:
    assert_true(PLAYBOOK.exists(), "playbook doc exists")
    text = PLAYBOOK.read_text(encoding="utf-8")
    for needle in (
        "Shadow mode must default OFF",
        "short observation windows",
        "python3 scripts/quality/karen_rc_full_smoke.py --keep-going",
        "[INTENT_ROUTER_V2_COMPARE]",
        "match=True",
        "match=False",
        "/etc/systemd/system/val0-bot.service.d/intent-router-shadow.conf",
        'Environment="VAL0_INTENT_ROUTER_V2_SHADOW=true"',
        "status output redacts secret-like environment values",
        "Do not paste raw systemd environment output externally",
        "Shadow mode should be disabled after every observation test window",
    ):
        assert_contains(text, needle, "playbook content")


def test_helper_content_and_syntax() -> None:
    assert_true(HELPER.exists(), "helper script exists")
    text = HELPER.read_text(encoding="utf-8")
    for needle in (
        "enable",
        "disable",
        "status",
        "logs",
        "VAL0_INTENT_ROUTER_V2_SHADOW=true",
        "systemctl daemon-reload",
        'systemctl restart "${SERVICE_NAME}"',
        "journalctl",
        "This command must be run as root",
        "is_secret_env_key",
        "print_redacted_environment",
        "RESEND_API_KEY",
        "***REDACTED***",
        "--property=Environment --value",
    ):
        assert_contains(text, needle, "helper script content")
    assert_true(
        'systemctl show "${SERVICE_NAME}" --property=Environment --no-pager' not in text,
        "helper does not print raw systemctl Environment output",
    )

    result = subprocess.run(
        ["bash", "-n", "scripts/ops/router_shadow_mode.sh"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"helper bash syntax: {result.stderr}")


def test_architecture_doc_mentions_router_05() -> None:
    assert_true(ARCH_DOC.exists(), "architecture doc exists")
    text = ARCH_DOC.read_text(encoding="utf-8")
    for needle in (
        "ROUTER-05 Shadow Observation Playbook",
        "docs/ops/ROUTER_05_SHADOW_OBSERVATION_PLAYBOOK.md",
        "scripts/ops/router_shadow_mode.sh",
        "short-window observation",
        "no behavior change",
        "comparison logs",
    ):
        assert_contains(text, needle, "architecture ROUTER-05 content")


def main() -> int:
    test_playbook_content()
    test_helper_content_and_syntax()
    test_architecture_doc_mentions_router_05()
    print("PASS: Router shadow playbook smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
