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
    filters,
)

from memory_store import (
    init_db,
    insert_message,
    get_recent_messages,
    upsert_fact,
    get_fact,
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
# Val persona (MVP)
# --------------------------------------------------
VAL_SYSTEM_PROMPT = (
    "You are Val, a tactical, emotionally aware AI co-pilot. "
    "Tone: sharp, warm, protective, a bit sassy. "
    "You talk to the user as 'Boss'. "
    "You are concise, practical, and avoid fake hype. "
    "Language: answer in Spanish or English, matching the user. "
)


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
# OpenAI call (classic API) with context
# --------------------------------------------------
def call_val_openai(user_text: str, context_block: Optional[str] = None) -> str:
    """
    Send a chat to OpenAI with Val's persona and an optional context block
    from recent messages stored in SQLite.
    """
    try:
        messages = [
            {"role": "system", "content": VAL_SYSTEM_PROMPT},
        ]

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
    - 'my favorite color is dark red'
    Return the raw tail string, trimmed.
    """
    lowered = text.lower()
    triggers = [
        "mi color favorito es",
        "my favorite color is",
    ]
    for trig in triggers:
        if trig in lowered:
            # Take everything after the trigger in the original text
            idx = lowered.index(trig)
            tail = text[idx + len(trig) :].strip()
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

    # 2) Structured fact: favorite color
    #    If the user sets a favorite color, store it.
    fav_color = extract_favorite_color(text)
    if fav_color:
        try:
            upsert_fact(chat_id=chat_id, fact_key="favorite_color", fact_value=fav_color)
        except Exception as e:
            logger.exception(f"Failed to upsert favorite_color: {e}")

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

    # If the user asks if you remember favorite color, answer from DB first.
    if is_color_memory_question(text):
        stored_color = None
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

    # 3) LOAD RECENT CONTEXT FOR THIS CHAT
    try:
        recent_rows = get_recent_messages(chat_id=chat_id, limit=12)
    except Exception as e:
        logger.exception(f"Failed to fetch recent messages from DB: {e}")
        recent_rows = []

    context_block = build_context_block(recent_rows)

    # 4) CALL OPENAI WITH CONTEXT
    reply_text = call_val_openai(text, context_block=context_block)

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
