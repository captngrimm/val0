#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_timeline_events import (  # noqa: E402
    PENDING_DRAFT_KEY,
    STORE_PATH_KEY,
    CaseTimelineEventJsonStore,
    maybe_handle_case_timeline_event_confirmation,
    maybe_handle_case_timeline_event_draft,
)


KAREN_CLIENT_ID = "kar" + "en"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
FORBIDDEN_USER_FACING = ("event:", "vfms:", "ID técnico", "efecto legal confirmado", "caso ganado")


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


def _assert_added_summary_safe(reply: str, *, label: str) -> None:
    assert_contains(reply, "Evento guardado", f"{label} saved summary")
    assert_contains(reply, "Caso Finca", f"{label} names case")
    assert_contains(reply, "Fecha:", f"{label} includes date")
    assert_contains(reply, "Estado:", f"{label} includes status")
    assert_contains(reply, "Fuente:", f"{label} includes source")
    assert_contains(reply, "Efecto legal: desconocido", f"{label} legal effect unknown")
    assert_contains(reply, "fixture/test temporal", f"{label} fixture storage warning")
    assert_contains(reply, "No toqué memoria real de Karen", f"{label} live-data warning")
    assert_contains(reply, "Nora/la abogada confirma efecto legal", f"{label} legal boundary")
    for phrase in FORBIDDEN_USER_FACING:
        assert_not_contains(reply, phrase, f"{label} avoids forbidden user-facing copy {phrase}")


def test_fixture_confirmation_writes_temp_store_only() -> None:
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    before_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None

    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_confirm_") as tmp:
        store_path = Path(tmp) / "case_timeline_events.json"
        context = FakeContext()
        context.chat_data[STORE_PATH_KEY] = str(store_path)
        draft_update = FakeUpdate()

        handled_draft = asyncio.run(
            maybe_handle_case_timeline_event_draft(
                draft_update,
                context=context,
                chat_id=123,
                client_id=KAREN_CLIENT_ID,
                text="Val, registra en Caso Finca que en 2021 se presentó una solicitud al Registro Público",
            )
        )
        assert_true(handled_draft, "draft route handled")
        assert_true(PENDING_DRAFT_KEY in context.chat_data, "pending draft created")
        assert_true(not store_path.exists(), "draft preview does not write store")

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
        assert_true(handled_confirm, "confirmation handled")
        assert_true(PENDING_DRAFT_KEY not in context.chat_data, "pending draft cleared after fixture write")
        assert_true(store_path.exists(), "fixture store written")
        assert_true(len(confirm_update.message.replies) == 1, "confirmation sends one reply")
        _assert_added_summary_safe(confirm_update.message.replies[0], label="fixture confirmation")

        records = CaseTimelineEventJsonStore(store_path).list_events()
        assert_true(len(records) == 1, "stored event can be read back")
        assert_true(records[0].event_date == "2021", "stored event date persisted")
        assert_true(records[0].event_date_precision == "year_only", "stored event precision persisted")
        assert_true(records[0].legal_effect_status == "unknown", "legal effect remains unknown")
        assert_true(records[0].audit_trail and records[0].audit_trail[0]["action"] == "created_from_draft", "create audit kept")

    after_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    after_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(before_folders == after_folders, "CLIENT_FOLDERS.json untouched")


def test_confirmation_without_pending_does_not_save() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_confirm_empty_") as tmp:
        store_path = Path(tmp) / "case_timeline_events.json"
        context = FakeContext()
        context.chat_data[STORE_PATH_KEY] = str(store_path)
        update = FakeUpdate()
        handled = asyncio.run(
            maybe_handle_case_timeline_event_confirmation(
                update,
                context=context,
                chat_id=123,
                client_id=KAREN_CLIENT_ID,
                text="sí",
            )
        )
        assert_true(not handled, "confirmation without pending draft ignored")
        assert_true(update.message.replies == [], "no reply without pending draft")
        assert_true(not store_path.exists(), "no store created without pending draft")


def test_default_mode_refuses_live_persistence() -> None:
    context = FakeContext()
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
    assert_true(handled_confirm, "default confirmation is consumed with refusal")
    assert_true(len(confirm_update.message.replies) == 1, "default refusal sends one reply")
    refusal = confirm_update.message.replies[0]
    assert_contains(refusal, "todavía no estoy guardando eventos reales", "default refuses live persistence")
    assert_contains(refusal, "No voy a tocar memoria real de Karen", "default live-data warning")
    assert_contains(refusal, "Nora/la abogada confirma efecto legal", "default legal boundary")
    assert_true(PENDING_DRAFT_KEY in context.chat_data, "pending draft retained after refusal")
    for phrase in FORBIDDEN_USER_FACING:
        assert_not_contains(refusal, phrase, f"default refusal avoids forbidden copy {phrase}")


def test_non_confirmation_or_non_karen_ignored() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_confirm_ignore_") as tmp:
        store_path = Path(tmp) / "case_timeline_events.json"
        context = FakeContext()
        context.chat_data[STORE_PATH_KEY] = str(store_path)
        context.chat_data[PENDING_DRAFT_KEY] = {
            "case_id": "CASE:KAREN-LAND-001",
            "workspace_title": "Caso Finca",
            "title": "Evento",
            "description": "Evento",
            "event_date": "2021",
            "event_date_precision": "year_only",
            "source_type": "user_note",
            "source_ref": "",
            "confirmation_status": "pending_confirmation",
            "confidence": "medium",
            "legal_effect_status": "unknown",
            "created_by": "user",
        }

        update = FakeUpdate()
        handled = asyncio.run(
            maybe_handle_case_timeline_event_confirmation(
                update,
                context=context,
                chat_id=123,
                client_id=KAREN_CLIENT_ID,
                text="qué hago ahora",
            )
        )
        assert_true(not handled, "non-confirmation ignored")
        assert_true(not store_path.exists(), "non-confirmation does not save")

        other_update = FakeUpdate()
        handled_other = asyncio.run(
            maybe_handle_case_timeline_event_confirmation(
                other_update,
                context=context,
                chat_id=123,
                client_id="other-client",
                text="sí",
            )
        )
        assert_true(not handled_other, "non-Karen confirmation ignored")
        assert_true(not store_path.exists(), "non-Karen does not save")


def main() -> None:
    test_fixture_confirmation_writes_temp_store_only()
    test_confirmation_without_pending_does_not_save()
    test_default_mode_refuses_live_persistence()
    test_non_confirmation_or_non_karen_ignored()
    print("PASS caso_finca_timeline_event_confirmation_smoke")


if __name__ == "__main__":
    main()
