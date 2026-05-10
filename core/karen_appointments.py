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


def _looks_like_appointment(text: str) -> bool:
    t = _norm(text)
    has_meeting = any(x in t for x in [
        "cita",
        "reunion",
        "reunión",
        "llamada",
        "entrega de documentos",
        "llevar documentos",
        "llevar la documentacion",
        "llevar la documentación",
    ])
    has_legal_person = any(x in t for x in [
        "abogada",
        "abogado",
        "nora",
        "nora santa",
        "despacho",
    ])
    return has_meeting and has_legal_person


def _looks_like_reschedule(text: str) -> bool:
    t = _norm(text)
    has_change = any(x in t for x in [
        "cambiaron",
        "cambio",
        "cambió",
        "cambiar",
        "movieron",
        "se movio",
        "se movió",
        "ya no es",
        "ahora es",
        "ahora queda",
        "quedo para",
        "quedó para",
    ])
    has_meeting = any(x in t for x in [
        "cita",
        "reunion",
        "reunión",
        "llamada",
        "abogada",
        "abogado",
        "nora",
    ])
    return has_change and has_meeting


def _clean_appointment_text(text: str) -> str:
    raw = (text or "").strip()
    prefixes = [
        "val,",
        "val ",
    ]
    low = raw.lower()
    for p in prefixes:
        if low.startswith(p):
            return raw[len(p):].strip()
    return raw


async def maybe_handle_karen_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    raw = _clean_appointment_text(text)

    # Reminder phrases must be handled by the reminder system, not appointment memory.
    # Examples:
    # - Val, recuérdame en 5 minutos revisar documentos
    # - recuérdame dos horas antes llevar documentos a Nora
    reminderish = _norm(raw)
    if (
        reminderish.startswith("recuerdame")
        or reminderish.startswith("recuérdame")
        or reminderish.startswith("recordatorio")
        or reminderish.startswith("acuerdame")
        or reminderish.startswith("acuérdame")
    ):
        return False

    if not (_looks_like_appointment(raw) or _looks_like_reschedule(raw)):
        return False

    chat_id = update.effective_chat.id

    from memory_store import insert_case_note, set_active_case_id

    set_active_case_id(int(chat_id), CASE_KEY)

    source = "case_appointment_reschedule_v0" if _looks_like_reschedule(raw) else "case_appointment_v0"
    label = "Cambio de cita / agenda del caso" if source == "case_appointment_reschedule_v0" else "Cita / agenda del caso"

    insert_case_note(
        chat_id=int(chat_id),
        case_id=CASE_KEY,
        note_text=f"{label}:\n\n{raw}",
        source=source,
        telegram_message_id=update.message.message_id,
    )

    if source == "case_appointment_reschedule_v0":
        await update.message.reply_text(
            "Listo, Insanity 😌📅\n\n"
            "Guardé el cambio de cita/agenda dentro del caso del terreno:\n\n"
            f"{raw}\n\n"
            "Ojo: esto queda registrado como seguimiento del caso. Si quieres un aviso automático exacto, dime también: "
            "“recuérdame…” con fecha y hora."
        )
        return True

    await update.message.reply_text(
        "Listo, Insanity 😌📅\n\n"
        "Guardé esta cita/agenda dentro del caso del terreno:\n\n"
        f"{raw}\n\n"
        "Siguiente paso: si quieres que además te avise, dime algo como: "
        "“Val, recuérdame una hora antes preparar los documentos”."
    )
    return True
