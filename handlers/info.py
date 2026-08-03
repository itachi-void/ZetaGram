from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func
from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask
from utils.telegram_api import check_user_subscription
from handlers.dynamic_subs import get_active_mandatory_channels

async def show_useful_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = await get_active_mandatory_channels()
    links_str = ""
    for c in channels:
        links_str += f"📢 **{c['title']}:**\n{c['channel_link']}\n\n"

    text = (
        "🔗 **الروابط المفيدة:**\n\n"
        f"{links_str}"
        "💡 اضغط على الروابط أعلاه لمتابعة آخر التحديثات وحركات التمويل."
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

async def show_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 **دليل وتعليمات الاستخدام:**\n\n"
        "1️⃣ **كسب الأرباح:** اختر `🧑‍💻 الأرباح` واشترك في القنوات والمجموعات المتاحة ثم اضغط على زر `🔄 فحص` للحصول على الرصيد.\n"
        "2️⃣ **الترويج لقناتك:** اختر `📣 الترويج` وحدد نوع الحساب والعدد وسعر الاشتراك للحصول على مشتركين حقيقيين.\n"
        "3️⃣ **المكافأة اليومية:** اضغط `🎁 المكافأة اليومية` يومياً للحصول على +100 غرام مجاناً.\n"
        "4️⃣ **نظام الإحالة:** انشر رابطك الخاص من قسم `📱 حسابي` واكسب نقاط إضافية عن كل صديق يكمل 3 مهام.\n"
        "5️⃣ **الشيكات وتحويل الرصيد:** يمكنك تحويل الرصيد لأصدقائك أو إنشاء شيكات هدايا.\n\n"
        "⚠️ **ملاحظة هامة:** يُمنع مغادرة القنوات قبل 7 أيام لتجنب الخصم والحظر."
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_bot_public_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        users_cnt = (await session.execute(select(func.count(User.telegram_id)))).scalar() or 0
        tasks_cnt = (await session.execute(select(func.count(Task.id)))).scalar() or 0
        completed_cnt = (await session.execute(select(func.count(UserTask.id)))).scalar() or 0

    text = (
        "📊 **إحصائيات الشبكة:**\n\n"
        f"👥 **إجمالي المستخدمين:** `{users_cnt:,}`\n"
        f"📌 **إجمالي المهام المضافة:** `{tasks_cnt:,}`\n"
        f"✅ **المهام المنفذة:** `{completed_cnt:,}`\n"
        f"⚡ **سرعة التنفيذ:** فوري 100%"
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def check_forced_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    channels = await get_active_mandatory_channels()

    unsubbed_channels = []
    for c in channels:
        is_subbed = await check_user_subscription(context.bot, c["channel_username"], user_id)
        if not is_subbed:
            unsubbed_channels.append(c)

    if not unsubbed_channels:
        await update.message.reply_text("✅ **حسابك مفعّل ومكتمل الاشتراك في جميع القنوات الإجبارية!**", parse_mode="Markdown")
    else:
        keyboard = []
        for c in unsubbed_channels:
            keyboard.append([InlineKeyboardButton(f"📢 {c['title']}", url=c["channel_link"])])
        keyboard.append([InlineKeyboardButton("🔄 تحقق الآن", callback_data="recheck_forced_sub")])

        await update.message.reply_text(
            "⚠️ **أنت غير مشترك في القنوات الإجبارية التالية!**\nيرجى الاشتراك في القنوات أدناه ثم الضغط على تحقق الآن.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
