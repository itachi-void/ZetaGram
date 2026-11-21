import math
import time
from datetime import timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageOriginUser
from telegram.ext import ContextTypes
from sqlalchemy import select, update as sa_update, and_
from sqlalchemy.exc import IntegrityError

from config import ADMIN_IDS, MIN_POST_VIEW_SECONDS
from database.db import AsyncSessionLocal
from database.models import Task, User, UserTask, SkippedTask, TaskReport
from utils.telegram_api import check_user_subscription_status
from utils.pagination import build_pagination_keyboard
from utils.security import user_lock_manager
from utils.gatekeeper import enforce_user_access
from utils.rewards import award_task_completion, dispatch_completion_notifications, format_flash_note
from utils.i18n import get_text, get_user_lang
from utils.html_utils import esc, utcnow

PAGE_SIZE = 10


async def handle_task_list(
    update: Update, context: ContextTypes.DEFAULT_TYPE, task_type: str, page: int = 1
):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    is_premium = bool(getattr(update.effective_user, "is_premium", False))
    user_lang = get_user_lang(db_user)

    async with AsyncSessionLocal() as session:
        completed_ids = [
            r[0]
            for r in (
                await session.execute(
                    select(UserTask.task_id).where(UserTask.user_id == user_id)
                )
            ).all()
        ]
        skipped_ids = [
            r[0]
            for r in (
                await session.execute(
                    select(SkippedTask.task_id).where(SkippedTask.user_id == user_id)
                )
            ).all()
        ]
        excluded_ids = list(set(completed_ids + skipped_ids))

        stmt = (
            select(Task)
            .where(
                and_(
                    Task.task_type == task_type,
                    Task.status == "active",
                    Task.created_by != user_id,
                    Task.completed_qty < Task.total_qty,
                    Task.id.not_in(excluded_ids) if excluded_ids else True,
                )
            )
            .order_by(Task.reward_grams.desc())
        )
        raw_tasks = (await session.execute(stmt)).scalars().all()

    all_tasks = []
    for t in raw_tasks:
        if t.requires_premium and not is_premium:
            continue
        if t.target_languages:
            allowed_langs = {
                x.strip().lower() for x in t.target_languages.split(",") if x.strip()
            }
            if allowed_langs and user_lang not in allowed_langs:
                continue
        all_tasks.append(t)

    total_items = len(all_tasks)
    total_pages = max(1, math.ceil(total_items / PAGE_SIZE))
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * PAGE_SIZE
    page_tasks = all_tasks[start_idx : start_idx + PAGE_SIZE]

    if task_type in ["channel", "group"]:
        header = get_text(user_lang, "task_list_channel_header")
    elif task_type == "post":
        header = get_text(user_lang, "task_list_post_header", seconds=MIN_POST_VIEW_SECONDS)
    elif task_type in ["reaction_random", "reaction_fixed"]:
        header = get_text(user_lang, "task_list_reactions_header")
    elif task_type == "premium":
        header = get_text(user_lang, "task_list_premium_header")
    else:
        header = get_text(user_lang, "task_list_bot_header")

    items_buttons = []
    if not page_tasks:
        items_buttons.append(
            [InlineKeyboardButton(get_text(user_lang, "task_list_empty"), callback_data="ignore")]
        )
    else:
        for t in page_tasks:
            skip_cb = f"skip_task_{t.id}_{task_type}_{page}"
            report_cb = f"report_task_{t.id}"
            if task_type in ["channel", "group"] or (task_type == "premium" and t.chat_id):
                row = [
                    InlineKeyboardButton("🚨", callback_data=report_cb),
                    InlineKeyboardButton("⏭️", callback_data=skip_cb),
                    InlineKeyboardButton(get_text(user_lang, "task_btn_check"), callback_data=f"check_task_{t.id}"),
                    InlineKeyboardButton(
                        get_text(user_lang, "task_btn_subscribe_item", reward=t.reward_grams), url=t.target_url
                    ),
                ]
            elif task_type == "post":
                row = [
                    InlineKeyboardButton("🚨", callback_data=report_cb),
                    InlineKeyboardButton("⏭️", callback_data=skip_cb),
                    InlineKeyboardButton(
                        get_text(user_lang, "task_btn_post_item", reward=t.reward_grams),
                        callback_data=f"start_post_{t.id}",
                    ),
                ]
            elif task_type.startswith("bot_"):
                row = [
                    InlineKeyboardButton("🚨", callback_data=report_cb),
                    InlineKeyboardButton("⏭️", callback_data=skip_cb),
                    InlineKeyboardButton(
                        get_text(user_lang, "task_btn_bot_item", reward=t.reward_grams),
                        callback_data=f"open_bot_task_{t.id}",
                    ),
                ]
            else:
                prefix = "⚡ " if getattr(t, "auto_verify_reactions", False) else "🔥 "
                row = [
                    InlineKeyboardButton("🚨", callback_data=report_cb),
                    InlineKeyboardButton("⏭️", callback_data=skip_cb),
                    InlineKeyboardButton(
                        get_text(
                            user_lang,
                            "task_btn_reaction_item",
                            prefix=prefix,
                            reward=t.reward_grams,
                        ),
                        callback_data=f"open_proof_task_{t.id}",
                    ),
                ]
            items_buttons.append(row)

    reply_markup = build_pagination_keyboard(
        items_buttons=items_buttons,
        current_page=page,
        total_pages=total_pages,
        category_code=task_type,
        back_callback="earnings_menu",
        lang=user_lang,
    )

    if query:
        await query.edit_message_text(header, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.message.reply_text(header, parse_mode="HTML", reply_markup=reply_markup)


async def check_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    user_lang = get_user_lang(db_user)
    task_id = int(query.data.split("_")[-1])

    async with user_lock_manager.acquire_ordered_locks(("user", user_id), ("task", task_id)):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            task = (
                await session.execute(select(Task).where(Task.id == task_id))
            ).scalar_one_or_none()
            if user:
                user_lang = get_user_lang(user)
            if not task or task.status != "active" or task.completed_qty >= task.total_qty:
                await query.answer(get_text(user_lang, "task_err_unavailable"), show_alert=True)
                return
            if task.created_by == user_id:
                await query.answer(get_text(user_lang, "task_err_own"), show_alert=True)
                return

            already_done = (
                await session.execute(
                    select(UserTask).where(
                        and_(UserTask.user_id == user_id, UserTask.task_id == task_id)
                    )
                )
            ).scalar_one_or_none()
            if already_done:
                await query.answer(get_text(user_lang, "task_err_already"), show_alert=True)
                return
            chat_id = task.chat_id
            task_type = task.task_type

        if chat_id:
            sub_status = await check_user_subscription_status(context.bot, chat_id, user_id)
            if sub_status == "not_member":
                await query.answer(
                    get_text(user_lang, "task_err_not_member"),
                    show_alert=True,
                )
                return
            if sub_status == "error":
                await query.answer(
                    get_text(user_lang, "task_err_check_api"),
                    show_alert=True,
                )
                return

        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            task = (
                await session.execute(select(Task).where(Task.id == task_id))
            ).scalar_one_or_none()
            if not user or not task or task.status != "active":
                await query.answer(get_text(user_lang, "task_err_unavailable"), show_alert=True)
                return

            upd = await session.execute(
                sa_update(Task)
                .where(
                    and_(
                        Task.id == task_id,
                        Task.status == "active",
                        Task.completed_qty < Task.total_qty,
                    )
                )
                .values(completed_qty=Task.completed_qty + 1)
            )
            if upd.rowcount != 1:
                await session.rollback()
                await query.answer(get_text(user_lang, "task_err_completed_now"), show_alert=True)
                return

            await session.refresh(task)
            submission = UserTask(user_id=user_id, task_id=task_id, status="completed")
            session.add(submission)

            reward_info = await award_task_completion(
                session, context.bot, user, task, submission, target_status="completed"
            )
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                await query.answer(get_text(user_lang, "task_err_already"), show_alert=True)
                return

    await dispatch_completion_notifications(context.bot, user_id, reward_info)
    flash_note = format_flash_note(user_lang, reward_info)
    await query.answer(
        get_text(
            user_lang,
            "task_completed_alert",
            reward=reward_info["total_reward"],
            flash_note=flash_note,
        ),
        show_alert=True,
    )
    if reward_info.get("recaptcha_triggered"):
        await enforce_user_access(update, context, apply_rate_limit=False)
        return
    await handle_task_list(update, context, task_type)


async def start_post_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.replace("start_post_", ""))

    async with AsyncSessionLocal() as session:
        task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()

    if not task or task.status != "active":
        await query.answer(get_text(user_lang, "task_err_unavailable"), show_alert=True)
        return

    context.user_data[f"post_timer_{task_id}"] = time.time()
    text = get_text(
        user_lang,
        "post_task_detail",
        title=esc(task.title),
        seconds=MIN_POST_VIEW_SECONDS,
        reward=task.reward_grams,
    )
    keyboard = [
        [InlineKeyboardButton(get_text(user_lang, "post_btn_open"), url=task.target_url)],
        [
            InlineKeyboardButton(
                get_text(user_lang, "post_btn_claim", reward=task.reward_grams),
                callback_data=f"claim_post_{task.id}",
            )
        ],
        [InlineKeyboardButton(get_text(user_lang, "btn_back"), callback_data="tasks_post")],
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def claim_post_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    user_lang = get_user_lang(db_user)
    task_id = int(query.data.replace("claim_post_", ""))

    started = context.user_data.get(f"post_timer_{task_id}")
    if not started:
        await query.answer(get_text(user_lang, "post_err_open_first"), show_alert=True)
        return

    elapsed = time.time() - float(started)
    if elapsed < MIN_POST_VIEW_SECONDS:
        rem = int(math.ceil(MIN_POST_VIEW_SECONDS - elapsed))
        await query.answer(get_text(user_lang, "post_err_wait", rem=rem), show_alert=True)
        return

    async with user_lock_manager.acquire_ordered_locks(("user", user_id), ("task", task_id)):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            task = (
                await session.execute(select(Task).where(Task.id == task_id))
            ).scalar_one_or_none()
            if user:
                user_lang = get_user_lang(user)
            if not user or not task or task.status != "active" or task.created_by == user_id:
                await query.answer(get_text(user_lang, "task_err_unavailable"), show_alert=True)
                return

            already = (
                await session.execute(
                    select(UserTask).where(
                        and_(UserTask.user_id == user_id, UserTask.task_id == task_id)
                    )
                )
            ).scalar_one_or_none()
            if already:
                await query.answer(get_text(user_lang, "post_err_already"), show_alert=True)
                return

            upd = await session.execute(
                sa_update(Task)
                .where(
                    and_(
                        Task.id == task_id,
                        Task.status == "active",
                        Task.completed_qty < Task.total_qty,
                    )
                )
                .values(completed_qty=Task.completed_qty + 1)
            )
            if upd.rowcount != 1:
                await session.rollback()
                await query.answer(get_text(user_lang, "task_err_completed_now"), show_alert=True)
                return

            await session.refresh(task)
            submission = UserTask(user_id=user_id, task_id=task_id, status="completed")
            session.add(submission)
            reward_info = await award_task_completion(
                session, context.bot, user, task, submission, target_status="completed"
            )
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                await query.answer(get_text(user_lang, "task_err_already"), show_alert=True)
                return

    context.user_data.pop(f"post_timer_{task_id}", None)
    await dispatch_completion_notifications(context.bot, user_id, reward_info)
    flash_note = format_flash_note(user_lang, reward_info)
    await query.answer(
        get_text(
            user_lang,
            "post_claimed_alert",
            reward=reward_info["total_reward"],
            flash_note=flash_note,
        ),
        show_alert=True,
    )
    if reward_info.get("recaptcha_triggered"):
        await enforce_user_access(update, context, apply_rate_limit=False)
        return
    await handle_task_list(update, context, "post")


async def open_bot_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.replace("open_bot_task_", ""))

    async with AsyncSessionLocal() as session:
        task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()

    if not task or task.status != "active":
        await query.answer(get_text(user_lang, "task_err_unavailable"), show_alert=True)
        return

    desc_line = (
        get_text(user_lang, "task_desc_line", desc=esc(task.description))
        if task.description
        else ""
    )
    text = get_text(
        user_lang,
        "bot_task_detail",
        title=esc(task.title),
        reward=task.reward_grams,
        desc_line=desc_line,
    )

    keyboard = [[InlineKeyboardButton(get_text(user_lang, "bot_btn_open"), url=task.target_url)]]
    if task.bot_username:
        keyboard.append(
            [
                InlineKeyboardButton(
                    get_text(user_lang, "bot_btn_fwd"),
                    callback_data=f"prompt_bot_fwd_{task.id}",
                )
            ]
        )
    keyboard.append(
        [InlineKeyboardButton(get_text(user_lang, "bot_btn_proof"), callback_data=f"submit_proof_{task.id}")]
    )
    keyboard.append([InlineKeyboardButton(get_text(user_lang, "btn_back"), callback_data=f"tasks_{task.task_type}")])

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def prompt_bot_forward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.replace("prompt_bot_fwd_", ""))

    async with AsyncSessionLocal() as session:
        task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()

    if not task or not task.bot_username:
        await query.answer(get_text(user_lang, "bot_fwd_err_disabled"), show_alert=True)
        return

    context.user_data["awaiting_bot_forward_task_id"] = task_id
    await query.edit_message_text(
        get_text(user_lang, "bot_fwd_prompt", bot_username=esc(task.bot_username)),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(get_text(user_lang, "btn_back"), callback_data=f"open_bot_task_{task.id}")]]
        ),
    )


async def handle_bot_forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Process forwarded bot message for instant auto-verification."""
    task_id = context.user_data.get("awaiting_bot_forward_task_id")
    if not task_id:
        return False

    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return True

    user_id = update.effective_user.id
    user_lang = get_user_lang(db_user)
    origin = getattr(update.message, "forward_origin", None)

    if not isinstance(origin, MessageOriginUser) or not origin.sender_user.is_bot:
        await update.message.reply_text(get_text(user_lang, "bot_fwd_err_not_bot"))
        return True

    fwd_username = (origin.sender_user.username or "").lstrip("@").lower()
    fwd_dt = (
        origin.date.astimezone(timezone.utc).replace(tzinfo=None)
        if origin.date.tzinfo
        else origin.date
    )
    if (utcnow() - fwd_dt).total_seconds() > 300:
        await update.message.reply_text(get_text(user_lang, "bot_fwd_err_stale"))
        return True

    async with user_lock_manager.acquire_ordered_locks(("user", user_id), ("task", task_id)):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            task = (
                await session.execute(select(Task).where(Task.id == task_id))
            ).scalar_one_or_none()
            if user:
                user_lang = get_user_lang(user)
            if not user or not task or task.status != "active":
                context.user_data.pop("awaiting_bot_forward_task_id", None)
                await update.message.reply_text(get_text(user_lang, "task_err_unavailable"))
                return True

            expected = (task.bot_username or "").lstrip("@").lower()
            if not expected or fwd_username != expected:
                await update.message.reply_text(
                    get_text(
                        user_lang,
                        "bot_fwd_err_wrong_bot",
                        actual=esc(fwd_username),
                        expected=esc(expected),
                    ),
                    parse_mode="HTML",
                )
                return True

            already = (
                await session.execute(
                    select(UserTask).where(
                        and_(UserTask.user_id == user_id, UserTask.task_id == task_id)
                    )
                )
            ).scalar_one_or_none()
            if already:
                context.user_data.pop("awaiting_bot_forward_task_id", None)
                await update.message.reply_text(get_text(user_lang, "task_err_already"))
                return True

            upd = await session.execute(
                sa_update(Task)
                .where(
                    and_(
                        Task.id == task_id,
                        Task.status == "active",
                        Task.completed_qty < Task.total_qty,
                    )
                )
                .values(completed_qty=Task.completed_qty + 1)
            )
            if upd.rowcount != 1:
                await session.rollback()
                context.user_data.pop("awaiting_bot_forward_task_id", None)
                await update.message.reply_text(get_text(user_lang, "task_err_completed_now"))
                return True

            await session.refresh(task)
            submission = UserTask(user_id=user_id, task_id=task_id, status="completed")
            session.add(submission)
            reward_info = await award_task_completion(
                session, context.bot, user, task, submission, target_status="completed"
            )
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                context.user_data.pop("awaiting_bot_forward_task_id", None)
                await update.message.reply_text(get_text(user_lang, "task_err_already"))
                return True

    context.user_data.pop("awaiting_bot_forward_task_id", None)
    await dispatch_completion_notifications(context.bot, user_id, reward_info)
    flash_note = format_flash_note(user_lang, reward_info)
    await update.message.reply_text(
        get_text(
            user_lang,
            "bot_fwd_success",
            reward=reward_info["total_reward"],
            flash_note=flash_note,
        ),
        parse_mode="HTML",
    )
    return True


async def open_proof_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.replace("open_proof_task_", ""))

    async with AsyncSessionLocal() as session:
        task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()

    if not task or task.status != "active":
        await query.answer(get_text(user_lang, "task_err_unavailable"), show_alert=True)
        return

    emoji_line = (
        get_text(user_lang, "proof_emoji_line", emoji=esc(task.required_emoji))
        if task.required_emoji
        else ""
    )
    desc_line = (
        get_text(user_lang, "task_desc_line", desc=esc(task.description))
        if task.description
        else ""
    )
    is_auto_rx = bool(
        getattr(task, "auto_verify_reactions", False)
        and task.task_type in ("reaction_random", "reaction_fixed")
    )
    steps_text = get_text(
        user_lang,
        "proof_task_auto_note" if is_auto_rx else "proof_task_manual_steps",
    )

    text = get_text(
        user_lang,
        "proof_task_detail",
        title=esc(task.title),
        reward=task.reward_grams,
        emoji_line=emoji_line,
        desc_line=desc_line,
        steps_text=steps_text,
    )

    keyboard = [
        [InlineKeyboardButton(get_text(user_lang, "proof_btn_open"), url=task.target_url)],
        [InlineKeyboardButton(get_text(user_lang, "proof_btn_submit"), callback_data=f"submit_proof_{task.id}")],
        [InlineKeyboardButton(get_text(user_lang, "btn_back"), callback_data=f"tasks_{task.task_type}")],
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def submit_proof_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.replace("submit_proof_", ""))
    context.user_data["pending_task_id"] = task_id

    await query.edit_message_text(get_text(user_lang, "proof_submit_prompt"), parse_mode="HTML")


async def skip_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_lang = get_user_lang(db_user)
    query = update.callback_query
    user_id = update.effective_user.id
    parts = query.data.split("_")
    task_id = int(parts[2])
    page = int(parts[-1])
    category = "_".join(parts[3:-1])

    async with AsyncSessionLocal() as session:
        session.add(SkippedTask(user_id=user_id, task_id=task_id))
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()

    await query.answer(get_text(user_lang, "task_skipped_alert"))
    await handle_task_list(update, context, category, page)


async def report_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.replace("report_task_", ""))
    context.user_data["awaiting_report_task_id"] = task_id
    await query.edit_message_text(
        get_text(user_lang, "report_task_prompt", task_id=task_id),
        parse_mode="HTML",
    )


async def report_issue_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_report_task_id"] = 0
    await query.edit_message_text(
        get_text(user_lang, "report_issue_prompt"),
        parse_mode="HTML",
    )


async def process_report_reason_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    task_id = context.user_data.get("awaiting_report_task_id")
    if task_id is None:
        return False

    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return True

    user_id = update.effective_user.id
    user_lang = get_user_lang(db_user)
    reason = update.message.text.strip()[:500]
    context.user_data.pop("awaiting_report_task_id", None)

    report_id = None
    task_title = "بلاغ عام"
    if task_id > 0:
        async with AsyncSessionLocal() as session:
            task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
            if task:
                task_title = task.title
                rep = TaskReport(reporter_id=user_id, task_id=task_id, reason=reason, status="open")
                session.add(rep)
                await session.commit()
                report_id = rep.id

    await update.message.reply_text(get_text(user_lang, "report_received"), parse_mode="HTML")

    admin_msg = (
        f"🚨 <b>بلاغ جديد من مستخدم:</b>\n\n"
        f"👤 المبلغ: <code>{user_id}</code>\n"
        f"📌 المهمة: #{task_id} — <b>{esc(task_title)}</b>\n"
        f"📝 السبب: {esc(reason)}"
    )
    keyboard = []
    if report_id:
        keyboard = [
            [
                InlineKeyboardButton("⏸️ إيقاف المهمة", callback_data=f"admin_report_pause_{report_id}"),
                InlineKeyboardButton("🗑️ حذف المهمة", callback_data=f"admin_report_del_{report_id}"),
            ],
            [InlineKeyboardButton("✔️ إغلاق البلاغ", callback_data=f"admin_report_dismiss_{report_id}")],
        ]
    markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id, text=admin_msg, parse_mode="HTML", reply_markup=markup
            )
        except Exception:
            pass
    return True
