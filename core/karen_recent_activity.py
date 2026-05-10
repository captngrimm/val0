from telegram import Update
from telegram.ext import ContextTypes

CASE_KEY = "KAREN-LAND-001"


def _norm(text: str) -> str:
    text = (text or "").lower().strip()
    text = (
        text.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    return " ".join(text.split())


def _clean_event_text(text: str) -> str:
    raw = (text or "").strip()

    prefixes = [
        "ok registra el siguiente evento,",
        "ok registra el siguiente evento:",
        "registra el siguiente evento,",
        "registra el siguiente evento:",
        "ahora, registra este evento:",
        "ahora registra este evento:",
        "registra este evento:",
        "registra este evento,",
        "guarda este evento:",
        "guarda este evento,",
    ]

    low = _norm(raw)
    for pfx in prefixes:
        pfx_norm = _norm(pfx)
        if low.startswith(pfx_norm):
            # Remove approximately by original prefix length fallback.
            # Good enough Mark 1: split on first ":" or "," if present.
            if ":" in raw[:80]:
                return raw.split(":", 1)[1].strip()
            if "," in raw[:80]:
                return raw.split(",", 1)[1].strip()

    return raw


def _clip(text: str, limit: int = 420) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _looks_like_event_capture(text: str) -> bool:
    t = _norm(text)
    markers = (
        "registra el siguiente evento",
        "registra este evento",
        "guarda este evento",
        "ok registra el siguiente evento",
        "ahora registra este evento",
    )
    return any(m in t for m in markers)


def _looks_like_recent_summary_query(text: str) -> bool:
    t = _norm(text)

    markers = (
        "ultimos datos compartidos",
        "ultimos eventos compartidos",
        "resumen de los eventos compartidos",
        "resumen de eventos compartidos",
        "resumen de los ultimos eventos",
        "resumen de ultimos eventos",
        "dame un resumen de los ultimos datos",
        "dame un resumen de los ultimos eventos",
        "revisa y dame un resumen de los eventos",
        "eventos recientes del caso",
        "que eventos recientes tienes",
        "que fue lo ultimo que te comparti del caso",
        "que fue lo ultimo compartido del caso",
    )

    return any(m in t for m in markers)


async def maybe_capture_karen_case_event(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    if not _looks_like_event_capture(text):
        return False

    chat_id = update.effective_chat.id
    event_text = _clean_event_text(text)

    from memory_store import insert_case_note, set_active_case_id

    set_active_case_id(int(chat_id), CASE_KEY)

    insert_case_note(
        chat_id=int(chat_id),
        case_id=CASE_KEY,
        note_text="Evento reciente del caso:\n\n" + event_text,
        source="case_recent_event_v0",
        telegram_message_id=update.message.message_id,
    )

    await update.message.reply_text(
        "Guardé este evento del caso ✅📁\n\n"
        f"{_clip(event_text, 700)}\n\n"
        "Si después quieres, dime: “dame un resumen de los últimos eventos compartidos”."
    )
    return True


def render_recent_case_events(chat_id: int, limit: int = 6) -> str:
    from memory_store import fetch_case_notes

    notes = fetch_case_notes(int(chat_id), CASE_KEY, limit=120)

    interesting_sources = {
        "case_recent_event_v0",
        "document_inventory_v0",
        "document_holder_v0",
        "document_registry_details_v0",
        "lawyer_questions_v0",
    }

    items = []
    for n in notes:
        source = str(n.get("source") or "").strip()
        raw = str(n.get("note_text") or "").strip()
        created_at = str(n.get("created_at") or "").strip()

        if not raw:
            continue

        if source not in interesting_sources:
            continue

        # Hide static lawyer question blob unless no better items exist.
        if source == "lawyer_questions_v0":
            label = "Preguntas para abogado guardadas"
            text = "Hay una lista de preguntas para abogado guardada dentro del caso."
        elif source == "case_recent_event_v0":
            label = "Evento"
            text = raw.replace("Evento reciente del caso:", "").strip()
        elif source == "document_inventory_v0":
            label = "Inventario documental"
            text = raw.replace("Inventario inicial de documentos:", "").strip()
        elif source == "document_holder_v0":
            label = "Custodia de documentos"
            text = raw.replace("Custodia / ubicación de documentos:", "").strip()
        elif source == "document_registry_details_v0":
            label = "Datos registrales"
            text = raw.replace("Datos registrales / identificadores mencionados:", "").strip()
        else:
            label = "Nota"
            text = raw

        items.append({
            "label": label,
            "text": text,
            "created_at": created_at,
        })

    if not items:
        return (
            "Claro, Insanity 😌📁\n\n"
            "Todavía no tengo eventos recientes del caso guardados como eventos.\n\n"
            "Puedes decirme algo como:\n"
            "“Registra este evento: el viernes se visitó el juzgado...”"
        )

    latest = list(reversed(items))[:limit]

    lines = [
        "Claro, Insanity 😌📁",
        "",
        "Estos son los últimos eventos/datos recientes que tengo del caso:",
        "",
    ]

    for i, item in enumerate(latest, start=1):
        lines.append(f"{i}. {item['label']}: {_clip(item['text'], 520)}")
        if item.get("created_at"):
            lines.append(f"   Guardado: {item['created_at']}")
        lines.append("")

    lines.append(
        "Siguiente paso sugerido:\n"
        "Si esos eventos están correctos, puedo ayudarte a convertirlos en preguntas para la abogada "
        "o en pendientes con fecha. Si falta algo, dime: “registra este evento...” y lo agrego."
    )

    return "\n".join(lines).strip()


async def maybe_handle_karen_recent_events_summary(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    if not _looks_like_recent_summary_query(text):
        return False

    chat_id = update.effective_chat.id
    await update.message.reply_text(render_recent_case_events(int(chat_id)))
    return True
