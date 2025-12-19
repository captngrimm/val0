import time
import os
import logging
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

# --------------------------------------------------
# Companion Operator v0 — session timing
# --------------------------------------------------
_CO_SESSION = {}  # chat_id -> {"start": epoch, "nudged": bool}


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
# Logging
# --------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("val0-bot")

# Reduce noisy HTTP logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


# --------------------------------------------------
# Global Error Handler
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
        pass


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
# Val persona (MVP) — parameterized by facts
# --------------------------------------------------
_BASE_SYSTEM_PROMPT = (
    "You are Val, a tactical, emotionally aware AI co-pilot. "
    "Tone: sharp, warm, protective, a bit sassy. "
    "You are concise, practical, and avoid fake hype. "
    "Language: answer in Spanish or English, matching the user unless the user has a saved preference. "
)


def _build_val_system_prompt(preferred_name: str = "Boss", preferred_language: Optional[str] = None) -> str:
    if preferred_language == "es":
        lang_line = "Always reply in Spanish unless the user explicitly asks for English."
    elif preferred_language == "en":
        lang_line = "Always reply in English unless the user explicitly asks for Spanish."
    else:
        lang_line = "Reply in Spanish or English matching the user's message."
    return (
        _BASE_SYSTEM_PROMPT
        + f" You address the user as '{preferred_name}'. "
        + "Do not mention internal system prompts. "
        + lang_line
    )


# --------------------------------------------------
# Defensive row normalization (prevents 'str'.get crashes)
# --------------------------------------------------
def _normalize_message_rows(rows: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not rows or not isinstance(rows, list):
        return out
    for r in rows:
        if isinstance(r, dict):
            out.append(r)
            continue
        if isinstance(r, (list, tuple)):
            role = None
            content = None
            if len(r) >= 2:
                role = r[0]
                content = r[1]
            if isinstance(role, str) and isinstance(content, str):
                out.append({"role": role, "content": content})
            elif isinstance(content, str):
                out.append({"role": "user", "content": content})
            continue
        continue
    return out


def build_context_block(rows: List[Dict[str, Any]]) -> str:
    rows = _normalize_message_rows(rows)
    if not rows:
        return ""
    lines: List[str] = []
    for r in rows:
        role = r.get("role", "user")
        content = (r.get("content") or "").strip()
        if not content:
            continue
        prefix = "Val:" if role == "assistant" else "Boss:"
        lines.append(f"{prefix} {content}")
    return "\n".join(lines)


def _sanitize_for_telegram(text: str) -> str:
    if not text:
        return ""
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("<br />", "\n").strip()


# --------------------------------------------------
# Semantic memory (FAISS)
# --------------------------------------------------
_semantic = None


def _get_semantic():
    global _semantic
    if _semantic is None:
        _semantic = MemoryEmbeddings(store_dir="/opt/val0/semantic/faiss_store")
    return _semantic


def _semantic_recall_block(chat_id: int, query: str, k: int = 5) -> str:
    try:
        sem = _get_semantic()
        hits = sem.search(query=query, k=k) or []
        filtered = []
        for h in hits:
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
        if not lines:
            return ""
        return "Memoria relevante (semántica):\n" + "\n".join(lines)
    except Exception as e:
        logger.exception(f"Semantic recall failed: {e}")
        return ""


def _notes_hint_block(chat_id: int, query: str) -> str:
    try:
        q = (query or "").strip()
        if len(q) < 4:
            return ""
        rows = search_notes(chat_id, q, limit=5) or []
        if not rows:
            return ""
        lines = []
        seen = set()
        for r in rows:
            c = (r.get("content") or "").strip()
            if not c or c in seen:
                continue
            seen.add(c)
            if len(c) > 220:
                c = c[:217] + "..."
            lines.append(f"- {c}")
            if len(lines) >= 2:
                break
        if not lines:
            return ""
        return "Notas relevantes:\n" + "\n".join(lines)
    except Exception as e:
        logger.exception(f"Notes hint failed: {e}")
        return ""


# --------------------------------------------------
# OpenAI call
# --------------------------------------------------
def call_val_openai(
    user_text: str,
    preferred_name: str = "Boss",
    preferred_language: Optional[str] = None,
    context_block: Optional[str] = None,
    facts_block: Optional[str] = None,
    semantic_block: Optional[str] = None,
    notes_block: Optional[str] = None,
) -> str:
    try:
        messages = [{"role": "system", "content": _build_val_system_prompt(preferred_name, preferred_language)}]

        if facts_block:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Datos persistentes sobre el usuario (memoria de largo plazo). "
                        "Úsalos como hechos. No inventes.\n" + facts_block
                    ),
                }
            )

        if semantic_block:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Recuerdos relevantes recuperados (semántica). "
                        "Úsalos solo si aplican a la pregunta actual.\n" + semantic_block
                    ),
                }
            )

        if notes_block:
            messages.append({"role": "system", "content": "Pistas desde notas del usuario:\n" + notes_block})

        if context_block:
            messages.append(
                {
                    "role": "system",
                    "content": "Contexto reciente (no lo repitas; úsalo para continuidad):\n" + context_block,
                }
            )

        messages.append({"role": "user", "content": user_text})

        resp = openai.ChatCompletion.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.7,
        )
        out = resp["choices"][0]["message"]["content"]
        return _sanitize_for_telegram(out)
    except Exception as e:
        logger.exception(f"OpenAI call failed: {e}")
        return "Algo se rompió hablando con el modelo. Intenta otra vez en un momento."


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
    lowered = text.lower().strip()
    triggers = [
        "háblame en",
        "hablame en",
        "prefiero que me hables en",
        "quiero que me hables en",
        "my preferred language is",
        "i prefer you speak in",
    ]
    if not any(lowered.startswith(t) for t in triggers):
        return None
    if "español" in lowered or "spanish" in lowered:
        return "es"
    if "inglés" in lowered or "ingles" in lowered or "english" in lowered:
        return "en"
    return None


def extract_preferred_name(text: str) -> Optional[str]:
    original = text.strip()
    lowered = original.lower()
    triggers = [
        "quiero que me llames ",
        "quiero que me llame ",
        "llámame ",
        "llamame ",
        "puedes llamarme ",
        "call me ",
        "you can call me ",
    ]
    for t in triggers:
        if lowered.startswith(t):
            tail = original[len(t):].strip()
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


def _places_query_from_text(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    low = t.lower()
    if ("panama" not in low) and ("panamá" not in low):
        t = f"{t}, Panama"
    return t


def _reply_language(text: str) -> str:
    t = (text or "").lower()
    spanish_markers = ["á", "é", "í", "ó", "ú", "ñ", "cerca", "dónde", "donde", "recom", "busca", "encuentra", "panamá"]
    return "es" if any(m in t for m in spanish_markers) else "en"


# ✅ FIX: Places detection must require INTENT, not just category words.
def _looks_like_places_request(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False

    # intent markers: user is asking to find/recommend/locate something
    intent_markers_es = [
        "cerca", "cerca de", "busca", "búsc", "buscame", "búscame", "encuentra",
        "dónde", "donde", "recom", "recomiénd", "recomiend", "queda", "ubicación", "ubicacion"
    ]
    intent_markers_en = [
        "near", "near me", "find", "search", "where", "recommend", "location", "closest"
    ]

    # category words (do NOT trigger on these alone)
    category_words = [
        "café", "cafe", "coffee", "restaurant", "restaurante", "pizza", "pizzería", "pizzeria",
        "farmacia", "pharmacy", "hotel", "bar", "gym", "gimnasio", "dentista", "dentist",
        "clínica", "clinica", "clinic", "hospital", "atm", "cajero", "mall", "centro comercial"
    ]

    has_intent = any(m in t for m in intent_markers_es) or any(m in t for m in intent_markers_en)
    has_category = any(w in t for w in category_words)

    # Only trigger if BOTH: intent + category/context.
    return bool(has_intent and has_category)


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
        await update.message.reply_text("La nota estaba vacía o algo raro pasó. Intenta de nuevo con más detalle.")
        return
    await update.message.reply_text(f"Listo. Guardé la nota #{note_id}:\n{text}")


async def notes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rows = get_notes(chat_id, limit=20)
    if not rows:
        await update.message.reply_text("Todavía no tienes notas guardadas. Usa /note algo que quieras recordar.")
        return
    lines = ["Notas guardadas (más recientes primero):"]
    for idx, r in enumerate(rows, start=1):
        content = (r.get("content") or "").strip()
        if len(content) > 200:
            content = content[:197] + "..."
        lines.append(f"{idx}. #{r.get('id')} - {content}")
    await update.message.reply_text("\n".join(lines))


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("Dime qué quieres buscar en tus notas. Ejemplo:\n/search dentista")
        return
    rows = search_notes(chat_id, query, limit=20)
    if not rows:
        await update.message.reply_text(f"No encontré notas que contengan '{query}'.")
        return
    seen_contents = set()
    lines = [f"Notas que contienen '{query}' (más recientes primero):"]
    for r in rows:
        content = (r.get("content") or "").strip()
        if content in seen_contents:
            continue
        seen_contents.add(content)
        if len(content) > 200:
            content = content[:197] + "..."
        lines.append(f"- #{r.get('id')} - {content}")
    await update.message.reply_text("\n".join(lines))


async def place_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("Dime qué buscar. Ejemplo:\n/place dentista panama")
        return
    results = places_search(query, limit=5)
    if isinstance(results, dict) and "error" in results:
        await update.message.reply_text(f"Error buscando lugares: {results['error']}")
        return
    if not results:
        await update.message.reply_text("No encontré nada con esa búsqueda.")
        return

    safe_results = [r for r in results if isinstance(r, dict)]
    lines = []
    for r in safe_results:
        name = r.get("name", "Sin nombre")
        addr = r.get("address", "Sin dirección")
        rating = r.get("rating", "N/A")
        place_id = r.get("place_id", "")
        lines.append(f"📍 {name}\n{addr}\n⭐ {rating}\n{place_id}\n")

    await update.message.reply_text("\n".join(lines), parse_mode=None)


# --------------------------------------------------
# Voice handler (Whisper)
# --------------------------------------------------
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice:
        return

    chat_id = update.effective_chat.id
    tg_msg_id = update.message.message_id
    voice = update.message.voice
    file_id = voice.file_id

    logger.info(f"voice msg chat_id={chat_id}: duration={voice.duration}s file_id={file_id}")

    try:
        file = await context.bot.get_file(file_id)
        tmp_dir = "/opt/val0/tmp"
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(tmp_dir, f"voice_{chat_id}_{tg_msg_id}.ogg")
        await file.download_to_drive(tmp_path)
    except Exception as e:
        logger.exception(f"Failed to download voice file from Telegram: {e}")
        await update.message.reply_text("No pude descargar ese mensaje de voz. Intenta de nuevo.")
        return

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcribed_text = (transcript.get("text") or "").strip()
    except Exception as e:
        logger.exception(f"Whisper transcription failed: {e}")
        await update.message.reply_text("No pude transcribir ese audio. Intenta con texto o mándalo de nuevo.")
        return
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as e:
            logger.exception(f"Failed to remove tmp voice file {tmp_path}: {e}")

    if not transcribed_text:
        await update.message.reply_text("No entendí el audio. Intenta de nuevo o mándalo por texto.")
        return

    await _process_text_pipeline(update, context, transcribed_text)


# --------------------------------------------------
# Core Message Pipeline
# --------------------------------------------------
async def _process_text_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if not update.message:
        return

    chat_id = update.effective_chat.id
    tg_msg_id = update.message.message_id
    logger.info(f"msg from chat_id={chat_id}: {text!r}")

    # Store user msg
    try:
        insert_message(chat_id=chat_id, role="user", content=text, telegram_message_id=tg_msg_id, model_used=None)
    except Exception as e:
        logger.exception(f"Failed to insert user message into DB: {e}")

    # Load facts EARLY so all paths (including Places) use preferred_name
    try:
        facts = get_all_facts(chat_id=chat_id) or {}
    except Exception as e:
        logger.exception(f"Failed to fetch user facts from DB: {e}")
        facts = {}

    preferred_name = (facts.get("preferred_name") or "Boss") if isinstance(facts, dict) else "Boss"
    preferred_language = (facts.get("preferred_language") or None) if isinstance(facts, dict) else None

    # CO1 nudge
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

    # Color memory question
    if is_color_memory_question(text):
        try:
            stored = get_fact(chat_id=chat_id, fact_key="favorite_color")
        except Exception as e:
            logger.exception(f"Failed to read favorite_color fact: {e}")
            stored = None

        if stored:
            reply = f"Claro, {preferred_name}, tu color favorito es {stored}."
        else:
            reply = f"Todavía no me has dicho claramente tu color favorito, {preferred_name}. Dímelo con: 'mi color favorito es ...'."

        sent = await update.message.reply_text(reply)
        try:
            insert_message(chat_id=chat_id, role="assistant", content=reply, telegram_message_id=sent.message_id, model_used="gpt-4.1-mini")
        except Exception as e:
            logger.exception(f"Failed to insert assistant message into DB: {e}")
        return

    # Favorite color setter
    fav = extract_favorite_color(text)
    if fav:
        try:
            upsert_fact(chat_id=chat_id, fact_key="favorite_color", fact_value=fav)
        except Exception as e:
            logger.exception(f"Failed to upsert favorite_color: {e}")
        reply = f"Queda registrado, {preferred_name}: tu color favorito ahora es {fav}."
        sent = await update.message.reply_text(reply)
        try:
            insert_message(chat_id=chat_id, role="assistant", content=reply, telegram_message_id=sent.message_id, model_used="gpt-4.1-mini")
        except Exception as e:
            logger.exception(f"Failed to insert assistant message into DB: {e}")
        return

    # Main goal setter
    goal = extract_main_goal(text)
    if goal:
        try:
            upsert_fact(chat_id=chat_id, fact_key="main_goal", fact_value=goal)
        except Exception as e:
            logger.exception(f"Failed to upsert main_goal: {e}")
        reply = f"Queda registrado, {preferred_name}: tu objetivo principal ahora es '{goal}'."
        sent = await update.message.reply_text(reply)
        try:
            insert_message(chat_id=chat_id, role="assistant", content=reply, telegram_message_id=sent.message_id, model_used="gpt-4.1-mini")
        except Exception as e:
            logger.exception(f"Failed to insert assistant message into DB: {e}")
        return

    # Preferred language setter
    lang = extract_preferred_language(text)
    if lang:
        try:
            upsert_fact(chat_id=chat_id, fact_key="preferred_language", fact_value=lang)
        except Exception as e:
            logger.exception(f"Failed to upsert preferred_language: {e}")
        human = "español" if lang == "es" else "inglés"
        reply = f"Listo, {preferred_name}: a partir de ahora prefieres que te hable en {human}."
        sent = await update.message.reply_text(reply)
        try:
            insert_message(chat_id=chat_id, role="assistant", content=reply, telegram_message_id=sent.message_id, model_used="gpt-4.1-mini")
        except Exception as e:
            logger.exception(f"Failed to insert assistant message into DB: {e}")
        return

    # Preferred name setter
    nm = extract_preferred_name(text)
    if nm:
        try:
            upsert_fact(chat_id=chat_id, fact_key="preferred_name", fact_value=nm)
        except Exception as e:
            logger.exception(f"Failed to upsert preferred_name: {e}")
        reply = f"Perfecto. A partir de ahora te voy a llamar {nm}."
        sent = await update.message.reply_text(reply)
        try:
            insert_message(chat_id=chat_id, role="assistant", content=reply, telegram_message_id=sent.message_id, model_used="gpt-4.1-mini")
        except Exception as e:
            logger.exception(f"Failed to insert assistant message into DB: {e}")
        return

    # Natural-language note
    note = extract_freeform_note(text)
    if note:
        try:
            note_id = add_note(chat_id, note)
        except Exception as e:
            logger.exception(f"Failed to insert natural note: {e}")
            await update.message.reply_text(f"Quise guardar esa nota pero algo falló, {preferred_name}.")
            return

        if note_id <= 0:
            await update.message.reply_text(f"La nota quedó vacía, {preferred_name}. Dímela con más detalle.")
            return

        reply = f"Listo, {preferred_name}. Guardé la nota #{note_id}:\n{note}"
        sent = await update.message.reply_text(reply)
        try:
            insert_message(chat_id=chat_id, role="assistant", content=reply, telegram_message_id=sent.message_id, model_used="gpt-4.1-mini")
        except Exception as e:
            logger.exception(f"Failed to insert assistant message into DB: {e}")
        return

    # Number-to-details (Places)
    if text.isdigit():
        sel = int(text)
        sess = _places_session_get(chat_id)
        if sess and 1 <= sel <= 5:
            if int(time.time()) - int(sess.get("ts", 0)) <= 600:
                results = sess.get("results") or []
                idx = sel - 1
                if idx < len(results):
                    raw = results[idx]
                    pid = raw.get("place_id") if isinstance(raw, dict) else None
                    if pid:
                        d = place_details(pid)
                        if isinstance(d, dict) and d.get("error"):
                            await update.message.reply_text(f"Se cayó el detalle del lugar, {preferred_name}.")
                            return

                        name = (d.get("name") or "?") if isinstance(d, dict) else "?"
                        addr = (d.get("address") or "") if isinstance(d, dict) else ""
                        phone = (d.get("phone") or "") if isinstance(d, dict) else ""
                        rating = d.get("rating") if isinstance(d, dict) else None
                        website = (d.get("website") or "") if isinstance(d, dict) else ""
                        maps_url = (d.get("maps_url") or "") if isinstance(d, dict) else ""
                        if not maps_url and isinstance(raw, dict):
                            maps_url = raw.get("maps_url") or ""

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

                        await update.message.reply_text("\n".join(parts), parse_mode=None, disable_web_page_preview=True)
                        return

    # Natural language → Google Places (fixed intent gate)
    if _looks_like_places_request(text):
        q = _places_query_from_text(text)
        try:
            results = places_search(q, limit=5)
        except Exception as e:
            logger.exception(f"Places search failed: {e}")
            await update.message.reply_text(f"Se cayó la búsqueda de lugares, {preferred_name}. Intenta otra vez en un minuto.")
            return

        if isinstance(results, list):
            safe = [r for r in results if isinstance(r, dict)]
            _places_session_set(chat_id, safe)
            results = safe

        if not results:
            await update.message.reply_text(f"No encontré resultados, {preferred_name}. Prueba con más detalle (tipo + zona).")
            return

        lang2 = _reply_language(text)
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

        header = f"Aquí tienes, {preferred_name}:" if lang2 == "es" else f"Here you go, {preferred_name}:"
        footer = "\n\nResponde con un número (1–5) para ver detalles." if lang2 == "es" else "\n\nReply with a number (1–5) to see details."
        await update.message.reply_text(header + "\n\n" + "\n\n".join(lines) + footer, parse_mode=None, disable_web_page_preview=True)
        return

    # LLM path (smarter recall)
    try:
        recent = get_recent_messages(chat_id=chat_id, limit=12)
    except Exception as e:
        logger.exception(f"Failed to fetch recent messages: {e}")
        recent = []

    context_block = build_context_block(recent)

    facts_block = ""
    if isinstance(facts, dict) and facts:
        facts_block = "\n".join([f"{k}: {v}" for k, v in facts.items()])

    semantic_block = _semantic_recall_block(chat_id=chat_id, query=text, k=5)
    notes_block = _notes_hint_block(chat_id=chat_id, query=text)

    reply = call_val_openai(
        text,
        preferred_name=preferred_name,
        preferred_language=preferred_language,
        context_block=context_block,
        facts_block=facts_block,
        semantic_block=semantic_block,
        notes_block=notes_block,
    )

    sent = await update.message.reply_text(reply)
    try:
        insert_message(chat_id=chat_id, role="assistant", content=reply, telegram_message_id=sent.message_id, model_used="gpt-4.1-mini")
    except Exception as e:
        logger.exception(f"Failed to insert assistant message: {e}")


# --------------------------------------------------
# Semantic Memory Commands (FAISS)
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
            meta={"chat_id": str(chat_id), "ts": int(time.time()), "source": "telegram"},
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
        hits = [h for h in hits if str(h.get("meta", {}).get("chat_id", "")) == str(chat_id)]
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("memory", memory_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("note", note_cmd))
    app.add_handler(CommandHandler("notes", notes_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("place", place_cmd))
    app.add_handler(CommandHandler("sremember", sremember_cmd))
    app.add_handler(CommandHandler("ssearch", ssearch_cmd))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
