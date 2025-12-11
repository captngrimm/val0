import os
import logging
import json
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
import openai
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from memory_store import (
    init_db,
    insert_message,
    get_recent_messages,
    upsert_fact,
    get_fact,
    get_all_facts,
)

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("val0-bot")

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
# Persona config
# --------------------------------------------------
def _load_persona_config() -> Dict[str, Any]:
    """
    Load persona_config.json from disk.

    If the file is missing or invalid, fall back to safe defaults.
    """
    default = {
        "default_persona": {
            "name": "Val",
            "nickname": "Boss",
            "tone": "warm_sassy",
            "language": "auto",
            "cussing_level": "light",
            "humor_level": "medium",
            "slang_pack": "panama_core",
            "celebration_intensity": 2,
        }
    }
    cfg_path = "/opt/val0/persona_config.json"
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "default_persona" in data:
                    return data
                else:
                    logger.warning(
                        "persona_config.json is invalid structure, using defaults."
                    )
        else:
            logger.info("persona_config.json not found, using default persona config.")
    except Exception as e:
        logger.exception(f"Failed to load persona_config.json: {e}")
    return default


def _build_system_prompt(persona_cfg: Dict[str, Any]) -> str:
    """
    Build the base SYSTEM prompt string based on persona config.

    Language overrides per-chat are handled separately via lang_hint.
    """
    p = persona_cfg.get("default_persona", {})
    name = p.get("name", "Val")
    nickname = p.get("nickname", "Boss")
    language = p.get("language", "auto")

    base = (
        f"You are {name}, a tactical, emotionally aware AI co-pilot. "
        "Tone: sharp, warm, protective, a bit sassy. "
        f"You talk to the user as '{nickname}'. "
        "You are concise, practical, and avoid fake hype. "
    )

    # Default language behavior from config
    if language == "es":
        lang_part = "Language: always answer in Spanish. "
    elif language == "en":
        lang_part = "Language: always answer in English. "
    else:
        lang_part = "Language: answer in Spanish or English, matching the user. "

    return base + lang_part


_PERSONA_CONFIG = _load_persona_config()
VAL_SYSTEM_PROMPT = _build_system_prompt(_PERSONA_CONFIG)


def build_context_block(rows: List[Dict[str, Any]]) -> str:
    """Build a short text block from recent messages."""
    if not rows:
        return ""

    lines: List[str] = []
    for r in rows:
        role = r.get("role", "user")
        content = (r.get("content") or "").strip()
        if not content:
            continue
        if role == "assistant":
            prefix = "Val:"
        else:
            prefix = "Boss:"
        lines.append(f"{prefix} {content}")

    return "\n".join(lines)


# --------------------------------------------------
# OpenAI call (classic API) with context + facts + lang hint
# --------------------------------------------------
def call_val_openai(
    user_text: str,
    context_block: Optional[str] = None,
    facts_block: Optional[str] = None,
    lang_hint: Optional[str] = None,
) -> str:
    """
    Send a chat to OpenAI with Val's persona and optional:
    - facts_block: persistent structured memory (user_facts)
    - context_block: recent conversational context (messages)
    - lang_hint: 'es' or 'en' to override language behavior per chat
    """
    try:
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": VAL_SYSTEM_PROMPT},
        ]

        if lang_hint == "es":
            messages.append(
                {
                    "role": "system",
                    "content": "El usuario prefiere que siempre le hables en español.",
                }
            )
        elif lang_hint == "en":
            messages.append(
                {
                    "role": "system",
                    "content": "The user prefers that you always reply in English.",
                }
            )

        if facts_block:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Datos persistentes sobre el Boss (memoria de largo plazo):\n"
                        + facts_block
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
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception(f"OpenAI call failed: {e}")
        return (
            "Algo se rompió hablando con el modelo, Boss. "
            "Intenta otra vez en un momento."
        )


# --------------------------------------------------
# Simple NLP helpers for facts
# --------------------------------------------------
def extract_favorite_color(text: str) -> Optional[str]:
    """
    Try to extract a color name from phrases like:
    - 'mi color favorito es el azul oscuro'
    - 'mi color favorito ahora es el azul'
    - 'my favorite color is dark red'
    - 'my favorite color now is blue'
    Return the raw tail string, trimmed.

    IMPORTANT:
    Only treat as a setter if the phrase is at the beginning of the message.
    """
    lowered = text.lower()
    triggers = [
        "mi color favorito es",
        "mi color favorito ahora es",
        "my favorite color is",
        "my favorite color now is",
    ]
    for trig in triggers:
        if lowered.startswith(trig):
            idx = len(trig)
            tail = text[idx:].strip()
            # Strip common filler like 'el', 'la'
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
    """
    Try to extract the user's main goal from phrases like:
    - 'mi objetivo principal es ...'
    - 'mi objetivo es ...'
    - 'my main goal is ...'
    - 'my goal is ...'
    Return the tail string, trimmed.

    We also only treat this as a setter when the phrase is at the start.
    """
    lowered = text.lower()
    triggers = [
        "mi objetivo principal es",
        "mi objetivo es",
        "my main goal is",
        "my goal is",
    ]
    for trig in triggers:
        if lowered.startswith(trig):
            idx = len(trig)
            tail = text[idx:].strip()
            return tail or None
    return None


def extract_preferred_language(text: str) -> Optional[str]:
    """
    Extract preferred language from phrases at the start of the message.

    Examples:
    - 'háblame en español'
    - 'hablame en ingles'
    - 'prefiero que me hables en español'
    - 'my preferred language is english'

    Returns:
        'es' for Spanish
        'en' for English
        None if not clearly specified.
    """
    lowered = text.lower().strip()
    triggers = [
        "háblame en",
        "hablame en",
        "prefiero que me hables en",
        "quiero que me hables en",
        "my preferred language is",
        "i prefer you speak in",
    ]
    if not any(lowered.startswith(trig) for trig in triggers):
        return None

    if "español" in lowered or "spanish" in lowered:
        return "es"
    if "inglés" in lowered or "ingles" in lowered or "english" in lowered:
        return "en"
    return None


# --------------------------------------------------
# Telegram handlers
# --------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    logger.info(
        f"/start from user_id={user.id} chat_id={chat.id} username={user.username}"
    )
    await update.message.reply_text(
        "Val-0 online. Ya puedo hablar contigo por aquí, Boss."
    )


async def memory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show persistent facts stored for this chat."""
    user = update.effective_user
    chat = update.effective_chat
    chat_id = chat.id
    logger.info(f"/memory from user_id={user.id} chat_id={chat_id}")

    try:
        facts = get_all_facts(chat_id)
    except Exception as e:
        logger.exception(f"Failed to fetch user facts for /memory: {e}")
        await update.message.reply_text(
            "No pude leer la memoria persistente ahora mismo, Boss."
        )
        return

    if not facts:
        await update.message.reply_text(
            "Todavía no tengo datos persistentes guardados para este chat, Boss."
        )
        return

    lines = ["Memoria persistente para este chat:"]
    for k, v in facts.items():
        lines.append(f"- {k}: {v}")
    text_out = "\n".join(lines)
    await update.message.reply_text(text_out)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Basic health/status check for this chat."""
    user = update.effective_user
    chat = update.effective_chat
    chat_id = chat.id
    logger.info(f"/status from user_id={user.id} chat_id={chat_id}")

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


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat = update.effective_chat
    text = update.message.text.strip()
    user_id = user.id
    chat_id = chat.id
    tg_msg_id = update.message.message_id

    logger.info(f"msg from user_id={user_id} chat_id={chat_id}: {text!r}")

    # 1) STORE USER MESSAGE IMMEDIATELY
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

    # 1b) If the user is asking about favorite color memory, answer first
    # and do NOT treat this as a setter.
    if is_color_memory_question(text):
        stored_color: Optional[str] = None
        try:
            stored_color = get_fact(chat_id=chat_id, fact_key="favorite_color")
        except Exception as e:
            logger.exception(f"Failed to read favorite_color fact: {e}")

        if stored_color:
            reply_text = (
                f"Claro, Boss, tu color favorito es {stored_color}. "
                "Eso no se me olvida tan fácil."
            )
        else:
            reply_text = (
                "Todavía no me has dicho claramente cuál es tu color favorito, Boss. "
                "Dímelo con: 'mi color favorito es ...'."
            )

        sent = await update.message.reply_text(reply_text)
        try:
            insert_message(
                chat_id=chat_id,
                role="assistant",
                content=reply_text,
                telegram_message_id=sent.message_id,
                model_used="gpt-4.1-mini",
            )
        except Exception as e:
            logger.exception(f"Failed to insert assistant message into DB: {e}")
        return

    # 2) Structured fact: favorite color (only when explicitly set)
    fav_color = extract_favorite_color(text)
    if fav_color:
        try:
            upsert_fact(chat_id=chat_id, fact_key="favorite_color", fact_value=fav_color)
        except Exception as e:
            logger.exception(f"Failed to upsert favorite_color: {e}")

        # Reply in the language we know the user prefers, if any
        lang_for_reply = get_fact(chat_id=chat_id, fact_key="preferred_language")
        if lang_for_reply == "en":
            reply_text = (
                f"Noted, Boss: your favorite color just switched to {fav_color}. "
                "I’ve updated it in memory."
            )
        else:
            reply_text = (
                f"Queda registrado, Boss: tu color favorito ahora es {fav_color}. "
                "Lo tengo guardado."
            )

        sent = await update.message.reply_text(reply_text)
        # Store assistant reply
        try:
            insert_message(
                chat_id=chat_id,
                role="assistant",
                content=reply_text,
                telegram_message_id=sent.message_id,
                model_used="gpt-4.1-mini",
            )
        except Exception as e:
            logger.exception(f"Failed to insert assistant message into DB: {e}")
        return

    # 2b) Structured fact: main goal
    main_goal = extract_main_goal(text)
    if main_goal:
        try:
            upsert_fact(chat_id=chat_id, fact_key="main_goal", fact_value=main_goal)
        except Exception as e:
            logger.exception(f"Failed to upsert main_goal: {e}")

        reply_text = (
            "Queda registrado, Boss: tu objetivo principal ahora es: "
            f"'{main_goal}'. Lo tengo en memoria de largo plazo."
        )
        sent = await update.message.reply_text(reply_text)
        # Store assistant reply
        try:
            insert_message(
                chat_id=chat_id,
                role="assistant",
                content=reply_text,
                telegram_message_id=sent.message_id,
                model_used="gpt-4.1-mini",
            )
        except Exception as e:
            logger.exception(f"Failed to insert assistant message into DB: {e}")
        return

    # 2c) Structured fact: preferred language (setter)
    new_pref_lang = extract_preferred_language(text)
    if new_pref_lang:
        try:
            upsert_fact(
                chat_id=chat_id,
                fact_key="preferred_language",
                fact_value=new_pref_lang,
            )
        except Exception as e:
            logger.exception(f"Failed to upsert preferred_language: {e}")

        human_label = "español" if new_pref_lang == "es" else "inglés"
        reply_text = (
            f"Listo, Boss: a partir de ahora prefieres que te hable en {human_label}. "
            "Lo tengo guardado en memoria."
        )
        sent = await update.message.reply_text(reply_text)
        try:
            insert_message(
                chat_id=chat_id,
                role="assistant",
                content=reply_text,
                telegram_message_id=sent.message_id,
                model_used="gpt-4.1-mini",
            )
        except Exception as e:
            logger.exception(
                f"Failed to insert assistant message into DB (preferred_language): {e}"
            )
        return

    # 3) LOAD RECENT CONTEXT FOR THIS CHAT
    try:
        recent_rows = get_recent_messages(chat_id=chat_id, limit=12)
    except Exception as e:
        logger.exception(f"Failed to fetch recent messages from DB: {e}")
        recent_rows = []

    context_block = build_context_block(recent_rows)

    # 3b) LOAD STRUCTURED FACTS (PERSISTENT MEMORY) FOR THIS CHAT
    facts_block = ""
    try:
        facts = get_all_facts(chat_id=chat_id)
    except Exception as e:
        logger.exception(f"Failed to fetch user facts from DB: {e}")
        facts = {}

    if facts:
        fact_lines: List[str] = []
        for k, v in facts.items():
            fact_lines.append(f"{k}: {v}")
        facts_block = "\n".join(fact_lines)

    # Derive lang_hint from facts
    lang_hint = None
    if isinstance(facts, dict):
        pref = facts.get("preferred_language")
        if pref in ("es", "en"):
            lang_hint = pref

    # 4) CALL OPENAI WITH CONTEXT + FACTS + LANG HINT
    reply_text = call_val_openai(
        text,
        context_block=context_block,
        facts_block=facts_block,
        lang_hint=lang_hint,
    )

    # 5) SEND REPLY TO TELEGRAM
    sent = await update.message.reply_text(reply_text)

    # 6) STORE ASSISTANT MESSAGE AFTER SUCCESSFUL SEND
    try:
        insert_message(
            chat_id=chat_id,
            role="assistant",
            content=reply_text,
            telegram_message_id=sent.message_id,
            model_used="gpt-4.1-mini",
        )
    except Exception as e:
        logger.exception(f"Failed to insert assistant message into DB: {e}")


# --------------------------------------------------
# Main
# --------------------------------------------------
def main() -> None:
    logger.info("Initializing SQLite memory spine…")
    init_db()
    logger.info("Starting Val-0 Telegram bot…")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("memory", memory_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
