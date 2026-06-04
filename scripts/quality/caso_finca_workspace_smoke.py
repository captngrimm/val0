#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_workspace import (  # noqa: E402
    CASO_FINCA_WORKSPACE,
    detect_case_workspace_view,
    extract_case_workspace_document_summary_number,
    get_workspace_document_by_number,
    load_caso_finca_workspace_source_labeled,
    looks_like_caso_finca_workspace_request,
    maybe_handle_case_workspace_status,
    render_workspace_compact_status,
    render_workspace_document_number_summary,
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
        "Val, muéstrame documentos del Caso Finca",
        "Val, muéstrame preguntas para Nora",
        "Val, muéstrame pendientes del Caso Finca",
        "Val, muéstrame todo el Caso Finca",
        "Val, muéstrame detalles técnicos de los documentos del Caso Finca",
        "Val, resume el documento 1",
        "resume documento 3",
    )
    for phrase in positive:
        assert_true(looks_like_caso_finca_workspace_request(phrase), f"workspace phrase detected: {phrase}")
    assert_true(detect_case_workspace_view("Val, abre mi Caso Finca") == "compact", "open phrase selects compact view")
    assert_true(detect_case_workspace_view("Val, muéstrame documentos del Caso Finca") == "documents", "documents view selected")
    assert_true(
        detect_case_workspace_view("Val, muéstrame detalles técnicos de los documentos del Caso Finca") == "document_details",
        "document technical details view selected",
    )
    assert_true(detect_case_workspace_view("Val, muéstrame preguntas para Nora") == "questions", "questions view selected")
    assert_true(detect_case_workspace_view("Val, muéstrame pendientes del Caso Finca") == "pending", "pending view selected")
    assert_true(detect_case_workspace_view("Val, muéstrame todo el Caso Finca") == "full", "full view selected")
    assert_true(detect_case_workspace_view("Val, resume el documento 1") == "document_summary", "document number summary selected")
    assert_true(extract_case_workspace_document_summary_number("Val, resume el documento 1") == 1, "extract document number 1")
    assert_true(extract_case_workspace_document_summary_number("resume documento 3") == 3, "extract document number 3")
    assert_true(extract_case_workspace_document_summary_number("Val, resume el documento dos") == 2, "extract document number word")

    negative = (
        "Val, qué tareas activas tengo?",
        "Val, recuérdame mañana llamar a Nora",
        "Val, agenda cita con Nora mañana a las 3",
    )
    for phrase in negative:
        assert_false(looks_like_caso_finca_workspace_request(phrase), f"non-workspace phrase ignored: {phrase}")


def test_renderer_shape_and_safety() -> None:
    case = load_caso_finca_workspace_source_labeled()
    compact = render_workspace_compact_status(case, client_id=KAREN_CLIENT_ID)
    assert_contains(compact, "Tany, abrí tu Caso Finca", "compact warm opening")
    assert_contains(compact, "📁 Estado rápido", "compact status header")
    assert_contains(compact, "Uno ya tiene lectura OCR disponible", "compact OCR explanation")
    assert_contains(compact, "Nora/la abogada confirma el efecto legal", "compact legal boundary")
    assert_contains(compact, '"Val, muéstrame documentos del Caso Finca"', "compact documents command")
    assert_contains(compact, '"Val, muéstrame todo el Caso Finca"', "compact full command")
    assert_not_contains(compact, "ID técnico del documento", "compact avoids technical document IDs")
    assert_not_contains(compact, "Fuente:", "compact avoids detailed source labels")
    assert_not_contains(compact, "candidato pendiente", "compact avoids dense candidate labels")

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
    assert_contains(reply, "Fuente del tablero: datos registrados y auditoría de documentos", "friendly board source")
    assert_contains(reply, "Fuente: auditoría de documentos", "friendly source labels")
    assert_contains(reply, "Confianza: alta", "friendly confidence labels")
    assert_contains(reply, "Estado: requiere revisión legal", "friendly status labels")
    assert_contains(reply, "vfms:20260531_000001", "trusted document id")
    assert_contains(reply, "ID técnico del documento: vfms:20260531_000001", "trusted document id label")
    assert_contains(reply, "OCR: disponible", "trusted OCR status")
    assert_contains(reply, "Siguiente paso seguro:", "safe next action in Spanish")
    assert_contains(reply, 'Pedir: "Val, resume con OCR el último documento"', "quoted OCR command example")
    assert_contains(reply, "Nora/la abogada confirma efecto legal", "legal boundary")
    assert_contains(reply, "lectura y organizacion; no voy a mover nada", "read-only copy")
    for label in (
        "fixture/source-labeled v1",
        "source_type=",
        "source_name=",
        "confidence=",
        "status=",
        "document_id:",
        "OCR status:",
        "safe next action:",
    ):
        assert_not_contains(reply, label, f"no raw/internal label: {label}")
    for phrase in STALE_PHRASES:
        assert_not_contains(reply, phrase, f"no stale contamination: {phrase}")
    assert_not_contains(reply, "conclusion legal definitiva", "no fake legal conclusion")

    doc1 = get_workspace_document_by_number(case, 1)
    doc2 = get_workspace_document_by_number(case, 2)
    assert_true(doc1 is not None and doc1.document_id == "vfms:20260531_000001", "document 1 maps to trusted OCR attachment")
    assert_true(doc2 is not None and doc2.document_id == "vfms:20260511_000012", "document 2 maps to trusted summary candidate")
    doc1_reply = render_workspace_document_number_summary(case, number=1, client_id=KAREN_CLIENT_ID)
    assert_contains(doc1_reply, "vfms:20260531_000001", "document 1 summary includes mapped id")
    assert_contains(doc1_reply, "OCR: disponible", "document 1 summary shows OCR availability")
    assert_contains(doc1_reply, "Resumen seguro v1", "document 1 summary is safe v1")
    assert_contains(doc1_reply, "Nora/la abogada confirma efecto legal", "document summary legal boundary")
    assert_not_contains(doc1_reply, "JUZGADO PRIMERO DE CIRCUITO", "document summary avoids raw private body")
    doc2_reply = render_workspace_document_number_summary(case, number=2, client_id=KAREN_CLIENT_ID)
    assert_contains(doc2_reply, "vfms:20260511_000012", "document 2 summary includes mapped id")
    assert_contains(doc2_reply, "todavía no tengo una lectura/OCR usable", "document 2 unavailable summary copy")
    missing_reply = render_workspace_document_number_summary(case, number=99, client_id=KAREN_CLIENT_ID)
    assert_contains(missing_reply, "no encuentro el documento 99", "out-of-range graceful error")


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
    assert_true(len(update.message.replies) == 1, "default workspace route is compact, not chunked")
    assert_contains(update.message.replies[0], "Caso Finca", "route reply contains workspace")
    assert_contains(update.message.replies[0], "📁 Estado rápido", "default route returns compact first screen")
    assert_not_contains(update.message.replies[0], "Documentos relacionados", "default route does not dump full workspace")
    assert_not_contains(update.message.replies[0], "ID técnico del documento", "default route avoids technical details")
    assert_true(before == after, "CLIENT_GROCERY.md untouched by workspace route")

    section_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            section_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, muéstrame documentos del Caso Finca",
        )
    )
    assert_true(handled, "documents section route handled")
    assert_contains(section_update.message.replies[0], "📄 Documentos del Caso Finca", "documents section rendered")
    assert_contains(section_update.message.replies[0], "Estado simple:", "documents section uses compact cards")
    assert_contains(section_update.message.replies[0], "Lectura:", "documents section shows plain reading availability")
    assert_contains(section_update.message.replies[0], "Siguiente paso:", "documents section gives one command")
    assert_contains(section_update.message.replies[0], "detalles técnicos", "documents section points to technical details")
    assert_not_contains(section_update.message.replies[0], "ID técnico del documento", "default documents section hides technical ids")
    assert_not_contains(section_update.message.replies[0], "Fuente: auditoría de documentos", "default documents section hides source metadata")

    details_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            details_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, muéstrame detalles técnicos de los documentos del Caso Finca",
        )
    )
    assert_true(handled, "document technical details route handled")
    assert_contains(details_update.message.replies[0], "📄 Detalles técnicos de documentos", "technical details section rendered")
    assert_contains(details_update.message.replies[0], "ID técnico del documento", "technical details include document id")
    assert_contains(details_update.message.replies[0], "Fuente: auditoría de documentos", "technical details include friendly source")

    doc_summary_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            doc_summary_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, resume el documento 1",
        )
    )
    assert_true(handled, "document number summary route handled")
    assert_contains(doc_summary_update.message.replies[0], "vfms:20260531_000001", "route maps document 1 id")
    assert_contains(doc_summary_update.message.replies[0], "Resumen seguro v1", "route returns safe summary")
    assert_not_contains(doc_summary_update.message.replies[0], "JUZGADO PRIMERO DE CIRCUITO", "route avoids raw private body")

    doc_summary_update_2 = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            doc_summary_update_2,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="resume documento 3",
        )
    )
    assert_true(handled, "document number summary route handles no-prefix phrase")
    assert_contains(doc_summary_update_2.message.replies[0], "documento 3", "route responds for document 3")

    missing_doc_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            missing_doc_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, resume el documento 99",
        )
    )
    assert_true(handled, "out-of-range document number route handled")
    assert_contains(missing_doc_update.message.replies[0], "no encuentro el documento 99", "out-of-range graceful route reply")

    questions_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            questions_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, muéstrame preguntas para Nora",
        )
    )
    assert_true(handled, "questions section route handled")
    assert_contains(questions_update.message.replies[0], "❓ Preguntas para Nora", "questions section rendered")

    pending_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            pending_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, muéstrame pendientes del Caso Finca",
        )
    )
    assert_true(handled, "pending section route handled")
    assert_contains(pending_update.message.replies[0], "📌 Pendientes del Caso Finca", "pending section rendered")

    full_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            full_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, muéstrame todo el Caso Finca",
        )
    )
    assert_true(handled, "full route handled")
    assert_true(len(full_update.message.replies) >= 2, "full route still replies in chunks")
    assert_contains(full_update.message.replies[0], "[1/", "full route keeps chunk prefix")


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
