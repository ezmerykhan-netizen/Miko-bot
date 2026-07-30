import subprocess
import os
from database import Session, Bot

class BotManager:
    def create_bot_project(self, bot_token, username):
        folder = f"bots/{username}"
        os.makedirs(folder, exist_ok=True)

        with open(f"{folder}/bot.py", "w") as f:
            f.write(f"""
from telegram.ext import ApplicationBuilder, CommandHandler

async def start(update, context):
    await update.message.reply_text("ربات شما فعال شد!")

app = ApplicationBuilder().token("{bot_token}").build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
""")

        return folder

    def run_bot(self, username):
        subprocess.Popen(["python3", f"bots/{username}/bot.py"])

    def stop_bot(self, username):
        os.system(f"pkill -f bots/{username}/bot.py")
