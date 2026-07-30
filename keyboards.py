from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu(lang="fa"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ساخت ربات جدید", callback_data="create_bot")],
        [InlineKeyboardButton("🤖 ربات‌های من", callback_data="my_bots")],
        [InlineKeyboardButton("🌐 تغییر زبان", callback_data="change_lang")]
    ])
