from telegram import Update
from telegram.ext import ContextTypes

CASE_KEY = "KAREN-LAND-001"

def _clip(text: str, limit: int = 260) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."

def _bucket_notes(notes: list[dict]) -> dict:
    buckets = {
        "interrogator": [],
        "lawyer_questions": [],
        "documents": [],
        "holders": [],
        "registry": [],
        "other": [],
    }

    for n in notes:
        source = str(n.get("source") or "").strip()
        txt = str(n.get("note_text") or "").strip()
        if not txt:
            continue

        if source.startswith("interrogator"):
            buckets["interrogator"].append(txt)
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

    if buckets["interrogator"]:
        lines.append("")
        lines.append("🧠 Arranque del caso:")
        for txt in reversed(buckets["interrogator"][-5:]):
            lines.append(f"- {_clip(txt, 180)}")

    if buckets["documents"]:
        lines.append("")
        lines.append("📎 Documentos mencionados:")
        for txt in reversed(buckets["documents"][-2:]):
            lines.append(f"- {_clip(txt, 220)}")

    if buckets["holders"]:
        lines.append("")
        lines.append("📍 Quién tiene documentos:")
        for txt in reversed(buckets["holders"][-2:]):
            lines.append(f"- {_clip(txt, 220)}")

    if buckets["registry"]:
        lines.append("")
        lines.append("🏛️ Datos registrales / pendientes de verificar:")
        for txt in reversed(buckets["registry"][-2:]):
            lines.append(f"- {_clip(txt, 220)}")

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
