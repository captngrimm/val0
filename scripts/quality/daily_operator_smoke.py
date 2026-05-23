from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.daily_operator import (
    DailyOperatorItem,
    build_daily_operator_snapshot,
    choose_suggested_next_action,
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

    assert_equal(snapshot.suggested_next_action, "Preparar documentos", "conservative next action")
    assert_equal(choose_suggested_next_action(snapshot), "Preparar documentos", "chosen next action")

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
    assert_equal(empty.suggested_next_action, "", "empty no suggested action")
    assert_equal(safe_daily_operator_summary(empty)["warnings"], [], "empty warnings safe")

    print("PASS: daily operator smoke cases passed.")


if __name__ == "__main__":
    main()
