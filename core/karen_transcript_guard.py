from telegram import Update
from telegram.ext import ContextTypes

def looks_like_pasted_transcript(text: str) -> bool:
    t = text or ""
    low = t.lower()

    # WhatsApp / Telegram style pasted logs
    transcript_markers = (
        "valeria:",
        "frank:",
        "karen:",
        "[5/",
        "[202",
        "am]",
        "pm]",
    )

    marker_hits = sum(1 for m in transcript_markers if m in low)

    # Long pasted blocks / logs
    line_count = t.count("\n") + 1
    very_long = len(t) >= 900
    many_lines = line_count >= 10

    # Code/terminal-ish pasted blocks during user flows
    codeish = (
        "python3 -" in low
        or "systemctl" in low
        or "git log" in low
        or "traceback" in low
        or "```" in t
    )

    return marker_hits >= 2 or very_long or many_lines or codeish


def has_active_karen_flow(context: ContextTypes.DEFAULT_TYPE) -> bool:
    flows = (
        "karen_interrogator",
        "karen_document_inventory",
    )

    for key in flows:
        state = context.user_data.get(key) or {}
        if state.get("active"):
            return True

    return False


def set_pending_transcript_guard(context: ContextTypes.DEFAULT_TYPE, flow_key: str, text: str):
    context.user_data["karen_pending_transcript_guard"] = {
        "active": True,
        "flow_key": flow_key,
        "text": text,
    }


def get_active_flow_key(context: ContextTypes.DEFAULT_TYPE) -> str:
    for key in ("karen_interrogator", "karen_document_inventory"):
        state = context.user_data.get(key) or {}
        if state.get("active"):
            return key
    return ""


async def maybe_guard_pasted_transcript(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    if not has_active_karen_flow(context):
        return False

    if not looks_like_pasted_transcript(text):
        return False

    flow_key = get_active_flow_key(context)
    set_pending_transcript_guard(context, flow_key=flow_key, text=text)

    await update.message.reply_text(
        "Ojito 😏📎\n\n"
        "Esto parece un transcript, bloque largo o texto pegado, no una respuesta normal a la pregunta actual.\n\n"
        "Para no ensuciar el caso como gaveta de cables, dime qué hago con esto:\n\n"
        "1. usar como respuesta actual\n"
        "2. guardar como nota del caso\n"
        "3. ignorar"
    )
    return True


async def maybe_handle_pending_transcript_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    pending = context.user_data.get("karen_pending_transcript_guard") or {}
    if not pending.get("active"):
        return False

    t = (text or "").lower().strip()
    t = t.strip(".!¡¿? ")

    original = pending.get("text") or ""

    if t in {"3", "ignorar", "ignóralo", "ignoralo", "descartar", "no"}:
        context.user_data.pop("karen_pending_transcript_guard", None)
        await update.message.reply_text("Listo. Ignoré ese bloque para el flujo actual. Nada de ensuciar memoria. 😌")
        return True

    if t in {"2", "guardar como nota", "nota", "guardalo como nota", "guárdalo como nota", "guardar nota"}:
        from memory_store import insert_case_note, set_active_case_id

        chat_id = int(update.effective_chat.id)
        case_key = "KAREN-LAND-001"
        set_active_case_id(chat_id, case_key)

        insert_case_note(
            chat_id=chat_id,
            case_id=case_key,
            note_text="Bloque/transcript pegado por el usuario:\n\n" + original,
            source="pasted_transcript_guard_v0",
            telegram_message_id=update.message.message_id,
        )

        context.user_data.pop("karen_pending_transcript_guard", None)
        await update.message.reply_text(
            "Guardado ✅📎\n\n"
            "Lo dejé como nota del caso, separado del flujo actual para no confundir respuestas."
        )
        return True

    if t in {"1", "usar como respuesta actual", "usar", "respuesta actual", "úsalo", "usalo"}:
        # Do not process recursively here; caller should detect this flag and route original text.
        context.user_data["karen_pending_transcript_guard"]["use_as_current_answer"] = True
        await update.message.reply_text(
            "Perfecto. Lo usaré como respuesta actual.\n\n"
            "Reenvía el bloque una vez más y lo proceso en el flujo. Sí, es un paso extra; mejor eso que meter basura al caso como animal. 😏"
        )
        context.user_data.pop("karen_pending_transcript_guard", None)
        return True

    await update.message.reply_text(
        "Respóndeme con una opción simple:\n"
        "1 = usar como respuesta actual\n"
        "2 = guardar como nota del caso\n"
        "3 = ignorar"
    )
    return True
