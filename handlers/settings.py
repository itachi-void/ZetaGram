from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select

from database.db import AsyncSessionLocal
from database.models import User
from utils.gatekeeper import enforce_user_access
from utils.i18n import get_text, get_user_lang, get_vip_title
from utils.html_utils import esc


async def show_user_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
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

    lang = get_user_lang(user or db_user)
    notif_on = True if user.notifications_enabled is None else bool(user.notifications_enabled)
    notif_str = get_text(lang, "settings_notif_on" if notif_on else "settings_notif_off")
    toggle_btn_label = get_text(
        lang, "settings_btn_disable_notif" if notif_on else "settings_btn_enable_notif"
    )
    lvl_title = get_vip_title(lang, user.vip_level)

    text = get_text(
        lang,
        "settings_title",
        notif_str=notif_str,
        lang=esc(lang),
        level_title=esc(lvl_title),
        trust_score=user.trust_score if user.trust_score is not None else 100,
        violations=user.violations_count or 0,
    )

    keyboard = [
        [InlineKeyboardButton(toggle_btn_label, callback_data="toggle_notifs")],
        [InlineKeyboardButton(get_text(lang, "settings_btn_change_lang"), callback_data="open_lang_menu")],
        [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")],
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
        lang = get_user_lang(user)
        current = True if user.notifications_enabled is None else bool(user.notifications_enabled)
        user.notifications_enabled = not current
        new_state = user.notifications_enabled
        await session.commit()

    await query.answer(
        get_text(lang, "settings_notif_enabled_alert" if new_state else "settings_notif_disabled_alert"),
        show_alert=True,
    )
    await show_user_settings(update, context)
