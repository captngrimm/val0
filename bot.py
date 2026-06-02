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
from core.client_identity import KAREN_CHAT_ID, resolve_client_id, client_vocative
from core.client_contacts import get_email_contact
from core.client_profiles import (
    WORKFLOW_DAILY_OPERATOR,
    WORKFLOW_DOCUMENTS,
    WORKFLOW_GROCERIES,
    WORKFLOW_LEGAL_CASE,
    WORKFLOW_TIMELINE,
    get_client_profile_for_chat,
    render_workflow_not_enabled_message,
    require_workflow_access,
)
from core.founder_intro import (
    INTENT_UNKNOWN as FOUNDER_INTRO_UNKNOWN,
    normalize_founder_intro_intent,
    render_founder_intro_response,
)
from core.conversation_router import classify_deterministic_intent, normalize_message
from core.intent_router_v2 import classify_intent_shadow
from core.intent_router_v2_observer import (
    record_actual_intent,
    record_predicted_intent,
    render_intent_observation,
)
from core.case_timeline import (
    build_timeline_events_from_case_notes,
    safe_timeline_event_summary,
    timeline_events_for_year,
)
from core.document_extraction_readiness import document_capability_summary
from core.document_registry import document_record_from_vfms_metadata
from core.daily_operator import (
    build_daily_operator_snapshot_from_sources,
    filter_today_items,
    render_daily_operator_compact,
    safe_daily_operator_summary,
)
from core.karen_day0_routes import (
    ROUTE_AGENDA_TOMORROW,
    ROUTE_CAPABILITY_WEEK,
    ROUTE_DOCUMENT_INVENTORY,
    ROUTE_FINCA_FACTS,
    ROUTE_NEXT_ACTION,
    classify_karen_day0_route,
)
from core.response_envelope import (
    ResponseType,
    StyleMode,
    create_response_envelope,
    render_polished_fixture_response,
)
from core.pending_actions import (
    PendingAction,
    ConfirmationDecision,
    classify_confirmation_reply,
    create_pending_action,
    get_pending_action,
    clear_pending_action,
)
from core.bug_report import (
    bug_cmd,
    feedback_cmd,
    idea_cmd,
    reports_cmd,
    cancelreport_cmd,
    handle_pending_bug_report,
    get_pending_bug_report_text,
    _PENDING_BUG_REPORT,
)

from core.context_snapshot import build_context_snapshot
from core.karen_interrogator import interrogate_cmd, maybe_handle_karen_interrogator
from core.karen_plan_state import karen_plan_cmd, maybe_handle_karen_plan_query
from core.karen_lawyer_questions import karen_lawyer_questions_cmd, maybe_handle_karen_lawyer_questions
from core.karen_case_status import karen_case_status_cmd, maybe_handle_karen_case_status
from core.karen_lawyer_package import karen_lawyer_package_cmd, maybe_handle_karen_lawyer_package
from core.karen_meeting_prep import looks_like_karen_meeting_prep_request, render_karen_meeting_prep_checklist
from core.karen_next_action import maybe_handle_pending_next_action, karen_next_action_callback, maybe_handle_document_inventory, start_document_inventory
from core.document_inventory_queries import maybe_handle_document_query
from core.document_semantic_queries import maybe_handle_document_semantic_query
from core.document_summary_queries import (
    maybe_handle_latest_document_status_query,
    maybe_handle_document_alias_save_query,
    maybe_handle_document_naming_metadata_query,
    maybe_handle_document_ocr_query,
    maybe_handle_document_summary_query,
)
from core.karen_case_facts import (
    CASE_KEY,
    load_karen_case_facts,
    maybe_capture_karen_case_facts,
    maybe_handle_karen_case_facts,
    render_case_facts,
)
from core.karen_notes_tasks_visibility import (
    is_auxiliary_task_row,
    load_karen_auxiliary_task_items,
    parse_karen_task_schedule_for_tomorrow,
    looks_like_karen_case_pendientes_query,
    looks_like_karen_notes_query,
    looks_like_karen_tasks_query,
    merge_karen_task_items,
    render_karen_case_pendientes_view,
    render_karen_case_notes_view,
    render_karen_tasks_view,
    select_karen_task_for_schedule,
)
from core.karen_recent_activity import maybe_capture_karen_case_event, maybe_handle_karen_recent_events_summary
from core.karen_appointments import maybe_handle_karen_appointment
from core.karen_transcript_guard import maybe_guard_pasted_transcript, maybe_handle_pending_transcript_choice
from subprocess import check_output



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
from datetime import timedelta, timezone
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

_ACTIVE_NODE = {}
_PENDING_CONVERT = {}
_LAST_NODE_IDEA = {}

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    Defaults,
    filters,
)

# Memory + Notes
from memory_store import (
    insert_message,
    fetch_recent_messages,
    trim_messages_for_chat,
    set_pm_focus,
    get_pm_focus,
    evaluate_pm_input,
    log_pm_decision,
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
    get_active_case_id,
    fetch_case_notes,
    insert_case_note,
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
_KAREN_NUMBERED_ACTION_DIRTY: dict[int, set[str]] = {}
_KAREN_REMINDER_LIST_CONTEXT: dict[int, str] = {}
_KAREN_GCAL_EVENT_LIST_CONTEXT: dict[int, dict] = {}
_KAREN_PENDING_REMINDER_CONTEXT: dict[int, dict] = {}
_KAREN_PENDING_TASK_DELETE_CONTEXT: dict[int, dict] = {}
_INLINE_NUDGE_LAST = {}
# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("val0-bot")


def _intent_router_v2_shadow_enabled() -> bool:
    return os.getenv("VAL0_INTENT_ROUTER_V2_SHADOW", "").strip().lower() == "true"


def _intent_router_v2_pending_state_for_shadow(chat_id: int | None):
    if chat_id is None:
        return None
    try:
        pending_task_delete = _KAREN_PENDING_TASK_DELETE_CONTEXT.get(int(chat_id))
        if pending_task_delete and time.time() - float(pending_task_delete.get("ts") or 0) <= 600:
            return {"type": "task_delete_clarification"}
    except Exception:
        return None
    return None


def _maybe_log_intent_router_v2_shadow(text: str, *, chat_id: int | None = None, client_id: str | None = None, message_id=None, pending_state=None) -> None:
    if not _intent_router_v2_shadow_enabled():
        return
    try:
        if pending_state is None:
            pending_state = _intent_router_v2_pending_state_for_shadow(chat_id)
        decision = classify_intent_shadow(
            text or "",
            client_id=client_id,
            chat_id=chat_id,
            pending_state=pending_state,
        )
        record_predicted_intent(chat_id, message_id, decision)
        preview = re.sub(r"\s+", " ", str(text or "")).strip()[:160]
        logger.info(
            '[INTENT_ROUTER_V2_SHADOW] client=%s intent=%s confidence=%.2f reason="%s" text="%s"',
            client_id or "unknown",
            decision.selected_intent,
            float(decision.confidence or 0.0),
            str(decision.reason or "")[:180],
            preview,
        )
    except Exception as e:
        logger.exception(f"[INTENT_ROUTER_V2_SHADOW] failed: {e}")


def _maybe_log_intent_router_v2_actual(actual_intent: str, handler_name: str, *, chat_id: int | None = None, message_id=None, text: str = "", reason: str = "") -> None:
    if not _intent_router_v2_shadow_enabled():
        return
    try:
        observation = record_actual_intent(chat_id, message_id, actual_intent, handler_name, reason=reason)
        preview = re.sub(r"\s+", " ", str(text or "")).strip()[:160]
        logger.info(
            '[INTENT_ROUTER_V2_ACTUAL] intent=%s handler=%s text="%s"',
            actual_intent,
            handler_name,
            preview,
        )
        if observation.predicted_intent:
            logger.info(
                "[INTENT_ROUTER_V2_COMPARE] %s",
                render_intent_observation(observation),
            )
    except Exception as e:
        logger.exception(f"[INTENT_ROUTER_V2_ACTUAL] failed: {e}")

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

    bug_pending = get_pending_bug_report_text(int(chat_id))
    if bug_pending:
        parts.append(bug_pending)

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

    return get_email_contact(fallback_name)


def get_last_assistant_message(chat_id: int) -> str:
    conn = _get_conn()
    try:
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
        if not row:
            return ""
        return (row["content"] if hasattr(row, "keys") else row[0]) or ""
    finally:
        conn.close()


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

        is_doc_request = (
            "hazme un contrato" in low or
            "redacta un contrato" in low or
            "redáctame un contrato" in low or
            "hazme un documento" in low or
            "redacta un documento" in low or
            "redáctame un documento" in low or
            "escrito" in low or
            "contrato" in low or
            "demanda" in low or
            "acuerdo" in low or
            "poder" in low or
            "mándamelo" in low or
            "mandamelo" in low or
            "envíamelo" in low or
            "enviamelo" in low
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

        # Safety gate:
        # - queries should not create tasks here
        # - document requests should never be ingested as Forge tasks
        # - only clear task-like inputs continue
        if not tasks or is_query or is_doc_request or not is_task_candidate:
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


TECHNICAL_PASTE_REPLY = (
    "Parece que pegaste un comando o salida técnica. No lo voy a procesar como caso, agenda ni memoria. "
    "Si quieres que lo revise, mándamelo como output o dime ‘Val, analiza este log’."
)


def looks_like_technical_paste(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False

    low = raw.lower()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    first = lines[0] if lines else raw
    first_low = first.lower()

    if first.startswith("==="):
        return True

    if first_low.startswith(("```bash", "```sh", "```shell", "```python", "```console")):
        return True

    if re.match(r"^(cd\s+/opt/|sudo\s+|systemctl\s+|journalctl\s+|git\s+(log|status)\b)", first_low):
        return True

    strong_markers = (
        "git log",
        "git status",
        "systemctl",
        "tee /root/launchpad",
        "<<'py'",
        '<<"py"',
        "./scripts/val0py",
    )
    if any(marker in low for marker in strong_markers):
        return True

    if len(lines) >= 4:
        shell_markers = (
            "echo ",
            "python3",
            "./scripts/val0py",
            "git ",
            "systemctl",
            "journalctl",
            "tee ",
            "cat <<",
            "&&",
            "||",
            "{",
            "}",
        )
        hits = sum(1 for marker in shell_markers if marker in low)
        if hits >= 3:
            return True

    return False


def _conversation_router_shadow_enabled() -> bool:
    return os.getenv("VAL0_CONVERSATION_ROUTER_SHADOW", "").strip().lower() == "true"


def _log_conversation_router_shadow(text: str, chat_id: int | None, client_id: str | None) -> None:
    if not _conversation_router_shadow_enabled():
        return

    try:
        message = normalize_message(text, chat_id=chat_id, client_id=client_id)
        intent = classify_deterministic_intent(message)
        logger.info(
            "[CONVERSATION_ROUTER_SHADOW] chat_id=%s client_id=%s predicted_intent=%s confidence=%s reason=%s line_count=%s is_group=%s",
            chat_id,
            client_id or "",
            intent.value,
            "1.0",
            "deterministic_v1",
            message.line_count,
            message.is_group_chat,
        )
    except Exception as e:
        logger.exception("[CONVERSATION_ROUTER_SHADOW] failed: %s", e)


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

    # Phrase forms where the name appears after a fixed trigger.
    triggers = [
        "quiero que me llames ",
        "quiero que me llame ",
        "llamame ",
        "llámame ",
        "puedes llamarme ",
        "me llamo ",
        "mi nombre es ",
        "soy ",
        "call me ",
        "you can call me ",
        "my name is ",
        "i am ",
        "i'm ",
    ]

    for t in triggers:
        if norm.startswith(_norm_text(t)):
            # Use the normalized trigger length only for simple ASCII-ish slicing safety.
            # For Spanish accents, fall back to regex below if slicing is weird.
            tail = original[len(t):].strip() if len(original) >= len(t) else ""
            if len(tail) > 1:
                return tail.strip(" .,:;!¡?¿")

    import re

    patterns = [
        r"(?i)^me llamo\s+(.+)$",
        r"(?i)^mi nombre es\s+(.+)$",
        r"(?i)^soy\s+(.+)$",
        r"(?i)^ll[aá]mame\s+(.+)$",
        r"(?i)^puedes llamarme\s+(.+)$",
        r"(?i)^call me\s+(.+)$",
        r"(?i)^my name is\s+(.+)$",
        r"(?i)^i am\s+(.+)$",
        r"(?i)^i'm\s+(.+)$",
    ]

    for pat in patterns:
        m = re.match(pat, original)
        if m:
            name = (m.group(1) or "").strip(" .,:;!¡?¿")
            if len(name) > 1:
                return name

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
    chat_id = update.effective_chat.id if update.effective_chat else 0
    try:
        preferred_name = get_fact(chat_id=chat_id, fact_key="preferred_name") or ""
    except Exception:
        preferred_name = ""
    await update.message.reply_text(build_alpha_onboarding_reply(preferred_name))



async def route_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Debug-only Operator Router test.
    Usage:
    /route ¿Qué hago ahora?
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    text = " ".join(context.args or []).strip()

    if not text:
        await update.message.reply_text(
            "Uso: /route <mensaje>\n\n"
            "Ejemplo:\n"
            "/route ¿Qué le digo al proveedor?"
        )
        return

    try:
        preferred_language = get_fact(chat_id=chat_id, fact_key="preferred_language") or "es"
    except Exception:
        preferred_language = "es"

    data = route_operator_intent(
        chat_id=int(chat_id),
        user_text=text,
        preferred_language=preferred_language,
    )

    import json
    pretty = json.dumps(data, ensure_ascii=False, indent=2)

    await update.message.reply_text(
        "🧭 Operator router\n\n"
        f"Input:\n{text}\n\n"
        f"JSON:\n{pretty}"
    )


async def classify_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Debug-only Exocortex classifier test.
    Usage:
    /classify Val, today was rough. Remind me tomorrow to call Carlos and save the supplier idea.
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    text = " ".join(context.args or []).strip()

    if not text:
        await update.message.reply_text(
            "Uso: /classify <mensaje>\n\n"
            "Ejemplo:\n"
            "/classify Val, hoy fue pesado. Recuérdame mañana llamar a Carlos y guarda la idea de seguimiento a proveedores."
        )
        return

    try:
        preferred_language = get_fact(chat_id=chat_id, fact_key="preferred_language") or "es"
    except Exception:
        preferred_language = "es"

    data = classify_exocortex_intent(
        chat_id=int(chat_id),
        user_text=text,
        preferred_language=preferred_language,
    )

    import json
    pretty = json.dumps(data, ensure_ascii=False, indent=2)

    await update.message.reply_text(
        "🧠 Exocortex classifier\n\n"
        f"Input:\n{text}\n\n"
        f"JSON:\n{pretty}"
    )






async def draftfollowup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Exocortex Mark 1 action demo.
    Usage:
    /draftfollowup

    Reads recent follow_up memory and drafts a practical message.
    Does not send anything.
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0

    try:
        preferred_language = get_fact(chat_id=chat_id, fact_key="preferred_language") or "es"
    except Exception:
        preferred_language = "es"

    try:
        from memory_store import fetch_recent_memory
        rows = fetch_recent_memory(int(chat_id), limit=15)
    except Exception as e:
        logger.exception(f"[DRAFTFOLLOWUP] fetch failed: {e}")
        await update.message.reply_text(f"No pude leer memoria reciente: {e}")
        return

    followups = []
    context_items = []

    for row in rows or []:
        r = dict(row) if hasattr(row, "keys") else {
            "id": row[0],
            "bucket": row[1],
            "raw_input": row[2],
            "summary": row[3],
            "created_at": row[4],
        }

        bucket = str(r.get("bucket") or "").strip()
        summary = str(r.get("summary") or "").strip()
        raw = str(r.get("raw_input") or "").strip()
        created_at = str(r.get("created_at") or "").strip()

        if bucket == "follow_up":
            followups.append({
                "id": r.get("id"),
                "bucket": bucket,
                "summary": summary,
                "raw": raw[:500],
                "created_at": created_at,
            })

        if bucket in {"reflection", "care_mode", "idea", "note", "project"}:
            context_items.append({
                "id": r.get("id"),
                "bucket": bucket,
                "summary": summary,
                "raw": raw[:300],
                "created_at": created_at,
            })

    if not followups:
        await update.message.reply_text(
            "✍️ Draft follow-up\n\n"
            "No encontré un seguimiento reciente para redactar.\n\n"
            "Primero prueba con /journal y menciona algo como: "
            "Carlos necesita la cotización o el proveedor no respondió."
        )
        return

    latest = followups[0]

    context_lines = []
    context_lines.append(
        f"FOLLOW_UP PRINCIPAL:\n"
        f"- id: {latest.get('id')}\n"
        f"- fecha: {latest.get('created_at')}\n"
        f"- resumen: {latest.get('summary')}\n"
        f"- raw: {latest.get('raw')}"
    )

    if context_items:
        context_lines.append("\nCONTEXTO RECIENTE:")
        for item in context_items[:5]:
            context_lines.append(
                f"- {item.get('bucket')} #{item.get('id')}: "
                f"{item.get('summary') or item.get('raw')}"
            )

    memory_block = "\n".join(context_lines)

    system_rules = f"""
You are Valeria drafting a practical follow-up message from Exocortex memory.

Task:
Draft ONE message the user can send.

Rules:
- Do not send the message.
- Preserve concrete details from memory whenever available: names, client, supplier/provider, quote/cotización, project type, deadline, blocker.
- If memory says a named person needs a quote/cotización, treat that person as the client/requester, NOT automatically as the supplier.
- If memory mentions Carlos needs the solar quote, Carlos is likely the client/requester waiting for the quote.
- If memory contains "cotización solar" or "solar quote", the draft should mention "cotización solar".
- If memory contains Carlos and the quote is for Carlos, the draft should mention "para Carlos" or "nuestro cliente Carlos".
- If the supplier/provider name is unknown, do NOT greet the supplier by the client's name.
- If the likely recipient is unclear, write the message to the supplier/provider generically: "Hola, buen día."
- Include client context naturally, e.g. "necesitamos avanzar con la cotización solar para Carlos."
- Do not invent names/details not in memory.
- Keep the message professional, warm, and concise.
- Include a short intro line before the draft.
- If Spanish is preferred, draft in Spanish.
- Avoid hype.
- Do not mention internal buckets unless useful.
- Do not end with "si quieres" or "quieres que lo haga".
- End with one concrete next step, such as: "Siguiente paso: copia este mensaje y envíalo al proveedor."

MEMORY:
{memory_block}
"""

    try:
        reply = call_val_openai(
            chat_id=int(chat_id),
            user_text="Draft the follow-up message from recent memory.",
            forced_lang=preferred_language,
            system_rules=system_rules,
        )
        reply = (reply or "").strip()
    except Exception as e:
        logger.exception(f"[DRAFTFOLLOWUP] model failed: {e}")
        reply = ""

    if not reply:
        reply = (
            "✍️ Draft follow-up\n\n"
            "Aquí tienes un borrador simple:\n\n"
            "Hola, buen día. Quería dar seguimiento a la cotización pendiente. "
            "¿Me puedes confirmar el estado y cuándo podrías enviármela? Gracias."
        )

    await update.message.reply_text("✍️ Mensaje de seguimiento\n\n" + reply)


async def whatnow_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Exocortex Mark 1 recovery command.
    Usage:
    /whatnow

    Reads recent structured memory and asks Val for one grounded next step.
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0

    try:
        preferred_language = get_fact(chat_id=chat_id, fact_key="preferred_language") or "es"
    except Exception:
        preferred_language = "es"

    try:
        from memory_store import fetch_recent_memory
        rows = fetch_recent_memory(int(chat_id), limit=12)
    except Exception as e:
        logger.exception(f"[WHATNOW] fetch failed: {e}")
        await update.message.reply_text(f"No pude leer memoria reciente: {e}")
        return

    try:
        facts = get_all_facts(chat_id=int(chat_id)) or {}
    except Exception as e:
        logger.exception(f"[WHATNOW] facts fetch failed: {e}")
        facts = {}

    profile_keys = [
        "preferred_name",
        "primary_role",
        "use_case",
        "main_goal",
        "friction_points",
        "current_tools",
        "tracking_buckets",
        "starter_workflow",
        "onboarding_status",
    ]

    profile_lines = []
    for k in profile_keys:
        v = str(facts.get(k) or "").strip()
        if v:
            profile_lines.append(f"- {k}: {v}")

    profile_block = "\n".join(profile_lines) if profile_lines else "No operating profile saved yet."

    useful = []
    allowed = {"reflection", "care_mode", "follow_up", "idea", "note", "task", "reminder", "decision", "project"}

    for row in rows or []:
        r = dict(row) if hasattr(row, "keys") else {
            "id": row[0],
            "bucket": row[1],
            "raw_input": row[2],
            "summary": row[3],
            "created_at": row[4],
        }

        bucket = str(r.get("bucket") or "").strip()
        if bucket not in allowed:
            continue

        summary = str(r.get("summary") or "").strip()
        raw = str(r.get("raw_input") or "").strip()
        created_at = str(r.get("created_at") or "").strip()

        useful.append({
            "id": r.get("id"),
            "bucket": bucket,
            "summary": summary,
            "raw": raw[:300],
            "created_at": created_at,
        })

    if not useful:
        await update.message.reply_text(
            "🧭 Qué hago ahora\n\n"
            "No tengo suficiente memoria estructurada reciente para recomendar un siguiente paso.\n\n"
            "Prueba primero con /exotest usando un mensaje real de tu día."
        )
        return

    memory_lines = []
    for item in useful[:8]:
        memory_lines.append(
            f"- #{item['id']} · {item['bucket']} · {item['created_at']}\n"
            f"  Resumen: {item['summary'] or item['raw']}"
        )

    memory_block = "\n".join(memory_lines)

    system_rules = f"""
You are Val0 Exocortex Mark 1 recovery mode.

The user is asking: "what now?"

Use the recent structured memory below to recommend ONE grounded next step.

Rules:
- Be honest and concise.
- Do not pretend to know more than the memory shows.
- Use the operating profile to understand the user's role, goal, tools, friction points, and starter workflow.
- If recent memory conflicts with the operating profile, recent memory wins.
- If there is a follow_up/client/business item, prioritize the item closest to action or money.
- If the profile includes a main_goal, connect the recommendation to that goal when relevant.
- If the profile includes friction_points, prefer actions that reduce that friction.
- If there is a reflection/care_mode item, acknowledge emotional load briefly but do not overdo it.
- Do not give a giant plan.
- Structure the answer clearly, but make it sound like Valeria, not a report template.
- Include:
  1) "Veo esto:" with 2-4 bullets
  2) "Mi recomendación:" with one next step
  3) "Siguiente acción:" with one concrete action the user can take now
- Do not end with "si quieres", "dime si quieres", "puedo ayudarte si quieres", or passive optional wording.
- In "Siguiente acción:", give a concrete command or action.
- If the next step is drafting a follow-up, tell the user naturally: "Dime: hazme el mensaje."
- Do not tell normal users to use /draftfollowup unless they specifically use commands.
- Do not add "si quieres" after that instruction.
- Avoid permission-softening on demo/action commands.
- Be helpful, direct, and grounded.
- Do not claim reminders were created unless memory says so.
- Do not claim you can contact, call, email, message, or follow up with someone directly unless an actual deterministic sending/contact tool has executed.
- For external actions, say you can draft the message, prepare the follow-up, track the pending item, or remind the user.
- Never say "empiezo a contactar", "voy a contactar", "I will contact", or equivalent unless the system actually sends the message.
- Avoid sounding corporate or generic.
- Respond in Spanish unless the user's language preference is English.

OPERATING PROFILE:
{profile_block}

RECENT STRUCTURED MEMORY:
{memory_block}
"""

    try:
        reply = call_val_openai(
            chat_id=int(chat_id),
            user_text="What now?",
            forced_lang=preferred_language,
            system_rules=system_rules,
        )
        reply = (reply or "").strip()
    except Exception as e:
        logger.exception(f"[WHATNOW] model failed: {e}")
        reply = ""

    if not reply:
        reply = (
            "🧭 What now?\n\n"
            "Veo memoria reciente, pero no pude generar una recomendación limpia.\n"
            "Mi recomendación: revisa el seguimiento más cercano a acción o dinero."
        )

    await update.message.reply_text("🧭 Qué hago ahora\n\n" + reply)



async def exosummary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clean Exocortex demo viewer.
    Shows the latest grouped capture without dumping raw duplicate rows.
    Usage:
    /exosummary
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0

    try:
        from memory_store import fetch_recent_memory
        rows = fetch_recent_memory(int(chat_id), limit=15)
    except Exception as e:
        logger.exception(f"[EXOSUMMARY] failed: {e}")
        await update.message.reply_text(f"No pude leer lo guardado recientemente: {e}")
        return

    allowed = {"reflection", "care_mode", "follow_up", "idea", "note", "task", "reminder", "decision", "project"}
    items = []

    for row in rows or []:
        r = dict(row) if hasattr(row, "keys") else {
            "id": row[0],
            "bucket": row[1],
            "raw_input": row[2],
            "summary": row[3],
            "created_at": row[4],
        }

        bucket = str(r.get("bucket") or "").strip()
        if bucket not in allowed:
            continue

        raw = str(r.get("raw_input") or "").strip()
        summary = str(r.get("summary") or "").strip()

        # Hide low-quality generic classifier artifacts from demo summary.
        # They may still exist in raw memory, but should not pollute the user-facing view.
        if bucket == "task" and summary in {"task_low", "task_medium", "task_high"}:
            continue

        if not raw:
            continue

        items.append({
            "id": r.get("id"),
            "bucket": bucket,
            "raw": raw,
            "summary": summary,
            "created_at": str(r.get("created_at") or "").strip(),
        })

    if not items:
        await update.message.reply_text(
            "🧠 Esto guardé\n\n"
            "No encontré una captura reciente.\n\n"
            "Cuéntame algo que quieras guardar y lo ordeno."
        )
        return

    # Group latest capture by timestamp window.
    # Narrative Capture stores separate raw_span values per extracted item,
    # so grouping by raw text no longer works.
    latest_created = items[0].get("created_at") or ""
    latest_minute = latest_created[:16] if latest_created else ""

    if latest_minute:
        grouped = [
            x for x in items
            if str(x.get("created_at") or "").startswith(latest_minute)
        ][:8]
    else:
        grouped = items[:5]

    if not grouped:
        grouped = items[:5]

    buckets = []
    for x in grouped:
        if x["bucket"] not in buckets:
            buckets.append(x["bucket"])

    created_at = grouped[0].get("created_at") or ""

    label_map = {
        "reflection": "Reflexión",
        "care_mode": "Apoyo / orden personal",
        "follow_up": "Seguimiento",
        "idea": "Idea",
        "note": "Nota",
        "task": "Tarea",
        "reminder": "Recordatorio",
        "decision": "Decisión",
        "parking_lot": "Parking Lot",
        "project": "Proyecto",
    }

    lines = []
    lines.append("🧠 Esto guardé")
    lines.append("")
    if created_at:
        lines.append(f"Fecha guardada: {created_at}")
        lines.append("")

    lines.append("Detecté:")
    for b in buckets:
        lines.append(f"- {label_map.get(b, b)}")

    lines.append("")
    lines.append("Resumen:")
    for x in grouped:
        b = x.get("bucket") or ""
        item_summary = x.get("summary") or x.get("raw") or ""
        if item_summary:
            lines.append(f"- {label_map.get(b, b)}: {item_summary}")

    lines.append("")
    lines.append("Siguiente paso:")
    lines.append("Pregunta: ¿Qué hago ahora?")

    await update.message.reply_text("\n".join(lines))


async def exorecent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Debug-only Exocortex recent memory viewer.
    Usage:
    /exorecent
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0

    try:
        from memory_store import fetch_recent_memory
        rows = fetch_recent_memory(int(chat_id), limit=10)
    except Exception as e:
        logger.exception(f"[EXORECENT] failed: {e}")
        await update.message.reply_text(f"Exocortex recent memory error: {e}")
        return

    if not rows:
        await update.message.reply_text("🧠 Memoria reciente\n\nNo hay memoria reciente estructurada.")
        return

    lines = ["🧠 Memoria reciente", ""]

    for row in rows:
        r = dict(row) if hasattr(row, "keys") else {
            "id": row[0],
            "bucket": row[1],
            "raw_input": row[2],
            "summary": row[3],
            "created_at": row[4],
        }

        rid = r.get("id")
        bucket = str(r.get("bucket") or "").strip()
        summary = str(r.get("summary") or "").strip()
        created_at = str(r.get("created_at") or "").strip()
        raw = str(r.get("raw_input") or "").strip()

        if len(raw) > 180:
            raw = raw[:177] + "..."

        lines.append(f"#{rid} · {bucket} · {created_at}")
        if summary:
            lines.append(f"Resumen: {summary}")
        if raw:
            lines.append(f"Raw: {raw}")
        lines.append("")

    await update.message.reply_text("\n".join(lines).strip())




_ONBOARDING_FIELDS = [
    ("preferred_name", "¿Cómo quieres que te llame?"),
    ("primary_role", "¿Qué haces principalmente — trabajo, negocio, estudios, casa, mezcla?"),
    ("use_case", "¿Quieres usarme más para vida personal, trabajo, negocio, o todo junto?"),
    ("main_goal", "¿Qué quieres mejorar primero?"),
    ("friction_points", "¿Dónde se te caen más las cosas: clientes, pendientes, citas, proveedores, pagos, ideas, foco, algo más?"),
    ("current_tools", "¿Qué usas hoy para organizarte? WhatsApp, Excel, papel, Google Calendar, memoria pura, otra cosa."),
    ("tracking_buckets", "¿Qué cosas deberíamos empezar a rastrear? Ejemplo: clientes, proveedores, cotizaciones, tareas, ideas, pagos, familia."),
]

_ONBOARDING_STATE = {}


async def onboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Onboarding Consultant v1.
    Usage:
    /onboard
    /onboard reset
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    args = [a.strip().lower() for a in (context.args or [])]

    if args and args[0] in {"reset", "reiniciar", "restart"}:
        _ONBOARDING_STATE.pop(int(chat_id), None)
        await update.message.reply_text(
            "Listo. Reinicié el onboarding.\n\n"
            "Cuando quieras empezar otra vez, escribe /onboard."
        )
        return

    _ONBOARDING_STATE[int(chat_id)] = {"idx": 0, "answers": {}}

    intro = (
        "Vamos a armar tu perfil operativo Mark 1.\n\n"
        "No es un formulario eterno. Es para que Val entienda tu mundo y no te trate como usuario genérico.\n\n"
        f"1/{len(_ONBOARDING_FIELDS)} — {_ONBOARDING_FIELDS[0][1]}"
    )
    await update.message.reply_text(intro)



async def flowrequest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Workflow Designer v1: capture a roadmap/workflow request.
    Usage:
    /flowrequest Carpintero quiere rastrear fotos y diseños por proyecto.
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    text = " ".join(context.args or []).strip()

    if not text:
        await update.message.reply_text(
            "🧩 Flow request\n\n"
            "Uso:\n"
            "/flowrequest Carpintero quiere rastrear fotos y diseños por proyecto.\n\n"
            "Esto guarda una solicitud para revisar después, no promete que ya esté construido."
        )
        return

    try:
        facts = get_all_facts(chat_id=int(chat_id)) or {}
    except Exception:
        facts = {}

    profile_bits = []
    for k in ("primary_role", "use_case", "main_goal", "friction_points", "current_tools", "tracking_buckets"):
        v = str(facts.get(k) or "").strip()
        if v:
            profile_bits.append(f"{k}: {v}")

    active_profile_context = " | ".join(profile_bits) if profile_bits else "no_active_profile"

    # Lightweight target-context inference for roadmap clarity.
    low = text.lower()
    target_context = "general"
    if any(x in low for x in ["carpinter", "carpentry", "carpenter"]):
        target_context = "carpentry"
    elif any(x in low for x in ["legal", "caso", "expediente", "audiencia"]):
        target_context = "legal"
    elif any(x in low for x in ["solar", "panel", "cotización", "cotizacion", "proveedor"]):
        target_context = "solar_or_supplier_workflow"
    elif any(x in low for x in ["limpieza", "cleaning", "casa", "cliente"]):
        target_context = "cleaning_or_home_services"

    summary = (
        f"flow_request: {text} | "
        f"target_context: {target_context} | "
        f"active_user_profile: {active_profile_context}"
    )

    try:
        from memory_store import insert_memory_item
        insert_memory_item(
            chat_id=int(chat_id),
            bucket="parking_lot",
            raw_input=text,
            summary=summary,
        )
    except Exception as e:
        logger.exception(f"[FLOWREQUEST] storage failed: {e}")
        await update.message.reply_text(f"No pude guardar el flow request: {e}")
        return

    await update.message.reply_text(
        "🧩 Flow request guardado.\n\n"
        "Lo dejé como solicitud de mejora, no como promesa activa.\n\n"
        f"Solicitud:\n{text}\n\n"
        "Modo actual: podemos operar con workaround manual si aplica.\n"
        "Roadmap: queda marcado para revisión del Boss / ValPrime."
    )


async def onboard_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows current onboarding facts.
    Usage:
    /onboardstatus
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0

    try:
        facts = get_all_facts(chat_id=int(chat_id)) or {}
    except Exception as e:
        logger.exception(f"[ONBOARD_STATUS] failed: {e}")
        await update.message.reply_text(f"No pude leer tu perfil operativo: {e}")
        return

    preferred_name = str(facts.get("preferred_name") or "").strip()
    primary_role = str(facts.get("primary_role") or "").strip()
    use_case = str(facts.get("use_case") or "").strip()
    main_goal = str(facts.get("main_goal") or "").strip()
    friction_points = str(facts.get("friction_points") or "").strip()
    current_tools = str(facts.get("current_tools") or "").strip()
    tracking_buckets = str(facts.get("tracking_buckets") or "").strip()
    starter_workflow = str(facts.get("starter_workflow") or "").strip()
    onboarding_status = str(facts.get("onboarding_status") or "").strip()

    if not any([preferred_name, primary_role, use_case, main_goal, friction_points, current_tools, tracking_buckets]):
        await update.message.reply_text(
            "Todavía no tengo un perfil tuyo guardado.\n\n"
            "Empieza con /onboard y te hago unas preguntas rápidas para entender tu mundo."
        )
        return

    name = preferred_name or "ti"

    lines = []
    lines.append("🧭 Esto sé de ti hasta ahora")
    lines.append("")
    if preferred_name:
        lines.append(f"- Te puedo llamar {preferred_name}.")
    if primary_role:
        lines.append(f"- Tu contexto principal ahora mismo es: {primary_role}.")
    if use_case:
        lines.append(f"- Quieres usarme para: {use_case}.")
    if main_goal:
        lines.append(f"- Lo primero que quieres mejorar es: {main_goal}.")
    if friction_points:
        lines.append(f"- Donde más se te caen las cosas: {friction_points}.")
    if current_tools:
        lines.append(f"- Hoy te organizas con: {current_tools}.")
    if tracking_buckets:
        lines.append(f"- Vamos a empezar rastreando: {tracking_buckets}.")
    if starter_workflow:
        display_workflow = starter_workflow.replace("/whatnow", "“¿Qué hago ahora?”")
        display_workflow = display_workflow.replace("/draftfollowup", "“Hazme el mensaje”")

        lines.append("")
        lines.append("Primer flujo sugerido:")
        lines.append(f"- {display_workflow}")

    lines.append("")
    lines.append("Cómo usarme:")
    lines.append("- Cuéntame cosas en lenguaje normal.")
    lines.append("- Yo intento separarlas en ideas, tareas, eventos, seguimientos o recordatorios.")
    lines.append("- Si no sabes por dónde empezar, dime: ¿Qué hago ahora?")

    lines.append("")
    lines.append("Si algo está mal, dime algo como:")
    lines.append("“Corrige mi perfil: ...”")

    await update.message.reply_text("\n".join(lines))


async def _maybe_handle_onboarding_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    """
    Handles active onboarding answers in the normal text pipeline.
    Returns True if consumed.
    """
    if not update.message:
        return False

    chat_id = update.effective_chat.id if update.effective_chat else 0
    state = _ONBOARDING_STATE.get(int(chat_id))
    if not state:
        return False

    answer = (text or "").strip()
    if not answer:
        return False

    # Allow user to stop.
    norm = unicodedata.normalize("NFKD", answer.lower())
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = re.sub(r"[¿?¡!.,:;]+", "", norm).strip()

    if norm in {"cancel", "cancelar", "stop", "para", "detener"}:
        _ONBOARDING_STATE.pop(int(chat_id), None)
        await update.message.reply_text("Entendido. Pausé el onboarding.")
        return True

    idx = int(state.get("idx", 0))
    if idx < 0 or idx >= len(_ONBOARDING_FIELDS):
        _ONBOARDING_STATE.pop(int(chat_id), None)
        return False

    fact_key, _question = _ONBOARDING_FIELDS[idx]

    try:
        from memory_store import upsert_fact, insert_memory_item

        value = answer.strip()
        if fact_key == "preferred_name":
            value = value.strip().title()

        upsert_fact(
            chat_id=int(chat_id),
            fact_key=fact_key,
            fact_value=value,
        )

        insert_memory_item(
            chat_id=int(chat_id),
            bucket="project",
            raw_input=answer,
            summary=f"onboarding:{fact_key}={value}",
        )

    except Exception as e:
        logger.exception(f"[ONBOARDING] failed to store {fact_key}: {e}")
        await update.message.reply_text(f"No pude guardar esa respuesta: {e}")
        return True

    state["answers"][fact_key] = value
    idx += 1
    state["idx"] = idx

    if idx < len(_ONBOARDING_FIELDS):
        next_key, next_question = _ONBOARDING_FIELDS[idx]
        await update.message.reply_text(
            f"Guardado.\n\n"
            f"{idx + 1}/{len(_ONBOARDING_FIELDS)} — {next_question}"
        )
        return True

    # Complete onboarding.
    answers = dict(state.get("answers") or {})

    role = answers.get("primary_role", "")
    use_case = answers.get("use_case", "")
    friction = answers.get("friction_points", "")
    buckets = answers.get("tracking_buckets", "")

    starter_workflow = (
        "Captura diaria → seguimiento de pendientes → /whatnow para decidir el siguiente paso"
    )

    if any(x in (friction + " " + buckets).lower() for x in ["cliente", "client", "proveedor", "supplier", "cotizacion", "cotización", "quote"]):
        starter_workflow = (
            "Clientes/proveedores → cotizaciones/seguimientos → /whatnow → /draftfollowup"
        )

    try:
        from memory_store import upsert_fact
        upsert_fact(
            chat_id=int(chat_id),
            fact_key="starter_workflow",
            fact_value=starter_workflow,
        )
        upsert_fact(
            chat_id=int(chat_id),
            fact_key="onboarding_status",
            fact_value="complete_v1",
        )
    except Exception as e:
        logger.exception(f"[ONBOARDING] failed completion facts: {e}")

    _ONBOARDING_STATE.pop(int(chat_id), None)

    lines = []
    lines.append("Listo. Ya tengo tu perfil operativo Mark 1.")
    lines.append("")
    lines.append("Lo que entiendo:")
    if role:
        lines.append(f"- Rol/contexto: {role}")
    if use_case:
        lines.append(f"- Uso principal: {use_case}")
    if friction:
        lines.append(f"- Fricción: {friction}")
    if buckets:
        lines.append(f"- Vamos a rastrear: {buckets}")
    lines.append("")
    lines.append("Primer workflow recomendado:")
    lines.append(f"- {starter_workflow}")
    lines.append("")
    lines.append("Cómo usarme ahora:")
    lines.append("- Cuéntame el desorden del día en lenguaje normal.")
    lines.append("- Yo lo separo en reflexión, seguimiento, idea o tarea.")
    lines.append("- Luego usa /whatnow para sacar el siguiente paso.")

    await update.message.reply_text("\n".join(lines))
    return True


async def journal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User-facing Exocortex Smart Journal Mark 1.
    Usage:
    /journal Hoy fue pesado. Carlos necesita la cotización, el proveedor no respondió y estoy abrumado.

    This is the non-debug entry point:
    - classifies messy journal input
    - stores structured memory buckets
    - replies conversationally
    - does NOT create reminders yet
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    text = " ".join(context.args or []).strip()

    if not text:
        await update.message.reply_text(
            "📝 Journal Mark 1\n\n"
            "Cuéntame cómo va tu día o suelta el desorden completo.\n\n"
            "Ejemplo:\n"
            "/journal Hoy fue pesado. Carlos necesita la cotización solar, "
            "el proveedor no respondió y estoy abrumado."
        )
        return

    try:
        preferred_language = get_fact(chat_id=chat_id, fact_key="preferred_language") or "es"
    except Exception:
        preferred_language = "es"

    data = classify_exocortex_intent(
        chat_id=int(chat_id),
        user_text=text,
        preferred_language=preferred_language,
    )

    buckets = data.get("buckets") or ["normal_chat"]
    summary = (data.get("summary") or "").strip()
    confidence = data.get("confidence", 0.0)

    stored = []
    allowed = {
        "note",
        "idea",
        "reflection",
        "care_mode",
        "decision",
        "parking_lot",
        "project",
        "follow_up",
        "normal_chat",
        "task",
        "reminder",
    }

    try:
        from memory_store import insert_memory_item

        items = data.get("items") or []

        if items:
            for item in items:
                bucket = str(item.get("bucket") or "").strip()
                item_summary = str(item.get("summary") or "").strip()
                raw_span = str(item.get("raw_span") or "").strip()

                if bucket not in allowed:
                    bucket = "normal_chat"

                insert_memory_item(
                    chat_id=int(chat_id),
                    bucket=bucket,
                    raw_input=raw_span or text,
                    summary=item_summary or summary or f"journal:{bucket}",
                )
                stored.append(bucket)
        else:
            for bucket in buckets:
                bucket = str(bucket or "").strip()
                if bucket not in allowed:
                    bucket = "normal_chat"

                insert_memory_item(
                    chat_id=int(chat_id),
                    bucket=bucket,
                    raw_input=text,
                    summary=summary or f"journal:{bucket}",
                )
                stored.append(bucket)

    except Exception as e:
        logger.exception(f"[JOURNAL] storage failed: {e}")
        await update.message.reply_text(f"No pude guardar el journal: {e}")
        return

    label_map = {
        "reflection": "reflexión",
        "care_mode": "care mode",
        "follow_up": "seguimiento",
        "idea": "idea",
        "note": "nota",
        "task": "tarea",
        "reminder": "recordatorio",
        "decision": "decisión",
        "parking_lot": "parking lot",
        "project": "proyecto",
        "normal_chat": "conversación",
    }

    stored_labels = [label_map.get(b, b) for b in stored]

    system_rules = f"""
You are Valeria in Smart Journal Mark 1.

The user just gave a journal/life/work update.

You must:
- respond like Valeria, not like a form or admin report
- sound conversational, grounded, and useful
- briefly say what was saved, but avoid robotic phrases like "Detecté" unless necessary
- do not overpromise
- do not say reminders were created unless explicitly created by deterministic code
- if follow_up exists, mention it as something to act on, not as a created reminder
- if reflection or care_mode exists, acknowledge the emotional state briefly and naturally
- avoid gendered emotional adjectives unless the user's profile explicitly provides gender
- prefer neutral wording like "te sientes con mucha carga", "esto pesa", "hay bastante presión", "suena agotador"
- end with one concrete next step
- avoid "si quieres" endings unless genuinely asking permission
- keep it concise
- style target: warm operator, not checklist bot

Saved buckets: {stored_labels}
Classifier summary: {summary}
Classifier confidence: {confidence}
"""

    try:
        reply = call_val_openai(
            chat_id=int(chat_id),
            user_text=text,
            forced_lang=preferred_language,
            system_rules=system_rules,
        )
        reply = (reply or "").strip()
    except Exception as e:
        logger.exception(f"[JOURNAL] model reply failed: {e}")
        reply = ""

    if not reply:
        reply = (
            "📝 Guardé este journal.\n\n"
            f"Detecté: {', '.join(stored_labels)}.\n"
            f"Resumen: {summary or 'sin resumen'}\n\n"
            "Siguiente paso: cuando quieras, dime /whatnow y te ayudo a sacar una acción concreta."
        )

    await update.message.reply_text(reply)


async def exotest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Debug-only Exocortex Mark 1 test.
    Usage:
    /exotest Val, today was rough. Carlos still needs the solar quote, supplier didn’t answer, and I’m honestly overwhelmed. Also save the supplier follow-up idea.

    This command:
    - classifies messy input
    - stores classifier buckets into memory_items
    - replies with a crude Wow Loop summary
    - does NOT create reminders yet
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    text = " ".join(context.args or []).strip()

    if not text:
        await update.message.reply_text(
            "Uso: /exotest <mensaje>\n\n"
            "Ejemplo:\n"
            "/exotest Val, hoy fue pesado. Carlos necesita la cotización solar, "
            "el proveedor no respondió, y estoy abrumado. Guarda la idea de seguimiento a proveedores."
        )
        return

    try:
        preferred_language = get_fact(chat_id=chat_id, fact_key="preferred_language") or "es"
    except Exception:
        preferred_language = "es"

    data = classify_exocortex_intent(
        chat_id=int(chat_id),
        user_text=text,
        preferred_language=preferred_language,
    )

    buckets = data.get("buckets") or ["normal_chat"]
    summary = (data.get("summary") or "").strip()
    confidence = data.get("confidence", 0.0)
    suggested_action = data.get("suggested_action", "reply_only")

    # Safe storage only. No automatic reminders/tasks yet.
    stored = []
    try:
        from memory_store import insert_memory_item

        for bucket in buckets:
            bucket = str(bucket or "").strip()
            if not bucket:
                continue

            # Keep Mark 1 conservative: store only exocortex-relevant buckets.
            if bucket not in (
                "note",
                "idea",
                "reflection",
                "care_mode",
                "decision",
                "parking_lot",
                "project",
                "follow_up",
                "normal_chat",
                "task",
                "reminder",
            ):
                bucket = "normal_chat"

            insert_memory_item(
                chat_id=int(chat_id),
                bucket=bucket,
                raw_input=text,
                summary=summary or f"exocortex:{bucket}",
            )
            stored.append(bucket)

    except Exception as e:
        logger.exception(f"[EXOTEST] storage failed: {e}")
        await update.message.reply_text(f"Exocortex storage error: {e}")
        return

    lines = []
    lines.append("🧠 Exocortex Mark 1 test")
    lines.append("")
    lines.append("Estoy sorting that — versión cruda.")
    lines.append("")
    lines.append("Detecté:")
    for bucket in stored:
        label = {
            "reflection": "Reflexión",
            "care_mode": "Apoyo / orden personal",
            "follow_up": "Seguimiento",
            "idea": "Idea",
            "note": "Nota",
            "task": "Tarea",
            "reminder": "Recordatorio",
            "decision": "Decisión",
            "parking_lot": "Parking Lot",
            "project": "Proyecto",
            "normal_chat": "Conversación",
        }.get(bucket, bucket)
        lines.append(f"- {label}")

    lines.append("")
    lines.append(f"Resumen: {summary or 'sin resumen'}")
    lines.append(f"Confianza: {confidence}")
    lines.append(f"Acción sugerida: {suggested_action}")
    lines.append("")
    lines.append("Guardé esto como memoria estructurada Mark 1.")
    lines.append("")
    lines.append("Siguiente paso demo: pregúntame luego /memory o probamos un /whatnow Mark 1.")

    await update.message.reply_text("\n".join(lines))


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
# Attachment handler — Karen/VFMS bridge v0
# --------------------------------------------------
def _render_attachment_readiness_status(extract_status: str, capability: dict) -> str:
    status = str(capability.get("status") or "")
    file_type = str(capability.get("file_type") or "")

    if status == "ready":
        return "texto extraído e indexado; listo para resumen"
    if file_type == "image" or status in {"ocr_needed", "ocr_failed"}:
        return "archivo guardado; necesita OCR o revisión manual antes de resumirlo"
    if file_type == "docx":
        return "archivo guardado; Word/docx todavía no está soportado para extracción automática"
    if status == "unsupported" or file_type == "unsupported":
        return "archivo guardado; tipo no soportado para extracción automática todavía"
    return extract_status


async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    v0 bridge:
    - receives Telegram document/photo
    - downloads to Val0 local storage
    - registers file through VFMS ingest
    - best-effort extract/index for text-like files
    - does NOT promise OCR/analysis yet
    """
    if not update.message:
        return

    chat_id = update.effective_chat.id
    msg_id = update.message.message_id
    user = update.effective_user
    caption_text = (update.message.caption or "").strip()

    upload_root = "/opt/val0/vfms_data/telegram_uploads"
    os.makedirs(upload_root, exist_ok=True)

    file_id = None
    original_name = None
    kind = None
    mime_type = ""

    if update.message.document:
        doc = update.message.document
        file_id = doc.file_id
        original_name = doc.file_name or f"document_{msg_id}"
        kind = "document"
        mime_type = getattr(doc, "mime_type", "") or ""
    elif update.message.photo:
        photo = update.message.photo[-1]
        file_id = photo.file_id
        original_name = f"photo_{chat_id}_{msg_id}.jpg"
        kind = "photo"
        mime_type = "image/jpeg"
    else:
        return

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", original_name).strip("_") or f"upload_{msg_id}"
    local_dir = os.path.join(upload_root, str(chat_id))
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, f"{msg_id}__{safe_name}")

    try:
        tg_file = await context.bot.get_file(file_id)
        await tg_file.download_to_drive(local_path)
    except Exception as e:
        logger.exception(f"Attachment download failed: {e}")
        await update.message.reply_text("No pude descargar ese archivo. Intenta mandarlo otra vez.")
        return

    ingest_id = None
    vfms_status = "registrado"
    extract_status = "no extraído todavía"
    active_case_id = ""
    case_note_status = ""

    try:
        proc = subprocess.run(
            ["/opt/val0/.venv/bin/python", "/opt/val0/vfms.py", "ingest", local_path],
            cwd="/opt/val0",
            text=True,
            capture_output=True,
            timeout=60,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
        ingest_id = proc.stdout.strip().splitlines()[-1].strip()

        ext = os.path.splitext(local_path)[1].lower()

        auto_extract_exts = {
            ".txt",
            ".md",
            ".csv",
            ".tsv",
            ".pdf",
        }

        if ext in auto_extract_exts:
            subprocess.run(
                [
                    "/opt/val0/.venv/bin/python",
                    "/opt/val0/vfms.py",
                    "extract",
                    ingest_id,
                    "--ocr",
                    "auto" if ext == ".pdf" else "off",
                ],
                cwd="/opt/val0",
                text=True,
                capture_output=True,
                timeout=60,
                check=True,
            )
            subprocess.run(
                ["/opt/val0/.venv/bin/python", "/opt/val0/vfms.py", "index", ingest_id],
                cwd="/opt/val0",
                text=True,
                capture_output=True,
                timeout=60,
                check=True,
            )
            extract_status = "texto extraído e indexado"
        else:
            extract_status = "archivo guardado; OCR/análisis queda como paso manual"

        try:
            active_case_id = get_active_case_id(int(chat_id))
            if active_case_id:
                note_text = (
                    "Documento recibido vía Telegram y registrado en VFMS.\n"
                    f"- Archivo: {safe_name}\n"
                    f"- Tipo: {kind}\n"
                    f"- VFMS ingest_id: {ingest_id}\n"
                    f"- Ruta local: {local_path}\n"
                    f"- Estado: {extract_status}\n"
                )
                if caption_text:
                    note_text += f"- Nota usuario: {caption_text}\n"
                insert_case_note(
                    chat_id=int(chat_id),
                    case_id=str(active_case_id),
                    note_text=note_text,
                    source="telegram_attachment_vfms",
                    telegram_message_id=int(msg_id),
                )
                case_note_status = f"asociado al caso CASE:{active_case_id}"
        except Exception as e:
            logger.exception(f"Failed to link attachment to active case: {e}")
            case_note_status = "registrado en VFMS; no pude asociarlo al caso activo"

    except Exception as e:
        logger.exception(f"VFMS attachment registration failed: {e}")
        vfms_status = "guardado localmente, pero VFMS falló"
        extract_status = str(e)[:180]

    display_extract_status = extract_status
    if ingest_id:
        record = document_record_from_vfms_metadata(
            client_id=resolve_client_id(chat_id),
            case_id=str(active_case_id or ""),
            chat_id=int(chat_id),
            metadata={
                "ingest_id": ingest_id,
                "filename": safe_name,
                "caption": caption_text,
                "status": extract_status,
                "hash": "",
                "mime_type": mime_type,
                "stored_path": local_path,
                "kind": kind,
                "vfms_status": vfms_status,
                "original_name": original_name,
            },
            caption=caption_text,
            status=extract_status,
            source="telegram_attachment_vfms",
            source_message_id=int(msg_id),
        )
        display_extract_status = _render_attachment_readiness_status(
            extract_status,
            document_capability_summary(record),
        )
        if not case_note_status:
            case_note_status = "guardado en VFMS; no quedó asociado a un caso activo."

    reply = (
        "📎 Documento recibido.\n"
        f"Tipo: {kind}\n"
        f"Archivo: {safe_name}\n"
        f"VFMS: {vfms_status}\n"
    )
    if ingest_id:
        reply += f"ID VFMS: {ingest_id}\n"
    reply += f"Estado: {display_extract_status}"
    if caption_text:
        reply += "\n📝 Nota asociada al documento."
    if case_note_status:
        reply += f"\nCaso: {case_note_status}"

    await update.message.reply_text(reply)




# --------------------------------------------------
# Legacy attachment inventory handler removed
# Source of truth:
# core/document_inventory_queries.py
# --------------------------------------------------

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
            "No entendí nada claro en ese audio. Intenta de nuevo o mándalo por texto."
        )
        return

    # --------------------------------------------------
    # VOICE TOMORROW DASHBOARD OVERRIDE
    # Keep voice "Qué tengo mañana" aligned with text behavior.
    # --------------------------------------------------
    try:
        voice_norm = unicodedata.normalize("NFKD", (transcribed_text or "").lower())
        voice_norm = "".join(ch for ch in voice_norm if not unicodedata.combining(ch))
        voice_norm = re.sub(r"[¿?¡!.,:;]+", "", voice_norm).strip()

        voice_tomorrow_markers = (
            "que tengo manana",
            "que tengo mañana",
            "qué tengo manana",
            "qué tengo mañana",
            "tengo manana",
            "tengo mañana",
            "manana",
            "mañana",
            "que debo hacer manana",
            "que debo hacer mañana",
            "qué debo hacer manana",
            "qué debo hacer mañana",
            "mis pendientes de manana",
            "mis pendientes de mañana",
            "que hay manana",
            "que hay mañana",
            "qué hay manana",
            "qué hay mañana",
        )

        if voice_norm in voice_tomorrow_markers:
            reply = build_unified_tomorrow_dashboard(int(chat_id))
            await update.message.reply_text(reply)
            return

    except Exception as e:
        logger.exception(f"[VOICE_TOMORROW_DASHBOARD_OVERRIDE] failed: {e}")

    # --------------------------------------------------
    # KAREN VOICE DIRECT GATE
    # --------------------------------------------------
    # Voice transcription can hit older generic legal routes inside the text pipeline.
    # For Karen LandOps, catch explicit event/summary/inventory commands directly here first.
    try:
        from core.karen_recent_activity import maybe_capture_karen_case_event, maybe_handle_karen_recent_events_summary
        from core.karen_next_action import start_document_inventory

        voice_norm_karen = _norm_text(transcribed_text or "")

        from core.karen_appointments import maybe_handle_karen_appointment

        if await maybe_handle_karen_appointment(update, context, transcribed_text):
            return

        if await maybe_capture_karen_case_event(update, context, transcribed_text):
            return

        if await maybe_handle_karen_recent_events_summary(update, context, transcribed_text):
            return

        if voice_norm_karen in {
            "inventario de documentos",
            "empezar inventario de documentos",
            "iniciar inventario de documentos",
            "hagamos inventario de documentos",
            "hacer inventario de documentos",
        }:
            await start_document_inventory(update, context)
            return

    except Exception as e:
        logger.exception(f"[KAREN_VOICE_DIRECT_GATE] failed: {e}")

    # --------------------------------------------------
    # VOICE → TEXT PIPELINE ALIGNMENT
    # --------------------------------------------------
    # Voice should behave like the same text typed by the user.
    # Older code below classifies voice into memory/tasks before Karen routes,
    # which caused wrong replies like "no hago recordatorios" or "no encuentro ese caso".
    # For Karen/Val0 reliability, send transcription into the canonical text pipeline first.
    try:
        logger.info(f"[VOICE_PIPELINE] routing transcription through text pipeline: {transcribed_text!r}")
        await _process_text_pipeline(update, context, transcribed_text)
        return
    except Exception as e:
        logger.exception(f"[VOICE_PIPELINE] canonical text pipeline failed, falling back to legacy voice path: {e}")

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

    # --------------------------------------------------
    # KAREN_INTERROGATOR_VOICE_GATE
    # Voice answers should continue the active Interrogator session
    # instead of being swallowed by task/background Forge routing.
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_interrogator(update, context, chat_id, transcribed_text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_INTERROGATOR_VOICE_GATE] failed: {e}")

    is_query = (
        "que tengo" in low or
        "qué tengo" in low or
        "para mañana" in low or
        "para hoy" in low or
        "esta semana" in low or
        "mis tareas" in low or
        "mis pendientes" in low or
        "que hay" in low or
        "qué hay" in low or
        "puedes" in low or
        "puedo" in low or
        low.startswith("puedes ") or
        low.startswith("puedo ") or
        low.startswith("me puedes ") or
        low.startswith("me podrías ") or
        low.startswith("me podrias ") or
        (
            "recordarme cosas" in low
            and not any(x in low for x in [
                "mañana", "manana", "hoy", "a las", "a la",
                "revisar", "llamar", "comprar", "pagar", "enviar", "hacer"
            ])
        )
    )

    is_doc_request = (
        "hazme un contrato" in low or
        "redacta un contrato" in low or
        "redáctame un contrato" in low or
        "hazme un documento" in low or
        "redacta un documento" in low or
        "redáctame un documento" in low or
        "escrito" in low or
        "contrato" in low or
        "demanda" in low or
        "acuerdo" in low or
        "poder" in low or
        "mándamelo" in low or
        "mandamelo" in low or
        "envíamelo" in low or
        "enviamelo" in low
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

    # Queries and document requests should stay in the main pipeline
    if is_query or is_doc_request:
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

async def try_where_were_we(update, chat_id, text) -> bool:
    """
    Bridge Val0 -> Forge graph memory.
    Handles:
    - donde estabamos
    - dónde estábamos
    - where were we
    """
    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))

    triggers = (
        "donde estabamos",
        "where were we",
    )

    if t not in triggers:
        return False

    try:
        out = check_output(
            [
                "ssh",
                "-o", "BatchMode=yes",
                "forge@forge",
                "python3 ~/valeria_graph/where.py",
            ],
            text=True,
            timeout=12,
        ).strip()

        if not out:
            await update.message.reply_text("No encontré contexto recuperable.")
            return True

        await update.message.reply_text(out)
        return True

    except Exception:
        await update.message.reply_text("No pude recuperar el contexto desde Forge.")
        return True

async def try_resume_node(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip()

    if not t.lower().startswith("retoma "):
        return False

    node = t[7:].strip()

    if not node:
        await update.message.reply_text("¿Qué quieres retomar?")
        return True

    try:
        # tell Forge this node was touched
        from subprocess import check_output

        check_output(
            [
                "ssh",
                "-o", "BatchMode=yes",
                "forge@forge",
                f'python3 ~/valeria_graph/touch_node.py "{node}"',
            ],
            text=True,
            timeout=10,
        )

        pretty = " ".join(word.capitalize() for word in node.replace("_", " ").split())

        _ACTIVE_NODE[int(chat_id)] = pretty

        await update.message.reply_text(
            f"📌 Retomando: {pretty}\n\n"
            f"Dime qué quieres hacer con esto y lo ejecutamos."
        )

        return True

    except Exception:
        await update.message.reply_text("No pude retomar ese nodo.")
        return True

async def try_node_followup(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    node = _ACTIVE_NODE.get(int(chat_id))
    if not node:
        return False

    t = (text or "").strip().lower()
    if not t:
        return False

    low_signal = (
        "quiero que esto",
        "esto deberia",
        "esto debería",
        "haz que esto",
        "aqui",
        "aquí",
        "en esto",
        "para esto",
    )

    idea_signals = (
        "quiero que",
        "haz que",
        "deberia",
        "debería",
        "necesito que",
        "podria",
        "podría",
    )

    # if it's a strong idea → let auto-propose handle it
    if any(x in t for x in idea_signals):
        return False

    if not any(x in t for x in low_signal):
        return False

    _LAST_NODE_IDEA[int(chat_id)] = (text or "").strip()   

    await update.message.reply_text(
        f"🧠 Contexto activo: {node}\n\n"
        f"Entendido. Tomo esto como trabajo dentro de {node}.\n"
        f"Ahora dime la regla, comportamiento o resultado exacto que quieres definir."
    )
    return True

async def try_recovery_protocol(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip().lower()

    if "recovery protocol" not in t:
        return False

    try:
        from subprocess import check_output

        base = "/home/forge/valeria_ops"

        current = check_output(
            ["ssh", "-o", "BatchMode=yes", "forge@forge", f"cat {base}/current_state.md"],
            text=True,
            timeout=8
        ).strip()

        tasks = check_output(
            ["ssh", "-o", "BatchMode=yes", "forge@forge", f"cat {base}/tasks.md"],
            text=True,
            timeout=8
        ).strip()

        done = check_output(
            ["ssh", "-o", "BatchMode=yes", "forge@forge", f"tail -n 12 {base}/done_log.md"],
            text=True,
            timeout=8
        ).strip()

        node = check_output(
            ["ssh", "-o", "BatchMode=yes", "forge@forge", "python3 ~/valeria_graph/current_node.py"],
            text=True,
            timeout=8
        ).strip()

        # ------------------------------
        # ACTIVE NODE PRIORITY
        # ------------------------------
        active = _ACTIVE_NODE.get(int(chat_id))

        if active:
            node = active
        elif node:
            _ACTIVE_NODE[int(chat_id)] = node

        # ------------------------------
        # AUTO NEXT TASK (from tasks.md)
        # ------------------------------
        next_line = ""

        for line in tasks.splitlines():
            if line.strip().startswith("- [ ]"):
                next_line = line.replace("- [ ]", "").strip()
                break

        # ------------------------------
        # FALLBACK LOGIC
        # ------------------------------
        if next_line:
            next_action = next_line
        elif node:
            next_action = f"Continúa en {node} y define el siguiente bloque concreto."
        else:
            next_action = "Define el siguiente paso concreto."

        # ------------------------------
        # FINAL MESSAGE
        # ------------------------------
        msg = f"""🧠 SYSTEM RECOVERY

Current Focus:
{current}

Recent Actions:
{done}

Pending:
{tasks}

Active Context:
{node or "No claro"}

⚡ Next Action:
{next_action}
"""

        await update.message.reply_text(msg)
        return True

    except Exception:
        await update.message.reply_text("Recovery protocol failed.")
        return True

async def try_auto_propose_node(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    node = _ACTIVE_NODE.get(int(chat_id))
    if not node:
        return False

    t = (text or "").strip().lower()
    if not t:
        return False

    # skip if explicit commands
    if t in ("convierte esto", "convert this", "hazlo nodo", "hazlo bloque"):
        return False

    # skip if already handled patterns
    if any(x in t for x in (
        "retoma ",
        "donde estabamos",
        "where were we",
    )):
        return False

    # detect "idea-like" messages
    idea_signals = (
        "quiero que",
        "haz que",
        "deberia",
        "debería",
        "necesito que",
        "podria",
        "podría",
    )

    if not any(x in t for x in idea_signals):
        return False

    idea = (text or "").strip()

    title = _normalize_draft_title(idea)
    triggers = _infer_trigger_conditions(idea)
    behavior = _infer_proposed_behavior(idea)

    trigger_preview = ", ".join(triggers[:2])
    behavior_preview = ", ".join(b.split()[0] for b in behavior[:2])

    await update.message.reply_text(
        f"🧠 {node} — propuesta rápida\n\n"
        f"• {title}\n"
        f"• Trigger: {trigger_preview}\n"
        f"• Acción: {behavior_preview}...\n\n"
        f"Si quieres convertir esta idea en un nodo de Forge, dime: sí"
    )

    # store idea anyway for later conversion
    _LAST_NODE_IDEA[int(chat_id)] = idea
    _PENDING_CONVERT[int(chat_id)] = True

    return True


def _normalize_draft_title(raw: str) -> str:
    t = (raw or "").strip()

    replacements = [
        ("quiero que esto ", ""),
        ("quiero que ", ""),
        ("haz que esto ", ""),
        ("haz que ", ""),
        ("esto ", ""),
    ]

    low = t.lower()
    for old, new in replacements:
        if low.startswith(old):
            t = t[len(old):].strip()
            break

    title_map = [
        ("detecte cuando procrastino", "Procrastination Detection"),
        ("detecte procrastinacion", "Procrastination Detection"),
        ("detecte procrastinación", "Procrastination Detection"),
        ("me detecte cuando procrastino", "Procrastination Detection"),
        ("me recuerde", "Reminder Behavior"),
        ("me empuje", "Escalation Behavior"),
        ("me haga follow up", "Follow-Up Behavior"),
    ]

    low = t.lower()
    for pattern, title in title_map:
        if pattern in low:
            return title

    t = t.replace("_", " ").strip()
    if not t:
        return "Draft Update"

    return " ".join(word.capitalize() for word in t.split())


def _infer_trigger_conditions(raw: str) -> list[str]:
    low = (raw or "").lower()

    if "procrastin" in low:
        return [
            "inactividad prolongada",
            "cambio repetido de tareas",
            "evasión de tarea prioritaria",
        ]

    if "record" in low or "recuerde" in low:
        return [
            "tarea pendiente sin avance",
            "vencimiento cercano",
            "ausencia de confirmación",
        ]

    if "follow up" in low or "seguimiento" in low:
        return [
            "compromiso no cumplido",
            "sin respuesta después de intervalo esperado",
            "estado incierto",
        ]

    return [
        "definir trigger principal",
        "definir señal secundaria",
        "definir umbral de activación",
    ]


def _infer_proposed_behavior(raw: str) -> list[str]:
    low = (raw or "").lower()

    if "procrastin" in low:
        return [
            "detectar señales combinadas de procrastinación",
            "activar nudge inicial",
            "escalar tono si no hay acción",
        ]

    if "record" in low or "recuerde" in low:
        return [
            "emitir recordatorio inicial",
            "esperar ventana de respuesta",
            "escalar si sigue pendiente",
        ]

    if "follow up" in low or "seguimiento" in low:
        return [
            "revisar estado del compromiso",
            "enviar seguimiento corto",
            "marcar como pendiente si no hay respuesta",
        ]

    return [
        "definir acción principal",
        "definir escalación",
        "definir resultado esperado",
    ]


def _infer_for_dummies(node: str, raw: str) -> str:
    low = (raw or "").lower()

    if "procrastin" in low:
        return (
            f"Permite que {node} detecte señales de procrastinación antes de que "
            f"el usuario pierda demasiado tiempo o se desvíe por completo."
        )

    if "record" in low or "recuerde" in low:
        return (
            f"Permite que {node} recuerde cosas importantes sin depender de que "
            f"el usuario las pida en el momento exacto."
        )

    return (
        f"Explica en lenguaje simple qué significa esta idea dentro de {node} "
        f"y qué mejora concreta aporta al sistema."
    )

async def try_confirm_convert(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    if not _PENDING_CONVERT.get(int(chat_id)):
        return False

    t = (text or "").strip().lower()

    yes_signals = ("si", "sí", "yes", "dale", "hazlo")

    if t not in yes_signals:
        return False

    # clear flag
    _PENDING_CONVERT[int(chat_id)] = False

    # reuse convert logic
    return await try_convert_node_idea(update, chat_id, "convierte esto")

async def try_convert_node_idea(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip().lower()

    triggers = (
        "convierte esto",
        "convert this",
        "hazlo nodo",
        "hazlo bloque",
    )

    if t not in triggers:
        return False

    node = _ACTIVE_NODE.get(int(chat_id))
    idea = _LAST_NODE_IDEA.get(int(chat_id))

    if not node:
        await update.message.reply_text("No tengo un nodo activo. Usa: retoma <Nodo>")
        return True

    if not idea:
        await update.message.reply_text("No tengo una idea reciente para convertir.")
        return True

    title = _normalize_draft_title(idea)
    trigger_conditions = _infer_trigger_conditions(idea)
    proposed_behavior = _infer_proposed_behavior(idea)
    for_dummies = _infer_for_dummies(node, idea)

    trigger_lines = "\n".join(f"- {x}" for x in trigger_conditions)
    behavior_lines = "\n".join(f"- {x}" for x in proposed_behavior)

    block = (
        f"## Draft Update — {title}\n\n"
        f"### Contexto\n"
        f"Este bloque pertenece a [[{node}]].\n\n"
        f"### Idea Original\n"
        f"{idea}\n\n"
        f"### For Dummies\n"
        f"{for_dummies}\n\n"
        f"### Trigger Conditions\n"
        f"{trigger_lines}\n\n"
        f"### Proposed Behavior\n"
        f"{behavior_lines}\n\n"
        f"### Links\n"
        f"- [[{node}]]\n\n"
        f"### Status\n"
        f"draft\n"
    )

    await update.message.reply_text(
        f"🧩 Borrador listo para Obsidian\n\n```markdown\n{block}```",
        parse_mode="Markdown",
    )
    return True

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
        link = (result.get("link") or "").strip()

        msg = (
            f"📅 Evento creado\n\n"
            f"Título: {title}\n"
            f"Inicio: {start_dt.strftime('%Y-%m-%d %I:%M %p')}"
        )

        if link:
            msg += f"\nLink: {link}"

        await update.message.reply_text(msg, disable_web_page_preview=True)
        return True

    await update.message.reply_text("No pude crear el evento.")
    return True

def _is_pm_admin_request(text: str) -> bool:
    low = (text or "").strip().lower()
    return low.startswith("/focus") or low.startswith("/showfocus") or low.startswith("/pm")

def _looks_like_doc_request(text: str) -> bool:
    low = unicodedata.normalize("NFKD", (text or "").lower())
    low = "".join(ch for ch in low if not unicodedata.combining(ch))

    doc_triggers = (
        "contrato",
        "hazme un contrato",
        "generame un contrato",
        "modelo de",
        "borrador de",
        "acuerdo",
        "convenio",
        "documento",
    )
    return any(t in low for t in doc_triggers)

def _is_pm_drift_candidate(text: str) -> bool:
    low = (text or "").lower()
    markers = (
        "watch", "wear", "alexa", "ui", "interfaz", "theme", "tema",
        "app", "aplicacion", "aplicación", "multidevice", "device",
        "speaker", "audio flow", "book", "newspaper",
    )
    return any(m in low for m in markers)


def _is_karen_client_ops_intent(text: str) -> bool:
    """
    Guardrail: Frank Operator / PM drift redirects must never leak into Karen/client flows.

    Karen may say things like:
    - "Registra cita para mañana con Mabel, tema libro Finca 10082"
    - "Val que tengo mañana"
    - "recuérdame una hora antes..."
    - grocery/list/supermarket commands

    Words like "tema" can look like PM/product drift, but in Karen context they are normal
    client/case/agenda language.
    """
    low = (text or "").lower()

    client_markers = (
        "cita",
        "reunion",
        "reunión",
        "recordatorio",
        "recuerdame",
        "recuérdame",
        "recordarme",
        "agenda",
        "que tengo hoy",
        "qué tengo hoy",
        "que tengo mañana",
        "qué tengo mañana",
        "que tengo esta semana",
        "qué tengo esta semana",
        "finca",
        "nora",
        "mabel",
        "abogado",
        "abogada",
        "juzgado",
        "oficio",
        "documento",
        "supermercado",
        "super",
        "súper",
        "lista",
        "comprar",
        "google calendar",
        "calendario",
    )

    return any(marker in low for marker in client_markers)


def _build_pm_redirect_reply(pm_state: dict) -> str:
    return (
        f"No ahora. Eso es drift.\n\n"
        f"Foco actual: {pm_state.get('current_focus', '')}\n"
        f"Decisión: {pm_state.get('decision', '')}\n"
        f"Siguiente acción: {pm_state.get('next_action', '')}"
    ).strip()

def _build_pm_system_block(pm_state: dict) -> str:
    return (
        "\nPM LOOP (INTERNAL)\n"
        f"- current_focus: {pm_state.get('current_focus', '')}\n"
        f"- decision: {pm_state.get('decision', '')}\n"
        f"- reason: {pm_state.get('reason', '')}\n"
        f"- next_action: {pm_state.get('next_action', '')}\n"
        "Rules:\n"
        "- Keep the response aligned with current_focus.\n"
        "- If decision is DEFER, acknowledge briefly and redirect.\n"
        "- If decision is DISCARD, do not expand the idea.\n"
        "- Do not expose this PM block unless the user is drifting, debugging, or explicitly asks.\n"
    )


async def focus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    raw = " ".join(context.args).strip() if context.args else ""
    if not raw:
        return await update.message.reply_text("Uso: /focus titulo | resumen | roadmap")

    parts = [p.strip() for p in raw.split("|")]
    title = parts[0] if len(parts) > 0 else "General execution"
    summary = parts[1] if len(parts) > 1 else ""
    roadmap = parts[2] if len(parts) > 2 else ""

    set_pm_focus(int(chat_id), title, summary, roadmap)
    await update.message.reply_text("Focus updated.")


async def showfocus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    focus = get_pm_focus(int(chat_id))
    msg = (
        f"Current focus: {focus.get('focus_title', '')}\n"
        f"Summary: {focus.get('focus_summary', '')}\n"
        f"Roadmap: {focus.get('roadmap_note', '')}"
    ).strip()
    await update.message.reply_text(msg)

def _infer_focus_candidate(text: str) -> dict | None:
    low = (text or "").lower().strip()

    pm_memory_markers = (
        "pm loop", "pm", "bertha", "memory", "memoria", "session memory",
        "session continuity", "continuity", "context", "contexto",
        "pipeline", "bot.py", "val0", "focus", "foco",
    )

    calendar_markers = (
        "calendar", "calendario", "agenda", "evento", "event", "reminder",
        "recordatorio", "gcal", "google calendar",
    )

    miguel_demo_markers = (
        "miguel", "demo", "demo readiness",
    )

    if any(m in low for m in pm_memory_markers):
        return {
            "focus_title": "Val0 PM + session continuity",
            "focus_summary": "Implement automatic focus control and conversational continuity in Val0",
            "roadmap_note": "Defer watch/UI/device work until after MVP",
        }

    if any(m in low for m in calendar_markers):
        return {
            "focus_title": "Val0 calendar + reminder hardening",
            "focus_summary": "Harden calendar, reminder, and agenda reliability for MVP",
            "roadmap_note": "Keep conversational continuity and PM stable while tightening utility flows",
        }

    if any(m in low for m in miguel_demo_markers):
        return {
            "focus_title": "Miguel demo readiness",
            "focus_summary": "Prepare a stable, guided, promise-safe Val0 demo flow for Miguel",
            "roadmap_note": "Prioritize continuity, reminders, and useful execution over side features",
        }

    return None


def _is_focus_switch_signal(text: str) -> bool:
    low = (text or "").lower().strip()
    markers = (
        "switch to",
        "let's work on",
        "lets work on",
        "now let's do",
        "now lets do",
        "vamos con",
        "cambiemos a",
        "ahora trabajemos en",
        "trabajemos en",
    )
    return any(m in low for m in markers)


def _is_focus_continue_signal(text: str) -> bool:
    low = (text or "").lower().strip()
    markers = (
        "continue",
        "keep going",
        "what were we doing",
        "where were we",
        "the other thing",
        "seguimos",
        "continua",
        "continúa",
        "que estabamos haciendo",
        "qué estábamos haciendo",
        "en que ibamos",
        "en qué íbamos",
    )
    return any(m in low for m in markers)


def _maybe_autoset_focus(chat_id: int, text: str) -> dict:
    current = get_pm_focus(int(chat_id))
    candidate = _infer_focus_candidate(text)

    # If the user is clearly asking to continue/recover, keep current focus sticky.
    if _is_focus_continue_signal(text):
        return current

    # No strong candidate detected: keep current focus as-is.
    if not candidate:
        return current

    current_title = (current.get("focus_title") or "").strip()
    candidate_title = (candidate.get("focus_title") or "").strip()

    # If current focus is generic/unset, auto-bootstrap.
    if not current_title or current_title == "General execution":
        set_pm_focus(
            int(chat_id),
            candidate["focus_title"],
            candidate["focus_summary"],
            candidate["roadmap_note"],
        )
        return get_pm_focus(int(chat_id))

    # If candidate matches current, refresh timestamp implicitly by rewriting same focus.
    if current_title == candidate_title:
        set_pm_focus(
            int(chat_id),
            candidate["focus_title"],
            candidate["focus_summary"],
            candidate["roadmap_note"],
        )
        return get_pm_focus(int(chat_id))

    # Auto-promote from broad demo focus into active implementation lane
    # when the new message strongly matches PM/memory work.
    if current_title == "Miguel demo readiness" and candidate_title == "Val0 PM + session continuity":
        set_pm_focus(
            int(chat_id),
            candidate["focus_title"],
            candidate["focus_summary"],
            candidate["roadmap_note"],
        )
        return get_pm_focus(int(chat_id))

    # Only switch other focus lanes automatically when the user gives a strong switch signal.
    if _is_focus_switch_signal(text):
        set_pm_focus(
            int(chat_id),
            candidate["focus_title"],
            candidate["focus_summary"],
            candidate["roadmap_note"],
        )
        return get_pm_focus(int(chat_id))

    # Otherwise keep current focus sticky.
    return current

def _is_continuation_query(text: str) -> bool:
    low = (text or "").lower().strip()
    markers = (
        "continue",
        "okay continue",
        "ok continue",
        "keep going",
        "what was the last concrete thing",
        "what were we doing",
        "where were we",
        "summarize that",
        "turn that into 3 steps",
        "turn it into 3 steps",
        "what are step 2 and step 3",
        "no, continue with launch",
        "continue with launch",
        "continue with the real priority",
        "no, continue with the real priority",
        "not that, continue",
        "seguimos",
        "continua",
        "continúa",
        "sigue con launch",
        "sigue con lo real",
        "sigue con la prioridad real",
        "no, sigue con launch",
        "no, sigue con lo real",
        "resume eso",
        "resumelo",
        "resúmelo",
        "conviertelo en 3 pasos",
        "conviértelo en 3 pasos",
        "que estabamos haciendo",
        "qué estábamos haciendo",
        "cual era la ultima cosa concreta",
        "cuál era la última cosa concreta",
        "en que ibamos",
        "en qué íbamos",
    )
    return any(m in low for m in markers)


def _get_last_user_work_message(chat_id: int) -> str:
    try:
        rows = fetch_recent_messages(int(chat_id), limit=20)
    except Exception:
        return ""

    skip_markers = (
        "continue",
        "okay continue",
        "ok continue",
        "keep going",
        "what was the last concrete thing",
        "what were we doing",
        "where were we",
        "summarize that",
        "turn that into 3 steps",
        "turn it into 3 steps",
        "what are step 2 and step 3",
        "seguimos",
        "sigue",
        "continua",
        "continúa",
        "resume eso",
        "resumelo",
        "resúmelo",
        "conviertelo en 3 pasos",
        "conviértelo en 3 pasos",
        "que estabamos haciendo",
        "qué estábamos haciendo",
        "que tengo manana",
        "que audiencias tengo manana",
        "que vence manana",
        "recuérdame",
        "recuerdame",
        "agenda manana",
        "agenda mañana",
        "foco actual",
        "current focus",
        )

    stale_lane_markers = (
        "val0 pm + session continuity",
        "implement automatic focus control and conversational continuity in val0",
        "defer watch/ui/device work until after mvp",
        "revisar contrato",
        "llamar a miguel",
        "audiencia del 15 de abril",
    )

    seen = set()

    for row in reversed(rows):
        role = (row.get("role") or "").strip().lower()
        content = (row.get("content") or "").strip()

        if role != "user":
            continue
        if not content:
            continue
        if content in seen:
            continue
        seen.add(content)

        low = unicodedata.normalize("NFKD", content.lower())
        low = "".join(ch for ch in low if not unicodedata.combining(ch))
        low = re.sub(r"[¿?¡!.,:;]+", "", low).strip()

        if any(m in low for m in skip_markers):
            continue
        if any(m in low for m in stale_lane_markers):
            continue

        return content

    return ""

def _extract_send_email_payload(text: str) -> tuple[str, str]:
    """
    Returns (target_name, body_text) for patterns like:
    - mandale un email a frank que diga: hola
    - enviale un correo a frank diciendo hola
    - send an email to frank that says hello
    """
    raw = (text or "").strip()
    norm = unicodedata.normalize("NFKD", raw.lower())
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))

    patterns = [
        r"mandale un email a ([a-z0-9_.-]+)\s+que diga[:\s]+(.+)$",
        r"mandale un correo a ([a-z0-9_.-]+)\s+que diga[:\s]+(.+)$",
        r"enviale un email a ([a-z0-9_.-]+)\s+que diga[:\s]+(.+)$",
        r"enviale un correo a ([a-z0-9_.-]+)\s+que diga[:\s]+(.+)$",
        r"send an email to ([a-z0-9_.-]+)\s+that says[:\s]+(.+)$",
    ]

    for pat in patterns:
        m = re.match(pat, norm, flags=re.IGNORECASE)
        if m:
            who = (m.group(1) or "").strip().lower()
            body = (m.group(2) or "").strip()
            return who, body

    return "", ""

def _extract_redirect_target(text: str) -> str:
    raw = (text or "").strip()
    norm = unicodedata.normalize("NFKD", raw.lower())
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = re.sub(r"[¿?¡!.,:;]+", "", norm).strip()

    patterns = [
        r"no mejor enviaselo a ([a-z0-9_.-]+)$",
        r"no mejor mandaselo a ([a-z0-9_.-]+)$",
        r"enviaselo mejor a ([a-z0-9_.-]+)$",
        r"mandaselo mejor a ([a-z0-9_.-]+)$",
        r"send it to ([a-z0-9_.-]+) instead$",
        r"send the last email to ([a-z0-9_.-]+) instead$",
    ]

    for pat in patterns:
        m = re.match(pat, norm, flags=re.IGNORECASE)
        if m:
            return (m.group(1) or "").strip().lower()

    return ""

def _extract_redirect_sent_message_target(text: str) -> str:
    raw = (text or "").strip()
    norm = unicodedata.normalize("NFKD", raw.lower())
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = re.sub(r"[¿?¡!.,:;]+", "", norm).strip()

    patterns = [
        r"no mejor mandale ese email a ([a-z0-9_.-]+)$",
        r"no mejor enviaselo a ([a-z0-9_.-]+)$",
        r"no mejor mandaselo a ([a-z0-9_.-]+)$",
        r"mandale ese email a ([a-z0-9_.-]+)$",
        r"enviaselo a ([a-z0-9_.-]+)$",
        r"send that to ([a-z0-9_.-]+) instead$",
        r"send the last message to ([a-z0-9_.-]+) instead$",
    ]

    for pat in patterns:
        m = re.match(pat, norm, flags=re.IGNORECASE)
        if m:
            return (m.group(1) or "").strip().lower()

    return ""

def _extract_copy_target(text: str) -> str:
    raw = (text or "").strip()
    norm = unicodedata.normalize("NFKD", raw.lower())
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = re.sub(r"[¿?¡!.,:;]+", "", norm).strip()

    patterns = [
        r"mandale una copia a ([a-z0-9_.-]+)$",
        r"mandale copia a ([a-z0-9_.-]+)$",
        r"enviale una copia a ([a-z0-9_.-]+)$",
        r"enviale copia a ([a-z0-9_.-]+)$",
        r"send a copy to ([a-z0-9_.-]+)$",
        r"send it to ([a-z0-9_.-]+) too$",
        r"cc ([a-z0-9_.-]+)$",
    ]

    for pat in patterns:
        m = re.match(pat, norm, flags=re.IGNORECASE)
        if m:
            return (m.group(1) or "").strip().lower()

    return ""


def build_alpha_onboarding_reply(preferred_name: str = "") -> str:
    preferred_name = (preferred_name or "").strip()
    greeting = f"👀 Hola, {preferred_name}. " if preferred_name else "👀 Hola. "
    name_prompt = "" if preferred_name else "\n\nAntes de empezar: dime cómo quieres que te llame."

    return (
        f"{greeting}Soy Valeria, una asistente en founder beta dentro de Telegram. "
        "Estoy para ayudarte a recordar, capturar y organizar cosas simples del día sin que todo viva en tu cabeza.\n\n"
        "Prueba con una de estas:\n"
        "1. Guarda esta nota: comprar leche\n"
        "2. Recuérdame llamar mañana a las 9\n"
        "3. Tengo una idea: Val debería ayudarme a no perder foco\n"
        "4. ¿Qué tengo mañana?\n"
        "5. Estoy perdida, ¿qué hago?\n\n"
        "Si quieres ver más opciones, escribe: Ayuda"
        f"{name_prompt}"
    )


def build_alpha_capability_reply(preferred_name: str = "") -> str:
    safe_name = (preferred_name or "").strip()
    name_line = f"{safe_name}, " if safe_name and safe_name.lower() not in ("boss", "jefe") else ""

    return (
        f"{name_line}Puedo ayudarte a bajar el ruido del día: guardar cosas, recordarte pendientes "
        "y recuperar el hilo cuando se te empieza a llenar la cabeza.\n\n"
        "Ahora mismo soy útil para:\n"
        "• 📝 Notas: Guarda esta nota: comprar leche\n"
        "• ⏰ Recordatorios: Recuérdame llamar mañana a las 9\n"
        "• ✅ Tareas: Tengo que revisar X\n"
        "• 💡 Ideas: Tengo una idea: Val debería ayudarme a no perder foco\n"
        "• 🎙️ Voz: puedes mandarme notas de voz\n"
        "• 🧭 Recuperación: Estoy perdida, ¿qué hago?\n\n"
        "Siguiente paso: mándame una nota, idea o recordatorio simple y lo probamos."
    )




def route_operator_intent(
    chat_id: int,
    user_text: str,
    preferred_language: str | None = None,
) -> dict:
    """
    Val0 Operator Router v1.
    Purpose:
    - infer whether natural user text should route to a known safe operator action
    - DO NOT execute actions here
    - deterministic pipeline decides what to run
    """
    import json

    text = (user_text or "").strip()
    if not text:
        return {
            "route": "normal_chat",
            "confidence": 1.0,
            "reason": "empty input",
            "needs_clarification": False,
            "clarifying_question": "",
        }

    system_rules = """
You are Val0's Operator Router v1.

Return ONLY valid JSON. No markdown. No prose.

Your job:
Classify the user's message into ONE route.

Allowed routes:
- whatnow
- exosummary
- draft_followup
- journal_capture
- flow_request
- normal_chat
- clarify

Route meanings:
- whatnow: user asks what to do next, where to start, what now, feels lost and wants next step
- exosummary: user asks what was saved, what Val remembers from the latest capture, summary of what was captured
- draft_followup: user asks Val to write/draft/prepare a message, reply, follow-up, or wording based on recent context
- journal_capture: user is telling a life/work/business update/story that should be saved/sorted
- flow_request: user asks for a new capability/workflow that is not currently built or wants it added to roadmap
- normal_chat: general question, explanation, casual chat, or anything that should not trigger a tool/action
- clarify: user intent is ambiguous and one short clarification is needed

Rules:
- You route. You do not execute.
- Prefer normal_chat if unsure.
- Use high confidence only when intent is clear.
- If user says "what should I do", "what should I do first", "what do I do first", "qué hago", "qué debería hacer primero", "qué hago primero", "por dónde empiezo", route whatnow.
- If the user asks for prioritization, first step, next step, or where to begin, route whatnow.
- If user says "what did you save", "qué guardaste", "muéstrame el resumen", route exosummary.
- If user says "write the message", "hazme el mensaje", "redáctame eso", "qué le digo", route draft_followup.
- If user tells a messy story/update about their day/work/life with enough detail, route journal_capture.
- If user says "add this to roadmap", "could Val do X later", "feature request", "flow request", route flow_request.
- Never route to draft_followup unless the user is asking for wording/message/reply/follow-up.
- Never route to whatnow just because user is emotional unless they ask for next action/help deciding.

JSON schema:
{
  "route": "whatnow|exosummary|draft_followup|journal_capture|flow_request|normal_chat|clarify",
  "confidence": 0.0,
  "reason": "short factual reason",
  "needs_clarification": false,
  "clarifying_question": ""
}
"""

    try:
        raw = call_val_openai(
            chat_id=int(chat_id),
            user_text=text,
            forced_lang=preferred_language or "es",
            system_rules=system_rules,
        )
        raw = (raw or "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        if not isinstance(data, dict):
            raise ValueError("router returned non-dict JSON")

        allowed_routes = {
            "whatnow",
            "exosummary",
            "draft_followup",
            "journal_capture",
            "flow_request",
            "normal_chat",
            "clarify",
        }

        route = str(data.get("route") or "normal_chat").strip()
        if route not in allowed_routes:
            route = "normal_chat"

        try:
            confidence = float(data.get("confidence") or 0.0)
        except Exception:
            confidence = 0.0

        return {
            "route": route,
            "confidence": confidence,
            "reason": str(data.get("reason") or "").strip(),
            "needs_clarification": bool(data.get("needs_clarification") or False),
            "clarifying_question": str(data.get("clarifying_question") or "").strip(),
        }

    except Exception as e:
        logger.exception(f"[OPERATOR_ROUTER] failed: {e}")
        return {
            "route": "normal_chat",
            "confidence": 0.0,
            "reason": f"router failed: {e}",
            "needs_clarification": False,
            "clarifying_question": "",
        }


def classify_exocortex_intent(
    chat_id: int,
    user_text: str,
    preferred_language: str | None = None,
) -> dict:
    """
    Val0 Exocortex Mark 1 classifier.
    Purpose:
    - classify messy user input into structured intent/buckets
    - DO NOT execute actions here
    - deterministic code decides storage/reminders/tasks afterward
    """
    import json

    text = (user_text or "").strip()
    if not text:
        return {
            "intent": "empty",
            "confidence": 1.0,
            "buckets": [],
            "summary": "",
            "suggested_action": "ignore",
            "needs_clarification": False,
            "clarifying_question": "",
        }

    system_rules = """
You are Val0's Exocortex Mark 1 intent classifier.

Return ONLY valid JSON. No markdown. No prose.

Classify the user's message into one or more buckets.

Allowed buckets:
- note
- reminder
- task
- idea
- reflection
- care_mode
- decision
- parking_lot
- project
- follow_up
- normal_chat

Rules:
- You classify. You do not execute.
- If the user is venting, discouraged, overwhelmed, spiraling, or emotionally processing, include reflection.
- If the user asks Val to take charge, calm them down, stop them, or decide what to do, include care_mode.
- If the user mentions a future time/date and wants to be reminded, include reminder.
- If the user says they have an idea, include idea.
- If the user describes something to remember without action, include note.
- If the message contains multiple things, return multiple buckets.
- If buckets has more than one item, suggested_action should usually be "multi_action".
- If a person/client/customer/provider/supplier still needs something, include follow_up.
- If the user says someone "needs" something, "is waiting", "didn't answer", "hasn't replied", or "still needs X", include follow_up.
- If a supplier/provider/vendor did not answer or caused friction, include follow_up and summarize it as supplier/provider friction.
- If business context appears, preserve concrete entities in summary: people, client names, supplier/provider, quote, payment, appointment, delivery.
- If uncertain, use normal_chat and set needs_clarification true only if needed.
- Keep summary short and factual, but include concrete action/context items.
- Do not invent details.
- For story-like or long messages, extract separate items.
- Each meaningful memory/action should become its own item.
- Do not give every item the same generic summary if the message contains multiple distinct things.
- Example:
  User says: "Today was awful. Carlos needs the quote. Supplier did not answer. Save idea: track suppliers."
  items should include:
  reflection: user had a rough/overwhelming day
  follow_up: Carlos needs the quote
  follow_up: supplier did not answer
  idea: track supplier follow-ups

JSON schema:
{
  "intent": "short_primary_intent",
  "confidence": 0.0,
  "buckets": ["bucket1"],
  "summary": "short overall summary",
  "items": [
    {
      "bucket": "reflection|follow_up|idea|note|task|reminder|care_mode|decision|parking_lot|project|normal_chat",
      "summary": "specific summary for this one item",
      "raw_span": "short original fragment if useful"
    }
  ],
  "suggested_action": "store_reflection|store_note|create_reminder|store_idea|ask_clarifying_question|reply_only|multi_action",
  "needs_clarification": false,
  "clarifying_question": ""
}
"""

    try:
        raw = call_val_openai(
            chat_id=int(chat_id),
            user_text=text,
            forced_lang=preferred_language or "es",
            system_rules=system_rules,
        )
        raw = (raw or "").strip()
        # Strip accidental code fences if model misbehaves.
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        if not isinstance(data, dict):
            raise ValueError("classifier returned non-dict JSON")

        data.setdefault("intent", "normal_chat")
        data.setdefault("confidence", 0.0)
        data.setdefault("buckets", ["normal_chat"])
        data.setdefault("summary", "")
        data.setdefault("items", [])
        data.setdefault("suggested_action", "reply_only")
        data.setdefault("needs_clarification", False)
        data.setdefault("clarifying_question", "")

        if not isinstance(data.get("buckets"), list):
            data["buckets"] = ["normal_chat"]

        if not isinstance(data.get("items"), list):
            data["items"] = []

        clean_items = []
        allowed_item_buckets = {
            "note", "reminder", "task", "idea", "reflection", "care_mode",
            "decision", "parking_lot", "project", "follow_up", "normal_chat"
        }

        for item in data.get("items", []):
            if not isinstance(item, dict):
                continue
            bucket = str(item.get("bucket") or "").strip()
            if bucket not in allowed_item_buckets:
                bucket = "normal_chat"
            item_summary = str(item.get("summary") or "").strip()
            raw_span = str(item.get("raw_span") or "").strip()
            clean_items.append({
                "bucket": bucket,
                "summary": item_summary,
                "raw_span": raw_span,
            })

        data["items"] = clean_items

        return data

    except Exception as e:
        logger.exception(f"[EXOCORTEX_CLASSIFIER] failed: {e}")
        return {
            "intent": "normal_chat",
            "confidence": 0.0,
            "buckets": ["normal_chat"],
            "summary": text[:180],
            "suggested_action": "reply_only",
            "needs_clarification": False,
            "clarifying_question": "",
        }


def build_dynamic_founder_beta_reply(
    chat_id: int,
    user_text: str,
    kind: str,
    preferred_name: str = "",
    preferred_language: str | None = None,
) -> str | None:
    """
    Dynamic founder-beta identity/capability answer.
    Deterministic intent, model-written wording, safe facts.
    Falls back to static builders if model fails.
    """
    safe_name = (preferred_name or "").strip()
    name_rule = ""
    if safe_name and safe_name.lower() not in ("boss", "jefe"):
        name_rule = f"Puedes usar este nombre si suena natural: {safe_name}."

    safe_facts = """
FOUNDER-BETA SAFE FACTS:
- Eres Valeria, dentro de Val0.
- Val0 está en founder beta.
- La interfaz actual es Telegram porque es rápida, familiar y permite texto/voz.
- Telegram es la primera puerta, no necesariamente la identidad final del producto.
- Ayudas con notas, recordatorios, tareas, ideas, voz, pendientes y agenda básica.
- No prometas memoria perfecta, autonomía total, app final, ni confiabilidad enterprise.
- No inventes funciones.
- Responde breve, cálido, práctico y no corporativo.
- Máximo 2 párrafos o 5 bullets.
- No abras con "Hola, aquí Valeria" salvo que el usuario esté saludando.
- No suenes como brochure ni repitas siempre la misma estructura.
- Si explicas capacidades, incluye 2-4 ejemplos concretos.
- Puedes decir que creas recordatorios; NO digas que no generas notificaciones.
- No exageres calendario: di "agenda básica", no "gestionar calendario completo".
- Termina con un paso simple solo si ayuda.
"""

    if kind == "identity":
        task = (
            "El usuario pregunta qué eres. Responde como Valeria en español. "
            "Explica identidad, Telegram como primera interfaz, beta y utilidad real sin sobreprometer."
        )
    elif kind == "capability":
        task = (
            "El usuario pregunta qué puedes hacer. Responde como Valeria en español. "
            "Explica capacidades actuales con ejemplos concretos y límites honestos."
        )
    else:
        return None

    try:
        reply = call_val_openai(
            chat_id=int(chat_id),
            user_text=user_text,
            forced_lang=preferred_language or "es",
            system_rules=safe_facts + "\n" + name_rule + "\n" + task,
        )
        reply = (reply or "").strip()
        if not reply:
            return None

        # Founder-beta safety polish: prevent misleading reminder/notification wording.
        notification_replacements = {
            "no genero notificaciones automáticas": "puedo crear recordatorios para avisarte, aunque todavía no soy un calendario completo",
            "No genero notificaciones automáticas": "Puedo crear recordatorios para avisarte, aunque todavía no soy un calendario completo",
            "no puedo enviar notificaciones": "puedo crear recordatorios para avisarte",
            "No puedo enviar notificaciones": "Puedo crear recordatorios para avisarte",
            "tampoco genero notificaciones automáticas": "sí puedo crear recordatorios para avisarte",
            "Tampoco genero notificaciones automáticas": "Sí puedo crear recordatorios para avisarte",
        }
        for bad, good in notification_replacements.items():
            reply = reply.replace(bad, good)

        # Broader cleanup: the model sometimes says "no esperes notificaciones..."
        # which is misleading because Val0 can create reminders that notify.
        reply = re.sub(
            r"(?i)(no\s+esperes\s+notificaciones\s+autom[aá]ticas)",
            "puedo crear recordatorios para avisarte",
            reply,
        )
        reply = re.sub(
            r"(?i)(no\s+(puedo|genera|genero|manejo|env[ií]o)\s+notificaciones\s+autom[aá]ticas)",
            "puedo crear recordatorios para avisarte",
            reply,
        )

        return reply
    except Exception:
        return None


def build_alpha_lost_reply(preferred_name: str = "") -> str:
    safe_name = (preferred_name or "").strip()
    name_line = f"{safe_name}, " if safe_name and safe_name.lower() not in ("boss", "jefe") else ""

    return (
        f"{name_line}Tranquilo. No hay que resolver la vida completa ahorita. "
        "Vamos por una cosa.\n\n"
        "Escoge una:\n"
        "1. Revisar qué tienes pendiente\n"
        "2. Crear un recordatorio\n"
        "3. Guardar una nota o idea\n\n"
        "Si no sabes cuál, mándame: ¿Qué tengo pendiente?"
    )



def build_unified_pending_dashboard(chat_id: int) -> str:
    """
    User-facing pending dashboard.
    Combines open tasks + pending reminders so "¿Qué tengo pendiente?"
    does not fall into narrow legal/today-only priority logic.
    """
    from datetime import datetime, timezone, timedelta
    from zoneinfo import ZoneInfo
    from memory_store import _get_conn, fetch_open_commitments

    tz = ZoneInfo("America/Panama")
    now_local = datetime.now(tz)
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    tasks = []
    reminders = []

    try:
        rows = fetch_open_commitments(int(chat_id), limit=10) or []
        for r in rows:
            row = dict(r) if hasattr(r, "keys") else r
            raw = str(row.get("raw_input") or "").strip()
            due = str(row.get("due_date") or "").strip()

            if raw:
                if due:
                    tasks.append(f"- {raw} ({due[:10]})")
                else:
                    tasks.append(f"- {raw}")
    except Exception as e:
        tasks.append(f"- No pude leer tareas: {e}")

    try:
        conn = _get_conn()
        cur = conn.cursor()
        rows = cur.execute(
            """
            SELECT id, text, due_at_utc, status
            FROM reminders
            WHERE chat_id = ?
              AND status = 'pending'
              AND due_at_utc >= ?
            ORDER BY due_at_utc ASC, id ASC
            LIMIT 10
            """,
            (int(chat_id), now_utc),
        ).fetchall()
        conn.close()

        for r in rows:
            row = dict(r) if hasattr(r, "keys") else {
                "id": r[0],
                "text": r[1],
                "due_at_utc": r[2],
                "status": r[3],
            }

            due_raw = str(row.get("due_at_utc") or "")
            label = due_raw[:16]
            try:
                due_dt = datetime.strptime(due_raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(tz)
                if due_dt.date() == now_local.date():
                    label = "hoy " + due_dt.strftime("%H:%M")
                else:
                    label = due_dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

            txt = _display_karen_reminder_title(str(row.get("text") or "").strip()) or f"recordatorio #{row.get('id')}"
            reminders.append(f"- {label} · {txt}")

    except Exception as e:
        reminders.append(f"- No pude leer recordatorios: {e}")

    lines = ["📌 Pendiente", ""]

    lines.append("✅ Tareas abiertas")
    if tasks:
        lines.extend(tasks)
    else:
        lines.append("- No tienes tareas abiertas.")

    lines.append("")
    lines.append("⏰ Recordatorios pendientes")
    if reminders:
        lines.extend(reminders)
    else:
        lines.append("- No tienes recordatorios pendientes.")

    lines.append("")
    lines.append("Siguiente paso: puedo ayudarte a ordenar esto por prioridad o cerrar algo que ya hiciste.")

    return "\n".join(lines)

def build_unified_tomorrow_dashboard(chat_id: int) -> str:
    """
    User-facing tomorrow dashboard.
    Combines reminders + open commitments so normal users don't see contradictory answers.
    """
    _clear_karen_numbered_action_dirty(chat_id)
    _KAREN_REMINDER_LIST_CONTEXT[int(chat_id)] = "agenda"
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo
    from memory_store import _get_conn

    tz = ZoneInfo("America/Panama")
    tomorrow_dt = datetime.now(tz) + timedelta(days=1)
    tomorrow_date = tomorrow_dt.date().isoformat()

    weekday = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][tomorrow_dt.weekday()]
    month = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][tomorrow_dt.month]
    pretty = f"{weekday} {tomorrow_dt.day} {month}"

    start_local = datetime(tomorrow_dt.year, tomorrow_dt.month, tomorrow_dt.day, 0, 0, 0, tzinfo=tz)
    end_local = datetime(tomorrow_dt.year, tomorrow_dt.month, tomorrow_dt.day, 23, 59, 59, tzinfo=tz)
    start_utc = start_local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_utc = end_local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    reminders = []
    tasks = []
    reminder_like_tasks = []

    conn = _get_conn()
    cur = conn.cursor()

    try:
        rows = cur.execute(
            """
            SELECT id, text, due_at_utc, status
            FROM reminders
            WHERE chat_id = ?
              AND status = 'pending'
              AND due_at_utc >= ?
              AND due_at_utc <= ?
            ORDER BY due_at_utc ASC, id ASC
            """,
            (int(chat_id), start_utc, end_utc),
        ).fetchall()

        for r in rows:
            row = dict(r) if hasattr(r, "keys") else {
                "id": r[0],
                "text": r[1],
                "due_at_utc": r[2],
                "status": r[3],
            }
            due_raw = str(row.get("due_at_utc") or "")
            label = ""
            try:
                due_dt = datetime.strptime(due_raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(tz)
                label = due_dt.strftime("%H:%M")
            except Exception:
                label = due_raw[:16]

            txt = _display_karen_reminder_title(str(row.get("text") or "").strip()) or f"recordatorio #{row.get('id')}"
            reminders.append({"id": row.get("id"), "time": label, "text": txt})

    except Exception as e:
        reminders.append(f"- No pude leer recordatorios: {e}")

    try:
        rows = cur.execute(
            """
            SELECT id, raw_input, action, target, due_date, status
            FROM commitments
            WHERE chat_id = ?
              AND status = 'open'
              AND substr(COALESCE(due_date, ''), 1, 10) = ?
            ORDER BY id ASC
            """,
            (int(chat_id), tomorrow_date),
        ).fetchall()

        for r in rows:
            row = dict(r) if hasattr(r, "keys") else {
                "id": r[0],
                "raw_input": r[1],
                "action": r[2],
                "target": r[3],
                "due_date": r[4],
                "status": r[5],
            }

            raw = str(row.get("raw_input") or "").strip()
            if raw:
                item = {"id": row.get("id"), "text": raw}
            else:
                action = str(row.get("action") or "").strip()
                target = str(row.get("target") or "").strip()
                label = " ".join(x for x in [action, target] if x).strip() or f"tarea #{row.get('id')}"
                item = {"id": row.get("id"), "text": label}
            if _looks_like_reminder_command_text(item["text"]):
                reminder_like_tasks.append(item)
            else:
                tasks.append(item)

    except Exception as e:
        tasks.append(f"- No pude leer tareas: {e}")

    conn.close()

    lines = [f"📅 Mañana ({pretty})", ""]

    lines.append("⏰ Recordatorios de Val")
    if reminders:
        for idx, item in enumerate(reminders, start=1):
            if isinstance(item, dict):
                lines.append(f"{idx}. {item['time']} · {item['text']}{_karen_reminder_time_note(item['text'], item['time'])}")
            else:
                lines.append(f"- {item}")
    else:
        lines.append("- No tienes recordatorios para mañana.")

    lines.append("")
    lines.append("📌 Tareas de Val")
    task_display_number = 1
    if tasks:
        for item in tasks:
            if isinstance(item, dict):
                lines.append(f"{task_display_number}. {item['text']}")
                item["display_number"] = task_display_number
                task_display_number += 1
            else:
                lines.append(f"- {item}")
    else:
        lines.append("- No tienes tareas con fecha para mañana.")

    if reminder_like_tasks:
        lines.extend(["", "⚠️ Posible recordatorio guardado como tarea"])
        warning_numbers = []
        for item in reminder_like_tasks:
            lines.append(f"{task_display_number}. {item['text']}")
            warning_numbers.append(task_display_number)
            item["display_number"] = task_display_number
            task_display_number += 1
        if warning_numbers:
            first_warning = warning_numbers[0]
            lines.append(f"Puedes decir: “marca la tarea {first_warning} como hecha”. Todavía no convierto tareas a recordatorios automáticamente.")

    action_lines = ["", "Acciones útiles:"]
    if reminders:
        action_lines.append("- elimina el recordatorio 1")
        edit_number = 2 if len(reminders) >= 2 else 1
        action_lines.append(f"- cambia el recordatorio {edit_number} para las 11")
    if tasks or reminder_like_tasks:
        action_lines.extend([
            "- marca la tarea 1 como hecha",
            "- elimina la tarea 1",
        ])
    if len(action_lines) > 2:
        lines.extend(action_lines)

    return "\n".join(lines)


def _karen_number_word_to_int(value: str) -> int | None:
    norm = _norm_text(value or "")
    words = {
        "uno": 1,
        "una": 1,
        "primer": 1,
        "primero": 1,
        "dos": 2,
        "segundo": 2,
        "tres": 3,
        "tercero": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
        "nueve": 9,
        "diez": 10,
    }
    if norm.isdigit():
        return int(norm)
    return words.get(norm)


def _karen_extract_number_after(noun: str, text: str) -> int | None:
    norm = _norm_text(text or "")
    match = re.search(rf"\b{re.escape(noun)}\s+(\d{{1,2}}|uno|una|primer|primero|dos|segundo|tres|tercero|cuatro|cinco|seis|siete|ocho|nueve|diez)\b", norm)
    if match:
        return _karen_number_word_to_int(match.group(1))
    match = re.search(rf"\b(primer|primero)\s+{re.escape(noun)}\b", norm)
    if match:
        return 1
    return None


def _clear_karen_numbered_action_context(chat_id: int) -> None:
    """Avoid stale numbered task/reminder follow-ups after a list-changing action."""
    try:
        _LAST_ACTION.pop(int(chat_id), None)
    except Exception:
        pass


def _mark_karen_numbered_action_dirty(chat_id: int, kind: str) -> None:
    try:
        bucket = _KAREN_NUMBERED_ACTION_DIRTY.setdefault(int(chat_id), set())
        bucket.add(kind)
    except Exception:
        pass


def _clear_karen_numbered_action_dirty(chat_id: int, kind: str | None = None) -> None:
    try:
        key = int(chat_id)
        if kind is None:
            _KAREN_NUMBERED_ACTION_DIRTY.pop(key, None)
            return
        bucket = _KAREN_NUMBERED_ACTION_DIRTY.get(key)
        if not bucket:
            return
        bucket.discard(kind)
        if not bucket:
            _KAREN_NUMBERED_ACTION_DIRTY.pop(key, None)
    except Exception:
        pass


def _is_karen_numbered_action_dirty(chat_id: int, kind: str) -> bool:
    try:
        return kind in _KAREN_NUMBERED_ACTION_DIRTY.get(int(chat_id), set())
    except Exception:
        return False


def _karen_gcal_visible_events(chat_id: int) -> list[dict]:
    try:
        ctx = _KAREN_GCAL_EVENT_LIST_CONTEXT.get(int(chat_id), {}) or {}
        return list(ctx.get("events") or [])
    except Exception:
        return []


def _is_karen_gcal_event_context_stale(chat_id: int) -> bool:
    try:
        ctx = _KAREN_GCAL_EVENT_LIST_CONTEXT.get(int(chat_id), {}) or {}
        return bool(ctx.get("stale_after_delete"))
    except Exception:
        return False


def _mark_karen_gcal_event_context_stale(chat_id: int) -> None:
    try:
        ctx = dict(_KAREN_GCAL_EVENT_LIST_CONTEXT.get(int(chat_id), {}) or {})
        ctx["events"] = []
        ctx["stale_after_delete"] = True
        ctx["stale_reason"] = "deleted_numbered_gcal_event"
        ctx["ts"] = time.time()
        _KAREN_GCAL_EVENT_LIST_CONTEXT[int(chat_id)] = ctx
    except Exception:
        pass


def _is_karen_client_id(client_id: str) -> bool:
    try:
        return str(client_id or "") == str(resolve_client_id(KAREN_CHAT_ID))
    except Exception:
        return False


def _karen_reminder_time_note(text: str, scheduled_label: str) -> str:
    clean = _norm_text(text or "")
    if not clean:
        return ""
    scheduled_hour = ""
    try:
        scheduled_hour = str(scheduled_label or "")[:2].lstrip("0") or ""
    except Exception:
        scheduled_hour = ""
    time_matches = re.findall(
        r"\b(?:a\s+las?\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\s*m|p\s*m|md|mediodia|medio dia)?\b",
        clean,
    )
    for hour, minute, suffix in time_matches:
        hour_int = int(hour)
        suffix = (suffix or "").replace(" ", "")
        if suffix in {"pm", "pm"} and hour_int < 12:
            hour_int += 12
        if suffix in {"md", "mediodia", "mediodia"}:
            hour_int = 12
        if scheduled_hour and str(hour_int) != scheduled_hour:
            return " ⚠️ texto menciona otra hora"
    return ""


def _display_karen_reminder_title(text: str) -> str:
    value = str(text or "").strip()
    if _norm_text(value).strip(" .") == "cumpleanos de miguel":
        return "cumpleaños de Miguel"
    return value


def _looks_like_reminder_command_text(text: str) -> bool:
    norm = _normalize_daily_operator_query(text)
    if norm.startswith(("recuerdame", "recordatorio")):
        return True
    if "recuerdame" in norm and re.search(r"\b(manana|mañana|hoy|a las|am|pm|mediodia|medio dia|md|\d{1,2}:\d{2})\b", norm):
        return True
    return bool(norm.startswith(("val recuerdame", "vale recuerdame", "bal recuerdame")))


def _karen_reminder_rows(chat_id: int, *, when: str = "all", limit: int = 25) -> list[dict]:
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo
    from memory_store import list_reminders_for_chat

    rows = list_reminders_for_chat(int(chat_id), statuses=["pending", "sending"], limit=max(1, int(limit or 25))) or []
    tz = ZoneInfo("America/Panama")
    now = datetime.now(tz)
    if when == "tomorrow":
        target_date = (now + timedelta(days=1)).date()
    elif when == "today":
        target_date = now.date()
    else:
        target_date = None

    out = []
    for row in rows:
        rd = dict(row) if hasattr(row, "keys") else dict(row)
        due_raw = str(rd.get("due_at_utc") or "").strip()
        due_local = due_raw
        local_date = ""
        try:
            due_dt = datetime.strptime(due_raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(tz)
            local_date = due_dt.date().isoformat()
            due_local = due_dt.strftime("%Y-%m-%d %H:%M")
            if when in {"all", "active"} and due_dt < now:
                continue
            if when == "past" and due_dt >= now:
                continue
            if target_date and due_dt.date() != target_date:
                continue
        except Exception:
            if target_date or when == "past":
                continue
        text_value = _display_karen_reminder_title(str(rd.get("text") or "").replace("\n", " ").strip()) or f"recordatorio {rd.get('id')}"
        out.append({
            **rd,
            "due_local": due_local,
            "local_date": local_date,
            "text": text_value,
            "time_note": _karen_reminder_time_note(text_value, due_local[11:16] if len(due_local) >= 16 else due_local),
        })
    return out


def _karen_past_reminder_count(chat_id: int) -> int:
    return len(_karen_reminder_rows(chat_id, when="past", limit=100))


def _render_karen_reminder_list(chat_id: int, *, when: str = "all") -> str:
    _clear_karen_numbered_action_dirty(chat_id, "reminder")
    _KAREN_REMINDER_LIST_CONTEXT[int(chat_id)] = "past" if when == "past" else "active"
    rows = _karen_reminder_rows(chat_id, when=when, limit=100)[:25]
    if when == "past":
        title = "⏰ Recordatorios vencidos"
    elif when == "tomorrow":
        title = "⏰ Recordatorios de mañana"
    else:
        title = "⏰ Recordatorios de Val"
    lines = [title, ""]
    if not rows:
        lines.append("No encontré recordatorios pendientes para esa consulta.")
    else:
        for idx, row in enumerate(rows, start=1):
            due = str(row.get("due_local") or "").strip()
            text_value = str(row.get("text") or "").strip()
            time_label = due[11:16] if when == "tomorrow" and len(due) >= 16 else due
            lines.append(f"{idx}. {time_label} · {text_value}{row.get('time_note') or ''}")
    if when in {"all", "active"} and _karen_past_reminder_count(chat_id):
        lines.extend(["", "Hay recordatorios vencidos ocultos. Puedes pedir: “Val, recordatorios vencidos”."])
    if rows:
        lines.append("")
        if when == "past":
            lines.extend([
                "Puedes decir: “elimina el recordatorio vencido 1”.",
                "Conserva el historial si no estás segura.",
            ])
        else:
            lines.append("Puedes decir: “elimina el recordatorio 1” o “cambia el recordatorio 1 para las 10”.")
    return "\n".join(lines)


def _render_karen_reminder_updated_list(chat_id: int, *, when: str) -> str:
    _clear_karen_numbered_action_dirty(chat_id, "reminder")
    _KAREN_REMINDER_LIST_CONTEXT[int(chat_id)] = "past" if when == "past" else "active"
    rows = _karen_reminder_rows(chat_id, when=when, limit=100)[:25]
    if when == "past":
        if not rows:
            return "Recordatorios vencidos actualizados\n\nNo tienes recordatorios vencidos."
        lines = ["Recordatorios vencidos actualizados", ""]
    else:
        if not rows:
            return "Recordatorios actualizados\n\nNo tienes recordatorios activos."
        lines = ["Recordatorios actualizados", ""]
    for idx, row in enumerate(rows, start=1):
        due = str(row.get("due_local") or "").strip()
        text_value = str(row.get("text") or "").strip()
        lines.append(f"{idx}. {due} · {text_value}{row.get('time_note') or ''}")
    return "\n".join(lines)


def _looks_like_karen_reminder_list_query(text: str) -> str:
    norm = _normalize_daily_operator_query(text)
    tomorrow_markers = (
        "que recordatorios tengo manana",
        "que recordatorios tengo mañana",
        "recordatorios de manana",
        "recordatorios de mañana",
    )
    all_markers = (
        "que recordatorios tengo",
        "dime mis recordatorios",
        "muestrame mis recordatorios",
        "que tengo registrado como recordatorio",
        "que tengo en recordatorio",
    )
    past_markers = (
        "recordatorios vencidos",
        "muestrame recordatorios pasados",
        "muéstrame recordatorios pasados",
        "recordatorios pasados",
    )
    if any(marker in norm for marker in past_markers):
        return "past"
    if any(marker in norm for marker in tomorrow_markers):
        return "tomorrow"
    if any(marker in norm for marker in all_markers):
        return "all"
    return ""


def _parse_karen_reminder_management(text: str) -> dict:
    norm = _normalize_daily_operator_query(text)
    delete_verbs = r"(?:elimina|eliminar|borra|borrar|cancela|cancelar|quita|quitar)"
    number_words = r"(?:\d{1,2}|uno|una|primer|primero|dos|segundo|tres|tercero|cuatro|cinco|seis|siete|ocho|nueve|diez)"
    if re.search(rf"\b{delete_verbs}\s+recordatorios\s+(?:vencidos|pasados)\b", norm):
        return {"type": "bulk_past_delete_confirm", "number": None, "target": ""}

    past_number = None
    past_match = re.search(
        rf"\brecordatorio\s+(?:vencido|vencidos|pasado|pasados)\s+(?P<num>{number_words})\b",
        norm,
    )
    if not past_match:
        past_match = re.search(
            rf"\b(?P<num>primer|primero)\s+recordatorio\s+(?:vencido|pasado)\b",
            norm,
        )
    if past_match:
        past_number = _karen_number_word_to_int(past_match.group("num"))

    number = past_number or _karen_extract_number_after("recordatorio", text)
    if number is None:
        generic = re.search(rf"\b{delete_verbs}\s+(?:el\s+)?(?P<num>{number_words})\b", norm)
        if generic:
            number = _karen_number_word_to_int(generic.group("num"))
            return {"type": "context_delete", "number": number, "target": ""}
    elif past_number is not None and re.fullmatch(
        rf"(?:recordatorio\s+(?:vencido|vencidos|pasado|pasados)\s+{number_words}|(?:primer|primero)\s+recordatorio\s+(?:vencido|pasado))",
        norm,
    ):
        return {"type": "recordatorio_number_clarify", "number": past_number, "target": "", "when": "past"}
    elif re.fullmatch(r"recordatorio\s+(\d{1,2}|uno|una|primer|primero|dos|segundo|tres|tercero|cuatro|cinco|seis|siete|ocho|nueve|diez)", norm):
        return {"type": "recordatorio_number_clarify", "number": number, "target": ""}

    if past_number is not None and re.search(rf"\b{delete_verbs}\s+(?:el\s+)?recordatorio\s+(?:vencido|vencidos|pasado|pasados)\b", norm):
        return {"type": "delete", "number": past_number, "target": "", "when": "past"}

    if re.search(rf"\b{delete_verbs}\s+(?:el\s+)?recordatorio\b", norm):
        target = ""
        m = re.search(rf"\b{delete_verbs}\s+(?:el\s+)?recordatorio\s+de\s+(.+)$", norm)
        if m:
            target = m.group(1).strip()
        return {"type": "delete", "number": number, "target": target, "when": "active"}

    if re.search(r"\b(cambia|mueve)\s+(?:el\s+)?recordatorio\b", norm) or re.search(r"\bcambia\s+.+\s+para\b", norm):
        target = ""
        m = re.search(r"\bcambia\s+(.+?)\s+para\b", norm)
        if m and "recordatorio" not in m.group(1):
            target = m.group(1).strip()
        return {"type": "edit", "number": number, "target": target}

    return {}


def _observer_intent_for_karen_reminder_management(text: str) -> str:
    list_when = _looks_like_karen_reminder_list_query(text)
    if list_when:
        return "reminder_query"
    request = _parse_karen_reminder_management(text)
    request_type = str(request.get("type") or "")
    if request_type == "edit":
        return "reminder_update"
    if request_type in {"delete", "context_delete", "recordatorio_number_clarify", "bulk_past_delete_confirm"}:
        return "reminder_delete"
    return "reminder_query"


async def maybe_handle_karen_reminder_management(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> bool:
    if not update.message:
        return False

    list_when = _looks_like_karen_reminder_list_query(text)
    if list_when:
        await update.message.reply_text(_render_karen_reminder_list(int(chat_id), when=list_when))
        return True

    request = _parse_karen_reminder_management(text)
    if not request:
        return False

    if request.get("type") == "ambiguous_delete":
        _clear_karen_numbered_action_context(chat_id)
        await update.message.reply_text(f"¿Quieres eliminar el recordatorio {request.get('number')} o la tarea {request.get('number')}?")
        return True

    if request.get("type") == "bulk_past_delete_confirm":
        _clear_karen_numbered_action_context(chat_id)
        await update.message.reply_text(
            "Puedo revisar los recordatorios vencidos contigo, pero no los elimino en bloque sin confirmación. "
            "Dime: “Val, recordatorios vencidos” y luego “elimina el recordatorio 1”."
        )
        return True

    if request.get("type") == "recordatorio_number_clarify":
        _clear_karen_numbered_action_context(chat_id)
        await update.message.reply_text(
            f"¿Qué quieres hacer con el recordatorio {request.get('number')}? "
            f"Puedes decir: “elimina el recordatorio {request.get('number')}”."
        )
        return True

    requested_when = str(request.get("when") or "").strip()
    if not requested_when and request.get("type") == "context_delete":
        last_context = _KAREN_REMINDER_LIST_CONTEXT.get(int(chat_id), "")
        if last_context == "past":
            requested_when = "past"
        elif last_context == "active":
            requested_when = "active"
        else:
            _clear_karen_numbered_action_context(chat_id)
            if _karen_gcal_visible_events(chat_id):
                gcal_label = "Google " + "Calendar"
                await update.message.reply_text(
                    f"¿Quieres eliminar el evento {request.get('number')} de {gcal_label}, "
                    f"el recordatorio {request.get('number')} de Val o la tarea {request.get('number')} de Val?"
                )
            else:
                await update.message.reply_text(f"¿Quieres eliminar el recordatorio {request.get('number')} o la tarea {request.get('number')}?")
            return True

    row_scope = "past" if requested_when == "past" else "all"
    rows = _karen_reminder_rows(int(chat_id), when=row_scope, limit=100)
    selected = None
    number = request.get("number")
    target = _norm_text(str(request.get("target") or ""))
    if number:
        if request.get("type") == "delete" and _is_karen_numbered_action_dirty(chat_id, "reminder"):
            _clear_karen_numbered_action_context(chat_id)
            await update.message.reply_text(
                f"Después de borrar uno, la lista cambió. ¿Quieres que elimine el nuevo recordatorio {number}? "
                "Pide primero “Val, qué recordatorios tengo” para verlo actualizado."
            )
            return True
        if 1 <= int(number) <= len(rows):
            selected = rows[int(number) - 1]
        else:
            await update.message.reply_text("No veo ese número de recordatorio. Pide “Val, qué recordatorios tengo” para ver la lista.")
            return True
    elif target:
        matches = [row for row in rows if target in _norm_text(str(row.get("text") or ""))]
        if len(matches) == 1:
            selected = matches[0]
        elif len(matches) > 1:
            await update.message.reply_text("Encontré más de un recordatorio parecido. Pide “Val, qué recordatorios tengo” y dime el número.")
            return True

    if not selected:
        await update.message.reply_text("No pude identificar un recordatorio claro. Pide “Val, qué recordatorios tengo” y dime el número.")
        return True

    reminder_text = str(selected.get("text") or "recordatorio").strip()
    display_num = number or (rows.index(selected) + 1)

    if request.get("type") == "edit":
        _clear_karen_numbered_action_context(chat_id)
        await update.message.reply_text(
            "Todavía no puedo editarlo directamente. Puedo eliminarlo y crear uno nuevo con la nueva hora. "
            "¿Quieres que lo haga?"
        )
        return True

    try:
        from memory_store import cancel_reminder
        ok = bool(cancel_reminder(int(chat_id), int(selected.get("id"))))
    except Exception as e:
        logger.exception(f"[KAREN_REMINDER_NUMBERED_DELETE] failed: {e}")
        ok = False
    if not ok:
        _clear_karen_numbered_action_context(chat_id)
        await update.message.reply_text("No pude eliminar ese recordatorio. Puede que ya no esté pendiente.")
        return True

    _clear_karen_numbered_action_context(chat_id)
    updated = _render_karen_reminder_updated_list(int(chat_id), when="past" if requested_when == "past" else "all")
    if requested_when == "past":
        lead = f"Listo. Eliminé el recordatorio vencido: {reminder_text}."
    else:
        lead = f"Listo. Eliminé: {reminder_text}."
    await update.message.reply_text(
        f"{lead}\n\n{updated}"
    )
    return True


def _extract_karen_task_creation_text(text: str) -> str:
    norm = _normalize_daily_operator_query(text)
    if norm.startswith("recuerdame") or norm.startswith("recordatorio"):
        return ""
    patterns = (
        r"^(?:registra|agrega|anota)\s+(?:una\s+)?tarea\s*:?\s+(.+)$",
        r"^tarea\s*:?\s+(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, norm)
        if match:
            task_text = re.sub(r"\s+", " ", (match.group(1) or "").strip())
            return task_text[:180].strip()
    return ""


async def maybe_handle_karen_task_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, client_id: str, text: str) -> bool:
    if not update.message:
        return False
    case_id = ""
    try:
        case_id = get_active_case_id(int(chat_id)) or ""
    except Exception:
        case_id = ""
    is_karen_flow = str(chat_id) == str(KAREN_CHAT_ID) or client_id == resolve_client_id(KAREN_CHAT_ID) or str(case_id) == CASE_KEY
    if not is_karen_flow:
        return False
    task_text = _extract_karen_task_creation_text(text)
    if not task_text:
        return False
    try:
        from memory_store import upsert_commitment
        upsert_commitment(
            chat_id=int(chat_id),
            raw_input=task_text,
            action=task_text,
            target="",
            due_date=None,
            confidence="explicit_task",
        )
        await update.message.reply_text(f"Listo. Guardé esta tarea: {task_text}.")
        return True
    except Exception as e:
        logger.exception(f"[KAREN_TASK_CREATE] failed: {e}")
        await update.message.reply_text("Intenté guardar la tarea, pero algo falló.")
        return True


def _format_client_gcal_event_time(raw_start: str, tz_name: str = "America/Panama") -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    raw_start = str(raw_start or "").strip()
    label = raw_start
    try:
        if "T" in raw_start:
            dt = datetime.fromisoformat(raw_start.replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.astimezone(ZoneInfo(tz_name))
            label = dt.strftime("%a %d/%m %I:%M %p").replace(" 0", " ")
        elif raw_start:
            label = raw_start
    except Exception:
        pass
    return label


def _format_client_gcal_events_section(client_id: str, start_local, end_local, tz_name: str = "America/Panama", limit: int = 10, chat_id: int | None = None) -> str:
    """
    Google Calendar section for client agenda dashboards.

    Safety:
    - lists events by visible number
    - create/delete still require explicit routes/confirmation
    - clearly labels source as Google Calendar
    - does not expose attendee/details/description
    """
    try:
        from core.client_gcal_read import get_client_events_between

        if chat_id is not None:
            _KAREN_GCAL_EVENT_LIST_CONTEXT[int(chat_id)] = {
                "ts": time.time(),
                "client_id": client_id,
                "events": [],
                "stale_after_delete": False,
            }

        result = get_client_events_between(
            client_id,
            start_local,
            end_local,
            tz=tz_name,
            limit=limit,
        )

        lines = ["🌐 Eventos de Google Calendar"]

        if result.status == "not_connected":
            lines.append("- No está conectado para este cliente.")
            return "\n".join(lines)

        if result.status != "ok":
            lines.append(f"- No pude leer Google Calendar: {result.reason or result.status}")
            return "\n".join(lines)

        if not result.events:
            lines.append("- No encontré eventos en Google Calendar para esta ventana.")
            return "\n".join(lines)

        visible_events = []
        for idx, ev in enumerate(result.events, start=1):
            raw_start = str(ev.get("start") or "").strip()
            title = str(ev.get("summary") or "(sin título)").strip()
            label = _format_client_gcal_event_time(raw_start, tz_name=tz_name)

            lines.append(f"{idx}. {label} · {title}")
            visible_events.append({
                "number": idx,
                "event_id": ev.get("id") or "",
                "summary": title,
                "start": raw_start,
                "end": ev.get("end") or "",
                "display_start": label,
            })

        if chat_id is not None:
            _KAREN_GCAL_EVENT_LIST_CONTEXT[int(chat_id)] = {
                "ts": time.time(),
                "client_id": client_id,
                "events": visible_events,
                "stale_after_delete": False,
            }

        return "\n".join(lines)

    except Exception as e:
        return "🌐 Eventos de Google Calendar\n- No pude leer Google Calendar ahora mismo. Lo intento de nuevo más tarde."


def _karen_month_number(name: str) -> int | None:
    months = {
        "enero": 1, "ene": 1,
        "febrero": 2, "feb": 2,
        "marzo": 3, "mar": 3,
        "abril": 4, "abr": 4,
        "mayo": 5, "may": 5,
        "junio": 6, "jun": 6,
        "julio": 7, "jul": 7,
        "agosto": 8, "ago": 8,
        "septiembre": 9, "setiembre": 9, "sep": 9, "sept": 9,
        "octubre": 10, "oct": 10,
        "noviembre": 11, "nov": 11,
        "diciembre": 12, "dic": 12,
    }
    return months.get(_norm_text(name or ""))


def _karen_weekday_index(name: str) -> int | None:
    return {
        "lunes": 0,
        "martes": 1,
        "miercoles": 2,
        "miércoles": 2,
        "jueves": 3,
        "viernes": 4,
        "sabado": 5,
        "sábado": 5,
        "domingo": 6,
    }.get(_norm_text(name or ""))


def _karen_next_weekday_date(weekday_idx: int, *, now=None, force_next: bool = False):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("America/Panama")
    now_local = now or datetime.now(tz)
    if now_local.tzinfo is None:
        now_local = now_local.replace(tzinfo=tz)
    days_ahead = (int(weekday_idx) - now_local.weekday()) % 7
    if days_ahead == 0 or force_next:
        days_ahead = 7 if days_ahead == 0 else days_ahead
    return (now_local + timedelta(days=days_ahead)).date()


def _parse_karen_weekday_agenda_target(text: str, *, now=None):
    import datetime as dt
    from datetime import date
    from zoneinfo import ZoneInfo

    norm = _norm_text(text or "")
    norm = re.sub(r"[¿?¡!.,;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(a ver|bueno|ok|okay|oye|val|valeria|vale|bal)\s+", "", norm).strip()
    if not re.search(r"\b(que tengo|que hay|tengo algo|hay algo|agenda)\b", norm):
        return None

    explicit = re.search(
        r"\b(?P<weekday>lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\s+(?P<day>[0-3]?\d)\s+(?:de\s+)?(?P<month>enero|ene|febrero|feb|marzo|mar|abril|abr|mayo|may|junio|jun|julio|julio|agosto|ago|septiembre|setiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dic)\b",
        norm,
    )
    tz = ZoneInfo("America/Panama")
    now_local = now or dt.datetime.now(tz)
    if explicit:
        month = _karen_month_number(explicit.group("month"))
        day = int(explicit.group("day"))
        year = now_local.year
        if month:
            try:
                target = date(year, month, day)
                if target < now_local.date():
                    target = date(year + 1, month, day)
                return target
            except ValueError:
                return None

    match = re.search(
        r"\b(?:para\s+el\s+|para\s+|el\s+)?(?P<prefix>proximo|próximo)?\s*(?P<weekday>lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\b",
        norm,
    )
    if not match:
        return None
    weekday_idx = _karen_weekday_index(match.group("weekday"))
    if weekday_idx is None:
        return None
    return _karen_next_weekday_date(weekday_idx, now=now_local, force_next=bool(match.group("prefix")))


def _build_val_agenda_for_date(chat_id: int, target_date) -> str:
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    from memory_store import _get_conn

    tz = ZoneInfo("America/Panama")
    start_local = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=tz)
    end_local = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=tz)
    start_utc = start_local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_utc = end_local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    date_key = target_date.isoformat()

    reminders = []
    tasks = []
    try:
        conn = _get_conn()
        conn.row_factory = None
        cur = conn.cursor()
        reminders = cur.execute(
            """
            SELECT id, text, due_at_utc
            FROM reminders
            WHERE chat_id = ?
              AND status IN ('pending', 'sending', 'sent')
              AND due_at_utc >= ?
              AND due_at_utc <= ?
            ORDER BY due_at_utc ASC, id ASC
            LIMIT 20
            """,
            (int(chat_id), start_utc, end_utc),
        ).fetchall() or []
        tasks = cur.execute(
            """
            SELECT id, raw_input, action, target, due_date
            FROM commitments
            WHERE chat_id = ?
              AND status = 'open'
              AND substr(COALESCE(due_date, ''), 1, 10) = ?
            ORDER BY id ASC
            LIMIT 20
            """,
            (int(chat_id), date_key),
        ).fetchall() or []
        conn.close()
    except Exception:
        reminders = []
        tasks = []

    lines = ["⏰ Recordatorios de Val"]
    if reminders:
        for idx, row in enumerate(reminders, start=1):
            rid, text_value, due_at_utc = row[0], row[1], row[2]
            time_label = "sin hora"
            try:
                dt_utc = datetime.strptime(str(due_at_utc or ""), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                time_label = dt_utc.astimezone(tz).strftime("%H:%M")
            except Exception:
                pass
            lines.append(f"{idx}. {time_label} · {_display_karen_reminder_title(str(text_value or '').strip()) or f'recordatorio #{rid}'}")
    else:
        lines.append("- No tienes recordatorios de Val para esa fecha.")

    lines.extend(["", "📌 Tareas de Val"])
    if tasks:
        for idx, row in enumerate(tasks, start=1):
            raw = str(row[1] or "").strip()
            label = raw or " ".join(part for part in (str(row[2] or "").strip(), str(row[3] or "").strip()) if part).strip() or f"tarea #{row[0]}"
            lines.append(f"{idx}. {label}")
    else:
        lines.append("- No tienes tareas de Val con fecha para ese día.")

    return "\n".join(lines)


def build_client_weekday_agenda_dashboard(client_id: str, chat_id: int, target_date) -> str:
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    tz_name = "America/Panama"
    tz = ZoneInfo(tz_name)
    start_local = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    weekday = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"][target_date.weekday()]
    month_name = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][target_date.month]
    title = f"🗓️ Agenda para {weekday} {target_date.day} de {month_name}"
    gcal = _format_client_gcal_events_section(
        client_id=client_id,
        start_local=start_local,
        end_local=end_local,
        tz_name=tz_name,
        limit=10,
        chat_id=chat_id,
    )
    internal = _build_val_agenda_for_date(chat_id, target_date)
    return "\n\n".join([title, gcal, internal])


async def maybe_handle_karen_weekday_agenda_query(update, chat_id: int, client_id: str, text: str) -> bool:
    if not _is_karen_client_id(client_id) or not update or not getattr(update, "message", None):
        return False
    target_date = _parse_karen_weekday_agenda_target(text)
    if not target_date:
        return False
    await update.message.reply_text(
        build_client_weekday_agenda_dashboard(client_id, chat_id, target_date),
        disable_web_page_preview=True,
    )
    return True


def _karen_registered_name_norm(text: str) -> str:
    norm = _norm_text(text or "")
    norm = re.sub(r"[¿?¡!.,;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(a ver|bueno|ok|okay|oye|val|valeria|vale|bal)\s+", "", norm).strip()
    return norm


async def maybe_handle_karen_name_language_guard(update, chat_id: int, client_id: str, text: str) -> bool:
    if not _is_karen_client_id(client_id) or not update or not getattr(update, "message", None):
        return False

    norm = _karen_registered_name_norm(text)
    nickname_queries = {
        "que apodo me tienes registrado",
        "cual es mi apodo registrado",
        "cuál es mi apodo registrado",
        "cual es mi apodo",
        "como me vas a llamar",
        "como me tienes registrada",
        "cual es mi nombre registrado",
    }
    if norm in nickname_queries:
        await update.message.reply_text("Tu apodo registrado es: Tany. Lo estoy usando con y griega.")
        return True

    wants_tany_name = "tany" in norm and (
        "apodo" in norm
        or "llamar" in norm
        or "llames" in norm
        or "nombre" in norm
    )
    if wants_tany_name and re.search(r"\b(cambia|cambiar|pon|poner|puedes|llamar|llamame|llámame|oficial)\b", norm):
        try:
            upsert_fact(chat_id=int(chat_id), fact_key="preferred_name", fact_value="Tany")
        except Exception as e:
            logger.exception(f"[KAREN_NAME_GUARD_UPSERT] failed: {e}")
        await update.message.reply_text("Listo, Tany. Tu apodo/nombre preferido registrado es Tany; te voy a llamar Tany.")
        return True

    spanish_markers = (
        "responde en espanol",
        "responde en español",
        "respondeme en espanol",
        "respóndeme en español",
        "hablame en espanol",
        "háblame en español",
        "quiero que respondas en espanol",
        "quiero que respondas en español",
    )
    if norm in spanish_markers or any(marker in norm for marker in spanish_markers):
        try:
            upsert_fact(chat_id=int(chat_id), fact_key="preferred_language", fact_value="es")
        except Exception as e:
            logger.exception(f"[KAREN_LANGUAGE_GUARD_UPSERT] failed: {e}")
        await update.message.reply_text("Claro, Tany. Te respondo en español.")
        return True

    return False


def _parse_karen_time_phrase(norm: str) -> tuple[int, int] | None:
    """
    Parse Karen reminder clock phrases without losing minutes.

    Supports:
    - a las 9:20
    - a las 9 y 20
    - para las 9:20
    - 9:20
    - 3 de la tarde
    - 10 de la noche
    - 13 / 13:30 military-style
    """
    patterns = [
        # Prefer phrases with daypart so "3 de la tarde" becomes 15:00.
        r"\b(?:a\s+las?|a\s+la|para\s+las?|para\s+la)?\s*"
        r"(?P<hour>\d{1,2})"
        r"(?:(?::|\s+y\s+|\s+con\s+)(?P<minute>\d{1,2}))?"
        r"\s*(?P<ampm>am|pm|a\s*m|p\s*m)?"
        r"\s+de\s+la\s+(?P<daypart>manana|mañana|tarde|noche)\b",

        # General clock expression.
        r"\b(?:a\s+las?|a\s+la|para\s+las?|para\s+la)?\s*"
        r"(?P<hour>\d{1,2})"
        r"(?:(?::|\s+y\s+|\s+con\s+)(?P<minute>\d{1,2}))?"
        r"\s*(?P<ampm>am|pm|a\s*m|p\s*m)?\b",
    ]

    match = None
    for pattern in patterns:
        match = re.search(pattern, norm)
        if match:
            break
    if not match:
        return None

    hour = int(match.group("hour"))
    minute = int(match.group("minute") or "0")
    ampm = (match.group("ampm") or "").replace(" ", "")
    daypart = match.groupdict().get("daypart")

    if ampm == "pm" and hour < 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    elif not ampm and daypart in ("tarde", "noche") and 1 <= hour <= 11:
        hour += 12

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour, minute

def _karen_time_phrase_is_explicit_period(norm: str) -> bool:
    """
    True when the user explicitly provided AM/PM, daypart, or a 24h-style hour.
    Used to avoid silently changing explicit times.
    """
    if re.search(r"\b(?:am|pm|a\s*m|p\s*m)\b", norm):
        return True
    if re.search(r"\bde\s+la\s+(?:manana|mañana|tarde|noche)\b", norm):
        return True
    m = re.search(
        r"\b(?:a\s+las?|a\s+la|para\s+las?|para\s+la)?\s*(?P<hour>\d{1,2})(?:(?::|\s+y\s+|\s+con\s+)\d{1,2})?\b",
        norm,
    )
    if m:
        try:
            return int(m.group("hour")) >= 13
        except Exception:
            return False
    return False


def _karen_roll_forward_ambiguous_today_time(time_parts: tuple[int, int] | None, target_date, norm: str, now_local):
    """
    If Karen says an ambiguous 1-11 clock time for today and that AM time already passed,
    interpret it as PM when it still lands later today.

    Example at 6:16 PM:
    - "hoy a las 9:20" => 21:20
    """
    if not time_parts or target_date is None or now_local is None:
        return time_parts
    if target_date != now_local.date():
        return time_parts
    if _karen_time_phrase_is_explicit_period(norm):
        return time_parts

    hour, minute = time_parts
    if not (1 <= int(hour) <= 11):
        return time_parts

    import datetime as dt
    candidate = dt.datetime(target_date.year, target_date.month, target_date.day, int(hour), int(minute), 0, tzinfo=now_local.tzinfo)
    if candidate > now_local:
        return time_parts

    pm_candidate = candidate + dt.timedelta(hours=12)
    if pm_candidate.date() == target_date and pm_candidate > now_local:
        return pm_candidate.hour, pm_candidate.minute

    return time_parts


def _karen_strip_time_phrase_from_title(title: str) -> str:
    """
    Remove recognized time phrases from reminder title without eating useful text.

    Handles:
    - hoy a las 9:20 prueba exacta -> prueba exacta
    - a las 9 y 20 prueba exacta -> prueba exacta
    - a las 10 de la noche prueba nocturna -> prueba nocturna
    - 10 de la noche prueba nocturna -> prueba nocturna
    """
    patterns = [
        # Full phrase with prefix + daypart.
        r"\b(?:hoy\s+)?(?:a\s+las?|a\s+la|para\s+las?|para\s+la)\s*\d{1,2}(?:(?::|\s+y\s+|\s+con\s+)\d{1,2})?\s*(?:am|pm|a\s*m|p\s*m)?\s+de\s+la\s+(?:manana|mañana|tarde|noche)\b",
        # Bare daypart phrase, e.g. "10 de la noche".
        r"\b\d{1,2}\s+de\s+la\s+(?:manana|mañana|tarde|noche)\b",
        # Full phrase with prefix but no daypart.
        r"\b(?:hoy\s+)?(?:a\s+las?|a\s+la|para\s+las?|para\s+la)\s*\d{1,2}(?:(?::|\s+y\s+|\s+con\s+)\d{1,2})?\s*(?:am|pm|a\s*m|p\s*m)?\b",
        # Bare exact time with minutes, e.g. "9:20" or "9 y 20".
        r"\b\d{1,2}(?:(?::|\s+y\s+|\s+con\s+)\d{1,2})\s*(?:am|pm|a\s*m|p\s*m)?\b",
        # Bare AM/PM.
        r"\b\d{1,2}\s*(?:am|pm|a\s*m|p\s*m)\b",
    ]
    for pattern in patterns:
        title = re.sub(pattern, " ", title)
    # Cleanup leftovers from a partially stripped phrase, defensive.
    title = re.sub(r"\bde\s+la\s+(?:manana|mañana|tarde|noche)\b", " ", title)
    return re.sub(r"\s+", " ", title).strip(" .,:;")

def _karen_small_number_word_to_int(token: str) -> int | None:
    value = _karen_number_word_to_int(token)
    if value is not None:
        return value
    return {
        "cero": 0,
        "once": 11,
        "doce": 12,
        "trece": 13,
        "catorce": 14,
        "quince": 15,
        "veinte": 20,
        "treinta": 30,
        "cuarenta": 40,
        "cincuenta": 50,
        "sesenta": 60,
    }.get(str(token or "").strip())


def _parse_karen_relative_minutes(norm: str, *, now=None) -> tuple[int, tuple[int, int], object] | None:
    import datetime as dt
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("America/Panama")
    base_now = now or dt.datetime.now(tz)
    if getattr(base_now, "tzinfo", None) is None:
        base_now = base_now.replace(tzinfo=tz)

    half_hour = re.search(r"\b(?:en|dentro\s+de)\s+(?:media\s+hora|medio\s+hora)\b", norm)
    if half_hour:
        minutes = 30
        due_local = base_now + dt.timedelta(minutes=minutes)
        return minutes, (due_local.hour, due_local.minute), due_local.date()

    hour_and_half = re.search(
        r"\b(?:en|dentro\s+de)\s+(?:una|1)\s+hora\s+y\s+media\b",
        norm,
    )
    if hour_and_half:
        minutes = 90
        due_local = base_now + dt.timedelta(minutes=minutes)
        return minutes, (due_local.hour, due_local.minute), due_local.date()

    hour_match = re.search(
        r"\b(?:en|dentro\s+de)\s+(?P<num>\d{1,2}|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)\s+horas?\b",
        norm,
    )
    if hour_match:
        hours = _karen_small_number_word_to_int(hour_match.group("num"))
        if hours and hours >= 1:
            minutes = int(hours) * 60
            due_local = base_now + dt.timedelta(minutes=minutes)
            return minutes, (due_local.hour, due_local.minute), due_local.date()

    match = re.search(
        r"\b(?:en|dentro\s+de)\s+(?P<num>\d{1,3}|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|veinte|treinta|cuarenta|cincuenta|sesenta)\s+minutos?\b",
        norm,
    )
    if not match:
        return None
    minutes = _karen_small_number_word_to_int(match.group("num"))
    if not minutes or minutes < 1:
        return None
    due_local = base_now + dt.timedelta(minutes=int(minutes))
    return int(minutes), (due_local.hour, due_local.minute), due_local.date()


def _parse_karen_natural_reminder_request(text: str, *, now=None) -> dict | None:
    legacy_structural_time_regex_marker = r"a\\s+las?"
    import datetime as dt
    from datetime import date
    from zoneinfo import ZoneInfo

    raw = text or ""
    norm = _norm_text(raw)
    norm = re.sub(r"[¿?¡!.,;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(a ver|bueno|ok|okay|oye|val|valeria|vale|bal)\s+", "", norm).strip()
    if not (
        norm.startswith(("recuerdame", "recordatorio", "recordarme"))
        or "registrar un recordatorio" in norm
        or "registrar recordatorio" in norm
        or "un recordatorio para" in norm
    ):
        return None

    tz = ZoneInfo("America/Panama")
    now_local = now or dt.datetime.now(tz)
    if now_local.tzinfo is None:
        now_local = now_local.replace(tzinfo=tz)

    relative_minutes = _parse_karen_relative_minutes(norm, now=now_local)
    target_date = None
    date_span = None
    if relative_minutes:
        _, rel_time, rel_date = relative_minutes
        target_date = rel_date
    explicit = re.search(
        r"\b(?P<weekday>lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\s+(?P<day>[0-3]?\d)\s+(?:de\s+)?(?P<month>enero|ene|febrero|feb|marzo|mar|abril|abr|mayo|may|junio|jun|julio|jul|agosto|ago|septiembre|setiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dic)\b",
        norm,
    )
    if explicit:
        month = _karen_month_number(explicit.group("month"))
        day = int(explicit.group("day"))
        year = now_local.year
        if month:
            try:
                target_date = date(year, month, day)
                if target_date < now_local.date():
                    target_date = date(year + 1, month, day)
                date_span = explicit.span()
            except ValueError:
                target_date = None

    if target_date is None:
        weekday_match = re.search(
            r"\b(?:para\s+el\s+|para\s+|el\s+)?(?P<prefix>proximo|próximo)?\s*(?P<weekday>lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\b",
            norm,
        )
        if weekday_match:
            idx = _karen_weekday_index(weekday_match.group("weekday"))
            if idx is not None:
                target_date = _karen_next_weekday_date(idx, now=now_local, force_next=bool(weekday_match.group("prefix")))
                date_span = weekday_match.span()
        elif "manana" in norm or "mañana" in norm:
            target_date = (now_local + dt.timedelta(days=1)).date()
            date_span = re.search(r"\bmanana|mañana\b", norm).span()
        elif "hoy" in norm:
            target_date = now_local.date()
            date_span = re.search(r"\bhoy\b", norm).span()

    time_parts = relative_minutes[1] if relative_minutes else _parse_karen_time_phrase(norm)
    time_parts = _karen_roll_forward_ambiguous_today_time(time_parts, target_date, norm, now_local)

    title = norm
    title = re.sub(r"^(?:recuerdame|recordarme|recordatorio)\s+", "", title).strip()
    title = re.sub(r"^quiero\s+registrar\s+un\s+recordatorio\s+(?:para\s+)?", "", title).strip()
    title = re.sub(
        r"\b(?:en|dentro\s+de)\s+(?:"
        r"media\s+hora|medio\s+hora|"
        r"(?:una|1)\s+hora\s+y\s+media|"
        r"(?:\d{1,2}|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)\s+horas?|"
        r"(?:\d{1,3}|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|veinte|treinta|cuarenta|cincuenta|sesenta)\s+minutos?"
        r")\b",
        " ",
        title,
    )
    title = _karen_strip_time_phrase_from_title(title)
    if date_span:
        # Recompute spans after possible time removal by textual date regex cleanup.
        title = re.sub(
            r"\b(?:para\s+el\s+|para\s+|el\s+)?(?:proximo|próximo)?\s*(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)(?:\s+[0-3]?\d\s+(?:de\s+)?(?:enero|ene|febrero|feb|marzo|mar|abril|abr|mayo|may|junio|jun|jul|julio|agosto|ago|septiembre|setiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dic))?\b",
            " ",
            title,
        )
        title = re.sub(r"\b(?:para\s+)?(?:manana|mañana|hoy)\b", " ", title)
    title = re.sub(
        r"\b(?:el\s+)?(?:proximo|próximo)?\s*(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\b",
        " ",
        title,
    )
    title = re.sub(
        r"\b[0-3]?\d\s+(?:de\s+)?(?:enero|ene|febrero|feb|marzo|mar|abril|abr|mayo|may|junio|jun|jul|julio|agosto|ago|septiembre|setiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dic)\b",
        " ",
        title,
    )
    title = re.sub(r"\blo puedes hacer\b", " ", title)
    title = re.sub(r"\bpuedes hacerlo\b", " ", title)
    title = re.sub(r"\s+", " ", title).strip(" .,:;")
    if title in {"", "para", "el", "recordatorio"}:
        title = ""

    return {"title": title, "date": target_date, "time": time_parts}


def _remember_karen_pending_reminder(chat_id: int, parsed: dict, missing: str) -> None:
    _KAREN_PENDING_REMINDER_CONTEXT[int(chat_id)] = {
        "title": parsed.get("title") or "",
        "date": parsed.get("date"),
        "time": parsed.get("time"),
        "missing": missing,
        "ts": time.time(),
    }


def _parse_karen_pending_reminder_reply(text: str) -> dict:
    import datetime as dt
    from datetime import date
    from zoneinfo import ZoneInfo

    raw = text or ""
    norm = _norm_text(raw)
    norm = re.sub(r"[¿?¡!.,;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(a ver|bueno|ok|okay|oye|val|valeria|vale|bal|pal|va\s+el)\s+", "", norm).strip()

    tz = ZoneInfo("America/Panama")
    now_local = dt.datetime.now(tz)
    out = {"title": "", "date": None, "time": None}

    relative_minutes = _parse_karen_relative_minutes(norm)
    if relative_minutes:
        _, rel_time, rel_date = relative_minutes
        out["date"] = rel_date
        out["time"] = rel_time

    if out["date"] is None:
        explicit = re.search(
            r"\b(?P<day>[0-3]?\d)\s+(?:de\s+)?(?P<month>enero|ene|febrero|feb|marzo|mar|abril|abr|mayo|may|junio|jun|jul|julio|agosto|ago|septiembre|setiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dic)\b",
            norm,
        )
        if explicit:
            month = _karen_month_number(explicit.group("month"))
            day = int(explicit.group("day"))
            if month:
                try:
                    candidate = date(now_local.year, month, day)
                    if candidate < now_local.date():
                        candidate = date(now_local.year + 1, month, day)
                    out["date"] = candidate
                except ValueError:
                    pass
        elif "manana" in norm or "mañana" in norm:
            out["date"] = (now_local + dt.timedelta(days=1)).date()
        elif norm in {"hoy", "para hoy"} or "para hoy" in norm:
            out["date"] = now_local.date()
        else:
            weekday_match = re.search(
                r"\b(?:para\s+el\s+|para\s+|el\s+)?(?P<prefix>proximo|próximo)?\s*(?P<weekday>lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\b",
                norm,
            )
            if weekday_match:
                idx = _karen_weekday_index(weekday_match.group("weekday"))
                if idx is not None:
                    out["date"] = _karen_next_weekday_date(idx, now=now_local, force_next=bool(weekday_match.group("prefix")))

    if out["time"] is None:
        out["time"] = _parse_karen_time_phrase(norm)

    if out["date"] is None and out["time"] is None:
        title = re.sub(
            r"\b(?:en|dentro\s+de)\s+(?:\d{1,3}|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|veinte|treinta|cuarenta|cincuenta|sesenta)\s+minutos?\b",
            " ",
            norm,
        )
        title = re.sub(
            r"\ba\s+las?\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?(?:\s+de\s+la\s+(?:manana|mañana|tarde|noche))?\b",
            " ",
            title,
        )
        title = re.sub(r"\b(?:para\s+)?(?:manana|mañana|hoy)\b", " ", title)
        title = re.sub(r"\s+", " ", title).strip(" .,:;")
        if title not in {"", "para", "el", "la"}:
            out["title"] = title
    return out


async def maybe_handle_karen_pending_reminder_context(update, chat_id: int, client_id: str, text: str) -> bool:
    if not _is_karen_client_id(client_id) or not update or not getattr(update, "message", None):
        return False
    pending = _KAREN_PENDING_REMINDER_CONTEXT.get(int(chat_id))
    if not pending:
        return False
    if time.time() - float(pending.get("ts") or 0) > 900:
        _KAREN_PENDING_REMINDER_CONTEXT.pop(int(chat_id), None)
        return False

    update_bits = _parse_karen_pending_reminder_reply(text)
    if update_bits.get("date"):
        pending["date"] = update_bits["date"]
    if update_bits.get("time"):
        pending["time"] = update_bits["time"]
    if update_bits.get("title") and not pending.get("title"):
        pending["title"] = update_bits["title"]
    pending["ts"] = time.time()
    _KAREN_PENDING_REMINDER_CONTEXT[int(chat_id)] = pending

    if not pending.get("date"):
        await update.message.reply_text("Sí puedo crear el recordatorio, Tany. ¿Para qué fecha lo pongo?")
        return True
    if not pending.get("title"):
        await update.message.reply_text("Sí puedo crear el recordatorio, Tany. ¿Qué quieres que te recuerde?")
        return True
    if not pending.get("time"):
        await update.message.reply_text("Sí puedo crear el recordatorio, Tany. ¿A qué hora lo pongo?")
        return True

    from memory_store import insert_reminder
    import datetime as dt
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("America/Panama")
    hour, minute = pending["time"]
    target_date = pending["date"]
    due_local = dt.datetime(target_date.year, target_date.month, target_date.day, hour, minute, 0, tzinfo=tz)
    due_utc = due_local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    title = _display_karen_reminder_title(str(pending["title"]).strip())
    insert_reminder(
        chat_id=int(chat_id),
        due_at_utc=due_utc,
        text=title,
        status="pending",
        entity_type="reminder",
        parent_ref=None,
    )
    _KAREN_PENDING_REMINDER_CONTEXT.pop(int(chat_id), None)
    weekday = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"][due_local.weekday()]
    month_name = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][due_local.month]
    await update.message.reply_text(
        f"Listo, Tany. Guardé el recordatorio: {title} — {weekday} {due_local.day} de {month_name}, {due_local.strftime('%I:%M %p').lstrip('0')}."
    )
    return True


async def maybe_handle_karen_natural_weekday_reminder(update, chat_id: int, client_id: str, text: str) -> bool:
    if not _is_karen_client_id(client_id) or not update or not getattr(update, "message", None):
        return False
    parsed = _parse_karen_natural_reminder_request(text)
    if not parsed:
        return False
    if not parsed.get("date"):
        _remember_karen_pending_reminder(chat_id, parsed, "date")
        await update.message.reply_text("Sí puedo crear el recordatorio, Tany. ¿Para qué fecha lo pongo?")
        return True
    if not parsed.get("title"):
        _remember_karen_pending_reminder(chat_id, parsed, "title")
        await update.message.reply_text("Sí puedo crear el recordatorio, Tany. ¿Qué quieres que te recuerde?")
        return True
    if not parsed.get("time"):
        _remember_karen_pending_reminder(chat_id, parsed, "time")
        await update.message.reply_text("Sí puedo crear el recordatorio, Tany. ¿A qué hora lo pongo?")
        return True

    from memory_store import insert_reminder
    import datetime as dt
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("America/Panama")
    hour, minute = parsed["time"]
    target_date = parsed["date"]
    due_local = dt.datetime(target_date.year, target_date.month, target_date.day, hour, minute, 0, tzinfo=tz)
    due_utc = due_local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    title = _display_karen_reminder_title(str(parsed["title"]).strip())
    rid = insert_reminder(
        chat_id=int(chat_id),
        due_at_utc=due_utc,
        text=title,
        status="pending",
        entity_type="reminder",
        parent_ref=None,
    )
    weekday = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"][due_local.weekday()]
    month_name = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][due_local.month]
    await update.message.reply_text(
        f"Listo, Tany. Guardé el recordatorio: {title} — {weekday} {due_local.day} de {month_name}, {due_local.strftime('%I:%M %p').lstrip('0')}."
    )
    return True


def build_client_agenda_dashboard(client_id: str, chat_id: int, window: str) -> str:
    """
    Combined client agenda dashboard:
    - Google Calendar read-only
    - Val internal agenda/reminders/tasks

    V0 is intentionally conservative and source-labeled.
    """
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    tz_name = "America/Panama"
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)

    if window == "tomorrow":
        target = now + timedelta(days=1)
        start_local = datetime(target.year, target.month, target.day, 0, 0, 0, tzinfo=tz)
        end_local = start_local + timedelta(days=1)
        title = "🗓️ Agenda de mañana"
        try:
            internal = build_unified_tomorrow_dashboard(int(chat_id))
        except Exception as e:
            internal = f"No pude leer agenda interna de mañana: {e}"

    elif window == "week":
        start_local = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=tz)
        end_local = start_local + timedelta(days=7)
        title = "🗓️ Agenda de los próximos 7 días"
        try:
            internal = _generate_week_horizon(int(chat_id), days=7)
        except Exception as e:
            internal = f"No pude leer agenda interna semanal: {e}"

    else:
        start_local = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=tz)
        end_local = start_local + timedelta(days=1)
        title = "🗓️ Agenda de hoy"
        try:
            internal = _generate_morning_brief_det(int(chat_id), start_local.date().isoformat())
        except Exception as e:
            internal = f"No pude leer agenda interna de hoy: {e}"

        if not internal:
            internal = "No encontré recordatorios ni términos internos para hoy."

    gcal = _format_client_gcal_events_section(
        client_id=client_id,
        start_local=start_local,
        end_local=end_local,
        tz_name=tz_name,
        limit=10,
        chat_id=chat_id,
    )
    if window == "tomorrow":
        internal_lines = str(internal or "").splitlines()
        if internal_lines and internal_lines[0].startswith("📅 Mañana"):
            internal_lines = internal_lines[2:] if len(internal_lines) > 1 and not internal_lines[1].strip() else internal_lines[1:]
        internal_block = "\n".join(internal_lines).strip()
    else:
        internal_block = str(internal or "").strip()
    internal_block = re.sub(r"(?m)^⏰ Recordatorios$", "⏰ Recordatorios de Val", internal_block)
    internal_block = re.sub(r"(?m)^📌 Tareas$", "📌 Tareas de Val", internal_block)

    blocks = [title, gcal]
    if internal_block:
        blocks.append(internal_block)
    return "\n\n".join(blocks)


async def maybe_handle_karen_explicit_case_note(update, chat_id: int, client_id: str, text: str) -> bool:
    """
    Karen MVP note capture for explicit "guarda nota de finca/caso" phrasing.
    Keeps saved context separate from agenda/cita/reminder language.
    """
    if not _is_karen_client_id(client_id) or not update or not getattr(update, "message", None):
        return False

    raw = (text or "").strip()
    if not raw:
        return False

    norm = unicodedata.normalize("NFKD", raw.lower())
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = re.sub(r"[¿?¡!]+", "", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(?:oye\s+)?(?:val|valeria|vale)[,:\s]+", "", norm).strip()

    match = re.match(
        r"^(?:guarda|guardar|anota|toma)\s+(?:esta\s+)?nota\s+de\s+(?:finca|caso)\s*:?\s*(.+)$",
        norm,
    )
    if not match:
        return False

    raw_payload = raw
    if ":" in raw_payload:
        note_text = raw_payload.split(":", 1)[1].strip()
    else:
        note_text = re.sub(
            r"(?is)^\s*(?:oye\s+)?(?:val|valeria|vale)[,:\s]+",
            "",
            raw_payload,
        ).strip()
        note_text = re.sub(
            r"(?is)^(?:guarda|guardar|anota|toma)\s+(?:esta\s+)?nota\s+de\s+(?:finca|caso)\s*",
            "",
            note_text,
        ).strip(" :-")

    if not note_text:
        await update.message.reply_text("Dime qué nota de finca/caso quieres guardar.")
        return True

    try:
        from memory_store import set_active_case_id

        case_id = get_active_case_id(int(chat_id)) or CASE_KEY
        set_active_case_id(int(chat_id), str(case_id))
        note_id = insert_case_note(
            chat_id=int(chat_id),
            case_id=str(case_id),
            note_text=note_text,
            source="karen_explicit_case_note",
        )
        _LAST_ACTION[int(chat_id)] = {
            "type": "note_insert",
            "id": note_id,
            "case_id": str(case_id),
        }
        await update.message.reply_text(
            "📝 Guardé esta nota de finca/caso.\n\n"
            f"{note_text}\n\n"
            "Si quieres que te avise, dime: “Val, recuérdame esto mañana a las 9”."
        )
        return True
    except Exception as e:
        logger.exception(f"[KAREN_EXPLICIT_CASE_NOTE] failed: {e}")
        await update.message.reply_text("Intenté guardar la nota de finca/caso, pero algo falló.")
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
    client_id = resolve_client_id(chat_id)
    shadow_message_id = getattr(update.message, "message_id", None)
    _maybe_log_intent_router_v2_shadow(text, chat_id=chat_id, client_id=client_id, message_id=shadow_message_id)

    try:
        if await maybe_handle_karen_name_language_guard(update, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_NAME_LANGUAGE_GUARD_PIPELINE] failed: {e}")

    # RC-KAREN-05B HARD TASK QUERY GATE:
    # Must remain above GCal/document/case routes and MEMORY_TEST_TEXT insertion.
    try:
        if await maybe_handle_karen_task_query_hard_gate(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("task_query", "maybe_handle_karen_task_query_hard_gate", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_QUERY_HARD_GATE_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_gcal_create_confirmation_first(update, chat_id, text):
            _maybe_log_intent_router_v2_actual("destructive_confirmation", "maybe_handle_karen_gcal_create_confirmation_first", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[GCAL_CONFIRM_ROUTE_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_pending_reminder_context(update, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("pending_action_reply", "maybe_handle_karen_pending_reminder_context", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_PENDING_REMINDER_CONTEXT_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_task_delete_followup(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("pending_action_reply", "maybe_handle_karen_task_delete_followup", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_DELETE_FOLLOWUP_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_pending_gcal_delete_confirmation(update, chat_id, text):
            _maybe_log_intent_router_v2_actual("destructive_confirmation", "maybe_handle_pending_gcal_delete_confirmation", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[GCAL_DELETE_CONFIRM_ROUTE_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_gcal_event_number_delete(update, chat_id, text):
            _maybe_log_intent_router_v2_actual("gcal_delete", "maybe_handle_karen_gcal_event_number_delete", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_GCAL_EVENT_NUMBER_DELETE_PIPELINE] failed: {e}")

    try:
        if _looks_like_karen_gcal_event_create_request(text):
            logger.info("[GCAL_CREATE_ROUTE] matched live text category=gcal_event_create")
            if await try_appointment_save_natural(update, chat_id, text):
                _maybe_log_intent_router_v2_actual("gcal_create", "try_appointment_save_natural", chat_id=chat_id, message_id=shadow_message_id, text=text)
                return
    except Exception as e:
        logger.exception(f"[GCAL_CREATE_ROUTE_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_weekday_agenda_query(update, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("agenda_query", "maybe_handle_karen_weekday_agenda_query", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_WEEKDAY_AGENDA_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_natural_weekday_reminder(update, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("reminder_create", "maybe_handle_karen_natural_weekday_reminder", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_NATURAL_WEEKDAY_REMINDER_PIPELINE] failed: {e}")

    if looks_like_technical_paste(text):
        await update.message.reply_text(TECHNICAL_PASTE_REPLY)
        return

    try:
        if parse_karen_task_schedule_for_tomorrow(text):
            if await maybe_handle_karen_task_schedule_for_tomorrow(update, context, chat_id, client_id, text):
                return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_SCHEDULE_EARLY_PIPELINE] failed: {e}")

    try:
        if await maybe_guard_unknown_client_protected_workflow(update, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[CLIENT_WORKFLOW_GUARD_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_notes_tasks_visibility(update, context, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_NOTES_TASKS_VISIBILITY_EARLY_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_explicit_case_note(update, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_EXPLICIT_CASE_NOTE_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_task_delete_followup(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("pending_action_reply", "maybe_handle_karen_task_delete_followup", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
        if await maybe_handle_karen_reminder_management(update, context, chat_id, text):
            _maybe_log_intent_router_v2_actual(_observer_intent_for_karen_reminder_management(text), "maybe_handle_karen_reminder_management", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_REMINDER_MANAGEMENT_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_task_creation(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("task_create", "maybe_handle_karen_task_creation", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_CREATE_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_notes_tasks_visibility(update, context, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_NOTES_TASKS_VISIBILITY_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_task_schedule_for_tomorrow(update, context, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_SCHEDULE_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_task_delete_request(update, context, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_DELETE_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_task_completion(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("task_complete", "maybe_handle_karen_task_completion", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_COMPLETION_PIPELINE] failed: {e}")

    try:
        if _looks_like_karen_gcal_event_create_request(text):
            if await try_appointment_save_natural(update, chat_id, text):
                _maybe_log_intent_router_v2_actual("gcal_create", "try_appointment_save_natural", chat_id=chat_id, message_id=shadow_message_id, text=text)
                return
    except Exception as e:
        logger.exception(f"[KAREN_GCAL_CREATE_EARLY_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_day0_route(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("agenda_query", "maybe_handle_karen_day0_route", chat_id=chat_id, message_id=shadow_message_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_DAY0_ROUTE_RELIABILITY_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_karen_daily_operator_query(update, context, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_DAILY_OPERATOR_PIPELINE_ROUTE] failed: {e}")

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

    # --------------------------------------------------
    # KAREN EARLY CAPABILITIES HARD GATE
    # Must run before document/case routes. Karen asked this in live test and
    # it was hijacked by CASE:KAREN-LAND-001 document listing.
    # --------------------------------------------------
    try:
        early_norm = unicodedata.normalize("NFKD", (text or "").lower())
        early_norm = "".join(ch for ch in early_norm if not unicodedata.combining(ch))
        early_norm = re.sub(r"[¿?¡!.,:;]+", " ", early_norm)
        early_norm = re.sub(r"\s+", " ", early_norm).strip()
        early_norm = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", early_norm).strip()
        early_norm = re.sub(r"^(val|valeria|vale)\s+", "", early_norm).strip()
        early_norm = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", early_norm).strip()

        # EARLY KAREN AGENDA HARD OVERRIDE
        # Must beat document/case routes. "Qué tengo hoy" was being hijacked
        # by document inventory for CASE:KAREN-LAND-001.
        early_agenda_direct_markers = {
            "que tengo hoy": "today",
            "que tengo para hoy": "today",
            "tengo para hoy": "today",
            "que hay hoy": "today",
            "que hay para hoy": "today",
            "que debo hacer hoy": "today",
            "que tengo manana": "tomorrow",
            "que tengo para manana": "tomorrow",
            "tengo para manana": "tomorrow",
            "que tengo mañana": "tomorrow",
            "que tengo para mañana": "tomorrow",
            "tengo para mañana": "tomorrow",
            "que hay manana": "tomorrow",
            "que hay para manana": "tomorrow",
            "que hay mañana": "tomorrow",
            "que hay para mañana": "tomorrow",
            "que tengo esta semana": "week",
            "que tengo para esta semana": "week",
            "tengo para esta semana": "week",
            "que hay para esta semana": "week",
        }

        if early_norm in early_agenda_direct_markers:
            reply = build_client_agenda_dashboard(
                client_id,
                chat_id,
                early_agenda_direct_markers[early_norm],
            )
            await update.message.reply_text(reply, disable_web_page_preview=True)
            return

        if _looks_like_karen_gcal_event_create_request(text):
            if await try_appointment_save_natural(update, chat_id, text):
                return

        early_capability_markers = (
            "que puedes hacer hoy",
            "que puedes hacer",
            "que sabes hacer",
            "como me puedes ayudar",
            "capacidades",
        )

        if any(m in early_norm for m in early_capability_markers):
            from core.client_context_reader import render_client_context_answer
            reply = render_client_context_answer(text or "", client_id=client_id)
            if reply:
                await update.message.reply_text(reply)
                return
    except Exception as e:
        logger.exception(f"[KAREN_EARLY_CAPABILITIES_HARD_GATE] failed: {e}")

    # --------------------------------------------------
    # KAREN_INTERROGATOR_EARLY_GATE
    # If an Interrogator session is active, consume the user's answer
    # before greeting/router/journal/task layers can steal it.
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_interrogator(update, context, chat_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_INTERROGATOR_EARLY_GATE] failed: {e}")

    # --------------------------------------------------
    # GREETING OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        text_norm_greet = unicodedata.normalize("NFKD", (text or "").lower())
        text_norm_greet = "".join(ch for ch in text_norm_greet if not unicodedata.combining(ch))
        text_norm_greet = re.sub(r"[¿?¡!.,:;]+", "", text_norm_greet).strip()

        # M5J: Karen preferred-name/vocative hard guard.
        # Stored active profile wins over contradictory recent memory.
        karen_name_norm = re.sub(r"^(val|valeria|vale)\s+", "", text_norm_greet).strip()
        if _is_karen_client_id(client_id):
            if karen_name_norm in (
                "cual es mi apodo registrado",
                "como me vas a llamar",
                "cual es mi nombre registrado",
                "cual es mi apodo",
            ):
                await update.message.reply_text("Tu apodo registrado es: Tany. Lo estoy usando con y griega.")
                return

            if karen_name_norm in (
                "saludame como me llamarias normalmente",
                "saludame como me llamarias",
                "saludame normal",
                "saludame",
            ):
                await update.message.reply_text("Tany, ¿qué movida seguimos hoy?")
                return

        greeting_markers = (
            "hola",
            "hola val",
            "buenas",
            "buenas val",
            "hello",
            "hi",
            "hey",
        )

        help_markers = (
            "ayuda",
            "help",
            "comandos",
            "ejemplos",
        )

        capability_markers = (
            "que puedes hacer",
            "que haces",
            "para que sirves",
            "what can you do",
            "what do you do",
        )

        lost_markers = (
            "estoy perdida",
            "estoy perdido",
            "me perdi",
            "me perdi",
            "no se que hacer",
            "no se que hacer",
            "que hago",
            "que hago",
            "estoy perdida que hago",
            "estoy perdido que hago",
        )

        if text_norm_greet in greeting_markers:
            reply = "Hola 👀 Estoy aquí. Dime qué quieres recordar, organizar o resolver."
            await update.message.reply_text(reply)
            return

        if text_norm_greet in help_markers:
            from core.control import build_user_help_message
            reply = build_user_help_message()
            await update.message.reply_text(reply)
            return

        if text_norm_greet in lost_markers:
            reply = build_alpha_lost_reply(preferred_name)
            await update.message.reply_text(reply)
            return

        identity_markers = (
            "quien eres",
            "quién eres",
            "quien sos",
            "quién sos",
            "quien es valeria",
            "quién es valeria",
            "que eres",
            "qué eres",
            "who are you",
            "what are you",
        )

        if text_norm_greet in identity_markers:
            reply = build_dynamic_founder_beta_reply(
                int(chat_id),
                text,
                kind="identity",
                preferred_name=preferred_name,
                preferred_language=preferred_language,
            )
            if not reply:
                reply = (
                    "Soy Valeria, una asistente en founder-beta dentro de Telegram. "
                    "Mi trabajo es ayudarte a recordar, ordenar y avanzar sin que todo viva en tu cabeza.\n\n"
                    "Hoy puedo ayudarte con notas, recordatorios, ideas, pendientes, voz y agenda básica. "
                    "Todavía estoy en beta, así que no prometo magia ni autonomía perfecta; "
                    "pero para capturar y organizar el caos diario, ya sirvo."
                )
            await update.message.reply_text(reply)
            return

        if text_norm_greet in capability_markers:
            reply = build_dynamic_founder_beta_reply(
                int(chat_id),
                text,
                kind="capability",
                preferred_name=preferred_name,
                preferred_language=preferred_language,
            )
            if not reply:
                reply = build_alpha_capability_reply(preferred_name)
            await update.message.reply_text(reply)
            return

        reminder_capability_markers = (
            "puedes recordarme cosas",
            "puedes recordarme algo",
            "me puedes recordar cosas",
            "me puedes recordar algo",
            "puedes hacer recordatorios",
            "haces recordatorios",
            "recordarme cosas",
            "recordarme algo",
            "puedes crear recordatorios",
            "puedes poner recordatorios",
        )

        if text_norm_greet in reminder_capability_markers:
            reply = (
                "Sí. Puedo ayudarte con recordatorios si me dices qué y cuándo.\n\n"
                "Ejemplo: Recuérdame mañana a las 9 revisar una compra."
            )
            await update.message.reply_text(reply)
            return

        calendar_capability_markers = (
            "puedes manejar mi calendario completo",
            "puedes manejar mi calendario",
            "manejas calendario",
            "manejas mi calendario",
            "puedes gestionar mi calendario",
            "puedes usar mi calendario",
            "puedes crear eventos",
            "puedes revisar mi agenda",
            "puedes manejar agenda",
            "puedes manejar mi agenda",
        )

        if text_norm_greet in calendar_capability_markers:
            reply = (
                "Sí, puedo ayudarte con calendario cuando está conectado: revisar agenda, "
                "crear eventos básicos, organizar tu día y trabajar con recordatorios.\n\n"
                "Lo que todavía no prometo en founder-beta es manejo perfecto o control completo "
                "de todos los casos. Para agenda y eventos básicos, sí."
            )
            await update.message.reply_text(reply)
            return

        # --------------------------------------------------
        # KAREN UPPER REMINDER / AGENDA / MULTI-INTENT SHIELD
        # Must run before Carpeta Clara / whatnow / document gates.
        # This prevents "recuérdame..." and "agenda" from being hijacked
        # by land-case/document routes.
        # --------------------------------------------------
        try:
            karen_upper_norm = text_norm_greet
            karen_upper_norm = re.sub(r"^val\s+", "", karen_upper_norm).strip()

            # Multi-intent shield: 1/2/3-style bundled request.
            has_numbered_multi = (
                ("1" in karen_upper_norm or "uno" in karen_upper_norm)
                and ("2" in karen_upper_norm or "dos" in karen_upper_norm)
                and ("3" in karen_upper_norm or "tres" in karen_upper_norm)
            )
            has_karen_multi_content = (
                ("paquete" in karen_upper_norm and "nora" in karen_upper_norm)
                or ("preguntas" in karen_upper_norm and ("reunion" in karen_upper_norm or "reunión" in karen_upper_norm))
                or ("recordatorio" in karen_upper_norm or "recuerdame" in karen_upper_norm)
            )

            if has_numbered_multi and has_karen_multi_content:
                reply = (
                    "Veo varias instrucciones juntas, Insanity 😌📌\n\n"
                    "Te las separo para que no se vuelva sopa de letras legal:\n\n"
                    "1️⃣ Paquete para Nora: puedo prepararlo.\n"
                    "2️⃣ Preguntas principales para la reunión: puedo sacarlas del paquete.\n"
                    "3️⃣ Recordatorio para la cita: necesito la hora exacta de la cita para calcular “una hora antes”.\n\n"
                    "Mándame una de estas ahora:\n"
                    "• “Val, prepárame el paquete para Nora”\n"
                    "• “Val, dame las preguntas principales para Nora”\n"
                    "• “Val, la cita es hoy a las 3:00 pm, recuérdame una hora antes preparar documentos”\n\n"
                    "Una por una, y yo las voy ejecutando sin hacer malabares con machetes. 😏"
                )
                await update.message.reply_text(reply)
                return

            # Reminder list shield.
            reminder_list_markers = (
                "que tengo registrado como recordatorio",
                "que tienes registrado como recordatorio",
                "que tengo en recordatorio",
                "que recordatorios tengo",
                "dime mis recordatorios",
                "muestrame mis recordatorios",
            )

            if any(m in karen_upper_norm for m in reminder_list_markers):
                await reminders_cmd(update, context)
                return

            # Client Google Calendar connect preview shield.
            calendar_connect_markers = (
                "conecta mi google calendar",
                "conectar mi google calendar",
                "conecta google calendar",
                "conectar google calendar",
                "quiero conectar mi calendario",
                "conectar mi calendario",
                "conecta mi calendario",
            )

            if any(m in karen_upper_norm for m in calendar_connect_markers):
                await update.message.reply_text(
                    "📅 Conectar Google Calendar\n\n"
                    "Ya estoy preparando la conexión de Google Calendar para Karen, "
                    "pero todavía no voy a pedirte autorización real.\n\n"
                    "Modo planeado:\n"
                    "• conexión por cliente\n"
                    "• solo lectura primero\n"
                    "• sin usar credenciales globales\n"
                    "• sin crear, cambiar ni borrar eventos\n\n"
                    "Qué ya puedo hacer ahora:\n"
                    "• manejar tu agenda interna de Val\n"
                    "• guardar citas\n"
                    "• recordarte antes de una cita\n"
                    "• decirte qué tienes en agenda dentro de Val\n\n"
                    "Qué falta antes de conectar Google Calendar real:\n"
                    "• activar callback seguro público con HTTPS\n"
                    "• guardar token solo en tu carpeta de cliente\n"
                    "• confirmar que no se registren códigos ni tokens en logs\n\n"
                    "Cuando esté listo, te voy a dar un enlace de autorización seguro. "
                    "Por ahora no tienes que tocar nada."
                )
                return

            # Client calendar connection status shield.
            calendar_status_markers = (
                "mi calendario esta conectado",
                "mi calendario está conectado",
                "puedes ver mi calendario",
                "puedes revisar mi calendario",
                "tienes acceso a mi calendario",
                "mi google calendar esta conectado",
                "mi google calendar está conectado",
                "google calendar esta conectado",
                "google calendar está conectado",
            )

            if any(m in karen_upper_norm for m in calendar_status_markers):
                from core.client_calendar_config import render_client_calendar_status
                await update.message.reply_text(render_client_calendar_status(client_id))
                return

            # Natural Appointment Save v0.
            appointment_save_markers = (
                "tengo cita",
                "tengo una cita",
                "cita con",
                "reunion con",
                "reunión con",
                "tengo reunion",
                "tengo reunión",
                "crea evento",
                "crear evento",
                "google calendar",
                "pon en mi calendario",
                "pon en el calendario",
                "agrega al calendario",
                "agregar al calendario",
                "agregala al calendario",
                "agrégala al calendario",
            )

            if any(m in karen_upper_norm for m in appointment_save_markers):
                if await try_appointment_save_natural(update, chat_id, text):
                    return

            # Agenda Bridge v0: specific date lookup.
            agenda_date_lookup_markers = (
                "que cita tengo",
                "que citas tengo",
                "que tengo para el",
                "que tengo el",
                "tengo algo el",
                "hay algo el",
                "agenda para el",
            )

            if any(m in karen_upper_norm for m in agenda_date_lookup_markers):
                if await try_agenda_date_lookup_natural(update, chat_id, text):
                    return

            # Agenda query shield.
            agenda_direct_markers = (
                "que tengo hoy",
                "que tengo para hoy",
                "tengo para hoy",
                "que hay hoy",
                "que hay para hoy",
                "que debo hacer hoy",
                "que tengo manana",
                "que tengo para manana",
                "tengo para manana",
                "que tengo mañana",
                "que tengo para mañana",
                "tengo para mañana",
                "que hay manana",
                "que hay para manana",
                "que hay mañana",
                "que hay para mañana",
                "que tengo esta semana",
                "que tengo para esta semana",
                "tengo para esta semana",
                "que hay para esta semana",
            )

            if any(m == karen_upper_norm for m in agenda_direct_markers):
                if "esta semana" in karen_upper_norm:
                    reply = build_client_agenda_dashboard(client_id, chat_id, "week")
                elif "manana" in karen_upper_norm or "mañana" in karen_upper_norm:
                    reply = build_client_agenda_dashboard(client_id, chat_id, "tomorrow")
                else:
                    reply = build_client_agenda_dashboard(client_id, chat_id, "today")

                await update.message.reply_text(reply, disable_web_page_preview=True)
                return

            agenda_query_markers = (
                "que tengo en agenda",
                "dime que tengo en agenda",
                "mi agenda",
            )

            if any(m in karen_upper_norm for m in agenda_query_markers):
                voc = client_vocative(client_id)
                reply = (
                    f"Claro{voc} 😌📅\n\n"
                    "Para agenda puedo revisar por ventana de tiempo. Dime una de estas:\n\n"
                    "• “Val, ¿qué tengo hoy?”\n"
                    "• “Val, ¿qué tengo mañana?”\n"
                    "• “Val, ¿qué tengo esta semana?”\n\n"
                    "Así no mezclo agenda real con el novelón del terreno, porque ahí es donde el caos se pone creativo. 😏"
                )
                await update.message.reply_text(reply)
                return

            # Relative reminder shield.
            reminder_prefixes = (
                "recuerdame",
                "recordarme",
                "recordatorio",
            )
            relative_before_markers = (
                "una hora antes",
                "1 hora antes",
                "una hora antes de",
                "1 hora antes de",
            )
            has_explicit_clock = bool(re.search(r"\b(?:a las|a la)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", karen_upper_norm))

            if (
                any(p in karen_upper_norm for p in reminder_prefixes)
                and any(m in karen_upper_norm for m in relative_before_markers)
                and not has_explicit_clock
            ):
                voc = client_vocative(client_id)
                reply = (
                    f"Sí, puedo hacerlo{voc} ⏰📁\n\n"
                    "Pero necesito la hora exacta de la cita para calcular “una hora antes”. "
                    "Todavía no voy a adivinar horarios como bruja de feria, gracias. 😌\n\n"
                    "Mándamelo así:\n"
                    "“Val, la cita es hoy a las 3:00 pm, recuérdame una hora antes preparar documentos.”"
                )
                await update.message.reply_text(reply)
                return

        except Exception as e:
            logger.exception(f"[KAREN_UPPER_REMINDER_AGENDA_SHIELD] failed: {e}")

        # --------------------------------------------------
        # KAREN TRUST-KILLER PRIORITY SHIELD V0
        # Runs before legal/docs routing so supermarket/capabilities/agenda
        # do not get hijacked by the land-case routes.
        # --------------------------------------------------
        try:
            kr_priority_norm = text_norm_greet
            kr_priority_norm = re.sub(r"^val\s+", "", kr_priority_norm).strip()

            # Capabilities must answer the founder-beta capabilities, not documents/case.
            capability_priority_markers = (
                "que puedes hacer hoy",
                "que puedes hacer",
                "que sabes hacer",
                "como me puedes ayudar",
                "cómo me puedes ayudar",
                "capacidades",
            )
            if any(m in kr_priority_norm for m in capability_priority_markers):
                from core.client_context_reader import render_client_context_answer
                reply = render_client_context_answer(text or "", client_id=client_id)
                if reply:
                    await update.message.reply_text(reply)
                    return

            # Grocery/list must beat legal/case routes.
            grocery_priority_markers = (
                "super",
                "súper",
                "supermercado",
                "lista de compras",
                "lista del super",
                "lista del súper",
            )
            grocery_verbs = (
                "agrega ",
                "añade ",
                "anota ",
                "apunta ",
                "mete ",
                "borra ",
                "quita ",
                "elimina ",
                "saca ",
            )
            if any(m in kr_priority_norm for m in grocery_priority_markers) or kr_priority_norm.startswith(grocery_verbs):
                from core.client_context_reader import render_client_context_answer
                reply = render_client_context_answer(text or "", client_id=client_id)
                if reply:
                    await update.message.reply_text(reply)
                    return

            # Appointment/date lookup must not fall into the land-case response.
            appointment_lookup_markers = (
                "que cita tengo",
                "qué cita tengo",
                "que citas tengo",
                "qué citas tengo",
                "que tengo para el",
                "qué tengo para el",
                "cita para el",
                "citas para el",
            )
            if any(m in kr_priority_norm for m in appointment_lookup_markers):
                try:
                    await reminders_cmd(update, context)
                    return
                except Exception:
                    voc = client_vocative(client_id, prefix="")
                    lead = f"{voc}, " if voc else ""
                    await update.message.reply_text(
                        f"{lead}eso suena a consulta de agenda/cita 📅\n\n"
                        "Todavía estoy afinando búsqueda por fecha exacta, pero no lo voy a mezclar con el caso del terreno. "
                        "Prueba también: “Val, ¿qué tengo hoy?”, “Val, ¿qué tengo mañana?” o “Val, dime mis recordatorios”."
                    )
                    return

        except Exception as e:
            logger.exception(f"[KAREN_TRUST_KILLER_PRIORITY_SHIELD_V0] failed: {e}")

        # --------------------------------------------------
        # KAREN CLIENT CONTEXT READER V0
        # Lets Karen ask about current capabilities, roadmap, status, and ideas.
        # Read-only for now; idea persistence will come later.
        # --------------------------------------------------
        try:
            from core.client_context_reader import render_client_context_answer
            client_context_reply = render_client_context_answer(text or "", client_id=client_id)
            if client_context_reply:
                await update.message.reply_text(client_context_reply)
                return
        except Exception as e:
            logger.exception(f"[KAREN_CLIENT_CONTEXT_READER_V0] failed: {e}")

        # --------------------------------------------------
        # KAREN NATURAL INTENT ROUTER V0
        # Deterministic classifier over internal tools.
        # Connect legal/docs intents first; leave agenda/reminders to existing gates.
        # --------------------------------------------------
        try:
            from core.karen_intent_router import classify_karen_intent
            karen_intent = classify_karen_intent(text or "")

            if karen_intent.confidence >= 0.85:
                if karen_intent.name == "prepare_lawyer":
                    from core.karen_lawyer_package import render_lawyer_package
                    await reply_text_chunked_safe(update, render_lawyer_package(int(chat_id)))
                    return

                if karen_intent.name == "review_missing":
                    await update.message.reply_text(render_karen_missing_review_checklist())
                    return

                if karen_intent.name == "organize_documents":
                    reply = (
                        "📁✨ Empezamos ordenando el caso por partes, Insanity. Sin drama, sin bolsa de papeles explotando en la mesa. 😌\n\n"
                        "1. Primero vemos qué documentos/fotos ya tengo registrados.\n"
                        "2. Después separo qué tiene texto extraído y qué necesita OCR o revisión manual.\n"
                        "3. Luego preparo un resumen claro: cronología, datos clave, pendientes y preguntas para Nora.\n\n"
                        "Puedes seguir con una de estas:\n"
                        "- “Val, ¿qué documentos tengo registrados?”\n"
                        "- “Val, ¿qué falta revisar antes de hablar con la abogada?”\n"
                        "- “Val, prepárame el paquete para Nora.”"
                    )
                    await update.message.reply_text(reply)
                    return

        except Exception as e:
            logger.exception(f"[KAREN_NATURAL_INTENT_ROUTER_V0] failed: {e}")

        # --------------------------------------------------
        # KAREN / CARPETA CLARA DOCUMENT ONBOARDING GATE
        # Must run before generic whatnow.
        # --------------------------------------------------
        try:
            carpeta_norm = text_norm_greet
            carpeta_doc_markers = (
                "organizar documentos",
                "ordenar documentos",
                "documentos de mi caso",
                "documentos del caso",
                "papeles del caso",
                "quiero organizar documentos",
                "quiero ordenar documentos",
            )
            carpeta_start_markers = (
                "por donde empezamos",
                "por dónde empezamos",
                "por donde empiezo",
                "por dónde empiezo",
                "como empezamos",
                "cómo empezamos",
                "que hago primero",
                "qué hago primero",
            )

            if (
                any(m in carpeta_norm for m in carpeta_doc_markers)
                and (
                    any(m in carpeta_norm for m in carpeta_start_markers)
                    or "empezamos" in carpeta_norm
                    or "empiezo" in carpeta_norm
                )
            ):
                reply = (
                    "📁✨ Empezamos ordenando el caso por partes, Insanity. Sin drama, sin bolsa de papeles explotando en la mesa. 😌\n\n"
                    "1. Primero vemos qué documentos/fotos ya tengo registrados.\n"
                    "2. Después separo qué tiene texto extraído y qué necesita OCR o revisión manual.\n"
                    "3. Luego preparo un resumen claro: cronología, datos clave, pendientes y preguntas para Nora.\n\n"
                    "Puedes seguir con una de estas:\n"
                    "- “Val, ¿qué documentos tengo registrados?”\n"
                    "- “Val, ¿qué falta revisar antes de hablar con la abogada?”\n"
                    "- “Val, prepárame el paquete para Nora.”"
                )
                await update.message.reply_text(reply)
                return
        except Exception as e:
            logger.exception(f"[KAREN_CARPETA_CLARA_ONBOARDING_GATE] failed: {e}")

        # --------------------------------------------------
        # KAREN NATURAL ABOGADA DOCUMENT PREP GATE
        # Catches voice/natural phrases like:
        # "tengo que llevarle documentos a la abogada"
        # "preparar documentos para la abogada"
        # before whatnow/task capture hijacks them.
        # --------------------------------------------------
        try:
            prep_norm = text_norm_greet
            prep_context = (
                "abogada" in prep_norm
                or "abogado" in prep_norm
                or "nora" in prep_norm
            )
            prep_doc_markers = (
                "llevarle documentos",
                "llevarle los documentos",
                "llevarle mis documentos",
                "llevar documentos",
                "llevar los documentos",
                "llevar mis documentos",
                "llevarle papeles",
                "llevarle los papeles",
                "llevarle mis papeles",
                "llevar papeles",
                "llevar los papeles",
                "llevar mis papeles",
                "preparar documentos",
                "preparar los documentos",
                "preparar mis documentos",
                "preparar papeles",
                "preparar los papeles",
                "preparar mis papeles",
                "documentos para la abogada",
                "los documentos para la abogada",
                "mis documentos para la abogada",
                "papeles para la abogada",
                "los papeles para la abogada",
                "mis papeles para la abogada",
                "documentos para nora",
                "los documentos para nora",
                "mis documentos para nora",
                "papeles para nora",
                "los papeles para nora",
                "mis papeles para nora",
            )
            prep_help_markers = (
                "ayudame",
                "ayúdame",
                "prepararme",
                "prepararlos",
                "prepararlo",
                "que hago",
                "qué hago",
                "como me preparo",
                "cómo me preparo",
            )

            if (
                prep_context
                and any(m in prep_norm for m in prep_doc_markers)
                and (
                    any(m in prep_norm for m in prep_help_markers)
                    or "tengo que" in prep_norm
                    or "necesito" in prep_norm
                )
            ):
                from core.karen_lawyer_package import render_lawyer_package
                await reply_text_chunked_safe(update, render_lawyer_package(int(chat_id)))
                return

        except Exception as e:
            logger.exception(f"[KAREN_NATURAL_ABOGADA_DOC_PREP_GATE] failed: {e}")

        # --------------------------------------------------
        # PRIORITY DECISION / WHATNOW GUARD
        # Must run before task/commitment capture so questions like
        # "¿Qué debería hacer primero?" do not become fake tasks.
        # --------------------------------------------------
        try:
            whatnow_priority_markers = (
                "que deberia hacer primero",
                "qué debería hacer primero",
                "que debo hacer primero",
                "qué debo hacer primero",
                "que hago primero",
                "qué hago primero",
                "que hago ahora",
                "qué hago ahora",
                "por donde empiezo",
                "por dónde empiezo",
                "cual es el primer paso",
                "cuál es el primer paso",
                "cual es el siguiente paso",
                "cuál es el siguiente paso",
                "what should i do first",
                "what do i do first",
                "where do i start",
                "what is the first step",
                "what is the next step",
            )

            if any(m in text_norm_greet for m in whatnow_priority_markers):
                await whatnow_cmd(update, context)
                return

        except Exception as e:
            logger.exception(f"[WHATNOW_PRIORITY_GUARD] failed: {e}")

        # --------------------------------------------------
        # LLM OPERATOR ROUTER V1
        # --------------------------------------------------
        operator_route = "normal_chat"
        operator_confidence = 0.0

        # Karen lawyer-package requests must beat generic draft/follow-up routing.
        # Phrases like "prepara un paquete para la abogada Nora Santa..."
        # are attorney package requests, not sales follow-up drafts.
        try:
            if await maybe_handle_karen_lawyer_package(update, context, text):
                return
        except Exception as e:
            logger.exception(f"[KAREN_LAWYER_PACKAGE_EARLY_PIPELINE_GATE] failed: {e}")

        try:
            if looks_like_karen_meeting_prep_request(text):
                await update.message.reply_text(render_karen_meeting_prep_checklist(text))
                return
        except Exception as e:
            logger.exception(f"[KAREN_MEETING_PREP_EARLY_GATE] failed: {e}")

        # Karen / Nora attorney-prep EARLY gate
        # Must beat document_summary_query so "resumen claro para Nora" and
        # "qué falta revisar antes de hablar con la abogada" return the polished package.
        try:
            nora_early_norm = _norm_text(text or "")
            nora_early_context = (
                "nora" in nora_early_norm
                or "abogada" in nora_early_norm
                or "abogado" in nora_early_norm
            )
            nora_early_markers = (
                "preparame un resumen",
                "prepárame un resumen",
                "resumen claro",
                "llevarle esto",
                "que me falta revisar",
                "qué me falta revisar",
                "que falta revisar",
                "qué falta revisar",
                "que me falta conseguir",
                "qué me falta conseguir",
                "que falta conseguir",
                "qué falta conseguir",
                "antes de hablar",
                "paquete para nora",
                "paquete para la abogada",
            )
            if nora_early_context and any(m in nora_early_norm for m in nora_early_markers):
                missing_review_markers = (
                    "que me falta revisar",
                    "qué me falta revisar",
                    "que falta revisar",
                    "qué falta revisar",
                    "que me falta conseguir",
                    "qué me falta conseguir",
                    "que falta conseguir",
                    "qué falta conseguir",
                    "antes de hablar",
                )
                package_markers = (
                    "paquete para nora",
                    "paquete para la abogada",
                    "preparame un resumen",
                    "prepárame un resumen",
                    "resumen claro",
                    "llevarle esto",
                )

                if any(m in nora_early_norm for m in missing_review_markers) and not any(m in nora_early_norm for m in package_markers):
                    await update.message.reply_text(render_karen_missing_review_checklist())
                    return

                from core.karen_lawyer_package import render_lawyer_package
                await _reply_text_chunked(update, render_lawyer_package(int(chat_id)))
                return
        except Exception as e:
            logger.exception(f"[KAREN_NORA_PREP_EARLY_GATE] failed: {e}")

        try:
            if await maybe_handle_document_ocr_query(update, context, chat_id, text):
                _maybe_log_intent_router_v2_actual("document_ocr", "maybe_handle_document_ocr_query", chat_id=chat_id, message_id=shadow_message_id, text=text)
                return
        except Exception as e:
            logger.exception(f"[KAREN_DOCUMENT_OCR_EARLY_PIPELINE] failed: {e}")

        # Karen combined legal/document summary requests must beat generic draft-follow-up routing.
        # Example:
        # "Val, hazme un resumen legal del documento con cronología, datos clave,
        # observaciones y recomendaciones para hablar con la abogada."
        try:
            early_doc_norm = _norm_text(text or "")
            early_doc_summary_markers = (
                "dame el resumen de",
                "dame resumen de",
                "hazme resumen de",
                "resume con ocr",
                "resumen con ocr",
                "haz ocr",
                "lee visualmente",
                "resume el documento",
                "resume el pdf",
                "resumen legal",
                "resumen del documento",
                "resumen de documento",
                "resumen de documentos",
                "cronologia",
                "tabla cronologica",
            )
            early_doc_context_markers = (
                "documento",
                "documentos",
                "vfms",
                "datos clave",
                "observaciones",
                "recomendaciones",
                "abogada",
                "abogado",
            )

            if (
                any(m in early_doc_norm for m in early_doc_summary_markers)
                and any(m in early_doc_norm for m in early_doc_context_markers)
            ):
                if await maybe_handle_document_summary_query(update, context, chat_id, text):
                    _maybe_log_intent_router_v2_actual("document_summary", "maybe_handle_document_summary_query", chat_id=chat_id, message_id=shadow_message_id, text=text)
                    return
        except Exception as e:
            logger.exception(f"[KAREN_COMBINED_LEGAL_DOC_SUMMARY_GATE] failed: {e}")

        try:
            # Keep this conservative: only route meaningful non-tiny messages.
            if text and len(text.strip()) >= 8:
                routed = route_operator_intent(
                    chat_id=int(chat_id),
                    user_text=text,
                    preferred_language=preferred_language or "es",
                )
                operator_route = str(routed.get("route") or "normal_chat").strip()
                operator_confidence = float(routed.get("confidence") or 0.0)

                # Rich story beats whatnow:
                # If the user includes emotional context / multiple life areas / "I don't know where to start",
                # capture the update first instead of jumping straight to advice.
                rich_story_markers = (
                    "tengo muchas cosas",
                    "cosas mezcladas",
                    "muchas cosas mezcladas",
                    "me frustra",
                    "no quiero que me regañes",
                    "quiero que me ayudes a ordenar",
                    "salud",
                    "pendientes",
                    "ideas",
                    "casa",
                    "familia",
                    "trabajo",
                    "todo mezclado",
                    "i have a lot going on",
                    "everything is mixed",
                    "help me organize",
                )

                looks_like_rich_story = (
                    len(text or "") >= 55
                    and any(m in text_norm_greet for m in rich_story_markers)
                )

                if operator_confidence >= 0.82 and operator_route == "whatnow" and not looks_like_rich_story:
                    await whatnow_cmd(update, context)
                    return

                if looks_like_rich_story:
                    operator_route = "journal_capture"
                    operator_confidence = max(operator_confidence, 0.86)

                if operator_confidence >= 0.82 and operator_route == "exosummary":
                    # Karen sprint context-aware summary:
                    # If this chat has Karen land-case facts, show those instead of generic saved-memory view.
                    try:
                        from core.karen_case_facts import load_karen_case_facts, render_case_facts
                        case_facts = load_karen_case_facts(int(chat_id))
                        if case_facts:
                            await update.message.reply_text(render_case_facts(case_facts, mode="all", chat_id=int(chat_id)))
                            return
                    except Exception as e:
                        logger.exception(f"[KAREN_CASE_FACTS_ROUTER_SUMMARY] failed: {e}")

                    await exosummary_cmd(update, context)
                    return

                if operator_confidence >= 0.82 and operator_route == "draft_followup":
                    await draftfollowup_cmd(update, context)
                    return

                # journal_capture is handled below by Natural Smart Journal.
                # flow_request remains command-based for now to avoid accidental roadmap spam.

        except Exception as e:
            logger.exception(f"[LLM_OPERATOR_ROUTER_GATE] failed: {e}")

        # --------------------------------------------------
        # NATURAL OPERATOR COMMAND ROUTES (FRIENDLY MARK 1)
        # Fallback phrase routes if LLM router fails or confidence is low.
        # --------------------------------------------------
        try:
            whatnow_natural_markers = (
                "que hago ahora",
                "qué hago ahora",
                "que hago",
                "qué hago",
                "que sigue",
                "qué sigue",
                "cual es el siguiente paso",
                "cuál es el siguiente paso",
                "por donde empiezo",
                "por dónde empiezo",
                "estoy perdida",
                "estoy perdido",
                "estoy enredada",
                "estoy enredado",
                "no se por donde empezar",
                "no sé por dónde empezar",
                "what now",
                "what should i do",
                "where do i start",
            )

            summary_natural_markers = (
                "que guardaste",
                "qué guardaste",
                "que tienes guardado",
                "qué tienes guardado",
                "muestrame lo que guardaste",
                "muéstrame lo que guardaste",
                "muestrame el resumen",
                "muéstrame el resumen",
                "resumen de esto",
                "show me what you saved",
                "show me the summary",
                "what did you save",
            )

            draft_natural_markers = (
                "hazme el mensaje",
                "redactame el mensaje",
                "redáctame el mensaje",
                "preparame el mensaje",
                "prepárame el mensaje",
                "haz el follow up",
                "haz el seguimiento",
                "redacta el seguimiento",
                "draft the message",
                "draft the follow up",
                "write the message",
            )

            if any(m in text_norm_greet for m in whatnow_natural_markers):
                await whatnow_cmd(update, context)
                return

            if any(m in text_norm_greet for m in summary_natural_markers):
                # Karen sprint context-aware summary:
                # If this chat has Karen land-case facts, "qué guardaste" should show
                # the useful case facts instead of generic Exocortex/debug-ish memory.
                try:
                    from core.karen_case_facts import load_karen_case_facts, render_case_facts
                    case_facts = load_karen_case_facts(int(chat_id))
                    if case_facts:
                        await update.message.reply_text(render_case_facts(case_facts, mode="all", chat_id=int(chat_id)))
                        return
                except Exception as e:
                    logger.exception(f"[KAREN_CASE_FACTS_SUMMARY_FALLBACK] failed: {e}")

                await exosummary_cmd(update, context)
                return

            if any(m in text_norm_greet for m in draft_natural_markers):
                await draftfollowup_cmd(update, context)
                return

        except Exception as e:
            logger.exception(f"[NATURAL_OPERATOR_ROUTES] failed: {e}")

        # --------------------------------------------------
        # NATURAL SMART JOURNAL ROUTE (CONSERVATIVE MARK 1)
        # --------------------------------------------------
        try:
            natural_journal_markers = (
                "today was",
                "today has been",
                "rough day",
                "bad day",
                "hard day",
                "i'm overwhelmed",
                "im overwhelmed",
                "i feel overwhelmed",
                "i'm honestly overwhelmed",
                "hoy fue",
                "hoy ha sido",
                "dia pesado",
                "día pesado",
                "dia dificil",
                "día difícil",
                "estoy abrumado",
                "estoy abrumada",
                "me siento abrumado",
                "me siento abrumada",
                "me siento cargado",
                "me siento cargada",
            )

            business_journal_markers = (
                "supplier",
                "provider",
                "quote",
                "client",
                "customer",
                "follow-up",
                "follow up",
                "didn't answer",
                "did not answer",
                "still needs",
                "proveedor",
                "cotizacion",
                "cotización",
                "cliente",
                "seguimiento",
                "no respondio",
                "no respondió",
                "necesita",
            )

            looks_like_journal = (
                (
                    operator_route == "journal_capture"
                    and operator_confidence >= 0.75
                    and len(text or "") >= 25
                )
                or (
                    len(text or "") >= 45
                    and (
                        any(m in text_norm_greet for m in natural_journal_markers)
                        or (
                            any(m in text_norm_greet for m in business_journal_markers)
                            and any(x in text_norm_greet for x in ("save", "guarda", "idea", "abrum", "rough", "pesado", "dificil", "difícil"))
                        )
                    )
                )
            )

            if looks_like_journal:
                data = classify_exocortex_intent(
                    chat_id=int(chat_id),
                    user_text=text,
                    preferred_language=preferred_language or "es",
                )

                buckets = data.get("buckets") or ["normal_chat"]
                confidence = float(data.get("confidence") or 0.0)

                exo_buckets = {
                    "reflection",
                    "care_mode",
                    "follow_up",
                    "idea",
                    "note",
                    "decision",
                    "parking_lot",
                    "project",
                }

                should_route_journal = (
                    confidence >= 0.65
                    and any(str(b).strip() in exo_buckets for b in buckets)
                )

                if should_route_journal:
                    summary = (data.get("summary") or "").strip()
                    stored = []
                    allowed = {
                        "note",
                        "idea",
                        "reflection",
                        "care_mode",
                        "decision",
                        "parking_lot",
                        "project",
                        "follow_up",
                        "normal_chat",
                        "task",
                        "reminder",
                    }

                    from memory_store import insert_memory_item

                    items = data.get("items") or []

                    if items:
                        for item in items:
                            bucket = str(item.get("bucket") or "").strip()
                            item_summary = str(item.get("summary") or "").strip()
                            raw_span = str(item.get("raw_span") or "").strip()

                            if bucket not in allowed:
                                bucket = "normal_chat"

                            insert_memory_item(
                                chat_id=int(chat_id),
                                bucket=bucket,
                                raw_input=raw_span or text,
                                summary=item_summary or summary or f"journal:{bucket}",
                            )
                            stored.append(bucket)
                    else:
                        for bucket in buckets:
                            bucket = str(bucket or "").strip()
                            if bucket not in allowed:
                                bucket = "normal_chat"

                            insert_memory_item(
                                chat_id=int(chat_id),
                                bucket=bucket,
                                raw_input=text,
                                summary=summary or f"journal:{bucket}",
                            )
                            stored.append(bucket)

                    label_map = {
                        "reflection": "reflexión",
                        "care_mode": "care mode",
                        "follow_up": "seguimiento",
                        "idea": "idea",
                        "note": "nota",
                        "task": "tarea",
                        "reminder": "recordatorio",
                        "decision": "decisión",
                        "parking_lot": "parking lot",
                        "project": "proyecto",
                        "normal_chat": "conversación",
                    }
                    stored_labels = [label_map.get(b, b) for b in stored]

                    system_rules = f"""
You are Valeria in Natural Smart Journal Mark 1.

The user gave a natural life/work update without using /journal.

You must:
- respond like Valeria, not like a form or admin report
- sound conversational, grounded, and useful
- briefly say what was saved, but avoid robotic phrases like "Detecté" unless necessary
- do not overpromise
- do not say reminders were created unless explicitly created by deterministic code
- if follow_up exists, mention it as something to act on, not as a created reminder
- if reflection or care_mode exists, acknowledge the emotional state briefly and naturally
- avoid gendered emotional adjectives unless the user's profile explicitly provides gender
- prefer neutral wording like "te sientes con mucha carga", "esto pesa", "hay bastante presión", "suena agotador"
- end with one concrete next step
- avoid "si quieres" endings unless genuinely asking permission
- keep it concise
- style target: warm operator, not checklist bot

Saved buckets: {stored_labels}
Classifier summary: {summary}
Classifier confidence: {confidence}
"""
                    reply = call_val_openai(
                        chat_id=int(chat_id),
                        user_text=text,
                        forced_lang=preferred_language or "es",
                        system_rules=system_rules,
                    )
                    reply = (reply or "").strip()

                    if not reply:
                        reply = (
                            "Guardé esto como journal.\n\n"
                            f"Detecté: {', '.join(stored_labels)}.\n"
                            f"Resumen: {summary or 'sin resumen'}\n\n"
                            "Siguiente paso: dime /whatnow y te ayudo a sacar una acción concreta."
                        )

                    await update.message.reply_text(reply)
                    return

        except Exception as e:
            logger.exception(f"[NATURAL_SMART_JOURNAL] failed: {e}")

    except Exception as e:
        logger.exception(f"[GREETING_OVERRIDE] failed: {e}")

    text = _strip_smalltalk_prefix(text)
    tg_msg_id = update.message.message_id
    logger.info(f"msg from chat_id={chat_id}: {text!r}")

    # --------------------------------------------------
    # ONBOARDING CONSULTANT V1 ACTIVE ANSWER GATE
    # --------------------------------------------------
    try:
        if await _maybe_handle_onboarding_answer(update, context, text):
            return
    except Exception as e:
        logger.exception(f"[ONBOARDING_GATE] failed: {e}")

    # --------------------------------------------------
    # --------------------------------------------------
    # Karen Interrogator active-answer gate
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_interrogator(update, context, chat_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_INTERROGATOR_GATE] failed: {e}")

    # Pending bug/feedback/idea report (hard gate before notes/tasks/PM)
    # --------------------------------------------------
    try:
        if await handle_pending_bug_report(update, int(chat_id), text):
            return
    except Exception as e:
        logger.exception(f"[PENDING_REPORT_HARD_GATE] failed: {e}")
    # --------------------------------------------------
    # NATURAL IDEA CAPTURE → GUIDED IDEA FLOW
    # --------------------------------------------------
    try:
        natural_idea_prefixes = (
            "tengo una idea",
            "tengo una idea:",
            "idea:",
            "se me ocurrio",
            "se me ocurrió",
            "se me ocurrio:",
            "se me ocurrió:",
        )

        if any(text_norm_greet.startswith(pfx) for pfx in natural_idea_prefixes):
            raw_text = (update.message.text or text or "").strip()
            idea_text = raw_text

            if ":" in raw_text:
                idea_text = raw_text.split(":", 1)[1].strip()

            if not idea_text:
                idea_text = raw_text.strip()

            user = update.effective_user
            _PENDING_BUG_REPORT[int(chat_id)] = {
                "kind": "idea",
                "step": "actual",
                "started_at": datetime.utcnow().isoformat(),
                "chat_id": int(chat_id),
                "user_id": getattr(user, "id", None),
                "username": getattr(user, "username", None),
                "display_name": getattr(user, "full_name", None),
                "attempted_action": idea_text,
            }

            await update.message.reply_text(
                "Buena. La registro como idea.\n\n"
                "2/4 — ¿Qué problema resolvería o qué mejoraría?"
            )
            return

    except Exception as e:
        logger.exception(f"[NATURAL_IDEA_CAPTURE] failed: {e}")

    # --------------------------------------------------
    # UNIFIED PENDING DASHBOARD OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        pending_dashboard_markers = (
            "que tengo pendiente",
            "qué tengo pendiente",
            "que tengo pendientes",
            "qué tengo pendientes",
            "mis pendientes",
            "pendientes",
            "que debo hacer",
            "qué debo hacer",
            "que debo hacer hoy",
            "qué debo hacer hoy",
        )

        if text_norm_greet in pending_dashboard_markers:
            reply = build_unified_pending_dashboard(int(chat_id))
            await update.message.reply_text(reply)
            return

    except Exception as e:
        logger.exception(f"[PENDING_DASHBOARD_OVERRIDE] failed: {e}")
        await update.message.reply_text("No pude armar tus pendientes ahora mismo. Reviso logs.")
        return

    # --------------------------------------------------
    # UNIFIED TOMORROW DASHBOARD OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        tomorrow_dashboard_markers = (
            "que tengo manana",
            "que tengo mañana",
            "qué tengo manana",
            "qué tengo mañana",
            "que debo hacer manana",
            "que debo hacer mañana",
            "qué debo hacer manana",
            "qué debo hacer mañana",
            "mis pendientes de manana",
            "mis pendientes de mañana",
            "que hay manana",
            "que hay mañana",
            "qué hay manana",
            "qué hay mañana",
        )

        if text_norm_greet in tomorrow_dashboard_markers:
            reply = build_unified_tomorrow_dashboard(int(chat_id))
            await update.message.reply_text(reply)
            return

    except Exception as e:
        logger.exception(f"[TOMORROW_DASHBOARD_OVERRIDE] failed: {e}")
        await update.message.reply_text("No pude armar el resumen de mañana. Reviso logs.")
        return

    # --------------------------------------------------
    # NATURAL NOTE OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        note_patterns = (
            r"^guarda esta nota[:\s]+(.+)$",
            r"^guardar nota[:\s]+(.+)$",
            r"^guarda nota[:\s]+(.+)$",
            r"^anota[:\s]+(.+)$",
            r"^nota[:\s]+(.+)$",
            r"^remember this[:\s]+(.+)$",
            r"^save this note[:\s]+(.+)$",
        )

        note_prefixes = (
            "guarda esta nota",
            "guardar nota",
            "guarda nota",
            "anota",
            "nota",
            "remember this",
            "save this note",
        )

        for pat in note_patterns:
            m = re.match(pat, text_norm_greet, flags=re.IGNORECASE)
            if m:
                # Match using normalized text, but extract from original text to preserve casing/accenting.
                # Use original Telegram text directly; `text` may have been normalized/lowercased upstream.
                raw_text = ""
                try:
                    raw_text = (update.message.text or "").strip()
                except Exception:
                    raw_text = (text or "").strip()

                note_text = ""

                for prefix in note_prefixes:
                    prefix_norm = unicodedata.normalize("NFKD", prefix.lower())
                    prefix_norm = "".join(ch for ch in prefix_norm if not unicodedata.combining(ch))

                    if text_norm_greet.startswith(prefix_norm):
                        # Find the payload start by searching for ':' first; otherwise slice after raw prefix length.
                        if ":" in raw_text:
                            note_text = raw_text.split(":", 1)[1].strip()
                        else:
                            note_text = raw_text[len(prefix):].strip()
                        break

                if not note_text:
                    note_text = (m.group(1) or "").strip()

                if not note_text:
                    await update.message.reply_text("Dime qué nota quieres guardar.")
                    return

                note_id = add_note(chat_id, note_text)
                if note_id <= 0:
                    await update.message.reply_text("No pude guardar esa nota. Intenta de nuevo.")
                    return

                await update.message.reply_text(f"Listo. Guardé la nota #{note_id}:\n{note_text}")
                return

    except Exception as e:
        logger.exception(f"[NATURAL_NOTE_OVERRIDE] failed: {e}")
        await update.message.reply_text("Intenté guardar la nota, pero algo falló.")
        return

    # --------------------------------------------------
    # SESSION MEMORY: persist inbound user turn
    # --------------------------------------------------
    try:
        insert_message(
            int(chat_id),
            "user",
            text,
            telegram_message_id=int(tg_msg_id),
            model_used=None,
        )
        trim_messages_for_chat(int(chat_id), keep_last=12)
    except Exception as e:
        logger.exception(f"[SESSION_MEMORY_INBOUND] failed: {e}")
        
    # --------------------------------------------------
    # AUTO-FOCUS + PM LOOP
    # --------------------------------------------------
    try:
        auto_focus = _maybe_autoset_focus(int(chat_id), text)
    except Exception as e:
        logger.exception(f"[AUTO_FOCUS] failed: {e}")
        auto_focus = get_pm_focus(int(chat_id))

    try:
        pm_state = evaluate_pm_input(int(chat_id), text)
        pm_state["current_focus"] = auto_focus.get("focus_title", pm_state.get("current_focus", "General execution"))
        pm_state["focus_summary"] = auto_focus.get("focus_summary", pm_state.get("focus_summary", ""))
        pm_state["roadmap_note"] = auto_focus.get("roadmap_note", pm_state.get("roadmap_note", ""))
    except Exception as e:
        logger.exception(f"[PM_EVAL] failed: {e}")
        pm_state = {
            "current_focus": "General execution",
            "focus_summary": "",
            "roadmap_note": "",
            "decision": "DO_NOW",
            "reason": "PM evaluation fallback.",
            "next_action": "Continue current focus.",
        }
    # Hard redirect when drift is obvious
    if (
        pm_state["decision"] in ("DEFER", "DISCARD")
        and _is_pm_drift_candidate(text)
        and not _looks_like_doc_request(text)
        and not _is_karen_client_ops_intent(text)
    ):

        surfaced = _build_pm_redirect_reply(pm_state)
        try:
            log_pm_decision(
                int(chat_id),
                text,
                pm_state["decision"],
                pm_state["reason"],
                pm_state["next_action"],
                surfaced_to_user=True,
            )
        except Exception as e:
            logger.exception(f"[PM_LOG_SURFACED] failed: {e}")

        await _send_reply(update, context, surfaced)
        return

    try:
        log_pm_decision(
            int(chat_id),
            text,
            pm_state["decision"],
            pm_state["reason"],
            pm_state["next_action"],
            surfaced_to_user=False,
        )
    except Exception as e:
        logger.exception(f"[PM_LOG] failed: {e}")

    # --------------------------------------------------
    # PM FOCUS QUERY OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        text_norm_focus = unicodedata.normalize("NFKD", (text or "").lower())
        text_norm_focus = "".join(ch for ch in text_norm_focus if not unicodedata.combining(ch))

        focus_queries = (
            "what is the current focus",
            "current focus",
            "what are we working on",
            "what were we working on",
            "cual es el foco actual",
            "cuál es el foco actual",
            "en que estamos trabajando",
            "en qué estamos trabajando",
            "que estamos trabajando",
            "qué estamos trabajando",
            "en que andamos",
            "en qué andamos",
        )

        if any(q in text_norm_focus for q in focus_queries):
            focus = get_pm_focus(int(chat_id))
            reply = (
                f"Foco actual: {focus.get('focus_title', '')}\n"
                f"Resumen: {focus.get('focus_summary', '')}\n"
                f"Roadmap: {focus.get('roadmap_note', '')}"
            ).strip()
            await _send_reply(update, context, reply)
            return

    except Exception as e:
        logger.exception(f"[PM_FOCUS_OVERRIDE] failed: {e}")  

    # --------------------------------------------------
    # PM CONTINUATION OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        if _is_continuation_query(text):
            focus = get_pm_focus(int(chat_id))
            last_work = _get_last_user_work_message(int(chat_id))
            lang = resolve_user_language(int(chat_id))

            def L(es_text: str, en_text: str) -> str:
                return es_text if lang == "es" else en_text

            stale_lane_markers = (
                "val0 pm + session continuity",
                "implement automatic focus control and conversational continuity in val0",
                "defer watch/ui/device work until after mvp",
                "revisar contrato",
                "llamar a miguel",
                "audiencia del 15 de abril",
            )

            if last_work:
                low_last_work = unicodedata.normalize("NFKD", last_work.lower())
                low_last_work = "".join(ch for ch in low_last_work if not unicodedata.combining(ch))
                if any(m in low_last_work for m in stale_lane_markers):
                    last_work = ""

            text_norm_cont = unicodedata.normalize("NFKD", (text or "").lower())
            text_norm_cont = "".join(ch for ch in text_norm_cont if not unicodedata.combining(ch))

            real_priority_markers = (
                "continue with launch",
                "continue with the real priority",
                "no, continue with launch",
                "no, continue with the real priority",
                "not that, continue",
                "sigue con launch",
                "sigue con lo real",
                "sigue con la prioridad real",
                "no, sigue con launch",
                "no, sigue con lo real",
            )

            if any(m in text_norm_cont for m in real_priority_markers):
                approved = ""
                try:
                    approved = get_last_non_drift_user_input(int(chat_id), limit=20)
                except Exception:
                    approved = ""

                if approved:
                    reply = (
                        L("Volvemos a la prioridad real:\n", "Back to the real priority:\n")
                        + f"- {approved}\n\n"
                        + L("Foco actual: ", "Current focus: ") + f"{focus.get('focus_title', '')}\n"
                        + L("Resumen: ", "Summary: ") + f"{focus.get('focus_summary', '')}\n"
                        + L("Siguiente dirección: ", "Next direction: ") + f"{focus.get('roadmap_note', '')}"
                    )
                else:
                    reply = (
                        L("Volvemos a la prioridad real.\n\n", "Back to the real priority.\n\n")
                        + L("Foco actual: ", "Current focus: ") + f"{focus.get('focus_title', '')}\n"
                        + L("Resumen: ", "Summary: ") + f"{focus.get('focus_summary', '')}\n"
                        + "Roadmap: " + f"{focus.get('roadmap_note', '')}"
                    )

                await _send_reply(update, context, reply)
                return

            if (
                "turn that into 3 steps" in text_norm_cont
                or "turn it into 3 steps" in text_norm_cont
                or "conviertelo en 3 pasos" in text_norm_cont
                or "conviértelo en 3 pasos" in text_norm_cont
            ):
                if last_work:
                    reply = (
                        L(
                            f"Claro. Para avanzar en {focus.get('focus_title', 'el foco actual')}:\n\n",
                            f"Sure. To move forward in {focus.get('focus_title', 'the current focus')}:\n\n",
                        )
                        + L(
                            f"1. Definir con precisión el objetivo de este bloque: {last_work}\n",
                            f"1. Define precisely the goal of this block: {last_work}\n",
                        )
                        + L(
                            "2. Identificar el punto exacto de integración o bloqueo dentro del flujo actual.\n",
                            "2. Identify the exact integration point or blockage in the current flow.\n",
                        )
                        + L(
                            "3. Ejecutar el siguiente cambio concreto y verificarlo en Telegram.",
                            "3. Execute the next concrete change and verify it in Telegram.",
                        )
                    )
                else:
                    reply = (
                        L(
                            f"Claro. Para avanzar en {focus.get('focus_title', 'el foco actual')}:\n\n",
                            f"Sure. To move forward in {focus.get('focus_title', 'the current focus')}:\n\n",
                        )
                        + L("1. Reconfirmar el objetivo inmediato.\n", "1. Reconfirm the immediate goal.\n")
                        + L(
                            "2. Identificar el siguiente bloqueo o integración pendiente.\n",
                            "2. Identify the next blockage or pending integration.\n",
                        )
                        + L(
                            "3. Ejecutar y verificar el siguiente cambio concreto.",
                            "3. Execute and verify the next concrete change.",
                        )
                    )
                await _send_reply(update, context, reply)
                return

            if (
                "what was the last concrete thing" in text_norm_cont
                or "cual era la ultima cosa concreta" in text_norm_cont
                or "cuál era la última cosa concreta" in text_norm_cont
            ):
                if last_work:
                    reply = (
                        L("La última cosa concreta era esta:\n", "The last concrete thing was this:\n")
                        + f"- {last_work}\n\n"
                        + L("Eso cae bajo:\n", "That falls under:\n")
                        + L("Foco actual: ", "Current focus: ") + f"{focus.get('focus_title', '')}"
                    )
                else:
                    reply = (
                        L(
                            "No tengo una acción concreta reciente suficientemente clara en el hilo.\n\n",
                            "I do not have a recent concrete enough action in the thread.\n\n",
                        )
                        + L("Foco actual: ", "Current focus: ") + f"{focus.get('focus_title', '')}\n"
                        + L("Resumen: ", "Summary: ") + f"{focus.get('focus_summary', '')}"
                    )
                await _send_reply(update, context, reply)
                return

            # Generic continue / what were we doing / summarize that
            if last_work:
                reply = (
                    L("Seguimos con esto:\n", "We are continuing with this:\n")
                    + f"- {last_work}\n\n"
                    + L("Foco actual: ", "Current focus: ") + f"{focus.get('focus_title', '')}\n"
                    + L("Resumen: ", "Summary: ") + f"{focus.get('focus_summary', '')}\n"
                    + L("Siguiente dirección: ", "Next direction: ") + f"{focus.get('roadmap_note', '')}"
                )
            else:
                reply = (
                    L("Volvemos al foco actual.\n\n", "Back to the current focus.\n\n")
                    + L("Foco actual: ", "Current focus: ") + f"{focus.get('focus_title', '')}\n"
                    + L("Resumen: ", "Summary: ") + f"{focus.get('focus_summary', '')}\n"
                    + "Roadmap: " + f"{focus.get('roadmap_note', '')}"
                )

            await _send_reply(update, context, reply)
            return

    except Exception as e:
        logger.exception(f"[PM_CONTINUATION_OVERRIDE] failed: {e}")

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

        time_question_patterns = (
            r"^que hora es\??$",
            r"^qué hora es\??$",
            r"^hora actual\??$",
            r"^dime la hora\??$",
            r"^me dices la hora\??$",
        )

        is_time_question = any(re.search(p, text_norm_time.strip()) for p in time_question_patterns)

        if (not is_task_intent) and is_time_question:
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
            "documento",
        )

        email_triggers = (
            "envialo",
            "enviamelo",
            "mandamelo",
            "mandamelo por correo",
            "enviamelo por correo",
            "mandes por correo",
            "mandarlo por correo",
            "mandalo por correo",
            "enviar por correo",
            "enviarlo por correo",
            "por correo",
            "por email",
            "mandamelo al correo",
            "enviamelo al correo",
            "send it",
            "email it",
        )

        is_doc = any(t in text_norm for t in doc_triggers)
        wants_email = any(t in text_norm for t in email_triggers)

        logger.info(
            "[DOC_MODE_DEBUG] chat_id=%s is_doc=%s wants_email=%s text_norm=%r",
            chat_id,
            is_doc,
            wants_email,
            text_norm,
        )

        if is_doc:
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
                    "- DO NOT say that you cannot send email.\n"
                    "- DO NOT mention email capability limits inside the draft.\n"
                    "- Email confirmation is handled outside the model response.\n"
                ),
            )

            if reply:
                cleanup_patterns = (
                    r"\n*No puedo enviar(?:lo)? por correo[^.\n]*\.?",
                    r"\n*No puedo enviar correos[^.\n]*\.?",
                    r"\n*No envío correos[^.\n]*\.?",
                    r"\n*Si quieres, dime el correo al que deseas que lo envíe[^.\n]*\.?",
                    r"\n*Si quieres, dime el correo[^.\n]*\.?",
                    r"\n*Si quieres, indícame[^.\n]*correo[^.\n]*\.?",
                    r"\n*Si prefieres que te lo envíe por correo[^.\n]*\.?",
                    r"\n*Si quieres, dime a que correo lo envio[^.\n]*\.?",
                    r"\n*Si quieres, dime a qué correo lo envío[^.\n]*\.?",
                    r"\n*Si deseas, indicame a que correo enviarlo[^.\n]*\.?",
                    r"\n*Si deseas, indícame a qué correo enviarlo[^.\n]*\.?",
                    r"\n*Tambien puedo ajustar el contrato a tus necesidades especificas[^.\n]*\.?",
                    r"\n*También puedo ajustar el contrato a tus necesidades específicas[^.\n]*\.?",
                    r"\n*Si quieres, dime los datos que faltan[^.\n]*\.?",
                    r"\n*Si quieres, indicame los datos que faltan[^.\n]*\.?",
                    r"\n*Si quieres, indícame los datos que faltan[^.\n]*\.?",
                    r"\n*Puedo ayudarte a dejarlo listo para que lo guardes tú misma[^.\n]*\.?",
                    r"\n*Todo está aquí para que lo copies y uses[^.\n]*\.?",
                    r"\n*Puedes copiar y pegar este texto para enviarlo tu mismo[^.\n]*\.?",
                    r"\n*Puedes copiar y pegar este texto para enviarlo tú mismo[^.\n]*\.?",
                )

                for pat in cleanup_patterns:
                    reply = re.sub(pat, "", reply, flags=re.IGNORECASE)

                reply = re.sub(r"\n{3,}", "\n\n", reply).strip()

            if wants_email and reply:
                try:
                    to_email = get_fact(chat_id=chat_id, fact_key="user_email")
                except Exception:
                    to_email = None

                to_email = (to_email or "").strip()

                logger.info(
                    "[DOC_MODE_DEBUG] chat_id=%s resolved_to_email=%r",
                    chat_id,
                    to_email,
                )

                if to_email:
                    try:
                        logger.info(
                            "[DOC_MODE_DEBUG] chat_id=%s sending_contract_email_to=%r",
                            chat_id,
                            to_email,
                        )
                        send_email_resend(
                            to_email=to_email,
                            subject="Valeria – Borrador de contrato",
                            body=reply,
                        )

                        post_send_cleanup_patterns = (
                            r"\n*No puedo enviar(?:lo)? por correo[^.\n]*\.?",
                            r"\n*No puedo enviar correos[^.\n]*\.?",
                            r"\n*No envío correos[^.\n]*\.?",
                            r"\n*Si quieres[^.\n]*correo[^.\n]*\.?",
                            r"\n*Si deseas[^.\n]*correo[^.\n]*\.?",
                            r"\n*Puedes copiar y pegar[^.\n]*\.?",
                            r"\n*Todo está aquí para que lo copies y uses[^.\n]*\.?",
                        )

                        for pat in post_send_cleanup_patterns:
                            reply = re.sub(pat, "", reply, flags=re.IGNORECASE)

                        reply = re.sub(r"\n{3,}", "\n\n", reply).strip()
                        reply = reply + f"\n\n📧 Te lo envié a {to_email}."
                        try:
                            upsert_fact(chat_id=chat_id, fact_key="last_email_sent_to", fact_value=to_email)
                            upsert_fact(chat_id=chat_id, fact_key="last_email_subject", fact_value="Valeria – Borrador de contrato")
                            upsert_fact(chat_id=chat_id, fact_key="last_document_type", fact_value="contract")
                            upsert_fact(chat_id=chat_id, fact_key="last_email_sent_at", fact_value=datetime.now(timezone.utc).isoformat())
                            upsert_fact(chat_id=chat_id, fact_key="last_email_had_attachment", fact_value="no")
                            upsert_fact(chat_id=chat_id, fact_key="last_attachment_name", fact_value="")
                            upsert_fact(chat_id=chat_id, fact_key="last_email_channel", fact_value="email")
                        except Exception as e:
                            logger.exception(f"[DOC_MODE_EMAIL_FACTS] failed: {e}")
                    except Exception as e:
                        logger.exception(
                            "[DOC_MODE_DEBUG] chat_id=%s email_send_failed to=%r err=%s",
                            chat_id,
                            to_email,
                            e,
                        )
                        reply = reply + (
                            f"\n\n⚠️ No pude enviarlo por correo ahora mismo a {to_email}. "
                            "Aquí lo tienes en el chat."
                        )
                else:
                    logger.info(
                        "[DOC_MODE_DEBUG] chat_id=%s no_confirmed_email_in_chat",
                        chat_id,
                    )
                    reply = reply + (
                        "\n\n⚠️ No tengo un correo confirmado en este chat, así que por seguridad "
                        "no lo envié por email. Aquí lo tienes en el chat."
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
                logger.exception(f"[DOC_MODE_INSERT] failed: {e}")

            return

    except Exception as e:
        logger.exception(f"[DOC_MODE_EARLY] failed: {e}")

    # --------------------------------------------------
    # EMAIL STATUS OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        text_norm_email = unicodedata.normalize("NFKD", (text or "").lower())
        text_norm_email = "".join(ch for ch in text_norm_email if not unicodedata.combining(ch))
        text_norm_email = re.sub(r"[¿?¡!.,:;]+", "", text_norm_email).strip()

        ask_sent_markers = (
            "a que correo lo enviaste",
            "a que correo exactamente",
        )

        if any(m in text_norm_email for m in ask_sent_markers):
            try:
                last_email_sent_to = get_fact(chat_id=chat_id, fact_key="last_email_sent_to")
            except Exception:
                last_email_sent_to = None

            last_email_sent_to = (last_email_sent_to or "").strip()

            if last_email_sent_to:
                await update.message.reply_text(f"Te lo envié a {last_email_sent_to}.")
            else:
                await update.message.reply_text(
                    "No tengo registro de un envío de correo confirmado en este chat."
                )
            return

    except Exception as e:
        logger.exception(f"[EMAIL_STATUS_OVERRIDE] failed: {e}")    

    # --------------------------------------------------
    # LAST EMAIL SUMMARY OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        text_norm_email_summary = unicodedata.normalize("NFKD", (text or "").lower())
        text_norm_email_summary = "".join(ch for ch in text_norm_email_summary if not unicodedata.combining(ch))
        text_norm_email_summary = re.sub(r"[¿?¡!.,:;]+", "", text_norm_email_summary).strip()

        ask_last_email_markers = (
            "que fue lo ultimo que enviaste por correo",
            "que fue lo ultimo que mandaste por correo",
            "cual fue el ultimo correo que enviaste",
            "what was the last thing you emailed",
            "what was the last email you sent",
        )

        if any(m in text_norm_email_summary for m in ask_last_email_markers):
            try:
                last_to = (get_fact(chat_id=chat_id, fact_key="last_email_sent_to") or "").strip()
            except Exception:
                last_to = ""

            try:
                last_subject = (get_fact(chat_id=chat_id, fact_key="last_email_subject") or "").strip()
            except Exception:
                last_subject = ""

            try:
                last_doc_type = (get_fact(chat_id=chat_id, fact_key="last_document_type") or "").strip()
            except Exception:
                last_doc_type = ""

            if last_to or last_subject or last_doc_type:
                parts = []
                if last_doc_type:
                    parts.append(f"tipo: {last_doc_type}")
                if last_subject:
                    parts.append(f"asunto: {last_subject}")
                if last_to:
                    parts.append(f"destinatario: {last_to}")

                await update.message.reply_text("Lo último que envié por correo fue:\n- " + "\n- ".join(parts))
            else:
                await update.message.reply_text("No tengo registro de un último correo enviado en este chat.")
            return

    except Exception as e:
        logger.exception(f"[LAST_EMAIL_SUMMARY_OVERRIDE] failed: {e}")

    # --------------------------------------------------
    # LAST ATTACHMENT STATUS OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        text_norm_attach = unicodedata.normalize("NFKD", (text or "").lower())
        text_norm_attach = "".join(ch for ch in text_norm_attach if not unicodedata.combining(ch))
        text_norm_attach = re.sub(r"[¿?¡!.,:;]+", "", text_norm_attach).strip()

        ask_attachment_markers = (
            "tenia adjunto",
            "tenia attachment",
            "llevaba adjunto",
            "what was attached",
            "did it have an attachment",
            "did the last email have an attachment",
            "que fue lo ultimo que mandaste adjunto",
            "que adjunto llevaba",
        )

        if any(m in text_norm_attach for m in ask_attachment_markers):
            try:
                had_attachment = (get_fact(chat_id=chat_id, fact_key="last_email_had_attachment") or "").strip().lower()
            except Exception:
                had_attachment = ""

            try:
                attachment_name = (get_fact(chat_id=chat_id, fact_key="last_attachment_name") or "").strip()
            except Exception:
                attachment_name = ""

            if had_attachment == "yes":
                if attachment_name:
                    await update.message.reply_text(f"Sí. El último email llevaba este adjunto: {attachment_name}.")
                else:
                    await update.message.reply_text("Sí. El último email llevaba un adjunto, pero no tengo el nombre guardado.")
            elif had_attachment == "no":
                await update.message.reply_text("No. El último email no llevaba adjunto.")
            else:
                await update.message.reply_text("No tengo registro del estado de adjuntos para el último email en este chat.")
            return

    except Exception as e:
        logger.exception(f"[LAST_ATTACHMENT_STATUS_OVERRIDE] failed: {e}")

    # --------------------------------------------------
    # REDIRECT SENT MESSAGE OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        who = _extract_redirect_sent_message_target(text)

        if who:
            to_email = get_email_contact(who)
            if not to_email:
                await update.message.reply_text(f"No tengo correo configurado para {who}.")
                return

            try:
                subject = (get_fact(chat_id=chat_id, fact_key="last_email_subject") or "").strip()
            except Exception:
                subject = ""

            if not subject:
                subject = "Valeria – Documento generado"

            body = get_last_assistant_message(chat_id).strip()
            if not body:
                await update.message.reply_text("No encontré contenido reciente para reenviar.")
                return

            try:
                send_email_resend(
                    to_email=to_email,
                    subject=subject,
                    body=body,
                )

                try:
                    upsert_fact(chat_id=chat_id, fact_key="last_email_sent_to", fact_value=to_email)
                    upsert_fact(chat_id=chat_id, fact_key="last_email_sent_at", fact_value=datetime.now(timezone.utc).isoformat())
                    upsert_fact(chat_id=chat_id, fact_key="last_email_had_attachment", fact_value="no")
                    upsert_fact(chat_id=chat_id, fact_key="last_attachment_name", fact_value="")
                    upsert_fact(chat_id=chat_id, fact_key="last_email_channel", fact_value="email")
                except Exception as e:
                    logger.exception(f"[REDIRECT_SENT_MESSAGE_FACTS] failed: {e}")

                await update.message.reply_text(f"📧 Listo. Se lo mandé a {who.title()} en {to_email}.")
            except Exception as e:
                logger.exception(f"[REDIRECT_SENT_MESSAGE_OVERRIDE] failed: {e}")
                await update.message.reply_text(f"⚠️ No pude mandárselo a {who.title()} en {to_email}.")
            return

    except Exception as e:
        logger.exception(f"[REDIRECT_SENT_MESSAGE_OVERRIDE] failed: {e}")

    # --------------------------------------------------
    # SEND COPY OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    
    try:
        who = _extract_copy_target(text)

        if who:
            to_email = get_email_contact(who)
            if not to_email:
                await update.message.reply_text(f"No tengo correo configurado para {who}.")
                return

            body = get_last_assistant_message(chat_id)
            body = (body or "").strip()
            if not body:
                await update.message.reply_text("No encontré un documento reciente para reenviar.")
                return

            try:
                last_subject = (get_fact(chat_id=chat_id, fact_key="last_email_subject") or "").strip()
            except Exception:
                last_subject = ""

            if not last_subject:
                last_subject = "Valeria – Documento generado"

            try:
                send_email_resend(
                    to_email=to_email,
                    subject=last_subject,
                    body=body,
                )

                try:
                    upsert_fact(chat_id=chat_id, fact_key="last_email_sent_to", fact_value=to_email)
                    upsert_fact(chat_id=chat_id, fact_key="last_email_sent_at", fact_value=datetime.now(timezone.utc).isoformat())
                    upsert_fact(chat_id=chat_id, fact_key="last_email_had_attachment", fact_value="no")
                    upsert_fact(chat_id=chat_id, fact_key="last_attachment_name", fact_value="")
                    upsert_fact(chat_id=chat_id, fact_key="last_email_channel", fact_value="email")
                except Exception as e:
                    logger.exception(f"[SEND_COPY_FACTS] failed: {e}")

                await update.message.reply_text(f"📧 Listo. Le mandé una copia a {who.title()} en {to_email}.")
            except Exception as e:
                logger.exception(f"[SEND_COPY_OVERRIDE] failed: {e}")
                await update.message.reply_text(
                    f"⚠️ No pude enviarle la copia a {who.title()} en {to_email}."
                )
            return

    except Exception as e:
        logger.exception(f"[SEND_COPY_OVERRIDE] failed: {e}")

    # --------------------------------------------------
    # REDIRECT LAST EMAIL OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        who = _extract_redirect_target(text)

        if who:
            to_email = get_email_contact(who)
            if not to_email:
                await update.message.reply_text(f"No tengo correo configurado para {who}.")
                return

            body = get_last_assistant_message(chat_id)
            body = (body or "").strip()
            if not body:
                await update.message.reply_text("No encontré contenido reciente para redirigir.")
                return

            try:
                last_subject = (get_fact(chat_id=chat_id, fact_key="last_email_subject") or "").strip()
            except Exception:
                last_subject = ""

            if not last_subject:
                last_subject = "Valeria – Documento generado"

            try:
                send_email_resend(
                    to_email=to_email,
                    subject=last_subject,
                    body=body,
                )

                try:
                    upsert_fact(chat_id=chat_id, fact_key="last_email_sent_to", fact_value=to_email)
                    upsert_fact(chat_id=chat_id, fact_key="last_email_sent_at", fact_value=datetime.now(timezone.utc).isoformat())
                    upsert_fact(chat_id=chat_id, fact_key="last_email_had_attachment", fact_value="no")
                    upsert_fact(chat_id=chat_id, fact_key="last_attachment_name", fact_value="")
                    upsert_fact(chat_id=chat_id, fact_key="last_email_channel", fact_value="email")
                except Exception as e:
                    logger.exception(f"[REDIRECT_LAST_EMAIL_FACTS] failed: {e}")

                await update.message.reply_text(f"📧 Listo. Redirigí el último correo a {who.title()} en {to_email}.")
            except Exception as e:
                logger.exception(f"[REDIRECT_LAST_EMAIL_OVERRIDE] failed: {e}")
                await update.message.reply_text(f"⚠️ No pude redirigir el último correo a {who.title()} en {to_email}.")
            return

    except Exception as e:
        logger.exception(f"[REDIRECT_LAST_EMAIL_OVERRIDE] failed: {e}")

    # --------------------------------------------------
    # RESEND LAST EMAIL OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        text_norm_resend = unicodedata.normalize("NFKD", (text or "").lower())
        text_norm_resend = "".join(ch for ch in text_norm_resend if not unicodedata.combining(ch))
        text_norm_resend = re.sub(r"[¿?¡!.,:;]+", "", text_norm_resend).strip()

        resend_markers = (
            "reenvialo",
            "reenvialo por correo",
            "mandalo otra vez",
            "mandalo de nuevo",
            "envialo otra vez",
            "envialo de nuevo",
            "resend it",
            "send it again",
            "resend the last email",
        )

        if any(m in text_norm_resend for m in resend_markers):
            try:
                to_email = (get_fact(chat_id=chat_id, fact_key="last_email_sent_to") or "").strip()
            except Exception:
                to_email = ""

            try:
                subject = (get_fact(chat_id=chat_id, fact_key="last_email_subject") or "").strip()
            except Exception:
                subject = ""

            body = get_last_assistant_message(chat_id).strip()

            if not to_email:
                await update.message.reply_text("No tengo registro del último destinatario en este chat.")
                return

            if not subject:
                subject = "Valeria – Documento generado"

            if not body:
                await update.message.reply_text("No encontré contenido reciente para reenviar.")
                return

            try:
                send_email_resend(
                    to_email=to_email,
                    subject=subject,
                    body=body,
                )

                try:
                    upsert_fact(chat_id=chat_id, fact_key="last_email_sent_at", fact_value=datetime.now(timezone.utc).isoformat())
                except Exception as e:
                    logger.exception(f"[RESEND_LAST_EMAIL_FACTS] failed: {e}")

                await update.message.reply_text(f"📧 Listo. Reenvié el último correo a {to_email}.")
            except Exception as e:
                logger.exception(f"[RESEND_LAST_EMAIL_OVERRIDE] failed: {e}")
                await update.message.reply_text(f"⚠️ No pude reenviar el último correo a {to_email}.")
            return

    except Exception as e:
        logger.exception(f"[RESEND_LAST_EMAIL_OVERRIDE] failed: {e}")

    # --------------------------------------------------
    # SEND FREEFORM EMAIL OVERRIDE (DETERMINISTIC)
    # --------------------------------------------------
    try:
        who, body_text = _extract_send_email_payload(text)

        if who and body_text:
            to_email = get_email_contact(who)
            if not to_email:
                await update.message.reply_text(f"No tengo correo configurado para {who}.")
                return

            subject = f"Valeria – Mensaje para {who.title()}"

            try:
                send_email_resend(
                    to_email=to_email,
                    subject=subject,
                    body=body_text,
                )

                try:
                    upsert_fact(chat_id=chat_id, fact_key="last_email_sent_to", fact_value=to_email)
                    upsert_fact(chat_id=chat_id, fact_key="last_email_subject", fact_value=subject)
                    upsert_fact(chat_id=chat_id, fact_key="last_document_type", fact_value="freeform_email")
                    upsert_fact(chat_id=chat_id, fact_key="last_email_sent_at", fact_value=datetime.now(timezone.utc).isoformat())
                    upsert_fact(chat_id=chat_id, fact_key="last_email_had_attachment", fact_value="no")
                    upsert_fact(chat_id=chat_id, fact_key="last_attachment_name", fact_value="")
                    upsert_fact(chat_id=chat_id, fact_key="last_email_channel", fact_value="email")
                except Exception as e:
                    logger.exception(f"[FREEFORM_EMAIL_FACTS] failed: {e}")

                await update.message.reply_text(f"📧 Listo. Le mandé el email a {who.title()} en {to_email}.")
            except Exception as e:
                logger.exception(f"[FREEFORM_EMAIL_OVERRIDE] failed: {e}")
                await update.message.reply_text(f"⚠️ No pude enviarle el email a {who.title()} en {to_email}.")
            return

    except Exception as e:
        logger.exception(f"[FREEFORM_EMAIL_OVERRIDE] failed: {e}")

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
            "mandalo por correo",
            "enviarlo por correo",
            "mandamelo al correo",
            "enviamelo al correo",
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

            to_email = (to_email or "").strip()

            if not to_email:
                await update.message.reply_text(
                    "No tengo un correo confirmado en este chat. Por seguridad no envié nada."
                )
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

            try:
                send_email_resend(to_email=to_email, subject=subject, body=last_reply)
                await update.message.reply_text(f"📧 Listo. Lo envié a {to_email}.")
            except Exception as e:
                logger.exception(f"[EMAIL_SEND_CMD_SEND] failed: {e}")
                await update.message.reply_text(
                    f"⚠️ No pude enviarlo por correo a {to_email}. El contenido sigue disponible en el chat."
                )
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
            _maybe_log_intent_router_v2_actual("pending_action_reply", "handle_pending_reminder_confirmation", chat_id=chat_id, message_id=shadow_message_id, text=text)
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
            _maybe_log_intent_router_v2_actual("reminder_create", "handle_reminder_gate", chat_id=chat_id, message_id=shadow_message_id, text=text)
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
        from core.conflict_detector import (
            try_conflicts_tomorrow,
            try_reschedule_tomorrow,
        )

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

        # --------------------------------------------------
        # HARD CONTEXT GRAPH OVERRIDES (PLACE HERE)
        # --------------------------------------------------
        try:

            t = (text or "").strip().lower()
            t = unicodedata.normalize("NFKD", t)
            t = "".join(ch for ch in t if not unicodedata.combining(ch))

            if t == "donde estabamos" or t == "where were we":
                if await try_where_were_we(update, chat_id, text):
                    return

            if t == "run recovery protocol":
                if await try_recovery_protocol(update, chat_id, text):
                    return        

            if t.startswith("retoma "):
                if await try_resume_node(update, chat_id, text):
                    return

        except Exception as e:
            logger.exception(f"[HARD_CONTEXT_OVERRIDE] failed: {e}")



        HANDLERS = [
            try_debug_mode,
            try_help,
            try_undo_last_action,
            try_where_were_we,
            try_recovery_protocol,
            try_resume_node,
            try_node_followup,
            try_auto_propose_node,
            try_confirm_convert,
            try_convert_node_idea,

            # due / agenda natural FIRST
            try_due_today_natural,
            try_agenda_tomorrow_natural,
            try_due_tomorrow_natural,
            try_week_natural,
            # conflict checks
            try_reschedule_tomorrow,
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
        schedule_tomorrow_intent = parse_karen_task_schedule_for_tomorrow(text)

        # --------------------------------------------------
        # HARD AGENDA OVERRIDE (guaranteed deterministic)
        # --------------------------------------------------
        try:
            t = (text or "").strip().lower()
            t = unicodedata.normalize("NFKD", t)
            t = "".join(ch for ch in t if not unicodedata.combining(ch))
            t = re.sub(r"[¿?¡!.,:;]+", "", t).strip()

            if re.match(r"^que\s+tengo\s+manana$", t) or re.match(r"^que\s+audiencias\s+tengo\s+manana$", t):
                if await try_agenda_tomorrow_natural(update, chat_id, text):
                    return

            if re.match(r"^que\s+vence\s+manana$", t):
                from core.case_mvp import try_due_tomorrow
                if await try_due_tomorrow(update, chat_id, text):
                    return

        except Exception as e:
            logger.exception(f"[HARD_AGENDA_OVERRIDE] failed: {e}")

        for handler in HANDLERS:
            if schedule_tomorrow_intent and handler in (
                try_due_tomorrow_natural,
                try_due_tomorrow,
                try_due_range,
            ):
                continue

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
    # User-facing memory dashboard
    # --------------------------------------------------
    try:
        if _is_what_do_you_remember_query(text):
            reply = build_user_memory_dashboard(int(chat_id))
            sent = await _send_reply(update, context, reply)
            try:
                insert_message(chat_id, "assistant", reply, sent.message_id, "gpt-4.1-mini")
            except Exception:
                pass
            return
    except Exception as e:
        logger.exception(f"[USER_MEMORY_DASHBOARD] failed: {e}")
        await update.message.reply_text("No pude leer tu memoria ahora mismo.")
        return

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
        name_prefix = f"{preferred_name}, " if preferred_name else ""
        reply = f"Queda registrado, {name_prefix}tu color favorito ahora es {fav}. Lo tengo guardado."
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

        pm_system_block = _build_pm_system_block(pm_state)
        combined_system_rules = ((advisory_system_rules or "") + pm_system_block).strip()

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
            if _has_active_commitment(text) and not _is_continuation_query(text):

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

            - You are not a generic assistant. You are an operator companion.
            - Prioritize continuity over politeness.
            - Protect operator time.
            - Be sharp, grounded, and slightly witty.
            - Use dry humor when useful, but never become cartoonish.
            - If the user is drifting, say so clearly and redirect.
            - If the system is failing, be candid and calm, not corporate.
            - If something matters repeatedly, treat it as important.
            - Respond based on pattern, not just the last message.
            - Apply light pressure when something is pending.
            - Avoid offering vague generic help when a concrete next action is better.
            - Keep replies short, alive, and context-aware.
            - Sound like a smart, protective copiloto — not a helpdesk bot.

            GOOD:
            "Ojo. Eso es drift. Volvamos a lo que sí mueve esto."
            "Yeah, that path is cute, but it’s not the priority."
            "Seguimos con lo real. Siguiente paso: cerrar X."
            "El sistema hizo algo raro. No te voy a vender humo."

            BAD:
            "¿Quieres que te ayude con sugerencias?"
            "Aquí tienes algunas ideas generales."
            "Como asistente virtual, puedo..."

            FOUNDER-BETA VALERIA PERSONA:

            - You are Valeria inside Val0 founder beta.
            - You are conversational, practical, useful, and direct.
            - You are not a corporate assistant and not a generic chatbot.
            - If asked what you are, explain plainly that you are a Telegram-based assistant/operator in beta.
            - If asked what you can do, explain current capabilities without overpromising.
            - Identity, product, pricing, beta, and capability questions are NOT drift.
            - Normal conversation should feel human-coded, warm, sharp, and useful.
            - Do not claim perfect memory, full autonomy, or production-grade reliability.
            - Do not invent features.
            - Deterministic rails always win for reminders, notes, tasks, reports, calendar, and doc/email state.
            - If the user is just chatting, answer naturally and briefly, then offer one useful next step only if appropriate.

            TONE:
            - Intelligent
            - Slightly dangerous
            - Protective
            - Anti-corporate
            - Calm under pressure
            - Witty, but not needy
            - Never submissive
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

        pm_footer_block_triggers = (
            "what are we working on",
            "what is the current focus",
            "what was the last concrete thing",
            "turn that into 3 steps",
            "turn it into 3 steps",
            "continue",
            "okay continue",
            "ok continue",
            "keep going",
            "cual es el foco actual",
            "cuál es el foco actual",
            "que estabamos haciendo",
            "qué estábamos haciendo",
            "conviertelo en 3 pasos",
            "conviértelo en 3 pasos",
            "en que estamos trabajando",
            "en qué estamos trabajando",
        )

        low = (text or "").lower()
        pm_footer_blocked = any(t in low for t in pm_footer_block_triggers)

        if tasks and not _has_active_commitment(text) and not pm_footer_blocked:
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

            meta_reply_markers = (
                "que estabamos haciendo",
                "qué estábamos haciendo",
                "sigue",
                "seguimos",
                "convierte eso en 3 pasos",
                "conviertelo en 3 pasos",
                "conviértelo en 3 pasos",
                "what are we working on",
                "what were we doing",
                "continue with launch",
                "continue with the real priority",
                "no, continue with launch",
                "no, continue with the real priority",
            )

            should_nudge = False
            suppress_nudge = any(m in low for m in meta_reply_markers)

            explicit_task_nudge_markers = (
                "pendiente",
                "pendientes",
                "tarea",
                "tareas",
                "que debo hacer",
                "qué debo hacer",
                "que tengo pendiente",
                "qué tengo pendiente",
                "status",
                "estado",
            )

            wants_task_nudge = any(m in low for m in explicit_task_nudge_markers)

            if not suppress_nudge and wants_task_nudge:
                if len(tasks) >= 1:
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
        # AUTO EMAIL inline disabled for alpha safety.
        # Email sending is handled only in explicit document/email flows
        # and only when the current chat has a confirmed user_email.
        pass
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




async def try_anchored_reminder_before_appointment_natural(update, chat_id, text) -> bool:
    """
    Anchored Reminder v0.

    Example:
    - Val, recuérdame una hora antes de la cita con Nora
    - Val, recuérdame 1 hora antes de la cita de Nora preparar documentos
    """
    import re
    import unicodedata
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo

    if not update or not getattr(update, "message", None):
        return False

    client_id = resolve_client_id(chat_id)
    voc = client_vocative(client_id)

    raw = (text or "").strip()
    t = raw.lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"[¿?¡!.,;]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^\s*(?:oye\s+)?(?:val|valeria|vale|bal|pal|va\s+el)\s+", "", t).strip()

    if not (t.startswith("recuerdame") or t.startswith("recordarme") or t.startswith("recordatorio")):
        return False

    if not any(x in t for x in ("antes de la cita", "antes de mi cita", "antes de cita", "antes de la reunion", "antes de reunión", "antes de reunion")):
        return False

    # Offset: currently support 1/una hour, N hours, 30 minutes.
    offset_minutes = None
    if "una hora antes" in t or "1 hora antes" in t:
        offset_minutes = 60
    else:
        hm = re.search(r"\b(?P<n>\d{1,2})\s+horas?\s+antes\b", t)
        mm = re.search(r"\b(?P<n>\d{1,3})\s+minutos?\s+antes\b", t)
        if hm:
            offset_minutes = int(hm.group("n")) * 60
        elif mm:
            offset_minutes = int(mm.group("n"))

    if not offset_minutes:
        await update.message.reply_text(
            f"Puedo hacerlo{voc} ⏰📅\n\n"
            "Dime cuánto antes. Por ahora entiendo cosas como:\n"
            "• “Val, recuérdame una hora antes de la cita con Nora”\n"
            "• “Val, recuérdame 30 minutos antes de la cita con Nora”"
        )
        return True

    # Try to extract appointment keyword/person after "cita con/de ..."
    target = ""
    m = re.search(r"\bcita\s+(?:con|de)\s+(?P<target>[a-z0-9áéíóúñü\s]+)", raw, re.IGNORECASE)
    if m:
        target = m.group("target").strip()
        target = re.split(r"\b(preparar|llevar|revisar|recordar|para)\b", target, flags=re.IGNORECASE)[0].strip()

    # Fallback: common named anchor in Karen flow.
    if not target and "nora" in t:
        target = "Nora"

    if not target:
        await update.message.reply_text(
            "Sí puedo crear el recordatorio, pero necesito saber de cuál cita hablamos.\n\n"
            "Ejemplo: “Val, recuérdame una hora antes de la cita con Nora”."
        )
        return True

    # Reminder task text. If user says "preparar documentos", preserve that; otherwise default.
    action = ""
    am = re.search(r"\b(preparar|llevar|revisar|recordar)\b(?P<rest>.+)$", raw, re.IGNORECASE)
    if am:
        action = (am.group(0) or "").strip()
    if not action:
        action = f"preparar la cita con {target}"

    try:
        import memory_store
        conn = memory_store._get_conn()
        cur = conn.cursor()

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        like = f"%{target.strip()}%"

        row = cur.execute(
            """
            SELECT id, due_at_utc, text
            FROM reminders
            WHERE chat_id = ?
              AND entity_type = 'appointment'
              AND status = 'pending'
              AND due_at_utc >= ?
              AND lower(text) LIKE lower(?)
            ORDER BY due_at_utc ASC, id ASC
            LIMIT 1
            """,
            (int(chat_id), now_utc, like),
        ).fetchone()
        conn.close()
    except Exception:
        row = None

    if not row:
        await update.message.reply_text(
            f"No encontré una cita pendiente con {target} para anclar el recordatorio.\n\n"
            "Primero guarda la cita, por ejemplo:\n"
            "“Val, tengo cita con Nora el 29 a las 3pm”."
        )
        return True

    rd = dict(row) if hasattr(row, "keys") else {"id": row[0], "due_at_utc": row[1], "text": row[2]}
    appt_id = int(rd["id"])
    appt_text = (rd.get("text") or "").strip()
    appt_due = rd.get("due_at_utc")

    try:
        appt_dt_utc = datetime.strptime(appt_due, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        reminder_dt_utc = appt_dt_utc - timedelta(minutes=int(offset_minutes))
    except Exception:
        await update.message.reply_text("Encontré la cita, pero no pude calcular la hora del recordatorio. Eso sí está feo; no lo voy a fingir. 😌")
        return True

    if reminder_dt_utc <= datetime.now(timezone.utc):
        await update.message.reply_text(
            f"Ese recordatorio caería en el pasado{voc}. Dame otra ventana o revisamos la cita."
        )
        return True

    due_utc = reminder_dt_utc.strftime("%Y-%m-%d %H:%M:%S")
    reminder_text = action.rstrip(".") + "."

    try:
        from memory_store import insert_reminder
        rid = insert_reminder(
            int(chat_id),
            due_utc,
            reminder_text,
            status="pending",
            entity_type="reminder",
            parent_ref=f"APPOINTMENT:{appt_id}",
        )
    except Exception as e:
        await update.message.reply_text(f"No pude guardar el recordatorio anclado ahora mismo. Error: {e}")
        return True

    tz = ZoneInfo("America/Panama")
    rem_local = reminder_dt_utc.astimezone(tz)
    appt_local = appt_dt_utc.astimezone(tz)
    weekday = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][rem_local.weekday()]
    month_name = ["","enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"][rem_local.month]

    msg = (
        f"⏰ Listo{voc}. Guardé el recordatorio antes de la cita.\n\n"
        f"• Recordatorio: {weekday} {rem_local.day} de {month_name}, {rem_local.strftime('%I:%M %p').lstrip('0')}\n"
        f"• Acción: {reminder_text}\n"
        f"• Cita anclada: {appt_local.strftime('%I:%M %p').lstrip('0')} — {appt_text}\n"
        f"• Reminder ID: #{rid}\n"
        f"• Appointment ID: #{appt_id}"
    )
    await update.message.reply_text(msg)
    return True




def _audit_client_gcal_event(action: str, chat_id: int, client_id: str, payload: dict) -> None:
    """
    Append-only local audit log for client Google Calendar writes/deletes.
    No tokens. No secrets. Event IDs and titles are okay for ops traceability.
    """
    import json
    from datetime import datetime
    from pathlib import Path

    try:
        path = Path("/opt/val0/logs/karen_gcal_events_audit.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)

        row = {
            "ts_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "client_id": client_id,
            "chat_id": int(chat_id),
            "action": action,
            **(payload or {}),
        }

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception as e:
        logger.exception(f"[KAREN_GCAL_AUDIT] failed: {e}")



# --------------------------------------------------
# Karen Google Calendar appointment confirmation v0
# Natural flow:
# user: "Val, tengo cita con Mabel mañana a las 5pm"
# Val: draft + confirmation
# user: "sí" / "dale" / "confirmo"
# Val: creates Google Calendar event
# --------------------------------------------------
GCAL_CREATE_ACTION_TYPE = "gcal_create_event"
GCAL_DELETE_ACTION_TYPE = "gcal_delete_event"
GCAL_PENDING_TTL = timedelta(days=365)

GCAL_CREATE_CONFIRM_WORDS = (
    "si",
    "sí",
    "si confirma",
    "sí confirma",
    "confirma",
    "ok",
    "okay",
    "dale",
    "correcto",
    "confirmo",
    "confirmar",
    "confirmalo",
    "confírmalo",
    "crealo",
    "créalo",
    "crear",
    "hazlo",
    "yes",
)

GCAL_CREATE_CANCEL_WORDS = (
    "no",
    "cancelar",
    "cancela",
    "cancelalo",
    "cancélalo",
    "dejalo",
    "déjalo",
    "mejor no",
    "olvidalo",
    "olvídalo",
    "stop",
)

GCAL_DELETE_CONFIRM_WORDS = (
    "si",
    "sí",
    "si confirma",
    "sí confirma",
    "confirma",
    "ok",
    "okay",
    "dale",
    "correcto",
    "confirmo",
    "confirmar",
    "borralo",
    "bórralo",
    "eliminalo",
    "elimínalo",
    "hazlo",
    "yes",
)

GCAL_DELETE_CANCEL_WORDS = (
    "no",
    "cancelar",
    "cancela",
    "dejalo",
    "déjalo",
    "mejor no",
    "olvidalo",
    "olvídalo",
    "stop",
)


def _gcal_pending_expires_at():
    import datetime as dt

    return dt.datetime.now(timezone.utc) + GCAL_PENDING_TTL


def _gcal_action_id(action_type: str, chat_id: int) -> str:
    return f"{action_type}:{int(chat_id)}:{time.time_ns()}"


def _clear_existing_gcal_pending(chat_id: int, client_id: str, action_type: str) -> None:
    existing = get_pending_action(chat_id, action_type=action_type, client_id=client_id)
    if existing:
        clear_pending_action(existing.action_id)


def _get_gcal_pending_action_any_state(chat_id: int, client_id: str, action_type: str = GCAL_CREATE_ACTION_TYPE) -> PendingAction | None:
    from core import pending_actions as pending_store

    matches = []
    for action in pending_store._PENDING_ACTIONS.values():
        if int(action.chat_id) != int(chat_id):
            continue
        if action.client_id != client_id:
            continue
        if action.action_type != action_type:
            continue
        matches.append(action)
    if not matches:
        return None
    matches.sort(key=lambda action: action.created_at, reverse=True)
    return matches[0]


def _norm_gcal_confirm_text(text: str) -> str:
    import re
    import unicodedata

    t = (text or "").strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"[¿?¡!.,:;]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^(val|valeria|vale|bal|pal|va\s+el)\s+", "", t).strip()
    return t


def _matches_gcal_pending_reply(text: str, action: PendingAction) -> bool:
    norm = _norm_gcal_confirm_text(text)
    if not norm:
        return False
    confirm_words = {_norm_gcal_confirm_text(word) for word in action.confirm_words}
    cancel_words = {_norm_gcal_confirm_text(word) for word in action.cancel_words}
    return norm in confirm_words or norm in cancel_words


def _gcal_user_event_title(title: str) -> str:
    display = (title or "").strip()
    display = re.sub(r"(?i)^cita:\s*", "", display).strip()
    return display or (title or "").strip() or "evento"


def _cleanup_karen_gcal_event_title(title: str) -> str:
    value = str(title or "").strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"^[,.;:\-\s]+", "", value).strip()
    value = re.sub(r"(?i)^(?:el|la|lo|este|esto)\s*[,.;:\-]+\s*", "", value).strip()
    value = re.sub(r"(?i)^(?:el|la|lo|este|esto)\s+(?=(?:llamar|cita|reunion|reunión|reunirme|hablar|ir|recoger|llevar)\b)", "", value).strip()
    value = re.sub(r"(?i)\b(?:de\s+la|de\s+el|del|a\s+la|a\s+las)\s*$", "", value).strip(" ,.;:-")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _looks_like_karen_gcal_event_create_request(text: str) -> bool:
    norm = _norm_gcal_confirm_text(text)
    if not norm:
        return False
    if norm.startswith(("que ", "qué ", "dime ", "cual ", "cuál ", "muestrame ", "muéstrame ")):
        return False
    if "recuerdame" in norm or "recordatorio" in norm:
        return False

    explicit_markers = (
        "agenda cita",
        "agendar cita",
        "agenda para",
        "agendar para",
        "programa cita",
        "programar cita",
        "crea evento",
        "crear evento",
        "google calendar",
        "pon en mi calendario",
        "pon en el calendario",
        "agrega al calendario",
        "agregar al calendario",
        "agregala al calendario",
        "agrégala al calendario",
        "tengo cita",
        "tengo una cita",
        "cita con",
        "reunion con",
        "reunión con",
        "tengo reunion",
        "tengo reunión",
    )
    if any(marker in norm for marker in explicit_markers):
        return True

    has_date = bool(re.search(
        r"\b(hoy|manana|mañana|pasado manana|pasado mañana|lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo|(?:el\s+)?[0-3]?\d(?:\s+de\s+\w+)?)\b",
        norm,
    ))
    has_time = bool(re.search(r"\b(?:a\s+las|a\s+la)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", norm))
    return norm.startswith("agenda ") and has_date and has_time


async def maybe_handle_karen_gcal_create_confirmation_first(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    client_id = resolve_client_id(chat_id)
    if not client_id:
        return False

    action = _get_gcal_pending_action_any_state(chat_id, client_id)
    if not action or not _matches_gcal_pending_reply(text, action):
        return False

    logger.info("[GCAL_CONFIRM_ROUTE] matched pending gcal_create_event reply")
    return await maybe_handle_pending_gcal_appointment_confirmation(update, chat_id, text)


async def maybe_handle_pending_gcal_appointment_confirmation(update, chat_id, text) -> bool:
    from datetime import datetime
    from core.client_gcal_write import create_client_event

    if not update or not getattr(update, "message", None):
        return False

    client_id = resolve_client_id(chat_id)
    if not client_id:
        return False
    action = _get_gcal_pending_action_any_state(chat_id, client_id)
    if not action:
        return False
    if not _matches_gcal_pending_reply(text, action):
        return False

    pending = action.payload
    decision = classify_confirmation_reply(text, action)

    if decision == ConfirmationDecision.CANCEL:
        clear_pending_action(action.action_id)
        await update.message.reply_text(
            "Listo, no creé el evento en Google Calendar."
        )
        return True

    if decision == ConfirmationDecision.EXPIRED:
        clear_pending_action(action.action_id)
        await update.message.reply_text(
            "Esa confirmación ya venció. Vuelve a pedirme que agende la cita."
        )
        return True

    if decision != ConfirmationDecision.CONFIRM:
        return False

    start_dt = datetime.fromisoformat(pending["start_iso"])
    display_title = _gcal_user_event_title(pending.get("title") or "")

    # Duplicate guard: avoid creating the same event twice for same title/time.
    try:
        from datetime import timedelta
        from core.client_gcal_read import get_client_events_between

        window_start = start_dt - timedelta(minutes=2)
        window_end = start_dt + timedelta(minutes=2)
        existing = get_client_events_between(
            client_id,
            window_start,
            window_end,
            tz="America/Panama",
            limit=10,
        )

        pending_title_norm = (pending["title"] or "").strip().lower()
        duplicate = None
        for ev in existing.events:
            ev_title = (ev.get("summary") or "").strip().lower()
            ev_start = (ev.get("start") or "").strip()
            if ev_title == pending_title_norm and ev_start.startswith(start_dt.strftime("%Y-%m-%dT%H:%M")):
                duplicate = ev
                break

        if duplicate:
            clear_pending_action(action.action_id)
            await update.message.reply_text(
                "📅 Esa cita ya existe en Google Calendar. No la dupliqué.\n\n"
                f"• {pending['pretty_date']}\n"
                f"• {pending['pretty_time']}\n"
                f"• {display_title}\n\n"
                "Tu agenda queda limpia y sin eventos repetidos. 😌"
            )
            return True
    except Exception as e:
        logger.exception(f"[KAREN_GCAL_CREATE_DUPLICATE_CHECK] failed: {e}")

    result = create_client_event(
        client_id,
        pending["title"],
        start_dt,
        duration_minutes=int(pending.get("duration_minutes", 60)),
        description=pending.get("description") or "Evento creado por Val0 después de confirmación explícita.",
        dry_run=False,
    )

    if result.status == "created":
        _audit_client_gcal_event("create", chat_id, client_id, {
            "status": result.status,
            "event_id": result.event_id,
            "title": result.title,
            "start": result.start,
            "end": result.end,
            "source": "natural_appointment_confirmation",
        })
        clear_pending_action(action.action_id)
        await update.message.reply_text(
            "Listo. Agregué al Google Calendar: "
            f"{display_title} — {pending.get('pretty_short') or pending['pretty_date']} {pending['pretty_time']}.\n\n"
            "Google Calendar se encargará de sus notificaciones según tu configuración.\n"
            "Solo creé este evento. No creé recordatorios de Val, ni borré ni edité nada más."
        )
        return True

    clear_pending_action(action.action_id)
    await update.message.reply_text(
        "No pude crear el evento en Google Calendar por un problema de autorización/conexión. "
        "No lo marqué como creado.\n\n"
        f"Estado: {result.status}\n"
        f"Razón: {result.reason}"
    )
    return True


async def maybe_handle_pending_gcal_delete_confirmation(update, chat_id, text) -> bool:
    from core.client_gcal_write import delete_client_event

    if not update or not getattr(update, "message", None):
        return False

    client_id = resolve_client_id(chat_id)
    if not client_id:
        return False
    action = _get_gcal_pending_action_any_state(chat_id, client_id, action_type=GCAL_DELETE_ACTION_TYPE)
    if not action:
        return False
    if not _matches_gcal_pending_reply(text, action):
        return False
    pending = action.payload
    decision = classify_confirmation_reply(text, action)

    if decision == ConfirmationDecision.CANCEL:
        clear_pending_action(action.action_id)
        await update.message.reply_text(
            "Listo, no eliminé el evento de Google Calendar."
        )
        return True

    if decision == ConfirmationDecision.EXPIRED:
        clear_pending_action(action.action_id)
        await update.message.reply_text(
            "Esa confirmación ya venció. Vuelve a pedirme que elimine el evento."
        )
        return True

    if decision != ConfirmationDecision.CONFIRM:
        return False

    try:
        result = delete_client_event(
            client_id,
            pending["event_id"],
            dry_run=False,
        )
    except Exception as e:
        logger.exception(f"[KAREN_GCAL_DELETE_CONFIRM] failed: {e}")
        clear_pending_action(action.action_id)
        await update.message.reply_text(
            "No pude eliminar ese evento. Es posible que ya no exista o que Google Calendar no lo haya encontrado. "
            "No toqué recordatorios ni tareas de Val."
        )
        return True

    if result.status == "deleted":
        _audit_client_gcal_event("delete", chat_id, client_id, {
            "status": result.status,
            "event_id": result.event_id,
            "deleted_event_id": result.deleted_event_id,
            "title": pending.get("summary") or "",
            "start": pending.get("start") or "",
            "end": pending.get("end") or "",
            "source": "natural_delete_confirmation",
        })
        clear_pending_action(action.action_id)
        _mark_karen_gcal_event_context_stale(chat_id)
        await update.message.reply_text(
            "Listo. Eliminé de Google Calendar: "
            f"{pending.get('summary') or 'evento'} — {pending.get('display_start') or pending.get('start') or ''}.\n\n"
            "Solo eliminé ese evento específico. No toqué recordatorios ni tareas de Val."
        )
        return True

    clear_pending_action(action.action_id)
    await update.message.reply_text(
        "No pude eliminar ese evento. Es posible que ya no exista o que Google Calendar no lo haya encontrado. "
        "No toqué recordatorios ni tareas de Val."
    )
    return True


def _parse_karen_gcal_event_number_delete(text: str) -> int | None:
    norm = _norm_gcal_confirm_text(text)
    delete_verbs = r"(?:elimina|eliminar|borra|borrar|cancela|cancelar)"
    number_words = r"(?:\d{1,2}|uno|una|primer|primero|dos|segundo|tres|tercero|cuatro|cinco|seis|siete|ocho|nueve|diez)"
    patterns = (
        rf"\b{delete_verbs}\s+(?:el\s+)?evento(?:\s+de\s+google\s+calendar|\s+google\s+calendar)?\s+(?P<num>{number_words})\b",
        rf"\b{delete_verbs}\s+evento\s+(?P<num>{number_words})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, norm)
        if match:
            return _karen_number_word_to_int(match.group("num"))
    return None


async def maybe_handle_karen_gcal_event_number_delete(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    number = _parse_karen_gcal_event_number_delete(text)
    if number is None:
        return False

    client_id = resolve_client_id(chat_id)
    if not client_id:
        return False

    if _is_karen_gcal_event_context_stale(chat_id):
        await update.message.reply_text(
            "La lista de eventos cambió después de borrar uno. "
            "Pídeme “qué tengo mañana” o “qué tengo para el lunes” para verla actualizada antes de borrar otro evento por número."
        )
        return True

    events = _karen_gcal_visible_events(chat_id)
    if not events:
        await update.message.reply_text(
            "No tengo una lista reciente de eventos de Google Calendar para usar ese número. "
            "Pide “Val, qué tengo mañana?” y dime el número del evento."
        )
        return True

    if int(number) < 1 or int(number) > len(events):
        await update.message.reply_text(
            "No veo ese número de evento en la última agenda. Pide “Val, qué tengo mañana?” para verla actualizada."
        )
        return True

    selected = events[int(number) - 1]
    if not selected.get("event_id"):
        await update.message.reply_text(
            "No pude identificar ese evento de Google Calendar con seguridad. No cambié nada."
        )
        return True

    delete_payload = {
        "event_id": selected.get("event_id") or "",
        "summary": selected.get("summary") or "evento",
        "start": selected.get("start") or "",
        "end": selected.get("end") or "",
        "display_start": selected.get("display_start") or selected.get("start") or "",
        "number": int(number),
    }
    _clear_existing_gcal_pending(chat_id, client_id, GCAL_DELETE_ACTION_TYPE)
    create_pending_action(
        PendingAction(
            action_id=_gcal_action_id(GCAL_DELETE_ACTION_TYPE, chat_id),
            chat_id=int(chat_id),
            client_id=client_id,
            action_type=GCAL_DELETE_ACTION_TYPE,
            display_summary=f"{delete_payload['display_start']} · {delete_payload['summary']}",
            confirm_words=GCAL_DELETE_CONFIRM_WORDS,
            cancel_words=GCAL_DELETE_CANCEL_WORDS,
            expires_at=_gcal_pending_expires_at(),
            payload=delete_payload,
            audit_metadata={"source": "numbered_agenda_event_delete"},
        )
    )
    await update.message.reply_text(
        "Voy a eliminar este evento de Google Calendar:\n"
        f"{delete_payload['summary']} — {delete_payload['display_start']}.\n\n"
        "¿Confirmas?"
    )
    return True


async def try_gcal_delete_natural(update, chat_id, text) -> bool:
    import re
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from core.client_gcal_write import find_client_events_by_title

    if not update or not getattr(update, "message", None):
        return False

    client_id = resolve_client_id(chat_id)
    if not client_id:
        return False
    vocative = client_vocative(client_id)
    raw = (text or "").strip()
    norm = _norm_gcal_confirm_text(raw)

    delete_prefixes = (
        "borra evento",
        "borrar evento",
        "borra la cita",
        "borrar la cita",
        "borra cita",
        "borrar cita",
        "elimina evento",
        "eliminar evento",
        "elimina la cita",
        "eliminar la cita",
        "elimina cita",
        "eliminar cita",
        "borra",
        "elimina",
    )

    if not any(norm.startswith(p) for p in delete_prefixes):
        return False

    query = norm
    for prefix in sorted(delete_prefixes, key=len, reverse=True):
        if query.startswith(prefix):
            query = query[len(prefix):].strip()
            break

    query = re.sub(r"^(de|del|la|el)\s+", "", query).strip()

    if not query:
        await update.message.reply_text(
            "Puedo borrar un evento, pero dime cuál. Ejemplo:\n"
            "“Val, borra cita con Mabel”."
        )
        return True

    tz = ZoneInfo("America/Panama")
    matches = find_client_events_by_title(
        client_id,
        query,
        datetime.now(tz),
        days_ahead=30,
        limit=10,
    )

    if not matches:
        await update.message.reply_text(
            f"No encontré un evento futuro con ese nombre en Google Calendar{vocative}. 😬\n\n"
            f"Búsqueda: {query}\n\n"
            "No borré nada."
        )
        return True

    if len(matches) > 1:
        lines = [
            "Encontré más de un evento parecido. Para evitar errores, no voy a borrar ninguno todavía. 😌",
            "",
        ]
        for i, m in enumerate(matches[:5], 1):
            lines.append(f"{i}. {m.get('start')} · {m.get('summary')}")
        lines.append("")
        lines.append("Por ahora dime el nombre más exacto o lo hacemos manual.")
        await update.message.reply_text("\n".join(lines))
        return True

    m = matches[0]
    delete_payload = {
        "event_id": m.get("id") or "",
        "summary": m.get("summary") or "",
        "start": m.get("start") or "",
        "end": m.get("end") or "",
    }
    _clear_existing_gcal_pending(chat_id, client_id, GCAL_DELETE_ACTION_TYPE)
    create_pending_action(
        PendingAction(
            action_id=_gcal_action_id(GCAL_DELETE_ACTION_TYPE, chat_id),
            chat_id=int(chat_id),
            client_id=client_id,
            action_type=GCAL_DELETE_ACTION_TYPE,
            display_summary=f"{delete_payload['start']} · {delete_payload['summary']}",
            confirm_words=GCAL_DELETE_CONFIRM_WORDS,
            cancel_words=GCAL_DELETE_CANCEL_WORDS,
            expires_at=_gcal_pending_expires_at(),
            payload=delete_payload,
            audit_metadata={"source": "natural_delete_confirmation"},
        )
    )

    await update.message.reply_text(
        "🗑️ Encontré este evento en Google Calendar:\n\n"
        f"• {m.get('start')}\n"
        f"• {m.get('summary')}\n\n"
        "¿Confirmas que lo borre?\n"
        "Respóndeme: “sí”, “dale” o “cancelar”."
    )
    return True


async def try_appointment_save_natural(update, chat_id, text) -> bool:
    """
    Natural Appointment Save v0.

    Examples:
    - Val, tengo cita con Nora el 28 a las 3pm
    - Val, cita con la abogada el 28 de mayo a la 1
    - Val, tengo reunión con Nora el 28 a las 15:00
    """
    import re
    import unicodedata
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    if not update or not getattr(update, "message", None):
        return False

    client_id = resolve_client_id(chat_id)
    if not client_id:
        return False
    vocative = client_vocative(client_id)
    raw = (text or "").strip()
    t = raw.lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"[¿?¡!.,;]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^\s*(?:oye\s+)?(?:val|valeria|vale|bal|pal|va\s+el)\s+", "", t).strip()

    save_markers = (
        "tengo cita",
        "tengo una cita",
        "cita con",
        "registra cita",
        "registrar cita",
        "guarda cita",
        "guardar cita",
        "agenda cita",
        "agendar cita",
        "agenda para",
        "agendar para",
        "programa cita",
        "programar cita",
        "reunion con",
        "reunión con",
        "tengo reunion",
        "tengo reunión",
        "crea evento",
        "crear evento",
        "google calendar",
        "pon en mi calendario",
        "pon en el calendario",
        "agrega al calendario",
        "agregar al calendario",
        "agregala al calendario",
        "agrégala al calendario",
    )
    if not any(m in t for m in save_markers) and not _looks_like_karen_gcal_event_create_request(text):
        return False

    # Avoid hijacking lookup questions.
    if t.startswith(("que ", "qué ", "dime ", "cual ", "cuál ")):
        return False

    months = {
        "enero": 1, "ene": 1,
        "febrero": 2, "feb": 2,
        "marzo": 3, "mar": 3,
        "abril": 4, "abr": 4,
        "mayo": 5, "may": 5,
        "junio": 6, "jun": 6,
        "julio": 7, "jul": 7,
        "agosto": 8, "ago": 8,
        "septiembre": 9, "setiembre": 9, "sep": 9, "sept": 9,
        "octubre": 10, "oct": 10,
        "noviembre": 11, "nov": 11,
        "diciembre": 12, "dic": 12,
    }

    tz = ZoneInfo("America/Panama")
    now = datetime.now(tz)

    relative_date_label = None
    relative_date_dt = None

    if "pasado mañana" in t or "pasado manana" in t:
        relative_date_dt = now + timedelta(days=2)
        relative_date_label = "pasado mañana"
    elif "mañana" in t or "manana" in t:
        relative_date_dt = now + timedelta(days=1)
        relative_date_label = "mañana"
    elif "hoy" in t:
        relative_date_dt = now
        relative_date_label = "hoy"

    weekday_names = {
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
    weekday_date_dt = None
    if relative_date_dt is None:
        for weekday_name, weekday_idx in weekday_names.items():
            if re.search(rf"\b(?:el\s+)?{weekday_name}\b", t):
                days_ahead = (weekday_idx - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                weekday_date_dt = now + timedelta(days=days_ahead)
                relative_date_label = weekday_name
                break

    day = None
    month = None
    year = now.year

    # Date: "28 de mayo" / "28 mayo" / "el 28"
    m = re.search(r"\b(?:el\s+)?(?P<day>[0-3]?\d)\s*(?:de\s+)?(?P<month>enero|ene|febrero|feb|marzo|mar|abril|abr|mayo|may|junio|jun|julio|jul|agosto|ago|septiembre|setiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dic)\b", t)
    explicit_month = bool(m)
    if m:
        day = int(m.group("day"))
        month = months.get(m.group("month"))
    else:
        m = re.search(r"\b(?:el|para el|dia)\s+(?P<day>[0-3]?\d)\b", t)
        if m:
            day = int(m.group("day"))
            month = now.month

    if relative_date_dt is not None:
        day = relative_date_dt.day
        month = relative_date_dt.month
        year = relative_date_dt.year
    elif weekday_date_dt is not None:
        day = weekday_date_dt.day
        month = weekday_date_dt.month
        year = weekday_date_dt.year

    if not day or not month:
        await update.message.reply_text(
            f"Sí puedo crear el evento en Google Calendar{vocative} 📅\n\n"
            "Pero necesito la fecha. ¿Para qué fecha lo agendo?"
        )
        return True

    # Time: "a las 3pm", "a la 1", "a las 15:30"
    tm = re.search(r"\b(?:a\s+las|a\s+la)\s+(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>am|pm)?\b", t)
    if not tm:
        if relative_date_label:
            await update.message.reply_text(
                f"Sí puedo crear el evento en Google Calendar{vocative} 📅\n\n"
                f"Tengo la fecha: {relative_date_label}.\n"
                "¿A qué hora lo agendo?"
            )
        else:
            await update.message.reply_text(
                f"Tengo la fecha, pero me falta la hora{vocative} ⏰\n\n"
                "¿A qué hora lo agendo?"
            )
        return True

    hour = int(tm.group("hour"))
    minute = int(tm.group("minute") or "0")
    ampm = tm.group("ampm")

    if ampm == "pm" and hour < 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    elif ampm is None and 1 <= hour <= 7:
        # Practical default for appointments like "a las 3" = afternoon.
        hour += 12

    try:
        due_local = datetime(year, month, day, hour, minute, 0, tzinfo=tz)
    except ValueError:
        await update.message.reply_text("Esa fecha/hora no me cuadra. Dame día, mes y hora para no hacer brujería barata. 😌")
        return True

    if due_local < now and not explicit_month:
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        try:
            due_local = datetime(next_year, next_month, day, hour, minute, 0, tzinfo=tz)
        except ValueError:
            pass

    due_utc = due_local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Extract a compact title for display.
    # Keep useful context after the time, e.g. "tema libro Finca 10082".
    title = raw
    title = re.sub(r"^\s*(val|valeria|vale|bal|pal|va\s+el)[,:]?\s*", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(crea|crear)\s+(?:un\s+)?evento\s+(?:en\s+)?(?:google\s+calendar|mi\s+calendario|el\s+calendario|calendario)\s*:?\s*", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(pon)\s+en\s+(?:mi\s+|el\s+)?calendario\s*:?\s*", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(agrega|agregar)\s+(?:esto\s+)?(?:al|a\s+mi|en\s+mi)\s+calendario\s*:?\s*", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(agenda|agendar|programa|programar)\s+", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(para\s+(?:el\s+)?)", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(registra|registrar|guarda|guardar|agenda|agendar|programa|programar)\s+cita\s*", "cita ", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(tengo\s+una\s+|tengo\s+)", "", title, flags=re.IGNORECASE).strip()

    # Remove explicit/relative date words but do not destroy the subject/context.
    title = re.sub(r"\b(el|para el)\s+\d{1,2}(\s+de\s+\w+)?\b", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"\b(hoy|mañana|manana|pasado mañana|pasado manana)\b", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b", "", title, flags=re.IGNORECASE).strip()

    # Remove only the time expression, preserving text after it.
    title = re.sub(r"\ba\s+la?s?\s+\d{1,2}(:\d{2})?\s*(am|pm)?\b", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"\b(agregala|agrégala|agregalo|agrégalo|agrega|agregar|ponlo)\s+(?:al|a\s+mi|en\s+mi)\s+calendario\b", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"\b(?:en\s+)?google\s+calendar\b", "", title, flags=re.IGNORECASE).strip()

    title = re.sub(r"\s*,\s*", ", ", title).strip(" ,.;:-")
    title = re.sub(r"\s+", " ", title).strip()
    title = _cleanup_karen_gcal_event_title(title)

    # Clean common speech-to-text leftovers before final title normalization.
    title = re.sub(r"^(para\s+el\s+)+", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(para\s+la\s+)+", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(para\s+)", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(tengo\s+cita\s+con\s+)", "cita con ", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(tengo\s+reunion\s+con\s+|tengo\s+reunión\s+con\s+)", "cita con ", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(cita\s+para\s+el\s+)", "cita ", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"^(cita\s+para\s+la\s+)", "cita ", title, flags=re.IGNORECASE).strip()

    # Normalize leading appointment phrasing.
    title = re.sub(r"^cita\s+para\s+", "Cita para ", title, flags=re.IGNORECASE)
    title = re.sub(r"^cita\s+con\s+", "Cita con ", title, flags=re.IGNORECASE)
    title = re.sub(r"^cita\s+", "Cita ", title, flags=re.IGNORECASE)
    if title and not title.lower().startswith("cita"):
        title = "Cita: " + title

    if not title or title.lower() in {"cita", "evento", "reunion", "reunión"}:
        await update.message.reply_text("¿Qué título le pongo al evento?")
        return True

    reminder_text = f"{title}."

    weekday = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][due_local.weekday()]
    month_name = ["","enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"][due_local.month]
    pretty_date = f"{weekday} {due_local.day} de {month_name}"
    pretty_short = f"{weekday} {due_local.day:02d}/{due_local.month:02d}"
    pretty_time = due_local.strftime("%I:%M %p").lstrip("0")

    # Google Calendar write is now available for Karen, but must stay behind confirmation.
    appointment_payload = {
        "title": title,
        "start_iso": due_local.isoformat(),
        "duration_minutes": 60,
        "description": "Evento creado por Val0 desde flujo natural de cita con confirmación explícita.",
        "pretty_date": pretty_date,
        "pretty_short": pretty_short,
        "pretty_time": pretty_time,
        "source_phrase_category": "natural_gcal_event_create",
    }
    _clear_existing_gcal_pending(chat_id, client_id, GCAL_CREATE_ACTION_TYPE)
    create_pending_action(
        PendingAction(
            action_id=_gcal_action_id(GCAL_CREATE_ACTION_TYPE, chat_id),
            chat_id=int(chat_id),
            client_id=client_id,
            action_type=GCAL_CREATE_ACTION_TYPE,
            display_summary=f"{pretty_date} · {pretty_time} · {title}",
            confirm_words=GCAL_CREATE_CONFIRM_WORDS,
            cancel_words=GCAL_CREATE_CANCEL_WORDS,
            expires_at=_gcal_pending_expires_at(),
            payload=appointment_payload,
            audit_metadata={"source": "natural_appointment_confirmation", "source_phrase_category": "natural_gcal_event_create"},
        )
    )

    msg = (
        f"📅 Puedo crear esta cita en tu Google Calendar{vocative}.\n\n"
        "Revísala antes de confirmarla:\n\n"
        f"• {pretty_date}\n"
        f"• {pretty_time}\n"
        f"• {title}\n"
        "• Duración: 1 hora\n\n"
        "¿Confirmas que la cree en Google Calendar?\n"
        "Respóndeme: “sí”, “dale” o “cancelar”.\n\n"
        "Google Calendar se encargará de sus notificaciones según tu configuración."
    )
    await update.message.reply_text(msg)
    return True




async def try_agenda_summary_natural(update, chat_id, text) -> bool:
    """
    Richer Agenda List v0.

    Examples:
    - Val, qué tengo en agenda?
    - Val, muéstrame mi agenda
    - Val, próximas citas
    """
    import re
    import unicodedata
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    if not update or not getattr(update, "message", None):
        return False

    client_id = resolve_client_id(chat_id)

    raw = (text or "").strip()
    t = raw.lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"[¿?¡!.,;]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^\s*(?:oye\s+)?(?:val|valeria)\s+", "", t).strip()

    markers = (
        "que tengo en agenda",
        "mi agenda",
        "muestrame mi agenda",
        "mostrar mi agenda",
        "proximas citas",
        "proximos recordatorios",
        "agenda interna",
        "que citas tengo",
    )

    if not any(m in t for m in markers):
        return False

    tz = ZoneInfo("America/Panama")
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    try:
        import memory_store
        conn = memory_store._get_conn()
        cur = conn.cursor()
        rows = cur.execute(
            """
            SELECT id, due_at_utc, text, status, entity_type, parent_ref
            FROM reminders
            WHERE chat_id = ?
              AND status = 'pending'
              AND due_at_utc >= ?
            ORDER BY due_at_utc ASC, id ASC
            LIMIT 20
            """,
            (int(chat_id), now_utc),
        ).fetchall()
        conn.close()
    except Exception:
        rows = []

    appointments = []
    reminders = []

    for r in rows:
        rd = dict(r) if hasattr(r, "keys") else {
            "id": r[0], "due_at_utc": r[1], "text": r[2], "status": r[3],
            "entity_type": r[4], "parent_ref": r[5],
        }
        if rd.get("entity_type") == "appointment":
            appointments.append(rd)
        else:
            reminders.append(rd)

    def fmt_item(rd):
        due = rd.get("due_at_utc") or ""
        txt = (rd.get("text") or "").replace("\n", " ").strip()
        rid = rd.get("id")
        try:
            dt_utc = datetime.strptime(due, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            dt = dt_utc.astimezone(tz)
            weekday = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][dt.weekday()]
            month_name = ["","enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"][dt.month]
            label = f"{weekday} {dt.day} de {month_name}, {dt.strftime('%I:%M %p').lstrip('0')}"
        except Exception:
            label = "sin fecha clara"
        return f"• {label} — {txt}  #{rid}"

    lines = ["📅 Agenda interna de Val", ""]

    if appointments:
        lines.append("Próximas citas:")
        for rd in appointments[:8]:
            lines.append(fmt_item(rd))
        lines.append("")

    if reminders:
        lines.append("Recordatorios:")
        for rd in reminders[:8]:
            lines.append(fmt_item(rd))
        lines.append("")

    if not appointments and not reminders:
        lines.append("No veo citas ni recordatorios pendientes en la agenda interna.")
        lines.append("Si quieres, guarda una así: “Val, tengo cita con Nora el 29 a las 3pm”.")
        lines.append("")
    else:
        lines.append("Puedes preguntarme por una fecha específica, por ejemplo:")
        lines.append("“Val, qué cita tengo para el 29?”")
        lines.append("")

    try:
        from core.client_calendar_config import get_client_calendar_config
        cfg = get_client_calendar_config(client_id)
        if cfg.connection_status != "connected":
            lines.append("Google Calendar todavía no está conectado para Karen; esto es solo agenda interna de Val.")
    except Exception:
        pass

    await update.message.reply_text("\n".join(lines).strip())
    return True



async def try_agenda_date_lookup_natural(update, chat_id, text) -> bool:
    """
    Agenda Bridge v0: specific date lookup for Karen-style phrases.

    Examples:
    - Que cita tengo para el 28
    - Qué tengo el 28
    - Qué tengo para el 28 de mayo
    - Tengo algo el 28?
    """
    import re
    import unicodedata
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    if not update or not getattr(update, "message", None):
        return False

    client_id = resolve_client_id(chat_id)
    voc = client_vocative(client_id)

    raw = (text or "").strip()
    t = raw.lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"[¿?¡!.,:;]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^\s*(?:oye\s+)?(?:val|valeria)\s+", "", t).strip()

    intent_markers = (
        "que cita tengo",
        "que citas tengo",
        "que tengo",
        "tengo algo",
        "hay algo",
        "mi agenda",
        "agenda",
        "cita",
        "citas",
    )
    if not any(m in t for m in intent_markers):
        return False

    months = {
        "enero": 1, "ene": 1,
        "febrero": 2, "feb": 2,
        "marzo": 3, "mar": 3,
        "abril": 4, "abr": 4,
        "mayo": 5, "may": 5,
        "junio": 6, "jun": 6,
        "julio": 7, "jul": 7,
        "agosto": 8, "ago": 8,
        "septiembre": 9, "setiembre": 9, "sep": 9, "sept": 9,
        "octubre": 10, "oct": 10,
        "noviembre": 11, "nov": 11,
        "diciembre": 12, "dic": 12,
    }

    tz = ZoneInfo("America/Panama")
    now = datetime.now(tz)

    day = None
    month = None
    year = now.year

    # "28 de mayo" / "28 mayo"
    m = re.search(r"\b(?:el\s+)?(?P<day>[0-3]?\d)\s*(?:de\s+)?(?P<month>enero|ene|febrero|feb|marzo|mar|abril|abr|mayo|may|junio|jun|julio|jul|agosto|ago|septiembre|setiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dic)\b", t)
    if m:
        day = int(m.group("day"))
        month = months.get(m.group("month"))
    else:
        # "para el 28" / "el 28" / "dia 28"
        m = re.search(r"\b(?:para\s+el|para|el|dia)\s+(?P<day>[0-3]?\d)\b", t)
        if not m:
            # cautious fallback only if agenda/cita intent exists
            m = re.search(r"\b(?P<day>[0-3]?\d)\b", t)
        if m:
            day = int(m.group("day"))
            month = now.month

    if not day or not month:
        return False

    try:
        target_start = datetime(year, month, day, 0, 0, 0, tzinfo=tz)
    except ValueError:
        await update.message.reply_text(f"Esa fecha no me cuadra{voc}. Dame día y mes para no inventar calendario. 😌")
        return True

    # If user only gave day number and that day already passed this month, assume next month.
    if target_start.date() < now.date() and not re.search(r"(enero|ene|febrero|feb|marzo|mar|abril|abr|mayo|may|junio|jun|julio|jul|agosto|ago|septiembre|setiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dic)", t):
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        try:
            target_start = datetime(next_year, next_month, day, 0, 0, 0, tzinfo=tz)
        except ValueError:
            pass

    target_end = target_start.replace(hour=23, minute=59, second=59)

    start_utc = target_start.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_utc = target_end.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    reminders = []
    case_hits = []

    try:
        import memory_store
        conn = memory_store._get_conn()
        cur = conn.cursor()

        reminders = cur.execute(
            """
            SELECT id, text, due_at_utc, status, entity_type, parent_ref
            FROM reminders
            WHERE chat_id = ?
              AND due_at_utc >= ?
              AND due_at_utc <= ?
              AND status IN ('pending', 'sending', 'sent')
            ORDER BY due_at_utc ASC, id ASC
            LIMIT 20
            """,
            (int(chat_id), start_utc, end_utc),
        ).fetchall()

        # Secondary context only: search appointment/cita-ish case notes.
        date_tokens = [
            str(day),
            f"{day:02d}",
            target_start.strftime("%Y-%m-%d"),
        ]
        rows = cur.execute(
            """
            SELECT id, note_text, source, created_at, parent_ref
            FROM case_notes
            WHERE chat_id = ?
              AND (
                lower(note_text) LIKE '%cita%'
                OR lower(note_text) LIKE '%agenda%'
                OR lower(note_text) LIKE '%abogada%'
                OR lower(note_text) LIKE '%nora%'
              )
            ORDER BY id DESC
            LIMIT 15
            """,
            (int(chat_id),),
        ).fetchall()

        for r in rows:
            note = (r["note_text"] if hasattr(r, "keys") else r[1]) or ""
            note_low = note.lower()
            if any(tok in note_low for tok in date_tokens):
                case_hits.append(r)

        conn.close()
    except Exception:
        reminders = []
        case_hits = []

    weekday = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][target_start.weekday()]
    month_name = ["","enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"][target_start.month]
    pretty = f"{weekday} {target_start.day} de {month_name}"

    lines = [f"🗓️ Agenda para {pretty}"]

    found = False

    if reminders:
        found = True
        lines.append("")
        lines.append("Recordatorios de Val:")
        for r in reminders:
            rd = dict(r) if hasattr(r, "keys") else {
                "id": r[0], "text": r[1], "due_at_utc": r[2], "status": r[3],
                "entity_type": r[4], "parent_ref": r[5],
            }
            txt = _display_karen_reminder_title((rd.get("text") or "").replace("\n", " ").strip())
            due = (rd.get("due_at_utc") or "").strip()
            time_label = "sin hora"
            try:
                dt_utc = datetime.strptime(due, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                time_label = dt_utc.astimezone(tz).strftime("%I:%M %p").lstrip("0")
            except Exception:
                pass
            lines.append(f"• {time_label} — {txt}")

    if case_hits:
        found = True
        lines.append("")
        lines.append("Notas del caso que podrían estar relacionadas:")
        for r in case_hits[:5]:
            rd = dict(r) if hasattr(r, "keys") else {
                "id": r[0], "note_text": r[1], "source": r[2], "created_at": r[3], "parent_ref": r[4],
            }
            note = (rd.get("note_text") or "").replace("\n", " ").strip()
            if len(note) > 180:
                note = note[:180] + "…"
            lines.append(f"• {note}")

    try:
        from core.client_calendar_config import get_client_calendar_config
        cfg = get_client_calendar_config(client_id)
        if cfg.connection_status != "connected":
            lines.append("")
            lines.append("Google Calendar todavía no está conectado para Karen, así que revisé solo memoria/recordatorios internos.")
    except Exception:
        pass

    if not found:
        lines.append("")
        lines.append("No veo citas ni recordatorios guardados para esa fecha.")
        lines.append("Si esa cita existe, dime fecha y hora y la guardo sin inventarme la novela. 😌")

    await update.message.reply_text("\n".join(lines))
    return True



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

    if parse_karen_task_schedule_for_tomorrow(text):
        logger.info("[DUE_TOMORROW_GATE] skipped because Karen task scheduling intent detected")
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
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"[¿?¡!.,:;]+", "", t).strip()

    patterns = [
        r"^que tengo manana$",
        r"^que audiencias tengo manana$",
    ]

    for p in patterns:
        if re.match(p, t):
            tz = ZoneInfo("America/Panama")
            tomorrow = (datetime.now(tz) + timedelta(days=1)).date().isoformat()

            out = _generate_morning_brief_det(int(chat_id), tomorrow)

            tomorrow_dt = datetime.now(tz) + timedelta(days=1)
            weekday = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][tomorrow_dt.weekday()]
            month = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"][tomorrow_dt.month]
            pretty = f"{weekday} {tomorrow_dt.day} {month}"

            # Normalize reused daily-brief header when this path is explicitly "mañana"
            try:
                out = (out or "").strip()

                # Drop an old "Hoy (...)" header if present.
                out = re.sub(
                    r"^\s*📋\s*Hoy\s*\([^)]+\):\s*",
                    "",
                    out,
                    flags=re.IGNORECASE,
                ).lstrip()

                # Drop an existing "Mañana (...)" header if present.
                out = re.sub(
                    r"^\s*📅\s*Mañana\s*\([^)]+\)\s*",
                    "",
                    out,
                    flags=re.IGNORECASE,
                ).lstrip()

                if out:
                    out = f"📅 Mañana ({pretty})\n\n{out}"
                else:
                    out = f"📅 Mañana ({pretty})\n\nNo veo nada agendado para mañana."
            except Exception:
                pass

            # Pull Google Calendar events for tomorrow and append them.
            gcal_lines = []
            try:
                from core.gcal_client import get_events_between
                from datetime import timezone

                start_local = datetime(tomorrow_dt.year, tomorrow_dt.month, tomorrow_dt.day, 0, 0, 0, tzinfo=tz)
                end_local = datetime(tomorrow_dt.year, tomorrow_dt.month, tomorrow_dt.day, 23, 59, 59, tzinfo=tz)

                events = get_events_between(
                    start_local.astimezone(timezone.utc),
                    end_local.astimezone(timezone.utc),
                    limit=50,
                )

                for ev in events or []:
                    title = (ev.get("summary") or "(sin título)").strip()
                    start_raw = (ev.get("start") or "").strip()

                    time_label = "sin hora"
                    try:
                        ev_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                        if ev_dt.tzinfo is None:
                            ev_dt = ev_dt.replace(tzinfo=timezone.utc)
                        time_label = ev_dt.astimezone(tz).strftime("%I:%M %p")
                    except Exception:
                        if len(start_raw) == 10:
                            time_label = "Todo el día"

                    gcal_lines.append(f"• {time_label} — {title}")

            except Exception:
                gcal_lines = []

            if not out:
                out = f"📅 Mañana ({pretty})\n\nNo veo nada agendado para mañana."

            # If the deterministic brief returned the old empty-state text, normalize it.
            if "— No tengo nada agendado —" in out:
                out = f"📅 Mañana ({pretty})\n\nNo veo nada agendado para mañana."

            if gcal_lines:
                if out.strip():
                    out = out.rstrip() + "\n\nGoogle Calendar:\n" + "\n".join(gcal_lines)
                else:
                    out = f"📅 Mañana ({pretty})\n\nGoogle Calendar:\n" + "\n".join(gcal_lines)

            await update.message.reply_text(out)
            return True

    return False

async def try_week_natural(update, chat_id, text) -> bool:
    """
    Natural-language gate for week agenda.
    """
    import re

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
    if looks_like_technical_paste(t):
        return await _send_reply(update, context, TECHNICAL_PASTE_REPLY)

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
    


def _is_question_or_status_query(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False

    if "?" in t or "¿" in t:
        return True

    markers = (
        "que tengo",
        "qué tengo",
        "que debo hacer",
        "qué debo hacer",
        "que hago",
        "qué hago",
        "que hay",
        "qué hay",
        "mis pendientes",
        "mis tareas",
        "pendiente",
        "pendientes",
    )
    return any(m in t for m in markers)


def _is_reminder_creation_request(text: str) -> bool:
    t = (text or "").strip().lower()
    return (
        t.startswith("recuerdame")
        or t.startswith("recuérdame")
        or t.startswith("recordarme")
        or t.startswith("remind me")
        or "recordatorio" in t
    )


def _is_commitment_capture_allowed(text: str) -> bool:
    if _is_question_or_status_query(text):
        return False
    if _is_reminder_creation_request(text):
        return False
    return True

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
        "ya hice",
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


def _is_what_do_you_remember_query(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False

    t_norm = unicodedata.normalize("NFKD", t)
    t_norm = "".join(ch for ch in t_norm if not unicodedata.combining(ch))

    markers = (
        "que recuerdas de mi",
        "que sabes de mi",
        "que tienes guardado de mi",
        "que sabes sobre mi",
        "what do you remember about me",
        "what do you know about me",
    )

    return any(m in t_norm for m in markers)


def build_user_memory_dashboard(chat_id: int) -> str:
    from memory_store import get_all_facts, fetch_open_commitments

    try:
        facts = get_all_facts(chat_id=chat_id) or {}
    except Exception:
        facts = {}

    try:
        open_tasks = fetch_open_commitments(int(chat_id), limit=10) or []
    except Exception:
        open_tasks = []

    lines = ["🧠 Esto recuerdo de ti:", ""]

    preferred_name = (facts.get("preferred_name") or "").strip()
    favorite_color = (facts.get("favorite_color") or "").strip()
    main_goal = (facts.get("main_goal") or "").strip()
    preferred_language = (facts.get("preferred_language") or "").strip()

    remembered_anything = False

    if preferred_name:
        lines.append(f"- Te llamas {preferred_name}.")
        remembered_anything = True

    if favorite_color:
        lines.append(f"- Tu color favorito es {favorite_color}.")
        remembered_anything = True

    if main_goal:
        lines.append(f"- Tu objetivo principal es: {main_goal}.")
        remembered_anything = True

    if preferred_language:
        lang_label = "español" if preferred_language == "es" else preferred_language
        lines.append(f"- Prefieres hablar en {lang_label}.")
        remembered_anything = True

    if not remembered_anything:
        lines.append("- Todavía no tengo datos personales claros guardados para ti.")

    lines.append("")
    lines.append("📌 Tareas abiertas:")

    if open_tasks:
        for row in open_tasks:
            r = dict(row) if hasattr(row, "keys") else row
            raw = str(r.get("raw_input") or "").strip()
            due = str(r.get("due_date") or "").strip()
            if due:
                lines.append(f"- {raw} ({due})")
            else:
                lines.append(f"- {raw}")
    else:
        lines.append("- No tienes tareas abiertas ahora mismo.")

    lines.append("")
    lines.append("Siguiente paso: puedo guardar una preferencia, nota, tarea o recordatorio.")

    return "\n".join(lines)




async def reply_text_chunked_safe(update, text: str, chunk_size: int = 3800):
    """Send long Telegram text safely in chunks from any handler scope."""
    text = str(text or "").strip()
    if not text:
        return

    chunks = []
    remaining = text

    while len(remaining) > chunk_size:
        split_at = remaining.rfind("\n\n", 0, chunk_size)
        if split_at < 1000:
            split_at = remaining.rfind("\n", 0, chunk_size)
        if split_at < 1000:
            split_at = chunk_size

        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    if remaining:
        chunks.append(remaining)

    total = len(chunks)
    for i, chunk in enumerate(chunks, 1):
        if total > 1:
            chunk = f"[{i}/{total}]\n{chunk}"
        await update.message.reply_text(chunk)


def render_karen_abogada_doc_prep_response() -> str:
    return (
        "⚖️📁 Claro, Insanity. Si tienes que llevarle documentos a la abogada, vamos a prepararte sin convertir esto en una avalancha de papeles con trauma generacional. 😌\n\n"
        "Para llegar lista con Nora, haz esto:\n\n"
        "1. Separa lo que ya está registrado\n"
        "- Pide: “Val, ¿qué documentos tengo registrados?”\n"
        "- Así vemos qué ya existe en Val y qué está solo en físico/foto.\n\n"
        "2. Revisa qué falta validar\n"
        "- Pide: “Val, ¿qué falta revisar antes de hablar con la abogada?”\n"
        "- Ahí te doy la lista corta de pendientes: OCR, fotos, originales, copias, Registro Público y dudas clave.\n\n"
        "3. Lleva el paquete ordenado\n"
        "- Pide: “Val, prepárame el paquete para Nora.”\n"
        "- Eso te saca el resumen completo con datos, eventos, documentos, preguntas y checklist.\n\n"
        "4. Antes de salir\n"
        "- Confirma fecha y hora de la cita.\n"
        "- Confirma qué papeles físicos tienes en mano.\n"
        "- Si quieres recordatorio, dime la hora exacta de la cita y te ayudo a dejarlo anotado.\n\n"
        "Mi recomendación: primero revisemos documentos registrados, luego faltantes, y después saco el paquete para Nora. Una cosa a la vez, porque el caos familiar no necesita esteroides. 😏"
    )


def render_karen_missing_review_checklist() -> str:
    return (
        "📋🔎 Insanity, antes de hablar con Nora falta revisar esto, sin convertir la mesa en zona de desastre legal. 😌\n\n"
        "1. Documentos con texto extraído vs. documentos solo guardados\n"
        "- Ya hay PDFs con texto extraído/indexado.\n"
        "- Las fotos y algunos archivos guardados todavía pueden necesitar OCR o revisión manual.\n\n"
        "2. Fotos / scans pendientes\n"
        "- Confirmar qué fotos son legibles.\n"
        "- Separar lo que necesita escaneo, OCR o transcripción manual.\n\n"
        "3. Originales, copias y custodia\n"
        "- Marcar quién tiene originales.\n"
        "- Marcar quién tiene copias/fotos.\n"
        "- Identificar qué papeles físicos faltan por revisar.\n\n"
        "4. Datos registrales clave\n"
        "- Confirmar Finca 10082.\n"
        "- Confirmar Tomo/Rollo 316.\n"
        "- Confirmar Folio 308.\n"
        "- Confirmar Escritura Pública No. 920 y fecha del 16 de agosto de 2002.\n\n"
        "5. Tema Registro Público / Juncá\n"
        "- Llevar clara la inconsistencia detectada con Registro Público.\n"
        "- Preguntar qué efecto tiene la cancelación del caso de Juncá en 2024.\n\n"
        "6. Preguntas para Nora\n"
        "- Qué documento falta para que ella pueda opinar con seguridad.\n"
        "- Qué se debe pedir en Registro Público.\n"
        "- Qué puede adelantar la familia esta semana.\n"
        "- Costos, riesgos, responsables y siguiente paso concreto.\n\n"
        "Siguiente paso sugerido: si quieres, dime “Val, prepárame el paquete para Nora” y te saco el paquete completo para llevarlo ordenado. 📦⚖️"
    )


def _karen_timeline_query_year(text: str) -> str:
    norm = _norm_text(text or "")
    m = re.search(r"\bque paso en (19\d{2}|20\d{2})\b", norm)
    return m.group(1) if m else ""


def _normalize_karen_timeline_query(text: str) -> str:
    norm = _norm_text(text or "")
    norm = re.sub(r"[¿?¡!.,:;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    return re.sub(r"^(val|valeria|vale)\s+", "", norm).strip()


def _looks_like_karen_timeline_query(text: str) -> bool:
    norm = _normalize_karen_timeline_query(text)

    broad_document_markers = (
        "que dice este documento",
        "que dice el documento",
        "que documentos tengo",
        "que archivos tengo",
        "donde sale",
        "donde aparece",
    )
    if any(marker in norm for marker in broad_document_markers):
        return False

    document_summary_markers = (
        "vfms",
        "documento",
        "documentos",
        "ficha legal",
        "datos registrales",
        "registro publico",
    )
    if any(marker in norm for marker in document_summary_markers) and "caso" not in norm:
        return False

    if "cronologia" in norm:
        return True
    if "linea de tiempo" in norm:
        return True
    if "resumen cronologico" in norm:
        return True
    if _karen_timeline_query_year(norm):
        return True
    return False


def _karen_timeline_clip(text: str, limit: int = 260) -> str:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(clean) <= limit:
        return clean
    return clean[: max(0, limit - 1)].rstrip() + "…"


def _karen_timeline_description(summary: dict) -> str:
    source_type = str(summary.get("source_type") or "").strip()
    description = str(summary.get("description") or "").strip()
    title = str(summary.get("title") or "").strip()

    if source_type == "telegram_attachment_vfms":
        # Attachment case notes contain local paths and VFMS metadata; keep the user-facing line clean.
        return _karen_timeline_clip(title or "Documento registrado para el caso.")

    description = description.replace("Evento reciente del caso:", "").strip()
    kept_lines = []
    for line in description.splitlines():
        clean = line.strip()
        if not clean:
            continue
        low = clean.lower()
        if low.startswith("- ruta local:"):
            continue
        if low.startswith("- vfms ingest_id:"):
            continue
        kept_lines.append(clean)

    if kept_lines:
        return _karen_timeline_clip(" ".join(kept_lines))
    return _karen_timeline_clip(title or "Evento registrado.")


def _render_karen_case_timeline(events, *, case_id: str, year: str = "", limit: int = 12) -> str:
    selected = timeline_events_for_year(events, year) if year else list(events)
    if not selected:
        target = f" en {year}" if year else ""
        return (
            f"No tengo eventos de cronología disponibles{target} para CASE:{case_id} todavía.\n\n"
            "Puedes subir documentos, registrar eventos del caso o agregar notas con fechas para armarla.\n\n"
            "Esto organiza información registrada; no sustituye revisión de abogada."
        )

    title = f"Cronología del caso — CASE:{case_id}"
    if year:
        title = f"Cronología del caso en {year} — CASE:{case_id}"

    lines = [title, ""]
    for event in selected[:limit]:
        summary = safe_timeline_event_summary(event)
        precision = str(summary.get("date_precision") or "")
        date_text = str(summary.get("event_date") or "").strip()
        if not date_text or precision == "unknown":
            date_label = "fecha no determinada"
        elif precision == "created_at_only":
            date_label = f"{date_text} (fecha de registro)"
        else:
            date_label = date_text

        lines.append(f"- {date_label}: {_karen_timeline_description(summary)}")
        source = str(summary.get("source_type") or "nota").strip()
        source_id = str(summary.get("source_id") or "").strip()
        confidence = float(summary.get("confidence") or 0.0)
        if confidence >= 0.75:
            confidence_label = "alta"
        elif confidence >= 0.55:
            confidence_label = "media"
        else:
            confidence_label = "baja"

        provenance = f"  Fuente: {source}"
        if source_id:
            provenance += f" #{source_id}"
        if summary.get("ingest_id"):
            provenance += f" · VFMS {summary['ingest_id']}"
        provenance += f" · confianza {confidence_label}"
        lines.append(provenance)

    if len(selected) > limit:
        lines.append(f"- Hay {len(selected) - limit} evento(s) más no mostrado(s) en esta vista corta.")

    lines.append("")
    lines.append("Esto organiza información registrada; no sustituye revisión de abogada.")
    return "\n".join(lines)


async def maybe_handle_karen_case_timeline_query(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, client_id: str, text: str) -> bool:
    if not update.message:
        return False

    case_id = get_active_case_id(int(chat_id))
    is_karen_flow = str(chat_id) == str(KAREN_CHAT_ID) or client_id == resolve_client_id(KAREN_CHAT_ID) or str(case_id) == CASE_KEY
    if not is_karen_flow:
        return False

    year = _karen_timeline_query_year(text)
    if year and not case_id:
        return False
    if not _looks_like_karen_timeline_query(text):
        return False

    if not case_id:
        await update.message.reply_text(
            "No tengo eventos de cronología disponibles todavía porque no hay un caso activo para este chat.\n\n"
            "Puedes activar/registrar el caso, subir documentos o agregar notas con fechas para armarla.\n\n"
            "Esto organiza información registrada; no sustituye revisión de abogada."
        )
        return True

    notes = fetch_case_notes(int(chat_id), str(case_id), limit=160)
    events = build_timeline_events_from_case_notes(notes, client_id=client_id, case_id=str(case_id))
    await update.message.reply_text(_render_karen_case_timeline(events, case_id=str(case_id), year=year))
    return True


def _normalize_daily_operator_query(text: str) -> str:
    norm = _norm_text(text or "")
    norm = re.sub(r"[¿?¡!.,:;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", norm).strip()
    norm = re.sub(r"^(bal|val|valeria|vale)\s+", "", norm).strip()
    norm = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", norm).strip()
    return norm


def _looks_like_karen_daily_operator_query(text: str) -> bool:
    norm = _normalize_daily_operator_query(text)
    if not norm:
        return False

    negative_markers = (
        "agenda",
        "cita",
        "calendario",
        "google calendar",
        "manana",
        "mañana",
        "esta semana",
        "recuerdame",
        "recuérdame",
        "recordatorio",
        "documento",
        "documentos",
        "archivo",
        "archivos",
        "vfms",
        "cronologia",
        "cronología",
        "linea de tiempo",
        "línea de tiempo",
        "que paso en",
        "qué pasó en",
        "super",
        "súper",
        "supermercado",
        "lista",
        "finca",
        "terreno",
        "heredero",
        "herederos",
        "abogada",
        "abogado",
        "nora",
        "paquete",
    )
    if any(marker in norm for marker in negative_markers):
        return False

    exact_markers = {
        "que hago hoy",
        "qué hago hoy",
        "que sigue",
        "qué sigue",
        "dame el resumen completo de hoy",
        "resumen completo de hoy",
        "detalles completos de hoy",
        "operador diario completo",
        "dame mi resumen del dia",
        "dame mi resumen del día",
        "resumen del dia",
        "resumen del día",
        "estoy perdida organizame",
        "estoy perdida organízame",
        "estoy perdido organizame",
        "estoy perdido organízame",
        "que tengo pendiente",
        "qué tengo pendiente",
        "que tengo pendientes",
        "qué tengo pendientes",
        "mis pendientes",
    }
    if norm in exact_markers:
        return True

    return (
        "estoy perdida" in norm
        and ("organizame" in norm or "organízame" in norm)
    )


def _looks_like_karen_daily_operator_full_query(text: str) -> bool:
    norm = _normalize_daily_operator_query(text)
    full_markers = {
        "dame el resumen completo de hoy",
        "resumen completo de hoy",
        "detalles completos de hoy",
        "operador diario completo",
        "dame mi resumen completo del dia",
        "dame mi resumen completo del día",
    }
    return norm in full_markers


def _daily_operator_document_records_from_notes(notes) -> list[dict]:
    records = []
    for note in notes or ():
        source = str(note.get("source") or "").strip()
        if source != "telegram_attachment_vfms":
            continue
        note_text = str(note.get("note_text") or "")

        def first(pattern: str) -> str:
            m = re.search(pattern, note_text, flags=re.IGNORECASE)
            return m.group(1).strip() if m else ""

        filename = first(r"- Archivo:\s*(.+)") or "documento"
        status = first(r"- Estado:\s*(.+)") or "stored"
        caption = first(r"- Nota usuario:\s*(.+)")
        ingest_id = first(r"- VFMS ingest_id:\s*(.+)")
        records.append({
            "document_id": f"case_note:{note.get('id')}",
            "filename": filename,
            "status": status,
            "caption": caption,
            "ingest_id": ingest_id,
            "source": source,
            "source_id": str(note.get("id") or ""),
            "created_at": str(note.get("created_at") or ""),
        })
    return records


def _format_daily_operator_items(items, *, empty: str, limit: int = 5) -> list[str]:
    out = []
    for item in list(items or ())[:limit]:
        title = str(item.get("title") or "").strip()
        due = str(item.get("due_at") or "").strip()
        status = str(item.get("status") or "").strip()
        label = title or "(sin título)"
        if due:
            label = f"{due[:16]} · {label}"
        if status and status not in ("pending", "today"):
            label = f"{label} [{status}]"
        out.append(f"- {label}")
    return out or [f"- {empty}"]


def _build_karen_daily_operator_reply(chat_id: int, client_id: str, *, compact: bool = True) -> str:
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    from memory_store import fetch_open_commitments, list_reminders_for_chat

    tz = ZoneInfo("America/Panama")
    today = datetime.now(tz).date().isoformat()
    warnings = ["Google Calendar no se consultó en este modo v0; agenda externa queda separada."]
    reminders = []
    tasks = []
    pending_actions = []
    notes = []
    case_id = ""

    try:
        reminder_rows = list_reminders_for_chat(int(chat_id), statuses=["pending", "sending"], limit=10) or []
        for row in reminder_rows:
            due = str(row.get("due_at_utc") or "")
            reminders.append({
                "id": row.get("id"),
                "text": row.get("text") or "",
                "due_at_utc": due,
                "status": row.get("status") or "pending",
                "source": "reminder",
            })
    except Exception as e:
        warnings.append(f"No pude leer recordatorios internos: {e}")

    try:
        task_rows = fetch_open_commitments(int(chat_id), limit=10) or []
        for row in task_rows:
            task = dict(row) if hasattr(row, "keys") else {
                "id": row[0],
                "raw_input": row[1],
                "action": row[2],
                "target": row[3],
                "due_date": row[4],
                "confidence": row[5],
                "status": row[6],
            }
            tasks.append(task)
    except Exception as e:
        warnings.append(f"No pude leer tareas abiertas: {e}")

    try:
        for action_type in (GCAL_CREATE_ACTION_TYPE, GCAL_DELETE_ACTION_TYPE):
            action = get_pending_action(int(chat_id), action_type=action_type, client_id=client_id)
            if action:
                pending_actions.append(action)
    except Exception as e:
        warnings.append(f"No pude revisar confirmaciones pendientes: {e}")

    try:
        case_id = get_active_case_id(int(chat_id)) or ""
        if case_id:
            notes = fetch_case_notes(int(chat_id), str(case_id), limit=160)
    except Exception as e:
        warnings.append(f"No pude leer notas del caso activo: {e}")
        case_id = ""

    timeline_events = []
    document_records = []
    case_priorities = []
    if case_id:
        try:
            timeline_events = build_timeline_events_from_case_notes(notes, client_id=client_id, case_id=str(case_id))[:8]
        except Exception as e:
            warnings.append(f"No pude armar cronología del caso: {e}")
        try:
            document_records = _daily_operator_document_records_from_notes(notes)
        except Exception as e:
            warnings.append(f"No pude revisar documentos pendientes: {e}")
        case_priorities.append({
            "id": f"case:{case_id}:review",
            "title": "Revisar próximos pasos del caso activo",
            "description": f"CASE:{case_id}",
            "source": "case_active",
            "priority": "high",
            "status": "pending",
        })

    snapshot = build_daily_operator_snapshot_from_sources(
        client_id=client_id,
        case_id=str(case_id or ""),
        snapshot_date=today,
        calendar_events=(),
        reminders=reminders,
        tasks=tasks,
        pending_actions=pending_actions,
        case_priority_sources=case_priorities,
        document_records=document_records,
        timeline_events=timeline_events,
        warnings=warnings,
        metadata={"route": "karen_daily_operator_v0", "read_only": True},
    )
    safe = safe_daily_operator_summary(snapshot)

    provenance = []
    for field in ("pending_actions", "case_priorities", "document_items", "timeline_items"):
        for item in safe.get(field, ()):
            source_type = str(item.get("source_type") or "").strip()
            source_id = str(item.get("source_id") or "").strip()
            if source_type or source_id:
                provenance.append({"source_type": source_type, "source_id": source_id})

    if compact:
        deterministic_text = render_daily_operator_compact(snapshot)
        envelope = create_response_envelope(
            response_id=f"karen_daily_operator_compact:{chat_id}:{today}",
            client_id=client_id,
            source_route="karen_daily_operator",
            response_type=ResponseType.DAILY_OPERATOR.value,
            factual_payload=safe,
            rendered_text=deterministic_text,
            allowed_style_mode=StyleMode.WARM.value,
            legal_boundary="Esto es una organización operativa; no sustituye revisión legal.",
            provenance=provenance,
            metadata={"route": "karen_daily_operator_v0", "read_only": True, "mode": "compact"},
        )
        return render_polished_fixture_response(envelope)

    today_agenda = (
        filter_today_items(snapshot.reminders, snapshot.snapshot_date)
        + filter_today_items(snapshot.tasks, snapshot.snapshot_date)
    )

    lines = [
        "🧭 Modo operador diario",
        "",
        "Hoy / Agenda",
    ]
    lines.extend(_format_daily_operator_items([safe_item for safe_item in safe["calendar_items"]], empty="No consulté calendario externo en este modo."))
    if today_agenda:
        lines.extend(f"- {item.title}" for item in today_agenda[:5])

    lines.extend(["", "Pendientes / recordatorios"])
    combined_pending = list(safe["pending_actions"]) + list(safe["reminders"]) + list(safe["tasks"])
    lines.extend(_format_daily_operator_items(combined_pending, empty="No encontré pendientes internos abiertos."))

    lines.extend(["", "Caso legal / finca"])
    if case_id:
        case_items = list(safe["case_priorities"]) + list(safe["timeline_items"])
        lines.extend(_format_daily_operator_items(case_items, empty="No encontré eventos de caso listos para mostrar."))
    else:
        lines.append("- No hay caso activo para este chat.")

    lines.extend(["", "Documentos a revisar"])
    lines.extend(_format_daily_operator_items(safe["document_items"], empty="No encontré documentos pendientes de revisión."))

    lines.extend([
        "",
        "Siguiente acción sugerida",
        f"- {safe['suggested_next_action'] or 'revisar agenda y próximos pasos'}",
    ])

    if safe["warnings"]:
        lines.extend(["", "Notas"])
        lines.extend(f"- {w}" for w in safe["warnings"][:3])

    lines.extend([
        "",
        "Esto es una organización operativa; no sustituye revisión legal.",
    ])
    deterministic_text = "\n".join(lines)

    envelope = create_response_envelope(
        response_id=f"karen_daily_operator:{chat_id}:{today}",
        client_id=client_id,
        source_route="karen_daily_operator",
        response_type=ResponseType.DAILY_OPERATOR.value,
        factual_payload=safe,
        rendered_text=deterministic_text,
        allowed_style_mode=StyleMode.WARM.value,
        legal_boundary="Esto es una organización operativa; no sustituye revisión legal.",
        provenance=provenance,
        metadata={"route": "karen_daily_operator_v0", "read_only": True, "mode": "full"},
    )
    return render_polished_fixture_response(envelope)


async def maybe_handle_karen_daily_operator_query(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, client_id: str, text: str) -> bool:
    if not update.message:
        return False
    if looks_like_technical_paste(text):
        return False

    case_id = ""
    try:
        case_id = get_active_case_id(int(chat_id)) or ""
    except Exception:
        case_id = ""

    is_karen_flow = str(chat_id) == str(KAREN_CHAT_ID) or client_id == resolve_client_id(KAREN_CHAT_ID) or str(case_id) == CASE_KEY
    if not is_karen_flow:
        return False
    if not _looks_like_karen_daily_operator_query(text):
        return False

    full = _looks_like_karen_daily_operator_full_query(text)
    await update.message.reply_text(
        _build_karen_daily_operator_reply(int(chat_id), client_id, compact=not full),
        disable_web_page_preview=True,
    )
    return True


async def maybe_handle_karen_notes_tasks_visibility(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, client_id: str, text: str) -> bool:
    if not update.message:
        return False

    case_id = ""
    try:
        case_id = get_active_case_id(int(chat_id)) or ""
    except Exception:
        case_id = ""

    is_karen_flow = str(chat_id) == str(KAREN_CHAT_ID) or client_id == resolve_client_id(KAREN_CHAT_ID) or str(case_id) == CASE_KEY
    if not is_karen_flow:
        return False

    if looks_like_karen_case_pendientes_query(text):
        case_id = case_id or CASE_KEY
        try:
            notes = fetch_case_notes(int(chat_id), str(case_id), limit=80)
        except Exception as e:
            logger.exception(f"[KAREN_PENDIENTES_NOTES] failed: {e}")
            notes = []
        try:
            from memory_store import fetch_open_commitments

            tasks = fetch_open_commitments(int(chat_id), limit=10) or []
        except Exception as e:
            logger.exception(f"[KAREN_PENDIENTES_TASKS] failed: {e}")
            tasks = []
        auxiliary_tasks = load_karen_auxiliary_task_items(client_id)
        await update.message.reply_text(render_karen_case_pendientes_view(tasks=tasks, notes=notes, auxiliary_tasks=auxiliary_tasks))
        return True

    if looks_like_karen_notes_query(text):
        case_id = case_id or CASE_KEY
        try:
            notes = fetch_case_notes(int(chat_id), str(case_id), limit=40)
        except Exception as e:
            logger.exception(f"[KAREN_NOTES_VISIBILITY] failed: {e}")
            notes = []
        await update.message.reply_text(render_karen_case_notes_view(notes, case_id=str(case_id)))
        return True

    if looks_like_karen_tasks_query(text):
        try:
            from memory_store import fetch_open_commitments

            tasks = fetch_open_commitments(int(chat_id), limit=10) or []
        except Exception as e:
            logger.exception(f"[KAREN_TASKS_VISIBILITY] failed: {e}")
            tasks = []
        auxiliary_tasks = load_karen_auxiliary_task_items(client_id)
        actual_reminders, completed_tasks = _karen_task_hygiene_sources(chat_id)
        _clear_karen_numbered_action_dirty(chat_id, "task")
        await update.message.reply_text(
            render_karen_tasks_view(
                tasks,
                auxiliary_tasks=auxiliary_tasks,
                actual_reminders=actual_reminders,
                completed_tasks=completed_tasks,
            )
        )
        return True

    return False


def _karen_task_hygiene_sources(chat_id: int) -> tuple[list, list]:
    reminders: list = []
    completed: list = []
    try:
        from memory_store import list_reminders_for_chat

        reminders = list_reminders_for_chat(int(chat_id), statuses=["pending", "sending", "sent"], limit=100) or []
    except Exception as e:
        logger.exception(f"[KAREN_TASK_HYGIENE_REMINDERS] failed: {e}")
    try:
        conn = _get_conn()
        cur = conn.cursor()
        completed = cur.execute(
            """
            SELECT id, raw_input, action, target, due_date, confidence, status, completed_at, created_at
            FROM commitments
            WHERE chat_id=?
              AND status IN ('done', 'deleted')
            ORDER BY COALESCE(completed_at, created_at) DESC, id DESC
            LIMIT 100
            """,
            (int(chat_id),),
        ).fetchall() or []
        conn.close()
    except Exception as e:
        logger.exception(f"[KAREN_TASK_HYGIENE_COMPLETED] failed: {e}")
        completed = []
    return reminders, completed


async def maybe_handle_karen_task_query_hard_gate(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, client_id: str, text: str) -> bool:
    """
    Ultra-early Karen task-list guard.

    Keep this above GCal/document/case routes and above MEMORY_TEST_TEXT insertion:
    live voice transcriptions like "Val, qué tareas tengo activa?" must render
    tasks, not become memory or finca/case summaries.
    """
    if not update.message:
        return False
    if not _is_karen_client_id(client_id):
        return False
    if not looks_like_karen_tasks_query(text):
        return False
    try:
        from memory_store import fetch_open_commitments

        tasks = fetch_open_commitments(int(chat_id), limit=10) or []
    except Exception as e:
        logger.exception(f"[KAREN_TASK_QUERY_HARD_GATE_FETCH] failed: {e}")
        tasks = []
    auxiliary_tasks = load_karen_auxiliary_task_items(client_id)
    actual_reminders, completed_tasks = _karen_task_hygiene_sources(chat_id)
    _clear_karen_numbered_action_dirty(chat_id, "task")
    await update.message.reply_text(
        render_karen_tasks_view(
            tasks,
            auxiliary_tasks=auxiliary_tasks,
            actual_reminders=actual_reminders,
            completed_tasks=completed_tasks,
        )
    )
    logger.info("[KAREN_TASK_QUERY_HARD_GATE] handled=True text=%r", text)
    return True


def _normalize_task_completion_request(text: str) -> tuple[Optional[int], str]:
    norm = _norm_text(text or "")
    norm = re.sub(r"[¿?¡!.,:;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(bal|val|valeria|vale)\s+", "", norm).strip()

    number_match = re.search(r"\btarea\s+(?P<num>\d{1,2}|uno|una|primer|primero|dos|segundo|tres|tercero|cuatro|cinco|seis|siete|ocho|nueve|diez)\b", norm)
    number = _karen_number_word_to_int(number_match.group("num")) if number_match else None

    target = ""
    patterns = (
        r"marca\s+como\s+hecha\s+la\s+tarea\s+de\s+(.+)$",
        r"marca\s+como\s+hecha\s+tarea\s+de\s+(.+)$",
        r"marcar\s+como\s+hecha\s+la\s+tarea\s+de\s+(.+)$",
        r"marcar\s+como\s+hecha\s+tarea\s+de\s+(.+)$",
        r"marca\s+la\s+tarea\s+de\s+(.+?)\s+como\s+hecha$",
        r"marca\s+tarea\s+de\s+(.+?)\s+como\s+hecha$",
        r"cierra\s+la\s+tarea\s+de\s+(.+)$",
        r"cierra\s+tarea\s+de\s+(.+)$",
        r"completa\s+la\s+tarea\s+de\s+(.+)$",
        r"completa\s+tarea\s+de\s+(.+)$",
        r"ya\s+hice\s+la\s+tarea\s+de\s+(.+)$",
        r"ya\s+hice\s+tarea\s+de\s+(.+)$",
        r"ya\s+hice\s+(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, norm)
        if match:
            target = (match.group(1) or "").strip()
            break

    return number, target


def _parse_karen_task_delete_request(text: str) -> int | None:
    norm = _normalize_daily_operator_query(text)
    if not re.search(r"\b(borra|elimina|cancela)\s+(?:la\s+)?tarea\b", norm):
        return None
    number = _karen_extract_number_after("tarea", text)
    return number or 0


def _looks_like_karen_task_delete_followup(text: str) -> str | None:
    norm = _normalize_daily_operator_query(text)
    if re.search(r"\b(marca|marcar)\w*\s+(?:como\s+)?hecha\b", norm) or norm in {"hecha", "como hecha", "marcar hecha"}:
        return "done"
    delete_markers = (
        "eliminarla",
        "eliminarlo",
        "eliminar del listado",
        "eliminarla del listado",
        "eliminarlo del listado",
        "borrala",
        "borralo",
        "sacala del listado",
        "sacarlo del listado",
        "quitarla",
        "quitarlo",
        "quita del listado",
        "removerla",
        "removerlo",
    )
    if norm in delete_markers or any(marker in norm for marker in delete_markers):
        return "delete"
    return None


async def maybe_handle_karen_task_delete_followup(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, client_id: str, text: str) -> bool:
    if not update.message:
        return False
    pending = _KAREN_PENDING_TASK_DELETE_CONTEXT.get(int(chat_id))
    if not pending:
        return False
    if time.time() - float(pending.get("ts") or 0) > 600:
        _KAREN_PENDING_TASK_DELETE_CONTEXT.pop(int(chat_id), None)
        return False
    choice = _looks_like_karen_task_delete_followup(text)
    if not choice:
        return False

    task_text = str(pending.get("task_text") or "esta tarea").strip()
    task_id = pending.get("task_id")
    if choice == "done":
        if not task_id:
            _KAREN_PENDING_TASK_DELETE_CONTEXT.pop(int(chat_id), None)
            await update.message.reply_text(
                "Esa tarea está guardada como pendiente sin fecha. Puedo mostrarla, pero todavía necesito convertirla a tarea formal para cerrarla."
            )
            return True
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE commitments
                SET status='done',
                    completed_at=CURRENT_TIMESTAMP
                WHERE id=? AND chat_id=? AND status='open'
                """,
                (int(task_id), int(chat_id)),
            )
            changed = cur.rowcount
            conn.commit()
            conn.close()
        except Exception as e:
            logger.exception(f"[KAREN_TASK_DELETE_FOLLOWUP_DONE] failed: {e}")
            await update.message.reply_text("No pude marcar esa tarea como hecha ahora mismo.")
            return True
        _KAREN_PENDING_TASK_DELETE_CONTEXT.pop(int(chat_id), None)
        _mark_karen_numbered_action_dirty(chat_id, "task")
        if not changed:
            await update.message.reply_text("Esa tarea ya no aparece abierta. Pide “Val, qué tareas tengo” para verificar.")
            return True
        await update.message.reply_text(f"Listo. Marqué esta tarea como hecha: {task_text}.")
        return True

    if pending.get("is_auxiliary") or not task_id:
        _KAREN_PENDING_TASK_DELETE_CONTEXT.pop(int(chat_id), None)
        await update.message.reply_text(
            "Todavía no elimino tareas del historial; puedo marcarla como hecha para quitarla de pendientes. "
            "¿Quieres que la marque como hecha?"
        )
        return True

    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE commitments
            SET status='deleted',
                completed_at=CURRENT_TIMESTAMP
            WHERE id=? AND chat_id=? AND status='open'
            """,
            (int(task_id), int(chat_id)),
        )
        changed = cur.rowcount
        conn.commit()
        conn.close()
    except Exception as e:
        logger.exception(f"[KAREN_TASK_DELETE_FOLLOWUP_DELETE] failed: {e}")
        await update.message.reply_text(
            "Todavía no elimino tareas del historial; puedo marcarla como hecha para quitarla de pendientes. "
            "¿Quieres que la marque como hecha?"
        )
        return True

    _KAREN_PENDING_TASK_DELETE_CONTEXT.pop(int(chat_id), None)
    _mark_karen_numbered_action_dirty(chat_id, "task")
    if not changed:
        await update.message.reply_text("Esa tarea ya no aparece abierta. Pide “Val, qué tareas tengo” para verificar.")
        return True
    await update.message.reply_text(f"Listo. Quité esta tarea del listado activo: {task_text}.")
    return True


async def maybe_handle_karen_task_delete_request(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, client_id: str, text: str) -> bool:
    if not update.message:
        return False
    case_id = ""
    try:
        case_id = get_active_case_id(int(chat_id)) or ""
    except Exception:
        case_id = ""
    is_karen_flow = str(chat_id) == str(KAREN_CHAT_ID) or client_id == resolve_client_id(KAREN_CHAT_ID) or str(case_id) == CASE_KEY
    if not is_karen_flow:
        return False
    number = _parse_karen_task_delete_request(text)
    if number is None:
        return False
    _clear_karen_numbered_action_context(chat_id)
    if not number:
        _KAREN_PENDING_TASK_DELETE_CONTEXT[int(chat_id)] = {"task_id": None, "task_text": "", "is_auxiliary": False, "ts": time.time()}
        await update.message.reply_text("¿Quieres marcarla como hecha o eliminarla del listado?")
        return True
    try:
        from memory_store import fetch_open_commitments

        rows = merge_karen_task_items(
            fetch_open_commitments(int(chat_id), limit=20) or [],
            load_karen_auxiliary_task_items(client_id),
        )
    except Exception as e:
        logger.exception(f"[KAREN_TASK_DELETE_FETCH] failed: {e}")
        rows = []
    if rows and 1 <= int(number) <= len(rows):
        selected = _karen_task_row_dict(rows[int(number) - 1])
        task_text = str(selected.get("raw_input") or selected.get("action") or f"tarea {number}").strip()
        _KAREN_PENDING_TASK_DELETE_CONTEXT[int(chat_id)] = {
            "task_id": selected.get("id") if not is_auxiliary_task_row(selected) else None,
            "task_text": task_text,
            "is_auxiliary": bool(is_auxiliary_task_row(selected)),
            "number": int(number),
            "ts": time.time(),
        }
    else:
        _KAREN_PENDING_TASK_DELETE_CONTEXT[int(chat_id)] = {"task_id": None, "task_text": f"tarea {number}", "is_auxiliary": False, "number": int(number), "ts": time.time()}
    await update.message.reply_text(
        f"¿Quieres marcar la tarea {number} como hecha o eliminarla del listado? "
        "Para mantener historial, lo más seguro es: “marca la tarea "
        f"{number} como hecha”."
    )
    return True


def _tomorrow_panama_date() -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("America/Panama")
    return (datetime.now(tz) + timedelta(days=1)).date().isoformat()


def _karen_task_row_dict(row) -> dict:
    if isinstance(row, dict):
        return dict(row)
    if hasattr(row, "keys"):
        return dict(row)
    return {
        "id": row[0],
        "raw_input": row[1],
        "action": row[2],
        "target": row[3],
        "due_date": row[4],
    }


def _karen_schedule_text_key(text: str) -> str:
    norm = _norm_text(text or "")
    norm = re.sub(r"[^\w\s]", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def _karen_existing_open_task_with_due(chat_id: int, task_text: str, due_date: str) -> dict | None:
    key = _karen_schedule_text_key(task_text)
    if not key:
        return None
    try:
        from memory_store import fetch_open_commitments

        for row in fetch_open_commitments(int(chat_id), limit=30) or []:
            rd = _karen_task_row_dict(row)
            row_key = _karen_schedule_text_key(str(rd.get("raw_input") or rd.get("action") or ""))
            row_due = str(rd.get("due_date") or "").strip()[:10]
            if row_key == key and row_due == due_date:
                return rd
    except Exception as e:
        logger.exception(f"[KAREN_TASK_SCHEDULE_DEDUPE] failed: {e}")
    return None


async def maybe_handle_karen_task_schedule_for_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, client_id: str, text: str) -> bool:
    if not update.message:
        return False

    request = parse_karen_task_schedule_for_tomorrow(text)
    if not request:
        return False

    case_id = ""
    try:
        case_id = get_active_case_id(int(chat_id)) or ""
    except Exception:
        case_id = ""

    is_karen_flow = str(chat_id) == str(KAREN_CHAT_ID) or client_id == resolve_client_id(KAREN_CHAT_ID) or str(case_id) == CASE_KEY
    if not is_karen_flow:
        return False

    try:
        from memory_store import fetch_open_commitments

        rows = merge_karen_task_items(
            fetch_open_commitments(int(chat_id), limit=20) or [],
            load_karen_auxiliary_task_items(client_id),
        )
    except Exception as e:
        logger.exception(f"[KAREN_TASK_SCHEDULE_FETCH] failed: {e}")
        await update.message.reply_text("No pude leer tus tareas abiertas ahora mismo.")
        return True

    if not rows:
        await update.message.reply_text("No encontré tareas abiertas para poner para mañana.")
        return True

    if request.get("number") is not None and _is_karen_numbered_action_dirty(chat_id, "task"):
        _clear_karen_numbered_action_context(chat_id)
        await update.message.reply_text(
            f"La lista de tareas cambió. Pide “Val, qué tareas tengo” antes de actuar sobre la tarea {request.get('number')}."
        )
        return True

    selected, status = select_karen_task_for_schedule(rows, request)
    if selected is None:
        if status == "ambiguous":
            await update.message.reply_text(
                "Encontré más de una tarea posible. Pide “Val, qué tareas tengo” y dime el número: "
                "“pon la tarea 1 para mañana”."
            )
        else:
            await update.message.reply_text(
                "No pude identificar una sola tarea para poner para mañana. "
                "Pide “Val, qué tareas tengo” y dime el número."
            )
        return True

    selected_row = _karen_task_row_dict(selected)
    task_text = str(selected_row.get("raw_input") or selected_row.get("action") or "tarea sin fecha").strip()
    tomorrow = _tomorrow_panama_date()

    if _karen_existing_open_task_with_due(int(chat_id), task_text, tomorrow):
        await update.message.reply_text(f"Ya tengo esa tarea para mañana: {task_text}.")
        return True

    if is_auxiliary_task_row(selected_row):
        try:
            from memory_store import upsert_commitment

            upsert_commitment(
                chat_id=int(chat_id),
                raw_input=task_text,
                action=task_text,
                target="",
                due_date=tomorrow,
                confidence="derived_from_pending",
            )
            log_action(chat_id, "task_scheduled_from_pending", task_text)
            _mark_karen_numbered_action_dirty(chat_id, "task")
        except Exception as e:
            logger.exception(f"[KAREN_TASK_SCHEDULE_CONVERT] failed: {e}")
            await update.message.reply_text("No pude poner esa tarea para mañana ahora mismo.")
            return True
    else:
        try:
            task_id = int(selected_row.get("id"))
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE commitments
                SET due_date=?
                WHERE id=? AND chat_id=? AND status='open'
                """,
                (tomorrow, task_id, int(chat_id)),
            )
            changed = cur.rowcount
            conn.commit()
            conn.close()
            if not changed:
                await update.message.reply_text(
                    "Esa tarea ya no aparece abierta. Pide “Val, qué tareas tengo” para verificar."
                )
                return True
            log_action(chat_id, "task_scheduled_for_tomorrow", task_text)
            _mark_karen_numbered_action_dirty(chat_id, "task")
        except Exception as e:
            logger.exception(f"[KAREN_TASK_SCHEDULE_UPDATE] failed: {e}")
            await update.message.reply_text("No pude poner esa tarea para mañana ahora mismo.")
            return True

    await update.message.reply_text(f"Listo. Puse esta tarea para mañana: {task_text}.")
    return True


async def maybe_handle_karen_task_completion(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, client_id: str, text: str) -> bool:
    if not update.message:
        return False

    case_id = ""
    try:
        case_id = get_active_case_id(int(chat_id)) or ""
    except Exception:
        case_id = ""

    is_karen_flow = str(chat_id) == str(KAREN_CHAT_ID) or client_id == resolve_client_id(KAREN_CHAT_ID) or str(case_id) == CASE_KEY
    if not is_karen_flow:
        return False

    norm = _normalize_daily_operator_query(text)
    completion_markers = (
        "marca como hecha la tarea",
        "marca como hecha tarea",
        "marcar como hecha la tarea",
        "marcar como hecha tarea",
        "marca la tarea",
        "marca tarea",
        "ya hice la tarea",
        "ya hice tarea",
        "cierra la tarea",
        "cierra tarea",
        "completa la tarea",
        "completa tarea",
        "ya hice",
    )
    if not any(marker in norm for marker in completion_markers):
        return False

    number, target = _normalize_task_completion_request(text)

    try:
        from memory_store import fetch_open_commitments

        rows = merge_karen_task_items(
            fetch_open_commitments(int(chat_id), limit=20) or [],
            load_karen_auxiliary_task_items(client_id),
        )
    except Exception as e:
        logger.exception(f"[KAREN_TASK_COMPLETION_FETCH] failed: {e}")
        await update.message.reply_text("No pude leer tus tareas abiertas ahora mismo.")
        return True

    if not rows:
        _clear_karen_numbered_action_context(chat_id)
        await update.message.reply_text("No encontré tareas abiertas para marcar como hechas.")
        return True

    selected = None
    if number is not None:
        if _is_karen_numbered_action_dirty(chat_id, "task"):
            _clear_karen_numbered_action_context(chat_id)
            await update.message.reply_text(
                f"La lista de tareas cambió. Pide “Val, qué tareas tengo” antes de actuar sobre la tarea {number}."
            )
            return True
        if number < 1 or number > len(rows):
            await update.message.reply_text(
                f"No veo una tarea {number}. Pide “Val, qué tareas tengo” para ver la lista actual."
            )
            return True
        selected = rows[number - 1]
    elif target:
        target_key = _norm_text(target)
        matches = []
        for row in rows:
            rd = dict(row) if hasattr(row, "keys") else {
                "id": row[0],
                "raw_input": row[1],
                "action": row[2],
                "target": row[3],
                "due_date": row[4],
            }
            raw_key = _norm_text(str(rd.get("raw_input") or ""))
            combo_key = _norm_text(" ".join(str(rd.get(k) or "") for k in ("action", "target")))
            if target_key and (target_key in raw_key or target_key in combo_key):
                matches.append(row)
        if len(matches) == 1:
            selected = matches[0]
        elif len(matches) > 1:
            await update.message.reply_text(
                "Encontré más de una tarea parecida. Pide “Val, qué tareas tengo” y dime el número: "
                "“marca como hecha la tarea 1”."
            )
            return True

    if selected is None:
        await update.message.reply_text(
            "No pude identificar una sola tarea para cerrar. Pide “Val, qué tareas tengo” y dime el número."
        )
        return True

    selected_row = dict(selected) if hasattr(selected, "keys") else {
        "id": selected[0],
        "raw_input": selected[1],
        "action": selected[2],
        "target": selected[3],
        "due_date": selected[4],
    }
    task_text = str(selected_row.get("raw_input") or selected_row.get("action") or "tarea sin fecha").strip()

    if is_auxiliary_task_row(selected_row):
        _clear_karen_numbered_action_context(chat_id)
        await update.message.reply_text(
            "Esa tarea está guardada como pendiente sin fecha. Puedo mostrarla, "
            "pero todavía necesito convertirla a tarea formal para cerrarla."
        )
        return True

    task_id = int(selected_row.get("id"))
    task_text = task_text or f"tarea {task_id}"

    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE commitments
            SET status='done',
                completed_at=CURRENT_TIMESTAMP
            WHERE id=? AND chat_id=? AND status='open'
            """,
            (task_id, int(chat_id)),
        )
        changed = cur.rowcount
        conn.commit()
        conn.close()
    except Exception as e:
        logger.exception(f"[KAREN_TASK_COMPLETION_UPDATE] failed: {e}")
        await update.message.reply_text("No pude marcar esa tarea como hecha ahora mismo.")
        return True

    if not changed:
        _clear_karen_numbered_action_context(chat_id)
        await update.message.reply_text("Esa tarea ya no aparece abierta. Pide “Val, qué tareas tengo” para verificar.")
        return True

    log_action(chat_id, "task_closed", task_text)
    _clear_karen_numbered_action_context(chat_id)
    _mark_karen_numbered_action_dirty(chat_id, "task")
    await update.message.reply_text(
        "✅ Listo. Marqué esta tarea como hecha:\n"
        f"- {task_text}\n\n"
        "No borré el historial y no toqué Google Calendar ni recordatorios."
    )
    return True


def _workflow_allowed_for_chat(chat_id: int, client_id: str, workflow: str) -> bool:
    profile = get_client_profile_for_chat(chat_id)
    if not profile:
        return False
    if client_id and profile.client_id != client_id:
        return False
    return require_workflow_access(profile.client_id, workflow).allowed


def _looks_like_karen_document_workflow_request(text: str) -> bool:
    norm = _norm_text(text or "")
    return any(marker in norm for marker in (
        "inventario de documentos",
        "empezar inventario de documentos",
        "iniciar inventario de documentos",
        "hagamos inventario de documentos",
        "hacer inventario de documentos",
        "que documentos tengo",
        "que archivos tengo",
        "que dice este documento",
        "que dice el documento",
        "resumen vfms",
        "vfms",
        "resumen del documento",
        "resumen de documento",
        "resumen de documentos",
        "tabla cronologica",
        "ficha legal",
        "datos registrales",
        "registro publico",
        "donde sale finca",
        "donde aparece finca",
    ))


def _looks_like_karen_legal_case_workflow_request(text: str) -> bool:
    norm = _norm_text(text or "")
    direct_markers = (
        "finca",
        "terreno",
        "heredero",
        "herederos",
        "nora",
        "abogada",
        "abogado",
        "paquete para nora",
        "paquete para la abogada",
        "caso del terreno",
        "caso legal",
        "datos basicos del caso",
    )
    if any(marker in norm for marker in direct_markers):
        return True

    review_markers = (
        "que falta revisar",
        "que me falta revisar",
        "que falta conseguir",
        "que me falta conseguir",
        "antes de hablar",
    )
    legal_context = ("abogada" in norm or "abogado" in norm or "nora" in norm)
    return legal_context and any(marker in norm for marker in review_markers)


def _looks_like_karen_grocery_workflow_request(text: str) -> bool:
    norm = _norm_text(text or "")
    grocery_markers = (
        "supermercado",
        "lista del super",
        "lista de super",
        "lista para el super",
        "lista del supermercado",
        "lista de supermercado",
        "lista de compras",
    )
    if any(marker in norm for marker in grocery_markers):
        return True
    return norm.startswith((
        "agrega a la lista",
        "agregar a la lista",
        "anade a la lista",
        "añade a la lista",
        "quita de la lista",
        "quitar de la lista",
    ))


async def maybe_guard_unknown_client_protected_workflow(update: Update, chat_id: int, client_id: str, text: str) -> bool:
    if not update.message:
        return False

    workflow_checks = (
        (WORKFLOW_DAILY_OPERATOR, _looks_like_karen_daily_operator_query(text)),
        (WORKFLOW_TIMELINE, _looks_like_karen_timeline_query(text)),
        (WORKFLOW_DOCUMENTS, _looks_like_karen_document_workflow_request(text)),
        (WORKFLOW_LEGAL_CASE, _looks_like_karen_legal_case_workflow_request(text)),
        (WORKFLOW_GROCERIES, _looks_like_karen_grocery_workflow_request(text)),
    )
    for workflow, requested in workflow_checks:
        if requested and not _workflow_allowed_for_chat(chat_id, client_id, workflow):
            profile = get_client_profile_for_chat(chat_id)
            decision = require_workflow_access(profile.client_id if profile else client_id, workflow)
            await update.message.reply_text(render_workflow_not_enabled_message(decision))
            return True
    return False


def _looks_like_founder_intro_excluded_route(text: str) -> bool:
    norm = _norm_text(text or "")
    if not norm:
        return True

    if looks_like_technical_paste(text):
        return True

    protected_checks = (
        _looks_like_karen_daily_operator_query(text),
        _looks_like_karen_timeline_query(text),
        _looks_like_karen_document_workflow_request(text),
        _looks_like_karen_legal_case_workflow_request(text),
        _looks_like_karen_grocery_workflow_request(text),
    )
    if any(protected_checks):
        return True

    route_markers = (
        "agenda",
        "calendario",
        "google calendar",
        "cita",
        "reunion con",
        "reunión con",
        "tengo reunion",
        "tengo reunión",
        "que tengo hoy",
        "qué tengo hoy",
        "que tengo manana",
        "que tengo mañana",
        "qué tengo mañana",
        "recuerdame",
        "recuérdame",
        "recordatorio",
        "crea recordatorio",
        "borra recordatorio",
        "documento",
        "documentos",
        "archivo",
        "archivos",
        "vfms",
        "cronologia",
        "cronología",
        "linea de tiempo",
        "línea de tiempo",
        "que paso en",
        "qué pasó en",
        "super",
        "súper",
        "supermercado",
        "lista de compras",
        "lista del super",
        "lista del súper",
        "finca",
        "terreno",
        "nora",
        "abogada",
        "abogado",
        "lawyer",
    )
    return any(marker in norm for marker in route_markers)


async def maybe_handle_founder_intro_query(update: Update, text: str) -> bool:
    if not update.message:
        return False
    if _looks_like_founder_intro_excluded_route(text):
        return False

    intent = normalize_founder_intro_intent(text)
    if intent == FOUNDER_INTRO_UNKNOWN:
        return False

    await update.message.reply_text(render_founder_intro_response(intent), disable_web_page_preview=True)
    return True


async def maybe_handle_karen_day0_route(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, client_id: str, text: str) -> bool:
    if not update.message:
        return False

    is_karen_flow = str(chat_id) == str(KAREN_CHAT_ID) or client_id == resolve_client_id(KAREN_CHAT_ID)
    if not is_karen_flow:
        return False

    route = classify_karen_day0_route(text or "")
    if not route.name:
        return False

    if route.name == ROUTE_AGENDA_TOMORROW:
        await update.message.reply_text(
            build_client_agenda_dashboard(client_id, chat_id, "tomorrow"),
            disable_web_page_preview=True,
        )
        return True

    if route.name == ROUTE_CAPABILITY_WEEK:
        from core.founder_intro import render_founder_trial_guidance

        await update.message.reply_text(render_founder_trial_guidance(), disable_web_page_preview=True)
        return True

    if route.name == ROUTE_FINCA_FACTS:
        facts = load_karen_case_facts(int(chat_id))
        await update.message.reply_text(render_case_facts(facts, mode="all", chat_id=int(chat_id)))
        return True

    if route.name == ROUTE_DOCUMENT_INVENTORY:
        if await maybe_handle_document_query(update, context, chat_id, "Val, qué documentos tengo"):
            return True
        await update.message.reply_text(
            "📎 Documentos registrados\n\n"
            "No encontré un inventario estructurado disponible para este chat todavía.\n\n"
            "Límite: esto organiza información registrada; no sustituye revisión legal o profesional."
        )
        return True

    if route.name == ROUTE_NEXT_ACTION:
        await update.message.reply_text(
            _build_karen_daily_operator_reply(int(chat_id), client_id, compact=True),
            disable_web_page_preview=True,
        )
        return True

    return False


# --------------------------------------------------
# Text handler
# --------------------------------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.message and update.message.text):
        return

    text = update.message.text.strip()
    raw_input = text
    chat_id = update.effective_chat.id
    client_id = resolve_client_id(chat_id)
    tg_msg_id = getattr(update.message, "message_id", None)
    _maybe_log_intent_router_v2_shadow(text, chat_id=chat_id, client_id=client_id, message_id=tg_msg_id)

    try:
        if await maybe_handle_karen_name_language_guard(update, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_NAME_LANGUAGE_GUARD_HANDLE_TEXT] failed: {e}")

    # RC-KAREN-05B HARD TASK QUERY GATE:
    # Must remain above GCal/document/case routes and MEMORY_TEST_TEXT insertion.
    try:
        if await maybe_handle_karen_task_query_hard_gate(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("task_query", "maybe_handle_karen_task_query_hard_gate", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_QUERY_HARD_GATE_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_gcal_create_confirmation_first(update, chat_id, text):
            _maybe_log_intent_router_v2_actual("destructive_confirmation", "maybe_handle_karen_gcal_create_confirmation_first", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[GCAL_CONFIRM_ROUTE_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_pending_reminder_context(update, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("pending_action_reply", "maybe_handle_karen_pending_reminder_context", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_PENDING_REMINDER_CONTEXT_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_task_delete_followup(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("pending_action_reply", "maybe_handle_karen_task_delete_followup", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_DELETE_FOLLOWUP_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_pending_gcal_delete_confirmation(update, chat_id, text):
            _maybe_log_intent_router_v2_actual("destructive_confirmation", "maybe_handle_pending_gcal_delete_confirmation", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[GCAL_DELETE_CONFIRM_ROUTE_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_gcal_event_number_delete(update, chat_id, text):
            _maybe_log_intent_router_v2_actual("gcal_delete", "maybe_handle_karen_gcal_event_number_delete", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_GCAL_EVENT_NUMBER_DELETE_HANDLE_TEXT] failed: {e}")

    try:
        if _looks_like_karen_gcal_event_create_request(text):
            logger.info("[GCAL_CREATE_ROUTE] matched live text category=gcal_event_create")
            if await try_appointment_save_natural(update, chat_id, text):
                _maybe_log_intent_router_v2_actual("gcal_create", "try_appointment_save_natural", chat_id=chat_id, message_id=tg_msg_id, text=text)
                return
    except Exception as e:
        logger.exception(f"[GCAL_CREATE_ROUTE_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_weekday_agenda_query(update, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("agenda_query", "maybe_handle_karen_weekday_agenda_query", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_WEEKDAY_AGENDA_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_natural_weekday_reminder(update, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("reminder_create", "maybe_handle_karen_natural_weekday_reminder", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_NATURAL_WEEKDAY_REMINDER_HANDLE_TEXT] failed: {e}")

    if looks_like_technical_paste(text):
        await update.message.reply_text(TECHNICAL_PASTE_REPLY)
        return

    _log_conversation_router_shadow(text, chat_id, client_id)

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

    try:
        if parse_karen_task_schedule_for_tomorrow(text):
            if await maybe_handle_karen_task_schedule_for_tomorrow(update, context, chat_id, client_id, text):
                return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_SCHEDULE_EARLY_HANDLE_TEXT] failed: {e}")

    try:
        if _looks_like_karen_gcal_event_create_request(text):
            if await try_appointment_save_natural(update, chat_id, text):
                return
    except Exception as e:
        logger.exception(f"[KAREN_GCAL_CREATE_EARLY_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_task_delete_followup(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("pending_action_reply", "maybe_handle_karen_task_delete_followup", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
        if await maybe_handle_karen_reminder_management(update, context, chat_id, text):
            _maybe_log_intent_router_v2_actual(_observer_intent_for_karen_reminder_management(text), "maybe_handle_karen_reminder_management", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
        if await maybe_handle_karen_task_delete_request(update, context, chat_id, client_id, text):
            return
        if await maybe_handle_karen_task_completion(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("task_complete", "maybe_handle_karen_task_completion", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_NUMBERED_ACTION_EARLY_HANDLE_TEXT] failed: {e}")

    # Reminder action intercept
    try:
        if await handle_reminder_action_intercept(
            update, chat_id, tg_msg_id, text, normalized, send_telegram_reply
        ):
            return
    except Exception as e:
        logger.exception(f"[REMINDER_ACTION] failed: {e}")

    try:
        if await maybe_guard_unknown_client_protected_workflow(update, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[CLIENT_WORKFLOW_GUARD] failed: {e}")

    try:
        if await maybe_handle_karen_notes_tasks_visibility(update, context, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_NOTES_TASKS_VISIBILITY_EARLY_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_explicit_case_note(update, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_EXPLICIT_CASE_NOTE_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_reminder_management(update, context, chat_id, text):
            _maybe_log_intent_router_v2_actual(_observer_intent_for_karen_reminder_management(text), "maybe_handle_karen_reminder_management", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_REMINDER_MANAGEMENT_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_task_creation(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("task_create", "maybe_handle_karen_task_creation", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_CREATE_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_notes_tasks_visibility(update, context, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_NOTES_TASKS_VISIBILITY_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_task_schedule_for_tomorrow(update, context, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_SCHEDULE_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_task_delete_request(update, context, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_DELETE_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_task_completion(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("task_complete", "maybe_handle_karen_task_completion", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_TASK_COMPLETION_HANDLE_TEXT] failed: {e}")

    try:
        if await maybe_handle_karen_day0_route(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("agenda_query", "maybe_handle_karen_day0_route", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_DAY0_ROUTE_RELIABILITY] failed: {e}")

    try:
        if await maybe_handle_karen_daily_operator_query(update, context, chat_id, client_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_DAILY_OPERATOR_ROUTE] failed: {e}")

    try:
        if await maybe_handle_founder_intro_query(update, text):
            return
    except Exception as e:
        logger.exception(f"[FOUNDER_INTRO_ROUTE] failed: {e}")

    _audit(
        chat_id,
        action="IN_TEXT",
        entity_type="tg_msg",
        entity_id=str(tg_msg_id) if tg_msg_id is not None else None,
        payload=text[:500],
        source="group" if int(chat_id) < 0 else "dm",
    )

    # --------------------------------------------------
    # FRANK OPERATOR MODE V0
    # Personal cockpit phrases for Frank/Boss.
    # Small, deterministic, and safe: capture ideas, parking lot,
    # drift recovery, status, and next-action routing.
    # --------------------------------------------------
    try:
        fom_norm = _norm_text(text or "").strip()
        fom_norm = re.sub(r"^(?:val|valeria)[,:]?\s+", "", fom_norm).strip()
        fom_raw = (text or "").strip()

        # Drift / bring me back
        drift_markers = (
            "estoy drifting",
            "estoy drifteando",
            "me estoy desviando",
            "me fui por las ramas",
            "traeme al carril",
            "tráeme al carril",
            "bring me back",
            "back to mission",
        )

        if any(m in fom_norm for m in drift_markers):
            try:
                priority = get_fact(chat_id=chat_id, fact_key="current_priority") or ""
            except Exception:
                priority = ""

            if not priority:
                priority = "revisar el último checkpoint activo y bajar a la próxima acción concreta del cockpit personal."

            reply = (
                "Ojo, Boss 😌⚓\n\n"
                "Sí: estás drifting un poco. No pasa nada; te agarro por el cuello de la camisa antes de que el conejo blanco nos meta en otra cueva.\n\n"
                f"🎯 Prioridad actual:\n{priority}\n\n"
                "Siguiente acción: dime “Val, qué sigue” y te bajo a una acción concreta."
            )
            await update.message.reply_text(reply)
            return

        # Next action
        next_action_markers = (
            "que sigue",
            "qué sigue",
            "que hago ahora",
            "qué hago ahora",
            "siguiente accion",
            "siguiente acción",
            "next action",
            "what now",
        )

        if any(m == fom_norm for m in next_action_markers):
            await whatnow_cmd(update, context)
            return

        # Mini operator status
        status_markers = (
            "estado operador",
            "status operador",
            "operator status",
            "estado boss",
            "boss status",
        )

        if any(m == fom_norm for m in status_markers):
            try:
                priority = get_fact(chat_id=chat_id, fact_key="current_priority") or ""
            except Exception:
                priority = ""

            lines = [
                "🧭 Boss Mode / Operator Status",
                "",
                "Modo: Val0 personal cockpit v0",
                "Funciones activas:",
                "- Capturar ideas",
                "- Parking lot",
                "- Drift recovery",
                "- Next action / whatnow",
                "- Notas y recordatorios básicos",
                "",
                f"Prioridad actual: {priority or 'No tengo una prioridad explícita guardada todavía.'}",
                "",
                "Prueba:",
                "• Val, estoy drifting",
                "• Val, captura idea: ...",
                "• Val, parking lot: ...",
                "• Val, qué sigue",
            ]
            await update.message.reply_text("\n".join(lines))
            return

        # Capture idea
        idea_prefixes = (
            "captura idea",
            "capturar idea",
            "guarda idea",
            "guardar idea",
            "idea",
        )

        for prefix in idea_prefixes:
            if fom_norm.startswith(prefix):
                idea_text = fom_raw
                if ":" in idea_text:
                    idea_text = idea_text.split(":", 1)[1].strip()
                else:
                    idea_text = re.sub(r"(?is)^\s*(val[,:]?\s*)?(captura idea|capturar idea|guarda idea|guardar idea|idea)\s+", "", idea_text).strip()

                if not idea_text:
                    await update.message.reply_text("Dame la idea después de los dos puntos, Boss. Ejemplo: Val, captura idea: botón rápido para voice notes.")
                    return

                note_id = add_note(chat_id, f"IDEA: {idea_text}")
                await update.message.reply_text(f"💡 Guardé la idea #{note_id}, Boss. No se nos escapa al pantano. 😌\n\n{idea_text}")
                return

        # Parking lot
        parking_prefixes = (
            "parking lot",
            "manda esto al parking lot",
            "manda al parking lot",
            "parquealo",
            "parquéalo",
        )

        for prefix in parking_prefixes:
            if fom_norm.startswith(prefix):
                parking_text = fom_raw
                if ":" in parking_text:
                    parking_text = parking_text.split(":", 1)[1].strip()
                else:
                    parking_text = re.sub(r"(?is)^\s*(val[,:]?\s*)?(parking lot|manda esto al parking lot|manda al parking lot|parquealo|parquéalo)\s+", "", parking_text).strip()

                if not parking_text:
                    await update.message.reply_text("Dame qué quieres mandar al Parking Lot, Boss. Ejemplo: Val, parking lot: Safe Runner con Run ID.")
                    return

                note_id = add_note(chat_id, f"PARKING_LOT: {parking_text}")
                await update.message.reply_text(f"🅿️ Parking Lot guardado #{note_id}, Boss. Lo parqueo sin dejarlo morir en el limbo. 😏\n\n{parking_text}")
                return

    except Exception as e:
        logger.exception(f"[FRANK_OPERATOR_MODE_V0] failed: {e}")

    # --------------------------------------------------
    # Karen numbered reminder/task action priority gate v0
    # Must beat Google Calendar delete/search and stale pending action flows.
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_reminder_management(update, context, chat_id, text):
            _maybe_log_intent_router_v2_actual(_observer_intent_for_karen_reminder_management(text), "maybe_handle_karen_reminder_management", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
        if await maybe_handle_karen_task_delete_request(update, context, chat_id, client_id, text):
            return
        if await maybe_handle_karen_task_completion(update, context, chat_id, client_id, text):
            _maybe_log_intent_router_v2_actual("task_complete", "maybe_handle_karen_task_completion", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_NUMBERED_ACTION_PRIORITY_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Google Calendar Delete Priority Gate v0
    # Must run before grocery/list delete so:
    # "Val, borra Cabalgata Intensa" does not become supermarket cleanup.
    # --------------------------------------------------
    try:
        if await maybe_handle_pending_gcal_delete_confirmation(update, chat_id, text):
            _maybe_log_intent_router_v2_actual("destructive_confirmation", "maybe_handle_pending_gcal_delete_confirmation", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
        if await maybe_handle_karen_gcal_event_number_delete(update, chat_id, text):
            _maybe_log_intent_router_v2_actual("gcal_delete", "maybe_handle_karen_gcal_event_number_delete", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
        if await try_gcal_delete_natural(update, chat_id, text):
            _maybe_log_intent_router_v2_actual("gcal_delete", "try_gcal_delete_natural", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_GCAL_DELETE_PRIORITY_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Grocery/List Priority Gate v0
    # Must run before reminder/drift routing so grocery commands like
    # "Val, borra pan de la lista del súper" do not become reminder deletes.
    try:
        from core.client_context_reader import (
            classify_client_context_query,
            render_client_context_answer,
            render_client_grocery_delete,
            _extract_grocery_delete_items,
            _ensure_grocery_file,
            _norm,
        )

        grocery_text = text or ""
        grocery_qtype = classify_client_context_query(grocery_text)
        grocery_reply = None

        if grocery_qtype in ("grocery_add", "grocery_list", "grocery_delete"):
            grocery_reply = render_client_context_answer(grocery_text, client_id=client_id)

        else:
            # Human shortcut support: "quitar leche", "borra pan".
            # Only treat as grocery delete if the target already exists in Karen's grocery file.
            delete_targets = _extract_grocery_delete_items(grocery_text)
            if delete_targets:
                grocery_path = _ensure_grocery_file(client_id)
                if grocery_path and grocery_path.exists():
                    grocery_lines = [
                        line.strip()[2:].strip()
                        for line in grocery_path.read_text(encoding="utf-8").splitlines()
                        if line.strip().startswith("- ")
                    ]
                    grocery_items_norm = {_norm(item) for item in grocery_lines}
                    if any(_norm(target) in grocery_items_norm for target in delete_targets):
                        grocery_reply = render_client_grocery_delete(grocery_text, client_id=client_id, persist=True)

        if grocery_reply:
            await update.message.reply_text(grocery_reply)
            return
    except Exception as e:
        logger.exception(f"[KAREN_GROCERY_PRIORITY_GATE] failed: {e}")

    # Karen Reminder / Agenda / Multi-intent Shield
    # Must run before Karen legal/doc routes so phrases like
    # "Val, recuérdame una hora antes..." do not get hijacked
    # by document inventory / case memory.
    # --------------------------------------------------
    try:
        kr_norm = _norm_text(text or "").strip()
        # Normalize Val prefix and punctuation before agenda matching.
        # Example: "Val, ¿qué tengo hoy?" must become "que tengo hoy".
        kr_norm = re.sub(r"[¿?¡!.,:;]+", " ", kr_norm)
        kr_norm = re.sub(r"\s+", " ", kr_norm).strip()
        kr_norm = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", kr_norm).strip()
        kr_norm = re.sub(r"^(val|valeria|vale)\s+", "", kr_norm).strip()
        kr_norm = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", kr_norm).strip()

        # 0) Pending Google Calendar appointment confirmation.
        # Must run before appointment parsing so "sí"/"dale" confirms the draft.
        if await maybe_handle_pending_gcal_appointment_confirmation(update, chat_id, text):
            _maybe_log_intent_router_v2_actual("destructive_confirmation", "maybe_handle_pending_gcal_appointment_confirmation", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return

        # 1) Multi-intent beta shield:
        # Karen may paste several numbered instructions in one message.
        # For now, identify the split and ask for the missing reminder anchor
        # instead of pretending it was one instruction.
        has_numbered_multi = (
            ("1." in kr_norm or "1)" in kr_norm or "uno" in kr_norm)
            and ("2." in kr_norm or "2)" in kr_norm or "dos" in kr_norm)
            and ("3." in kr_norm or "3)" in kr_norm or "tres" in kr_norm)
        )
        has_karen_multi_content = (
            ("paquete" in kr_norm and "nora" in kr_norm)
            or ("preguntas" in kr_norm and ("reunion" in kr_norm or "reunión" in kr_norm))
            or ("recordatorio" in kr_norm or "recuerdame" in kr_norm or "recuérdame" in kr_norm)
        )

        if has_numbered_multi and has_karen_multi_content:
            reply = (
                "Veo varias instrucciones juntas, Insanity 😌📌\n\n"
                "Te las separo para que no se vuelva sopa de letras legal:\n\n"
                "1️⃣ Paquete para Nora: puedo prepararlo.\n"
                "2️⃣ Preguntas principales para la reunión: puedo sacarlas del paquete.\n"
                "3️⃣ Recordatorio para la cita: necesito la hora exacta de la cita para calcular “una hora antes”.\n\n"
                "Mándame una de estas ahora:\n"
                "• “Val, prepárame el paquete para Nora”\n"
                "• “Val, dame las preguntas principales para Nora”\n"
                "• “Val, la cita es hoy a las 3:00 pm, recuérdame una hora antes preparar documentos”\n\n"
                "Una por una, y yo las voy ejecutando sin hacer malabares con machetes. 😏"
            )
            await update.message.reply_text(reply)
            return

        # 1A-1) Richer Agenda List v0:
        # "qué tengo en agenda" / "mi agenda" / "próximas citas"
        agenda_summary_markers = (
            "que tengo en agenda",
            "qué tengo en agenda",
            "mi agenda",
            "muestrame mi agenda",
            "muéstrame mi agenda",
            "proximas citas",
            "próximas citas",
            "agenda interna",
        )

        if any(m in kr_norm for m in agenda_summary_markers):
            if await try_agenda_summary_natural(update, chat_id, text):
                return

        # 1A0) Anchored Reminder Before Appointment v0:
        # "recuérdame una hora antes de la cita con Nora"
        anchored_reminder_markers = (
            "recuerdame",
            "recuérdame",
            "recordarme",
            "recordatorio",
        )

        if any(m in kr_norm for m in anchored_reminder_markers) and "antes de" in kr_norm and "cita" in kr_norm:
            if await try_anchored_reminder_before_appointment_natural(update, chat_id, text):
                return

        # 1A) Natural Appointment Save v0:
        # Must run before legacy Karen appointment/case-note handler.
        appointment_save_markers = (
            "tengo cita",
            "tengo una cita",
            "cita con",
            "registra cita",
            "registrar cita",
            "guarda cita",
            "guardar cita",
            "agenda cita",
            "agendar cita",
            "programa cita",
            "programar cita",
            "reunion con",
            "reunión con",
            "tengo reunion",
            "tengo reunión",
            "crea evento",
            "crear evento",
            "google calendar",
            "pon en mi calendario",
            "pon en el calendario",
            "agrega al calendario",
            "agregar al calendario",
            "agregala al calendario",
            "agrégala al calendario",
        )

        if any(m in kr_norm for m in appointment_save_markers):
            if await try_appointment_save_natural(update, chat_id, text):
                return

        # 1B) Direct agenda window shield:
        # "Val que tengo hoy" / "qué tengo mañana" / "qué tengo esta semana"
        # must hit agenda/due gates before document inventory can hijack it.
        agenda_direct_markers = (
            "que tengo hoy",
            "que tengo para hoy",
            "tengo para hoy",
            "que hay hoy",
            "que hay para hoy",
            "que debo hacer hoy",
            "que tengo manana",
            "que tengo para manana",
            "tengo para manana",
            "que tengo mañana",
            "que tengo para mañana",
            "tengo para mañana",
            "que hay manana",
            "que hay para manana",
            "que hay mañana",
            "que hay para mañana",
            "que tengo esta semana",
            "que tengo para esta semana",
            "tengo para esta semana",
            "que hay para esta semana",
        )

        if any(m == kr_norm for m in agenda_direct_markers):
            if "esta semana" in kr_norm:
                reply = build_client_agenda_dashboard(client_id, chat_id, "week")
            elif "manana" in kr_norm or "mañana" in kr_norm:
                reply = build_client_agenda_dashboard(client_id, chat_id, "tomorrow")
            else:
                reply = build_client_agenda_dashboard(client_id, chat_id, "today")

            await update.message.reply_text(reply, disable_web_page_preview=True)
            return

        # 2) Reminder list / agenda query shield.
        reminder_list_markers = (
            "que tengo registrado como recordatorio",
            "qué tengo registrado como recordatorio",
            "que tengo en recordatorio",
            "qué tengo en recordatorio",
            "que recordatorios tengo",
            "qué recordatorios tengo",
            "dime mis recordatorios",
            "muestrame mis recordatorios",
            "muéstrame mis recordatorios",
        )

        if any(m in kr_norm for m in reminder_list_markers):
            await reminders_cmd(update, context)
            return

        agenda_query_markers = (
            "que tengo en agenda",
            "qué tengo en agenda",
            "dime que tengo en agenda",
            "dime qué tengo en agenda",
            "mi agenda",
        )

        if any(m in kr_norm for m in agenda_query_markers):
            voc = client_vocative(client_id)
            reply = (
                f"Claro{voc} 😌📅\n\n"
                "Para agenda puedo revisar por ventana de tiempo. Dime una de estas:\n\n"
                "• “Val, ¿qué tengo hoy?”\n"
                "• “Val, ¿qué tengo mañana?”\n"
                "• “Val, ¿qué tengo esta semana?”\n\n"
                "Así no mezclo agenda real con el novelón del terreno, porque ahí es donde el caos se pone creativo. 😏"
            )
            await update.message.reply_text(reply)
            return

        # 3) Relative reminder shield:
        # "recuérdame una hora antes..." needs a real appointment time.
        # If no explicit anchor hour exists, ask for it before document/case gates hijack it.
        reminder_prefixes = (
            "recuerdame",
            "recuérdame",
            "recordarme",
            "recordatorio",
        )
        relative_before_markers = (
            "una hora antes",
            "1 hora antes",
            "una hora antes de",
            "1 hora antes de",
        )
        has_explicit_clock = bool(re.search(r"\b(?:a las|a la)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", kr_norm))

        if (
            any(p in kr_norm for p in reminder_prefixes)
            and any(m in kr_norm for m in relative_before_markers)
            and not has_explicit_clock
        ):
            voc = client_vocative(client_id)
            reply = (
                f"Sí, puedo hacerlo{voc} ⏰📁\n\n"
                "Pero necesito la hora exacta de la cita para calcular “una hora antes”. "
                "Todavía no voy a adivinar horarios como bruja de feria, gracias. 😌\n\n"
                "Mándamelo así:\n"
                "“Val, la cita es hoy a las 3:00 pm, recuérdame una hora antes preparar documentos.”"
            )
            await update.message.reply_text(reply)
            return

    except Exception as e:
        logger.exception(f"[KAREN_REMINDER_AGENDA_SHIELD] failed: {e}")

    # --------------------------------------------------
    # Karen / Nora attorney-prep priority gate
    # Must beat generic document summary.
    # --------------------------------------------------
    try:
        if looks_like_karen_meeting_prep_request(text):
            await update.message.reply_text(render_karen_meeting_prep_checklist(text))
            return
    except Exception as e:
        logger.exception(f"[KAREN_MEETING_PREP_PRIORITY_GATE] failed: {e}")

    try:
        nora_norm = _norm_text(text or "")
        nora_context = (
            "nora" in nora_norm
            or "abogada" in nora_norm
            or "abogado" in nora_norm
        )
        nora_intent_markers = (
            "preparame un resumen",
            "prepárame un resumen",
            "resumen claro",
            "llevarle esto",
            "que me falta revisar",
            "qué me falta revisar",
            "que falta revisar",
            "qué falta revisar",
            "que me falta conseguir",
            "qué me falta conseguir",
            "que falta conseguir",
            "qué falta conseguir",
            "antes de hablar",
            "paquete para nora",
            "paquete para la abogada",
        )

        if nora_context and any(m in nora_norm for m in nora_intent_markers):
            missing_review_markers = (
                "que me falta revisar",
                "qué me falta revisar",
                "que falta revisar",
                "qué falta revisar",
                "que me falta conseguir",
                "qué me falta conseguir",
                "que falta conseguir",
                "qué falta conseguir",
                "antes de hablar",
            )
            package_markers = (
                "paquete para nora",
                "paquete para la abogada",
                "preparame un resumen",
                "prepárame un resumen",
                "resumen claro",
                "llevarle esto",
            )

            if any(m in nora_norm for m in missing_review_markers) and not any(m in nora_norm for m in package_markers):
                await update.message.reply_text(render_karen_missing_review_checklist())
                return

            from core.karen_lawyer_package import render_lawyer_package
            await _reply_text_chunked(update, render_lawyer_package(int(chat_id)))
            return
    except Exception as e:
        logger.exception(f"[KAREN_NORA_PREP_PRIORITY_GATE] failed: {e}")

    try:
        if await maybe_handle_document_alias_save_query(update, context, chat_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_DOCUMENT_ALIAS_SAVE_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_latest_document_status_query(update, context, chat_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_LATEST_DOCUMENT_STATUS_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_document_naming_metadata_query(update, context, chat_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_DOCUMENT_NAMING_METADATA_PIPELINE] failed: {e}")

    try:
        if await maybe_handle_document_ocr_query(update, context, chat_id, text):
            _maybe_log_intent_router_v2_actual("document_ocr", "maybe_handle_document_ocr_query", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_DOCUMENT_OCR_PIPELINE] failed: {e}")

    # --------------------------------------------------
    # Karen/VFMS Document Summary Priority Gate
    # Explicit VFMS/document-summary requests must beat generic memory,
    # follow-up, recent-activity, and guided-flow handlers.
    # Example: "Resumen VFMS 20260511_000012"
    # --------------------------------------------------
    try:
        priority_doc_norm = (text or "").lower()
        priority_doc_markers = (
            "vfms",
            "dame el resumen de",
            "dame resumen de",
            "hazme resumen de",
            "resume con ocr",
            "resumen con ocr",
            "haz ocr",
            "lee visualmente",
            "transcribe este documento",
            "transcribe el documento que acabo de subir",
            "haz un resumen",
            "resume el documento",
            "resume el pdf",
            "resume este documento",
            "resume el último documento",
            "resume el ultimo documento",
            "documento que acabo de subir",
            "resumen del documento",
            "resumen de documento",
            "resumen de documentos",
            "tabla cronológica",
            "tabla cronologica",
            "ficha legal",
            "datos registrales",
        )
        if any(m in priority_doc_norm for m in priority_doc_markers):
            if await maybe_handle_document_summary_query(update, context, chat_id, text):
                _maybe_log_intent_router_v2_actual("document_summary", "maybe_handle_document_summary_query", chat_id=chat_id, message_id=tg_msg_id, text=text)
                return
    except Exception as e:
        logger.exception(f"[KAREN_VFMS_PRIORITY_SUMMARY_GATE] failed: {e}")

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

    # --------------------------------------------------
    # Reminder Priority Gate
    # Must run before Karen appointment/case gates so "Val, recuérdame..."
    # creates a real reminder instead of becoming case status/appointment memory.
    # --------------------------------------------------
    try:
        if await handle_reminder_gate(update, chat_id, text, _audit):
            _maybe_log_intent_router_v2_actual("reminder_create", "handle_reminder_gate", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[REMINDER_PRIORITY_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Pasted Transcript Guard gate
    # If a Karen guided flow is active and user pastes a long transcript/log,
    # ask before consuming it as the current answer.
    # --------------------------------------------------
    try:
        if await maybe_handle_pending_transcript_choice(update, context, text):
            return
        if await maybe_guard_pasted_transcript(update, context, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_TRANSCRIPT_GUARD_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Appointment / Reschedule gate
    # Captures natural cita/reunión/cambio de cita before generic reminders/case handlers.
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_appointment(update, context, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_APPOINTMENT_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Recent Case Activity gate
    # Captures "registra este evento..." and answers "últimos eventos/datos compartidos"
    # before generic facts/status handlers hijack the request.
    # --------------------------------------------------
    try:
        if await maybe_capture_karen_case_event(update, context, text):
            return
        if await maybe_handle_karen_recent_events_summary(update, context, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_RECENT_ACTIVITY_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Natural Document Inventory start gate
    # "inventario de documentos" should start Karen inventory, not generic ChatGPT template mode.
    # --------------------------------------------------
    try:
        inv_norm = _norm_text(text or "")
        if inv_norm in {
            "inventario de documentos",
            "empezar inventario de documentos",
            "iniciar inventario de documentos",
            "hagamos inventario de documentos",
            "hacer inventario de documentos",
        }:
            await start_document_inventory(update, context)
            return
    except Exception as e:
        logger.exception(f"[KAREN_NATURAL_INVENTORY_START] failed: {e}")

    # --------------------------------------------------
    # Karen Interrogator handle_text gate
    # Must run before unified memory/task capture so "hay que..."
    # answers are not stolen by task creation.
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_interrogator(update, context, chat_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_INTERROGATOR_HANDLE_TEXT_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Document Inventory active-answer gate
    # If document inventory is active, it must consume the answer
    # before document lookup/summary/semantic query handlers steal it.
    # --------------------------------------------------
    try:
        if await maybe_handle_document_inventory(update, context, chat_id, text):
            return

        if await maybe_handle_document_alias_save_query(update, context, chat_id, text):
            return

        if await maybe_handle_latest_document_status_query(update, context, chat_id, text):
            return

        if await maybe_handle_document_naming_metadata_query(update, context, chat_id, text):
            return

        if await maybe_handle_document_ocr_query(update, context, chat_id, text):
            _maybe_log_intent_router_v2_actual("document_ocr", "maybe_handle_document_ocr_query", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return

        if await maybe_handle_document_query(update, context, chat_id, text):
            return

        if await maybe_handle_karen_case_timeline_query(update, context, chat_id, client_id, text):
            return

        if await maybe_handle_document_summary_query(update, context, chat_id, text):
            _maybe_log_intent_router_v2_actual("document_summary", "maybe_handle_document_summary_query", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return

        if await maybe_handle_document_semantic_query(update, context, chat_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_DOCUMENT_INVENTORY_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Case Facts query gate
    # Direct questions like "dame la finca" or "quiénes son los herederos"
    # must answer from case facts before generic status/time/chat handlers.
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_case_facts(update, context, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_CASE_FACTS_QUERY_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Case Status query gate
    # Lets natural questions like "¿Qué tengo del caso del terreno?"
    # retrieve Karen LandOps case memory before generic handlers.
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_case_status(update, context, text):
            _maybe_log_intent_router_v2_actual("case_status", "maybe_handle_karen_case_status", chat_id=chat_id, message_id=tg_msg_id, text=text)
            return
    except Exception as e:
        logger.exception(f"[KAREN_CASE_STATUS_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Lawyer Package query gate
    # Lets natural phrases like "prepara paquete para abogado"
    # generate the attorney-ready case package before generic handlers.
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_lawyer_package(update, context, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_LAWYER_PACKAGE_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Pending Next Action gate
    # Lets short confirmations like OK / dale / sí continue
    # the suggested next workflow.
    # --------------------------------------------------
    try:
        if await maybe_handle_pending_next_action(update, context, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_PENDING_NEXT_ACTION_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Plan State query gate
    # Must run before unified memory/task capture so "qué falta" etc.
    # does not become a fake task.
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_plan_query(update, context, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_PLAN_STATE_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Lawyer Questions gate
    # Must run before unified memory/task capture so lawyer prep phrases
    # do not become generic notes/tasks.
    # --------------------------------------------------
    try:
        if await maybe_handle_karen_lawyer_questions(update, context, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_LAWYER_QUESTIONS_GATE] failed: {e}")

    # --------------------------------------------------
    # Karen Case Facts passive capture gate
    # If user pastes registry/basic case data, save it into CASE:KAREN-LAND-001.
    # --------------------------------------------------
    try:
        if await maybe_capture_karen_case_facts(update, context, chat_id, text):
            return
    except Exception as e:
        logger.exception(f"[KAREN_CASE_FACTS_CAPTURE_GATE] failed: {e}")

    # --------------------------------------------------
    # Pending bug/feedback/idea report (hard gate before unified memory/task capture)
    # --------------------------------------------------
    try:
        if await handle_pending_bug_report(update, int(chat_id), text):
            return
    except Exception as e:
        logger.exception(f"[PENDING_REPORT_MEMORY_GATE] failed: {e}")

    # Store text input in unified memory layer
    try:
        from memory_store import insert_memory_item, classify_memory_item

        if text and not text.startswith("/"):
            bucket, summary = classify_memory_item(text, source="text")

            # --- HARD TASK OVERRIDE (critical for reliability) ---
            text_low = (text or "").lower()
            is_query_not_task = _is_user_query_not_task(text)

            force_task = (
                _is_commitment_capture_allowed(text)
                and any(x in text_low for x in [
                    "tengo que",
                    "i need to",
                    "i have to",
                    "debo",
                    "must",
                ])
            )

            if force_task:
                bucket = "task"
                summary = "task_forced"

            logger.info(
                f"[MEMORY_TEST_TEXT] inserting memory for chat_id={chat_id}: "
                f"bucket={bucket} summary={summary} text={text}"
            )

            # HARD EXCLUSION: natural idea phrases must never become tasks/commitments.
            try:
                _idea_norm = _norm_text(text or "")
                _idea_prefixes = (
                    "tengo una idea",
                    "idea:",
                    "se me ocurrio",
                    "se me ocurrió",
                )
                if any(_idea_norm.startswith(pfx) for pfx in _idea_prefixes):
                    bucket = "idea"
                    summary = "natural_idea"
            except Exception:
                pass

            insert_memory_item(
                chat_id=int(chat_id),
                bucket=bucket,
                raw_input=text,
                summary=summary
            )

            if bucket == "task" and not _is_commitment_capture_allowed(text):
                logger.info(f"[COMMITMENT_GUARD] blocked task capture for text={text!r}")
                bucket = "memory"
                summary = "blocked_task_like_query_or_reminder"

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

                try:
                    await update.message.reply_text(
                        f"Listo. Guardé la tarea:\n{commitment['raw_input']}"
                    )
                    return
                except Exception:
                    pass
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

    # KAREN HANDLE_TEXT CAPABILITIES GUARD
    # This must run before maybe_handle_document_query(), because document query
    # was hijacking "Val, qué puedes hacer hoy?" and returning CASE documents.
    try:
        ht_norm = _norm_text(text or "").strip()
        ht_norm = re.sub(r"^val\s+", "", ht_norm).strip()

        ht_capability_markers = (
            "que puedes hacer hoy",
            "qué puedes hacer hoy",
            "que puedes hacer",
            "qué puedes hacer",
            "que sabes hacer",
            "qué sabes hacer",
            "como me puedes ayudar",
            "cómo me puedes ayudar",
            "capacidades",
        )

        if any(m in ht_norm for m in ht_capability_markers):
            from core.client_context_reader import render_client_context_answer
            reply = render_client_context_answer(text or "", client_id=client_id)
            if reply:
                await update.message.reply_text(reply)
                return
    except Exception as e:
        logger.exception(f"[KAREN_HANDLE_TEXT_CAPABILITIES_GUARD] failed: {e}")

    try:
        doc_summary_norm = _norm_text(text or "")
        if (
            "dame el resumen de" in doc_summary_norm
            or "dame resumen de" in doc_summary_norm
            or "hazme resumen de" in doc_summary_norm
            or "resume el documento" in doc_summary_norm
            or "resume el pdf" in doc_summary_norm
            or "resumen de " in doc_summary_norm
        ):
            if await maybe_handle_document_summary_query(update, context, chat_id, text):
                return
    except Exception as e:
        logger.exception(f"[KAREN_HANDLE_TEXT_SPECIFIC_DOC_SUMMARY] failed: {e}")

    if await maybe_handle_document_query(update, context, chat_id, text):
        return

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

def _tts_text_sanitize(t: str) -> str:
    t = (t or "").strip()
    # keep it short-ish for driving; tweak via env
    max_chars = int(os.getenv("VAL0_TTS_MAX_CHARS", "900"))
    if len(t) > max_chars:
        t = t[:max_chars].rstrip() + "…"
    return t

def _prepare_tts_text(t: str) -> str:
    """
    Final TTS shaping for Spanish replies.
    Keeps one single authoritative prep path.
    """
    import re

    t = _tts_text_sanitize(t)

    # Piper struggles with inverted punctuation
    t = t.replace("¿", "").replace("¡", "")

    # Force digit-by-digit pronunciation
    t = re.sub(r"\d+", lambda m: " ".join(m.group(0)), t)

    # Add light pause shaping
    t = t.replace(". ", ".  ")
    t = t.replace(", ", ",  ")
    t = t.replace("? ", "?  ")

    # Softer ending question hint
    if t.endswith("?"):
        t = t[:-1] + " ?"

    return t.strip()

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

    async def _persist_assistant_reply(sent_obj=None):
        try:
            telegram_message_id = None
            if sent_obj is not None and hasattr(sent_obj, "message_id"):
                telegram_message_id = int(sent_obj.message_id)

            if chat_id is not None:
                insert_message(
                    int(chat_id),
                    "assistant",
                    reply,
                    telegram_message_id=telegram_message_id,
                    model_used="val0",
                )
                trim_messages_for_chat(int(chat_id), keep_last=12)
        except Exception as e:
            logger.exception(f"[SESSION_MEMORY_OUTBOUND] failed: {e}")

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

    # Voice reply path remains disabled globally for founder-beta safety.
    # Test-only override: /voice test forces exactly one short TTS reply.
    force_tts_once = False
    try:
        key = f"force_tts_once:{int(chat_id)}"
        force_tts_once = bool(context.bot_data.pop(key, False))
    except Exception:
        force_tts_once = False

    if force_tts_once and _tts_enabled():
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
                sent = await msg.reply_text(reply)
                await _persist_assistant_reply(sent)
                return sent

            # Quick ACK before TTS so the user does not think Val0 froze
            try:
                await msg.reply_text("🎙️ Te escuché. Estoy preparando la respuesta en voz...")
            except Exception:
                pass

            tmp_dir = os.getenv("VAL0_TMP_DIR", "/opt/val0/tmp")
            os.makedirs(tmp_dir, exist_ok=True)

            # Light punctuation tuning so Piper breathes a bit
            t = (reply or "").strip()

            # --- Case/expediente digits: force digit-by-digit for clarity ---
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
            t = t.replace("...", ".")
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

                await _persist_assistant_reply(sent)
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
            sent = await msg.reply_text(reply)
            await _persist_assistant_reply(sent)
            return sent

    # TEXT PATH
    _audit_out(reply)
    sent = await msg.reply_text(reply)
    await _persist_assistant_reply(sent)
    return sent
async def voice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /voice on|off|status
    """
    from memory_store import get_chat_voice_enabled, set_chat_voice_enabled

    msg = update.effective_message
    chat = update.effective_chat
    chat_id = chat.id if chat else None

    if chat_id is None or msg is None:
        return

    parts = (msg.text or "").strip().split()
    mode = parts[1].lower() if len(parts) >= 2 else "status"

    if mode in ("on", "1", "yes", "enable", "enabled"):
        set_chat_voice_enabled(int(chat_id), True)
        await msg.reply_text("🎧 Modo voz: activado. Te responderé con audio cuando tenga sentido.")
        return

    if mode == "test":
        set_chat_voice_enabled(int(chat_id), True)
        context.bot_data[f"force_tts_once:{int(chat_id)}"] = True
        return await _send_reply(update, context, "Prueba corta de voz desde Valeria.")

    if mode in ("off", "0", "no", "disable", "disabled"):
        set_chat_voice_enabled(int(chat_id), False)
        await msg.reply_text("🛑 Modo voz: desactivado. Vuelvo a texto normal.")
        return

    on = get_chat_voice_enabled(int(chat_id))
    await msg.reply_text(
        f"🎧 Modo voz: {'activado' if on else 'desactivado'}"
    )

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


def _is_user_query_not_task(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False

    query_markers = (
        "que tengo",
        "qué tengo",
        "que debo hacer",
        "qué debo hacer",
        "que hago",
        "qué hago",
        "que hay",
        "qué hay",
        "cuales son",
        "cuáles son",
        "mis pendientes",
        "mis tareas",
    )

    return t.endswith("?") or any(m in t for m in query_markers)


async def tasks_cmd(update, context):
    if not update or not update.effective_chat or not update.message:
        return

    chat_id = update.effective_chat.id

    try:
        from memory_store import fetch_open_commitments

        rows = fetch_open_commitments(int(chat_id), limit=10)

        if not rows:
            await update.message.reply_text("No tienes tareas abiertas para este chat.")
            return

        lines = ["Tareas abiertas:"]
        for idx, r in enumerate(rows, start=1):
            row = dict(r) if hasattr(r, "keys") else r
            raw = str(row["raw_input"] if isinstance(row, dict) else row[1]).strip()
            due = str(row["due_date"] if isinstance(row, dict) else row[4] or "").strip()
            if due:
                lines.append(f"{idx}. {raw} ({due})")
            else:
                lines.append(f"{idx}. {raw}")

        await update.message.reply_text("\n".join(lines))

    except Exception as e:
        logger.exception(f"[TASKS_CMD] failed: {e}")
        await update.message.reply_text("No pude leer tus tareas ahora mismo.")

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
        lines.append("🧭 Estado de Valeria")
        lines.append("")
        lines.append(f"✅ Sistema: activo")
        lines.append("🧠 Memoria: ok")
        lines.append("")
        lines.append(f"📌 Tareas abiertas: {open_tasks}")

        if open_task_lines:
            lines.extend(open_task_lines)
        else:
            lines.append("- No tienes tareas abiertas.")

        lines.append("")
        lines.append("Puedes probar:")
        lines.append("• Guarda esta nota: comprar leche")
        lines.append("• Recuérdame llamar mañana a las 9")
        lines.append("• ¿Qué tengo mañana?")
        lines.append("• Estoy perdida, ¿qué hago?")

        lines.append("")
        lines.append("Siguiente paso: dime una nota, tarea o recordatorio.")

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

    try:
        app.job_queue.run_repeating(
            _reminder_tick,
            interval=interval,
            first=5,
            name=REMINDER_JOB_NAME,
        )
        logger.info(f"[REMINDER_RUNNER] scheduled {REMINDER_JOB_NAME} interval={interval}s")
    except Exception as e:
        logger.exception(f"[REMINDER_RUNNER] failed to schedule {REMINDER_JOB_NAME}: {e}")

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
    from core.control import help_cmd
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ops", ops_cmd))
    app.add_handler(CommandHandler("health", health_cmd))
    app.add_handler(CommandHandler("reminders", reminders_cmd))
    #app.add_handler(CommandHandler("cancel", rmd_cmd))
    app.add_handler(CommandHandler("rmd", rmd_cmd))
    app.add_handler(CommandHandler("route", route_cmd))
    app.add_handler(CommandHandler("classify", classify_cmd))
    app.add_handler(CommandHandler("draftfollowup", draftfollowup_cmd))
    app.add_handler(CommandHandler("whatnow", whatnow_cmd))
    app.add_handler(CommandHandler("exosummary", exosummary_cmd))
    app.add_handler(CommandHandler("exorecent", exorecent_cmd))
    app.add_handler(CommandHandler("onboard", onboard_cmd))
    app.add_handler(CommandHandler("flowrequest", flowrequest_cmd))
    app.add_handler(CommandHandler("interrogate", interrogate_cmd))
    app.add_handler(CommandHandler("karenplan", karen_plan_cmd))
    app.add_handler(CommandHandler("karencase", karen_case_status_cmd))
    app.add_handler(CommandHandler("lawyerpackage", karen_lawyer_package_cmd))
    app.add_handler(CommandHandler("lawyerquestions", karen_lawyer_questions_cmd))
    app.add_handler(CallbackQueryHandler(karen_next_action_callback, pattern=r"^karen:"))
    app.add_handler(CommandHandler("onboardstatus", onboard_status_cmd))
    app.add_handler(CommandHandler("journal", journal_cmd))
    app.add_handler(CommandHandler("exotest", exotest_cmd))
    app.add_handler(CommandHandler("memory", memory_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("tasks", tasks_cmd))
    app.add_handler(CommandHandler("note", note_cmd))
    app.add_handler(CommandHandler("notes", notes_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("context", context_cmd))
    app.add_handler(CommandHandler("focus", focus_cmd))
    app.add_handler(CommandHandler("showfocus", showfocus_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("cancelreport", cancelreport_cmd))

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
    app.add_handler(CommandHandler("bug", bug_cmd))
    app.add_handler(CommandHandler("feedback", feedback_cmd))
    app.add_handler(CommandHandler("idea", idea_cmd))
    app.add_handler(CommandHandler("reports", reports_cmd))
    app.add_handler(CommandHandler("mem", handle_mem))

    
    app.add_handler(CommandHandler("remember", handle_remember))


    app.add_handler(CommandHandler("sremember", sremember_cmd))
    app.add_handler(CommandHandler("ssearch", ssearch_cmd))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_attachment))

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
            await update.message.reply_text("No tienes recordatorios pendientes.")
            return

        from datetime import datetime
        from zoneinfo import ZoneInfo

        tz = ZoneInfo("America/Panama")

        lines = [f"Tienes {len(rows)} recordatorio(s) pendiente(s):"]
        for r in rows:
            rid = r.get("id")
            due = (r.get("due_at_utc") or "").strip()
            st = (r.get("status") or "").strip()
            txt = (r.get("text") or "").replace("\n", " ").strip()

            if len(txt) > 70:
                txt = txt[:70] + "…"

            due_local = due
            try:
                from datetime import timezone
                due_dt_utc = datetime.strptime(due, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                due_local = due_dt_utc.astimezone(tz).strftime("%Y-%m-%d %I:%M %p")
            except Exception:
                pass

            lines.append(f"#{rid} · {due_local} · {st}")
            lines.append(f"  {txt}")

        lines.append("")
        lines.append("Para cancelar uno: /rmd <id>")

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
        await update.message.reply_text("Uso: /rmd <id>\nEjemplo: /rmd 27")
        return

    try:
        rid = int(parts[1])
    except Exception:
        await update.message.reply_text("Ese id no parece válido.\nEjemplo: /rmd 27")
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
            await update.message.reply_text(f"Listo. Cancelé el recordatorio #{rid}.")
        else:
            await update.message.reply_text("No pude cancelarlo. Puede que no exista, no sea tuyo, o ya se haya enviado.")
    except Exception as e:
        logger.exception(f"rmd_cmd failed: {e}")
        await update.message.reply_text("Se cayó la cancelación. Intenta otra vez.")


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
