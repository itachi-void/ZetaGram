import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func
from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask, DisputeTicket, Transaction
from utils.security import is_admin_user

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    query = update.callback_query
    if query:
        await query.answer()

    text = (
        "⚙️ **لوحة أدمن GramPulse التفاعلية الرئيسية:**\n\n"
        "مرحباً بك عزيزي الأدمن 👋 اختر القسم المراد التحكم به من القائمة أدناه:"
    )

    keyboard = [
        [
            InlineKeyboardButton("📊 الإحصائيات العامة", callback_data="admin_stats_view"),
            InlineKeyboardButton("💾 تحميل النسخة الاحتياطية", callback_data="admin_backup_db")
        ],
        [
            InlineKeyboardButton("➕/➖ تعديل رصيد مستخدم", callback_data="admin_balance_help"),
            InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_ban_help")
        ],
        [
            InlineKeyboardButton("📑 إدارة المهام النشطة", callback_data="admin_tasks_manage"),
            InlineKeyboardButton("🎟️ تذاكر الاعتراض والنزاع", callback_data="admin_tickets_manage")
        ],
        [
            InlineKeyboardButton("📢 الاشتراك الإجباري", callback_data="admin_mand_subs_view"),
            InlineKeyboardButton("📢 الإذاعة العامة (Broadcast)", callback_data="admin_broadcast_help")
        ]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def admin_stats_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    query = update.callback_query
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        users_count = (await session.execute(select(func.count(User.telegram_id)))).scalar() or 0
        tasks_count = (await session.execute(select(func.count(Task.id)))).scalar() or 0
        active_tasks = (await session.execute(select(func.count(Task.id)).where(Task.status == "active"))).scalar() or 0
        completed_tasks = (await session.execute(select(func.count(UserTask.id)))).scalar() or 0
        open_tickets = (await session.execute(select(func.count(DisputeTicket.id)).where(DisputeTicket.status == "open"))).scalar() or 0

    text = (
        f"📊 **إحصائيات النظام الشاملة:**\n\n"
        f"👥 **إجمالي المستخدمين:** `{users_count:,}`\n"
        f"📌 **إجمالي المهام:** `{tasks_count:,}`\n"
        f"🟢 **المهام النشطة:** `{active_tasks:,}`\n"
        f"✅ **المهام المنفذة:** `{completed_tasks:,}`\n"
        f"🎟️ **تذاكر الاعتراض المفتوحة:** `{open_tickets:,}`\n"
    )

    keyboard = [[InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin_main_menu")]]
    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def admin_backup_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    query = update.callback_query
    if query:
        await query.answer()

    db_path = "bot.db"
    if not os.path.exists(db_path):
        await update.message.reply_text("❌ لم يتم العثور على ملف قاعدة البيانات bot.db.")
        return

    await context.bot.send_document(
        chat_id=user_id,
        document=open(db_path, "rb"),
        filename=f"bot_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db",
        caption="💾 **نسخة احتياطية كاملة لقاعدة بيانات البوت bot.db**",
        parse_mode="Markdown"
    )

async def admin_balance_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    query = update.callback_query
    await query.answer()
    text = (
        "➕/➖ **تعليمات تعديل رصيد مستخدم:**\n\n"
        "يمكنك إضافة أو خصم رصيد أي مستخدم عبر التعليمة التالية:\n"
        "`/setbalance <user_id> <المبلغ>`\n\n"
        "مثال للإضافة: `/setbalance 123456789 5000`\n"
        "مثال للخصم: `/setbalance 123456789 -2000`"
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_main_menu")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_setbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ **الاستخدام الخاطئ!**\n"
            "الصيغة: `/setbalance <user_id> <المبلغ>`",
            parse_mode="Markdown"
        )
        return

    try:
        target_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ يرجى أدخال أرقام صحيحة.")
        return

    async with AsyncSessionLocal() as session:
        target_user = (await session.execute(select(User).where(User.telegram_id == target_id))).scalar_one_or_none()
        if not target_user:
            await update.message.reply_text("❌ لم يتم العثور على هذا المستخدم في القاعدة.")
            return

        target_user.balance += amount
        tx = Transaction(
            user_id=target_id,
            trans_type="admin_adjust",
            amount=amount,
            description=f"تعديل بواسطة الأدمن {user_id}"
        )
        session.add(tx)
        await session.commit()

        await update.message.reply_text(
            f"✅ **تم تعديل الرصيد بنجاح!**\n"
            f"👤 المستهدف: `{target_id}`\n"
            f"💰 التغيير: `{amount:+,}` غرام\n"
            f"💳 الرصيد الجديد: `{target_user.balance:,}` غرام",
            parse_mode="Markdown"
        )

async def admin_ban_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    query = update.callback_query
    await query.answer()
    text = (
        "🚫 **تعليمات إدارة الحظر:**\n\n"
        "لحظر مستخدم لمدة معينة بالتهام:\n"
        "`/ban <user_id> <عدد_الأيام>` (مثال: `/ban 123456789 7`)\n\n"
        "لإلغاء حظر مستخدم:\n"
        "`/unban <user_id>` (مثال: `/unban 123456789`)"
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_main_menu")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text("الصيغة: `/ban <user_id> [عدد_الأيام]`", parse_mode="Markdown")
        return

    try:
        target_id = int(args[0])
        days = int(args[1]) if len(args) > 1 else 30
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال آيدي وعدد أيام صحيحة.")
        return

    async with AsyncSessionLocal() as session:
        target_user = (await session.execute(select(User).where(User.telegram_id == target_id))).scalar_one_or_none()
        if not target_user:
            await update.message.reply_text("❌ لم يتم العثور على هذا المستخدم.")
            return

        target_user.banned_until = datetime.utcnow() + timedelta(days=days)
        await session.commit()

    await update.message.reply_text(f"🚫 تم حظر العضو `{target_id}` لمدة {days} يوم.", parse_mode="Markdown")

async def handle_unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text("الصيغة: `/unban <user_id>`", parse_mode="Markdown")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال آيدي صحيح.")
        return

    async with AsyncSessionLocal() as session:
        target_user = (await session.execute(select(User).where(User.telegram_id == target_id))).scalar_one_or_none()
        if target_user:
            target_user.banned_until = None
            await session.commit()

    await update.message.reply_text(f"✅ تم إلغاء حظر العضو `{target_id}` بنجاح.", parse_mode="Markdown")

async def admin_tasks_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    query = update.callback_query
    await query.answer()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Task).order_by(Task.created_at.desc()).limit(10))
        tasks = result.scalars().all()

    text = "📑 **إدارة المهام النشطة (آخر 10 مهام):**\n\n"
    keyboard = []

    if not tasks:
        text += "لا توجد مهام مضافة في القاعدة."
    else:
        for t in tasks:
            status_icon = "🟢" if t.status == "active" else "🔴"
            text += f"{status_icon} **{t.title}** (ID: `{t.id}`)\n"
            text += f"النوع: `{t.task_type}` | المنفذ: `{t.completed_qty}/{t.total_qty}`\n\n"
            keyboard.append([
                InlineKeyboardButton(f"🗑️ حذف #{t.id}", callback_data=f"admin_deltask_{t.id}"),
                InlineKeyboardButton(f"⏯️ تبديل الحالة #{t.id}", callback_data=f"admin_toggletask_{t.id}")
            ])

    keyboard.append([InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin_main_menu")])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_admin_task_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    query = update.callback_query
    data = query.data
    if data.startswith("admin_deltask_"):
        t_id = int(data.replace("admin_deltask_", ""))
        async with AsyncSessionLocal() as session:
            t = (await session.execute(select(Task).where(Task.id == t_id))).scalar_one_or_none()
            if t:
                await session.delete(t)
                await session.commit()
                await query.answer("✅ تم حذف المهمة بنجاح", show_alert=True)
    elif data.startswith("admin_toggletask_"):
        t_id = int(data.replace("admin_toggletask_", ""))
        async with AsyncSessionLocal() as session:
            t = (await session.execute(select(Task).where(Task.id == t_id))).scalar_one_or_none()
            if t:
                t.status = "paused" if t.status == "active" else "active"
                await session.commit()
                await query.answer(f"✅ تم تغيير حالة المهمة إلى {t.status}", show_alert=True)

    await admin_tasks_manage(update, context)

async def admin_broadcast_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    query = update.callback_query
    await query.answer()
    text = (
        "📢 **إذاعة رسالة لجميع المستخدمين:**\n\n"
        "يمكنك إرسال إذاعة لجميع مستخدمي البوت عبر التعليمة التالية:\n"
        "`/broadcast <الرسالة>`\n\n"
        "أو قم بالرد على أي رسالة (نص، صورة، فيديو، ميديا) بالتعليمة:\n"
        "`/broadcast`"
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_main_menu")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    reply = update.message.reply_to_message
    broadcast_text = " ".join(context.args)

    if not reply and not broadcast_text:
        await update.message.reply_text("⚠️ يرجى كتابة نص الرسالة بعد `/broadcast` أو الرد على الرسالة المراد إذاعتها.")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User.telegram_id))
        all_user_ids = result.scalars().all()

    total = len(all_user_ids)
    success = 0
    failed = 0

    await update.message.reply_text(f"🚀 جاري بدء الإذاعة لـ {total:,} مستخدم...")

    for uid in all_user_ids:
        try:
            if reply:
                await reply.copy(chat_id=uid)
            else:
                await context.bot.send_message(chat_id=uid, text=broadcast_text, parse_mode="Markdown")
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await update.message.reply_text(
        f"✅ **تم الانتهاء من الإذاعة!**\n\n"
        f"🎯 الناجح: {success:,}\n"
        f"❌ الفاشل: {failed:,}",
        parse_mode="Markdown"
    )

async def add_task_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
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
