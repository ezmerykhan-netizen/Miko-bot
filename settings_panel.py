from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def settings_keyboard(music, referral, other_bots, music_join):
    """پنل تنظیمات قابلیت‌ها"""
    def status(v):
        return "✅ فعال" if v == "1" else "❌ غیرفعال"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"🎵 آهنگ: {status(music)}",
            callback_data="toggle_music"
        )],
        [InlineKeyboardButton(
            f"🎁 دعوت: {status(referral)}",
            callback_data="toggle_referral"
        )],
        [InlineKeyboardButton(
            f"🤖 ربات‌های دیگر: {status(other_bots)}",
            callback_data="toggle_other_bots"
        )],
        [InlineKeyboardButton(
            f"📢 عضویت اجباری آهنگ: {status(music_join)}",
            callback_data="toggle_music_join"
        )],
        [InlineKeyboardButton("✏️ تنظیم تعداد دعوت", callback_data="set_ref_count")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")],
    ])
