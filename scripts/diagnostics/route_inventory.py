#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_RELATIVE = "tmp/route_inventory/route_inventory.txt"
DEFAULT_OUTPUT = REPO_ROOT / DEFAULT_OUTPUT_RELATIVE

SEARCH_FILES = [
    REPO_ROOT / "bot.py",
    *sorted((REPO_ROOT / "core").glob("*.py")),
]

MARKERS = (
    "maybe_handle_",
    "_looks_like_",
    "Priority Gate",
    "HARD TASK QUERY GATE",
    "KAREN_",
    "GCAL",
    "REMINDER",
    "DOCUMENT",
    "CASE",
    "MEMORY_TEST_TEXT",
    "LLM",
)

CATEGORIES = (
    "pending actions / confirmations",
    "agenda / Google Calendar",
    "reminders",
    "tasks",
    "documents / OCR",
    "case/finca/legal",
    "memory capture",
    "generic/LLM fallback",
)


@dataclass
class RouteHit:
    path: Path
    line_no: int
    function: str
    category: str
    marker: str
    text: str


def _function_at(lines: list[str], line_no: int) -> str:
    function = "(module)"
    for idx in range(0, max(0, line_no)):
        line = lines[idx]
        match = re.match(r"^\s*(?:async\s+def|def)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
        if match:
            function = match.group(1)
    return function


def _category(line: str, function: str, path: Path) -> str:
    haystack = f"{path.name} {function} {line}".lower()

    if any(token in haystack for token in ("pending", "confirmation", "confirmacion", "confirmación", "destructive")):
        return "pending actions / confirmations"
    if any(token in haystack for token in ("gcal", "google calendar", "calendar", "agenda", "evento")):
        return "agenda / Google Calendar"
    if any(token in haystack for token in ("reminder", "recordatorio", "vencido", "rmd")):
        return "reminders"
    if any(token in haystack for token in ("task", "tarea", "commitment", "pendiente")):
        return "tasks"
    if any(token in haystack for token in ("document", "documento", "vfms", "ocr", "watermark")):
        return "documents / OCR"
    if any(token in haystack for token in ("case", "finca", "legal", "lawyer", "nora", "terreno")):
        return "case/finca/legal"
    if any(token in haystack for token in ("memory", "memoria", "insert_message", "insert_case_note", "capture")):
        return "memory capture"
    if any(token in haystack for token in ("llm", "openai", "fallback", "generic", "normal_chat")):
        return "generic/LLM fallback"
    return "generic/LLM fallback"


def _marker_for(line: str) -> str:
    for marker in MARKERS:
        if marker in line:
            return marker
    return ""


def collect_hits() -> list[RouteHit]:
    hits: list[RouteHit] = []
    for path in SEARCH_FILES:
        if not path.exists() or path.name.startswith("__"):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(lines, start=1):
            marker = _marker_for(line)
            if not marker:
                continue
            clean = line.strip()
            if not clean:
                continue
            function = _function_at(lines, idx - 1)
            hits.append(
                RouteHit(
                    path=path.relative_to(REPO_ROOT),
                    line_no=idx,
                    function=function,
                    category=_category(clean, function, path),
                    marker=marker,
                    text=clean[:220],
                )
            )
    return hits


def render_inventory(hits: list[RouteHit]) -> str:
    grouped: dict[str, list[RouteHit]] = defaultdict(list)
    for hit in hits:
        grouped[hit.category].append(hit)

    lines = [
        "Val0 Route Inventory",
        "====================",
        "",
        "Static diagnostic generated from bot.py and core/*.py.",
        "This is an architecture aid only; it does not inspect live Telegram state or execute routes.",
        "",
        f"Files scanned: {len([p for p in SEARCH_FILES if p.exists()])}",
        f"Route/gate marker hits: {len(hits)}",
        "",
    ]

    for category in CATEGORIES:
        category_hits = grouped.get(category, [])
        lines.append(category)
        lines.append("-" * len(category))
        if not category_hits:
            lines.append("(none found)")
        for hit in category_hits:
            lines.append(
                f"- {hit.path}:{hit.line_no} [{hit.function}] "
                f"{hit.marker}: {hit.text}"
            )
        lines.append("")

    leftovers = [hit for hit in hits if hit.category not in CATEGORIES]
    if leftovers:
        lines.append("uncategorized")
        lines.append("-------------")
        for hit in leftovers:
            lines.append(f"- {hit.path}:{hit.line_no} [{hit.function}] {hit.marker}: {hit.text}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory Val0 route/gate markers for Intent Router v2 planning.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to save the rendered inventory.")
    parser.add_argument("--no-save", action="store_true", help="Print only; do not write tmp/route_inventory output.")
    args = parser.parse_args()

    inventory = render_inventory(collect_hits())
    print(inventory, end="")

    if not args.no_save:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(inventory, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
