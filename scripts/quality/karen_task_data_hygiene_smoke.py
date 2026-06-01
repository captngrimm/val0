#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BOT = (ROOT / "bot.py").read_text(encoding="utf-8")


from core.karen_notes_tasks_visibility import render_karen_tasks_view  # noqa: E402


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


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


def test_reminder_like_task_hidden_when_actual_reminder_exists() -> None:
    rendered = render_karen_tasks_view(
        [
            {
                "id": 1,
                "raw_input": "Val recuérdame el lunes cumpleaños de Miguel",
                "due_date": "",
                "status": "open",
            },
            {
                "id": 2,
                "raw_input": "llamar al juzgado",
                "due_date": "",
                "status": "open",
            },
        ],
        actual_reminders=[{"text": "cumpleaños de Miguel"}],
    )
    assert_contains(rendered, "📌 Tareas pendientes", "task heading")
    assert_contains(rendered, "llamar al juzgado", "normal task remains visible")
    assert_not_contains(rendered, "Val recuérdame el lunes cumpleaños de Miguel", "stale reminder-task hidden")
    assert_contains(rendered, "Oculté posibles recordatorios antiguos guardados como tarea", "hidden stale task note")
    assert_not_contains(rendered, "Esto es lo que tengo guardado del caso del terreno", "no finca/case summary")


def test_deleted_and_completed_auxiliary_tasks_are_hidden() -> None:
    rendered_deleted = render_karen_tasks_view([
        {
            "id": 3,
            "raw_input": "llevar papeles",
            "due_date": "",
            "status": "deleted",
        }
    ])
    assert_not_contains(rendered_deleted, "llevar papeles", "deleted task hidden from active view")

    rendered_aux = render_karen_tasks_view(
        [],
        auxiliary_tasks=[
            {
                "id": "aux:pedir al topografo cotizacion",
                "raw_input": "pedir al topógrafo cotización",
                "due_date": "",
                "status": "open",
                "source_type": "auxiliary_task",
            }
        ],
        completed_tasks=[
            {
                "id": 9,
                "raw_input": "pedir al topógrafo cotización",
                "due_date": "",
                "status": "done",
            }
        ],
    )
    assert_not_contains(rendered_aux, "pedir al topógrafo cotización", "completed auxiliary task hidden")


def test_task_delete_followup_is_not_gcal() -> None:
    followup = function_body("maybe_handle_karen_task_delete_followup")
    assert_contains(followup, "status='deleted'", "delete from list marks task deleted")
    assert_contains(followup, "Listo. Quité esta tarea del listado activo", "delete success copy")
    assert_not_contains(followup, "delete_client_event", "task delete follow-up does not touch gcal")


def main() -> int:
    test_reminder_like_task_hidden_when_actual_reminder_exists()
    test_deleted_and_completed_auxiliary_tasks_are_hidden()
    test_task_delete_followup_is_not_gcal()
    print("PASS: Karen task data hygiene smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
