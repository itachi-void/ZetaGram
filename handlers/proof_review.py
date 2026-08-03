from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, and_
from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask, Transaction, DisputeTicket
from config import ADMIN_IDS

async def process_proof_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when a user sends a photo while performing a proof-based task.
    Expects context.user_data['pending_task_id'] to be set.
    """
    user_id = update.effective_user.id
    task_id = context.user_data.get("pending_task_id")

    if not task_id:
        # Check if user is replying/resubmitting for a revision
        revision_ut_id = context.user_data.get("revision_ut_id")
        if revision_ut_id:
            return await process_revision_photo(update, context, revision_ut_id)
        return False

    photo = update.message.photo[-1]
    file_id = photo.file_id

    async with AsyncSessionLocal() as session:
        task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
        if not task or task.status != "active":
            await update.message.reply_text("❌ المهمة غير متاحة حالياً.")
            context.user_data.pop("pending_task_id", None)
            return True

        # Create or update UserTask record with status 'pending_approval'
        ut = (await session.execute(
            select(UserTask).where(and_(UserTask.user_id == user_id, UserTask.task_id == task_id))
        )).scalar_one_or_none()

        if ut:
            ut.status = "pending_approval"
            ut.proof_file_id = file_id
        else:
            ut = UserTask(
                user_id=user_id,
                task_id=task_id,
                status="pending_approval",
                proof_file_id=file_id
            )
            session.add(ut)

        await session.commit()
        ut_id = ut.id

    context.user_data.pop("pending_task_id", None)
    await update.message.reply_text("✅ **تم استلام صورة الإثبات بنجاح!**\nتم إرسال الإثبات لصاحب المهمة للمراجعة.", parse_mode="Markdown")

    # Send photo & approval keyboard to task creator
    creator_id = task.created_by
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول ودفع", callback_data=f"proof_approve_{ut_id}"),
            InlineKeyboardButton("❌ رفض المعاملة", callback_data=f"proof_reject_{ut_id}")
        ],
        [
            InlineKeyboardButton("🔄 طلب إعادة مراجعة جديدة", callback_data=f"proof_revision_{ut_id}")
        ]
    ]
    caption = (
        f"📩 **إثبات تنفيذ جديد لمهمتك!**\n\n"
        f"📌 المهمة: {task.title}\n"
        f"👤 المنفذ: `{user_id}`\n"
        f"💰 المكافأة: {task.reward_grams:,} غرام\n\n"
        f"يرجى المعاينة واختيار الإجراء المناسب:"
    )

    try:
        await context.bot.send_photo(
            chat_id=creator_id,
            photo=file_id,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Error notifying task creator {creator_id}: {e}")

    return True

async def process_revision_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, ut_id: int):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file_id = photo.file_id

    async with AsyncSessionLocal() as session:
        ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
        if not ut:
            await update.message.reply_text("❌ لم يتم العثور على المعاملة.")
            return True

        task = (await session.execute(select(Task).where(Task.id == ut.task_id))).scalar_one_or_none()
        ut.status = "pending_approval"
        ut.proof_file_id = file_id
        await session.commit()

    context.user_data.pop("revision_ut_id", None)
    await update.message.reply_text("✅ **تم إعادة إرسال صورة الإثبات بنجاح!**", parse_mode="Markdown")

    keyboard = [
        [
            InlineKeyboardButton("✅ قبول ودفع", callback_data=f"proof_approve_{ut_id}"),
            InlineKeyboardButton("❌ رفض المعاملة", callback_data=f"proof_reject_{ut_id}")
        ],
        [
            InlineKeyboardButton("🔄 طلب إعادة مراجعة جديدة", callback_data=f"proof_revision_{ut_id}")
        ]
    ]
    caption = (
        f"🔄 **تم إعادة تقديم إثبات جديد للمهمة!**\n\n"
        f"📌 المهمة: {task.title if task else ''}\n"
        f"👤 المنفذ: `{user_id}`\n\n"
        f"يرجى المراجعة واتخاذ الإجراء:"
    )

    try:
        await context.bot.send_photo(
            chat_id=task.created_by,
            photo=file_id,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        pass

    return True

async def handle_creator_proof_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    parts = data.split("_")
    action = parts[1] # approve, reject, revision
    ut_id = int(parts[2])

    async with AsyncSessionLocal() as session:
        ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
        if not ut:
            await query.answer("❌ لم يتم العثور على سجل هذه المهمة.", show_alert=True)
            return

        task = (await session.execute(select(Task).where(Task.id == ut.task_id))).scalar_one_or_none()
        if not task or task.created_by != user_id:
            await query.answer("❌ أنت لست صاحب هذه المهمة!", show_alert=True)
            return

        worker = (await session.execute(select(User).where(User.telegram_id == ut.user_id))).scalar_one_or_none()

        if action == "approve":
            if ut.status == "approved":
                await query.answer("⚠️ تم قبول هذه المهمة مسبقاً!", show_alert=True)
                return

            ut.status = "approved"
            if worker:
                worker.balance += task.reward_grams
                tx = Transaction(
                    user_id=worker.telegram_id,
                    trans_type="earn_task",
                    amount=task.reward_grams,
                    description=f"كسب من مهمة: {task.title}"
                )
                session.add(tx)

            task.completed_qty += 1
            if task.completed_qty >= task.total_qty:
                task.status = "completed"

            await session.commit()
            await query.answer("✅ تم قبول المهمة وتحويل الرصيد للمنفذ بنجاح!", show_alert=True)
            await query.edit_message_caption("✅ **تم قبول هذه المهمة ودفع الرصيد للمنفذ.**", parse_mode="Markdown")

            try:
                await context.bot.send_message(
                    chat_id=ut.user_id,
                    text=f"🎉 **مبروك!** تم قبول إثبات المهمة ({task.title}) وإضافة **+{task.reward_grams:,} غرام** إلى رصيدك!",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        elif action == "reject":
            ut.status = "rejected"
            await session.commit()
            await query.answer("❌ تم رفض المهمة.", show_alert=True)
            await query.edit_message_caption("❌ **تم رفض الإثبات لهذه المهمة.**", parse_mode="Markdown")

            keyboard = [
                [InlineKeyboardButton("📤 إرسال إثبات جديد", callback_data=f"resubmit_proof_{ut.id}")],
                [InlineKeyboardButton("⚖️ فتح اعتراض (تذكرة أدمن)", callback_data=f"file_dispute_{ut.id}")]
            ]
            try:
                await context.bot.send_message(
                    chat_id=ut.user_id,
                    text=f"❌ **للأسف، قام صاحب المهمة ({task.title}) برفض إثباتك.**\n\n"
                         f"إذا كنت تعتقد أنك قمت بالتنفيذ بشكل صحيح، يمكنك إعادة إرسال إثبات جديد أو فتح اعتراض للأدمن.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception:
                pass

        elif action == "revision":
            ut.status = "revision_requested"
            await session.commit()
            await query.answer("🔄 تم طلب إعادة مراجعة جديدة من المنفذ.", show_alert=True)
            await query.edit_message_caption("🔄 **تم طلب إعادة مراجعة وإرسال إثبات جديد من المنفذ.**", parse_mode="Markdown")

            keyboard = [
                [InlineKeyboardButton("📤 إرسال إثبات جديد الآن", callback_data=f"resubmit_proof_{ut.id}")]
            ]
            try:
                await context.bot.send_message(
                    chat_id=ut.user_id,
                    text=f"🔄 **طلب صاحب المهمة ({task.title}) إعادة مراجعة جديدة.**\n\n"
                         f"يرجى التقاط صورة إثبات أوضح وإرسالها مجدداً.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception:
                pass

async def handle_worker_dispute_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("resubmit_proof_"):
        ut_id = int(data.replace("resubmit_proof_", ""))
        context.user_data["revision_ut_id"] = ut_id
        await query.answer()
        await query.edit_message_text(
            "📤 **إعادة إرسال إثبات الصورة:**\n\n"
            "يرجى قم بإرسال صورة الإثبات الجديدة الآن مباشرة في الشات.",
            parse_mode="Markdown"
        )

    elif data.startswith("file_dispute_"):
        ut_id = int(data.replace("file_dispute_", ""))

        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            if not ut or ut.user_id != user_id:
                await query.answer("❌ تعذر العثور على المعاملة.", show_alert=True)
                return

            task = (await session.execute(select(Task).where(Task.id == ut.task_id))).scalar_one_or_none()

            # Create DisputeTicket
            ticket = DisputeTicket(
                user_id=user_id,
                task_id=ut.task_id,
                user_task_id=ut.id,
                proof_file_id=ut.proof_file_id,
                status="open"
            )
            ut.status = "disputed"
            session.add(ticket)
            await session.commit()
            ticket_id = ticket.id

        await query.answer("⚖️ تم فتح تذكرة اعتراض وتصعيدها للأدمن بنجاح!", show_alert=True)
        await query.edit_message_text("⚖️ **تم رفع تذكرة اعتراض للأدمن.** سيتم مراجعة الإثبات وتصفية الحقوق فوراً.", parse_mode="Markdown")

        # Notify Admins
        keyboard = [
            [
                InlineKeyboardButton("💰 خصم من المنشئ ودفع للعامل", callback_data=f"admin_disp_pay_{ticket_id}"),
                InlineKeyboardButton("❌ تأكيد الرفض والإغلاق", callback_data=f"admin_disp_rej_{ticket_id}")
            ]
        ]
        caption = (
            f"⚖️ **تذكرة اعتراض جديدة (#Ticket-{ticket_id})**\n\n"
            f"👤 العامل: `{user_id}`\n"
            f"👤 صاحب المهمة: `{task.created_by}`\n"
            f"📌 المهمة: {task.title if task else ''}\n"
            f"💰 المستحق: {task.reward_grams if task else 0:,} غرام\n\n"
            f"اختر قرار الأدمن النهائي:"
        )
        for admin_id in ADMIN_IDS:
            try:
                if ut.proof_file_id:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=ut.proof_file_id,
                        caption=caption,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=caption,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            except Exception:
                pass

async def handle_admin_dispute_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    parts = data.split("_")
    action = parts[2] # pay or rej
    ticket_id = int(parts[3])

    async with AsyncSessionLocal() as session:
        ticket = (await session.execute(select(DisputeTicket).where(DisputeTicket.id == ticket_id))).scalar_one_or_none()
        if not ticket or ticket.status != "open":
            await query.answer("⚠️ هذه التذكرة مغلقة بالفعل أو غير موجودة.", show_alert=True)
            return

        ut = (await session.execute(select(UserTask).where(UserTask.id == ticket.user_task_id))).scalar_one_or_none()
        task = (await session.execute(select(Task).where(Task.id == ticket.task_id))).scalar_one_or_none()
        worker = (await session.execute(select(User).where(User.telegram_id == ticket.user_id))).scalar_one_or_none()
        creator = (await session.execute(select(User).where(User.telegram_id == task.created_by))).scalar_one_or_none() if task else None

        if action == "pay":
            ticket.status = "resolved_worker_paid"
            if ut:
                ut.status = "approved"

            # Pay worker & optionally deduct from creator if balance available
            if worker and task:
                worker.balance += task.reward_grams
                tx_w = Transaction(
                    user_id=worker.telegram_id,
                    trans_type="earn_task",
                    amount=task.reward_grams,
                    description=f"مكافأة قرار الأدمن في الاعتراض (#Ticket-{ticket_id})"
                )
                session.add(tx_w)

                if creator and creator.balance >= task.reward_grams:
                    creator.balance -= task.reward_grams
                    tx_c = Transaction(
                        user_id=creator.telegram_id,
                        trans_type="spend_promo",
                        amount=-task.reward_grams,
                        description=f"خصم قرار الأدمن لصالح العامل (#Ticket-{ticket_id})"
                    )
                    session.add(tx_c)

            await session.commit()
            await query.answer("✅ تم قبول الاعتراض ودفع مستحقات العامل بنجاح!", show_alert=True)
            if query.message.caption:
                await query.edit_message_caption(f"✅ **تم حسم الاعتراض لصالح العامل ورصد المستحقات.** (#Ticket-{ticket_id})")
            else:
                await query.edit_message_text(f"✅ **تم حسم الاعتراض لصالح العامل ورصد المستحقات.** (#Ticket-{ticket_id})")

            # Notify parties
            try:
                await context.bot.send_message(
                    chat_id=ticket.user_id,
                    text=f"⚖️ **قرار الأدمن:** تم قبول اعتراضك وإضافة **+{task.reward_grams:,} غرام** لرصيدك!",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        elif action == "rej":
            ticket.status = "resolved_rejected"
            if ut:
                ut.status = "rejected"

            await session.commit()
            await query.answer("❌ تم تأكيد رفض الاعتراض وإغلاق التذكرة.", show_alert=True)
            if query.message.caption:
                await query.edit_message_caption(f"❌ **تم تأكيد رفض الاعتراض وإغلاق التذكرة.** (#Ticket-{ticket_id})")
            else:
                await query.edit_message_text(f"❌ **تم تأكيد رفض الاعتراض وإغلاق التذكرة.** (#Ticket-{ticket_id})")

            try:
                await context.bot.send_message(
                    chat_id=ticket.user_id,
                    text=f"⚖️ **قرار الأدمن:** تم مراجعة الإثبات وتأكيد صحة موقف صاحب المهمة وإغلاق الاعتراض.",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
