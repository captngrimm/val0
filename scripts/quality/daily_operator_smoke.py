from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.daily_operator import (
    DailyOperatorItem,
    build_daily_operator_snapshot,
    build_daily_operator_snapshot_from_sources,
    choose_suggested_next_action,
    collect_calendar_items,
    collect_document_review_items,
    collect_pending_action_items,
    collect_reminder_items,
    collect_task_items,
    collect_timeline_items,
    filter_today_items,
    normalize_operator_priority,
    normalize_operator_status,
    safe_daily_operator_summary,
)


def assert_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value, label):
    if not value:
        raise AssertionError(label)


def assert_false(value, label):
    if value:
        raise AssertionError(label)


def main():
    assert_equal(normalize_operator_priority("crítico"), "urgent", "critical priority")
    assert_equal(normalize_operator_priority("alta"), "high", "high priority")
    assert_equal(normalize_operator_priority("odd"), "normal", "unknown priority")
    assert_equal(normalize_operator_status("pendiente"), "pending", "pending status")
    assert_equal(normalize_operator_status("revisión"), "needs_review", "review status")
    assert_equal(normalize_operator_status("odd"), "unknown", "unknown status")

    snapshot = build_daily_operator_snapshot(
        client_id="client-a",
        case_id="CASE-1",
        snapshot_date="2026-05-23",
        calendar_items=[
            {
                "id": "gcal-1",
                "title": "Cita con Nora",
                "due_at": "2026-05-23T15:00:00-05:00",
                "source": "google_calendar",
                "priority": "high",
                "status": "pending",
                "metadata": {"raw_path": "/opt/val0/vfms_data/nope"},
            },
            {
                "id": "gcal-2",
                "title": "Cita de mañana",
                "due_at": "2026-05-24T10:00:00-05:00",
                "source": "google_calendar",
            },
        ],
        reminders=[
            DailyOperatorItem(
                item_id="rem-1",
                item_type="reminder",
                title="Preparar documentos",
                due_at="2026-05-23 14:00:00",
                source_type="reminders",
                source_id="rem-1",
                priority="urgent",
                status="today",
            )
        ],
        tasks=[
            {
                "id": "task-1",
                "title": "Llamar al Registro Publico",
                "due_at": "2026-05-25",
                "source": "commitment",
                "priority": "normal",
            }
        ],
        pending_actions=[
            {
                "id": "pending-gcal",
                "title": "Confirmar creación de cita",
                "source": "pending_action",
                "status": "pending",
            }
        ],
        case_priorities=[
            {
                "id": "case-1",
                "title": "Revisar qué falta para Nora",
                "source": "karen_plan",
                "priority": "high",
            }
        ],
        document_items=[
            {
                "id": "doc-1",
                "title": "Foto de escritura necesita revisión",
                "description": "Guardada; necesita OCR/manual review.",
                "source": "telegram_attachment_vfms",
                "status": "needs_review",
                "metadata": {
                    "stored_path": "/opt/val0/vfms_data/raw/private.jpg",
                    "hash": "secret",
                },
            }
        ],
        timeline_items=[
            {
                "id": "timeline-1986",
                "title": "Trámite familiar empezó en 1986",
                "source": "case_timeline",
                "source_id": "note-203",
                "status": "ready",
            }
        ],
        warnings=["Google Calendar read-only fixture"],
        metadata={"fixture": True},
    )

    assert_equal(snapshot.client_id, "client-a", "client preserved")
    assert_equal(snapshot.case_id, "CASE-1", "case preserved")
    assert_equal(len(snapshot.calendar_items), 2, "calendar item count")
    assert_equal(len(snapshot.reminders), 1, "reminder item count")
    assert_equal(len(snapshot.tasks), 1, "task item count")
    assert_equal(len(snapshot.document_items), 1, "document item count")
    assert_equal(snapshot.case_priorities[0].item_type, "case_priority", "case priority separated")
    assert_equal(snapshot.calendar_items[0].item_type, "calendar", "calendar separated")

    today_calendar = filter_today_items(snapshot.calendar_items, snapshot.snapshot_date)
    assert_equal(len(today_calendar), 1, "today calendar filter")
    today_all = filter_today_items(
        list(snapshot.calendar_items) + list(snapshot.reminders),
        snapshot.snapshot_date,
    )
    assert_equal(len(today_all), 2, "today mixed filter")

    assert_equal(snapshot.suggested_next_action, "Atender hoy: Preparar documentos", "today concrete next action")
    assert_equal(choose_suggested_next_action(snapshot), "Atender hoy: Preparar documentos", "chosen next action")

    safe = safe_daily_operator_summary(snapshot)
    assert_equal(safe["client_id"], "client-a", "safe client")
    assert_equal(safe["case_id"], "CASE-1", "safe case")
    assert_equal(safe["calendar_items"][0]["source_type"], "google_calendar", "safe calendar source")
    assert_equal(safe["timeline_items"][0]["source_id"], "note-203", "safe provenance")
    assert_true(safe["document_items"][0]["source_type"], "safe document source")
    assert_false("/opt/val0" in str(safe), "safe summary no raw path")
    assert_false("secret" in str(safe), "safe summary no hash")
    assert_false("metadata" in str(safe), "safe summary no metadata")

    empty = build_daily_operator_snapshot(client_id="client-b", case_id="", snapshot_date=None)
    assert_equal(empty.client_id, "client-b", "empty client preserved")
    assert_equal(empty.suggested_next_action, "Elegir una prioridad concreta para hoy", "empty conservative fallback")
    assert_equal(safe_daily_operator_summary(empty)["warnings"], [], "empty warnings safe")

    calendar_items = collect_calendar_items([
        {"id": "cal-1", "summary": "Audiencia", "start": "2026-05-23T09:00:00-05:00"},
    ])
    assert_equal(len(calendar_items), 1, "collector calendar count")
    assert_equal(calendar_items[0].item_type, "calendar", "collector calendar type")

    reminder_items = collect_reminder_items([
        {"id": "rem-2", "text": "Llevar documentos", "due_at_utc": "2026-05-23 13:00:00", "status": "pending"},
    ])
    task_items = collect_task_items([
        {"id": "task-2", "raw_input": "Llamar a Nora", "due_date": "2026-05-23"},
    ])
    assert_equal(reminder_items[0].source_id, "rem-2", "collector reminder source")
    assert_equal(task_items[0].title, "Llamar a Nora", "collector task title")

    long_raw = (
        "NOTA: Esta es una nota larguísima pegada desde una conversación vieja con demasiados detalles "
        "sobre documentos, vueltas, contexto repetido y texto que no debe ocupar media pantalla en el "
        "modo operador diario porque solo necesitamos una pista accionable."
    )
    cleaned_task = collect_task_items([
        {
            "id": "task-long",
            "raw_input": long_raw,
            "due_date": "2026-05-23",
            "status": "pending",
        }
    ])[0]
    assert_true(cleaned_task.title.startswith("Esta es una nota larguísima"), "long raw note prefix cleaned")
    assert_true(len(cleaned_task.title) <= 96, "long raw note truncated")

    pending_items = collect_pending_action_items([
        {"action_id": "pa-1", "display_summary": "Confirmar cita con Nora", "action_type": "gcal_create_event"},
    ])
    assert_equal(pending_items[0].priority, "high", "pending high priority")
    assert_equal(pending_items[0].item_type, "pending_action", "pending type")

    document_review = collect_document_review_items([
        {
            "document_id": "doc-ocr",
            "filename": "foto_escritura.jpg",
            "status": "ocr_needed",
            "caption": "Foto necesita revisión manual",
            "stored_path": "/opt/val0/vfms_data/raw/foto.jpg",
            "hash": "secret-hash",
            "source": "telegram_attachment_vfms",
        },
        {
            "document_id": "doc-ready",
            "filename": "registro.pdf",
            "status": "ready",
            "source": "telegram_attachment_vfms",
        },
        {
            "document_id": "doc-docx",
            "filename": "resumen.docx",
            "status": "unsupported",
            "source": "telegram_attachment_vfms",
        },
        {
            "document_id": "doc-unknown",
            "filename": "archivo_sin_estado.pdf",
            "status": "weird_status",
            "source": "telegram_attachment_vfms",
        },
    ])
    assert_equal(len(document_review), 3, "document review filters ready")
    assert_equal(document_review[0].status, "ocr_needed", "document ocr status")
    assert_equal(document_review[1].status, "unsupported", "document unsupported status")
    document_safe = safe_daily_operator_summary(build_daily_operator_snapshot(document_items=document_review))
    assert_equal(document_safe["document_items"][0]["status"], "requiere OCR/revisión", "ocr status display")
    assert_equal(document_safe["document_items"][1]["status"], "no extraíble automático", "unsupported status display")
    assert_equal(document_safe["document_items"][2]["status"], "estado por revisar", "unknown status display")
    assert_false("[unknown]" in str(document_safe), "safe summary no unknown bracket noise")
    assert_false("/opt/val0" in str(document_safe), "collector safe no path")

    timeline_items = collect_timeline_items([
        {
            "event_id": "event-1",
            "title": "Juzgado canceló expediente por falta de respuesta",
            "event_date": "2024",
            "source_type": "manual_note",
            "source_id": "note-1",
        }
    ])
    assert_equal(timeline_items[0].item_type, "timeline", "timeline item type")
    assert_equal(timeline_items[0].source_id, "note-1", "timeline provenance")

    composed = build_daily_operator_snapshot_from_sources(
        client_id="client-a",
        case_id="CASE-1",
        snapshot_date="2026-05-23",
        calendar_events=calendar_items,
        reminders=reminder_items,
        tasks=task_items,
        pending_actions=pending_items,
        case_priority_sources=[
            {"id": "case-pri-1", "title": "Revisar faltantes para Nora", "source": "karen_plan"}
        ],
        document_records=document_review,
        timeline_events=timeline_items,
    )
    assert_equal(composed.client_id, "client-a", "composed client")
    assert_equal(composed.case_id, "CASE-1", "composed case")
    assert_equal(len(composed.calendar_items), 1, "composed calendar")
    assert_equal(len(composed.case_priorities), 1, "composed case priority")
    assert_equal(composed.calendar_items[0].item_type, "calendar", "composed agenda separate")
    assert_equal(composed.case_priorities[0].item_type, "case_priority", "composed case separate")
    assert_equal(composed.suggested_next_action, "Atender hoy: Llamar a Nora", "composed dated item first")
    composed_safe = safe_daily_operator_summary(composed)
    assert_false("/opt/val0" in str(composed_safe), "composed safe no raw path")
    assert_false("secret" in str(composed_safe), "composed safe no hash")

    upcoming_concrete = build_daily_operator_snapshot(
        client_id="client-a",
        snapshot_date="2026-05-23",
        reminders=[
            {
                "id": "rem-upcoming",
                "text": "Preparar carpeta para reunión",
                "due_at": "2026-05-23T11:00:00-05:00",
                "priority": "high",
                "status": "pending",
            }
        ],
        case_priorities=[
            {
                "id": "case-vague",
                "title": "Revisar próximos pasos del caso activo",
                "priority": "high",
            }
        ],
    )
    assert_equal(upcoming_concrete.suggested_next_action, "Atender hoy: Preparar carpeta para reunión", "concrete upcoming item preferred")

    future_concrete = build_daily_operator_snapshot(
        client_id="client-a",
        snapshot_date="2026-05-23",
        tasks=[
            {
                "id": "task-future",
                "title": "Cita con Mabel, tema Libro Finca 10082",
                "due_at": "2026-05-24T18:00:00-05:00",
                "priority": "normal",
                "status": "pending",
            }
        ],
        case_priorities=[
            {
                "id": "case-vague-2",
                "title": "Revisar próximos pasos del caso activo",
                "priority": "high",
            }
        ],
    )
    assert_equal(future_concrete.suggested_next_action, "Próximo pendiente: Cita con Mabel, tema Libro Finca 10082", "concrete dated item beats generic case review")

    document_next = build_daily_operator_snapshot(
        client_id="client-a",
        snapshot_date="2026-05-23",
        document_items=[
            {
                "id": "doc-review",
                "title": "foto_escritura_reciente.jpg",
                "status": "ocr_needed",
                "source": "telegram_attachment_vfms",
            }
        ],
        case_priorities=[
            {
                "id": "case-vague-3",
                "title": "Revisar próximos pasos del caso activo",
                "priority": "high",
            }
        ],
    )
    assert_equal(document_next.suggested_next_action, "Revisar documento pendiente: foto_escritura_reciente.jpg", "document review beats generic case review")

    future_beats_overdue = build_daily_operator_snapshot(
        client_id="client-a",
        snapshot_date="2026-05-23",
        reminders=[
            {
                "id": "rem-old",
                "text": "Val, recuérdame llamar al Juzgado Primero de La Chorrera",
                "due_at": "2026-05-10T09:00:00-05:00",
                "priority": "urgent",
                "status": "pending",
            },
            {
                "id": "rem-future",
                "text": "Preparar la cita con Nora",
                "due_at": "2026-05-24T09:00:00-05:00",
                "priority": "normal",
                "status": "pending",
            },
        ],
    )
    assert_equal(future_beats_overdue.suggested_next_action, "Próximo pendiente: Preparar la cita con Nora", "future beats overdue reminder")
    assert_false(future_beats_overdue.suggested_next_action.startswith("Atender hoy: Val, recuérdame"), "overdue does not render as today")
    future_beats_overdue_safe = safe_daily_operator_summary(future_beats_overdue)
    assert_equal(future_beats_overdue_safe["reminders"][0]["status"], "vencido por revisar", "overdue reminder status honest")

    overdue_with_document = build_daily_operator_snapshot(
        client_id="client-a",
        snapshot_date="2026-05-23",
        reminders=[
            {
                "id": "rem-old-2",
                "text": "Val, recuérdame llamar al Juzgado Primero de La Chorrera",
                "due_at": "2026-05-10T09:00:00-05:00",
                "priority": "urgent",
                "status": "pending",
            }
        ],
        document_items=[
            {
                "id": "doc-review-2",
                "title": "foto_nueva_para_revisar.jpg",
                "status": "ocr_needed",
            }
        ],
    )
    assert_equal(overdue_with_document.suggested_next_action, "Revisar documento pendiente: foto_nueva_para_revisar.jpg", "review document beats overdue reminder")

    overdue_only = build_daily_operator_snapshot(
        client_id="client-a",
        snapshot_date="2026-05-23",
        reminders=[
            {
                "id": "rem-old-3",
                "text": "Val, recuérdame llamar al Juzgado Primero de La Chorrera",
                "due_at": "2026-05-10T09:00:00-05:00",
                "priority": "urgent",
                "status": "pending",
            }
        ],
    )
    assert_equal(overdue_only.suggested_next_action, "Pendiente vencido por revisar: Val, recuérdame llamar al Juzgado Primero de La Chorrera", "overdue-only uses overdue language")
    assert_false(overdue_only.suggested_next_action.startswith("Atender hoy:"), "overdue-only never uses today label")

    recent_document_beats_generic = build_daily_operator_snapshot(
        client_id="client-a",
        snapshot_date="2026-05-23",
        document_items=[
            {
                "id": "doc-old-review",
                "title": "foto_anterior.jpg",
                "status": "ocr_needed",
                "due_at": "2026-05-20T10:00:00-05:00",
            },
            {
                "id": "doc-new-review",
                "title": "foto_reciente.jpg",
                "status": "needs_review",
                "due_at": "2026-05-23T08:00:00-05:00",
            },
        ],
        case_priorities=[
            {
                "id": "case-vague-doc",
                "title": "Revisar próximos pasos del caso activo",
                "priority": "high",
            }
        ],
    )
    assert_equal(recent_document_beats_generic.suggested_next_action, "Revisar documento pendiente: foto_reciente.jpg", "recent review document beats generic fallback")

    generic_case_fallback = build_daily_operator_snapshot(
        client_id="client-a",
        snapshot_date="2026-05-23",
        case_priorities=[
            {
                "id": "case-vague-4",
                "title": "Revisar próximos pasos del caso activo",
                "priority": "high",
            }
        ],
    )
    assert_equal(generic_case_fallback.suggested_next_action, "Revisar próximos pasos del caso activo", "generic case review fallback")

    long_suggested = build_daily_operator_snapshot(
        client_id="client-a",
        snapshot_date="2026-05-23",
        reminders=[
            {
                "id": "rem-long",
                "text": (
                    "Preparar la cita con Nora revisando carpeta completa, documentos nuevos, fotos, "
                    "notas, preguntas y todo lo que falte para no llegar perdida"
                ),
                "due_at": "2026-05-23T09:00:00-05:00",
                "priority": "high",
            }
        ],
    )
    assert_true(len(long_suggested.suggested_next_action) <= 112, "suggested action text truncated cleanly")
    assert_true(long_suggested.suggested_next_action.startswith("Atender hoy: Preparar la cita con Nora"), "suggested action keeps useful meaning")

    rendered_boundary_fixture = (
        "Modo: lectura solamente. No creé, cambié ni borré nada.\n"
        "Esto es una organización operativa; no sustituye revisión legal."
    )
    assert_true("lectura solamente" in rendered_boundary_fixture, "read-only boundary preserved fixture")
    assert_true("no sustituye revisión legal" in rendered_boundary_fixture, "legal boundary preserved fixture")

    print("PASS: daily operator smoke cases passed.")


if __name__ == "__main__":
    main()
