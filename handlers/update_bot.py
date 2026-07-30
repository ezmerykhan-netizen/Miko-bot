from telegram import Update
from telegram.ext import ContextTypes
from github_manager import GitHubManager
from database import Session, Bot

github = GitHubManager()

async def update_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    session = Session()
    bot = session.query(Bot).filter_by(owner_id=query.from_user.id).first()
    session.close()

    if not bot or not bot.repo_name:
        await query.message.reply_text("برای این ربات هنوز ریپازیتوری GitHub ثبت نشده.")
        return

    await query.message.reply_text("فعلاً فقط پیام تست آپدیت می‌فرستم؛ می‌تونیم بعداً کد رو از تلگرام بگیریم و روی GitHub آپلود کنیم.")
