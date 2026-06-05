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
)
ALLOWED_TEST_COMMANDS = (
    "python3 scripts/quality/night_runner_readiness_summary_smoke.py",
    "python3 scripts/quality/night_runner_docs_diagnostic_smoke.py",
    "python3 scripts/quality/night_runner_tiny_task_dry_run_smoke.py",
    "python3 scripts/quality/client_isolation_audit.py",
    "git diff --check",
    "git status --short --branch",
)
VALID_TASK_MODES = {"dry_run", "safe_diagnostic", "dry_run_with_tests", "reported_patch"}
EXECUTION_TASK_MODES = {"safe_diagnostic", "dry_run_with_tests", "reported_patch"}
PATCH_TASK_MODES = {"reported_patch"}
DECISION_PASS = "PASS_TINY_TASK_DRY_RUN_READY"
DECISION_EXECUTION_PASS = "PASS_TINY_TASK_EXECUTION_GUARD"
DECISION_PATCH_PASS = "PASS_TINY_REPORTED_PATCH_GUARD"
DECISION_UNSAFE = "REFUSE_UNSAFE_PACKET"
DECISION_PROTECTED = "REFUSE_PROTECTED_FILE_RISK"
DECISION_REPORT = "REFUSE_REPORT_PATH"
DECISION_TEST = "REFUSE_TEST_NOT_ALLOWLISTED"
DECISION_FAIL_TEST = "FAIL_SAFE_TEST_COMMAND"
DECISION_FORBIDDEN_CHANGED = "REFUSE_CHANGED_FORBIDDEN_FILE"
DECISION_RUNTIME_CHANGED = "REFUSE_CHANGED_RUNTIME_FILE"


@dataclass(frozen=True)
class CommandResult:
    command: str
    status: str
    exit_code: int | None
    output_excerpt: str


@dataclass(frozen=True)
class SafetySnapshot:
    head: str
    status_short_branch: str
    staged_files: tuple[str, ...]
    protected_hashes: dict[str, str]


@dataclass(frozen=True)
class TinyTaskResult:
    decision: str
    reasons: tuple[str, ...]
    report: str
    report_written: bool
    tests_run: tuple[CommandResult, ...]
    before: SafetySnapshot | None = None
    after: SafetySnapshot | None = None


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


def current_staged_files() -> tuple[str, ...]:
    out = _git(["diff", "--cached", "--name-only"])
    return tuple(line.strip() for line in out.splitlines() if line.strip())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def protected_live_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in PROTECTED_LIVE_FILES:
        target = ROOT / path
        hashes[path] = _sha256_file(target) if target.exists() else "(missing)"
    return hashes


def safety_snapshot(*, status_short_branch: str | None = None, head: str | None = None) -> SafetySnapshot:
    return SafetySnapshot(
        head=head if head is not None else current_head(),
        status_short_branch=status_short_branch if status_short_branch is not None else current_git_status(),
        staged_files=current_staged_files(),
        protected_hashes=protected_live_hashes(),
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
    if packet.get("task_mode") not in VALID_TASK_MODES:
        reasons.append("task_mode must be safe_diagnostic or dry_run_with_tests")
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


def changed_files_from_status(status_short_branch: str) -> tuple[str, ...]:
    return tuple(path for _code, path in _status_entries(status_short_branch))


def _is_runtime_file(path: str) -> bool:
    return path == "bot.py" or path.startswith("core/")


def _is_report_path(path: str, report_path: str) -> bool:
    if not report_path:
        return False
    report = Path(report_path)
    if report.is_absolute():
        return False
    report_posix = report.as_posix()
    return path == report_posix or _path_matches(path, "tmp/night_runner")


def _path_allowed_by(path: str, allowed_files: list[str]) -> bool:
    return any(_path_matches(path, allowed) for allowed in allowed_files)


def _append_reported_patch_guards(
    *,
    after_status_short_branch: str,
    allowed_files: list[str],
    forbidden_files: list[str],
    report_path: str,
    reasons: list[str],
) -> None:
    for code, path in _status_entries(after_status_short_branch):
        if _is_staged(code):
            reasons.append(f"staged changes are not allowed: {path}")
        if _is_report_path(path, report_path):
            continue
        if path in PROTECTED_LIVE_FILES:
            if _is_staged(code):
                reasons.append(f"protected live file is staged: {path}")
            continue
        if _is_runtime_file(path):
            reasons.append(f"changed runtime file is not allowed: {path}")
            continue
        for forbidden in forbidden_files:
            if _path_matches(path, forbidden):
                reasons.append(f"changed forbidden file is not allowed: {path}")
                break
        else:
            if not _path_allowed_by(path, allowed_files):
                reasons.append(f"changed file is outside allowed_files: {path}")


def _append_test_guards(tests_to_run: list[str], reasons: list[str]) -> None:
    for command in tests_to_run:
        if command not in ALLOWED_TEST_COMMANDS:
            reasons.append(f"test command is not allowlisted: {command}")


def _classify_decision(reasons: list[str]) -> str:
    if not reasons:
        return DECISION_PASS
    if any("changed runtime file" in reason for reason in reasons):
        return DECISION_RUNTIME_CHANGED
    if any("changed forbidden file" in reason or "outside allowed_files" in reason for reason in reasons):
        return DECISION_FORBIDDEN_CHANGED
    if any("report_path" in reason for reason in reasons):
        return DECISION_REPORT
    if any("protected live file" in reason or "staged changes" in reason for reason in reasons):
        return DECISION_PROTECTED
    if any("test command is not allowlisted" in reason for reason in reasons):
        return DECISION_TEST
    if any("safe diagnostic failed" in reason or "post-run safety check failed" in reason for reason in reasons):
        return DECISION_FAIL_TEST
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


def _append_post_run_guards(before: SafetySnapshot, after: SafetySnapshot, reasons: list[str]) -> None:
    if after.head != before.head:
        reasons.append(f"post-run safety check failed: git head changed {before.head} -> {after.head}")
    if after.staged_files:
        reasons.append(f"post-run safety check failed: staged files exist: {', '.join(after.staged_files)}")
    for path, before_hash in before.protected_hashes.items():
        after_hash = after.protected_hashes.get(path)
        if after_hash != before_hash:
            reasons.append(f"post-run safety check failed: protected live file hash changed: {path}")
    runtime_touched = [
        path
        for _code, path in _status_entries(after.status_short_branch)
        if path == "bot.py" or path.startswith("core/")
    ]
    if runtime_touched:
        reasons.append(f"post-run safety check failed: runtime file touched: {', '.join(runtime_touched)}")


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
    before: SafetySnapshot | None = None,
    after: SafetySnapshot | None = None,
) -> str:
    tests_to_run = _as_list(packet.get("tests_to_run"))
    changed_files = changed_files_from_status(after.status_short_branch if after else status_short_branch)
    lines = [
        "Night Runner Tiny Task Execution Guard Report",
        "=============================================",
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
        lines.append("- execution guard did not execute tests")

    lines.extend(["", "Tests requested:"])
    if tests_to_run:
        lines.extend(f"- {command}" for command in tests_to_run)
    else:
        lines.append("- none")

    lines.extend(["", "Changed files summary:"])
    if changed_files:
        lines.extend(f"- {path}" for path in changed_files)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Before/after safety checks:",
            f"- git head unchanged: {_yes_no(before is not None and after is not None and before.head == after.head)}",
            f"- staged files after run: {', '.join(after.staged_files) if after and after.staged_files else 'none'}",
            f"- protected live hashes unchanged: {_yes_no(_protected_hashes_unchanged(before, after))}",
            f"- runtime files touched: {_runtime_touched_summary(after)}",
            "",
            "Git status:",
        ]
    )
    lines.extend(f"  {line}" for line in status_short_branch.splitlines())
    lines.extend(
        [
            "",
            "Next morning action:",
            "- Review this report, confirm no protected data was touched, then choose the next branch-only lane.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _protected_hashes_unchanged(before: SafetySnapshot | None, after: SafetySnapshot | None) -> bool:
    if before is None or after is None:
        return False
    return before.protected_hashes == after.protected_hashes


def _runtime_touched_summary(snapshot: SafetySnapshot | None) -> str:
    if snapshot is None:
        return "unknown"
    paths = [
        path
        for _code, path in _status_entries(snapshot.status_short_branch)
        if path == "bot.py" or path.startswith("core/")
    ]
    return ", ".join(paths) if paths else "none"


def evaluate_packet(
    packet: dict[str, Any],
    *,
    status_short_branch: str | None = None,
    after_status_short_branch: str | None = None,
    branch: str | None = None,
    head: str | None = None,
    after_head: str | None = None,
) -> TinyTaskResult:
    status = status_short_branch if status_short_branch is not None else current_git_status()
    actual_branch = branch if branch is not None else current_branch()
    actual_head = head if head is not None else current_head()
    before = safety_snapshot(status_short_branch=status, head=actual_head)
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
        for item in tests_run:
            if item.status != "PASS":
                reasons.append(f"safe diagnostic failed: {item.command} exited {item.exit_code}")

    after = safety_snapshot(
        status_short_branch=after_status_short_branch
        if after_status_short_branch is not None
        else (status if status_short_branch is not None else None),
        head=after_head if after_head is not None else (actual_head if head is not None else None),
    )
    if decision == DECISION_PASS:
        _append_post_run_guards(before, after, reasons)
        if packet.get("task_mode") in PATCH_TASK_MODES:
            _append_reported_patch_guards(
                after_status_short_branch=after.status_short_branch,
                allowed_files=allowed_files,
                forbidden_files=forbidden_files,
                report_path=report_path,
                reasons=reasons,
            )

    if reasons:
        decision = _classify_decision(reasons)
    elif packet.get("task_mode") in PATCH_TASK_MODES:
        decision = DECISION_PATCH_PASS
    elif packet.get("task_mode") in EXECUTION_TASK_MODES and run_tests:
        decision = DECISION_EXECUTION_PASS

    report = render_report(
        packet=packet,
        decision=decision,
        reasons=reasons,
        status_short_branch=status,
        branch=actual_branch,
        head=actual_head,
        tests_run=tests_run,
        before=before,
        after=after,
    )
    report_written = _write_report(report_path, report) if ok_report else False
    return TinyTaskResult(
        decision=decision,
        reasons=tuple(reasons),
        report=report,
        report_written=report_written,
        tests_run=tests_run,
        before=before,
        after=after,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny Night Runner task packet in dry-run mode.")
    parser.add_argument("--packet", required=True, help="Path to a JSON/YAML tiny task packet.")
    args = parser.parse_args(argv)
    packet = load_packet(Path(args.packet))
    result = evaluate_packet(packet)
    print(result.report, end="")
    pass_decisions = {DECISION_PASS, DECISION_EXECUTION_PASS, DECISION_PATCH_PASS}
    return 0 if result.decision in pass_decisions else 1


if __name__ == "__main__":
    raise SystemExit(main())
