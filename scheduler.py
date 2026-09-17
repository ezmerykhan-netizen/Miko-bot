import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import database as db
from config import TIMEZONE, SCHEDULER_INTERVAL, MAX_RETRIES

TZ = ZoneInfo(TIMEZONE)


async def process_scheduled(context):
    """حلقه اصلی زمان‌بندی"""
    while True:
        try:
            pending = await db.get_pending_scheduled()
            now = datetime.now(TZ)

            for sid, chat_id, file_id, ftype, caption, run_at in pending:
                try:
                    run_dt = datetime.fromisoformat(run_at)
                    if run_dt.tzinfo is None:
                        run_dt = run_dt.replace(tzinfo=TZ)
                except Exception:
                    continue

                if run_dt <= now:
                    try:
                        await send_scheduled_post(
                            context, chat_id, file_id, ftype, caption
                        )
                        await db.mark_sent(sid)
                        print(f"[SCHEDULER] ✅ ارسال شد: #{sid}")
                    except Exception as e:
                        print(f"[SCHEDULER] ❌ خطا در #{sid}: {e}")
                        await db.increment_retry(sid)
        except Exception as e:
            print(f"[SCHEDULER] خطای کلی: {e}")

        await asyncio.sleep(SCHEDULER_INTERVAL)


async def send_scheduled_post(context, chat_id, file_id, ftype, caption):
    """ارسال پست بر اساس نوع"""
    caption = caption or None

    if ftype == "text":
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption or "",
            disable_web_page_preview=True
        )
    elif ftype == "photo":
        await context.bot.send_photo(chat_id, file_id, caption=caption)
    elif ftype == "video":
        await context.bot.send_video(chat_id, file_id, caption=caption)
    elif ftype == "audio":
        await context.bot.send_audio(chat_id, file_id, caption=caption)
    elif ftype == "voice":
        await context.bot.send_voice(chat_id, file_id, caption=caption)
    elif ftype == "animation":
        await context.bot.send_animation(chat_id, file_id, caption=caption)
    else:
        await context.bot.send_document(chat_id, file_id, caption=caption)
