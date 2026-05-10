from telegram import Update
from telegram.ext import ContextTypes

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


def render_lawyer_package(chat_id: int) -> str:
    """
    Dynamic attorney-facing package for Karen LandOps.

    Uses stored case facts and recent case notes. It should organize information
    for the attorney, not replace attorney review.
    """
    data = _collect_case_package_data(int(chat_id))
    facts = data["facts"]

    lines = []
    lines.append("⚖️📦 Paquete para abogada — caso del terreno familiar")
    lines.append("")
    lines.append(
        "Nota rápida: esto organiza hechos, documentos y preguntas para la consulta. "
        "No reemplaza revisión legal; la abogada debe validar estrategia, documentos y riesgos. 😌"
    )
    lines.append("")

    lines.append("1. Resumen corto del caso")
    lines.append("- Se trata de un trámite/disputa familiar sobre la finca hereditaria.")
    if facts.get("finca"):
        lines.append(f"- La finca principal identificada es la Finca {facts['finca']}.")
    if facts.get("tipo_proceso"):
        lines.append(f"- El proceso base identificado es: {facts['tipo_proceso']}.")
    lines.append("- Karen/Insanity y Frank están organizando información, eventos, documentos y próximos pasos.")
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

    lines.append("5. Documentos disponibles o mencionados")
    lines.extend(_latest_lines(
        data["documents"],
        "Pendiente completar inventario documental.",
        limit=2,
    ))
    lines.append("")

    lines.append("6. Quién tiene documentos / custodia")
    lines.extend(_latest_lines(
        data["holders"],
        "Pendiente confirmar quién tiene originales, copias, fotos o papeles físicos.",
        limit=2,
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

    lines.append("10. Checklist antes de la reunión")
    lines.append("- Llevar o compartir fotos legibles de documentos.")
    lines.append("- Separar documentos de Registro Público, Word/resúmenes, fotos de WhatsApp y papeles físicos.")
    lines.append("- Confirmar quién tiene originales y quién tiene copias.")
    lines.append("- Tener a mano Finca/Tomo/Folio/Escritura/fechas.")
    lines.append("- Llevar lista de herederos declarados.")
    lines.append("- Anotar preguntas sobre costos, plazos y próximos pasos.")
    lines.append("")

    lines.append("11. Siguiente acción recomendada")
    lines.append(
        "Confirmar si ya hay cita, llamada o entrega de documentos con la abogada. "
        "Si hay fecha/hora, Val puede dejarlo como seguimiento o recordatorio. "
        "Nada de confiarle 40 años de arroz con mango familiar a la memoria humana, por favor. 😏"
    )

    return "\n".join(lines)


async def karen_lawyer_package_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.effective_chat.id
    await update.message.reply_text(render_lawyer_package(int(chat_id)))


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
    )

    if any(m in t for m in markers):
        chat_id = update.effective_chat.id
        await update.message.reply_text(render_lawyer_package(int(chat_id)))
        return True

    return False
