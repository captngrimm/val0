import logging

logger = logging.getLogger("val0-bot")

DEBUG_MODE = {}
def pop_debug_mode(chat_id: int) -> bool:
    return DEBUG_MODE.pop(int(chat_id), False)


async def try_debug_mode(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip().lower()

    if not (
        t.startswith("val debug")
        or t == "debug"
        or "debug mode" in t
    ):
        return False

    DEBUG_MODE[int(chat_id)] = True

    await update.message.reply_text(
        "🧠 Debug mode ACTIVATED\n"
        "Next command will include internal reasoning."
    )

    return True

def build_user_help_message() -> str:
    return (
        "🧭 Ayuda rápida de Valeria\n\n"
        "Puedes usarme como una asistente simple por Telegram para memoria, notas, recordatorios y tareas.\n\n"

        "📝 Notas\n"
        "• Guarda esta nota: comprar leche\n"
        "• Anota: llamar a mamá\n"
        "• /notes\n\n"

        "⏰ Recordatorios\n"
        "• Recuérdame llamar mañana a las 9\n"
        "• /reminders\n"
        "• /rmd <id> para cancelar uno\n\n"

        "✅ Tareas\n"
        "• Tengo que revisar el contrato mañana\n"
        "• /tasks\n"
        "• Ya hice revisar el contrato\n\n"

        "📌 Pendientes y agenda\n"
        "• ¿Qué tengo pendiente?\n"
        "• ¿Qué tengo mañana?\n"
        "• ¿Qué debo hacer hoy?\n\n"

        "🧠 Memoria\n"
        "• Me llamo Karen\n"
        "• Mi color favorito es verde\n"
        "• ¿Qué recuerdas de mí?\n\n"

        "🎙️ Voz\n"
        "• /voice on\n"
        "• /voice off\n\n"

        "🛠️ Reportes\n"
        "• /bug algo falló\n"
        "• /feedback comentario\n"
        "• /idea nueva idea\n\n"

        "Siguiente paso: prueba una nota, recordatorio o tarea simple."
    )


async def help_cmd(update, context):
    if not update or not getattr(update, "message", None):
        return
    await update.message.reply_text(build_user_help_message())


async def try_help(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").lower()

    if not (
        "ayuda" in t
        or "help" in t
        or "comandos" in t
        or "ejemplos" in t
    ):
        return False

    await update.message.reply_text(build_user_help_message())
    return True
