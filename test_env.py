import os
from dotenv import load_dotenv

DOTENV_PATH = "/opt/val0/.env"

print("Using dotenv path:", DOTENV_PATH)
loaded = load_dotenv(dotenv_path=DOTENV_PATH)
print("load_dotenv() returned:", loaded)

openai_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

print("OPENAI_API_KEY present?", bool(openai_key))
print("OPENAI_API_KEY prefix:", openai_key[:8] if openai_key else None)

print("TELEGRAM_BOT_TOKEN present?", bool(telegram_token))
if telegram_token:
    # print only the bot id before the colon, never the full token
    print("TELEGRAM_BOT_TOKEN bot id prefix:", telegram_token.split(":")[0])
else:
    print("TELEGRAM_BOT_TOKEN bot id prefix:", None)
