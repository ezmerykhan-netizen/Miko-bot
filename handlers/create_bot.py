async def create_bot_handler(update, context):
    await update.message.reply_text("توکن ربات جدید را ارسال کنید:")
    context.user_data["awaiting_bot_token"] = True

async def handle_token(update, context):
    if not context.user_data.get("awaiting_bot_token"):
        return

    token = update.message.text
    context.user_data["awaiting_bot_token"] = False
    await update.message.reply_text("توکن ذخیره شد. ادامهٔ ساخت بعداً اضافه می‌شود.")
