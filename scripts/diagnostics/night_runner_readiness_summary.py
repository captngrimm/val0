#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]

CORE_NIGHT_RUNNER_SCRIPTS = (
    "scripts/ops/night_runner_dry_run.py",
    "scripts/ops/night_runner_codex_bridge_discovery.py",
    "scripts/ops/night_runner_codex_attempt_dry_run.py",
    "scripts/ops/night_runner_codex_noop_invoke.py",
    "scripts/ops/night_runner_codex_readonly_plan.py",
)

CODEX_BRIDGE_DISCOVERY_DOCS = (
    "docs/ops/NIGHT_RUNNER_CODEX_BRIDGE_DISCOVERY.md",
    "docs/ops/night_runner_codex_bridge_packet.yaml",
)

NOOP_INVOCATION_DOCS = (
    "docs/ops/NIGHT_RUNNER_CODEX_NOOP_INVOCATION.md",
    "docs/ops/night_runner_codex_noop_packet.yaml",
)

READONLY_PLANNING_DOCS = (
    "docs/ops/NIGHT_RUNNER_CODEX_READONLY_PLAN.md",
    "docs/ops/night_runner_codex_readonly_plan_packet.yaml",
)

DOCS_DIAGNOSTIC_FILES = (
    "docs/ops/NIGHT_RUNNER_DOCS_DIAGNOSTIC.md",
    "scripts/quality/night_runner_docs_diagnostic_smoke.py",
)

PROTECTED_LIVE_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)

NEXT_LANE = "NIGHT-RUNNER-12 - Branch-only Tiny Safe Task Runner Dry-Run"


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
    entries: dict[str, str] = {}
    status = _git(["status", "--short", "--branch"])
    for line in status.splitlines():
        if line.startswith("##") or len(line) < 4:
            continue
        code = line[:2]
        path = line[3:].strip() if line[2] == " " else line[2:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        entries[path] = code
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


def _presence_line(path: str) -> str:
    return f"- {path}: {'present' if (ROOT / path).exists() else 'missing'}"


def render_summary() -> str:
    branch = _git(["branch", "--show-current"]) or "(unknown)"
    head = _git(["rev-parse", "--short", "HEAD"]) or "(unknown)"
    status_entries = _status_entries()

    lines = [
        "Night Runner Readiness Summary",
        "==============================",
        "",
        f"Repo: {ROOT}",
        f"Branch: {branch}",
        f"Head: {head}",
        "",
        "Core Night Runner scripts:",
    ]
    lines.extend(_presence_line(path) for path in CORE_NIGHT_RUNNER_SCRIPTS)

    lines.extend(["", "Codex bridge discovery:"])
    lines.extend(_presence_line(path) for path in CODEX_BRIDGE_DISCOVERY_DOCS)

    lines.extend(["", "No-op invocation:"])
    lines.extend(_presence_line(path) for path in NOOP_INVOCATION_DOCS)

    lines.extend(["", "Read-only planning:"])
    lines.extend(_presence_line(path) for path in READONLY_PLANNING_DOCS)

    lines.extend(["", "Docs diagnostic smoke:"])
    lines.extend(_presence_line(path) for path in DOCS_DIAGNOSTIC_FILES)

    lines.extend(
        [
            "",
            "Protected live files:",
            "- status source: git status only",
            "- live client file contents read: no",
        ]
    )
    for path in PROTECTED_LIVE_FILES:
        lines.append(f"- {path}: {_describe_git_state(status_entries.get(path))}")

    lines.extend(
        [
            "",
            "Safety:",
            "- writes performed: no",
            "- secret contents read: no",
            "- auth.json/config.toml contents printed: no",
            "- runtime files inspected for content: no",
            "",
            "Recommended next lane:",
            f"- {NEXT_LANE}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    print(render_summary(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
