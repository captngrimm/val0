#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]

COMPILE_TARGETS = (
    "bot.py",
    "core/pending_actions.py",
    "core/document_registry.py",
    "core/document_extraction_readiness.py",
    "core/case_timeline.py",
    "core/daily_operator.py",
    "core/response_envelope.py",
    "core/client_profiles.py",
)

SMOKE_CHECKS = (
    ("pending actions smoke", ("./scripts/val0py", "scripts/quality/pending_actions_smoke.py")),
    ("document registry smoke", ("./scripts/val0py", "scripts/quality/document_registry_smoke.py")),
    (
        "document extraction readiness smoke",
        ("./scripts/val0py", "scripts/quality/document_extraction_readiness_smoke.py"),
    ),
    ("case timeline smoke", ("./scripts/val0py", "scripts/quality/case_timeline_smoke.py")),
    ("daily operator smoke", ("./scripts/val0py", "scripts/quality/daily_operator_smoke.py")),
    ("response envelope smoke", ("./scripts/val0py", "scripts/quality/response_envelope_smoke.py")),
    ("client profiles smoke", ("./scripts/val0py", "scripts/quality/client_profiles_smoke.py")),
)

MANUAL_CHECKS = (
    "Karen Telegram live smoke: document inventory, timeline, year query, Daily Operator, agenda.",
    "Safe upload test if the demo includes upload.",
    "Unknown real chat smoke when available.",
    "Confirm bot restarted after bot.py runtime changes.",
)

RED_FLAGS = (
    "Dirty worktree before demo.",
    "Any automated check fails.",
    "Client isolation audit fails.",
    "Telegram route priority differs from the demo smoke checklist.",
    "Unknown client can enter a protected workflow.",
    "Photo/image is presented as read when OCR is not ready.",
    "Calendar create/delete happens without explicit confirmation.",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def _run(command: tuple[str, ...]) -> CheckResult:
    proc = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=120,
    )
    return CheckResult(
        name=" ".join(command),
        command=command,
        returncode=proc.returncode,
        stdout=(proc.stdout or "").strip(),
        stderr=(proc.stderr or "").strip(),
    )


def _short_output(result: CheckResult, limit: int = 600) -> str:
    text = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _print_check(label: str, result: CheckResult, *, show_output_on_pass: bool = False) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[{status}] {label}")
    output = _short_output(result)
    if output and (show_output_on_pass or not result.passed):
        for line in output.splitlines():
            print(f"  {line}")


def main() -> int:
    timestamp = datetime.now(timezone.utc).isoformat()

    git_status = _run(("git", "status", "--short"))
    branch = _run(("git", "branch", "--show-current"))
    latest_commit = _run(("git", "log", "--oneline", "-1"))

    compile_check = _run(("./scripts/val0py", "-m", "py_compile", *COMPILE_TARGETS))
    audit_check = _run(("python3", "scripts/quality/client_isolation_audit.py"))
    smoke_results = [
        (label, _run(command))
        for label, command in SMOKE_CHECKS
    ]

    worktree_clean = git_status.passed and not git_status.stdout.strip()
    automated_results = [compile_check, audit_check, *(result for _, result in smoke_results)]
    automated_pass = worktree_clean and all(result.passed for result in automated_results)

    print("FOUNDER-BETA READINESS REPORT")
    print(f"timestamp: {timestamp}")
    print(f"repo: {REPO_ROOT}")
    print(f"branch: {branch.stdout.strip() if branch.passed else 'unknown'}")
    print(f"latest commit: {latest_commit.stdout.strip() if latest_commit.passed else 'unknown'}")
    print(f"working tree: {'clean' if worktree_clean else 'dirty'}")
    if git_status.stdout.strip():
        for line in git_status.stdout.splitlines():
            print(f"  {line}")
    print()

    print(f"OVERALL AUTOMATED READINESS: {'PASS' if automated_pass else 'FAIL'}")
    print()

    print("AUTOMATED CHECKS")
    _print_check("git status --short", git_status, show_output_on_pass=False)
    _print_check("py_compile key modules", compile_check)
    _print_check("client isolation audit", audit_check, show_output_on_pass=True)
    for label, result in smoke_results:
        _print_check(label, result, show_output_on_pass=True)
    print()

    print("MANUAL CHECKS STILL REQUIRED")
    for item in MANUAL_CHECKS:
        print(f"- TODO: {item}")
    print()

    print("RED FLAGS")
    for item in RED_FLAGS:
        print(f"- {item}")
    print()

    if automated_pass:
        print("Next action: run the manual Telegram demo smoke before showing Val0 live.")
        return 0

    print("Next action: stop demo prep, fix failing checks, then rerun this report.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
