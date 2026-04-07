import logging
import re
import unicodedata

from memory_store import (
    _get_conn,
    insert_case_event,
    mark_processed_event_once,
)
from core.case_summary import refresh_case_summary
from core.reminder_actions import parse_reminder_action, apply_reminder_action
from core.reminders_mvp import try_create_reminder, try_cancel_reminder

logger = logging.getLogger("val0-bot")
_PENDING_REMINDER_CONFIRM = {}


async def handle_pending_reminder_confirmation(update, chat_id, text, last_action_dict):
    """
    Handle confirmation/cancellation of pending reminder registration.
    last_action_dict: reference to bot.py's _LAST_ACTION dict
    """
    if int(chat_id) not in _PENDING_REMINDER_CONFIRM:
        return False

    pending = _PENDING_REMINDER_CONFIRM.get(int(chat_id))

    confirm_low = (text or "").strip().lower()
    confirm_low = unicodedata.normalize("NFKD", confirm_low)
    confirm_low = "".join(ch for ch in confirm_low if not unicodedata.combining(ch))
    confirm_low = re.sub(r"[^\w\s]", " ", confirm_low)
    confirm_low = re.sub(r"\s+", " ", confirm_low).strip()

    confirm_yes = (
        "si", "ok", "dale", "hazlo", "registralo", "guardalo",
        "si dale", "si hazlo", "si registralo", "si guardalo",
        "ok dale", "ok hazlo", "ok registralo", "dale hazlo",
    )
    confirm_no = (
        "no", "cancelar", "olvidalo", "mejor no",
        "no lo registres", "no lo registres por ahora",
    )

    if confirm_low in confirm_yes:
        _PENDING_REMINDER_CONFIRM.pop(int(chat_id), None)

        event_text = f"RECORDATORIO: {pending['reminder_text']}"

        dup = False
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id
                FROM case_events
                WHERE chat_id=?
                  AND case_id=?
                  AND event_text=?
                  AND IFNULL(deadline_date,'') = IFNULL(?, '')
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    int(chat_id),
                    int(pending["case_id"]),
                    event_text,
                    pending["due_date"],
                ),
            )
            row = cur.fetchone()
            conn.close()
            if row:
                dup = True
        except Exception:
            dup = False

        if dup:
            await update.message.reply_text(
                f"⚠️ Recordatorio duplicado detectado en CASE:{pending['case_id']}."
            )
            return True

        insert_case_event(
            chat_id=int(chat_id),
            case_id=int(pending["case_id"]),
            event_text=event_text,
            deadline_date=pending["due_date"],
        )

        event_id = None
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id
                FROM case_events
                WHERE chat_id=?
                  AND case_id=?
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    int(chat_id),
                    int(pending["case_id"]),
                ),
            )
            row = cur.fetchone()
            conn.close()
            if row:
                event_id = row["id"] if hasattr(row, "keys") else row[0]
        except Exception:
            pass

        last_action_dict[int(chat_id)] = {
            "type": "reminder_insert",
            "id": event_id,
            "case_id": str(pending["case_id"]),
        }

        refresh_case_summary(int(chat_id), str(pending["case_id"]))

        await update.message.reply_text(
            f"⏰ Recordatorio registrado en CASE:{pending['case_id']}\nFecha: {pending['due_date']}"
        )
        return True

    if confirm_low in confirm_no:
        _PENDING_REMINDER_CONFIRM.pop(int(chat_id), None)
        await update.message.reply_text("Entendido. No lo registré.")
        return True

    return False


async def handle_reminder_action_intercept(update, chat_id, tg_msg_id, text, normalized, send_reply_fn):
    """
    Handle explicit reminder actions (done, snooze, etc.).
    send_reply_fn: callback function for sending telegram reply
    """
    try:
        parsed = parse_reminder_action(text)
        if parsed:
            action_name = parsed.get("action", "unknown")
            reminder_event_key = f"reminder_action:{chat_id}:{tg_msg_id}:{action_name}:{normalized}"

            inserted = mark_processed_event_once(reminder_event_key, "reminder_action")
            if not inserted:
                logger.info(f"[IDEMPOTENCY] skip duplicate reminder action: {reminder_event_key}")
                return True

            result = apply_reminder_action(chat_id, parsed)
            if result:
                await send_reply_fn(update, result, chat_id, "reminder_action_reply")
                return True
    except Exception as e:
        logger.exception(f"[REMINDER_ACTION] failed: {e}")
    return False


async def handle_reminder_gate(update, chat_id, text, audit_fn):
    """
    Deterministic reminder creation/cancellation gate (DM only).
    """
    try:
        audit_fn(
            chat_id,
            action="DEBUG_REMINDER_GATE_ENTER",
            entity_type="debug",
            entity_id=None,
            payload=(text or "")[:200],
            source="dm",
        )

        if int(chat_id) > 0:
            cancel_handled = await try_cancel_reminder(update, chat_id, text, audit_fn=audit_fn)
            logger.info(f"[REMINDER_GATE] cancel_handled={cancel_handled} text={text!r}")
            if cancel_handled:
                return True

            create_handled = await try_create_reminder(update, chat_id, text, audit_fn=audit_fn)
            logger.info(f"[REMINDER_GATE] create_handled={create_handled} text={text!r}")
            if create_handled:
                return True
    except Exception as e:
        logger.exception(f"[GATE] reminder gate failed: {e}")
    return False
