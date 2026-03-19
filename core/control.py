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

