import asyncio
from config import CARD_NUMBER, CARD_NAME, CARD_DELETE_DELAY
from texts import DONATE, CARD_WARNING, AFTER_CARD
import database as db


async def send_banner(context, chat_id):
    banner = await db.get_banner()
    if not banner:
        return
    file_id, ftype, caption = banner
    try:
        if ftype == "photo":
            await context.bot.send_photo(chat_id, file_id, caption=caption)
        elif ftype == "video":
            await context.bot.send_video(chat_id, file_id, caption=caption)
        elif ftype == "animation":
            await context.bot.send_animation(chat_id, file_id, caption=caption)
        else:
            await context.bot.send_document(chat_id, file_id, caption=caption)
    except Exception:
        pass


async def broadcast_banner(context):
    banner = await db.get_banner()
    if not banner:
        return 0
    file_id, ftype, caption = banner
    users = await db.get_all_users()
    count = 0
    for uid in users:
        try:
            if ftype == "photo":
                await context.bot.send_photo(uid, file_id, caption=caption)
            elif ftype == "video":
                await context.bot.send_video(uid, file_id, caption=caption)
            elif ftype == "animation":
                await context.bot.send_animation(uid, file_id, caption=caption)
            else:
                await context.bot.send_document(uid, file_id, caption=caption)
            count += 1
            await asyncio.sleep(0.05)  # rate limit
        except Exception:
            continue
    return count


async def send_donate_info(context, chat_id):
    await context.bot.send_message(chat_id, DONATE)
    msg = await context.bot.send_message(
        chat_id,
        f"💳 شماره کارت:\n`{CARD_NUMBER}`\n\n"
        f"👤 به نام: {CARD_NAME}\n\n"
        f"{CARD_WARNING}",
        parse_mode="Markdown"
    )
    await asyncio.sleep(CARD_DELETE_DELAY)
    try:
        await msg.delete()
    except Exception:
        pass
    await context.bot.send_message(chat_id, AFTER_CARD)
