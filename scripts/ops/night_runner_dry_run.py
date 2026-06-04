#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
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


def _validate_packet(packet: dict[str, Any], git: GitSnapshot) -> tuple[str, ...]:
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
                reasons.append(f"forbidden file is dirty/staged: {dirty_path}")

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


def build_report(packet: dict[str, Any], git: GitSnapshot, reasons: tuple[str, ...]) -> str:
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


def evaluate_packet(packet: dict[str, Any], git: GitSnapshot) -> DryRunResult:
    reasons = _validate_packet(packet, git)
    report = build_report(packet, git, reasons)
    written = _write_report_if_safe(packet, report)
    return DryRunResult(
        decision="REFUSED" if reasons else "PASS_DRY_RUN",
        reasons=reasons,
        report=report,
        report_written=written,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Night Runner lane packet without executing work."
    )
    parser.add_argument("packet", nargs="?", type=Path, help="Path to JSON or simple YAML lane packet.")
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

    result = evaluate_packet(packet, current_git_snapshot())
    print(result.report, end="")
    print(f"Report written: {'yes' if result.report_written else 'no'}")
    return 0 if result.decision == "PASS_DRY_RUN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
