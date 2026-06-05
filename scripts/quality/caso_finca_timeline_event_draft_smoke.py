#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_timeline_events import (  # noqa: E402
    PENDING_DRAFT_KEY,
    maybe_handle_case_timeline_event_draft,
    parse_case_timeline_event_draft,
    render_case_timeline_event_draft_preview,
)


KAREN_CLIENT_ID = "kar" + "en"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
STALE_PHRASES = ("bajar de peso", "task_high", "memoria pura")
FORBIDDEN_USER_FACING = ("vfms:", "ID técnico", "caso ganado", "caso perdido", "efecto legal confirmado")


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


def _assert_preview_safe(preview: str, *, label: str) -> None:
    assert_contains(preview, "Tany", f"{label} warm opening")
    assert_contains(preview, "Caso Finca", f"{label} names workspace")
    assert_contains(preview, "No lo he guardado todavía", f"{label} says not saved")
    assert_contains(preview, "¿Lo guardo en Caso Finca?", f"{label} asks confirmation")
    assert_contains(preview, "Nora/la abogada confirma", f"{label} legal boundary")
    assert_contains(preview, "todavía no persiste eventos", f"{label} persistence caveat")
    for phrase in STALE_PHRASES:
        assert_not_contains(preview, phrase, f"{label} avoids stale phrase {phrase}")
    for phrase in FORBIDDEN_USER_FACING:
        assert_not_contains(preview, phrase, f"{label} avoids forbidden copy {phrase}")


def _runtime_replies(text: str) -> list[str]:
    message_id = time.time_ns() % 1_000_000_000
    probe = f"""
import asyncio
import json
from types import SimpleNamespace
import bot

class Msg:
    def __init__(self, text):
        self.text = text
        self.message_id = {message_id}
        self.replies = []
    async def reply_text(self, text, **_kwargs):
        self.replies.append(text)
        return text

class Ctx:
    def __init__(self):
        self.chat_data = {{}}
        self.user_data = {{}}

async def main():
    message = Msg({text!r})
    update = SimpleNamespace(message=message, effective_chat=SimpleNamespace(id=bot.KAREN_CHAT_ID))
    await bot.handle_text(update, Ctx())
    print("===VAL0_RUNTIME_REPLIES===")
    print(json.dumps(message.replies, ensure_ascii=False))

asyncio.run(main())
"""
    proc = subprocess.run(
        ["./scripts/val0py", "-"],
        cwd=ROOT,
        input=probe,
        text=True,
        capture_output=True,
        check=True,
    )
    marker = "===VAL0_RUNTIME_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def test_parser_precisions_and_preview() -> None:
    year = parse_case_timeline_event_draft("Val, registra en Caso Finca que en 2021 pasó X")
    assert_true(year is not None, "year-only draft parsed")
    assert_true(year.event_date == "2021", "year-only date stored as year")
    assert_true(year.event_date_precision == "year_only", "year-only precision")
    assert_true(year.source_type == "user_note", "year-only source is user_note")
    assert_true(year.confirmation_status == "pending_confirmation", "year-only status pending")
    year_preview = render_case_timeline_event_draft_preview(year)
    assert_contains(year_preview, "Precisión: solo año", "year-only precision rendered")
    _assert_preview_safe(year_preview, label="year-only preview")

    exact = parse_case_timeline_event_draft(
        "Val, anota en Caso Finca que el 12 de mayo de 2024 recibimos respuesta del juzgado"
    )
    assert_true(exact is not None, "exact-date draft parsed")
    assert_true(exact.event_date == "2024-05-12", "exact date normalized")
    assert_true(exact.event_date_precision == "exact", "exact precision")
    exact_preview = render_case_timeline_event_draft_preview(exact)
    assert_contains(exact_preview, "Fecha: 2024-05-12", "exact date rendered")
    assert_contains(exact_preview, "Precisión: fecha exacta", "exact precision rendered")
    _assert_preview_safe(exact_preview, label="exact preview")

    unknown = parse_case_timeline_event_draft("Val, agrega a la línea de tiempo que falta confirmar la fecha del oficio")
    assert_true(unknown is not None, "unknown-date draft parsed")
    assert_true(unknown.event_date == "", "unknown date left empty")
    assert_true(unknown.event_date_precision == "unknown", "unknown precision")
    unknown_preview = render_case_timeline_event_draft_preview(unknown)
    assert_contains(unknown_preview, "Fecha: fecha pendiente", "unknown date rendered")
    assert_contains(unknown_preview, "Estado: candidato", "uncertain status rendered")
    _assert_preview_safe(unknown_preview, label="unknown preview")

    document = parse_case_timeline_event_draft("Val, anota que el documento 1 parece ser de 2019")
    assert_true(document is not None, "document-reference draft parsed")
    assert_true(document.event_date == "2019", "document reference year detected")
    assert_true(document.event_date_precision == "year_only", "document reference precision")
    assert_true(document.source_type == "document_metadata", "document reference source type")
    assert_true(document.source_ref == "documento 1", "document reference source ref")
    assert_true(document.confirmation_status == "candidate", "document uncertainty marks candidate")
    document_preview = render_case_timeline_event_draft_preview(document)
    assert_contains(document_preview, "Fuente: referencia a documento 1", "document source rendered safely")
    assert_contains(document_preview, "Cuidado: lo marco como candidato", "candidate caveat rendered")
    _assert_preview_safe(document_preview, label="document preview")


def test_async_handler_preview_only() -> None:
    update = FakeUpdate()
    context = FakeContext()
    handled = asyncio.run(
        maybe_handle_case_timeline_event_draft(
            update,
            context=context,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, registra en Caso Finca que en 2021 pasó X",
        )
    )
    assert_true(handled, "async handler handles timeline draft")
    assert_true(len(update.message.replies) == 1, "async handler sends one reply")
    _assert_preview_safe(update.message.replies[0], label="async preview")
    assert_true(PENDING_DRAFT_KEY in context.chat_data, "draft stored only in volatile chat_data")

    other = FakeUpdate()
    other_context = FakeContext()
    handled_other = asyncio.run(
        maybe_handle_case_timeline_event_draft(
            other,
            context=other_context,
            chat_id=123,
            client_id="other-client",
            text="Val, registra en Caso Finca que en 2021 pasó X",
        )
    )
    assert_true(not handled_other, "non-Karen client ignored")
    assert_true(other.message.replies == [], "non-Karen gets no reply")


def test_runtime_route_and_live_files_untouched() -> None:
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    before_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None

    replies = _runtime_replies("Val, registra en Caso Finca que en 2021 pasó X")
    assert_true(len(replies) == 1, "runtime draft route sends one reply")
    reply = replies[0]
    _assert_preview_safe(reply, label="runtime preview")
    assert_contains(reply, "Precisión: solo año", "runtime year-only precision")
    assert_not_contains(reply, "memoria mágica", "runtime avoids founder limitations")
    assert_not_contains(reply, "no debe prometer", "runtime avoids founder limitations")

    whatnow = _runtime_replies("Val, qué hago ahora?")
    assert_true(len(whatnow) >= 1, "generic whatnow still replies")
    assert_not_contains("\n".join(whatnow), "borrador de evento", "whatnow not routed to timeline draft")
    assert_not_contains("\n".join(whatnow), "¿Lo guardo en Caso Finca?", "whatnow not confirmation preview")

    after_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    after_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(before_folders == after_folders, "CLIENT_FOLDERS.json untouched")

    proc = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
            "--",
            str(LIVE_GROCERY.relative_to(ROOT)),
            str(LIVE_FOLDERS.relative_to(ROOT)),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert_true(proc.stdout.strip() == "", "live client files are not staged")


def main() -> None:
    test_parser_precisions_and_preview()
    test_async_handler_preview_only()
    test_runtime_route_and_live_files_untouched()
    print("PASS caso_finca_timeline_event_draft_smoke")


if __name__ == "__main__":
    main()
