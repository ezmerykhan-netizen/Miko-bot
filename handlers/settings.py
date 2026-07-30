from telegram import Update
from telegram.ext import ContextTypes

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("فعلاً تنظیمات ساده‌ست؛ بعداً می‌تونیم زبان و حالت اجرا رو اضافه کنیم.")
