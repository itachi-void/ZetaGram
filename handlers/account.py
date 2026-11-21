from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from config import BOT_NAME, DAILY_QUEST_TARGET
from database.db import AsyncSessionLocal
from database.models import User, UserTask
from utils.gatekeeper import enforce_user_access
from utils.i18n import get_text, get_user_lang, get_vip_title
from utils.html_utils import esc, utcnow


async def show_account_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    bot_info = await context.bot.get_me()
    today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        if not user:
            await update.message.reply_text(get_text(lang, "not_registered"))
            return

        lang = get_user_lang(user)
        completed_count = (
            await session.execute(
                select(func.count(UserTask.id)).where(
                    UserTask.user_id == user_id,
                    UserTask.status.in_(["completed", "approved"]),
                )
            )
        ).scalar() or 0

        today_count = (
            await session.execute(
                select(func.count(UserTask.id)).where(
                    UserTask.user_id == user_id,
                    UserTask.status.in_(["completed", "approved"]),
                    UserTask.completed_at >= today_start,
                )
            )
        ).scalar() or 0

        referrals_count = (
            await session.execute(
                select(func.count(User.telegram_id)).where(User.referred_by == user_id)
            )
        ).scalar() or 0

    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    level_title = get_vip_title(lang, user.vip_level)
    quest_progress = min(today_count, DAILY_QUEST_TARGET)

    text = get_text(
        lang,
        "account_summary",
        bot_name=esc(BOT_NAME),
        telegram_id=user.telegram_id,
        first_name=esc(user.first_name or ""),
        level_title=esc(level_title),
        trust_score=user.trust_score if user.trust_score is not None else 100,
        streak=user.daily_streak or 0,
        quest_progress=quest_progress,
        quest_target=DAILY_QUEST_TARGET,
        balance=user.balance,
        completed_count=completed_count,
        referrals_count=referrals_count,
        ref_link=esc(ref_link),
    )

    keyboard = [
        [
            InlineKeyboardButton(get_text(lang, "account_btn_levels"), callback_data="show_levels"),
            InlineKeyboardButton(get_text(lang, "account_btn_history"), callback_data="show_tx_history"),
        ],
        [
            InlineKeyboardButton(get_text(lang, "account_btn_vault"), callback_data="show_vault_menu"),
            InlineKeyboardButton(get_text(lang, "account_btn_raffle"), callback_data="show_raffle_menu"),
        ],
        [
            InlineKeyboardButton(get_text(lang, "account_btn_transfer"), callback_data="show_transfer_menu"),
            InlineKeyboardButton(get_text(lang, "account_btn_vouchers"), callback_data="my_vouchers"),
        ],
        [
            InlineKeyboardButton(get_text(lang, "account_btn_leaderboard"), callback_data="show_leaderboard"),
            InlineKeyboardButton(get_text(lang, "account_btn_settings"), callback_data="show_user_settings"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
