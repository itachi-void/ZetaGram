from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func
from database.db import AsyncSessionLocal
from database.models import Task, UserTask

async def show_earnings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        # Get active tasks count by category
        channel_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type == "channel", Task.status == "active"))).scalar() or 0
        group_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type == "group", Task.status == "active"))).scalar() or 0
        post_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type == "post", Task.status == "active"))).scalar() or 0
        bot_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type.like("bot_%"), Task.status == "active"))).scalar() or 0
        reactions_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type.like("reaction_%"), Task.status == "active"))).scalar() or 0
        premium_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type == "premium", Task.status == "active"))).scalar() or 0

    text = (
        f"📣 مهام القنوات: {channel_count}\n"
        f"👤 مهام المجموعات: {group_count}\n"
        f"👁️ مهام المشاهدة: {post_count}\n"
        f"🤖 مهام البوت: {bot_count}\n"
        f"⚡ مهام الشحن: {premium_count}\n"
        f"🔥 مهام التفاعل: {reactions_count}\n\n"
        f"🔔 اختر طريقة الكسب👇"
    )

    keyboard = [
        [InlineKeyboardButton("📣 اشترك في القناة", callback_data="tasks_channel")],
        [InlineKeyboardButton("👥 انضم إلى المجموعة", callback_data="tasks_group")],
        [InlineKeyboardButton("👁️ عرض المنشورات", callback_data="tasks_post")],
        [InlineKeyboardButton("🤖 الانتقال إلى البوت", callback_data="tasks_bot_menu")],
        [InlineKeyboardButton("🔥 تفاعلات", callback_data="tasks_reactions_menu")],
        [InlineKeyboardButton("⚡ شحن بريميوم", callback_data="tasks_premium")],
        [InlineKeyboardButton("📕 القواعد", callback_data="tasks_rules")],
        [InlineKeyboardButton("🔙 إلغاء", callback_data="close_menu")]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

async def show_bot_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with AsyncSessionLocal() as session:
        normal_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type == "bot_normal", Task.status == "active"))).scalar() or 0
        webapp_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type == "bot_webapp", Task.status == "active"))).scalar() or 0
        conditions_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type == "bot_conditions", Task.status == "active"))).scalar() or 0

    text = (
        f"اختر فئة البوت.\n"
        f"العادية: {normal_count}\n"
        f"الويب: {webapp_count}\n"
        f"مع الشروط: {conditions_count}\n\n"
        f"📱 **بوتات مع Web App**\n"
        f"بوتات تملك تكاملاً مع تطبيقات الويب.\n\n"
        f"🤖 **بوتات عادية**\n"
        f"بوتات تليجرام التقليدية دون واجهات ويب إضافية.\n\n"
        f"📋 **بوتات بشروط إضافية**\n"
        f"لا يكفي الضغط على Start، بل يجب تنفيذ إجراءات إضافية: اجتياز كابتشا، اختيار لغة، الاشتراك في قنوات."
    )

    keyboard = [
        [
            InlineKeyboardButton("🤖 بوتات عادية", callback_data="tasks_bot_normal"),
            InlineKeyboardButton("📱 بوتات مع Web App", callback_data="tasks_bot_webapp")
        ],
        [InlineKeyboardButton("📋 مع شروط إضافية", callback_data="tasks_bot_conditions")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="earnings_menu")]
    ]

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_reactions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with AsyncSessionLocal() as session:
        random_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type == "reaction_random", Task.status == "active"))).scalar() or 0
        fixed_count = (await session.execute(select(func.count(Task.id)).where(Task.task_type == "reaction_fixed", Task.status == "active"))).scalar() or 0

    text = (
        f"اختر فئة التفاعل.\n"
        f"أي تفاعل: {random_count}\n"
        f"التفاعل المحدد: {fixed_count}\n\n"
        f"أي تفاعل – يمكنك اختيار ما تريد للحصول على الدفع.\n\n"
        f"التفاعل المحدد – يجب استخدام التفاعل المذكور للدفع."
    )

    keyboard = [
        [InlineKeyboardButton("تفاعلات عشوائية", callback_data="tasks_reaction_random")],
        [InlineKeyboardButton("👥 تفاعلات ثابته", callback_data="tasks_reaction_fixed")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="earnings_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_rules_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "ُيمنع إلغاء الاشتراك من القنوات/المحادثات لمدة 7 أيام. مخالفة القاعدة تعني حظر المهام وإلغاء الأرباح.\n\n"
        "مخالفة أولى – حظر 24 ساعة\n"
        "مخالفتان – حظر 7 أيام\n"
        "ثلاث مخالفات أو أكثر – 7 أيام"
    )

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="earnings_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

