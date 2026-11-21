import random
import string
from datetime import timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, update as sa_update, func, and_
from sqlalchemy.exc import IntegrityError

from config import ADMIN_IDS, MIN_TASKS_FOR_TRANSFER
from database.db import AsyncSessionLocal
from database.models import User, UserTask, Voucher, VoucherRedemption, Transaction
from utils.security import user_lock_manager, sanitize_amount, send_security_alert
from utils.gatekeeper import enforce_user_access
from utils.i18n import get_text, get_user_lang
from utils.html_utils import esc, utcnow


def generate_voucher_code(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    rand_str = "".join(random.choices(chars, k=length))
    return f"GRAM-{rand_str[:4]}-{rand_str[4:]}"


async def show_vouchers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    if query:
        await query.answer()

    text = get_text(lang, "vouchers_menu")
    keyboard = [
        [
            InlineKeyboardButton(get_text(lang, "vouchers_btn_redeem"), callback_data="prompt_redeem_voucher"),
            InlineKeyboardButton(get_text(lang, "vouchers_btn_create"), callback_data="prompt_create_voucher"),
        ],
        [InlineKeyboardButton(get_text(lang, "vouchers_btn_my"), callback_data="my_created_vouchers")],
        [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def prompt_redeem_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_voucher_code"] = True
    await query.edit_message_text(get_text(lang, "voucher_prompt_redeem"), parse_mode="HTML")


async def prompt_create_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_create_voucher"] = True
    await query.edit_message_text(get_text(lang, "voucher_prompt_create"), parse_mode="HTML")


async def handle_create_voucher_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(get_text(lang, "voucher_cmd_usage"), parse_mode="HTML")
        return

    ok_amt, amount, err_amt = sanitize_amount(args[0], min_val=1, lang=lang)
    if not ok_amt:
        await update.message.reply_text(err_amt)
        return

    max_uses = 1
    if len(args) > 1:
        ok_u, max_uses, err_u = sanitize_amount(args[1], min_val=1, max_val=10_000, lang=lang)
        if not ok_u:
            await update.message.reply_text(err_u)
            return

    await create_and_send_voucher(update, context, amount, max_uses)


async def process_create_voucher_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return True

    lang = get_user_lang(db_user)
    text = update.message.text.strip()
    parts = text.split()

    if len(parts) < 1:
        await update.message.reply_text(get_text(lang, "voucher_err_enter_amount"))
        return True

    ok_amt, amount, err_amt = sanitize_amount(parts[0], min_val=1, lang=lang)
    if not ok_amt:
        await update.message.reply_text(err_amt)
        return True

    max_uses = 1
    if len(parts) > 1:
        ok_u, max_uses, err_u = sanitize_amount(parts[1], min_val=1, max_val=10_000, lang=lang)
        if not ok_u:
            await update.message.reply_text(err_u)
            return True

    context.user_data.pop("awaiting_create_voucher", None)
    await create_and_send_voucher(update, context, amount, max_uses)
    return True


async def create_and_send_voucher(
    update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int, max_uses: int
):
    user_id = update.effective_user.id
    lang = "ar"

    async with user_lock_manager.get_lock(f"u_{user_id}"):
        total_cost = amount * max_uses

        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not user:
                await update.message.reply_text(get_text(lang, "not_registered"))
                return

            lang = get_user_lang(user)

            if user_id not in ADMIN_IDS and (user.vip_level or 1) < 2:
                completed_cnt = (
                    await session.execute(
                        select(func.count(UserTask.id)).where(
                            and_(
                                UserTask.user_id == user_id,
                                UserTask.status.in_(["completed", "approved"]),
                            )
                        )
                    )
                ).scalar() or 0
                if completed_cnt < MIN_TASKS_FOR_TRANSFER:
                    await update.message.reply_text(
                        get_text(
                            lang,
                            "voucher_err_new_account",
                            min_tasks=MIN_TASKS_FOR_TRANSFER,
                            completed=completed_cnt,
                        ),
                        parse_mode="HTML",
                    )
                    return

            if user.balance < total_cost:
                await update.message.reply_text(
                    get_text(
                        lang,
                        "voucher_err_insufficient",
                        total_cost=total_cost,
                        amount=amount,
                        max_uses=max_uses,
                        balance=user.balance,
                    )
                )
                return

            user.balance -= total_cost
            code = generate_voucher_code()

            voucher = Voucher(
                code=code,
                amount=amount,
                max_uses=max_uses,
                used_count=0,
                created_by=user_id,
            )
            session.add(voucher)

            tx = Transaction(
                user_id=user_id,
                trans_type="voucher_create",
                amount=-total_cost,
                description=f"إنشاء شيك {code} بقيمة {amount} لـ {max_uses} مستخدمين",
            )
            session.add(tx)
            await session.commit()

    bot_info = await context.bot.get_me()
    v_link = f"https://t.me/{bot_info.username}?start=v_{code}"

    res_text = get_text(
        lang,
        "voucher_created",
        code=esc(code),
        amount=amount,
        max_uses=max_uses,
        total_cost=total_cost,
        v_link=esc(v_link),
    )
    await update.message.reply_text(res_text, parse_mode="HTML")


async def redeem_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    code = code.strip().upper()

    if code.startswith("V_"):
        code = code[2:]

    now = utcnow()
    reply_target = update.message or (update.callback_query.message if update.callback_query else None)

    async def _send(msg: str):
        if reply_target:
            await reply_target.reply_text(msg, parse_mode="HTML")
        else:
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode="HTML")

    async with user_lock_manager.acquire_ordered_locks(f"u_{user_id}", f"v_{code}"):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not user:
                return
            lang = get_user_lang(user)

            if user.voucher_banned_until and now < user.voucher_banned_until:
                rem = user.voucher_banned_until - now
                mins = max(1, int(rem.total_seconds() / 60) + 1)
                await _send(get_text(lang, "voucher_locked_bruteforce", mins=mins))
                return

            voucher = (
                await session.execute(select(Voucher).where(Voucher.code == code))
            ).scalar_one_or_none()

            if not voucher:
                user.failed_voucher_attempts = (user.failed_voucher_attempts or 0) + 1
                if user.failed_voucher_attempts >= 5:
                    user.voucher_banned_until = now + timedelta(minutes=15)
                    user.failed_voucher_attempts = 0
                    await session.commit()

                    await send_security_alert(
                        context.bot,
                        f"⚠️ <b>تخمين متكرر للشيكات (Anti-Bruteforce)!</b>\n"
                        f"👤 المستخدم: <code>{esc(user_id)}</code> قام بإدخال كود شيك خاطئ 5 مرات متتالية.\n"
                        f"🔒 تم قفل استبدال الشيكات له لمدة 15 دقيقة تلقائياً.",
                        alert_key=f"voucher_bf_{user_id}",
                    )
                    await _send(get_text(lang, "voucher_locked_now"))
                    return
                else:
                    await session.commit()
                    await _send(
                        get_text(lang, "voucher_invalid_attempt", attempts=user.failed_voucher_attempts)
                    )
                    return

            if voucher.used_count >= voucher.max_uses:
                await _send(get_text(lang, "voucher_exhausted"))
                return

            already_used = (
                await session.execute(
                    select(VoucherRedemption).where(
                        VoucherRedemption.voucher_id == voucher.id,
                        VoucherRedemption.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()

            if already_used:
                await _send(get_text(lang, "voucher_already_used"))
                return

            upd = await session.execute(
                sa_update(Voucher)
                .where(and_(Voucher.id == voucher.id, Voucher.used_count < Voucher.max_uses))
                .values(used_count=Voucher.used_count + 1)
            )
            if upd.rowcount != 1:
                await session.rollback()
                await _send(get_text(lang, "voucher_exhausted"))
                return

            user.failed_voucher_attempts = 0
            user.balance += voucher.amount

            session.add(VoucherRedemption(voucher_id=voucher.id, user_id=user_id))
            session.add(
                Transaction(
                    user_id=user_id,
                    trans_type="voucher_claim",
                    amount=voucher.amount,
                    description=f"استبدال شيك {code}",
                )
            )

            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                await _send(get_text(lang, "voucher_already_used"))
                return

            await _send(get_text(lang, "voucher_redeemed_success", amount=voucher.amount))


async def show_my_vouchers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        vouchers = (
            await session.execute(
                select(Voucher)
                .where(Voucher.created_by == user_id)
                .order_by(Voucher.created_at.desc())
                .limit(10)
            )
        ).scalars().all()

    keyboard = []
    if not vouchers:
        text = get_text(lang, "voucher_my_empty")
    else:
        text = get_text(lang, "voucher_my_header")
        for v in vouchers:
            rem = max(0, v.max_uses - v.used_count)
            status = (
                get_text(lang, "voucher_status_active", rem=rem, max_uses=v.max_uses)
                if rem > 0
                else get_text(lang, "voucher_status_done")
            )
            text += get_text(
                lang, "voucher_row", code=esc(v.code), amount=v.amount, status=status
            )
            if rem > 0:
                refund_est = rem * v.amount
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            get_text(lang, "voucher_btn_cancel", code=v.code, refund=refund_est),
                            callback_data=f"cancel_voucher_{v.id}",
                        )
                    ]
                )

    keyboard.append([InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="my_vouchers")])
    markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def cancel_voucher_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(db_user)
    query = update.callback_query
    user_id = update.effective_user.id
    v_id = int(query.data.replace("cancel_voucher_", ""))

    async with AsyncSessionLocal() as session:
        v_probe = (
            await session.execute(select(Voucher).where(Voucher.id == v_id))
        ).scalar_one_or_none()
        if not v_probe or v_probe.created_by != user_id:
            await query.answer(get_text(lang, "voucher_err_not_owner"), show_alert=True)
            return
        v_code = v_probe.code

    async with user_lock_manager.acquire_ordered_locks(f"u_{user_id}", f"v_{v_code}"):
        async with AsyncSessionLocal() as session:
            v = (await session.execute(select(Voucher).where(Voucher.id == v_id))).scalar_one_or_none()
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not v or v.created_by != user_id or not user:
                await query.answer(get_text(lang, "voucher_err_not_found"), show_alert=True)
                return

            lang = get_user_lang(user)
            rem = max(0, v.max_uses - v.used_count)
            if rem <= 0:
                await query.answer(get_text(lang, "voucher_err_already_done"), show_alert=True)
                return

            refund = rem * v.amount
            v.max_uses = v.used_count
            user.balance += refund
            session.add(
                Transaction(
                    user_id=user_id,
                    trans_type="voucher_refund",
                    amount=refund,
                    description=f"إلغاء شيك {v.code} واسترداد {rem} استخدام",
                )
            )
            await session.commit()

    await query.answer(get_text(lang, "voucher_cancelled_alert", refund=refund), show_alert=True)
    await show_my_vouchers(update, context)
