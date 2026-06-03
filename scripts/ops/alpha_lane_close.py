#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BENCHMARK = ROOT / "docs" / "ops" / "VAL0_ALPHA_BENCHMARK_LOG.md"
CLIENT_GROCERY = "CLIENT_GROCERY.md"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close/update a Val0 Alpha benchmark lane.")
    parser.add_argument("--benchmark-path", default=str(DEFAULT_BENCHMARK), help="Benchmark markdown path.")
    parser.add_argument("--id", required=True, help="Lane id, e.g. A-012.")
    parser.add_argument("--lane", required=True, help="Lane title.")
    parser.add_argument("--estimate", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--actual", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--notes", required=True)
    parser.add_argument("--next-note", default="", help="Optional replacement text for Current Tactical Note.")
    parser.add_argument("--planned-name", default="", help="Optional planned milestone name to update.")
    parser.add_argument("--planned-status", default="", help="Optional planned milestone status replacement.")
    parser.add_argument("--replace", action="store_true", help="Replace existing lane id instead of refusing duplicates.")
    parser.add_argument("--dry-run", action="store_true", help="Print proposed benchmark without writing.")
    return parser.parse_args(argv)


def _escape_cell(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text.replace("|", "/")


def _commit_cell(value: str) -> str:
    text = _escape_cell(value)
    if not text:
        return ""
    if text.startswith("`") and text.endswith("`"):
        return text
    return f"`{text}`"


def _lane_row(args: argparse.Namespace) -> str:
    cells = [
        args.id,
        args.lane,
        args.estimate,
        args.start,
        args.end,
        args.actual,
        _commit_cell(args.commit),
        args.status,
        args.notes,
    ]
    return "| " + " | ".join(_escape_cell(cell) for cell in cells) + " |"


def _section_bounds(text: str, heading: str) -> tuple[int, int]:
    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"Missing section: {heading}")
    next_start = text.find("\n## ", start + len(marker))
    return start, next_start if next_start >= 0 else len(text)


def _update_lanes_section(text: str, args: argparse.Namespace) -> tuple[str, str]:
    start, end = _section_bounds(text, "Lanes Since Alpha")
    section = text[start:end]
    row = _lane_row(args)
    lane_pattern = re.compile(rf"^\|\s*{re.escape(args.id)}\s*\|.*$", re.MULTILINE)
    match = lane_pattern.search(section)

    if match and not args.replace:
        raise ValueError(f"Lane id {args.id} already exists. Use --replace to update it.")
    if match:
        updated_section = section[:match.start()] + row + section[match.end():]
        action = "replaced"
    else:
        lines = section.splitlines()
        insert_at = len(lines)
        for idx, line in enumerate(lines):
            if line.startswith("|") and not line.startswith("|---") and idx > 0:
                insert_at = idx + 1
        lines.insert(insert_at, row)
        updated_section = "\n".join(lines)
        action = "inserted"

    return text[:start] + updated_section + text[end:], action


def _update_current_tactical_note(text: str, note: str) -> str:
    note = str(note or "").strip()
    if not note:
        return text
    start, end = _section_bounds(text, "Current Tactical Note")
    replacement = f"## Current Tactical Note\n\n{note}\n"
    return text[:start] + replacement + text[end:]


def _update_planned_status(text: str, planned_name: str, planned_status: str) -> str:
    planned_name = str(planned_name or "").strip()
    planned_status = str(planned_status or "").strip()
    if not planned_name or not planned_status:
        return text
    start, end = _section_bounds(text, "Planned Next Milestones")
    section = text[start:end]
    lines = section.splitlines()
    updated = False
    for idx, line in enumerate(lines):
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 5 or cells[0] == "#":
            continue
        if cells[1].lower() == planned_name.lower():
            cells[3] = _escape_cell(planned_status)
            lines[idx] = "| " + " | ".join(cells) + " |"
            updated = True
            break
    if not updated:
        raise ValueError(f"Planned milestone not found: {planned_name}")
    return text[:start] + "\n".join(lines) + text[end:]


def update_benchmark(text: str, args: argparse.Namespace) -> tuple[str, str]:
    updated, action = _update_lanes_section(text, args)
    updated = _update_planned_status(updated, args.planned_name, args.planned_status)
    updated = _update_current_tactical_note(updated, args.next_note)
    return updated.rstrip() + "\n", action


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    benchmark_path = Path(args.benchmark_path)
    original = benchmark_path.read_text(encoding="utf-8")
    updated, action = update_benchmark(original, args)

    if CLIENT_GROCERY in str(benchmark_path):
        raise SystemExit("Refusing to write CLIENT_GROCERY.md.")

    if args.dry_run:
        print(f"DRY RUN: would {action} lane {args.id} in {benchmark_path}")
        print(_lane_row(args))
        if args.next_note:
            print(f"Would update Current Tactical Note: {_escape_cell(args.next_note)}")
        if args.planned_name and args.planned_status:
            print(f"Would update planned milestone: {_escape_cell(args.planned_name)} -> {_escape_cell(args.planned_status)}")
        return 0

    benchmark_path.write_text(updated, encoding="utf-8")
    print(f"OK: {action} lane {args.id} in {benchmark_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
