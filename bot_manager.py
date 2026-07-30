from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.start import start_handler
from handlers.create_bot import create_bot_handler, handle_token
from handlers.mybots import mybots_handler
from handlers.settings import settings_handler
from handlers.update_bot import update_bot_handler
from handlers.logs import logs_handler
from config import Config

app = ApplicationBuilder().token(Config.BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start_handler))
app.add_handler(CallbackQueryHandler(create_bot_handler, pattern="create_bot"))
app.add_handler(CallbackQueryHandler(mybots_handler, pattern="my_bots"))
app.add_handler(CallbackQueryHandler(settings_handler, pattern="settings"))
app.add_handler(CallbackQueryHandler(update_bot_handler, pattern="update_bot"))
app.add_handler(CallbackQueryHandler(logs_handler, pattern="logs"))

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_token))

# اجرای اصلی ربات
if __name__ == "__main__":
    app.run_polling()
