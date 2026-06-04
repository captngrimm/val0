from __future__ import annotations

import re
import unicodedata
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


STALE_CONTAMINATION_PHRASES = ("bajar de peso", "task_high", "memoria pura")
CASE_WORKSPACE_FIXTURE_CLIENT = "kar" + "en"
DEFAULT_CASO_FINCA_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "tests" / "fixtures" / CASE_WORKSPACE_FIXTURE_CLIENT / "caso_finca_workspace.json"
)


@dataclass(frozen=True)
class SourceLabel:
    source_type: str = "fixture"
    source_name: str = "static workspace seed"
    confidence: str = "medium"
    status: str = "test-safe"
    created_at: str = ""
    observed_at: str = ""


@dataclass(frozen=True)
class WorkspaceRecord:
    text: str
    source: SourceLabel = field(default_factory=SourceLabel)


@dataclass(frozen=True)
class WorkspaceDocument:
    title: str
    status: str
    source_label: str
    source: SourceLabel = field(default_factory=SourceLabel)
    document_id: str = ""
    path_category: str = ""
    ocr_status: str = ""
    summary_status: str = ""
    relevance: str = ""
    safe_next_action: str = ""


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
    timeline_events: tuple[WorkspaceRecord, ...] = field(default_factory=tuple)
    known_records: tuple[WorkspaceRecord, ...] = field(default_factory=tuple)
    confirmation_records: tuple[WorkspaceRecord, ...] = field(default_factory=tuple)
    question_records: tuple[WorkspaceRecord, ...] = field(default_factory=tuple)
    pending_records: tuple[WorkspaceRecord, ...] = field(default_factory=tuple)
    next_action_records: tuple[WorkspaceRecord, ...] = field(default_factory=tuple)
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


def _source_from_mapping(data: dict[str, Any] | None, fallback: SourceLabel | None = None) -> SourceLabel:
    if not isinstance(data, dict):
        return fallback or SourceLabel()
    status = data.get("source_status") or data.get("status") or (fallback.status if fallback else "test-safe")
    return SourceLabel(
        source_type=str(data.get("source_type") or (fallback.source_type if fallback else "fixture")).strip(),
        source_name=str(data.get("source_name") or (fallback.source_name if fallback else "static workspace seed")).strip(),
        confidence=str(data.get("confidence") or (fallback.confidence if fallback else "medium")).strip(),
        status=str(status).strip(),
        created_at=str(data.get("created_at") or (fallback.created_at if fallback else "")).strip(),
        observed_at=str(data.get("observed_at") or (fallback.observed_at if fallback else "")).strip(),
    )


def _record_from_value(value: Any, default_source: SourceLabel) -> WorkspaceRecord:
    if isinstance(value, dict):
        text = str(value.get("text") or value.get("title") or "").strip()
        return WorkspaceRecord(text=text, source=_source_from_mapping(value, default_source))
    return WorkspaceRecord(text=str(value or "").strip(), source=default_source)


def _records_from_values(values: Any, default_source: SourceLabel) -> tuple[WorkspaceRecord, ...]:
    if not isinstance(values, list):
        return ()
    return tuple(record for record in (_record_from_value(item, default_source) for item in values) if record.text)


def _documents_from_values(values: Any, default_source: SourceLabel) -> tuple[WorkspaceDocument, ...]:
    if not isinstance(values, list):
        return ()
    documents: list[WorkspaceDocument] = []
    for item in values:
        if isinstance(item, dict):
            source = _source_from_mapping(item, default_source)
            title = str(item.get("title") or item.get("text") or "").strip()
            status = str(item.get("document_status") or item.get("status") or "").strip()
            source_label = str(item.get("source_label") or source.source_name or source.source_type).strip()
            if title:
                documents.append(
                    WorkspaceDocument(
                        title=title,
                        status=status,
                        source_label=source_label,
                        source=source,
                        document_id=str(item.get("document_id") or "").strip(),
                        path_category=str(item.get("path_category") or "").strip(),
                        ocr_status=str(item.get("ocr_status") or "").strip(),
                        summary_status=str(item.get("summary_status") or item.get("saved_summary_status") or "").strip(),
                        relevance=str(item.get("relevance") or item.get("possible_caso_finca_relevance") or "").strip(),
                        safe_next_action=str(item.get("safe_next_action") or "").strip(),
                    )
                )
        elif str(item or "").strip():
            documents.append(
                WorkspaceDocument(
                    title=str(item).strip(),
                    status="registrado",
                    source_label=default_source.source_name,
                    source=default_source,
                )
            )
    return tuple(documents)


def load_workspace_case_from_json(path: str | Path) -> WorkspaceCase:
    fixture_path = Path(path)
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Workspace fixture must be an object: {fixture_path}")
    if isinstance(data.get("workspace_case"), dict):
        data = data["workspace_case"]

    default_source = _source_from_mapping(data.get("source") if isinstance(data.get("source"), dict) else data)
    known_records = _records_from_values(data.get("what_we_know"), default_source)
    confirmation_records = _records_from_values(data.get("needs_confirmation"), default_source)
    question_records = _records_from_values(data.get("questions_for_lawyer"), default_source)
    pending_records = _records_from_values(data.get("pending_items"), default_source)
    next_action_records = _records_from_values(data.get("next_actions"), default_source)
    timeline_events = _records_from_values(data.get("timeline_events"), default_source)
    documents = _documents_from_values(data.get("documents"), default_source)

    return WorkspaceCase(
        case_id=str(data.get("case_id") or CASO_FINCA_WORKSPACE.case_id).strip(),
        client_id=str(data.get("client_id") or CASO_FINCA_WORKSPACE.client_id).strip(),
        title=str(data.get("title") or CASO_FINCA_WORKSPACE.title).strip(),
        aliases=tuple(str(alias).strip() for alias in data.get("aliases", ()) if str(alias).strip()),
        what_we_know=tuple(record.text for record in known_records) or CASO_FINCA_WORKSPACE.what_we_know,
        needs_confirmation=tuple(record.text for record in confirmation_records) or CASO_FINCA_WORKSPACE.needs_confirmation,
        documents=documents or CASO_FINCA_WORKSPACE.documents,
        questions_for_lawyer=tuple(record.text for record in question_records) or CASO_FINCA_WORKSPACE.questions_for_lawyer,
        pending_items=tuple(record.text for record in pending_records) or CASO_FINCA_WORKSPACE.pending_items,
        next_actions=tuple(record.text for record in next_action_records) or CASO_FINCA_WORKSPACE.next_actions,
        timeline_events=timeline_events,
        known_records=known_records,
        confirmation_records=confirmation_records,
        question_records=question_records,
        pending_records=pending_records,
        next_action_records=next_action_records,
        source_label=str(data.get("source_label") or "fixture/source-labeled v1").strip(),
    )


def load_caso_finca_workspace_source_labeled(path: str | Path | None = None) -> WorkspaceCase:
    fixture_path = Path(path) if path else DEFAULT_CASO_FINCA_FIXTURE_PATH
    if not fixture_path.exists():
        return CASO_FINCA_WORKSPACE
    try:
        return load_workspace_case_from_json(fixture_path)
    except Exception:
        return CASO_FINCA_WORKSPACE


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


def _source_suffix(source: SourceLabel) -> str:
    pieces = [
        f"source_type={source.source_type}",
        f"source_name={source.source_name}",
        f"confidence={source.confidence}",
        f"status={source.status}",
    ]
    if source.observed_at:
        pieces.append(f"observed_at={source.observed_at}")
    if source.created_at:
        pieces.append(f"created_at={source.created_at}")
    return " [" + "; ".join(pieces) + "]"


def _records_or_plain(records: tuple[WorkspaceRecord, ...], plain: tuple[str, ...]) -> tuple[WorkspaceRecord, ...]:
    if records:
        return records
    return tuple(WorkspaceRecord(text=item) for item in plain)


def _append_record_lines(lines: list[str], records: tuple[WorkspaceRecord, ...], *, numbered: bool = False) -> None:
    for idx, record in enumerate(records, start=1):
        prefix = f"{idx}. " if numbered else "- "
        lines.append(f"{prefix}{record.text}{_source_suffix(record.source)}")


def _document_metadata_lines(doc: WorkspaceDocument) -> list[str]:
    details: list[str] = []
    if doc.document_id:
        details.append(f"document_id: {doc.document_id}")
    if doc.path_category:
        details.append(f"source/path category: {doc.path_category}")
    if doc.ocr_status:
        details.append(f"OCR status: {doc.ocr_status}")
    if doc.summary_status:
        details.append(f"summary status: {doc.summary_status}")
    if doc.relevance:
        details.append(f"relevance: {doc.relevance}")
    if doc.safe_next_action:
        details.append(f"safe next action: {doc.safe_next_action}")
    return details


def render_workspace_status(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None) -> str:
    lines: list[str] = [
        f"Tany, abro {case.title}. Esto es lectura y organizacion; no voy a mover nada.",
        "",
        f"📁 {case.title}",
        f"ID de workspace: {case.case_id}",
        f"Fuente: {case.source_label}",
        "",
        "Lo que sabemos",
    ]
    _append_record_lines(lines, _records_or_plain(case.known_records, case.what_we_know))

    lines.extend(["", "Qué falta confirmar"])
    _append_record_lines(lines, _records_or_plain(case.confirmation_records, case.needs_confirmation))

    lines.extend(["", "Documentos relacionados"])
    for idx, doc in enumerate(case.documents, start=1):
        status = f" — {doc.status}" if doc.status else ""
        lines.append(f"{idx}. {doc.title}{status}. Fuente: {doc.source_label}.{_source_suffix(doc.source)}")
        for detail in _document_metadata_lines(doc):
            lines.append(f"   - {detail}")

    lines.extend(["", "Línea de tiempo / eventos"])
    if case.timeline_events:
        _append_record_lines(lines, case.timeline_events, numbered=True)
    else:
        lines.append("1. Sin línea de tiempo fuente-etiquetada todavía; revisar documentos y notas antes de concluir.")

    lines.extend(["", "Preguntas para Nora"])
    _append_record_lines(lines, _records_or_plain(case.question_records, case.questions_for_lawyer), numbered=True)

    lines.extend(["", "Pendientes"])
    _append_record_lines(lines, _records_or_plain(case.pending_records, case.pending_items), numbered=True)

    lines.extend(["", "Próximo paso sugerido"])
    _append_record_lines(lines, _records_or_plain(case.next_action_records, case.next_actions), numbered=True)

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
    await update.message.reply_text(render_workspace_status(load_caso_finca_workspace_source_labeled(), client_id=client_id))
    return True
