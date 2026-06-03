#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "diagnostics" / "karen_document_inventory_audit.py"
LIVE_FILE = ROOT / "clients" / ("kar" + "en") / "CLIENT_GROCERY.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in output")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in output")


def run_script(*args: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout


def cached_live_file() -> str:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", str(LIVE_FILE.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout.strip()


def test_text_output_is_metadata_only() -> None:
    before = LIVE_FILE.read_text(encoding="utf-8") if LIVE_FILE.exists() else None
    output = run_script("--limit", "8")
    after = LIVE_FILE.read_text(encoding="utf-8") if LIVE_FILE.exists() else None

    assert_contains(output, "Karen document inventory audit", "label")
    assert_contains(output, "Metadata-only", "privacy boundary")
    assert_contains(output, "OCR status", "OCR field")
    assert_contains(output, "saved summary status", "summary field")
    assert_contains(output, "possible Caso Finca relevance", "relevance field")
    assert_contains(output, "safe next action", "next action field")
    assert_contains(output, "No mutation performed", "read-only proof")

    for forbidden in (
        "Copia para propósitos informativos solamente",
        "Copia para propositos informativos solamente",
        "JUZGADO PRIMERO DE CIRCUITO",
        "Prescripción Adquisitiva de Dominio",
        "hash:",
        "sha256",
    ):
        assert_not_contains(output, forbidden, f"no raw body/hash dump: {forbidden}")

    assert_true(before == after, "CLIENT_GROCERY.md content unchanged")
    assert_true(cached_live_file() == "", "CLIENT_GROCERY.md not staged")


def test_json_output_is_structured() -> None:
    payload = json.loads(run_script("--limit", "5", "--json"))
    assert_true(payload.get("label") == "Karen document inventory audit", "json label")
    assert_true("records" in payload, "json records")
    assert_true("totals" in payload, "json totals")
    assert_contains(payload.get("privacy", ""), "No raw OCR text", "json privacy boundary")
    for record in payload.get("records", []):
        body_blob = json.dumps(record, ensure_ascii=False).lower()
        assert_not_contains(body_blob, "copia para propósitos informativos solamente", "json no OCR body")
        assert_not_contains(body_blob, "juzgado primero de circuito", "json no legal body")


def main() -> int:
    assert_true(SCRIPT.exists(), "diagnostic script exists")
    test_text_output_is_metadata_only()
    test_json_output_is_structured()
    print("PASS: Karen document inventory audit smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
