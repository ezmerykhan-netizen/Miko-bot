import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

import database as db
from config import BOT_TOKEN, ADMIN_ID, TIMEZONE
from texts import *
from jalali import jalali_to_gregorian
from force_join import is_user_joined, send_join_prompt, check_join_callback
from admin_panel import admin_keyboard, is_admin, show_admin_panel
from user_panel import user_keyboard
from schedule_panel import schedule_panel_keyboard
from banner import send_banner, broadcast_banner, send_donate_info
from support import forward_to_admin, forward_receipt
from gemini_chat import get_gemini_reply
from scheduler import process_scheduled

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TZ = ZoneInfo(TIMEZONE)


# ============ پارس تاریخ ============
def parse_datetime(text):
    """پارس تاریخ شمسی یا میلادی"""
    try:
        text = text.strip()
        parts = text.split()
        date_part = parts[0]
        time_part = parts[1] if len(parts) > 1 else "00:00"

        y, m, d = map(int, date_part.split("-"))
        hh, mm = map(int, time_part.split(":"))

        if y < 1500:
            gy, gm, gd = jalali_to_gregorian(y, m, d)
            dt = datetime(gy, gm, gd, hh, mm, tzinfo=TZ)
        else:
            dt = datetime(y, m, d, hh, mm, tzinfo=TZ)

        return dt.isoformat()
    except Exception:
        return None


# ============ استارت ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.add_user(user.id, user.username, user.first_name)

    if not await is_user_joined(context, user.id):
        await send_join_prompt(update, context)
        return

    if is_admin(user.id):
        await show_admin_panel(update, context)
        return

    await update.message.reply_text(
        WELCOME_AFTER_JOIN,
        reply_markup=user_keyboard()
    )


# ============ کال‌بک‌ها ============
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # ---- بررسی عضویت ----
    if data == "check_join":
        await check_join_callback(update, context)
        return

    # ---- حمایت مالی ----
    if data == "donate":
        await send_donate_info(context, query.message.chat_id)
        return

    # ---- تماس با ادمین ----
    if data == "contact_admin":
        await db.set_fsm(user_id, "awaiting_support")
        await query.edit_message_text(CONTACT_ADMIN)
        return

    # ---- فقط ادمین ----
    if not is_admin(user_id):
        return

    # ============ پنل اصلی ============
    if data == "admin_back":
        await query.edit_message_text(
            ADMIN_PANEL_TITLE,
            reply_markup=admin_keyboard()
        )
        return

    # ---- آمار ----
    if data == "admin_stats":
        users = await db.get_users_count()
        files = await db.get_all_files()
        channels = await db.get_all_channels()
        scheduled = await db.get_all_scheduled()
        text = (
            f"📊 آمار ربات\n\n"
            f"👥 کاربران: {users}\n"
            f"📁 فایل‌ها: {len(files)}\n"
            f"📢 کانال‌ها: {len(channels)}\n"
            f"⏰ پست‌های زمان‌بندی: {len(scheduled)}"
        )
        await query.edit_message_text(text, reply_markup=admin_keyboard())
        return

    # ============ مدیریت فایل ============
    if data == "admin_add_file":
        await db.set_fsm(user_id, "awaiting_file")
        await query.edit_message_text("📎 فایل رو بفرست (عکس/ویدیو/PDF/ZIP/فایل) با کپشن دلخواه:")
        return

    if data == "admin_edit_caption":
        files = await db.get_all_files()
        if not files:
            await query.edit_message_text("📭 فایلی نیست.", reply_markup=admin_keyboard())
            return
        keyboard = []
        for f in files[:20]:
            title = f[3][:25] if f[3] else "بدون کپشن"
            keyboard.append([InlineKeyboardButton(
                f"#{f[0]} — {title}",
                callback_data=f"editcap_{f[0]}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")])
        await query.edit_message_text(
            "کدوم فایل؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("editcap_"):
        fid = int(data.split("_")[1])
        await db.set_fsm(user_id, "awaiting_new_caption", {"file_id": fid})
        await query.edit_message_text("✏️ کپشن جدید رو بفرست:")
        return

    if data == "admin_delete_file":
        files = await db.get_all_files()
        if not files:
            await query.edit_message_text("📭 فایلی نیست.", reply_markup=admin_keyboard())
            return
        keyboard = []
        for f in files[:20]:
            title = f[3][:25] if f[3] else "بدون کپشن"
            keyboard.append([InlineKeyboardButton(
                f"🗑 #{f[0]} — {title}",
                callback_data=f"delfile_{f[0]}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")])
        await query.edit_message_text(
            "کدوم حذف بشه؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("delfile_"):
        fid = int(data.split("_")[1])
        await db.delete_file(fid)
        await query.edit_message_text(
            f"✅ فایل #{fid} حذف شد.",
            reply_markup=admin_keyboard()
        )
        return

    if data == "admin_list_files":
        files = await db.get_all_files()
        if not files:
            await query.edit_message_text("📭 فایلی نیست.", reply_markup=admin_keyboard())
            return
        text = "📋 فایل‌ها:\n\n"
        for f in files[:30]:
            title = f[3][:30] if f[3] else "بدون کپشن"
            text += f"#{f[0]} | {f[2]} | {title}\n"
        await query.edit_message_text(text, reply_markup=admin_keyboard())
        return

    # ============ کانال‌ها ============
    if data == "admin_add_channel":
        await db.set_fsm(user_id, "awaiting_channel")
        await query.edit_message_text(
            "📢 آیدی کانال رو بفرست:\n"
            "مثال: `@mychannel` یا `-1001234567890`\n\n"
            "⚠️ ربات باید ادمین کانال باشه."
        )
        return

    if data == "admin_del_channel":
        channels = await db.get_all_channels()
        if not channels:
            await query.edit_message_text("📭 کانالی نیست.", reply_markup=admin_keyboard())
            return
        keyboard = []
        for c in channels:
            keyboard.append([InlineKeyboardButton(
                f"🗑 {c[2]}",
                callback_data=f"delch_{c[0]}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")])
        await query.edit_message_text(
            "کدوم حذف بشه؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("delch_"):
        cid = int(data.split("_")[1])
        await db.delete_channel(cid)
        await query.edit_message_text(
            "✅ کانال حذف شد.",
            reply_markup=admin_keyboard()
        )
        return

    if data == "admin_list_channels":
        channels = await db.get_all_channels()
        if not channels:
            await query.edit_message_text("📭 کانالی نیست.", reply_markup=admin_keyboard())
            return
        text = "📋 کانال‌ها:\n\n"
        for c in channels:
            text += f"• {c[2]} — `{c[1]}`\n"
        await query.edit_message_text(text, reply_markup=admin_keyboard())
        return

    # ============ بنر ============
    if data == "admin_set_banner":
        await db.set_fsm(user_id, "awaiting_banner")
        await query.edit_message_text(
            "🖼 بنر رو بفرست (عکس/ویدیو/فایل + کپشن):"
        )
        return

    if data == "admin_broadcast":
        count = await broadcast_banner(context)
        if count == 0:
            await query.edit_message_text(
                "❌ بنری تنظیم نشده یا ارسال نشد.",
                reply_markup=admin_keyboard()
            )
        else:
            await query.edit_message_text(
                f"✅ بنر فوری ارسال شد به {count} کاربر.",
                reply_markup=admin_keyboard()
            )
        return

    # ============ زمان‌بندی ============
    if data == "admin_schedule":
        await query.edit_message_text(
            "⏰ پنل زمان‌بندی\n\nنوع پست رو انتخاب کن:",
            reply_markup=schedule_panel_keyboard()
        )
        return

    if data == "sch_list":
        posts = await db.get_all_scheduled()
        if not posts:
            await query.edit_message_text(
                "📭 هیچ پست زمان‌بندی شده‌ای نیست.",
                reply_markup=schedule_panel_keyboard()
            )
            return
        text = "📋 پست‌های زمان‌بندی شده:\n\n"
        for p in posts[:25]:
            sid, chat_id, fid, ftype, cap, run_at, sent = p
            status = "✅" if sent else "⏳"
            text += f"{status} #{sid} | {ftype} | {chat_id}\n    📅 {run_at[:16]}\n"
        await query.edit_message_text(
            text,
            reply_markup=schedule_panel_keyboard()
        )
        return

    if data == "sch_delete":
        posts = await db.get_all_scheduled()
        if not posts:
            await query.edit_message_text(
                "📭 چیزی برای حذف نیست.",
                reply_markup=schedule_panel_keyboard()
            )
            return
        keyboard = []
        for p in posts[:15]:
            sid, chat_id, fid, ftype, cap, run_at, sent = p
            status = "✅" if sent else "⏳"
            keyboard.append([InlineKeyboardButton(
                f"{status} #{sid} — {run_at[:16]}",
                callback_data=f"schdel_{sid}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_schedule")])
        await query.edit_message_text(
            "کدوم پست حذف بشه؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("schdel_"):
        sid = int(data.split("_")[1])
        await db.delete_scheduled(sid)
        await query.edit_message_text(
            f"✅ پست #{sid} حذف شد.",
            reply_markup=schedule_panel_keyboard()
        )
        return

    # ---- انتخاب نوع پست ----
    if data.startswith("sch_"):
        ptype = data.replace("sch_", "")
        await db.set_fsm(user_id, "schedule_step1", {"ptype": ptype})
        await query.edit_message_text(
            f"✅ نوع: {ptype}\n\n"
            "🏠 الان آیدی چت مقصد رو بفرست:\n"
            "مثال: `@mychannel` یا `-1001234567890`"
        )
        return


# ============ هندلر پیام‌ها ============
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    if not msg:
        return

    state, data = await db.get_fsm(user.id)

    # ============ چت گروه ============
    if msg.chat.type in ("group", "supergroup"):
        if msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id:
            text = msg.text or msg.caption or ""
            reply = await get_gemini_reply(text, msg.chat_id)
            if reply:
                await msg.reply_text(reply)
        elif msg.text and f"@{context.bot.username}" in msg.text:
            clean = msg.text.replace(f"@{context.bot.username}", "").strip()
            reply = await get_gemini_reply(clean, msg.chat_id)
            if reply:
                await msg.reply_text(reply)
        return

    # ============ چت خصوصی ============
    if not await is_user_joined(context, user.id):
        await send_join_prompt(update, context)
        return

    # ============ FSM ادمین ============
    if is_admin(user.id):

        # ---- افزودن فایل ----
        if state == "awaiting_file":
            ftype, file_id = None, None
            if msg.photo:
                ftype, file_id = "photo", msg.photo[-1].file_id
            elif msg.video:
                ftype, file_id = "video", msg.video.file_id
            elif msg.audio:
                ftype, file_id = "audio", msg.audio.file_id
            elif msg.voice:
                ftype, file_id = "voice", msg.voice.file_id
            elif msg.animation:
                ftype, file_id = "animation", msg.animation.file_id
            elif msg.document:
                ftype, file_id = "document", msg.document.file_id
            if file_id:
                await db.add_file(file_id, ftype, msg.caption or "")
                await msg.reply_text(
                    f"✅ فایل ذخیره شد.\n"
                    f"نوع: {ftype}\n"
                    f"کپشن: {msg.caption or 'بدون کپشن'}"
                )
            else:
                await msg.reply_text("❌ فایلی دریافت نشد.")
            await db.clear_fsm(user.id)
            return

        # ---- ویرایش کپشن ----
        if state == "awaiting_new_caption":
            fid = data.get("file_id")
            await db.update_caption(fid, msg.text or "")
            await msg.reply_text(f"✅ کپشن فایل #{fid} آپدیت شد.")
            await db.clear_fsm(user.id)
            return

        # ---- افزودن کانال ----
        if state == "awaiting_channel":
            try:
                target = msg.text.strip()
                chat = await context.bot.get_chat(target)
                invite = None
                if chat.username:
                    invite = f"https://t.me/{chat.username}"
                elif chat.invite_link:
                    invite = chat.invite_link
                await db.add_channel(str(chat.id), chat.title, invite)
                await msg.reply_text(f"✅ کانال اضافه شد:\n{chat.title}")
            except Exception as e:
                await msg.reply_text(f"❌ خطا: {e}")
            await db.clear_fsm(user.id)
            return

        # ---- تنظیم بنر ----
        if state == "awaiting_banner":
            ftype, file_id = None, None
            if msg.photo:
                ftype, file_id = "photo", msg.photo[-1].file_id
            elif msg.video:
                ftype, file_id = "video", msg.video.file_id
            elif msg.animation:
                ftype, file_id = "animation", msg.animation.file_id
            elif msg.document:
                ftype, file_id = "document", msg.document.file_id
            if file_id:
                await db.set_banner(file_id, ftype, msg.caption or "")
                await msg.reply_text("✅ بنر تنظیم شد.")
            else:
                await msg.reply_text("❌ بنر دریافت نشد.")
            await db.clear_fsm(user.id)
            return

        # ============ FSM زمان‌بندی ============
        if state == "schedule_step1":
            data["chat_id"] = msg.text.strip()
            await db.set_fsm(user.id, "schedule_step2", data)
            await msg.reply_text(
                f"✅ چت ثبت شد: `{data['chat_id']}`\n\n"
                f"📎 الان {data.get('ptype')} رو با کپشن بفرست:"
            )
            return

        if state == "schedule_step2":
            ptype = data.get("ptype")
            file_id = None

            if ptype == "text":
                file_id = msg.text or ""
            elif ptype == "photo" and msg.photo:
                file_id = msg.photo[-1].file_id
            elif ptype == "video" and msg.video:
                file_id = msg.video.file_id
            elif ptype == "document" and msg.document:
                file_id = msg.document.file_id
            elif ptype == "audio" and msg.audio:
                file_id = msg.audio.file_id
            elif ptype == "voice" and msg.voice:
                file_id = msg.voice.file_id
            elif ptype == "animation" and msg.animation:
                file_id = msg.animation.file_id
            else:
                await msg.reply_text(f"❌ نوع فایل اشتباهه. باید {ptype} بفرستی.")
                return

            data["file_id"] = file_id
            data["caption"] = msg.caption or (msg.text if ptype == "text" else "")
            await db.set_fsm(user.id, "schedule_step3", data)
            await msg.reply_text(
                "✅ محتوا ثبت شد.\n\n"
                "⏰ الان زمان ارسال رو بفرست:\n\n"
                "📅 میلادی: `2026-10-01 20:30`\n"
                "📅 شمسی: `1404-07-15 20:30`\n\n"
                "⚠️ سال کمتر از 1500 = شمسی"
            )
            return

        if state == "schedule_step3":
            time_str = msg.text.strip()
            run_at = parse_datetime(time_str)
            if not run_at:
                await msg.reply_text(
                    "❌ فرمت زمان اشتباهه.\n"
                    "دوباره بفرست: `YYYY-MM-DD HH:MM`"
                )
                return

            await db.add_scheduled(
                data["chat_id"],
                data["file_id"],
                data.get("ptype"),
                data.get("caption"),
                run_at
            )
            await db.clear_fsm(user.id)
            await msg.reply_text(
                f"✅ پست زمان‌بندی شد!\n\n"
                f"📅 زمان: {run_at[:16]}\n"
                f"📍 مقصد: {data['chat_id']}\n"
                f"🎯 نوع: {data.get('ptype')}"
            )
            return

    # ============ FSM کاربر ============
    if state == "awaiting_support":
        ok = await forward_to_admin(context, user, msg)
        if ok:
            await msg.reply_text("✅ فرستادم برای آدم اصلی.")
        else:
            await msg.reply_text(ERROR)
        await db.clear_fsm(user.id)
        return

    # ============ FSM رسید حمایت ============
    if state == "awaiting_receipt":
        ok = await forward_receipt(context, user, msg)
        if ok:
            await msg.reply_text("✅ رسیدت رسید دست ادمین.")
        else:
            await msg.reply_text(ERROR)
        await db.clear_fsm(user.id)
        return

    # ============ فایل معمولی کاربر ============
    if msg.photo or msg.video or msg.document or msg.audio or msg.voice or msg.animation:
        await msg.reply_text(FILE_SENT)
        await send_banner(context, msg.chat_id)
        return

    # ============ پیش‌فرض ============
    await msg.reply_text(FILE_NOT_FOUND)


# ============ Post Init ============
async def post_init(app):
    asyncio.create_task(process_scheduled(app))


# ============ اجرای ربات ============
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN تو .env تنظیم نشده!")
        return
    if not ADMIN_ID:
        print("❌ ADMIN_ID تو .env تنظیم نشده!")
        return

    # init DB
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(db.init_db())
    loop.close()

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))

    print("🚀 ربات روشن شد...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
