from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func
from database.db import AsyncSessionLocal
from database.models import User, UserTask
from utils.i18n import get_text

async def show_referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    async with AsyncSessionLocal() as session:
        # Get count of referred users
        referred_users_stmt = select(User).where(User.referred_by == user_id)
        referred_users = (await session.execute(referred_users_stmt)).scalars().all()
        total_invites = len(referred_users)

        # Count active invited users who completed >= 3 tasks
        active_invites = 0
        for ref_u in referred_users:
            task_cnt = (await session.execute(
                select(func.count(UserTask.id)).where(UserTask.user_id == ref_u.telegram_id, UserTask.status == "completed")
            )).scalar() or 0
            if task_cnt >= 3:
                active_invites += 1

        total_earned = active_invites * 250

    text = (
        f"👥 **نظام دعوة الأصدقاء والمكافآت (Referral System):**\n\n"
        f"قم بدعوة أصدقائك لاستخدام البوت واكسب مكافآت ضخمة وحقيقية!\n\n"
        f"📊 **إحصائيات إحالاتك:**\n"
        f"• 👥 **إجمالي المدعوين:** `{total_invites}` عضو\n"
        f"• ⚡ **الأصدقاء النشطون (أكملوا 3 مهام):** `{active_invites}` عضو\n"
        f"• 💰 **إجمالي الأرباح المكتسبة:** `{total_earned:,}` غرام\n\n"
        f"🎁 **تفاصيل المكافآت:**\n"
        f"• يحصل صديقك على **+100 غرام** فور الانضمام واجتياز الكابتشا.\n"
        f"• تحصُل أنت على **+250 غرام** فور إكمال صديقك لـ 3 مهام.\n"
        f"• تحصل على **10% عمولة دائمية** من أرباح أصدقائك!\n\n"
        f"🔗 **رابط الدعوة الخاص بك:**\n"
        f"`{ref_link}`"
    )

    share_url = f"https://t.me/share/url?url={ref_link}&text=اشترك%20في%20بوت%20GramPulse%20لكسب%20وترويج%20القنوات%20والأرباح!"

    keyboard = [
        [InlineKeyboardButton("📤 مشاركة رابط الدعوة", url=share_url)],
        [InlineKeyboardButton("👥 قائمة المدعوين", callback_data="my_referrals_list")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]
    ]

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True)

async def show_referrals_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    async with AsyncSessionLocal() as session:
        referred_users = (await session.execute(select(User).where(User.referred_by == user_id))).scalars().all()

        if not referred_users:
            text = "👥 **قائمة المدعوين:**\n\nلم يقم أحد بالانضمام عبر رابطك بعد. انشر رابطك واكسب المكافآت!"
        else:
            text = f"👥 **قائمة الأعضاء المدعوين ({len(referred_users)}):**\n\n"
            for idx, u in enumerate(referred_users, start=1):
                name = u.first_name or u.username or f"User {u.telegram_id}"
                task_cnt = (await session.execute(
                    select(func.count(UserTask.id)).where(UserTask.user_id == u.telegram_id, UserTask.status == "completed")
                )).scalar() or 0
                status_icon = "✅ (نشط)" if task_cnt >= 3 else f"⌛ ({task_cnt}/3 مهام)"
                text += f"{idx}. {name} — {status_icon}\n"

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="show_referral_main")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
