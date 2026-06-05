#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
)
ALLOWED_TEST_COMMANDS = (
    "python3 scripts/quality/night_runner_readiness_summary_smoke.py",
    "python3 scripts/quality/night_runner_docs_diagnostic_smoke.py",
    "python3 scripts/quality/client_isolation_audit.py",
    "git diff --check",
)
DECISION_PASS = "PASS_TINY_TASK_DRY_RUN_READY"
DECISION_UNSAFE = "REFUSE_UNSAFE_PACKET"
DECISION_PROTECTED = "REFUSE_PROTECTED_FILE_RISK"
DECISION_REPORT = "REFUSE_REPORT_PATH"
DECISION_TEST = "REFUSE_TEST_NOT_ALLOWLISTED"


@dataclass(frozen=True)
class CommandResult:
    command: str
    status: str
    exit_code: int | None
    output_excerpt: str


@dataclass(frozen=True)
class TinyTaskResult:
    decision: str
    reasons: tuple[str, ...]
    report: str
    report_written: bool
    tests_run: tuple[CommandResult, ...]


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
    current_list_key: str | None = None
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current_list_key is None:
                raise ValueError("YAML list item found before a list key")
            data.setdefault(current_list_key, []).append(_parse_scalar(stripped[2:]))
            continue
        if ":" not in stripped:
            raise ValueError(f"Unsupported YAML line: {raw_line!r}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            data[key] = _parse_scalar(value)
            current_list_key = None
        else:
            data[key] = []
            current_list_key = key
    return data


def load_packet(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if path.suffix.lower() == ".json" or stripped.startswith("{"):
        packet = json.loads(text)
    else:
        packet = _parse_simple_yaml(text)
    if not isinstance(packet, dict):
        raise ValueError("packet must be a JSON/YAML object")
    return packet


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


def current_git_status() -> str:
    return _git(["status", "--short", "--branch"]) or "(no output)"


def current_branch() -> str:
    return _git(["branch", "--show-current"]) or "(unknown)"


def current_head() -> str:
    return _git(["rev-parse", "--short", "HEAD"]) or "(unknown)"


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
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


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


def _append_setting_guards(packet: dict[str, Any], reasons: list[str]) -> None:
    if packet.get("task_mode") != "dry_run":
        reasons.append("task_mode must be dry_run")
    for field in ("allow_file_edits", "allow_commit", "allow_restart", "allow_live_writes"):
        if packet.get(field) is not False:
            reasons.append(f"{field} must be false")


def _append_required_field_guards(packet: dict[str, Any], reasons: list[str]) -> None:
    for field in REQUIRED_FIELDS:
        if field not in packet:
            reasons.append(f"missing required field: {field}")


def _append_protected_file_guards(
    *,
    status_short_branch: str,
    forbidden_files: list[str],
    reasons: list[str],
) -> None:
    for code, path in _status_entries(status_short_branch):
        if _is_staged(code):
            reasons.append(f"staged changes are not allowed: {path}")
        if path in PROTECTED_LIVE_FILES:
            if _is_staged(code):
                reasons.append(f"protected live file is staged: {path}")
            if path not in forbidden_files:
                reasons.append(f"dirty protected live file is not forbidden: {path}")


def _append_file_scope_guards(
    *,
    allowed_files: list[str],
    forbidden_files: list[str],
    reasons: list[str],
) -> None:
    for protected in PROTECTED_LIVE_FILES:
        if protected not in forbidden_files:
            reasons.append(f"protected live file missing from forbidden_files: {protected}")
    for allowed in allowed_files:
        for forbidden in forbidden_files:
            if _path_matches(allowed, forbidden):
                reasons.append(f"allowed_files includes forbidden file: {allowed}")


def _append_test_guards(tests_to_run: list[str], reasons: list[str]) -> None:
    for command in tests_to_run:
        if command not in ALLOWED_TEST_COMMANDS:
            reasons.append(f"test command is not allowlisted: {command}")


def _classify_decision(reasons: list[str]) -> str:
    if not reasons:
        return DECISION_PASS
    if any("report_path" in reason for reason in reasons):
        return DECISION_REPORT
    if any("protected live file" in reason or "staged changes" in reason for reason in reasons):
        return DECISION_PROTECTED
    if any("test command is not allowlisted" in reason for reason in reasons):
        return DECISION_TEST
    return DECISION_UNSAFE


def _run_test_command(command: str) -> CommandResult:
    proc = subprocess.run(
        command.split(),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = (proc.stdout or "").strip()
    excerpt = "\n".join(output.splitlines()[:40])
    return CommandResult(
        command=command,
        status="PASS" if proc.returncode == 0 else "FAIL",
        exit_code=proc.returncode,
        output_excerpt=excerpt,
    )


def _write_report(path: str, text: str) -> bool:
    ok, _reason = _safe_report_path(path)
    if not ok:
        return False
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return True


def render_report(
    *,
    packet: dict[str, Any],
    decision: str,
    reasons: list[str],
    status_short_branch: str,
    branch: str,
    head: str,
    tests_run: tuple[CommandResult, ...],
) -> str:
    tests_to_run = _as_list(packet.get("tests_to_run"))
    lines = [
        "Night Runner Tiny Task Dry-Run Report",
        "=====================================",
        "",
        f"Decision: {decision}",
        f"Lane: {packet.get('lane_id', '(missing)')}",
        f"Task: {packet.get('task_name', '(missing)')}",
        f"Branch: {branch}",
        f"Head: {head}",
        "",
        "Safety settings:",
        f"- allow_file_edits: {packet.get('allow_file_edits', '(missing)')}",
        f"- allow_commit: {packet.get('allow_commit', '(missing)')}",
        f"- allow_restart: {packet.get('allow_restart', '(missing)')}",
        f"- allow_live_writes: {packet.get('allow_live_writes', '(missing)')}",
        "- protected live file contents read: no",
        "- secret contents read: no",
        "",
        "Reasons:",
    ]
    if reasons:
        lines.extend(f"- {reason}" for reason in reasons)
    else:
        lines.append("- none")

    lines.extend(["", "Protected live files:"])
    forbidden_files = set(_as_list(packet.get("forbidden_files")))
    for protected in PROTECTED_LIVE_FILES:
        forbidden = "yes" if protected in forbidden_files else "no"
        state = "clean-or-unreported"
        for code, path in _status_entries(status_short_branch):
            if path == protected:
                state = f"reported by git status ({code})"
        lines.append(f"- {protected}: forbidden={forbidden}; {state}")

    lines.extend(["", "Tests summary:"])
    if tests_run:
        passed = sum(1 for item in tests_run if item.status == "PASS")
        failed = sum(1 for item in tests_run if item.status != "PASS")
        lines.append(f"- run: {len(tests_run)}")
        lines.append(f"- pass: {passed}")
        lines.append(f"- fail: {failed}")
        for item in tests_run:
            lines.append(f"- {item.status}: {item.command} (exit {item.exit_code})")
    else:
        lines.append("- run: 0")
        lines.append("- dry-run did not execute tests")

    lines.extend(["", "Tests requested:"])
    if tests_to_run:
        lines.extend(f"- {command}" for command in tests_to_run)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Git status:",
            *[f"  {line}" for line in status_short_branch.splitlines()],
            "",
            "Next morning action:",
            "- Review this report, confirm no protected data was touched, then choose the next branch-only lane.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def evaluate_packet(
    packet: dict[str, Any],
    *,
    status_short_branch: str | None = None,
    branch: str | None = None,
    head: str | None = None,
) -> TinyTaskResult:
    status = status_short_branch if status_short_branch is not None else current_git_status()
    actual_branch = branch if branch is not None else current_branch()
    actual_head = head if head is not None else current_head()
    reasons: list[str] = []

    _append_required_field_guards(packet, reasons)
    allowed_files = _as_list(packet.get("allowed_files"))
    forbidden_files = _as_list(packet.get("forbidden_files"))
    tests_to_run = _as_list(packet.get("tests_to_run"))
    report_path = str(packet.get("report_path", "")).strip()
    run_tests = packet.get("run_tests") is True

    _append_setting_guards(packet, reasons)
    _append_file_scope_guards(allowed_files=allowed_files, forbidden_files=forbidden_files, reasons=reasons)
    _append_protected_file_guards(
        status_short_branch=status,
        forbidden_files=forbidden_files,
        reasons=reasons,
    )
    ok_report, report_reason = _safe_report_path(report_path)
    if not ok_report:
        reasons.append(report_reason)
    _append_test_guards(tests_to_run, reasons)

    decision = _classify_decision(reasons)
    tests_run: tuple[CommandResult, ...] = ()
    if decision == DECISION_PASS and run_tests:
        tests_run = tuple(_run_test_command(command) for command in tests_to_run)

    report = render_report(
        packet=packet,
        decision=decision,
        reasons=reasons,
        status_short_branch=status,
        branch=actual_branch,
        head=actual_head,
        tests_run=tests_run,
    )
    report_written = _write_report(report_path, report) if ok_report else False
    return TinyTaskResult(
        decision=decision,
        reasons=tuple(reasons),
        report=report,
        report_written=report_written,
        tests_run=tests_run,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny Night Runner task packet in dry-run mode.")
    parser.add_argument("--packet", required=True, help="Path to a JSON/YAML tiny task packet.")
    args = parser.parse_args(argv)
    packet = load_packet(Path(args.packet))
    result = evaluate_packet(packet)
    print(result.report, end="")
    return 0 if result.decision == DECISION_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
