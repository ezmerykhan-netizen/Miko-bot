from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def schedule_panel_keyboard():
    """پنل شیشه‌ای زمان‌بندی"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 پست متنی", callback_data="sch_text")],
        [InlineKeyboardButton("🖼 پست عکس", callback_data="sch_photo")],
        [InlineKeyboardButton("🎬 پست ویدیو", callback_data="sch_video")],
        [InlineKeyboardButton("📄 پست فایل/PDF/ZIP", callback_data="sch_document")],
        [InlineKeyboardButton("🎵 پست صوتی", callback_data="sch_audio")],
        [InlineKeyboardButton("🎞 گیف", callback_data="sch_animation")],
        [InlineKeyboardButton("🎙 ویس", callback_data="sch_voice")],
        [InlineKeyboardButton("📋 لیست پست‌های زمان‌بندی", callback_data="sch_list")],
        [InlineKeyboardButton("🗑 حذف پست زمان‌بندی", callback_data="sch_delete")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")],
    ])
