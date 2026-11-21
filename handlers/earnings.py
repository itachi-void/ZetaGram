from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, and_

from database.db import AsyncSessionLocal
from database.models import Task, UserTask, SkippedTask
from utils.gatekeeper import enforce_user_access
from utils.promotions import get_active_flash_event, format_multiplier
from utils.i18n import get_text, get_user_lang
from utils.html_utils import esc


async def _get_available_counts_for_user(
    user_id: int, user_lang: str, is_premium: bool
) -> tuple[Counter, object]:
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
        excluded = list(set(completed_ids + skipped_ids))

        stmt = select(Task).where(
            and_(
                Task.status == "active",
                Task.created_by != user_id,
                Task.completed_qty < Task.total_qty,
                Task.id.not_in(excluded) if excluded else True,
            )
        )
        tasks = (await session.execute(stmt)).scalars().all()
        flash_event = await get_active_flash_event(session)

    counts = Counter()
    for t in tasks:
        if t.requires_premium and not is_premium:
            continue
        if t.target_languages:
            allowed = {x.strip().lower() for x in t.target_languages.split(",") if x.strip()}
            if allowed and user_lang not in allowed:
                continue
        counts[t.task_type] += 1
    return counts, flash_event


async def show_earnings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_id = update.effective_user.id
    user_lang = get_user_lang(db_user)
    is_premium = bool(getattr(update.effective_user, "is_premium", False))

    counts, flash_event = await _get_available_counts_for_user(user_id, user_lang, is_premium)
    channel_count = counts["channel"]
    group_count = counts["group"]
    post_count = counts["post"]
    bot_count = counts["bot_normal"] + counts["bot_webapp"] + counts["bot_conditions"]
    reactions_count = counts["reaction_random"] + counts["reaction_fixed"]
    premium_count = counts["premium"]

    banner = ""
    if flash_event:
        banner = get_text(
            user_lang,
            "flash_banner_earnings",
            title=esc(flash_event.title),
            mult=format_multiplier(flash_event.multiplier_pct),
            ends=flash_event.ends_at.strftime("%Y-%m-%d %H:%M"),
        )

    text = banner + get_text(
        user_lang,
        "earnings_menu",
        channel_count=channel_count,
        group_count=group_count,
        post_count=post_count,
        bot_count=bot_count,
        premium_count=premium_count,
        reactions_count=reactions_count,
    )

    keyboard = [
        [InlineKeyboardButton(get_text(user_lang, "earnings_btn_channel"), callback_data="tasks_channel")],
        [InlineKeyboardButton(get_text(user_lang, "earnings_btn_group"), callback_data="tasks_group")],
        [InlineKeyboardButton(get_text(user_lang, "earnings_btn_post"), callback_data="tasks_post")],
        [InlineKeyboardButton(get_text(user_lang, "earnings_btn_bot"), callback_data="tasks_bot_menu")],
        [InlineKeyboardButton(get_text(user_lang, "earnings_btn_reactions"), callback_data="tasks_reactions_menu")],
        [InlineKeyboardButton(get_text(user_lang, "earnings_btn_premium"), callback_data="tasks_premium")],
        [InlineKeyboardButton(get_text(user_lang, "earnings_btn_rules"), callback_data="tasks_rules")],
        [InlineKeyboardButton(get_text(user_lang, "btn_cancel"), callback_data="close_menu")],
    ]

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def show_bot_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_lang = get_user_lang(db_user)
    is_premium = bool(getattr(update.effective_user, "is_premium", False))

    counts, _ = await _get_available_counts_for_user(user_id, user_lang, is_premium)

    text = get_text(
        user_lang,
        "earnings_bot_menu",
        bot_normal=counts["bot_normal"],
        bot_webapp=counts["bot_webapp"],
        bot_conditions=counts["bot_conditions"],
    )

    keyboard = [
        [
            InlineKeyboardButton(get_text(user_lang, "earnings_btn_bot_normal"), callback_data="tasks_bot_normal"),
            InlineKeyboardButton(get_text(user_lang, "earnings_btn_bot_webapp"), callback_data="tasks_bot_webapp"),
        ],
        [InlineKeyboardButton(get_text(user_lang, "earnings_btn_bot_conditions"), callback_data="tasks_bot_conditions")],
        [InlineKeyboardButton(get_text(user_lang, "btn_back"), callback_data="earnings_menu")],
    ]

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_reactions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_lang = get_user_lang(db_user)
    is_premium = bool(getattr(update.effective_user, "is_premium", False))

    counts, _ = await _get_available_counts_for_user(user_id, user_lang, is_premium)

    text = get_text(
        user_lang,
        "earnings_reactions_menu",
        reaction_random=counts["reaction_random"],
        reaction_fixed=counts["reaction_fixed"],
    )

    keyboard = [
        [InlineKeyboardButton(get_text(user_lang, "earnings_btn_reaction_random"), callback_data="tasks_reaction_random")],
        [InlineKeyboardButton(get_text(user_lang, "earnings_btn_reaction_fixed"), callback_data="tasks_reaction_fixed")],
        [InlineKeyboardButton(get_text(user_lang, "btn_back"), callback_data="earnings_menu")],
    ]

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_rules_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    lang = get_user_lang(db_user)

    text = get_text(lang, "earnings_rules_text")
    keyboard = [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="earnings_menu")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
