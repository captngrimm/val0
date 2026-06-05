#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ops.night_runner_bedtime_trial import (  # noqa: E402
    DECISION_MANUAL_PASS,
    evaluate_packet,
    load_packet,
)


PACKET = ROOT / "docs" / "ops" / "night_runner_bedtime_packet_v2.yaml"
REPORT = ROOT / "tmp" / "night_runner" / "manual_overnight_trial_report.md"
PROTECTED_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)
FORBIDDEN_OUTPUT_MARKERS = (
    "refresh_token",
    "access_token",
    "id_token",
    "client_secret",
    "sk-",
    "auth.json contents",
    "config.toml contents",
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_equal(left, right, label: str) -> None:
    if left != right:
        raise AssertionError(f"{label}: expected {right!r}, got {left!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r}")


def _git_cached_names() -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"git cached diff failed: {proc.stderr.strip()}")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def test_manual_overnight_trial() -> None:
    packet = load_packet(PACKET)
    result = evaluate_packet(packet, trial_label="manual_overnight_trial")
    assert_equal(result.decision, DECISION_MANUAL_PASS, "manual overnight decision")
    assert_true(result.report_written, "primary report written")
    assert_true(result.trial_report_written, "trial report written")
    assert_equal(result.trial_report_path, "tmp/night_runner/manual_overnight_trial_report.md", "trial path")
    assert_true(REPORT.exists(), "manual overnight report exists")

    report = REPORT.read_text(encoding="utf-8")
    for needle in (
        "Night Runner Manual Overnight Trial",
        "Decision",
        "Trial Label",
        "Tests Run",
        "Test Results",
        "Changed Files",
        "Safety Status",
        "Protected Live Data",
        "Morning Review Options",
        "approve",
        "discard",
        "continue",
        "ask_valprime",
        "NIGHT-RUNNER-21",
        "protected live file contents read: no",
        "contents printed: no",
    ):
        assert_contains(report, needle, f"report contains {needle}")
    for marker in FORBIDDEN_OUTPUT_MARKERS:
        assert_not_contains(report, marker, "secret marker")


def test_protected_live_files_not_staged() -> None:
    staged = set(_git_cached_names())
    for path in PROTECTED_FILES:
        assert_true(path not in staged, f"{path} is not staged")
    assert_true(not staged, "no staged files remain")


def main() -> None:
    test_manual_overnight_trial()
    test_protected_live_files_not_staged()
    print("PASS night_runner_manual_overnight_trial_smoke")


if __name__ == "__main__":
    main()
