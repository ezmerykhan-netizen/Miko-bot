import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "fa")

    RAILWAY_PROJECT_ID = os.getenv("RAILWAY_PROJECT_ID")
    KOYEB_API_TOKEN = os.getenv("KOYEB_API_TOKEN")
