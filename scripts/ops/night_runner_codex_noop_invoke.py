#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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
    "task_mode",
    "task_prompt",
    "allowed_files",
    "forbidden_files",
    "tests_to_run",
    "report_path",
    "allow_codex_execute",
    "allow_file_edits",
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
COMMON_CODEX_PATHS = (
    "/root/.vscode-server/extensions/openai.chatgpt-26.601.21317-linux-x64/bin/linux-x86_64/codex",
    "/usr/local/bin/codex",
    "/usr/bin/codex",
    str(Path.home() / ".local" / "bin" / "codex"),
)
SECRET_PATTERNS = ("sk-", "refresh_token", "access_token", "authorization:", "bearer ")


@dataclass(frozen=True)
class GitSnapshot:
    branch: str
    head: str
    status_short_branch: str


@dataclass(frozen=True)
class ProtectedSnapshot:
    hashes: dict[str, str]


@dataclass(frozen=True)
class NoopInvokeResult:
    decision: str
    reasons: tuple[str, ...]
    report: str
    report_written: bool
    codex_path: str
    command: tuple[str, ...]
    codex_exit_code: int | None
    codex_output: str
    codex_executed: bool


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


def _has_staged(status_short_branch: str) -> bool:
    return any((code[0] if code else " ") not in {" ", "?"} for code, _path in _status_entries(status_short_branch))


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
    normalized = candidate.as_posix()
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


def _file_hash(path: Path) -> str:
    if not path.exists():
        return "(missing)"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def protected_snapshot() -> ProtectedSnapshot:
    return ProtectedSnapshot(hashes={path: _file_hash(ROOT / path) for path in PROTECTED_LIVE_FILES})


def _redact(text: str, *, limit: int = 2400) -> str:
    safe = str(text or "")
    for pattern in SECRET_PATTERNS:
        safe = safe.replace(pattern, "[REDACTED]")
    if len(safe) > limit:
        safe = safe[:limit].rstrip() + "\n... [truncated]"
    return safe.strip()


def build_noop_prompt(packet: dict[str, Any]) -> str:
    operator_prompt = str(packet.get("task_prompt") or "").strip()
    return "\n".join(
        [
            "Night Runner no-op readiness report.",
            "",
            "You are running in a guarded no-op invocation.",
            "Do not edit files.",
            "Do not run commands that modify state.",
            "Do not commit, push, reset, restart services, touch client data, or access secrets.",
            "Do not inspect or print auth/token/config secret contents.",
            "Output only a short plain-text readiness note with: repo path, branch if known, and whether you understand this is no-op.",
            "",
            f"Operator prompt: {operator_prompt}",
        ]
    )


def build_codex_command(codex_path: str, packet: dict[str, Any]) -> tuple[str, ...]:
    return (
        codex_path,
        "exec",
        "-C",
        str(ROOT),
        "-s",
        "read-only",
        "--ephemeral",
        "--",
        build_noop_prompt(packet),
    )


def _validate_packet(
    packet: dict[str, Any],
    git: GitSnapshot,
    codex_path: str,
    *,
    require_execute: bool,
) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in packet:
            reasons.append(f"missing required field: {field}")
    if str(packet.get("branch_name") or "").strip() != git.branch:
        reasons.append(f"branch mismatch: packet={packet.get('branch_name')!r} current={git.branch!r}")
    if str(packet.get("task_mode") or "").strip() != "noop_report":
        reasons.append("task_mode must be noop_report")
    if require_execute and packet.get("allow_codex_execute") is not True:
        reasons.append("allow_codex_execute must be true for actual no-op invocation")
    if packet.get("allow_file_edits") is not False:
        reasons.append("allow_file_edits must be false")
    if packet.get("allow_commit") is not False:
        reasons.append("allow_commit must be false")
    if packet.get("allow_restart") is not False:
        reasons.append("allow_restart must be false")
    if _has_staged(git.status_short_branch):
        reasons.append("staged files are not allowed")

    allowed_files = _as_list(packet.get("allowed_files"))
    forbidden_files = list(dict.fromkeys([*DEFAULT_FORBIDDEN_FILES, *_as_list(packet.get("forbidden_files"))]))
    for allowed in allowed_files:
        if allowed not in {"", "tmp/night_runner/", "tmp/night_runner"}:
            reasons.append(f"allowed_files must be empty or tmp/night_runner only: {allowed}")
        if _matches_any(allowed, forbidden_files):
            reasons.append(f"allowed_files includes forbidden path: {allowed}")
    for protected in PROTECTED_LIVE_FILES:
        if not _matches_any(protected, forbidden_files):
            reasons.append(f"protected file must be listed in forbidden_files: {protected}")
    for code, path in _status_entries(git.status_short_branch):
        if path in PROTECTED_LIVE_FILES and (code[0] if code else " ") not in {" ", "?"}:
            reasons.append(f"protected file is staged: {path}")
    safe_report, report_reason = _safe_report_path(str(packet.get("report_path") or ""))
    if not safe_report:
        reasons.append(report_reason)
    if not codex_path:
        reasons.append("codex binary not found")

    if not reasons:
        return "PASS_NOOP_CODEX_INVOKE_READY" if require_execute else "PASS_NOOP_CODEX_DRY_RUN_READY", ()
    if any("codex binary" in reason for reason in reasons):
        return "REFUSE_CODEX_MISSING", tuple(dict.fromkeys(reasons))
    if any("protected file" in reason or "staged" in reason for reason in reasons):
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


def _status_delta_allowed(before: GitSnapshot, after: GitSnapshot) -> tuple[bool, str]:
    if before.head != after.head:
        return False, f"git head changed: before={before.head} after={after.head}"
    if before.status_short_branch != after.status_short_branch:
        return False, "git status changed after Codex invocation"
    if _has_staged(after.status_short_branch):
        return False, "staged files found after Codex invocation"
    return True, ""


def render_report(
    packet: dict[str, Any],
    before_git: GitSnapshot,
    after_git: GitSnapshot,
    *,
    decision: str,
    reasons: tuple[str, ...],
    codex_path: str,
    command: tuple[str, ...],
    codex_exit_code: int | None,
    codex_output: str,
    codex_executed: bool,
    protected_unchanged: bool,
    status_unchanged: bool,
) -> str:
    lines = [
        "Night Runner Codex No-op Invocation Report",
        "==========================================",
        "",
        f"Lane: {packet.get('lane_id', '(missing)')}",
        f"Branch: {before_git.branch}",
        f"Head before: {before_git.head}",
        f"Head after: {after_git.head}",
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
            f"- binary path: {codex_path or '(not found)'}",
            f"- executed: {'yes' if codex_executed else 'no'}",
            f"- exit code: {codex_exit_code if codex_exit_code is not None else '(not run)'}",
            "",
            "Command:",
            " ".join(shlex.quote(part) for part in command) if command else "(not built)",
            "",
            "Post-run checks:",
            f"- protected live files unchanged: {protected_unchanged}",
            f"- git status/head unchanged: {status_unchanged}",
            "- staged files after run: no" if not _has_staged(after_git.status_short_branch) else "- staged files after run: yes",
            "",
            "Output excerpt:",
            _redact(codex_output) or "(no output)",
            "",
            f"Report path: {packet.get('report_path', '(missing)')}",
            "",
            "Safety:",
            "- No file edits were allowed.",
            "- No commits, restarts, live writes, or production DB migrations were allowed.",
            "- Secret files were not read or printed by this wrapper.",
            "- Protected live client files were not touched.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def evaluate_packet(
    packet: dict[str, Any],
    *,
    codex_path_override: str = "",
    invoke: bool = True,
    git_snapshot: GitSnapshot | None = None,
) -> NoopInvokeResult:
    before_git = git_snapshot or current_git_snapshot()
    before_protected = protected_snapshot()
    codex_path = _discover_codex_path(packet, override=codex_path_override)
    command = build_codex_command(codex_path, packet) if codex_path else ()
    decision, reasons = _validate_packet(packet, before_git, codex_path, require_execute=invoke)
    codex_exit_code: int | None = None
    output = ""
    executed = False

    if invoke and decision == "PASS_NOOP_CODEX_INVOKE_READY":
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=180,
        )
        codex_exit_code = proc.returncode
        output = proc.stdout or ""
        executed = True

    after_git = current_git_snapshot() if git_snapshot is None else before_git
    after_protected = protected_snapshot()
    protected_unchanged = before_protected == after_protected
    status_ok, status_reason = _status_delta_allowed(before_git, after_git)
    if executed and not protected_unchanged:
        reasons = (*reasons, "protected live file hash changed after Codex invocation")
        decision = "REFUSE_PROTECTED_FILE_RISK"
    if executed and not status_ok:
        reasons = (*reasons, status_reason)
        decision = "REFUSE_POST_RUN_MUTATION"
    if executed and codex_exit_code not in {0}:
        reasons = (*reasons, f"codex exited nonzero: {codex_exit_code}")
        decision = "CODEX_NOOP_INVOKE_FAILED"

    report = render_report(
        packet,
        before_git,
        after_git,
        decision=decision,
        reasons=tuple(dict.fromkeys(reasons)),
        codex_path=codex_path,
        command=command,
        codex_exit_code=codex_exit_code,
        codex_output=output,
        codex_executed=executed,
        protected_unchanged=protected_unchanged,
        status_unchanged=status_ok,
    )
    written = _write_report_if_safe(packet, report)
    return NoopInvokeResult(
        decision=decision,
        reasons=tuple(dict.fromkeys(reasons)),
        report=report,
        report_written=written,
        codex_path=codex_path,
        command=command,
        codex_exit_code=codex_exit_code,
        codex_output=output,
        codex_executed=executed,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one guarded Codex no-op invocation from a packet.")
    parser.add_argument("--packet", required=True, type=Path, help="Path to no-op Codex invocation packet.")
    parser.add_argument("--codex-path", help="Optional explicit Codex binary path override.")
    parser.add_argument(
        "--dry-run-only",
        action="store_true",
        help="Validate and build the command, but do not invoke Codex.",
    )
    args = parser.parse_args(argv)

    try:
        packet = load_lane_packet(args.packet)
    except Exception as exc:
        print("Night Runner Codex No-op Invocation Report")
        print("==========================================")
        print("")
        print("Decision: REFUSE_UNSAFE_PACKET")
        print(f"Refusal reasons:\n- could not load packet: {exc}")
        return 2

    result = evaluate_packet(packet, codex_path_override=str(args.codex_path or ""), invoke=not args.dry_run_only)
    print(result.report, end="")
    print(f"Report written: {'yes' if result.report_written else 'no'}")
    if result.decision in {"PASS_NOOP_CODEX_INVOKE_READY", "PASS_NOOP_CODEX_DRY_RUN_READY"}:
        return 0
    if result.decision == "CODEX_NOOP_INVOKE_FAILED":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
