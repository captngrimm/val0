#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_RELATIVE = Path("tmp/docs_inventory/markdown_docs_inventory.txt")
OUTPUT_PATH = ROOT / OUTPUT_RELATIVE

SCAN_ROOTS = (
    ROOT / "docs",
    ROOT / "clients",
)

IGNORED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "tmp",
    "cache",
}

KEY_TERMS = (
    "Karen",
    "Router",
    "OCR",
    "Obsidian",
    "ValPrime",
    "OPEL",
    "milestone",
    "roadmap",
    "parking",
    "client",
    "source of truth",
    "source-of-truth",
    "checkpoint",
)

CATEGORIES = (
    "ACTIVE_SOURCE_OF_TRUTH",
    "ACTIVE_ROADMAP",
    "ARCHITECTURE_REPORT",
    "OPS_PLAYBOOK",
    "PARKING_LOT",
    "CLIENT_PRIVATE_OR_STATE",
    "HISTORICAL_REPORT",
    "POSSIBLE_STALE_OR_DUPLICATE",
    "UNKNOWN_REVIEW",
)


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)


def _markdown_paths() -> list[Path]:
    paths: list[Path] = []
    for scan_root in SCAN_ROOTS:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*.md"):
            if path.is_file() and not _is_ignored(path):
                paths.append(path)
    paths.extend(path for path in ROOT.glob("*.md") if path.is_file() and not _is_ignored(path))
    return sorted(set(paths), key=lambda p: str(p.relative_to(ROOT)))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _title(text: str, path: Path) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return path.stem


def _terms(text: str, rel: str) -> list[str]:
    haystack = f"{rel}\n{text}".lower()
    found: list[str] = []
    for term in KEY_TERMS:
        if term.lower() in haystack:
            found.append(term)
    return found


def _classify(path: Path, title: str, text: str, found_terms: list[str]) -> str:
    rel = str(path.relative_to(ROOT))
    rel_lower = rel.lower()
    title_lower = title.lower()
    text_lower = text.lower()

    if rel_lower.startswith("clients/"):
        return "CLIENT_PRIVATE_OR_STATE"

    active_truth = {
        "docs/product/VAL0_MASTER_MILESTONE_MAP.md",
        "docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md",
        "docs/product/VAL0_DOCS_VALUE_MAP.md",
        "docs/ops/VAL0_SESSION_STARTUP_CHECKLIST.md",
        "docs/product/KAREN_RC_STATUS_MAP.md",
        "docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md",
        "docs/architecture/OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md",
    }
    if rel in active_truth:
        return "ACTIVE_SOURCE_OF_TRUTH"

    if rel_lower.startswith("docs/architecture/router_") or rel_lower.startswith("docs/architecture/") and "report" in title_lower:
        return "ARCHITECTURE_REPORT"

    if rel_lower.startswith("docs/ops/"):
        return "OPS_PLAYBOOK"

    if "roadmap" in rel_lower or "roadmap" in title_lower:
        return "ACTIVE_ROADMAP"

    if "parking" in rel_lower or "parking" in text_lower:
        return "PARKING_LOT"

    if any(marker in rel_lower for marker in ("recap", "handoff", "checklist", "log_", "2026_", "202605")):
        return "HISTORICAL_REPORT"

    if any(marker in rel_lower for marker in ("old", "backup", "duplicate", "stale")):
        return "POSSIBLE_STALE_OR_DUPLICATE"

    if "source of truth" in text_lower or "source-of-truth" in text_lower:
        return "ACTIVE_SOURCE_OF_TRUTH"

    if "ocr" in found_terms or "router" in found_terms or "obsidian" in found_terms:
        return "ARCHITECTURE_REPORT"

    return "UNKNOWN_REVIEW"


def build_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _markdown_paths():
        text = _read(path)
        rel = str(path.relative_to(ROOT))
        title = _title(text, path)
        found_terms = _terms(text, rel)
        try:
            mtime = int(path.stat().st_mtime)
        except OSError:
            mtime = 0
        rows.append({
            "path": rel,
            "title": title,
            "category": _classify(path, title, text, found_terms),
            "modified_time": mtime,
            "line_count": len(text.splitlines()),
            "key_terms": found_terms,
        })
    return rows


def render_table(rows: list[dict[str, Any]]) -> str:
    path_width = min(70, max(len("path"), *(len(row["path"]) for row in rows)))
    category_width = max(len("category"), *(len(row["category"]) for row in rows))
    lines = [
        "Markdown docs inventory",
        "",
        f"{'category':<{category_width}}  {'lines':>5}  {'path':<{path_width}}  title",
        "-" * (category_width + path_width + 18),
    ]
    for row in rows:
        path = row["path"]
        if len(path) > path_width:
            path = "..." + path[-(path_width - 3):]
        lines.append(
            f"{row['category']:<{category_width}}  {row['line_count']:>5}  {path:<{path_width}}  {row['title']}"
        )

    counts = Counter(row["category"] for row in rows)
    lines.extend(["", "Counts by category:"])
    for category in CATEGORIES:
        if counts.get(category, 0):
            lines.append(f"- {category}: {counts[category]}")
    return "\n".join(lines)


def write_output(text: str) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory markdown docs and classify their likely value/role.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a readable table.")
    parser.add_argument("--no-write", action="store_true", help=f"Do not write {OUTPUT_RELATIVE}.")
    args = parser.parse_args()

    rows = build_inventory()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        rendered = render_table(rows)
        print(rendered)
        if not args.no_write:
            write_output(rendered)
            print(f"\nWrote: {OUTPUT_RELATIVE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
