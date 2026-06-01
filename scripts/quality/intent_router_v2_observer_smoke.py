#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.intent_router_v2 import classify_intent_shadow  # noqa: E402
from core.intent_router_v2_observer import (  # noqa: E402
    clear_observations,
    record_actual_intent,
    record_predicted_intent,
    render_intent_observation,
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_observer_helper_compiles_and_compares() -> None:
    result = subprocess.run(
        ["./scripts/val0py", "-m", "py_compile", "core/intent_router_v2_observer.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"observer compiles: {result.stderr}")
    clear_observations()
    decision = classify_intent_shadow("Val que tareas tengo activas?", client_id="client-zero", chat_id=1)
    record_predicted_intent(1, 10, decision)
    obs = record_actual_intent(1, 10, "task_query", "maybe_handle_karen_task_query_hard_gate")
    rendered = render_intent_observation(obs)
    assert_contains(rendered, "predicted=task_query", "render predicted")
    assert_contains(rendered, "actual=task_query", "render actual")
    assert_contains(rendered, "match=True", "render match")


def test_bot_actual_labels_are_shadow_only() -> None:
    bot = _read("bot.py")
    for needle in (
        "[INTENT_ROUTER_V2_ACTUAL]",
        "[INTENT_ROUTER_V2_COMPARE]",
        "record_actual_intent",
        "record_predicted_intent",
        '"task_query", "maybe_handle_karen_task_query_hard_gate"',
        '"gcal_create", "try_appointment_save_natural"',
        '"gcal_delete", "maybe_handle_karen_gcal_event_number_delete"',
        '"document_ocr", "maybe_handle_document_ocr_query"',
        '"agenda_query", "maybe_handle_karen_weekday_agenda_query"',
        '"agenda_query", "maybe_handle_karen_day0_route"',
        '"reminder_create", "handle_reminder_gate"',
        '"reminder_create", "maybe_handle_karen_natural_weekday_reminder"',
        '"destructive_confirmation", "maybe_handle_karen_gcal_create_confirmation_first"',
        '"destructive_confirmation", "maybe_handle_pending_gcal_delete_confirmation"',
        '"destructive_confirmation", "maybe_handle_pending_gcal_appointment_confirmation"',
    ):
        assert_contains(bot, needle, "bot observer labels")

    start = bot.find("def _maybe_log_intent_router_v2_actual")
    end = bot.find("\n# =========================", start)
    assert_true(start >= 0 and end > start, "actual helper body found")
    helper = bot[start:end]
    assert_contains(helper, "_intent_router_v2_shadow_enabled()", "actual helper env-gated")
    assert_true("return True" not in helper and "return False" not in helper, "actual helper does not route")


def test_demo_and_docs() -> None:
    result = subprocess.run(
        ["python3", "scripts/diagnostics/intent_router_v2_observer_demo.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"observer demo runs: {result.stderr}")
    assert_contains(result.stdout, "match=True", "demo has match example")
    assert_contains(result.stdout, "match=False", "demo has mismatch example")
    doc = _read("docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md")
    assert_contains(doc, "ROUTER-04 Predicted vs Actual Handler Labels", "docs mention ROUTER-04")
    assert_contains(doc, "predicted intent against the current legacy handler", "docs explain comparison")


def main() -> int:
    test_observer_helper_compiles_and_compares()
    test_bot_actual_labels_are_shadow_only()
    test_demo_and_docs()
    print("PASS: Intent Router v2 observer smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
