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

    msg = (
        "🧭 Comandos básicos\n\n"

        "📁 Crear caso\n"
        "• val crea el caso 12345 para Juan Pérez\n\n"

        "📝 Agregar nota\n"
        "• val guarda esto en el caso de Juan Pérez: cliente llamó para seguimiento\n\n"

        "⏳ Registrar término\n"
        "• val registra término en el caso de Juan Pérez: vence contestación el 25 de marzo\n\n"

        "📊 Ver estado del caso\n"
        "• val cómo va el caso de Juan Pérez\n\n"

        "🎯 Ver prioridades\n"
        "• val qué debo hacer hoy\n"
        "• val qué debo hacer mañana\n"
        "• val qué debo hacer esta semana\n\n"

        "⚠️ Casos sin movimiento\n"
        "• val casos sin movimiento\n\n"

        "⚖️ Resumen diario\n"
        "• val resumen de trabajo de hoy\n"
    )

    await update.message.reply_text(msg)
    return True
