from telegram import Update
from telegram.ext import ContextTypes

def set_pending_next_action(context: ContextTypes.DEFAULT_TYPE, action: str, label: str):
    context.user_data["karen_pending_next_action"] = {
        "action": action,
        "label": label,
    }

def get_pending_next_action(context: ContextTypes.DEFAULT_TYPE):
    return context.user_data.get("karen_pending_next_action") or {}

def clear_pending_next_action(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("karen_pending_next_action", None)

def is_confirmation(text: str) -> bool:
    t = (text or "").lower().strip()
    t = t.strip(".!¡¿? ")
    confirmations = {
        "ok",
        "okay",
        "dale",
        "si",
        "sí",
        "va",
        "vamos",
        "hagamoslo",
        "hagámoslo",
        "perfecto",
        "listo",
        "de una",
        "claro",
    }
    return t in confirmations

async def maybe_handle_pending_next_action(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    pending = get_pending_next_action(context)
    if not pending:
        return False

    if not is_confirmation(text):
        return False

    action = pending.get("action")
    clear_pending_next_action(context)

    if action == "start_document_inventory":
        await update.message.reply_text(
            "Perfecto 😏📎 Empecemos el inventario de documentos.\n\n"
            "Primera pregunta:\n"
            "¿Qué documentos tienes ahora mismo del caso?\n\n"
            "Puedes responder desordenado, por ejemplo:\n"
            "- Registro Público\n"
            "- escrituras\n"
            "- fotos de papeles\n"
            "- Word/PDF\n"
            "- resúmenes\n"
            "- papeles físicos que hay que escanear"
        )
        context.user_data["karen_document_inventory"] = {
            "active": True,
            "step": 0,
        }
        return True

    return False
