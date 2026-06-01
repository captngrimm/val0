#!/usr/bin/env python3
from __future__ import annotations

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


def test_task_create_intent() -> None:
    phrases = (
        "Val registra tarea: router prueba completar",
        "registra tarea: comprar leche",
        "guarda tarea: llamar al topógrafo",
        "Val agrega tarea pedir cotización",
    )
    for phrase in phrases:
        decision = classify_intent_shadow(phrase, client_id="client-zero")
        assert_equal(decision.selected_intent, "task_create", phrase)
        assert_true(decision.confidence >= 0.9, f"task_create confidence: {phrase}")


def test_pending_task_delete_context() -> None:
    pending = {"type": "task_delete_clarification"}
    for phrase in ("Eliminarla del listado", "eliminarla", "bórrala", "quitarla", "sácala del listado"):
        decision = classify_intent_shadow(phrase, client_id="client-zero", pending_state=pending)
        assert_equal(decision.selected_intent, "pending_action_reply", phrase)
        assert_contains(decision.reason, "task_delete_clarification", "pending reason")

    no_pending = classify_intent_shadow("Eliminarla del listado", client_id="client-zero")
    assert_equal(no_pending.selected_intent, "llm_fallback", "orphan delete follow-up stays fallback")


def test_shadow_hook_pending_state_is_limited_and_non_routing() -> None:
    bot = (ROOT / "bot.py").read_text(encoding="utf-8")
    for needle in (
        "_intent_router_v2_pending_state_for_shadow",
        "_KAREN_PENDING_TASK_DELETE_CONTEXT",
        '"task_delete_clarification"',
        "pending_state = _intent_router_v2_pending_state_for_shadow(chat_id)",
        '"task_create", "maybe_handle_karen_task_creation"',
    ):
        assert_contains(bot, needle, "bot shadow pending/task_create support")
    start = bot.find("def _intent_router_v2_pending_state_for_shadow")
    end = bot.find("\n\ndef _maybe_log_intent_router_v2_shadow", start)
    assert_true(start >= 0 and end > start, "pending helper body found")
    helper = bot[start:end]
    assert_true("await " not in helper, "pending helper does not call async handlers")
    assert_true("reply_text" not in helper, "pending helper does not reply")


def test_sample_harness_still_passes() -> None:
    result = subprocess.run(
        ["python3", "scripts/diagnostics/intent_router_v2_sample_harness.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"sample harness passes: {result.stdout}\n{result.stderr}")
    assert_contains(result.stdout, "task_create", "sample harness includes task_create")


def main() -> int:
    test_task_create_intent()
    test_pending_task_delete_context()
    test_shadow_hook_pending_state_is_limited_and_non_routing()
    test_sample_harness_still_passes()
    print("PASS: Intent Router v2 pending context smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
