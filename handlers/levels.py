from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from config import VIP_PERKS
from database.db import AsyncSessionLocal
from database.models import User, UserTask, Transaction
from utils.security import user_lock_manager
from utils.gatekeeper import enforce_user_access
from utils.i18n import get_text, get_user_lang, get_vip_title, get_milestone_title
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

        lang = get_user_lang(user)
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
        level_title = get_vip_title(lang, lvl)

        text = get_text(
            lang,
            "levels_menu",
            level_title=esc(level_title),
            completed_tasks=completed_tasks_count,
            referrals=referrals_count,
            promo_fee=round(perks["promo_fee"] * 100, 1),
            transfer_fee=round(perks["transfer_fee"] * 100, 1),
            task_bonus=round(perks["task_bonus"] * 100, 1),
            vault_bonus=round(perks["vault_bonus"] * 100, 1),
        )

        keyboard = []
        for m in MILESTONES:
            ms_title = get_milestone_title(lang, m["id"])
            is_claimed = m["id"] in claimed
            tasks_ok = completed_tasks_count >= m["req_tasks"]
            refs_ok = referrals_count >= m["req_refs"]
            can_claim = tasks_ok and refs_ok and not is_claimed

            if is_claimed:
                btn_text = get_text(lang, "levels_btn_claimed", title=ms_title)
                cb = "ignore"
            elif can_claim:
                btn_text = get_text(lang, "levels_btn_claim", title=ms_title, reward=m["reward"])
                cb = f"claim_m_{m['id']}"
            else:
                btn_text = get_text(lang, "levels_btn_locked", title=ms_title, reward=m["reward"])
                cb = "ignore"

            keyboard.append([InlineKeyboardButton(btn_text, callback_data=cb)])

        keyboard.append([InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")])
        markup = InlineKeyboardMarkup(keyboard)

        if query:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
        else:
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def claim_milestone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    ms_id = query.data.replace("claim_m_", "")

    milestone = next((m for m in MILESTONES if m["id"] == ms_id), None)
    if not milestone:
        await query.answer(get_text(lang, "levels_err_unknown"), show_alert=True)
        return

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not user:
                return
            lang = get_user_lang(user)

            claimed = [c for c in (user.claimed_milestones or "").split(",") if c]
            if ms_id in claimed:
                await query.answer(get_text(lang, "levels_err_already"), show_alert=True)
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
                await query.answer(get_text(lang, "levels_err_requirements"), show_alert=True)
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
        get_text(lang, "levels_claimed_alert", reward=milestone["reward"]), show_alert=True
    )
    await show_levels_menu(update, context)
