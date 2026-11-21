from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func, and_

from config import BOT_NAME, REFERRAL_JOIN_BONUS, REFERRAL_ACTIVE_BONUS
from database.db import AsyncSessionLocal
from database.models import User, UserTask, Transaction
from utils.gatekeeper import enforce_user_access
from utils.i18n import get_text, get_user_lang
from utils.html_utils import esc


async def show_referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    async with AsyncSessionLocal() as session:
        task_counts_sub = (
            select(UserTask.user_id, func.count(UserTask.id).label("cnt"))
            .where(UserTask.status.in_(["completed", "approved"]))
            .group_by(UserTask.user_id)
            .subquery()
        )
        rows = (
            await session.execute(
                select(User.telegram_id, func.coalesce(task_counts_sub.c.cnt, 0))
                .outerjoin(task_counts_sub, User.telegram_id == task_counts_sub.c.user_id)
                .where(User.referred_by == user_id)
            )
        ).all()

        total_invites = len(rows)
        active_invites = sum(1 for _, cnt in rows if cnt >= 3)

        total_earned = (
            await session.execute(
                select(func.sum(Transaction.amount)).where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.trans_type.in_(["referral_milestone", "referral_commission"]),
                    )
                )
            )
        ).scalar() or 0

    text = get_text(
        lang,
        "ref_menu",
        bot_name=esc(BOT_NAME),
        total_invites=total_invites,
        active_invites=active_invites,
        total_earned=total_earned,
        join_bonus=REFERRAL_JOIN_BONUS,
        active_bonus=REFERRAL_ACTIVE_BONUS,
        ref_link=esc(ref_link),
    )

    share_text = quote(get_text(lang, "ref_share_text", bot_name=BOT_NAME))
    share_url = f"https://t.me/share/url?url={quote(ref_link)}&text={share_text}"

    keyboard = [
        [InlineKeyboardButton(get_text(lang, "ref_btn_share"), url=share_url)],
        [InlineKeyboardButton(get_text(lang, "ref_btn_list"), callback_data="my_referrals_list")],
        [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")],
    ]

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True
        )


async def show_referrals_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    lang = get_user_lang(db_user)

    async with AsyncSessionLocal() as session:
        task_counts_sub = (
            select(UserTask.user_id, func.count(UserTask.id).label("cnt"))
            .where(UserTask.status.in_(["completed", "approved"]))
            .group_by(UserTask.user_id)
            .subquery()
        )
        rows = (
            await session.execute(
                select(
                    User.telegram_id,
                    User.first_name,
                    User.username,
                    func.coalesce(task_counts_sub.c.cnt, 0),
                )
                .outerjoin(task_counts_sub, User.telegram_id == task_counts_sub.c.user_id)
                .where(User.referred_by == user_id)
                .order_by(User.created_at.desc())
                .limit(30)
            )
        ).all()

    if not rows:
        text = get_text(lang, "ref_list_empty")
    else:
        text = get_text(lang, "ref_list_title", count=len(rows))
        for idx, (uid, fname, uname, task_cnt) in enumerate(rows, start=1):
            name = esc(fname or uname or f"User {uid}")
            status_str = (
                get_text(lang, "ref_status_active")
                if task_cnt >= 3
                else get_text(lang, "ref_status_pending", cnt=task_cnt)
            )
            text += f"{idx}. {name} — {status_str}\n"

    keyboard = [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="show_referral_main")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
