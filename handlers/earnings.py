from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, and_

from database.db import AsyncSessionLocal
from database.models import Task, UserTask, SkippedTask
from utils.gatekeeper import enforce_user_access


async def _get_available_counts_for_user(
    user_id: int, user_lang: str, is_premium: bool
) -> Counter:
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

    counts = Counter()
    for t in tasks:
        if t.requires_premium and not is_premium:
            continue
        if t.target_languages:
            allowed = {x.strip().lower() for x in t.target_languages.split(",") if x.strip()}
            if allowed and user_lang not in allowed:
                continue
        counts[t.task_type] += 1
    return counts


async def show_earnings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_id = update.effective_user.id
    user_lang = (db_user.language if db_user and db_user.language else "ar").lower()
    is_premium = bool(getattr(update.effective_user, "is_premium", False))

    counts = await _get_available_counts_for_user(user_id, user_lang, is_premium)
    channel_count = counts["channel"]
    group_count = counts["group"]
    post_count = counts["post"]
    bot_count = counts["bot_normal"] + counts["bot_webapp"] + counts["bot_conditions"]
    reactions_count = counts["reaction_random"] + counts["reaction_fixed"]
    premium_count = counts["premium"]

    text = (
        f"📣 مهام القنوات: {channel_count}\n"
        f"👤 مهام المجموعات: {group_count}\n"
        f"👁️ مهام المشاهدة: {post_count}\n"
        f"🤖 مهام البوت: {bot_count}\n"
        f"⚡ مهام الشحن: {premium_count}\n"
        f"🔥 مهام التفاعل: {reactions_count}\n\n"
        f"🔔 اختر طريقة الكسب 👇"
    )

    keyboard = [
        [InlineKeyboardButton("📣 اشترك في القناة", callback_data="tasks_channel")],
        [InlineKeyboardButton("👥 انضم إلى المجموعة", callback_data="tasks_group")],
        [InlineKeyboardButton("👁️ عرض المنشورات", callback_data="tasks_post")],
        [InlineKeyboardButton("🤖 الانتقال إلى البوت", callback_data="tasks_bot_menu")],
        [InlineKeyboardButton("🔥 تفاعلات", callback_data="tasks_reactions_menu")],
        [InlineKeyboardButton("⚡ شحن بريميوم", callback_data="tasks_premium")],
        [InlineKeyboardButton("📕 القواعد", callback_data="tasks_rules")],
        [InlineKeyboardButton("🔙 إلغاء", callback_data="close_menu")],
    ]

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)


async def show_bot_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_lang = (db_user.language if db_user and db_user.language else "ar").lower()
    is_premium = bool(getattr(update.effective_user, "is_premium", False))

    counts = await _get_available_counts_for_user(user_id, user_lang, is_premium)

    text = (
        f"اختر فئة البوت.\n"
        f"العادية: {counts['bot_normal']}\n"
        f"الويب: {counts['bot_webapp']}\n"
        f"مع الشروط: {counts['bot_conditions']}\n\n"
        f"📱 <b>بوتات مع Web App</b>\n"
        f"بوتات تملك تكاملاً مع تطبيقات الويب.\n\n"
        f"🤖 <b>بوتات عادية</b>\n"
        f"بوتات تليجرام التقليدية دون واجهات ويب إضافية.\n\n"
        f"📋 <b>بوتات بشروط إضافية</b>\n"
        f"يجب تنفيذ إجراءات إضافية: اجتياز كابتشا، اختيار لغة، أو الاشتراك في قنوات."
    )

    keyboard = [
        [
            InlineKeyboardButton("🤖 بوتات عادية", callback_data="tasks_bot_normal"),
            InlineKeyboardButton("📱 بوتات مع Web App", callback_data="tasks_bot_webapp"),
        ],
        [InlineKeyboardButton("📋 مع شروط إضافية", callback_data="tasks_bot_conditions")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="earnings_menu")],
    ]

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_reactions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_lang = (db_user.language if db_user and db_user.language else "ar").lower()
    is_premium = bool(getattr(update.effective_user, "is_premium", False))

    counts = await _get_available_counts_for_user(user_id, user_lang, is_premium)

    text = (
        f"اختر فئة التفاعل.\n"
        f"أي تفاعل: {counts['reaction_random']}\n"
        f"التفاعل المحدد: {counts['reaction_fixed']}\n\n"
        f"أي تفاعل – يمكنك اختيار ما تريد للحصول على الدفع.\n\n"
        f"التفاعل المحدد – يجب استخدام التفاعل المذكور للدفع."
    )

    keyboard = [
        [InlineKeyboardButton("تفاعلات عشوائية", callback_data="tasks_reaction_random")],
        [InlineKeyboardButton("🎯 تفاعلات ثابتة", callback_data="tasks_reaction_fixed")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="earnings_menu")],
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_rules_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()

    text = (
        "📕 <b>قواعد تنفيذ المهام:</b>\n\n"
        "يُمنع إلغاء الاشتراك من القنوات/المجموعات قبل مرور <b>7 أيام</b>.\n"
        "مخالفة القاعدة تعني خصم المكافأة تلقائياً، خفض نقاط الثقة، وحظر تنفيذ المهام:\n\n"
        "• مخالفة أولى – حظر 24 ساعة\n"
        "• مخالفتان – حظر 7 أيام\n"
        "• ثلاث مخالفات أو أكثر – <b>حظر دائم</b>"
    )

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="earnings_menu")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
