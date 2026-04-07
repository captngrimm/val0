import logging
import re
import unicodedata
from datetime import datetime

from memory_store import upsert_fact

logger = logging.getLogger("val0-bot")
_INLINE_NUDGE_LAST = {}


def _has_active_commitment(text: str) -> bool:
    if not text:
        return False

    low = text.lower()

    markers = (
        "tengo que",
        "debo",
        "hay que",
        "debería",
        "deberia",
        "quizá",
        "quizas",
        "quizás",
        "podría",
        "podria",
    )

    return any(m in low for m in markers)


def val_select_priority_commitment(commitments: list[dict]) -> dict | None:
    if not commitments:
        return None

    def score(c):
        due = c.get("due_date") or ""
        text = (c.get("raw_input") or "").lower()

        urgency = 0
        if "ahora" in text or "now" in text:
            urgency += 3
        if due:
            urgency += 2

        length_penalty = len(text) * 0.001
        return urgency - length_penalty

    ranked = sorted(commitments, key=score, reverse=True)
    return ranked[0]


def should_emit_inline_operator_nudge(chat_id: int, raw_text: str, cooldown_seconds: int = 180) -> bool:
    global _INLINE_NUDGE_LAST

    try:
        norm = (raw_text or "").strip().lower()
        norm = unicodedata.normalize("NFKD", norm)
        norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
        norm = re.sub(r"[^\w\s]", " ", norm)
        norm = re.sub(r"\s+", " ", norm).strip()

        if not norm:
            return True

        key = f"{int(chat_id)}::{norm}"
        now = datetime.utcnow()

        last_dt = _INLINE_NUDGE_LAST.get(key)
        if last_dt is not None:
            try:
                if (now - last_dt).total_seconds() < cooldown_seconds:
                    return False
            except Exception:
                pass

        _INLINE_NUDGE_LAST[key] = now

        try:
            fact_key = f"inline_nudge_at:{norm}"
            upsert_fact(chat_id=chat_id, fact_key=fact_key, fact_value=now.isoformat())
        except Exception:
            pass

        return True

    except Exception as e:
        logger.exception(f"[INLINE_NUDGE_COOLDOWN] failed: {e}")
        return True
