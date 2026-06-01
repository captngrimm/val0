#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/diagnostics/karen_ocr_spike_01.py"
DOC = ROOT / "docs/product/OCR_SPIKE_01_REGISTRO_PUBLICO.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> int:
    assert_true(SCRIPT.exists(), "diagnostic script exists")
    assert_true(DOC.exists(), "OCR spike doc exists")
    source = SCRIPT.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    assert_contains(source, "add_argument(\"pdf_path\"", "script has CLI PDF path argument")
    assert_contains(source, "pdftoppm", "script renders PDF pages when possible")
    assert_contains(source, "tesseract", "script runs OCR when available")
    assert_contains(source, "tmp/ocr_spike_01", "script writes ignored diagnostic output")
    assert_contains(source, "WATERMARK", "script tracks watermark phrase")
    assert_contains(source, "LEGAL_MARKERS", "script tracks legal markers")
    assert_contains(source, "MEDIDAS CAUTELARES", "script includes legal marker")
    assert_contains(source, "ocr_usable", "script reports usable recommendation")
    assert_contains(source, "ocr_needs_preprocessing", "script reports preprocessing recommendation")
    assert_contains(source, "ocr_not_available", "script reports missing tools")
    assert_contains(source, "ocr_failed", "script reports failure")

    assert_contains(doc, "diagnostic spike, not runtime OCR", "doc says spike only")
    assert_contains(doc, "Do not paste full OCR output", "doc avoids sensitive full text")
    assert_contains(doc, "python3 scripts/diagnostics/karen_ocr_spike_01.py", "doc includes run command")
    assert_contains(doc, "Copia para propositos informativos solamente", "doc names watermark without needing OCR run")
    print("PASS: OCR spike script smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
