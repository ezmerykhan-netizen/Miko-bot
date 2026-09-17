from config import ADMIN_ID
from texts import ERROR


async def forward_to_admin(context, user, message):
    """ارسال پیام کاربر به ادمین"""
    try:
        text = (
            f"📩 پیام جدید\n\n"
            f"👤 نام: {user.first_name}\n"
            f"🆔 آیدی: `{user.id}`\n"
            f"📛 یوزر: @{user.username or 'ندارد'}\n\n"
            f"💬 متن:\n{message.text or '(بدون متن)'}"
        )
        await context.bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
        if message.photo:
            await context.bot.send_photo(ADMIN_ID, message.photo[-1].file_id)
        elif message.video:
            await context.bot.send_video(ADMIN_ID, message.video.file_id)
        elif message.document:
            await context.bot.send_document(ADMIN_ID, message.document.file_id)
        return True
    except Exception:
        return False


async def forward_receipt(context, user, message):
    """ارسال رسید حمایت مالی به ادمین"""
    try:
        text = (
            f"💰 رسید حمایت مالی\n\n"
            f"👤 از: {user.first_name} (@{user.username or 'ندارد'})\n"
            f"🆔 آیدی: `{user.id}`"
        )
        await context.bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
        if message.photo:
            await context.bot.send_photo(
                ADMIN_ID, message.photo[-1].file_id,
                caption=message.caption or ""
            )
        elif message.document:
            await context.bot.send_document(
                ADMIN_ID, message.document.file_id,
                caption=message.caption or ""
            )
        return True
    except Exception:
        return False
