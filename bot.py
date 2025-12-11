import os
import logging

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

# Our SQLite memory spine
from memory_store import init_db, save_message, get_recent_messages

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

# --------------------------------------------------
# Context builder using SQLite memory
# --------------------------------------------------
def build_context_messages(chat_id: int, user_text: str) -> list[dict]:
    """
    Build the messages list for OpenAI using:
    - Val's system prompt
    - recent history from SQLite
    - the current user message
    """
    messages: list[dict] = [{"role": "system", "content": VAL_SYSTEM_PROMPT}]

    try:
        recent = get_recent_messages(chat_id=chat_id, limit=10)
        for row in recent:
            role = row.get("role", "user")
            content = row.get("content", "")
            if not content:
                continue
            # OpenAI expects only 'user' or 'assistant' here
            if role not in ("user", "assistant"):
                role = "user"
            messages.append({"role": role, "content": content})
    except Exception as e:
        logger.exception(f"Failed to load recent messages for chat_id={chat_id}: {e}")

    # Current user turn at the end
    messages.append({"role": "user", "content": user_text})
    return messages

# --------------------------------------------------
# OpenAI call (classic API)
# --------------------------------------------------
def call_val_openai(chat_id: int, user_text: str) -> str:
    """
    Send a multi-turn chat to OpenAI with Val's persona and SQLite context.
    Uses classic ChatCompletion API (openai<1.0).
    """
    try:
        messages = build_context_messages(chat_id=chat_id, user_text=user_text)
        resp = openai.ChatCompletion.create(
            model="gpt-4.1-mini",  # can swap later if needed
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
# Telegram handlers
# --------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat

    logger.info(f"/start from user_id={user.id} username={user.username}")

    # Optionally log /start as a user message
    try:
        save_message(
            chat_id=chat.id,
            role="user",
            content="/start",
            telegram_message_id=update.message.message_id if update.message else None,
            model_used=None,
        )
    except Exception as e:
        logger.exception(f"Failed to save /start message: {e}")

    await update.message.reply_text(
        "Val-0 online. Ya puedo hablar contigo por aquí, Boss."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat = update.effective_chat
    text = update.message.text.strip()

    logger.info(f"msg from user_id={user.id} chat_id={chat.id}: {text!r}")

    # 1) Store USER message immediately
    try:
        save_message(
            chat_id=chat.id,
            role="user",
            content=text,
            telegram_message_id=update.message.message_id,
            model_used=None,
        )
    except Exception as e:
        logger.exception(f"Failed to save user message for chat_id={chat.id}: {e}")

    # 2) Ask Val (with context from SQLite)
    reply = call_val_openai(chat_id=chat.id, user_text=text)

    # 3) Send reply to Telegram
    sent_message = None
    try:
        sent_message = await update.message.reply_text(reply)
    except Exception as e:
        logger.exception(f"Failed to send reply to Telegram for chat_id={chat.id}: {e}")
        return  # don't store assistant message if we didn't send it

    # 4) Store ASSISTANT message only after successful send
    try:
        save_message(
            chat_id=chat.id,
            role="assistant",
            content=reply,
            telegram_message_id=sent_message.message_id if sent_message else None,
            model_used="gpt-4.1-mini",
        )
    except Exception as e:
        logger.exception(f"Failed to save assistant message for chat_id={chat.id}: {e}")

# --------------------------------------------------
# Main
# --------------------------------------------------
def main() -> None:
    logger.info("Initializing SQLite memory spine…")
    try:
        init_db()
    except Exception as e:
        logger.exception(f"init_db() failed: {e}")
        raise

    logger.info("Starting Val-0 Telegram bot…")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
