import datetime
import logging
import re
import unicodedata
from datetime import timedelta
from zoneinfo import ZoneInfo

from memory_store import (
    fetch_due_commitments,
    mark_commitment_nudged,
    log_action,
    get_last_nudge_at,
    set_last_nudge_at,
    set_last_surface_commitment_id,
)
from core.commitment_utils import val_select_priority_commitment
from core.language_utils import resolve_user_language

logger = logging.getLogger("val0-bot")
_OPERATOR_FOLLOWUP_RUNNING = False


async def operator_followup_tick(context):
    global _OPERATOR_FOLLOWUP_RUNNING

    if _OPERATOR_FOLLOWUP_RUNNING:
        logger.info("[OPERATOR_FOLLOWUP_TICK] skipped: already running")
        return

    _OPERATOR_FOLLOWUP_RUNNING = True
    try:
        NUDGE_COOLDOWN_MINUTES = 10

        def _utcnow_iso():
            return datetime.datetime.utcnow().isoformat()

        def _parse_iso(ts):
            try:
                return datetime.datetime.fromisoformat(ts)
            except Exception:
                return None

        def _norm_text(s: str) -> str:
            s = (s or "").strip().lower()
            s = unicodedata.normalize("NFKD", s)
            s = "".join(ch for ch in s if not unicodedata.combining(ch))
            s = re.sub(r"[^\w\s]", " ", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s

        rows = fetch_due_commitments(limit=50)
        fresh_cutoff = datetime.datetime.now(ZoneInfo("America/Panama")).replace(tzinfo=None) - timedelta(minutes=3)
        filtered_rows = []

        for r in rows:
            row = dict(r) if hasattr(r, "keys") else {
                "id": r[0],
                "chat_id": r[1],
                "raw_input": r[2],
                "action": r[3],
                "target": r[4],
                "due_date": r[5],
                "confidence": r[6],
                "status": r[7],
                "last_nudged_at": r[8],
                "created_at": r[9],
            }

            created_raw = row.get("created_at")
            if created_raw:
                try:
                    created_dt = datetime.datetime.fromisoformat(str(created_raw).replace(" ", "T"))
                    if created_dt > fresh_cutoff:
                        continue
                except Exception:
                    pass

            filtered_rows.append(r)

        rows = filtered_rows

        chosen_by_chat = {}
        seen_text_by_chat = {}

        for r in rows:
            row = dict(r) if hasattr(r, "keys") else r

            commitment_id = row["id"] if isinstance(row, dict) else row[0]
            chat_id = row["chat_id"] if isinstance(row, dict) else row[1]
            raw_input = row["raw_input"] if isinstance(row, dict) else row[2]

            raw_clean = (raw_input or "").strip()

            if _has_explicit_legal_intent(raw_clean):
                continue

            norm = _norm_text(raw_clean)
            if chat_id not in seen_text_by_chat:
                seen_text_by_chat[chat_id] = set()

            if norm in seen_text_by_chat[chat_id]:
                continue

            allow_nudge = True
            last_nudge = get_last_nudge_at(int(chat_id), int(commitment_id))

            if last_nudge:
                last_dt = _parse_iso(last_nudge)
                if last_dt and (datetime.datetime.utcnow() - last_dt) < timedelta(minutes=NUDGE_COOLDOWN_MINUTES):
                    allow_nudge = False

            if not allow_nudge:
                continue

            if int(chat_id) in chosen_by_chat:
                continue

            chosen_by_chat[int(chat_id)] = {
                "commitment_id": int(commitment_id),
                "chat_id": int(chat_id),
                "raw_input": raw_clean,
            }
            seen_text_by_chat[chat_id].add(norm)

        grouped = {}
        for _, item in chosen_by_chat.items():
            grouped.setdefault(item["chat_id"], []).append(item)

        for chat_id, items in grouped.items():
            selected = val_select_priority_commitment(items)
            if not selected:
                continue

            commitment_id = selected["commitment_id"]
            clean = str(selected["raw_input"] or "").strip()

            if clean:
                clean = clean[:1].upper() + clean[1:]

            clean = re.sub(r"\bnoah\b", "Noah", clean, flags=re.IGNORECASE)

            lang = resolve_user_language(int(chat_id))

            if lang == "en":
                msg = f"⏰ *{clean}* is still pending.\nDone, tonight, or snooze?"
            else:
                msg = f"⏰ *{clean}* sigue pendiente.\n¿Hecho, esta noche o posponer?"

            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

            set_last_surface_commitment_id(int(chat_id), int(commitment_id))
            set_last_nudge_at(int(chat_id), int(commitment_id), _utcnow_iso())
            mark_commitment_nudged(commitment_id)
            log_action(int(chat_id), "operator_nudge", clean)

    except Exception as e:
        logger.exception(f"[OPERATOR_FOLLOWUP_TICK] failed: {e}")
    finally:
        _OPERATOR_FOLLOWUP_RUNNING = False


def _has_explicit_legal_intent(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False

    legal_markers = [
        "caso",
        "expediente",
        "recordatorio legal",
        "legal",
        "registrar en caso",
        "registrar caso",
        "en el caso",
        "para el caso",
        "case:",
        "case ",
        "client_name",
        "principal_id",
    ]

    return any(marker in t for marker in legal_markers)
