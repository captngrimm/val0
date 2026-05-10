from telegram import Update
from telegram.ext import ContextTypes

CASE_KEY = "KAREN-LAND-001"

def _clip(text: str, limit: int = 260) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."

def _looks_like_pasted_transcript(text: str) -> bool:
    t = text or ""
    return (
        "[5/" in t
        or "Valeria:" in t
        or "Frank:" in t
        or t.count("\n") >= 12
    )


def _clean_note_text(text: str) -> str:
    text = (text or "").strip()

    prefixes = (
        "Inventario inicial de documentos:",
        "Custodia / ubicación de documentos:",
        "Datos registrales / identificadores mencionados:",
        "Nombre del caso:",
        "Personas/herederos involucrados:",
        "Evento más antiguo recordado:",
        "Cita, fecha límite o urgencia de esta semana:",
    )

    for pfx in prefixes:
        if text.startswith(pfx):
            text = text[len(pfx):].strip()

    # Remove category appendix for compact display.
    if "\nCategorías detectadas:" in text:
        text = text.split("\nCategorías detectadas:", 1)[0].strip()

    return text.strip()


def _bucket_notes(notes: list[dict]) -> dict:
    buckets = {
        "case_name": [],
        "people": [],
        "timeline": [],
        "urgency": [],
        "lawyer_questions": [],
        "documents": [],
        "holders": [],
        "registry": [],
        "other": [],
    }

    for n in notes:
        source = str(n.get("source") or "").strip()
        raw = str(n.get("note_text") or "").strip()
        if not raw:
            continue

        # Test noise / transcripts should not pollute the user-facing case status.
        if raw == "Interrogator v0 iniciado para caso de terreno familiar.":
            continue

        if source == "document_registry_details_v0" and _looks_like_pasted_transcript(raw):
            # Keep the section useful instead of showing pasted Telegram transcript trash.
            buckets["registry"].append("Pendiente: revisar fotos y papeles físicos para confirmar finca, folio, inscripción, fecha, tomo o asiento.")
            continue

        txt = _clean_note_text(raw)
        if not txt:
            continue

        if source == "interrogator_step_0":
            buckets["case_name"].append(txt)
        elif source == "interrogator_step_1":
            buckets["people"].append(txt)
        elif source == "interrogator_step_2":
            buckets["timeline"].append(txt)
        elif source == "interrogator_step_4":
            buckets["urgency"].append(txt)
        elif source == "lawyer_questions_v0":
            buckets["lawyer_questions"].append(txt)
        elif source == "document_inventory_v0":
            buckets["documents"].append(txt)
        elif source == "document_holder_v0":
            buckets["holders"].append(txt)
        elif source == "document_registry_details_v0":
            buckets["registry"].append(txt)
        else:
            buckets["other"].append(txt)

    return buckets

def render_karen_case_status(chat_id: int) -> str:
    from memory_store import fetch_case_notes

    notes = fetch_case_notes(int(chat_id), CASE_KEY, limit=80)
    buckets = _bucket_notes(notes)

    lines = []
    lines.append("📁 Caso del terreno familiar — estado actual")
    lines.append("")

    lines.append("Lo que tengo hasta ahora:")

    lines.append("")
    lines.append("🧠 Base del caso:")
    if buckets["case_name"]:
        lines.append(f"- Caso: {_clip(buckets['case_name'][-1], 180)}")
    else:
        lines.append("- Caso: Terreno familiar")

    if buckets["people"]:
        lines.append(f"- Personas/herederos: {_clip(buckets['people'][-1], 220)}")
    else:
        lines.append("- Personas/herederos: pendiente de limpiar/confirmar")

    if buckets["timeline"]:
        lines.append(f"- Timeline inicial: {_clip(buckets['timeline'][-1], 220)}")
    else:
        lines.append("- Timeline inicial: pendiente")

    if buckets["urgency"]:
        lines.append(f"- Urgencia/cita: {_clip(buckets['urgency'][-1], 220)}")

    if buckets["documents"]:
        lines.append("")
        lines.append("📎 Documentos mencionados:")
        lines.append(f"- {_clip(buckets['documents'][-1], 300)}")

    if buckets["holders"]:
        lines.append("")
        lines.append("📍 Quién tiene documentos:")
        lines.append(f"- {_clip(buckets['holders'][-1], 260)}")

    if buckets["registry"]:
        lines.append("")
        lines.append("🏛️ Datos registrales / pendientes de verificar:")
        lines.append(f"- {_clip(buckets['registry'][-1], 260)}")
    else:
        lines.append("")
        lines.append("🏛️ Datos registrales / pendientes de verificar:")
        lines.append("- Falta revisar si los documentos tienen finca, folio, inscripción, tomo, asiento o fecha.")

    if buckets["lawyer_questions"]:
        lines.append("")
        lines.append("⚖️ Abogado:")
        lines.append("- Ya hay una lista de preguntas preparada y guardada en el caso.")

    if not notes:
        return (
            "Todavía no tengo notas guardadas para el caso del terreno 😕📁\n\n"
            "Empieza con /interrogate para levantar el caso."
        )

    lines.append("")
    lines.append("Siguiente acción recomendada:")
    lines.append("- Preparar paquete para abogado: timeline inicial, herederos, documentos disponibles, quién tiene qué, y preguntas para abogado.")
    lines.append("")
    lines.append("Para ver dirección general, dime: ¿cuál es el plan? 😏")

    return "\n".join(lines)

async def karen_case_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.effective_chat.id
    await update.message.reply_text(render_karen_case_status(int(chat_id)))

async def maybe_handle_karen_case_status(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    t = (text or "").lower().strip()

    markers = (
        "que tengo del caso del terreno",
        "qué tengo del caso del terreno",
        "muestrame el caso del terreno",
        "muéstrame el caso del terreno",
        "que hay guardado del terreno",
        "qué hay guardado del terreno",
        "que tenemos del terreno",
        "qué tenemos del terreno",
        "estado del caso del terreno",
        "resumen del caso del terreno",
        "caso del terreno",
    )

    if any(m in t for m in markers):
        chat_id = update.effective_chat.id
        await update.message.reply_text(render_karen_case_status(int(chat_id)))
        return True

    return False
