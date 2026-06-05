#!/usr/bin/env python3
from __future__ import annotations

import stat
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ops.night_runner_codex_attempt_dry_run import (  # noqa: E402
    GitSnapshot,
    evaluate_packet,
)


BRANCH = "val0-post-m41-conversationality-memory-lab-2026-05-25"
KAREN_CLIENT_ID = "kar" + "en"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
SECRET_SENTINELS = ("SUPER_SECRET_TOKEN", "sk-test-secret", "refresh_token")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_equal(left, right, label: str) -> None:
    if left != right:
        raise AssertionError(f"{label}: expected {right!r}, got {left!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _read_live_file(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _fake_git(status: str | None = None, *, branch: str = BRANCH) -> GitSnapshot:
    return GitSnapshot(
        branch=branch,
        head="abc1234",
        status_short_branch=status
        if status is not None
        else (
            f"## {BRANCH}\n"
            " M clients/karen/CLIENT_GROCERY.md\n"
            " M clients/karen/CLIENT_FOLDERS.json\n"
        ),
    )


def _fake_codex(tmpdir: Path) -> str:
    binary = tmpdir / "codex"
    binary.write_text("#!/bin/sh\nprintf 'fake codex should not run\\n'\n", encoding="utf-8")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    return str(binary)


def _packet(report_name: str = "codex_attempt_smoke_report.md", **overrides):
    packet = {
        "lane_id": "NIGHT-RUNNER-06-SMOKE",
        "branch_name": BRANCH,
        "task_prompt": "No-op Codex dry-run only. Report readiness; do not edit files.",
        "allowed_files": ["docs/ops/", "tmp/night_runner/"],
        "forbidden_files": [
            "clients/karen/CLIENT_GROCERY.md",
            "clients/karen/CLIENT_FOLDERS.json",
            "/etc/val0",
            "val0_memory.enc.db",
            "*.db",
            "*.sqlite",
        ],
        "tests_to_run": [
            "python3 scripts/quality/night_runner_codex_attempt_dry_run_smoke.py",
            "python3 scripts/quality/client_isolation_audit.py",
            "git diff --check",
        ],
        "report_path": f"tmp/night_runner/{report_name}",
        "allow_codex_execute": False,
        "allow_commit": False,
        "allow_restart": False,
    }
    packet.update(overrides)
    return packet


def _assert_safe_report(result) -> None:
    assert_contains(result.report, "Night Runner Codex Attempt Dry-Run", "report header")
    assert_contains(result.report, "Codex was not executed.", "no execution")
    assert_contains(result.report, "No commits, restarts, live writes", "no live actions")
    assert_contains(result.report, "Secret files were not read or printed.", "secret safety")
    assert_contains(result.report, "clients/karen/CLIENT_GROCERY.md", "protected grocery reported")
    assert_contains(result.report, "clients/karen/CLIENT_FOLDERS.json", "protected folders reported")
    for sentinel in SECRET_SENTINELS:
        assert_not_contains(result.report, sentinel, f"secret sentinel hidden: {sentinel}")


def test_valid_safe_packet_passes_and_writes_report() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_codex_attempt_valid_") as tmp:
        result = evaluate_packet(_packet(), _fake_git(), codex_path_override=_fake_codex(Path(tmp)))
        assert_equal(result.decision, "PASS_DRY_RUN_CODEX_ATTEMPT_READY", "valid packet decision")
        assert_true(result.report_written, "valid packet writes report")
        assert_contains(result.would_run_command, "codex", "would-run command includes codex")
        assert_contains(result.would_run_command, "--cwd /opt/val0", "would-run command includes cwd")
        assert_contains(result.would_run_command, "--sandbox workspace-write", "would-run command includes sandbox")
        _assert_safe_report(result)
        assert_true((ROOT / "tmp" / "night_runner" / "codex_attempt_smoke_report.md").exists(), "report file exists")


def test_missing_codex_refuses() -> None:
    result = evaluate_packet(_packet("codex_attempt_missing_report.md"), _fake_git(), codex_path_override="/tmp/does-not-exist-codex")
    assert_equal(result.decision, "REFUSE_CODEX_MISSING", "missing codex decision")
    assert_contains(result.report, "codex binary not found", "missing codex reason")


def test_protected_staged_refuses_and_dirty_forbidden_allowed() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_codex_attempt_protected_") as tmp:
        staged = _fake_git(f"## {BRANCH}\nM  clients/karen/CLIENT_GROCERY.md\n")
        staged_result = evaluate_packet(_packet("codex_attempt_staged_report.md"), staged, codex_path_override=_fake_codex(Path(tmp)))
        assert_equal(staged_result.decision, "REFUSE_PROTECTED_FILE_RISK", "staged protected decision")
        assert_contains(staged_result.report, "protected file is staged", "staged protected reason")

        dirty = _fake_git(f"## {BRANCH}\n M clients/karen/CLIENT_GROCERY.md\n M clients/karen/CLIENT_FOLDERS.json\n")
        dirty_result = evaluate_packet(_packet("codex_attempt_dirty_report.md"), dirty, codex_path_override=_fake_codex(Path(tmp)))
        assert_equal(dirty_result.decision, "PASS_DRY_RUN_CODEX_ATTEMPT_READY", "dirty forbidden protected allowed")


def test_unsafe_packet_refusals() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_codex_attempt_unsafe_") as tmp:
        codex = _fake_codex(Path(tmp))
        cases = [
            (_packet("codex_attempt_bad_path.md", report_path="../outside.md"), "REFUSE_UNSAFE_PACKET", "report_path"),
            (_packet("codex_attempt_execute.md", allow_codex_execute=True), "REFUSE_UNSAFE_PACKET", "allow_codex_execute"),
            (_packet("codex_attempt_commit.md", allow_commit=True), "REFUSE_UNSAFE_PACKET", "allow_commit"),
            (_packet("codex_attempt_restart.md", allow_restart=True), "REFUSE_UNSAFE_PACKET", "allow_restart"),
            (_packet("codex_attempt_broad.md", allowed_files=["."]), "REFUSE_UNSAFE_PACKET", "too broad"),
            (
                _packet("codex_attempt_prompt.md", task_prompt="Please run git commit and push."),
                "REFUSE_UNSAFE_PACKET",
                "unsafe request",
            ),
        ]
        for packet, decision, reason in cases:
            result = evaluate_packet(packet, _fake_git(), codex_path_override=codex)
            assert_equal(result.decision, decision, f"{reason} decision")
            assert_contains(result.report, reason, f"{reason} reason")


def test_branch_and_missing_field_refusals() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_codex_attempt_branch_") as tmp:
        codex = _fake_codex(Path(tmp))
        branch_result = evaluate_packet(_packet("codex_attempt_branch_report.md"), _fake_git(branch="other-branch"), codex_path_override=codex)
        assert_equal(branch_result.decision, "REFUSE_BRANCH_RISK", "branch mismatch decision")
        assert_contains(branch_result.report, "branch mismatch", "branch mismatch reason")

        missing = _packet("codex_attempt_missing_field_report.md")
        del missing["lane_id"]
        missing_result = evaluate_packet(missing, _fake_git(), codex_path_override=codex)
        assert_equal(missing_result.decision, "REFUSE_UNSAFE_PACKET", "missing field decision")
        assert_contains(missing_result.report, "missing required field", "missing field reason")


def test_live_files_untouched() -> None:
    before_grocery = _read_live_file(LIVE_GROCERY)
    before_folders = _read_live_file(LIVE_FOLDERS)
    with tempfile.TemporaryDirectory(prefix="val0_codex_attempt_live_files_") as tmp:
        result = evaluate_packet(_packet("codex_attempt_live_files_report.md"), _fake_git(), codex_path_override=_fake_codex(Path(tmp)))
        assert_equal(result.decision, "PASS_DRY_RUN_CODEX_ATTEMPT_READY", "live file safety packet passes")
    assert_true(_read_live_file(LIVE_GROCERY) == before_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(_read_live_file(LIVE_FOLDERS) == before_folders, "CLIENT_FOLDERS.json untouched")


def main() -> None:
    test_valid_safe_packet_passes_and_writes_report()
    test_missing_codex_refuses()
    test_protected_staged_refuses_and_dirty_forbidden_allowed()
    test_unsafe_packet_refusals()
    test_branch_and_missing_field_refusals()
    test_live_files_untouched()
    print("PASS night_runner_codex_attempt_dry_run_smoke")


if __name__ == "__main__":
    main()
