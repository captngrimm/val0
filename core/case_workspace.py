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
VFMS_EXTRACTED_DIR = Path("/opt/val0/vfms_data/extracted")
VFMS_OCR_RUNTIME_DIR = Path("/opt/val0/vfms_data/ocr_runtime")


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


def _case_context_present(norm: str) -> bool:
    return any(marker in norm for marker in ("caso finca", "caso del terreno", "con la finca", "de la finca", "del caso"))


def _number_word_to_int(value: str) -> int:
    normalized = _strip_accents(value).lower().strip()
    if normalized.isdigit():
        return int(normalized)
    mapping = {
        "primer": 1,
        "primero": 1,
        "uno": 1,
        "una": 1,
        "dos": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
        "nueve": 9,
        "diez": 10,
    }
    return mapping.get(normalized, 0)


def extract_case_workspace_document_summary_number(text: str) -> int:
    norm = normalize_workspace_text(text)
    if not norm:
        return 0
    if not re.search(r"\b(?:resume|resumen|resumeme|resumir|lee|leeme|dime\s+que\s+dice|que\s+dice|dice)\b", norm):
        return 0
    match = re.search(r"\b(?:documento|doc)\s+(\d{1,2}|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\b", norm)
    if match:
        return _number_word_to_int(match.group(1))
    match = re.search(
        r"\b(\d{1,2}|primer|primero|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s+(?:documento|doc)\b",
        norm,
    )
    return _number_word_to_int(match.group(1)) if match else 0


def detect_case_workspace_view(text: str) -> str | None:
    norm = normalize_workspace_text(text)
    if not norm:
        return None

    if extract_case_workspace_document_summary_number(text):
        return "document_summary"

    has_case_context = _case_context_present(norm)

    full_markers = (
        "muestrame todo el caso finca",
        "muestra todo el caso finca",
        "muestrame todo caso finca",
        "muestra todo caso finca",
        "todo el caso finca",
        "todo caso finca",
    )
    if any(marker in norm for marker in full_markers):
        return "full"

    timeline_markers = (
        "linea de tiempo",
        "línea de tiempo",
        "eventos tengo registrados",
        "eventos registrados",
        "que paso primero",
        "qué pasó primero",
        "cronologia",
        "cronología",
    )
    if has_case_context and any(marker in norm for marker in timeline_markers):
        return "timeline"

    timeline_gap_markers = (
        "falta ordenar por fecha",
        "falta ordenar fechas",
        "eventos faltan confirmar",
        "eventos falta confirmar",
        "fechas faltan confirmar",
        "huecos de fecha",
        "falta fecha",
    )
    if has_case_context and any(marker in norm for marker in timeline_gap_markers):
        return "timeline_gaps"
    if "falta ordenar por fecha" in norm:
        return "timeline_gaps"

    doc_context = "document" in norm or "papel" in norm or "papeles" in norm

    if has_case_context and doc_context and any(marker in norm for marker in ("detalle", "detalles", "tecnico", "tecnicos")):
        return "document_details"

    if has_case_context and doc_context and any(marker in norm for marker in ("muestrame", "mostrar", "ver", "lista", "ensename")):
        return "documents"

    if ("nora" in norm and any(marker in norm for marker in ("muestrame", "mostrar", "preguntas", "que le pregunto"))) or (
        has_case_context and "preguntas" in norm
    ):
        return "questions"

    if has_case_context and any(marker in norm for marker in ("pendientes", "pendiente", "faltantes")) and any(
        marker in norm for marker in ("muestrame", "mostrar", "ver", "lista")
    ):
        return "pending"

    explicit_open = (
        "abre mi caso finca",
        "abrir mi caso finca",
        "abre caso finca",
        "abrir caso finca",
        "abre la carpeta finca",
        "abre carpeta finca",
        "abre lo de la finca",
        "abre lo de finca",
        "carpeta clara caso finca",
        "carpeta caso finca",
    )
    if any(marker in norm for marker in explicit_open):
        return "compact"

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
        return "compact"

    if "nora" in norm and any(marker in norm for marker in ("que le pregunto", "preguntas")):
        return "questions"

    return None


def looks_like_caso_finca_workspace_request(text: str) -> bool:
    return detect_case_workspace_view(text) is not None


def _clean_output(text: str) -> str:
    cleaned = str(text or "")
    for phrase in STALE_CONTAMINATION_PHRASES:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"[ \t]{2,}", " ", cleaned).strip()


def _numbered(items: tuple[str, ...]) -> list[str]:
    return [f"{idx}. {item}" for idx, item in enumerate(items, start=1)]


def _friendly_source_label(source: SourceLabel) -> str:
    source_type = _strip_accents(source.source_type).lower().strip()
    source_name = _strip_accents(source.source_name).lower().strip()
    status = _strip_accents(source.status).lower().strip()

    if "karen_document_inventory_audit" in source_name or "vfms" in source_type:
        return "auditoría de documentos"
    if any(marker in source_type for marker in ("document", "summary", "repo_fixture")):
        return "documento registrado"
    if "candidate" in status or "confirm" in status or "uncertain" in status:
        return "pendiente de confirmar"
    if source_type == "fixture":
        return "nota de trabajo"
    return "documento registrado"


def _friendly_confidence(value: str) -> str:
    normalized = _strip_accents(value).lower().strip()
    mapping = {
        "high": "alta",
        "alta": "alta",
        "medium": "media",
        "media": "media",
        "low": "baja",
        "baja": "baja",
        "unknown": "por confirmar",
        "": "por confirmar",
    }
    return mapping.get(normalized, value.strip() or "por confirmar")


def _friendly_status(value: str) -> str:
    normalized = _strip_accents(value).lower().strip()
    if not normalized:
        return "por revisar"
    if "trusted metadata" in normalized and "legal review" in normalized:
        return "requiere revisión legal"
    if "needs legal review" in normalized:
        return "requiere revisión legal"
    if "candidate" in normalized and "human review" in normalized:
        return "candidato; requiere revisión humana"
    if "uncertain candidate" in normalized:
        return "candidato pendiente de confirmar"
    if "confirm with nora" in normalized:
        return "confirmar con Nora"
    if "confirm with lawyer" in normalized:
        return "confirmar con la abogada"
    if "observed" in normalized:
        return "observado"
    if "open" in normalized:
        return "abierto"
    if "suggested" in normalized:
        return "sugerido"
    if "needs ordering" in normalized:
        return "requiere orden por fecha"
    if "question draft" in normalized:
        return "pregunta borrador"
    if "test-safe" in normalized:
        return "solo lectura"
    return value.strip()


def _friendly_path_category(value: str) -> str:
    normalized = _strip_accents(value).lower().strip()
    if not normalized:
        return ""
    if normalized in {"vfms_raw", "vfms raw"}:
        return "documento registrado en VFMS"
    return value.strip()


def _friendly_ocr_status(value: str) -> str:
    normalized = _strip_accents(value).lower().strip()
    mapping = {
        "available": "disponible",
        "missing": "pendiente",
        "unknown": "desconocido",
        "failed": "falló",
        "low_quality": "baja calidad",
    }
    return mapping.get(normalized, value.strip())


def _friendly_summary_status(value: str) -> str:
    normalized = _strip_accents(value).lower().strip()
    mapping = {
        "available": "disponible",
        "missing": "pendiente",
        "unknown": "desconocido",
        "none": "pendiente",
    }
    return mapping.get(normalized, value.strip())


def _friendly_relevance(value: str) -> str:
    normalized = _strip_accents(value).lower().strip()
    mapping = {
        "high": "alta",
        "medium": "media",
        "low": "baja",
        "unknown": "por confirmar",
    }
    return mapping.get(normalized, value.strip())


def _source_suffix(source: SourceLabel) -> str:
    pieces = [
        f"Fuente: {_friendly_source_label(source)}",
        f"Confianza: {_friendly_confidence(source.confidence)}",
        f"Estado: {_friendly_status(source.status)}",
    ]
    if source.observed_at:
        pieces.append(f"Observado: {source.observed_at}")
    if source.created_at:
        pieces.append(f"Creado: {source.created_at}")
    return " (" + "; ".join(pieces) + ")"


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
        details.append(f"ID técnico del documento: {doc.document_id}")
    details.append(f"Fuente: {_friendly_source_label(doc.source)}")
    details.append(f"Confianza: {_friendly_confidence(doc.source.confidence)}")
    details.append(f"Estado: {_friendly_status(doc.source.status)}")
    if doc.path_category:
        details.append(f"Categoría: {_friendly_path_category(doc.path_category)}")
    if doc.ocr_status:
        details.append(f"OCR: {_friendly_ocr_status(doc.ocr_status)}")
    if doc.summary_status:
        details.append(f"Resumen: {_friendly_summary_status(doc.summary_status)}")
    if doc.relevance:
        details.append(f"Relevancia para Caso Finca: {_friendly_relevance(doc.relevance)}")
    if doc.safe_next_action:
        details.append(f"Siguiente paso seguro: {doc.safe_next_action}")
    return details


def _document_review_label(doc: WorkspaceDocument) -> str:
    status = _strip_accents(f"{doc.status} {doc.source.status}").lower()
    confidence = _friendly_confidence(doc.source.confidence)
    if "trusted metadata" in status or confidence == "alta":
        return "confiable como referencia inicial; efecto legal por confirmar"
    if any(marker in status for marker in ("candidate", "candidato", "uncertain")):
        return "parece relevante, pero falta confirmarlo"
    return "registrado para revisión"


def _document_availability_label(doc: WorkspaceDocument) -> str:
    ocr = _friendly_ocr_status(doc.ocr_status)
    summary = _friendly_summary_status(doc.summary_status)
    bits: list[str] = []
    if ocr:
        bits.append(f"OCR: {ocr}")
    if summary:
        bits.append(f"resumen: {summary}")
    return "; ".join(bits) if bits else "lectura pendiente"


def _document_compact_next_command(doc: WorkspaceDocument, idx: int) -> str:
    if _strip_accents(doc.ocr_status).lower().strip() == "available":
        return 'Pedir: "Val, resume con OCR el último documento", si quieres leerlo visualmente.'
    return f'Pedir: "Val, resume el documento {idx}", si quieres revisar este archivo.'


def _document_ingest_id(doc: WorkspaceDocument) -> str:
    raw = str(doc.document_id or "").strip()
    if raw.startswith("vfms:"):
        raw = raw.split(":", 1)[1]
    match = re.search(r"\b(20\d{6}_\d{6})\b", raw)
    return match.group(1) if match else raw


def _read_saved_workspace_document_text(doc: WorkspaceDocument) -> tuple[str, str]:
    if _strip_accents(doc.ocr_status).lower().strip() != "available":
        return "", ""
    ingest_id = _document_ingest_id(doc)
    if not ingest_id:
        return "", ""

    candidates = [
        (VFMS_OCR_RUNTIME_DIR / f"{ingest_id}__ocr_runtime.txt", "OCR guardado"),
        (VFMS_EXTRACTED_DIR / f"{ingest_id}.txt", "texto extraído"),
    ]
    for path, label in candidates:
        try:
            if path.exists() and path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace").strip()
                if _saved_document_text_usable(text):
                    return text, label
        except Exception:
            continue
    return "", ""


def _saved_document_text_usable(text: str) -> bool:
    normalized = _strip_accents(text).lower()
    if len(normalized.strip()) < 500:
        return False
    watermark_count = normalized.count("copia para propositos informativos solamente")
    markers = (
        "juzgado",
        "auto",
        "oficio",
        "finca",
        "registro",
        "demanda",
        "secuestro",
        "embargo",
        "medidas cautelares",
        "prescripcion",
    )
    marker_hits = sum(1 for marker in markers if marker in normalized)
    return marker_hits >= 3 and watermark_count <= max(2, marker_hits)


def _has_text_marker(text: str, *markers: str) -> bool:
    normalized = _strip_accents(text).lower()
    return any(_strip_accents(marker).lower() in normalized for marker in markers)


def _case_document_ocr_summary_bullets(text: str) -> tuple[list[str], list[str], list[str]]:
    important: list[str] = []
    confirm: list[str] = []
    questions: list[str] = []

    if _has_text_marker(text, "juzgado", "oficio"):
        important.append("La lectura menciona un documento/oficio judicial relacionado con el juzgado.")
        confirm.append("Confirmar qué efecto tiene ese oficio dentro del expediente actual.")
        questions.append("¿Qué efecto práctico tiene este oficio para el estado actual del caso?")
    if _has_text_marker(text, "registro publico", "registro público"):
        important.append("Aparece una actuación o comunicación vinculada al Registro Público.")
        confirm.append("Verificar si lo indicado ya aparece reflejado en una certificación registral actualizada.")
        questions.append("¿Conviene pedir una certificación actualizada del Registro Público?")
    if _has_text_marker(text, "finca", "folio real", "10082", "codigo de ubicacion", "código de ubicación"):
        important.append("La lectura contiene datos registrales de la finca o folio real.")
        confirm.append("Confirmar que esos datos coinciden con la finca correcta y con el estado registral actual.")
        questions.append("¿Estos datos registrales son suficientes para identificar la finca sin ambigüedad?")
    if _has_text_marker(text, "demanda", "prescripcion adquisitiva", "prescripción adquisitiva"):
        important.append("Se menciona una demanda o proceso de prescripción adquisitiva.")
        confirm.append("Confirmar si esa demanda sigue vigente, fue modificada, inscrita, cancelada o quedó sin efecto.")
        questions.append("¿La demanda mencionada sigue teniendo algún efecto legal o registral?")
    if _has_text_marker(text, "auto no", "auto n", "auto"):
        important.append("La lectura menciona uno o más autos judiciales.")
        confirm.append("Revisar con Nora qué ordena exactamente cada auto y si está vigente.")
        questions.append("¿Cuál auto es el más importante para explicar el estado actual?")
    if _has_text_marker(text, "secuestro", "embargo", "medidas cautelares"):
        important.append("Aparecen palabras asociadas a medidas cautelares, secuestro o embargo.")
        confirm.append("Confirmar si esas medidas están vigentes, canceladas o solo mencionadas en el documento.")
        questions.append("¿Hay alguna medida cautelar vigente que afecte la finca?")

    if not important:
        important.append("Hay lectura guardada, pero necesito revisión humana para clasificar los puntos principales con confianza.")
    if not confirm:
        confirm.append("Confirmar con Nora el efecto legal exacto antes de depender del documento.")
    if not questions:
        questions.append("¿Qué dato de este documento debo usar como punto central del caso?")

    return important[:5], confirm[:4], questions[:4]


def _render_ocr_backed_document_summary(doc: WorkspaceDocument, *, number: int, text: str, text_source: str) -> str:
    important, confirm, questions = _case_document_ocr_summary_bullets(text)
    lines = [
        f"Tany, revisé la lectura disponible del documento {number} de Caso Finca.",
        "",
        f"📄 {doc.title}",
        f"ID técnico del documento: {doc.document_id or 'sin ID técnico registrado'}",
        f"Fuente de lectura: {text_source}.",
        "",
        "Lo importante:",
    ]
    lines.extend(f"- {item}" for item in important)
    lines.extend(["", "Qué falta confirmar:"])
    lines.extend(f"- {item}" for item in confirm)
    lines.extend(["", "Preguntas para Nora:"])
    lines.extend(f"- {item}" for item in questions)
    lines.extend(
        [
            "",
            "Límite legal:",
            "Val organiza y resume; Nora/la abogada confirma efecto legal.",
        ]
    )
    return _clean_output("\n".join(lines))


def get_workspace_document_by_number(case: WorkspaceCase, number: int) -> WorkspaceDocument | None:
    idx = int(number or 0) - 1
    if idx < 0 or idx >= len(case.documents):
        return None
    return case.documents[idx]


def render_workspace_document_number_summary(
    case: WorkspaceCase = CASO_FINCA_WORKSPACE,
    *,
    number: int,
    client_id: str | None = None,
) -> str:
    doc = get_workspace_document_by_number(case, number)
    if not doc:
        total = len(case.documents)
        suffix = f"Ahora mismo tengo {total} documento(s) numerados en {case.title}." if total else "No tengo documentos numerados en este tablero."
        return _clean_output(
            "\n".join(
                [
                    f"Tany, no encuentro el documento {int(number or 0)} dentro de {case.title}.",
                    suffix,
                    'Puedes pedir: "Val, muéstrame documentos del Caso Finca" para ver la lista actualizada.',
                ]
            )
        )

    availability = _document_availability_label(doc)
    review = _document_review_label(doc)
    saved_text, text_source = _read_saved_workspace_document_text(doc)
    if saved_text:
        return _render_ocr_backed_document_summary(doc, number=number, text=saved_text, text_source=text_source)

    lines = [
        f"Tany, el documento {number} de {case.title} es:",
        f"📄 {doc.title}",
        "",
        "Resumen seguro v1",
        f"- ID técnico del documento: {doc.document_id or 'sin ID técnico registrado'}",
        f"- Estado simple: {review}.",
        f"- Lectura disponible: {availability}.",
    ]
    if _strip_accents(doc.ocr_status).lower().strip() == "available":
        lines.append("- Puedo ayudarte a revisarlo con la lectura OCR ya guardada, sin crear ni cambiar documentos.")
        lines.append('Siguiente paso: "Val, resume con OCR el último documento", si quieres una lectura visual más completa.')
    else:
        lines.append("- Ese documento está registrado, pero todavía no tengo una lectura/OCR usable para resumirlo con confianza.")
        lines.append('Siguiente paso: "Val, muéstrame detalles técnicos de los documentos del Caso Finca" para ver qué falta.')
    lines.extend(
        [
            "",
            "Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.",
        ]
    )
    return _clean_output("\n".join(lines))


def _count_ocr_available(case: WorkspaceCase) -> int:
    return sum(1 for doc in case.documents if _strip_accents(doc.ocr_status).lower().strip() == "available")


def _count_candidate_documents(case: WorkspaceCase) -> int:
    count = 0
    for doc in case.documents:
        status = _strip_accents(f"{doc.status} {doc.source.status}").lower()
        if any(marker in status for marker in ("candidate", "candidato", "confirm", "uncertain")):
            count += 1
    return count


def render_workspace_compact_status(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None) -> str:
    document_count = len(case.documents)
    ocr_count = _count_ocr_available(case)
    candidate_count = _count_candidate_documents(case)
    doc_line = (
        f"Encontré {document_count} documentos que parecen relacionados con el caso."
        if document_count
        else "Todavía no tengo documentos relacionados en este tablero."
    )
    ocr_line = (
        "Uno ya tiene lectura OCR disponible."
        if ocr_count == 1
        else f"{ocr_count} ya tienen lectura OCR disponible."
        if ocr_count > 1
        else "Aún no veo una lectura OCR lista en este tablero."
    )
    candidate_line = (
        "Otros parecen relevantes, pero hay que confirmarlos antes de depender de ellos."
        if candidate_count
        else "Lo que aparezca aquí sigue siendo material para ordenar, no una conclusión legal."
    )

    lines = [
        f"Tany, abrí tu {case.title}. Te muestro el estado en limpio, sin mover ni cambiar nada.",
        "",
        "📁 Estado rápido",
        f"- {doc_line}",
        f"- {ocr_line}",
        f"- {candidate_line}",
        "- Val solo está organizando la información; Nora/la abogada confirma el efecto legal.",
        "",
        "Puedes pedirme:",
        '1. "Val, muéstrame documentos del Caso Finca"',
        '2. "Val, muéstrame preguntas para Nora"',
        '3. "Val, muéstrame pendientes del Caso Finca"',
        '4. "Val, muéstrame la línea de tiempo del Caso Finca"',
        '5. "Val, muéstrame todo el Caso Finca"',
    ]
    return _clean_output("\n".join(lines))


def render_workspace_documents_section(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None) -> str:
    lines = [
        f"Tany, estos son los documentos que tengo a la vista para {case.title}. Te los pongo en limpio primero.",
        "",
        "📄 Documentos del Caso Finca",
    ]
    if not case.documents:
        lines.append("1. No veo documentos relacionados todavía.")
    for idx, doc in enumerate(case.documents, start=1):
        lines.append(f"{idx}. {doc.title}")
        lines.append(f"   - Estado simple: {_document_review_label(doc)}.")
        lines.append(f"   - Lectura: {_document_availability_label(doc)}.")
        lines.append(f"   - Siguiente paso: {_document_compact_next_command(doc, idx)}")
    lines.extend([
        "",
        'Para ver IDs y fuentes internas, pide: "Val, muéstrame detalles técnicos de los documentos del Caso Finca".',
        "Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.",
    ])
    return _clean_output("\n".join(lines))


def render_workspace_document_details_section(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None) -> str:
    lines = [
        f"Tany, estos son los detalles técnicos de los documentos de {case.title}. No estoy moviendo ni cambiando nada.",
        "",
        "📄 Detalles técnicos de documentos",
    ]
    if not case.documents:
        lines.append("1. No veo documentos relacionados todavía.")
    for idx, doc in enumerate(case.documents, start=1):
        status = f" — {doc.status}" if doc.status else ""
        lines.append(f"{idx}. {doc.title}{status}.")
        for detail in _document_metadata_lines(doc):
            lines.append(f"   - {detail}")
    lines.extend(["", "Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal."])
    return _clean_output("\n".join(lines))


def render_workspace_questions_section(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None) -> str:
    lines = [
        f"Tany, estas son preguntas útiles para llevarle a Nora sobre {case.title}.",
        "",
        "❓ Preguntas para Nora",
    ]
    _append_record_lines(lines, _records_or_plain(case.question_records, case.questions_for_lawyer), numbered=True)
    lines.extend(["", "Límite legal: Val organiza las preguntas; Nora/la abogada confirma efecto legal."])
    return _clean_output("\n".join(lines))


def render_workspace_pending_section(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None) -> str:
    lines = [
        f"Tany, estos son los pendientes que veo para ordenar {case.title}.",
        "",
        "📌 Pendientes del Caso Finca",
    ]
    _append_record_lines(lines, _records_or_plain(case.pending_records, case.pending_items), numbered=True)
    lines.extend([
        "",
        "Siguiente paso seguro: escoger uno y pedirme que lo prepare en limpio.",
        "Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.",
    ])
    return _clean_output("\n".join(lines))


def _record_event_date_label(record: WorkspaceRecord) -> str:
    for value in (record.source.created_at, record.source.observed_at):
        if str(value or "").strip():
            return f"fecha pendiente; registrado en Val: {str(value).strip()}"
    return "fecha pendiente"


def _timeline_event_status(record: WorkspaceRecord) -> str:
    status = _friendly_status(record.source.status)
    confidence = _friendly_confidence(record.source.confidence)
    return f"estado: {status}; confianza: {confidence}"


def render_workspace_timeline_section(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None) -> str:
    lines = [
        f"Tany, esta es la línea de tiempo que tengo para {case.title}. Es lectura de trabajo: no estoy creando ni cambiando eventos.",
        "",
        "🧭 Línea de tiempo",
        "",
        "Eventos confirmados en Val",
    ]
    if case.timeline_events:
        for idx, record in enumerate(case.timeline_events, start=1):
            lines.append(f"{idx}. {_record_event_date_label(record)} · {record.text}")
            lines.append(f"   - {_timeline_event_status(record)}")
    else:
        lines.append("1. No tengo eventos fuente-etiquetados todavía.")

    lines.extend(["", "Eventos por confirmar"])
    if case.timeline_events:
        lines.append("1. Confirmar con Nora qué eventos/documentos tienen efecto legal vigente y cuáles son solo antecedentes.")
    else:
        lines.append("1. Falta convertir documentos/notas en eventos con fecha verificable.")

    lines.extend(
        [
            "",
            "Huecos / falta fecha",
            "1. Ordenar documentos por fecha real del documento, fecha de presentación y fecha de inscripción si aplica.",
            "2. Separar fecha del evento legal de la fecha en que Val detectó o registró el documento.",
            "",
            "Preguntas para Nora",
            '1. "¿Cuál es el orden correcto de estos documentos y actuaciones?"',
            '2. "¿Qué fecha manda legalmente: auto, oficio, registro o inscripción?"',
            "",
            "Próximo paso sugerido",
            '1. "Val, muéstrame documentos del Caso Finca" para escoger qué documento ordenar primero.',
            "",
            "Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.",
        ]
    )
    return _clean_output("\n".join(lines))


def render_workspace_timeline_gaps_section(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None) -> str:
    lines = [
        f"Tany, esto es lo que falta ordenar por fecha en {case.title}. Lo mantengo separado para no venderte seguridad falsa con moñito.",
        "",
        "Huecos / falta fecha",
        "1. Fecha exacta de cada auto, oficio o actuación importante.",
        "2. Fecha en que cada documento empezó a tener efecto, si tuvo alguno.",
        "3. Qué documento es el más reciente y si cambia lo anterior.",
        "",
        "Eventos por confirmar",
    ]
    if case.timeline_events:
        for idx, record in enumerate(case.timeline_events, start=1):
            lines.append(f"{idx}. {record.text} ({_record_event_date_label(record)}; {_timeline_event_status(record)})")
    else:
        lines.append("1. No tengo eventos confirmados en Val todavía.")
    lines.extend(
        [
            "",
            "Preguntas para Nora",
            '1. "¿Qué fecha debo usar como referencia principal para explicar el caso?"',
            '2. "¿Hay algún documento más reciente que cambie el orden de los hechos?"',
            "",
            "Próximo paso sugerido",
            '1. "Val, muéstrame la línea de tiempo del Caso Finca"',
            "",
            "Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.",
        ]
    )
    return _clean_output("\n".join(lines))


def render_workspace_view(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None, view: str = "compact") -> str:
    if view.startswith("document_summary:"):
        try:
            number = int(view.split(":", 1)[1])
        except Exception:
            number = 0
        return render_workspace_document_number_summary(case, client_id=client_id, number=number)
    if view == "full":
        return render_workspace_status(case, client_id=client_id)
    if view == "document_details":
        return render_workspace_document_details_section(case, client_id=client_id)
    if view == "documents":
        return render_workspace_documents_section(case, client_id=client_id)
    if view == "questions":
        return render_workspace_questions_section(case, client_id=client_id)
    if view == "pending":
        return render_workspace_pending_section(case, client_id=client_id)
    if view == "timeline":
        return render_workspace_timeline_section(case, client_id=client_id)
    if view == "timeline_gaps":
        return render_workspace_timeline_gaps_section(case, client_id=client_id)
    return render_workspace_compact_status(case, client_id=client_id)


def render_workspace_status(case: WorkspaceCase = CASO_FINCA_WORKSPACE, *, client_id: str | None = None) -> str:
    lines: list[str] = [
        f"Tany, abro {case.title}. Esto es lectura y organizacion; no voy a mover nada.",
        "",
        f"📁 {case.title}",
        f"ID de workspace: {case.case_id}",
        "Fuente del tablero: datos registrados y auditoría de documentos (solo lectura).",
        "",
        "Lo que sabemos",
    ]
    _append_record_lines(lines, _records_or_plain(case.known_records, case.what_we_know))

    lines.extend(["", "Qué falta confirmar"])
    _append_record_lines(lines, _records_or_plain(case.confirmation_records, case.needs_confirmation))

    lines.extend(["", "Documentos relacionados"])
    for idx, doc in enumerate(case.documents, start=1):
        status = f" — {doc.status}" if doc.status else ""
        lines.append(f"{idx}. {doc.title}{status}.{_source_suffix(doc.source)}")
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
        "Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.",
    ])
    return _clean_output("\n".join(lines))


def _split_telegram_text(text: str, *, limit: int = 3600) -> list[str]:
    body = str(text or "").strip()
    if not body:
        return []
    if len(body) <= limit:
        return [body]

    chunks: list[str] = []
    current = ""
    for block in body.split("\n\n"):
        candidate = block if not current else current + "\n\n" + block
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current.strip())
            current = ""
        if len(block) <= limit:
            current = block
            continue
        start = 0
        while start < len(block):
            chunks.append(block[start:start + limit].strip())
            start += limit
    if current:
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


async def _reply_text_chunked(update: Any, text: str, *, limit: int = 3600) -> list[Any]:
    if not update or not getattr(update, "message", None):
        return []
    chunks = _split_telegram_text(text, limit=limit)
    if not chunks:
        return []
    if len(chunks) == 1:
        return [await update.message.reply_text(chunks[0])]
    sent = []
    total = len(chunks)
    for idx, chunk in enumerate(chunks, start=1):
        sent.append(await update.message.reply_text(f"[{idx}/{total}]\n{chunk}"))
    return sent


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
    view = detect_case_workspace_view(text)
    if not view:
        return False
    if view == "document_summary":
        view = f"document_summary:{extract_case_workspace_document_summary_number(text)}"
    await _reply_text_chunked(
        update,
        render_workspace_view(load_caso_finca_workspace_source_labeled(), client_id=client_id, view=view),
    )
    return True
