#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ops.night_runner_dry_run import (  # noqa: E402
    GitSnapshot,
    evaluate_packet,
    load_lane_packet,
    validate_test_command,
)


BRANCH = "val0-post-m41-conversationality-memory-lab-2026-05-25"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_equal(left, right, label: str) -> None:
    if left != right:
        raise AssertionError(f"{label}: expected {right!r}, got {left!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def _git(status: str = f"## {BRANCH}\n") -> GitSnapshot:
    return GitSnapshot(branch=BRANCH, head="abc1234", status_short_branch=status)


def _packet(tmpdir: Path, **overrides):
    packet = {
        "lane_id": "NIGHT-RUNNER-SMOKE-001",
        "branch_name": BRANCH,
        "task_prompt": "Prepare a dry-run report only.",
        "allowed_files": [str(tmpdir), "tmp/night_runner/"],
        "forbidden_files": [
            "clients/karen/CLIENT_GROCERY.md",
            "clients/karen/CLIENT_FOLDERS.json",
        ],
        "tests_to_run": [
            "python3 scripts/diagnostics/val0_milestone_radar.py",
            "git diff --check",
        ],
        "commit_allowed": False,
        "restart_allowed": False,
        "destructive_commands_allowed": False,
        "report_path": str(tmpdir / "morning_report.md"),
        "stop_if_uncertain": True,
    }
    packet.update(overrides)
    return packet


def _run(packet: dict, git: GitSnapshot | None = None):
    return evaluate_packet(packet, git or _git())


def test_valid_minimal_passes(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir))
    assert_equal(result.decision, "PASS_DRY_RUN", "valid packet decision")
    assert_true(result.report_written, "valid packet writes report")
    assert_true((tmpdir / "morning_report.md").exists(), "report file exists")
    assert_contains(result.report, "PASS_DRY_RUN", "report says pass")
    assert_contains(result.report, "Tests it would run", "report lists tests")


def test_run_tests_allowed_commands(tmpdir: Path) -> None:
    packet = _packet(
        tmpdir,
        tests_to_run=[
            "python3 scripts/diagnostics/val0_milestone_radar.py",
            "git diff --check",
        ],
    )
    result = evaluate_packet(packet, _git(), run_tests=True)
    assert_equal(result.decision, "PASS_DRY_RUN", "run-tests safe packet decision")
    assert_equal(len(result.test_results), 2, "run-tests result count")
    assert_true(all(item.status == "PASS" for item in result.test_results), "allowed commands pass")
    assert_contains(result.report, "Tests run:", "run-tests report section")
    assert_contains(result.report, "pass: 2", "run-tests pass summary")


def test_dirty_live_data_refuses(tmpdir: Path) -> None:
    status = (
        f"## {BRANCH}\n"
        " M clients/karen/CLIENT_GROCERY.md\n"
        " M clients/karen/CLIENT_FOLDERS.json\n"
    )
    result = _run(_packet(tmpdir), _git(status))
    assert_equal(result.decision, "REFUSED", "dirty live data refuses")
    assert_contains(result.report, "forbidden file is dirty/staged", "dirty live reason")


def test_allow_protected_dirty_readonly_permits_forbidden_live_files(tmpdir: Path) -> None:
    status = (
        f"## {BRANCH}\n"
        " M clients/karen/CLIENT_GROCERY.md\n"
        " M clients/karen/CLIENT_FOLDERS.json\n"
    )
    result = evaluate_packet(
        _packet(tmpdir, tests_to_run=["python3 scripts/diagnostics/val0_milestone_radar.py"]),
        _git(status),
        run_tests=True,
        allow_protected_dirty_readonly=True,
    )
    assert_equal(result.decision, "PASS_DRY_RUN", "readonly protected dirty decision")
    assert_equal(len(result.test_results), 1, "readonly protected dirty runs safe test")
    assert_equal(result.test_results[0].status, "PASS", "readonly protected dirty safe test passes")
    assert_contains(result.report, "Protected live files are dirty and were not touched.", "protected dirty warning")


def test_allow_protected_dirty_requires_forbidden_listing(tmpdir: Path) -> None:
    status = f"## {BRANCH}\n M clients/karen/CLIENT_GROCERY.md\n"
    packet = _packet(tmpdir, forbidden_files=["clients/karen/CLIENT_FOLDERS.json"])
    result = evaluate_packet(packet, _git(status), allow_protected_dirty_readonly=True)
    assert_equal(result.decision, "REFUSED", "protected dirty missing forbidden listing refuses")
    assert_contains(result.report, "dirty protected file is not listed in forbidden_files", "missing forbidden listing reason")


def test_allow_protected_dirty_refuses_allowed_protected(tmpdir: Path) -> None:
    status = f"## {BRANCH}\n M clients/karen/CLIENT_GROCERY.md\n"
    packet = _packet(tmpdir, allowed_files=[str(tmpdir), "clients/karen/CLIENT_GROCERY.md"])
    result = evaluate_packet(packet, _git(status), allow_protected_dirty_readonly=True)
    assert_equal(result.decision, "REFUSED", "protected dirty in allowed_files refuses")
    assert_contains(result.report, "allowed_files includes forbidden", "protected allowed reason")


def test_allow_protected_dirty_refuses_staged_protected(tmpdir: Path) -> None:
    status = f"## {BRANCH}\nM  clients/karen/CLIENT_GROCERY.md\n"
    result = evaluate_packet(_packet(tmpdir), _git(status), allow_protected_dirty_readonly=True)
    assert_equal(result.decision, "REFUSED", "staged protected refuses")
    assert_contains(result.report, "staged protected file is not allowed", "staged protected reason")


def test_allow_protected_dirty_refuses_staged_changes(tmpdir: Path) -> None:
    status = f"## {BRANCH}\nM  docs/ops/example.md\n"
    result = evaluate_packet(_packet(tmpdir), _git(status), allow_protected_dirty_readonly=True)
    assert_equal(result.decision, "REFUSED", "staged non-protected refuses")
    assert_contains(result.report, "staged changes exist", "staged changes reason")


def test_allow_protected_dirty_refuses_nonprotected_dirty(tmpdir: Path) -> None:
    status = f"## {BRANCH}\n M scripts/ops/night_runner_dry_run.py\n"
    result = evaluate_packet(_packet(tmpdir), _git(status), allow_protected_dirty_readonly=True)
    assert_equal(result.decision, "REFUSED", "non-protected dirty refuses")
    assert_contains(result.report, "non-protected dirty file is not allowed", "non-protected dirty reason")


def test_refused_packet_runs_no_tests(tmpdir: Path) -> None:
    status = f"## {BRANCH}\n M clients/karen/CLIENT_GROCERY.md\n"
    result = evaluate_packet(_packet(tmpdir), _git(status), run_tests=True)
    assert_equal(result.decision, "REFUSED", "refused run-tests decision")
    assert_equal(len(result.test_results), 0, "refused packet does not run tests")
    assert_true((tmpdir / "morning_report.md").exists(), "refused packet still writes report")


def test_branch_mismatch_refuses(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir, branch_name="other-branch"))
    assert_equal(result.decision, "REFUSED", "branch mismatch refuses")
    assert_contains(result.report, "branch mismatch", "branch mismatch reason")


def test_boolean_guards_refuse(tmpdir: Path) -> None:
    for field in (
        "commit_allowed",
        "restart_allowed",
        "destructive_commands_allowed",
    ):
        result = _run(_packet(tmpdir, **{field: True}))
        assert_equal(result.decision, "REFUSED", f"{field} refuses")
        assert_contains(result.report, f"{field} must be false", f"{field} reason")


def test_broad_and_forbidden_allowed_files_refuse(tmpdir: Path) -> None:
    broad = _run(_packet(tmpdir, allowed_files=["."]))
    assert_equal(broad.decision, "REFUSED", "broad allowed_files refuses")
    assert_contains(broad.report, "too broad", "broad reason")

    forbidden = _run(_packet(tmpdir, allowed_files=["clients/karen/CLIENT_GROCERY.md"]))
    assert_equal(forbidden.decision, "REFUSED", "forbidden allowed_files refuses")
    assert_contains(forbidden.report, "includes forbidden", "forbidden allowed reason")


def test_staged_changes_refuse(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir), _git(f"## {BRANCH}\nM  docs/ops/example.md\n"))
    assert_equal(result.decision, "REFUSED", "staged changes refuse")
    assert_contains(result.report, "staged changes exist", "staged reason")


def test_report_path_safety_refuses(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir, report_path="clients/karen/CLIENT_GROCERY.md"))
    assert_equal(result.decision, "REFUSED", "forbidden report path refuses")
    assert_contains(result.report, "report_path targets forbidden file", "report path reason")


def test_missing_required_fields_refuse(tmpdir: Path) -> None:
    packet = _packet(tmpdir)
    del packet["lane_id"]
    result = _run(packet)
    assert_equal(result.decision, "REFUSED", "missing field refuses")
    assert_contains(result.report, "missing required field", "missing reason")


def test_prompt_forbidden_requests_refuse(tmpdir: Path) -> None:
    result = _run(_packet(tmpdir, task_prompt="Please commit and restart production."))
    assert_equal(result.decision, "REFUSED", "forbidden prompt refuses")
    assert_contains(result.report, "task_prompt contains forbidden request", "prompt reason")


def test_unsafe_test_command_rejected(tmpdir: Path) -> None:
    packet = _packet(tmpdir, tests_to_run=["git commit -m nope"])
    result = evaluate_packet(packet, _git(), run_tests=True)
    assert_equal(result.decision, "PASS_DRY_RUN", "unsafe command packet validation passes")
    assert_equal(len(result.test_results), 1, "unsafe command result count")
    assert_equal(result.test_results[0].status, "REJECTED", "unsafe command rejected")
    assert_contains(result.report, "REJECTED: git commit -m nope", "unsafe command report")


def test_failing_test_command_recorded(tmpdir: Path) -> None:
    packet = _packet(tmpdir, tests_to_run=["python3 scripts/quality/__missing_smoke.py"])
    result = evaluate_packet(packet, _git(), run_tests=True)
    assert_equal(result.decision, "PASS_DRY_RUN", "failing command packet validation passes")
    assert_equal(len(result.test_results), 1, "failing command result count")
    assert_equal(result.test_results[0].status, "FAIL", "failing command recorded")
    assert_true((result.test_results[0].exit_code or 0) != 0, "failing command exit code")


def test_command_allow_list() -> None:
    allowed, _reason, _parts = validate_test_command("python3 scripts/quality/night_runner_dry_run_smoke.py")
    assert_true(allowed, "quality smoke command allowed")
    allowed, _reason, _parts = validate_test_command("./scripts/val0py -m py_compile scripts/ops/night_runner_dry_run.py")
    assert_true(allowed, "py_compile command allowed")
    allowed, reason, _parts = validate_test_command("python3 scripts/quality/a.py && git status")
    assert_true(not allowed, "shell chaining rejected")
    assert_contains(reason, "unsafe command pattern", "shell chaining reason")


def test_packet_loaders(tmpdir: Path) -> None:
    json_path = tmpdir / "packet.json"
    json_path.write_text(json.dumps(_packet(tmpdir)), encoding="utf-8")
    assert_equal(load_lane_packet(json_path)["lane_id"], "NIGHT-RUNNER-SMOKE-001", "json loader")

    yaml_path = tmpdir / "packet.yaml"
    yaml_path.write_text(
        "\n".join(
            [
                "lane_id: NIGHT-RUNNER-SMOKE-002",
                f"branch_name: {BRANCH}",
                "task_prompt: Dry-run only.",
                "allowed_files:",
                f"  - {tmpdir}",
                "forbidden_files:",
                "  - clients/karen/CLIENT_GROCERY.md",
                "tests_to_run:",
                "  - git diff --check",
                "commit_allowed: false",
                "restart_allowed: false",
                "destructive_commands_allowed: false",
                f"report_path: {tmpdir / 'yaml_report.md'}",
                "stop_if_uncertain: true",
            ]
        ),
        encoding="utf-8",
    )
    assert_equal(load_lane_packet(yaml_path)["lane_id"], "NIGHT-RUNNER-SMOKE-002", "yaml loader")


def test_canonical_bedtime_packet(tmpdir: Path) -> None:
    packet_path = ROOT / "docs" / "ops" / "night_runner_bedtime_packet.yaml"
    assert_true(packet_path.exists(), "canonical bedtime packet exists")
    packet = load_lane_packet(packet_path)
    assert_equal(packet["lane_id"], "NIGHT-RUNNER-BEDTIME-DEFAULT", "bedtime lane id")
    assert_equal(packet["commit_allowed"], False, "bedtime commit disabled")
    assert_equal(packet["restart_allowed"], False, "bedtime restart disabled")
    assert_equal(packet["destructive_commands_allowed"], False, "bedtime destructive disabled")
    assert_contains(packet["report_path"], "tmp/night_runner/morning_report.md", "bedtime report path")
    assert_true("git diff --check" in packet["tests_to_run"], "bedtime includes diff check")

    test_packet = dict(packet)
    test_packet["report_path"] = str(tmpdir / "bedtime_report.md")
    result = evaluate_packet(test_packet, _git())
    assert_equal(result.decision, "PASS_DRY_RUN", "bedtime packet validates with clean synthetic git")
    assert_true(result.report_written, "bedtime packet writes report in smoke temp")


def test_help_runs() -> None:
    proc = subprocess.run(
        ["python3", "scripts/ops/night_runner_dry_run.py", "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert_equal(proc.returncode, 0, "help return code")
    assert_contains(proc.stdout, "Validate a Night Runner lane packet", "help copy")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="night_runner_smoke_") as tmp:
        tmpdir = Path(tmp)
        test_valid_minimal_passes(tmpdir)
        test_run_tests_allowed_commands(tmpdir)
        test_dirty_live_data_refuses(tmpdir)
        test_allow_protected_dirty_readonly_permits_forbidden_live_files(tmpdir)
        test_allow_protected_dirty_requires_forbidden_listing(tmpdir)
        test_allow_protected_dirty_refuses_allowed_protected(tmpdir)
        test_allow_protected_dirty_refuses_staged_protected(tmpdir)
        test_allow_protected_dirty_refuses_staged_changes(tmpdir)
        test_allow_protected_dirty_refuses_nonprotected_dirty(tmpdir)
        test_refused_packet_runs_no_tests(tmpdir)
        test_branch_mismatch_refuses(tmpdir)
        test_boolean_guards_refuse(tmpdir)
        test_broad_and_forbidden_allowed_files_refuse(tmpdir)
        test_staged_changes_refuse(tmpdir)
        test_report_path_safety_refuses(tmpdir)
        test_missing_required_fields_refuse(tmpdir)
        test_prompt_forbidden_requests_refuse(tmpdir)
        test_unsafe_test_command_rejected(tmpdir)
        test_failing_test_command_recorded(tmpdir)
        test_command_allow_list()
        test_packet_loaders(tmpdir)
        test_canonical_bedtime_packet(tmpdir)
        test_help_runs()
    print("PASS: Night Runner dry-run smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
