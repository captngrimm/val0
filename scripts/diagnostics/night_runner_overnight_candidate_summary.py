#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
PROTECTED_LIVE_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)
CAPABILITY_FILES = (
    ("bedtime workflow packet", "docs/ops/night_runner_bedtime_packet_v2.yaml"),
    ("manual overnight trial", "scripts/ops/night_runner_bedtime_trial.py"),
    ("manual overnight smoke", "scripts/quality/night_runner_manual_overnight_trial_smoke.py"),
    ("manual overnight report", "tmp/night_runner/manual_overnight_trial_report.md"),
    ("bedtime report path", "tmp/night_runner/bedtime_v2_report.md"),
)
FORBIDDEN_STILL = (
    "bot.py/core runtime edits",
    "client data edits",
    "restarts",
    "live DB writes",
    "commits unless explicitly approved",
    "Codex execution unless explicitly allowed in a future lane",
)
NEXT_LANE = "NIGHT-RUNNER-22 - Tiny Useful Candidate With Reported Patch Review"


def _git(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return f"(git unavailable: {proc.stderr.strip() or proc.stdout.strip()})"
    return proc.stdout.strip()


def _status_entries() -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    status = _git(["status", "--short", "--branch"])
    for line in status.splitlines():
        if line.startswith("##") or len(line) < 4:
            continue
        code = line[:2]
        path = line[3:].strip() if line[2] == " " else line[2:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        entries.append((code, path))
    return entries


def _describe_git_state(code: str | None) -> str:
    if code is None:
        return "clean-or-unreported"
    staged = code[0] != " "
    dirty = code[1] != " "
    if staged and dirty:
        return f"staged-and-dirty ({code})"
    if staged:
        return f"staged ({code})"
    if dirty:
        return f"dirty-unstaged ({code})"
    return f"reported-clean ({code})"


def _presence(path: str) -> str:
    return "present" if (ROOT / path).exists() else "missing"


def render_summary() -> str:
    branch = _git(["branch", "--show-current"]) or "(unknown)"
    head = _git(["rev-parse", "--short", "HEAD"]) or "(unknown)"
    status = _git(["status", "--short", "--branch"]) or "(no output)"
    status_entries = {path: code for code, path in _status_entries()}

    lines = [
        "Night Runner Overnight Candidate Summary",
        "========================================",
        "",
        f"Repo: {ROOT}",
        f"Branch: {branch}",
        f"Head: {head}",
        "",
        "Git Status Summary",
        "------------------",
    ]
    lines.extend(f"- {line}" for line in status.splitlines())

    lines.extend(
        [
            "",
            "Protected Live Data",
            "-------------------",
            "- status source: git status only",
            "- live client file contents read: no",
        ]
    )
    for path in PROTECTED_LIVE_FILES:
        lines.append(f"- {path}: {_describe_git_state(status_entries.get(path))}")

    lines.extend(["", "Sleep-Mode Capability Summary", "-----------------------------"])
    for label, path in CAPABILITY_FILES:
        lines.append(f"- {label}: {_presence(path)} ({path})")

    lines.extend(["", "Still Forbidden", "---------------"])
    lines.extend(f"- {item}" for item in FORBIDDEN_STILL)

    lines.extend(
        [
            "",
            "Next Useful Milestone",
            "---------------------",
            f"- {NEXT_LANE}",
            "",
            "Recommendation",
            "--------------",
            "- Safe to continue with non-runtime overnight candidates only.",
            "",
            "Safety Notes",
            "------------",
            "- secret contents read: no",
            "- auth.json/config.toml contents printed: no",
            "- protected live client contents printed: no",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    print(render_summary(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
