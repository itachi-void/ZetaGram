from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from config import BOT_NAME, REFERRAL_JOIN_BONUS, REFERRAL_ACTIVE_BONUS, DAILY_QUEST_TARGET, DAILY_QUEST_REWARD
from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask
from utils.telegram_api import check_user_subscription_status
from utils.gatekeeper import (
    enforce_user_access,
    get_mandatory_channels_list,
    invalidate_sub_cache,
)
from utils.i18n import get_text, get_user_lang
from utils.html_utils import esc


async def show_useful_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    channels = await get_mandatory_channels_list(lang=lang)
    links_str = ""
    for c in channels:
        links_str += f"📢 <b>{esc(c['title'])}:</b>\n{esc(c['channel_link'])}\n\n"
    if not links_str:
        links_str = get_text(lang, "info_no_links")

    text = get_text(
        lang,
        "info_useful_links",
        bot_name=esc(BOT_NAME),
        links_str=links_str,
    )
    keyboard = [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")]]
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )


async def show_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    text = get_text(
        lang,
        "info_instructions",
        bot_name=esc(BOT_NAME),
        quest_target=DAILY_QUEST_TARGET,
        quest_reward=DAILY_QUEST_REWARD,
        ref_active_bonus=REFERRAL_ACTIVE_BONUS,
        ref_join_bonus=REFERRAL_JOIN_BONUS,
    )
    keyboard = [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")]]
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_bot_public_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    async with AsyncSessionLocal() as session:
        users_cnt = (await session.execute(select(func.count(User.telegram_id)))).scalar() or 0
        tasks_cnt = (await session.execute(select(func.count(Task.id)))).scalar() or 0
        completed_cnt = (
            await session.execute(
                select(func.count(UserTask.id)).where(UserTask.status.in_(["completed", "approved"]))
            )
        ).scalar() or 0

    text = get_text(
        lang,
        "info_public_stats",
        bot_name=esc(BOT_NAME),
        users_cnt=users_cnt,
        tasks_cnt=tasks_cnt,
        completed_cnt=completed_cnt,
    )
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "info_btn_leaderboard"), callback_data="show_leaderboard")],
        [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")],
    ]
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def _find_unsubbed_mandatory(bot, user_id: int, lang: str = "ar"):
    channels = await get_mandatory_channels_list(lang=lang)
    unsubbed = []
    for c in channels:
        status = await check_user_subscription_status(bot, c["channel_username"], user_id)
        if status == "not_member":
            unsubbed.append(c)
    return unsubbed


async def check_forced_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(
        update, context, require_mandatory_sub=False
    )
    if not ok:
        return

    user_id = update.effective_user.id
    lang = get_user_lang(user)
    invalidate_sub_cache(user_id)

    unsubbed = await _find_unsubbed_mandatory(context.bot, user_id, lang=lang)
    if not unsubbed:
        await update.message.reply_text(get_text(lang, "forced_sub_ok"), parse_mode="HTML")
    else:
        keyboard = [
            [InlineKeyboardButton(f"📢 {c['title']}", url=c["channel_link"])]
            for c in unsubbed
        ]
        keyboard.append(
            [InlineKeyboardButton(get_text(lang, "btn_recheck_now"), callback_data="recheck_forced_sub")]
        )
        await update.message.reply_text(
            get_text(lang, "forced_sub_required"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def recheck_forced_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(
        update, context, require_mandatory_sub=False
    )
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_user_lang(user)
    invalidate_sub_cache(user_id)

    unsubbed = await _find_unsubbed_mandatory(context.bot, user_id, lang=lang)
    if not unsubbed:
        await query.answer(get_text(lang, "forced_sub_verified_alert"), show_alert=True)
        await query.edit_message_text(get_text(lang, "forced_sub_ok"), parse_mode="HTML")
    else:
        await query.answer(get_text(lang, "forced_sub_missing_alert"), show_alert=True)
        keyboard = [
            [InlineKeyboardButton(f"📢 {c['title']}", url=c["channel_link"])]
            for c in unsubbed
        ]
        keyboard.append(
            [InlineKeyboardButton(get_text(lang, "btn_recheck_now"), callback_data="recheck_forced_sub")]
        )
        await query.edit_message_text(
            get_text(lang, "forced_sub_required"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
