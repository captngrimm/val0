import time
import os
import logging
import unicodedata
import re
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
import openai

from telegram import Update
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
    user_text: str,
    context_block: Optional[str] = None,
    facts_block: Optional[str] = None,
    semantic_block: Optional[str] = None,
    forced_lang: Optional[str] = None,
) -> str:
    try:
        messages = [{"role": "system", "content": VAL_SYSTEM_PROMPT}]

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
                        "=== MEMORIA SEMÁNTICA (READ-ONLY / ASISTIVA) ===\n"
                        "Estos son fragmentos previos proporcionados por el Boss (pueden estar incompletos).\n"
                        "Trátalos como pistas, no como hechos verificados.\n"
                        "- Úsala SOLO si es claramente relevante al mensaje actual.\n"
                        "- NUNCA cambies de tema por algo leído aquí.\n"
                        "- NO la cites, NO la repitas, NO la enumeres.\n"
                        "- NO edites ni “corrijas” estos fragmentos (solo apoyo).\n"
                        "- Si hay duda o ambigüedad, PREGUNTA al Boss para confirmar.\n"
                        "— BEGIN SNIPPETS (READ-ONLY) —\n"
                        + semantic_block
                        + "\n— END SNIPPETS —"
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

    try:
        file = await context.bot.get_file(file_id)
        tmp_dir = "/opt/val0/tmp"
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(tmp_dir, f"voice_{chat_id}_{tg_msg_id}.ogg")
        await file.download_to_drive(tmp_path)
    except Exception as e:
        logger.exception(f"Failed to download voice file from Telegram: {e}")
        await update.message.reply_text("No pude descargar ese mensaje de voz, Boss. Intenta de nuevo.")
        return

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
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
        await update.message.reply_text("No entendí nada claro en ese audio, Boss. Intenta de nuevo o mándalo por texto.")
        return

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

    Precision hardening:
    - Keeps existing length/control gating unchanged (handled by caller).
    - Does NOT change memory write behavior.
    - Filters candidate hits with a lightweight lexical relevance check to reduce noisy/off-topic recalls.
    """
    try:
        sem = _get_semantic()
        hits = sem.search(query=query, k=k) or []

        # Chat isolation (only memories from this chat)
        candidates = []
        for h in hits:
            if not isinstance(h, dict):
                continue
            meta = h.get("meta", {}) or {}
            if str(meta.get("chat_id", "")) != str(chat_id):
                continue

            txt = (meta.get("text") or "").strip()
            if not txt:
                continue

            score = h.get("score", None)
            candidates.append({"text": txt, "score": score})

        if not candidates:
            return ""

        # --- lexical relevance filter (score-agnostic, reduces off-topic recalls) ---
        def _tok(s: str):
            s = _norm_text(s or "")
            # Keep words with letters/numbers, strip punctuation-ish
            raw = re.findall(r"[a-z0-9]+", s)
            # Drop tiny tokens and common stopwords (ES+EN)
            stop = {
                "a","an","and","are","as","at","be","but","by","do","does","did","for","from","how","i","if","in","is","it",
                "me","my","of","on","or","so","that","the","this","to","was","were","what","when","where","who","why","you",
                "your","yours","we","our","ours","they","their","them","he","she","him","her","its",
                "el","la","los","las","un","una","unos","unas","y","o","de","del","al","por","para","con","sin","que","como",
                "cuando","donde","quien","quienes","cual","cuales","mi","mis","tu","tus","su","sus","yo","me","te","se","es",
                "son","era","fue","ser","estar","estoy","estas","esta","estaba","estaban","en","lo","le","les","ya","si",
                "no","pero","porque","porq","pq","muy","mas","menos","tambien","también","aqui","aquí","ahi","ahí",
            }
            out = []
            for w in raw:
                if len(w) < 3:
                    continue
                if w in stop:
                    continue
                out.append(w)
            return set(out)

        q_tokens = _tok(query)
        if q_tokens:
            filtered = []
            seen = set()
            for c in candidates:
                t = c["text"]
                if t in seen:
                    continue
                seen.add(t)

                t_tokens = _tok(t)
                # Require at least one meaningful shared token OR substring match on tokens
                if (q_tokens & t_tokens):
                    filtered.append(c)
                    continue
                # Substring fallback (handles compounds / short queries)
                t_norm = _norm_text(t)
                if any(tok in t_norm for tok in q_tokens):
                    filtered.append(c)

            candidates = filtered

        if not candidates:
            return ""

        # Cap returned snippets (higher precision, less noise)
        MAX_SNIPPETS = 3

        lines = []
        for c in candidates[:MAX_SNIPPETS]:
            txt = c["text"]
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

        sent = await update.message.reply_text(reply)
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
        sent = await update.message.reply_text(reply)
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
        sent = await update.message.reply_text(reply)
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
        sent = await update.message.reply_text(reply)
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
        sent = await update.message.reply_text(reply)
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
        sent = await update.message.reply_text(reply)
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

    reply = call_val_openai(
        text,
        context_block=context_block,
        facts_block=facts_block,
        semantic_block=semantic_block,
        forced_lang=preferred_language,
    )

    sent = await update.message.reply_text(reply)
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
# Text handler
# --------------------------------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await _process_text_pipeline(update, context, update.message.text.strip())


# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    init_db()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).defaults(Defaults(parse_mode=None)).build()
    app.add_error_handler(_error_handler)

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("memory", memory_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("note", note_cmd))
    app.add_handler(CommandHandler("notes", notes_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("place", place_cmd))
    app.add_handler(CommandHandler("sremember", sremember_cmd))
    app.add_handler(CommandHandler("ssearch", ssearch_cmd))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
