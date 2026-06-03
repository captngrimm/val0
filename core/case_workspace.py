from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any


STALE_CONTAMINATION_PHRASES = ("bajar de peso", "task_high", "memoria pura")


@dataclass(frozen=True)
class WorkspaceDocument:
    title: str
    status: str
    source_label: str


@dataclass(frozen=True)
class WorkspaceCase:
    case_id: str
    client_id: str
    title: str
    aliases: tuple[str, ...] = field(default_factory=tuple)
    what_we_know: tuple[str, ...] = field(default_factory=tuple)
    needs_confirmation: tuple[str, ...] = field(default_factory=tuple)
    documents: tuple[WorkspaceDocument, ...] = field(default_factory=tuple)
    questions_for_lawyer: tuple[str, ...] = field(default_factory=tuple)
    pending_items: tuple[str, ...] = field(default_factory=tuple)
    next_actions: tuple[str, ...] = field(default_factory=tuple)
    source_label: str = "fixture/static v1"


CASO_FINCA_WORKSPACE = WorkspaceCase(
    case_id="CASE:KAREN-LAND-001",
    client_id="client-zero",
    title="Caso Finca",
    aliases=("caso finca", "caso del terreno", "finca", "terreno familiar"),
    what_we_know=(
        "Es un caso familiar relacionado con una finca/terreno y documentos registrales o judiciales por ordenar.",
        "Hay documentos registrados en Val0/VFMS, algunos con OCR o resumen disponible.",
        "Nora/la abogada debe confirmar el efecto legal exacto de autos, oficios y datos registrales.",
    ),
    needs_confirmation=(
        "Estado registral actual de la finca en Registro Publico.",
        "Que documentos prueban mejor el estado actual del caso.",
        "Que fechas, autos u oficios tienen efecto legal vigente.",
    ),
    documents=(
        WorkspaceDocument("Documentos de Registro Publico / juzgado", "registrados; algunos requieren OCR o revision visual", "VFMS/OCR"),
        WorkspaceDocument("Resumenes de documentos", "disponibles cuando el texto extraido u OCR es usable", "generated_summary"),
    ),
    questions_for_lawyer=(
        "Que documento prueba mejor el estado actual de la finca?",
        "Que falta pedir al juzgado o Registro Publico?",
        "Que efecto tiene cada auto, oficio o cancelacion mencionada?",
    ),
    pending_items=(
        "Revisar documentos con OCR pendiente o lectura visual incompleta.",
        "Separar hechos confirmados de datos mencionados pero no verificados.",
        "Preparar paquete corto para Nora antes de la proxima conversacion.",
    ),
    next_actions=(
        "Pedir: Val, resume con OCR el ultimo documento, si el PDF tiene marca de agua.",
        "Pedir: Val, preparame el paquete para Nora, cuando quieras llevarlo ordenado.",
    ),
)


def _strip_accents(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def normalize_workspace_text(text: str) -> str:
    value = _strip_accents(text).lower()
    value = re.sub(r"[¿?¡!.,:;]+", " ", value)
    value = re.sub(r"\b(?:valeria|vale|val|va\s+el|bal|pal)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def looks_like_caso_finca_workspace_request(text: str) -> bool:
    norm = normalize_workspace_text(text)
    if not norm:
        return False

    explicit_open = (
        "abre mi caso finca",
        "abrir mi caso finca",
        "abre caso finca",
        "abrir caso finca",
        "abre la carpeta finca",
        "abre carpeta finca",
        "carpeta clara caso finca",
        "carpeta caso finca",
    )
    if any(marker in norm for marker in explicit_open):
        return True

    has_case_context = any(marker in norm for marker in ("caso finca", "caso del terreno", "con la finca", "de la finca", "del caso"))
    workspace_questions = (
        "que sabemos",
        "que falta confirmar",
        "que falta revisar",
        "que le pregunto a nora",
        "preguntas para nora",
        "que sigue",
        "proximo paso",
        "siguiente paso",
    )
    if has_case_context and any(marker in norm for marker in workspace_questions):
        return True

    if "nora" in norm and any(marker in norm for marker in ("que le pregunto", "preguntas")):
        return True

    return False


def _clean_output(text: str) -> str:
    cleaned = str(text or "")
    for phrase in STALE_CONTAMINATION_PHRASES:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"[ \t]{2,}", " ", cleaned).strip()


def _numbered(items: tuple[str, ...]) -> list[str]:
    return [f"{idx}. {item}" for idx, item in enumerate(items, start=1)]


def render_workspace_status(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None) -> str:
    lines: list[str] = [
        f"Tany, abro {case.title}. Esto es lectura y organizacion; no voy a mover nada.",
        "",
        f"📁 {case.title}",
        f"ID de workspace: {case.case_id}",
        f"Fuente: {case.source_label}",
        "",
        "Lo importante",
    ]
    lines.extend(f"- {item}" for item in case.what_we_know)

    lines.extend(["", "Que falta confirmar"])
    lines.extend(f"- {item}" for item in case.needs_confirmation)

    lines.extend(["", "Documentos relacionados"])
    for idx, doc in enumerate(case.documents, start=1):
        lines.append(f"{idx}. {doc.title} — {doc.status}. Fuente: {doc.source_label}.")

    lines.extend(["", "Preguntas para Nora"])
    lines.extend(_numbered(case.questions_for_lawyer))

    lines.extend(["", "Pendientes"])
    lines.extend(_numbered(case.pending_items))

    lines.extend(["", "Que sigue"])
    lines.extend(_numbered(case.next_actions))

    lines.extend([
        "",
        "Limite legal: Val organiza y resume informacion registrada. Nora/la abogada confirma el efecto legal.",
    ])
    return _clean_output("\n".join(lines))


async def maybe_handle_case_workspace_status(
    update: Any,
    context: Any,
    chat_id: int,
    client_id: str,
    text: str,
) -> bool:
    if not update or not getattr(update, "message", None):
        return False
    if str(client_id or "").strip().lower() not in {"karen", "client-zero"}:
        return False
    if not looks_like_caso_finca_workspace_request(text):
        return False
    await update.message.reply_text(render_workspace_status(CASO_FINCA_WORKSPACE, client_id=client_id))
    return True
