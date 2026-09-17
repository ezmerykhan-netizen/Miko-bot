from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from texts import BTN_SUPPORT


def user_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 حمایت مالی", callback_data="donate")],
        [InlineKeyboardButton(BTN_SUPPORT, callback_data="contact_admin")],
    ])
