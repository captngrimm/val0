#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.intent_router_v2 import classify_intent_shadow  # noqa: E402


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: {actual!r} != {expected!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_module_compiles_and_priority_terms_exist() -> None:
    assert_true((ROOT / "core" / "intent_router_v2.py").exists(), "intent router module exists")
    result = subprocess.run(
        ["./scripts/val0py", "-m", "py_compile", "core/intent_router_v2.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"intent router compiles: {result.stderr}")
    source = _read("core/intent_router_v2.py")
    for needle in (
        "classify_intent_shadow",
        "pending action",
        "destructive confirmation",
        "direct utilities",
        "documents/OCR",
        "case/finca",
        "memory capture",
        "LLM fallback",
        "IntentCandidate",
        "IntentDecision",
    ):
        assert_contains(source, needle, "router source priority terms")


def test_classifier_examples() -> None:
    cases = {
        "Val que tareas tengo activas?": "task_query",
        "Val, qué tengo mañana?": "agenda_query",
        "Val, agenda prueba mañana a las 10": "gcal_create",
        "Val, elimina el evento 1": "gcal_delete",
        "Recuérdame en 10 minutos llamar a Mabel": "reminder_create",
        "Val, resume con OCR el último documento": "document_ocr",
        "Val, resume el último documento": "document_summary",
        "Qué tengo del caso del terreno": "case_status",
    }
    for phrase, expected in cases.items():
        decision = classify_intent_shadow(phrase, client_id="client-zero", chat_id=8660371933)
        assert_equal(decision.selected_intent, expected, phrase)
        assert_true(decision.confidence > 0, f"confidence set: {phrase}")


def test_shadow_env_defaults_off_and_hook_is_non_routing() -> None:
    assert_true(os.getenv("VAL0_INTENT_ROUTER_V2_SHADOW") != "true", "shadow env defaults off in smoke")
    bot = _read("bot.py")
    assert_contains(bot, 'VAL0_INTENT_ROUTER_V2_SHADOW", "").strip().lower() == "true"', "env-gated shadow hook")
    assert_contains(bot, "[INTENT_ROUTER_V2_SHADOW]", "shadow log marker")
    assert_contains(bot, "_maybe_log_intent_router_v2_shadow(text, chat_id=chat_id, client_id=client_id, message_id=", "hook called in text paths")

    start = bot.find("def _maybe_log_intent_router_v2_shadow")
    end = bot.find("\n# =========================", start)
    assert_true(start >= 0 and end > start, "shadow helper body found")
    helper = bot[start:end]
    assert_contains(helper, "classify_intent_shadow", "helper classifies")
    assert_contains(helper, "logger.info", "helper logs")
    assert_true("await " not in helper, "shadow helper does not await handlers")
    assert_true("return True" not in helper and "return False" not in helper, "shadow helper does not signal route handling")


def test_architecture_doc_mentions_arch_02() -> None:
    doc = _read("docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md")
    for needle in (
        "ARCH-02 Shadow Skeleton",
        "default OFF",
        "VAL0_INTENT_ROUTER_V2_SHADOW=true",
        "does not route messages",
        "predicted intent vs actual handler",
    ):
        assert_contains(doc, needle, "architecture doc ARCH-02 section")


def main() -> int:
    test_module_compiles_and_priority_terms_exist()
    test_classifier_examples()
    test_shadow_env_defaults_off_and_hook_is_non_routing()
    test_architecture_doc_mentions_arch_02()
    print("PASS: Intent Router v2 shadow smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
