import json
import os
from datetime import datetime, timezone

_PENDING_BUG_REPORT = {}

BUG_REPORT_PATH = "/opt/val0/logs/bug_reports.jsonl"


def _ensure_bug_log_dir() -> None:
    os.makedirs(os.path.dirname(BUG_REPORT_PATH), exist_ok=True)


def _append_bug_report(payload: dict) -> None:
    _ensure_bug_log_dir()
    with open(BUG_REPORT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def get_pending_bug_report_text(chat_id: int) -> str | None:
    p = _PENDING_BUG_REPORT.get(int(chat_id))
    if not p:
        return None

    step = p.get("step", "attempt")
    labels = {
        "attempt": "qué intentabas hacer",
        "actual": "qué pasó",
        "expected": "qué esperabas",
        "channel": "si fue por texto o por voz",
    }
    return f"• Reporte de bug pendiente: falta {labels.get(step, step)}"


async def bug_cmd(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if msg is None or chat is None:
        return

    chat_id = int(chat.id)

    _PENDING_BUG_REPORT[chat_id] = {
        "step": "attempt",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "chat_id": chat_id,
        "user_id": getattr(user, "id", None),
        "username": getattr(user, "username", None),
    }

    await msg.reply_text(
        "Vamos a registrar el problema.\n\n"
        "1/4 — ¿Qué intentabas hacer?"
    )


async def handle_pending_bug_report(update, chat_id: int, text: str) -> bool:
    msg = update.effective_message
    if msg is None:
        return False

    p = _PENDING_BUG_REPORT.get(int(chat_id))
    if not p:
        return False

    t = (text or "").strip()
    if not t:
        await msg.reply_text("Necesito un poco más de detalle para seguir.")
        return True

    step = p.get("step")

    if step == "attempt":
        p["attempted_action"] = t
        p["step"] = "actual"
        await msg.reply_text("2/4 — ¿Qué pasó realmente?")
        return True

    if step == "actual":
        p["actual_result"] = t
        p["step"] = "expected"
        await msg.reply_text("3/4 — ¿Qué esperabas que pasara?")
        return True

    if step == "expected":
        p["expected_result"] = t
        p["step"] = "channel"
        await msg.reply_text("4/4 — ¿Fue por texto o por voz?")
        return True

    if step == "channel":
        p["channel"] = t
        p["completed_at"] = datetime.now(timezone.utc).isoformat()

        payload = {
            "started_at": p.get("started_at"),
            "completed_at": p.get("completed_at"),
            "chat_id": p.get("chat_id"),
            "user_id": p.get("user_id"),
            "username": p.get("username"),
            "attempted_action": p.get("attempted_action", ""),
            "actual_result": p.get("actual_result", ""),
            "expected_result": p.get("expected_result", ""),
            "channel": p.get("channel", ""),
        }

        _append_bug_report(payload)
        _PENDING_BUG_REPORT.pop(int(chat_id), None)

        await msg.reply_text(
            "Listo. Ya quedó registrado para revisión.\n\n"
            "Si quieres, ahora puedes mandarme screenshot o más contexto en otro mensaje."
        )
        return True

    _PENDING_BUG_REPORT.pop(int(chat_id), None)
    return False

