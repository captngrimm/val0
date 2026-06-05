#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_timeline_events import (  # noqa: E402
    CASE_ID,
    PENDING_DRAFT_KEY,
    SQLITE_STORE_PATH_KEY,
    CaseTimelineEventSqliteStore,
    maybe_handle_case_timeline_event_confirmation,
    maybe_handle_case_timeline_event_draft,
)


KAREN_CLIENT_ID = "kar" + "en"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
FORBIDDEN_USER_FACING = ("event:", "vfms:", "ID técnico", "efecto legal confirmado", "case_timeline_events")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


class FakeMessage:
    def __init__(self) -> None:
        self.replies: list[str] = []

    async def reply_text(self, text: str, **_kwargs):
        self.replies.append(text)
        return text


class FakeUpdate:
    def __init__(self) -> None:
        self.message = FakeMessage()


class FakeContext:
    def __init__(self) -> None:
        self.chat_data: dict[str, object] = {}


def _assert_sqlite_summary_safe(reply: str, *, label: str) -> None:
    assert_contains(reply, "Evento guardado", f"{label} saved summary")
    assert_contains(reply, "Caso Finca", f"{label} names case")
    assert_contains(reply, "Fecha:", f"{label} includes date")
    assert_contains(reply, "Estado:", f"{label} includes status")
    assert_contains(reply, "Fuente:", f"{label} includes source")
    assert_contains(reply, "Efecto legal: desconocido", f"{label} legal effect unknown")
    assert_contains(reply, "fixture/test SQLite temporal", f"{label} SQLite fixture label")
    assert_contains(reply, "No toqué memoria real de Karen", f"{label} live-data warning")
    assert_contains(reply, "Nora/la abogada confirma efecto legal", f"{label} legal boundary")
    for phrase in FORBIDDEN_USER_FACING:
        assert_not_contains(reply, phrase, f"{label} avoids forbidden user-facing copy {phrase}")


def test_sqlite_fixture_confirmation_writes_temp_db_only() -> None:
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    before_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None

    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_sqlite_confirm_") as tmp:
        db_path = Path(tmp) / "case_timeline_events.sqlite3"
        context = FakeContext()
        context.chat_data[SQLITE_STORE_PATH_KEY] = str(db_path)

        draft_update = FakeUpdate()
        handled_draft = asyncio.run(
            maybe_handle_case_timeline_event_draft(
                draft_update,
                context=context,
                chat_id=123,
                client_id=KAREN_CLIENT_ID,
                text="Val, anota en Caso Finca que el 12 de mayo de 2024 recibimos respuesta del juzgado",
            )
        )
        assert_true(handled_draft, "draft route handled")
        assert_true(PENDING_DRAFT_KEY in context.chat_data, "pending draft created")
        assert_true(not db_path.exists(), "draft preview does not write SQLite DB")

        confirm_update = FakeUpdate()
        handled_confirm = asyncio.run(
            maybe_handle_case_timeline_event_confirmation(
                confirm_update,
                context=context,
                chat_id=123,
                client_id=KAREN_CLIENT_ID,
                text="sí, guárdalo",
            )
        )
        assert_true(handled_confirm, "SQLite fixture confirmation handled")
        assert_true(PENDING_DRAFT_KEY not in context.chat_data, "pending draft cleared after SQLite write")
        assert_true(db_path.exists(), "temp SQLite DB written")
        assert_true(len(confirm_update.message.replies) == 1, "SQLite confirmation sends one reply")
        _assert_sqlite_summary_safe(confirm_update.message.replies[0], label="SQLite confirmation")

        store = CaseTimelineEventSqliteStore(db_path)
        records = store.list_events(client_id=KAREN_CLIENT_ID, case_id=CASE_ID)
        assert_true(len(records) == 1, "saved event can be read back")
        assert_true(records[0].event_date == "2024-05-12", "saved event date persisted")
        assert_true(records[0].event_date_precision == "exact", "saved event precision persisted")
        assert_true(records[0].legal_effect_status == "unknown", "legal effect remains unknown")
        audit = store.audit_rows(event_id=records[0].event_id)
        assert_true(len(audit) == 1, "audit row exists after save")
        assert_true(audit[0]["action"] == "created_from_draft", "audit action")

    after_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    after_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(before_folders == after_folders, "CLIENT_FOLDERS.json untouched")


def test_confirmation_without_pending_or_generic_yes_does_not_save() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_sqlite_confirm_empty_") as tmp:
        db_path = Path(tmp) / "case_timeline_events.sqlite3"
        context = FakeContext()
        context.chat_data[SQLITE_STORE_PATH_KEY] = str(db_path)

        no_pending = FakeUpdate()
        handled = asyncio.run(
            maybe_handle_case_timeline_event_confirmation(
                no_pending,
                context=context,
                chat_id=123,
                client_id=KAREN_CLIENT_ID,
                text="sí",
            )
        )
        assert_true(not handled, "confirmation without pending draft ignored")
        assert_true(no_pending.message.replies == [], "no reply without pending draft")
        assert_true(not db_path.exists(), "no DB created without pending draft")

        context.chat_data["unrelated_pending"] = {"kind": "not_case_timeline"}
        generic_yes = FakeUpdate()
        handled_generic = asyncio.run(
            maybe_handle_case_timeline_event_confirmation(
                generic_yes,
                context=context,
                chat_id=123,
                client_id=KAREN_CLIENT_ID,
                text="sí",
            )
        )
        assert_true(not handled_generic, "generic yes after unrelated context ignored")
        assert_true(not db_path.exists(), "generic yes does not save")


def test_default_mode_refuses_live_persistence_and_non_tmp_refused() -> None:
    context = FakeContext()
    draft_update = FakeUpdate()
    handled_draft = asyncio.run(
        maybe_handle_case_timeline_event_draft(
            draft_update,
            context=context,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, registra en Caso Finca que en 2021 pasó X",
        )
    )
    assert_true(handled_draft, "draft route handled in default mode")
    assert_true(PENDING_DRAFT_KEY in context.chat_data, "pending draft exists in default mode")

    confirm_update = FakeUpdate()
    handled_confirm = asyncio.run(
        maybe_handle_case_timeline_event_confirmation(
            confirm_update,
            context=context,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="dale",
        )
    )
    assert_true(handled_confirm, "default confirmation consumed with refusal")
    refusal = confirm_update.message.replies[0]
    assert_contains(refusal, "todavía no estoy guardando eventos reales", "default refuses live persistence")
    assert_contains(refusal, "No voy a tocar memoria real de Karen", "default live-data warning")
    assert_contains(refusal, "Nora/la abogada confirma efecto legal", "default legal boundary")

    context.chat_data[SQLITE_STORE_PATH_KEY] = str(ROOT / "val0_memory.enc.db")
    non_tmp_update = FakeUpdate()
    try:
        asyncio.run(
            maybe_handle_case_timeline_event_confirmation(
                non_tmp_update,
                context=context,
                chat_id=123,
                client_id=KAREN_CLIENT_ID,
                text="guardar",
            )
        )
    except ValueError as exc:
        assert_contains(str(exc), "outside temp directory", "non-/tmp DB refused")
    else:
        raise AssertionError("non-/tmp SQLite path was not refused")


def main() -> None:
    test_sqlite_fixture_confirmation_writes_temp_db_only()
    test_confirmation_without_pending_or_generic_yes_does_not_save()
    test_default_mode_refuses_live_persistence_and_non_tmp_refused()
    print("PASS caso_finca_timeline_event_sqlite_confirmation_smoke")


if __name__ == "__main__":
    main()
