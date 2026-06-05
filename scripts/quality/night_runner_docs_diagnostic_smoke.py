#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "NIGHT_RUNNER_DOCS_DIAGNOSTIC.md"
PROTECTED_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def _git_cached_names() -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"git cached diff failed: {proc.stderr.strip()}")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def test_doc_guardrail_language() -> None:
    assert_true(DOC.exists(), "Night Runner docs diagnostic doc exists")
    text = DOC.read_text(encoding="utf-8")
    assert_contains(text, "docs-only", "docs-only language")
    assert_contains(text, "no runtime behavior", "no runtime behavior language")
    assert_contains(text, "CLIENT_GROCERY.md", "CLIENT_GROCERY.md forbidden reference")
    assert_contains(text, "CLIENT_FOLDERS.json", "CLIENT_FOLDERS.json forbidden reference")
    assert_contains(text, "Tiny Docs Patch With Smoke", "tiny docs patch section")
    assert_contains(text, "does not prove runtime/code edits are safe", "runtime/code warning")


def test_protected_live_files_not_staged() -> None:
    staged = set(_git_cached_names())
    for path in PROTECTED_FILES:
        assert_true(path not in staged, f"{path} is not staged")


def main() -> None:
    test_doc_guardrail_language()
    test_protected_live_files_not_staged()
    print("PASS night_runner_docs_diagnostic_smoke")


if __name__ == "__main__":
    main()
