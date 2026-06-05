#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ops.night_runner_tiny_task_dry_run import (  # noqa: E402
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
        "lane_id": "NIGHT-RUNNER-12-SMOKE",
        "task_name": "Tiny safe dry-run readiness task",
        "task_mode": "dry_run",
        "allowed_files": [],
        "forbidden_files": list(PROTECTED_FILES),
        "tests_to_run": [
            "python3 scripts/quality/night_runner_readiness_summary_smoke.py",
            "python3 scripts/quality/night_runner_docs_diagnostic_smoke.py",
        ],
        "report_path": f"tmp/night_runner/{tmpdir.name}_tiny_task_report.md",
        "allow_file_edits": False,
        "allow_commit": False,
        "allow_restart": False,
        "allow_live_writes": False,
        "run_tests": True,
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
        branch=BRANCH,
        head="abc1234",
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


def test_valid_sample_packet_passes() -> None:
    packet = load_packet(ROOT / "docs" / "ops" / "night_runner_tiny_task_packet.yaml")
    result = evaluate_packet(packet, branch=BRANCH, head="abc1234")
    assert_equal(result.decision, DECISION_PASS, "sample packet decision")
    assert_true(result.report_written, "sample packet writes report")
    assert_contains(result.report, "Night Runner Tiny Task Dry-Run Report", "report title")
    assert_contains(result.report, "Tests summary", "tests summary")


def test_boolean_guards_refuse(tmpdir: Path) -> None:
    for field in ("allow_file_edits", "allow_commit", "allow_restart", "allow_live_writes"):
        packet = _packet(tmpdir, **{field: True})
        result = _run(packet)
        assert_equal(result.decision, DECISION_UNSAFE, f"{field} refuses")
        assert_contains(result.report, f"{field} must be false", f"{field} reason")


def test_report_path_refuses(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir, report_path="docs/ops/not_allowed.md"))
    assert_equal(result.decision, DECISION_REPORT, "outside report path refuses")
    assert_contains(result.report, "report_path must be under tmp/night_runner", "report path reason")


def test_non_allowlisted_test_refuses(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir, tests_to_run=["python3 scripts/quality/not_allowlisted.py"]))
    assert_equal(result.decision, DECISION_TEST, "non-allowlisted test refuses")
    assert_contains(result.report, "test command is not allowlisted", "test allowlist reason")


def test_protected_staged_refuses(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir), _status("M  clients/karen/CLIENT_GROCERY.md"))
    assert_equal(result.decision, DECISION_PROTECTED, "staged protected refuses")
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
    assert_contains(result.report, "CLIENT_GROCERY.md", "protected status reported")
    assert_contains(result.report, "protected live file contents read: no", "live content guard")


def test_missing_forbidden_protected_refuses(tmpdir: Path) -> None:
    packet = _packet(tmpdir, forbidden_files=["clients/karen/CLIENT_GROCERY.md"])
    result = _run(packet)
    assert_equal(result.decision, DECISION_PROTECTED, "missing protected forbidden refuses")
    assert_contains(result.report, "protected live file missing from forbidden_files", "missing protected reason")


def test_report_written_and_tests_run(tmpdir: Path) -> None:
    packet = _packet(tmpdir)
    result = _run(packet)
    assert_equal(result.decision, DECISION_PASS, "run-tests packet passes")
    assert_equal(len(result.tests_run), 2, "tests run count")
    assert_true(all(item.status == "PASS" for item in result.tests_run), "allowlisted diagnostics pass")
    report_path = ROOT / packet["report_path"]
    assert_true(report_path.exists(), "report path exists")
    report = report_path.read_text(encoding="utf-8")
    assert_contains(report, DECISION_PASS, "report contains decision")
    assert_contains(report, "run: 2", "report contains tests count")


def test_no_secret_or_live_content_markers(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir))
    for marker in ("refresh_token", "access_token", "client_secret", "sk-"):
        assert_not_contains(result.report, marker, "secret marker")
    assert_contains(result.report, "protected live file contents read: no", "no live content statement")
    assert_contains(result.report, "secret contents read: no", "no secret content statement")


def test_no_staged_files() -> None:
    staged = set(_git_cached_names())
    for path in PROTECTED_FILES:
        assert_true(path not in staged, f"{path} is not staged")
    assert_true(not staged, "no staged files remain")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="night-runner-tiny-task-") as tmp:
        tmpdir = Path(tmp)
        test_valid_sample_packet_passes()
        test_boolean_guards_refuse(tmpdir)
        test_report_path_refuses(tmpdir)
        test_non_allowlisted_test_refuses(tmpdir)
        test_protected_staged_refuses(tmpdir)
        test_protected_dirty_forbidden_accepts(tmpdir)
        test_missing_forbidden_protected_refuses(tmpdir)
        test_report_written_and_tests_run(tmpdir)
        test_no_secret_or_live_content_markers(tmpdir)
        test_no_staged_files()
    print("PASS night_runner_tiny_task_dry_run_smoke")


if __name__ == "__main__":
    main()
