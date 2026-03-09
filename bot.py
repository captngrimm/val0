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

# --- MIGUEL MVP: gates wiring (do not remove) ---
try:
    from core.case_mvp import try_case_summary, try_due_today, try_due_range  # preferred
    from core.ops_cmds import ops_cmd, health_cmd, reminders_cmd, rmd_cmd
except Exception:
    pass
    # Fallback stubs: keep bot stable even if module isn't present yet

import os
import logging
import unicodedata
import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from datetime import time as dt_time
from dotenv import load_dotenv
import openai
import re

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

    fetch_due_reminders,
    claim_due_reminders,
    claim_reminder,
    mark_reminder_sent,
    mark_reminder_failed,
    revert_reminder_pending,
)

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
    """
    Deterministic deadline extractor for Sprint08.
    Supports:
    - vence hoy
    - vence mañana
    - vence el YYYY-MM-DD
    Returns ISO date string or "".
    """
    import re
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    if not text:
        return ""

    t = text.strip().lower()

    tz = ZoneInfo("America/Panama")
    today = datetime.now(tz).date()

    if "vence hoy" in t or "audiencia hoy" in t:
        return today.isoformat()

    if (
        "vence mañana" in t
        or "vence manana" in t
        or "audiencia mañana" in t
        or "audiencia manana" in t
    ):
        return (today + timedelta(days=1)).isoformat()

    m = re.search(r"vence\s+el\s+(\d{4}-\d{2}-\d{2})", t)
    if m:
        return m.group(1)

    return ""

async def _maybe_capture_case_note(update, chat_id: int, text: str, source: str):
    """
    Phase B0 behavior:
    - If text contains an expediente/case number => set as active case
    - If there is an active case => store the note to case_notes
    - If text clearly contains a deadline phrase => also create a case_event
    """
    try:
        from memory_store import (
            get_active_case_id,
            set_active_case_id,
            insert_case_note,
            insert_case_event,
            _get_conn,
        )
    except Exception:
        return False

    tg_msg_id = None
    try:
        if update and getattr(update, "message", None):
            tg_msg_id = int(update.message.message_id)
    except Exception:
        tg_msg_id = None

    raw_text = str(text or "").strip()
    if not raw_text:
        return False

    low = raw_text.lower()

    # Do NOT store case status / summary queries as notes
    if (
        low.startswith("nota caso")
        or low.startswith("nota expediente")
        or low.startswith("cómo va el caso")
        or low.startswith("como va el caso")
        or low.startswith("cómo vamos con el caso")
        or low.startswith("como vamos con el caso")
        or low.startswith("por donde va el caso")
        or low.startswith("por dónde va el caso")
        or low.startswith("resumen del caso")
        or low.startswith("dame un resumen del caso")
        or low.startswith("estado del caso")
        or low.startswith("situacion actual del caso")
        or low.startswith("situación actual del caso")
    ):
        return False   

    found = _extract_case_id(raw_text)
    if found:
        set_active_case_id(int(chat_id), found)

    active = get_active_case_id(int(chat_id)) or found
    if not active:
        return False

    # Always capture note
    note_id = insert_case_note(
        chat_id=int(chat_id),
        case_id=str(active),
        note_text=raw_text,
        source=str(source or "text"),
        telegram_message_id=tg_msg_id,
    )
    logger.info(f"[CASE_NOTE] inserted id={note_id} case_id={active} source={source}")

    # Deterministic event capture (Sprint08 minimal scope)
    deadline_date = _extract_deadline_date(raw_text)
    if not deadline_date:
        return False

    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, expediente
            FROM cases
            WHERE chat_id=? AND lower(expediente)=lower(?)
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(chat_id), str(active)),
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            logger.warning(f"[CASE_EVENT] no case row found for expediente={active} chat_id={chat_id}")
            return False

        case_row_id = int(row["id"] if hasattr(row, "keys") else row[0])

        event_id = insert_case_event(
            chat_id=int(chat_id),
            case_id=case_row_id,
            event_text=raw_text,
            term_days=None,
            start_date=None,
            deadline_date=deadline_date,
            raw_text=raw_text,
            principal_id=None,
        )

        logger.info(
            f"[CASE_EVENT] inserted id={event_id} case_id={active} deadline_date={deadline_date} source={source}"
        )

        # --- Sprint09: conflict detection ---
        try:
            conn = _get_conn()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT ce.event_text, ce.deadline_date, c.expediente
                FROM case_events ce
                JOIN cases c ON c.id = ce.case_id
                WHERE ce.chat_id = ?
                AND ce.deadline_date = ?
                AND ce.id != ?
                ORDER BY ce.id ASC
                LIMIT 5
                """,
                (int(chat_id), deadline_date, int(event_id)),
            )

            conflicts = cur.fetchall()
            conn.close()

            if conflicts:
                lines = []
                for r in conflicts:
                    exp = r["expediente"] if hasattr(r, "keys") else r[2]
                    txt = r["event_text"] if hasattr(r, "keys") else r[0]
                    lines.append(f"• Expediente {exp} — {txt}")

                msg = (
                    f"⚠️ Boss, ya tienes otra diligencia ese mismo día ({deadline_date}):\n\n"
                    + "\n".join(lines)
                )

                await update.message.reply_text(msg)
                return True
        except Exception as e:
            logger.exception(f"[CASE_CONFLICT_CHECK] failed: {e}")

    except Exception as e:
        logger.exception(f"[CASE_EVENT] insert failed case_id={active} err={e}")

import asyncio

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
        msg = "Boss, algo se rompió procesando eso. Ya lo vi en los logs."

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
    "You talk to the user as 'Boss' unless the user asks otherwise. "
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
        prefix = "Val:" if role == "assistant" else "Boss:"
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
        messages = [{"role": "system", "content": VAL_SYSTEM_PROMPT}]
# Additional hard rules injected by pipeline (kept separate from VAL_SYSTEM_PROMPT)
        if system_rules:
            messages.append({"role": "system", "content": system_rules.strip()})


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
                    "content": "Datos persistentes sobre el Boss (memoria de largo plazo):\n" + facts_block,
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
                        "úsalo solo para recordar detalles del Boss):\n"
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
        return "Algo se rompió hablando con el modelo, Boss. Intenta otra vez en un momento."


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
        "hablame en",
        "prefiero que me hables en",
        "quiero que me hables en",
        "my preferred language is",
        "i prefer you speak in",
        "speak to me in",
        "talk to me in",
    ]
    if not any(norm.startswith(t) for t in triggers):
        return None

    if "espanol" in norm or "spanish" in norm:
        return "es"
    if "ingles" in norm or "english" in norm:
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
    await update.message.reply_text("Val-0 online. Ya puedo hablar contigo por aquí, Boss.")

async def memory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    facts = get_all_facts(chat_id)
    if not facts:
        await update.message.reply_text("Todavía no tengo datos persistentes guardados para este chat, Boss.")
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
            "Boss, dime qué nota quieres guardar. Ejemplo:\n"
            "/note pedir cita con el dentista el lunes"
        )
        return
    note_id = add_note(chat_id, text)
    if note_id <= 0:
        await update.message.reply_text(
            "La nota estaba vacía o algo raro pasó, Boss. Intenta de nuevo con más detalle."
        )
        return
    await update.message.reply_text(f"Listo, Boss. Guardé la nota #{note_id}:\n{text}")

async def notes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rows = get_notes(chat_id, limit=20)
    if not rows:
        await update.message.reply_text(
            "Todavía no tienes notas guardadas, Boss. Usa /note algo que quieras recordar."
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
            "Dime qué quieres buscar en tus notas, Boss. Ejemplo:\n"
            "/search dentista"
        )
        return
    rows = search_notes(chat_id, query, limit=20)
    if not rows:
        await update.message.reply_text(f"No encontré notas que contengan '{query}', Boss.")
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
            "Dime qué buscar, Boss. Ejemplo:\n"
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
        await update.message.reply_text("No encontré nada con esa búsqueda, Boss.")
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

    # Download voice to tmp
    tmp_dir = "/opt/val0/tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"voice_{chat_id}_{tg_msg_id}.ogg")

    try:
        file = await context.bot.get_file(file_id)
        await file.download_to_drive(tmp_path)
    except Exception as e:
        logger.exception(f"Failed to download voice file from Telegram: {e}")
        await update.message.reply_text(
            "No pude descargar ese mensaje de voz, Boss. Intenta de nuevo."
        )
        return

    # Transcribe (Whisper) + perf log
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
            "No pude transcribir ese audio con Whisper, Boss. Intenta con texto o mándalo de nuevo."
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

    # Capture note + continue normal pipeline
    await _maybe_capture_case_note(update, chat_id, transcribed_text, source="voice")
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


# --------------------------------------------------
# Core Message Pipeline
# --------------------------------------------------
async def _process_text_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if not update.message:
        return

    chat = update.effective_chat
    chat_id = chat.id

    # Preferred name (defaults)
    try:
        preferred_name = get_fact(chat_id=chat_id, fact_key="preferred_name") or "Boss"
    except Exception:
        preferred_name = "Boss"


    # Preferred language (hard enforcement for model replies)
    try:
        preferred_language = get_fact(chat_id=chat_id, fact_key="preferred_language")
        if preferred_language not in ("es", "en"):
            preferred_language = None
    except Exception:
        preferred_language = None

    # --------------------------------------------------
    # CO1 — Companion Operator timer nudge (1x per chat session)
    # Default: 3600s (1 hour). Override with CO1_NUDGE_SECONDS env.
    # --------------------------------------------------
    try:
        now = int(time.time())
        threshold = int(os.getenv("CO1_NUDGE_SECONDS", "3600"))
        sess = _CO_SESSION.get(int(chat_id))
        if not sess:
            _CO_SESSION[int(chat_id)] = {"start": now, "nudged": False}
        else:
            elapsed = now - int(sess.get("start", now))
            if elapsed >= threshold and not sess.get("nudged", False):
                _CO_SESSION[int(chat_id)]["nudged"] = True
                await update.message.reply_text(f"{preferred_name}: water + stretch for 30 seconds. 💧")
    except Exception:
        pass

    tg_msg_id = update.message.message_id
    logger.info(f"msg from chat_id={chat_id}: {text!r}")

    # --------------------------------------------------
    # Reminder Creator + Cancel (DM only) — deterministic
    # --------------------------------------------------
    try:
        from core.reminders_mvp import try_create_reminder, try_cancel_reminder

        _audit(
            chat_id,
            action="DEBUG_REMINDER_GATE_ENTER",
            entity_type="debug",
            entity_id=None,
            payload=(text or "")[:200],
            source="dm",
        )

        if int(chat_id) > 0:
            # Cancel FIRST (so "cancela 25" doesn't fall through)
            cancel_handled = await try_cancel_reminder(update, chat_id, text, audit_fn=_audit)
            logger.info(f"[REMINDER_GATE] cancel_handled={cancel_handled} text={text!r}")
            if cancel_handled:
                return

            create_handled = await try_create_reminder(update, chat_id, text, audit_fn=_audit)
            logger.info(f"[REMINDER_GATE] create_handled={create_handled} text={text!r}")
            if create_handled:
                return

    except Exception as e:
        logger.exception(f"[GATE] reminder gate failed: {e}")
    
    # --------------------------------------------------
    # Case note command — deterministic
    # Example:
    # nota caso 524242024: juez sugirió conciliación
    # --------------------------------------------------
    try:
        m = re.match(r"(?is)^\s*nota\s+(?:del\s+)?(?:caso|expediente)\s+(\d{4,})\s*:\s*(.+?)\s*$", text or "")
        if m:
            case_id = (m.group(1) or "").strip()
            note_text = (m.group(2) or "").strip()

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
                    action="CMD_CASE_NOTE_CREATE",
                    entity_type="case_note",
                    entity_id=str(note_id),
                    payload=f"case_id={case_id} | text={note_text}"[:500],
                    source="dm",
                )

                await update.message.reply_text(f"Listo, Boss. Guardé la nota en CASE:{case_id}.")
                return

    except Exception as e:
        logger.exception(f"[CASE_NOTE_CMD] failed: {e}")

    # --- Sprint10: court-day timeline queries ---
    try:
        from core.case_mvp import try_case_status, try_timeline_for_case, try_timeline_today, try_due_today, try_due_range, try_due_tomorrow

        handled = await try_case_status(update, chat_id, text)
        if handled:
            return
        handled = await try_timeline_for_case(update, chat_id, text)
        if handled:
            return

        handled = await try_timeline_today(update, chat_id, text)
        if handled:
            return

        handled = await try_due_today(update, chat_id, text)
        if handled:
            return

        handled = await try_due_tomorrow(update, chat_id, text)
        if handled:
            return

        handled = await try_due_range(update, chat_id, text)
        if handled:
            return

    except Exception as e:
        logger.exception(f"[CASE_TIMELINE] failed: {e}")

    case_note_handled = await _maybe_capture_case_note(update, chat_id, text, source="text")
    if case_note_handled:
        return
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

        # Confirm once, in the chosen primary language.
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
            upsert_fact(chat_id=chat_id, fact_key="preferred_name", fact_value=name)
        except Exception as e:
            logger.exception(f"Failed to upsert preferred_name: {e}")
        reply = f"Perfecto. A partir de ahora te voy a llamar {name}. Lo dejo anotado en memoria."
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
    # If the last reply was a Places list, user can respond with "1".."5"
    # --------------------------------------------------
    if text.isdigit():
        sel = int(text)
        sess = _places_session_get(chat_id)
        if sess and 1 <= sel <= 5:
            if int(time.time()) - int(sess.get("ts", 0)) <= 600:  # TTL 10 min
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

                        # HARDEN details too
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
    # Natural language → Google Places (fixed intent gate + control ack gate)
    # --------------------------------------------------
    if _is_places_intent(text) and _looks_like_places_request(text):
        q = _places_query_from_text(text)
        try:
            results = places_search(q, limit=5)
        except Exception as e:
            logger.exception(f"Places search failed: {e}")
            await update.message.reply_text(f"Se cayó la búsqueda de lugares, {preferred_name}. Intenta otra vez en un minuto.")
            return

        # Error object
        if isinstance(results, dict) and results.get("error"):
            await update.message.reply_text(f"Error buscando lugares, {preferred_name}: {results.get('error')}")
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
    # Reminder Creator + Cancel (DM only) — deterministic
    # --------------------------------------------------
    try:
        from core.reminders_mvp import try_create_reminder, try_cancel_reminder

        _audit(
            chat_id,
            action="DEBUG_REMINDER_GATE_ENTER",
            entity_type="debug",
            entity_id=None,
            payload=(text or "")[:200],
            source="dm",
        )

        if int(chat_id) > 0:
            # Cancel FIRST (so "cancela 25" doesn't fall through to model)
            if await try_cancel_reminder(update, chat_id, text, audit_fn=_audit):
                return
            if await try_create_reminder(update, chat_id, text, audit_fn=_audit):
                return

    except Exception as e:
        logger.exception(f"[GATE] reminder gate failed: {e}")

    # --------------------------------------------------
    # MIGUEL MVP — GATES (must run BEFORE model call)
    # --------------------------------------------------
    try:
        logger.info('[GATE] try_case_summary check')
        if await try_case_summary(update, chat_id, text):
            logger.info('[GATE] try_case_summary HIT (short-circuit)')
            return
    except Exception as e:
        logger.exception(f"[GATE] try_case_summary failed: {e}")

    try:
        logger.info('[GATE] try_due_today check')
        if await try_due_today(update, chat_id, text):
            logger.info('[GATE] try_due_today HIT (short-circuit)')
            return
    except Exception as e:
        logger.exception(f"[GATE] try_due_today failed: {e}")
    try:
        logger.info('[GATE] try_due_range check')
        if await try_due_range(update, chat_id, text):
            logger.info('[GATE] try_due_range HIT (short-circuit)')
            return
    except Exception as e:
        logger.exception(f"[GATE] try_due_range failed: {e}")


    # --------------------------------------------------
    # Load context + facts + semantic recall (C2) — with C3 gating
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

    # C3 gate: don't inject semantic memory for ultra-short / control chatter
    tclean = (text or "").strip()
    if len(tclean) < 8 or _is_control_ack(tclean):
        semantic_block = ""

    # HARD BLOCK: group chats are deterministic only (never call model)
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

    reply = call_val_openai(
        chat_id,
        text,
        context_block=context_block,
        facts_block=facts_block,
        semantic_block=semantic_block,
        forced_lang=preferred_language,
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
        user_text,
        context_block=context_block,
        facts_block=merged_facts,
        semantic_block=semantic_block,
        forced_lang=forced_lang,
    )
    return (out or "").strip()

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
            summary = _daily_auto_generate(chat_id=chat_id, date=date)
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

        await update.message.reply_text(f"Listo, Boss. Guardé el daily auto de {date} ✅\n\n{summary}")
        return

    # MANUAL MODE
    summary = arg
    ok, msg = upsert_daily_log(chat_id=chat_id, date=date, summary=summary)
    if not ok:
        await update.message.reply_text(f"No pude guardar el daily: {msg}")
        return

    await update.message.reply_text(f"Listo, Boss. Guardé el daily de {date} ✅")

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
    try:
        due = fetch_due_reminders(limit=_reminder_batch_limit())

        # tick telemetry for /health
        global _VAL0_LAST_TICK_TS, _VAL0_LAST_TICK_DUE
        _VAL0_LAST_TICK_TS = int(time.time())
        _VAL0_LAST_TICK_DUE = len(due)

        # Phase 1 ops hardening: throttle tick log to reduce noise (no behavior change)
        global _VAL0_LAST_TICK_LOG_TS
        now_ts = int(time.time())
        if _VAL0_LAST_TICK_LOG_TS is None or (now_ts - _VAL0_LAST_TICK_LOG_TS) >= 600:
            logger.info("ReminderRunner tick: due=%d", len(due))
            _VAL0_LAST_TICK_LOG_TS = now_ts
        if not due:
            return

        for r in due:
            rid = int(r.get("id"))
            chat_id = int(r.get("chat_id"))
            text = (r.get("text") or "").strip()

            # empty reminder text -> mark sent to avoid clogging
            if not text:
                if claim_reminder(rid):
                    mark_reminder_sent(rid)
                continue

            # claim the reminder first to prevent double-send
            if not claim_reminder(rid):
                continue

            try:
                await context.bot.send_message(chat_id=chat_id, text=text)
                mark_reminder_sent(rid)
                logger.info("ReminderRunner: sent id=%s chat_id=%s", rid, chat_id)
            except Exception as e:
                from telegram.error import Forbidden

                if isinstance(e, Forbidden):
                    logger.warning(
                        "ReminderRunner: user blocked bot id=%s chat_id=%s",
                        rid,
                        chat_id,
                    )
                    mark_reminder_failed(rid, reason="blocked")
                else:
                    logger.exception(
                        "ReminderRunner: send failed id=%s chat_id=%s err=%s",
                        rid,
                        chat_id,
                        e,
                    )
                    revert_reminder_pending(rid)
    except Exception as e:
        logger.exception("ReminderRunner tick crashed: %s", e)

async def evening_brief_tick(context):
    """
    Sends a short briefing for tomorrow.
    """
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo
    from memory_store import _get_conn
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

# --------------------------------------------------
# Text handler
# --------------------------------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        text = update.message.text.strip()
        chat_id = update.effective_chat.id
        tg_msg_id = getattr(update.message, "message_id", None)

        _audit(
            chat_id,
            action="IN_TEXT",
            entity_type="tg_msg",
            entity_id=str(tg_msg_id) if tg_msg_id is not None else None,
            payload=text[:500],
            source="group" if int(chat_id) < 0 else "dm",
        )

        if int(chat_id) < 0:
            return await _handle_group_deterministic(update, context, text)

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

    app.job_queue.run_repeating(
        _reminder_tick,
        interval=interval,
        first=10,
        name=REMINDER_JOB_NAME,
    )

    app.job_queue.run_daily(
        evening_brief_tick,
        time=dt_time(hour=21, minute=0),
        name="EVENING_BRIEF_JOB",
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
    app.add_handler(CommandHandler("dailies", dailies_cmd))
    app.add_handler(CommandHandler("dsearch", dsearch_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("place", place_cmd))
    # HOTFIX: temporarily disabled until voice_cmd is defined correctly
    app.add_handler(CommandHandler("voice", voice_cmd))

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
            await update.message.reply_text(f"Listo, Boss. Cancelado #{rid}.")
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