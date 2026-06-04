from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from core.case_workspace import (
    WorkspaceCase,
    WorkspaceDocument,
    get_workspace_document_by_number,
    load_caso_finca_workspace_source_labeled,
)


KAREN_CLIENT_IDS = {"karen", "client-zero"}
LEGAL_BOUNDARY = "Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal."
OCR_CAVEAT = "Nota OCR: esta lectura puede tener errores; conviene contrastarla con el PDF original."
FORBIDDEN_LEGAL_CERTAINTY = (
    "definitivamente",
    "caso ganado",
    "caso perdido",
    "no necesitas abogada",
    "conclusión legal definitiva",
)
STALE_CONTAMINATION_PHRASES = ("bajar de peso", "task_high", "memoria pura")


@dataclass(frozen=True)
class CasoFincaQAPacket:
    client_id: str
    workspace_id: str
    workspace_title: str
    user_question: str
    question_type: str
    known_facts: tuple[str, ...] = field(default_factory=tuple)
    needs_confirmation: tuple[str, ...] = field(default_factory=tuple)
    questions_for_nora: tuple[str, ...] = field(default_factory=tuple)
    pending_items: tuple[str, ...] = field(default_factory=tuple)
    next_actions: tuple[str, ...] = field(default_factory=tuple)
    documents: tuple[WorkspaceDocument, ...] = field(default_factory=tuple)
    selected_document_number: int = 0
    selected_document: WorkspaceDocument | None = None
    source_note: str = "Fuente: tablero Caso Finca y documentos registrados."
    uses_ocr_backed_reading: bool = False


def _strip_accents(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def normalize_case_qa_text(text: str) -> str:
    value = _strip_accents(text).lower()
    value = re.sub(r"[¿?¡!.,:;]+", " ", value)
    value = re.sub(r"\b(?:valeria|vale|val|va\s+el|bal|pal)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _has_any(norm: str, markers: tuple[str, ...]) -> bool:
    return any(marker in norm for marker in markers)


def _case_context(norm: str) -> bool:
    return _has_any(
        norm,
        (
            "caso",
            "finca",
            "terreno",
            "nora",
            "abogada",
            "primer documento",
            "documento 1",
        ),
    )


def _word_number_to_int(token: str) -> int:
    value = _strip_accents(token).lower().strip()
    if value.isdigit():
        return int(value)
    return {
        "primer": 1,
        "primero": 1,
        "uno": 1,
        "una": 1,
        "dos": 2,
        "segundo": 2,
        "tres": 3,
        "tercero": 3,
        "cuatro": 4,
        "cinco": 5,
    }.get(value, 0)


def extract_case_qa_document_number(text: str) -> int:
    norm = normalize_case_qa_text(text)
    match = re.search(
        r"\b(?:(primer|primero|uno|una|dos|segundo|tres|tercero|cuatro|cinco|\d{1,2})\s+documento|documento\s+(primer|primero|uno|una|dos|segundo|tres|tercero|cuatro|cinco|\d{1,2}))\b",
        norm,
    )
    if not match:
        return 0
    return _word_number_to_int(match.group(1) or match.group(2) or "")


def classify_case_qa_question(text: str) -> str | None:
    norm = normalize_case_qa_text(text)
    contextless_demo_markers = (
        "que falta revisar",
        "que sabemos seguro y que falta confirmar",
        "cual documento deberia revisar primero",
        "que documento deberia revisar primero",
        "hay algo raro",
        "hay algo contradictorio",
    )
    if not norm or not _case_context(norm):
        if not any(marker in norm for marker in contextless_demo_markers):
            return None

    if _has_any(norm, ("abre ", "muestrame documentos", "mostrar documentos", "ensename los papeles", "resume el documento")):
        return None

    if extract_case_qa_document_number(text) and _has_any(norm, ("por que importa", "porque importa", "que significa", "que dice")):
        return "document_explanation"

    if _has_any(norm, ("cual documento deberia revisar primero", "que documento deberia revisar primero", "documento revisar primero")):
        return "document_priority"

    if _has_any(norm, ("que sabemos seguro", "que falta confirmar", "seguro y que falta")):
        return "known_vs_uncertain"

    if _has_any(norm, ("que falta revisar", "que me falta revisar", "que falta confirmar")):
        return "needs_review"

    if _has_any(norm, ("que le pregunto a nora", "preguntas para nora", "preguntarle a nora")):
        return "nora_questions"

    if _has_any(norm, ("que hago antes de hablar", "antes de hablar con la abogada", "antes de hablar con nora")):
        return "next_action"

    if _has_any(norm, ("hay algo raro", "contradictorio", "contradiccion", "contradicciones")):
        return "possible_contradictions"

    if _has_any(norm, ("explicame lo de la finca", "palabras simples", "que sabes del caso", "que sabes de la finca", "que sabemos del caso")):
        if "palabras simples" in norm or "explicame" in norm:
            return "plain_language_explanation"
        return "case_overview"

    return None


def _take(values: tuple[str, ...], limit: int) -> tuple[str, ...]:
    return tuple(item for item in values if str(item).strip())[:limit]


def build_case_qa_packet(
    text: str,
    *,
    client_id: str = "karen",
    case: WorkspaceCase | None = None,
) -> CasoFincaQAPacket | None:
    question_type = classify_case_qa_question(text)
    if not question_type:
        return None
    workspace = case or load_caso_finca_workspace_source_labeled()
    doc_number = extract_case_qa_document_number(text)
    selected_doc = get_workspace_document_by_number(workspace, doc_number) if doc_number else None
    uses_ocr = bool(selected_doc and _strip_accents(selected_doc.ocr_status).lower().strip() == "available")
    return CasoFincaQAPacket(
        client_id=client_id,
        workspace_id=workspace.case_id,
        workspace_title=workspace.title,
        user_question=str(text or "").strip(),
        question_type=question_type,
        known_facts=_take(workspace.what_we_know, 4),
        needs_confirmation=_take(workspace.needs_confirmation, 4),
        questions_for_nora=_take(workspace.questions_for_lawyer, 4),
        pending_items=_take(workspace.pending_items, 4),
        next_actions=_take(workspace.next_actions, 3),
        documents=workspace.documents,
        selected_document_number=doc_number,
        selected_document=selected_doc,
        uses_ocr_backed_reading=uses_ocr,
    )


def _numbered(items: tuple[str, ...] | list[str], *, empty: str = "No tengo datos suficientes todavía.") -> list[str]:
    clean = [str(item).strip() for item in items if str(item).strip()]
    if not clean:
        return [f"1. {empty}"]
    return [f"{idx}. {item}" for idx, item in enumerate(clean, start=1)]


def _first_ocr_document(packet: CasoFincaQAPacket) -> tuple[int, WorkspaceDocument] | tuple[int, None]:
    for idx, doc in enumerate(packet.documents, start=1):
        if _strip_accents(doc.ocr_status).lower().strip() == "available":
            return idx, doc
    return (1, packet.documents[0]) if packet.documents else (0, None)


def _document_plain_status(doc: WorkspaceDocument) -> str:
    bits: list[str] = []
    if _strip_accents(doc.ocr_status).lower().strip() == "available":
        bits.append("tiene lectura OCR disponible")
    if _strip_accents(doc.summary_status).lower().strip() == "available":
        bits.append("tiene resumen guardado")
    if _strip_accents(doc.relevance).lower().strip() == "high":
        bits.append("parece muy relacionado con el caso")
    return "; ".join(bits) if bits else "está registrado, pero falta confirmar su utilidad"


def _render_document_explanation(packet: CasoFincaQAPacket) -> str:
    doc = packet.selected_document
    if not doc:
        return "\n".join(
            [
                "Tany, necesito que me digas cuál documento quieres revisar dentro de Caso Finca.",
                "",
                'Puedes decir: "Val, dime qué dice el primer documento".',
                "",
                LEGAL_BOUNDARY,
            ]
        )
    number = packet.selected_document_number or 1
    lines = [
        f"Tany, el documento {number} importa como punto de partida dentro de Caso Finca.",
        "",
        f"📄 {doc.title}",
        "",
        "Lo que sé",
        f"1. Este documento {_document_plain_status(doc)}.",
        "2. Lo uso como referencia de trabajo, no como conclusión legal.",
        "",
        "Lo que falta confirmar",
        "1. Si lo que menciona sigue vigente o solo es antecedente.",
        "2. Si coincide con el estado registral/judicial más actualizado.",
        "",
        "Pregunta para Nora",
        '1. "Este documento sigue teniendo efecto legal o solo sirve como antecedente?"',
    ]
    if packet.uses_ocr_backed_reading:
        lines.extend(["", OCR_CAVEAT])
    lines.extend(["", LEGAL_BOUNDARY])
    return "\n".join(lines)


def render_case_qa_answer(packet: CasoFincaQAPacket) -> str:
    qt = packet.question_type
    if qt == "document_explanation":
        body = _render_document_explanation(packet)
    elif qt == "document_priority":
        number, doc = _first_ocr_document(packet)
        if doc:
            body = "\n".join(
                [
                    "Tany, revisaría primero el documento que ya tiene mejor punto de lectura.",
                    "",
                    "Documento recomendado",
                    f"1. Documento {number}: {doc.title}",
                    f"2. Motivo: {_document_plain_status(doc)}.",
                    "",
                    "Próximo paso sugerido",
                    f'1. "Val, resume el documento {number}"',
                    "",
                    packet.source_note,
                    "",
                    LEGAL_BOUNDARY,
                ]
            )
        else:
            body = "\n".join(["Tany, no tengo documentos suficientes en Caso Finca para priorizar todavía.", "", LEGAL_BOUNDARY])
    elif qt == "known_vs_uncertain":
        body = "\n".join(
            [
                "Tany, te lo separo en limpio para no mezclar hechos con novela registral:",
                "",
                "Lo que sé",
                *_numbered(packet.known_facts),
                "",
                "Lo que falta confirmar",
                *_numbered(packet.needs_confirmation),
                "",
                "Pregunta clave para Nora",
                '1. "Con estos documentos, cuál prueba mejor el estado actual de la finca?"',
                "",
                packet.source_note,
                "",
                LEGAL_BOUNDARY,
            ]
        )
    elif qt == "needs_review":
        body = "\n".join(
            [
                "Tany, esto es lo que falta revisar del Caso Finca:",
                "",
                "Lo que falta confirmar",
                *_numbered(packet.needs_confirmation),
                "",
                "Pendientes",
                *_numbered(packet.pending_items),
                "",
                "Próximo paso sugerido",
                "1. Revisar primero el documento con OCR disponible y sacar preguntas para Nora.",
                "",
                packet.source_note,
                "",
                LEGAL_BOUNDARY,
            ]
        )
    elif qt == "nora_questions":
        body = "\n".join(
            [
                "Tany, estas son preguntas útiles para llevarle a Nora sobre Caso Finca:",
                "",
                "Preguntas para Nora",
                *_numbered(packet.questions_for_nora),
                "",
                "Para abrir la conversación",
                '1. "¿Qué documento prueba mejor el estado actual de la finca?"',
                "",
                LEGAL_BOUNDARY,
            ]
        )
    elif qt == "next_action":
        body = "\n".join(
            [
                "Tany, antes de hablar con la abogada sobre Caso Finca yo haría esto, en orden:",
                "",
                "Próximo paso sugerido",
                *_numbered(packet.pending_items[:2] or packet.next_actions[:2]),
                "",
                "Para Nora",
                "1. Llevarle la lista de documentos y pedirle que confirme efecto legal.",
                "",
                LEGAL_BOUNDARY,
            ]
        )
    elif qt == "possible_contradictions":
        body = "\n".join(
            [
                "Tany, no voy a declarar contradicción legal todavía, pero sí marcaría focos para revisar:",
                "",
                "Posibles puntos raros",
                "1. Si un documento menciona una actuación y otro no la refleja, hay que confirmar cuál es más reciente.",
                "2. Si OCR lee mal nombres, números de finca o fechas, eso puede cambiar la interpretación.",
                "3. Si aparecen medidas cautelares, hay que confirmar si están vigentes o canceladas.",
                "",
                "Pregunta para Nora",
                '1. "¿Hay algún documento más reciente que cambie o contradiga estos datos?"',
                "",
                LEGAL_BOUNDARY,
            ]
        )
    elif qt == "plain_language_explanation":
        body = "\n".join(
            [
                "Tany, en palabras simples: Caso Finca es tu carpeta para ordenar el tema de la finca sin que los papeles se vuelvan una torre con actitud.",
                "",
                "Lo que sé",
                *_numbered(packet.known_facts[:3]),
                "",
                "Lo importante",
                "1. Hay documentos que parecen relacionados.",
                "2. Uno ya tiene lectura OCR disponible.",
                "3. Nora/la abogada debe confirmar qué efecto legal tiene cada cosa.",
                "",
                "Próximo paso sugerido",
                '1. "Val, cuál documento debería revisar primero?"',
                "",
                packet.source_note,
                "",
                LEGAL_BOUNDARY,
            ]
        )
    else:
        body = "\n".join(
            [
                "Tany, lo que tengo del Caso Finca en limpio es esto:",
                "",
                "Lo que sé",
                *_numbered(packet.known_facts),
                "",
                "Lo que falta confirmar",
                *_numbered(packet.needs_confirmation),
                "",
                "Preguntas para Nora",
                *_numbered(packet.questions_for_nora[:2]),
                "",
                "Próximo paso sugerido",
                "1. Revisar primero el documento con OCR disponible y preparar preguntas para Nora.",
                "",
                packet.source_note,
                "",
                LEGAL_BOUNDARY,
            ]
        )
    return _clean_answer(body)


def _clean_answer(text: str) -> str:
    cleaned = str(text or "")
    for phrase in STALE_CONTAMINATION_PHRASES:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)
    for phrase in FORBIDDEN_LEGAL_CERTAINTY:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


async def maybe_handle_case_workspace_qa(update: Any, context: Any, chat_id: int, client_id: str, text: str) -> bool:
    if str(client_id or "").strip().lower() not in KAREN_CLIENT_IDS:
        return False
    if not update or not getattr(update, "message", None):
        return False
    packet = build_case_qa_packet(text, client_id=client_id)
    if not packet:
        return False
    await update.message.reply_text(render_case_qa_answer(packet))
    return True
