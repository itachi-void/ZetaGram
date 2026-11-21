from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from config import BOT_NAME, DAILY_QUEST_TARGET
from database.db import AsyncSessionLocal
from database.models import User, UserTask
from handlers.levels import LEVEL_TITLES
from utils.gatekeeper import enforce_user_access
from utils.html_utils import esc, utcnow


async def show_account_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    user_id = update.effective_user.id
    bot_info = await context.bot.get_me()
    today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        if not user:
            await update.message.reply_text("❌ لم يتم العثور على حسابك. يرجى كتابة /start لتسجيل الحساب.")
            return

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
    level_title = LEVEL_TITLES.get(user.vip_level or 1, "🥉 مبتدئ")
    quest_progress = min(today_count, DAILY_QUEST_TARGET)

    text = (
        f"📱 <b>معلومات حسابك في {esc(BOT_NAME)}:</b>\n\n"
        f"🆔 <b>معرف الحساب:</b> <code>{user.telegram_id}</code>\n"
        f"👤 <b>الاسم:</b> {esc(user.first_name)}\n"
        f"🏅 <b>المستوى:</b> {esc(level_title)}\n"
        f"🛡️ <b>نقاط الثقة:</b> <code>{user.trust_score if user.trust_score is not None else 100}/200</code>\n"
        f"🔥 <b>سلسلة الدخول اليومي:</b> <code>{user.daily_streak or 0}</code> يوم\n"
        f"🎯 <b>التحدي اليومي:</b> <code>{quest_progress}/{DAILY_QUEST_TARGET}</code> مهام\n"
        f"💰 <b>الرصيد:</b> <code>{user.balance:,}</code> غرام\n"
        f"✅ <b>المهام المكتملة:</b> {completed_count}\n"
        f"👥 <b>عدد الإحالات:</b> {referrals_count}\n\n"
        f"🔗 <b>رابط الإحالة الخاص بك:</b>\n"
        f"<code>{esc(ref_link)}</code>\n\n"
        f"🎁 شارك رابط الإحالة مع أصدقائك واكسب مكافآت فورية وعمولة 10%!"
    )

    keyboard = [
        [
            InlineKeyboardButton("🏅 الإنجازات والمستويات", callback_data="show_levels"),
            InlineKeyboardButton("📜 سجل المعاملات", callback_data="show_tx_history"),
        ],
        [
            InlineKeyboardButton("🏛️ الخزنة والاستثمار", callback_data="show_vault_menu"),
            InlineKeyboardButton("🎟️ اليانصيب والسحب", callback_data="show_raffle_menu"),
        ],
        [
            InlineKeyboardButton("💸 تحويل رصيد", callback_data="show_transfer_menu"),
            InlineKeyboardButton("🏷️ الشيكات والكوبونات", callback_data="my_vouchers"),
        ],
        [
            InlineKeyboardButton("🏆 لوحة المتصدرين", callback_data="show_leaderboard"),
            InlineKeyboardButton("⚙️ الإعدادات", callback_data="show_user_settings"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
