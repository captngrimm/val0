#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_LOG = REPO_ROOT / "docs" / "ops" / "VAL0_ALPHA_BENCHMARK_LOG.md"


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
class TimeRange:
    min_hours: float
    max_hours: float
    parsed: bool
    note: str = ""


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
        if len(row) < 8:
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


def _hours(value: float, unit: str) -> float:
    unit = unit.casefold()
    if unit.startswith("min"):
        return value / 60.0
    if unit.startswith("d"):
        return value * 8.0
    return value


def _parse_time_range(text: str) -> TimeRange:
    raw = str(text or "").strip()
    if not raw or raw.lower() in {"n/a", "pending calibration"}:
        return TimeRange(0.0, 0.0, False, raw or "missing")
    lower = raw.casefold()
    if "same-day" in lower or "elapsed includes" in lower:
        return TimeRange(0.0, 0.0, False, raw)

    range_match = re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*(min|h|d)\b", lower)
    if range_match:
        low = _hours(float(range_match.group(1)), range_match.group(3))
        high = _hours(float(range_match.group(2)), range_match.group(3))
        return TimeRange(low, high, True)

    single_match = re.search(r"~?\s*(\d+(?:\.\d+)?)\s*(min|h|d)\b", lower)
    if single_match:
        value = _hours(float(single_match.group(1)), single_match.group(2))
        return TimeRange(value, value, True)

    return TimeRange(0.0, 0.0, False, raw)


def _category(lane: Lane) -> str:
    blob = f"{lane.lane} {lane.notes}".casefold()
    if "night runner" in blob:
        return "Automation/Night Runner"
    if "fixture" in blob or "smoke" in blob or "test" in blob:
        return "Test/fixture"
    if "guard" in blob or "safety" in blob or "isolation" in blob:
        return "Safety/guardrail"
    if "design" in blob or "docs" in blob or "benchmark" in blob or "roadmap" in blob:
        return "Docs/design"
    if "conversationality" in blob or "personality" in blob or "warmth" in blob or "ux" in blob:
        return "UX/personality"
    if "radar" in blob or "runner" in blob or "diagnostic" in blob or "harness" in blob:
        return "Infrastructure"
    return "Product"


def _skew(estimate: TimeRange, actual: TimeRange) -> str:
    if not estimate.parsed or not actual.parsed:
        return "unknown"
    if actual.max_hours < estimate.min_hours:
        return "over-estimated"
    if actual.min_hours > estimate.max_hours:
        return "under-estimated"
    return "within range"


def _manual_minutes_saved(lane: Lane) -> int:
    blob = f"{lane.lane} {lane.notes}".casefold()
    minutes = 0
    if "night runner" in blob:
        minutes += 10
    if "brief" in blob or "radar" in blob or "benchmark" in blob:
        minutes += 8
    if "fixture" in blob or "smoke" in blob or "harness" in blob:
        minutes += 8
    if "helper" in blob or "audit" in blob or "inventory" in blob:
        minutes += 6
    if "route" in blob or "alias" in blob:
        minutes += 5
    return min(minutes, 20)


def _format_hours(hours: float) -> str:
    if hours == 0:
        return "0 h"
    if hours < 1:
        return f"{hours * 60:.0f} min"
    return f"{hours:.1f} h"


def _lane_line(lane: Lane, actual: TimeRange, estimate: TimeRange) -> str:
    actual_label = _format_hours(actual.max_hours) if actual.parsed else f"unknown ({actual.note})"
    estimate_label = (
        f"{_format_hours(estimate.min_hours)}-{_format_hours(estimate.max_hours)}"
        if estimate.parsed and estimate.min_hours != estimate.max_hours
        else (_format_hours(estimate.max_hours) if estimate.parsed else f"unknown ({estimate.note})")
    )
    return f"- {lane.lane_id}: {lane.lane} | estimate {estimate_label} | actual {actual_label}"


def build_roi_radar() -> str:
    text = BENCHMARK_LOG.read_text(encoding="utf-8") if BENCHMARK_LOG.exists() else ""
    lanes = _parse_lanes(text)
    parsed: list[tuple[Lane, TimeRange, TimeRange, str]] = []
    for lane in lanes:
        estimate = _parse_time_range(lane.estimate)
        actual = _parse_time_range(lane.actual)
        parsed.append((lane, estimate, actual, _skew(estimate, actual)))

    estimate_min = sum(estimate.min_hours for _lane, estimate, _actual, _skew_label in parsed if estimate.parsed)
    estimate_max = sum(estimate.max_hours for _lane, estimate, _actual, _skew_label in parsed if estimate.parsed)
    actual_total = sum(actual.max_hours for _lane, _estimate, actual, _skew_label in parsed if actual.parsed)
    parseable_actuals = [(lane, estimate, actual, skew) for lane, estimate, actual, skew in parsed if actual.parsed]
    incomplete = [lane for lane, estimate, actual, _skew_label in parsed if not estimate.parsed or not actual.parsed]

    skew_counts = {
        "under-estimated": sum(1 for *_rest, skew in parsed if skew == "under-estimated"),
        "over-estimated": sum(1 for *_rest, skew in parsed if skew == "over-estimated"),
        "within range": sum(1 for *_rest, skew in parsed if skew == "within range"),
        "unknown": sum(1 for *_rest, skew in parsed if skew == "unknown"),
    }

    categories: dict[str, list[Lane]] = {}
    for lane in lanes:
        categories.setdefault(_category(lane), []).append(lane)

    fastest = sorted(parseable_actuals, key=lambda item: item[2].max_hours)[:6]
    skewed = sorted(
        [
            (lane, estimate, actual, actual.max_hours - estimate.max_hours)
            for lane, estimate, actual, skew in parseable_actuals
            if estimate.parsed and skew == "under-estimated"
        ],
        key=lambda item: item[3],
        reverse=True,
    )[:5]

    night_runner = [item for item in parsed if "night runner" in item[0].lane.casefold() or item[0].lane_id.startswith("NIGHT-RUNNER")]
    nr_estimate_min = sum(estimate.min_hours for _lane, estimate, _actual, _skew_label in night_runner if estimate.parsed)
    nr_estimate_max = sum(estimate.max_hours for _lane, estimate, _actual, _skew_label in night_runner if estimate.parsed)
    nr_actual = sum(actual.max_hours for _lane, _estimate, actual, _skew_label in night_runner if actual.parsed)
    nr_saved = sum(_manual_minutes_saved(lane) for lane, _estimate, _actual, _skew_label in night_runner)

    saved_minutes = sum(_manual_minutes_saved(lane) for lane in lanes)
    roi_verdict = "continue"
    if nr_actual > 4 and nr_saved < 30:
        roi_verdict = "pause"
    if nr_actual > 8 and nr_saved < 20:
        roi_verdict = "stop"

    lines = [
        "VAL0 Benchmark ROI Radar",
        "========================",
        "",
        f"Benchmark log: {BENCHMARK_LOG}",
        "",
        "Summary",
        "-------",
        f"- Total lanes analyzed: {len(lanes)}",
        f"- Parseable estimate range total: {_format_hours(estimate_min)}-{_format_hours(estimate_max)}",
        f"- Parseable actual total: {_format_hours(actual_total)}",
        f"- Incomplete/non-numeric rows: {len(incomplete)}",
        "",
        "ETA skew summary",
        "----------------",
        f"- under-estimated: {skew_counts['under-estimated']}",
        f"- over-estimated: {skew_counts['over-estimated']}",
        f"- within range: {skew_counts['within range']}",
        f"- unknown/incomplete: {skew_counts['unknown']}",
        "",
        "Top fastest parseable lanes",
        "---------------------------",
    ]
    lines.extend(_lane_line(lane, actual, estimate) for lane, estimate, actual, _skew_label in fastest)
    if not fastest:
        lines.append("- No parseable actuals found.")
    lines.extend(["", "Largest under-estimate skew", "-----------------------------"])
    if skewed:
        for lane, estimate, actual, drift in skewed:
            lines.append(
                f"- {lane.lane_id}: {lane.lane} | actual exceeded high estimate by {_format_hours(drift)}"
            )
    else:
        lines.append("- No parseable under-estimated lanes found.")

    lines.extend(["", "Category grouping", "-----------------"])
    for category in sorted(categories):
        category_lanes = categories[category]
        category_actual = sum(
            _parse_time_range(lane.actual).max_hours
            for lane in category_lanes
            if _parse_time_range(lane.actual).parsed
        )
        lines.append(f"- {category}: {len(category_lanes)} lanes, parseable actual {_format_hours(category_actual)}")

    lines.extend(
        [
            "",
            "Night Runner subtotal",
            "---------------------",
            f"- Night Runner lanes: {len(night_runner)}",
            f"- Estimate range: {_format_hours(nr_estimate_min)}-{_format_hours(nr_estimate_max)}",
            f"- Actual parseable total: {_format_hours(nr_actual)}",
            "- Unlocked: refusal-first lane validation, safe allow-listed diagnostics/tests, and a bedtime packet/report workflow.",
            f"- Conservative operator-time-saved heuristic: about {nr_saved} min per repeated use cycle once adopted.",
            f"- Current ROI verdict: {roi_verdict}",
        ]
    )

    lines.extend(
        [
            "",
            "Operator-time-saved heuristic",
            "-----------------------------",
            f"- Conservative total potential saved per repeated use cycle: about {saved_minutes} min.",
            "- This is intentionally conservative and does not count product value from better Karen behavior.",
            "- High-signal repeat-work reducers: Night Runner, Alpha brief/radar, fixtures/smokes, audits, and benchmark helper lanes.",
            "",
            "Recommendation",
            "--------------",
            "- Keep investing lightly in Night Runner only until one real bedtime/morning cycle proves useful.",
            "- Then return to product work unless the report saves meaningful operator time.",
            "- Do not add more automation layers until the current Night Runner packet is used at least once.",
            "",
            "Next 3 suggested lanes",
            "----------------------",
            "1. BENCH-02: close benchmark data gaps by normalizing prose actuals into numeric calibration notes.",
            "2. A-025D: shadow logging/observation for bounded voice renderer if continuing Caso Finca intelligence.",
            "3. Fixture Migration v2 or M45 Router Coverage Closeout if returning to test/router foundation.",
            "",
            "Data caveats",
            "------------",
        ]
    )
    if incomplete:
        lines.append("- Some estimate/actual cells are prose, n/a, or pending; totals only include parseable rows.")
        for lane in incomplete[:8]:
            lines.append(f"  - {lane.lane_id}: estimate={lane.estimate!r}, actual={lane.actual!r}")
        if len(incomplete) > 8:
            lines.append(f"  - ... {len(incomplete) - 8} more incomplete rows")
    else:
        lines.append("- All rows were parseable.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    print(build_roi_radar(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
