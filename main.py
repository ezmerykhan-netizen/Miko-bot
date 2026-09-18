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
from settings_panel import settings_keyboard
from banner import send_banner, broadcast_banner
from support import forward_to_admin, forward_receipt
from gemini_chat import get_gemini_reply
from scheduler import process_scheduled
from music import search_music

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TZ = ZoneInfo(TIMEZONE)


def parse_datetime(text):
    try:
        parts = text.strip().split()
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
        reply_markup=await user_keyboard()
    )


# ============ کال‌بک‌ها ============
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # --- بررسی عضویت ---
    if data == "check_join":
        await check_join_callback(update, context)
        return

    # --- حمایت مالی (فقط پیام به ادمین) ---
    if data == "donate":
        await query.edit_message_text(DONATE)
        return

    # --- تماس با ادمین ---
    if data == "contact_admin":
        await db.set_fsm(user_id, "awaiting_support")
        await query.edit_message_text(CONTACT_ADMIN)
        return

    # --- آهنگ ---
    if data == "music_start":
        if await db.get_setting("music_enabled", "1") != "1":
            await query.edit_message_text(MUSIC_DISABLED)
            return
        await db.set_fsm(user_id, "awaiting_music")
        await query.edit_message_text(MUSIC_PROMPT)
        return

    # ============ ادمین ============
    if not is_admin(user_id):
        return

    if data == "admin_back":
        await query.edit_message_text(ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())
        return

    if data == "admin_stats":
        users = await db.get_users_count()
        files = await db.get_all_files()
        channels = await db.get_all_channels()
        scheduled = await db.get_all_scheduled()
        music_status = await db.get_setting("music_enabled", "1")
        text = (
            f"📊 آمار ربات\n\n"
            f"👥 کاربران: {users}\n"
            f"📁 فایل‌ها: {len(files)}\n"
            f"📢 کانال‌ها: {len(channels)}\n"
            f"⏰ پست‌های زمان‌بندی: {len(scheduled)}\n"
            f"🎵 آهنگ: {'✅ فعال' if music_status == '1' else '❌ غیرفعال'}"
        )
        await query.edit_message_text(text, reply_markup=admin_keyboard())
        return

    # ============ تنظیمات قابلیت‌ها ============
    if data == "admin_settings":
        music = await db.get_setting("music_enabled", "1")
        referral = await db.get_setting("referral_enabled", "0")
        other_bots = await db.get_setting("other_bots_enabled", "0")
        music_join = await db.get_setting("music_force_join", "0")
        await query.edit_message_text(
            "⚙️ تنظیمات قابلیت‌ها\n\nبرای فعال/غیرفعال کردن، کلیک کن:",
            reply_markup=settings_keyboard(music, referral, other_bots, music_join)
        )
        return

    if data.startswith("toggle_"):
        key_map = {
            "toggle_music": "music_enabled",
            "toggle_referral": "referral_enabled",
            "toggle_other_bots": "other_bots_enabled",
            "toggle_music_join": "music_force_join",
        }
        key = key_map.get(data)
        if key:
            cur = await db.get_setting(key, "0")
            new = "0" if cur == "1" else "1"
            await db.set_setting(key, new)
        music = await db.get_setting("music_enabled", "1")
        referral = await db.get_setting("referral_enabled", "0")
        other_bots = await db.get_setting("other_bots_enabled", "0")
        music_join = await db.get_setting("music_force_join", "0")
        await query.edit_message_reply_markup(
            reply_markup=settings_keyboard(music, referral, other_bots, music_join)
        )
        return

    if data == "set_ref_count":
        await db.set_fsm(user_id, "awaiting_ref_count")
        await query.edit_message_text("تعداد دعوت مورد نیاز رو بفرست (عدد):")
        return

    # ============ فایل ============
    if data == "admin_add_file":
        await db.set_fsm(user_id, "awaiting_file")
        await query.edit_message_text("📎 فایل رو با کپشن بفرست:")
        return

    if data == "admin_edit_caption":
        files = await db.get_all_files()
        if not files:
            await query.edit_message_text("📭 فایلی نیست.", reply_markup=admin_keyboard())
            return
        kb = []
        for f in files[:20]:
            t = f[3][:25] if f[3] else "بدون کپشن"
            kb.append([InlineKeyboardButton(f"#{f[0]} — {t}", callback_data=f"editcap_{f[0]}")])
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")])
        await query.edit_message_text("کدوم؟", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("editcap_"):
        fid = int(data.split("_")[1])
        await db.set_fsm(user_id, "awaiting_new_caption", {"file_id": fid})
        await query.edit_message_text("کپشن جدید رو بفرست:")
        return

    if data == "admin_delete_file":
        files = await db.get_all_files()
        if not files:
            await query.edit_message_text("📭 فایلی نیست.", reply_markup=admin_keyboard())
            return
        kb = []
        for f in files[:20]:
            t = f[3][:25] if f[3] else "بدون کپشن"
            kb.append([InlineKeyboardButton(f"🗑 #{f[0]} — {t}", callback_data=f"delfile_{f[0]}")])
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")])
        await query.edit_message_text("کدوم حذف بشه؟", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("delfile_"):
        fid = int(data.split("_")[1])
        await db.delete_file(fid)
        await query.edit_message_text("✅ حذف شد.", reply_markup=admin_keyboard())
        return

    if data == "admin_list_files":
        files = await db.get_all_files()
        if not files:
            await query.edit_message_text("📭 فایلی نیست.", reply_markup=admin_keyboard())
            return
        text = "📋 فایل‌ها:\n\n"
        for f in files[:30]:
            t = f[3][:30] if f[3] else "بدون کپشن"
            text += f"#{f[0]} | {f[2]} | {t}\n"
        await query.edit_message_text(text, reply_markup=admin_keyboard())
        return

    # ============ کانال ============
    if data == "admin_add_channel":
        await db.set_fsm(user_id, "awaiting_channel")
        await query.edit_message_text(
            "📢 آیدی کانال رو بفرست:\nمثال: `@mychannel` یا `-1001234567890`"
        )
        return

    if data == "admin_del_channel":
        channels = await db.get_all_channels()
        if not channels:
            await query.edit_message_text("📭 کانالی نیست.", reply_markup=admin_keyboard())
            return
        kb = [[InlineKeyboardButton(f"🗑 {c[2]}", callback_data=f"delch_{c[0]}")] for c in channels]
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")])
        await query.edit_message_text("کدوم؟", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("delch_"):
        cid = int(data.split("_")[1])
        await db.delete_channel(cid)
        await query.edit_message_text("✅ حذف شد.", reply_markup=admin_keyboard())
        return

    if data == "admin_list_channels":
        channels = await db.get_all_channels()
        if not channels:
            await query.edit_message_text("📭 کانالی نیست.", reply_markup=admin_keyboard())
            return
        text = "📋 کانال‌ها:\n\n" + "\n".join(f"• {c[2]} — `{c[1]}`" for c in channels)
        await query.edit_message_text(text, reply_markup=admin_keyboard())
        return

    # ============ بنر ============
    if data == "admin_set_banner":
        await db.set_fsm(user_id, "awaiting_banner")
        await query.edit_message_text("🖼 بنر رو بفرست (عکس/ویدیو/فایل + کپشن):")
        return

    if data == "admin_broadcast":
        count = await broadcast_banner(context)
        await query.edit_message_text(
            f"✅ ارسال شد به {count} کاربر." if count else "❌ بنری تنظیم نشده.",
            reply_markup=admin_keyboard()
        )
        return

    # ============ زمان‌بندی ============
    if data == "admin_schedule":
        await query.edit_message_text(
            "⏰ نوع پست رو انتخاب کن:",
            reply_markup=schedule_panel_keyboard()
        )
        return

    if data == "sch_list":
        posts = await db.get_all_scheduled()
        if not posts:
            await query.edit_message_text("📭 خالیه.", reply_markup=schedule_panel_keyboard())
            return
        text = "📋 زمان‌بندی‌ها:\n\n"
        for p in posts[:25]:
            sid, chat_id, fid, ftype, cap, run_at, sent = p
            s = "✅" if sent else "⏳"
            text += f"{s} #{sid} | {ftype} | {run_at[:16]}\n"
        await query.edit_message_text(text, reply_markup=schedule_panel_keyboard())
        return

    if data == "sch_delete":
        posts = await db.get_all_scheduled()
        if not posts:
            await query.edit_message_text("📭 خالیه.", reply_markup=schedule_panel_keyboard())
            return
        kb = [[InlineKeyboardButton(f"🗑 #{p[0]} — {p[5][:16]}", callback_data=f"schdel_{p[0]}")] for p in posts[:15]]
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_schedule")])
        await query.edit_message_text("کدوم؟", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("schdel_"):
        sid = int(data.split("_")[1])
        await db.delete_scheduled(sid)
        await query.edit_message_text("✅ حذف شد.", reply_markup=schedule_panel_keyboard())
        return

    if data.startswith("sch_"):
        ptype = data.replace("sch_", "")
        await db.set_fsm(user_id, "schedule_step1", {"ptype": ptype})
        await query.edit_message_text(
            f"✅ نوع: {ptype}\n\n🏠 آیدی چت مقصد رو بفرست:"
        )
        return


# ============ هندلر پیام ============
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    if not msg:
        return

    state, data = await db.get_fsm(user.id)

    # ============ گروه (Gemini) ============
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
                await msg.reply_text(f"✅ ذخیره شد.\nکپشن: {msg.caption or 'بدون کپشن'}")
            else:
                await msg.reply_text("❌ فایلی نبود.")
            await db.clear_fsm(user.id)
            return

        if state == "awaiting_new_caption":
            await db.update_caption(data.get("file_id"), msg.text or "")
            await msg.reply_text("✅ آپدیت شد.")
            await db.clear_fsm(user.id)
            return

        if state == "awaiting_channel":
            try:
                chat = await context.bot.get_chat(msg.text.strip())
                invite = f"https://t.me/{chat.username}" if chat.username else chat.invite_link
                await db.add_channel(str(chat.id), chat.title, invite)
                await msg.reply_text(f"✅ {chat.title} اضافه شد.")
            except Exception as e:
                await msg.reply_text(f"❌ {e}")
            await db.clear_fsm(user.id)
            return

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
                await msg.reply_text("❌ بنر نبود.")
            await db.clear_fsm(user.id)
            return

        if state == "awaiting_ref_count":
            try:
                n = int(msg.text.strip())
                await db.set_setting("referral_count", str(n))
                await msg.reply_text(f"✅ تعداد دعوت: {n} نفر")
            except Exception:
                await msg.reply_text("❌ عدد بفرست.")
            await db.clear_fsm(user.id)
            return

        # ==== زمان‌بندی ====
        if state == "schedule_step1":
            data["chat_id"] = msg.text.strip()
            await db.set_fsm(user.id, "schedule_step2", data)
            await msg.reply_text(f"✅ چت ثبت شد.\n📎 الان {data.get('ptype')} رو بفرست:")
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
                await msg.reply_text(f"❌ باید {ptype} بفرستی.")
                return
            data["file_id"] = file_id
            data["caption"] = msg.caption or (msg.text if ptype == "text" else "")
            await db.set_fsm(user.id, "schedule_step3", data)
            await msg.reply_text(
                "✅ ثبت شد.\n\n⏰ زمان رو بفرست:\n"
                "📅 میلادی: `2026-10-01 20:30`\n"
                "📅 شمسی: `1404-07-15 20:30`"
            )
            return

        if state == "schedule_step3":
            run_at = parse_datetime(msg.text.strip())
            if not run_at:
                await msg.reply_text("❌ فرمت اشتباه.\nدوباره: `YYYY-MM-DD HH:MM`")
                return
            await db.add_scheduled(data["chat_id"], data["file_id"],
                                    data.get("ptype"), data.get("caption"), run_at)
            await db.clear_fsm(user.id)
            await msg.reply_text(f"✅ زمان‌بندی شد!\n📅 {run_at[:16]}")
            return

    # ============ FSM کاربر ============
    if state == "awaiting_support":
        ok = await forward_to_admin(context, user, msg)
        await msg.reply_text("✅ رسید دست ادمین." if ok else ERROR)
        await db.clear_fsm(user.id)
        return

    if state == "awaiting_music":
        q = msg.text or ""
        if not q.strip():
            await msg.reply_text("❌ اسم آهنگ رو بنویس.")
            return
        await msg.reply_text(MUSIC_SEARCHING)
        results = await search_music(q, max_results=5)
        if not results:
            await msg.reply_text(MUSIC_NOT_FOUND)
            await db.clear_fsm(user.id)
            return
        text = "🎵 نتایج:\n\n"
        for i, r in enumerate(results, 1):
            text += f"{i}. <a href='{r['url']}'>{r['title']}</a>\n   📺 {r['channel']}\n\n"
        await msg.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)
        await db.clear_fsm(user.id)
        return

    # ============ فایل معمولی کاربر ============
    if msg.photo or msg.video or msg.document or msg.audio or msg.voice or msg.animation:
        await msg.reply_text(FILE_SENT)
        await send_banner(context, msg.chat_id)
        return

    await msg.reply_text(FILE_NOT_FOUND)


# ============ Post Init ============
async def post_init(app):
    asyncio.create_task(process_scheduled(app))


# ============ اجرا ============
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN نیست!")
        return

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
