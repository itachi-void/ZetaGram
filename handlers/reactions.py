from typing import Tuple, Set
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select, update as sa_update, and_
from sqlalchemy.exc import IntegrityError

from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask
from utils.telegram_api import normalize_emoji
from utils.security import user_lock_manager
from utils.rewards import award_task_completion, dispatch_completion_notifications
from utils.i18n import get_text, get_user_lang
from utils.html_utils import esc, utcnow


def _extract_reaction_tokens(reactions) -> Tuple[Set[str], Set[str]]:
    """
    Extract normalized reaction tokens and emoji strings from a Telegram ReactionType sequence.
    Returns (all_tokens, normalized_emojis).
    """
    all_tokens: Set[str] = set()
    norm_emojis: Set[str] = set()
    if not reactions:
        return all_tokens, norm_emojis

    for r in reactions:
        emoji_val = getattr(r, "emoji", None)
        if emoji_val:
            ne = normalize_emoji(emoji_val)
            all_tokens.add(f"emoji:{ne}")
            norm_emojis.add(ne)
            continue
        custom_id = getattr(r, "custom_emoji_id", None)
        if custom_id:
            all_tokens.add(f"custom:{custom_id}")
            continue
        all_tokens.add(f"other:{getattr(r, 'type', 'paid')}")

    return all_tokens, norm_emojis


async def handle_message_reaction_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Automatically verify and pay out reaction tasks when a user reacts to a tracked
    channel/group message (MessageReactionUpdated) without requiring screenshots.
    Returns the number of tasks awarded.
    """
    mr = getattr(update, "message_reaction", None)
    if not mr or not mr.user or getattr(mr.user, "is_bot", False):
        return 0

    new_tokens, new_emojis = _extract_reaction_tokens(getattr(mr, "new_reaction", None))
    old_tokens, _ = _extract_reaction_tokens(getattr(mr, "old_reaction", None))
    added_tokens = new_tokens - old_tokens
    if not added_tokens:
        return 0

    user_id = mr.user.id
    chat = getattr(mr, "chat", None)
    if not chat:
        return 0

    candidate_chats: Set[str] = {str(chat.id).lower()}
    if getattr(chat, "username", None):
        candidate_chats.add(f"@{chat.username.lstrip('@').lower()}")

    msg_id = mr.message_id
    async with AsyncSessionLocal() as session:
        stmt = select(Task).where(
            and_(
                Task.task_type.in_(["reaction_random", "reaction_fixed"]),
                Task.status == "active",
                Task.target_message_id == msg_id,
                Task.completed_qty < Task.total_qty,
                Task.created_by != user_id,
            )
        )
        raw_tasks = (await session.execute(stmt)).scalars().all()

    matching_tasks = [
        t for t in raw_tasks if (t.chat_id or "").strip().lower() in candidate_chats
    ]
    if not matching_tasks:
        return 0

    is_premium = bool(getattr(mr.user, "is_premium", False))
    awarded_count = 0

    for t in matching_tasks:
        if t.task_type == "reaction_fixed" and t.required_emoji:
            if normalize_emoji(t.required_emoji) not in new_emojis:
                continue

        reward_info = None
        task_title = t.title
        u_lang = "ar"

        async with user_lock_manager.acquire_ordered_locks(("user", user_id), ("task", t.id)):
            async with AsyncSessionLocal() as session:
                user = (
                    await session.execute(select(User).where(User.telegram_id == user_id))
                ).scalar_one_or_none()
                task = (
                    await session.execute(select(Task).where(Task.id == t.id))
                ).scalar_one_or_none()

                now = utcnow()
                if not user or not user.is_captcha_verified:
                    continue
                if user.banned_until and now < user.banned_until:
                    continue
                if (
                    not task
                    or task.status != "active"
                    or task.completed_qty >= task.total_qty
                    or task.created_by == user_id
                ):
                    continue
                if task.requires_premium and not is_premium:
                    continue

                u_lang = get_user_lang(user)
                if task.target_languages:
                    allowed = {
                        x.strip().lower()
                        for x in task.target_languages.split(",")
                        if x.strip()
                    }
                    if allowed and u_lang not in allowed:
                        continue

                existing_ut = (
                    await session.execute(
                        select(UserTask).where(
                            and_(UserTask.user_id == user_id, UserTask.task_id == task.id)
                        )
                    )
                ).scalar_one_or_none()

                if existing_ut and existing_ut.status in ("completed", "approved"):
                    continue

                upd = await session.execute(
                    sa_update(Task)
                    .where(
                        and_(
                            Task.id == task.id,
                            Task.status == "active",
                            Task.completed_qty < Task.total_qty,
                        )
                    )
                    .values(completed_qty=Task.completed_qty + 1)
                )
                if upd.rowcount != 1:
                    await session.rollback()
                    continue

                await session.refresh(task)
                if existing_ut:
                    submission = existing_ut
                else:
                    submission = UserTask(
                        user_id=user_id, task_id=task.id, status="completed"
                    )
                    session.add(submission)

                reward_info = await award_task_completion(
                    session, context.bot, user, task, submission, target_status="completed"
                )
                task_title = task.title
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    continue

        if reward_info:
            awarded_count += 1
            await dispatch_completion_notifications(context.bot, user_id, reward_info)
            try:
                if reward_info.get("flash_bonus"):
                    msg_text = get_text(
                        u_lang,
                        "reaction_auto_paid_flash",
                        title=esc(task_title),
                        mult=reward_info.get("flash_mult_str", "2x"),
                        reward=reward_info["total_reward"],
                        flash_bonus=reward_info["flash_bonus"],
                    )
                else:
                    msg_text = get_text(
                        u_lang,
                        "reaction_auto_paid",
                        title=esc(task_title),
                        reward=reward_info["total_reward"],
                    )
                await context.bot.send_message(
                    chat_id=user_id, text=msg_text, parse_mode="HTML"
                )
            except Exception:
                pass

    return awarded_count
