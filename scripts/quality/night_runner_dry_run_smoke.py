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


def test_dirty_live_data_refuses(tmpdir: Path) -> None:
    status = (
        f"## {BRANCH}\n"
        " M clients/karen/CLIENT_GROCERY.md\n"
        " M clients/karen/CLIENT_FOLDERS.json\n"
    )
    result = _run(_packet(tmpdir), _git(status))
    assert_equal(result.decision, "REFUSED", "dirty live data refuses")
    assert_contains(result.report, "forbidden file is dirty/staged", "dirty live reason")


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
        test_dirty_live_data_refuses(tmpdir)
        test_branch_mismatch_refuses(tmpdir)
        test_boolean_guards_refuse(tmpdir)
        test_broad_and_forbidden_allowed_files_refuse(tmpdir)
        test_staged_changes_refuse(tmpdir)
        test_missing_required_fields_refuse(tmpdir)
        test_prompt_forbidden_requests_refuse(tmpdir)
        test_packet_loaders(tmpdir)
        test_help_runs()
    print("PASS: Night Runner dry-run smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
