from datetime import timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func, and_

from config import LEADERBOARD_PRIZES
from database.db import AsyncSessionLocal
from database.models import User, UserTask
from utils.gatekeeper import enforce_user_access
from utils.html_utils import esc, utcnow


async def show_leaderboard(
    update: Update, context: ContextTypes.DEFAULT_TYPE, tab: str = "tasks"
):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    now = utcnow()
    this_monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    async with AsyncSessionLocal() as session:
        if tab == "refs":
            rows = (
                await session.execute(
                    select(User.referred_by, func.count(User.telegram_id).label("cnt"))
                    .where(and_(User.referred_by.isnot(None), User.created_at >= this_monday))
                    .group_by(User.referred_by)
                    .order_by(func.count(User.telegram_id).desc())
                    .limit(10)
                )
            ).all()
            my_score = (
                await session.execute(
                    select(func.count(User.telegram_id)).where(
                        and_(User.referred_by == user_id, User.created_at >= this_monday)
                    )
                )
            ).scalar() or 0
            title = "👥 <b>أفضل الداعين هذا الأسبوع:</b>"
            unit = "إحالة"
        else:
            rows = (
                await session.execute(
                    select(UserTask.user_id, func.count(UserTask.id).label("cnt"))
                    .where(
                        and_(
                            UserTask.status.in_(["completed", "approved"]),
                            UserTask.completed_at >= this_monday,
                        )
                    )
                    .group_by(UserTask.user_id)
                    .order_by(func.count(UserTask.id).desc())
                    .limit(10)
                )
            ).all()
            my_score = (
                await session.execute(
                    select(func.count(UserTask.id)).where(
                        and_(
                            UserTask.user_id == user_id,
                            UserTask.status.in_(["completed", "approved"]),
                            UserTask.completed_at >= this_monday,
                        )
                    )
                )
            ).scalar() or 0
            title = "✅ <b>أفضل منفذي المهام هذا الأسبوع:</b>"
            unit = "مهمة"

        uid_list = [r[0] for r in rows]
        names_map = {}
        if uid_list:
            users_rows = (
                await session.execute(
                    select(User.telegram_id, User.first_name, User.username).where(
                        User.telegram_id.in_(uid_list)
                    )
                )
            ).all()
            for uid, fname, uname in users_rows:
                names_map[uid] = fname or uname or f"User {uid}"

    medals = ["🥇", "🥈", "🥉"]
    lines = [
        "🏆 <b>لوحة المتصدرين الأسبوعية (Weekly Leaderboard)</b>\n",
        f"{title}\n",
    ]
    if not rows:
        lines.append("لا يوجد نشاط مسجل هذا الأسبوع بعد — كن أول المتصدرين!\n")
    else:
        for idx, (uid, cnt) in enumerate(rows):
            medal = medals[idx] if idx < 3 else f"#{idx + 1}"
            prize_note = (
                f" — 🎁 <code>+{LEADERBOARD_PRIZES[idx]:,}</code> غرام"
                if idx < len(LEADERBOARD_PRIZES)
                else ""
            )
            name = esc(names_map.get(uid, f"User {uid}"))
            lines.append(f"{medal} <b>{name}</b>: <code>{cnt}</code> {unit}{prize_note}")

    lines.append(
        f"\n📊 <b>نتيجتك هذا الأسبوع:</b> <code>{my_score}</code> {unit}\n"
        f"🎁 <b>جوائز المراكز الثلاثة الأولى:</b> "
        f"🥇 {LEADERBOARD_PRIZES[0]:,} | 🥈 {LEADERBOARD_PRIZES[1]:,} | 🥉 {LEADERBOARD_PRIZES[2]:,} غرام"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                ("✅ " if tab == "tasks" else "") + "أفضل المنفذين",
                callback_data="lb_tab_tasks",
            ),
            InlineKeyboardButton(
                ("✅ " if tab == "refs" else "") + "أفضل الداعين",
                callback_data="lb_tab_refs",
            ),
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")],
    ]

    text = "\n".join(lines)
    markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)
