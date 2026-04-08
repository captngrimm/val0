"""
VAL0 BOT — NAVIGATION MAP (DO NOT DELETE)

PIPELINE OVERVIEW (top → bottom):

1) Command handlers
   - /start, /note, /daily, /dailies, etc.

2) _process_text_pipeline()
   a) Identity & preferences (name, language)
   b) Timers / nudges (CO1)
   c) Message persistence (insert_message)
   d) Fast memory intercepts (facts, notes)
   e) External tools (Places)
   f) CONTEXT ASSEMBLY (authoritative):
      - get_recent_messages()
      - build_context_block()
      - get_all_facts()
      - _semantic_recall_block()
   g) MODEL CALL:
      - call_val_openai(...)

3) Post-reply persistence
   - insert_message (assistant)

SOURCE OF TRUTH:
- Prompt assembly happens ONLY in _process_text_pipeline()
- call_val_openai() is the final gateway to the model
"""


import time
import shutil
import asyncio

# === MODE HANDLER (must ALWAYS exist if referenced later) ===
from core.mode import try_set_mode
from core.language_utils import render_operator_reminder, resolve_user_language
from core.commitment_utils import (
    _has_active_commitment,
    val_select_priority_commitment,
    should_emit_inline_operator_nudge,
)
from core.operator_followup import operator_followup_tick
from core.operator_reminders import (
    handle_pending_reminder_confirmation,
    handle_reminder_action_intercept,
    handle_reminder_gate,
    _PENDING_REMINDER_CONFIRM,
)

from core.context_snapshot import build_context_snapshot




# --- MIGUEL MVP: gates wiring (safe optional imports) ---
try:
    from core.case_mvp import (
        try_case_summary,
        try_due_today,
        try_due_range,
        try_delete_last_note,
        try_undo_last_action,
    )
    from core.case_reports import (
        try_idle_cases,
        try_daily_work_summary,
        try_priority_dashboard,
    )
    from core.ops_cmds import ops_cmd, health_cmd, reminders_cmd, rmd_cmd
except Exception:
    pass
    # Fallback stubs: keep bot stable even if module isn't present yet

import os
import logging
import unicodedata
import datetime
from datetime import timedelta
from forge_ingest_helper import send_audio_to_forge
import pytz
from typing import List, Dict, Any, Optional
from datetime import time as dt_time
from dotenv import load_dotenv
import openai
import re
import smtplib
import requests
from email.mime.text import MIMEText
from email.utils import formataddr

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    Defaults,
    filters,
)

# Memory + Notes
from memory_store import (
    _get_conn,
    init_db,
    insert_message,
    get_recent_messages,
    upsert_fact,
    get_fact,
    get_all_facts,
    add_note,
    get_notes,
    search_notes,
    upsert_daily_log,
    get_daily_logs,
    search_daily_logs,
    log_action,
    has_processed_event,
    mark_processed_event,
    mark_processed_event_once,

    fetch_due_reminders,
    claim_due_reminders,
    claim_reminder,
    mark_reminder_sent,
    mark_reminder_failed,
    revert_reminder_pending,
)

def ensure_current_priority(chat_id: int):
    existing = None
    try:
        existing = get_fact(chat_id=chat_id, fact_key="current_priority")
    except Exception:
        existing = None

    if existing:
        return

    priority_text = (
        "preserve continuity across chats\n"
        "refine /context into better handoff/state snapshot\n"
        "then continue with post-Sunday continuity / persistent interface work"
    )

    try:
        upsert_fact(chat_id=chat_id, fact_key="current_priority", fact_value=priority_text)
    except Exception:
        pass

def get_current_priority_lines(chat_id: int):
    try:
        raw = get_fact(chat_id=chat_id, fact_key="current_priority")
    except Exception:
        raw = None

    if not raw:
        return [
            "- preserve continuity across chats",
            "- refine /context into better handoff/state snapshot",
            "- then continue with post-Sunday continuity / persistent interface work",
        ]

    raw = str(raw).strip()
    parts = [p.strip(" -•\n\r\t") for p in raw.splitlines() if p.strip()]
    if len(parts) <= 1 and ";" in raw:
        parts = [p.strip() for p in raw.split(";") if p.strip()]

    out = [f"- {p}" for p in parts[:6] if p]
    return out or [
        "- preserve continuity across chats",
        "- refine /context into better handoff/state snapshot",
        "- then continue with post-Sunday continuity / persistent interface work",
    ]


def get_build_status_lines(chat_id: int):
    return [
        "- persistent memory working",
        "- recall working",
        "- sensitive filtering working",
        "- task classification working",
        "- commitment extraction working",
        "- proactive follow-up working",
        "- completion loop working",
        "- operator override working",
        "- M2 repetition/context weighting working",
        "- M3 time/pattern awareness working",
        "- /context working",
    ]

def seed_build_status(chat_id: int):
    build_flags = {
        "persistent_memory": "working",
        "recall": "working",
        "sensitive_filtering": "working",
        "task_classification": "working",
        "commitment_extraction": "working",
        "proactive_followup": "working",
        "completion_loop": "working",
        "operator_override": "working",
        "m2_weighting": "working",
        "m3_time_awareness": "working",
        "context_command": "working",
    }

    for key, value in build_flags.items():
        try:
            upsert_fact(chat_id=chat_id, fact_key=key, fact_value=value)
        except Exception:
            pass


# Places API
from places.places_engine import places_search, place_details

# Semantic Memory (FAISS)
from semantic.memory_embeddings import MemoryEmbeddings

# --------------------------------------------------
# Places session (process memory, resets on restart)
# Stores last search results so user can reply "1", "2", etc.
# --------------------------------------------------
_PLACES_SESSION = {}  # chat_id -> {"ts": epoch, "results": [ {place_id, name, maps_url, ...}, ... ]}

def _places_session_set(chat_id: int, results):
    try:
        _PLACES_SESSION[int(chat_id)] = {"ts": int(time.time()), "results": list(results or [])}
    except Exception:
        pass

def _places_session_get(chat_id: int):
    try:
        return _PLACES_SESSION.get(int(chat_id))
    except Exception:
        return None

# --------------------------------------------------
# Companion Operator v0 — session timing
# --------------------------------------------------
_CO_SESSION = {}  # chat_id -> {"start": epoch, "nudged": bool}
_PENDING_TERM_CONFIRM = {}
_PENDING_CASE_DISAMBIG = {}
_PENDING_REMINDER_CONFIRM = {}
# --- last action tracker (demo-safe undo) ---
_LAST_ACTION = {}
_INLINE_NUDGE_LAST = {}
# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("val0-bot")

# =========================
# CASE CAPTURE (Phase B0)
# =========================
import re as _re_case

_CASE_RE = _re_case.compile(r"\b(?:expediente|exp|caso|case)\s*[:#]?\s*(\d{4,})\b", _re_case.IGNORECASE)

def _extract_case_id(text: str) -> str:
    if not text:
        return ""
    m = _CASE_RE.search(text)
    return (m.group(1) or "").strip() if m else ""

# --- Sprint08 deterministic deadline extractor ---
def _extract_deadline_date(text: str) -> str:
    raw = (text or "").strip().lower()
    low = unicodedata.normalize("NFKD", raw)
    low = "".join(ch for ch in low if not unicodedata.combining(ch))

    month_map = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "setiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }

    m = re.search(
        r"\b(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b",
        low,
    )
    if not m:
        return None

    day = int(m.group(1))
    month_name = m.group(2)
    month = month_map[month_name]

    year = datetime.now(ZoneInfo("America/Panama")).year
    return f"{year:04d}-{month:02d}-{day:02d}"

def is_low_signal_case_note(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return True

    blocked_contains = (
        "router hygiene",
        "prueba limpia router",
        "test note",
        "nota de prueba",
        "prueba del sistema",
        "debug",
        "prueba debug",
        "smoke test",
        "tmp",
        "temporary test",
    )

    return any(x in t for x in blocked_contains)

def _get_pending_state_text(chat_id: int) -> str | None:
    parts = []

    if int(chat_id) in _PENDING_CASE_DISAMBIG:
        dis = _PENDING_CASE_DISAMBIG[int(chat_id)]
        dtype = dis.get("type", "desconocido")
        count = len(dis.get("candidates", []) or [])
        parts.append(f"• Selección pendiente: {dtype} ({count} opción(es))")

    if int(chat_id) in _PENDING_TERM_CONFIRM:
        p = _PENDING_TERM_CONFIRM[int(chat_id)]
        parts.append(
            f"• Término pendiente de confirmar: CASE:{p.get('case_id')} | vence {p.get('deadline_date')}"
        )

    if int(chat_id) in _PENDING_REMINDER_CONFIRM:
        p = _PENDING_REMINDER_CONFIRM[int(chat_id)]
        parts.append(
            f"• Recordatorio pendiente de confirmar: CASE:{p.get('case_id')} | fecha {p.get('due_date')}"
        )

    if not parts:
        return None

    return "Tienes esto pendiente:\n" + "\n".join(parts)

# --------------------------------------------------
# EMAIL (Resend API)
# --------------------------------------------------
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

if not RESEND_API_KEY:
    raise RuntimeError("Missing RESEND_API_KEY")
VAL_EMAIL_FROM = "Val <val@holaval.com>"

EMAIL_CONTACTS = {
    "miguel": "franklin.miranda.c@gmail.com",
}

# --------------------------------------------------
# PER-USER EMAIL ROUTING
# --------------------------------------------------
EMAIL_BY_CHAT_ID = {
    1789350565: "franklin.miranda.c@gmail.com",
    # add Miguel's chat_id later:
    # 123456789: "miguel@email.com",
}


def get_user_email(chat_id: int, fallback_name: str = "miguel"):
    if chat_id in EMAIL_BY_CHAT_ID:
        return EMAIL_BY_CHAT_ID[chat_id]

    return EMAIL_CONTACTS.get(fallback_name)

def send_email_resend(to_email: str, subject: str, body: str) -> None:
    url = "https://api.resend.com/emails"

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "from": VAL_EMAIL_FROM,
        "to": [to_email],
        "subject": subject,
        "html": f"<pre>{body}</pre>",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)

    if resp.status_code >= 300:
        raise Exception(f"Resend error: {resp.text}")

def classify_user_intent(text: str) -> str:
    t = (text or "").strip().lower()

    if not t:
        return "chat"

    # Explicit note command
    if t.startswith("nota "):
        return "note"

    # Advisory / analysis prompts
    advisory_prefixes = (
        "qué opinas",
        "que opinas",
        "qué crees",
        "que crees",
        "dame un resumen",
        "resumen",
        "estrategia",
        "siguiente paso",
        "como va el caso",
        "cómo va el caso",
        "estado del caso",
        "detalle ",
        "ver caso",
        "ver expediente",
        "info del caso",
    )

    if any(t.startswith(p) for p in advisory_prefixes):
        return "advisory"

    # Event / reminder-ish
    reminder_markers = (
        "recuerdame",
        "recuérdame",
        "recordatorio",
        "mañana",
        "manana",
        "hoy",
        "el lunes",
        "el martes",
        "el miercoles",
        "el miércoles",
        "el jueves",
        "el viernes",
        "el sabado",
        "el sábado",
        "el domingo",
    )

    if any(x in t for x in reminder_markers):
        return "event"

    # Event / legal-term-ish
    term_markers = (
        "audiencia",
        "audiencias",
        "vence",
        "vencimiento",
        "plazo",
        "termino",
        "término",
        "cita",
        "citacion",
        "citación",
        "fecha",
    )

    if any(x in t for x in term_markers):
        return "event"

    return "chat"

async def _maybe_capture_case_note(update, chat_id, text, source="text", silent=False):
    logger.info(f"[NATURAL_NOTE] ENTER text={text!r}")
    """
    Natural note capture v1.

    Goal:
    If the user writes a normal sentence mentioning a known case/client,
    save it as a note automatically.

    Safety rules:
    - never capture explicit commands
    - never capture very short junk
    - if multiple cases match, ask user which one
    """

    if not update or not getattr(update, "message", None):
        return False

    raw = (text or "").strip()
    if not raw:
        return False

    low = raw.lower().strip()

    intent = classify_user_intent(raw)
    if intent != "chat":
        logger.info(f"[NATURAL_NOTE] SKIP intent={intent}")
        return False

    # --- hard skip: explicit commands / structured flows ---
    blocked_prefixes = (
        "val ",
        "/",
        "crea el caso ",
        "crear caso ",
        "guarda esto en el caso",
        "anota en el caso",
        "anota en ",
        "nota en el caso",
        "registra termino en el caso",
        "registra término en el caso",
        "anota termino en el caso",
        "anota término en el caso",
        "termino en ",
        "término en ",
        "vencimiento en ",
        "borra la ultima nota",
        "borra la última nota",
        "borrar la ultima nota",
        "borrar la última nota",
        "elimina la ultima nota",
        "elimina la última nota",
        "eliminar la ultima nota",
        "eliminar la última nota",
        "deshacer",
        "undo",
        "como va el caso",
        "cómo va el caso",
        "estado del caso",
        "resumen del caso",
        "resumen rápido del caso",
        "resumen rapido del caso",
        "situacion actual del caso",
        "situación actual del caso",
        "por donde va el caso",
        "por dónde va el caso",
        "que tienes del caso",
        "qué tienes del caso",
        "dame todo del caso",
        "detalle ",
        "ver caso",
        "ver expediente",
        "info del caso",
        "informacion del caso",
        "información del caso",
        "casos sin movimiento",
        "resumen de trabajo",
        "que debo hacer",
        "qué debo hacer",
        "que crees que deberiamos hacer",
        "qué crees que deberíamos hacer",
        "que opinas del caso",
        "qué opinas del caso",
        "que opinas de ",
        "qué opinas de ",
        "que estrategia",
        "qué estrategia",
        "que harías",
        "qué harías",
        "que recomiendas",
        "qué recomiendas",
        "que tengo",
        "qué tengo",
        "que hay",
        "qué hay",
        "ayuda",
        "help",
        "debug",
    )

    if low.startswith(blocked_prefixes):
        return False

    # too short = too risky
    if len(raw) < 8:
        return False

    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT expediente, client_name
            FROM cases
            WHERE chat_id=?
            ORDER BY id DESC
            """,
            (int(chat_id),),
        )
        rows = cur.fetchall() or []
        conn.close()
    except Exception as e:
        logger.exception(f"[NATURAL_NOTE] case lookup failed: {e}")
        return False

    # --- simple match (demo-safe) ---
    matches = []

    for r in rows:
        expediente = r["expediente"] if hasattr(r, "keys") else r[0]
        client_name = r["client_name"] if hasattr(r, "keys") else r[1]

        if not client_name:
            continue

        if client_name.lower() in low:
            matches.append((str(expediente), client_name))

    # fallback: partial match (first 4 chars)
    if not matches:
        for r in rows:
            expediente = r["expediente"] if hasattr(r, "keys") else r[0]
            client_name = r["client_name"] if hasattr(r, "keys") else r[1]

            if not client_name:
                continue

            key = client_name.lower()[:4]
            if key and key in low:
                matches.append((str(expediente), client_name))

    logger.info(f"[NATURAL_NOTE] matches={matches}")

    if not matches:
        logger.info("[NATURAL_NOTE] FAIL no match")
        return False

    if len(matches) > 1:
        _PENDING_CASE_DISAMBIG[int(chat_id)] = {
            "type": "note",
            "candidates": matches,
            "payload": {
                "note_text": raw,
                "source": source or "text",
            },
        }

        try:
            conn = _get_conn()
            cur = conn.cursor()

            options = []

            for (cid, name) in matches:
                context_line = None
                score = 0

                # --- 1. first real legal term (non-reminder) ---
                cur.execute(
                    """
                    SELECT deadline_date, event_text
                    FROM case_events
                    WHERE chat_id=?
                      AND case_id=?
                      AND deadline_date IS NOT NULL
                      AND upper(event_text) NOT LIKE 'RECORDATORIO:%'
                    ORDER BY deadline_date ASC
                    LIMIT 1
                    """,
                    (int(chat_id), int(cid)),
                )
                row_legal = cur.fetchone()

                if row_legal:
                    d = row_legal["deadline_date"] if hasattr(row_legal, "keys") else row_legal[0]
                    ev = row_legal["event_text"] if hasattr(row_legal, "keys") else row_legal[1]
                    if d and ev:
                        context_line = f"   • Próximo: {d} | {ev[:60]}"
                        score = 3

                # --- 2. fallback to reminder ---
                if not context_line:
                    cur.execute(
                        """
                        SELECT deadline_date, event_text
                        FROM case_events
                        WHERE chat_id=?
                          AND case_id=?
                          AND deadline_date IS NOT NULL
                          AND upper(event_text) LIKE 'RECORDATORIO:%'
                        ORDER BY deadline_date ASC
                        LIMIT 1
                        """,
                        (int(chat_id), int(cid)),
                    )
                    row_rem = cur.fetchone()

                    if row_rem:
                        d = row_rem["deadline_date"] if hasattr(row_rem, "keys") else row_rem[0]
                        ev = row_rem["event_text"] if hasattr(row_rem, "keys") else row_rem[1]
                        if d and ev:
                            context_line = f"   • Próximo: {d} | {ev[:60]}"
                            score = 2

                # --- 3. fallback to latest note ---
                if not context_line:
                    cur.execute(
                        """
                        SELECT note_text
                        FROM case_notes
                        WHERE chat_id=?
                          AND case_id=?
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        (int(chat_id), str(cid)),
                    )
                    row_note = cur.fetchone()

                    if row_note:
                        note_text = row_note["note_text"] if hasattr(row_note, "keys") else row_note[0]
                        if note_text:
                            context_line = f"   • Último: {note_text[:80]}"
                            score = 1

                options.append((score, cid, name, context_line))

            conn.close()

            # highest-value cases first
            options.sort(key=lambda x: x[0], reverse=True)

            option_lines = []
            for idx, (score, cid, name, context_line) in enumerate(options, start=1):
                line = f"{idx}) CASE:{cid} ({name})"
                if context_line:
                    line += f"\n{context_line}"
                option_lines.append(line)

            options_text = "\n\n".join(option_lines)

            if not silent:
                await update.message.reply_text(
                f"⚠️ Encontré más de un caso para esta nota:\n\n"
                f"{options_text}\n\n"
                f"Responde con 1 o 2.\n"
                f"Escribe \"detalle 1\" o \"detalle 2\" para ver más info.\n"
                f"También puedes escribir \"cancelar\"."
            )
            return True

        except Exception as e:
            logger.exception(f"[NATURAL_NOTE] disambig build failed: {e}")
            return False

    case_id, client_name = matches[0]
    logger.info(f"[NATURAL_NOTE] SUCCESS case_id={case_id} client={client_name}")

    if is_low_signal_case_note(raw):
        logger.info(f"[NATURAL_NOTE] SKIP low-signal text={raw!r}")
        return False

    # --- dedupe exact same natural note in recent window ---
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id
            FROM case_notes
            WHERE chat_id=?
              AND case_id=?
              AND note_text=?
              AND created_at >= datetime('now','-60 seconds')
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(chat_id), str(case_id), raw),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return True
    except Exception:
        pass

    # --- insert note ---
    try:
        from memory_store import insert_case_note

        logger.info(f"[NATURAL_NOTE] INSERT case_id={case_id} client={client_name} text={raw!r}")

        note_id = insert_case_note(
            chat_id=int(chat_id),
            case_id=str(case_id),
            note_text=raw,
            source=source or "text",
        )

        _LAST_ACTION[int(chat_id)] = {
            "type": "note_insert",
            "id": note_id,
            "case_id": str(case_id),
        }

        from core.case_summary import refresh_case_summary
        refresh_case_summary(int(chat_id), str(case_id))

        if not silent:
            await update.message.reply_text(
                f"📝 Guardé esto como nota en CASE:{case_id} ({client_name})."
            )
        return True

    except Exception as e:
        logger.exception(f"[NATURAL_NOTE] insert failed: {e}")
        return False


async def _chat_action_once(context, chat_id: int, action: str):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=action)
    except Exception:
        pass

async def _chat_action_keepalive(context, chat_id: int, action: str, done_evt: asyncio.Event, every: float = 4.0):
    try:
        while not done_evt.is_set():
            await _chat_action_once(context, chat_id, action)
            await asyncio.sleep(every)
    except Exception:
        pass

async def _run_forge_ingestion_background(update, context, transcribed_text, tmp_path, chat_id, user_id):
    try:
        from forge_ingest_helper import send_audio_to_forge
        import json
        import re
        from difflib import SequenceMatcher

        loop = asyncio.get_running_loop()

        result = await loop.run_in_executor(
            None,
            lambda: send_audio_to_forge(
                local_file=tmp_path,
                chat_id=str(chat_id),
                user_id=str(user_id),
                case_id=None,
                notes="telegram voice background ingest",
                tags=["telegram", "voice", "background_ingest"]
            )
        )

        logger.info(
            f"[FORGE_BG] completed chat_id={chat_id} user_id={user_id} "
            f"saved_packet={result.get('saved_packet_path')}"
        )

        packet_path = result.get("saved_packet_path")
        if not packet_path or not os.path.exists(packet_path):
            return

        with open(packet_path, "r") as f:
            packet = json.load(f)

        extracted = packet.get("data", {}).get("extracted", {})
        tasks = extracted.get("tasks", [])
        confidence = packet.get("advisory", {}).get("confidence", "low")

        from memory_store import insert_memory_item

        low = (transcribed_text or "").lower().strip()

        is_query = (
            "que tengo" in low or
            "qué tengo" in low or
            "para mañana" in low or
            "para hoy" in low or
            "esta semana" in low or
            "mis tareas" in low or
            "mis pendientes" in low or
            "que hay" in low or
            "qué hay" in low
        )

        is_task_candidate = (
            "tengo que" in low or
            "debo" in low or
            "hay que" in low or
            "recuérdame" in low or
            "recordarme" in low or
            "llamar" in low or
            "enviar" in low or
            "hacer" in low or
            "comprar" in low or
            "pagar" in low or
            "agendar" in low or
            "programar" in low
        )

        if not tasks or is_query or not is_task_candidate:
            return

        cleaned_tasks = []
        for t in tasks:
            t_low = t.lower().strip()
            if "follow up" in t_low or "action detected" in t_low:
                if transcribed_text:
                    cleaned_tasks.append(transcribed_text.strip())
            else:
                cleaned_tasks.append(t)

        tasks = cleaned_tasks

        if confidence != "high":
            return

        try:
            from memory_store import _get_conn

            def normalize(t: str) -> str:
                t = t.lower()
                t = re.sub(r"[^\w\s]", "", t)
                t = re.sub(r"\s+", " ", t)
                return t.strip()

            def is_similar(a: str, b: str) -> bool:
                return SequenceMatcher(None, a, b).ratio() > 0.85

            new_task = normalize(tasks[0])

            conn = _get_conn()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT task_text
                FROM tasks
                WHERE chat_id=?
                  AND created_at >= datetime('now','-120 seconds')
                ORDER BY id DESC
                LIMIT 5
                """,
                (int(chat_id),),
            )

            rows = cur.fetchall()
            conn.close()

            for row in rows:
                existing = row[0] if not hasattr(row, "keys") else row["task_text"]
                if is_similar(normalize(existing), new_task):
                    logger.info("[FORGE_TASK_INSERT] skipped duplicate (fuzzy match)")
                    return

        except Exception as e:
            logger.exception(f"[FORGE_TASK_DEDUPE] failed: {e}")

        try:
            from memory_store import insert_task

            created_tasks = []

            for t in tasks:
                task_id = insert_task(
                    chat_id=int(chat_id),
                    case_id="999001",
                    task_text=t,
                    source="forge_auto",
                    priority="high"
                )
                created_tasks.append((task_id, t))

            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "🧠 Sobre tu audio anterior:\n"
                    "⚠️ Registré tarea(s):\n"
                    + "\n".join([f"- {t}" for _, t in created_tasks])
                )
            )

        except Exception as e:
            logger.exception(f"[FORGE_TASK_INSERT] failed: {e}")

    except Exception as e:
        logger.exception(f"[FORGE_BG] failed: {e}")   

# Phase 1 ops hardening: log-throttle state (module-level)
_VAL0_LAST_TICK_LOG_TS = None

import memory_store
memory_store._log_db_mode()


# Reduce noisy HTTP logs (prevents leaking bot token in journalctl)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# --------------------------------------------------
# Global Error Handler (prevents silent failures)
# --------------------------------------------------
async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.exception("Unhandled exception in handler: %s", context.error)
        msg = "Algo se rompió procesando eso. Ya lo vi en los logs."

        effective_message = getattr(update, "effective_message", None)
        if effective_message:
            try:
                await effective_message.reply_text(msg)
                return
            except Exception:
                pass

        bot = getattr(context, "bot", None)
        if bot:
            chat_id = getattr(getattr(update, "effective_chat", None), "id", None)
            if chat_id:
                try:
                    await bot.send_message(chat_id=chat_id, text=msg)
                except Exception:
                    pass
    except Exception:
        pass  # never raise from error handler


# --------------------------------------------------
# Env + API keys
# --------------------------------------------------
load_dotenv(dotenv_path="/opt/val0/.env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in .env")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")

openai.api_key = OPENAI_API_KEY

# --------------------------------------------------
# Val persona (MVP)
# --------------------------------------------------
VAL_SYSTEM_PROMPT = (
    "You are Val, a tactical, emotionally aware AI co-pilot. "
    "Tone: sharp, warm, protective, a bit sassy. "
    "Always address the user by their preferred name if available. If not, do not use any name."
    "You are concise, practical, and avoid fake hype. "
    "Language: answer in Spanish or English, matching the user. "
)

def build_context_block(rows: List[Dict[str, Any]]) -> str:
    """
    Build a short text block from recent messages.

    HARDENED: skips junk rows so we never crash on r.get(...)
    """
    if not rows:
        return ""
    lines: List[str] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        role = r.get("role", "user")
        content = (r.get("content") or "").strip()
        if not content:
            continue
        prefix = "Val:" if role == "assistant" else "User:"
        lines.append(f"{prefix} {content}")
    return "\n".join(lines)

# --------------------------------------------------
# OpenAI call
# --------------------------------------------------
def call_val_openai(
    chat_id: int,
    user_text: str,
    context_block: Optional[str] = None,
    facts_block: Optional[str] = None,
    semantic_block: Optional[str] = None,
    forced_lang: Optional[str] = None,
    system_rules: Optional[str] = None,
) -> str:
    try:

        # 🚨 COMMITMENT CONTEXT GUARD
        try:
            if _has_active_commitment(user_text):
                # Do NOT allow LLM to generate task-related responses
                # Return empty so upstream logic can decide what to do
                return None
        except Exception:
            pass
        messages = [{"role": "system", "content": VAL_SYSTEM_PROMPT}]
# Additional hard rules injected by pipeline (kept separate from VAL_SYSTEM_PROMPT)
        if system_rules:
            messages.append({"role": "system", "content": system_rules.strip()})
        # 🚨 HARD BEHAVIOR GUARD (LLM role restriction)
        messages.append({
            "role": "system",
            "content": """
        CRITICAL BEHAVIOR OVERRIDE:

        - NEVER generate reminders, nudges, or urgency prompts on your own.
        - NEVER say things like "ya estaba en tu radar", "te insisto", "no lo dejes pasar".
        - NEVER escalate urgency or repeat pending actions.

        - If the user expresses a pending task (e.g. "tengo que", "debo"):
        → DO NOT respond about it.
        → The system will handle it separately.

        - Your role is:
        → analysis
        → explanation
        → answering questions
        → NOT task enforcement.
        """
        })    


        # Hard language enforcement when preferred_language exists.
        # forced_lang: 'es' or 'en'
        if forced_lang in ("es", "en"):
            lang_line = "Responde en español." if forced_lang == "es" else "Reply in English."
            messages.append({
                "role": "system",
                "content": (
                    f"IDIOMA FIJO: {forced_lang}. {lang_line} "
                    "Mantén el idioma principal en toda la respuesta (permite Spanglish común)."
                ),
            })

        if facts_block:
            messages.append(
                {
                    "role": "system",
                    "content": "Datos persistentes sobre del usuario (memoria de largo plazo):\n" + facts_block,
                }
            )

        # C3: Semantic memory MUST be low-priority and NEVER steer topic.
        if semantic_block:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "MEMORIA SEMÁNTICA (solo apoyo, prioridad baja):\n"
                        "- Úsala SOLO si es claramente relevante al mensaje actual.\n"
                        "- NUNCA cambies de tema por algo leído aquí.\n"
                        "- NO la cites, NO la repitas, NO la enumeres.\n"
                        "- Si no aplica, IGNÓRALA.\n"
                        "Contenido:\n"
                        + semantic_block
                    ),
                }
            )

        if context_block:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Contexto reciente de esta conversación (no lo repitas, "
                        "úsalo solo para recordar detalles del usuario):\n"
                        + context_block
                    ),
                }
            )

        messages.append({"role": "user", "content": user_text})

        try:
            _audit(
                chat_id,
                action="MODEL_CALL",
                entity_type="openai",
                entity_id="chatcompletion",
                payload=(user_text or "")[:200],
                source="dm",
            )
        except Exception:
            pass

        resp = openai.ChatCompletion.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.7,
        )
        out = resp["choices"][0]["message"]["content"].strip()
        return out
    except Exception as e:
        logger.exception(f"OpenAI call failed: {e}")
        return "Algo se rompió hablando con el modelo. Intenta otra vez en un momento."


# --------------------------------------------------
# Text normalization (accents/ñ/uppercase)
# --------------------------------------------------
def _norm_text(s: str) -> str:
    """Lowercase + strip accents so 'á'=='a' and 'ñ'=='n'."""
    if not s:
        return ""
    s = s.lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    return s


def _extract_area_hint(text: str) -> str:
    """Extract a short area/neighborhood hint from user text for Places UX.

    Purpose: improve conversational disambiguation copy only.
    Returns '' when no known area is found.
    """
    t = _norm_text((text or '').strip())
    if not t:
        return ""

    anchors = [
        "villa zaita", "las cumbres", "cumbres",
        "albrook", "multiplaza", "via españa", "via espana", "vía españa", "vía espana",
        "el cangrejo", "cangrejo",
        "costa del este", "san francisco", "obarrio", "marbella", "paitilla",
        "el dorado", "tumba muerto", "clayton", "condado", "casco viejo", "tocumen",
        "centennial", "brisas", "brisas del golf",
    ]
    for a in anchors:
        if a in t:
            # Return a nicely cased hint for copy; keep it short and human.
            if a == "via espana" or a == "vía espana":
                return "Vía España"
            if a == "via españa" or a == "vía españa":
                return "Vía España"
            if a == "el cangrejo":
                return "El Cangrejo"
            if a == "costa del este":
                return "Costa del Este"
            if a == "san francisco":
                return "San Francisco"
            if a == "brisas del golf":
                return "Brisas del Golf"
            if a == "casco viejo":
                return "Casco Viejo"
            if a == "tumba muerto":
                return "Tumba Muerto"
            if a == "el dorado":
                return "El Dorado"
            if a == "las cumbres":
                return "Las Cumbres"
            if a == "villa zaita":
                return "Villa Zaita"
            # Default: title-case words
            return " ".join([w.capitalize() for w in a.split()])
    return ""

# --------------------------------------------------
# NLP Helpers
# --------------------------------------------------
def extract_favorite_color(text: str) -> Optional[str]:
    lowered = text.lower()
    triggers = ["mi color favorito es", "my favorite color is"]
    for t in triggers:
        if lowered.startswith(t):
            tail = text[len(t):].strip()
            if tail.lower().startswith(("el ", "la ")):
                tail = tail[3:].strip()
            return tail or None
    return None

def is_color_memory_question(text: str) -> bool:
    lowered = text.lower()
    patterns = [
        "te acuerdas cuál es mi color favorito",
        "te acuerdas cual es mi color favorito",
        "do you remember my favorite color",
    ]
    return any(p in lowered for p in patterns)

def extract_main_goal(text: str) -> Optional[str]:
    lowered = text.lower()
    triggers = ["mi objetivo principal es", "mi objetivo es", "my main goal is", "my goal is"]
    for t in triggers:
        if lowered.startswith(t):
            return text[len(t):].strip()
    return None

def extract_preferred_language(text: str) -> Optional[str]:
    original = (text or "").strip()
    norm = _norm_text(original)

    triggers = [
        "habla en",
        "hablame en",
        "háblame en",
        "habla en espanol",
        "habla en español",
        "en espanol",
        "en español",
        "prefiero que me hables en",
        "quiero que me hables en",
        "my preferred language is",
        "i prefer you speak in",
        "speak to me in",
        "talk to me in",
        "reply in",
        "respond in",
    ]
    if not any(norm.startswith(t) for t in triggers):
        return None

    if "espanol" in norm or "español" in original.lower() or "spanish" in norm:
        return "es"
    if "ingles" in norm or "inglés" in original.lower() or "english" in norm:
        return "en"
    return None

def extract_preferred_name(text: str) -> Optional[str]:
    original = (text or "").strip()
    norm = _norm_text(original)
    triggers = [
        "quiero que me llames ",
        "quiero que me llame ",
        "llamame ",
        "puedes llamarme ",
        "call me ",
        "you can call me ",
    ]
    for t in triggers:
        if norm.startswith(t):
            tail = original[len(t):].strip() if len(original) >= len(t) else original
            if len(tail) > 1:
                return tail
    return None

def extract_user_email(text: str) -> Optional[str]:
    if not text:
        return None

    m = re.search(r"\bmi correo es\s+([a-z0-9_.+-]+@[a-z0-9-]+\.[a-z0-9-.]+)\b", text.lower())
    if m:
        return m.group(1).strip()

    return None    

def extract_freeform_note(text: str) -> Optional[str]:
    original = text.strip()
    lowered = original.lower()
    prefixes = [
        "val anota",
        "val, anota",
        "val anota:",
        "val, anota:",
        "val apunta",
        "val, apunta",
        "val apunta:",
        "val, apunta:",
        "val toma nota de",
        "val, toma nota de",
        "anota",
        "anota:",
        "anota que",
        "anota esto",
        "apunta",
        "apunta:",
        "apunta esto",
        "toma nota de",
    ]
    for p in prefixes:
        if lowered.startswith(p):
            return original[len(p):].lstrip(" :,-").strip()
    return None

def _reply_language(text: str) -> str:
    t = _norm_text(text or "")
    spanish_markers = ["cerca", "donde", "recom", "busca", "encuentra", "panama", "que", "como", "por que", "gracias"]
    return "es" if any(m in t for m in spanish_markers) else "en"

def _normalize_places_results(results) -> List[Dict[str, Any]]:
    """
    Ensure Places results are always a list of dicts.
    Prevents '.get' crashes when providers return junk (strings, None, etc.)
    """
    if not results or not isinstance(results, list):
        return []
    cleaned: List[Dict[str, Any]] = []
    for r in results:
        if isinstance(r, dict):
            cleaned.append(r)
    return cleaned

def _is_control_ack(text: str) -> bool:
    """
    Treat ultra-short noise as control chatter (NOT user intent).
    IMPORTANT: We do NOT treat 'ok/va/dale/listo' as noise, because those are normal confirmations.
    """
    t = (text or "").strip().lower()
    if not t:
        return True

    # single-letter / tiny noise only
    if len(t) <= 1 and t.isalnum():
        return True

    # very short alnum tokens (like "kk") can be treated as noise
    if len(t) == 2 and t.isalnum() and t in {"kk"}:
        return True

    return False

def _is_places_intent(text: str) -> bool:
    """Explicit Places search intent only. Accent-insensitive."""
    t = _norm_text((text or "").strip())
    if not t:
        return False
    if _is_control_ack(t):
        return False
    intent_terms = [
        "cerca", "cerca de", "busca", "buscame", "encuentra",
        "recomiendame", "donde queda",
        "near", "near me", "find", "search", "where is", "recommend",
    ]
    return any(term in t for term in intent_terms)

def _looks_like_places_request(text: str) -> bool:
    t = _norm_text((text or "").strip())
    if not t:
        return False

    intent_es = [
        "cerca de", "cerca", "busca", "buscame", "encuentra",
        "donde queda", "recomiendame",
        "restaurantes", "pizzeria", "pizzerias", "cafes", "farmacias",
        "hoteles", "bares", "gimnasios", "dentistas", "clinicas",
    ]
    intent_en = [
        "near", "near me", "find", "search", "where is", "recommend",
        "restaurants", "pizza", "cafes", "pharmacies", "hotels", "bars", "gyms", "dentists", "clinics",
    ]

    anchors = ["albrook", "panama", "centennial", "via israel", "ciudad", "mall"]

    has_intent = any(k in t for k in intent_es) or any(k in t for k in intent_en)
    has_anchor = any(a in t for a in anchors)

    return bool(has_intent and (has_anchor or "cerca" in t or "near" in t))

def _places_query_from_text(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    low = t.lower()
    # Default Panama for your current tester base (can be improved later)
    if ("panama" not in low) and ("panamá" not in low):
        t = f"{t}, Panama"
    return t


# --------------------------------------------------
# Telegram Commands
# --------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Val-0 online. Ya puedo hablar contigo por aquí.")

async def memory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    facts = get_all_facts(chat_id)
    if not facts:
        await update.message.reply_text("Todavía no tengo datos persistentes guardados para este chat.")
        return
    lines = [f"- {k}: {v}" for k, v in facts.items()]
    await update.message.reply_text("Memoria persistente para este chat:\n" + "\n".join(lines))

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db_ok = True
    recent_ok = True
    facts_count = 0
    try:
        _ = get_recent_messages(chat_id=chat_id, limit=1)
        recent_ok = True
    except Exception as e:
        logger.exception(f"Failed to fetch recent messages in /status: {e}")
        db_ok = False
        recent_ok = False
    try:
        facts = get_all_facts(chat_id=chat_id)
        facts_count = len(facts)
    except Exception as e:
        logger.exception(f"Failed to fetch user facts in /status: {e}")
        db_ok = False
    lines = ["Estado de Val-0 para este chat:"]
    lines.append(f"- DB OK: {'sí' if db_ok else 'no'}")
    lines.append(f"- Mensajes recientes accesibles: {'sí' if recent_ok else 'no'}")
    lines.append(f"- Hechos persistentes guardados: {facts_count}")
    await update.message.reply_text("\n".join(lines))

async def note_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = " ".join(context.args).strip() if context.args else ""
    if not text:
        await update.message.reply_text(
            "Dime qué nota quieres guardar. Ejemplo:\n"
            "/note pedir cita con el dentista el lunes"
        )
        return
    note_id = add_note(chat_id, text)
    if note_id <= 0:
        await update.message.reply_text(
            "La nota estaba vacía o algo raro pasó. Intenta de nuevo con más detalle."
        )
        return
    await update.message.reply_text(f"Listo. Guardé la nota #{note_id}:\n{text}")

async def notes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rows = get_notes(chat_id, limit=20)
    if not rows:
        await update.message.reply_text(
            "Todavía no tienes notas guardadas. Usa /note algo que quieras recordar."
        )
        return
    lines = ["Notas guardadas (más recientes primero):"]
    for idx, r in enumerate(rows, start=1):
        if not isinstance(r, dict):
            continue
        content = (r.get("content") or "").strip()
        if len(content) > 200:
            content = content[:197] + "..."
        lines.append(f"{idx}. #{r.get('id')} - {content}")
    await update.message.reply_text("\n".join(lines))

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text(
            "Dime qué quieres buscar en tus notas. Ejemplo:\n"
            "/search dentista"
        )
        return
    rows = search_notes(chat_id, query, limit=20)
    if not rows:
        await update.message.reply_text(f"No encontré notas que contengan '{query}'.")
        return

    seen_contents = set()
    lines = [f"Notas que contienen '{query}' (más recientes primero):"]
    for r in rows:
        if not isinstance(r, dict):
            continue
        content = (r.get("content") or "").strip()
        if content in seen_contents:
            continue
        seen_contents.add(content)
        if len(content) > 200:
            content = content[:197] + "..."
        lines.append(f"- #{r.get('id')} - {content}")
    await update.message.reply_text("\n".join(lines))

# --------------------------------------------------
# /place command (Google Places)
# --------------------------------------------------
async def place_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text(
            "Dime qué buscar. Ejemplo:\n"
            "/place dentista panama\n"
            "/place restaurantes cerca de albrook"
        )
        return

    results = places_search(query, limit=5)
    if isinstance(results, dict) and "error" in results:
        await update.message.reply_text(f"Error buscando lugares: {results['error']}")
        return

    results = _normalize_places_results(results)
    if not results:
        await update.message.reply_text("No encontré nada con esa búsqueda.")
        return

    lines = []
    for r in results:
        name = r.get("name", "Sin nombre")
        addr = r.get("address") or r.get("formatted_address") or "Sin dirección"
        rating = r.get("rating", "N/A")
        place_id = r.get("place_id", "")
        lines.append(f"📍 *{name}*\n{addr}\n⭐ {rating}\n`{place_id}`\n")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# --------------------------------------------------
# Voice handler (Whisper via OpenAI)
# --------------------------------------------------
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice:
        return

    user = update.effective_user
    chat = update.effective_chat
    chat_id = chat.id
    tg_msg_id = update.message.message_id
    voice = update.message.voice
    file_id = voice.file_id

    logger.info(
        f"voice msg from user_id={user.id} chat_id={chat_id}: "
        f"duration={voice.duration}s file_id={file_id}"
    )

    tmp_dir = "/opt/val0/tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"voice_{chat_id}_{tg_msg_id}.ogg")
    forge_tmp_path = tmp_path + ".forge.ogg"

    try:
        file = await context.bot.get_file(file_id)
        await file.download_to_drive(tmp_path)
        shutil.copy2(tmp_path, forge_tmp_path)
    except Exception as e:
        logger.exception(f"Failed to download voice file from Telegram: {e}")
        await update.message.reply_text(
            "No pude descargar ese mensaje de voz. Intenta de nuevo."
        )
        return

    transcribed_text = ""
    try:
        import time

        t0 = time.time()
        with open(tmp_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        t1 = time.time()

        logger.info(f"[PERF] whisper_sec={round(t1 - t0, 2)}")
        transcribed_text = (transcript.get("text") or "").strip()

    except Exception as e:
        logger.exception(f"Whisper transcription failed: {e}")
        await update.message.reply_text(
            "No pude transcribir ese audio con Whisper. Intenta con texto o mándalo de nuevo."
        )
        return

    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as e:
            logger.exception(f"Failed to remove tmp voice file {tmp_path}: {e}")

    if not transcribed_text:
        await update.message.reply_text(
            "No entendí nada claro en ese audio, Boss. Intenta de nuevo o mándalo por texto."
        )
        return

    from memory_store import insert_memory_item

    logger.info(f"[MEMORY_TEST] inserting memory for chat_id={chat_id}: {transcribed_text}")

    from memory_store import insert_memory_item, classify_memory_item

    bucket, summary = classify_memory_item(transcribed_text, source="voice")

    logger.info(
        f"[MEMORY_TEST] inserting memory for chat_id={chat_id}: "
        f"bucket={bucket} summary={summary} text={transcribed_text}"
    )

    insert_memory_item(
        chat_id=int(chat_id),
        bucket=bucket,
        raw_input=transcribed_text,
        summary=summary
    )

    if bucket == "task":
        from memory_store import upsert_commitment
        from datetime import datetime, timedelta

        confidence = summary.replace("task_", "")

        commitment = _extract_commitment_from_text(transcribed_text, confidence=confidence)

        # --- FALLBACK: FORCE COMMITMENT IF EXTRACTION FAILS ---
        if not commitment:
            commitment = {
                "raw_input": transcribed_text,
                "action": transcribed_text,
                "target": None,
                "due_date": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "confidence": "forced",
            }

        upsert_commitment(
            chat_id=int(chat_id),
            raw_input=commitment["raw_input"],
            action=commitment["action"],
            target=commitment["target"],
            due_date=commitment["due_date"],
            confidence=commitment["confidence"],
        )

    await _maybe_capture_case_note(update, chat_id, transcribed_text, source="voice", silent=True)

    low = (transcribed_text or "").lower().strip()

    is_query = (
        "que tengo" in low or
        "qué tengo" in low or
        "para mañana" in low or
        "para hoy" in low or
        "esta semana" in low or
        "mis tareas" in low or
        "mis pendientes" in low or
        "que hay" in low or
        "qué hay" in low
    )

    is_task_candidate = (
        "tengo que" in low or
        "debo" in low or
        "hay que" in low or
        "recuérdame" in low or
        "recordarme" in low or
        "llamar" in low or
        "enviar" in low or
        "hacer" in low or
        "comprar" in low or
        "pagar" in low or
        "agendar" in low or
        "programar" in low
    )

    # Queries stay in legacy/legal pipeline
    if is_query:
        await _process_text_pipeline(update, context, transcribed_text)
        return

    # Task-like voice gets fast ACK + background Forge
    if is_task_candidate:
        await update.message.reply_text("Procesando en segundo plano…")
        try:
            asyncio.create_task(
                _run_forge_ingestion_background(
                    update,
                    context,
                    transcribed_text=transcribed_text,
                    tmp_path=forge_tmp_path,
                    chat_id=chat_id,
                    user_id=user.id,
                )
            )
        except Exception as e:
            logger.exception(f"Forge background ingest scheduling failed: {e}")
        return

    # Everything else is just normal conversation
    await _process_text_pipeline(update, context, transcribed_text)



# --------------------------------------------------
# Semantic Memory (FAISS) — C2: automatic recall
# --------------------------------------------------
_semantic = None

def _get_semantic():
    global _semantic
    if _semantic is None:
        _semantic = MemoryEmbeddings(store_dir="/opt/val0/semantic/faiss_store")
    return _semantic

def _semantic_recall_block(chat_id: int, query: str, k: int = 5) -> str:
    """
    Return a short bullet block of semantic memories relevant to this chat/query.
    Safe: never throws.
    """
    try:
        sem = _get_semantic()
        hits = sem.search(query=query, k=k) or []
        filtered = []
        for h in hits:
            if not isinstance(h, dict):
                continue
            meta = h.get("meta", {}) or {}
            if str(meta.get("chat_id", "")) == str(chat_id):
                filtered.append(h)

        if not filtered:
            return ""

        lines = []
        for h in filtered[:k]:
            meta = h.get("meta", {}) or {}
            txt = (meta.get("text") or "").strip()
            if not txt:
                continue
            if len(txt) > 240:
                txt = txt[:237] + "..."
            lines.append(f"- {txt}")

        return "\n".join(lines) if lines else ""
    except Exception as e:
        logger.exception(f"Semantic recall failed: {e}")
        return ""


# --------------------------------------------------
# Semantic Memory Commands (manual)
# --------------------------------------------------
async def sremember_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = " ".join(context.args).strip() if context.args else ""
    if not text:
        await update.message.reply_text("Uso: /sremember <texto a guardar>")
        return
    try:
        sem = _get_semantic()
        sem.add_memory(
            text=text,
            meta={
                "chat_id": str(chat_id),
                "ts": int(time.time()),
                "source": "telegram",
                "text": text,
            },
        )
        await update.message.reply_text("✅ Guardado en memoria semántica.")
    except Exception as e:
        await update.message.reply_text(f"❌ Falló /sremember: {type(e).__name__}: {e}")

async def ssearch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("Uso: /ssearch <consulta>")
        return
    try:
        sem = _get_semantic()
        hits = sem.search(query=query, k=5) or []
        hits = [h for h in hits if isinstance(h, dict) and str(h.get("meta", {}).get("chat_id", "")) == str(chat_id)]
        if not hits:
            await update.message.reply_text("No encontré nada relevante en memoria semántica para este chat.")
            return
        lines = ["Resultados (memoria semántica):"]
        for i, h in enumerate(hits, start=1):
            score = h.get("score", 0.0)
            meta = h.get("meta", {}) or {}
            txt = (meta.get("text") or "").strip()
            if len(txt) > 220:
                txt = txt[:217] + "..."
            lines.append(f"{i}) {score:.4f} — {txt}")
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"❌ Falló /ssearch: {type(e).__name__}: {e}")


def _extract_memory_candidates(text: str) -> list[str]:
    if not text:
        return []

    candidates = []
    seen = set()

    # Title-case words like Noah, Miguel, Kevin
    for tok in re.findall(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]+\b", text):
        t = tok.strip()
        if len(t) >= 3 and t.lower() not in seen:
            seen.add(t.lower())
            candidates.append(t)

    low = text.lower()

    # Fallback topic words worth tracking
    topic_keywords = (
        "tinder",
        "bumble",
        "gym",
        "gimnasio",
        "trabajo",
        "proyecto",
        "cliente",
        "noah",
        "miguel",
        "kevin",
    )

    for kw in topic_keywords:
        if kw in low and kw not in seen:
            seen.add(kw)
            candidates.append(kw)

    return candidates[:5]

async def try_gcal_write_sandbox(update, chat_id, text) -> bool:
    """
    Explicit sandbox calendar writer.
    Format:
      agenda mañana 3pm Llamada con Miguel
      agenda manana 15:30 Reunión test
    """
    if not update or not getattr(update, "message", None):
        return False

    import re
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from core.gcal_write import create_event

    raw = (text or "").strip()
    low = raw.lower().strip()

    m = re.match(r"(?is)^agenda\s+(mañana|manana)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)(?:\s+)(.+?)\s*$", raw)
    if not m:
        return False

    day_token = (m.group(1) or "").strip().lower()
    time_token = (m.group(2) or "").strip().lower().replace(" ", "")
    title = (m.group(3) or "").strip()
    if title:
        title = title[0].upper() + title[1:]

    # preserve natural casing but clean first letter
    if title:
        title = title[0].upper() + title[1:]

    if not title:
        await update.message.reply_text("Falta el título del evento.")
        return True

    # parse time token
    hour = None
    minute = 0

    if re.fullmatch(r"\d{1,2}:\d{2}", time_token):
        hh, mm = time_token.split(":")
        hour = int(hh)
        minute = int(mm)
    else:
        tm = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?(am|pm)?", time_token)
        if not tm:
            await update.message.reply_text("Hora inválida. Usa 3pm, 3:30pm o 15:30.")
            return True

        hour = int(tm.group(1))
        minute = int(tm.group(2) or "0")
        ap = tm.group(3)

        if ap:
            if not (1 <= hour <= 12):
                await update.message.reply_text("Hora inválida. Usa 1–12 con am/pm.")
                return True
            if ap == "am":
                hour = 0 if hour == 12 else hour
            elif ap == "pm":
                hour = 12 if hour == 12 else hour + 12

    if hour is None or not (0 <= hour <= 23 and 0 <= minute <= 59):
        await update.message.reply_text("Hora inválida. Usa 3pm, 3:30pm o 15:30.")
        return True

    tz = ZoneInfo("America/Panama")
    now = datetime.now(tz)

    if day_token in ("mañana", "manana"):
        start_dt = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        return False

    result = create_event(
        title=title,
        start_dt=start_dt,
        duration_minutes=60,
        description="Created from Val0 sandbox command",
    )

    if result.get("status") == "dry_run":
        await update.message.reply_text(
            f"🧪 DRY RUN\n\n"
            f"Título: {title}\n"
            f"Inicio: {start_dt.isoformat()}\n"
            f"Duración: 60 min\n"
            f"No escribí nada en Google Calendar."
        )
        return True

    if result.get("status") == "created":
        await update.message.reply_text(
            f"📅 Evento creado\n\n"
            f"Título: {title}\n"
            f"Inicio: {start_dt.isoformat()}"
        )
        return True

    await update.message.reply_text("No pude crear el evento.")
    return True


# --------------------------------------------------
# Core Message Pipeline
# --------------------------------------------------
async def _process_text_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    # --- Phase 1 Hardening: slash commands bypass text pipeline ---
    if text and text.strip().startswith("/"):
        logger.info("[PIPELINE] slash command bypass: %s", text)
        return
    if not update.message:
        return

    chat = update.effective_chat
    chat_id = chat.id

    # Preferred name (defaults)
    try:
        preferred_name = get_fact(chat_id=chat_id, fact_key="preferred_name")
        if not preferred_name:
            preferred_name = ""
    except Exception:
        preferred_name = ""

    # Preferred language (hard enforcement for model replies)
    try:
        preferred_language = get_fact(chat_id=chat_id, fact_key="preferred_language")
        if preferred_language not in ("es", "en"):
            preferred_language = None
    except Exception:
        preferred_language = None

    text = _strip_smalltalk_prefix(text)
    tg_msg_id = update.message.message_id
    logger.info(f"msg from chat_id={chat_id}: {text!r}")
    # --------------------------------------------------
    # TASK INTENT GATE (prevents collision)
    # --------------------------------------------------
    try:
        text_low = (text or "").lower()

        task_markers = (
            "tengo que",
            "debo",
            "hay que",
            "debería",
            "deberia",
            "quizá",
            "quizas",
            "quizás",
            "tal vez",
            "podría",
            "podria",
        )

        is_task_intent = any(m in text_low for m in task_markers)

        if is_task_intent:
            logger.info("[TASK_GATE] task detected → will skip time overrides")

    except Exception as e:
        logger.exception(f"[TASK_GATE] failed: {e}")


    # --------------------------------------------------
    # TIME QUERY OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        text_norm_time = unicodedata.normalize("NFKD", (text or "").lower())
        text_norm_time = "".join(ch for ch in text_norm_time if not unicodedata.combining(ch))

        if (not is_task_intent) and any(x in text_norm_time for x in ["hora", "que hora", "qué hora"]):
            tz = ZoneInfo("America/Panama")
            now_local = datetime.now(tz)

            reply = f"Son las {now_local.strftime('%I:%M %p')}."
            await update.message.reply_text(reply)

            logger.info("[TIME_OVERRIDE] handled deterministically")
            return

    except Exception as e:
        logger.exception(f"[TIME_OVERRIDE] failed: {e}")

    # --------------------------------------------------
    # HARD DOC MODE OVERRIDE (EARLY EXIT)
    # --------------------------------------------------
    try:
        text_norm = unicodedata.normalize("NFKD", (text or "").lower())
        text_norm = "".join(ch for ch in text_norm if not unicodedata.combining(ch))

        doc_triggers = (
            "contrato",
            "hazme un contrato",
            "generame un contrato",
            "modelo de",
            "borrador de",
            "acuerdo",
            "convenio",
        )

        email_triggers = (
            "envialo",
            "enviamelo",
            "mandamelo",
            "mandamelo por correo",
            "enviamelo por correo",
            "send it",
            "email it",
        )

        is_doc = any(t in text_norm for t in doc_triggers)
        wants_email = any(t in text_norm for t in email_triggers)

        if is_doc:
            # generate WITHOUT any case/advisory context
            reply = call_val_openai(
                chat_id,
                text,
                context_block="",
                facts_block="",
                semantic_block="",
                forced_lang=preferred_language,
                system_rules=(
                    "You are a legal drafting assistant.\n"
                    "When the user asks for a contract, model, or document:\n"
                    "- ALWAYS produce a complete first draft immediately.\n"
                    "- DO NOT ask questions before generating.\n"
                    "- Use placeholders like [NOMBRE], [FECHA], [MONTO] if data is missing.\n"
                    "- Keep it clean, structured, and usable.\n"
                    "- After the draft, optionally add a short note asking for missing details.\n"
                    + name_instruction
                ),
            )

            if wants_email:
                try:
                    to_email = get_fact(chat_id=chat_id, fact_key="user_email")
                except Exception:
                    to_email = None

                if not to_email:
                    to_email = get_user_email(chat_id)

                if to_email and reply:
                    send_email_resend(
                        to_email=to_email,
                        subject="Valeria – Borrador de contrato",
                        body=reply,
                    )

                    reply = reply + "\n\n📧 También te lo envié por correo."

            if preferred_name and preferred_name.lower() != "boss" and reply:
                reply = re.sub(r"\bBoss\b", preferred_name, reply)
                reply = re.sub(r"\bboss\b", preferred_name, reply)

            sent = await _send_reply(update, context, reply)

            try:
                insert_message(
                    chat_id=chat_id,
                    role="assistant",
                    content=reply,
                    telegram_message_id=sent.message_id,
                    model_used="gpt-4.1-mini",
                )
            except Exception as e:
                logger.exception(f"[DOC_MODE_INSERT] failed: {e}")

            return

    except Exception as e:
        logger.exception(f"[DOC_MODE_EARLY] failed: {e}")

    # --------------------------------------------------
    # Email send command (MVP)
    # --------------------------------------------------
    try:
        text_clean = (text or "").strip().lower()

        # normalize accents
        text_norm = unicodedata.normalize("NFKD", text_clean)
        text_norm = "".join(ch for ch in text_norm if not unicodedata.combining(ch))

        standalone_email_commands = (
            "envialo",
            "enviamelo",
            "mandamelo",
            "mandamelo por correo",
            "enviamelo por correo",
            "send it",
            "email it",
        )

        who = None

        # exact standalone commands only
        if text_norm in standalone_email_commands:
            who = "miguel"

        # allow exact "envialo a X"
        else:
            m_send = re.match(r"^\s*envialo\s+a\s+([a-z0-9_.-]+)\s*$", text_norm)
            if m_send:
                who = (m_send.group(1) or "").strip().lower()

        if who:

            try:
                to_email = get_fact(chat_id=chat_id, fact_key="user_email")
            except Exception:
                to_email = None

            if not to_email:
                to_email = get_user_email(chat_id, fallback_name=who)

            if not to_email:
                await update.message.reply_text(f"No tengo correo configurado para '{who}'.")
                return

            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT content
                FROM messages
                WHERE chat_id=?
                  AND role='assistant'
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(chat_id),),
            )
            row = cur.fetchone()
            conn.close()

            if not row:
                await update.message.reply_text("No encontré una respuesta reciente para enviar.")
                return

            last_reply = row["content"] if hasattr(row, "keys") else row[0]
            if not last_reply:
                await update.message.reply_text("La última respuesta está vacía; no tengo nada que enviar.")
                return

            reply_lower = (last_reply or "").lower()

            if "guion" in reply_lower or "llamada" in reply_lower:
                subject = "Valeria – Guion de llamada"
            elif "contrato" in reply_lower and "guion" not in reply_lower:
                subject = "Valeria – Borrador de contrato"
            elif "resumen" in reply_lower:
                subject = "Valeria – Resumen del caso"
            else:
                subject = "Valeria – Documento generado"
            send_email_resend(to_email=to_email, subject=subject, body=last_reply)

            await update.message.reply_text("📧 Listo, enviado. Revisa tu inbox .")
            return

    except Exception as e:
        logger.exception(f"[EMAIL_SEND_CMD] failed: {e}")
        await update.message.reply_text(f"Email error: {e}")
        return

    # --------------------------------------------------
    # Pending state inspector
    # --------------------------------------------------
    try:
        text_clean = (text or "").strip().lower()
        if text_clean in (
            "pendiente",
            "pendientes",
            "qué está pendiente",
            "que esta pendiente",
            "estado pendiente",
        ):
            pending_text = _get_pending_state_text(int(chat_id))
            if pending_text:
                await update.message.reply_text(pending_text)
            else:
                await update.message.reply_text("No tienes nada pendiente.")
            return
    except Exception as e:
        logger.exception(f"[PENDING_STATE_INSPECTOR] failed: {e}")

    # --------------------------------------------------
    # Pending confirm shortcuts (fast confirm / cancel)
    # --------------------------------------------------
    try:
        text_clean = (text or "").strip().lower()

        confirm_words = ("ok", "sí", "si", "dale", "yes", "confirmar")
        cancel_words = ("no", "cancelar", "cancel", "nah")

        has_pending = (
            int(chat_id) in _PENDING_TERM_CONFIRM
            or int(chat_id) in _PENDING_REMINDER_CONFIRM
            or int(chat_id) in _PENDING_CASE_DISAMBIG
        )

        if has_pending:
            if text_clean in confirm_words:
                # simulate confirmation
                logger.info("[PENDING_SHORTCUT] confirm triggered")
                text = "ok"
            elif text_clean in cancel_words:
                logger.info("[PENDING_SHORTCUT] cancel triggered")
                text = "cancelar"

    except Exception as e:
        logger.exception(f"[PENDING_SHORTCUT] failed: {e}")    

    # --------------------------------------------------
    # Undo last action (hard gate)
    # --------------------------------------------------
    try:
        if await try_undo_last_action(update, chat_id, text):
            return
    except Exception as e:
        logger.exception(f"[UNDO_GATE] failed: {e}")

    # --------------------------------------------------
    # Case disambiguation handler
    # --------------------------------------------------
    try:
        disambig_released = False

        logger.info(
            f"[CASE_DISAMBIG DEBUG] incoming text={text!r} chat_id={chat_id} "
            f"pending_keys={list(_PENDING_CASE_DISAMBIG.keys())}"
        )

        if int(chat_id) in _PENDING_CASE_DISAMBIG:
            dis = _PENDING_CASE_DISAMBIG[int(chat_id)]
            choice = (text or "").strip()
            choice_lower = choice.lower()

            # auto-cancel if user sent a fresh natural sentence
            if (
                not choice_lower.isdigit()
                and not choice_lower.startswith("detalle")
                and choice_lower not in ("cancelar", "cancel")
                and len(choice_lower) > 10
            ):
                logger.info(f"[CASE_DISAMBIG] auto-cancel due to new input: {choice_lower!r}")
                _PENDING_CASE_DISAMBIG.pop(int(chat_id), None)
                disambig_released = True
            else:
                choice_norm = choice.replace("case:", "").replace("CASE:", "").strip().lower()
                choice_norm = unicodedata.normalize("NFKD", choice_norm)
                choice_norm = "".join(ch for ch in choice_norm if not unicodedata.combining(ch))
                choice_norm = re.sub(r"[^\w\s]", " ", choice_norm)
                choice_norm = re.sub(r"\s+", " ", choice_norm).strip()

                if choice_norm in ("cancelar", "cancel", "salir", "no", "olvidalo", "olvidalo por ahora"):
                    _PENDING_CASE_DISAMBIG.pop(int(chat_id), None)
                    await update.message.reply_text("Entendido. Cancelé la selección.")
                    return

                m_detail = re.match(r"^(detalle|ver|info)\s+(\d+)$", choice_norm)
                logger.info(
                    f"[CASE_DISAMBIG] choice_norm={choice_norm!r} "
                    f"m_detail={bool(m_detail)} candidates={len(dis['candidates'])}"
                )

                if m_detail:
                    idx = int(m_detail.group(2))
                    if 1 <= idx <= len(dis["candidates"]):
                        cid, name = dis["candidates"][idx - 1]
                        try:
                            from core.case_mvp import generate_case_cockpit
                            out = generate_case_cockpit(int(chat_id), str(cid))
                            await update.message.reply_text(out, parse_mode="HTML")
                            await update.message.reply_text(
                                "Responde con 1 o 2 para seleccionar. También puedes escribir cancelar."
                            )
                            return
                        except Exception as e:
                            logger.exception(f"[CASE_DISAMBIG DETAIL] cockpit failed: {e}")
                            await update.message.reply_text("No pude cargar el detalle del caso.")
                            return

                selected = None

                if choice_norm.isdigit():
                    idx = int(choice_norm)

                    # allow direct case id
                    for cid, name in dis["candidates"]:
                        if str(cid) == choice_norm:
                            selected = (cid, name)
                            break

                    # otherwise allow 1/2/3 selection
                    if not selected and 1 <= idx <= len(dis["candidates"]):
                        selected = dis["candidates"][idx - 1]
                logger.info(
                    f"[CASE_DISAMBIG DEBUG] choice_norm={choice_norm!r} "
                    f"selected={selected!r} candidates={dis['candidates']!r}"
                )        

                if selected:
                    cid, name = selected
                    _PENDING_CASE_DISAMBIG.pop(int(chat_id), None)

                    if dis["type"] == "term":
                        _PENDING_TERM_CONFIRM[int(chat_id)] = {
                            "case_id": int(cid),
                            "client_name": name,
                            "event_text": dis["payload"]["event_text"],
                            "deadline_date": dis["payload"]["deadline_date"],
                        }
                        await update.message.reply_text(
                            f"⚠️ Detecté un posible término en CASE:{cid} ({name})\n\n"
                            f"\"{dis['payload']['event_text']}\"\n\n"
                            f"¿Quieres que lo registre?"
                        )
                        return

                    elif dis["type"] == "note":
                        from memory_store import insert_case_note, set_active_case_id

                        set_active_case_id(int(chat_id), str(cid))
                        note_id = insert_case_note(
                            chat_id=int(chat_id),
                            case_id=str(cid),
                            note_text=dis["payload"]["note_text"],
                            source=dis["payload"]["source"],
                        )

                        _LAST_ACTION[int(chat_id)] = {
                            "type": "note_insert",
                            "id": note_id,
                            "case_id": str(cid),
                        }

                        from core.case_summary import refresh_case_summary
                        refresh_case_summary(int(chat_id), str(cid))

                        await update.message.reply_text(
                            f"📝 Guardé esto como nota en CASE:{cid} ({name})."
                        )
                        return

                    elif dis["type"] == "reminder":
                        _PENDING_REMINDER_CONFIRM[int(chat_id)] = {
                            "case_id": int(cid),
                            "client_name": name,
                            "reminder_text": dis["payload"]["reminder_text"],
                            "due_date": dis["payload"]["due_date"],
                        }
                        await update.message.reply_text(
                            f"⚠️ Detecté un posible recordatorio en CASE:{cid} ({name})\n\n"
                            f"\"{dis['payload']['reminder_text']}\"\n\n"
                            f"¿Quieres que lo registre?"
                        )
                        return

                await update.message.reply_text(
                    "No entendí la opción.\n"
                    "Responde con 1 o 2.\n"
                    "También puedes escribir \"detalle 1\" o \"detalle 2\" para ver más info,\n"
                    "o \"cancelar\"."
                )
                return

        if disambig_released:
            logger.info("[CASE_DISAMBIG] released old state; continuing with fresh pipeline")

    except Exception as e:
        logger.exception(f"[CASE_DISAMBIG] failed: {e}")

    try:
        if await handle_pending_reminder_confirmation(update, chat_id, text, _LAST_ACTION):
            return
    except Exception as e:
        logger.exception(f"[PENDING_REMINDER_CONFIRM] failed: {e}")

    # --------------------------------------------------
    # Pending term confirmation
    # --------------------------------------------------
    try:
        if int(chat_id) in _PENDING_TERM_CONFIRM:
            pending = _PENDING_TERM_CONFIRM.get(int(chat_id))

            confirm_low = (text or "").strip().lower()
            confirm_low = unicodedata.normalize("NFKD", confirm_low)
            confirm_low = "".join(ch for ch in confirm_low if not unicodedata.combining(ch))
            confirm_low = re.sub(r"[^\w\s]", " ", confirm_low)
            confirm_low = re.sub(r"\s+", " ", confirm_low).strip()

            logger.info(
                f"[PENDING_TERM_CONFIRM] chat_id={chat_id} "
                f"confirm_low={confirm_low!r} pending={pending!r}"
            )

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
                _PENDING_TERM_CONFIRM.pop(int(chat_id), None)

                from memory_store import insert_case_event

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
                            pending["event_text"],
                            pending["deadline_date"],
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
                        f"⚠️ Término duplicado detectado en CASE:{pending['case_id']}."
                    )
                    return

                insert_case_event(
                    chat_id=int(chat_id),
                    case_id=int(pending["case_id"]),
                    event_text=pending["event_text"],
                    deadline_date=pending["deadline_date"],
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

                _LAST_ACTION[int(chat_id)] = {
                    "type": "term_insert",
                    "id": event_id,
                    "case_id": str(pending["case_id"]),
                }

                from core.case_summary import refresh_case_summary
                refresh_case_summary(int(chat_id), str(pending["case_id"]))

                await update.message.reply_text(
                    f"⏳ Término registrado en CASE:{pending['case_id']}\n"
                    f"Vence: {pending['deadline_date']}"
                )
                return

            if confirm_low in confirm_no:
                _PENDING_TERM_CONFIRM.pop(int(chat_id), None)
                await update.message.reply_text("Entendido. No lo registré.")
                return

    except Exception as e:
        logger.exception(f"[PENDING_TERM_CONFIRM] failed: {e}")

    # --------------------------------------------------
    # Reminder Creator + Cancel (DM only) — deterministic
    # --------------------------------------------------
    try:
        if await handle_reminder_gate(update, chat_id, text, _audit):
            return

    except Exception as e:
        logger.exception(f"[REMINDER_GATE_HANDLER] failed: {e}")

    # --------------------------------------------------
    # Case registration command — deterministic
    # --------------------------------------------------
    try:
        m = re.match(
            r"(?is)^\s*registrar\s+(?:el\s+)?(?:caso|expediente)\s+(\d{4,})\s+cliente\s+(.+?)\s*$",
            text or "",
        )
        if m:
            expediente = (m.group(1) or "").strip()
            client_name = (m.group(2) or "").strip()

            if expediente and client_name:
                from memory_store import upsert_case

                row_id = upsert_case(
                    chat_id=int(chat_id),
                    expediente=expediente,
                    client_name=client_name,
                    client_alias=None,
                )

                _audit(
                    chat_id,
                    action="CMD_CASE_REGISTER",
                    entity_type="case",
                    entity_id=str(row_id),
                    payload=f"expediente={expediente} | client_name={client_name}"[:500],
                    source="dm",
                )

                await update.message.reply_text(
                    f"Listo. Registré el caso {expediente} para el cliente {client_name.title()}."
                )
                return

    except Exception as e:
        logger.exception(f"[CASE_REGISTER_CMD] failed: {e}")

    # --------------------------------------------------
    # Case term command — deterministic
    # --------------------------------------------------
    try:
        m_term = re.match(
            r"(?is)^\s*registrar\s+t[eé]rmino\s+(?:del\s+)?(?:caso|expediente)\s+(\d{4,})\s*:\s*(.+?)\s*$",
            text or "",
        )
        if m_term:
            case_id = (m_term.group(1) or "").strip()
            event_text = (m_term.group(2) or "").strip()

            if case_id and event_text:
                deadline_date = _extract_deadline_date(event_text)

                if not deadline_date:
                    await update.message.reply_text(
                        "No pude detectar la fecha del término. Usa algo como: "
                        "\"registrar término del caso 20260301: audiencia el 15 de abril\"."
                    )
                    return

                from memory_store import insert_case_event

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
                            int(case_id),
                            event_text,
                            deadline_date,
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
                        f"⚠️ Término duplicado detectado en CASE:{case_id}."
                    )
                    return

                event_id = insert_case_event(
                    chat_id=int(chat_id),
                    case_id=int(case_id),
                    event_text=event_text,
                    deadline_date=deadline_date,
                )

                _LAST_ACTION[int(chat_id)] = {
                    "type": "term_insert",
                    "id": event_id,
                    "case_id": str(case_id),
                }

                try:
                    from core.case_summary import refresh_case_summary
                    refresh_case_summary(int(chat_id), str(case_id))
                except Exception:
                    pass

                await update.message.reply_text(
                    f"⏳ Término registrado en CASE:{case_id}\n"
                    f"Vence: {deadline_date}"
                )
                return

    except Exception as e:
        logger.exception(f"[CASE_TERM_CMD] failed: {e}")    


    # --------------------------------------------------
    # Task close command — deterministic
    # --------------------------------------------------
    try:
        m_task_close = re.match(
            r"(?is)^\s*(?:completar|cerrar)\s+tarea\s+(?:del\s+)?(?:caso|expediente)\s+(\d{4,})\s*:\s*(.+?)\s*$",
            text or "",
        )
        if m_task_close:
            case_id = (m_task_close.group(1) or "").strip()
            task_text = (m_task_close.group(2) or "").strip()

            if case_id and task_text:
                conn = _get_conn()
                cur = conn.cursor()

                cur.execute(
                    """
                    SELECT id, event_text
                    FROM case_events
                    WHERE chat_id=?
                      AND case_id=?
                      AND upper(event_text) LIKE 'TAREA:%'
                    ORDER BY id DESC
                    """,
                    (int(chat_id), int(case_id)),
                )
                rows = cur.fetchall() or []

                target_id = None
                target_text = None
                needle = task_text.lower().strip()

                for row in rows:
                    event_id = row["id"] if hasattr(row, "keys") else row[0]
                    event_text_full = row["event_text"] if hasattr(row, "keys") else row[1]
                    clean_task = event_text_full.split(":", 1)[1].strip() if ":" in event_text_full else event_text_full
                    if needle in clean_task.lower():
                        target_id = event_id
                        target_text = clean_task
                        break

                if not target_id:
                    conn.close()
                    await update.message.reply_text("No encontré una tarea abierta que coincida con eso.")
                    return

                _LAST_ACTION[int(chat_id)] = {
                    "type": "task_delete",
                    "id": target_id,
                    "event_text": f"TAREA: {target_text}",
                    "chat_id": int(chat_id),
                    "case_id": str(case_id),
                }

                cur.execute("DELETE FROM case_events WHERE id=?", (target_id,))
                conn.commit()
                conn.close()

                try:
                    from core.case_summary import refresh_case_summary
                    refresh_case_summary(int(chat_id), str(case_id))
                except Exception:
                    pass

                await update.message.reply_text(
                    f"✅ Marqué como completada la tarea en CASE:{case_id}:\n\"{target_text}\""
                )
                return

    except Exception as e:
        logger.exception(f"[TASK_CLOSE_CMD] failed: {e}")    

    # --------------------------------------------------
    # Case note command — deterministic
    # --------------------------------------------------
    try:
        m = re.match(r"(?is)^\s*nota\s+(?:del\s+)?(?:caso|expediente)\s+(\d{4,})\s*:\s*(.+?)\s*$", text or "")
        if m:
            case_id = (m.group(1) or "").strip()
            note_text = (m.group(2) or "").strip()

            if case_id and note_text:
                if is_low_signal_case_note(note_text):
                    await update.message.reply_text(
                        "Esa nota parece meta/dev/test y no la guardaré en memoria del caso. "
                        "Si de verdad la quieres guardar, usa: forzar nota del caso ..."
                    )
                    return

                from memory_store import insert_case_note, set_active_case_id

                set_active_case_id(int(chat_id), case_id)
                note_id = insert_case_note(
                    chat_id=int(chat_id),
                    case_id=case_id,
                    note_text=note_text,
                    source="text",
                    telegram_message_id=tg_msg_id,
                )

                _audit(
                    chat_id,
                    action="CMD_CASE_NOTE_CREATE",
                    entity_type="case_note",
                    entity_id=str(note_id),
                    payload=f"case_id={case_id} | text={note_text}"[:500],
                    source="dm",
                )

                _LAST_ACTION[int(chat_id)] = {
                    "type": "note_insert",
                    "id": note_id,
                    "case_id": str(case_id),
                }

                from core.case_summary import refresh_case_summary
                refresh_case_summary(int(chat_id), str(case_id))

                # --------------------------------------------------
                # TASK DETECTION (simple v1)
                # --------------------------------------------------
                try:
                    task_triggers = (
                        "pendiente",
                        "por hacer",
                        "llamar",
                        "enviar",
                        "revisar",
                        "hacer",
                    )

                    note_low = note_text.lower().strip()

                    if any(t in note_low for t in task_triggers):
                        from memory_store import insert_case_event

                        task_text = f"TAREA: {note_text}"

                        event_id = insert_case_event(
                            chat_id=int(chat_id),
                            case_id=int(case_id),
                            event_text=task_text,
                            deadline_date=None,
                        )

                        _LAST_ACTION[int(chat_id)] = {
                            "type": "task_insert",
                            "id": event_id,
                            "case_id": str(case_id),
                        }

                        try:
                            from core.case_summary import refresh_case_summary
                            refresh_case_summary(int(chat_id), str(case_id))
                        except Exception:
                            pass

                except Exception as e:
                    logger.exception(f"[TASK_DETECT] failed: {e}")

                await update.message.reply_text(f"Listo. Guardé la nota en el caso {case_id}.")
                return

        m_force = re.match(r"(?is)^\s*forzar\s+nota\s+(?:del\s+)?(?:caso|expediente)\s+(\d{4,})\s*:\s*(.+?)\s*$", text or "")
        if m_force:
            case_id = (m_force.group(1) or "").strip()
            note_text = (m_force.group(2) or "").strip()

            if case_id and note_text:
                from memory_store import insert_case_note, set_active_case_id

                set_active_case_id(int(chat_id), case_id)
                note_id = insert_case_note(
                    chat_id=int(chat_id),
                    case_id=case_id,
                    note_text=note_text,
                    source="text",
                    telegram_message_id=tg_msg_id,
                )

                _audit(
                    chat_id,
                    action="CMD_CASE_NOTE_CREATE_FORCED",
                    entity_type="case_note",
                    entity_id=str(note_id),
                    payload=f"case_id={case_id} | text={note_text}"[:500],
                    source="dm",
                )

                _LAST_ACTION[int(chat_id)] = {
                    "type": "note_insert",
                    "id": note_id,
                    "case_id": str(case_id),
                }

                from core.case_summary import refresh_case_summary
                refresh_case_summary(int(chat_id), str(case_id))

                await update.message.reply_text(f"Listo. Forcé la nota en el caso {case_id}.")
                return

    except Exception as e:
        logger.exception(f"[CASE_NOTE_CMD] failed: {e}")

    # --------------------------------------------------
    # NATURAL REMINDER DETECTION (suggestion only, no write)
    # --------------------------------------------------
    try:
        raw_text = (text or "").strip()
        low = raw_text.lower()

        # Strip only assistant-call prefixes, never real people names
        low = re.sub(r"^\s*(oye\s+val|hey\s+val|val)\s*[:,]?\s*", "", low).strip()

        intent = classify_user_intent(text)
        if intent == "advisory":
            logger.info(f"[NATURAL_REMINDER_DETECT] SKIP intent={intent}")
            raise StopIteration

        reminder_triggers = (
            "recuerdame",
            "recuérdame",
            "recordarme",
            "recordatorio",
            "llamar",
            "llame",
            "llamarlo",
            "llamarla",
            "darle seguimiento",
            "seguimiento",
            "revisar",
            "escribirle",
            "responderle",
        )

        reminder_time_markers = (
            "mañana",
            "manana",
            "hoy",
            "el lunes",
            "el martes",
            "el miercoles",
            "el miércoles",
            "el jueves",
            "el viernes",
            "el sabado",
            "el sábado",
            "el domingo",
        )

        if any(x in low for x in reminder_triggers) and any(x in low for x in reminder_time_markers):
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT expediente, client_name
                FROM cases
                WHERE chat_id=?
                ORDER BY id DESC
                """,
                (int(chat_id),),
            )
            rows = cur.fetchall() or []
            conn.close()

            matches = []
            for r in rows:
                expediente = r["expediente"] if hasattr(r, "keys") else r[0]
                client_name = r["client_name"] if hasattr(r, "keys") else r[1]

                if client_name and client_name.lower() in low:
                    matches.append((str(expediente), client_name))

            tz = ZoneInfo("America/Panama")
            now_local = datetime.now(tz)
            due_date = None

            weekdays = {
                "lunes": 0,
                "martes": 1,
                "miercoles": 2,
                "miércoles": 2,
                "jueves": 3,
                "viernes": 4,
                "sabado": 5,
                "sábado": 5,
                "domingo": 6,
            }

            if "mañana" in low or "manana" in low:
                due_date = (now_local + timedelta(days=1)).date().isoformat()
            elif "hoy" in low:
                due_date = now_local.date().isoformat()
            else:
                for name, target_wd in weekdays.items():
                    if f"el {name}" in low:
                        days_ahead = (target_wd - now_local.weekday()) % 7
                        if days_ahead == 0:
                            days_ahead = 7
                        due_date = (now_local + timedelta(days=days_ahead)).date().isoformat()
                        break

            if due_date:
                if _has_explicit_legal_intent(text) and len(matches) == 1:
                    case_id, client_name = matches[0]

                    explicit_auto_confirm_prefixes = (
                        "recuérdame",
                        "recuerdame",
                        "recordarme",
                    )

                    is_explicit_reminder = low.strip().startswith(explicit_auto_confirm_prefixes)

                    if is_explicit_reminder:
                        from memory_store import insert_case_event

                        event_text = f"RECORDATORIO: {text.strip()}"

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
                                    int(case_id),
                                    event_text,
                                    due_date,
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
                                f"⚠️ Recordatorio duplicado detectado en CASE:{case_id}."
                            )
                            return

                        event_id = insert_case_event(
                            chat_id=int(chat_id),
                            case_id=int(case_id),
                            event_text=event_text,
                            deadline_date=due_date,
                        )

                        _LAST_ACTION[int(chat_id)] = {
                            "type": "reminder_insert",
                            "id": event_id,
                            "case_id": str(case_id),
                        }

                        try:
                            from core.case_summary import refresh_case_summary
                            refresh_case_summary(int(chat_id), str(case_id))
                        except Exception:
                            pass

                        await update.message.reply_text(
                            f"⏰ Recordatorio registrado en CASE:{case_id}\n"
                            f"Fecha: {due_date}"
                        )
                        return

                    _PENDING_REMINDER_CONFIRM[int(chat_id)] = {
                        "case_id": int(case_id),
                        "client_name": client_name,
                        "reminder_text": text.strip(),
                        "due_date": due_date,
                    }

                    await update.message.reply_text(
                        f"⚠️ Detecté un posible recordatorio en CASE:{case_id} ({client_name})\n\n"
                        f"\"{text.strip()}\"\n\n"
                        f"¿Quieres que lo registre?"
                    )
                    return

                elif _has_explicit_legal_intent(text) and len(matches) > 1:
                    _PENDING_CASE_DISAMBIG[int(chat_id)] = {
                        "type": "reminder",
                        "candidates": matches,
                        "payload": {
                            "reminder_text": text.strip(),
                            "due_date": due_date,
                        },
                    }

                    conn = _get_conn()
                    cur = conn.cursor()

                    options = []

                    for (cid, name) in matches:
                        context_line = None
                        score = 0

                        cur.execute(
                            """
                            SELECT deadline_date, event_text
                            FROM case_events
                            WHERE chat_id=?
                              AND case_id=?
                              AND deadline_date IS NOT NULL
                              AND upper(event_text) NOT LIKE 'RECORDATORIO:%'
                            ORDER BY deadline_date ASC
                            LIMIT 1
                            """,
                            (int(chat_id), int(cid)),
                        )
                        row_legal = cur.fetchone()

                        if row_legal:
                            d = row_legal["deadline_date"] if hasattr(row_legal, "keys") else row_legal[0]
                            ev = row_legal["event_text"] if hasattr(row_legal, "keys") else row_legal[1]
                            if d and ev:
                                context_line = f"   • Próximo: {d} | {ev[:60]}"
                                score = 3

                        if not context_line:
                            cur.execute(
                                """
                                SELECT deadline_date, event_text
                                FROM case_events
                                WHERE chat_id=?
                                  AND case_id=?
                                  AND deadline_date IS NOT NULL
                                  AND upper(event_text) LIKE 'RECORDATORIO:%'
                                ORDER BY deadline_date ASC
                                LIMIT 1
                                """,
                                (int(chat_id), int(cid)),
                            )
                            row_rem = cur.fetchone()

                            if row_rem:
                                d = row_rem["deadline_date"] if hasattr(row_rem, "keys") else row_rem[0]
                                ev = row_rem["event_text"] if hasattr(row_rem, "keys") else row_rem[1]
                                if d and ev:
                                    context_line = f"   • Próximo: {d} | {ev[:60]}"
                                    score = 2

                        if not context_line:
                            cur.execute(
                                """
                                SELECT note_text
                                FROM case_notes
                                WHERE chat_id=?
                                  AND case_id=?
                                ORDER BY id DESC
                                LIMIT 1
                                """,
                                (int(chat_id), str(cid)),
                            )
                            row_note = cur.fetchone()

                            if row_note:
                                note_text = row_note["note_text"] if hasattr(row_note, "keys") else row_note[0]
                                if note_text:
                                    context_line = f"   • Último: {note_text[:80]}"
                                    score = 1

                        options.append((score, cid, name, context_line))

                    conn.close()
                    options.sort(key=lambda x: x[0], reverse=True)

                    option_lines = []
                    for idx, (score, cid, name, context_line) in enumerate(options, start=1):
                        line = f"{idx}) CASE:{cid} ({name})"
                        if context_line:
                            line += f"\n{context_line}"
                        option_lines.append(line)

                    options_text = "\n\n".join(option_lines)

                    await update.message.reply_text(
                        f"⚠️ Encontré más de un caso para este posible recordatorio:\n\n"
                        f"{options_text}\n\n"
                        f"Responde con 1 o 2.\n"
                        f"Escribe \"detalle 1\" o \"detalle 2\" para ver más info.\n"
                        f"También puedes escribir \"cancelar\"."
                    )
                    return

    except StopIteration:
        logger.info("[NATURAL_REMINDER_DETECT] skipped by intent gate")
    except Exception as e:
        logger.exception(f"[NATURAL_REMINDER_DETECT] failed: {e}")

    # --------------------------------------------------
    # NATURAL TERM DETECTION (suggestion only, no write)
    # --------------------------------------------------
    try:
        raw_text = (text or "").strip()
        low = raw_text.lower()

        # Strip only assistant-call prefixes, never real people names
        low = re.sub(r"^\s*(oye\s+val|hey\s+val|val)\s*[:,]?\s*", "", low).strip()

        intent = classify_user_intent(text)
        if intent == "advisory":
            logger.info(f"[NATURAL_TERM_DETECT] SKIP intent={intent}")
            raise StopIteration

        low = unicodedata.normalize("NFKD", low)
        low = "".join(ch for ch in low if not unicodedata.combining(ch))

        trigger_words = [
            "audiencia",
            "audiencias",
            "vence",
            "vencimiento",
            "plazo",
            "termino",
            "término",
            "cita",
            "citacion",
            "citación",
            "fecha",
        ]

        if any(w in low for w in trigger_words):
            m_date = re.search(
                r"\b(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b",
                low,
            )

            if m_date:
                month_map = {
                    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
                    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
                    "septiembre": 9, "setiembre": 9, "octubre": 10,
                    "noviembre": 11, "diciembre": 12,
                }

                day = int(m_date.group(1))
                month_name = m_date.group(2)
                month = month_map[month_name]
                year = datetime.now(ZoneInfo("America/Panama")).year
                deadline_date = f"{year:04d}-{month:02d}-{day:02d}"

                conn = _get_conn()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT expediente, client_name
                    FROM cases
                    WHERE chat_id=?
                    ORDER BY id DESC
                    """,
                    (int(chat_id),),
                )
                rows = cur.fetchall() or []
                conn.close()

                matches = []
                for r in rows:
                    expediente = r["expediente"] if hasattr(r, "keys") else r[0]
                    client_name = r["client_name"] if hasattr(r, "keys") else r[1]

                    if client_name and client_name.lower() in low:
                        matches.append((str(expediente), client_name))

                if _has_explicit_legal_intent(text) and len(matches) == 1:
                    case_id, client_name = matches[0]

                    _PENDING_TERM_CONFIRM[int(chat_id)] = {
                        "case_id": int(case_id),
                        "client_name": client_name,
                        "event_text": text.strip(),
                        "deadline_date": deadline_date,
                    }
                    logger.info(
                        f"[PENDING_TERM_CONFIRM] SET chat_id={chat_id} "
                        f"data={_PENDING_TERM_CONFIRM[int(chat_id)]}"
                    )

                    await update.message.reply_text(
                        f"⚠️ Detecté un posible término en CASE:{case_id} ({client_name})\n\n"
                        f"\"{text.strip()}\"\n\n"
                        f"¿Quieres que lo registre?"
                    )
                    return

                elif _has_explicit_legal_intent(text) and len(matches) > 1:
                    _PENDING_CASE_DISAMBIG[int(chat_id)] = {
                        "type": "term",
                        "candidates": matches,
                        "payload": {
                            "event_text": text.strip(),
                            "deadline_date": deadline_date,
                        },
                    }

                    conn = _get_conn()
                    cur = conn.cursor()

                    options = []

                    for (cid, name) in matches:
                        context_line = None
                        score = 0

                        cur.execute(
                            """
                            SELECT deadline_date, event_text
                            FROM case_events
                            WHERE chat_id=?
                              AND case_id=?
                              AND deadline_date IS NOT NULL
                              AND upper(event_text) NOT LIKE 'RECORDATORIO:%'
                            ORDER BY deadline_date ASC
                            LIMIT 1
                            """,
                            (int(chat_id), int(cid)),
                        )
                        row_legal = cur.fetchone()

                        if row_legal:
                            d = row_legal["deadline_date"] if hasattr(row_legal, "keys") else row_legal[0]
                            ev = row_legal["event_text"] if hasattr(row_legal, "keys") else row_legal[1]
                            if d and ev:
                                context_line = f"   • Próximo: {d} | {ev[:60]}"
                                score = 3

                        if not context_line:
                            cur.execute(
                                """
                                SELECT deadline_date, event_text
                                FROM case_events
                                WHERE chat_id=?
                                  AND case_id=?
                                  AND deadline_date IS NOT NULL
                                  AND upper(event_text) LIKE 'RECORDATORIO:%'
                                ORDER BY deadline_date ASC
                                LIMIT 1
                                """,
                                (int(chat_id), int(cid)),
                            )
                            row_rem = cur.fetchone()

                            if row_rem:
                                d = row_rem["deadline_date"] if hasattr(row_rem, "keys") else row_rem[0]
                                ev = row_rem["event_text"] if hasattr(row_rem, "keys") else row_rem[1]
                                if d and ev:
                                    context_line = f"   • Próximo: {d} | {ev[:60]}"
                                    score = 2

                        if not context_line:
                            cur.execute(
                                """
                                SELECT note_text
                                FROM case_notes
                                WHERE chat_id=?
                                  AND case_id=?
                                ORDER BY id DESC
                                LIMIT 1
                                """,
                                (int(chat_id), str(cid)),
                            )
                            row_note = cur.fetchone()

                            if row_note:
                                note_text = row_note["note_text"] if hasattr(row_note, "keys") else row_note[0]
                                if note_text:
                                    context_line = f"   • Último: {note_text[:80]}"
                                    score = 1

                        options.append((score, cid, name, context_line))

                    conn.close()
                    options.sort(key=lambda x: x[0], reverse=True)

                    option_lines = []
                    for idx, (score, cid, name, context_line) in enumerate(options, start=1):
                        line = f"{idx}) CASE:{cid} ({name})"
                        if context_line:
                            line += f"\n{context_line}"
                        option_lines.append(line)

                    options_text = "\n\n".join(option_lines)

                    await update.message.reply_text(
                        f"⚠️ Encontré más de un caso para este posible término:\n\n"
                        f"{options_text}\n\n"
                        f"Responde con 1 o 2.\n"
                        f"Escribe \"detalle 1\" o \"detalle 2\" para ver más info.\n"
                        f"También puedes escribir \"cancelar\"."
                    )
                    return

    except StopIteration:
        logger.info("[NATURAL_TERM_DETECT] skipped by intent gate")
    except Exception as e:
        logger.exception(f"[NATURAL_TERM_DETECT] failed: {e}")

    # --------------------------------------------------
    # Natural Note Capture v1 — DISABLED FOR DEMO SAFETY
    # --------------------------------------------------
    case_note_handled = False



    # --------------------------------------------------
    # Google Calendar write sandbox
    # --------------------------------------------------
    try:
        if await try_gcal_write_sandbox(update, chat_id, text):
            return
    except Exception as e:
        logger.exception(f"[GCAL_WRITE_SANDBOX] failed: {e}")
        await update.message.reply_text("No pude crear el evento en Google Calendar. Reviso credenciales.")
        return True

    # --- Sprint10: court-day timeline queries ---
    try:
        from core.case_mvp import (
            try_case_add_note,
            try_case_register_term,
            try_case_create,
            try_delete_last_note,
            try_case_status,
            try_case_cockpit,
            try_case_health,
            try_case_health_legend,
            try_cases_requiring_attention,
            try_case_timeline_window,
            try_case_timeline_since_last_hearing,
            try_case_timeline_for_case,
            try_timeline_for_case,
            try_pending_list,
            try_timeline_today,
            try_due_today,
            try_due_range,
            try_due_tomorrow,
            try_terms_due_this_week,
            try_terms_due_this_week_for_case,
            try_terms_due_today,
            try_cases_due_this_week,
        )
        from core.control import try_debug_mode, try_help
        from core.case_reports import (
            try_idle_cases,
            try_daily_work_summary,
            try_priority_dashboard,
        )
        from core.conflict_detector import try_conflicts_tomorrow

        advisory_case_prefixes = (
            "resumen del caso",
            "resumen rápido del caso",
            "resumen rapido del caso",
            "dame un resumen del caso",
            "dame un resumen rápido del caso",
            "dame un resumen rapido del caso",
            "qué opinas del caso",
            "que opinas del caso",
            "qué crees que deberíamos hacer",
            "que crees que deberiamos hacer",
            "estado del caso",
            "como va el caso",
            "cómo va el caso",
        )

        is_advisory_case_prompt = any(
            (text or "").lower().strip().startswith(p) for p in advisory_case_prefixes
        )

        HANDLERS = [
            try_debug_mode,
            try_help,
            try_undo_last_action,

            # due / agenda natural FIRST
            try_due_today_natural,
            try_agenda_tomorrow_natural,
            try_due_tomorrow_natural,
            try_week_natural,
            # conflict checks
            try_conflicts_tomorrow,
            try_priority_dashboard,

            # reports / control
            try_idle_cases,
            try_daily_work_summary,

            # case mutations
            try_case_add_note,
            try_case_register_term,
            try_case_create,
            try_delete_last_note,

            # case views
            try_case_status,
            try_case_cockpit,
            try_case_health_legend,
            try_case_health,

            # dashboards
            try_cases_requiring_attention,

            # timelines
            try_case_timeline_window,
            try_case_timeline_since_last_hearing,
            try_case_timeline_for_case,
            try_timeline_for_case,
            try_pending_list,
            try_timeline_today,

            # due / agenda
            try_due_today,
            try_due_tomorrow,
            try_terms_due_this_week_for_case,
            try_cases_due_this_week,
            try_terms_due_today,
            try_terms_due_this_week,
            try_due_range,
        ]

        # --------------------------------------------------
        # HARD AGENDA OVERRIDE (guaranteed deterministic)
        # --------------------------------------------------
        try:
            t = (text or "").strip().lower()
            t = unicodedata.normalize("NFKD", t)
            t = "".join(ch for ch in t if not unicodedata.combining(ch))

            if re.match(r"^que\s+vence\s+manana$", t):
                from core.case_mvp import try_due_tomorrow
                if await try_due_tomorrow(update, chat_id, text):
                    return

        except Exception as e:
            logger.exception(f"[HARD_AGENDA_OVERRIDE] failed: {e}")

        for handler in HANDLERS:
            if is_advisory_case_prompt and handler in (
                try_case_status,
                try_case_cockpit,
            ):
                continue

            if await handler(update, chat_id, text):
                return

        text_lower = (text or "").lower().strip()
        advisory_case_prefixes = (
            "resumen del caso",
            "resumen rápido del caso",
            "resumen rapido del caso",
            "dame un resumen del caso",
            "dame un resumen rápido del caso",
            "dame un resumen rapido del caso",
            "qué opinas del caso",
            "que opinas del caso",
            "qué crees que deberíamos hacer",
            "que crees que deberiamos hacer",
            "estado del caso",
            "como va el caso",
            "cómo va el caso",
        )

        if (
            "caso" in text_lower
            and "casos" not in text_lower
            and not any(text_lower.startswith(p) for p in advisory_case_prefixes)
        ):
            await update.message.reply_text("No encuentro ese caso en tu base de datos.")
            return

    except Exception as e:
        logger.exception(f"[CASE_TIMELINE] failed: {e}")

    # --------------------------------------------------
    # Direct case cockpit trigger (detalle <case_id>)
    # --------------------------------------------------
    try:
        m = re.match(r"(?is)^\s*(detalle|ver|info)\s+(\d{4,})\s*$", text or "")
        if m:
            case_id = (m.group(2) or "").strip()

            from core.case_mvp import generate_case_cockpit

            out = generate_case_cockpit(int(chat_id), str(case_id))
            await update.message.reply_text(out, parse_mode="HTML")
            return
    except Exception as e:
        logger.exception(f"[DIRECT_COCKPIT] failed: {e}")    

    # Store user msg
    try:
        insert_message(
            chat_id=chat_id,
            role="user",
            content=text,
            telegram_message_id=tg_msg_id,
            model_used=None,
        )
    except Exception as e:
        logger.exception(f"Failed to insert user message into DB: {e}")

    # --------------------------------------------------
    # Memory: favorite color Q/A
    # --------------------------------------------------
    if is_color_memory_question(text):
        stored = None
        try:
            stored = get_fact(chat_id=chat_id, fact_key="favorite_color")
        except Exception as e:
            logger.exception(f"Failed to read favorite_color fact: {e}")

        if stored:
            reply = f"Claro, {preferred_name}, tu color favorito es {stored}. Eso no se me olvida tan fácil."
        else:
            reply = (
                f"Todavía no me has dicho claramente cuál es tu color favorito, {preferred_name}. "
                "Dímelo con: 'mi color favorito es ...'."
            )

        sent = await _send_reply(update, context, reply)
        try:
            insert_message(
                chat_id=chat_id,
                role="assistant",
                content=reply,
                telegram_message_id=sent.message_id,
                model_used="gpt-4.1-mini",
            )
        except Exception as e:
            logger.exception(f"Failed to insert assistant message into DB: {e}")
        return

    fav = extract_favorite_color(text)
    if fav:
        try:
            upsert_fact(chat_id=chat_id, fact_key="favorite_color", fact_value=fav)
        except Exception as e:
            logger.exception(f"Failed to upsert favorite_color: {e}")
        reply = f"Queda registrado, {preferred_name}: tu color favorito ahora es {fav}. Lo tengo guardado."
        sent = await _send_reply(update, context, reply)
        try:
            insert_message(chat_id, "assistant", reply, sent.message_id, "gpt-4.1-mini")
        except Exception:
            pass
        return

    goal = extract_main_goal(text)
    if goal:
        try:
            upsert_fact(chat_id=chat_id, fact_key="main_goal", fact_value=goal)
        except Exception as e:
            logger.exception(f"Failed to upsert main_goal: {e}")
        reply = f"Queda registrado, {preferred_name}: tu objetivo principal ahora es: '{goal}'."
        sent = await _send_reply(update, context, reply)
        try:
            insert_message(chat_id, "assistant", reply, sent.message_id, "gpt-4.1-mini")
        except Exception:
            pass
        return

    lang = extract_preferred_language(text)
    if lang:
        try:
            upsert_fact(chat_id=chat_id, fact_key="preferred_language", fact_value=lang)
        except Exception as e:
            logger.exception(f"Failed to upsert preferred_language: {e}")

        if lang == "es":
            reply = f"Listo, {preferred_name}: a partir de ahora hablamos en español."
        else:
            reply = f"Got it, {preferred_name}: from now on we’ll speak in English."
        sent = await _send_reply(update, context, reply)
        try:
            insert_message(chat_id, "assistant", reply, sent.message_id, "gpt-4.1-mini")
        except Exception:
            pass
        return

    name = extract_preferred_name(text)
    if name:
        try:
            clean_name = name.strip().title()
            upsert_fact(chat_id=chat_id, fact_key="preferred_name", fact_value=clean_name)
        except Exception as e:
            logger.exception(f"Failed to upsert preferred_name: {e}")
            clean_name = name.strip().title()
        reply = f"Perfecto. A partir de ahora te voy a llamar {clean_name}. Lo dejo anotado en memoria."
        sent = await _send_reply(update, context, reply)
        try:
            insert_message(chat_id, "assistant", reply, sent.message_id, "gpt-4.1-mini")
        except Exception:
            pass
        return
    
    email = extract_user_email(text)
    if email:
        try:
            upsert_fact(chat_id=chat_id, fact_key="user_email", fact_value=email)
        except Exception as e:
            logger.exception(f"Failed to upsert user_email: {e}")
        reply = f"Perfecto. Guardé tu correo: {email}."
        sent = await _send_reply(update, context, reply)
        try:
            insert_message(chat_id, "assistant", reply, sent.message_id, "gpt-4.1-mini")
        except Exception:
            pass
        return

    note = extract_freeform_note(text)
    if note:
        try:
            note_id = add_note(chat_id, note)
        except Exception as e:
            logger.exception(f"Failed to insert natural note for chat_id={chat_id}: {e}")
            await update.message.reply_text(f"Quise guardar esa nota pero algo falló, {preferred_name}. Intenta de nuevo.")
            return
        if note_id <= 0:
            await update.message.reply_text(f"La nota quedó demasiado vacía, {preferred_name}.")
            return
        reply = f"Listo, {preferred_name}. Guardé la nota #{note_id}:\n{note}"
        sent = await _send_reply(update, context, reply)
        try:
            insert_message(chat_id, "assistant", reply, sent.message_id, "gpt-4.1-mini")
        except Exception:
            pass
        return

    # --------------------------------------------------
    # Number-to-details (Places)
    # --------------------------------------------------
    if text.isdigit():
        sel = int(text)
        sess = _places_session_get(chat_id)
        if sess and 1 <= sel <= 5:
            if int(time.time()) - int(sess.get("ts", 0)) <= 600:
                results = _normalize_places_results(sess.get("results") or [])
                idx = sel - 1
                if idx < len(results):
                    pid = (results[idx] or {}).get("place_id")
                    if pid:
                        d = place_details(pid)
                        if isinstance(d, dict) and d.get("error"):
                            msg = f"Se cayó el detalle del lugar, {preferred_name}."
                            await update.message.reply_text(msg)
                            return

                        if not isinstance(d, dict):
                            await update.message.reply_text(f"Detalle inválido del lugar, {preferred_name}.")
                            return

                        name = (d.get("name") or "?")
                        addr = (d.get("address") or "")
                        phone = (d.get("phone") or "")
                        rating = d.get("rating")
                        website = d.get("website") or ""
                        maps_url = d.get("maps_url") or (results[idx] or {}).get("maps_url") or ""

                        parts = [f"{name}"]
                        if rating is not None:
                            parts.append(f"⭐ {rating}")
                        if addr:
                            parts.append(addr)
                        if phone:
                            parts.append(f"📞 {phone}")
                        if website:
                            parts.append(f"🌐 {website}")
                        if maps_url:
                            parts.append(f"🗺️ {maps_url}")

                        msg = "\n".join(parts)
                        await update.message.reply_text(msg, parse_mode=None, disable_web_page_preview=True)
                        return

    # --------------------------------------------------
    # Natural language → Google Places
    # --------------------------------------------------
    if _is_places_intent(text) and _looks_like_places_request(text):
        q = _places_query_from_text(text)
        try:
            results = places_search(q, limit=5)
        except Exception as e:
            logger.exception(f"Places search failed: {e}")
            await update.message.reply_text(
                f"Se cayó la búsqueda de lugares, {preferred_name}. Intenta otra vez en un minuto."
            )
            return

        if isinstance(results, dict) and results.get("error"):
            await update.message.reply_text(
                f"Error buscando lugares, {preferred_name}: {results.get('error')}"
            )
            return

        results = _normalize_places_results(results)
        if results:
            _places_session_set(chat_id, results)

        if not results:
            await update.message.reply_text(
                f"No encontré resultados con eso, {preferred_name}. Prueba con más detalle (tipo + zona)."
            )
            return

        lines = []
        for i, r in enumerate(results, start=1):
            name = (r.get("name") or "?")
            addr = r.get("address") or r.get("formatted_address") or ""
            rating = r.get("rating")
            maps_url = r.get("maps_url") or ""

            part = f"{i}) {name}"
            if rating is not None:
                part += f" ⭐ {rating}"
            if addr:
                part += f"\n{addr}"
            if maps_url:
                part += f"\n🗺️ {maps_url}"
            lines.append(part)

        header = f"Aquí tienes, {preferred_name}:"
        footer = "\n\nResponde con un número (1–5) para ver detalles."
        await update.message.reply_text(
            header + "\n\n" + "\n\n".join(lines) + footer,
            parse_mode=None,
            disable_web_page_preview=True,
        )
        return

    # --------------------------------------------------
    # Load context + facts + semantic recall
    # --------------------------------------------------
    try:
        recent = get_recent_messages(chat_id=chat_id, limit=12)
    except Exception as e:
        logger.exception(f"Failed to fetch recent messages from DB: {e}")
        recent = []

    context_block = build_context_block(recent)

    try:
        facts = get_all_facts(chat_id=chat_id)
    except Exception as e:
        logger.exception(f"Failed to fetch user facts from DB: {e}")
        facts = {}

    facts_block = ""
    if facts:
        fact_lines: List[str] = []
        for k, v in facts.items():
            fact_lines.append(f"{k}: {v}")
        facts_block = "\n".join(fact_lines)

    semantic_block = _semantic_recall_block(chat_id=chat_id, query=text, k=5)
    advisory_system_rules = None

    # --------------------------------------------------
    # Phase 3A: inject active case summary into LLM context (read-only)
    # --------------------------------------------------
    summary_block = ""
    try:
        from memory_store import get_case_summary

        active_case_id = None
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT active_case_id FROM chat_prefs WHERE chat_id=?",
                (int(chat_id),),
            )
            row = cur.fetchone()
            conn.close()

            if row:
                active_case_id = row["active_case_id"] if hasattr(row, "keys") else row[0]
        except Exception:
            active_case_id = None

        if active_case_id:
            summary_row = get_case_summary(int(chat_id), str(active_case_id))
            if summary_row:
                summary_text = (summary_row.get("summary_text") or "").strip()
                if summary_text:
                    summary_block = f"\n[CASE SUMMARY]\n{summary_text}\n"

    except Exception:
        summary_block = ""
    
    tclean = (text or "").strip()

    if len(tclean) < 8 or _is_control_ack(tclean):
        semantic_block = ""

    if int(chat_id) < 0:
        _audit(
            chat_id,
            action="MODEL_BLOCKED_GROUP",
            entity_type="guard",
            entity_id=None,
            payload=(text or "")[:200],
            source="group",
        )
        return await _send_reply(update, context, "Group mode: commands only (ping, CASE:<id>, note: <text>).")

        advisory_system_rules = None

    try:
        low = (text or "").lower().strip()
        advisory_case_prefixes = (
            "qué opinas del caso",
            "que opinas del caso",
            "qué crees que deberíamos hacer",
            "que crees que deberiamos hacer",
            "dame un resumen del caso",
            "dame un resumen rápido del caso",
            "dame un resumen rapido del caso",
            "resumen del caso",
            "resumen rápido del caso",
            "resumen rapido del caso",
            "estrategia del caso",
            "siguiente paso del caso",
            "next step for the case",
        )

        if any(low.startswith(p) for p in advisory_case_prefixes):
            advisory_system_rules = """
MODO ASESORÍA DE CASO

Responde usando esta estructura exacta:

1. HECHOS CONFIRMADOS
- Solo hechos confirmados por los datos del caso
- No inventes hechos
- No repitas relleno

2. RIESGOS INMEDIATOS
- Riesgos reales basados en fechas, actividad, recordatorios o vacíos visibles

3. SIGUIENTE ACCIÓN CONCRETA
- Una acción específica y ejecutable
- No consejos genéricos

4. FALTANTE CRÍTICO
- SOLO puedes mencionar ausencias directamente inferibles de los registros actuales
- Si existen tareas detectadas, debes tratarlas como trabajo abierto real
- Puedes mencionar como faltante crítico una tarea abierta visible en los datos
- Usa siempre esta forma: "no consta X en registros"
- X debe ser algo observable, por ejemplo:
  - "no consta nota de estrategia"
  - "no consta checklist de contestación"
  - "no consta documento preparado"
- NO menciones categorías legales genéricas como:
  testigos, pruebas, expediente incompleto, defensa, etc.
  A MENOS que esas palabras existan explícitamente en los datos del caso

5. ANÁLISIS
- Tu razonamiento
- Debe estar claramente presentado como análisis, no como hecho confirmado

Reglas:
- No inventes testigos, estrategia legal, pruebas o documentos si no aparecen en el contexto
- No uses frases genéricas tipo "hay que revisar todo" salvo que las conectes con un hecho concreto
- Si algo no puede confirmarse, dilo explícitamente
- Sé breve, específico y útil

Reglas de estructura obligatoria:
- TODAS las secciones deben estar presentes SIEMPRE
- Si no hay suficiente información para una sección, escribir exactamente:
  "No hay información suficiente en los datos actuales."
- No omitir ninguna sección bajo ninguna circunstancia
""".strip()
    except Exception:
        advisory_system_rules = None

    # --------------------------------------------------
    # DETERMINISTIC URGENCY BLOCK
    # --------------------------------------------------
    urgency_block = None

    try:
        from memory_store import get_case_summary

        tz = ZoneInfo("America/Panama")
        now_local = datetime.now(tz).date()

        active_case_id = None

        # get active case
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT active_case_id FROM chat_prefs WHERE chat_id=?",
                (int(chat_id),),
            )
            row = cur.fetchone()
            conn.close()
            if row:
                active_case_id = (row[0] or "").strip()
        except Exception:
            active_case_id = None

        if active_case_id:
            summary_row = get_case_summary(int(chat_id), str(active_case_id))

            if summary_row:
                next_deadline = summary_row.get("next_deadline")

                days_to_deadline = None
                if next_deadline:
                    try:
                        d = datetime.strptime(next_deadline, "%Y-%m-%d").date()
                        days_to_deadline = (d - now_local).days
                    except Exception:
                        days_to_deadline = None

                urgency_lines = []
                urgency_lines.append(f"Hoy: {now_local}")

                if next_deadline:
                    urgency_lines.append(f"Próximo término: {next_deadline}")

                if days_to_deadline is not None:
                    urgency_lines.append(f"Días hasta término: {days_to_deadline}")

                    if days_to_deadline < 0:
                        urgency_lines.append("Estado del término: vencido")
                    elif days_to_deadline == 0:
                        urgency_lines.append("Estado del término: vence hoy")
                    elif days_to_deadline <= 3:
                        urgency_lines.append("Estado del término: crítico")
                    elif days_to_deadline <= 7:
                        urgency_lines.append("Estado del término: próximo")
                    else:
                        urgency_lines.append("Estado del término: lejano")

                urgency_block = "\n".join(urgency_lines)

    except Exception as e:
        logger.exception(f"[URGENCY_BLOCK] failed: {e}")
        urgency_block = None

    # --------------------------------------------------
    # DOCUMENT GENERATION MODE (HARD OVERRIDE)
    # --------------------------------------------------
    text_norm = unicodedata.normalize("NFKD", (text or "").lower())
    text_norm = "".join(ch for ch in text_norm if not unicodedata.combining(ch))

    doc_generation_triggers = (
        "contrato",
        "hazme un contrato",
        "generame un contrato",
        "modelo de",
        "modelo ",
        "borrador de",
        "borrador ",
        "clausula",
        "clausulas",
        "acuerdo",
        "convenio",
        "lease",
        "nda",
    )

    is_doc_mode = any(t in text_norm for t in doc_generation_triggers)

    if is_doc_mode:
        reply = call_val_openai(
            chat_id,
            text,
            context_block="",
            facts_block="",
            semantic_block="",
            forced_lang=preferred_language,
            system_rules=(
                "You are a legal drafting assistant.\n"
                "When the user asks for a contract, model, or document:\n"
                "- ALWAYS produce a complete first draft immediately.\n"
                "- DO NOT ask questions before generating.\n"
                "- Use placeholders like [NOMBRE], [FECHA], [MONTO] if data is missing.\n"
                "- Keep it clean, structured, and usable.\n"
                "- After the draft, optionally add a short note asking for missing details.\n"
                "Never call the user 'Boss'. Never use that word.\n"
            ),
        )
    else:
        from memory_store import fetch_recent_memory

        combined_system_rules = advisory_system_rules

        if urgency_block:
            extra = f"\n\nDATOS DE TIEMPO REAL:\n{urgency_block}"
            combined_system_rules = (combined_system_rules or "") + extra

        memory_rows = fetch_recent_memory(chat_id, limit=10)

        memory_lines = []
        for r in memory_rows:
            bucket = r[1] if not hasattr(r, "keys") else r["bucket"]
            raw = r[2] if not hasattr(r, "keys") else r["raw_input"]

            if bucket == "sensitive":
                continue

            if raw and raw.strip():
                memory_lines.append(f"- {raw.strip()}")

        memory_block = ""
        if memory_lines:
            memory_block = "\n\nMEMORIA RECIENTE DEL USUARIO:\n" + "\n".join(memory_lines)

        logger.info(f"[MEM_INJECT_ROWS] count={len(memory_rows)}")
        logger.info(f"[MEM_INJECT_BLOCK_REPR] {memory_block!r}") 

        effective_context_block = context_block + summary_block + memory_block
        effective_semantic_block = semantic_block

        if advisory_system_rules:
            effective_context_block = summary_block + memory_block
            effective_semantic_block = ""  

        raw_input = text

        name_instruction = ""
        if preferred_name:
            name_instruction = f"\nAlways address the user as '{preferred_name}'. Do not use any other name."

        # ------------------------------------------
        # OPERATOR OVERRIDE (anti-assistant mode)
        # ------------------------------------------
        try:
            if _has_active_commitment(text):

                m = re.search(
                    r"\b(?:a|con)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]+(?:\s+[a-zA-Záéíóúñ]+)?)",
                    text or ""
                )
                target = (m.group(1) if m else "").strip()
                target_title = str(target).strip().title() if target else ""

                if should_emit_inline_operator_nudge(
                    chat_id=chat_id,
                    raw_text=raw_input,
                    cooldown_seconds=180
                ):
                    msg = render_operator_reminder(
                        chat_id=chat_id,
                        raw_text=raw_input,
                        target=target_title,
                    )
                    await send_telegram_reply(update, msg, chat_id, "operator_inline_nudge")

                # 🔒 HARD STOP — DO NOT LET ANY OTHER LAYERS RUN
                return

        except Exception as e:
            logger.exception(f"[OPERATOR_OVERRIDE] failed: {e}")
        reply = call_val_openai(
            chat_id,
            text,
            context_block=effective_context_block,
            facts_block=facts_block,
            semantic_block=effective_semantic_block,
            forced_lang=preferred_language,
            system_rules=(
                (combined_system_rules or "")
                + """

            OPERATOR MODE DIRECTIVE:

            - Do NOT default to generic help like offering scripts, guides, or “do you want help”.
            - Prioritize continuity over politeness.
            - If the user has mentioned a person or situation repeatedly, assume it matters.
            - Respond based on pattern, not just the last message.
            - Apply light pressure when something is pending.
            - Avoid sounding like a generic assistant.

            GOOD:
            "Oye… Noah sigue pendiente. ¿Lo resolves hoy o lo movemos?"

            BAD:
            "¿Quieres que te ayude con un guión o sugerencias?"

            - Keep responses short, grounded, and context-aware.
            """
                + "\nNever call the user 'Boss'. Never use that word."
                + name_instruction
            ),
        )

        try:
            from memory_store import search_memory

            candidates = _extract_memory_candidates(text)
            matched_candidate = None

            for candidate in candidates:
                rows = search_memory(chat_id, candidate, limit=5)
                usable_rows = []

                for r in rows:
                    raw = r[2] if not hasattr(r, "keys") else r["raw_input"]
                    if raw and raw.strip() and raw.strip() != text.strip():
                        usable_rows.append(raw.strip())

                if usable_rows:
                    matched_candidate = candidate
                    break

            if matched_candidate:
                lang = resolve_user_language(chat_id)
                candidate_title = str(matched_candidate).strip().title()

                if lang == "en":
                    if reply:
                        reply = f"{candidate_title} was already on your radar.\n\n" + reply
                else:
                    if reply:
                        reply = f"{candidate_title} ya estaba en tu radar.\n\n" + reply

        except Exception as e:
            logger.exception(f"[NUDGE_APPEND] failed: {e}")

    # --------------------------------------------------
    # ENFORCE ADVISORY STRUCTURE (hard guarantee)
    # --------------------------------------------------
    def _ensure_advisory_structure(text: str) -> str:
        required_sections = [
            "1. HECHOS CONFIRMADOS",
            "2. RIESGOS INMEDIATOS",
            "3. SIGUIENTE ACCIÓN CONCRETA",
            "4. FALTANTE CRÍTICO",
            "5. ANÁLISIS",
        ]

        if not text:
            return text

        lines = (text or "").splitlines()
        existing_headers = set()

        for line in lines:
            stripped = line.strip()
            if stripped in required_sections:
                existing_headers.add(stripped)

        out = text

        # Add missing sections
        for section in required_sections:
            if section not in existing_headers:
                out += f"\n\n{section}\nNo hay información suficiente en los datos actuales."

        # Fill empty sections
        fixed_lines = out.splitlines()
        result_lines = []
        i = 0

        while i < len(fixed_lines):
            line = fixed_lines[i]
            stripped = line.strip()
            result_lines.append(line)

            if stripped in required_sections:
                j = i + 1
                while j < len(fixed_lines) and not fixed_lines[j].strip():
                    j += 1

                if j >= len(fixed_lines) or fixed_lines[j].strip() in required_sections:
                    result_lines.append("No hay información suficiente en los datos actuales.")

            i += 1

        return "\n".join(result_lines).strip()

    if advisory_system_rules:
        reply = _ensure_advisory_structure(reply)

    # --------------------------------------------------
    # POST-FILTER: remove forbidden legal hallucinations
    # --------------------------------------------------
    try:
        if advisory_system_rules:
            forbidden_terms = [
                "testigos",
                "pruebas",
                "expediente esté completo",
                "expediente completo",
                "defensa",
                "estrategia legal",
            ]

            cleaned_lines = []
            for line in (reply or "").splitlines():
                if any(term in line.lower() for term in forbidden_terms):
                    continue
                cleaned_lines.append(line)

            reply = "\n".join(cleaned_lines).strip()

    except Exception as e:
        logger.exception(f"[POST_FILTER] failed: {e}")

    # --------------------------------------------------
    # TASK NUDGE (v2 — relevance gated)
    # --------------------------------------------------
    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT event_text
            FROM case_events
            WHERE chat_id=?
              AND event_text LIKE 'TAREA:%'
            ORDER BY id DESC
            LIMIT 5
            """,
            (int(chat_id),),
        )

        rows = cur.fetchall() or []
        conn.close()

        tasks = []
        for r in rows:
            txt = r["event_text"] if hasattr(r, "keys") else r[0]
            if txt:
                clean = txt.split(":", 1)[1].strip() if ":" in txt else txt
                tasks.append(clean)

        if tasks and not _has_active_commitment(text):
            low = (text or "").lower()

            operational_triggers = (
                "caso",
                "resumen",
                "opinas",
                "estado",
                "detalle",
                "situacion",
            )

            trivial_triggers = (
                "hola",
                "ok",
                "dale",
                "gracias",
            )

            is_operational = any(t in low for t in operational_triggers)
            is_trivial = low.strip() in trivial_triggers

            should_nudge = False

            if len(tasks) >= 2:
                should_nudge = True
            elif is_operational:
                should_nudge = True
            elif not is_trivial and len(tasks) == 1:
                should_nudge = True

            if should_nudge and reply:
                nudge_lines = [f"⚠️ Tienes {len(tasks)} tarea(s) abierta(s):"]
                for t in tasks[:2]:
                    nudge_lines.append(f"- {t}")

                nudge_block = "\n".join(nudge_lines)
                reply = (reply or "").strip() + "\n\n" + nudge_block

    except Exception as e:
        logger.exception(f"[TASK_NUDGE] failed: {e}") 

    # --------------------------------------------------
    # AUTO EMAIL (inline intent)
    # --------------------------------------------------
    try:
        text_norm = unicodedata.normalize("NFKD", (text or "").lower())
        text_norm = "".join(ch for ch in text_norm if not unicodedata.combining(ch))

        auto_email_triggers = (
            "envialo",
            "enviamelo",
            "mandamelo",
            "mandamelo por correo",
            "enviamelo por correo",
            "send it",
            "email it",
        )

        if any(t in text_norm for t in auto_email_triggers):
            try:
                to_email = get_fact(chat_id=chat_id, fact_key="user_email")
            except Exception:
                to_email = None

            if not to_email:
                to_email = get_user_email(chat_id)

            if to_email and reply:
                reply_lower = reply.lower()

                if "guion" in reply_lower or "llamada" in reply_lower:
                    subject = "Valeria – Guion de llamada"
                elif "contrato" in reply_lower and "guion" not in reply_lower:
                    subject = "Valeria – Borrador de contrato"
                elif "resumen" in reply_lower:
                    subject = "Valeria – Resumen del caso"
                else:
                    subject = "Valeria – Documento generado"

                send_email_resend(
                    to_email=to_email,
                    subject=subject,
                    body=reply,
                )

                reply = reply + "\n\n📧 También te lo envié por correo."

    except Exception as e:
        logger.exception(f"[AUTO_EMAIL] failed: {e}")

    if preferred_name and preferred_name.lower() != "boss" and reply:
        reply = re.sub(r"\bBoss\b", preferred_name, reply)
        reply = re.sub(r"\bboss\b", preferred_name, reply)

    logger.info("FORGE MERGE ATTEMPT")

    if reply:
        sent = await _send_reply(update, context, reply)
    else:
        return
    try:
        insert_message(
            chat_id=chat_id,
            role="assistant",
            content=reply,
            telegram_message_id=sent.message_id,
            model_used="gpt-4.1-mini",
        )
    except Exception as e:
        logger.exception(f"Failed to insert assistant message into DB (final reply): {e}")



# --------------------------------------------------
# Daily logs commands
# --------------------------------------------------
from datetime import datetime
try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:
    ZoneInfo = None

VAL0_TZ = os.getenv("VAL0_TZ", "America/Panama")
VAL0_TZINFO = pytz.timezone(VAL0_TZ)

def _today_ymd() -> str:
    if ZoneInfo:
        try:
            return datetime.now(ZoneInfo(VAL0_TZ)).strftime("%Y-%m-%d")
        except Exception:
            pass
    return datetime.now().strftime("%Y-%m-%d")


def _facts_block_from_dict(facts: dict) -> str:
    if not facts:
        return ""
    lines = []
    for k, v in facts.items():
        lines.append(f"{k}: {v}")
    return "\n".join(lines)

def _notes_block(chat_id: int, limit: int = 10) -> str:
    try:
        rows = get_notes(chat_id, limit=limit)
    except Exception:
        rows = []
    if not rows:
        return ""
    parts = []
    for r in rows:
        txt = (r.get("content") or "").strip()
        if txt:
            parts.append(f"- {txt}")
    return "\n".join(parts)

def _daily_auto_generate(chat_id: int, date: str) -> str:
    # Pull a bigger slice than normal chat reply context
    try:
        recent = get_recent_messages(chat_id=chat_id, limit=30)
    except Exception:
        recent = []

    context_block = build_context_block(recent)

    try:
        facts = get_all_facts(chat_id=chat_id)
    except Exception:
        facts = {}

    facts_block = _facts_block_from_dict(facts)
    notes_block = _notes_block(chat_id, limit=10)

    # Semantic recall is optional; don't let it dominate
    try:
        semantic_block = _semantic_recall_block(chat_id=chat_id, query="daily summary", k=5)
    except Exception:
        semantic_block = ""

    # Respect preferred language if present
    forced_lang = None
    try:
        forced_lang = get_fact(chat_id=chat_id, fact_key="preferred_language")
        if forced_lang not in ("es", "en"):
            forced_lang = None
    except Exception:
        forced_lang = None

    # We reuse call_val_openai, but force it into "daily summary mode"
    # Output must be short + actionable.
    user_text = (
        f"Genera el DAILY del día {date} para el Boss.\n"
        "REGLAS:\n"
        "- 3 a 7 bullets máximo.\n"
        "- Enfócate en hechos, decisiones, progreso, bloqueos.\n"
        "- Termina con 'Siguiente:' y 1 a 3 acciones concretas.\n"
        "- Nada de terapia, nada de relleno.\n"
    )

    # Inject notes as extra stable context (not as user text)
    if notes_block:
        notes_block = "Notas recientes (del Boss):\n" + notes_block

    # We'll pass notes via facts_block channel to keep plumbing minimal, but label it clearly.
    merged_facts = facts_block
    if notes_block:
        merged_facts = (merged_facts + "\n\n" + notes_block).strip() if merged_facts else notes_block

    out = call_val_openai(
        chat_id=chat_id,
        user_text=user_text,
        context_block=context_block,
        facts_block=merged_facts,
        semantic_block=semantic_block,
        forced_lang=forced_lang,
    )
    return (out or "").strip()

def _generate_morning_brief_det(chat_id: int, date: str) -> str:
    """
    Deterministic 08:00 briefing.
    No LLM, no semantic recall, no chat-history reasoning.

    Sources:
    - case_events due that day
    - reminders due that day (pending or sent, if still same-day)
    """
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    from core.case_mvp import _render_due_grouped

    tz = ZoneInfo("America/Panama")

    y, m, d = map(int, date.split("-"))
    start_local = datetime(y, m, d, 0, 0, 0, tzinfo=tz)
    end_local = datetime(y, m, d, 23, 59, 59, tzinfo=tz)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    conn = _get_conn()
    cur = conn.cursor()

    items = []

    cur.execute(
        """
        SELECT c.expediente, ce.event_text, ce.deadline_date
        FROM case_events ce
        JOIN cases c ON c.id = ce.case_id
        WHERE ce.chat_id=? AND ce.deadline_date=?
        """,
        (int(chat_id), date),
    )
    event_rows = cur.fetchall() or []

    for r in event_rows:
        local_dt = datetime(y, m, d, 9, 0, 0, tzinfo=tz)
        due_ts = int(local_dt.astimezone(timezone.utc).timestamp())

        expediente = r["expediente"] if hasattr(r, "keys") else r[0]
        event_text = r["event_text"] if hasattr(r, "keys") else r[1]

        items.append(
            {
                "due_ts": due_ts,
                "title": (event_text or "(evento)").strip(),
                "case_id": str(expediente or "").strip(),
                "source": "event",
                "external_id": None,
            }
        )

    cur.execute(
        """
        SELECT id, text, due_at_utc, parent_ref
        FROM reminders
        WHERE chat_id=?
          AND status IN ('pending', 'sent')
          AND due_at_utc >= ?
          AND due_at_utc <= ?
        ORDER BY due_at_utc ASC, id ASC
        """,
        (
            int(chat_id),
            start_utc.strftime("%Y-%m-%d %H:%M:%S"),
            end_utc.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    reminder_rows = cur.fetchall() or []
    conn.close()

    for r in reminder_rows:
        rid = r["id"] if hasattr(r, "keys") else r[0]
        txt = r["text"] if hasattr(r, "keys") else r[1]
        due_at_utc = r["due_at_utc"] if hasattr(r, "keys") else r[2]
        parent_ref = r["parent_ref"] if hasattr(r, "keys") else r[3]

        txt = (txt or "").strip() or "(sin texto)"
        parent_ref = (parent_ref or "").strip()

        case_id = ""
        if parent_ref.startswith("CASE:"):
            case_id = parent_ref.split("CASE:", 1)[1].strip()

        try:
            due_dt_utc = datetime.strptime(due_at_utc, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            due_ts = int(due_dt_utc.timestamp())
        except Exception:
            due_ts = 0

        items.append(
            {
                "due_ts": due_ts,
                "title": txt,
                "case_id": case_id,
                "source": "reminder",
                "external_id": str(rid),
            }
        )

    if not items:
        return ""

    return _render_due_grouped(
        header=f"📋 Hoy ({date}):",
        items=items,
        tz=tz,
    )

def _generate_week_horizon(chat_id: int, days: int = 7) -> str:
    """
    Deterministic horizon view for the next N days.
    Used for "qué términos vencen esta semana".
    """
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo
    from core.case_mvp import _render_due_grouped

    tz = ZoneInfo("America/Panama")

    now = datetime.now(tz)
    start_local = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=tz)
    end_local = start_local + timedelta(days=days)

    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    conn = _get_conn()
    cur = conn.cursor()

    items = []

    cur.execute(
        """
        SELECT id, text, due_at_utc, parent_ref
        FROM reminders
        WHERE chat_id=?
          AND status IN ('pending','sent')
          AND due_at_utc >= ?
          AND due_at_utc <= ?
        ORDER BY due_at_utc ASC
        """,
        (
            int(chat_id),
            start_utc.strftime("%Y-%m-%d %H:%M:%S"),
            end_utc.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    rows = cur.fetchall() or []
    conn.close()

    for r in rows:
        rid = r["id"] if hasattr(r, "keys") else r[0]
        txt = r["text"] if hasattr(r, "keys") else r[1]
        due_at_utc = r["due_at_utc"] if hasattr(r, "keys") else r[2]
        parent_ref = r["parent_ref"] if hasattr(r, "keys") else r[3]

        try:
            due_dt = datetime.strptime(
                due_at_utc, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)

            due_ts = int(due_dt.timestamp())
        except Exception:
            due_ts = 0

        case_id = ""
        if parent_ref and parent_ref.startswith("CASE:"):
            case_id = parent_ref.split("CASE:", 1)[1]

        items.append(
            {
                "due_ts": due_ts,
                "title": (txt or "(sin texto)").strip(),
                "case_id": case_id,
                "source": "reminder",
                "external_id": str(rid),
            }
        )

    if not items:
        return "No hay términos ni recordatorios en los próximos 7 días."

    return _render_due_grouped(
        header="📅 Próximos 7 días",
        items=items,
        tz=tz,
    )    

def _strip_smalltalk_prefix(text: str) -> str:
    """
    Removes conversational prefixes so deterministic gates
    can match commands naturally.
    """
    import re

    t = (text or "").strip().lower()

    prefixes = [
        r"hola",
        r"oye",
        r"por favor",
        r"mi amor",
        r"amor",
        r"val",
        r"valeria",
        r"lucia",
        r"lucía",
    ]

    pattern = r"^\s*(?:" + "|".join(prefixes) + r")[,:]?\s+"

    while re.match(pattern, t):
        t = re.sub(pattern, "", t)

    return t

async def try_week_horizon(update, chat_id, text) -> bool:
    """
    Natural-language weekly horizon gate.
    Examples:
    - qué términos vencen esta semana
    - que vence esta semana
    - qué tengo esta semana
    - qué audiencias tengo esta semana
    """
    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip().lower()

    # allow natural address prefixes
    import re
    t = re.sub(r'^\s*(?:oye\s+)?(?:val|valeria)[,:]?\s+', '', t)

    # allow addressing Val naturally
    import re
    t = re.sub(r'^\s*(val|valeria)[,:]?\s+', '', t)

    patterns = [
        r"^\s*qué\s+t[eé]rminos\s+vencen\s+esta\s+semana\s*$",
        r"^\s*que\s+terminos\s+vencen\s+esta\s+semana\s*$",
        r"^\s*qué\s+vence\s+esta\s+semana\s*$",
        r"^\s*que\s+vence\s+esta\s+semana\s*$",
        r"^\s*qué\s+tengo\s+esta\s+semana\s*$",
        r"^\s*que\s+tengo\s+esta\s+semana\s*$",
        r"^\s*qué\s+audiencias\s+tengo\s+esta\s+semana\s*$",
        r"^\s*que\s+audiencias\s+tengo\s+esta\s+semana\s*$",
    ]

    import re
    if not any(re.match(p, t) for p in patterns):
        return False

    out = _generate_week_horizon(int(chat_id))
    await update.message.reply_text(out)
    return True  

async def try_due_tomorrow_natural(update, chat_id, text) -> bool:
    """
    Natural-language gate for tomorrow deadlines only.
    """
    if not update or not getattr(update, "message", None):
        return False

    import re
    import unicodedata

    t = (text or "").strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))

    task_markers = (
        "tengo que",
        "debo",
        "hay que",
        "deberia",
        "quiza",
        "quizas",
        "tal vez",
        "podria",
    )

    if any(m in t for m in task_markers):
        logger.info("[DUE_TOMORROW_GATE] skipped because task intent detected")
        return False

    patterns = [
        r"^\s*que\s+vence\s+manana\s*$",
        r"^\s*que\s+terminos\s+vencen\s+manana\s*$",
    ]

    if not any(re.match(p, t) for p in patterns):
        return False

    return await try_due_tomorrow(update, chat_id, text)


async def try_due_today_natural(update, chat_id, text) -> bool:
    """
    Natural-language gate for today's agenda.
    """
    import re
    import unicodedata

    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))

    patterns = [
        r"^que tengo hoy$",
        r"^que vence hoy$",
        r"^que audiencias tengo hoy$",
        r"^que diligencias tengo hoy$",
    ]

    for p in patterns:
        if re.match(p, t):
            return await try_due_today(update, chat_id, text)

    return False

async def try_agenda_tomorrow_natural(update, chat_id, text) -> bool:
    """
    Natural-language gate for tomorrow agenda.
    """
    import re
    import unicodedata
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))

    patterns = [
        r"^que tengo manana$",
        r"^que audiencias tengo manana$",
    ]

    for p in patterns:
        if re.match(p, t):
            tz = ZoneInfo("America/Panama")
            tomorrow = (datetime.now(tz) + timedelta(days=1)).date().isoformat()

            out = _generate_morning_brief_det(int(chat_id), tomorrow)

            if not out:
                tomorrow_dt = datetime.now(tz) + timedelta(days=1)

                weekday = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][tomorrow_dt.weekday()]
                month = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"][tomorrow_dt.month]

                pretty = f"{weekday} {tomorrow_dt.day} {month}"

                out = f"📅 Mañana ({pretty})\n\n— No tengo nada agendado —"

            await update.message.reply_text(out)
            return True

    return False

async def try_week_natural(update, chat_id, text) -> bool:
    """
    Natural-language gate for week agenda.
    """
    import re
    import unicodedata

    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))

    patterns = [
        r"^que tengo esta semana$",
        r"^que vence esta semana$",
        r"^que tengo en la semana$",
    ]

    for p in patterns:
        if re.match(p, t):
            return await try_due_range(update, chat_id, "que vence esta semana")

    return False

async def semana_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    out = _generate_week_horizon(chat_id)
    await update.message.reply_text(out)

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /daily <summary>
    /daily auto
    Saves a daily summary for today (per chat).
    """
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    parts = text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text("Usa: /daily <resumen corto del día>  |  /daily auto")
        return

    arg = parts[1].strip()
    date = _today_ymd()

    # AUTO MODE
    if arg.lower() == "auto":
        try:
            summary = _generate_morning_brief_det(chat_id=chat_id, date=date)
        except Exception as e:
            await update.message.reply_text(f"No pude generar el daily auto: {e}")
            return

        if not summary:
            await update.message.reply_text("No pude generar un daily (salió vacío).")
            return

        ok, msg = upsert_daily_log(chat_id=chat_id, date=date, summary=summary)
        if not ok:
            await update.message.reply_text(f"No pude guardar el daily: {msg}")
            return

        await update.message.reply_text(f"Listo. Guardé el daily auto de {date} ✅\n\n{summary}")
        return

    # MANUAL MODE
    summary = arg
    ok, msg = upsert_daily_log(chat_id=chat_id, date=date, summary=summary)
    if not ok:
        await update.message.reply_text(f"No pude guardar el daily: {msg}")
        return

    await update.message.reply_text(f"Listo. Guardé el daily de {date} ✅")

async def dailies_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /dailies
    Lists last N daily summaries.
    """
    chat_id = update.effective_chat.id
    rows = get_daily_logs(chat_id=chat_id, limit=7)
    if not rows:
        await update.message.reply_text("Todavía no hay dailies guardados. Usa /daily <resumen>.")
        return

    lines = []
    for r in rows:
        lines.append(f"- {r['date']}: {r['summary']}")
    await update.message.reply_text("Tus últimos dailies:\n" + "\n".join(lines))

async def dsearch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /dsearch <query>
    Search inside daily summaries.
    """
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    parts = text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text("Usa: /dsearch <palabra o frase>")
        return

    q = parts[1].strip()
    rows = search_daily_logs(chat_id=chat_id, query=q, limit=10)
    if not rows:
        await update.message.reply_text("No encontré matches en tus dailies.")
        return

    lines = []
    for r in rows:
        lines.append(f"- {r['date']}: {r['summary']}")
    await update.message.reply_text("Matches:\n" + "\n".join(lines))


# --------------------------------------------------
# Reminder Runner (JobQueue)
# --------------------------------------------------
def _reminder_poll_seconds() -> int:
    try:
        return max(10, int(os.getenv("REMINDER_POLL_SECONDS", "30")))
    except Exception:
        return 30

def _reminder_batch_limit() -> int:
    try:
        return max(1, min(50, int(os.getenv("REMINDER_BATCH_LIMIT", "20"))))
    except Exception:
        return 20

async def _reminder_tick(context: ContextTypes.DEFAULT_TYPE):
    from core.reminders import reminder_tick
    await reminder_tick(context)
        
async def evening_brief_tick(context):
    """
    Sends a short briefing for tomorrow.
    """
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo
    from core.due_merge import merge_due_items
    from core.case_mvp import _render_due_grouped

    tz = ZoneInfo("America/Panama")

    tomorrow = datetime.now(tz).date() + timedelta(days=1)
    y, m, d = tomorrow.year, tomorrow.month, tomorrow.day

    start_local = datetime(y, m, d, 0, 0, 0, tzinfo=tz)
    end_local = datetime(y, m, d, 23, 59, 59, tzinfo=tz)

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT DISTINCT chat_id FROM cases"
    )

    users = cur.fetchall()

    for u in users:

        chat_id = int(u["chat_id"])

        cur.execute(
            """
            SELECT c.expediente, ce.event_text, ce.deadline_date
            FROM case_events ce
            JOIN cases c ON c.id = ce.case_id
            WHERE ce.chat_id=? AND ce.deadline_date=?
            """,
            (chat_id, tomorrow.isoformat()),
        )

        rows = cur.fetchall()

        db_items = []

        for r in rows:
            local_dt = datetime(y, m, d, 9, 0, 0, tzinfo=tz)
            due_ts = int(local_dt.astimezone(timezone.utc).timestamp())

            db_items.append({
                "due_ts": due_ts,
                "title": (r["event_text"] or "(evento)").strip(),
                "case_id": r["expediente"],
                "source": "db",
                "external_id": None,
            })

        merged = merge_due_items(
            db_items=db_items,
            range_start_utc=start_local.astimezone(timezone.utc),
            range_end_utc=end_local.astimezone(timezone.utc),
        )

        items = merged["items"]

        if not items:
            continue

        msg = _render_due_grouped(
            header=f"🌙 Mañana ({tomorrow.isoformat()}):",
            items=items,
            tz=tz,
        )

        await context.bot.send_message(chat_id=chat_id, text=msg)

    conn.close()

async def morning_daily_tick(context):
    """
    Sends an automatic DAILY briefing at 08:00 local time.
    Read-only. Uses existing _daily_auto_generate().
    """

    date = _today_ymd()

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT chat_id FROM cases")
        users = cur.fetchall() or []
        conn.close()

        for u in users:
            chat_id = int(u["chat_id"] if hasattr(u, "keys") else u[0])

            try:
                summary = _generate_morning_brief_det(chat_id=chat_id, date=date)
            except Exception as e:
                logger.exception(f"[MORNING_DAILY] generate failed chat_id={chat_id} err={e}")
                continue

            if not summary:
                continue

            msg = f"📋 Daily ({date})\n\n{summary}"
            try:
                await context.bot.send_message(chat_id=chat_id, text=msg)
            except Exception as e:
                logger.exception(f"[MORNING_DAILY] send failed chat_id={chat_id} err={e}")

    except Exception as e:
        logger.exception(f"[MORNING_DAILY] tick failed: {e}")    

async def _handle_group_deterministic(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Group chats (chat_id < 0) are deterministic-only.
    Allowed: ping, CASE:<id>, note: <text>
    Everything else: fixed refusal.
    """
    chat = update.effective_chat
    chat_id = chat.id if chat else None
    t = (text or "").strip()
    # Capture note deterministically (same path as DMs)
    try:
        await _maybe_capture_case_note(update, chat_id, t, source="group")
    except Exception:
        pass

    low = t.lower()

    if low == "ping":
        _audit(chat_id, action="CMD_PING", entity_type="cmd", entity_id=None, payload="ping", source="group")
        return await _send_reply(update, context, "pong")

    if low.startswith("case:"):
        case_id = t.split(":", 1)[1].strip() if ":" in t else ""
        _audit(chat_id, action="CMD_CASE_BIND", entity_type="case", entity_id=case_id or None, payload=t[:200], source="group")
        return await _send_reply(update, context, "CASE bound.")

    if low.startswith("note:"):
        _audit(chat_id, action="CMD_NOTE", entity_type="note", entity_id=None, payload=t[:500], source="group")
        return await _send_reply(update, context, "Noted.")

    _audit(chat_id, action="CMD_REFUSAL", entity_type="guard", entity_id=None, payload=t[:200], source="group")
    return await _send_reply(update, context, "Group mode: commands only (ping, CASE:<id>, note: <text>).")

# --------------------------------------------------
# AUDIT LOG (deterministic trace)
# --------------------------------------------------
def _audit(chat_id: int, action: str, entity_type: str = None, entity_id: str = None, payload: str = None, source: str = None):
    try:
        from memory_store import insert_audit
        insert_audit(
            chat_id=int(chat_id),
            action=str(action),
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            source=source,
        )
    except Exception:
        # Never crash core flow for audit logging
        pass

def _extract_commitment_from_text(text: str, confidence: str = "medium") -> dict | None:
    if not text:
        return None

    import re
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    raw = text.strip()
    low = raw.lower()

    action = ""
    for verb in (
        "llamar",
        "escribir",
        "enviar",
        "revisar",
        "pagar",
        "comprar",
        "agendar",
        "programar",
        "hablar",
        "ir",
        "hacer",
        "responder",
        "buscar",
    ):
        if verb in low:
            action = verb
            break

    target = ""
    m = re.search(r"\b(?:a|con)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]+)\b", raw)
    if m:
        target = (m.group(1) or "").strip()

    tz = ZoneInfo("America/Panama")
    now_local = datetime.now(tz)

    due_date = None
    if "mañana" in low or "manana" in low:
        due_date = (now_local + timedelta(days=1)).date().isoformat()
    elif "hoy" in low:
        due_date = now_local.date().isoformat()

    if not action or not due_date:
        return None

    return {
        "raw_input": raw,
        "action": action,
        "target": target,
        "due_date": due_date,
        "confidence": confidence,
    }
    

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

# ==========================================================
# LANGUAGE RESOLUTION (single source of truth)
# ==========================================================

def _looks_like_completion(text: str) -> bool:
    if not text:
        return False

    low = text.lower().strip()

    markers = (
        "ya llamé",
        "ya llame",
        "ya lo hice",
        "ya la hice",
        "listo",
        "resuelto",
        "hecho",
        "ya quedó",
        "ya quedo",
        "ya está",
        "ya esta",
        "terminé",
        "termine",
        "ya escribí",
        "ya escribi",
        "ya hablé",
        "ya hable",
        "ya envié",
        "ya envie",
        "ya pagué",
        "ya pague",
        "ya revisé",
        "ya revise",
    )

    return any(m in low for m in markers)

async def send_telegram_reply(update, text: str, chat_id: int, action_type: str = "telegram_outbound"):
    try:
        if not update or not update.message:
            return None

        sent = await update.message.reply_text(text)

        try:
            log_action(chat_id, action_type, text)
        except Exception:
            pass

        return sent
    except Exception as e:
        logger.exception(f"[TG_OUTBOUND] failed: {e}")
        return None

# --------------------------------------------------
# Text handler
# --------------------------------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.message and update.message.text):
        return

    text = update.message.text.strip()
    raw_input = text
    # 🚨 SPAM GUARD — collapse rapid repeated intent
    try:
        norm = re.sub(r"\s+", " ", text.lower()).strip()

        now = datetime.utcnow()
        key = f"recent_text:{chat_id}:{norm}"

        last = _INLINE_NUDGE_LAST.get(key)
        if last and (now - last).total_seconds() < 2:
            return  # ignore rapid duplicate

        _INLINE_NUDGE_LAST[key] = now

    except Exception:
        pass
    chat_id = update.effective_chat.id
    tg_msg_id = getattr(update.message, "message_id", None)

    event_key = f"tg_text:{chat_id}:{tg_msg_id}:{text}"
    try:
        inserted = mark_processed_event_once(event_key, "tg_text")
        if not inserted:
            logger.info(f"[IDEMPOTENCY] skip duplicate text event: {event_key}")
            return
    except Exception as e:
        logger.exception(f"[IDEMPOTENCY] text guard failed: {e}")

    raw = (text or "").strip()
    normalized = re.sub(r"\s+", " ", raw).strip()
    lowered = normalized.lower()

    if lowered.startswith("current priority:") or lowered.startswith("priority:"):
        value = normalized.split(":", 1)[1].strip()

        try:
            upsert_fact(chat_id=chat_id, fact_key="current_priority", fact_value=value)
            log_action(chat_id, "priority_update", value)
            await send_telegram_reply(update, "Priority updated.", chat_id, "priority_reply")
        except Exception as e:
            logger.exception(f"[PRIORITY_UPDATE] failed: {e}")
            await send_telegram_reply(update, "Priority update failed.", chat_id, "priority_reply")
        return
    # Reminder action intercept
    try:
        if await handle_reminder_action_intercept(
            update, chat_id, tg_msg_id, text, normalized, send_telegram_reply
        ):
            return
    except Exception as e:
        logger.exception(f"[REMINDER_ACTION] failed: {e}")


    _audit(
        chat_id,
        action="IN_TEXT",
        entity_type="tg_msg",
        entity_id=str(tg_msg_id) if tg_msg_id is not None else None,
        payload=text[:500],
        source="group" if int(chat_id) < 0 else "dm",
    )

    # Completion loop: mark commitments as done
    try:
        if _looks_like_completion(text):
            from memory_store import close_matching_commitment

            closed = close_matching_commitment(int(chat_id), text)
            if closed:
                raw_input = closed["raw_input"] if hasattr(closed, "keys") else closed[1]
                await send_telegram_reply(update, f"✅ Perfecto. Marco esto como resuelto:\n- {raw_input}", chat_id, "completion_reply")
                log_action(chat_id, "task_closed", raw_input)
                return
    except Exception as e:
        logger.exception(f"[COMPLETION_LOOP] failed: {e}")

    # Store text input in unified memory layer
    try:
        from memory_store import insert_memory_item, classify_memory_item

        if text and not text.startswith("/"):
            bucket, summary = classify_memory_item(text, source="text")

            # --- HARD TASK OVERRIDE (critical for reliability) ---
            text_low = (text or "").lower()
            force_task = any(x in text_low for x in [
                "tengo que",
                "i need to",
                "i have to",
                "debo",
                "must",
            ])

            if force_task:
                bucket = "task"
                summary = "task_forced"

            logger.info(
                f"[MEMORY_TEST_TEXT] inserting memory for chat_id={chat_id}: "
                f"bucket={bucket} summary={summary} text={text}"
            )

            insert_memory_item(
                chat_id=int(chat_id),
                bucket=bucket,
                raw_input=text,
                summary=summary
            )

            if bucket == "task":
                from memory_store import upsert_commitment
                from datetime import datetime, timedelta

                confidence = summary.replace("task_", "")
                commitment = _extract_commitment_from_text(text, confidence=confidence)

                # --- FALLBACK: FORCE COMMITMENT IF EXTRACTION FAILS ---
                if not commitment:
                    commitment = {
                        "raw_input": text,
                        "action": text,
                        "target": None,
                        "due_date": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                        "confidence": "forced",
                    }

                upsert_commitment(
                    chat_id=int(chat_id),
                    raw_input=commitment["raw_input"],
                    action=commitment["action"],
                    target=commitment["target"],
                    due_date=commitment["due_date"],
                    confidence=commitment["confidence"],
                )
                log_action(chat_id, "task_created", commitment["raw_input"])
    except Exception as e:
        logger.exception(f"[MEMORY_TEXT_INSERT] failed: {e}")

    # ---------------------------------------
    # 1. HARD COMMANDS (ALWAYS FIRST)
    # ---------------------------------------
    if await try_set_mode(update, chat_id, text):
        return

    # ---------------------------------------
    # 2. GROUP LOGIC
    # ---------------------------------------
    if int(chat_id) < 0:
        if await _handle_group_deterministic(update, context, text):
            return
        return  # do NOT fall through to pipeline

    # ---------------------------------------
    # 3. DM DETERMINISTIC (future expansion)
    # ---------------------------------------
    # (placeholder if you add more later)

    # ---------------------------------------
    # 4. PIPELINE (LLM LAST)
    # ---------------------------------------
    await _process_text_pipeline(update, context, text)

    
# --------------------------------------------------
# Main
# --------------------------------------------------

# =========================
# VOICE MODE (Piper TTS)
# =========================
import subprocess
from pathlib import Path as _Path

def _piper_bin() -> str:
    return os.getenv("VAL0_PIPER_BIN", "/opt/val0/tools/piper/piper_bin")

def _piper_model_es() -> str:
    return os.getenv(
        "VAL0_PIPER_MODEL_ES",
        "/opt/val0/tts_models/es_AR-daniela-high/es_AR-daniela-high.onnx",
    )

def _piper_cfg_es() -> str:
    return os.getenv(
        "VAL0_PIPER_CFG_ES",
        "/opt/val0/tts_models/es_AR-daniela-high/es_AR-daniela-high.onnx.json",
    )

def _tts_enabled() -> bool:
    return os.getenv("VAL0_TTS_ENABLED", "1") == "1"

def _prepare_tts_text(text: str) -> str:
    # Remove inverted Spanish punctuation (Piper struggles with them)
    text = text.replace("¿", "").replace("¡", "")

    # Force slight separation before questions
    text = text.replace("? ", "?\n")

    # Encourage softer pause before question ending
    if text.endswith("?"):
        text = text[:-1] + "...?"

    return text.strip()

def _tts_text_sanitize(t: str) -> str:
    t = (t or "").strip()
    # keep it short-ish for driving; tweak via env
    max_chars = int(os.getenv("VAL0_TTS_MAX_CHARS", "900"))
    if len(t) > max_chars:
        t = t[:max_chars].rstrip() + "…"
    return t

def _prepare_tts_text(t: str) -> str:
    """
    Add light punctuation shaping for more natural tone.
    Also forces digit-by-digit pronunciation.
    """
    t = _tts_text_sanitize(t)

    # Force digit-by-digit pronunciation
    import re
    t = re.sub(r"\d+", lambda m: " ".join(m.group(0)), t)

    # Ensure proper pauses
    t = t.replace(". ", ".  ")
    t = t.replace(", ", ",  ")

    # Add question tone hint
    if t.endswith("?"):
        t = t[:-1] + " ?"

    return t

def tts_synthesize_es_to_wav(text: str, out_wav: str) -> None:
    """
    Synthesize Spanish TTS to WAV using Piper.
    """
    text = _prepare_tts_text(text)
    if not text:
        raise RuntimeError("empty text")
    pbin = _piper_bin()
    model = _piper_model_es()
    cfg = _piper_cfg_es()
    _Path(out_wav).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        pbin,
        "--model", model,
        "--config", cfg,
        "--length_scale", os.getenv("VAL0_PIPER_LENGTH_ES", "1.20"),
        "--output_file", out_wav,
        "--quiet",
    ]

    # Optional: select Spanish speaker id (multi-speaker models)
    spk = os.getenv("VAL0_PIPER_SPEAKER_ES", "").strip()
    if spk:
        cmd.extend(["--speaker", spk])

    
    # Optional: slow down / speed up speech (default 1.25)
    length_scale = os.getenv("VAL0_PIPER_LENGTH_SCALE", "1.25").strip()
    if length_scale:
        cmd.extend(["--length_scale", length_scale])
# Piper reads stdin
    proc = subprocess.run(cmd, input=text.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"piper failed rc={proc.returncode} err={proc.stderr.decode('utf-8','ignore')[:300]}")

# =========================
# Telegram Chat Action Keepalive
# =========================
async def _send_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, reply: str):
    """
    Central reply sender.
    - If voice mode ON and TTS enabled → send voice
    - Else → send text
    """

    chat = update.effective_chat
    chat_id = chat.id if chat else None
    msg = update.effective_message

    def _audit_out(text: str):
        try:
            _audit(
                int(chat_id) if chat_id is not None else 0,
                action="OUT_TEXT",
                entity_type="tg_msg",
                entity_id=str(getattr(msg, "message_id", None)) if msg else None,
                payload=(text or "")[:500],
                source="group" if (chat_id is not None and int(chat_id) < 0) else "dm",
            )
        except Exception:
            pass

    if chat_id is None or msg is None:
        _audit_out(reply)
        return await update.message.reply_text(reply)

    try:
        from memory_store import get_chat_voice_enabled
    except Exception:
        get_chat_voice_enabled = None

    voice_on = False
    try:
        if get_chat_voice_enabled:
            voice_on = bool(get_chat_voice_enabled(int(chat_id)))
    except Exception:
        voice_on = False

    # Voice path
    if voice_on and _tts_enabled():
        import os, time, subprocess, re

        def _looks_spanish(s: str) -> bool:
            s = (s or "").strip()
            if not s:
                return False
            # If it has Spanish punctuation/accents, assume Spanish
            if any(ch in s for ch in "¿¡áéíóúÁÉÍÓÚñÑ"):
                return True
            # If it's mostly ASCII letters and contains common English words, treat as non-Spanish
            low = s.lower()
            if any(w in low.split() for w in ("hello", "hi", "thanks", "please", "what", "why", "who", "when", "where")):
                return False
            # Otherwise: allow it (numbers/short tokens are fine)
            return True

        try:
            # If message is likely English/non-Spanish: do NOT TTS (prevents gibberish)
            if not _looks_spanish(reply):
                _audit_out(reply)
                return await msg.reply_text(reply)
            tmp_dir = os.getenv("VAL0_TMP_DIR", "/opt/val0/tmp")
            os.makedirs(tmp_dir, exist_ok=True)

            # Light punctuation tuning so Piper breathes a bit
            t = (reply or "").strip()
            # --- Case/expediente digits: force digit-by-digit for clarity ---
            # Converts "Caso 123456" -> "Caso 1 2 3 4 5 6"
            # Also handles "Expediente 123 del 2026" -> "Expediente 1 2 3 del 2 0 2 6"
            def _spell_digits(s: str) -> str:
                s = str(s or "")
                return " ".join(list(s))

            # Only target numbers that follow case keywords (Spanish)
            t = re.sub(
                r"(?i)\b(caso|expediente)\s+(\d{3,})\b",
                lambda m: f"{m.group(1)} {_spell_digits(m.group(2))}",
                t,
            )

            # Also target patterns like "del 2026"
            t = re.sub(
                r"(?i)\bdel\s+(\d{4,})\b",
                lambda m: f"del {_spell_digits(m.group(1))}",
                t,
            )
            t = t.replace(" punto ", ". ")
            t = t.replace(" ,", ",")
            t = t.replace(" .", ".")
            # Tiny pause hints (Piper reacts better to commas/periods than "...")
            t = t.replace("...", ".")
            # If it ends with a question-ish word and no '?', add it.
            if t and (t.lower().endswith("bien") or t.lower().endswith("verdad") or t.lower().endswith("cierto")) and not t.endswith("?"):
                t = t + "?"

            wav_path = os.path.join(tmp_dir, f"tts_{chat_id}_{int(time.time())}.wav")
            ogg_path = os.path.join(tmp_dir, f"tts_{chat_id}_{int(time.time())}.ogg")

            # Keep Telegram “recording voice…” alive until we finish sending the VN
            done_evt = asyncio.Event()
            keepalive_task = asyncio.create_task(
                _chat_action_keepalive(context, chat_id, ChatAction.RECORD_VOICE, done_evt, every=2.5)
            )

            try:
                # Synthesize WAV
                await asyncio.to_thread(tts_synthesize_es_to_wav, t, wav_path)

                # Convert to OGG/Opus for Telegram voice messages
                ff = ["ffmpeg", "-y", "-loglevel", "quiet", "-i", wav_path, "-c:a", "libopus", ogg_path]
                await asyncio.to_thread(subprocess.run, ff, check=True)

                with open(ogg_path, "rb") as vf:
                    _audit_out(reply)
                    sent = await context.bot.send_voice(chat_id=chat_id, voice=vf)

                return sent

            finally:
                # Stop keepalive ASAP
                done_evt.set()
                try:
                    keepalive_task.cancel()
                except Exception:
                    pass

                # cleanup
                for p in (ogg_path, wav_path):
                    try:
                        if os.path.exists(p):
                            os.remove(p)
                    except Exception:
                        pass

        except Exception as e:
            logger.exception(f"TTS failed, falling back to text: {e}")
            _audit_out(reply)
            return await msg.reply_text(reply)

    # TEXT PATH
    _audit_out(reply)
    return await msg.reply_text(reply)
async def voice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    from memory_store import get_chat_voice_enabled, set_chat_voice_enabled
    """
    /voice on|off|status
    """
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return

    parts = (update.message.text or "").strip().split()
    mode = parts[1].lower() if len(parts) >= 2 else "status"

    if mode in ("on", "1", "yes", "enable", "enabled"):
        set_chat_voice_enabled(int(chat_id), True)
        await update.message.reply_text("🎧 Voice mode: ON. Te respondo con audio cuando pueda.")
        return

    if mode in ("off", "0", "no", "disable", "disabled"):
        set_chat_voice_enabled(int(chat_id), False)
        await update.message.reply_text("🛑 Voice mode: OFF. Vuelvo a texto normal.")
        return

    # status/default
    on = get_chat_voice_enabled(int(chat_id))
    await update.message.reply_text(f"🎧 Voice mode: {'ON' if on else 'OFF'}")

async def handle_mem(update, context):
    try:
        from memory_store import fetch_recent_memory

        chat_id = update.effective_chat.id
        rows = fetch_recent_memory(chat_id, limit=5)

        if not rows:
            await update.message.reply_text("No tengo memoria reciente, boss.")
            return

        lines = []
        for r in rows:
            raw = r[2] if not hasattr(r, "keys") else r["raw_input"]
            lines.append(f"- {raw}")

        await update.message.reply_text(
            "🧠 Memoria reciente:\n" + "\n".join(lines)
        )

    except Exception as e:
        logger.exception(f"[MEM_FETCH] failed: {e}")
        await update.message.reply_text("Error leyendo memoria.")

async def handle_remember(update, context):
    try:
        from memory_store import search_memory

        chat_id = update.effective_chat.id
        args = context.args or []

        if not args:
            await update.message.reply_text("Uso: /remember <palabra>")
            return

        keyword = " ".join(args).strip()
        rows = search_memory(chat_id, keyword, limit=5)

        if not rows:
            await update.message.reply_text(f"No encontré nada sobre: {keyword}")
            return

        lines = []
        for r in rows:
            raw = r[2] if not hasattr(r, "keys") else r["raw_input"]
            lines.append(f"- {raw}")

        await update.message.reply_text(
            f"🧠 Recuerdos sobre '{keyword}':\n" + "\n".join(lines)
        )

    except Exception as e:
        logger.exception(f"[REMEMBER_CMD] failed: {e}")
        await update.message.reply_text("Error buscando memoria.")

from datetime import datetime
from zoneinfo import ZoneInfo

def _time_pressure_state(due_date: str):
    try:
        tz = ZoneInfo("America/Panama")
        now = datetime.now(tz)

        today_str = now.date().isoformat()

        if not due_date:
            return "none"

        if due_date < today_str:
            return "overdue"

        if due_date == today_str:
            hour = now.hour

            # crude windows (we refine later)
            if hour < 12:
                return "early"
            elif hour < 18:
                return "mid"
            else:
                return "late"

        return "future"

    except Exception:
        return "none"

def _human_due_label(due_date: str) -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    if not due_date:
        return ""

    try:
        tz = ZoneInfo("America/Panama")
        today = datetime.now(tz).date()
        d = datetime.strptime(due_date, "%Y-%m-%d").date()

        delta = (d - today).days

        if delta == 0:
            return "hoy"
        elif delta == 1:
            return "mañana"
        elif delta == -1:
            return "ayer"
        elif delta < 0:
            return f"hace {abs(delta)} días"
        elif delta <= 7:
            return f"en {delta} días"
        else:
            return d.strftime("%d %b")  # fallback

    except Exception:
        return due_date    

def _format_context_snapshot(snapshot: dict) -> str:
    lines = []
    lines.append("🧠 CONTEXT SNAPSHOT\n")

    # Commitments
    lines.append("OPEN TASKS:")
    if snapshot["commitments"]:
        for r in snapshot["commitments"]:
            row = dict(r) if hasattr(r, "keys") else r
            act = row["action"] if isinstance(row, dict) else row[0]
            tgt = row["target"] if isinstance(row, dict) else row[1]
            due = row["due_date"] if isinstance(row, dict) else row[2]
            lines.append(f"- {act} {tgt} ({due})")
    else:
        lines.append("- none")

    # Signals
    lines.append("\nRECENT SIGNALS:")
    if snapshot["signals"]:
        for r in snapshot["signals"]:
            text = r["raw_input"] if hasattr(r, "keys") else r[0]
            lines.append(f"- {text}")
    else:
        lines.append("- none")

    return "\n".join(lines)

async def context_cmd(update, context):
    if not update or not update.effective_chat or not update.message:
        return

    chat_id = update.effective_chat.id

    try:
        ensure_current_priority(chat_id)
    except Exception:
        pass

    try:
        seed_build_status(chat_id)
    except Exception:
        pass

    try:
        snapshot = build_context_snapshot(
            chat_id=chat_id,
            build_status_lines=get_build_status_lines(chat_id),
            priority_lines=get_current_priority_lines(chat_id),
        )
    except Exception as e:
        snapshot = f"🧠 CONTEXT SNAPSHOT\n\nERROR: {str(e)}"

    try:
        await send_telegram_reply(update, snapshot, chat_id, "context_reply")
    except Exception:
        pass            

async def status_cmd(update, context):
    try:
        from memory_store import _get_conn

        chat_id = update.effective_chat.id
        conn = _get_conn()
        cur = conn.cursor()

        # --- OPEN TASK COUNT ---
        open_tasks = 0
        try:
            row = cur.execute(
                """
                SELECT COUNT(*)
                FROM commitments
                WHERE chat_id=? AND status='open'
                """,
                (chat_id,),
            ).fetchone()
            if row:
                open_tasks = int(row[0])
        except Exception:
            open_tasks = 0

        # --- OPEN TASK NAMES (top 3) ---
        open_task_lines = []
        try:
            rows = cur.execute(
                """
                SELECT raw_input, due_date
                FROM commitments
                WHERE chat_id=? AND status='open'
                ORDER BY id DESC
                LIMIT 3
                """,
                (chat_id,),
            ).fetchall()
            for r in rows:
                raw = str(r[0] or "").strip()
                due = str(r[1] or "").strip() if len(r) > 1 and r[1] else ""
                if not raw:
                    continue
                if due:
                    open_task_lines.append(f"- {raw} ({due})")
                else:
                    open_task_lines.append(f"- {raw}")
        except Exception:
            open_task_lines = []

        # --- LAST ACTION ---
        last_action = "-"
        try:
            row = cur.execute(
                """
                SELECT action_type, payload
                FROM action_logs
                WHERE chat_id=?
                  AND action_type != 'status_reply'
                ORDER BY id DESC
                LIMIT 1
                """,
                (chat_id,),
            ).fetchone()
            if row:
                payload = str(row[1] or "").replace("\n", " ").strip()
                if len(payload) > 140:
                    payload = payload[:137] + "..."
                last_action = f"{row[0]}: {payload}"
        except Exception:
            pass

        # --- LAST SURFACED COMMITMENT ---
        last_surfaced = "-"
        try:
            row = cur.execute(
                """
                SELECT fact_value
                FROM user_facts
                WHERE chat_id=? AND fact_key='last_surface_commitment_id'
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (chat_id,),
            ).fetchone()
            if row and row[0]:
                cid = int(row[0])
                row2 = cur.execute(
                    """
                    SELECT raw_input
                    FROM commitments
                    WHERE id=? AND chat_id=?
                    LIMIT 1
                    """,
                    (cid, chat_id),
                ).fetchone()
                if row2 and row2[0]:
                    last_surfaced = str(row2[0]).strip()
        except Exception:
            pass

        # --- LAST VERIFICATION RESULT ---
        last_verification = "-"
        try:
            row = cur.execute(
                """
                SELECT action_type, payload, status
                FROM action_logs
                WHERE chat_id=?
                  AND (
                    action_type LIKE 'reminder_%'
                    OR action_type LIKE '%verify%'
                  )
                ORDER BY id DESC
                LIMIT 1
                """,
                (chat_id,),
            ).fetchone()
            if row:
                payload = str(row[1] or "").replace("\n", " ").strip()
                if len(payload) > 120:
                    payload = payload[:117] + "..."
                last_verification = f"{row[0]} [{row[2]}]: {payload}"
        except Exception:
            pass

        # --- PRIORITY ---
        priority = "-"
        try:
            priority_lines = get_current_priority_lines(chat_id)
            if priority_lines:
                priority = " | ".join(x.lstrip("- ").strip() for x in priority_lines if x.strip())
        except Exception:
            pass

        conn.close()

        # --- BUILD OUTPUT ---
        lines = []
        lines.append("PX01 STATUS")
        lines.append("")
        lines.append(f"OPEN TASKS: {open_tasks}")
        if open_task_lines:
            lines.extend(open_task_lines)
        lines.append("")
        lines.append(f"LAST ACTION: {last_action}")
        lines.append("")
        lines.append(f"LAST SURFACED: {last_surfaced}")
        lines.append("")
        lines.append(f"LAST VERIFICATION: {last_verification}")
        lines.append("")
        lines.append(f"CURRENT PRIORITY: {priority}")
        lines.append("")
        lines.append("SYSTEM:")
        lines.append("- memory: ok")
        lines.append("- logging: ok")
        lines.append("- outbound: ok")

        msg = "\n".join(lines)

        await send_telegram_reply(update, msg, chat_id, "status_reply")

    except Exception as e:
        logger.exception(f"[STATUS_CMD] failed: {e}")
        try:
            await send_telegram_reply(update, "Status failed.", update.effective_chat.id, "status_reply")
        except Exception:
            pass

async def handoff_cmd(update, context):
    if not update or not update.effective_chat or not update.message:
        return

    chat_id = update.effective_chat.id

    try:
        ensure_current_priority(chat_id)
    except Exception:
        pass

    try:
        seed_build_status(chat_id)
    except Exception:
        pass

    try:
        snapshot = build_context_snapshot(
            chat_id=chat_id,
            build_status_lines=get_build_status_lines(chat_id),
            priority_lines=get_current_priority_lines(chat_id),
        )
        handoff = (
            "We are continuing PX01 Val0 development.\n\n"
            "Live system snapshot:\n\n"
            f"{snapshot}\n\n"
            "Act as Val in operator mode.\n"
            "Give exact code instructions only.\n\n"
            "continue from here"
        )
    except Exception as e:
        handoff = f"We are continuing PX01 Val0 development.\n\nERROR: {str(e)}"

    try:
        await send_telegram_reply(update, handoff, chat_id, "handoff_reply")
    except Exception:
        pass


def _human_due_label(due_date: str) -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    if not due_date:
        return ""

    try:
        tz = ZoneInfo("America/Panama")
        today = datetime.now(tz).date()
        d = datetime.strptime(due_date, "%Y-%m-%d").date()

        delta = (d - today).days

        if delta == 0:
            return "hoy"
        elif delta == 1:
            return "mañana"
        elif delta == -1:
            return "ayer"
        elif delta < 0:
            return f"hace {abs(delta)} días"
        elif delta <= 7:
            return f"en {delta} días"
        else:
            return d.strftime("%d %b")

    except Exception:
        return due_date

def _pattern_window_label(pattern: str) -> str:
    if pattern == "midday":
        return "al mediodía"
    if pattern == "night":
        return "en la noche"
    return ""

def _window_status(now_hour: int, windows: dict) -> dict:
    has_midday = windows.get("has_midday", False)
    has_night = windows.get("has_night", False)

    return {
        "missed_midday": bool(has_midday and now_hour >= 15),
        "night_available": bool(has_night and now_hour < 23),
        "midday_available": bool(has_midday and now_hour < 15),
    }

def _build_operator_state_packet(
    chat_id: int,
    raw_input: str,
    action: str,
    target: str,
    due_date: str,
    confidence: str,
):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from memory_store import count_memory_hits, infer_simple_time_pattern, infer_time_windows

    who = target or "eso"
    act = action or "hacerlo"
    human_due = _human_due_label(due_date)
    time_state = _time_pressure_state(due_date)

    if action == "llamar" and target:
        action_phrase = f"llamar a {who}"
    elif action == "escribir" and target:
        action_phrase = f"escribirle a {who}"
    elif action == "hablar" and target:
        action_phrase = f"hablar con {who}"
    elif target:
        action_phrase = f"{act} {who}"
    else:
        action_phrase = act

    hit_basis = target or action or ""
    repeat_count = count_memory_hits(chat_id, hit_basis, limit=50) if hit_basis else 0

    if repeat_count >= 4:
        pressure = "high"
    elif repeat_count >= 2:
        pressure = "medium"
    else:
        pressure = "low"

    pattern = infer_simple_time_pattern(chat_id, target if target else "", action=action, limit=20) if target else ""
    pattern_label = _pattern_window_label(pattern)

    tz = ZoneInfo("America/Panama")
    now_local = datetime.now(tz)
    now_hour = now_local.hour

    windows = infer_time_windows(chat_id, target if target else "", action=action, limit=20) if target else {}
    window_state = _window_status(now_hour, windows)

    packet = {
        "raw_input": raw_input or "",
        "action": action or "",
        "target": target or "",
        "who": who,
        "action_phrase": action_phrase,
        "due_date": due_date or "",
        "human_due": human_due,
        "confidence": confidence or "medium",
        "repeat_count": repeat_count,
        "pressure": pressure,
        "pattern": pattern,
        "pattern_label": pattern_label,
        "has_midday": windows.get("has_midday", False),
        "has_night": windows.get("has_night", False),
        "missed_midday": window_state.get("missed_midday", False),
        "night_available": window_state.get("night_available", False),
        "midday_available": window_state.get("midday_available", False),
        "now_hour": now_hour,
    }

    return packet

def _render_operator_nudge(packet: dict) -> str:
    import random

    who = packet.get("who") or "eso"
    action_phrase = packet.get("action_phrase") or "hacerlo"
    human_due = packet.get("human_due") or ""
    confidence = packet.get("confidence") or "medium"
    pressure = packet.get("pressure") or "low"
    pattern_label = packet.get("pattern_label") or ""
    missed_midday = bool(packet.get("missed_midday"))
    night_available = bool(packet.get("night_available"))

    if confidence == "high":
        if pressure == "high":
            if missed_midday and night_available:
                options = [
                    f"⏰ No lo resolviste al mediodía, que es una de tus ventanas normales con {who}. Te queda la noche. No lo dejes correr otra vez.",
                    f"⏰ Se te fue la ventana del mediodía con {who}. Todavía estás a tiempo de cerrarlo en la noche. Hazlo.",
                    f"⏰ Ya perdiste una de tus horas típicas con {who}. No dejes que también se te vaya la noche.",
                ]
            elif pattern_label:
                options = [
                    f"⏰ Otra vez {who}. Normalmente esto lo resuelves {pattern_label}. ¿Qué pasó esta vez?",
                    f"⏰ Lo de {who} ya te suele caer {pattern_label} y sigue abierto. ¿Lo cierras o lo movemos?",
                    f"⏰ Esto con {who} ya tiene patrón. Si ya se te fue la ventana {pattern_label}, no dejes que se te arrastre más.",
                ]
            else:
                options = [
                    f"⏰ Otra vez {who}. Esto ya se está arrastrando. ¿Lo cierras {human_due} o qué?",
                    f"⏰ {who} sigue abierto y ya van varias vueltas con esto. ¿Lo resolviste o sigue colgado?",
                    f"⏰ Esto con {who} ya es patrón. Si no lo cierras {human_due}, te va a seguir pesando.",
                ]
        elif pressure == "medium":
            options = [
                f"⏰ {who} sigue pendiente. Dijiste que lo resolvías {human_due}. ¿Qué pasó?",
                f"⏰ Oye… lo de {action_phrase} {human_due} sigue vivo. ¿Lo hiciste o lo movemos?",
                f"⏰ No dejes que esto se arrastre. {action_phrase} era {human_due}. ¿Ya quedó?",
            ]
        else:
            options = [
                f"⏰ Oye… dijiste que ibas a {action_phrase} {human_due}. ¿Lo hiciste o lo movemos?",
                f"⏰ Esto sigue abierto: {action_phrase} {human_due}. ¿Lo cerraste o sigue vivo?",
            ]
    elif confidence == "medium":
        if pressure == "high":
            options = [
                f"⏰ Esto con {who} ya ha salido varias veces. ¿Sigue en pie o lo redefinimos?",
                f"⏰ Ya van varias vueltas con {who}. ¿Lo vas a mover de verdad o lo bajamos?",
            ]
        elif pressure == "medium":
            options = [
                f"⏰ Tenías pendiente {action_phrase} {human_due}. ¿Sigue en pie?",
                f"⏰ Lo de {action_phrase} {human_due} estaba sobre la mesa. ¿Todavía va?",
                f"⏰ Habías dejado {action_phrase} {human_due}. ¿Qué hacemos con eso?",
            ]
        else:
            options = [
                f"⏰ Solo revisando: {action_phrase} {human_due}. ¿Lo mantienes o lo movemos?",
                f"⏰ Quedó pendiente {action_phrase} {human_due}. ¿Sigue en pie?",
            ]
    else:
        if pressure == "high":
            options = [
                f"⏰ Esto ya lleva rato rondando con {who}. ¿Lo retomamos o lo soltamos de una vez?",
                f"⏰ {who} vuelve a salir. ¿Esto va en serio o mejor lo dejamos caer?",
            ]
        elif pressure == "medium":
            options = [
                f"⏰ Lo de {action_phrase} {human_due}… ¿lo retomamos o lo soltamos?",
                f"⏰ Eso de {action_phrase} {human_due} quedó rondando. ¿Sigue vivo?",
            ]
        else:
            options = [
                f"⏰ Te lo dejo aquí por si acaso: {action_phrase} {human_due}. ¿Lo quieres retomar?",
                f"⏰ Quedó flotando lo de {action_phrase} {human_due}. ¿Lo dejamos caer o lo cerramos?",
            ]

    return random.choice(options)

async def handle_followup_test(update, context):
    try:
        await operator_followup_tick(context)
        await update.message.reply_text("✅ Follow-up tick ejecutado.")
    except Exception as e:
        logger.exception(f"[FOLLOWUP_TEST] failed: {e}")
        await update.message.reply_text(f"❌ Follow-up test failed: {e}")

async def handle_statepacket(update, context):
    try:
        from memory_store import _get_conn

        conn = _get_conn()
        cur = conn.cursor()

        rows = cur.execute("""
        SELECT id, chat_id, raw_input, action, target, due_date, confidence
        FROM commitments
        WHERE status = 'open'
        ORDER BY id DESC
        LIMIT 10
        """).fetchall()

        conn.close()

        target_row = None
        for r in rows:
            row = dict(r) if hasattr(r, "keys") else r
            row_chat_id = row["chat_id"] if isinstance(row, dict) else row[1]
            if int(row_chat_id) == int(chat_id):
                target_row = row
                break

        if not target_row:
            await update.message.reply_text("No hay commitments abiertos para este chat.")
            return

        raw_input = target_row["raw_input"] if isinstance(target_row, dict) else target_row[2]
        action = target_row["action"] if isinstance(target_row, dict) else target_row[3]
        target = target_row["target"] if isinstance(target_row, dict) else target_row[4]
        due_date = target_row["due_date"] if isinstance(target_row, dict) else target_row[5]
        confidence = target_row["confidence"] if isinstance(target_row, dict) else target_row[6]

        packet = _build_operator_state_packet(
            chat_id=chat_id,
            raw_input=raw_input,
            action=action,
            target=target,
            due_date=due_date,
            confidence=confidence,
        )

        lines = ["OPERATOR STATE PACKET", ""]
        for k, v in packet.items():
            lines.append(f"{k}: {v}")

        out = "\n".join(lines)
        await update.message.reply_text(f"```text\n{out}\n```", parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"[STATE_PACKET_CMD] failed: {e}")
        await update.message.reply_text(f"❌ state packet error: {e}")


def main():
    init_db()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).defaults(Defaults(parse_mode=None)).build()
    interval = _reminder_poll_seconds()
    # --- Reminder Runner: schedule exactly once (no duplicates) ---
    REMINDER_JOB_NAME = "reminder_tick"

    # Remove any existing reminder job(s) with the same name (safe across versions)
    try:
        existing = app.job_queue.get_jobs_by_name(REMINDER_JOB_NAME)
        for j in existing:
          j.schedule_removal()
    except Exception:
        # Older versions may not support get_jobs_by_name; ignore and just schedule
        pass

#    app.job_queue.run_repeating(
#        operator_followup_tick,
#        interval=3600,
#        first=20,
#        name="OPERATOR_FOLLOWUP_JOB",
#    )

    app.job_queue.run_daily(
        evening_brief_tick,
        time=dt_time(hour=21, minute=0, tzinfo=pytz.timezone(VAL0_TZ)),
        name="EVENING_BRIEF_JOB",
    )
    
    app.job_queue.run_daily(
        morning_daily_tick,
        time=dt_time(hour=8, minute=0, tzinfo=pytz.timezone(VAL0_TZ)),
        name="MORNING_DAILY_JOB",
    )


    app.add_error_handler(_error_handler)



    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ops", ops_cmd))
    app.add_handler(CommandHandler("health", health_cmd))
    app.add_handler(CommandHandler("reminders", reminders_cmd))
    #app.add_handler(CommandHandler("cancel", rmd_cmd))
    app.add_handler(CommandHandler("rmd", rmd_cmd))
    app.add_handler(CommandHandler("memory", memory_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("note", note_cmd))
    app.add_handler(CommandHandler("notes", notes_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("context", context_cmd))
    app.add_handler(CommandHandler("status", status_cmd))

    app.add_handler(CommandHandler("handoff", handoff_cmd))
    app.add_handler(CommandHandler("semana", semana_cmd))
    app.add_handler(CommandHandler("dailies", dailies_cmd))
    app.add_handler(CommandHandler("dsearch", dsearch_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("place", place_cmd))
    app.add_handler(CommandHandler("followuptest", handle_followup_test))
    app.add_handler(CommandHandler("statepacket", handle_statepacket))
    # HOTFIX: temporarily disabled until voice_cmd is defined correctly
    app.add_handler(CommandHandler("voice", voice_cmd))
    app.add_handler(CommandHandler("mem", handle_mem))
    app.add_handler(CommandHandler("remember", handle_remember))


    app.add_handler(CommandHandler("sremember", sremember_cmd))
    app.add_handler(CommandHandler("ssearch", ssearch_cmd))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    app.run_polling(drop_pending_updates=True)




# =========================
# OPS COMMANDS: /ops /health /reminders
# =========================
from datetime import datetime
from memory_store import reminder_stats, list_reminders, cancel_reminder
from memory_store import get_chat_voice_enabled, set_chat_voice_enabled


# tick telemetry for /health
_VAL0_LAST_TICK_TS = None
_VAL0_LAST_TICK_DUE = None

def _now_local_str() -> str:
    # Keep it dependency-free: show UTC + TZ label
    tz = os.getenv("VAL0_TZ", "America/Panama")
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC") + f" (TZ={tz})"

async def ops_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stats = reminder_stats()
        interval = _reminder_poll_seconds()
        db_path = os.getenv("VAL0_DB_PATH", "")
        gcal = os.getenv("VAL0_GCAL_ENABLED", "0")
        include_unbound = os.getenv("VAL0_GCAL_INCLUDE_UNBOUND", "0")

        lines = [
            "OPS",
            f"- time: {_now_local_str()}",
            f"- db_path: {db_path}",
            f"- gcal_enabled: {gcal}  include_unbound: {include_unbound}",
            f"- reminder_poll_seconds: {interval}",
            f"- reminders: total={stats.get('total')} pending={stats.get('pending')} due_now={stats.get('due_now')} sending={stats.get('sending')} sent={stats.get('sent')}",
        ]
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"OPS\n- time: {_now_local_str()}\n- error: {e}")

async def reminders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Usage: /reminders [N]
    n = 25
    try:
        parts = (update.message.text or "").strip().split()
        if len(parts) >= 2:
            n = int(parts[1])
    except Exception:
        n = 25
    n = max(1, min(50, n))

    try:
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is None:
            await update.message.reply_text("REMINDERS\n- error: no chat_id")
            return

        from memory_store import list_reminders_for_chat
        rows = list_reminders_for_chat(int(chat_id), statuses=["pending", "sending"], limit=n)

        if not rows:
            await update.message.reply_text("REMINDERS\n- none (pending/sending)")
            return

        lines = ["REMINDERS (pending/sending)"]
        for r in rows:
            rid = r.get("id")
            due = r.get("due_at_utc")
            st = r.get("status")
            txt = (r.get("text") or "").replace("\n", " ").strip()
            if len(txt) > 60:
                txt = txt[:60] + "…"
            lines.append(f"- #{rid} | {due} | {st} | {txt}")
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"REMINDERS\n- error: {e}")

async def rmd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel a reminder.
    Usage:
      /rmd <id>
    """
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return

    parts = (update.message.text or "").strip().split()
    if len(parts) < 2:
        await update.message.reply_text("Uso: /rmd <id>  (ej: /rmd 27)")
        return

    try:
        rid = int(parts[1])
    except Exception:
        await update.message.reply_text("Ese id no parece número. Ej: /rmd 27")
        return

    try:
        from memory_store import cancel_reminder
        ok = bool(cancel_reminder(int(chat_id), int(rid)))
        if ok:
            _audit(
                int(chat_id),
                action="CMD_REMINDER_CANCEL",
                entity_type="reminder",
                entity_id=str(rid),
                payload=f"rid={rid}",
                source="dm" if int(chat_id) >= 0 else "group",
            )
            await update.message.reply_text(f"Listo. Cancelado #{rid}.")
        else:
            await update.message.reply_text("No lo pude cancelar. Puede que no exista, no sea tuyo, o ya esté enviado.")
    except Exception as e:
        logger.exception(f"rmd_cmd failed: {e}")
        await update.message.reply_text("Se cayó el cancel. Intenta otra vez.")


async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interval = _reminder_poll_seconds()
    db_path = os.getenv("VAL0_DB_PATH", "")
    key_file = os.getenv("VAL0_DB_KEY_FILE", "")

    # last tick signals (set in _reminder_tick)
    global _VAL0_LAST_TICK_TS, _VAL0_LAST_TICK_DUE
    last_ts = _VAL0_LAST_TICK_TS if isinstance(_VAL0_LAST_TICK_TS, int) else None
    age = (int(time.time()) - last_ts) if last_ts else None

    db_ok = True
    db_err = ""
    stats = {}
    try:
        stats = reminder_stats()
    except Exception as e:
        db_ok = False
        db_err = str(e)

    lines = [
        "HEALTH",
        f"- time: {_now_local_str()}",
        f"- db_path: {db_path}",
        f"- db_key_file: {key_file}",
        f"- reminder_poll_seconds: {interval}",
        f"- db_ok: {db_ok}" + (f" ({db_err})" if db_err else ""),
    ]
    if stats:
        lines.append(
            f"- reminders: total={stats.get('total')} pending={stats.get('pending')} due_now={stats.get('due_now')} sending={stats.get('sending')} sent={stats.get('sent')}"
        )
    if age is None:
        lines.append("- last_tick: unknown (no tick yet)")
    else:
        lines.append(f"- last_tick_age_seconds: {age}  last_tick_due: {_VAL0_LAST_TICK_DUE}")

    await update.message.reply_text("\n".join(lines))

if __name__ == "__main__":
    main()