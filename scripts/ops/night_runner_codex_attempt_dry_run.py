#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ops.night_runner_dry_run import load_lane_packet  # noqa: E402


REQUIRED_FIELDS = (
    "lane_id",
    "branch_name",
    "task_prompt",
    "allowed_files",
    "forbidden_files",
    "tests_to_run",
    "report_path",
    "allow_codex_execute",
    "allow_commit",
    "allow_restart",
)
PROTECTED_LIVE_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)
DEFAULT_FORBIDDEN_FILES = (
    *PROTECTED_LIVE_FILES,
    "/etc/val0",
    ".env",
    "val0_memory.enc.db",
    "*.db",
    "*.sqlite",
)
BROAD_ALLOWED_FILES = {".", "./", "*", "**", "**/*", "/", "/*"}
UNSAFE_PROMPT_WORDS = (
    "git commit",
    "git push",
    "git reset",
    "systemctl",
    "/etc/val0",
    "oauth",
    "token",
    "secret",
    "production restart",
    "live db",
    "delete client",
)
COMMON_CODEX_PATHS = (
    "/root/.vscode-server/extensions/openai.chatgpt-26.601.21317-linux-x64/bin/linux-x86_64/codex",
    "/usr/local/bin/codex",
    "/usr/bin/codex",
    str(Path.home() / ".local" / "bin" / "codex"),
)


@dataclass(frozen=True)
class GitSnapshot:
    branch: str
    head: str
    status_short_branch: str


@dataclass(frozen=True)
class CodexAttemptResult:
    decision: str
    reasons: tuple[str, ...]
    report: str
    report_written: bool
    codex_path: str
    would_run_command: str


def _run_git(args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except Exception as exc:
        return f"(git unavailable: {exc})"
    return (proc.stdout or proc.stderr or "").strip()


def current_git_snapshot() -> GitSnapshot:
    return GitSnapshot(
        branch=_run_git(["branch", "--show-current"]) or "(unknown)",
        head=_run_git(["rev-parse", "--short", "HEAD"]) or "(unknown)",
        status_short_branch=_run_git(["status", "--short", "--branch"]) or "(no output)",
    )


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


def _is_staged(code: str) -> bool:
    staged = code[0] if code else " "
    return staged not in {" ", "?"}


def _path_matches(path: str, pattern: str) -> bool:
    path = path.strip()
    pattern = pattern.strip()
    if not path or not pattern:
        return False
    if pattern.startswith("*."):
        return path.endswith(pattern[1:])
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


def _matches_any(path: str, patterns: list[str] | tuple[str, ...]) -> bool:
    return any(_path_matches(path, pattern) for pattern in patterns)


def _safe_report_path(report_path: str) -> tuple[bool, str]:
    value = str(report_path or "").strip()
    if not value:
        return False, "report_path is empty"
    candidate = Path(value)
    if candidate.is_absolute():
        return False, "report_path must be relative under tmp/night_runner"
    try:
        normalized = candidate.as_posix()
    except Exception:
        return False, "report_path is invalid"
    if normalized == "tmp/night_runner" or normalized.startswith("tmp/night_runner/"):
        return True, ""
    return False, "report_path must be under tmp/night_runner"


def _discover_codex_path(packet: dict[str, Any], override: str = "") -> str:
    explicit = override or str(packet.get("codex_path") or "").strip()
    if explicit:
        path = Path(explicit)
        return str(path) if path.exists() and os.access(path, os.X_OK) else ""
    found = shutil.which("codex")
    if found:
        return found
    for candidate in COMMON_CODEX_PATHS:
        path = Path(candidate)
        if path.exists() and os.access(path, os.X_OK):
            return str(path)
    return ""


def _build_codex_command(codex_path: str, packet: dict[str, Any]) -> str:
    prompt = str(packet.get("task_prompt") or "").strip()
    args = [
        codex_path,
        "exec",
        "--cwd",
        str(ROOT),
        "--sandbox",
        "workspace-write",
        "--",
        prompt,
    ]
    return " ".join(shlex.quote(item) for item in args)


def _validate_packet(packet: dict[str, Any], git: GitSnapshot, codex_path: str) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in packet:
            reasons.append(f"missing required field: {field}")

    if str(packet.get("branch_name") or "").strip() != git.branch:
        reasons.append(f"branch mismatch: packet={packet.get('branch_name')!r} current={git.branch!r}")

    if packet.get("allow_codex_execute") is True:
        reasons.append("allow_codex_execute must be false for NIGHT-RUNNER-06")
    if packet.get("allow_commit") is True:
        reasons.append("allow_commit must be false")
    if packet.get("allow_restart") is True:
        reasons.append("allow_restart must be false")

    allowed_files = _as_list(packet.get("allowed_files"))
    forbidden_files = list(dict.fromkeys([*DEFAULT_FORBIDDEN_FILES, *_as_list(packet.get("forbidden_files"))]))
    for allowed in allowed_files:
        if allowed in BROAD_ALLOWED_FILES:
            reasons.append(f"allowed_files entry is too broad: {allowed}")
        if _matches_any(allowed, forbidden_files):
            reasons.append(f"allowed_files includes forbidden path: {allowed}")

    for protected in PROTECTED_LIVE_FILES:
        if not _matches_any(protected, forbidden_files):
            reasons.append(f"protected file must be listed in forbidden_files: {protected}")

    for code, path in _status_entries(git.status_short_branch):
        if path in PROTECTED_LIVE_FILES and _is_staged(code):
            reasons.append(f"protected file is staged: {path}")
        elif path in PROTECTED_LIVE_FILES and not _matches_any(path, forbidden_files):
            reasons.append(f"dirty protected file is not forbidden: {path}")

    safe_report, report_reason = _safe_report_path(str(packet.get("report_path") or ""))
    if not safe_report:
        reasons.append(report_reason)

    prompt = str(packet.get("task_prompt") or "").casefold()
    for word in UNSAFE_PROMPT_WORDS:
        if word in prompt:
            reasons.append(f"task_prompt contains unsafe request: {word}")

    if not codex_path:
        reasons.append("codex binary not found")

    if not reasons:
        return "PASS_DRY_RUN_CODEX_ATTEMPT_READY", ()
    if any("codex binary" in reason for reason in reasons):
        return "REFUSE_CODEX_MISSING", tuple(dict.fromkeys(reasons))
    if any("protected file" in reason for reason in reasons):
        return "REFUSE_PROTECTED_FILE_RISK", tuple(dict.fromkeys(reasons))
    if any("branch mismatch" in reason for reason in reasons):
        return "REFUSE_BRANCH_RISK", tuple(dict.fromkeys(reasons))
    return "REFUSE_UNSAFE_PACKET", tuple(dict.fromkeys(reasons))


def _write_report_if_safe(packet: dict[str, Any], report: str) -> bool:
    safe, _reason = _safe_report_path(str(packet.get("report_path") or ""))
    if not safe:
        return False
    destination = ROOT / str(packet["report_path"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report, encoding="utf-8")
    return True


def build_report(
    packet: dict[str, Any],
    git: GitSnapshot,
    *,
    decision: str,
    reasons: tuple[str, ...],
    codex_path: str,
    would_run_command: str,
) -> str:
    lines = [
        "Night Runner Codex Attempt Dry-Run",
        "===================================",
        "",
        f"Lane: {packet.get('lane_id', '(missing)')}",
        f"Branch: {git.branch}",
        f"Head: {git.head}",
        "",
        f"Decision: {decision}",
        "",
        "Refusal reasons:",
    ]
    lines.extend(f"- {reason}" for reason in reasons) if reasons else lines.append("- none")
    lines.extend(
        [
            "",
            "Codex:",
            f"- binary found: {'yes' if codex_path else 'no'}",
            f"- binary path: {codex_path or '(not found)'}",
            "- executed: no",
            "",
            "Would-run command:",
            would_run_command or "(not built)",
            "",
            "Permission gates:",
            f"- allow_codex_execute: {packet.get('allow_codex_execute', '(missing)')}",
            f"- allow_commit: {packet.get('allow_commit', '(missing)')}",
            f"- allow_restart: {packet.get('allow_restart', '(missing)')}",
            "",
            "Git status:",
            git.status_short_branch or "(no output)",
            "",
            "Protected live files:",
        ]
    )
    for protected in PROTECTED_LIVE_FILES:
        status = "reported only; not modified"
        lines.append(f"- {protected}: {status}")
    lines.extend(
        [
            "",
            f"Report path: {packet.get('report_path', '(missing)')}",
            "",
            "Safety:",
            "- Codex was not executed.",
            "- No commits, restarts, live writes, or production DB migrations were allowed.",
            "- Secret files were not read or printed.",
            "- Protected live client files were not touched.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def evaluate_packet(packet: dict[str, Any], git: GitSnapshot, *, codex_path_override: str = "") -> CodexAttemptResult:
    codex_path = _discover_codex_path(packet, override=codex_path_override)
    would_run = _build_codex_command(codex_path, packet) if codex_path else ""
    decision, reasons = _validate_packet(packet, git, codex_path)
    report = build_report(packet, git, decision=decision, reasons=reasons, codex_path=codex_path, would_run_command=would_run)
    written = _write_report_if_safe(packet, report)
    return CodexAttemptResult(
        decision=decision,
        reasons=reasons,
        report=report,
        report_written=written,
        codex_path=codex_path,
        would_run_command=would_run,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a branch-only Codex attempt packet without executing Codex.")
    parser.add_argument("--packet", required=True, type=Path, help="Path to Codex attempt packet JSON/YAML.")
    parser.add_argument("--codex-path", help="Optional explicit Codex binary path override.")
    args = parser.parse_args(argv)

    try:
        packet = load_lane_packet(args.packet)
    except Exception as exc:
        print("Night Runner Codex Attempt Dry-Run")
        print("===================================")
        print("")
        print("Decision: REFUSE_UNSAFE_PACKET")
        print(f"Refusal reasons:\n- could not load packet: {exc}")
        return 2

    result = evaluate_packet(packet, current_git_snapshot(), codex_path_override=str(args.codex_path or ""))
    print(result.report, end="")
    print(f"Report written: {'yes' if result.report_written else 'no'}")
    return 0 if result.decision == "PASS_DRY_RUN_CODEX_ATTEMPT_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
