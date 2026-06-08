#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.intent_router_v2 import classify_intent_shadow  # noqa: E402
from scripts.diagnostics.intent_router_v2_sample_harness import SAMPLES  # noqa: E402


CLIENT_ZERO_PATH = Path("clients") / "karen"
PROTECTED = (
    (CLIENT_ZERO_PATH / "CLIENT_FOLDERS.json").as_posix(),
    (CLIENT_ZERO_PATH / "CLIENT_GROCERY.md").as_posix(),
)


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: {actual!r} != {expected!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r}")


def test_sample_harness_contains_adaptive_phrases() -> None:
    sample_inputs = {sample.text for sample in SAMPLES if sample.category == "adaptive_intake"}
    for phrase in (
        "Val, no sé qué necesito",
        "Val, ayúdame a empezar",
        "Val, estoy perdida",
        "Val, tengo demasiadas cosas",
        "Val, no sé por dónde empezar",
        "todo me sirve",
        "trabajo",
        "soy cajera",
        "soy cajera en una tienda de departamento",
        "atiendo caja en una tienda",
        "trabajo en retail",
        "horarios",
        "pendientes",
        "recordatorios",
        "dinero y pagos",
        "cansancio después del turno",
        "tengo clientes que perseguir",
        "tengo papeles regados",
        "ideas para un libro",
        "quiero organizar mi día",
    ):
        assert_true(phrase in sample_inputs, f"adaptive intake sample present: {phrase}")


def test_shadow_classifier_adaptive_labels() -> None:
    cases = (
        ("Val, no sé qué necesito", None, "adaptive_intake_start"),
        ("Val, ayúdame a empezar", None, "adaptive_intake_start"),
        ("Val, estoy perdida", None, "adaptive_intake_start"),
        ("soy cajera en una tienda de departamento", None, "adaptive_intake_followup"),
        ("atiendo caja en una tienda", None, "adaptive_intake_followup"),
        ("trabajo en retail", None, "adaptive_intake_followup"),
        ("tengo clientes que perseguir", None, "adaptive_intake_domain"),
        ("tengo papeles regados", None, "adaptive_intake_domain"),
        ("ideas para un libro", None, "adaptive_intake_domain"),
        ("horarios", {"type": "adaptive_intake_recommendation"}, "adaptive_intake_recommendation"),
        ("pendientes", {"type": "adaptive_intake_recommendation"}, "adaptive_intake_recommendation"),
        ("recordatorios", {"type": "adaptive_intake_recommendation"}, "adaptive_intake_recommendation"),
        ("dinero y pagos", {"type": "adaptive_intake_recommendation"}, "adaptive_intake_recommendation"),
        ("cansancio después del turno", {"type": "adaptive_intake_recommendation"}, "adaptive_intake_recommendation"),
        ("trabajo", {"type": "adaptive_intake_domain"}, "adaptive_intake_domain"),
    )
    for phrase, pending_state, expected in cases:
        decision = classify_intent_shadow(phrase, client_id="client-zero", pending_state=pending_state)
        assert_equal(decision.selected_intent, expected, phrase)
        assert_true(decision.handler_hint == f"shadow:{expected}", f"shadow handler hint: {phrase}")


def test_orphan_short_phrases_stay_fallback() -> None:
    for phrase in ("trabajo", "horarios", "pendientes", "recordatorios", "todo me sirve"):
        decision = classify_intent_shadow(phrase, client_id="client-zero")
        assert_equal(decision.selected_intent, "llm_fallback", f"orphan short phrase stays fallback: {phrase}")
        assert_true(decision.confidence <= 0.35, f"orphan short phrase has low confidence: {phrase}")


def test_sample_harness_runs_with_adaptive_samples() -> None:
    result = subprocess.run(
        ["python3", "scripts/diagnostics/intent_router_v2_sample_harness.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"sample harness passes: {result.stdout}\n{result.stderr}")
    assert_contains(result.stdout, "adaptive_intake", "harness output includes adaptive category")
    assert_true("FAIL" not in result.stdout, "sample harness has no failures")


def test_doc_records_shadow_only_boundary() -> None:
    doc = (ROOT / "docs/architecture/LLM_ROUTER_01B_ADAPTIVE_INTAKE_SHADOW_SAMPLE_EXPANSION.md").read_text(encoding="utf-8")
    for needle in (
        "shadow/sample diagnostics",
        "does not edit `bot.py`",
        "does not route messages through Intent Router v2",
        "adaptive_intake_start",
        "adaptive_intake_domain",
        "adaptive_intake_followup",
        "adaptive_intake_recommendation",
        "Short orphan replies",
        "remain `llm_fallback`",
        "deterministic handlers execute",
        "feature flag default OFF",
    ):
        assert_contains(doc, needle, f"doc boundary {needle}")


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
    test_sample_harness_contains_adaptive_phrases()
    test_shadow_classifier_adaptive_labels()
    test_orphan_short_phrases_stay_fallback()
    test_sample_harness_runs_with_adaptive_samples()
    test_doc_records_shadow_only_boundary()
    test_protected_not_staged()
    print("PASS: LLM router adaptive intake shadow sample smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
