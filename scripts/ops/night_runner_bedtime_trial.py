#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROTECTED_LIVE_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)
REQUIRED_FIELDS = (
    "lane_id",
    "task_name",
    "task_mode",
    "allowed_files",
    "forbidden_files",
    "tests_to_run",
    "report_path",
    "allow_file_edits",
    "allow_commit",
    "allow_restart",
    "allow_live_writes",
    "morning_review",
)
ALLOWED_COMMANDS = (
    "python3 scripts/quality/night_runner_bedtime_packet_v2_smoke.py",
    "python3 scripts/quality/night_runner_patch_review_smoke.py",
    "python3 scripts/quality/night_runner_readiness_summary_smoke.py",
    "python3 scripts/quality/night_runner_tiny_task_execution_guard_smoke.py",
    "python3 scripts/quality/night_runner_reported_patch_guard_smoke.py",
    "python3 scripts/quality/client_isolation_audit.py",
    "git diff --check",
    "git status --short --branch",
)
DECISION_PASS = "PASS_BEDTIME_TRIAL_READY"
DECISION_MANUAL_PASS = "PASS_MANUAL_OVERNIGHT_TRIAL"
DECISION_UNSAFE = "REFUSE_UNSAFE_PACKET"
DECISION_PROTECTED = "REFUSE_PROTECTED_FILE_RISK"
DECISION_REPORT = "REFUSE_REPORT_PATH"
DECISION_TEST = "REFUSE_TEST_NOT_ALLOWLISTED"
DECISION_FAIL_TEST = "FAIL_BEDTIME_TEST_COMMAND"
DECISION_OVERNIGHT_FAIL_TEST = "FAIL_OVERNIGHT_TEST_COMMAND"
NEXT_LANE = "NIGHT-RUNNER-20 - First Real Manual Overnight Trial"
MANUAL_NEXT_LANE = "NIGHT-RUNNER-21 - First Tiny Useful Overnight Candidate"


@dataclass(frozen=True)
class CommandResult:
    command: str
    status: str
    exit_code: int | None
    output_excerpt: str


@dataclass(frozen=True)
class Snapshot:
    head: str
    status_short_branch: str
    staged_files: tuple[str, ...]
    protected_hashes: dict[str, str]


@dataclass(frozen=True)
class TrialResult:
    decision: str
    reasons: tuple[str, ...]
    report: str
    report_written: bool
    trial_report_path: str | None
    trial_report_written: bool
    tests_run: tuple[CommandResult, ...]
    before: Snapshot
    after: Snapshot


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current_key is None:
                raise ValueError("YAML list item found before a list key")
            data.setdefault(current_key, []).append(_parse_scalar(stripped[2:]))
            continue
        if ":" not in stripped:
            raise ValueError(f"Unsupported YAML line: {raw_line!r}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            data[key] = _parse_scalar(value)
            current_key = None
        else:
            data[key] = []
            current_key = key
    return data


def load_packet(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if path.suffix.lower() == ".json" or stripped.startswith("{"):
        loaded = json.loads(text)
    else:
        loaded = _parse_simple_yaml(text)
    if not isinstance(loaded, dict):
        raise ValueError("packet must be a JSON/YAML object")
    return loaded


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _git(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return (proc.stdout or proc.stderr or "").strip()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def protected_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for path in PROTECTED_LIVE_FILES:
        target = ROOT / path
        result[path] = _sha256_file(target) if target.exists() else "(missing)"
    return result


def current_staged_files() -> tuple[str, ...]:
    out = _git(["diff", "--cached", "--name-only"])
    return tuple(line.strip() for line in out.splitlines() if line.strip())


def snapshot(*, status_short_branch: str | None = None, head: str | None = None) -> Snapshot:
    return Snapshot(
        head=head if head is not None else (_git(["rev-parse", "--short", "HEAD"]) or "(unknown)"),
        status_short_branch=status_short_branch
        if status_short_branch is not None
        else (_git(["status", "--short", "--branch"]) or "(no output)"),
        staged_files=current_staged_files(),
        protected_hashes=protected_hashes(),
    )


def _status_entries(status_short_branch: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in status_short_branch.splitlines():
        if not line.strip() or line.startswith("##"):
            continue
        code = line[:2]
        path = line[3:].strip() if len(line) > 3 and line[2] == " " else line[2:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        entries.append((code, path))
    return entries


def _is_staged(code: str) -> bool:
    staged = code[0] if code else " "
    return staged not in {" ", "?"}


def _path_matches(path: str, pattern: str) -> bool:
    path = path.strip()
    pattern = pattern.strip()
    if not path or not pattern:
        return False
    if pattern.endswith("/**"):
        return path == pattern[:-3] or path.startswith(pattern[:-3].rstrip("/") + "/")
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


def _is_runtime(path: str) -> bool:
    return path == "bot.py" or path.startswith("core/")


def _safe_report_path(report_path: str) -> tuple[bool, str]:
    if not report_path:
        return False, "report_path is empty"
    candidate = Path(report_path)
    if candidate.is_absolute():
        return False, "report_path must be relative and under tmp/night_runner"
    normalized = candidate.as_posix()
    if not _path_matches(normalized, "tmp/night_runner"):
        return False, "report_path must be under tmp/night_runner"
    if normalized in {"tmp/night_runner", "tmp/night_runner/"}:
        return False, "report_path must be a file under tmp/night_runner"
    return True, ""


def _append_packet_guards(packet: dict[str, Any], reasons: list[str]) -> None:
    for field in REQUIRED_FIELDS:
        if field not in packet:
            reasons.append(f"missing required field: {field}")
    if packet.get("task_mode") != "bedtime_diagnostic":
        reasons.append("task_mode must be bedtime_diagnostic")
    for field in ("allow_file_edits", "allow_commit", "allow_restart", "allow_live_writes"):
        if packet.get(field) is not False:
            reasons.append(f"{field} must be false")


def _append_file_guards(packet: dict[str, Any], status_short_branch: str, reasons: list[str]) -> None:
    forbidden = _as_list(packet.get("forbidden_files"))
    for protected in PROTECTED_LIVE_FILES:
        if protected not in forbidden:
            reasons.append(f"protected live file missing from forbidden_files: {protected}")
    for code, path in _status_entries(status_short_branch):
        if _is_staged(code):
            reasons.append(f"staged changes are not allowed: {path}")
        if path in PROTECTED_LIVE_FILES:
            if _is_staged(code):
                reasons.append(f"protected live file is staged: {path}")
            if path not in forbidden:
                reasons.append(f"dirty protected live file is not forbidden: {path}")


def _append_test_guards(packet: dict[str, Any], reasons: list[str]) -> None:
    for command in _as_list(packet.get("tests_to_run")):
        if command not in ALLOWED_COMMANDS:
            reasons.append(f"test command is not allowlisted: {command}")


def _append_post_guards(before: Snapshot, after: Snapshot, packet: dict[str, Any], reasons: list[str]) -> None:
    if after.head != before.head:
        reasons.append(f"git head changed: {before.head} -> {after.head}")
    if after.staged_files:
        reasons.append(f"staged files exist after run: {', '.join(after.staged_files)}")
    if after.protected_hashes != before.protected_hashes:
        reasons.append("protected live file hash changed")
    forbidden = _as_list(packet.get("forbidden_files"))
    report_path = str(packet.get("report_path", ""))
    for _code, path in _status_entries(after.status_short_branch):
        if path in PROTECTED_LIVE_FILES:
            continue
        if report_path and _path_matches(path, str(Path(report_path).parent)):
            continue
        if _is_runtime(path):
            reasons.append(f"runtime file touched after run: {path}")
        for forbidden_path in forbidden:
            if _path_matches(path, forbidden_path):
                reasons.append(f"forbidden file touched after run: {path}")
                break


def _decision(reasons: list[str]) -> str:
    if not reasons:
        return DECISION_PASS
    if any("report_path" in reason for reason in reasons):
        return DECISION_REPORT
    if any("protected live file" in reason or "staged changes" in reason for reason in reasons):
        return DECISION_PROTECTED
    if any("test command is not allowlisted" in reason for reason in reasons):
        return DECISION_TEST
    if any("exited" in reason or "hash changed" in reason for reason in reasons):
        return DECISION_FAIL_TEST
    return DECISION_UNSAFE


def _run_command(command: str) -> CommandResult:
    proc = subprocess.run(
        command.split(),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = (proc.stdout or "").strip()
    return CommandResult(
        command=command,
        status="PASS" if proc.returncode == 0 else "FAIL",
        exit_code=proc.returncode,
        output_excerpt="\n".join(output.splitlines()[:40]),
    )


def _write_report(report_path: str, report: str) -> bool:
    ok, _reason = _safe_report_path(report_path)
    if not ok:
        return False
    target = ROOT / report_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report, encoding="utf-8")
    return True


def _safe_trial_report_path(trial_label: str) -> str:
    safe_label = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in trial_label)
    safe_label = safe_label.strip("_-") or "manual_overnight_trial"
    return f"tmp/night_runner/{safe_label}_report.md"


def render_report(
    packet: dict[str, Any],
    decision: str,
    reasons: list[str],
    before: Snapshot,
    after: Snapshot,
    tests: tuple[CommandResult, ...],
    *,
    title: str = "Night Runner Bedtime Report",
    trial_label: str | None = None,
    next_lane: str = NEXT_LANE,
) -> str:
    morning = _as_list(packet.get("morning_review"))
    changed_files = [path for _code, path in _status_entries(after.status_short_branch)]
    runtime_touched = _runtime_summary(after.status_short_branch)
    protected_touched = "no" if before.protected_hashes == after.protected_hashes else "yes"
    staged_files = ", ".join(after.staged_files) if after.staged_files else "none"
    lines = [
        title,
        "=" * len(title),
        "",
        "Decision",
        "--------",
        decision,
        "",
    ]
    if trial_label:
        lines.extend(["Trial Label", "-----------", trial_label, ""])
    lines.extend(
        [
        "Task",
        "----",
        f"- lane_id: {packet.get('lane_id', '(missing)')}",
        f"- task_name: {packet.get('task_name', '(missing)')}",
        f"- task_mode: {packet.get('task_mode', '(missing)')}",
        f"- report_path: {packet.get('report_path', '(missing)')}",
        "",
        "Reasons:",
        ]
    )
    lines.extend(f"- {reason}" for reason in reasons) if reasons else lines.append("- none")

    lines.extend(["", "Tests Run", "---------"])
    requested = _as_list(packet.get("tests_to_run"))
    if requested:
        lines.extend(f"- {command}" for command in requested)
    else:
        lines.append("- none")

    lines.extend(["", "Test Results / Exit Codes", "-------------------------"])
    if tests:
        lines.append(f"- run: {len(tests)}")
        lines.append(f"- pass: {sum(1 for item in tests if item.status == 'PASS')}")
        lines.append(f"- fail: {sum(1 for item in tests if item.status != 'PASS')}")
        for item in tests:
            lines.append(f"- {item.status}: {item.command} (exit {item.exit_code})")
    else:
        lines.append("- run: 0")

    lines.extend(["", "Changed Files", "-------------"])
    if changed_files:
        lines.extend(f"- {path}" for path in changed_files)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Safety Status",
            "-------------",
            f"- runtime files touched: {'no' if runtime_touched == 'none' else 'yes'}",
            f"- protected live files touched: {protected_touched}",
            f"- staged files: {'yes' if after.staged_files else 'no'} ({staged_files})",
            f"- commits allowed: {'yes' if packet.get('allow_commit') else 'no'}",
            f"- restarts allowed: {'yes' if packet.get('allow_restart') else 'no'}",
            f"- live writes allowed: {'yes' if packet.get('allow_live_writes') else 'no'}",
            "- protected live file contents read: no",
            "- secret contents read: no",
            "",
            "Protected Live Data",
            "-------------------",
        ]
    )
    for path in PROTECTED_LIVE_FILES:
        state = "clean-or-unreported"
        for code, status_path in _status_entries(after.status_short_branch):
            if status_path == path:
                state = f"reported by git status ({code})"
        lines.append(f"- {path}: {state}; contents printed: no")

    lines.extend(["", "Morning Review Options", "----------------------"])
    lines.extend(f"- {item}" for item in morning)
    lines.extend(
        [
            "",
            "Before/after safety checks:",
            f"- git head unchanged: {'yes' if before.head == after.head else 'no'}",
            f"- staged files after run: {staged_files}",
            f"- protected live hashes unchanged: {'yes' if before.protected_hashes == after.protected_hashes else 'no'}",
            f"- runtime files touched: {runtime_touched}",
            "",
            "Recommended Next Step",
            "---------------------",
            f"- {next_lane}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _runtime_summary(status_short_branch: str) -> str:
    paths = [path for _code, path in _status_entries(status_short_branch) if _is_runtime(path)]
    return ", ".join(paths) if paths else "none"


def evaluate_packet(
    packet: dict[str, Any],
    *,
    status_short_branch: str | None = None,
    after_status_short_branch: str | None = None,
    head: str | None = None,
    after_head: str | None = None,
    trial_label: str | None = None,
) -> TrialResult:
    status = status_short_branch if status_short_branch is not None else (_git(["status", "--short", "--branch"]) or "")
    before = snapshot(status_short_branch=status, head=head)
    reasons: list[str] = []
    _append_packet_guards(packet, reasons)
    _append_file_guards(packet, status, reasons)
    ok_report, report_reason = _safe_report_path(str(packet.get("report_path", "")))
    if not ok_report:
        reasons.append(report_reason)
    _append_test_guards(packet, reasons)
    decision = _decision(reasons)
    tests: tuple[CommandResult, ...] = ()
    if decision == DECISION_PASS and packet.get("run_tests") is True:
        tests = tuple(_run_command(command) for command in _as_list(packet.get("tests_to_run")))
        for item in tests:
            if item.status != "PASS":
                reasons.append(f"bedtime diagnostic failed: {item.command} exited {item.exit_code}")
    after = snapshot(
        status_short_branch=after_status_short_branch
        if after_status_short_branch is not None
        else (status if status_short_branch is not None else None),
        head=after_head if after_head is not None else (head if head is not None else None),
    )
    if decision == DECISION_PASS:
        _append_post_guards(before, after, packet, reasons)
    decision = _decision(reasons)
    if trial_label and decision == DECISION_PASS:
        decision = DECISION_MANUAL_PASS
    elif trial_label and decision == DECISION_FAIL_TEST:
        decision = DECISION_OVERNIGHT_FAIL_TEST
    report = render_report(
        packet,
        decision,
        reasons,
        before,
        after,
        tests,
        title="Night Runner Manual Overnight Trial" if trial_label else "Night Runner Bedtime Report",
        trial_label=trial_label,
        next_lane=MANUAL_NEXT_LANE if trial_label else NEXT_LANE,
    )
    report_written = _write_report(str(packet.get("report_path", "")), report) if ok_report else False
    trial_report_path = _safe_trial_report_path(trial_label) if trial_label and ok_report else None
    trial_report_written = _write_report(trial_report_path, report) if trial_report_path else False
    return TrialResult(
        decision=decision,
        reasons=tuple(reasons),
        report=report,
        report_written=report_written,
        trial_report_path=trial_report_path,
        trial_report_written=trial_report_written,
        tests_run=tests,
        before=before,
        after=after,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a guarded Night Runner bedtime workflow v2 trial.")
    parser.add_argument("--packet", required=True, help="Path to bedtime workflow v2 packet.")
    parser.add_argument(
        "--trial-label",
        default=None,
        help="Run as a manual overnight trial and write tmp/night_runner/<label>_report.md.",
    )
    args = parser.parse_args(argv)
    packet = load_packet(Path(args.packet))
    result = evaluate_packet(packet, trial_label=args.trial_label)
    print(result.report, end="")
    print("")
    print("Morning Review Summary")
    print("======================")
    print(f"decision: {result.decision}")
    passed = sum(1 for item in result.tests_run if item.status == "PASS")
    failed = sum(1 for item in result.tests_run if item.status != "PASS")
    changed_files = [path for _code, path in _status_entries(result.after.status_short_branch)]
    runtime_touched = _runtime_summary(result.after.status_short_branch)
    protected_touched = "no" if result.before.protected_hashes == result.after.protected_hashes else "yes"
    print(f"tests run: {len(result.tests_run)}")
    print(f"tests passed: {passed}")
    print(f"tests failed: {failed}")
    print(f"report path: {packet.get('report_path')}")
    if result.trial_report_path:
        print(f"trial report path: {result.trial_report_path}")
    print("changed files: " + (", ".join(changed_files) if changed_files else "none"))
    print(
        "safety status: "
        f"runtime files touched={runtime_touched}; "
        f"protected live files touched={protected_touched}; "
        f"staged files={len(result.after.staged_files)}"
    )
    print("morning review options: " + ", ".join(_as_list(packet.get("morning_review"))))
    print(f"next suggested lane: {MANUAL_NEXT_LANE if args.trial_label else NEXT_LANE}")
    return 0 if result.decision in {DECISION_PASS, DECISION_MANUAL_PASS} else 1


if __name__ == "__main__":
    raise SystemExit(main())
