#!/usr/bin/env python3
from __future__ import annotations

import stat
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ops.night_runner_codex_readonly_plan import (  # noqa: E402
    GitSnapshot,
    evaluate_packet,
)


BRANCH = "val0-post-m41-conversationality-memory-lab-2026-05-25"
KAREN_CLIENT_ID = "kar" + "en"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
SECRET_SENTINELS = ("SUPER_SECRET_TOKEN", "sk-test-secret", "refresh_token", "access_token")


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


def _fake_codex(tmpdir: Path, *, exit_code: int = 0) -> str:
    binary = tmpdir / "codex"
    binary.write_text(
        "#!/bin/sh\n"
        "echo 'Read-only plan: inspect docs, add smoke, run audit. No files edited.'\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    return str(binary)


def _packet(report_name: str = "codex_readonly_plan_smoke_report.md", **overrides):
    packet = {
        "lane_id": "NIGHT-RUNNER-08-SMOKE",
        "branch_name": BRANCH,
        "task_mode": "readonly_plan",
        "task_prompt": "Inspect context and output a short implementation plan only.",
        "allowed_files": ["tmp/night_runner/"],
        "forbidden_files": [
            "clients/karen/CLIENT_GROCERY.md",
            "clients/karen/CLIENT_FOLDERS.json",
            "/etc/val0",
            "val0_memory.enc.db",
            "*.db",
            "*.sqlite",
        ],
        "tests_to_run": [
            "python3 scripts/quality/night_runner_codex_readonly_plan_smoke.py",
            "python3 scripts/quality/client_isolation_audit.py",
            "git diff --check",
        ],
        "report_path": f"tmp/night_runner/{report_name}",
        "allow_codex_execute": True,
        "allow_file_edits": False,
        "allow_commit": False,
        "allow_restart": False,
    }
    packet.update(overrides)
    return packet


def _assert_safe_report(report: str) -> None:
    assert_contains(report, "Night Runner Codex Read-only Planning Report", "report header")
    assert_contains(report, "Secret files were not read or printed", "secret safety")
    assert_contains(report, "Protected live client files were not touched", "protected safety")
    assert_contains(report, "No commits, restarts, live writes", "no live action")
    for sentinel in SECRET_SENTINELS:
        assert_not_contains(report, sentinel, f"secret sentinel hidden {sentinel}")


def test_execute_false_is_readiness_only() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_codex_plan_dry_") as tmp:
        packet = _packet("codex_plan_dry_report.md", allow_codex_execute=False)
        result = evaluate_packet(packet, codex_path_override=_fake_codex(Path(tmp)), invoke=False, git_snapshot=_fake_git())
        assert_equal(result.decision, "PASS_READONLY_PLAN_DRY_RUN_READY", "dry-run readiness decision")
        assert_true(not result.codex_executed, "dry-run does not invoke codex")
        assert_true(result.codex_exit_code is None, "dry-run has no exit code")
        _assert_safe_report(result.report)


def test_refuses_unsafe_packets() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_codex_plan_refuse_") as tmp:
        codex = _fake_codex(Path(tmp))
        cases = [
            (_packet("codex_plan_bad_mode.md", task_mode="noop_report"), "REFUSE_UNSAFE_PACKET", "task_mode"),
            (_packet("codex_plan_commit.md", allow_commit=True), "REFUSE_UNSAFE_PACKET", "allow_commit"),
            (_packet("codex_plan_restart.md", allow_restart=True), "REFUSE_UNSAFE_PACKET", "allow_restart"),
            (_packet("codex_plan_edits.md", allow_file_edits=True), "REFUSE_UNSAFE_PACKET", "allow_file_edits"),
            (_packet("codex_plan_bad_path.md", report_path="docs/ops/not_allowed.md"), "REFUSE_UNSAFE_PACKET", "report_path"),
            (_packet("codex_plan_allowed_docs.md", allowed_files=["docs/ops/"]), "REFUSE_UNSAFE_PACKET", "allowed_files"),
        ]
        for packet, decision, reason in cases:
            result = evaluate_packet(packet, codex_path_override=codex, invoke=False, git_snapshot=_fake_git())
            assert_equal(result.decision, decision, f"{reason} decision")
            assert_contains(result.report, reason, f"{reason} reason")


def test_missing_codex_and_staged_protected_refuse() -> None:
    missing = evaluate_packet(
        _packet("codex_plan_missing_report.md"),
        codex_path_override="/tmp/missing-codex-plan",
        invoke=False,
        git_snapshot=_fake_git(),
    )
    assert_equal(missing.decision, "REFUSE_CODEX_MISSING", "missing codex decision")
    assert_contains(missing.report, "codex binary not found", "missing codex reason")

    with tempfile.TemporaryDirectory(prefix="val0_codex_plan_staged_") as tmp:
        staged_git = _fake_git(f"## {BRANCH}\nM  clients/karen/CLIENT_GROCERY.md\n")
        staged = evaluate_packet(
            _packet("codex_plan_staged_report.md"),
            codex_path_override=_fake_codex(Path(tmp)),
            invoke=False,
            git_snapshot=staged_git,
        )
        assert_equal(staged.decision, "REFUSE_PROTECTED_FILE_RISK", "staged protected decision")
        assert_contains(staged.report, "staged", "staged reason")


def test_fake_actual_readonly_plan_invocation_does_not_change_live_files() -> None:
    before_grocery = _read_live_file(LIVE_GROCERY)
    before_folders = _read_live_file(LIVE_FOLDERS)
    with tempfile.TemporaryDirectory(prefix="val0_codex_plan_fake_run_") as tmp:
        result = evaluate_packet(
            _packet("codex_plan_fake_run_report.md"),
            codex_path_override=_fake_codex(Path(tmp)),
            invoke=True,
            git_snapshot=_fake_git(),
        )
        assert_equal(result.decision, "PASS_READONLY_PLAN_INVOKE_READY", "fake planning invocation decision")
        assert_true(result.codex_executed, "fake codex invoked")
        assert_equal(result.codex_exit_code, 0, "fake codex exit")
        assert_contains(result.report, "Read-only plan: inspect docs", "plan output captured")
        assert_contains(" ".join(result.command), " -o ", "last-message capture configured")
        assert_contains(result.report, "protected live files unchanged: True", "protected hashes unchanged")
        assert_contains(result.report, "git status/head unchanged: True", "git status unchanged")
        _assert_safe_report(result.report)
    assert_true(_read_live_file(LIVE_GROCERY) == before_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(_read_live_file(LIVE_FOLDERS) == before_folders, "CLIENT_FOLDERS.json untouched")


def test_nonzero_codex_is_reported() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_codex_plan_nonzero_") as tmp:
        result = evaluate_packet(
            _packet("codex_plan_nonzero_report.md"),
            codex_path_override=_fake_codex(Path(tmp), exit_code=6),
            invoke=True,
            git_snapshot=_fake_git(),
        )
        assert_equal(result.decision, "CODEX_READONLY_PLAN_FAILED", "nonzero decision")
        assert_equal(result.codex_exit_code, 6, "nonzero exit code captured")
        assert_contains(result.report, "codex exited nonzero: 6", "nonzero reason")


def main() -> None:
    test_execute_false_is_readiness_only()
    test_refuses_unsafe_packets()
    test_missing_codex_and_staged_protected_refuse()
    test_fake_actual_readonly_plan_invocation_does_not_change_live_files()
    test_nonzero_codex_is_reported()
    print("PASS night_runner_codex_readonly_plan_smoke")


if __name__ == "__main__":
    main()
