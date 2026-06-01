#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "scripts" / "diagnostics" / "intent_router_v2_sample_harness.py"
DOC = ROOT / "docs" / "architecture" / "INTENT_ROUTER_V2_MARCHING_ORDER.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def test_harness_exists_compiles_and_contains_samples() -> None:
    assert_true(HARNESS.exists(), "sample harness exists")
    result = subprocess.run(
        ["./scripts/val0py", "-m", "py_compile", "scripts/diagnostics/intent_router_v2_sample_harness.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"harness compiles: {result.stderr}")

    source = HARNESS.read_text(encoding="utf-8")
    for needle in (
        "Val que tareas tengo activas?",
        "Recuérdame en 10 minutos llamar a Mabel",
        "Val agenda prueba calendario mañana a las 10am",
        "Val resume con OCR el último documento",
        "Qué tengo guardado del caso del terreno",
        "--json",
        "--allow-failures",
        "classify_intent_shadow",
    ):
        assert_contains(source, needle, "harness representative content")


def test_harness_runs_text_and_json() -> None:
    text_run = subprocess.run(
        ["python3", "scripts/diagnostics/intent_router_v2_sample_harness.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(text_run.returncode == 0, f"harness text run passes: {text_run.stdout}\n{text_run.stderr}")
    assert_contains(text_run.stdout, "PASS", "text table has PASS rows")
    assert_contains(text_run.stdout, "task_query", "text table includes task query")
    assert_true("FAIL" not in text_run.stdout, "text table has no failures")

    json_run = subprocess.run(
        ["python3", "scripts/diagnostics/intent_router_v2_sample_harness.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(json_run.returncode == 0, f"harness json run passes: {json_run.stderr}")
    rows = json.loads(json_run.stdout)
    assert_true(isinstance(rows, list) and len(rows) >= 20, "json output has sample rows")
    assert_true(all(row.get("pass") for row in rows), "json output all pass")
    assert_true(any(row.get("expected") == "document_ocr" for row in rows), "json output includes OCR sample")


def test_architecture_doc_mentions_arch_03() -> None:
    doc = DOC.read_text(encoding="utf-8")
    assert_contains(doc, "ARCH-03 Shadow Sample Harness", "doc mentions ARCH-03")
    assert_contains(doc, "intent_router_v2_sample_harness.py", "doc mentions harness path")
    assert_contains(doc, "--json", "doc mentions json mode")


def main() -> int:
    test_harness_exists_compiles_and_contains_samples()
    test_harness_runs_text_and_json()
    test_architecture_doc_mentions_arch_03()
    print("PASS: Intent Router v2 sample harness smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
