#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ops.night_runner_bedtime_trial import (  # noqa: E402
    DECISION_PASS,
    DECISION_PROTECTED,
    DECISION_REPORT,
    DECISION_TEST,
    DECISION_UNSAFE,
    evaluate_packet,
    load_packet,
)


BRANCH = "val0-post-m41-conversationality-memory-lab-2026-05-25"
PROTECTED_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
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


def _status(*entries: str) -> str:
    return "\n".join((f"## {BRANCH}", *entries)) + "\n"


def _packet(tmpdir: Path, **overrides):
    packet = {
        "lane_id": "NIGHT-RUNNER-18-SMOKE",
        "task_name": "Bedtime workflow v2 trial",
        "task_mode": "bedtime_diagnostic",
        "allowed_files": [],
        "forbidden_files": [
            *PROTECTED_FILES,
            "bot.py",
            "core/**",
            "val0_memory.enc.db",
            "*.db",
            "*.sqlite",
            "/etc/val0",
        ],
        "tests_to_run": [
            "python3 scripts/quality/night_runner_bedtime_packet_v2_smoke.py",
            "python3 scripts/quality/night_runner_patch_review_smoke.py",
        ],
        "report_path": f"tmp/night_runner/{tmpdir.name}_bedtime_trial_report.md",
        "allow_file_edits": False,
        "allow_commit": False,
        "allow_restart": False,
        "allow_live_writes": False,
        "run_tests": True,
        "morning_review": ["approve", "discard", "continue", "ask_valprime"],
    }
    packet.update(overrides)
    return packet


def _run(packet: dict, status: str | None = None):
    return evaluate_packet(
        packet,
        status_short_branch=status
        or _status(
            " M clients/karen/CLIENT_GROCERY.md",
            " M clients/karen/CLIENT_FOLDERS.json",
        ),
        after_status_short_branch=status
        or _status(
            " M clients/karen/CLIENT_GROCERY.md",
            " M clients/karen/CLIENT_FOLDERS.json",
        ),
        head="abc1234",
        after_head="abc1234",
    )


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


def test_valid_v2_packet_passes() -> None:
    packet = load_packet(ROOT / "docs" / "ops" / "night_runner_bedtime_packet_v2.yaml")
    result = evaluate_packet(packet, head="abc1234", after_head="abc1234")
    assert_equal(result.decision, DECISION_PASS, "valid v2 packet decision")
    assert_true(result.report_written, "v2 packet writes report")
    assert_true(result.tests_run, "v2 packet runs tests")
    assert_true(all(item.exit_code == 0 for item in result.tests_run), "exit codes captured")
    assert_contains(result.report, "PASS_BEDTIME_TRIAL_READY", "decision in report")


def test_boolean_guards_refuse(tmpdir: Path) -> None:
    for field in ("allow_file_edits", "allow_commit", "allow_restart", "allow_live_writes"):
        result = _run(_packet(tmpdir, **{field: True}))
        assert_equal(result.decision, DECISION_UNSAFE, f"{field} refuses")
        assert_contains(result.report, f"{field} must be false", f"{field} reason")


def test_report_path_refuses(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir, report_path="docs/ops/not_allowed.md"))
    assert_equal(result.decision, DECISION_REPORT, "outside report path refuses")


def test_non_allowlisted_test_refuses(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir, tests_to_run=["python3 scripts/quality/not_allowlisted.py"]))
    assert_equal(result.decision, DECISION_TEST, "non-allowlisted command refuses")
    assert_contains(result.report, "test command is not allowlisted", "allowlist reason")


def test_protected_staged_refuses(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir), _status("M  clients/karen/CLIENT_GROCERY.md"))
    assert_equal(result.decision, DECISION_PROTECTED, "protected staged refuses")
    assert_contains(result.report, "protected live file is staged", "protected staged reason")


def test_protected_dirty_forbidden_accepts(tmpdir: Path) -> None:
    result = _run(
        _packet(tmpdir),
        _status(
            " M clients/karen/CLIENT_GROCERY.md",
            " M clients/karen/CLIENT_FOLDERS.json",
        ),
    )
    assert_equal(result.decision, DECISION_PASS, "dirty protected forbidden accepts")
    assert_contains(result.report, "protected live file contents read: no", "live content guard")


def test_report_written_and_safe(tmpdir: Path) -> None:
    packet = _packet(tmpdir)
    result = _run(packet)
    assert_true(result.report_written, "report written")
    report_path = ROOT / packet["report_path"]
    assert_true(report_path.exists(), "report path exists")
    report = report_path.read_text(encoding="utf-8")
    assert_contains(report, "Decision: PASS_BEDTIME_TRIAL_READY", "report decision")
    assert_contains(report, "Tests:", "tests section")
    assert_contains(report, "exit 0", "exit code captured")
    assert_contains(report, "Report path:", "report path line")
    assert_contains(report, "Morning review options", "morning review section")
    for option in ("approve", "discard", "continue", "ask_valprime"):
        assert_contains(report, option, f"morning option {option}")
    for marker in ("refresh_token", "access_token", "client_secret", "sk-"):
        assert_not_contains(report, marker, "secret marker")


def test_no_staged_files() -> None:
    staged = set(_git_cached_names())
    for path in PROTECTED_FILES:
        assert_true(path not in staged, f"{path} is not staged")
    assert_true(not staged, "no staged files remain")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="night-runner-bedtime-trial-") as tmp:
        tmpdir = Path(tmp)
        test_valid_v2_packet_passes()
        test_boolean_guards_refuse(tmpdir)
        test_report_path_refuses(tmpdir)
        test_non_allowlisted_test_refuses(tmpdir)
        test_protected_staged_refuses(tmpdir)
        test_protected_dirty_forbidden_accepts(tmpdir)
        test_report_written_and_safe(tmpdir)
        test_no_staged_files()
    print("PASS night_runner_bedtime_trial_smoke")


if __name__ == "__main__":
    main()
