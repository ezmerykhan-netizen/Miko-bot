import os
from dotenv import load_dotenv

load_dotenv(override=False)


def get_env(key, default=""):
    return os.environ.get(key, default)


BOT_TOKEN = get_env("BOT_TOKEN", "")
ADMIN_ID = int(get_env("ADMIN_ID", "0") or 0)
GEMINI_API_KEY = get_env("GEMINI_API_KEY", "")
GEMINI_MODEL = get_env("GEMINI_MODEL", "gemini-2.5-flash")
YOUTUBE_API_KEY = get_env("YOUTUBE_API_KEY", "")
DB_PATH = get_env("DB_PATH", "zara_bot.sqlite3")
TIMEZONE = get_env("TIMEZONE", "Asia/Tehran")

GEMINI_TYPING_DELAY_MIN = 1.0
GEMINI_TYPING_DELAY_MAX = 3.0
SCHEDULER_INTERVAL = 20
MAX_RETRIES = 3
