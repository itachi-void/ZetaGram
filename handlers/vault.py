from datetime import timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func, and_

from config import MAX_VAULT_DEPOSIT, MAX_ACTIVE_VAULT_DEPOSITS
from database.db import AsyncSessionLocal
from database.models import User, VaultDeposit, Transaction
from utils.security import user_lock_manager, sanitize_amount, get_vip_perks
from utils.gatekeeper import enforce_user_access
from utils.i18n import get_text, get_user_lang, get_vip_title
from utils.html_utils import esc, utcnow

PLAN_YIELDS = {
    7: 0.05,   # +5% base yield for 7 days
    30: 0.20,  # +20% base yield for 30 days
}


async def show_vault_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        if user:
            lang = get_user_lang(user)
        balance = user.balance if user else 0
        vip_level = user.vip_level if user else 1

        active_count = (
            await session.execute(
                select(func.count(VaultDeposit.id)).where(
                    and_(VaultDeposit.user_id == user_id, VaultDeposit.status == "active")
                )
            )
        ).scalar() or 0

    perks = get_vip_perks(vip_level)
    level_title = get_vip_title(lang, vip_level)
    bonus_pct = round(perks["vault_bonus"] * 100, 1)

    text = get_text(
        lang,
        "vault_menu",
        balance=balance,
        active_count=active_count,
        max_active=MAX_ACTIVE_VAULT_DEPOSITS,
        level_title=esc(level_title),
        bonus_pct=bonus_pct,
        max_deposit=MAX_VAULT_DEPOSIT,
    )

    keyboard = [
        [
            InlineKeyboardButton(get_text(lang, "vault_btn_7d"), callback_data="vault_deposit_7"),
            InlineKeyboardButton(get_text(lang, "vault_btn_30d"), callback_data="vault_deposit_30"),
        ],
        [InlineKeyboardButton(get_text(lang, "vault_btn_my"), callback_data="my_vault_deposits")],
        [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def prompt_vault_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    lang = get_user_lang(db_user)
    days = int(query.data.replace("vault_deposit_", ""))
    context.user_data["vault_plan_days"] = days
    context.user_data["awaiting_vault_amount"] = True

    rate_pct = int(PLAN_YIELDS.get(days, 0.05) * 100)
    await query.edit_message_text(
        get_text(
            lang,
            "vault_prompt",
            days=days,
            rate_pct=rate_pct,
            max_deposit=MAX_VAULT_DEPOSIT,
        ),
        parse_mode="HTML",
    )


async def process_vault_deposit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return True

    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    text = update.message.text.strip()
    days = context.user_data.get("vault_plan_days", 7)

    ok_amt, amount, err = sanitize_amount(text, min_val=500, max_val=MAX_VAULT_DEPOSIT, lang=lang)
    if not ok_amt:
        await update.message.reply_text(err)
        return True

    context.user_data.pop("awaiting_vault_amount", None)

    now = utcnow()
    lock_until = now + timedelta(days=days)

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not user or user.balance < amount:
                await update.message.reply_text(get_text(lang, "vault_err_insufficient"))
                return True

            lang = get_user_lang(user)
            active_count = (
                await session.execute(
                    select(func.count(VaultDeposit.id)).where(
                        and_(VaultDeposit.user_id == user_id, VaultDeposit.status == "active")
                    )
                )
            ).scalar() or 0
            if active_count >= MAX_ACTIVE_VAULT_DEPOSITS:
                await update.message.reply_text(
                    get_text(lang, "vault_err_max_active", max_active=MAX_ACTIVE_VAULT_DEPOSITS)
                )
                return True

            perks = get_vip_perks(user.vip_level)
            yield_rate = PLAN_YIELDS.get(days, 0.05) + perks["vault_bonus"]
            yield_amount = int(amount * yield_rate)

            user.balance -= amount
            deposit = VaultDeposit(
                user_id=user_id,
                amount=amount,
                yield_amount=yield_amount,
                duration_days=days,
                lock_until=lock_until,
                status="active",
            )
            session.add(deposit)
            session.add(
                Transaction(
                    user_id=user_id,
                    trans_type="vault_deposit",
                    amount=-amount,
                    description=f"إيداع في الخزنة ({days} يوم) بقيمة {amount}",
                )
            )
            await session.commit()

    await update.message.reply_text(
        get_text(
            lang,
            "vault_deposit_created",
            amount=amount,
            yield_amount=yield_amount,
            lock_until=lock_until.strftime("%Y-%m-%d %H:%M UTC"),
        ),
        parse_mode="HTML",
    )
    return True


async def show_my_vault_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    if query:
        await query.answer()

    now = utcnow()
    async with AsyncSessionLocal() as session:
        deposits = (
            await session.execute(
                select(VaultDeposit)
                .where(VaultDeposit.user_id == user_id)
                .order_by(VaultDeposit.created_at.desc())
                .limit(10)
            )
        ).scalars().all()

    if not deposits:
        text = get_text(lang, "vault_my_empty")
        keyboard = [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="show_vault_menu")]]
    else:
        text = get_text(lang, "vault_my_header")
        keyboard = []
        for d in deposits:
            if d.status == "withdrawn":
                text += get_text(
                    lang,
                    "vault_row_withdrawn",
                    dep_id=d.id,
                    days=d.duration_days,
                    amount=d.amount,
                    yield_amount=d.yield_amount,
                )
            else:
                is_matured = now >= d.lock_until
                status_str = (
                    get_text(lang, "vault_status_ready")
                    if is_matured
                    else get_text(lang, "vault_status_locked", date=d.lock_until.strftime("%Y-%m-%d"))
                )
                text += get_text(
                    lang,
                    "vault_row_active",
                    dep_id=d.id,
                    days=d.duration_days,
                    status=status_str,
                    amount=d.amount,
                    yield_amount=d.yield_amount,
                )
                if is_matured:
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                get_text(lang, "vault_btn_withdraw", dep_id=d.id),
                                callback_data=f"withdraw_vault_{d.id}",
                            )
                        ]
                    )

        keyboard.append([InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="show_vault_menu")])

    markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def handle_withdraw_vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    deposit_id = int(query.data.replace("withdraw_vault_", ""))
    now = utcnow()

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            dep = (
                await session.execute(select(VaultDeposit).where(VaultDeposit.id == deposit_id))
            ).scalar_one_or_none()
            if not dep or dep.user_id != user_id or dep.status != "active":
                await query.answer(get_text(lang, "vault_err_not_found"), show_alert=True)
                return

            if now < dep.lock_until:
                await query.answer(get_text(lang, "vault_err_not_matured"), show_alert=True)
                return

            total_payout = dep.amount + dep.yield_amount
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if user:
                lang = get_user_lang(user)
                user.balance += total_payout

            dep.status = "withdrawn"
            session.add(
                Transaction(
                    user_id=user_id,
                    trans_type="vault_withdraw",
                    amount=total_payout,
                    description=f"استرداد ودائع الخزنة #{dep.id} مع الأرباح",
                )
            )
            await session.commit()

    await query.answer(
        get_text(lang, "vault_withdrawn_alert", total_payout=total_payout), show_alert=True
    )
    await show_my_vault_deposits(update, context)
