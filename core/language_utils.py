import re

from memory_store import get_fact


def resolve_user_language(chat_id: int) -> str:
    try:
        lang = get_fact(chat_id=chat_id, fact_key="preferred_language")
        if lang in ("es", "en"):
            return lang
    except Exception:
        pass

    return "es"


def render_operator_reminder(chat_id: int, raw_text: str, target: str = "") -> str:
    lang = resolve_user_language(chat_id)

    target_title = str(target or "").strip().title()
    clean = (raw_text or "").strip()

    if lang == "en":
        if target_title:
            return f"{target_title} is still pending. Done, tonight, or snooze?"
        return f"{clean} is still pending. Done, tonight, or snooze?"

    clean = str(clean or "").strip()

    if clean:
        clean = clean[:1].upper() + clean[1:]

    clean = re.sub(r"\bnoah\b", "Noah", clean, flags=re.IGNORECASE)

    if target_title:
        return f"⏰ *{target_title}* sigue pendiente.\n¿Hecho, esta noche o posponer?"
    return f"⏰ *{clean}* sigue pendiente.\n¿Hecho, esta noche o posponer?"
