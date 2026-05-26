import re
from memory_store import _get_conn, get_active_case_id

DEFAULT_VISIBLE_LIMIT = 8

INTENT_PATTERNS = {
    "list_all": [
        "qué documentos",
        "que documentos",
        "qué archivos",
        "que archivos",
        "inventario de documentos",
        "inventario técnico de documentos",
        "inventario tecnico de documentos",
        "detalles técnicos de documentos",
        "detalles tecnicos de documentos",
        "documentos con ids",
        "documentos con id",
        "documentos de finca",
        "documentos de la finca",
        "documentos del caso",
        "documentos de caso",
    ],
    "pdf_only": [
        "qué pdf",
        "que pdf",
        "pdf",
    ],
    "today_only": [
        "hoy",
    ],
    "caption_only": [
        "caption",
        "nota",
        "descripción",
        "descripcion",
    ],
    "registro_publico": [
        "registro público",
        "registro publico",
    ],
}

def detect_intents(text: str) -> set[str]:
    t = (text or "").lower()
    found = set()

    for intent, markers in INTENT_PATTERNS.items():
        if any(m in t for m in markers):
            found.add(intent)

    return found

def _parse_note(note: str) -> dict:
    note = note or ""

    file_match = re.search(r"- Archivo:\s*(.+)", note)
    vfms_match = re.search(r"- VFMS ingest_id:\s*(.+)", note)
    caption_match = re.search(r"- Nota usuario:\s*(.+)", note)
    state_match = re.search(r"- Estado:\s*(.+)", note)

    return {
        "filename": file_match.group(1).strip() if file_match else "desconocido",
        "vfms_id": vfms_match.group(1).strip() if vfms_match else "?",
        "caption": caption_match.group(1).strip() if caption_match else "",
        "state": state_match.group(1).strip() if state_match else "",
        "raw": note.lower(),
        "has_caption": bool(caption_match and caption_match.group(1).strip()),
    }


def _normalize_query_text(text: str) -> str:
    try:
        import unicodedata

        norm = unicodedata.normalize("NFKD", (text or "").lower())
        norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    except Exception:
        norm = (text or "").lower()

    norm = re.sub(r"[¿?¡!.,:;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(val|valeria|vale)\s+", "", norm).strip()
    return norm


def _looks_like_technical_inventory_request(text: str) -> bool:
    norm = _normalize_query_text(text)
    markers = (
        "inventario tecnico de documentos",
        "inventario tecnico",
        "detalles tecnicos de documentos",
        "detalles tecnicos",
        "documentos con ids",
        "documentos con id",
        "con ids",
        "con id",
        "modo tecnico",
        "vista tecnica",
    )
    return any(marker in norm for marker in markers)


def _clean_filename(filename: str) -> str:
    filename = (filename or "").strip()
    filename = filename.replace("\\", "/").split("/")[-1].strip()
    if "__" in filename:
        filename = filename.split("__", 1)[1].strip()
    filename = re.sub(r"^(?:20\d{6}_\d{6}|[0-9a-f]{8,})[-_\s]+", "", filename, flags=re.I)
    return filename or "documento"


def _filename_kind(filename: str) -> str:
    low = (filename or "").lower()
    if low.endswith((".jpg", ".jpeg", ".png", ".heic", ".webp")):
        return "image"
    if low.endswith(".pdf"):
        return "pdf"
    if low.endswith((".doc", ".docx")):
        return "word"
    if low.endswith((".txt", ".md")):
        return "text"
    return "document"


def _type_label(filename: str) -> str:
    kind = _filename_kind(filename)
    return {
        "image": "foto",
        "pdf": "PDF",
        "word": "Word",
        "text": "texto",
        "document": "desconocido",
    }.get(kind, "desconocido")


def _looks_generic_filename(filename: str) -> bool:
    clean = _clean_filename(filename)
    stem = clean.rsplit(".", 1)[0] if "." in clean else clean
    normalized = stem.replace("_", " ").replace("-", " ").strip().lower()
    return bool(
        not normalized
        or normalized in {"documento", "documento registrado", "scan", "scanned", "untitled", "sin titulo"}
        or re.fullmatch(r"(img|image|scan|documento|doc)?\s*\d{3,}", normalized or "", flags=re.I)
        or re.fullmatch(r"[0-9a-f\s_-]{8,}", normalized or "", flags=re.I)
    )


def _display_title(item: dict) -> str:
    filename = _clean_filename(item.get("filename") or "")
    caption = re.sub(r"\s+", " ", (item.get("caption") or "").strip())
    kind = _filename_kind(filename)

    if kind == "image":
        return "Foto reciente"
    if kind == "text":
        return "Nota de texto"
    if kind == "word":
        return "Documento Word"

    title = filename.rsplit(".", 1)[0] if "." in filename else filename
    title = title.replace("_", " ").replace("-", " ")
    title = re.sub(r"\s+", " ", title).strip()

    if not title or re.fullmatch(r"[0-9a-f\s_-]{8,}", title, flags=re.I):
        title = "Documento registrado"

    if caption and title == "Documento registrado":
        title = caption

    if len(title) > 70:
        title = title[:67].rstrip() + "..."

    return title or "Documento registrado"


def _document_status(item: dict) -> str:
    filename = item.get("filename") or ""
    kind = _filename_kind(filename)
    state = (item.get("state") or "").lower()
    raw = (item.get("raw") or "").lower()
    combined = f"{state}\n{raw}"

    text_markers = (
        "texto leído",
        "texto leido",
        "texto indexado",
        "texto extraído",
        "texto extraido",
        "extracted",
        "transcrito",
        "ocr listo",
    )
    review_markers = (
        "requiere ocr",
        "ocr pendiente",
        "pendiente de ocr",
        "requiere revisión",
        "requiere revision",
        "por revisar",
        "manual review",
        "sin texto",
    )
    summary_markers = (
        "resumen disponible",
        "summary available",
        "summary_ready",
        "resumen listo",
    )

    if any(marker in combined for marker in summary_markers):
        return "resumen disponible"
    if any(marker in combined for marker in text_markers):
        return "texto leído"
    if any(marker in combined for marker in review_markers):
        if kind == "word":
            return "guardado sin extracción"
        return "necesita OCR/revisión"
    if kind == "image":
        return "necesita OCR/revisión"
    if item.get("state"):
        return "estado por revisar"
    return "guardado sin extracción"


def _is_legacy_noise(item: dict) -> bool:
    searchable = f"{item.get('filename') or ''}\n{item.get('caption') or ''}\n{item.get('raw') or ''}".lower()
    return any(marker in searchable for marker in ("test", "prueba", "dummy", "sample", "foto_prueba"))


def _inventory_sort_key(pair) -> tuple:
    item, status = pair
    is_legacy = _is_legacy_noise(item)
    if status == "resumen disponible":
        status_rank = 0
    elif status == "texto leído":
        status_rank = 1
    elif "OCR/revisión" in status or status == "estado por revisar":
        status_rank = 2
    else:
        status_rank = 3
    return (
        1 if is_legacy else 0,
        status_rank,
    )


def _render_document_inventory_technical(parsed: list[dict], case_id: str, *, limit: int = 15) -> str:
    lines = [f"📎 Documentos registrados para CASE:{case_id}:\n"]

    for p in parsed[:limit]:
        lines.append(f"- {p['filename']}")

        if p["caption"]:
            lines.append(f"  Nota: {p['caption']}")

        if p["vfms_id"]:
            lines.append(f"  VFMS: {p['vfms_id']}")

        if p["state"]:
            lines.append(f"  Estado: {p['state']}")

        lines.append(f"  Registro: #{p['id']} · {p['created_at']}")
        lines.append("")

    return "\n".join(lines).strip()


def render_document_inventory_compact(parsed: list[dict], *, visible_limit: int = DEFAULT_VISIBLE_LIMIT) -> str:
    total = len(parsed)
    visible_limit = max(1, min(int(visible_limit or DEFAULT_VISIBLE_LIMIT), 8))

    status_rows = [(item, _document_status(item)) for item in parsed]
    text_read_count = sum(1 for _, status in status_rows if status in {"texto leído", "resumen disponible"})
    summary_count = sum(1 for _, status in status_rows if status == "resumen disponible")
    review_count = sum(1 for _, status in status_rows if "OCR/revisión" in status or status == "estado por revisar")
    sorted_rows = sorted(status_rows, key=lambda pair: str(pair[0].get("created_at") or ""), reverse=True)
    sorted_rows = sorted(sorted_rows, key=_inventory_sort_key)

    lines = [
        "📎 Documentos registrados",
        "",
        "Resumen:",
        f"- {min(total, visible_limit)} de {total} documento(s) mostrado(s).",
        f"- {text_read_count} con texto leído.",
        f"- {summary_count} con resumen disponible.",
        f"- {review_count} necesitan OCR/revisión manual.",
        "",
    ]

    generic_hint_needed = False
    for idx, (item, status) in enumerate(sorted_rows[:visible_limit], start=1):
        filename = _clean_filename(item.get("filename") or "")
        date = str(item.get("created_at") or "").strip()[:10] or "sin fecha"
        type_label = _type_label(filename)
        title = _display_title(item)
        legacy = " · histórico/test" if _is_legacy_noise(item) else ""
        if _looks_generic_filename(filename):
            generic_hint_needed = True
        lines.append(f"{idx}. {title} — {date} · {type_label} · {status}{legacy}.")

    hidden = max(0, total - visible_limit)
    if hidden:
        lines.extend(["", f"Hay {hidden} documento(s) más no mostrados."])

    if generic_hint_needed:
        lines.extend(["", "Veo al menos un nombre genérico; puedo ayudarte a ponerle un nombre más claro."])

    lines.extend([
        "",
        "Siguientes acciones útiles:",
        "- pídeme el resumen de un documento",
        "- renombra o clasifica este documento",
        "- extrae fechas importantes",
        "- prepara paquete para Nora",
        "",
        "Límite: esto organiza información registrada; no sustituye revisión legal o profesional.",
    ])

    return "\n".join(lines).strip()


async def maybe_handle_document_query(update, context, chat_id: int, text: str) -> bool:
    # CAPABILITIES ESCAPE GUARD
    # This query handler must not hijack "Val, qué puedes hacer hoy?"
    # and return CASE document inventory. Capabilities belongs to client_context_reader.
    try:
        dq_norm = _normalize_query_text(text)

        capability_markers = (
            "que puedes hacer hoy",
            "que puedes hacer",
            "que sabes hacer",
            "como me puedes ayudar",
            "capacidades",
            "que eres",
            "quien eres",
        )

        if any(m in dq_norm for m in capability_markers):
            return False
    except Exception:
        pass

    intents = detect_intents(text)

    if not intents:
        return False

    case_id = get_active_case_id(int(chat_id))
    if not case_id:
        return False

    conn = _get_conn()
    conn.row_factory = None
    cur = conn.cursor()

    cur.execute("""
    select id, created_at, note_text
    from case_notes
    where case_id=?
      and source='telegram_attachment_vfms'
    order by id desc
    limit 100
    """, (case_id,))

    rows = cur.fetchall()
    conn.close()

    # DB already returns newest first

    parsed = []
    seen = set()

    for rid, created_at, note in rows:
        item = _parse_note(note)

        filename = item["filename"]
        caption = item["caption"]
        raw = item["raw"]

        if "pdf_only" in intents:
            if not filename.lower().endswith(".pdf"):
                continue

        if "caption_only" in intents:
            if not item["has_caption"]:
                continue

        if "registro_publico" in intents:
            searchable = f"{filename}\n{caption}\n{raw}".lower()

            registry_markers = (
                "registro público",
                "registro publico",
                "finca",
                "folio",
                "tomo",
                "rollo",
                "escritura",
            )

            if not any(m in searchable for m in registry_markers):
                continue

        dedupe_key = re.sub(
            r"\s+",
            "",
            item["filename"].strip().lower()
        )

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)

        parsed.append({
            "id": rid,
            "created_at": created_at,
            **item,
        })

    if not parsed:
        if _looks_like_technical_inventory_request(text):
            reply = f"No encontré documentos que coincidan en CASE:{case_id}."
        else:
            reply = (
                "📎 Documentos registrados\n\n"
                "No encontré documentos registrados que coincidan con esa consulta.\n\n"
                "Límite: esto organiza información registrada; no sustituye revisión legal o profesional."
            )
        await update.message.reply_text(
            reply
        )
        return True

    if _looks_like_technical_inventory_request(text):
        reply = _render_document_inventory_technical(parsed, case_id)
    else:
        reply = render_document_inventory_compact(parsed)

    await update.message.reply_text(reply)
    return True
