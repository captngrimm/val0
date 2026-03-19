from memory_store import set_proactive_mode
from core.case_mvp import _clean
import logging

logger = logging.getLogger(__name__)


async def try_set_mode(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if not t.startswith("val modo"):
        return False

    if "quiet" in t:
        mode = "quiet"
    elif "war" in t:
        mode = "war"
    else:
        mode = "tactical"

    try:
        set_proactive_mode(int(chat_id), mode)
    except Exception as e:
        logger.exception("mode persist failed: %s", e)

    await update.message.reply_text(f"Modo cambiado a: {mode.upper()}")

    return True

