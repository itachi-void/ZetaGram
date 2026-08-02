import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import User

# Prize pools with probability weights
PRIZES = [
    (50, 40),     # 50 Grams (40% chance)
    (100, 30),    # 100 Grams (30% chance)
    (250, 15),    # 250 Grams (15% chance)
    (500, 10),    # 500 Grams (10% chance)
    (1000, 4),    # 1000 Grams (4% chance)
    (2000, 1),    # 2000 Grams Jackpot (1% chance)
]

def pick_prize():
    rewards, weights = zip(*PRIZES)
    return random.choices(rewards, weights=weights, k=1)[0]

async def spin_wheel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.utcnow()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if not user:
            await update.message.reply_text("❌ يرجى كتابة /start لتسجيل حسابك أولاً.")
            return

        if user.last_spin_time:
            elapsed = now - user.last_spin_time
            if elapsed < timedelta(hours=24):
                remaining = timedelta(hours=24) - elapsed
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                await update.message.reply_text(
                    f"⌛ **لقد استخدمت لفة اليوم بالفعل!**\n\n"
                    f"يمكنك تدوير عجلة الحظ مجدداً بعد: **{hours} ساعة و {minutes} دقيقة**.",
                    parse_mode="Markdown"
                )
                return

        # Pick prize and update user balance
        prize = pick_prize()
        user.balance += prize
        user.last_spin_time = now
        await session.commit()

    # Wheel spinning animation
    msg = await update.message.reply_text("🎰 **جاري تدوير عجلة الحظ...**\n\n🌀 `[ 100 | 500 | 50 | 1000 | 250 | 2000 ]` 🌀")
    await asyncio.sleep(1.2)

    await msg.edit_text("🎰 **جاري التدوير... ⚡**\n\n🌀 `[ 250 | 2000 | 50 | 500 | 1000 ]` 🌀", parse_mode="Markdown")
    await asyncio.sleep(1.2)

    # Final Result
    is_jackpot = prize >= 1000
    badge = "🎉 **الجائزة الكبرى (JACKPOT)!** 🎉\n" if is_jackpot else ""

    text = (
        f"🎰 **نتيجة عجلة الحظ:**\n\n"
        f"{badge}"
        f"🎁 **مبروك! فزت بـ:** `+{prize:,}` غرام!\n"
        f"💳 **رصيدك الحالي:** `{user.balance:,}` غرام\n\n"
        f"عد غداً لتدوير العجلة والحصول على الجائزة القادمة! 🎡"
    )

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]]
    await msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
