import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func, and_

from config import ADMIN_IDS, MIN_TRANSFER_AMOUNT, DAILY_TRANSFER_LIMIT, MIN_TASKS_FOR_TRANSFER
from database.db import AsyncSessionLocal
from database.models import User, UserTask, Transaction
from utils.security import (
    user_lock_manager,
    sanitize_amount,
    get_vip_perks,
    detect_suspicious_transfer,
)
from utils.gatekeeper import enforce_user_access
from utils.i18n import get_text, get_user_lang, get_vip_title
from utils.html_utils import esc, utcnow


async def show_transfer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(user)
    perks = get_vip_perks(user.vip_level if user else 1)
    level_title = get_vip_title(lang, user.vip_level if user else 1)
    fee_pct = round(perks["transfer_fee"] * 100, 1)

    text = get_text(
        lang,
        "transfer_menu",
        min_amt=MIN_TRANSFER_AMOUNT,
        daily_limit=DAILY_TRANSFER_LIMIT,
        level_title=esc(level_title),
        fee_pct=fee_pct,
    )
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "transfer_btn_start"), callback_data="prompt_transfer_id")],
        [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=markup
        )
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def prompt_transfer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(user)
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_transfer_input"] = True
    await query.edit_message_text(get_text(lang, "transfer_prompt"), parse_mode="HTML")


async def process_transfer_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("awaiting_transfer_input"):
        return False

    ok, user = await enforce_user_access(update, context)
    if not ok:
        return True

    lang = get_user_lang(user)
    parts = update.message.text.strip().split()
    if len(parts) < 2:
        await update.message.reply_text(get_text(lang, "transfer_prompt_err"), parse_mode="HTML")
        return True

    context.user_data.pop("awaiting_transfer_input", None)
    await execute_transfer(update, context, parts[0], parts[1])
    return True


async def handle_transfer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(update, context)
    if not ok:
        return

    lang = get_user_lang(user)
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(get_text(lang, "transfer_cmd_usage"), parse_mode="HTML")
        return

    await execute_transfer(update, context, args[0], args[1])


async def execute_transfer(
    update: Update, context: ContextTypes.DEFAULT_TYPE, target_raw: str, amount_raw: str
):
    user_id = update.effective_user.id
    lang = "ar"

    async with AsyncSessionLocal() as pre_s:
        pre_u = (
            await pre_s.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        if pre_u:
            lang = get_user_lang(pre_u)

    try:
        target_id = int(target_raw.strip())
    except ValueError:
        await update.message.reply_text(get_text(lang, "transfer_err_bad_id"))
        return

    if target_id == user_id:
        await update.message.reply_text(get_text(lang, "transfer_err_self"))
        return

    ok, amount, err = sanitize_amount(
        amount_raw, min_val=MIN_TRANSFER_AMOUNT, max_val=DAILY_TRANSFER_LIMIT, lang=lang
    )
    if not ok:
        await update.message.reply_text(err)
        return

    today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    receiver_lang = "ar"

    async with user_lock_manager.acquire_ordered_locks(user_id, target_id):
        async with AsyncSessionLocal() as session:
            sender = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            receiver = (
                await session.execute(select(User).where(User.telegram_id == target_id))
            ).scalar_one_or_none()

            if not sender:
                await update.message.reply_text(get_text(lang, "account_error"))
                return
            lang = get_user_lang(sender)
            if not receiver:
                await update.message.reply_text(get_text(lang, "transfer_err_target_not_found"))
                return
            receiver_lang = get_user_lang(receiver)

            if user_id not in ADMIN_IDS and (sender.vip_level or 1) < 2:
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
                            "transfer_err_new_account",
                            min_tasks=MIN_TASKS_FOR_TRANSFER,
                            completed=completed_cnt,
                        ),
                        parse_mode="HTML",
                    )
                    return

            sent_today = (
                await session.execute(
                    select(func.sum(-Transaction.amount)).where(
                        and_(
                            Transaction.user_id == user_id,
                            Transaction.trans_type == "transfer_send",
                            Transaction.created_at >= today_start,
                        )
                    )
                )
            ).scalar() or 0

            if sent_today + amount > DAILY_TRANSFER_LIMIT:
                rem_limit = max(0, DAILY_TRANSFER_LIMIT - sent_today)
                await update.message.reply_text(
                    get_text(
                        lang,
                        "transfer_err_daily_limit",
                        daily_limit=DAILY_TRANSFER_LIMIT,
                        rem_limit=rem_limit,
                    ),
                    parse_mode="HTML",
                )
                return

            perks = get_vip_perks(sender.vip_level)
            fee_rate = perks["transfer_fee"]
            fee = math.ceil(amount * fee_rate) if fee_rate > 0 else 0
            total_deduct = amount + fee

            if sender.balance < total_deduct:
                await update.message.reply_text(
                    get_text(
                        lang,
                        "transfer_err_insufficient",
                        amount=amount,
                        fee_pct=round(fee_rate * 100, 1),
                        fee=fee,
                        total_deduct=total_deduct,
                        balance=sender.balance,
                    )
                )
                return

            sender.balance -= total_deduct
            receiver.balance += amount

            session.add(
                Transaction(
                    user_id=user_id,
                    trans_type="transfer_send",
                    amount=-total_deduct,
                    description=f"إرسال رصيد إلى {target_id} (شامل عمولة {fee})",
                )
            )
            session.add(
                Transaction(
                    user_id=target_id,
                    trans_type="transfer_receive",
                    amount=amount,
                    description=f"استلام رصيد من {user_id}",
                )
            )
            await session.commit()
            sender_bal = sender.balance
            receiver_bal = receiver.balance

            await detect_suspicious_transfer(
                session, user_id, target_id, amount, context.bot
            )

    await update.message.reply_text(
        get_text(
            lang,
            "transfer_success_sender",
            target_id=target_id,
            amount=amount,
            fee=fee,
            sender_bal=sender_bal,
        ),
        parse_mode="HTML",
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=get_text(
                receiver_lang,
                "transfer_received_dm",
                sender_id=user_id,
                amount=amount,
                receiver_bal=receiver_bal,
            ),
            parse_mode="HTML",
        )
    except Exception:
        pass
