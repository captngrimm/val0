import re
import unicodedata
from pathlib import Path



from memory_store import get_active_case_id, _get_conn, insert_case_note


async def _reply_text_chunked(update, text: str, limit: int = 3800):
    """Telegram-safe reply helper for long document summaries."""
    if not update or not getattr(update, "message", None):
        return []

    text = (text or "").strip()
    if not text:
        return []

    chunks = []
    current = ""

    for block in text.split("\n\n"):
        candidate = block if not current else current + "\n\n" + block

        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(block) <= limit:
            current = block
        else:
            start = 0
            while start < len(block):
                chunks.append(block[start:start + limit])
                start += limit

    if current:
        chunks.append(current)

    if len(chunks) <= 1:
        return [await update.message.reply_text(text)]

    sent = []
    total = len(chunks)
    for idx, chunk in enumerate(chunks, start=1):
        prefix = f"[{idx}/{total}]\n"
        sent.append(await update.message.reply_text(prefix + chunk))
    return sent


SUMMARY_MARKERS = (
    # General summary requests (multiple documents)
    "resumen de documentos",
    "resumen documentos",
    "resumen de los documentos",
    "dame resumen de documentos",
    "dame un resumen de documentos",
    "dame un resumen general",
    "resumen general",
    "resumen claro",
    "resumen estructurado",
    "resumen legal de los documentos",
    "resume documentos",
    "resume los documentos",
    "qué dicen los documentos",
    "que dicen los documentos",
    "qué dicen los pdf",
    "que dicen los pdf",
    "observaciones",
    "recomendaciones para hablar con la abogada",
    "hablar con la abogada",
    "cronología",
    "cronologia",
    "tabla cronológica",
    "tabla cronologica",
    "formatos",
    "formato",
    "opciones de resumen",
    "versiones",
    "cómo puedes resumir",
    "como puedes resumir",
    "qué formatos tienes",
    "que formatos tienes",
    "vfms",
    # Specific document summary requests (single, named/numbered document)
    "resumen de",
    "dame resumen de",
    "dame el resumen de",
    "dame resumen del documento",
    "dame el resumen del documento",
    "hazme resumen de",
    "hazme el resumen de",
    "resume el documento",
    "resume el pdf",
    "resumen del documento",
    "resumen legal del documento",
    "resumen legal de documento",
)

NAMING_METADATA_MARKERS = (
    "sugiere nombre para",
    "sugerir nombre para",
    "renombra",
    "clasifica",
    "que es este documento",
    "qué es este documento",
    "organiza este documento",
    "ponle etiquetas a",
    "pon etiquetas a",
    "que nombre le pondrias a",
    "qué nombre le pondrías a",
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
    alias_match = re.search(r"- Alias:\s*(.+)", note)
    tags_match = re.search(r"- Etiquetas:\s*(.+)", note)
    folder_match = re.search(r"- Carpeta sugerida:\s*(.+)", note)
    importance_match = re.search(r"- Por qué importa:\s*(.+)", note)

    return {
        "filename": _clean_filename(file_match.group(1).strip()) if file_match else "documento",
        "ingest_id": vfms_match.group(1).strip() if vfms_match else "",
        "caption": caption_match.group(1).strip() if caption_match else "",
        "state": state_match.group(1).strip() if state_match else "",
        "alias": alias_match.group(1).strip() if alias_match else "",
        "tags": tags_match.group(1).strip() if tags_match else "",
        "folder_suggestion": folder_match.group(1).strip() if folder_match else "",
        "why_it_matters": importance_match.group(1).strip() if importance_match else "",
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
        lines.append("🕒 TABLA CRONOLÓGICA / FECHAS IMPORTANTES")
        lines.append("Fecha | Evento / documento | Por qué importa")
        lines.append("--- | --- | ---")
        for event in chronology:
            if ":" in event:
                date_part, detail_part = event.split(":", 1)
                date_part = date_part.strip()
                detail_part = detail_part.strip()
            else:
                date_part = "Fecha mencionada"
                detail_part = event.strip()

            lines.append(
                f"{date_part} | {detail_part} | Revisar efecto exacto con abogado"
            )

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


SUMMARY_LIMIT_LINE = "Límite: resumo información registrada; no sustituye revisión legal o profesional."


def _render_clean_specific_doc_summary_body(text: str) -> str:
    bullets = _pick_grounded_bullets(text)
    lines = ["📋 Resumen claro"]
    if bullets:
        for bullet in bullets:
            lines.append(f"- {bullet}")
    else:
        lines.append("- No hay texto extraído suficiente para resumir este documento.")

    lines.extend([
        "",
        "Siguientes acciones útiles:",
        "- extraer fechas importantes",
        "- preparar preguntas para Nora",
        "- renombrar o clasificar este documento",
        "",
        SUMMARY_LIMIT_LINE,
    ])
    return "\n".join(lines).strip()


def _clean_specific_doc_summary_body_for_reply(summary_text: str) -> str:
    lines = []
    seen_limit = False
    saw_summary_header = False

    for raw_line in (summary_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue

        low = line.lower()
        if (
            line.startswith("📄")
            or low.startswith("vfms:")
            or low.startswith("id:")
            or low.startswith("estado:")
            or low.startswith("nota:")
            or low.startswith("resumen generado de documento")
            or low.startswith("- vfms ingest_id:")
            or low.startswith("- archivo:")
        ):
            continue

        if "resumen grounded" in low or low in {"📋 resumen", "resumen:"}:
            line = "📋 Resumen claro"

        if "límite:" in low or "limite:" in low or "no sustituye revisión legal" in low:
            if seen_limit:
                continue
            line = SUMMARY_LIMIT_LINE
            seen_limit = True

        if line == "📋 Resumen claro":
            if saw_summary_header:
                continue
            saw_summary_header = True

        lines.append(line)

    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()

    if not any(line == "📋 Resumen claro" for line in lines):
        lines.insert(0, "📋 Resumen claro")

    if not any("Siguientes acciones útiles:" == line for line in lines):
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend([
            "Siguientes acciones útiles:",
            "- extraer fechas importantes",
            "- preparar preguntas para Nora",
            "- renombrar o clasificar este documento",
        ])

    if not any(line == SUMMARY_LIMIT_LINE for line in lines):
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(SUMMARY_LIMIT_LINE)

    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def _looks_like_format_preview_request(text: str) -> bool:
    t = (text or "").lower()
    markers = (
        "formatos",
        "formato",
        "opciones de resumen",
        "versiones",
        "cómo puedes resumir",
        "como puedes resumir",
        "qué formatos tienes",
        "que formatos tienes",
        "muéstrame opciones",
        "muestrame opciones",
    )
    return any(m in t for m in markers)


def _looks_like_combined_legal_summary_request(text: str) -> bool:
    """
    Detects Karen-style natural requests that ask for a legal/document summary
    with chronology, key data, observations, and lawyer-prep recommendations.
    """
    raw = (text or "").lower()
    norm = raw
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
    }
    for src, dst in replacements.items():
        norm = norm.replace(src, dst)

    legal_summary_markers = (
        "resumen legal",
        "resumen del documento",
        "resumen de documento",
        "resumen de documentos",
    )
    structure_markers = (
        "cronologia",
        "datos clave",
        "observaciones",
        "recomendaciones",
        "abogada",
        "abogado",
        "hablar con la abogada",
        "hablar con el abogado",
    )

    return (
        any(m in norm for m in legal_summary_markers)
        and any(m in norm for m in structure_markers)
    )


def _render_combined_legal_documents_summary(case_id: str, docs: list[dict]) -> str:
    """
    Warmer Karen-facing combined legal summary.
    Uses grounded extracted text only; no invented legal certainty.
    """
    extracted_docs = [d for d in docs if (d.get("text") or "").strip()]
    pending_docs = [d for d in docs if not (d.get("text") or "").strip()]

    lines = [
        f"⚖️📚 Resumen legal organizado para CASE:{case_id}",
        "",
        "Insanity, aquí va ordenado para hablar con la abogada sin tener que nadar en papeles como si esto fuera novela de 40 temporadas. 😌",
        "Ojo: esto está basado solo en texto extraído/VFMS. No reemplaza criterio legal y no inventa certezas donde el documento no las da.",
        "",
    ]

    if not extracted_docs:
        lines.extend([
            "📌 Estado rápido",
            "- Tengo documentos registrados, pero ninguno tiene texto extraído suficiente para armar cronología o análisis grounded todavía.",
            "- Las fotos/documentos sin OCR quedan como revisión manual pendiente.",
            "",
            "➡️ Recomendación práctica",
            "- Llevar los archivos/fotos a Nora Santa y pedirle que confirme cuáles tienen valor legal, cuáles faltan y cuáles deben pedirse al Registro Público o al juzgado.",
        ])
        return "\n".join(lines).strip()

    lines.append("1. Resumen ejecutivo")
    lines.append("- Hay documentos registrados del caso del terreno familiar.")
    lines.append("- Algunos documentos tienen texto extraído y permiten organizar hechos, fechas, datos registrales y puntos para consulta.")
    if pending_docs:
        lines.append(f"- También hay {len(pending_docs)} documento(s)/foto(s) registrados sin texto extraído suficiente; esos quedan para OCR o revisión manual.")
    lines.append("")

    all_chronology = []
    all_registry = []
    all_review_points = []

    for idx, doc in enumerate(extracted_docs[:3], start=1):
        filename = _clean_filename(doc.get("filename", "documento"))
        ingest_id = doc.get("ingest_id", "")
        doc_text = doc.get("text", "") or ""

        chronology = _extract_chronology(doc_text)
        registry = _extract_registry_points(doc_text)
        header = _extract_legal_header(doc_text)

        lines.append(f"2.{idx}. Documento revisado: {filename}")
        lines.append(f"- VFMS: {ingest_id}")
        if doc.get("caption"):
            lines.append(f"- Nota: {doc.get('caption')}")
        if doc.get("state"):
            lines.append(f"- Estado: {doc.get('state')}")

        doc_type = header.get("tipo_documento") or "No identificado claramente en el texto extraído."
        court = header.get("juzgado") or "No identificado claramente en el texto extraído."
        process = header.get("tipo_proceso") or "No identificado claramente en el texto extraído."
        expediente = header.get("expediente") or "No identificado claramente en el texto extraído."

        lines.append("- Tipo de documento: " + doc_type)
        lines.append("- Juzgado / entidad: " + court)
        lines.append("- Tipo de proceso: " + process)
        lines.append("- Expediente / referencia: " + expediente)

        if header.get("partes"):
            lines.append("- Partes/personas mencionadas:")
            for party in header["partes"][:8]:
                lines.append(f"  - {party}")

        if registry:
            lines.append("- Datos registrales detectados:")
            for point in registry:
                lines.append(f"  - {point}")
                all_registry.append(point)

        if chronology:
            for event in chronology:
                all_chronology.append((filename, event))

        lines.append("")

    lines.append("3. Cronología detectada")
    if all_chronology:
        for filename, event in all_chronology[:10]:
            lines.append(f"- {event} ({filename})")
    else:
        lines.append("- No detecté fechas suficientes en el texto extraído para una cronología confiable.")
    lines.append("")

    lines.append("4. Datos clave para llevar a Nora")
    if all_registry:
        seen = set()
        for point in all_registry:
            key = point.lower()
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"- {point}")
    else:
        lines.append("- No detecté datos registrales claros en los textos extraídos revisados.")
    lines.append("- Confirmar con Nora el efecto exacto de cada auto, oficio o actuación mencionada.")
    lines.append("")

    lines.append("5. Observaciones")
    lines.append("- Lo más útil ahora no es sacar conclusiones legales aquí, sino ordenar documentos, fechas y preguntas.")
    lines.append("- Cuando el documento diga que algo fue cancelado, archivado, revocado o tenido como no presentado, Nora debe confirmar el efecto procesal y registral exacto.")
    if pending_docs:
        lines.append("- Las fotos/documentos sin texto extraído están guardados, pero necesitan OCR o revisión manual antes de resumirse con confianza.")
    lines.append("")

    lines.append("6. Recomendaciones para hablar con la abogada")
    lines.append("- Preguntar qué documento prueba mejor el estado actual de la finca y del proceso.")
    lines.append("- Preguntar si la cancelación de inscripción provisional ya aparece reflejada en Registro Público.")
    lines.append("- Preguntar qué falta pedir: certificación registral actualizada, copia íntegra del expediente, autos/oficios específicos o documentos notariales.")
    lines.append("- Pedirle a Nora que priorice próximos pasos por urgencia: Registro Público, juzgado, herederos/documentos familiares, o corrección de información faltante.")
    lines.append("")

    lines.append("7. Pendiente manual / OCR")
    if pending_docs:
        for doc in pending_docs[:5]:
            lines.append(f"- { _clean_filename(doc.get('filename', 'documento')) }: registrado, pero sin texto extraído suficiente para resumir.")
    else:
        lines.append("- No veo documentos pendientes sin texto dentro de los últimos documentos revisados.")

    return "\n".join(lines).strip()



def _format_preview_reply() -> str:
    return """Karen, te puedo mostrar el mismo documento en varios sabores 😄

La idea no es que adivines cuál quieres. Te doy mini ejemplos y tú escoges el que más te sirva.

1. Resumen corto 🧃
Para entender rápido sin meterte en la maleza.

Ejemplo:
“Este documento trata de un proceso de prescripción adquisitiva relacionado con la Finca 10082. Menciona autos judiciales, actuaciones del Registro Público y una cancelación de inscripción provisional.”

2. Ficha legal 📎
Para tener los datos ordenados como ficha.

Ejemplo:
- Juzgado / entidad:
- Expediente:
- Fecha principal:
- Partes mencionadas:
- Finca:
- Autos / oficios:
- Datos registrales:

3. Informe para abogado ⚖️
Para llevarlo más presentable a consulta.

Ejemplo:
“El documento menciona un proceso de prescripción adquisitiva, las partes involucradas, resoluciones relevantes y puntos que conviene revisar con el abogado antes de tomar decisiones.”

4. Tabla cronológica 🕒
Para ordenar el relajo por fechas, porque estos casos parecen serie larga con capítulos perdidos.

Ejemplo:
Fecha | Evento | Importancia
--- | --- | ---
2023 | Resolución del tribunal | Revisar efecto procesal
Enero 2024 | Auto No. 77 | Confirmar consecuencia
Abril 2024 | Auto No. 629 | Confirmar efecto registral
Mayo 2024 | Oficio al Registro Público | Verificar ejecución
Septiembre 2025 | Informe secretarial | Revisar estado actual

5. Tabla de datos importantes 🧾
Para ver los datos duros sin novela.

Ejemplo:
- Expediente:
- Finca:
- Código de ubicación:
- Juzgado:
- Personas:
- Autos:
- Oficios:
- Fechas importantes:

Dime cuál quieres, o dime “mezcla de varias” y te lo armo sin drama. Cero formulario del gobierno, prometido 😌"""




def _extract_specific_doc_name(text: str) -> str:
    """
    Extract document name/ID from specific summary requests.
    
    Examples:
    - "dame el resumen de six pdf" -> "six pdf"
    - "resumen de six_pdf.pdf" -> "six_pdf.pdf"
    - "resume el documento 1" -> "1"
    
    Note: Filters out generic requests like "resumen de documentos" (plural).
    """
    text_low = (text or "").lower()
    
    # Remove Val prefix if present
    text_low = re.sub(r"^val[,\s]+", "", text_low).strip()
    
    # Generic document/plural patterns to exclude
    generic_markers = (
        "documentos",
        "los documentos",
        "de los documentos",
        "los pdf",
        "de los pdf",
    )
    
    # Pattern: "resumen de X", "dame resumen de X", "hazmo resumen de X", etc.
    patterns = [
        r"(?:dame|hazme)?\s*(?:el)?\s*resumen\s+de\s+(.+?)(?:\s*$|\?|!)",
        r"(?:dame|hazme)?\s*(?:el)?\s*resumen\s+del\s+documento\s+(.+?)(?:\s*$|\?|!)",
        r"(?:resume)\s+(?:el)?\s*documento\s+(.+?)(?:\s*$|\?|!)",
        r"(?:resume)\s+(?:el)?\s*pdf\s+(.+?)(?:\s*$|\?|!)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_low, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up: remove trailing punctuation
            name = re.sub(r"[!?,;\s]+$", "", name).strip()
            if not re.search(r"\.(pdf|doc|docx|txt|jpg|jpeg|png)$", name, flags=re.I):
                name = name.rstrip(".").strip()
            
            # Reject if it's a generic marker
            name_lower = name.lower()
            if any(marker in name_lower for marker in generic_markers):
                return ""
            
            if name:
                return name
    
    return ""


def _extract_document_naming_target(text: str) -> str:
    raw = (text or "").strip()
    low = raw.lower()
    low = re.sub(r"^val[,\s]+", "", low).strip()
    low = re.sub(r"[?!.]+$", "", low).strip()

    patterns = [
        r"(?:sugiere|sugerir)\s+nombre\s+para\s+(.+)$",
        r"renombra\s+(.+)$",
        r"clasifica\s+(.+)$",
        r"(?:organiza)\s+(.+)$",
        r"ponle\s+etiquetas\s+a\s+(.+)$",
        r"pon\s+etiquetas\s+a\s+(.+)$",
        r"(?:que|qué)\s+nombre\s+le\s+pondr[ií]as\s+a\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, low, flags=re.I)
        if not match:
            continue
        target = (match.group(1) or "").strip()
        if target in {"este documento", "el documento", "documento"}:
            return ""
        return target
    return ""


def looks_like_document_naming_metadata_request(text: str) -> bool:
    low = (text or "").lower()
    return any(marker in low for marker in NAMING_METADATA_MARKERS)


_DOC_EXTENSION_WORDS = {"pdf", "doc", "docx", "txt", "jpg", "jpeg", "png", "heic", "webp"}


def _normalize_doc_name(name: str) -> str:
    """
    Normalize a document name for matching.
    Handles variations like "six pdf" vs "six_pdf.pdf"
    """
    name = (name or "").strip().lower()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    name = re.sub(r"\.(pdf|doc|docx|txt|jpg|jpeg|png)$", "", name, flags=re.I)
    tokens = [
        token for token in re.split(r"[^a-z0-9]+", name)
        if token and token not in _DOC_EXTENSION_WORDS and token not in {"documento", "doc"}
    ]
    return "".join(tokens)


def _compact_doc_name(name: str) -> str:
    name = (name or "").strip().lower()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", name)


def _doc_match_keys(value: str) -> set[str]:
    clean = (value or "").strip()
    if not clean:
        return set()
    stem = clean.rsplit(".", 1)[0] if "." in clean else clean
    keys = {
        _normalize_doc_name(clean),
        _normalize_doc_name(stem),
        _normalize_doc_name(clean.replace("_", " ")),
        _normalize_doc_name(clean.replace("-", " ")),
        _compact_doc_name(stem),
        _compact_doc_name(clean.replace(".", " ")),
    }
    return {key for key in keys if key}


def _doc_match_score(query_keys: set[str], parsed: dict) -> int:
    filename = parsed.get("filename", "")
    ingest_id = parsed.get("ingest_id", "")
    alias = parsed.get("alias", "")
    candidate_keys = _doc_match_keys(filename)
    candidate_keys.update(_doc_match_keys(ingest_id))
    candidate_keys.update(_doc_match_keys(alias))

    if not query_keys or not candidate_keys:
        return 0
    if query_keys.intersection(candidate_keys):
        return 100
    if any(q and c and (q in c or c in q) for q in query_keys for c in candidate_keys):
        return 70
    return 0


def _find_specific_doc_matches(case_id: str, chat_id: int, doc_name: str, *, limit: int = 5) -> list[dict]:
    """
    Find a document in VFMS inventory by name/ID.
    
    Returns:
    - dict with {filename, ingest_id, caption, state, text} if found
    - None if not found
    """
    if not doc_name:
        return []

    query_keys = _doc_match_keys(doc_name)
    if not query_keys:
        return []
    
    conn = _get_conn()
    cur = conn.cursor()
    
    cur.execute(
        """
        SELECT note_text
        FROM case_notes
        WHERE case_id=? AND chat_id=? AND source='telegram_attachment_vfms'
        ORDER BY id DESC
        LIMIT 100
        """,
        (case_id, int(chat_id)),
    )
    
    rows = cur.fetchall()
    conn.close()
    
    matches = []
    for row in rows:
        note = row[0] if not isinstance(row, dict) else row["note_text"]
        parsed = _parse_note(note)

        score = _doc_match_score(query_keys, parsed)
        if score:
            text = _read_extracted_text(parsed.get("ingest_id", ""))
            matches.append({
                **parsed,
                "text": text,
                "_match_score": score,
            })

    matches.sort(key=lambda item: (int(item.get("_match_score") or 0), str(item.get("ingest_id") or "")), reverse=True)
    return matches[: max(1, int(limit or 5))]


def _find_specific_doc_in_inventory(case_id: str, chat_id: int, doc_name: str) -> dict | None:
    matches = _find_specific_doc_matches(case_id, chat_id, doc_name, limit=2)
    return matches[0] if len(matches) == 1 else None


def _render_ambiguous_document_matches(matches: list[dict]) -> str:
    lines = ["Encontré varios documentos parecidos. ¿Cuál quieres?", ""]
    for idx, item in enumerate(matches[:5], start=1):
        filename = _clean_filename(item.get("filename", "documento"))
        ingest_id = str(item.get("ingest_id") or "").strip()
        suffix = f" · ID: {ingest_id}" if ingest_id else ""
        lines.append(f"{idx}. {filename}{suffix}")
    return "\n".join(lines).strip()


def _find_saved_specific_doc_summary(case_id: str, chat_id: int, ingest_id: str) -> str:
    ingest_id = (ingest_id or "").strip()
    if not ingest_id:
        return ""

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT note_text
        FROM case_notes
        WHERE case_id=?
          AND chat_id=?
          AND source='generated_summary'
          AND note_text LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (str(case_id), int(chat_id), f"%{ingest_id}%"),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return ""
    return str(row[0] if not isinstance(row, dict) else row["note_text"]).strip()


def _with_summary_available_state(note_text: str) -> str:
    note_text = (note_text or "").strip()
    if not note_text:
        return note_text
    if "resumen disponible" in note_text.lower() or "summary available" in note_text.lower():
        return note_text

    state_match = re.search(r"(?m)^- Estado:\s*(.+)$", note_text)
    if state_match:
        current = state_match.group(1).strip()
        updated = f"- Estado: {current}; resumen disponible"
        return note_text[: state_match.start()] + updated + note_text[state_match.end():]

    return note_text + "\n- Estado: resumen disponible"


def _mark_specific_doc_summary_available(case_id: str, chat_id: int, ingest_id: str) -> bool:
    ingest_id = (ingest_id or "").strip()
    if not ingest_id:
        return False

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, note_text
        FROM case_notes
        WHERE case_id=?
          AND chat_id=?
          AND source='telegram_attachment_vfms'
          AND note_text LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (str(case_id), int(chat_id), f"%{ingest_id}%"),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return False

    row_id = row[0] if not isinstance(row, dict) else row["id"]
    note_text = row[1] if not isinstance(row, dict) else row["note_text"]
    updated = _with_summary_available_state(str(note_text or ""))
    if updated != note_text:
        cur.execute(
            "UPDATE case_notes SET note_text=? WHERE id=?",
            (updated, int(row_id)),
        )
        conn.commit()
    conn.close()
    return True


def _generate_specific_doc_summary_text(doc_meta: dict) -> str:
    text = str(doc_meta.get("text") or "").strip()
    return _render_clean_specific_doc_summary_body(text)


def _doc_status_label(doc_meta: dict) -> str:
    state = str(doc_meta.get("state") or "").lower()
    text = str(doc_meta.get("text") or "").strip()
    if "resumen disponible" in state or str(doc_meta.get("saved_summary") or "").strip():
        return "resumen disponible"
    if text or "texto" in state or "extraído" in state or "extraido" in state or "indexado" in state:
        return "texto leído"
    if "ocr" in state or "revision" in state or "revisión" in state:
        return "necesita OCR/revisión"
    return state or "guardado"


def _looks_like_land_case_doc(doc_meta: dict) -> bool:
    combined = f"{doc_meta.get('filename') or ''}\n{doc_meta.get('text') or ''}".lower()
    return any(marker in combined for marker in (
        "finca",
        "10082",
        "registro público",
        "registro publico",
        "juzgado",
        "oficio no",
        "auto no",
        "prescripción adquisitiva",
        "prescripcion adquisitiva",
    ))


def _looks_like_ai_research_doc(doc_meta: dict) -> bool:
    combined = f"{doc_meta.get('filename') or ''}\n{doc_meta.get('text') or ''}".lower()
    return any(marker in combined for marker in (
        "agi",
        "artificial general intelligence",
        "inteligencia artificial",
        "ai",
        "predictions",
        "predicciones",
        "timeline",
        "2028",
        "2030",
    ))


def _suggest_document_tags(doc_meta: dict) -> list[str]:
    filename = _clean_filename(doc_meta.get("filename", ""))
    text = str(doc_meta.get("text") or "")
    combined = f"{filename}\n{text}".lower()
    tags = []
    if _looks_like_ai_research_doc(doc_meta):
        tags.extend(["AGI", "inteligencia artificial", "predicciones"])
        for year in ("2028", "2030"):
            if year in combined:
                tags.append(year)
    if _looks_like_land_case_doc(doc_meta):
        tags.append("Finca 10082")
    if filename.lower().endswith(".pdf"):
        tags.append("PDF")
    if "resumen disponible" in str(doc_meta.get("state") or "").lower() or doc_meta.get("saved_summary"):
        tags.append("resumen")
    if any(marker in combined for marker in ("registro público", "registro publico", "oficio", "auto no", "juzgado")):
        tags.append("documento legal")
    if "prueba" in combined:
        tags.append("prueba")
    if not tags:
        tags.append("documento")

    out = []
    seen = set()
    for tag in tags:
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(tag)
    return out[:6]


def _suggest_document_display_name(doc_meta: dict) -> str:
    text = str(doc_meta.get("text") or "")
    header = _extract_legal_header(text)
    registry = _extract_registry_points(text)
    filename = _clean_filename(doc_meta.get("filename", "documento"))
    combined = f"{filename}\n{text}".lower()

    if _looks_like_ai_research_doc(doc_meta):
        years = [year for year in ("2028", "2030") if year in combined]
        suffix = "_" + "_".join(years) if years else ""
        return f"AGI_Predicciones_y_Timeline{suffix}"
    if any("Finca No. 10082" in point for point in registry):
        if header.get("tipo_documento"):
            return f"Finca 10082 - {header['tipo_documento']}"
        return "Finca 10082 - documento legal"
    if header.get("tipo_documento"):
        return header["tipo_documento"]
    return re.sub(r"\s+", " ", filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")).strip() or filename


def _document_importance_note(doc_meta: dict) -> str:
    text = str(doc_meta.get("text") or "")
    registry = _extract_registry_points(text)
    chronology = _extract_chronology(text)
    if _looks_like_ai_research_doc(doc_meta):
        return "Parece útil como material de investigación o referencia sobre AGI, predicciones y posibles fechas."
    if registry:
        return "Ayuda a ubicar datos de la finca y actuaciones mencionadas para revisarlas con Nora."
    if chronology:
        return "Puede servir para ordenar fechas y eventos del caso antes de hablar con Nora."
    if str(doc_meta.get("saved_summary") or "").strip():
        return "Ya tiene resumen guardado, así que puede servir como referencia rápida del expediente."
    return "Sirve para tener identificado el documento y decidir qué revisar después."


def _document_case_folder_suggestion(doc_meta: dict, case_id: str) -> str:
    if _looks_like_land_case_doc(doc_meta):
        return f"Finca / CASE:{case_id}"
    if _looks_like_ai_research_doc(doc_meta):
        return f"General / Investigación. Caso actual: CASE:{case_id}, pero este documento parece no ser de finca."
    return f"Sin carpeta confirmada. Caso actual: CASE:{case_id}."


def _document_timeline_items(doc_meta: dict) -> list[str]:
    text = str(doc_meta.get("text") or "")
    chronology = _extract_chronology(text)
    if chronology:
        return chronology[:5]
    years = []
    for year in re.findall(r"\b20\d{2}\b", text):
        if year not in years:
            years.append(year)
    return [f"{year}: año mencionado en el texto." for year in years[:5]]


def build_document_naming_metadata(doc_meta: dict, *, case_id: str) -> dict:
    return {
        "filename": _clean_filename(doc_meta.get("filename", "documento")),
        "ingest_id": str(doc_meta.get("ingest_id") or "").strip(),
        "status": _doc_status_label(doc_meta),
        "alias": _suggest_document_display_name(doc_meta),
        "tags": _suggest_document_tags(doc_meta),
        "folder": _document_case_folder_suggestion(doc_meta, case_id),
        "why_it_matters": _document_importance_note(doc_meta),
        "timeline": _document_timeline_items(doc_meta),
    }


def render_document_naming_metadata_suggestion(doc_meta: dict, *, case_id: str) -> str:
    metadata = build_document_naming_metadata(doc_meta, case_id=case_id)
    filename = metadata["filename"]
    ingest_id = metadata["ingest_id"]
    status = metadata["status"]
    suggested_name = metadata["alias"]
    tags = metadata["tags"]
    chronology = metadata["timeline"]

    lines = [
        "📎 Documento",
        f"- Actual: {filename}",
    ]
    if ingest_id:
        lines.append(f"- ID: {ingest_id}")
    lines.append(f"- Estado: {status}")
    lines.extend([
        "",
        "🏷️ Sugerencia de nombre",
        f"- {suggested_name}",
        "",
        "🧩 Etiquetas sugeridas",
    ])
    lines.extend(f"- {tag}" for tag in tags)
    lines.extend([
        "",
        "🗂️ Carpeta / caso sugerido",
        f"- {metadata['folder']}",
        "",
        "🧭 Por qué importa",
        f"- {metadata['why_it_matters']}",
        "",
        "📅 Línea de tiempo",
    ])
    if chronology:
        lines.extend(f"- {item}" for item in chronology[:5])
    else:
        lines.append("- No detecté una fecha principal dentro del texto; puedo usar la fecha de carga.")
    lines.extend([
        "",
        "Siguiente paso:",
        "- guardar este nombre",
        "- extraer fechas",
        "- preparar preguntas para Nora",
        "",
        "Todavía no cambié el nombre; solo te estoy proponiendo una ficha.",
        "Límite: organizo información registrada; no doy conclusiones legales.",
    ])
    return "\n".join(lines).strip()


def _normalize_alias_save_text(text: str) -> str:
    raw = (text or "").strip()
    raw = re.sub(r"^val[,\s]+", "", raw, flags=re.I).strip()
    raw = re.sub(r"[?!.]+$", "", raw).strip()
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw = re.sub(r"[,;:]+", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


def _extract_document_alias_save_request(text: str) -> dict:
    norm = _normalize_alias_save_text(text)
    low = norm.lower()
    confirmation_markers = {
        "guarda ese nombre",
        "guarda ese nombre y etiquetas",
        "si guardalo",
        "si guarda ese nombre",
        "usa ese nombre",
        "guardalo",
        "guardar ese nombre",
    }
    if low in confirmation_markers:
        return {"kind": "confirm", "alias": "", "target": ""}

    patterns = [
        r"guarda\s+(.+?)\s+para\s+(.+)$",
        r"renombra\s+(.+?)\s+como\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, norm, flags=re.I)
        if not match:
            continue
        if pattern.startswith("guarda"):
            alias, target = match.group(1).strip(), match.group(2).strip()
        else:
            target, alias = match.group(1).strip(), match.group(2).strip()
        alias = re.sub(r"\s+", " ", alias).strip()
        target = re.sub(r"\s+", " ", target).strip()
        if alias and target:
            return {"kind": "explicit", "alias": alias, "target": target}
    return {}


def looks_like_document_alias_save_request(text: str) -> bool:
    return bool(_extract_document_alias_save_request(text))


def _with_document_alias_metadata(note_text: str, *, alias: str, tags: list[str] | str = "", folder: str = "", why_it_matters: str = "") -> str:
    note_text = (note_text or "").strip()
    alias = re.sub(r"\s+", " ", (alias or "").strip())
    if isinstance(tags, str):
        tag_text = re.sub(r"\s+", " ", tags.strip())
    else:
        tag_text = ", ".join(re.sub(r"\s+", " ", str(tag).strip()) for tag in tags if str(tag).strip())
    folder = re.sub(r"\s+", " ", (folder or "").strip())
    why_it_matters = re.sub(r"\s+", " ", (why_it_matters or "").strip())

    cleaned = []
    skip_prefixes = (
        "- Alias:",
        "- Etiquetas:",
        "- Carpeta sugerida:",
        "- Por qué importa:",
    )
    for line in note_text.splitlines():
        if any(line.startswith(prefix) for prefix in skip_prefixes):
            continue
        cleaned.append(line.rstrip())

    additions = []
    if alias:
        additions.append(f"- Alias: {alias}")
    if tag_text:
        additions.append(f"- Etiquetas: {tag_text}")
    if folder:
        additions.append(f"- Carpeta sugerida: {folder}")
    if why_it_matters:
        additions.append(f"- Por qué importa: {why_it_matters}")
    return "\n".join(cleaned + additions).strip()


def _persist_document_alias_metadata(case_id: str, chat_id: int, ingest_id: str, *, alias: str, tags: list[str] | str = "", folder: str = "", why_it_matters: str = "") -> dict:
    ingest_id = (ingest_id or "").strip()
    alias = (alias or "").strip()
    if not ingest_id or not alias:
        return {"saved": False}

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, note_text
        FROM case_notes
        WHERE case_id=?
          AND chat_id=?
          AND source='telegram_attachment_vfms'
          AND note_text LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (str(case_id), int(chat_id), f"%{ingest_id}%"),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"saved": False}

    row_id = row[0] if not isinstance(row, dict) else row["id"]
    note_text = str(row[1] if not isinstance(row, dict) else row["note_text"] or "")
    parsed = _parse_note(note_text)
    updated = _with_document_alias_metadata(
        note_text,
        alias=alias,
        tags=tags,
        folder=folder,
        why_it_matters=why_it_matters,
    )
    if updated != note_text:
        cur.execute("UPDATE case_notes SET note_text=? WHERE id=?", (updated, int(row_id)))
        conn.commit()
    conn.close()
    parsed.update({
        "alias": alias,
        "tags": ", ".join(tags) if isinstance(tags, list) else str(tags or ""),
        "folder_suggestion": folder,
        "why_it_matters": why_it_matters,
        "saved": True,
    })
    return parsed


def _alias_save_confirmation_reply(alias: str, original_filename: str, tags: list[str] | str = "") -> str:
    alias = (alias or "").strip()
    original_filename = _clean_filename(original_filename or "documento")
    lines = [
        "Listo. Guardé este nombre para el documento:",
        alias,
        "",
        f"El archivo original sigue intacto: {original_filename}.",
    ]
    if tags:
        tag_text = ", ".join(tags) if isinstance(tags, list) else str(tags)
        tag_text = re.sub(r"\s+", " ", tag_text).strip()
        if tag_text:
            lines.extend(["", f"También guardé estas etiquetas: {tag_text}."])
    return "\n".join(lines).strip()


def _store_pending_document_alias(context, *, case_id: str, chat_id: int, doc_meta: dict, metadata: dict) -> None:
    chat_data = getattr(context, "chat_data", None)
    if chat_data is None:
        return
    chat_data["karen_pending_doc_alias"] = {
        "case_id": str(case_id),
        "chat_id": int(chat_id),
        "ingest_id": str(doc_meta.get("ingest_id") or metadata.get("ingest_id") or "").strip(),
        "filename": _clean_filename(doc_meta.get("filename") or metadata.get("filename") or "documento"),
        "alias": str(metadata.get("alias") or "").strip(),
        "tags": list(metadata.get("tags") or []),
        "folder": str(metadata.get("folder") or "").strip(),
        "why_it_matters": str(metadata.get("why_it_matters") or "").strip(),
    }


def _persist_specific_doc_summary(case_id: str, chat_id: int, doc_meta: dict, summary_text: str) -> bool:
    ingest_id = str(doc_meta.get("ingest_id") or "").strip()
    summary_text = (summary_text or "").strip()
    if not ingest_id or not summary_text:
        return False

    existing = _find_saved_specific_doc_summary(str(case_id), int(chat_id), ingest_id)
    if not existing:
        note_text = "\n".join([
            "Resumen generado de documento VFMS",
            f"- VFMS ingest_id: {ingest_id}",
            f"- Archivo: {_clean_filename(doc_meta.get('filename', 'documento'))}",
            "",
            summary_text,
        ]).strip()
        insert_case_note(
            chat_id=int(chat_id),
            case_id=str(case_id),
            note_text=note_text,
            source="generated_summary",
        )

    _mark_specific_doc_summary_available(str(case_id), int(chat_id), ingest_id)
    return True


def _build_specific_doc_summary_reply(doc_meta: dict) -> str:
    """
    Build a reply for a specific document summary.
    
    If text is extracted, return a concise summary.
    If not, return honest copy about what's available.
    """
    filename = _clean_filename(doc_meta.get("filename", ""))
    display_title = re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", filename.rsplit(".", 1)[0] if "." in filename else filename)).strip()
    display_title = display_title or filename or "documento"
    ingest_id = doc_meta.get("ingest_id", "")
    caption = doc_meta.get("caption", "")
    state = doc_meta.get("state", "").lower()
    text = doc_meta.get("text", "").strip()
    saved_summary = str(doc_meta.get("saved_summary") or "").strip()
    
    lines = []
    lines.append(f"📄 {filename}")
    
    if ingest_id:
        lines.append(f"ID: {ingest_id}")
    
    if caption:
        lines.append(f"Nota: {caption}")
    
    # Check if text is extracted
    has_text = bool(text)
    body_includes_limit = False
    
    if saved_summary:
        lines.append("Estado: resumen disponible")
        lines.append("")
        lines.append(_clean_specific_doc_summary_body_for_reply(saved_summary))
        body_includes_limit = True
    elif has_text:
        if "resumen" in state or "summary" in state.lower():
            generated_summary = _generate_specific_doc_summary_text(doc_meta)
            lines.append("Estado: resumen disponible")
            lines.append("")
            lines.append(_clean_specific_doc_summary_body_for_reply(generated_summary))
            body_includes_limit = True
        else:
            # Text is extracted but no summary yet
            lines.append(f"Estado: {state or 'texto extraído e indexado'}")
            lines.append("")
            lines.append(
                f"Ya tengo el texto leído de {display_title}, "
                "pero todavía no tengo un resumen guardado. Puedo generar uno ahora."
            )
            lines.append("")
            lines.append("Siguientes acciones útiles:")
            lines.append("- generar resumen claro")
            lines.append("- extraer fechas importantes")
            lines.append("- preparar preguntas para Nora")
    else:
        lines.append("")
        lines.append("⏳ El documento está registrado pero el texto aún no ha sido extraído.")
        lines.append("")
        if "necesita ocr" in state or "ocr" in state.lower():
            lines.append("📌 Estado: Pendiente de OCR/extracción manual")
        else:
            lines.append(f"📌 Estado: {state or 'Por procesar'}")
        lines.append("")
        lines.append("Próximos pasos:")
        lines.append("- Si es un PDF o imagen, puedo extraer el texto")
        lines.append("- Luego podré hacerte un resumen")
    
    if not body_includes_limit:
        lines.append("")
        lines.append(SUMMARY_LIMIT_LINE)
    
    reply = "\n".join(lines).strip()
    reply = re.sub(r"\n{3,}", "\n\n", reply)
    return reply

async def maybe_handle_document_summary_query(update, context, chat_id: int, text: str) -> bool:
    """
    Handles VFMS document summary requests in Telegram.

    Adds:
    - _reply_text_chunked for long messages
    - Privacy guard for Karen documents
    """

    raw = (text or "").strip().lower()

    # ---------------------------
    # Karen / Nora attorney-prep escape hatch
    # If the user asks for a clear summary for Nora / abogada or asks
    # what is missing before talking to the lawyer, do NOT return raw
    # grounded VFMS. Return the polished lawyer package.
    # ---------------------------
    try:
        nora_context = (
            "nora" in raw
            or "abogada" in raw
            or "abogado" in raw
        )
        nora_intent_markers = (
            "preparame un resumen",
            "prepárame un resumen",
            "resumen claro",
            "llevarle esto",
            "que me falta revisar",
            "qué me falta revisar",
            "que falta revisar",
            "qué falta revisar",
            "que me falta conseguir",
            "qué me falta conseguir",
            "que falta conseguir",
            "qué falta conseguir",
            "antes de hablar",
            "paquete para nora",
            "paquete para la abogada",
        )

        if nora_context and any(m in raw for m in nora_intent_markers):
            from core.karen_lawyer_package import render_lawyer_package
            await _reply_text_chunked(update, render_lawyer_package(int(chat_id)))
            return True
    except Exception:
        # Do not break normal summary behavior if the package import/render fails.
        pass

    # ---------------------------
    # Step 0: Early exit if not a summary request
    # ---------------------------
    if not any(m in raw for m in SUMMARY_MARKERS):
        return False

    # ---------------------------
    # Step 0.5: Check for specific document summary request
    # ---------------------------
    specific_doc_name = _extract_specific_doc_name(text)
    
    case_id = get_active_case_id(int(chat_id))
    if not case_id:
        return False
    
    if specific_doc_name:
        # User asked for summary of a specific document (e.g., "dame el resumen de six pdf")
        matches = _find_specific_doc_matches(case_id, int(chat_id), specific_doc_name, limit=5)
        if len(matches) > 1:
            await update.message.reply_text(_render_ambiguous_document_matches(matches))
            return True
        doc_meta = matches[0] if matches else None
        if doc_meta:
            ingest_id = str(doc_meta.get("ingest_id") or "").strip()
            saved_summary = _find_saved_specific_doc_summary(str(case_id), int(chat_id), ingest_id)
            if saved_summary:
                doc_meta["saved_summary"] = saved_summary
            elif str(doc_meta.get("text") or "").strip():
                generated_summary = _generate_specific_doc_summary_text(doc_meta)
                _persist_specific_doc_summary(str(case_id), int(chat_id), doc_meta, generated_summary)
                doc_meta["saved_summary"] = generated_summary
                doc_meta["state"] = (
                    str(doc_meta.get("state") or "texto leído").strip() + "; resumen disponible"
                ).strip("; ")
            reply = _build_specific_doc_summary_reply(doc_meta)
            await _reply_text_chunked(update, reply)
            return True
        else:
            # Document name didn't match anything in inventory
            reply = (
                f"No encontré un documento que coincida con '{specific_doc_name}' "
                f"en el inventario del CASE:{case_id}.\n\n"
                f"Puedo ayudarte a:\n"
                f"- Ver qué documentos tienes: 'qué documentos tengo'\n"
                f"- Probar con el nombre exacto o el ID VFMS\n"
                f"- Buscar por tipo: 'qué pdf tengo' o 'documentos de finca'\n"
            )
            await update.message.reply_text(reply)
            return True

    # ---------------------------
    # Step 1: Preview requests
    # ---------------------------
    if _looks_like_format_preview_request(text):
        await update.message.reply_text(_format_preview_reply())
        return True

    # ---------------------------
    # Step 2: Get active case
    # ---------------------------
    if not case_id:
        return False

    # ---------------------------
    # Step 3: Extract VFMS ID from text
    # ---------------------------
    specific_vfms_id = _extract_vfms_id(text)

    # ---------------------------
    # Step 4: PRIVACY GUARD
    # ---------------------------
    # A VFMS document can only be summarized from the same Telegram chat
    # that owns the original attachment note.
    if specific_vfms_id:
        guard_conn = _get_conn()
        guard_cur = guard_conn.cursor()
        guard_cur.execute(
            """
            SELECT 1
            FROM case_notes
            WHERE case_id=?
              AND chat_id=?
              AND source='telegram_attachment_vfms'
              AND note_text LIKE ?
            LIMIT 1
            """,
            (str(case_id), int(chat_id), f"%{specific_vfms_id}%"),
        )
        allowed_doc = guard_cur.fetchone()
        guard_conn.close()

        if not allowed_doc:
            await update.message.reply_text(
                "⚠️ Acceso denegado: este documento pertenece a otro expediente/chat."
            )
            return True

    # ---------------------------
    # Step 5: Return specific doc if requested
    # ---------------------------
    if specific_vfms_id:
        reply = _build_specific_doc_summary(str(case_id), specific_vfms_id)
        await _reply_text_chunked(update, reply)
        return True

    # ---------------------------
    # Step 6: Fetch last 100 VFMS notes from DB
    # ---------------------------
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT note_text
        FROM case_notes
        WHERE case_id=? AND chat_id=? AND source='telegram_attachment_vfms'
        ORDER BY id DESC
        LIMIT 100
        """,
        (case_id, int(chat_id)),
    )
    rows = cur.fetchall()
    conn.close()

    # ---------------------------
    # Step 7: Deduplicate docs
    # ---------------------------
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

        if body_key and body_key in seen_body:
            continue

        seen_ingest.add(ingest_id)
        if body_key:
            seen_body.add(body_key)

        docs.append({**parsed, "text": text_body})

        if len(docs) >= 5:
            break

    # ---------------------------
    # Step 8: No docs found
    # ---------------------------
    if not docs:
        await update.message.reply_text(
            f"No encontré documentos extraídos para resumir en CASE:{case_id}."
        )
        return True

    # ---------------------------
    # Step 9: Build summary parts
    # ---------------------------
    if _looks_like_combined_legal_summary_request(text):
        reply = _render_combined_legal_documents_summary(str(case_id), docs)
        await _reply_text_chunked(update, reply)
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

    # ---------------------------
    # Step 10: Send chunked summary
    # ---------------------------
    await _reply_text_chunked(update, "\n".join(parts).strip())
    return True


async def maybe_handle_document_alias_save_query(update, context, chat_id: int, text: str) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    request = _extract_document_alias_save_request(text)
    if not request:
        return False

    case_id = get_active_case_id(int(chat_id))
    if not case_id:
        return False

    if request.get("kind") == "confirm":
        pending = getattr(context, "chat_data", {}).get("karen_pending_doc_alias") if context else None
        if not pending or str(pending.get("case_id")) != str(case_id) or int(pending.get("chat_id") or 0) != int(chat_id):
            await update.message.reply_text(
                "Necesito saber cuál documento. Dime: 'guarda este nombre para [documento]'."
            )
            return True

        saved = _persist_document_alias_metadata(
            str(case_id),
            int(chat_id),
            str(pending.get("ingest_id") or ""),
            alias=str(pending.get("alias") or ""),
            tags=list(pending.get("tags") or []),
            folder=str(pending.get("folder") or ""),
            why_it_matters=str(pending.get("why_it_matters") or ""),
        )
        if not saved.get("saved"):
            await update.message.reply_text(
                "No pude guardar ese nombre todavía. Prueba diciendo: 'guarda este nombre para [documento]'."
            )
            return True

        await update.message.reply_text(
            _alias_save_confirmation_reply(
                str(pending.get("alias") or ""),
                str(saved.get("filename") or pending.get("filename") or "documento"),
                list(pending.get("tags") or []),
            )
        )
        return True

    target = str(request.get("target") or "").strip()
    alias = str(request.get("alias") or "").strip()
    matches = _find_specific_doc_matches(str(case_id), int(chat_id), target, limit=5)
    if len(matches) > 1:
        await update.message.reply_text(_render_ambiguous_document_matches(matches))
        return True
    doc_meta = matches[0] if matches else None
    if not doc_meta:
        await update.message.reply_text(
            f"No encontré un documento que coincida con '{target}'. "
            "Puedes decir: 'Val, qué documentos tengo'."
        )
        return True

    saved_summary = _find_saved_specific_doc_summary(str(case_id), int(chat_id), doc_meta.get("ingest_id", ""))
    if saved_summary:
        doc_meta["saved_summary"] = saved_summary
    metadata = build_document_naming_metadata(doc_meta, case_id=str(case_id))
    saved = _persist_document_alias_metadata(
        str(case_id),
        int(chat_id),
        str(doc_meta.get("ingest_id") or ""),
        alias=alias,
        tags=list(metadata.get("tags") or []),
        folder=str(metadata.get("folder") or ""),
        why_it_matters=str(metadata.get("why_it_matters") or ""),
    )
    if not saved.get("saved"):
        await update.message.reply_text("No pude guardar ese nombre todavía. El archivo original no fue cambiado.")
        return True

    await update.message.reply_text(
        _alias_save_confirmation_reply(alias, str(saved.get("filename") or doc_meta.get("filename") or "documento"), metadata.get("tags") or [])
    )
    return True


async def maybe_handle_document_naming_metadata_query(update, context, chat_id: int, text: str) -> bool:
    if not update or not getattr(update, "message", None):
        return False
    if not looks_like_document_naming_metadata_request(text):
        return False

    case_id = get_active_case_id(int(chat_id))
    if not case_id:
        return False

    target = _extract_document_naming_target(text)
    if not target:
        target = "__latest__"

    if target == "__latest__":
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT note_text
            FROM case_notes
            WHERE case_id=? AND chat_id=? AND source='telegram_attachment_vfms'
            ORDER BY id DESC
            LIMIT 1
            """,
            (str(case_id), int(chat_id)),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            await update.message.reply_text("No encontré documentos registrados para organizar todavía.")
            return True
        parsed = _parse_note(row[0] if not isinstance(row, dict) else row["note_text"])
        parsed["text"] = _read_extracted_text(parsed.get("ingest_id", ""))
        saved_summary = _find_saved_specific_doc_summary(str(case_id), int(chat_id), parsed.get("ingest_id", ""))
        if saved_summary:
            parsed["saved_summary"] = saved_summary
        doc_meta = parsed
    else:
        matches = _find_specific_doc_matches(str(case_id), int(chat_id), target, limit=5)
        if len(matches) > 1:
            await update.message.reply_text(_render_ambiguous_document_matches(matches))
            return True
        doc_meta = matches[0] if matches else None

    if not doc_meta:
        await update.message.reply_text(
            f"No encontré un documento que coincida con '{target}'. "
            "Puedes decir: “Val, qué documentos tengo”."
        )
        return True

    saved_summary = _find_saved_specific_doc_summary(str(case_id), int(chat_id), doc_meta.get("ingest_id", ""))
    if saved_summary:
        doc_meta["saved_summary"] = saved_summary

    metadata = build_document_naming_metadata(doc_meta, case_id=str(case_id))
    _store_pending_document_alias(
        context,
        case_id=str(case_id),
        chat_id=int(chat_id),
        doc_meta=doc_meta,
        metadata=metadata,
    )
    await update.message.reply_text(render_document_naming_metadata_suggestion(doc_meta, case_id=str(case_id)))
    return True
