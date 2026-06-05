#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
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
    is_live_timeline_sqlite_enabled,
    maybe_handle_case_timeline_event_confirmation,
    maybe_handle_case_timeline_event_draft,
)


KAREN_CLIENT_ID = "kar" + "en"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
PRODUCTION_DB_CANDIDATE = ROOT / "val0_memory.enc.db"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _read_live_file(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _file_stamp(path: Path) -> tuple[bool, int | None, int | None]:
    if not path.exists():
        return False, None, None
    stat = path.stat()
    return True, stat.st_mtime_ns, stat.st_size


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


def _make_pending_draft(context: FakeContext) -> None:
    update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_timeline_event_draft(
            update,
            context=context,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, registra en Caso Finca que en 2021 se presentó una solicitud al Registro Público",
        )
    )
    assert_true(handled, "timeline event draft route handled")
    assert_true(PENDING_DRAFT_KEY in context.chat_data, "pending draft created")
    assert_true(update.message.replies, "draft preview was rendered")
    assert_contains(update.message.replies[0], "No lo he guardado todavía", "draft preview is not persisted")


def test_live_sqlite_disabled_by_default() -> None:
    assert_true(not is_live_timeline_sqlite_enabled(), "live SQLite timeline persistence disabled by default")


def test_default_confirmation_refuses_live_persistence_and_touches_no_prod_db() -> None:
    before_db = _file_stamp(PRODUCTION_DB_CANDIDATE)
    context = FakeContext()
    _make_pending_draft(context)

    update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_timeline_event_confirmation(
            update,
            context=context,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="sí, guárdalo",
        )
    )
    assert_true(handled, "default confirmation is consumed safely")
    assert_true(len(update.message.replies) == 1, "default refusal sends one reply")
    reply = update.message.replies[0]
    assert_contains(reply, "todavía no estoy guardando eventos reales", "live persistence refused")
    assert_contains(reply, "No voy a tocar memoria real de Karen", "live memory warning")
    assert_contains(reply, "Nora/la abogada confirma efecto legal", "legal boundary")
    assert_true(PENDING_DRAFT_KEY in context.chat_data, "pending draft remains available after refusal")
    assert_true(_file_stamp(PRODUCTION_DB_CANDIDATE) == before_db, "production DB candidate untouched")


def test_non_temp_sqlite_path_is_refused_and_prod_db_untouched() -> None:
    before_db = _file_stamp(PRODUCTION_DB_CANDIDATE)
    context = FakeContext()
    _make_pending_draft(context)
    context.chat_data[SQLITE_STORE_PATH_KEY] = str(PRODUCTION_DB_CANDIDATE)

    update = FakeUpdate()
    try:
        asyncio.run(
            maybe_handle_case_timeline_event_confirmation(
                update,
                context=context,
                chat_id=123,
                client_id=KAREN_CLIENT_ID,
                text="guardar",
            )
        )
    except ValueError as exc:
        assert_contains(str(exc), "outside temp directory", "non-temp DB path refused")
    else:
        raise AssertionError("non-temp SQLite path was not refused")
    assert_true(_file_stamp(PRODUCTION_DB_CANDIDATE) == before_db, "production DB candidate untouched after refusal")


def test_temp_sqlite_confirmation_still_passes() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_live_guard_temp_sqlite_") as tmp:
        db_path = Path(tmp) / "case_timeline_events.sqlite3"
        context = FakeContext()
        context.chat_data[SQLITE_STORE_PATH_KEY] = str(db_path)
        _make_pending_draft(context)

        update = FakeUpdate()
        handled = asyncio.run(
            maybe_handle_case_timeline_event_confirmation(
                update,
                context=context,
                chat_id=123,
                client_id=KAREN_CLIENT_ID,
                text="dale",
            )
        )
        assert_true(handled, "temp SQLite fixture confirmation handled")
        assert_true(len(update.message.replies) == 1, "temp SQLite confirmation sends one reply")
        assert_contains(update.message.replies[0], "fixture/test SQLite temporal", "fixture SQLite mode labeled")
        assert_contains(update.message.replies[0], "No toqué memoria real de Karen", "live memory not touched")
        records = CaseTimelineEventSqliteStore(db_path).list_events(client_id=KAREN_CLIENT_ID, case_id=CASE_ID)
        assert_true(len(records) == 1, "temp SQLite event can be read back")


def test_live_files_and_runtime_route_guard_untouched() -> None:
    before_grocery = _read_live_file(LIVE_GROCERY)
    before_folders = _read_live_file(LIVE_FOLDERS)

    bot_source = (ROOT / "bot.py").read_text(encoding="utf-8")
    assert_not_contains(bot_source, "SQLITE_STORE_PATH_KEY", "bot does not configure SQLite timeline store path")
    assert_not_contains(bot_source, "CASE_TIMELINE_SQLITE_LIVE_ENABLED", "bot does not expose live timeline flag")
    assert_not_contains(bot_source, "val0_memory.enc.db", "bot does not point timeline route at production DB")

    assert_true(_read_live_file(LIVE_GROCERY) == before_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(_read_live_file(LIVE_FOLDERS) == before_folders, "CLIENT_FOLDERS.json untouched")


def test_operator_env_var_does_not_enable_live_persistence() -> None:
    original = os.environ.get("CASE_TIMELINE_SQLITE_LIVE_ENABLED")
    os.environ["CASE_TIMELINE_SQLITE_LIVE_ENABLED"] = "true"
    try:
        assert_true(not is_live_timeline_sqlite_enabled(), "environment variable does not enable live writes yet")
    finally:
        if original is None:
            os.environ.pop("CASE_TIMELINE_SQLITE_LIVE_ENABLED", None)
        else:
            os.environ["CASE_TIMELINE_SQLITE_LIVE_ENABLED"] = original


def main() -> None:
    test_live_sqlite_disabled_by_default()
    test_default_confirmation_refuses_live_persistence_and_touches_no_prod_db()
    test_non_temp_sqlite_path_is_refused_and_prod_db_untouched()
    test_temp_sqlite_confirmation_still_passes()
    test_live_files_and_runtime_route_guard_untouched()
    test_operator_env_var_does_not_enable_live_persistence()
    print("PASS caso_finca_timeline_live_guard_smoke")


if __name__ == "__main__":
    main()
