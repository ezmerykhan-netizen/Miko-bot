from telegram import Update
from telegram.ext import ContextTypes
from languages import LANG
from keyboards import main_menu

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = "fa"  # فعلاً ثابت، بعداً از دیتابیس می‌گیریم

    text = LANG[lang]["start"]
    await update.message.reply_text(text, reply_markup=main_menu(lang))
