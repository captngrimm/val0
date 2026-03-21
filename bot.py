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

# === CORE DB ACCESS (must ALWAYS exist) ===
from memory_store import _get_conn

# === CORE DB ACCESS (must ALWAYS exist) ===
from memory_store import _get_conn

# === MODE HANDLER (must ALWAYS exist if referenced later) ===
from core.mode import try_set_mode

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
import pytz
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
_PENDING_TERM_CONFIRM = {}
_PENDING_CASE_DISAMBIG = {}
_PENDING_REMINDER_CONFIRM = {}
# --- last action tracker (demo-safe undo) ---
_LAST_ACTION = {}
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
        "situacion actual del caso",
        "situación actual del caso",
        "por donde va el caso",
        "por dónde va el caso",
        "que tienes del caso",
        "qué tienes del caso",
        "dame todo del caso",
        "ver caso",
        "ver expediente",
        "info del caso",
        "informacion del caso",
        "información del caso",
        "casos sin movimiento",
        "resumen de trabajo",
        "que debo hacer",
        "qué debo hacer",
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

        await update.message.reply_text(
            f"📝 Guardé esto como nota en CASE:{case_id} ({client_name})."
        )
        return True

    except Exception as e:
        logger.exception(f"[NATURAL_NOTE] insert failed: {e}")
        return False

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

    text = _strip_smalltalk_prefix(text)
    tg_msg_id = update.message.message_id
    logger.info(f"msg from chat_id={chat_id}: {text!r}")

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

    # --------------------------------------------------
    # Pending reminder confirmation
    # --------------------------------------------------
    try:
        if int(chat_id) in _PENDING_REMINDER_CONFIRM:
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

                from memory_store import insert_case_event

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
                    return

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

                _LAST_ACTION[int(chat_id)] = {
                    "type": "reminder_insert",
                    "id": event_id,
                    "case_id": str(pending["case_id"]),
                }

                from core.case_summary import refresh_case_summary
                refresh_case_summary(int(chat_id), str(pending["case_id"]))

                await update.message.reply_text(
                    f"⏰ Recordatorio registrado en CASE:{pending['case_id']}\n"
                    f"Fecha: {pending['due_date']}"
                )
                return

            if confirm_low in confirm_no:
                _PENDING_REMINDER_CONFIRM.pop(int(chat_id), None)
                await update.message.reply_text("Entendido. No lo registré.")
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
                    f"Listo, Boss. Registré CASE:{expediente} para cliente {client_name}."
                )
                return

    except Exception as e:
        logger.exception(f"[CASE_REGISTER_CMD] failed: {e}")

    # --------------------------------------------------
    # Case note command — deterministic
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

                _LAST_ACTION[int(chat_id)] = {
                    "type": "note_insert",
                    "id": note_id,
                    "case_id": str(case_id),
                }

                from core.case_summary import refresh_case_summary
                refresh_case_summary(int(chat_id), str(case_id))

                await update.message.reply_text(f"Listo, Boss. Guardé la nota en CASE:{case_id}.")
                return

    except Exception as e:
        logger.exception(f"[CASE_NOTE_CMD] failed: {e}")

    # --------------------------------------------------
    # NATURAL REMINDER DETECTION (suggestion only, no write)
    # --------------------------------------------------
    try:
        low = (text or "").lower()

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
                if len(matches) == 1:
                    case_id, client_name = matches[0]

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

                elif len(matches) > 1:
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

    except Exception as e:
        logger.exception(f"[NATURAL_REMINDER_DETECT] failed: {e}")

    # --------------------------------------------------
    # NATURAL TERM DETECTION (suggestion only, no write)
    # --------------------------------------------------
    try:
        low = (text or "").lower()
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

                if len(matches) == 1:
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

                elif len(matches) > 1:
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

    except Exception as e:
        logger.exception(f"[NATURAL_TERM_DETECT] failed: {e}")

    # --------------------------------------------------
    # Natural Note Capture v1 — AFTER term detection
    # --------------------------------------------------
    case_note_handled = await _maybe_capture_case_note(update, chat_id, text, source="text")
    if case_note_handled:
        return

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
            try_terms_due_tomorrow,
            try_cases_due_this_week,
        )
        from core.control import try_debug_mode, try_help
        from core.case_reports import (
            try_idle_cases,
            try_daily_work_summary,
            try_priority_dashboard,
        )

        HANDLERS = [
            try_debug_mode,
            try_help,
            try_undo_last_action,
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
            try_terms_due_tomorrow,
            try_terms_due_this_week,
            try_due_range,
        ]

        for handler in HANDLERS:
            if await handler(update, chat_id, text):
                return

        text_lower = (text or "").lower().strip()
        if "caso" in text_lower and "casos" not in text_lower:
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

    t = (text or "").strip().lower()

    patterns = [
        r"^\s*qué\s+vence\s+mañana\s*$",
        r"^\s*que\s+vence\s+mañana\s*$",
        r"^\s*qué\s+t[eé]rminos\s+vencen\s+mañana\s*$",
        r"^\s*que\s+terminos\s+vencen\s+mañana\s*$",
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

    patterns = [
        r"^que tengo mañana$",
        r"^qué tengo mañana$",
        r"^que tengo manana$",
        r"^qué audiencias tengo mañana$",
        r"^que audiencias tengo mañana$",
    ]

    for p in patterns:
        if re.match(p, t):
            tz = ZoneInfo("America/Panama")
            tomorrow = (datetime.now(tz) + timedelta(days=1)).date().isoformat()

            out = _generate_morning_brief_det(int(chat_id), tomorrow)

            if not out:
                tz = ZoneInfo("America/Panama")
                tomorrow_dt = datetime.now(tz) + timedelta(days=1)

                weekday = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][tomorrow_dt.weekday()]
                month = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"][tomorrow_dt.month]

                pretty = f"{weekday} {tomorrow_dt.day} {month}"

                out = f"📅 Mañana ({pretty})\n\n— No tengo nada agendado —"

            await update.message.reply_text(out)
            return True

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

# --------------------------------------------------
# Text handler
# --------------------------------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.message and update.message.text):
        return

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
    app.add_handler(CommandHandler("semana", semana_cmd))
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