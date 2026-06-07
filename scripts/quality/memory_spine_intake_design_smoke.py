#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "docs/product/MEMORY_SPINE_01A_INTAKE_MEMORY_LIBRARY_LAYER_DESIGN.md"
OBJECT_MODEL = ROOT / "docs/product/MEMORY_SPINE_01A_MEMORY_OBJECT_MODEL.md"
PROTECTED = (
    "clients/karen/CLIENT_FOLDERS.json",
    "clients/karen/CLIENT_GROCERY.md",
)


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r}")


def read_docs() -> str:
    assert_true(DESIGN.exists(), "memory spine design doc exists")
    assert_true(OBJECT_MODEL.exists(), "memory object model doc exists")
    return DESIGN.read_text(encoding="utf-8") + "\n\n" + OBJECT_MODEL.read_text(encoding="utf-8")


def test_required_concepts() -> None:
    text = read_docs()
    required = (
        "Desk / hot memory",
        "Side Table / warm memory",
        "Library Index / librarian",
        "Vault / cold storage",
        "consent before saving",
        "memory candidate",
        "confirmed memory",
        "workflow profile",
        "privacy boundary",
        "correction pattern",
        "no hidden profiling",
        "no manipulation",
        "no cross-client contamination",
        "delete/update memory",
        "examples",
        "future runtime mapping",
    )
    for needle in required:
        assert_contains(text, needle, f"required concept {needle}")


def test_object_model_concepts() -> None:
    text = OBJECT_MODEL.read_text(encoding="utf-8")
    for needle in (
        "memory_candidate",
        "user_preference",
        "workflow_profile",
        "intake_summary",
        "correction_pattern",
        "memory_index_entry",
        "privacy_boundary",
        "audit_event",
        "client_id / user_id",
        "consent_status",
        "retrieval_tags",
        "no raw secrets",
        "no unconfirmed sensitive facts",
        "no global leakage",
        "no Karen hardcoding",
        "client isolation first",
        "inspectable and deletable",
    ):
        assert_contains(text, needle, f"object model concept {needle}")


def test_no_forbidden_runtime_or_live_data_references() -> None:
    text = read_docs()
    for needle in (
        "CLIENT_GROCERY.md",
        "CLIENT_FOLDERS.json",
        "/" + "clients" + "/" + "karen",
        "Insan" + "ity",
        "bot.py",
        "core/",
        "DB schema migration added",
        "profile write implemented",
    ):
        assert_not_contains(text, needle, "design docs avoid forbidden/runtime leakage")


def test_protected_not_staged() -> None:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *PROTECTED],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert_true(proc.stdout.strip() == "", "protected live data files are not staged")


def main() -> int:
    test_required_concepts()
    test_object_model_concepts()
    test_no_forbidden_runtime_or_live_data_references()
    test_protected_not_staged()
    print("PASS: memory spine intake design smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
