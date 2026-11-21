from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, update as sa_update, and_

from config import ADMIN_IDS
from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask, Transaction, DisputeTicket
from utils.image_hash import compute_dhash, is_similar_hash
from utils.security import user_lock_manager, is_admin_user
from utils.gatekeeper import enforce_user_access
from utils.rewards import award_task_completion, dispatch_completion_notifications
from utils.html_utils import esc, utcnow

_QUICK_REASONS = {
    "unclear": "الصورة غير واضحة ولا تُظهر إتمام المطلوب",
    "notdone": "لم يتم تنفيذ شروط المهمة بالكامل",
    "rules": "مخالفة تعليمات المهمة أو لقطة شاشة غير مطابقة",
}


async def _download_and_hash_photo(context, file_id: str) -> str | None:
    try:
        tg_file = await context.bot.get_file(file_id)
        data = await tg_file.download_as_bytearray()
        return compute_dhash(bytes(data))
    except Exception:
        return None


async def _is_duplicate_proof(session, user_id: int, task_id: int, file_unique_id: str | None, phash: str | None, exclude_ut_id: int | None = None) -> bool:
    stmt = select(UserTask).where(
        (UserTask.task_id == task_id) | (UserTask.user_id == user_id)
    )
    rows = (await session.execute(stmt)).scalars().all()
    for r in rows:
        if exclude_ut_id and r.id == exclude_ut_id:
            continue
        if file_unique_id and r.proof_file_unique_id and r.proof_file_unique_id == file_unique_id:
            return True
        if phash and r.proof_phash and is_similar_hash(r.proof_phash, phash, max_distance=6):
            return True
    return False


async def process_proof_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when a user sends a photo for a proof-based task or revision.
    """
    task_id = context.user_data.get("pending_task_id")
    revision_ut_id = context.user_data.get("revision_ut_id")
    if not task_id and not revision_ut_id:
        return False

    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return True

    if not task_id and revision_ut_id:
        return await process_revision_photo(update, context, revision_ut_id)

    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file_unique_id = getattr(photo, "file_unique_id", None)
    phash = await _download_and_hash_photo(context, file_id)

    now = utcnow()
    async with user_lock_manager.get_lock(("user", user_id)):
        async with AsyncSessionLocal() as session:
            task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
            if not task or task.status != "active" or task.created_by == user_id:
                await update.message.reply_text("❌ المهمة غير متاحة حالياً.")
                context.user_data.pop("pending_task_id", None)
                return True

            if await _is_duplicate_proof(session, user_id, task_id, file_unique_id, phash):
                user = (
                    await session.execute(select(User).where(User.telegram_id == user_id))
                ).scalar_one_or_none()
                if user:
                    user.trust_score = max(0, (user.trust_score or 100) - 5)
                    await session.commit()
                await update.message.reply_text(
                    "🚫 <b>تم رفض الصورة تلقائياً!</b>\n"
                    "هذه الصورة مطابقة أو مكررة من إثبات سابق. يرجى إرسال لقطة شاشة جديدة أصلية.",
                    parse_mode="HTML",
                )
                return True

            ut = (
                await session.execute(
                    select(UserTask).where(
                        and_(UserTask.user_id == user_id, UserTask.task_id == task_id)
                    )
                )
            ).scalar_one_or_none()

            if ut:
                if ut.status in ("completed", "approved", "pending_approval"):
                    context.user_data.pop("pending_task_id", None)
                    await update.message.reply_text("⚠️ لديك إثبات معتمد أو قيد المراجعة لهذه المهمة بالفعل.")
                    return True
                ut.status = "pending_approval"
                ut.proof_file_id = file_id
                ut.proof_file_unique_id = file_unique_id
                ut.proof_phash = phash
                ut.submitted_at = now
            else:
                ut = UserTask(
                    user_id=user_id,
                    task_id=task_id,
                    status="pending_approval",
                    proof_file_id=file_id,
                    proof_file_unique_id=file_unique_id,
                    proof_phash=phash,
                    submitted_at=now,
                )
                session.add(ut)

            await session.commit()
            ut_id = ut.id
            creator_id = task.created_by
            task_title = task.title
            reward_grams = task.reward_grams

    context.user_data.pop("pending_task_id", None)
    await update.message.reply_text(
        "✅ <b>تم استلام صورة الإثبات بنجاح!</b>\n"
        "تم إرسال الإثبات لصاحب المهمة للمراجعة (وسيُعتمد تلقائياً بعد 24 ساعة في حال عدم الرد).",
        parse_mode="HTML",
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ قبول ودفع", callback_data=f"proof_approve_{ut_id}"),
            InlineKeyboardButton("❌ رفض مع سبب", callback_data=f"proof_reject_{ut_id}"),
        ],
        [InlineKeyboardButton("🔄 طلب إعادة مراجعة", callback_data=f"proof_revision_{ut_id}")],
    ]
    caption = (
        f"📩 <b>إثبات تنفيذ جديد لمهمتك!</b>\n\n"
        f"📌 المهمة: {esc(task_title)}\n"
        f"👤 المنفذ: <code>{user_id}</code>\n"
        f"💰 المكافأة: {reward_grams:,} غرام\n\n"
        f"يرجى المعاينة واختيار الإجراء المناسب:"
    )

    try:
        await context.bot.send_photo(
            chat_id=creator_id,
            photo=file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception:
        pass

    return True


async def process_revision_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE, ut_id: int
):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file_unique_id = getattr(photo, "file_unique_id", None)
    phash = await _download_and_hash_photo(context, file_id)
    now = utcnow()

    async with user_lock_manager.acquire_ordered_locks(("ut", ut_id), ("user", user_id)):
        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            if not ut or ut.user_id != user_id:
                context.user_data.pop("revision_ut_id", None)
                await update.message.reply_text("❌ غير مصرح أو لم يتم العثور على المعاملة.")
                return True
            if ut.status not in ("rejected", "revision_requested"):
                context.user_data.pop("revision_ut_id", None)
                await update.message.reply_text("⚠️ لا يمكن إعادة إرسال إثبات لهذه الحالة.")
                return True

            if await _is_duplicate_proof(session, user_id, ut.task_id, file_unique_id, phash, exclude_ut_id=ut_id):
                await update.message.reply_text(
                    "🚫 الصورة مكررة أو مطابقة لإثبات سابق، يرجى إرسال صورة جديدة واضحة."
                )
                return True

            task = (await session.execute(select(Task).where(Task.id == ut.task_id))).scalar_one_or_none()
            ut.status = "pending_approval"
            ut.proof_file_id = file_id
            ut.proof_file_unique_id = file_unique_id
            ut.proof_phash = phash
            ut.submitted_at = now
            await session.commit()
            creator_id = task.created_by if task else None
            task_title = task.title if task else ""

    context.user_data.pop("revision_ut_id", None)
    await update.message.reply_text("✅ <b>تم إعادة إرسال صورة الإثبات بنجاح!</b>", parse_mode="HTML")

    if creator_id:
        keyboard = [
            [
                InlineKeyboardButton("✅ قبول ودفع", callback_data=f"proof_approve_{ut_id}"),
                InlineKeyboardButton("❌ رفض مع سبب", callback_data=f"proof_reject_{ut_id}"),
            ],
            [InlineKeyboardButton("🔄 طلب إعادة مراجعة", callback_data=f"proof_revision_{ut_id}")],
        ]
        caption = (
            f"🔄 <b>تم إعادة تقديم إثبات جديد للمهمة!</b>\n\n"
            f"📌 المهمة: {esc(task_title)}\n"
            f"👤 المنفذ: <code>{user_id}</code>\n\n"
            f"يرجى المراجعة واتخاذ الإجراء:"
        )
        try:
            await context.bot.send_photo(
                chat_id=creator_id,
                photo=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception:
            pass

    return True


async def _apply_proof_rejection(context, ut_id: int, creator_id: int, reason: str, query=None):
    async with user_lock_manager.acquire_ordered_locks(("ut", ut_id)):
        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            if not ut:
                return False, "not_found", None, ""
            task = (await session.execute(select(Task).where(Task.id == ut.task_id))).scalar_one_or_none()
            if not task or task.created_by != creator_id:
                return False, "forbidden", None, ""
            if ut.status != "pending_approval":
                return False, "already_handled", None, ""

            ut.status = "rejected"
            ut.rejection_reason = reason
            worker_id = ut.user_id
            task_title = task.title
            await session.commit()

    keyboard = [
        [InlineKeyboardButton("📤 إرسال إثبات جديد", callback_data=f"resubmit_proof_{ut_id}")],
        [InlineKeyboardButton("⚖️ فتح اعتراض (تذكرة أدمن)", callback_data=f"file_dispute_{ut_id}")],
    ]
    try:
        await context.bot.send_message(
            chat_id=worker_id,
            text=(
                f"❌ <b>تم رفض إثباتك في المهمة ({esc(task_title)}).</b>\n\n"
                f"📝 <b>سبب الرفض:</b> {esc(reason)}\n\n"
                f"يمكنك إرسال إثبات جديد أو فتح اعتراض لمراجعة الإدارة."
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception:
        pass
    return True, "ok", worker_id, task_title


async def handle_creator_proof_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    # Quick reason buttons: proof_rej_r_<ut_id>_<code>
    if data.startswith("proof_rej_r_"):
        parts = data.split("_")
        ut_id = int(parts[3])
        reason_code = parts[4]
        reason = _QUICK_REASONS.get(reason_code, "رفض من المعلن")
        ok, err, _, _ = await _apply_proof_rejection(context, ut_id, user_id, reason, query)
        if not ok:
            await query.answer("⚠️ تعذر تنفيذ الرفض (ربما تم البت مسبقاً).", show_alert=True)
            return
        await query.answer("❌ تم رفض الإثبات وإرسال السبب للمنفذ.", show_alert=True)
        await query.edit_message_caption(
            f"❌ <b>تم رفض الإثبات.</b>\n📝 السبب: {esc(reason)}", parse_mode="HTML"
        )
        return

    if data.startswith("proof_rej_custom_"):
        ut_id = int(data.replace("proof_rej_custom_", ""))
        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            task = (await session.execute(select(Task).where(Task.id == ut.task_id))).scalar_one_or_none() if ut else None
            if not task or task.created_by != user_id:
                await query.answer("❌ غير مصرح.", show_alert=True)
                return
        context.user_data["awaiting_reject_reason_ut_id"] = ut_id
        await query.answer()
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✍️ اكتب سبب رفض الإثبات للمعاملة <code>#{ut_id}</code> الآن:",
            parse_mode="HTML",
        )
        return

    parts = data.split("_")
    action = parts[1]
    ut_id = int(parts[2])

    async with AsyncSessionLocal() as session:
        ut_probe = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
        if not ut_probe:
            await query.answer("❌ لم يتم العثور على سجل هذه المهمة.", show_alert=True)
            return
        worker_id = ut_probe.user_id
        task_id = ut_probe.task_id

    if action == "reject":
        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
            if not task or task.created_by != user_id:
                await query.answer("❌ أنت لست صاحب هذه المهمة!", show_alert=True)
                return
            if not ut or ut.status != "pending_approval":
                await query.answer("⚠️ تم التعامل مع هذا الإثبات مسبقاً!", show_alert=True)
                return

        await query.answer()
        reason_kb = [
            [InlineKeyboardButton("📷 الصورة غير واضحة", callback_data=f"proof_rej_r_{ut_id}_unclear")],
            [InlineKeyboardButton("❌ لم ينفذ المطلوب", callback_data=f"proof_rej_r_{ut_id}_notdone")],
            [InlineKeyboardButton("🚫 مخالفة الشروط", callback_data=f"proof_rej_r_{ut_id}_rules")],
            [InlineKeyboardButton("✍️ كتابة سبب مخصص", callback_data=f"proof_rej_custom_{ut_id}")],
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(reason_kb))
        return

    reward_info = None
    task_title = ""
    async with user_lock_manager.acquire_ordered_locks(("ut", ut_id), ("user", worker_id), ("task", task_id)):
        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
            if not ut or not task or task.created_by != user_id:
                await query.answer("❌ أنت لست صاحب هذه المهمة!", show_alert=True)
                return

            if action == "approve":
                if ut.status != "pending_approval":
                    await query.answer("⚠️ تم التعامل مع هذا الإثبات مسبقاً!", show_alert=True)
                    return

                worker = (
                    await session.execute(select(User).where(User.telegram_id == worker_id))
                ).scalar_one_or_none()
                if not worker:
                    await query.answer("❌ لم يتم العثور على المنفذ.", show_alert=True)
                    return

                await session.execute(
                    sa_update(Task)
                    .where(and_(Task.id == task_id, Task.completed_qty < Task.total_qty))
                    .values(completed_qty=Task.completed_qty + 1)
                )
                await session.refresh(task)

                reward_info = await award_task_completion(
                    session, context.bot, worker, task, ut, target_status="approved"
                )
                task_title = task.title
                await session.commit()

            elif action == "revision":
                if ut.status != "pending_approval":
                    await query.answer("⚠️ تم التعامل مع هذا الإثبات مسبقاً!", show_alert=True)
                    return
                ut.status = "revision_requested"
                task_title = task.title
                await session.commit()

    if action == "approve" and reward_info:
        await dispatch_completion_notifications(context.bot, worker_id, reward_info)
        await query.answer("✅ تم قبول المهمة وتحويل الرصيد للمنفذ بنجاح!", show_alert=True)
        await query.edit_message_caption(
            f"✅ <b>تم قبول هذه المهمة ودفع +{reward_info['total_reward']:,} غرام للمنفذ.</b>",
            parse_mode="HTML",
        )
        try:
            await context.bot.send_message(
                chat_id=worker_id,
                text=(
                    f"🎉 <b>مبروك!</b> تم قبول إثبات المهمة (<b>{esc(task_title)}</b>) "
                    f"وإضافة <b>+{reward_info['total_reward']:,} غرام</b> إلى رصيدك!"
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass
    elif action == "revision":
        await query.answer("🔄 تم طلب إعادة مراجعة جديدة من المنفذ.", show_alert=True)
        await query.edit_message_caption(
            "🔄 <b>تم طلب إعادة مراجعة وإرسال إثبات جديد من المنفذ.</b>", parse_mode="HTML"
        )
        keyboard = [
            [InlineKeyboardButton("📤 إرسال إثبات جديد الآن", callback_data=f"resubmit_proof_{ut_id}")]
        ]
        try:
            await context.bot.send_message(
                chat_id=worker_id,
                text=(
                    f"🔄 <b>طلب صاحب المهمة ({esc(task_title)}) إعادة مراجعة جديدة.</b>\n\n"
                    f"يرجى التقاط صورة إثبات أوضح وإرسالها مجدداً."
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception:
            pass


async def process_custom_reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    ut_id = context.user_data.get("awaiting_reject_reason_ut_id")
    if not ut_id:
        return False

    user_id = update.effective_user.id
    reason = update.message.text.strip()[:300]
    context.user_data.pop("awaiting_reject_reason_ut_id", None)

    ok, err, _, task_title = await _apply_proof_rejection(context, ut_id, user_id, reason)
    if not ok:
        await update.message.reply_text("⚠️ تعذر تطبيق الرفض (ربما تم التعامل مع الإثبات مسبقاً).")
        return True

    await update.message.reply_text(
        f"❌ <b>تم رفض الإثبات في مهمة {esc(task_title)} وإرسال السبب للمنفذ.</b>",
        parse_mode="HTML",
    )
    return True


async def handle_worker_dispute_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("resubmit_proof_"):
        ut_id = int(data.replace("resubmit_proof_", ""))
        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            if not ut or ut.user_id != user_id:
                await query.answer("❌ غير مصرح لك بالوصول لهذا السجل.", show_alert=True)
                return
            if ut.status not in ("rejected", "revision_requested"):
                await query.answer("⚠️ لا يمكن إعادة الإرسال في الحالة الحالية.", show_alert=True)
                return

        context.user_data["revision_ut_id"] = ut_id
        await query.answer()
        await query.edit_message_text(
            "📤 <b>إعادة إرسال إثبات الصورة:</b>\n\n"
            "يرجى إرسال صورة الإثبات الجديدة الآن مباشرة في الشات.",
            parse_mode="HTML",
        )

    elif data.startswith("file_dispute_"):
        ut_id = int(data.replace("file_dispute_", ""))

        async with user_lock_manager.acquire_ordered_locks(("ut", ut_id), ("user", user_id)):
            async with AsyncSessionLocal() as session:
                ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
                if not ut or ut.user_id != user_id:
                    await query.answer("❌ تعذر العثور على المعاملة.", show_alert=True)
                    return
                if ut.status != "rejected":
                    await query.answer("⚠️ يمكن الاعتراض فقط على الإثباتات المرفوضة.", show_alert=True)
                    return

                existing_ticket = (
                    await session.execute(
                        select(DisputeTicket).where(DisputeTicket.user_task_id == ut_id)
                    )
                ).scalar_one_or_none()
                if existing_ticket:
                    await query.answer("⚠️ تم فتح تذكرة اعتراض لهذا الإثبات مسبقاً!", show_alert=True)
                    return

                task = (
                    await session.execute(select(Task).where(Task.id == ut.task_id))
                ).scalar_one_or_none()

                ticket = DisputeTicket(
                    user_id=user_id,
                    task_id=ut.task_id,
                    user_task_id=ut.id,
                    reason=ut.rejection_reason,
                    proof_file_id=ut.proof_file_id,
                    status="open",
                )
                ut.status = "disputed"
                session.add(ticket)
                await session.commit()
                ticket_id = ticket.id
                proof_file_id = ut.proof_file_id
                creator_id = task.created_by if task else 0
                task_title = task.title if task else ""
                reward_grams = task.reward_grams if task else 0

        await query.answer("⚖️ تم فتح تذكرة اعتراض وتصعيدها للأدمن بنجاح!", show_alert=True)
        await query.edit_message_text(
            "⚖️ <b>تم رفع تذكرة اعتراض للأدمن.</b> سيتم مراجعة الإثبات وتصفية الحقوق فوراً.",
            parse_mode="HTML",
        )

        keyboard = [
            [
                InlineKeyboardButton("💰 اعتماد ودفع للعامل", callback_data=f"admin_disp_pay_{ticket_id}"),
                InlineKeyboardButton("❌ تأكيد الرفض والإغلاق", callback_data=f"admin_disp_rej_{ticket_id}"),
            ]
        ]
        caption = (
            f"⚖️ <b>تذكرة اعتراض جديدة (#Ticket-{ticket_id})</b>\n\n"
            f"👤 العامل: <code>{user_id}</code>\n"
            f"👤 صاحب المهمة: <code>{creator_id}</code>\n"
            f"📌 المهمة: {esc(task_title)}\n"
            f"💰 المستحق: {reward_grams:,} غرام\n\n"
            f"اختر قرار الأدمن النهائي:"
        )
        for admin_id in ADMIN_IDS:
            try:
                if proof_file_id:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=proof_file_id,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                else:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=caption,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
            except Exception:
                pass


async def handle_admin_dispute_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_disp"):
        return

    parts = data.split("_")
    action = parts[2]
    ticket_id = int(parts[3])

    async with AsyncSessionLocal() as session:
        t_probe = (
            await session.execute(select(DisputeTicket).where(DisputeTicket.id == ticket_id))
        ).scalar_one_or_none()
        if not t_probe:
            await query.answer("⚠️ هذه التذكرة غير موجودة.", show_alert=True)
            return
        ut_id = t_probe.user_task_id
        worker_id = t_probe.user_id
        task_id = t_probe.task_id

    reward_info = None
    reward_grams = 0
    async with user_lock_manager.acquire_ordered_locks(
        ("ticket", ticket_id), ("ut", ut_id), ("user", worker_id), ("task", task_id)
    ):
        async with AsyncSessionLocal() as session:
            ticket = (
                await session.execute(select(DisputeTicket).where(DisputeTicket.id == ticket_id))
            ).scalar_one_or_none()
            if not ticket or ticket.status != "open":
                await query.answer("⚠️ هذه التذكرة مغلقة بالفعل أو غير موجودة.", show_alert=True)
                return

            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
            worker = (
                await session.execute(select(User).where(User.telegram_id == worker_id))
            ).scalar_one_or_none()
            creator = (
                await session.execute(select(User).where(User.telegram_id == task.created_by))
            ).scalar_one_or_none() if task else None

            if action == "pay":
                ticket.status = "resolved_worker_paid"
                if creator:
                    creator.trust_score = max(0, (creator.trust_score or 100) - 15)

                if worker and task and ut:
                    reward_grams = task.reward_grams
                    # If task escrow does not cover reward, deduct from creator if available
                    if (task.escrow_balance or 0) < task.reward_grams and creator and creator.balance >= task.reward_grams:
                        creator.balance -= task.reward_grams
                        session.add(
                            Transaction(
                                user_id=creator.telegram_id,
                                trans_type="spend_promo",
                                amount=-task.reward_grams,
                                description=f"خصم قرار الأدمن لصالح العامل (#Ticket-{ticket_id})",
                            )
                        )
                        task.escrow_balance = (task.escrow_balance or 0) + task.reward_grams

                    await session.execute(
                        sa_update(Task)
                        .where(and_(Task.id == task_id, Task.completed_qty < Task.total_qty))
                        .values(completed_qty=Task.completed_qty + 1)
                    )
                    await session.refresh(task)
                    reward_info = await award_task_completion(
                        session, context.bot, worker, task, ut, target_status="approved"
                    )

                await session.commit()

            elif action == "rej":
                ticket.status = "resolved_rejected"
                if ut:
                    ut.status = "rejected"
                if worker:
                    worker.trust_score = max(0, (worker.trust_score or 100) - 10)
                await session.commit()

    if action == "pay":
        if reward_info:
            await dispatch_completion_notifications(context.bot, worker_id, reward_info)
            paid_amt = reward_info["total_reward"]
        else:
            paid_amt = reward_grams
        await query.answer("✅ تم قبول الاعتراض ودفع مستحقات العامل بنجاح!", show_alert=True)
        done_msg = f"✅ <b>تم حسم الاعتراض لصالح العامل ورصد المستحقات.</b> (#Ticket-{ticket_id})"
        if query.message.caption:
            await query.edit_message_caption(done_msg, parse_mode="HTML")
        else:
            await query.edit_message_text(done_msg, parse_mode="HTML")
        try:
            await context.bot.send_message(
                chat_id=worker_id,
                text=f"⚖️ <b>قرار الأدمن:</b> تم قبول اعتراضك وإضافة <b>+{paid_amt:,} غرام</b> لرصيدك!",
                parse_mode="HTML",
            )
        except Exception:
            pass
    elif action == "rej":
        await query.answer("❌ تم تأكيد رفض الاعتراض وإغلاق التذكرة.", show_alert=True)
        done_msg = f"❌ <b>تم تأكيد رفض الاعتراض وإغلاق التذكرة.</b> (#Ticket-{ticket_id})"
        if query.message.caption:
            await query.edit_message_caption(done_msg, parse_mode="HTML")
        else:
            await query.edit_message_text(done_msg, parse_mode="HTML")
        try:
            await context.bot.send_message(
                chat_id=worker_id,
                text="⚖️ <b>قرار الأدمن:</b> تم مراجعة الإثبات وتأكيد صحة موقف صاحب المهمة وإغلاق الاعتراض.",
                parse_mode="HTML",
            )
        except Exception:
            pass
