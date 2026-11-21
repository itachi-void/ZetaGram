import math
from datetime import timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestChat,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    LabeledPrice,
)
from telegram.ext import ContextTypes
from sqlalchemy import select

from config import STARS_FEE_FREE_COST
from database.db import AsyncSessionLocal
from database.models import User, Task, Transaction
from utils.security import user_lock_manager, sanitize_amount, get_vip_perks
from utils.gatekeeper import enforce_user_access
from utils.telegram_api import check_bot_is_admin
from utils.html_utils import esc, utcnow

_PROMO_LANGS = [
    ("ar", "🇸🇦 العربية"),
    ("en", "🇬🇧 English"),
    ("ru", "🇷🇺 Русский"),
    ("uk", "🇺🇦 Українська"),
    ("zh", "🇨🇳 中文"),
    ("de", "🇩🇪 Deutsch"),
    ("es", "🇪🇸 Español"),
    ("fa", "🇮🇷 فارسی"),
    ("hi", "🇮🇳 हिंदी"),
    ("tr", "🇹🇷 Türkçe"),
    ("fr", "🇫🇷 Français"),
    ("id", "🇮🇩 Indonesia"),
    ("bn", "🇧🇩 বাংলা"),
    ("pt", "🇧🇷 Português"),
    ("kk", "🇰🇿 Қазақша"),
    ("uz", "🇺🇿 O'zbekcha"),
]


def _get_effective_promo_fee(user: User) -> float:
    if user and user.fee_free_until and utcnow() < user.fee_free_until:
        return 0.0
    perks = get_vip_perks(user.vip_level if user else 1)
    return perks["promo_fee"]


async def show_promotion_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(update, context)
    if not ok:
        return

    balance = user.balance if user else 0
    fee_pct = round(_get_effective_promo_fee(user) * 100, 1)

    text = (
        f"📣 <b>ماذا تريد أن تروّج؟</b>\n\n"
        f"💳 <b>رصيدك:</b> <code>{balance:,}</code> غرام\n"
        f"📉 <b>عمولتك الحالية:</b> <code>{fee_pct}%</code>"
    )

    keyboard = [
        [
            InlineKeyboardButton("👥 مجموعة", callback_data="promo_cat_group"),
            InlineKeyboardButton("📣 قناة", callback_data="promo_cat_channel"),
        ],
        [
            InlineKeyboardButton("🤖 بوت", callback_data="promo_cat_bot"),
            InlineKeyboardButton("👁️ منشور", callback_data="promo_cat_post"),
        ],
        [
            InlineKeyboardButton("🔥 التفاعلات", callback_data="promo_cat_reactions"),
            InlineKeyboardButton("⚡ شحن بريميوم", callback_data="promo_cat_premium"),
        ],
        [InlineKeyboardButton("⚙️ إعدادات الترويج والعمولة", callback_data="promo_auto_settings")],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="close_menu"),
            InlineKeyboardButton("💼 مهامي وإدارتها", callback_data="promo_my_tasks"),
        ],
    ]

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def promo_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    category = query.data.replace("promo_cat_", "")

    if category == "bot":
        kb = [
            [InlineKeyboardButton("🤖 بوت عادي", callback_data="promo_sub_bot_normal")],
            [InlineKeyboardButton("📱 بوت Web App", callback_data="promo_sub_bot_webapp")],
            [InlineKeyboardButton("📋 بوت بشروط إضافية", callback_data="promo_sub_bot_conditions")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")],
        ]
        await query.edit_message_text(
            "🤖 <b>اختر نوع حملة البوت:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    if category == "reactions":
        kb = [
            [InlineKeyboardButton("🎲 تفاعل عشوائي", callback_data="promo_sub_reaction_random")],
            [InlineKeyboardButton("🎯 تفاعل محدد بإيموجي", callback_data="promo_sub_reaction_fixed")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")],
        ]
        await query.edit_message_text(
            "🔥 <b>اختر نوع التفاعل المطلوب:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    context.user_data["promo_category"] = category
    await _show_account_type_step(query)


async def promo_subtype_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    subtype = query.data.replace("promo_sub_", "")
    context.user_data["promo_category"] = subtype
    await _show_account_type_step(query)


async def _show_account_type_step(query):
    text = (
        "اختر نوع الحساب:\n\n"
        "1️⃣ <b>جميع المستخدمين</b> – متاح لكل مستخدمي ZetaGram للانتشار السريع.\n"
        "🔴 الحد الأدنى للسعر للوحدة – 750 غرام\n\n"
        "2️⃣ <b>Telegram Premium</b> – متاح فقط لمستخدمي Telegram Premium 🌟 الجمهور أعلى جودة.\n"
        "🔴 الحد الأدنى للسعر للوحدة – 1,400 غرام"
    )
    keyboard = [
        [InlineKeyboardButton("1️⃣ متاح لجميع المستخدمين", callback_data="account_type_all")],
        [InlineKeyboardButton("2️⃣ فقط مستخدمو Telegram Premium 🌟", callback_data="account_type_premium")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")],
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def promo_account_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    acc_type = query.data.replace("account_type_", "")
    context.user_data["promo_acc_type"] = acc_type
    context.user_data["min_price"] = 1400 if acc_type == "premium" else 750
    context.user_data["promo_langs"] = []

    text = (
        "🎯 <b>الجمهور:</b> 🌐 بدون قيود\n\n"
        "🌍 <b>اختر الجمهور المستهدف للمهمة:</b>\n\n"
        "💡 <i>يُضاف +100 غرام للحد الأدنى عند تخصيص لغات محددة.</i>"
    )
    keyboard = [
        [InlineKeyboardButton("🌍 السماح للجميع", callback_data="audience_all")],
        [InlineKeyboardButton("🎯 اختيار لغات محددة", callback_data="audience_custom")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")],
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def promo_audience_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    aud_choice = query.data

    if aud_choice == "audience_custom":
        return await show_language_grid(update, context)

    context.user_data["promo_langs"] = []
    return await prompt_price_input(update, context)


async def show_language_grid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    selected = set(context.user_data.get("promo_langs", []))
    selected_str = ", ".join(sorted(selected)) if selected else "🌐 بدون قيود"

    text = (
        f"🎯 <b>اللغات المختارة:</b> {esc(selected_str)}\n\n"
        "🌍 <b>اضغط على اللغات لاختيارها أو إلغائها:</b>\n"
        "💡 <i>تحديد لغة يضيف +100 غرام للحد الأدنى للسعر.</i>"
    )

    keyboard = []
    row = []
    for code, label in _PROMO_LANGS:
        prefix = "✅ " if code in selected else ""
        row.append(InlineKeyboardButton(f"{prefix}{label}", callback_data=f"lang_{code}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(f"✅ تأكيد ({len(selected)} لغة)", callback_data="audience_done")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="audience_all")])

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def toggle_promo_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    lang_code = query.data.replace("lang_", "")
    selected = list(context.user_data.get("promo_langs", []))
    if lang_code in selected:
        selected.remove(lang_code)
    else:
        selected.append(lang_code)
    context.user_data["promo_langs"] = selected
    await show_language_grid(update, context)


async def audience_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    selected = context.user_data.get("promo_langs", [])
    base_min = 1400 if context.user_data.get("promo_acc_type") == "premium" else 750
    context.user_data["min_price"] = base_min + (100 if selected else 0)
    await prompt_price_input(update, context)


async def prompt_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    min_price = context.user_data.get("min_price", 750)
    context.user_data["awaiting_promo_price"] = True

    text = (
        f"حدد سعر اشتراك/تنفيذ واحد. لإنشاء مهمة، يجب أن يكون لديك رصيد كافٍ.\n\n"
        f"🔴 <b>السعر الأدنى للوحدة – {min_price:,} غرام</b>\n\n"
        f"💡 <i>ملاحظة: لظهور أسرع في أعلى القائمة اجعل السعر أعلى من {min_price + 500:,} غرام.</i>\n\n"
        f"📝 <b>اكتب السعر المطلوب للمشترك الواحد الآن (رقم صحيح):</b>"
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")]]
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def process_promo_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("awaiting_promo_price"):
        return False

    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return True

    min_price = context.user_data.get("min_price", 750)
    ok_amt, price, err = sanitize_amount(update.message.text.strip(), min_val=min_price, max_val=1_000_000)
    if not ok_amt:
        await update.message.reply_text(err)
        return True

    context.user_data.pop("awaiting_promo_price", None)
    await prompt_qty_input(update, context, price)
    return True


async def prompt_qty_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, price: int, error_msg: str = None
):
    user_id = update.effective_user.id
    context.user_data["unit_price"] = price

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        balance = user.balance if user else 0
        fee_rate = _get_effective_promo_fee(user)

    context.user_data["promo_fee_rate"] = fee_rate
    cost_per_unit = price * (1.0 + fee_rate)
    max_qty = math.floor(balance / cost_per_unit) if cost_per_unit > 0 else 0
    context.user_data["max_qty"] = max_qty
    context.user_data["awaiting_promo_qty"] = True

    fee_pct = round(fee_rate * 100, 1)
    text = f"{esc(error_msg)}\n\n" if error_msg else ""
    text += (
        f"🔔 <b>تنبيه: العمولة المطبقة لحسابك هي {fee_pct}%.</b>\n\n"
        f"💵 <b>سعر التنفيذ الواحد:</b> {price:,} غرام\n"
        f"💰 <b>رصيدك:</b> {balance:,} غرام\n\n"
        f"📝 <b>اكتب عدد التنفيذات المطلوب (أدنى حد 3)، أو اختر:</b>\n"
        f"<b>الحد الأقصى لرصيدك:</b> {max_qty}"
    )

    keyboard = []
    if max_qty >= 3:
        row = []
        if max_qty >= 5:
            row.append(InlineKeyboardButton("5", callback_data="qty_select_5"))
        if max_qty >= 10:
            row.append(InlineKeyboardButton("10", callback_data="qty_select_10"))
        if max_qty >= 25:
            row.append(InlineKeyboardButton("25", callback_data="qty_select_25"))
        if row:
            keyboard.append(row)
        keyboard.append(
            [InlineKeyboardButton(f"(الحد الأقصى لرصيدك) {max_qty}", callback_data=f"qty_select_{max_qty}")]
        )
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")])

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def process_promo_qty_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("awaiting_promo_qty"):
        return False

    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return True

    ok_amt, qty, err = sanitize_amount(update.message.text.strip(), min_val=1, max_val=100_000)
    if not ok_amt:
        await update.message.reply_text(err)
        return True

    await process_qty_input(update, context, qty)
    return True


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

    context.user_data.pop("awaiting_promo_qty", None)
    context.user_data["task_qty"] = qty
    return await prompt_payment_method(update, context)


async def prompt_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    qty = context.user_data.get("task_qty", 3)
    price = context.user_data.get("unit_price", 750)

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        fee_rate = _get_effective_promo_fee(user)

    base_cost = qty * price
    total_gram = math.ceil(base_cost * (1.0 + fee_rate))
    context.user_data["total_gram"] = total_gram
    context.user_data["promo_fee_rate"] = fee_rate

    fee_pct = round(fee_rate * 100, 1)
    text = (
        f"💳 <b>اختر طريقة الدفع لمهمتك:</b>\n\n"
        f"• التكلفة الصافية: <code>{base_cost:,}</code> غرام\n"
        f"• العمولة المطبقة ({fee_pct}%): <code>{total_gram - base_cost:,}</code> غرام\n"
        f"• <b>الإجمالي:</b> <code>{total_gram:,}</code> غرام\n\n"
        f"💡 يمكنك التبرع بـ <b>{STARS_FEE_FREE_COST} ⭐</b> لإلغاء العمولة نهائياً لمدة 24 ساعة!"
    )

    keyboard = [
        [InlineKeyboardButton(f"💎 دفع {total_gram:,} GRAM", callback_data="pay_method_gram")],
    ]
    if fee_rate > 0:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🌟 دفع {STARS_FEE_FREE_COST} Telegram Stars (إعفاء عمولة 24س)",
                    callback_data="pay_method_stars",
                )
            ]
        )
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")])

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def handle_stars_fee_free_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    try:
        await context.bot.send_invoice(
            chat_id=user_id,
            title="إعفاء عمولة الترويج 24 ساعة",
            description="إلغاء كامل عمولة إنشاء الحملات الترويجية لمدة 24 ساعة في ZetaGram.",
            payload=f"stars_feefree_{user_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("إعفاء 24 ساعة", STARS_FEE_FREE_COST)],
        )
    except Exception:
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ الدفع عبر Telegram Stars غير مفعل حالياً، يمكنك الدفع برصيد GRAM مباشرة.",
        )


async def handle_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    if not payment or not payment.invoice_payload.startswith("stars_feefree_"):
        return

    user_id = update.effective_user.id
    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if user:
                user.fee_free_until = utcnow() + timedelta(hours=24)
                await session.commit()

    qty = context.user_data.get("task_qty", 3)
    price = context.user_data.get("unit_price", 750)
    context.user_data["total_gram"] = qty * price
    context.user_data["promo_fee_rate"] = 0.0

    await update.message.reply_text(
        "🌟 <b>تم تفعيل الإعفاء من العمولة لمدة 24 ساعة بنجاح!</b>\n"
        f"أصبحت تكلفة حملتك بدون عمولة: <code>{qty * price:,}</code> غرام.",
        parse_mode="HTML",
    )
    await prompt_target_chat_picker(update, context)


async def prompt_target_chat_picker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    if query:
        await query.answer()

    cat = context.user_data.get("promo_category", "channel")
    context.user_data["awaiting_promo_target"] = True

    if cat in ("channel", "group"):
        is_ch = cat == "channel"
        kind_ar = "القناة" if is_ch else "المجموعة"
        text = (
            f"📌 <b>تحديد {kind_ar} المستهدفة:</b>\n\n"
            f"⚠️ <b>يجب أن يكون البوت مشرفاً في {kind_ar} للتحقق من اشتراكات الأعضاء.</b>\n\n"
            f"1️⃣ اضغط زر «📣 اختيار {kind_ar}» أدناه لاختيارها فوراً.\n"
            f"2️⃣ أو أرسل بياناتها يدوياً بالصيغة:\n"
            f"<code>@username_أو_الرابط | اسم الحملة</code>\n"
            f"مثال: <code>@MyChannel | قناتي التقنية</code>"
        )
        req_kb = ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton(
                        f"📣 اختيار {kind_ar}",
                        request_chat=KeyboardButtonRequestChat(
                            request_id=1, chat_is_channel=is_ch
                        ),
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        if query:
            await context.bot.send_message(
                chat_id=update.effective_user.id, text=text, parse_mode="HTML", reply_markup=req_kb
            )
        else:
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=req_kb)
    else:
        extra_hint = ""
        if cat.startswith("bot_"):
            extra_hint = " | @BotUsername"
        elif cat == "reaction_fixed":
            extra_hint = " | 👍"

        text = (
            f"🔗 <b>أدخل رابط المهمة وعنوانها:</b>\n\n"
            f"أرسل البيانات مفصولة بـ <code>|</code> بالصيغة التالية:\n"
            f"<code>الرابط | عنوان المهمة{extra_hint}</code>\n\n"
            f"مثال:\n<code>https://t.me/my_target/15 | دعم منشور مهم{extra_hint}</code>"
        )
        kb = [[InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")]]
        if query:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def handle_chat_shared_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_promo_target"):
        return

    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    shared = update.message.chat_shared
    if not shared:
        return

    chat_id = shared.chat_id
    is_admin, status = await check_bot_is_admin(context.bot, chat_id)
    if not is_admin:
        await update.message.reply_text(
            f"❌ <b>البوت ليس مشرفاً في هذه المحادثة!</b> (الحالة: <code>{esc(status)}</code>)\n"
            f"يرجى رفع البوت كمشرف أولاً ثم اختيار المحادثة مجدداً.",
            parse_mode="HTML",
        )
        return

    title = f"محادثة {chat_id}"
    target_url = ""
    chat_ref = str(chat_id)
    try:
        chat_obj = await context.bot.get_chat(chat_id)
        title = chat_obj.title or title
        if getattr(chat_obj, "username", None):
            chat_ref = f"@{chat_obj.username}"
            target_url = f"https://t.me/{chat_obj.username}"
        elif getattr(chat_obj, "invite_link", None):
            target_url = chat_obj.invite_link
        else:
            link = await context.bot.export_chat_invite_link(chat_id)
            target_url = link
    except Exception:
        pass

    if not target_url:
        await update.message.reply_text(
            "⚠️ تعذر جلب رابط دعوة للمحادثة تلقائياً. يرجى إرسال الرابط والاسم يدوياً: <code>الرابط | الاسم</code>",
            parse_mode="HTML",
        )
        return

    context.user_data["promo_target_url"] = target_url
    context.user_data["promo_chat_id"] = chat_ref
    context.user_data["promo_title"] = title[:120]
    context.user_data["promo_extra"] = ""
    context.user_data.pop("awaiting_promo_target", None)

    await update.message.reply_text("✅ تم التحقق من المحادثة بنجاح!", reply_markup=ReplyKeyboardRemove())
    await show_promo_confirmation(update, context)


async def process_promo_target_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("awaiting_promo_target"):
        return False

    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return True

    raw = update.message.text.strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        await update.message.reply_text(
            "⚠️ يرجى الإدخال بالصيغة الصحيحة مفصولة بـ <code>|</code>:\n"
            "<code>@username_أو_الرابط | عنوان المهمة</code>",
            parse_mode="HTML",
        )
        return True

    target_in = parts[0]
    title = parts[1][:120]
    extra = parts[2][:60] if len(parts) > 2 else ""

    cat = context.user_data.get("promo_category", "channel")
    chat_id = None
    if target_in.startswith("@"):
        chat_id = target_in
        target_url = f"https://t.me/{target_in.lstrip('@')}"
    elif target_in.startswith("http://") or target_in.startswith("https://"):
        target_url = target_in
        if "t.me/" in target_in:
            slug = target_in.split("t.me/", 1)[1].split("/", 1)[0].split("?", 1)[0]
            if slug and not slug.startswith("+") and slug != "c":
                chat_id = f"@{slug}"
    else:
        await update.message.reply_text("❌ يرجى إدخال رابط يبدأ بـ https:// أو معرف يبدأ بـ @.")
        return True

    if cat in ("channel", "group"):
        if not chat_id:
            await update.message.reply_text("❌ يجب استخدام معرف عام (@username) أو زر اختيار القناة للتحقق.")
            return True
        is_admin, status = await check_bot_is_admin(context.bot, chat_id)
        if not is_admin:
            await update.message.reply_text(
                f"❌ <b>البوت ليس مشرفاً في {esc(chat_id)}!</b> ({esc(status)})\n"
                f"ارفع البوت كمشرف أولاً ثم أعد المحاولة.",
                parse_mode="HTML",
            )
            return True

    context.user_data["promo_target_url"] = target_url
    context.user_data["promo_chat_id"] = chat_id
    context.user_data["promo_title"] = title
    context.user_data["promo_extra"] = extra
    context.user_data.pop("awaiting_promo_target", None)

    await show_promo_confirmation(update, context)
    return True


async def show_promo_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = context.user_data.get("promo_category", "channel")
    qty = context.user_data.get("task_qty", 3)
    price = context.user_data.get("unit_price", 750)
    total_gram = context.user_data.get("total_gram", qty * price)
    title = context.user_data.get("promo_title", "")
    url = context.user_data.get("promo_target_url", "")
    langs = context.user_data.get("promo_langs", [])

    text = (
        f"📋 <b>مراجعة وتأكيد الحملة الترويجية:</b>\n\n"
        f"📌 <b>العنوان:</b> {esc(title)}\n"
        f"📂 <b>الفئة:</b> <code>{esc(cat)}</code>\n"
        f"🔗 <b>الرابط:</b> {esc(url)}\n"
        f"👥 <b>العدد المطلوب:</b> <code>{qty:,}</code>\n"
        f"💵 <b>مكافأة المنفذ:</b> <code>{price:,}</code> غرام\n"
        f"🌍 <b>الجمهور:</b> {esc(', '.join(langs) if langs else 'الجميع')}\n"
        f"💳 <b>التكلفة الإجمالية المخصومة:</b> <code>{total_gram:,}</code> غرام (محفوظة بالضمان المالي Escrow)"
    )
    keyboard = [
        [InlineKeyboardButton("✅ تأكيد وإنشاء الحملة الآن", callback_data="promo_confirm_create")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="promo_back_main")],
    ]
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True
    )


async def promo_confirm_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id

    cat = context.user_data.get("promo_category")
    qty = context.user_data.get("task_qty")
    price = context.user_data.get("unit_price")
    url = context.user_data.get("promo_target_url")
    chat_id = context.user_data.get("promo_chat_id")
    title = context.user_data.get("promo_title")
    extra = context.user_data.get("promo_extra", "")
    langs = context.user_data.get("promo_langs", [])
    acc_type = context.user_data.get("promo_acc_type", "all")

    if not cat or not qty or not price or not url or not title:
        await query.answer("❌ انتهت بيانات الحملة، يرجى البدء من جديد.", show_alert=True)
        return

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not user:
                await query.answer("❌ خطأ في الحساب.", show_alert=True)
                return

            fee_rate = _get_effective_promo_fee(user)
            escrow = qty * price
            total_cost = math.ceil(escrow * (1.0 + fee_rate))
            commission = total_cost - escrow

            if user.balance < total_cost:
                await query.answer("❌ رصيدك غير كافٍ الآن!", show_alert=True)
                return

            user.balance -= total_cost
            new_task = Task(
                title=title,
                task_type=cat,
                target_url=url,
                chat_id=chat_id,
                reward_grams=price,
                total_qty=qty,
                completed_qty=0,
                status="active",
                created_by=user_id,
                target_languages=",".join(langs) if langs else None,
                requires_premium=(acc_type == "premium"),
                escrow_balance=escrow,
                commission_paid=commission,
                bot_username=extra if cat.startswith("bot_") and extra else None,
                required_emoji=extra if cat == "reaction_fixed" and extra else None,
            )
            session.add(new_task)
            session.add(
                Transaction(
                    user_id=user_id,
                    trans_type="spend_promo",
                    amount=-total_cost,
                    description=f"إنشاء حملة ترويجية: {title} ({qty} × {price})",
                )
            )
            await session.commit()
            task_id = new_task.id

    for k in [
        "promo_category", "promo_acc_type", "promo_langs", "min_price",
        "unit_price", "max_qty", "task_qty", "total_gram", "promo_fee_rate",
        "promo_target_url", "promo_chat_id", "promo_title", "promo_extra",
    ]:
        context.user_data.pop(k, None)

    await query.answer("🎉 تم إطلاق حملتك الترويجية بنجاح!", show_alert=True)
    await query.edit_message_text(
        f"🚀 <b>تم إطلاق الحملة (#{task_id}) بنجاح!</b>\n\n"
        f"📌 <b>العنوان:</b> {esc(title)}\n"
        f"🛡️ <b>الضمان المالي (Escrow):</b> <code>{escrow:,}</code> غرام\n\n"
        f"يمكنك متابعتها وإدارتها في أي وقت من قسم «💼 مهامي وإدارتها».",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("💼 عرض حملاتي", callback_data="promo_my_tasks")]]
        ),
    )


async def show_promo_auto_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()

    perks = get_vip_perks(user.vip_level if user else 1)
    vip_fee = round(perks["promo_fee"] * 100, 1)
    now = utcnow()
    if user and user.fee_free_until and now < user.fee_free_until:
        stars_status = f"🟢 مفعل حتى <code>{user.fee_free_until.strftime('%Y-%m-%d %H:%M UTC')}</code> (عمولة 0%)"
    else:
        stars_status = "⚪ غير مفعل حالياً"

    text = (
        f"⚙️ <b>إعدادات الترويج والعمولة:</b>\n\n"
        f"🏅 <b>مستواك:</b> {esc(perks['title'])}\n"
        f"📉 <b>عمولة الترويج لمستواك:</b> <code>{vip_fee}%</code>\n"
        f"🌟 <b>إعفاء العمولة عبر Telegram Stars:</b> {stars_status}\n\n"
        f"🛡️ <b>نظام الضمان المالي (Escrow):</b>\n"
        f"• يتم حجز أجر المنفذين كاملاً داخل الحملة ولا يُصرف إلا بعد التحقق.\n"
        f"• عند إلغاء أي حملة يُردّ الرصيد المتبقي في الضمان لحسابك فوراً."
    )
    kb = [[InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def show_my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    async with AsyncSessionLocal() as session:
        user_tasks = (
            await session.execute(
                select(Task)
                .where(Task.created_by == user_id)
                .order_by(Task.created_at.desc())
                .limit(10)
            )
        ).scalars().all()

    keyboard = []
    if not user_tasks:
        text = "💼 <b>مهامي:</b>\n\nليس لديك أي حملات ترويجية قائمة حالياً."
    else:
        text = "💼 <b>قائمة حملاتك الترويجية (اضغط لإدارة الحملة):</b>\n\n"
        for t in user_tasks:
            icon = {"active": "🟢", "paused": "⏸️", "completed": "✅", "cancelled": "🗑️"}.get(t.status, "🔹")
            text += f"{icon} <b>{esc(t.title)}</b> ({t.completed_qty}/{t.total_qty}) — {t.reward_grams:,} غرام\n"
            keyboard.append(
                [InlineKeyboardButton(f"{icon} إدارة: {t.title[:28]}", callback_data=f"mytask_view_{t.id}")]
            )

    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="promo_back_main")])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def mytask_view_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: int | None = None
):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    if task_id is None:
        task_id = int(query.data.rsplit("_", 1)[-1])
    await query.answer()

    async with AsyncSessionLocal() as session:
        t = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()

    if not t or t.created_by != user_id:
        await query.answer("❌ الحملة غير موجودة.", show_alert=True)
        return

    remaining = max(0, t.total_qty - t.completed_qty)
    text = (
        f"💼 <b>إدارة الحملة #{t.id}:</b> {esc(t.title)}\n\n"
        f"📊 <b>التقدم:</b> <code>{t.completed_qty}/{t.total_qty}</code> (متبقي: {remaining})\n"
        f"💵 <b>السعر للوحدة:</b> <code>{t.reward_grams:,}</code> غرام\n"
        f"🛡️ <b>الضمان المتبقي (Escrow):</b> <code>{t.escrow_balance or 0:,}</code> غرام\n"
        f"📌 <b>الحالة:</b> <code>{esc(t.status)}</code>"
    )
    keyboard = []
    if t.status in ("active", "paused"):
        toggle_label = "⏸️ إيقاف مؤقت" if t.status == "active" else "▶️ استئناف الحملة"
        keyboard.append([InlineKeyboardButton(toggle_label, callback_data=f"mytask_toggle_{t.id}")])
        if remaining > 0:
            boost_cost = remaining * 100
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🚀 رفع السعر +100 غرام (بتكلفة {boost_cost:,})",
                        callback_data=f"mytask_boost_{t.id}",
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton("🗑️ إلغاء الحملة واسترداد المتبقي", callback_data=f"mytask_cancel_{t.id}")]
        )
    keyboard.append([InlineKeyboardButton("🔙 رجوع لحملاتي", callback_data="promo_my_tasks")])

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def mytask_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    parts = query.data.split("_")
    action = parts[1]
    task_id = int(parts[2])

    async with user_lock_manager.acquire_ordered_locks(("user", user_id), ("task", task_id)):
        async with AsyncSessionLocal() as session:
            t = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not t or t.created_by != user_id or not user:
                await query.answer("❌ الحملة غير موجودة.", show_alert=True)
                return

            if action == "toggle":
                if t.status not in ("active", "paused"):
                    await query.answer("⚠️ لا يمكن تغيير حالة حملة منتهية أو ملغاة.", show_alert=True)
                    return
                t.status = "paused" if t.status == "active" else "active"
                await session.commit()
                await query.answer(f"✅ تم تغيير الحالة إلى {t.status}", show_alert=True)

            elif action == "boost":
                remaining = max(0, t.total_qty - t.completed_qty)
                if t.status not in ("active", "paused") or remaining <= 0:
                    await query.answer("⚠️ الحملة غير نشطة أو مكتملة.", show_alert=True)
                    return
                extra_cost = remaining * 100
                if user.balance < extra_cost:
                    await query.answer(
                        f"❌ رصيدك غير كافٍ! المطلوب {extra_cost:,} غرام.", show_alert=True
                    )
                    return
                user.balance -= extra_cost
                t.reward_grams += 100
                t.escrow_balance = (t.escrow_balance or 0) + extra_cost
                session.add(
                    Transaction(
                        user_id=user_id,
                        trans_type="spend_promo",
                        amount=-extra_cost,
                        description=f"رفع سعر الحملة #{t.id} (+100 غرام للمتبقي {remaining})",
                    )
                )
                await session.commit()
                await query.answer("🚀 تم رفع سعر المهمة بنجاح!", show_alert=True)

            elif action == "cancel":
                if t.status in ("completed", "cancelled"):
                    await query.answer("⚠️ الحملة مكتملة أو ملغاة بالفعل.", show_alert=True)
                    return
                refund = max(0, t.escrow_balance or 0)
                t.escrow_balance = 0
                t.status = "cancelled"
                if refund > 0:
                    user.balance += refund
                    session.add(
                        Transaction(
                            user_id=user_id,
                            trans_type="promo_refund",
                            amount=refund,
                            description=f"استرداد ضمان إلغاء الحملة #{t.id} ({t.title})",
                        )
                    )
                await session.commit()
                await query.answer(
                    f"✅ تم إلغاء الحملة واسترداد +{refund:,} غرام لرصيدك!", show_alert=True
                )

    await mytask_view_callback(update, context, task_id=task_id)
