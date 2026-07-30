from telegram import Update
from telegram.ext import ContextTypes
from database import Session, Bot
from languages import LANG

async def create_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = "fa"
    await query.message.reply_text(LANG[lang]["create_bot"])

    # فعال کردن حالت انتظار برای دریافت توکن
    context.user_data["awaiting_bot_token"] = True


async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # اگر کاربر در حالت انتظار توکن نیست، هیچ کاری نکن
    if not context.user_data.get("awaiting_bot_token"):
        return

    token = update.message.text
    username = f"bot_{update.effective_user.id}"

    # ذخیره‌سازی توکن در دیتابیس
    session = Session()
    bot = Bot(
        owner_id=update.effective_user.id,
        token=token,
        username=username,
        status="saved"
    )
    session.add(bot)
    session.commit()
    session.close()

    # خاموش کردن حالت انتظار
    context.user_data["awaiting_bot_token"] = False

    await update.message.reply_text("توکن ذخیره شد. ادامهٔ ساخت ربات بعداً اضافه می‌شود. ✅")
