from telegram import Update
from telegram.ext import ContextTypes


async def _reply_text_chunked(update: Update, text: str, limit: int = 3500):
    """
    Send long lawyer-package output safely under Telegram message limits.
    Local helper to keep Karen package independent from bot.py internals.
    """
    if not update.message:
        return

    text = (text or "").strip()
    if not text:
        return

    chunks = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind("\n\n", 0, limit)
        if cut < 1200:
            cut = remaining.rfind("\n", 0, limit)
        if cut < 1200:
            cut = limit
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()

    if remaining:
        chunks.append(remaining)

    total = len(chunks)
    for i, chunk in enumerate(chunks, start=1):
        prefix = f"[{i}/{total}]\n" if total > 1 else ""
        await update.message.reply_text(prefix + chunk)


CASE_KEY = "KAREN-LAND-001"


def _clip(text: str, limit: int = 520) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _clean_note(raw: str, prefixes: tuple[str, ...] = ()) -> str:
    text = (raw or "").strip()
    for pfx in prefixes:
        if text.startswith(pfx):
            text = text[len(pfx):].strip()
    return text.strip()


def _collect_case_package_data(chat_id: int) -> dict:
    from memory_store import fetch_case_notes
    from core.karen_case_facts import load_karen_case_facts

    facts = load_karen_case_facts(int(chat_id))
    notes = fetch_case_notes(int(chat_id), CASE_KEY, limit=140)

    data = {
        "facts": facts,
        "recent_events": [],
        "documents": [],
        "holders": [],
        "registry": [],
        "lawyer_questions_saved": False,
    }

    for n in notes:
        source = str(n.get("source") or "").strip()
        raw = str(n.get("note_text") or "").strip()
        if not raw:
            continue

        if source == "case_recent_event_v0":
            data["recent_events"].append(
                _clean_note(raw, ("Evento reciente del caso:",))
            )
        elif source == "document_inventory_v0":
            data["documents"].append(
                _clean_note(raw, ("Inventario inicial de documentos:",))
            )
        elif source == "document_holder_v0":
            data["holders"].append(
                _clean_note(raw, ("Custodia / ubicación de documentos:",))
            )
        elif source == "document_registry_details_v0":
            data["registry"].append(
                _clean_note(raw, ("Datos registrales / identificadores mencionados:",))
            )
        elif source == "lawyer_questions_v0":
            data["lawyer_questions_saved"] = True

    return data


def _facts_lines(facts: dict) -> list[str]:
    lines = []

    if facts.get("finca"):
        lines.append(f"- Finca: {facts['finca']}")
    if facts.get("tomo_rollo"):
        lines.append(f"- Tomo/Rollo: {facts['tomo_rollo']}")
    if facts.get("folio"):
        lines.append(f"- Folio: {facts['folio']}")
    if facts.get("propietario_original"):
        lines.append(f"- Propietario original: {facts['propietario_original']}")
    if facts.get("tipo_proceso"):
        lines.append(f"- Tipo de proceso: {facts['tipo_proceso']}")
    if facts.get("fecha_fallecimiento"):
        lines.append(f"- Fecha de fallecimiento: {facts['fecha_fallecimiento']}")
    if facts.get("escritura_publica"):
        lines.append(f"- Escritura Pública No.: {facts['escritura_publica']}")
    if facts.get("fecha_escritura"):
        lines.append(f"- Fecha de escritura: {facts['fecha_escritura']}")
    if facts.get("notaria"):
        lines.append(f"- Notaría: {facts['notaria']}")

    if not lines:
        lines.append("- Aún faltan datos básicos claros de finca/tomo/folio.")

    return lines


def _heirs_lines(facts: dict) -> list[str]:
    heirs = facts.get("herederos") or []
    if not heirs:
        return ["- Pendiente confirmar nombres de herederos."]

    return [f"- {h}" for h in heirs]


def _latest_lines(items: list[str], empty: str, limit: int = 3) -> list[str]:
    clean = [x.strip() for x in items if x and x.strip()]
    if not clean:
        return [f"- {empty}"]

    latest = list(reversed(clean))[:limit]
    return [f"- {_clip(x, 520)}" for x in latest]


def _extract_holder_lines(text: str) -> list[str]:
    """
    Extract clean custody lines from either holder notes or inventory text.
    """
    raw = (text or "").strip()
    low = raw.lower()

    holders = []

    if "karen tiene" in low or "karen tiene algunos" in low or "karen tiene documentos" in low:
        holders.append("Karen tiene algunos documentos.")

    if "frank tiene" in low or "fotos por whatsapp" in low:
        holders.append("Frank tiene o compartió fotos por WhatsApp.")

    if "un familiar tiene" in low or "familiar tiene" in low or "papeles físicos" in low or "papeles fisicos" in low:
        holders.append("Un familiar tiene papeles físicos que hay que revisar o escanear.")

    if "abogado tiene" in low or "abogada tiene" in low:
        holders.append("La abogada/abogado tiene documentos relacionados.")

    unique = []
    for item in holders:
        if item not in unique:
            unique.append(item)

    return unique


def _document_category_lines(documents: list[str]) -> list[str]:
    """
    Convert raw inventory-flow notes into clean package bullets.
    Avoid dumping duplicated 'Categorías detectadas' blocks into attorney package.
    """
    raw = "\n".join([x.strip() for x in documents if x and x.strip()])
    low = raw.lower()

    categories = []

    checks = [
        ("Registro Público", ("registro público", "registro publico")),
        ("Fotos de documentos", ("fotos", "whatsapp")),
        ("Word / PDF / digital", ("word", "pdf", "digital")),
        ("Resúmenes", ("resumen", "resúmenes", "resumenes")),
        ("Papeles físicos por revisar/escanear", ("papeles físicos", "papeles fisicos", "escanear")),
        ("Escrituras / documentos notariales", ("escritura", "notaría", "notaria")),
    ]

    for label, needles in checks:
        if any(n in low for n in needles):
            categories.append(label)

    unique = []
    for item in categories:
        if item not in unique:
            unique.append(item)

    if unique:
        return [f"- {x}" for x in unique]

    clean = [x.strip() for x in documents if x and x.strip()]
    if not clean:
        return ["- Pendiente completar inventario documental."]

    return [f"- {_clip(clean[-1], 360)}"]


def _holder_fallback_from_documents(documents: list[str]) -> list[str]:
    """
    If custody was captured inside the inventory text but not saved as a separate
    holder note, extract only the custody bits for the lawyer package.
    """
    clean = [x.strip() for x in documents if x and x.strip()]
    if not clean:
        return []

    return _extract_holder_lines(clean[-1])


def render_lawyer_package(chat_id: int) -> str:
    """
    Dynamic attorney-facing package for Karen LandOps.

    Uses stored case facts and recent case notes. It should organize information
    for the attorney, not replace attorney review.
    """
    data = _collect_case_package_data(int(chat_id))
    facts = data["facts"]

    lines = []
    lines.append("⚖️📦 Paquete para la abogada Nora Santa — caso del terreno familiar")
    lines.append("")
    lines.append(
        "Insanity, aquí va el paquete ordenado para Nora. "
        "Esto organiza hechos, documentos y preguntas; no reemplaza la revisión legal "
        "ni inventa certeza donde todavía falta validar. 😌"
    )
    lines.append("")

    lines.append("1. Resumen ejecutivo")
    lines.append("- Caso familiar relacionado con una finca hereditaria y su situación registral/procesal.")
    if facts.get("finca"):
        lines.append(f"- La finca principal identificada es la Finca {facts['finca']}.")
    if facts.get("tipo_proceso"):
        lines.append(f"- El proceso base identificado es: {facts['tipo_proceso']}.")
    lines.append("- Karen, a quien Val llama Insanity, y Frank están ordenando hechos, documentos, custodia y próximos pasos para consulta legal.")
    lines.append("")

    lines.append("2. Datos básicos identificados")
    lines.extend(_facts_lines(facts))
    lines.append("")

    lines.append("3. Herederos declarados")
    lines.extend(_heirs_lines(facts))
    lines.append("")

    lines.append("4. Eventos recientes relevantes")
    lines.extend(_latest_lines(
        data["recent_events"],
        "Aún no tengo eventos recientes guardados como eventos específicos.",
        limit=4,
    ))
    lines.append("")

    lines.append("5. Documentos disponibles / mencionados")
    lines.extend(_document_category_lines(data["documents"]))
    lines.append("")

    lines.append("6. Quién tiene documentos / custodia")
    holder_items = []
    for h in data["holders"]:
        holder_items.extend(_extract_holder_lines(h))

    if not holder_items:
        holder_items = _holder_fallback_from_documents(data["documents"])

    lines.extend(_latest_lines(
        holder_items,
        "Pendiente confirmar quién tiene originales, copias, fotos o papeles físicos.",
        limit=4,
    ))
    lines.append("")

    lines.append("7. Datos registrales mencionados")
    lines.extend(_latest_lines(
        data["registry"],
        "Pendiente confirmar finca, folio, tomo/rollo, inscripción, asiento o fechas registrales.",
        limit=2,
    ))
    lines.append("")

    lines.append("8. Objetivo de la consulta con la abogada")
    lines.append("- Que revise el estado legal actual del caso con los documentos disponibles.")
    lines.append("- Que indique si el expediente/demanda de Juncá y su cancelación en 2024 generan acciones pendientes.")
    lines.append("- Que confirme cómo tratar la inconsistencia detectada por falta de registro en Registro Público.")
    lines.append("- Que defina ruta de acción, costos, riesgos, responsables y próximos plazos.")
    lines.append("")

    lines.append("9. Preguntas sugeridas para la abogada")
    lines.append("1. Con estos datos, ¿cuál es el estado legal actual de la finca?")
    lines.append("2. ¿Qué documentos deben verificarse primero en Registro Público?")
    lines.append("3. ¿Qué valor tiene la cancelación del caso de Juncá en 2024 por falta de respuesta?")
    lines.append("4. ¿Qué debe hacerse con la inconsistencia de no haberse registrado en Registro Público?")
    lines.append("5. ¿Sirven fotos/copias o se requieren certificados/originales?")
    lines.append("6. ¿Qué debe firmar o aprobar cada heredero?")
    lines.append("7. ¿Cuál es la ruta de acción recomendada y cuánto costaría tomar el caso?")
    lines.append("8. ¿Qué puede adelantar la familia esta semana antes de una siguiente cita?")
    lines.append("")

    lines.append("10. Checklist para llegar lista a la reunión")
    lines.append("- Llevar fotos legibles o copias de todos los documentos disponibles.")
    lines.append("- Separar por tipo: Registro Público, escrituras, Word/resúmenes, WhatsApp/fotos y papeles físicos.")
    lines.append("- Marcar quién tiene originales, quién tiene copias y qué falta escanear.")
    lines.append("- Tener visible: Finca, Tomo/Rollo, Folio, Escritura, fechas y nombres de herederos.")
    lines.append("- Preguntar costos, plazos, riesgos, documentos faltantes y primera acción concreta.")
    lines.append("")

    lines.append("11. Siguiente acción recomendada")
    lines.append(
        "Confirmar la próxima cita, llamada o entrega de documentos con Nora Santa. "
        "Si ya hay fecha/hora, Val puede dejarlo como recordatorio y seguimiento."
    )

    return "\n".join(lines)


async def karen_lawyer_package_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.effective_chat.id
    await _reply_text_chunked(update, render_lawyer_package(int(chat_id)))


async def maybe_handle_karen_lawyer_package(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    t = (text or "").lower().strip()

    markers = (
        "prepara paquete para abogado",
        "preparar paquete para abogado",
        "paquete para abogado",
        "hazme el paquete para abogado",
        "armar paquete para abogado",
        "armemos paquete para abogado",
        "resumen para abogado",
        "prepara resumen para abogado",
        "paquete para abogada",
        "prepara paquete para abogada",
        "resumen para abogada",
        "prepara resumen para abogada",
        "prepara un paquete para la abogada",
        "prepara un paquete para el abogado",
        "preparar un paquete para la abogada",
        "preparar un paquete para el abogado",
        "paquete para la abogada",
        "paquete para el abogado",
        "paquete para nora",
        "paquete para nora santa",
        "prepara un paquete para nora",
        "prepara un paquete para nora santa",
    )

    if any(m in t for m in markers):
        chat_id = update.effective_chat.id
        await _reply_text_chunked(update, render_lawyer_package(int(chat_id)))
        return True

    return False
