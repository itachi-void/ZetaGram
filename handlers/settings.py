from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select

from database.db import AsyncSessionLocal
from database.models import User
from handlers.levels import LEVEL_TITLES
from utils.gatekeeper import enforce_user_access
from utils.html_utils import esc


async def show_user_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        if not user:
            return

    notif_on = True if user.notifications_enabled is None else bool(user.notifications_enabled)
    notif_str = "🔔 مفعّلة" if notif_on else "🔕 متوقفة"
    toggle_btn_label = "🔕 إيقاف التذكيرات" if notif_on else "🔔 تفعيل التذكيرات"
    lvl_title = LEVEL_TITLES.get(user.vip_level or 1, "🥉 مبتدئ")

    text = (
        f"⚙️ <b>إعدادات الحساب وحالة الثقة:</b>\n\n"
        f"🔔 <b>إشعارات التذكير:</b> {notif_str}\n"
        f"🌐 <b>اللغة الحالية:</b> <code>{esc(user.language or 'ar')}</code>\n"
        f"🏅 <b>المستوى:</b> {esc(lvl_title)}\n"
        f"🛡️ <b>نقاط الثقة:</b> <code>{user.trust_score if user.trust_score is not None else 100}/200</code>\n"
        f"⚠️ <b>عدد المخالفات:</b> <code>{user.violations_count or 0}</code>"
    )

    keyboard = [
        [InlineKeyboardButton(toggle_btn_label, callback_data="toggle_notifs")],
        [InlineKeyboardButton("🌐 تغيير اللغة", callback_data="open_lang_menu")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def toggle_notifications_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        if not user:
            return
        current = True if user.notifications_enabled is None else bool(user.notifications_enabled)
        user.notifications_enabled = not current
        new_state = user.notifications_enabled
        await session.commit()

    await query.answer("🔔 تم تفعيل التذكيرات." if new_state else "🔕 تم إيقاف التذكيرات.", show_alert=True)
    await show_user_settings(update, context)
