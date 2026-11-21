import time
from datetime import timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select

from config import (
    CAPTCHA_TTL_SECONDS,
    CAPTCHA_MAX_ATTEMPTS,
    CAPTCHA_LOCK_MINUTES,
    REFERRAL_JOIN_BONUS,
)
from database.db import AsyncSessionLocal
from database.models import User, Transaction
from utils.captcha import send_captcha_challenge
from utils.security import send_security_alert
from utils.i18n import get_text, LANGUAGES
from utils.html_utils import esc, utcnow
from handlers.vouchers import redeem_voucher


def get_main_keyboard(lang: str = "ar"):
    return ReplyKeyboardMarkup(
        [
            [get_text(lang, "btn_referrals"), get_text(lang, "btn_bonus")],
            [get_text(lang, "btn_earnings"), get_text(lang, "btn_promotion")],
            [get_text(lang, "btn_account"), get_text(lang, "btn_vouchers")],
            [get_text(lang, "btn_stats"), get_text(lang, "btn_check_sub")],
            [get_text(lang, "btn_instructions"), get_text(lang, "btn_useful_links")],
            [get_text(lang, "btn_language")],
        ],
        resize_keyboard=True,
    )


def build_language_keyboard():
    keyboard = []
    lang_items = list(LANGUAGES.items())

    for i in range(0, len(lang_items), 2):
        row = []
        code1, name1 = lang_items[i]
        row.append(InlineKeyboardButton(name1, callback_data=f"set_lang_{code1}"))
        if i + 1 < len(lang_items):
            code2, name2 = lang_items[i + 1]
            row.append(InlineKeyboardButton(name2, callback_data=f"set_lang_{code2}"))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    voucher_code = None
    referred_by = None

    if args and len(args) > 0:
        arg0 = args[0]
        if arg0.startswith("v_"):
            voucher_code = arg0[2:]
        elif arg0.isdigit():
            referred_by = int(arg0)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user.id))
        db_user = result.scalar_one_or_none()

        if not db_user:
            if referred_by == user.id:
                referred_by = None
            elif referred_by:
                ref_exists = (
                    await session.execute(
                        select(User.telegram_id).where(User.telegram_id == referred_by)
                    )
                ).scalar_one_or_none()
                if not ref_exists:
                    referred_by = None

            init_lang = (
                user.language_code[:2]
                if user.language_code and user.language_code[:2] in LANGUAGES
                else "ar"
            )
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                language=init_lang,
                referred_by=referred_by,
                is_captcha_verified=False,
            )
            session.add(db_user)
            await session.commit()

            text = get_text(init_lang, "select_lang_first")
            await update.message.reply_text(
                text, parse_mode="HTML", reply_markup=build_language_keyboard()
            )
            if voucher_code:
                context.user_data["pending_voucher_redeem"] = voucher_code
            return

        # Keep username / first_name fresh
        if db_user.username != user.username or db_user.first_name != user.first_name:
            db_user.username = user.username
            db_user.first_name = user.first_name
            await session.commit()

        lang = db_user.language or "ar"
        is_verified = bool(db_user.is_captcha_verified)

    if voucher_code and not is_verified:
        context.user_data["pending_voucher_redeem"] = voucher_code

    await start_command_after_language(update, context, lang)

    if voucher_code and is_verified:
        await redeem_voucher(update, context, voucher_code)


async def start_command_after_language(
    update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str
):
    user_id = update.effective_user.id
    first_name = esc(update.effective_user.first_name)

    async with AsyncSessionLocal() as session:
        db_user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()

        if db_user and not db_user.is_captcha_verified:
            await send_captcha_challenge(
                update, context, lang=lang, locked_until=db_user.captcha_locked_until
            )
            return

    welcome_text = get_text(lang, "welcome", name=first_name)

    if update.callback_query:
        await context.bot.send_message(
            chat_id=user_id,
            text=welcome_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=get_main_keyboard(lang),
        )
    else:
        await update.message.reply_text(
            welcome_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=get_main_keyboard(lang),
        )


async def handle_captcha_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        lang = user.language if (user and user.language) else "ar"
        locked_until = user.captcha_locked_until if user else None

    try:
        await query.delete_message()
    except Exception:
        pass
    await send_captcha_challenge(update, context, lang=lang, locked_until=locked_until)


async def handle_captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    selected_val = int(query.data.split("_")[-1])
    correct_ans = context.user_data.get("captcha_answer")
    expires_at = context.user_data.get("captcha_expires_at", 0.0)
    now = utcnow()

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        lang = user.language if (user and user.language) else "ar"

        if user and user.captcha_locked_until and now < user.captcha_locked_until:
            rem_secs = (user.captcha_locked_until - now).total_seconds()
            mins = max(1, int(rem_secs // 60) + 1)
            await query.answer("⛔ محاولات الكابتشا مقفلة مؤقتاً.", show_alert=True)
            await context.bot.send_message(
                chat_id=user_id,
                text=get_text(lang, "captcha_locked", mins=mins),
                parse_mode="HTML",
            )
            return

    if correct_ans is None or time.time() > float(expires_at or 0):
        await query.answer(get_text(lang, "captcha_expired"), show_alert=True)
        try:
            await query.delete_message()
        except Exception:
            pass
        await send_captcha_challenge(update, context, lang=lang)
        return

    if selected_val != correct_ans:
        locked_now = False
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if user:
                user.captcha_attempts = (user.captcha_attempts or 0) + 1
                if user.captcha_attempts >= CAPTCHA_MAX_ATTEMPTS:
                    user.captcha_locked_until = now + timedelta(minutes=CAPTCHA_LOCK_MINUTES)
                    user.captcha_attempts = 0
                    locked_now = True
                await session.commit()

        if locked_now:
            await query.answer("⛔ تم قفل الكابتشا مؤقتاً!", show_alert=True)
            try:
                await query.delete_message()
            except Exception:
                pass
            await send_security_alert(
                context.bot,
                f"⚠️ <b>فشل متكرر في اختبار الكابتشا (Anti-Bot)!</b>\n"
                f"👤 المستخدم: <code>{esc(user_id)}</code> أخطأ {CAPTCHA_MAX_ATTEMPTS} مرات متتالية.\n"
                f"🔒 تم قفل الكابتشا له لمدة {CAPTCHA_LOCK_MINUTES} دقائق.",
                alert_key=f"captcha_lock_{user_id}",
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=get_text(lang, "captcha_locked", mins=CAPTCHA_LOCK_MINUTES),
                parse_mode="HTML",
            )
            return

        await query.answer(get_text(lang, "captcha_wrong"), show_alert=True)
        try:
            await query.delete_message()
        except Exception:
            pass
        await send_captcha_challenge(update, context, lang=lang)
        return

    # Correct Captcha Answer!
    join_bonus_awarded = False
    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        if user:
            user.is_captcha_verified = True
            user.captcha_attempts = 0
            user.captcha_locked_until = None
            user.tasks_since_captcha = 0

            if user.referred_by and not user.join_bonus_paid:
                user.join_bonus_paid = True
                user.balance += REFERRAL_JOIN_BONUS
                session.add(
                    Transaction(
                        user_id=user_id,
                        trans_type="reward",
                        amount=REFERRAL_JOIN_BONUS,
                        description="مكافأة ترحيب للانضمام عبر رابط دعوة",
                    )
                )
                join_bonus_awarded = True

            await session.commit()

    context.user_data.pop("captcha_answer", None)
    context.user_data.pop("captcha_expires_at", None)

    await query.answer(get_text(lang, "captcha_success"), show_alert=True)
    try:
        await query.delete_message()
    except Exception:
        pass

    welcome_text = get_text(lang, "welcome", name=esc(update.effective_user.first_name))
    if join_bonus_awarded:
        welcome_text += (
            f"\n\n🎁 <b>هدية الدعوة:</b> تم إضافة <b>+{REFERRAL_JOIN_BONUS:,} غرام</b> إلى رصيدك فور التفعيل!"
        )

    await context.bot.send_message(
        chat_id=user_id,
        text=welcome_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=get_main_keyboard(lang),
    )

    pending_v = context.user_data.pop("pending_voucher_redeem", None)
    if pending_v:
        await redeem_voucher(update, context, pending_v)
