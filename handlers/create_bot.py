from telegram import Update
from telegram.ext import ContextTypes
from database import Session, Bot
from bot_manager import BotManager
from languages import LANG

bot_manager = BotManager()

async def create_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = "fa"
    await query.message.reply_text(LANG[lang]["create_bot"])

    context.user_data["awaiting_bot_token"] = True

async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_bot_token"):
        return

    token = update.message.text
    username = f"bot_{update.effective_user.id}"

    folder = bot_manager.create_bot_project(token, username)
    bot_manager.run_bot(username)

    session = Session()
    bot = Bot(owner_id=update.effective_user.id, token=token, username=username, status="running")
    session.add(bot)
    session.commit()
    session.close()

    context.user_data["awaiting_bot_token"] = False
    await update.message.reply_text("ربات ساخته شد و الان در حال اجراست ✅")
