#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_LOG = REPO_ROOT / "docs" / "ops" / "VAL0_ALPHA_BENCHMARK_LOG.md"
LIVE_DATA_WARNING = (
    "clients/karen/CLIENT_GROCERY.md is live user data. "
    "Do not reset, discard, casually stage, or casually commit it."
)


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
    output = (proc.stdout or proc.stderr or "").strip()
    return output or "(no output)"


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
    next_start = text.find("\n## ", start + len(marker))
    return text[start: next_start if next_start >= 0 else len(text)].strip()


def _alpha_marker(text: str) -> list[str]:
    purpose = []
    marker_start = text.find("Alpha marker:")
    if marker_start < 0:
        return ["Alpha marker: not found"]
    next_heading = text.find("\n## ", marker_start)
    block = text[marker_start: next_heading if next_heading >= 0 else len(text)]
    for line in block.splitlines():
        line = line.strip()
        if line:
            purpose.append(line)
    return purpose


def _table_rows(section_text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        raw = line.strip()
        if not raw.startswith("|"):
            continue
        if set(raw.replace("|", "").replace(":", "").replace("-", "").strip()) == set():
            continue
        cells = [cell.strip() for cell in raw.strip("|").split("|")]
        if cells and cells[0] in {"ID", "#"}:
            continue
        if cells:
            rows.append(cells)
    return rows


def _lanes_since_alpha(text: str) -> list[list[str]]:
    return _table_rows(_section(text, "Lanes Since Alpha"))


def _planned_milestones(text: str) -> list[list[str]]:
    return _table_rows(_section(text, "Planned Next Milestones"))


def _human_outcome_summaries(text: str) -> str:
    section = _section(text, "Human Outcome Summaries")
    if not section:
        return "(no human outcome summaries found)"
    lines = section.splitlines()
    if lines and lines[0].strip() == "## Human Outcome Summaries":
        lines = lines[1:]
    return "\n".join(line.rstrip() for line in lines).strip() or "(no human outcome summaries found)"


def _current_tactical_note(text: str) -> str:
    section = _section(text, "Current Tactical Note")
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    if len(lines) <= 1:
        return "(no current tactical note found)"
    return " ".join(lines[1:])


def _recommended_next_action(text: str) -> str:
    note = _current_tactical_note(text)
    if "Recommended next:" in note:
        return note.split("Recommended next:", 1)[1].strip()
    for row in _planned_milestones(text):
        if len(row) >= 4 and row[3].strip().upper() in {"NEXT", "ACTIVE", "DESIGN"}:
            return f"{row[1]} ({row[3]})"
    for row in _planned_milestones(text):
        if len(row) >= 4 and row[3].strip().lower() == "planned":
            return f"{row[1]} (planned)"
    return "Review VAL0_ALPHA_BENCHMARK_LOG.md and choose the next safe lane."


def _format_lanes(rows: list[list[str]]) -> list[str]:
    if not rows:
        return ["- No Alpha lanes found."]
    out = []
    for row in rows:
        if len(row) < 8:
            continue
        lane_id, lane, _estimate, _start, end, _actual, commits, status = row[:8]
        notes = row[8] if len(row) > 8 else ""
        out.append(f"- {lane_id} [{status}] {lane} — {commits} — end {end}. {notes}")
    return out or ["- No parseable Alpha lanes found."]


def _format_planned(rows: list[list[str]]) -> list[str]:
    if not rows:
        return ["- No planned milestones found."]
    out = []
    for row in rows:
        if len(row) < 5:
            continue
        num, milestone, estimate, status, notes = row[:5]
        label = "NEXT" if status.strip().upper() == "NEXT" else status
        out.append(f"- {num}. {milestone} [{label}] {estimate}: {notes}")
    return out or ["- No parseable planned milestones found."]


def build_alpha_brief() -> str:
    benchmark_text = BENCHMARK_LOG.read_text(encoding="utf-8") if BENCHMARK_LOG.exists() else ""
    branch = _run_git(["branch", "--show-current"])
    status = _run_git(["status", "--short"])
    commits = _run_git(["log", "--oneline", "-8"])
    lanes = _lanes_since_alpha(benchmark_text)
    planned = _planned_milestones(benchmark_text)
    next_action = _recommended_next_action(benchmark_text)

    lines = [
        "VAL0 Alpha Brief",
        "================",
        "",
        f"Repo: {REPO_ROOT}",
        f"Branch: {branch}",
        "",
        "Git status --short",
        "------------------",
        status,
        "",
        "Latest 8 commits",
        "----------------",
        commits,
        "",
        "Alpha marker",
        "------------",
    ]
    lines.extend(_alpha_marker(benchmark_text))
    lines.extend([
        "",
        "Lanes since Alpha",
        "-----------------",
    ])
    lines.extend(_format_lanes(lanes))
    lines.extend([
        "",
        "Human outcome summaries",
        "-----------------------",
        _human_outcome_summaries(benchmark_text),
        "",
        "Planned next milestones",
        "-----------------------",
    ])
    lines.extend(_format_planned(planned))
    lines.extend([
        "",
        "Current tactical note",
        "---------------------",
        _current_tactical_note(benchmark_text),
        "",
        "Live-data warning",
        "-----------------",
        LIVE_DATA_WARNING,
        "",
        "Recommended next action",
        "-----------------------",
        f"NEXT: {next_action}",
        "",
        "Suggested validation commands",
        "-----------------------------",
        "- python3 scripts/quality/client_fixture_smoke.py --client karen",
        "- python3 scripts/quality/karen_rc_full_smoke.py --keep-going",
        "- git diff --check",
    ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    print(build_alpha_brief(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
