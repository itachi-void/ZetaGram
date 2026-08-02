from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import User

BONUS_AMOUNT = 100 # 100 Grams daily reward

async def claim_daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.utcnow()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if not user:
            await update.message.reply_text("❌ يرجى كتابة /start لتسجيل حسابك أولاً.")
            return

        if user.last_daily_bonus:
            elapsed = now - user.last_daily_bonus
            if elapsed < timedelta(hours=24):
                remaining = timedelta(hours=24) - elapsed
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                await update.message.reply_text(
                    f"⌛ **لقد حصلت على مكافأتك اليومية بالفعل!**\n\n"
                    f"يمكنك المطالبة بالمكافأة القادمة بعد: **{hours} ساعة و {minutes} دقيقة**.",
                    parse_mode="Markdown"
                )
                return

        # Grant daily bonus
        user.balance += BONUS_AMOUNT
        user.last_daily_bonus = now
        await session.commit()

        await update.message.reply_text(
            f"🎁 **مبروك! تم إضافة المكافأة اليومية إلى رصيدك!**\n\n"
            f"💰 **الهدية:** +{BONUS_AMOUNT:,} غرام\n"
            f"💳 **رصيدك الحالي:** {user.balance:,} غرام\n\n"
            f"عد غداً للحصول على مكافأة جديدة!",
            parse_mode="Markdown"
        )
