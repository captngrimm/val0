#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_notes_tasks_visibility import (  # noqa: E402
    auxiliary_task_items_from_lines,
    is_auxiliary_task_row,
    merge_karen_task_items,
    render_karen_case_pendientes_view,
    render_karen_tasks_view,
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _bot_source() -> str:
    return (REPO_ROOT / "bot.py").read_text(encoding="utf-8")


def _function_body(source: str, name: str) -> str:
    for marker in (f"async def {name}", f"def {name}"):
        start = source.find(marker)
        if start >= 0:
            break
    else:
        raise AssertionError(f"missing function {name}")
    next_def = source.find("\ndef ", start + 1)
    next_async_def = source.find("\nasync def ", start + 1)
    stops = [pos for pos in (next_def, next_async_def) if pos > start]
    end = min(stops) if stops else len(source)
    return source[start:end]


def test_auxiliary_task_rendering_and_dedupe() -> None:
    auxiliary = auxiliary_task_items_from_lines([
        "- pedir al topógrafo cotización",
        "- altopógrafo",
        "- cotización",
    ])
    assert_true(len(auxiliary) == 1, "only task-like auxiliary line extracted")
    assert_true(is_auxiliary_task_row(auxiliary[0]), "auxiliary task tagged read-only")

    rendered = render_karen_tasks_view([], auxiliary_tasks=auxiliary)
    assert_contains(rendered, "pedir al topógrafo cotización", "auxiliary task shown")
    assert_contains(rendered, "pendiente auxiliar", "auxiliary task labelled")
    assert_not_contains(rendered, "CLIENT_GROCERY", "no internal filename exposed")
    assert_not_contains(rendered, "/clients/" + "karen", "no internal path exposed")

    duplicate_commitment = [
        {
            "id": 1,
            "raw_input": "pedir al topógrafo cotización",
            "due_date": "",
            "status": "open",
        }
    ]
    merged = merge_karen_task_items(duplicate_commitment, auxiliary)
    assert_true(len(merged) == 1, "duplicate commitment and auxiliary task shown once")
    deduped = render_karen_tasks_view(duplicate_commitment, auxiliary_tasks=auxiliary)
    assert_true(deduped.lower().count("pedir al topógrafo cotización") == 1, "deduped render shows once")


def test_pendientes_include_auxiliary_task() -> None:
    auxiliary = auxiliary_task_items_from_lines(["- pedir al topógrafo cotización"])
    rendered = render_karen_case_pendientes_view(
        tasks=[],
        auxiliary_tasks=auxiliary,
        notes=[
            {
                "note_text": "Nora dijo que hay que revisar el oficio antes de la próxima reunión",
                "source": "karen_explicit_case_note",
                "created_at": "2026-05-26 15:00:00",
            }
        ],
    )
    assert_contains(rendered, "Tareas", "pending view has tasks section")
    assert_contains(rendered, "pedir al topógrafo cotización", "pending view includes auxiliary task")
    assert_not_contains(rendered, "CLIENT_GROCERY", "pending view hides internal filename")


def test_auxiliary_completion_is_read_only() -> None:
    body = _function_body(_bot_source(), "maybe_handle_karen_task_completion")
    assert_contains(body, "is_auxiliary_task_row", "completion checks auxiliary rows")
    assert_contains(body, "pendiente auxiliar", "completion explains auxiliary source")
    assert_contains(body, "todavía no puedo marcarla hecha desde aquí", "completion is read-only for auxiliary")


def main() -> int:
    test_auxiliary_task_rendering_and_dedupe()
    test_pendientes_include_auxiliary_task()
    test_auxiliary_completion_is_read_only()
    print("PASS: Karen task source unification smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
