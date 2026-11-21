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
from utils.html_utils import esc, utcnow


async def show_transfer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(update, context)
    if not ok:
        return

    perks = get_vip_perks(user.vip_level if user else 1)
    fee_pct = round(perks["transfer_fee"] * 100, 1)

    text = (
        "💸 <b>نظام تحويل الرصيد بين الأعضاء:</b>\n\n"
        "يمكنك إرسال غرامات من رصيدك لأي عضو آخر باستخدام معرفه (Telegram ID).\n"
        f"• 💵 <b>الحد الأدنى للتحويل:</b> <code>{MIN_TRANSFER_AMOUNT:,}</code> غرام\n"
        f"• 📊 <b>الحد الأقصى اليومي:</b> <code>{DAILY_TRANSFER_LIMIT:,}</code> غرام\n"
        f"• 📉 <b>عمولتك الحالية ({esc(perks['title'])}):</b> <code>{fee_pct}%</code>\n\n"
        "استخدم التعليمة المباشرة:\n"
        "<code>/transfer &lt;ID&gt; &lt;المبلغ&gt;</code>\n\n"
        "أو اضغط على الزر أدناه للتحويل التفاعلي."
    )
    keyboard = [
        [InlineKeyboardButton("💸 بدء تحويل رصيد", callback_data="prompt_transfer_id")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")],
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
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_transfer_input"] = True
    await query.edit_message_text(
        "💸 <b>تحويل رصيد:</b>\n\n"
        "أرسل آيدي المستلم والمبلغ مفصولين بمسافة:\n"
        "<code>&lt;ID_المستلم&gt; &lt;المبلغ&gt;</code>\n\n"
        "مثال: <code>123456789 500</code>",
        parse_mode="HTML",
    )


async def process_transfer_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("awaiting_transfer_input"):
        return False

    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return True

    parts = update.message.text.strip().split()
    if len(parts) < 2:
        await update.message.reply_text(
            "⚠️ يرجى إرسال الآيدي والمبلغ مفصولين بمسافة، مثال: <code>123456789 500</code>",
            parse_mode="HTML",
        )
        return True

    context.user_data.pop("awaiting_transfer_input", None)
    await execute_transfer(update, context, parts[0], parts[1])
    return True


async def handle_transfer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ <b>الاستخدام الخاطئ!</b>\n"
            "الصيغة الصحيحة:\n"
            "<code>/transfer &lt;ID_المستلم&gt; &lt;المبلغ&gt;</code>\n\n"
            "مثال: <code>/transfer 123456789 500</code>",
            parse_mode="HTML",
        )
        return

    await execute_transfer(update, context, args[0], args[1])


async def execute_transfer(
    update: Update, context: ContextTypes.DEFAULT_TYPE, target_raw: str, amount_raw: str
):
    user_id = update.effective_user.id

    try:
        target_id = int(target_raw.strip())
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال آيدي مستلم صحيح.")
        return

    if target_id == user_id:
        await update.message.reply_text("❌ لا يمكنك تحويل الرصيد لنفسك!")
        return

    ok, amount, err = sanitize_amount(amount_raw, min_val=MIN_TRANSFER_AMOUNT, max_val=DAILY_TRANSFER_LIMIT)
    if not ok:
        await update.message.reply_text(err)
        return

    today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    async with user_lock_manager.acquire_ordered_locks(user_id, target_id):
        async with AsyncSessionLocal() as session:
            sender = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            receiver = (
                await session.execute(select(User).where(User.telegram_id == target_id))
            ).scalar_one_or_none()

            if not sender:
                await update.message.reply_text("❌ حدث خطأ في بيانات حسابك.")
                return
            if not receiver:
                await update.message.reply_text("❌ لم يتم العثور على مستخدم بهذا الآيدي في البوت!")
                return

            # Anti-farming check for new accounts
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
                        f"🛡️ <b>حماية الحسابات الجديدة:</b>\n"
                        f"يجب إكمال <b>{MIN_TASKS_FOR_TRANSFER} مهام</b> على الأقل قبل تفعيل ميزة تحويل الرصيد (مهامك: {completed_cnt}/{MIN_TASKS_FOR_TRANSFER}).",
                        parse_mode="HTML",
                    )
                    return

            # Daily transfer cap check
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
                    f"⛔ <b>تجاوزت الحد اليومي للتحويلات ({DAILY_TRANSFER_LIMIT:,} غرام)!</b>\n"
                    f"المتبقي لك اليوم: <code>{rem_limit:,}</code> غرام.",
                    parse_mode="HTML",
                )
                return

            perks = get_vip_perks(sender.vip_level)
            fee_rate = perks["transfer_fee"]
            fee = math.ceil(amount * fee_rate) if fee_rate > 0 else 0
            total_deduct = amount + fee

            if sender.balance < total_deduct:
                await update.message.reply_text(
                    f"❌ رصيدك غير كافٍ!\n"
                    f"المبلغ المراد تحويله: {amount:,}\n"
                    f"العمولة ({round(fee_rate * 100, 1)}%): {fee:,}\n"
                    f"إجمالي المطلوب خصمه: {total_deduct:,} غرام\n"
                    f"رصيدك الحالي: {sender.balance:,} غرام"
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
        f"🎉 <b>تم التحويل بنجاح!</b>\n\n"
        f"👤 المستلم: <code>{target_id}</code>\n"
        f"💰 المبلغ المحول: {amount:,} غرام\n"
        f"📉 العمولة: {fee:,} غرام\n"
        f"💳 رصيدك المتبقي: {sender_bal:,} غرام",
        parse_mode="HTML",
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                f"🎁 <b>وصلك تحويل رصيد جديد!</b>\n\n"
                f"قام العضو <code>{user_id}</code> بتحويل <b>+{amount:,} غرام</b> إلى حسابك.\n"
                f"💳 رصيدك الجديد: {receiver_bal:,} غرام"
            ),
            parse_mode="HTML",
        )
    except Exception:
        pass
