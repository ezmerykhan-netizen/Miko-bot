import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
CARD_NUMBER = os.getenv("CARD_NUMBER", "")
CARD_NAME = os.getenv("CARD_NAME", "")
DB_PATH = os.getenv("DB_PATH", "zara_bot.sqlite3")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tehran")

CARD_DELETE_DELAY = 50
GEMINI_TYPING_DELAY_MIN = 1.0
GEMINI_TYPING_DELAY_MAX = 3.0
SCHEDULER_INTERVAL = 20
MAX_RETRIES = 3
