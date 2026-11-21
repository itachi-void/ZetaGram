from datetime import timedelta
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select

from config import STREAK_REWARDS
from database.db import AsyncSessionLocal
from database.models import User, Transaction
from utils.security import user_lock_manager
from utils.gatekeeper import enforce_user_access
from utils.html_utils import utcnow


async def claim_daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    user_id = update.effective_user.id
    now = utcnow()

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not user:
                await update.message.reply_text("❌ يرجى كتابة /start لتسجيل حسابك أولاً.")
                return

            if user.last_daily_bonus:
                elapsed = now - user.last_daily_bonus
                if elapsed < timedelta(hours=24):
                    remaining = timedelta(hours=24) - elapsed
                    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)

                    await update.message.reply_text(
                        f"⌛ <b>لقد حصلت على مكافأتك اليومية بالفعل!</b>\n\n"
                        f"🔥 سلسلتك الحالية: <b>{user.daily_streak or 1} يوم</b>\n"
                        f"يمكنك المطالبة بالمكافأة القادمة بعد: <b>{hours} ساعة و {minutes} دقيقة</b>.",
                        parse_mode="HTML",
                    )
                    return

                # Reset streak if > 48 hours elapsed
                if elapsed <= timedelta(hours=48):
                    new_streak = (user.daily_streak or 0) + 1
                else:
                    new_streak = 1
            else:
                new_streak = 1

            streak_idx = min(new_streak - 1, len(STREAK_REWARDS) - 1)
            reward = STREAK_REWARDS[streak_idx]

            user.daily_streak = new_streak
            user.balance += reward
            user.last_daily_bonus = now

            session.add(
                Transaction(
                    user_id=user_id,
                    trans_type="daily_bonus",
                    amount=reward,
                    description=f"مكافأة يومية (سلسلة اليوم {new_streak})",
                )
            )
            await session.commit()
            new_balance = user.balance

    next_idx = min(new_streak, len(STREAK_REWARDS) - 1)
    next_reward = STREAK_REWARDS[next_idx]
    await update.message.reply_text(
        f"🎁 <b>مبروك! تم إضافة المكافأة اليومية إلى رصيدك!</b>\n\n"
        f"🔥 <b>سلسلة الدخول المتتالية:</b> اليوم <b>{new_streak}</b>\n"
        f"💰 <b>الهدية المستلمة:</b> +{reward:,} غرام\n"
        f"💳 <b>رصيدك الحالي:</b> {new_balance:,} غرام\n\n"
        f"✨ مكافأتك غداً ستكون: <b>+{next_reward:,} غرام</b>!",
        parse_mode="HTML",
    )
