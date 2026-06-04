#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_workspace import (  # noqa: E402
    CASO_FINCA_WORKSPACE,
    load_caso_finca_workspace_source_labeled,
    looks_like_caso_finca_workspace_request,
    maybe_handle_case_workspace_status,
    render_workspace_status,
)


STALE_PHRASES = ("bajar de peso", "task_high", "memoria pura")
LIVE_FILE = ROOT / "clients" / "karen" / "CLIENT_GROCERY.md"
KAREN_CLIENT_ID = "kar" + "en"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_false(value, label: str) -> None:
    if value:
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


def test_phrase_detection() -> None:
    positive = (
        "Val, abre mi Caso Finca",
        "Val, qué sabemos del Caso Finca?",
        "Val, qué falta confirmar del caso?",
        "Val, qué le pregunto a Nora?",
        "Val, qué sigue con la finca?",
    )
    for phrase in positive:
        assert_true(looks_like_caso_finca_workspace_request(phrase), f"workspace phrase detected: {phrase}")

    negative = (
        "Val, qué tareas activas tengo?",
        "Val, recuérdame mañana llamar a Nora",
        "Val, agenda cita con Nora mañana a las 3",
    )
    for phrase in negative:
        assert_false(looks_like_caso_finca_workspace_request(phrase), f"non-workspace phrase ignored: {phrase}")


def test_renderer_shape_and_safety() -> None:
    case = load_caso_finca_workspace_source_labeled()
    reply = render_workspace_status(case, client_id=KAREN_CLIENT_ID)
    assert_contains(reply, "Tany", "warm Tany opening")
    assert_contains(reply, "Caso Finca", "case title")
    assert_contains(reply, "Lo que sabemos", "what we know section")
    assert_contains(reply, "Qué falta confirmar", "confirmation section")
    assert_contains(reply, "Documentos relacionados", "related documents section")
    assert_contains(reply, "Línea de tiempo / eventos", "timeline section")
    assert_contains(reply, "Preguntas para Nora", "Nora questions section")
    assert_contains(reply, "Pendientes", "pending items section")
    assert_contains(reply, "Próximo paso sugerido", "next step section")
    assert_contains(reply, "source_type=", "source type labels")
    assert_contains(reply, "confidence=", "confidence labels")
    assert_contains(reply, "vfms:20260531_000001", "trusted document id")
    assert_contains(reply, "OCR status: available", "trusted OCR status")
    assert_contains(reply, "Nora/la abogada confirma el efecto legal", "legal boundary")
    assert_contains(reply, "lectura y organizacion; no voy a mover nada", "read-only copy")
    for phrase in STALE_PHRASES:
        assert_not_contains(reply, phrase, f"no stale contamination: {phrase}")
    assert_not_contains(reply, "conclusion legal definitiva", "no fake legal conclusion")


def test_async_route_and_no_live_file_mutation() -> None:
    before = LIVE_FILE.read_text(encoding="utf-8") if LIVE_FILE.exists() else None
    update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, abre mi Caso Finca",
        )
    )
    after = LIVE_FILE.read_text(encoding="utf-8") if LIVE_FILE.exists() else None
    assert_true(handled, "workspace route handles phrase")
    assert_true(bool(update.message.replies), "workspace route replies")
    assert_contains(update.message.replies[0], "Caso Finca", "route reply contains workspace")
    assert_true(before == after, "CLIENT_GROCERY.md untouched by workspace route")


def test_bot_route_order() -> None:
    source = (ROOT / "bot.py").read_text(encoding="utf-8")
    workspace_idx = source.find("KAREN_CASE_WORKSPACE_STATUS_GATE")
    nora_idx = source.find("KAREN_NORA_PREP_PRIORITY_GATE")
    facts_idx = source.find("KAREN_CASE_FACTS_QUERY_GATE")
    status_idx = source.find("KAREN_CASE_STATUS_GATE")
    assert_true(workspace_idx >= 0, "bot has workspace route gate")
    assert_true(nora_idx < 0 or workspace_idx < nora_idx, "workspace beats Nora prep gate")
    assert_true(facts_idx < 0 or workspace_idx < facts_idx, "workspace beats case facts gate")
    assert_true(status_idx < 0 or workspace_idx < status_idx, "workspace beats case status gate")


def main() -> int:
    test_phrase_detection()
    test_renderer_shape_and_safety()
    test_async_route_and_no_live_file_mutation()
    test_bot_route_order()
    print("PASS: Caso Finca read-only workspace smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
