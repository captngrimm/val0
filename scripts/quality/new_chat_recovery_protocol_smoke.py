#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs" / "ops" / "NEWCHAT_01_RECOVERY_PROTOCOL.md"
BRIDGE = ROOT / "docs" / "ops" / "NEWCHAT_BRIDGE_PROMPT.md"
HELPER = ROOT / "scripts" / "diagnostics" / "new_chat_recovery_brief.py"
SOURCE_INDEX = ROOT / "docs" / "product" / "VAL0_SOURCE_OF_TRUTH_INDEX.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> int:
    assert_true(PROTOCOL.exists(), "NEWCHAT protocol exists")
    assert_true(BRIDGE.exists(), "NEWCHAT bridge prompt exists")
    assert_true(HELPER.exists(), "new chat recovery helper exists")

    compile_result = subprocess.run(
        ["./scripts/val0py", "-m", "py_compile", "scripts/diagnostics/new_chat_recovery_brief.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(compile_result.returncode == 0, f"helper compiles: {compile_result.stderr}")

    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PROTOCOL, BRIDGE, SOURCE_INDEX)
    )
    for needle in (
        "ValPrime",
        "/continuity",
        "new chat bundle",
        "Desk",
        "Side Table",
        "Library Index",
        "Vault",
        "val0_source_of_truth_check.py",
        "Karen RC full smoke",
        "source-of-truth",
        "Launchpad",
        "Do not rely on memory",
        "NEWCHAT_01_RECOVERY_PROTOCOL.md",
        "NEWCHAT_BRIDGE_PROMPT.md",
        "new_chat_recovery_brief.py",
    ):
        assert_contains(text, needle, "NEWCHAT docs/index")

    run_result = subprocess.run(
        ["python3", "scripts/diagnostics/new_chat_recovery_brief.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(run_result.returncode == 0, f"helper runs: {run_result.stderr}")
    assert_contains(run_result.stdout, "Val0 new chat recovery brief", "helper output")
    assert_contains(run_result.stdout, "Router coverage:", "helper output")
    assert_contains(run_result.stdout, "ValPrime /continuity", "helper output")

    print("PASS: New chat recovery protocol smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
