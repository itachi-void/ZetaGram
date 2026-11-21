from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, update as sa_update, and_

from config import ADMIN_IDS
from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask, Transaction, DisputeTicket
from utils.image_hash import compute_dhash, is_similar_hash
from utils.security import user_lock_manager, is_admin_user
from utils.gatekeeper import enforce_user_access
from utils.rewards import award_task_completion, dispatch_completion_notifications, format_flash_note
from utils.i18n import get_text, get_user_lang
from utils.html_utils import esc, utcnow


async def _download_and_hash_photo(context, file_id: str) -> str | None:
    try:
        tg_file = await context.bot.get_file(file_id)
        data = await tg_file.download_as_bytearray()
        return compute_dhash(bytes(data))
    except Exception:
        return None


async def _is_duplicate_proof(
    session,
    user_id: int,
    task_id: int,
    file_unique_id: str | None,
    phash: str | None,
    exclude_ut_id: int | None = None,
) -> bool:
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
    """Called when a user sends a photo for a proof-based task or revision."""
    task_id = context.user_data.get("pending_task_id")
    revision_ut_id = context.user_data.get("revision_ut_id")
    if not task_id and not revision_ut_id:
        return False

    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return True

    if not task_id and revision_ut_id:
        return await process_revision_photo(update, context, revision_ut_id)

    user_id = update.effective_user.id
    worker_lang = get_user_lang(db_user)
    creator_lang = "ar"
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file_unique_id = getattr(photo, "file_unique_id", None)
    phash = await _download_and_hash_photo(context, file_id)

    now = utcnow()
    async with user_lock_manager.get_lock(("user", user_id)):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if user:
                worker_lang = get_user_lang(user)

            task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
            if not task or task.status != "active" or task.created_by == user_id:
                await update.message.reply_text(get_text(worker_lang, "task_err_unavailable"))
                context.user_data.pop("pending_task_id", None)
                return True

            if await _is_duplicate_proof(session, user_id, task_id, file_unique_id, phash):
                if user:
                    user.trust_score = max(0, (user.trust_score or 100) - 5)
                    await session.commit()
                await update.message.reply_text(
                    get_text(worker_lang, "proof_err_duplicate"),
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
                    await update.message.reply_text(get_text(worker_lang, "proof_err_already_pending"))
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

            creator = (
                await session.execute(select(User).where(User.telegram_id == task.created_by))
            ).scalar_one_or_none()
            creator_lang = get_user_lang(creator)

            await session.commit()
            ut_id = ut.id
            creator_id = task.created_by
            task_title = task.title
            reward_grams = task.reward_grams

    context.user_data.pop("pending_task_id", None)
    await update.message.reply_text(
        get_text(worker_lang, "proof_submitted"),
        parse_mode="HTML",
    )

    keyboard = [
        [
            InlineKeyboardButton(get_text(creator_lang, "proof_btn_approve"), callback_data=f"proof_approve_{ut_id}"),
            InlineKeyboardButton(get_text(creator_lang, "proof_btn_reject"), callback_data=f"proof_reject_{ut_id}"),
        ],
        [InlineKeyboardButton(get_text(creator_lang, "proof_btn_revision"), callback_data=f"proof_revision_{ut_id}")],
    ]
    caption = get_text(
        creator_lang,
        "proof_creator_caption",
        title=esc(task_title),
        worker_id=user_id,
        reward=reward_grams,
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
    worker_lang = "ar"
    creator_lang = "ar"
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file_unique_id = getattr(photo, "file_unique_id", None)
    phash = await _download_and_hash_photo(context, file_id)
    now = utcnow()

    async with user_lock_manager.acquire_ordered_locks(("ut", ut_id), ("user", user_id)):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            worker_lang = get_user_lang(user)

            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            if not ut or ut.user_id != user_id:
                context.user_data.pop("revision_ut_id", None)
                await update.message.reply_text(get_text(worker_lang, "proof_err_not_found"))
                return True
            if ut.status not in ("rejected", "revision_requested"):
                context.user_data.pop("revision_ut_id", None)
                await update.message.reply_text(get_text(worker_lang, "proof_err_cannot_resubmit"))
                return True

            if await _is_duplicate_proof(session, user_id, ut.task_id, file_unique_id, phash, exclude_ut_id=ut_id):
                await update.message.reply_text(get_text(worker_lang, "proof_err_duplicate"), parse_mode="HTML")
                return True

            task = (await session.execute(select(Task).where(Task.id == ut.task_id))).scalar_one_or_none()
            if task:
                creator = (
                    await session.execute(select(User).where(User.telegram_id == task.created_by))
                ).scalar_one_or_none()
                creator_lang = get_user_lang(creator)
            ut.status = "pending_approval"
            ut.proof_file_id = file_id
            ut.proof_file_unique_id = file_unique_id
            ut.proof_phash = phash
            ut.submitted_at = now
            await session.commit()
            creator_id = task.created_by if task else None
            task_title = task.title if task else ""

    context.user_data.pop("revision_ut_id", None)
    await update.message.reply_text(get_text(worker_lang, "proof_rev_submitted"), parse_mode="HTML")

    if creator_id:
        keyboard = [
            [
                InlineKeyboardButton(get_text(creator_lang, "proof_btn_approve"), callback_data=f"proof_approve_{ut_id}"),
                InlineKeyboardButton(get_text(creator_lang, "proof_btn_reject"), callback_data=f"proof_reject_{ut_id}"),
            ],
            [InlineKeyboardButton(get_text(creator_lang, "proof_btn_revision"), callback_data=f"proof_revision_{ut_id}")],
        ]
        caption = get_text(
            creator_lang,
            "proof_creator_revision_caption",
            title=esc(task_title),
            worker_id=user_id,
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
    worker_lang = "ar"
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

            worker = (
                await session.execute(select(User).where(User.telegram_id == ut.user_id))
            ).scalar_one_or_none()
            worker_lang = get_user_lang(worker)

            ut.status = "rejected"
            ut.rejection_reason = reason
            worker_id = ut.user_id
            task_title = task.title
            await session.commit()

    keyboard = [
        [InlineKeyboardButton(get_text(worker_lang, "proof_btn_resubmit"), callback_data=f"resubmit_proof_{ut_id}")],
        [InlineKeyboardButton(get_text(worker_lang, "proof_btn_dispute"), callback_data=f"file_dispute_{ut_id}")],
    ]
    try:
        await context.bot.send_message(
            chat_id=worker_id,
            text=get_text(
                worker_lang,
                "proof_worker_rejected",
                title=esc(task_title),
                reason=esc(reason),
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

    async with AsyncSessionLocal() as pre_s:
        cr_user = (
            await pre_s.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        creator_lang = get_user_lang(cr_user)

    if data.startswith("proof_rej_r_"):
        parts = data.split("_")
        ut_id = int(parts[3])
        reason_code = parts[4]
        reason_key = {
            "unclear": "proof_rej_reason_unclear",
            "notdone": "proof_rej_reason_notdone",
            "rules": "proof_rej_reason_rules",
        }.get(reason_code)

        # Look up worker's language for the quick rejection reason
        worker_lang = creator_lang
        async with AsyncSessionLocal() as ws:
            ut_tmp = (await ws.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            if ut_tmp:
                wu = (
                    await ws.execute(select(User).where(User.telegram_id == ut_tmp.user_id))
                ).scalar_one_or_none()
                if wu:
                    worker_lang = get_user_lang(wu)

        reason = (
            get_text(worker_lang, reason_key)
            if reason_key
            else get_text(creator_lang, "proof_rej_caption", reason="").replace("❌ ", "")
        )
        ok, err, _, _ = await _apply_proof_rejection(context, ut_id, user_id, reason, query)
        if not ok:
            await query.answer(get_text(creator_lang, "proof_err_already_handled"), show_alert=True)
            return
        creator_reason_display = get_text(creator_lang, reason_key) if reason_key else reason
        await query.answer(get_text(creator_lang, "proof_rej_done_alert"), show_alert=True)
        await query.edit_message_caption(
            get_text(creator_lang, "proof_rej_caption", reason=esc(creator_reason_display)),
            parse_mode="HTML",
        )
        return

    if data.startswith("proof_rej_custom_"):
        ut_id = int(data.replace("proof_rej_custom_", ""))
        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            task = (
                await session.execute(select(Task).where(Task.id == ut.task_id))
            ).scalar_one_or_none() if ut else None
            if not task or task.created_by != user_id:
                await query.answer(get_text(creator_lang, "proof_err_forbidden"), show_alert=True)
                return
        context.user_data["awaiting_reject_reason_ut_id"] = ut_id
        await query.answer()
        await context.bot.send_message(
            chat_id=user_id,
            text=get_text(creator_lang, "proof_rej_custom_prompt", ut_id=ut_id),
            parse_mode="HTML",
        )
        return

    parts = data.split("_")
    action = parts[1]
    ut_id = int(parts[2])

    async with AsyncSessionLocal() as session:
        ut_probe = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
        if not ut_probe:
            await query.answer(get_text(creator_lang, "proof_err_not_found"), show_alert=True)
            return
        worker_id = ut_probe.user_id
        task_id = ut_probe.task_id

    if action == "reject":
        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
            if not task or task.created_by != user_id:
                await query.answer(get_text(creator_lang, "proof_err_forbidden"), show_alert=True)
                return
            if not ut or ut.status != "pending_approval":
                await query.answer(get_text(creator_lang, "proof_err_already_handled"), show_alert=True)
                return

        await query.answer()
        reason_kb = [
            [InlineKeyboardButton(get_text(creator_lang, "proof_rej_quick_unclear"), callback_data=f"proof_rej_r_{ut_id}_unclear")],
            [InlineKeyboardButton(get_text(creator_lang, "proof_rej_quick_notdone"), callback_data=f"proof_rej_r_{ut_id}_notdone")],
            [InlineKeyboardButton(get_text(creator_lang, "proof_rej_quick_rules"), callback_data=f"proof_rej_r_{ut_id}_rules")],
            [InlineKeyboardButton(get_text(creator_lang, "proof_rej_custom_btn"), callback_data=f"proof_rej_custom_{ut_id}")],
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(reason_kb))
        return

    reward_info = None
    task_title = ""
    worker_lang = "ar"
    async with user_lock_manager.acquire_ordered_locks(("ut", ut_id), ("user", worker_id), ("task", task_id)):
        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
            if not ut or not task or task.created_by != user_id:
                await query.answer(get_text(creator_lang, "proof_err_forbidden"), show_alert=True)
                return

            if action == "approve":
                if ut.status != "pending_approval":
                    await query.answer(get_text(creator_lang, "proof_err_already_handled"), show_alert=True)
                    return

                worker = (
                    await session.execute(select(User).where(User.telegram_id == worker_id))
                ).scalar_one_or_none()
                if not worker:
                    await query.answer(get_text(creator_lang, "not_registered"), show_alert=True)
                    return
                worker_lang = get_user_lang(worker)

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
                    await query.answer(get_text(creator_lang, "proof_err_already_handled"), show_alert=True)
                    return
                worker = (
                    await session.execute(select(User).where(User.telegram_id == worker_id))
                ).scalar_one_or_none()
                worker_lang = get_user_lang(worker)
                ut.status = "revision_requested"
                task_title = task.title
                await session.commit()

    if action == "approve" and reward_info:
        await dispatch_completion_notifications(context.bot, worker_id, reward_info)
        await query.answer(get_text(creator_lang, "proof_approve_done_alert"), show_alert=True)
        await query.edit_message_caption(
            get_text(creator_lang, "proof_approve_caption", reward=reward_info["total_reward"]),
            parse_mode="HTML",
        )
        flash_note = format_flash_note(worker_lang, reward_info)
        try:
            await context.bot.send_message(
                chat_id=worker_id,
                text=get_text(
                    worker_lang,
                    "proof_worker_approved",
                    title=esc(task_title),
                    reward=reward_info["total_reward"],
                    flash_note=flash_note,
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass
    elif action == "revision":
        await query.answer(get_text(creator_lang, "proof_rev_done_alert"), show_alert=True)
        await query.edit_message_caption(
            get_text(creator_lang, "proof_rev_caption"), parse_mode="HTML"
        )
        keyboard = [
            [InlineKeyboardButton(get_text(worker_lang, "proof_btn_resubmit"), callback_data=f"resubmit_proof_{ut_id}")]
        ]
        try:
            await context.bot.send_message(
                chat_id=worker_id,
                text=get_text(worker_lang, "proof_worker_rev_req", title=esc(task_title)),
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
    creator_lang = "ar"
    async with AsyncSessionLocal() as s:
        u = (await s.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        creator_lang = get_user_lang(u)

    reason = update.message.text.strip()[:300]
    context.user_data.pop("awaiting_reject_reason_ut_id", None)

    ok, err, _, task_title = await _apply_proof_rejection(context, ut_id, user_id, reason)
    if not ok:
        await update.message.reply_text(get_text(creator_lang, "proof_err_already_handled"))
        return True

    await update.message.reply_text(
        get_text(creator_lang, "proof_rej_custom_done", title=esc(task_title)),
        parse_mode="HTML",
    )
    return True


async def handle_worker_dispute_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    worker_lang = get_user_lang(db_user)

    if data.startswith("resubmit_proof_"):
        ut_id = int(data.replace("resubmit_proof_", ""))
        async with AsyncSessionLocal() as session:
            ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
            if not ut or ut.user_id != user_id:
                await query.answer(get_text(worker_lang, "proof_err_forbidden"), show_alert=True)
                return
            if ut.status not in ("rejected", "revision_requested"):
                await query.answer(get_text(worker_lang, "proof_err_cannot_resubmit"), show_alert=True)
                return

        context.user_data["revision_ut_id"] = ut_id
        await query.answer()
        await query.edit_message_text(get_text(worker_lang, "proof_rev_prompt"), parse_mode="HTML")

    elif data.startswith("file_dispute_"):
        ut_id = int(data.replace("file_dispute_", ""))

        async with user_lock_manager.acquire_ordered_locks(("ut", ut_id), ("user", user_id)):
            async with AsyncSessionLocal() as session:
                ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
                if not ut or ut.user_id != user_id:
                    await query.answer(get_text(worker_lang, "proof_err_not_found"), show_alert=True)
                    return
                if ut.status != "rejected":
                    await query.answer(get_text(worker_lang, "dispute_err_not_rejected"), show_alert=True)
                    return

                existing_ticket = (
                    await session.execute(
                        select(DisputeTicket).where(DisputeTicket.user_task_id == ut_id)
                    )
                ).scalar_one_or_none()
                if existing_ticket:
                    await query.answer(get_text(worker_lang, "dispute_err_exists"), show_alert=True)
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

        await query.answer(get_text(worker_lang, "dispute_filed_alert"), show_alert=True)
        await query.edit_message_text(get_text(worker_lang, "dispute_filed_msg"), parse_mode="HTML")

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
    worker_lang = "ar"
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
            worker_lang = get_user_lang(worker)
            creator = (
                await session.execute(select(User).where(User.telegram_id == task.created_by))
            ).scalar_one_or_none() if task else None

            if action == "pay":
                ticket.status = "resolved_worker_paid"
                if creator:
                    creator.trust_score = max(0, (creator.trust_score or 100) - 15)

                if worker and task and ut:
                    reward_grams = task.reward_grams
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
                text=get_text(worker_lang, "dispute_worker_won_dm", paid=paid_amt),
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
                text=get_text(worker_lang, "dispute_worker_lost_dm"),
                parse_mode="HTML",
            )
        except Exception:
            pass
