import random
import asyncio
from datetime import timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select

from database.db import AsyncSessionLocal
from database.models import User, Transaction
from utils.security import user_lock_manager
from utils.gatekeeper import enforce_user_access
from utils.i18n import get_text, get_user_lang
from utils.html_utils import utcnow

PRIZES = [
    (50, 40),
    (100, 30),
    (250, 15),
    (500, 10),
    (1000, 4),
    (2000, 1),
]


def pick_prize():
    rewards, weights = zip(*PRIZES)
    return random.choices(rewards, weights=weights, k=1)[0]


async def spin_wheel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    now = utcnow()

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not user:
                await update.message.reply_text(get_text(lang, "not_registered"))
                return

            lang = get_user_lang(user)

            if user.last_spin_time:
                elapsed = now - user.last_spin_time
                if elapsed < timedelta(hours=24):
                    remaining = timedelta(hours=24) - elapsed
                    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)

                    await update.message.reply_text(
                        get_text(lang, "spin_already_used", hours=hours, minutes=minutes),
                        parse_mode="HTML",
                    )
                    return

            prize = pick_prize()
            user.balance += prize
            user.last_spin_time = now

            session.add(
                Transaction(
                    user_id=user_id,
                    trans_type="spin",
                    amount=prize,
                    description="جائزة عجلة الحظ",
                )
            )
            await session.commit()
            new_balance = user.balance

    msg = await update.message.reply_text(
        get_text(lang, "spin_rolling_1"),
        parse_mode="HTML",
    )
    await asyncio.sleep(1.0)

    await msg.edit_text(
        get_text(lang, "spin_rolling_2"),
        parse_mode="HTML",
    )
    await asyncio.sleep(1.0)

    is_jackpot = prize >= 1000
    badge = get_text(lang, "spin_jackpot_badge") if is_jackpot else ""

    text = get_text(
        lang,
        "spin_result",
        badge=badge,
        prize=prize,
        balance=new_balance,
    )

    keyboard = [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")]]
    await msg.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
