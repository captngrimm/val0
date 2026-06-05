#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
PROTECTED_LIVE_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)
FORBIDDEN_STILL = (
    "runtime bot/core edits",
    "client data edits",
    "production restarts",
    "live DB writes",
    "commits unless explicitly approved",
)
NEXT_LANE = "NIGHT-RUNNER-17 - Bedtime Workflow Packet v2"


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


def _status_entries() -> dict[str, str]:
    result: dict[str, str] = {}
    status = _git(["status", "--short", "--branch"])
    for line in status.splitlines():
        if line.startswith("##") or len(line) < 4:
            continue
        code = line[:2]
        path = line[3:].strip() if line[2] == " " else line[2:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        result[path] = code
    return result


def _describe_git_state(code: str | None) -> str:
    if code is None:
        return "clean-or-unreported"
    if code == "??":
        return "untracked (??)"
    staged = code[0] != " "
    dirty = code[1] != " "
    if staged and dirty:
        return f"staged-and-dirty ({code})"
    if staged:
        return f"staged ({code})"
    if dirty:
        return f"dirty-unstaged ({code})"
    return f"reported-clean ({code})"


def _recent_night_runner_commits() -> list[str]:
    out = _git(["log", "--oneline", "-12", "--grep", "Night Runner"])
    return [line for line in out.splitlines() if line.strip()][:8]


def render_review() -> str:
    branch = _git(["branch", "--show-current"]) or "(unknown)"
    head = _git(["rev-parse", "--short", "HEAD"]) or "(unknown)"
    status = _git(["status", "--short", "--branch"]) or "(no output)"
    status_entries = _status_entries()
    recent = _recent_night_runner_commits()

    lines = [
        "Night Runner Patch Review",
        "=========================",
        "",
        f"Repo: {ROOT}",
        f"Branch: {branch}",
        f"Head: {head}",
        "",
        "Recent Night Runner commits:",
    ]
    lines.extend(f"- {line}" for line in recent) if recent else lines.append("- none found")

    lines.extend(["", "Changed-file status:"])
    changed = [
        f"- {path}: {_describe_git_state(code)}"
        for path, code in sorted(status_entries.items())
        if path not in PROTECTED_LIVE_FILES
    ]
    lines.extend(changed if changed else ["- no non-protected changes reported"])

    lines.extend(
        [
            "",
            "Protected live data status:",
            "- status source: git status only",
            "- live client file contents read: no",
        ]
    )
    for path in PROTECTED_LIVE_FILES:
        lines.append(f"- {path}: {_describe_git_state(status_entries.get(path))}")

    lines.extend(
        [
            "",
            "NIGHT-RUNNER-15 result:",
            "- Sleep Mode Ladder added to the readiness summary.",
            "- Patch stayed non-runtime.",
            "- reported patch guard passed.",
            "- no runtime/client/live data touched.",
            "",
            "Still forbidden:",
        ]
    )
    lines.extend(f"- {item}" for item in FORBIDDEN_STILL)
    lines.extend(
        [
            "",
            "Safety:",
            "- secret contents read: no",
            "- auth.json/config.toml contents printed: no",
            "- client data contents printed: no",
            "",
            "Recommended next lane:",
            f"- {NEXT_LANE}",
            "",
            "Git status:",
        ]
    )
    lines.extend(f"  {line}" for line in status.splitlines())
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    print(render_review(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
