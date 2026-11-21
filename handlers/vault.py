from datetime import timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func, and_

from config import MAX_VAULT_DEPOSIT, MAX_ACTIVE_VAULT_DEPOSITS
from database.db import AsyncSessionLocal
from database.models import User, VaultDeposit, Transaction
from utils.security import user_lock_manager, sanitize_amount, get_vip_perks
from utils.gatekeeper import enforce_user_access
from utils.html_utils import esc, utcnow

PLAN_YIELDS = {
    7: 0.05,   # +5% base yield for 7 days
    30: 0.20,  # +20% base yield for 30 days
}


async def show_vault_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
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
    bonus_pct = round(perks["vault_bonus"] * 100, 1)

    text = (
        f"🏛️ <b>خزنة التوفير والأرباح (Savings Vault):</b>\n\n"
        f"جمّد غراماتك في الخزنة واحصل على عوائد مجانية مضافة لرصيدك!\n\n"
        f"💳 <b>رصيدك المتاح:</b> <code>{balance:,}</code> غرام\n"
        f"📦 <b>الودائع النشطة:</b> <code>{active_count}/{MAX_ACTIVE_VAULT_DEPOSITS}</code>\n"
        f"🏅 <b>عائد إضافي لمستواك ({esc(perks['title'])}):</b> <code>+{bonus_pct}%</code>\n\n"
        f"📈 <b>خطط الاستثمار المتاحة:</b>\n"
        f"1️⃣ <b>خطة 7 أيام:</b> عائد أساسي <b>+5%</b> (+ عائد VIP).\n"
        f"2️⃣ <b>خطة 30 يوم:</b> عائد أساسي <b>+20%</b> (+ عائد VIP).\n"
        f"🔒 الحد الأقصى للإيداع الواحد: <code>{MAX_VAULT_DEPOSIT:,}</code> غرام."
    )

    keyboard = [
        [
            InlineKeyboardButton("➕ إيداع 7 أيام (+5%)", callback_data="vault_deposit_7"),
            InlineKeyboardButton("➕ إيداع 30 يوم (+20%)", callback_data="vault_deposit_30"),
        ],
        [InlineKeyboardButton("📜 ودائعي واسترداد الأرباح", callback_data="my_vault_deposits")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def prompt_vault_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    days = int(query.data.replace("vault_deposit_", ""))
    context.user_data["vault_plan_days"] = days
    context.user_data["awaiting_vault_amount"] = True

    rate_pct = int(PLAN_YIELDS.get(days, 0.05) * 100)
    await query.edit_message_text(
        f"➕ <b>إنشاء إيداع جديد ({days} يوم - عائد أساسي +{rate_pct}%):</b>\n\n"
        f"يرجى إرسال مبلغ الغرامات المراد تجميده في الشات مباشرة "
        f"(الحد الأدنى: 500، الحد الأقصى: {MAX_VAULT_DEPOSIT:,} غرام).",
        parse_mode="HTML",
    )


async def process_vault_deposit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return True

    user_id = update.effective_user.id
    text = update.message.text.strip()
    days = context.user_data.get("vault_plan_days", 7)

    ok_amt, amount, err = sanitize_amount(text, min_val=500, max_val=MAX_VAULT_DEPOSIT)
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
                await update.message.reply_text("❌ رصيدك الحالي غير كافٍ لإتمام هذا الإيداع.")
                return True

            active_count = (
                await session.execute(
                    select(func.count(VaultDeposit.id)).where(
                        and_(VaultDeposit.user_id == user_id, VaultDeposit.status == "active")
                    )
                )
            ).scalar() or 0
            if active_count >= MAX_ACTIVE_VAULT_DEPOSITS:
                await update.message.reply_text(
                    f"⚠️ وصلت للحد الأقصى للودائع النشطة ({MAX_ACTIVE_VAULT_DEPOSITS}). انتظر فك وديعة قبل إنشاء جديدة."
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
        f"🎉 <b>تم إنشاء الإيداع بنجاح!</b>\n\n"
        f"💰 <b>المبلغ المجمد:</b> <code>{amount:,}</code> غرام\n"
        f"📈 <b>الأرباح المتوقعة:</b> <code>+{yield_amount:,}</code> غرام\n"
        f"⏱️ <b>تاريخ الفك والتصفية:</b> <code>{lock_until.strftime('%Y-%m-%d %H:%M UTC')}</code>",
        parse_mode="HTML",
    )
    return True


async def show_my_vault_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
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
        text = "🏛️ <b>ودائعي في الخزنة:</b>\n\nلا توجد لديك أي ودائع حالياً."
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="show_vault_menu")]]
    else:
        text = "🏛️ <b>ودائعي في الخزنة:</b>\n\n"
        keyboard = []
        for d in deposits:
            if d.status == "withdrawn":
                text += f"✅ <b>إيداع منتهي #{d.id}</b> ({d.duration_days} يوم)\n المبلغ: <code>{d.amount:,}</code> + أرباح <code>{d.yield_amount:,}</code> غرام\n\n"
            else:
                is_matured = now >= d.lock_until
                status_str = (
                    "🟢 جاهز للاسترداد"
                    if is_matured
                    else f"⏳ متبقي حتى {d.lock_until.strftime('%Y-%m-%d')}"
                )
                text += f"🔹 <b>إيداع #{d.id}</b> ({d.duration_days} يوم) | {status_str}\n المبلغ: <code>{d.amount:,}</code> | الأرباح: <code>+{d.yield_amount:,}</code> غرام\n\n"
                if is_matured:
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                f"🎁 استرداد إيداع #{d.id} مع الأرباح",
                                callback_data=f"withdraw_vault_{d.id}",
                            )
                        ]
                    )

        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="show_vault_menu")])

    markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def handle_withdraw_vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    deposit_id = int(query.data.replace("withdraw_vault_", ""))
    now = utcnow()

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            dep = (
                await session.execute(select(VaultDeposit).where(VaultDeposit.id == deposit_id))
            ).scalar_one_or_none()
            if not dep or dep.user_id != user_id or dep.status != "active":
                await query.answer("❌ تعذر العثور على هذا الإيداع أو تم استرداده مسبقاً.", show_alert=True)
                return

            if now < dep.lock_until:
                await query.answer("⏳ لم ينتهي وقت التجميد بعد!", show_alert=True)
                return

            total_payout = dep.amount + dep.yield_amount
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if user:
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

    await query.answer(f"🎉 تم استرداد +{total_payout:,} غرام إلى رصيدك بنجاح!", show_alert=True)
    await show_my_vault_deposits(update, context)
