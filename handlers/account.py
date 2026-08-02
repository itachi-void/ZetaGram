from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func
from database.db import AsyncSessionLocal
from database.models import User, UserTask
from config import BOT_TOKEN

async def show_account_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_info = await context.bot.get_me()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if not user:
            await update.message.reply_text("❌ لم يتم العثور على حسابك. يرجى كتابة /start لتسجيل الحساب.")
            return

        # Count completed tasks
        completed_count = (await session.execute(
            select(func.count(UserTask.id)).where(UserTask.user_id == user_id, UserTask.status == "completed")
        )).scalar() or 0

        # Count referrals
        referrals_count = (await session.execute(
            select(func.count(User.telegram_id)).where(User.referred_by == user_id)
        )).scalar() or 0

    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    text = (
        f"📱 **معلومات حسابك في PR GRAM:**\n\n"
        f"🆔 **معرف الحساب:** `{user.telegram_id}`\n"
        f"👤 **الاسم:** {user.first_name}\n"
        f"💰 **الرصيد الحرفي:** `{user.balance:,}` غرام\n"
        f"✅ **المهام المكتملة:** {completed_count}\n"
        f"👥 **عدد الإحالات:** {referrals_count}\n\n"
        f"🔗 **رابط الإحالة الخاص بك:**\n"
        f"`{ref_link}`\n\n"
        f"🎁 شارك رابط الإحالة مع أصدقائك واكسب نقاط إضافية على كل عضو ينضم!"
    )

    keyboard = [
        [InlineKeyboardButton("➕ شحن الرصيد", callback_data="deposit_funds"), InlineKeyboardButton("💸 سحب الأرباح", callback_data="withdraw_funds")],
        [InlineKeyboardButton("🏷️ شيكاتي", callback_data="my_vouchers")]
    ]

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
