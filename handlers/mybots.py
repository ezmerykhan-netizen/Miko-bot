from telegram import Update
from telegram.ext import ContextTypes
from database import Session, Bot
from languages import LANG

async def mybots_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    session = Session()
    bots = session.query(Bot).filter_by(owner_id=query.from_user.id).all()
    session.close()

    if not bots:
        await query.message.reply_text("هنوز هیچ رباتی نساختی.")
        return

    text = "ربات‌های شما:\n\n"
    for b in bots:
        text += f"- {b.username} | وضعیت: {b.status}\n"

    await query.message.reply_text(text)
