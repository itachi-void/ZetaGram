from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func, and_

from config import BOT_NAME, REFERRAL_JOIN_BONUS, REFERRAL_ACTIVE_BONUS
from database.db import AsyncSessionLocal
from database.models import User, UserTask, Transaction
from utils.gatekeeper import enforce_user_access
from utils.html_utils import esc


async def show_referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    user_id = update.effective_user.id
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    async with AsyncSessionLocal() as session:
        # Single aggregated query (eliminates N+1 loop)
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

    text = (
        f"👥 <b>نظام دعوة الأصدقاء والمكافآت ({esc(BOT_NAME)}):</b>\n\n"
        f"قم بدعوة أصدقائك لاستخدام البوت واكسب مكافآت حقيقية ومستمرة!\n\n"
        f"📊 <b>إحصائيات إحالاتك:</b>\n"
        f"• 👥 <b>إجمالي المدعوين:</b> <code>{total_invites}</code> عضو\n"
        f"• ⚡ <b>الأصدقاء النشطون (أكملوا 3 مهام):</b> <code>{active_invites}</code> عضو\n"
        f"• 💰 <b>إجمالي أرباحك من الإحالات:</b> <code>{total_earned:,}</code> غرام\n\n"
        f"🎁 <b>تفاصيل المكافآت:</b>\n"
        f"• يحصل صديقك على <b>+{REFERRAL_JOIN_BONUS:,} غرام</b> فور الانضمام واجتياز الكابتشا.\n"
        f"• تحصل أنت على <b>+{REFERRAL_ACTIVE_BONUS:,} غرام</b> فور إكمال صديقك 3 مهام.\n"
        f"• وتحصل على <b>10% عمولة دائمة</b> من أرباح أصدقائك في كل مهمة!\n\n"
        f"🔗 <b>رابط الدعوة الخاص بك:</b>\n"
        f"<code>{esc(ref_link)}</code>"
    )

    share_text = quote(f"اشترك في بوت {BOT_NAME} لكسب الغرامات وترويج القنوات والمجموعات!")
    share_url = f"https://t.me/share/url?url={quote(ref_link)}&text={share_text}"

    keyboard = [
        [InlineKeyboardButton("📤 مشاركة رابط الدعوة", url=share_url)],
        [InlineKeyboardButton("👥 قائمة المدعوين", callback_data="my_referrals_list")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")],
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
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

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
        text = "👥 <b>قائمة المدعوين:</b>\n\nلم يقم أحد بالانضمام عبر رابطك بعد. انشر رابطك واكسب المكافآت!"
    else:
        text = f"👥 <b>قائمة الأعضاء المدعوين ({len(rows)}):</b>\n\n"
        for idx, (uid, fname, uname, task_cnt) in enumerate(rows, start=1):
            name = esc(fname or uname or f"User {uid}")
            status_icon = "✅ (نشط)" if task_cnt >= 3 else f"⌛ ({task_cnt}/3 مهام)"
            text += f"{idx}. {name} — {status_icon}\n"

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="show_referral_main")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
