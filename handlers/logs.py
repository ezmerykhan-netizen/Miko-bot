from telegram import Update
from telegram.ext import ContextTypes
from database import Session, Log

async def logs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    session = Session()
    logs = session.query(Log).all()
    session.close()

    if not logs:
        await query.message.reply_text("هنوز لاگی ثبت نشده.")
        return

    text = "آخرین لاگ‌ها:\n\n"
    for l in logs[-10:]:
        text += f"- {l.content}\n"

    await query.message.reply_text(text)
