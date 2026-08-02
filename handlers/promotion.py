import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import User, Task

async def show_promotion_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        balance = user.balance if user else 0

    text = (
        f"📣 ماذا تريد أن تروّج؟\n\n"
        f"💳 **رصيدك:** {balance:,} غرام"
    )

    keyboard = [
        [
            InlineKeyboardButton("👥 مجموعة", callback_data="promo_cat_group"),
            InlineKeyboardButton("📣 قناة", callback_data="promo_cat_channel")
        ],
        [
            InlineKeyboardButton("🤖 بوت", callback_data="promo_cat_bot"),
            InlineKeyboardButton("👁️ منشور", callback_data="promo_cat_post")
        ],
        [
            InlineKeyboardButton("🔥 التفاعلات", callback_data="promo_cat_reactions"),
            InlineKeyboardButton("⚡ شحن بريميوم", callback_data="promo_cat_premium")
        ],
        [InlineKeyboardButton("⚙️ إعدادات المهام التلقائية", callback_data="promo_auto_settings")],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="close_menu"),
            InlineKeyboardButton("💼 مهامي", callback_data="promo_my_tasks")
        ]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def promo_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("promo_cat_", "")
    context.user_data["promo_category"] = category

    text = (
        "اختر نوع الحساب:\n\n"
        "1️⃣ **جميع المستخدمين** – متاح لكل مستخدمي PR GRAM لانتشار السريع.\n"
        "🔴 الحد الأدنى للسعر للوحدة – 750 غرام\n\n"
        "2️⃣ **Telegram Premium** – متاح فقط لمستخدمي Telegram Premium 🌟 الجمهور أعلى جودة.\n"
        "🔴 الحد الأدنى للسعر للوحدة – 1,400 غرام"
    )

    keyboard = [
        [InlineKeyboardButton("1️⃣ متاح لجميع المستخدمين", callback_data="account_type_all")],
        [InlineKeyboardButton("2️⃣ فقط مستخدمو Telegram Premium 🌟", callback_data="account_type_premium")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")]
    ]

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def promo_account_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    acc_type = query.data.replace("account_type_", "")
    context.user_data["promo_acc_type"] = acc_type
    min_price = 1400 if acc_type == "premium" else 750
    context.user_data["min_price"] = min_price

    text = (
        "🎯 **الجمهور:** 🌐 بدون قيود\n\n"
        "🌍 **اختر الجمهور المستهدف للمهمة:**\n\n"
        "💡 *إلى الحد الأدنى للسعر لكل تنفيذ عند تطبيق الفلتر +100 GRAM*"
    )

    keyboard = [
        [InlineKeyboardButton("🌍 السماح للجميع", callback_data="audience_all")],
        [InlineKeyboardButton("🎯 اختيار الجمهور", callback_data="audience_custom")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")]
    ]

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def promo_audience_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    aud_choice = query.data

    if aud_choice == "audience_custom":
        return await show_language_grid(update, context)

    return await prompt_price_input(update, context)

async def show_language_grid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = (
        "🎯 **الجمهور:** 🌐 بدون قيود\n\n"
        "🌍 **اختر لغة أو أكثر بالضغط على الأزرار أدناه:**\n\n"
        "💡 *إلى الحد الأدنى للسعر لكل تنفيذ عند تطبيق الفلتر +100 GRAM*"
    )

    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"), InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"), InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"), InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"), InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")],
        [InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="lang_id"), InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"), InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa")],
        [InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn"), InlineKeyboardButton("🇮🇳 हिंदी", callback_data="lang_hi"), InlineKeyboardButton("🇧🇷 Português", callback_data="lang_pt")],
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kk"), InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr"), InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="audience_all")]
    ]

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def prompt_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    min_price = context.user_data.get("min_price", 750)

    text = (
        f"حدد سعر اشتراك واحد/انضمام إلى مجموعة لإنشاء مهمة، يجب أن يكون لديك رصيد GRAM كافٍ.\n\n"
        f"🔴 **السعر الأدنى للوحدة – {min_price:,} غرام**\n\n"
        f"💡 *ملاحظة: الطلب مرتفع حالياً، لذا لضمان الظهور في الصفحات الأولى اجعل السعر لا يقل عن {min_price + 965:,} غرام.*\n\n"
        f"📝 **أدخل السعر لـ مشترك واحد:**"
    )

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def prompt_qty_input(update: Update, context: ContextTypes.DEFAULT_TYPE, price: int, error_msg: str = None):
    user_id = update.effective_user.id
    context.user_data["unit_price"] = price

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        balance = user.balance if user else 0

    cost_per_unit = price * 1.15
    max_qty = math.floor(balance / cost_per_unit) if cost_per_unit > 0 else 0
    context.user_data["max_qty"] = max_qty

    text = ""
    if error_msg:
        text += f"{error_msg}\n\n"

    text += (
        f"🔔 **تنبيه: سيتم احتساب عمولة 15% عند إنشاء المهمة.**\n\n"
        f"💵 **سعر الاشتراك الواحد:** {price:,} غرام\n"
        f"💰 **رصيدك:** {balance:,} غرام\n\n"
        f"📝 **أدخل عدد الاشتراكات، أو اختر:**\n\n"
        f"**الحد الأقصى لرصيدك:** {max_qty}"
    )

    keyboard = []
    if max_qty >= 10:
        keyboard.append([InlineKeyboardButton("10", callback_data="qty_select_10")])
    if max_qty >= 3:
        keyboard.append([InlineKeyboardButton(f"(الحد الأقصى لرصيدك) {max_qty}", callback_data=f"qty_select_{max_qty}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def process_qty_input(update: Update, context: ContextTypes.DEFAULT_TYPE, qty: int):
    min_qty = 3
    max_qty = context.user_data.get("max_qty", 0)
    price = context.user_data.get("unit_price", 750)

    if qty < min_qty:
        err = "❌ خطأ! الحد الأدنى لعدد المشتركين في المهمة – 3."
        return await prompt_qty_input(update, context, price, error_msg=err)

    if qty > max_qty:
        err = f"❌ خطأ! الرصيد لا يكفي لإنشاء المهمة بعدد {qty}. الحد الأقصى لرصيدك هو {max_qty}."
        return await prompt_qty_input(update, context, price, error_msg=err)

    context.user_data["task_qty"] = qty
    return await prompt_payment_method(update, context)

async def prompt_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qty = context.user_data.get("task_qty", 3)
    price = context.user_data.get("unit_price", 750)
    total_gram = math.ceil(qty * price * 1.15)

    context.user_data["total_gram"] = total_gram

    text = (
        "اختر طريقة الدفع لمهمتك:\n\n"
        "🔔 **تنطبق عمولة 15% على مدفوعات GRAM.**\n"
        "💡 يمكنك التبرع بـ 50 🌟 على الأقل – وسيلغي تعطل العمولة لمدة 24 ساعة.\n"
        "كل 50 🌟 إضافية تمدد فترة بدون عمولة بـ 24 ساعة أخرى."
    )

    keyboard = [
        [InlineKeyboardButton(f"💎 {total_gram:,} GRAM", callback_data="pay_method_gram")],
        [InlineKeyboardButton("🌟 3 Telegram stars (-15%)", callback_data="pay_method_stars")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")]
    ]

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def prompt_target_chat_picker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    text = (
        "اضغط على الزر لاختيار المحادثة التي تريد الترويج لها.\n\n"
        "⚠️ **يجب أن يكون البوت مشرفاً في المحادثة/القناة.**\n\n"
        "يمكنك الاختيار:\n"
        "- 🏫 **محادثتي** حيث تكون أنت المشرف وسَيُمنح البوت صلاحيات الدعوة تلقائياً.\n"
        "- 🌐 **محادثة أخرى** حيث لست مشرفاً، وستحتاج لمنح البوت الصلاحيات يدوياً."
    )

    keyboard = [
        [InlineKeyboardButton("اختر 📣 قناتي", callback_data="pick_my_channel")],
        [InlineKeyboardButton("اختر 🌐 قناة أخرى", callback_data="pick_other_channel")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")]
    ]

    markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def show_my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    async with AsyncSessionLocal() as session:
        user_tasks = (await session.execute(select(Task).where(Task.created_by == user_id))).scalars().all()

    if not user_tasks:
        text = "💼 **مهامي:**\n\nليس لديك أي حملات ترويجية قائمة حالياً."
    else:
        text = "💼 **قائمة حملاتك الترويجية:**\n\n"
        for t in user_tasks:
            text += f"🔹 **{t.title}** ({t.completed_qty}/{t.total_qty}) - السعر: {t.reward_grams} غرام - الحالة: {t.status}\n"

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
