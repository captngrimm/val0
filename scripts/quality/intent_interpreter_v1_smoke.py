#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.intent_interpreter import interpret_user_intent  # noqa: E402


REQUIRED_KEYS = {
    "intent",
    "confidence",
    "fields",
    "missing_fields",
    "normalized_user_text",
    "route_hint",
    "should_execute",
    "requires_confirmation",
}


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _interpret(text: str, pending_state=None):
    result = interpret_user_intent(text, client_id="client-zero", pending_state=pending_state)
    assert_equal(set(result.keys()), REQUIRED_KEYS, f"strict keys for {text}")
    assert_true(result["should_execute"] is False, f"interpreter never executes: {text}")
    assert_true(isinstance(result["fields"], dict), f"fields dict: {text}")
    assert_true(isinstance(result["missing_fields"], list), f"missing_fields list: {text}")
    return result


def test_intent_examples() -> None:
    cases = {
        "Val, qué tengo hoy?": "agenda_query",
        "Val, qué recordatorios activos tengo?": "reminder_list",
        "Val, qué tareas activas tengo?": "task_list",
        "Val, recuérdame en media hora revisar documentos": "reminder_create",
        "Val, qué sabemos del caso del terreno?": "case_status",
        "Val, qué documentos tengo?": "document_list",
    }
    for phrase, expected in cases.items():
        result = _interpret(phrase)
        assert_equal(result["intent"], expected, phrase)
        assert_true(result["confidence"] >= 0.80, f"confidence for {phrase}")


def test_calendar_create_missing_time() -> None:
    result = _interpret("Val agenda para mañana cita con la broker y mi mamá")
    assert_equal(result["intent"], "calendar_create", "calendar create intent")
    assert_equal(result["fields"].get("date"), "manana", "calendar date extracted")
    assert_equal(result["fields"].get("duration_minutes"), 60, "calendar default duration")
    assert_true("broker" in result["fields"].get("title", ""), "calendar title extracted")
    assert_true("time" in result["missing_fields"], "calendar missing time")
    assert_true(result["requires_confirmation"] is True, "calendar create requires confirmation")


def test_calendar_followup_time() -> None:
    pending = {"intent": "calendar_create", "missing_fields": ["time"]}
    result = _interpret("una y media de la tarde", pending_state=pending)
    assert_equal(result["intent"], "calendar_create_followup", "calendar follow-up intent")
    assert_equal(result["fields"].get("time"), "13:30", "word time follow-up")
    assert_equal(result["missing_fields"], [], "follow-up no missing time")
    assert_true(result["confidence"] >= 0.90, "follow-up confidence")
    assert_true(result["requires_confirmation"] is True, "follow-up remains confirmation path")


def test_task_create_variants_extract_title_without_executing() -> None:
    cases = (
        "Val crea tarea comprar baterías para David y la pesa",
        "Val registra tarea comprar baterías para David y la pesa",
        "Val tengo que comprar baterías para David y la pesa",
    )
    for phrase in cases:
        result = _interpret(phrase)
        assert_equal(result["intent"], "task_create", phrase)
        assert_equal(result["missing_fields"], [], f"task title present: {phrase}")
        assert_true("comprar baterias para david y la pesa" in result["fields"].get("title", ""), f"title extracted: {phrase}")
        assert_equal(result["fields"].get("action"), result["fields"].get("title"), f"action mirrors title: {phrase}")
        assert_true(result["should_execute"] is False, f"interpreter does not create task: {phrase}")


def test_shadow_hook_is_default_off_and_non_routing() -> None:
    assert_true(os.getenv("VAL0_INTENT_INTERPRETER_V1_SHADOW") != "true", "interpreter shadow defaults off")
    bot = _read("bot.py")
    assert_contains(bot, 'VAL0_INTENT_INTERPRETER_V1_SHADOW", "").strip().lower() == "true"', "env-gated interpreter shadow")
    assert_contains(bot, "[INTENT_INTERPRETER_V1_SHADOW]", "interpreter shadow log marker")
    assert_contains(bot, "[INTENT_INTERPRETER_V1_COMPARE]", "interpreter compare log marker")
    assert_contains(bot, "interpret_user_intent(text or \"\"", "interpreter hook calls module")

    start = bot.find("def _maybe_log_intent_interpreter_v1_shadow")
    end = bot.find("\n\ndef _maybe_log_intent_interpreter_v1_actual", start)
    assert_true(start >= 0 and end > start, "interpreter shadow helper found")
    helper = bot[start:end]
    assert_true("await " not in helper, "interpreter shadow helper does not await handlers")
    assert_true("return True" not in helper and "return False" not in helper, "interpreter shadow helper does not handle routes")


def test_module_has_no_execution_imports() -> None:
    source = _read("core/intent_interpreter.py")
    for forbidden in (
        "insert_reminder",
        "create_event",
        "delete_event",
        "write_guarded",
        "send_telegram_reply",
        "Google Calendar",
    ):
        assert_true(forbidden not in source, f"interpreter has no executor reference: {forbidden}")
    assert_contains(source, "should_execute\": False", "interpreter hardcodes no execution")


def main() -> int:
    compile_result = subprocess.run(
        ["./scripts/val0py", "-m", "py_compile", "core/intent_interpreter.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(compile_result.returncode == 0, f"intent interpreter compiles: {compile_result.stderr}")
    test_intent_examples()
    test_calendar_create_missing_time()
    test_calendar_followup_time()
    test_task_create_variants_extract_title_without_executing()
    test_shadow_hook_is_default_off_and_non_routing()
    test_module_has_no_execution_imports()
    print("PASS: Intent Interpreter v1 smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
