from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from texts import BTN_SUPPORT
import database as db


async def user_keyboard():
    """پنل کاربر شیشه‌ای"""
    music_on = await db.get_setting("music_enabled", "1") == "1"

    buttons = []
    if music_on:
        buttons.append([InlineKeyboardButton("🎵 پیدا کردن آهنگ", callback_data="music_start")])
    buttons.append([InlineKeyboardButton("💰 حمایت مالی", callback_data="donate")])
    buttons.append([InlineKeyboardButton(BTN_SUPPORT, callback_data="contact_admin")])

    return InlineKeyboardMarkup(buttons)
