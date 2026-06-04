#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_LOG = REPO_ROOT / "docs" / "ops" / "VAL0_ALPHA_BENCHMARK_LOG.md"
LIVE_DATA_PATHS = {
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
}
THIS_SCRIPT = "scripts/diagnostics/val0_milestone_radar.py"


@dataclass(frozen=True)
class Lane:
    lane_id: str
    lane: str
    estimate: str
    start: str
    end: str
    actual: str
    commits: str
    status: str
    notes: str


@dataclass(frozen=True)
class PlannedMilestone:
    number: str
    milestone: str
    estimate: str
    status: str
    notes: str


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
    return text[start : next_start if next_start >= 0 else len(text)].strip()


def _table_rows(section_text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        raw = line.strip()
        if not raw.startswith("|"):
            continue
        cells = [cell.strip() for cell in raw.strip("|").split("|")]
        if not cells or cells[0] in {"ID", "#"}:
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells if cell):
            continue
        rows.append(cells)
    return rows


def _parse_lanes(text: str) -> list[Lane]:
    lanes: list[Lane] = []
    for row in _table_rows(_section(text, "Lanes Since Alpha")):
        if len(row) < 8 or not row[0].startswith("A-"):
            continue
        lanes.append(
            Lane(
                lane_id=row[0],
                lane=row[1],
                estimate=row[2],
                start=row[3],
                end=row[4],
                actual=row[5],
                commits=row[6],
                status=row[7],
                notes=row[8] if len(row) > 8 else "",
            )
        )
    return lanes


def _parse_planned(text: str) -> list[PlannedMilestone]:
    planned: list[PlannedMilestone] = []
    for row in _table_rows(_section(text, "Planned Next Milestones")):
        if len(row) < 5:
            continue
        planned.append(
            PlannedMilestone(
                number=row[0],
                milestone=row[1],
                estimate=row[2],
                status=row[3],
                notes=row[4],
            )
        )
    return planned


def _current_tactical_note(text: str) -> str:
    section = _section(text, "Current Tactical Note")
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    if len(lines) <= 1:
        return "(no current tactical note found)"
    return " ".join(lines[1:])


def _latest_sealed_lane(lanes: list[Lane]) -> Lane | None:
    sealed = [lane for lane in lanes if lane.status.upper() in {"PASS", "DONE"}]
    return sealed[-1] if sealed else (lanes[-1] if lanes else None)


def _candidate_lanes(
    tactical_note: str,
    planned: list[PlannedMilestone],
    *,
    latest_sealed_lane_id: str | None = None,
) -> list[str]:
    candidates: list[str] = []
    sealed_id = (latest_sealed_lane_id or "").strip()
    if "A-025C" in tactical_note and sealed_id != "A-025C":
        candidates.append(
            "A-025C shadow-only voice candidate generation for Caso Finca Q&A"
        )
    if re.search(r"Night Runner", tactical_note, flags=re.IGNORECASE):
        candidates.append("Night Runner v0 Dry-Run design")
    if "A-025D" in tactical_note:
        candidates.append("A-025D shadow logging/observation")
    for milestone in planned:
        if milestone.status.lower() in {"next", "active", "planned", "watch"}:
            label = f"{milestone.milestone} ({milestone.estimate}, {milestone.status})"
            if label not in candidates:
                candidates.append(label)
        if len(candidates) >= 5:
            break
    return candidates or ["Review the benchmark log and choose the next safe lane."]


def _stage(tactical_note: str, status_short: str) -> str:
    note = tactical_note.lower()
    if (
        "decide between" in note
        or "recommended next: decide" in note
        or "recommended next: choose" in note
    ):
        return "decision point"
    if "design" in note and "implementation" not in note:
        return "design"
    if "verify" in note or "smoke" in note:
        return "verify"
    if "live" in note:
        return "live test"
    if "close" in note or "sealed" in note:
        return "close / decision point"
    if status_short and status_short != "(no output)":
        return "implementation or review"
    return "decision point"


def _eta_lines(candidates: list[str], lanes: list[Lane]) -> list[str]:
    recent_actuals = [
        lane.actual
        for lane in lanes[-8:]
        if lane.actual and lane.actual not in {"n/a", "pending calibration"}
    ]
    calibration = "; recent actuals: " + ", ".join(recent_actuals[-4:]) if recent_actuals else ""
    lines: list[str] = []
    for candidate in candidates[:4]:
        lowered = candidate.lower()
        if "a-025c" in lowered:
            eta = "1-2 focused sessions"
        elif "a-025d" in lowered:
            eta = "1-2 h shadow logging/observation pass"
        elif "night runner" in lowered:
            eta = "30-60 min design, then 1-2 h skeleton"
        elif "fixture" in lowered:
            eta = "3-5 h from planned table"
        elif "router" in lowered:
            eta = "2-4 h from planned table"
        elif "conversation state" in lowered:
            eta = "4-6 h from planned table"
        else:
            eta = "use planned estimate or ask High Command to scope"
        lines.append(f"- {candidate}: {eta}{calibration}")
    return lines


def _status_paths(status_short: str) -> list[str]:
    paths: list[str] = []
    for line in status_short.splitlines():
        if not line.strip() or line.strip() == "(no output)":
            continue
        if len(line) > 3 and line[2] == " ":
            path = line[3:].strip()
        else:
            parts = line.strip().split(maxsplit=1)
            path = parts[1].strip() if len(parts) > 1 else line.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        paths.append(path)
    return paths


def _blockers_and_risks(status_short: str, candidates: list[str]) -> list[str]:
    paths = _status_paths(status_short)
    non_live_dirty = [
        path for path in paths if path not in LIVE_DATA_PATHS and path != THIS_SCRIPT
    ]
    risks = []
    live_dirty = [path for path in paths if path in LIVE_DATA_PATHS]
    if live_dirty:
        risks.append(
            "Live Karen data is dirty and must remain unstaged/uncommitted: "
            + ", ".join(live_dirty)
        )
    if non_live_dirty:
        risks.append("Working tree has review-needed changes: " + ", ".join(non_live_dirty))
    if len(candidates) >= 2:
        risks.append("Decision risk: choosing multiple next lanes at once causes drift.")
    return risks or ["No blockers detected from git status or benchmark note."]


def _exact_next_action(tactical_note: str, candidates: list[str]) -> str:
    note = tactical_note.lower()
    if "a-025d" in note and "night runner" in note and len(candidates) >= 2:
        return (
            "Choose one: Night Runner v0 Dry-Run design if prioritizing "
            "overnight automation, or A-025D shadow logging/observation if "
            "continuing voice renderer instrumentation."
        )
    if "decide between" in note and len(candidates) >= 2:
        return (
            "Ask High Command to choose one lane. Default to A-025C if continuing "
            "the Caso Finca product lane; choose Night Runner v0 only if ops automation "
            "is the priority."
        )
    return f"Start with: {candidates[0]}"


def _drift_warning(tactical_note: str, candidates: list[str], status_short: str) -> str:
    paths = _status_paths(status_short)
    non_live_dirty = [
        path for path in paths if path not in LIVE_DATA_PATHS and path != THIS_SCRIPT
    ]
    if non_live_dirty:
        return "DRIFT WATCH: unclosed work exists outside live data; inspect before changing lanes."
    if "decide between" in tactical_note.lower() and len(candidates) > 1:
        return "DRIFT WATCH: benchmark says this is a choice point. Pick one lane before implementation."
    return "No drift warning beyond normal lane discipline."


def build_milestone_radar() -> str:
    text = BENCHMARK_LOG.read_text(encoding="utf-8") if BENCHMARK_LOG.exists() else ""
    lanes = _parse_lanes(text)
    planned = _parse_planned(text)
    latest = _latest_sealed_lane(lanes)
    tactical_note = _current_tactical_note(text)
    candidates = _candidate_lanes(
        tactical_note,
        planned,
        latest_sealed_lane_id=latest.lane_id if latest else None,
    )
    branch = _run_git(["branch", "--show-current"])
    head = _run_git(["rev-parse", "--short", "HEAD"])
    status_short = _run_git(["status", "--short"])
    stage = _stage(tactical_note, status_short)
    blockers = _blockers_and_risks(status_short, candidates)

    lines = [
        "VAL0 Milestone Radar",
        "====================",
        "",
        f"Repo: {REPO_ROOT}",
        f"Branch: {branch}",
        f"Head: {head}",
        "",
        "Git status --short",
        "------------------",
        status_short,
        "",
        "Current sealed lane",
        "-------------------",
    ]
    if latest:
        lines.extend(
            [
                f"{latest.lane_id} — {latest.lane}",
                f"Status: {latest.status}",
                f"Commit(s): {latest.commits}",
                f"Actual: {latest.actual}",
                f"Notes: {latest.notes}",
            ]
        )
    else:
        lines.append("(no sealed Alpha lane found)")
    lines.extend(
        [
            "",
            "Current stage",
            "-------------",
            stage,
            "",
            "Current tactical note",
            "---------------------",
            tactical_note,
            "",
            "Next candidate lane(s)",
            "----------------------",
        ]
    )
    lines.extend(f"- {candidate}" for candidate in candidates)
    lines.extend(
        [
            "",
            "Rough ETA",
            "---------",
        ]
    )
    lines.extend(_eta_lines(candidates, lanes))
    lines.extend(
        [
            "",
            "Blockers / risks",
            "----------------",
        ]
    )
    lines.extend(f"- {risk}" for risk in blockers)
    lines.extend(
        [
            "",
            "Exact next action",
            "-----------------",
            _exact_next_action(tactical_note, candidates),
            "",
            "Drift warning",
            "-------------",
            _drift_warning(tactical_note, candidates, status_short),
            "",
            "Validation before closing a lane",
            "--------------------------------",
            "- python3 scripts/quality/client_fixture_smoke.py --client karen",
            "- python3 scripts/quality/karen_rc_full_smoke.py --keep-going",
            "- git diff --check",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    print(build_milestone_radar(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
