import math
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, and_, func
from database.db import AsyncSessionLocal
from database.models import Task, User, UserTask
from utils.telegram_api import check_user_subscription
from utils.pagination import build_pagination_keyboard


PAGE_SIZE = 10

async def handle_task_list(update: Update, context: ContextTypes.DEFAULT_TYPE, task_type: str, page: int = 1):
    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        # Get tasks user hasn't completed yet
        completed_task_ids_res = await session.execute(
            select(UserTask.task_id).where(UserTask.user_id == user_id)
        )
        completed_ids = [r[0] for r in completed_task_ids_res.all()]

        # Query active tasks of task_type not completed by user
        stmt = select(Task).where(
            and_(
                Task.task_type == task_type,
                Task.status == "active",
                Task.id.not_in(completed_ids) if completed_ids else True
            )
        ).order_by(Task.reward_grams.desc())

        result = await session.execute(stmt)
        all_tasks = result.scalars().all()

    total_items = len(all_tasks)
    total_pages = max(1, math.ceil(total_items / PAGE_SIZE))
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_tasks = all_tasks[start_idx:end_idx]

    # Build Header Message based on type
    if task_type in ["channel", "group"]:
        header = (
            "اضغط الأزرار لاختيار المهمة.\n\n"
            "⚠️ يُمنع إلغاء الاشتراك قبل 7 أيام من القنوات/المجموعات.\n"
            "وإلا، سيتم حظر قدرتك على إكمال المهام، وإلغاء الأموال المكتسبة."
        )
    elif task_type == "post":
        header = (
            "لكسب الغرامات شاهد المنشورات بالضغط على الأزرار.\n\n"
            "انتباه! بعض المنشورات طويلة، قم بالتمرير للأعلى والأسفل."
        )
    elif task_type in ["reaction_random", "reaction_fixed"]:
        header = (
            "اختر مهمة عبر الأزرار للانتقال إلى البوت وتأكيده ثم التقط لقطة شاشة لتأكيد التنفيذ.\n\n"
            "⚠️ يُمنع حظر البوت خلال 7 أيام، وإلا قد تتعرض للغرامة!\n"
            "لكسب الغرامات عليك التفاعل مع المنشور.\n"
            "اختر مهمة من الأزرار للانتقال إلى المنشور.\n"
            "أضف التفاعل تفاعل ثم التقط لقطة شاشة كدليل."
        )
    else:
        header = (
            "اختر مهمة عبر الأزرار للانتقال إلى البوت وتأكيده ثم التقط لقطة شاشة لتأكيد التنفيذ.\n\n"
            "⚠️ يُمنع حظر البوت خلال 7 أيام، وإلا قد تتعرض للغرامة!"
        )

    items_buttons = []
    if not page_tasks:
        items_buttons.append([InlineKeyboardButton("❌ لا توجد مهام متاحة حالياً", callback_data="ignore")])
    else:
        for t in page_tasks:
            if task_type in ["channel", "group"]:
                row = [
                    InlineKeyboardButton(f"🔄 فحص", callback_data=f"check_task_{t.id}"),
                    InlineKeyboardButton(f"اشتراك | +{t.reward_grams:,} 💰", url=t.target_url)
                ]
            elif task_type == "post":
                row = [
                    InlineKeyboardButton(f"💰 مشاهدة منشور +{t.reward_grams:,} غرام", url=t.target_url)
                ]
            elif task_type in ["reaction_random", "reaction_fixed"]:
                row = [
                    InlineKeyboardButton(f"💰 بدون مراجعة تفاعل | +{t.reward_grams:,} غرام", url=t.target_url)
                ]
            else:
                row = [
                    InlineKeyboardButton(f"💰 بدون مراجعة 🤖 الانتقال إلى البوت | +{t.reward_grams:,} غرام", url=t.target_url)
                ]
            items_buttons.append(row)


    reply_markup = build_pagination_keyboard(
        items_buttons=items_buttons,
        current_page=page,
        total_pages=total_pages,
        category_code=task_type,
        back_callback="earnings_menu"
    )

    if query:
        await query.edit_message_text(header, reply_markup=reply_markup)
    else:
        await update.message.reply_text(header, reply_markup=reply_markup)

async def check_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    task_id = int(query.data.split("_")[-1])

    async with AsyncSessionLocal() as session:
        # Check user ban status
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if user and user.banned_until and datetime.utcnow() < user.banned_until:
            ban_str = user.banned_until.strftime("%Y-%m-%d %H:%M UTC")
            await query.answer(f"❌ أنت محظور حالياً من تنفيذ المهام حتى ({ban_str}) بسبب مخالفات إلغاء الاشتراك!", show_alert=True)
            return

        # Check task status
        task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
        if not task or task.status != "active":
            await query.answer("❌ هذه المهمة غير متاحة الآن أو تم انتهائها.", show_alert=True)
            return

        already_done = (await session.execute(
            select(UserTask).where(and_(UserTask.user_id == user_id, UserTask.task_id == task_id))
        )).scalar_one_or_none()

        if already_done:
            await query.answer("⚠️ لقد قمت بإكمال هذه المهمة بالفعل!", show_alert=True)
            return

        # Perform subscription verification
        if task.chat_id:
            is_subbed = await check_user_subscription(context.bot, task.chat_id, user_id)
            if not is_subbed:
                await query.answer("❌ لم يتم التحقق من الانضمام بعد! يرجى الاشتراك في القناة/المجموعة ثم الضغط على فحص.", show_alert=True)
                return

        # Record completion & reward user
        if user:
            user.balance += task.reward_grams

        task.completed_qty += 1
        if task.completed_qty >= task.total_qty:
            task.status = "completed"

        submission = UserTask(user_id=user_id, task_id=task_id, status="completed")
        session.add(submission)

        # Check for 3-task referral reward trigger
        user_tasks_count = (await session.execute(
            select(func.count(UserTask.id)).where(UserTask.user_id == user_id)
        )).scalar() or 0

        if user_tasks_count == 3 and user and user.referred_by:
            referrer = (await session.execute(select(User).where(User.telegram_id == user.referred_by))).scalar_one_or_none()
            if referrer:
                referrer.balance += 250 # +250 Grams referral reward
                try:
                    await context.bot.send_message(
                        chat_id=referrer.telegram_id,
                        text=f"🎉 **مبروك!** لقد أكمل صديقك الموصى به 3 مهام، وتم إضافة +250 غرام إلى رصيدك!",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass

        await session.commit()

        await query.answer(f"🎉 تم التحقق بنجاح! تم إضافة +{task.reward_grams:,} غرام إلى رصيدك.", show_alert=True)

        # Refresh tasks view
        await handle_task_list(update, context, task.task_type)

