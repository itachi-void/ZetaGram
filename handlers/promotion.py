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
from sqlalchemy import select, update as sa_update, and_

from config import STARS_FEE_FREE_COST
from database.db import AsyncSessionLocal
from database.models import User, Task, Transaction, PromoCode, PromoCodeRedemption
from utils.security import user_lock_manager, sanitize_amount, get_vip_perks
from utils.gatekeeper import enforce_user_access
from utils.telegram_api import check_bot_is_admin, parse_telegram_post_link
from utils.promotions import validate_promo_code, calculate_campaign_pricing
from utils.i18n import get_text, get_user_lang, get_vip_title
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

    lang = get_user_lang(user)
    balance = user.balance if user else 0
    fee_pct = round(_get_effective_promo_fee(user) * 100, 1)

    text = get_text(lang, "promo_menu", balance=balance, fee_pct=fee_pct)

    keyboard = [
        [
            InlineKeyboardButton(get_text(lang, "promo_btn_group"), callback_data="promo_cat_group"),
            InlineKeyboardButton(get_text(lang, "promo_btn_channel"), callback_data="promo_cat_channel"),
        ],
        [
            InlineKeyboardButton(get_text(lang, "promo_btn_bot"), callback_data="promo_cat_bot"),
            InlineKeyboardButton(get_text(lang, "promo_btn_post"), callback_data="promo_cat_post"),
        ],
        [
            InlineKeyboardButton(get_text(lang, "promo_btn_reactions"), callback_data="promo_cat_reactions"),
            InlineKeyboardButton(get_text(lang, "promo_btn_premium"), callback_data="promo_cat_premium"),
        ],
        [InlineKeyboardButton(get_text(lang, "promo_btn_settings"), callback_data="promo_auto_settings")],
        [
            InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu"),
            InlineKeyboardButton(get_text(lang, "promo_btn_my_tasks"), callback_data="promo_my_tasks"),
        ],
    ]

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def promo_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    category = query.data.replace("promo_cat_", "")

    if category == "bot":
        kb = [
            [InlineKeyboardButton(get_text(lang, "promo_btn_bot_normal"), callback_data="promo_sub_bot_normal")],
            [InlineKeyboardButton(get_text(lang, "promo_btn_bot_webapp"), callback_data="promo_sub_bot_webapp")],
            [InlineKeyboardButton(get_text(lang, "promo_btn_bot_conditions"), callback_data="promo_sub_bot_conditions")],
            [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")],
        ]
        await query.edit_message_text(
            get_text(lang, "promo_bot_type_prompt"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return

    if category == "reactions":
        kb = [
            [InlineKeyboardButton(get_text(lang, "promo_btn_reaction_random"), callback_data="promo_sub_reaction_random")],
            [InlineKeyboardButton(get_text(lang, "promo_btn_reaction_fixed"), callback_data="promo_sub_reaction_fixed")],
            [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")],
        ]
        await query.edit_message_text(
            get_text(lang, "promo_reaction_type_prompt"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return

    context.user_data["promo_category"] = category
    await _show_account_type_step(query, lang)


async def promo_subtype_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    subtype = query.data.replace("promo_sub_", "")
    context.user_data["promo_category"] = subtype
    await _show_account_type_step(query, lang)


async def _show_account_type_step(query, lang: str = "ar"):
    text = get_text(lang, "promo_account_type_prompt")
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "promo_btn_acc_all"), callback_data="account_type_all")],
        [InlineKeyboardButton(get_text(lang, "promo_btn_acc_premium"), callback_data="account_type_premium")],
        [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")],
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def promo_account_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    acc_type = query.data.replace("account_type_", "")
    context.user_data["promo_acc_type"] = acc_type
    context.user_data["min_price"] = 1400 if acc_type == "premium" else 750
    context.user_data["promo_langs"] = []
    context.user_data.pop("promo_applied_code", None)

    text = get_text(lang, "promo_audience_prompt")
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "promo_btn_audience_all"), callback_data="audience_all")],
        [InlineKeyboardButton(get_text(lang, "promo_btn_audience_custom"), callback_data="audience_custom")],
        [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")],
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def promo_audience_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    aud_choice = query.data

    if aud_choice == "audience_custom":
        return await show_language_grid(update, context, lang=lang)

    context.user_data["promo_langs"] = []
    return await prompt_price_input(update, context, lang=lang)


async def show_language_grid(
    update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str | None = None
):
    if lang is None:
        async with AsyncSessionLocal() as s:
            u = (
                await s.execute(select(User).where(User.telegram_id == update.effective_user.id))
            ).scalar_one_or_none()
            lang = get_user_lang(u)

    query = update.callback_query
    selected = set(context.user_data.get("promo_langs", []))
    selected_str = (
        ", ".join(sorted(selected)) if selected else get_text(lang, "promo_lang_unlimited")
    )

    text = get_text(lang, "promo_lang_grid_prompt", selected=esc(selected_str))

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

    keyboard.append(
        [InlineKeyboardButton(get_text(lang, "promo_btn_lang_done", count=len(selected)), callback_data="audience_done")]
    )
    keyboard.append([InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="audience_all")])

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def toggle_promo_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    lang_code = query.data.replace("lang_", "")
    selected = list(context.user_data.get("promo_langs", []))
    if lang_code in selected:
        selected.remove(lang_code)
    else:
        selected.append(lang_code)
    context.user_data["promo_langs"] = selected
    await show_language_grid(update, context, lang=lang)


async def audience_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    selected = context.user_data.get("promo_langs", [])
    base_min = 1400 if context.user_data.get("promo_acc_type") == "premium" else 750
    context.user_data["min_price"] = base_min + (100 if selected else 0)
    await prompt_price_input(update, context, lang=lang)


async def prompt_price_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = "ar"
):
    query = update.callback_query
    min_price = context.user_data.get("min_price", 750)
    context.user_data["awaiting_promo_price"] = True

    text = get_text(
        lang,
        "promo_price_prompt",
        min_price=min_price,
        fast_price=min_price + 500,
    )
    keyboard = [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")]]
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def process_promo_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("awaiting_promo_price"):
        return False

    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return True

    lang = get_user_lang(db_user)
    min_price = context.user_data.get("min_price", 750)
    ok_amt, price, err = sanitize_amount(
        update.message.text.strip(), min_val=min_price, max_val=1_000_000, lang=lang
    )
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
        lang = get_user_lang(user)
        balance = user.balance if user else 0
        fee_rate = _get_effective_promo_fee(user)

    context.user_data["promo_fee_rate"] = fee_rate
    cost_per_unit = price * (1.0 + fee_rate)
    max_qty = math.floor(balance / cost_per_unit) if cost_per_unit > 0 else 0
    context.user_data["max_qty"] = max_qty
    context.user_data["awaiting_promo_qty"] = True

    fee_pct = round(fee_rate * 100, 1)
    error_prefix = f"{esc(error_msg)}\n\n" if error_msg else ""
    text = get_text(
        lang,
        "promo_qty_prompt",
        error_prefix=error_prefix,
        fee_pct=fee_pct,
        price=price,
        balance=balance,
        max_qty=max_qty,
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
            [
                InlineKeyboardButton(
                    get_text(lang, "promo_btn_max_qty", max_qty=max_qty),
                    callback_data=f"qty_select_{max_qty}",
                )
            ]
        )
    keyboard.append([InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")])

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def process_promo_qty_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("awaiting_promo_qty"):
        return False

    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return True

    lang = get_user_lang(db_user)
    ok_amt, qty, err = sanitize_amount(
        update.message.text.strip(), min_val=1, max_val=100_000, lang=lang
    )
    if not ok_amt:
        await update.message.reply_text(err)
        return True

    await process_qty_input(update, context, qty)
    return True


async def process_qty_input(update: Update, context: ContextTypes.DEFAULT_TYPE, qty: int):
    min_qty = 3
    max_qty = context.user_data.get("max_qty", 0)
    price = context.user_data.get("unit_price", 750)

    async with AsyncSessionLocal() as s:
        u = (
            await s.execute(select(User).where(User.telegram_id == update.effective_user.id))
        ).scalar_one_or_none()
        lang = get_user_lang(u)

    if qty < min_qty:
        err = get_text(lang, "promo_err_min_qty")
        return await prompt_qty_input(update, context, price, error_msg=err)

    if qty > max_qty:
        err = get_text(lang, "promo_err_max_qty", qty=qty, max_qty=max_qty)
        return await prompt_qty_input(update, context, price, error_msg=err)

    context.user_data.pop("awaiting_promo_qty", None)
    context.user_data["task_qty"] = qty
    return await prompt_payment_method(update, context)


async def prompt_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    qty = context.user_data.get("task_qty", 3)
    price = context.user_data.get("unit_price", 750)
    base_cost = qty * price
    applied_code = context.user_data.get("promo_applied_code")

    promo_obj = None
    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        lang = get_user_lang(user)
        fee_rate = _get_effective_promo_fee(user)
        if applied_code:
            ok_p, p_candidate, _ = await validate_promo_code(session, user_id, applied_code, base_cost)
            if ok_p and p_candidate:
                promo_obj = p_candidate
            else:
                context.user_data.pop("promo_applied_code", None)
                applied_code = None

    pricing = calculate_campaign_pricing(base_cost, fee_rate, promo_obj)
    total_gram = pricing["final_total"]
    context.user_data["total_gram"] = total_gram
    context.user_data["promo_fee_rate"] = fee_rate

    fee_pct = round(fee_rate * 100, 1)
    discount_line = ""
    if promo_obj and pricing["discount"] > 0:
        discount_line = get_text(
            lang,
            "promo_payment_discount_line",
            code=esc(promo_obj.code),
            discount=pricing["discount"],
        )

    text = get_text(
        lang,
        "promo_payment_method",
        base_cost=base_cost,
        fee_pct=fee_pct,
        commission=pricing["original_commission"],
        discount_line=discount_line,
        total_gram=total_gram,
        stars_cost=STARS_FEE_FREE_COST,
    )

    keyboard = [
        [InlineKeyboardButton(get_text(lang, "promo_btn_pay_gram", total_gram=total_gram), callback_data="pay_method_gram")],
    ]
    if applied_code and promo_obj:
        keyboard.append(
            [InlineKeyboardButton(get_text(lang, "promo_btn_clear_code", code=applied_code), callback_data="promo_clear_code")]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton(get_text(lang, "promo_btn_enter_code"), callback_data="promo_enter_code")]
        )
    if fee_rate > 0:
        keyboard.append(
            [
                InlineKeyboardButton(
                    get_text(lang, "promo_btn_pay_stars", stars_cost=STARS_FEE_FREE_COST),
                    callback_data="pay_method_stars",
                )
            ]
        )
    keyboard.append([InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")])

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def prompt_promo_code_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_promo_code"] = True
    await query.edit_message_text(
        get_text(lang, "promo_code_prompt"),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")]]
        ),
    )


async def clear_promo_code_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    context.user_data.pop("promo_applied_code", None)
    await update.callback_query.answer(get_text(lang, "promo_code_cleared"), show_alert=True)
    await prompt_payment_method(update, context)


async def process_promo_code_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("awaiting_promo_code"):
        return False

    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return True

    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    code_raw = update.message.text.strip().upper()
    context.user_data.pop("awaiting_promo_code", None)

    qty = context.user_data.get("task_qty", 3)
    price = context.user_data.get("unit_price", 750)
    base_cost = qty * price

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        fee_rate = _get_effective_promo_fee(user)
        ok_p, promo, err_key = await validate_promo_code(session, user_id, code_raw, base_cost)

    if not ok_p or not promo:
        if err_key == "promo_err_min_order" and promo:
            msg = get_text(lang, err_key, min_order=promo.min_order_grams or 0)
        else:
            msg = get_text(lang, err_key or "promo_err_invalid")
        await update.message.reply_text(msg, parse_mode="HTML")
        await prompt_payment_method(update, context)
        return True

    pricing = calculate_campaign_pricing(base_cost, fee_rate, promo)
    context.user_data["promo_applied_code"] = promo.code
    await update.message.reply_text(
        get_text(lang, "promo_code_applied", code=esc(promo.code), discount=pricing["discount"]),
        parse_mode="HTML",
    )
    await prompt_payment_method(update, context)
    return True


async def handle_stars_fee_free_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    try:
        await context.bot.send_invoice(
            chat_id=user_id,
            title=get_text(lang, "promo_stars_title"),
            description=get_text(lang, "promo_stars_desc"),
            payload=f"stars_feefree_{user_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(get_text(lang, "promo_stars_title"), STARS_FEE_FREE_COST)],
        )
    except Exception:
        await context.bot.send_message(
            chat_id=user_id,
            text=get_text(lang, "promo_stars_unavailable"),
        )


async def handle_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    if not payment or not payment.invoice_payload.startswith("stars_feefree_"):
        return

    user_id = update.effective_user.id
    lang = "ar"
    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if user:
                lang = get_user_lang(user)
                user.fee_free_until = utcnow() + timedelta(hours=24)
                await session.commit()

    qty = context.user_data.get("task_qty", 3)
    price = context.user_data.get("unit_price", 750)
    context.user_data["total_gram"] = qty * price
    context.user_data["promo_fee_rate"] = 0.0

    await update.message.reply_text(
        get_text(lang, "promo_stars_activated", total=qty * price),
        parse_mode="HTML",
    )
    await prompt_target_chat_picker(update, context)


async def prompt_target_chat_picker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    if query:
        await query.answer()

    cat = context.user_data.get("promo_category", "channel")
    context.user_data["awaiting_promo_target"] = True

    if cat in ("channel", "group"):
        is_ch = cat == "channel"
        kind_label = get_text(lang, "promo_kind_channel" if is_ch else "promo_kind_group")
        text = get_text(lang, "promo_target_chat_prompt", kind=kind_label)
        req_kb = ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton(
                        get_text(lang, "promo_btn_pick_chat", kind=kind_label),
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

        text = get_text(lang, "promo_target_url_prompt", extra_hint=extra_hint)
        kb = [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")]]
        if query:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def handle_chat_shared_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_promo_target"):
        return

    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    shared = update.message.chat_shared
    if not shared:
        return

    chat_id = shared.chat_id
    is_admin, status = await check_bot_is_admin(context.bot, chat_id)
    if not is_admin:
        await update.message.reply_text(
            get_text(lang, "promo_err_bot_not_admin", status=esc(status)),
            parse_mode="HTML",
        )
        return

    title = f"Chat {chat_id}"
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
            get_text(lang, "promo_err_invite_fetch"),
            parse_mode="HTML",
        )
        return

    context.user_data["promo_target_url"] = target_url
    context.user_data["promo_chat_id"] = chat_ref
    context.user_data["promo_title"] = title[:120]
    context.user_data["promo_extra"] = ""
    context.user_data["promo_message_id"] = None
    context.user_data["promo_auto_verify_reactions"] = False
    context.user_data.pop("awaiting_promo_target", None)

    await update.message.reply_text(get_text(lang, "promo_chat_verified"), reply_markup=ReplyKeyboardRemove())
    await show_promo_confirmation(update, context, lang=lang)


async def process_promo_target_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("awaiting_promo_target"):
        return False

    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return True

    lang = get_user_lang(db_user)
    raw = update.message.text.strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        await update.message.reply_text(
            get_text(lang, "promo_err_target_format"),
            parse_mode="HTML",
        )
        return True

    target_in = parts[0]
    title = parts[1][:120]
    extra = parts[2][:60] if len(parts) > 2 else ""

    cat = context.user_data.get("promo_category", "channel")
    chat_id = None
    msg_id = None
    auto_verify_reactions = False

    if target_in.startswith("@"):
        chat_id = target_in
        target_url = f"https://t.me/{target_in.lstrip('@')}"
    elif target_in.startswith("http://") or target_in.startswith("https://"):
        target_url = target_in
        if "t.me/" in target_in or "telegram.me/" in target_in:
            parsed_chat, parsed_msg = parse_telegram_post_link(target_url)
            if parsed_chat:
                chat_id = parsed_chat
                msg_id = parsed_msg
            elif "t.me/" in target_in:
                slug = target_in.split("t.me/", 1)[1].split("/", 1)[0].split("?", 1)[0]
                if slug and not slug.startswith("+") and slug != "c":
                    chat_id = f"@{slug}"
    else:
        await update.message.reply_text(get_text(lang, "promo_err_bad_url"))
        return True

    if cat in ("channel", "group"):
        if not chat_id:
            await update.message.reply_text(get_text(lang, "promo_err_need_public_chat"))
            return True
        is_admin, status = await check_bot_is_admin(context.bot, chat_id)
        if not is_admin:
            await update.message.reply_text(
                get_text(lang, "promo_err_bot_not_admin", status=esc(status)),
                parse_mode="HTML",
            )
            return True
    elif cat in ("reaction_random", "reaction_fixed") and chat_id and msg_id:
        is_admin, _ = await check_bot_is_admin(context.bot, chat_id)
        if is_admin:
            try:
                chat_obj = await context.bot.get_chat(chat_id)
                if getattr(chat_obj, "id", None):
                    chat_id = str(chat_obj.id)
            except Exception:
                pass
            auto_verify_reactions = True

    context.user_data["promo_target_url"] = target_url
    context.user_data["promo_chat_id"] = chat_id
    context.user_data["promo_message_id"] = msg_id
    context.user_data["promo_auto_verify_reactions"] = auto_verify_reactions
    context.user_data["promo_title"] = title
    context.user_data["promo_extra"] = extra
    context.user_data.pop("awaiting_promo_target", None)

    await show_promo_confirmation(update, context, lang=lang)
    return True


async def show_promo_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = "ar"
):
    cat = context.user_data.get("promo_category", "channel")
    qty = context.user_data.get("task_qty", 3)
    price = context.user_data.get("unit_price", 750)
    total_gram = context.user_data.get("total_gram", qty * price)
    title = context.user_data.get("promo_title", "")
    url = context.user_data.get("promo_target_url", "")
    langs = context.user_data.get("promo_langs", [])
    auto_rx = bool(context.user_data.get("promo_auto_verify_reactions", False))

    rx_badge = ""
    if cat in ("reaction_random", "reaction_fixed"):
        rx_badge = get_text(
            lang, "promo_auto_rx_badge_on" if auto_rx else "promo_auto_rx_badge_off"
        )

    audience = esc(", ".join(langs)) if langs else get_text(lang, "promo_audience_all")
    text = get_text(
        lang,
        "promo_confirm_summary",
        title=esc(title),
        cat=esc(cat),
        url=esc(url),
        qty=qty,
        price=price,
        audience=audience,
        rx_badge=rx_badge,
        total_gram=total_gram,
    )
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "promo_btn_confirm_create"), callback_data="promo_confirm_create")],
        [InlineKeyboardButton(get_text(lang, "btn_cancel"), callback_data="promo_back_main")],
    ]
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True
    )


async def promo_confirm_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    user_id = update.effective_user.id

    cat = context.user_data.get("promo_category")
    qty = context.user_data.get("task_qty")
    price = context.user_data.get("unit_price")
    url = context.user_data.get("promo_target_url")
    chat_id = context.user_data.get("promo_chat_id")
    msg_id = context.user_data.get("promo_message_id")
    auto_rx = bool(context.user_data.get("promo_auto_verify_reactions", False))
    title = context.user_data.get("promo_title")
    extra = context.user_data.get("promo_extra", "")
    langs = context.user_data.get("promo_langs", [])
    acc_type = context.user_data.get("promo_acc_type", "all")
    applied_code = context.user_data.get("promo_applied_code")

    if not cat or not qty or not price or not url or not title:
        await query.answer(get_text(lang, "promo_err_expired_session"), show_alert=True)
        return

    locks = [("user", user_id)]
    if applied_code:
        locks.append(("promo", applied_code))

    async with user_lock_manager.acquire_ordered_locks(*locks):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not user:
                await query.answer(get_text(lang, "account_error"), show_alert=True)
                return

            lang = get_user_lang(user)
            fee_rate = _get_effective_promo_fee(user)
            escrow = qty * price

            promo_obj = None
            if applied_code:
                ok_p, p_cand, _ = await validate_promo_code(session, user_id, applied_code, escrow)
                if not ok_p or not p_cand:
                    context.user_data.pop("promo_applied_code", None)
                    await query.answer(get_text(lang, "promo_err_code_race"), show_alert=True)
                    return
                promo_obj = p_cand

            pricing = calculate_campaign_pricing(escrow, fee_rate, promo_obj)
            total_cost = pricing["final_total"]
            commission = pricing["commission_paid"]
            promo_subsidy = pricing["promo_subsidy"]

            if user.balance < total_cost:
                await query.answer(get_text(lang, "promo_err_insufficient"), show_alert=True)
                return

            if promo_obj:
                upd_promo = await session.execute(
                    sa_update(PromoCode)
                    .where(
                        and_(
                            PromoCode.id == promo_obj.id,
                            PromoCode.is_active == True,
                            PromoCode.used_count < PromoCode.max_uses,
                        )
                    )
                    .values(used_count=PromoCode.used_count + 1)
                )
                if upd_promo.rowcount != 1:
                    await session.rollback()
                    context.user_data.pop("promo_applied_code", None)
                    await query.answer(get_text(lang, "promo_err_code_race"), show_alert=True)
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
                target_message_id=msg_id,
                auto_verify_reactions=auto_rx,
                promo_code_used=promo_obj.code if promo_obj else None,
                promo_subsidy=promo_subsidy,
            )
            session.add(new_task)
            await session.flush()

            if promo_obj:
                session.add(
                    PromoCodeRedemption(
                        promo_code_id=promo_obj.id,
                        user_id=user_id,
                        task_id=new_task.id,
                        discount_grams=pricing["discount"],
                    )
                )

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
        "promo_target_url", "promo_chat_id", "promo_message_id",
        "promo_auto_verify_reactions", "promo_title", "promo_extra",
        "promo_applied_code", "awaiting_promo_code",
    ]:
        context.user_data.pop(k, None)

    await query.answer(get_text(lang, "promo_created_alert"), show_alert=True)
    await query.edit_message_text(
        get_text(lang, "promo_created_msg", task_id=task_id, title=esc(title), escrow=escrow),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(get_text(lang, "promo_btn_view_my"), callback_data="promo_my_tasks")]]
        ),
    )


async def show_promo_auto_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(user)
    query = update.callback_query
    await query.answer()

    vip_lvl = user.vip_level if user else 1
    perks = get_vip_perks(vip_lvl)
    level_title = get_vip_title(lang, vip_lvl)
    vip_fee = round(perks["promo_fee"] * 100, 1)
    now = utcnow()
    if user and user.fee_free_until and now < user.fee_free_until:
        stars_status = get_text(
            lang, "promo_stars_on", until=user.fee_free_until.strftime("%Y-%m-%d %H:%M")
        )
    else:
        stars_status = get_text(lang, "promo_stars_off")

    text = get_text(
        lang,
        "promo_settings_view",
        level_title=esc(level_title),
        vip_fee=vip_fee,
        stars_status=stars_status,
    )
    kb = [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


async def show_my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
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
        text = get_text(lang, "promo_my_empty")
    else:
        text = get_text(lang, "promo_my_header")
        for t in user_tasks:
            icon = {"active": "🟢", "paused": "⏸️", "completed": "✅", "cancelled": "🗑️"}.get(t.status, "🔹")
            text += f"{icon} <b>{esc(t.title)}</b> ({t.completed_qty}/{t.total_qty}) — {t.reward_grams:,}\n"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        get_text(lang, "promo_my_btn_manage", icon=icon, title=t.title[:28]),
                        callback_data=f"mytask_view_{t.id}",
                    )
                ]
            )

    keyboard.append([InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="promo_back_main")])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def mytask_view_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: int | None = None
):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    user_id = update.effective_user.id
    if task_id is None:
        task_id = int(query.data.rsplit("_", 1)[-1])
    await query.answer()

    async with AsyncSessionLocal() as session:
        t = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()

    if not t or t.created_by != user_id:
        await query.answer(get_text(lang, "promo_err_task_not_found"), show_alert=True)
        return

    remaining = max(0, t.total_qty - t.completed_qty)
    text = get_text(
        lang,
        "promo_task_view",
        task_id=t.id,
        title=esc(t.title),
        completed=t.completed_qty,
        total=t.total_qty,
        remaining=remaining,
        reward=t.reward_grams,
        escrow=t.escrow_balance or 0,
        status=esc(t.status),
    )
    keyboard = []
    if t.status in ("active", "paused"):
        toggle_label = get_text(
            lang, "promo_btn_pause" if t.status == "active" else "promo_btn_resume"
        )
        keyboard.append([InlineKeyboardButton(toggle_label, callback_data=f"mytask_toggle_{t.id}")])
        if remaining > 0:
            boost_cost = remaining * 100
            keyboard.append(
                [
                    InlineKeyboardButton(
                        get_text(lang, "promo_btn_boost", boost_cost=boost_cost),
                        callback_data=f"mytask_boost_{t.id}",
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton(get_text(lang, "promo_btn_cancel"), callback_data=f"mytask_cancel_{t.id}")]
        )
    keyboard.append([InlineKeyboardButton(get_text(lang, "promo_btn_back_my"), callback_data="promo_my_tasks")])

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def mytask_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
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
                await query.answer(get_text(lang, "promo_err_task_not_found"), show_alert=True)
                return

            lang = get_user_lang(user)

            if action == "toggle":
                if t.status not in ("active", "paused"):
                    await query.answer(get_text(lang, "promo_err_task_closed"), show_alert=True)
                    return
                t.status = "paused" if t.status == "active" else "active"
                await session.commit()
                await query.answer(get_text(lang, "promo_toggled_alert", status=t.status), show_alert=True)

            elif action == "boost":
                remaining = max(0, t.total_qty - t.completed_qty)
                if t.status not in ("active", "paused") or remaining <= 0:
                    await query.answer(get_text(lang, "promo_err_boost_closed"), show_alert=True)
                    return
                extra_cost = remaining * 100
                if user.balance < extra_cost:
                    await query.answer(
                        get_text(lang, "promo_err_boost_balance", extra_cost=extra_cost),
                        show_alert=True,
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
                await query.answer(get_text(lang, "promo_boosted_alert"), show_alert=True)

            elif action == "cancel":
                if t.status in ("completed", "cancelled"):
                    await query.answer(get_text(lang, "promo_err_already_closed"), show_alert=True)
                    return
                # Subtract any platform-subsidized promo discount to prevent cancel-refund arbitrage
                refund = max(0, (t.escrow_balance or 0) - (t.promo_subsidy or 0))
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
                    get_text(lang, "promo_cancelled_alert", refund=refund), show_alert=True
                )

    await mytask_view_callback(update, context, task_id=task_id)
