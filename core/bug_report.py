import json
import os
from datetime import datetime, timezone

_PENDING_BUG_REPORT = {}

BUG_REPORT_PATH = "/opt/val0/logs/bug_reports.jsonl"


async def _block_if_pending_report(update, kind: str) -> bool:
    """
    Prevent slash-command interruption while a guided bug/feedback/idea flow is active.

    kind:
      - "same" for re-entering the same command (/bug while bug active, etc.)
      - "other" for trying a different command like /reports during an active flow
    """
    if not update or not getattr(update, "effective_chat", None):
        return False

    msg = getattr(update, "effective_message", None)
    if msg is None:
        return False

    chat_id = int(update.effective_chat.id)
    pending = _PENDING_BUG_REPORT.get(chat_id)
    if not pending:
        return False

    pending_kind = str(pending.get("kind") or "bug").strip().lower()

    if kind == "same":
        await msg.reply_text(
            f"Tienes un {pending_kind} en curso.\n\n"
            "Respóndeme la siguiente pregunta para terminarlo, o escribe /cancelreport para cancelarlo."
        )
        return True

    await msg.reply_text(
        f"Tienes un {pending_kind} en curso.\n\n"
        "Termínalo primero o escribe /cancelreport para cancelarlo antes de usar otro comando."
    )
    return True


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
    kind = (p.get("kind") or "bug").strip().lower()

    labels = {
        "attempt": "qué intentabas hacer",
        "actual": "qué pasó",
        "expected": "qué esperabas",
        "channel": "si fue por texto o por voz",
    }

    kind_labels = {
        "bug": "Reporte de bug",
        "feedback": "Feedback",
        "idea": "Idea",
    }

    return f"• {kind_labels.get(kind, 'Reporte')} pendiente: falta {labels.get(step, step)}"


def _start_report(update, kind: str):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if msg is None or chat is None:
        return None, None

    chat_id = int(chat.id)

    _PENDING_BUG_REPORT[chat_id] = {
        "kind": kind,
        "step": "attempt",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "chat_id": chat_id,
        "user_id": getattr(user, "id", None),
        "username": getattr(user, "username", None),
        "display_name": getattr(user, "full_name", None),
    }

    opening = {
        "bug": "Vamos a registrar el problema.",
        "feedback": "Vamos a registrar tu feedback.",
        "idea": "Vamos a registrar tu idea.",
    }

    return msg, opening.get(kind, "Vamos a registrar esto.")


async def cancelreport_cmd(update, context):
    if not update or not getattr(update, "effective_chat", None):
        return

    msg = getattr(update, "effective_message", None)
    if msg is None:
        return

    chat_id = int(update.effective_chat.id)
    pending = _PENDING_BUG_REPORT.pop(chat_id, None)

    if pending:
        kind = str(pending.get("kind") or "reporte").strip().lower()
        await msg.reply_text(f"Entendido. Cancelé el {kind} en curso.")
    else:
        await msg.reply_text("No tienes ningún reporte en curso.")


async def bug_cmd(update, context):
    if await _block_if_pending_report(update, "same"):
        return

    msg, opening = _start_report(update, "bug")
    if msg is None:
        return

    await msg.reply_text(
        opening + "\n\n"
        "1/4 — ¿Qué intentabas hacer?"
    )


async def feedback_cmd(update, context):
    if await _block_if_pending_report(update, "other"):
        return

    msg, opening = _start_report(update, "feedback")
    if msg is None:
        return

    await msg.reply_text(
        opening + "\n\n"
        "1/4 — ¿Qué intentabas hacer o en qué contexto estabas?"
    )


async def idea_cmd(update, context):
    if await _block_if_pending_report(update, "other"):
        return

    msg, opening = _start_report(update, "idea")
    if msg is None:
        return

    await msg.reply_text(
        opening + "\n\n"
        "1/4 — ¿Cuál es la idea o mejora que se te ocurrió?"
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
    kind = (p.get("kind") or "bug").strip().lower()

    q2 = {
        "bug": "2/4 — ¿Qué pasó realmente?",
        "feedback": "2/4 — ¿Qué pasó o cómo se sintió?",
        "idea": "2/4 — ¿Qué problema resolvería o qué mejoraría?",
    }

    q3 = {
        "bug": "3/4 — ¿Qué esperabas que pasara?",
        "feedback": "3/4 — ¿Qué te habría gustado que pasara?",
        "idea": "3/4 — ¿Cómo te imaginas que debería funcionar?",
    }

    if step == "attempt":
        p["attempted_action"] = t
        p["step"] = "actual"
        await msg.reply_text(q2.get(kind, "2/4 — ¿Qué pasó realmente?"))
        return True

    if step == "actual":
        p["actual_result"] = t
        p["step"] = "expected"
        await msg.reply_text(q3.get(kind, "3/4 — ¿Qué esperabas que pasara?"))
        return True

    if step == "expected":
        p["expected_result"] = t
        p["step"] = "channel"
        await msg.reply_text("4/4 — ¿Esto viene más por texto, voz, o uso general?")
        return True

    if step == "channel":
        p["channel"] = t
        p["completed_at"] = datetime.now(timezone.utc).isoformat()

        payload = {
            "kind": p.get("kind", "bug"),
            "started_at": p.get("started_at"),
            "completed_at": p.get("completed_at"),
            "chat_id": p.get("chat_id"),
            "user_id": p.get("user_id"),
            "username": p.get("username"),
            "display_name": p.get("display_name"),
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


def read_recent_reports(limit: int = 5) -> list[dict]:
    if limit < 1:
        limit = 1
    if limit > 20:
        limit = 20

    if not os.path.exists(BUG_REPORT_PATH):
        return []

    rows = []
    with open(BUG_REPORT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = (line or "").strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue

    return rows[-limit:]


async def reports_cmd(update, context):
    if await _block_if_pending_report(update, "other"):
        return

    msg = update.effective_message
    if msg is None:
        return

    from memory_store import get_fact

    n = 5
    try:
        parts = (msg.text or "").strip().split()
        if len(parts) >= 2:
            n = int(parts[1])
    except Exception:
        n = 5

    rows = read_recent_reports(limit=n)

    if not rows:
        await msg.reply_text("No veo reportes todavía.")
        return

    lines = [f"Últimos {len(rows)} reporte(s):", ""]

    for idx, r in enumerate(reversed(rows), start=1):
        kind = (r.get("kind") or "bug").strip().upper()
        attempted = (r.get("attempted_action") or "").strip()
        actual = (r.get("actual_result") or "").strip()
        expected = (r.get("expected_result") or "").strip()
        channel = (r.get("channel") or "").strip()

        report_chat_id = r.get("chat_id")
        preferred_name = ""
        try:
            if report_chat_id is not None:
                preferred_name = (get_fact(int(report_chat_id), "preferred_name") or "").strip()
        except Exception:
            preferred_name = ""

        display_name = (r.get("display_name") or "").strip()
        username = (r.get("username") or "").strip()
        user_id = r.get("user_id")

        author = preferred_name or display_name or username or (str(user_id) if user_id is not None else "desconocido")

        def _clip(s: str, limit: int = 90) -> str:
            s = (s or "").strip()
            return s if len(s) <= limit else s[:limit] + "…"

        lines.append(f"[{kind}] {author}")
        if attempted:
            lines.append(f"- Contexto: {_clip(attempted)}")
        if actual:
            lines.append(f"- Resultado: {_clip(actual)}")
        if expected:
            lines.append(f"- Esperado: {_clip(expected)}")
        if channel:
            lines.append(f"- Canal: {_clip(channel, 40)}")

        if idx < len(rows):
            lines.append("")

    await msg.reply_text("\n".join(lines))