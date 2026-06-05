#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ops.night_runner_tiny_task_dry_run import (  # noqa: E402
    DECISION_FORBIDDEN_CHANGED,
    DECISION_PATCH_PASS,
    DECISION_PROTECTED,
    DECISION_RUNTIME_CHANGED,
    evaluate_packet,
    load_packet,
)


BRANCH = "val0-post-m41-conversationality-memory-lab-2026-05-25"
DOC = ROOT / "docs" / "ops" / "NIGHT_RUNNER_DOCS_DIAGNOSTIC.md"
PROTECTED_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)
ALLOWED_PATCH_FILES = (
    "scripts/ops/night_runner_tiny_task_dry_run.py",
    "scripts/quality/night_runner_tiny_task_execution_guard_smoke.py",
    "scripts/quality/night_runner_tiny_task_dry_run_smoke.py",
    "scripts/quality/night_runner_reported_patch_guard_smoke.py",
    "docs/ops/night_runner_tiny_task_packet.yaml",
    "docs/ops/NIGHT_RUNNER_DOCS_DIAGNOSTIC.md",
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
        "lane_id": "NIGHT-RUNNER-14-SMOKE",
        "task_name": "Tiny reported patch guard task",
        "task_mode": "reported_patch",
        "allowed_files": list(ALLOWED_PATCH_FILES),
        "forbidden_files": [
            *PROTECTED_FILES,
            "val0_memory.enc.db",
            "/etc/val0",
        ],
        "tests_to_run": [
            "python3 scripts/quality/night_runner_readiness_summary_smoke.py",
            "python3 scripts/quality/night_runner_docs_diagnostic_smoke.py",
        ],
        "report_path": f"tmp/night_runner/{tmpdir.name}_reported_patch_report.md",
        "allow_file_edits": False,
        "allow_commit": False,
        "allow_restart": False,
        "allow_live_writes": False,
        "run_tests": True,
    }
    packet.update(overrides)
    return packet


def _run(packet: dict, after_status: str):
    before = _status(
        " M clients/karen/CLIENT_GROCERY.md",
        " M clients/karen/CLIENT_FOLDERS.json",
    )
    return evaluate_packet(
        packet,
        status_short_branch=before,
        after_status_short_branch=after_status,
        branch=BRANCH,
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


def test_doc_section() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert_contains(text, "Reported Patch Guard", "reported patch section")
    assert_contains(text, "records exactly what changed", "changed-file language")
    assert_contains(text, "allowed_files", "allowed files language")


def test_sample_packet_reports_current_patch() -> None:
    packet = load_packet(ROOT / "docs" / "ops" / "night_runner_tiny_task_packet.yaml")
    result = evaluate_packet(packet, branch=BRANCH, head="abc1234")
    assert_equal(result.decision, DECISION_PATCH_PASS, "current patch guard decision")
    assert_contains(result.report, "Changed files summary", "changed files summary")
    assert_contains(result.report, "docs/ops/NIGHT_RUNNER_DOCS_DIAGNOSTIC.md", "doc changed file")


def test_allowed_changed_files_pass(tmpdir: Path) -> None:
    result = _run(
        _packet(tmpdir),
        _status(
            " M clients/karen/CLIENT_GROCERY.md",
            " M clients/karen/CLIENT_FOLDERS.json",
            " M docs/ops/NIGHT_RUNNER_DOCS_DIAGNOSTIC.md",
            " M scripts/ops/night_runner_tiny_task_dry_run.py",
        ),
    )
    assert_equal(result.decision, DECISION_PATCH_PASS, "allowed changed files pass")
    assert_contains(result.report, "PASS_TINY_REPORTED_PATCH_GUARD", "pass decision in report")


def test_forbidden_changed_file_refuses(tmpdir: Path) -> None:
    result = _run(
        _packet(tmpdir),
        _status(
            " M clients/karen/CLIENT_GROCERY.md",
            " M clients/karen/CLIENT_FOLDERS.json",
            " M val0_memory.enc.db",
        ),
    )
    assert_equal(result.decision, DECISION_FORBIDDEN_CHANGED, "forbidden changed file refuses")
    assert_contains(result.report, "changed forbidden file is not allowed", "forbidden reason")


def test_runtime_changed_file_refuses(tmpdir: Path) -> None:
    result = _run(
        _packet(tmpdir),
        _status(
            " M clients/karen/CLIENT_GROCERY.md",
            " M clients/karen/CLIENT_FOLDERS.json",
            " M bot.py",
        ),
    )
    assert_equal(result.decision, DECISION_RUNTIME_CHANGED, "runtime changed file refuses")
    assert_contains(result.report, "changed runtime file is not allowed", "runtime reason")


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
    assert_equal(result.decision, DECISION_PATCH_PASS, "dirty forbidden protected accepts")
    assert_contains(result.report, "protected live hashes unchanged: yes", "hash guard")


def test_report_and_output_safety(tmpdir: Path) -> None:
    packet = _packet(tmpdir)
    result = _run(
        packet,
        _status(
            " M clients/karen/CLIENT_GROCERY.md",
            " M clients/karen/CLIENT_FOLDERS.json",
            " M docs/ops/NIGHT_RUNNER_DOCS_DIAGNOSTIC.md",
        ),
    )
    assert_true(result.report_written, "report written")
    report_path = ROOT / packet["report_path"]
    assert_true(report_path.exists(), "report path exists")
    report = report_path.read_text(encoding="utf-8")
    assert_contains(report, "Decision: PASS_TINY_REPORTED_PATCH_GUARD", "report decision")
    assert_contains(report, "Changed files summary", "changed summary")
    for marker in ("refresh_token", "access_token", "client_secret", "sk-"):
        assert_not_contains(report, marker, "secret marker")
    assert_contains(report, "protected live file contents read: no", "no live content statement")


def test_no_staged_files() -> None:
    staged = set(_git_cached_names())
    for path in PROTECTED_FILES:
        assert_true(path not in staged, f"{path} is not staged")
    assert_true(not staged, "no staged files remain")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="night-runner-reported-patch-") as tmp:
        tmpdir = Path(tmp)
        test_doc_section()
        test_sample_packet_reports_current_patch()
        test_allowed_changed_files_pass(tmpdir)
        test_forbidden_changed_file_refuses(tmpdir)
        test_runtime_changed_file_refuses(tmpdir)
        test_protected_staged_refuses(tmpdir)
        test_protected_dirty_forbidden_accepts(tmpdir)
        test_report_and_output_safety(tmpdir)
        test_no_staged_files()
    print("PASS night_runner_reported_patch_guard_smoke")


if __name__ == "__main__":
    main()
