#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "product" / "CASO_FINCA_CARPETA_CLARA_DESIGN_V1.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> int:
    assert_true(DOC.exists(), "Caso Finca design doc exists")
    text = DOC.read_text(encoding="utf-8")

    assert_contains(text, "Caso Finca", "Caso Finca named")
    assert_contains(text, "Carpeta Clara", "Carpeta Clara named")
    assert_contains(text, "Nora", "Nora workflow included")
    assert_contains(text, "Val does not give legal conclusions", "legal boundary in English")
    assert_contains(text, "Val organiza lo que esta registrado", "legal boundary in Spanish")
    assert_contains(text, "Now Val Will Be Able To", "Boss outcome section")
    assert_contains(text, "MVP Phases", "MVP phases")
    assert_contains(text, "Phase 1: Read-only case status", "read-only MVP phase")
    assert_contains(text, "WorkspaceCase", "generic internal model")
    assert_contains(text, "client isolation", "client isolation risk/test")
    assert_contains(text, "No live data mutation", "no live mutation test strategy")
    print("PASS: Caso Finca / Carpeta Clara design smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
