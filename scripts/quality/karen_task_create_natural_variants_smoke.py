#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.intent_interpreter import interpret_user_intent  # noqa: E402
from core.intent_router_v2 import classify_intent_shadow  # noqa: E402


TASK_PHRASES = (
    "Val crea tarea comprar baterías para David y la pesa",
    "Val registra tarea comprar baterías para David y la pesa",
    "Val tengo que comprar baterías para David y la pesa",
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def _source() -> str:
    return (ROOT / "bot.py").read_text(encoding="utf-8")


def _function_body(source: str, name: str) -> str:
    start = source.find(f"def {name}")
    if start < 0:
        start = source.find(f"async def {name}")
    assert_true(start >= 0, f"{name} found")
    next_def = source.find("\ndef ", start + 1)
    next_async = source.find("\nasync def ", start + 1)
    candidates = [idx for idx in (next_def, next_async) if idx > start]
    end = min(candidates) if candidates else len(source)
    return source[start:end]


def test_interpreter_and_shadow_router_variants() -> None:
    for phrase in TASK_PHRASES:
        interpreted = interpret_user_intent(phrase, client_id="client-zero")
        assert_equal(interpreted["intent"], "task_create", f"interpreter intent: {phrase}")
        assert_equal(interpreted["fields"].get("title"), "comprar baterias para david y la pesa", f"interpreter title: {phrase}")
        assert_true(interpreted["should_execute"] is False, f"interpreter does not execute: {phrase}")

        shadow = classify_intent_shadow(phrase, client_id="client-zero")
        assert_equal(shadow.selected_intent, "task_create", f"shadow router intent: {phrase}")


def test_task_create_beats_draft_followup() -> None:
    source = _source()
    extractor = _function_body(source, "_extract_karen_task_creation_text")
    assert_contains(extractor, "crea|crear", "task extractor supports crea tarea")
    assert_contains(extractor, "tengo\\s+que|debo|hay\\s+que", "task extractor supports tengo que")
    assert_contains(extractor, "recuerdame", "task extractor still avoids reminder commands")

    for function_name in ("_process_text_pipeline", "handle_text"):
        body = _function_body(source, function_name)
        task_idx = body.find("maybe_handle_karen_task_creation")
        draft_idx = body.find("draftfollowup_cmd")
        assert_true(task_idx >= 0, f"{function_name} has task creation route")
        if draft_idx >= 0:
            assert_true(task_idx < draft_idx, f"{function_name} task creation beats draft follow-up")


def main() -> int:
    test_interpreter_and_shadow_router_variants()
    test_task_create_beats_draft_followup()
    print("PASS: Karen natural task-create variant smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
