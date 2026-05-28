#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "product" / "KAREN_DOCUMENT_MVP_RC_READINESS_2026_05_28.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r}")


def main() -> int:
    assert_true(DOC.exists(), "RC readiness doc exists")
    text = DOC.read_text(encoding="utf-8")

    for needle, label in (
        ("val0-post-m41-conversationality-memory-lab-2026-05-25", "branch recorded"),
        ("8b96566 Add Karen last uploaded document context", "head recorded"),
        ("karen-founder-beta-safe-2026-05-25", "safe fallback branch"),
        ("4712a05", "safe fallback commit"),
        ("Upload", "upload checklist"),
        ("Extraction / index", "extraction checklist"),
        ("Inventory", "inventory checklist"),
        ("Summary persistence", "summary persistence checklist"),
        ("Alias / tags", "alias tags checklist"),
        ("Latest-document context", "latest context checklist"),
        ("Val, transcribe este documento y hazme un resumen", "upload command"),
        ("Val, qué documentos tengo?", "inventory command"),
        ("Val, qué fue lo último que subí?", "latest upload command"),
        ("Val, resume el último documento", "latest summary command"),
        ("Val, sugiere nombre para este documento", "naming command"),
        ("Val, guarda ese nombre", "alias save command"),
        ("OCR/manual review limitations", "OCR caveat"),
        ("Word/DOCX boundaries", "Word caveat"),
        ("Batch upload is parked", "batch caveat"),
        ("clients/karen/CLIENT_GROCERY.md", "dirty file caveat"),
        ("literal_karen", "audit warning caveat"),
        ("one real legal PDF only", "live protocol"),
        ("Compile passes", "compile RC criterion"),
        ("Client isolation audit passes", "audit RC criterion"),
        ("Service restart is clean", "service restart criterion"),
        ("Recommendation: **Go", "go recommendation"),
    ):
        assert_contains(text, needle, label)

    assert_not_contains(text, "physically rename original files.", "no destructive rename promise")
    assert_contains(text, "does not physically rename original uploaded files", "non-destructive alias note")
    print("PASS: Karen document MVP RC readiness smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
