from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from config import VIP_PERKS
from database.db import AsyncSessionLocal
from database.models import User, UserTask, Transaction
from utils.security import user_lock_manager
from utils.gatekeeper import enforce_user_access
from utils.html_utils import esc

LEVEL_TITLES = {lvl: info["title"] for lvl, info in VIP_PERKS.items()}

MILESTONES = [
    {"id": "tasks_10", "title": "إكمال 10 مهام", "req_tasks": 10, "req_refs": 0, "reward": 100, "level_up": 2},
    {"id": "tasks_50", "title": "إكمال 50 مهمة", "req_tasks": 50, "req_refs": 0, "reward": 500, "level_up": 2},
    {"id": "tasks_100", "title": "إكمال 100 مهمة", "req_tasks": 100, "req_refs": 0, "reward": 1000, "level_up": 3},
    {"id": "refs_10", "title": "دعوة 10 أصدقاء", "req_tasks": 0, "req_refs": 10, "reward": 1000, "level_up": 4},
]


async def show_levels_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    user_id = update.effective_user.id
    query = update.callback_query
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        if not user:
            return

        completed_tasks_count = (
            await session.execute(
                select(func.count(UserTask.id)).where(
                    UserTask.user_id == user_id,
                    UserTask.status.in_(["completed", "approved"]),
                )
            )
        ).scalar() or 0

        referrals_count = (
            await session.execute(
                select(func.count(User.telegram_id)).where(User.referred_by == user_id)
            )
        ).scalar() or 0

        claimed = [c for c in (user.claimed_milestones or "").split(",") if c]
        lvl = user.vip_level or 1
        perks = VIP_PERKS.get(lvl, VIP_PERKS[1])

        text = (
            f"🏅 <b>قسم الإنجازات ومستويات VIP:</b>\n\n"
            f"👤 <b>مستواك الحالي:</b> {esc(perks['title'])}\n"
            f"✅ <b>المهام المكتملة:</b> {completed_tasks_count}\n"
            f"👥 <b>الأعضاء المدعوين:</b> {referrals_count}\n\n"
            f"✨ <b>مزايا مستواك الفعلية:</b>\n"
            f"• 📣 عمولة الترويج: <code>{round(perks['promo_fee']*100, 1)}%</code>\n"
            f"• 💸 عمولة التحويل: <code>{round(perks['transfer_fee']*100, 1)}%</code>\n"
            f"• 💰 مكافأة إضافية على المهام: <code>+{round(perks['task_bonus']*100, 1)}%</code>\n"
            f"• 🏛️ عائد إضافي للخزنة: <code>+{round(perks['vault_bonus']*100, 1)}%</code>\n\n"
            f"🎁 <b>المكافآت والإنجازات المتاحة:</b>"
        )

        keyboard = []
        for m in MILESTONES:
            is_claimed = m["id"] in claimed
            tasks_ok = completed_tasks_count >= m["req_tasks"]
            refs_ok = referrals_count >= m["req_refs"]
            can_claim = tasks_ok and refs_ok and not is_claimed

            if is_claimed:
                btn_text = f"✅ {m['title']} (تم الاستلام)"
                cb = "ignore"
            elif can_claim:
                btn_text = f"🎁 استلام مكافأة: {m['title']} (+{m['reward']:,} غرام)"
                cb = f"claim_m_{m['id']}"
            else:
                btn_text = f"🔒 {m['title']} (+{m['reward']:,} غرام)"
                cb = "ignore"

            keyboard.append([InlineKeyboardButton(btn_text, callback_data=cb)])

        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")])
        markup = InlineKeyboardMarkup(keyboard)

        if query:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
        else:
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def claim_milestone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    ms_id = query.data.replace("claim_m_", "")

    milestone = next((m for m in MILESTONES if m["id"] == ms_id), None)
    if not milestone:
        await query.answer("❌ إنجاز غير معروف", show_alert=True)
        return

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not user:
                return

            claimed = [c for c in (user.claimed_milestones or "").split(",") if c]
            if ms_id in claimed:
                await query.answer("⚠️ لقد قمت باستلام هذه المكافأة مسبقاً!", show_alert=True)
                return

            completed_tasks_count = (
                await session.execute(
                    select(func.count(UserTask.id)).where(
                        UserTask.user_id == user_id,
                        UserTask.status.in_(["completed", "approved"]),
                    )
                )
            ).scalar() or 0

            referrals_count = (
                await session.execute(
                    select(func.count(User.telegram_id)).where(User.referred_by == user_id)
                )
            ).scalar() or 0

            if completed_tasks_count < milestone["req_tasks"] or referrals_count < milestone["req_refs"]:
                await query.answer("❌ لم تحقق متطلبات هذا الإنجاز بعد!", show_alert=True)
                return

            user.balance += milestone["reward"]
            if milestone["level_up"] > (user.vip_level or 1):
                user.vip_level = milestone["level_up"]

            claimed.append(ms_id)
            user.claimed_milestones = ",".join(claimed)

            session.add(
                Transaction(
                    user_id=user_id,
                    trans_type="reward",
                    amount=milestone["reward"],
                    description=f"مكافأة إنجاز: {milestone['title']}",
                )
            )
            await session.commit()

    await query.answer(
        f"🎉 مبروك! تم إضافة +{milestone['reward']:,} غرام وتحديث مستواك!", show_alert=True
    )
    await show_levels_menu(update, context)
