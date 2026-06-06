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
    render_workspace_timeline_gaps_section,
    render_workspace_timeline_section,
)
from core.founder_intro import INTENT_LIMITATIONS, normalize_founder_intro_intent, render_founder_intro_response  # noqa: E402


STALE_PHRASES = ("bajar de peso", "task_high", "memoria pura")
FOUNDER_LIMITATION_PHRASES = ("memoria mágica", "no debe prometer")
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


def _runtime_replies(text: str) -> list[str]:
    message_id = time.time_ns() % 1_000_000_000
    probe = f"""
import asyncio
import json
from types import SimpleNamespace
import bot

bot.mark_processed_event_once = lambda *_args, **_kwargs: True
bot._audit = lambda *_args, **_kwargs: None

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


def _runtime_sequence_replies(texts: list[str]) -> list[list[str]]:
    message_id = time.time_ns() % 1_000_000_000
    probe = f"""
import asyncio
import json
from types import SimpleNamespace
import bot

bot.mark_processed_event_once = lambda *_args, **_kwargs: True
bot._audit = lambda *_args, **_kwargs: None

class Msg:
    def __init__(self, text, message_id):
        self.text = text
        self.message_id = message_id
        self.replies = []
    async def reply_text(self, text, **_kwargs):
        self.replies.append(text)
        return text

class Ctx:
    def __init__(self):
        self.chat_data = {{}}
        self.user_data = {{}}

async def main():
    ctx = Ctx()
    all_replies = []
    for idx, text in enumerate({texts!r}, start=0):
        message = Msg(text, {message_id} + idx)
        update = SimpleNamespace(message=message, effective_chat=SimpleNamespace(id=bot.KAREN_CHAT_ID))
        await bot.handle_text(update, ctx)
        all_replies.append(message.replies)
    print("===VAL0_RUNTIME_SEQUENCE_REPLIES===")
    print(json.dumps(all_replies, ensure_ascii=False))

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
    marker = "===VAL0_RUNTIME_SEQUENCE_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime sequence probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def test_phrase_detection() -> None:
    positive = (
        "Val, abre mi Caso Finca",
        "Val, abre lo de la finca",
        "Val, qué sabemos del Caso Finca?",
        "Val, qué falta confirmar del caso?",
        "Val, qué le pregunto a Nora?",
        "Val, qué sigue con la finca?",
        "Val, muéstrame documentos del Caso Finca",
        "Val, enséñame los papeles de la finca",
        "Val, muéstrame preguntas para Nora",
        "Val, muéstrame pendientes del Caso Finca",
        "Val, muéstrame la línea de tiempo del Caso Finca",
        "Val, qué eventos tengo registrados del Caso Finca?",
        "Val, qué pasó primero en el Caso Finca?",
        "Val, qué falta ordenar por fecha?",
        "Val, qué eventos faltan confirmar del Caso Finca?",
        "Val, muéstrame todo el Caso Finca",
        "Val, muéstrame detalles técnicos de los documentos del Caso Finca",
        "Val, resume el documento 1",
        "Val, dime qué dice el primer documento",
        "resume documento 3",
    )
    for phrase in positive:
        assert_true(looks_like_caso_finca_workspace_request(phrase), f"workspace phrase detected: {phrase}")
    assert_true(detect_case_workspace_view("Val, abre mi Caso Finca") == "compact", "open phrase selects compact view")
    assert_true(detect_case_workspace_view("Val, abre lo de la finca") == "compact", "natural finca open alias selects compact view")
    assert_true(detect_case_workspace_view("Val, muéstrame documentos del Caso Finca") == "documents", "documents view selected")
    assert_true(detect_case_workspace_view("Val, enséñame los papeles de la finca") == "documents", "natural papeles alias selects documents")
    assert_true(
        detect_case_workspace_view("Val, muéstrame detalles técnicos de los documentos del Caso Finca") == "document_details",
        "document technical details view selected",
    )
    assert_true(detect_case_workspace_view("Val, muéstrame preguntas para Nora") == "questions", "questions view selected")
    assert_true(detect_case_workspace_view("Val, muéstrame pendientes del Caso Finca") == "pending", "pending view selected")
    assert_true(detect_case_workspace_view("Val, muéstrame la línea de tiempo del Caso Finca") == "timeline", "timeline view selected")
    assert_true(detect_case_workspace_view("Val, qué eventos tengo registrados del Caso Finca?") == "timeline", "events view selected")
    assert_true(detect_case_workspace_view("Val, qué pasó primero en el Caso Finca?") == "timeline", "first event view selected")
    assert_true(detect_case_workspace_view("Val, qué falta ordenar por fecha?") == "timeline_gaps", "timeline gaps view selected")
    assert_true(detect_case_workspace_view("Val, qué eventos faltan confirmar del Caso Finca?") == "timeline_gaps", "timeline event confirmation gaps selected")
    assert_true(detect_case_workspace_view("Val, muéstrame todo el Caso Finca") == "full", "full view selected")
    assert_true(detect_case_workspace_view("Val, resume el documento 1") == "document_summary", "document number summary selected")
    assert_true(detect_case_workspace_view("Val, dime qué dice el primer documento") == "document_summary", "natural first document summary selected")
    assert_true(extract_case_workspace_document_summary_number("Val, resume el documento 1") == 1, "extract document number 1")
    assert_true(extract_case_workspace_document_summary_number("Val, dime qué dice el primer documento") == 1, "extract first document natural alias")
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
    assert_contains(compact, '"Val, muéstrame la línea de tiempo del Caso Finca"', "compact timeline command")
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
    assert_contains(doc1_reply, "revisé la lectura disponible", "document 1 uses OCR/text-backed path")
    assert_contains(doc1_reply, "Lo importante:", "document 1 has useful OCR-backed summary")
    assert_contains(doc1_reply, "Qué falta confirmar:", "document 1 has confirmation section")
    assert_contains(doc1_reply, "Preguntas para Nora:", "document 1 has Nora questions")
    assert_contains(doc1_reply, "Nora/la abogada confirma efecto legal", "document summary legal boundary")
    assert_not_contains(doc1_reply, "ID técnico del documento", "document 1 normal summary hides technical ID label")
    assert_not_contains(doc1_reply, "vfms:", "document 1 normal summary hides VFMS ID")
    assert_not_contains(doc1_reply, "JUZGADO PRIMERO DE CIRCUITO", "document summary avoids raw private body")
    assert_not_contains(doc1_reply, "Ricardo Arturo Juncá García", "document summary avoids raw party dump")
    doc2_reply = render_workspace_document_number_summary(case, number=2, client_id=KAREN_CLIENT_ID)
    assert_contains(doc2_reply, "todavía no tengo una lectura/OCR usable", "document 2 unavailable summary copy")
    assert_not_contains(doc2_reply, "ID técnico del documento", "document 2 normal summary hides technical ID label")
    assert_not_contains(doc2_reply, "vfms:", "document 2 normal summary hides VFMS ID")
    missing_reply = render_workspace_document_number_summary(case, number=99, client_id=KAREN_CLIENT_ID)
    assert_contains(missing_reply, "no encuentro el documento 99", "out-of-range graceful error")

    timeline = render_workspace_timeline_section(case, client_id=KAREN_CLIENT_ID)
    assert_contains(timeline, "🧭 Línea de tiempo", "timeline header")
    assert_contains(timeline, "Eventos confirmados en Val", "timeline confirmed section")
    assert_contains(timeline, "Eventos por confirmar", "timeline candidate section")
    assert_contains(timeline, "Huecos / falta fecha", "timeline gaps section")
    assert_contains(timeline, "Preguntas para Nora", "timeline Nora questions")
    assert_contains(timeline, "Próximo paso sugerido", "timeline next step")
    assert_contains(timeline, "fecha pendiente", "timeline does not invent dates")
    assert_contains(timeline, "Nora/la abogada confirma efecto legal", "timeline legal boundary")
    assert_not_contains(timeline, "vfms:", "timeline hides internal IDs")
    assert_not_contains(timeline, "JUZGADO PRIMERO DE CIRCUITO", "timeline avoids raw OCR body")

    timeline_gaps = render_workspace_timeline_gaps_section(case, client_id=KAREN_CLIENT_ID)
    assert_contains(timeline_gaps, "Huecos / falta fecha", "timeline gaps header")
    assert_contains(timeline_gaps, "Eventos por confirmar", "timeline gaps candidate section")
    assert_contains(timeline_gaps, "Qué fecha debo usar", "timeline gaps Nora question")
    assert_contains(timeline_gaps, "Nora/la abogada confirma efecto legal", "timeline gaps legal boundary")


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

    alias_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            alias_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, abre lo de la finca",
        )
    )
    assert_true(handled, "natural finca alias route handled")
    assert_contains(alias_update.message.replies[0], "Tany, abrí tu Caso Finca", "natural finca alias opens compact workspace")

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

    papers_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            papers_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, enséñame los papeles de la finca",
        )
    )
    assert_true(handled, "natural papeles alias route handled")
    assert_contains(papers_update.message.replies[0], "📄 Documentos del Caso Finca", "papeles alias renders document list")

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
    assert_contains(doc_summary_update.message.replies[0], "Lo importante:", "route returns OCR-backed safe summary")
    assert_contains(doc_summary_update.message.replies[0], "Preguntas para Nora:", "route returns Nora questions")
    assert_not_contains(doc_summary_update.message.replies[0], "ID técnico del documento", "normal route hides technical ID label")
    assert_not_contains(doc_summary_update.message.replies[0], "vfms:", "normal route hides VFMS ID")
    assert_not_contains(doc_summary_update.message.replies[0], "JUZGADO PRIMERO DE CIRCUITO", "route avoids raw private body")

    first_doc_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            first_doc_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, dime qué dice el primer documento",
        )
    )
    assert_true(handled, "natural first document summary route handled")
    assert_contains(first_doc_update.message.replies[0], "documento 1 de Caso Finca", "first document alias maps to document 1")
    assert_contains(first_doc_update.message.replies[0], "Lo importante:", "first document alias returns safe summary")

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

    timeline_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            timeline_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, muéstrame la línea de tiempo del Caso Finca",
        )
    )
    assert_true(handled, "timeline section route handled")
    assert_contains(timeline_update.message.replies[0], "🧭 Línea de tiempo", "timeline route rendered")
    assert_contains(timeline_update.message.replies[0], "fecha pendiente", "timeline route labels missing dates")

    timeline_gaps_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            timeline_gaps_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, qué falta ordenar por fecha?",
        )
    )
    assert_true(handled, "timeline gaps route handled")
    assert_contains(timeline_gaps_update.message.replies[0], "Huecos / falta fecha", "timeline gaps route rendered")
    for phrase in FOUNDER_LIMITATION_PHRASES:
        assert_not_contains(timeline_gaps_update.message.replies[0], phrase, "timeline gaps avoids founder limitations copy")

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
    assert_contains(source, "falta ordenar por fecha", "founder exclusion protects timeline date-gap alias")
    assert_contains(source, "eventos faltan confirmar", "founder exclusion protects event confirmation alias")


def test_founder_limitations_still_available() -> None:
    phrase = "Val, qué no puedes hacer todavía?"
    assert_true(normalize_founder_intro_intent(phrase) == INTENT_LIMITATIONS, "generic limitations prompt still recognized")
    reply = render_founder_intro_response(INTENT_LIMITATIONS)
    assert_contains(reply, "no debe prometer", "founder limitations copy remains available")


def test_runtime_route_priority_for_date_gap_alias() -> None:
    replies = _runtime_replies("Val, qué falta ordenar por fecha?")
    assert_true(len(replies) == 1, "runtime date-gap route sends one reply")
    assert_contains(replies[0], "Huecos / falta fecha", "runtime date-gap reaches timeline gaps")
    assert_contains(replies[0], "Caso Finca", "runtime date-gap names case")
    for phrase in FOUNDER_LIMITATION_PHRASES:
        assert_not_contains(replies[0], phrase, "runtime date-gap avoids founder limitations")

    limitation_replies = _runtime_replies("Val, qué no puedes hacer todavía?")
    assert_true(len(limitation_replies) == 1, "runtime limitations route sends one reply")
    assert_contains(limitation_replies[0], "no debe prometer", "runtime limitations still reaches founder copy")

    limits_replies = _runtime_replies("Val, cuáles son tus límites?")
    assert_true(len(limits_replies) == 1, "runtime limits route sends one reply")
    assert_contains(limits_replies[0], "no debe prometer", "runtime limits still reaches founder copy")

    whatnow_replies = _runtime_replies("Val, qué hago ahora?")
    assert_true(len(whatnow_replies) == 1, "runtime whatnow route sends one reply")
    assert_not_contains(whatnow_replies[0], "Huecos / falta fecha", "runtime whatnow avoids timeline gaps")


def test_runtime_live_path_for_demo_trust_killers() -> None:
    sequence = _runtime_sequence_replies(["Val, abre mi Caso Finca", "Val, ves algo raro?"])
    assert_true(len(sequence) == 2, "runtime sequence has two turns")
    assert_true(len(sequence[0]) == 1, "runtime open route sends one reply")
    assert_true(len(sequence[1]) == 1, "runtime contextual weirdness route sends one reply")
    weird_reply = sequence[1][0]
    assert_contains(weird_reply, "focos para revisar", "runtime weirdness reaches bounded possible contradictions")
    assert_contains(weird_reply, "Nora/la abogada confirma efecto legal", "runtime weirdness has legal boundary")
    assert_not_contains(weird_reply, "ID técnico del documento", "runtime weirdness hides technical IDs")
    assert_not_contains(weird_reply, "vfms:", "runtime weirdness hides VFMS IDs")
    assert_not_contains(weird_reply, "caso ganado", "runtime weirdness avoids won claim")
    assert_not_contains(weird_reply, "caso perdido", "runtime weirdness avoids lost claim")

    doc_replies = _runtime_replies("Val, resume el documento 1")
    assert_true(len(doc_replies) == 1, "runtime document summary route sends one reply")
    assert_contains(doc_replies[0], "Lo importante:", "runtime document summary reaches workspace summary")
    assert_contains(doc_replies[0], "Nora/la abogada confirma efecto legal", "runtime document summary legal boundary")
    assert_not_contains(doc_replies[0], "ID técnico del documento", "runtime normal document summary hides technical ID label")
    assert_not_contains(doc_replies[0], "vfms:", "runtime normal document summary hides VFMS ID")


def main() -> int:
    test_phrase_detection()
    test_renderer_shape_and_safety()
    test_async_route_and_no_live_file_mutation()
    test_bot_route_order()
    test_founder_limitations_still_available()
    test_runtime_route_priority_for_date_gap_alias()
    test_runtime_live_path_for_demo_trust_killers()
    print("PASS: Caso Finca read-only workspace smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
