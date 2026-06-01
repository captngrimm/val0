#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTIC = ROOT / "scripts" / "diagnostics" / "markdown_docs_inventory.py"
VALUE_MAP = ROOT / "docs" / "product" / "VAL0_DOCS_VALUE_MAP.md"
SOURCE_INDEX = ROOT / "docs" / "product" / "VAL0_SOURCE_OF_TRUTH_INDEX.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def test_diagnostic_exists_compiles_and_runs() -> None:
    assert_true(DIAGNOSTIC.exists(), "markdown inventory diagnostic exists")
    source = DIAGNOSTIC.read_text(encoding="utf-8")
    assert_contains(source, "--json", "diagnostic json support")
    assert_contains(source, "tmp/docs_inventory/markdown_docs_inventory.txt", "diagnostic output path")

    compile_result = subprocess.run(
        ["./scripts/val0py", "-m", "py_compile", "scripts/diagnostics/markdown_docs_inventory.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(compile_result.returncode == 0, f"diagnostic compiles: {compile_result.stderr}")

    run_result = subprocess.run(
        ["python3", "scripts/diagnostics/markdown_docs_inventory.py", "--no-write"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(run_result.returncode == 0, f"diagnostic runs: {run_result.stderr}")
    assert_contains(run_result.stdout, "Counts by category", "diagnostic table output")

    json_result = subprocess.run(
        ["python3", "scripts/diagnostics/markdown_docs_inventory.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(json_result.returncode == 0, f"diagnostic json runs: {json_result.stderr}")
    rows = json.loads(json_result.stdout)
    assert_true(isinstance(rows, list) and rows, "diagnostic json returns rows")
    assert_true(any(row.get("path") == "docs/product/VAL0_DOCS_VALUE_MAP.md" for row in rows), "value map appears in inventory")


def test_value_map_and_source_index() -> None:
    assert_true(VALUE_MAP.exists(), "docs value map exists")
    text = VALUE_MAP.read_text(encoding="utf-8")
    for needle in (
        "ACTIVE_SOURCE_OF_TRUTH",
        "ACTIVE_ROADMAP",
        "CLIENT_PRIVATE_OR_STATE",
        "POSSIBLE_STALE_OR_DUPLICATE",
        "Never delete docs automatically",
        "source-of-truth docs",
        "Obsidian",
        "Router",
        "OCR",
        "Karen",
    ):
        assert_contains(text, needle, "docs value map")

    assert_true(SOURCE_INDEX.exists(), "source-of-truth index exists")
    index = SOURCE_INDEX.read_text(encoding="utf-8")
    assert_contains(index, "Markdown docs inventory / value map", "source index inventory section")
    assert_contains(index, "docs/product/VAL0_DOCS_VALUE_MAP.md", "source index value map")
    assert_contains(index, "scripts/diagnostics/markdown_docs_inventory.py", "source index inventory script")


def main() -> int:
    test_diagnostic_exists_compiles_and_runs()
    test_value_map_and_source_index()
    print("PASS: Markdown docs inventory smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
