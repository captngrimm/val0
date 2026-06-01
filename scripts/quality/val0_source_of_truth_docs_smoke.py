#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "docs" / "product" / "VAL0_MASTER_MILESTONE_MAP.md"
INDEX = ROOT / "docs" / "product" / "VAL0_SOURCE_OF_TRUTH_INDEX.md"
CHECKLIST = ROOT / "docs" / "ops" / "VAL0_SESSION_STARTUP_CHECKLIST.md"
HELPER = ROOT / "scripts" / "diagnostics" / "val0_source_of_truth_check.py"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def _combined_docs() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in (MASTER, INDEX, CHECKLIST))


def test_docs_exist_and_contain_core_terms() -> None:
    for path, label in (
        (MASTER, "master milestone map"),
        (INDEX, "source-of-truth index"),
        (CHECKLIST, "startup checklist"),
        (HELPER, "diagnostic helper"),
    ):
        assert_true(path.exists(), f"{label} exists")

    text = _combined_docs()
    for needle in (
        "M45",
        "Karen RC full smoke",
        "Intent Router v2",
        "OCR",
        "Obsidian",
        "ValPrime",
        "OPEL",
        "source-of-truth",
        "OFF",
        "Do not start broad router refactor",
    ):
        assert_contains(text, needle, "source-of-truth docs")


def test_helper_compiles_and_runs_without_full() -> None:
    compile_result = subprocess.run(
        ["./scripts/val0py", "-m", "py_compile", "scripts/diagnostics/val0_source_of_truth_check.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(compile_result.returncode == 0, f"helper compiles: {compile_result.stderr}")

    run_result = subprocess.run(
        ["python3", "scripts/diagnostics/val0_source_of_truth_check.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(run_result.returncode == 0, f"helper runs: {run_result.stderr}")
    assert_contains(run_result.stdout, "SKIPPED by default", "helper default skips full smoke")
    assert_contains(run_result.stdout, "Intent Router v2 coverage report", "helper runs coverage report")


def main() -> int:
    test_docs_exist_and_contain_core_terms()
    test_helper_compiles_and_runs_without_full()
    print("PASS: Val0 source-of-truth docs smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
