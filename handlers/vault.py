from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, and_
from database.db import AsyncSessionLocal
from database.models import User, VaultDeposit, Transaction
from utils.security import user_lock_manager, sanitize_amount

PLAN_YIELDS = {
    7: 0.05,   # +5% yield for 7 days
    30: 0.20   # +20% yield for 30 days
}

async def show_vault_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        balance = user.balance if user else 0

        active_deposits = (await session.execute(
            select(VaultDeposit).where(and_(VaultDeposit.user_id == user_id, VaultDeposit.status == "active"))
        )).scalars().all()

    text = (
        f"🏛️ **خزنة التوفير والأرباح (Savings Vault):**\n\n"
        f"جمّد غراماتك في الخزنة واحصل على عوائد مجانية مضافة لرصيدك!\n\n"
        f"💳 **رصيدك الحرفي المتاح:** `{balance:,}` غرام\n"
        f"📦 **عدد الودائع النشطة:** `{len(active_deposits)}`\n\n"
        f"📈 **خطط الاستثمار المتاحة:**\n"
        f"1️⃣ **خطة 7 أيام:** عائد **+5%** مجاناً.\n"
        f"2️⃣ **خطة 30 يوم:** عائد **+20%** مجاناً (للخطط طويلة الأجل).\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("➕ إيداع 7 أيام (+5%)", callback_data="vault_deposit_7"),
            InlineKeyboardButton("➕ إيداع 30 يوم (+20%)", callback_data="vault_deposit_30")
        ],
        [InlineKeyboardButton("📜 ودائعي واسترداد الأرباح", callback_data="my_vault_deposits")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def prompt_vault_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    days = int(query.data.replace("vault_deposit_", ""))
    context.user_data["vault_plan_days"] = days
    context.user_data["awaiting_vault_amount"] = True

    rate_pct = int(PLAN_YIELDS[days] * 100)
    await query.edit_message_text(
        f"➕ **إنشاء إيداع جديد ({days} يوم - عائد +{rate_pct}%):**\n\n"
        f"يرجى إرسال مبلغ الغرامات المراد تجميده في الشات مباشرة (الحد الأدنى: 500 غرام).",
        parse_mode="Markdown"
    )

async def process_vault_deposit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    days = context.user_data.get("vault_plan_days", 7)

    ok, amount, err = sanitize_amount(text, min_val=500)
    if not ok:
        await update.message.reply_text(err)
        return True

    context.user_data.pop("awaiting_vault_amount", None)

    yield_rate = PLAN_YIELDS.get(days, 0.05)
    yield_amount = int(amount * yield_rate)
    now = datetime.utcnow()
    lock_until = now + timedelta(days=days)

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
            if not user or user.balance < amount:
                await update.message.reply_text("❌ رصيدك الحالي غير كافٍ لإتمام هذا الإيداع.")
                return True

            user.balance -= amount
            deposit = VaultDeposit(
                user_id=user_id,
                amount=amount,
                yield_amount=yield_amount,
                duration_days=days,
                lock_until=lock_until,
                status="active"
            )
            session.add(deposit)

            tx = Transaction(
                user_id=user_id,
                trans_type="vault_deposit",
                amount=-amount,
                description=f"إيداع في الخزنة ({days} يوم) بقيمة {amount}"
            )
            session.add(tx)
            await session.commit()

    await update.message.reply_text(
        f"🎉 **تم إنشاء الإيداع بنجاح!**\n\n"
        f"💰 **المبلغ المجمد:** `{amount:,}` غرام\n"
        f"📈 **الأرباح المتوقعة:** `+{yield_amount:,}` غرام\n"
        f"⏱️ **تاريخ الفك والتصفية:** `{lock_until.strftime('%Y-%m-%d %H:%M UTC')}`",
        parse_mode="Markdown"
    )
    return True

async def show_my_vault_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    now = datetime.utcnow()

    async with AsyncSessionLocal() as session:
        deposits = (await session.execute(
            select(VaultDeposit).where(VaultDeposit.user_id == user_id).order_by(VaultDeposit.created_at.desc()).limit(10)
        )).scalars().all()

    if not deposits:
        text = "🏛️ **ودائعي في الخزنة:**\n\nلا توجد لديك أي ودائع حالياً."
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="show_vault_menu")]]
    else:
        text = "🏛️ **ودائعي في الخزنة:**\n\n"
        keyboard = []
        for d in deposits:
            if d.status == "withdrawn":
                text += f"✅ **إيداع منتهي #{d.id}** ({d.duration_days} يوم)\n المبلغ: `{d.amount:,}` + أرباح `{d.yield_amount:,}` غرام\n\n"
            else:
                is_matured = now >= d.lock_until
                status_str = "🟢 جاهز للاسترداد" if is_matured else f"⏳ متبقي حتى {d.lock_until.strftime('%Y-%m-%d')}"
                text += f"🔹 **إيداع #{d.id}** ({d.duration_days} يوم) | {status_str}\n المبلغ: `{d.amount:,}` | الأرباح: `+{d.yield_amount:,}` غرام\n\n"
                if is_matured:
                    keyboard.append([InlineKeyboardButton(f"🎁 استرداد إيداع #{d.id} مع الأرباح", callback_data=f"withdraw_vault_{d.id}")])

        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="show_vault_menu")])

    markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def handle_withdraw_vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    deposit_id = int(query.data.replace("withdraw_vault_", ""))
    now = datetime.utcnow()

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            dep = (await session.execute(select(VaultDeposit).where(VaultDeposit.id == deposit_id))).scalar_one_or_none()
            if not dep or dep.user_id != user_id or dep.status != "active":
                await query.answer("❌ تعذر العثور على هذا الإيداع أو تم استرداده مسبقاً.", show_alert=True)
                return

            if now < dep.lock_until:
                await query.answer("⏳ لم ينتهي وقت التجميد بعد!", show_alert=True)
                return

            total_payout = dep.amount + dep.yield_amount
            user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
            if user:
                user.balance += total_payout

            dep.status = "withdrawn"
            tx = Transaction(
                user_id=user_id,
                trans_type="vault_withdraw",
                amount=total_payout,
                description=f"استرداد ودائع الخزنة #{dep.id} مع الأرباح"
            )
            session.add(tx)
            await session.commit()

            await query.answer(f"🎉 تم استرداد +{total_payout:,} غرام إلى رصيدك بنجاح!", show_alert=True)
            await show_my_vault_deposits(update, context)
