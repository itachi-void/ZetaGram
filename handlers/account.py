from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func
from database.db import AsyncSessionLocal
from database.models import User, UserTask
from handlers.levels import LEVEL_TITLES

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
    level_title = LEVEL_TITLES.get(user.vip_level or 1, "🥉 مبتدئ")

    text = (
        f"📱 **معلومات حسابك في PR GRAM:**\n\n"
        f"🆔 **معرف الحساب:** `{user.telegram_id}`\n"
        f"👤 **الاسم:** {user.first_name}\n"
        f"🏅 **المستوى:** {level_title}\n"
        f"💰 **الرصيد:** `{user.balance:,}` غرام\n"
        f"✅ **المهام المكتملة:** {completed_count}\n"
        f"👥 **عدد الإحالات:** {referrals_count}\n\n"
        f"🔗 **رابط الإحالة الخاص بك:**\n"
        f"`{ref_link}`\n\n"
        f"🎁 شارك رابط الإحالة مع أصدقائك واكسب نقاط إضافية على كل عضو ينضم!"
    )

    keyboard = [
        [
            InlineKeyboardButton("🏅 الإنجازات والمستويات", callback_data="show_levels"),
            InlineKeyboardButton("📜 سجل المعاملات", callback_data="show_tx_history")
        ],
        [
            InlineKeyboardButton("🏛️ الخزنة والاستثمار", callback_data="show_vault_menu"),
            InlineKeyboardButton("🎟️ اليانصيب والسحب", callback_data="show_raffle_menu")
        ],
        [
            InlineKeyboardButton("💸 تحويل رصيد", callback_data="show_transfer_menu"),
            InlineKeyboardButton("🏷️ الشيكات والكوبونات", callback_data="my_vouchers")
        ]
    ]

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
