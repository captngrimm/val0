#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIVE_FORBIDDEN = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
    ".env",
    "/etc/val0",
)
READONLY_PROTECTED_DIRTY_ALLOWED = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)
PROTECTED_DIRTY_WARNING = "Protected live files are dirty and were not touched."
REQUIRED_FIELDS = (
    "lane_id",
    "branch_name",
    "task_prompt",
    "allowed_files",
    "forbidden_files",
    "tests_to_run",
    "commit_allowed",
    "restart_allowed",
    "destructive_commands_allowed",
    "report_path",
    "stop_if_uncertain",
)
BROAD_ALLOWED_FILES = {".", "./", "*", "**", "**/*", "/*", "/"}
PROMPT_FORBIDDEN_PATTERNS = (
    r"\bcommit\b",
    r"\bpush\b",
    r"\breset\b",
    r"\brestarts?\b",
    r"\bsystemctl\b",
    r"\bproduction\b",
    r"\blive writes?\b",
    r"\boauth\b",
    r"\btoken\b",
    r"\bsecret\b",
    r"\bdestructive\b",
    r"\bdelete\b",
    r"\brm\s+-",
    r"\bbroad refactor\b",
)
UNSAFE_COMMAND_PATTERNS = (
    r"[;&|`$<>]",
    r"\bgit\s+commit\b",
    r"\bgit\s+push\b",
    r"\bgit\s+reset\b",
    r"\bgit\s+clean\b",
    r"\bsystemctl\b",
    r"\brm\b",
    r"\bcurl\b",
    r"\bwget\b",
    r"\boauth\b",
    r"\btoken\b",
    r"\bsecret\b",
    r"\.env\b",
    r"/etc/val0",
    r"\bgoogle\s+calendar\s+(write|delete)\b",
    r"\bgcal\s+(write|delete|create|delete)\b",
)


@dataclass(frozen=True)
class GitSnapshot:
    branch: str
    head: str
    status_short_branch: str


@dataclass(frozen=True)
class DryRunResult:
    decision: str
    reasons: tuple[str, ...]
    report: str
    report_written: bool
    test_results: tuple["TestCommandResult", ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class TestCommandResult:
    command: str
    allowed: bool
    exit_code: int | None
    status: str
    output_excerpt: str
    reason: str = ""


def _run_git(args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except Exception as exc:
        return f"(git command failed: {exc})"
    return (proc.stdout or proc.stderr or "").strip()


def current_git_snapshot() -> GitSnapshot:
    return GitSnapshot(
        branch=_run_git(["branch", "--show-current"]) or "(unknown)",
        head=_run_git(["rev-parse", "--short", "HEAD"]) or "(unknown)",
        status_short_branch=_run_git(["status", "--short", "--branch"]) or "(no output)",
    )


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
        line = raw_line.rstrip()
        stripped = line.strip()
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
        if not value:
            data[key] = []
            current_list_key = key
        else:
            data[key] = _parse_scalar(value)
            current_list_key = None
    return data


def load_lane_packet(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if path.suffix.lower() == ".json" or stripped.startswith("{"):
        loaded = json.loads(text)
    else:
        loaded = _parse_simple_yaml(text)
    if not isinstance(loaded, dict):
        raise ValueError("lane packet must be a JSON/YAML object")
    return loaded


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _status_entries(status_short_branch: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in status_short_branch.splitlines():
        if not line.strip() or line.startswith("##"):
            continue
        code = line[:2]
        path = line[3:].strip() if len(line) > 3 and line[2] == " " else line.strip()[2:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        entries.append((code, path))
    return entries


def _has_staged_changes(status_short_branch: str) -> bool:
    for code, _path in _status_entries(status_short_branch):
        staged = code[0] if code else " "
        if staged not in {" ", "?"}:
            return True
    return False


def _is_staged_code(code: str) -> bool:
    staged = code[0] if code else " "
    return staged not in {" ", "?"}


def _dirty_paths(status_short_branch: str) -> set[str]:
    return {path for _code, path in _status_entries(status_short_branch)}


def _path_matches(path: str, pattern: str) -> bool:
    path = path.strip()
    pattern = pattern.strip()
    if not path or not pattern:
        return False
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


def _safe_report_path(report_path: str, forbidden_files: list[str]) -> tuple[bool, str]:
    if not report_path:
        return False, "report_path is empty"
    candidate = Path(report_path)
    if candidate.is_absolute():
        try:
            candidate.relative_to(Path("/tmp"))
        except ValueError:
            return False, "absolute report_path must be under /tmp"
    normalized = report_path.strip()
    for forbidden in forbidden_files:
        if _path_matches(normalized, forbidden):
            return False, f"report_path targets forbidden file: {forbidden}"
    if normalized in BROAD_ALLOWED_FILES:
        return False, "report_path is too broad"
    return True, ""


def _matches_any(path: str, patterns: list[str] | tuple[str, ...]) -> bool:
    return any(_path_matches(path, pattern) for pattern in patterns)


def _is_report_area_path(path: str, report_path: str) -> bool:
    if not path or not report_path:
        return False
    if _path_matches(path, "tmp/night_runner"):
        return True
    report = str(report_path).strip()
    if not report or Path(report).is_absolute():
        return False
    return path == report or _path_matches(path, str(Path(report).parent))


def _protected_dirty_warning_entries(
    packet: dict[str, Any],
    git: GitSnapshot,
    *,
    allow_protected_dirty_readonly: bool,
) -> tuple[str, ...]:
    if not allow_protected_dirty_readonly:
        return ()
    packet_forbidden = _as_list(packet.get("forbidden_files"))
    entries = []
    for code, path in _status_entries(git.status_short_branch):
        if not _matches_any(path, READONLY_PROTECTED_DIRTY_ALLOWED):
            continue
        if _is_staged_code(code):
            continue
        if not _matches_any(path, packet_forbidden):
            continue
        entries.append(path)
    if not entries:
        return ()
    return (PROTECTED_DIRTY_WARNING + " " + ", ".join(sorted(set(entries))),)


def _validate_packet(
    packet: dict[str, Any],
    git: GitSnapshot,
    *,
    allow_protected_dirty_readonly: bool = False,
) -> tuple[str, ...]:
    reasons: list[str] = []
    missing = [field for field in REQUIRED_FIELDS if field not in packet]
    if missing:
        reasons.append("missing required field(s): " + ", ".join(missing))

    allowed_files = _as_list(packet.get("allowed_files"))
    packet_forbidden = _as_list(packet.get("forbidden_files"))
    forbidden_files = list(dict.fromkeys([*DEFAULT_LIVE_FORBIDDEN, *packet_forbidden]))

    if str(packet.get("branch_name", "")).strip() and str(packet.get("branch_name")).strip() != git.branch:
        reasons.append(f"branch mismatch: packet={packet.get('branch_name')} current={git.branch}")

    if packet.get("commit_allowed") is True:
        reasons.append("commit_allowed must be false in v0")
    if packet.get("restart_allowed") is True:
        reasons.append("restart_allowed must be false in v0")
    if packet.get("destructive_commands_allowed") is True:
        reasons.append("destructive_commands_allowed must be false in v0")

    if not allowed_files:
        reasons.append("allowed_files must not be empty")
    for allowed in allowed_files:
        if allowed in BROAD_ALLOWED_FILES:
            reasons.append(f"allowed_files entry is too broad: {allowed}")
        for forbidden in forbidden_files:
            if _path_matches(allowed, forbidden) or _path_matches(forbidden, allowed):
                reasons.append(f"allowed_files includes forbidden file/path: {allowed}")
                break

    dirty = _dirty_paths(git.status_short_branch)
    for forbidden in forbidden_files:
        for dirty_path in dirty:
            if _path_matches(dirty_path, forbidden):
                dirty_entry = next(
                    ((code, path) for code, path in _status_entries(git.status_short_branch) if path == dirty_path),
                    ("", dirty_path),
                )
                is_readonly_allowed = (
                    allow_protected_dirty_readonly
                    and _matches_any(dirty_path, READONLY_PROTECTED_DIRTY_ALLOWED)
                    and _matches_any(dirty_path, packet_forbidden)
                    and not _is_staged_code(dirty_entry[0])
                )
                if not is_readonly_allowed:
                    reasons.append(f"forbidden file is dirty/staged: {dirty_path}")

    if allow_protected_dirty_readonly:
        report_path = str(packet.get("report_path", ""))
        for code, dirty_path in _status_entries(git.status_short_branch):
            if _matches_any(dirty_path, READONLY_PROTECTED_DIRTY_ALLOWED):
                if not _matches_any(dirty_path, packet_forbidden):
                    reasons.append(f"dirty protected file is not listed in forbidden_files: {dirty_path}")
                if _matches_any(dirty_path, allowed_files):
                    reasons.append(f"dirty protected file cannot be in allowed_files: {dirty_path}")
                if _is_staged_code(code):
                    reasons.append(f"staged protected file is not allowed: {dirty_path}")
                continue
            if not _is_report_area_path(dirty_path, report_path):
                reasons.append(f"non-protected dirty file is not allowed in readonly mode: {dirty_path}")

    if _has_staged_changes(git.status_short_branch):
        reasons.append("staged changes exist")

    prompt = str(packet.get("task_prompt", ""))
    lowered_prompt = prompt.casefold()
    for pattern in PROMPT_FORBIDDEN_PATTERNS:
        if re.search(pattern, lowered_prompt):
            reasons.append(f"task_prompt contains forbidden request: {pattern}")
            break

    safe_path, path_reason = _safe_report_path(str(packet.get("report_path", "")), forbidden_files)
    if not safe_path:
        reasons.append(path_reason)

    return tuple(dict.fromkeys(reasons))


def _command_excerpt(text: str, *, limit: int = 1800) -> str:
    compact = str(text or "").strip()
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "\n... [truncated]"


def _is_allowed_py_compile(parts: list[str]) -> tuple[bool, str]:
    if len(parts) < 4:
        return False, "py_compile command must include at least one file"
    if parts[:3] != ["./scripts/val0py", "-m", "py_compile"]:
        return False, "not a val0py py_compile command"
    for target in parts[3:]:
        if target.startswith("-"):
            return False, f"py_compile target is not a file: {target}"
        if target in BROAD_ALLOWED_FILES or target.startswith("/"):
            return False, f"py_compile target is unsafe: {target}"
    return True, ""


def validate_test_command(command: str) -> tuple[bool, str, list[str]]:
    raw = str(command or "").strip()
    if not raw:
        return False, "empty command", []
    lowered = raw.casefold()
    for pattern in UNSAFE_COMMAND_PATTERNS:
        if re.search(pattern, lowered):
            return False, f"unsafe command pattern: {pattern}", []
    try:
        parts = shlex.split(raw)
    except ValueError as exc:
        return False, f"could not parse command: {exc}", []
    if not parts:
        return False, "empty parsed command", []

    if parts == ["git", "diff", "--check"]:
        return True, "", parts
    if parts == ["python3", "scripts/diagnostics/val0_milestone_radar.py"]:
        return True, "", parts
    if parts == ["python3", "scripts/diagnostics/val0_alpha_brief.py"]:
        return True, "", parts
    if (
        len(parts) == 2
        and parts[0] == "python3"
        and parts[1].startswith("scripts/quality/")
        and parts[1].endswith(".py")
        and ".." not in parts[1]
    ):
        return True, "", parts
    ok, reason = _is_allowed_py_compile(parts)
    if ok:
        return True, "", parts
    return False, reason or "command is outside allowed categories", parts


def run_test_commands(commands: list[str]) -> tuple[TestCommandResult, ...]:
    results: list[TestCommandResult] = []
    for command in commands:
        allowed, reason, parts = validate_test_command(command)
        if not allowed:
            results.append(
                TestCommandResult(
                    command=command,
                    allowed=False,
                    exit_code=None,
                    status="REJECTED",
                    output_excerpt="",
                    reason=reason,
                )
            )
            continue
        proc = subprocess.run(
            parts,
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        output = _command_excerpt(proc.stdout or "")
        results.append(
            TestCommandResult(
                command=command,
                allowed=True,
                exit_code=proc.returncode,
                status="PASS" if proc.returncode == 0 else "FAIL",
                output_excerpt=output,
            )
        )
    return tuple(results)


def build_report(
    packet: dict[str, Any],
    git: GitSnapshot,
    reasons: tuple[str, ...],
    test_results: tuple[TestCommandResult, ...] = (),
    warnings: tuple[str, ...] = (),
) -> str:
    decision = "REFUSED" if reasons else "PASS_DRY_RUN"
    allowed_files = _as_list(packet.get("allowed_files"))
    forbidden_files = list(
        dict.fromkeys([*DEFAULT_LIVE_FORBIDDEN, *_as_list(packet.get("forbidden_files"))])
    )
    tests = _as_list(packet.get("tests_to_run"))
    lines = [
        "Night Runner v0 Dry-Run Report",
        "==============================",
        "",
        f"Lane: {packet.get('lane_id', '(missing)')}",
        f"Branch: {git.branch}",
        f"Head: {git.head}",
        "",
        f"Safety decision: {decision}",
        "",
        "Refusal reasons:",
    ]
    if reasons:
        lines.extend(f"- {reason}" for reason in reasons)
    else:
        lines.append("- none")
    if warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {warning}" for warning in warnings)
    lines.extend(
        [
            "",
            "Git status summary:",
            git.status_short_branch or "(no output)",
            "",
            "Allowed files:",
        ]
    )
    lines.extend(f"- {item}" for item in (allowed_files or ["(none)"]))
    lines.append("")
    lines.append("Forbidden files:")
    lines.extend(f"- {item}" for item in forbidden_files)
    lines.extend(["", "Tests it would run:"])
    lines.extend(f"- {item}" for item in (tests or ["(none)"]))
    if test_results:
        passed = sum(1 for result in test_results if result.status == "PASS")
        failed = sum(1 for result in test_results if result.status == "FAIL")
        rejected = sum(1 for result in test_results if result.status == "REJECTED")
        lines.extend(
            [
                "",
                "Tests run:",
                f"- total: {len(test_results)}",
                f"- pass: {passed}",
                f"- fail: {failed}",
                f"- rejected: {rejected}",
                "",
                "Command results:",
            ]
        )
        for result in test_results:
            lines.append(f"- {result.status}: {result.command}")
            if result.exit_code is not None:
                lines.append(f"  exit_code: {result.exit_code}")
            if result.reason:
                lines.append(f"  reason: {result.reason}")
            if result.output_excerpt:
                lines.append("  output:")
                for output_line in result.output_excerpt.splitlines()[:40]:
                    lines.append(f"    {output_line}")
    lines.extend(
        [
            "",
            f"Report path: {packet.get('report_path', '(missing)')}",
            "",
            "Exact next morning action:",
        ]
    )
    if reasons:
        lines.append("Review refusal reasons, fix the lane packet or repo state, then rerun dry-run.")
    elif test_results and all(result.status == "PASS" for result in test_results):
        lines.append("Review passing morning report, then decide whether a human should start the lane.")
    elif test_results:
        lines.append("Review failed/rejected command results before any implementation work.")
    else:
        lines.append("Human may review this PASS_DRY_RUN report and decide whether a later lane should implement work.")
    return "\n".join(lines).rstrip() + "\n"


def _write_report_if_safe(packet: dict[str, Any], report: str) -> bool:
    report_path = str(packet.get("report_path", "")).strip()
    packet_forbidden = _as_list(packet.get("forbidden_files"))
    forbidden_files = list(dict.fromkeys([*DEFAULT_LIVE_FORBIDDEN, *packet_forbidden]))
    safe, _reason = _safe_report_path(report_path, forbidden_files)
    if not safe:
        return False
    destination = Path(report_path)
    if not destination.is_absolute():
        destination = REPO_ROOT / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report, encoding="utf-8")
    return True


def evaluate_packet(
    packet: dict[str, Any],
    git: GitSnapshot,
    *,
    run_tests: bool = False,
    allow_protected_dirty_readonly: bool = False,
) -> DryRunResult:
    reasons = _validate_packet(
        packet,
        git,
        allow_protected_dirty_readonly=allow_protected_dirty_readonly,
    )
    warnings = _protected_dirty_warning_entries(
        packet,
        git,
        allow_protected_dirty_readonly=allow_protected_dirty_readonly,
    )
    test_results: tuple[TestCommandResult, ...] = ()
    if run_tests and not reasons:
        test_results = run_test_commands(_as_list(packet.get("tests_to_run")))
    report = build_report(packet, git, reasons, test_results, warnings)
    written = _write_report_if_safe(packet, report)
    return DryRunResult(
        decision="REFUSED" if reasons else "PASS_DRY_RUN",
        reasons=reasons,
        report=report,
        report_written=written,
        test_results=test_results,
        warnings=warnings,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Night Runner lane packet without executing work."
    )
    parser.add_argument("packet", nargs="?", type=Path, help="Path to JSON or simple YAML lane packet.")
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="After PASS_DRY_RUN validation, run only tests_to_run commands that match the safe allow-list.",
    )
    parser.add_argument(
        "--allow-protected-dirty-readonly",
        action="store_true",
        help=(
            "Allow unstaged protected Karen live files to remain dirty for a read-only report, "
            "only when they are explicitly listed in forbidden_files."
        ),
    )
    args = parser.parse_args()
    if args.packet is None:
        parser.print_help()
        return 0

    try:
        packet = load_lane_packet(args.packet)
    except Exception as exc:
        print("Night Runner v0 Dry-Run Report")
        print("==============================")
        print("")
        print("Safety decision: REFUSED")
        print("")
        print(f"Refusal reasons:\n- could not load lane packet: {exc}")
        return 2

    result = evaluate_packet(
        packet,
        current_git_snapshot(),
        run_tests=args.run_tests,
        allow_protected_dirty_readonly=args.allow_protected_dirty_readonly,
    )
    print(result.report, end="")
    print(f"Report written: {'yes' if result.report_written else 'no'}")
    if result.decision != "PASS_DRY_RUN":
        return 2
    if result.test_results and any(result.status != "PASS" for result in result.test_results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
