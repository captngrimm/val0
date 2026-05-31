#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOT = (ROOT / "bot.py").read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r}")


def function_body(name: str) -> str:
    for marker in (f"async def {name}", f"def {name}"):
        start = BOT.find(marker)
        if start >= 0:
            break
    else:
        raise AssertionError(f"missing function {name}")
    next_def = BOT.find("\ndef ", start + 1)
    next_async = BOT.find("\nasync def ", start + 1)
    stops = [pos for pos in (next_def, next_async) if pos > start]
    end = min(stops) if stops else len(BOT)
    return BOT[start:end]


def test_successful_delete_marks_visible_context_stale() -> None:
    marker = function_body("_mark_karen_gcal_event_context_stale")
    pending_delete = function_body("maybe_handle_pending_gcal_delete_confirmation")
    formatter = function_body("_format_client_gcal_events_section")

    assert_contains(marker, '"events"] = []', "stale marker clears numbered event list")
    assert_contains(marker, '"stale_after_delete"] = True', "stale marker records post-delete state")
    assert_contains(pending_delete, "_mark_karen_gcal_event_context_stale(chat_id)", "successful delete marks context stale")
    assert_contains(formatter, '"stale_after_delete": False', "agenda refresh clears stale state")


def test_repeated_numbered_delete_requires_fresh_agenda() -> None:
    numbered_delete = function_body("maybe_handle_karen_gcal_event_number_delete")
    assert_contains(numbered_delete, "_is_karen_gcal_event_context_stale", "numbered delete checks stale state first")
    assert_contains(numbered_delete, "La lista de eventos cambió después de borrar uno", "stale copy explains changed list")
    assert_contains(numbered_delete, "qué tengo mañana", "stale copy suggests agenda refresh")
    assert_contains(numbered_delete, "qué tengo para el lunes", "stale copy suggests weekday refresh")
    stale_branch = numbered_delete.split("La lista de eventos cambió después de borrar uno", 1)[1].split("return True", 1)[0]
    assert_not_contains(stale_branch, "create_pending_action", "stale repeat does not create delete pending action")
    assert_not_contains(stale_branch, "delete_client_event", "stale repeat does not delete")
    assert_not_contains(numbered_delete, "Listo, Tany. ¿Qué sigue?", "stale route does not fall through to generic persona")
    assert_not_contains(numbered_delete, "/rmd", "stale route has no legacy slash copy")


def test_failure_copy_is_specific_and_terminal() -> None:
    pending_delete = function_body("maybe_handle_pending_gcal_delete_confirmation")
    assert_contains(pending_delete, "No pude eliminar ese evento", "failure copy is specific")
    assert_contains(pending_delete, "Google Calendar no lo haya encontrado", "failure copy names likely deleted/missing event")
    assert_contains(pending_delete, "No toqué recordatorios ni tareas de Val", "failure copy preserves Val separation")
    assert_contains(pending_delete, "clear_pending_action(action.action_id)", "failure/cancel paths clear pending action")
    assert_not_contains(pending_delete, "Listo, Tany. ¿Qué sigue?", "failure does not fall through to generic persona")


def main() -> int:
    test_successful_delete_marks_visible_context_stale()
    test_repeated_numbered_delete_requires_fresh_agenda()
    test_failure_copy_is_specific_and_terminal()
    print("PASS: Karen GCal delete stale context smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
