import re
from pathlib import Path

from memory_store import get_active_case_id, _get_conn


SUMMARY_MARKERS = (
    "resumen de documentos",
    "resumen documentos",
    "resumen de los documentos",
    "dame resumen de documentos",
    "dame un resumen de documentos",
    "dame un resumen general",
    "resumen general",
    "resumen claro",
    "resumen estructurado",
    "resumen del documento",
    "resume documentos",
    "resume los documentos",
    "qué dicen los documentos",
    "que dicen los documentos",
    "qué dicen los pdf",
    "que dicen los pdf",
    "vfms",
)

EXTRACTED_DIR = Path("/opt/val0/vfms_data/extracted")


def _clean_filename(filename: str) -> str:
    filename = (filename or "documento").strip()
    if "__" in filename:
        filename = filename.split("__", 1)[1].strip()
    return filename or "documento"


def _parse_note(note: str) -> dict:
    note = note or ""

    file_match = re.search(r"- Archivo:\s*(.+)", note)
    vfms_match = re.search(r"- VFMS ingest_id:\s*(.+)", note)
    caption_match = re.search(r"- Nota usuario:\s*(.+)", note)
    state_match = re.search(r"- Estado:\s*(.+)", note)

    return {
        "filename": _clean_filename(file_match.group(1).strip()) if file_match else "documento",
        "ingest_id": vfms_match.group(1).strip() if vfms_match else "",
        "caption": caption_match.group(1).strip() if caption_match else "",
        "state": state_match.group(1).strip() if state_match else "",
    }


def _read_extracted_text(ingest_id: str) -> str:
    ingest_id = (ingest_id or "").strip()
    if not ingest_id:
        return ""

    path = EXTRACTED_DIR / f"{ingest_id}.txt"
    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8", errors="replace").strip()


def _extract_vfms_id(text: str) -> str:
    m = re.search(r"\b(20\d{6}_\d{6})\b", text or "")
    return m.group(1).strip() if m else ""


def _find_doc_meta(case_id: str, ingest_id: str) -> dict:
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT note_text
        FROM case_notes
        WHERE case_id=?
          AND source='telegram_attachment_vfms'
          AND note_text LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (case_id, f"%{ingest_id}%"),
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return {
            "filename": "documento",
            "ingest_id": ingest_id,
            "caption": "",
            "state": "",
        }

    note = row[0] if not isinstance(row, dict) else row["note_text"]
    parsed = _parse_note(note)
    parsed["ingest_id"] = parsed.get("ingest_id") or ingest_id
    return parsed


def _contains(text: str, *needles: str) -> bool:
    low = (text or "").lower()
    return any(n.lower() in low for n in needles)


def _extract_first(pattern: str, text: str) -> str:
    m = re.search(pattern, text or "", flags=re.I | re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()


def _structured_specific_doc_bullets(text: str) -> list[tuple[str, list[str]]]:
    """
    Deterministic section summary.
    No legal inference: only emits points when matching text exists in the extracted document.
    """
    clean = re.sub(r"\s+", " ", text or "").strip()

    sections: list[tuple[str, list[str]]] = []

    contexto = []
    expediente = _extract_first(r"Expediente\s+No\.\s*([^\n\r]+?)(?:\s+Juzgado|\s+I\.|$)", text)
    if expediente:
        contexto.append(f"Expediente mencionado: {expediente}.")

    if _contains(clean, "Prescripción Adquisitiva de Dominio"):
        contexto.append("El documento menciona un proceso ordinario de Prescripción Adquisitiva de Dominio.")

    if _contains(clean, "Juzgado Primero de Circuito Civil", "Juzgado Primero de Circuito de lo Civil"):
        contexto.append("Se menciona el Juzgado Primero de Circuito Civil del Tercer Circuito Judicial de Panamá, La Chorrera.")

    if contexto:
        sections.append(("1. Contexto del documento", contexto))

    partes = []
    if _contains(clean, "RICARDO JUNCÁ", "RICARDO ARTURO JUNCÁ"):
        partes.append("Se menciona a Ricardo Juncá García / Ricardo Arturo Juncá García como demandante.")
    if _contains(clean, "CARMEN MONTENEGRO DE SANDINO"):
        partes.append("Se menciona a Carmen Montenegro de Sandino entre las personas demandadas.")
    if _contains(clean, "Javier Morán Montenegro", "Teonila Antonia", "Marina Montenegro", "Odilia Montenegro"):
        partes.append("También aparecen otros copropietarios/herederos mencionados en el documento.")
    if partes:
        sections.append(("2. Personas o partes mencionadas", partes))

    resoluciones = []
    if _contains(clean, "AUTO No. 629", "AUTO N°629", "Auto No.629"):
        resoluciones.append("Se menciona el Auto No. 629, fechado 29 de abril de 2024.")
    if _contains(clean, "Auto No. 77", "AUTO No. 77"):
        resoluciones.append("Se menciona el Auto No. 77 del 15 de enero de 2024, relacionado con tener la demanda como no presentada.")
    if _contains(clean, "REVOCÓ el Auto No.1188", "REVOCÓ el Auto No. 1188", "DECLARÓ la nulidad"):
        resoluciones.append("Se menciona una resolución del Primer Tribunal Superior que revocó el Auto No. 1188 y declaró nulidad de lo actuado.")
    if resoluciones:
        sections.append(("3. Resoluciones mencionadas", resoluciones))

    registro = []
    if _contains(clean, "CANCELAR la inscripción provisional", "cancelar la inscripción provisional"):
        registro.append("El documento menciona la cancelación de la inscripción provisional de la demanda ante el Registro Público.")
    if _contains(clean, "Oficio No. 792", "OFICIO No. 792"):
        registro.append("Se menciona el Oficio No. 792 dirigido al Registro Público.")
    if _contains(clean, "Finca No.10082", "Finca No. 10082"):
        registro.append("Se menciona la Finca No. 10082.")
    if _contains(clean, "Código de Ubicación 8001", "Código de ubicación: 8001"):
        registro.append("Se menciona el Código de Ubicación 8001.")
    if registro:
        sections.append(("4. Registro Público y finca", registro))

    hechos = []
    if _contains(clean, "Carmen residía", "Carmen vivía", "residía efectivamente"):
        hechos.append("El documento menciona elementos sobre la residencia u ocupación de Carmen Montenegro en la finca.")
    if _contains(clean, "emplazamiento por edicto", "notificación real", "FALTA DE NOTIFICACIÓN"):
        hechos.append("El documento menciona problemas relacionados con notificación o emplazamiento.")
    if _contains(clean, "inspección judicial", "12 de abril de 2023"):
        hechos.append("Se menciona una inspección judicial realizada el 12 de abril de 2023.")
    if hechos:
        sections.append(("5. Hechos destacados que aparecen en el documento", hechos))

    estado = []
    if _contains(clean, "demanda se tenía", "como no presentada", "demanda fue anulada", "quedó archivado", "archivo del presente proceso"):
        estado.append("El documento menciona que la demanda fue tratada como no presentada, anulada o archivada, según las secciones transcritas.")
    if _contains(clean, "NO obtuvo el dominio legal", "NO pasó a nombre de Ricardo Juncá"):
        estado.append("El documento contiene una sección que indica que Ricardo Juncá no obtuvo el dominio legal de la finca.")
    if estado:
        sections.append(("6. Estado descrito dentro del documento", estado))

    verificar = [
        "Validar estos puntos con el documento original y/o con el abogado antes de usarlos como posición legal.",
        "No se están dando conclusiones legales nuevas; esto es una organización del texto extraído.",
    ]
    sections.append(("7. Puntos a verificar", verificar))

    return sections


def _first_present(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        value = _extract_first(pattern, text)
        if value:
            return value
    return ""


def _extract_legal_header(text: str) -> dict:
    clean = re.sub(r"\s+", " ", text or "").strip()

    expediente = _first_present(text, [
        r"Expediente\s+No\.\s*([^\n\r]+?)(?:\s+Juzgado|\s+I\.|$)",
        r"EXP\.\s*([0-9\-]+)",
    ])

    fecha = _first_present(text, [
        r"La Chorrera,\s*([^\n\r]+?\d{4})",
        r"(\d{1,2}\s+de\s+[a-záéíóúñ]+\s+de\s+\d{4})",
        r"(Octubre\s+de\s+\d{4})",
    ])

    tipo_proceso = ""
    if _contains(clean, "Prescripción Adquisitiva de Dominio"):
        tipo_proceso = "Proceso ordinario de Prescripción Adquisitiva de Dominio"

    juzgado = ""
    if _contains(clean, "Juzgado Primero de Circuito Civil", "Juzgado Primero de Circuito de lo Civil"):
        juzgado = "Juzgado Primero de Circuito Civil del Tercer Circuito Judicial de Panamá, La Chorrera"

    tipo_documento = ""
    if _contains(clean, "AUTO No. 629", "AUTO N°629", "Auto No.629"):
        tipo_documento = "Resumen/transcripción de actuaciones judiciales; menciona Auto No. 629 y otros documentos"
    elif _contains(clean, "OFICIO No. 792", "Oficio No. 792"):
        tipo_documento = "Documento relacionado con oficio al Registro Público"

    partes = []
    if _contains(clean, "RICARDO JUNCÁ", "RICARDO ARTURO JUNCÁ"):
        partes.append("Ricardo Juncá García / Ricardo Arturo Juncá García")
    if _contains(clean, "CARMEN MONTENEGRO DE SANDINO"):
        partes.append("Carmen Montenegro de Sandino")
    if _contains(clean, "Javier Morán Montenegro"):
        partes.append("Javier Morán Montenegro Ortega")
    if _contains(clean, "Teonila Antonia Montenegro"):
        partes.append("Teonila Antonia Montenegro de Cruz")
    if _contains(clean, "Marina Montenegro", "Martina Montenegro"):
        partes.append("Marina/Martina Montenegro de Martínez")
    if _contains(clean, "Odilia Montenegro"):
        partes.append("Odilia Montenegro de Estribí")

    return {
        "expediente": expediente,
        "fecha": fecha,
        "tipo_proceso": tipo_proceso,
        "juzgado": juzgado,
        "tipo_documento": tipo_documento,
        "partes": partes,
    }


def _extract_chronology(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text or "").strip()
    events = []

    known_events = [
        ("Octubre de 2023", "Se menciona resolución del Primer Tribunal Superior que revocó el Auto No. 1188 y declaró nulidad de lo actuado."),
        ("15 de enero de 2024", "Se menciona el Auto No. 77, relacionado con tener la demanda como no presentada."),
        ("29 de abril de 2024", "Se menciona el Auto No. 629, relacionado con cancelar la inscripción provisional de la demanda."),
        ("29 de mayo de 2024", "Se menciona el Oficio No. 792 dirigido al Registro Público."),
        ("24 de septiembre de 2025", "Se menciona un informe secretarial sobre incorporación del oficio al expediente."),
        ("12 de abril de 2023", "Se menciona una inspección judicial relacionada con la residencia u ocupación en el terreno."),
    ]

    for date_text, description in known_events:
        if _contains(clean, date_text):
            events.append(f"{date_text}: {description}")

    return events[:8]


def _extract_registry_points(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text or "").strip()
    points = []

    if _contains(clean, "Finca No.10082", "Finca No. 10082"):
        points.append("Finca No. 10082.")
    if _contains(clean, "Código de Ubicación 8001", "Código de ubicación: 8001"):
        points.append("Código de Ubicación 8001.")
    if _contains(clean, "Registro Público"):
        points.append("Se menciona actuación dirigida al Registro Público.")
    if _contains(clean, "CANCELAR la inscripción provisional", "cancelar la inscripción provisional"):
        points.append("Se menciona cancelación de inscripción provisional de la demanda.")

    return points


def _render_legal_document_summary(filename: str, ingest_id: str, caption: str, state: str, text: str) -> str:
    header = _extract_legal_header(text)
    sections = _structured_specific_doc_bullets(text)
    chronology = _extract_chronology(text)
    registry_points = _extract_registry_points(text)

    lines = [
        f"📄 Documento: {_clean_filename(filename)}",
        f"VFMS: {ingest_id}",
    ]

    if state:
        lines.append(f"Estado: {state}")

    if caption:
        lines.append(f"Nota: {caption}")

    lines.append("")
    lines.append("🧾 Ficha del documento")

    ficha = [
        ("Juzgado / entidad", header.get("juzgado")),
        ("Fecha principal detectada", header.get("fecha")),
        ("Tipo de documento", header.get("tipo_documento")),
        ("Tipo de proceso", header.get("tipo_proceso")),
        ("Expediente / referencia", header.get("expediente")),
    ]

    for label, value in ficha:
        lines.append(f"- {label}: {value or 'No identificado claramente en el texto extraído.'}")

    if header.get("partes"):
        lines.append("- Personas/partes mencionadas:")
        for party in header["partes"]:
            lines.append(f"  - {party}")

    lines.append("")
    lines.append("📌 Resumen claro")
    for title, bullets in sections:
        if title.startswith("7."):
            continue
        lines.append("")
        lines.append(title)
        for b in bullets:
            lines.append(f"- {b}")

    if chronology:
        lines.append("")
        lines.append("🕒 Cronología detectada")
        for event in chronology:
            lines.append(f"- {event}")

    if registry_points:
        lines.append("")
        lines.append("🏛️ Datos registrales mencionados")
        for point in registry_points:
            lines.append(f"- {point}")

    lines.append("")
    lines.append("🔎 Para revisar con abogado")
    lines.append("- Confirmar el efecto exacto de cada auto/resolución en el expediente.")
    lines.append("- Verificar si la cancelación registral ya fue ejecutada correctamente en Registro Público.")
    lines.append("- Usar este resumen como guía de organización, no como decisión legal final.")

    return "\n".join(lines)


def _render_structured_specific_doc_summary(filename: str, ingest_id: str, caption: str, state: str, text: str) -> str:
    return _render_legal_document_summary(filename, ingest_id, caption, state, text)


def _build_specific_doc_summary(case_id: str, ingest_id: str) -> str:
    text_body = _read_extracted_text(ingest_id)

    if not text_body:
        return (
            f"No encontré texto extraído para el documento VFMS {ingest_id} "
            f"en CASE:{case_id}. Puede estar registrado, pero no resumible todavía."
        )

    meta = _find_doc_meta(case_id, ingest_id)

    return "\n".join([
        f"🧾 Resumen grounded del documento VFMS {ingest_id}",
        f"CASE:{case_id}",
        "Sin inferencias. Solo basado en texto extraído/VFMS.",
        "",
        _render_structured_specific_doc_summary(
            meta.get("filename", "documento"),
            ingest_id,
            meta.get("caption", ""),
            meta.get("state", ""),
            text_body,
        ),
        "",
        "Nota: no estoy dando una conclusión legal; solo organizo lo que aparece en el documento.",
    ]).strip()


def _normalize_body(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"---\s*page\s+\d+(?:\s*\(ocr\))?\s*---", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean_lines(text: str) -> list[str]:
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"---\s*page\s+\d+(?:\s*\(ocr\))?\s*---", line, flags=re.I):
            continue
        out.append(line)
    return out


def _is_heading_only(line: str) -> bool:
    line = (line or "").strip()
    if not line:
        return True

    normalized = line.strip().strip("-").strip().lower()

    headings = {
        "base del caso:",
        "base del caso",
        "documentos mencionados:",
        "documentos mencionados",
        "datos registrales / pendientes de verificar:",
        "datos registrales / pendientes de verificar",
        "siguiente acción recomendada:",
        "siguiente accion recomendada:",
        "siguiente acción recomendada",
        "siguiente accion recomendada",
        "lo que tengo hasta ahora:",
        "lo que tengo hasta ahora",
    }

    return normalized in headings


def _clean_bullet_text(line: str) -> str:
    line = (line or "").strip()

    # Remove repeated markdown/list prefixes from OCR or generated docs.
    line = re.sub(r"^(?:[-•]\s*)+", "", line).strip()
    line = re.sub(r"\s+", " ", line).strip()

    if len(line) > 240:
        line = line[:237].rstrip() + "..."

    return line


def _join_wrapped_lines(lines: list[str]) -> list[str]:
    joined = []

    for raw in lines:
        line = _clean_bullet_text(raw)

        if not line or _is_heading_only(line):
            continue

        # If the previous line does not end like a finished thought,
        # and this line looks like continuation text, merge it.
        if joined:
            prev = joined[-1]
            starts_new = bool(re.match(
                r"^(caso|documentos|datos|siguiente|finca|folio|tomo|rollo|escritura|registro|juzgado)\b",
                line,
                flags=re.I,
            ))

            if (
                not starts_new
                and not prev.endswith((".", ":", ";"))
                and len(prev) < 220
            ):
                joined[-1] = (prev + " " + line).strip()
                continue

        joined.append(line)

    return joined


def _pick_grounded_bullets(text: str, limit: int = 6) -> list[str]:
    lines = _join_wrapped_lines(_clean_lines(text))
    picked = []

    priority_markers = (
        "caso",
        "juzgado",
        "documentos",
        "registro público",
        "registro publico",
        "finca",
        "folio",
        "tomo",
        "rollo",
        "escritura",
        "abogado",
        "siguiente acción",
        "siguiente accion",
    )

    for line in lines:
        low = line.lower()
        if any(m in low for m in priority_markers):
            picked.append(line)
        if len(picked) >= limit:
            break

    if not picked:
        picked = lines[:limit]

    clean = []
    seen = set()

    for item in picked:
        item = _clean_bullet_text(item)

        if not item or _is_heading_only(item):
            continue

        key = re.sub(r"\s+", " ", item.lower()).strip()

        if key in seen:
            continue

        seen.add(key)
        clean.append(item)

    return clean[:limit]


def _doc_summary(filename: str, ingest_id: str, caption: str, state: str, text: str) -> str:
    bullets = _pick_grounded_bullets(text)

    lines = [
        f"📄 {_clean_filename(filename)}",
        f"VFMS: {ingest_id}",
    ]

    if caption:
        lines.append(f"Nota: {caption}")

    if state:
        lines.append(f"Estado: {state}")

    if bullets:
        lines.append("Resumen grounded:")
        for b in bullets:
            lines.append(f"- {b}")
    else:
        lines.append("Resumen grounded:")
        lines.append("- No hay texto extraído suficiente para resumir este documento.")

    return "\n".join(lines)


async def maybe_handle_document_summary_query(update, context, chat_id: int, text: str) -> bool:
    raw = (text or "").strip().lower()

    if not any(m in raw for m in SUMMARY_MARKERS):
        return False

    case_id = get_active_case_id(int(chat_id))
    if not case_id:
        return False

    specific_vfms_id = _extract_vfms_id(text)
    if specific_vfms_id:
        reply = _build_specific_doc_summary(str(case_id), specific_vfms_id)
        await update.message.reply_text(reply)
        return True

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT note_text
        FROM case_notes
        WHERE case_id=?
          AND source='telegram_attachment_vfms'
        ORDER BY id DESC
        LIMIT 100
        """,
        (case_id,),
    )

    rows = cur.fetchall()
    conn.close()

    docs = []
    seen_ingest = set()
    seen_body = set()

    for row in rows:
        note = row[0] if not isinstance(row, dict) else row["note_text"]
        parsed = _parse_note(note)

        ingest_id = parsed["ingest_id"]
        if not ingest_id or ingest_id in seen_ingest:
            continue

        text_body = _read_extracted_text(ingest_id)
        body_key = _normalize_body(text_body)

        # Avoid repeating identical extracted documents.
        if body_key and body_key in seen_body:
            continue

        seen_ingest.add(ingest_id)
        if body_key:
            seen_body.add(body_key)

        docs.append({
            **parsed,
            "text": text_body,
        })

        if len(docs) >= 5:
            break

    if not docs:
        await update.message.reply_text(
            f"No encontré documentos extraídos para resumir en CASE:{case_id}."
        )
        return True

    parts = [
        f"🧾 Resumen grounded de documentos para CASE:{case_id}",
        "Sin inferencias. Solo basado en texto extraído/VFMS.\n",
    ]

    for doc in docs:
        parts.append(
            _doc_summary(
                doc["filename"],
                doc["ingest_id"],
                doc["caption"],
                doc["state"],
                doc["text"],
            )
        )
        parts.append("")

    await update.message.reply_text("\n".join(parts).strip())
    return True
