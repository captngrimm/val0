#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "diagnostics" / "val0_alpha_brief.py"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r} in output")


def main() -> int:
    assert_true(SCRIPT.exists(), "alpha brief script exists")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"alpha brief script failed: {proc.stderr}")
    output = proc.stdout

    assert_contains(output, "VAL0 Alpha Brief", "brief title")
    assert_contains(output, "Alpha", "Alpha marker/lanes")
    assert_contains(output, "CLIENT_GROCERY.md", "live data warning")
    assert_contains(output, "NEXT", "recommended next action")
    assert_contains(output, "A-007", "recent Alpha lane")
    assert_contains(output, "Human outcome summaries", "human outcome section")
    assert_contains(output, "Now Val can", "human outcome capability copy")
    assert_contains(output, "Example interaction", "human outcome example")
    assert_contains(output, "Remaining gap / watch item", "human outcome watch item")
    assert_contains(output, "python3 scripts/quality/client_fixture_smoke.py --client karen", "fixture validation command")
    assert_contains(output, "python3 scripts/quality/karen_rc_full_smoke.py --keep-going", "full smoke validation command")
    assert_contains(output, "git diff --check", "diff validation command")
    print("PASS: Val0 Alpha brief smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
