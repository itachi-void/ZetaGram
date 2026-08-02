from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select, func
from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask, Voucher
from config import ADMIN_IDS

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    async with AsyncSessionLocal() as session:
        users_count = (await session.execute(select(func.count(User.telegram_id)))).scalar() or 0
        tasks_count = (await session.execute(select(func.count(Task.id)))).scalar() or 0
        active_tasks = (await session.execute(select(func.count(Task.id)).where(Task.status == "active"))).scalar() or 0
        completed_tasks = (await session.execute(select(func.count(UserTask.id)))).scalar() or 0

    text = (
        f"📊 **لوحة إحصائيات الأدمن:**\n\n"
        f"👥 **إجمالي المستخدمين:** {users_count:,}\n"
        f"📌 **إجمالي المهام:** {tasks_count:,}\n"
        f"🟢 **المهام النشطة:** {active_tasks:,}\n"
        f"✅ **المهام المنفذة:** {completed_tasks:,}\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def add_task_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Format: /addtask <type> <reward> <qty> <target_url> <chat_id> <title...>
    Types: channel, group, post, bot_normal, bot_webapp, bot_conditions
    Example: /addtask channel 1111 100 https://t.me/MyChannel @MyChannel قناة الأخبار الرسمية
    """
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    args = context.args
    if len(args) < 6:
        await update.message.reply_text(
            "⚠️ **الاستخدام الخاطئ!**\n"
            "التعليمة الصحيحة:\n"
            "`/addtask <type> <reward> <qty> <target_url> <chat_id> <title...>`\n\n"
            "أنواع المهام المتاحة:\n`channel`, `group`, `post`, `bot_normal`, `bot_webapp`, `bot_conditions`",
            parse_mode="Markdown"
        )
        return

    task_type = args[0]
    reward = int(args[1])
    qty = int(args[2])
    target_url = args[3]
    chat_id = args[4]
    title = " ".join(args[5:])

    async with AsyncSessionLocal() as session:
        new_task = Task(
            title=title,
            task_type=task_type,
            target_url=target_url,
            chat_id=chat_id,
            reward_grams=reward,
            total_qty=qty,
            created_by=user_id
        )
        session.add(new_task)
        await session.commit()

    await update.message.reply_text(f"🎉 تم إضافة المهمة بنجاح لرقم ID: {new_task.id}")
