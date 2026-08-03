from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import User, Transaction
from utils.security import user_lock_manager, sanitize_amount

TRANSFER_FEE_PERCENT = 2.0 # 2% fee

async def show_transfer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💸 **نظام تحويل الرصيد بين الأعضاء:**\n\n"
        "يمكنك إرسال غرامات من رصيدك لأي عضو آخر باستخدام معرفه (Telegram ID).\n"
        f"💡 *يتم خصم عمولة تحويل بسيطة قدرها {TRANSFER_FEE_PERCENT}% من قيمة المبلغ.*\n\n"
        "إما باستخدام التعليمة المباشرة:\n"
        "`/transfer <ID> <المبلغ>`\n\n"
        "أو بالضغط على الزر أدناه لبدء عملية التحويل."
    )
    keyboard = [
        [InlineKeyboardButton("💸 بدء تحويل رصيد", callback_data="prompt_transfer_id")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def handle_transfer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Format: /transfer <target_user_id> <amount>
    Example: /transfer 123456789 500
    """
    user_id = update.effective_user.id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ **الاستخدام الخاطئ!**\n"
            "الصيغة الصحيحة:\n"
            "`/transfer <ID_المستلم> <المبلغ>`\n\n"
            "مثال: `/transfer 123456789 500`",
            parse_mode="Markdown"
        )
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال آيدي مستلم صحيح.")
        return

    if target_id == user_id:
        await update.message.reply_text("❌ لا يمكنك تحويل الرصيد لنفسك!")
        return

    ok, amount, err = sanitize_amount(args[1], min_val=1)
    if not ok:
        await update.message.reply_text(err)
        return

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            sender = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
            receiver = (await session.execute(select(User).where(User.telegram_id == target_id))).scalar_one_or_none()

            if not sender:
                await update.message.reply_text("❌ حدث خطأ في بيانات حسابك.")
                return

            if not receiver:
                await update.message.reply_text("❌ لم يتم العثور على مستخدم بهذا الآيدي في البوت!")
                return

            fee = int(amount * (TRANSFER_FEE_PERCENT / 100.0))
            total_deduct = amount + fee

            if sender.balance < total_deduct:
                await update.message.reply_text(
                    f"❌ رصيدك غير كافٍ!\n"
                    f"المبلغ المراد تحويله: {amount:,}\n"
                    f"العمولة ({TRANSFER_FEE_PERCENT}%): {fee:,}\n"
                    f"إجمالي المطلوب خصمه: {total_deduct:,} غرام\n"
                    f"رصيدك الحالي: {sender.balance:,} غرام"
                )
                return

            # Perform transfer
            sender.balance -= total_deduct
            receiver.balance += amount

            # Record transactions
            tx_sender = Transaction(
                user_id=user_id,
                trans_type="transfer_send",
                amount=-total_deduct,
                description=f"إرسال رصيد إلى {target_id} (شامل عمولة {fee})"
            )
            tx_receiver = Transaction(
                user_id=target_id,
                trans_type="transfer_receive",
                amount=amount,
                description=f"استلام رصيد من {user_id}"
            )
            session.add(tx_sender)
            session.add(tx_receiver)

            await session.commit()

            # Send confirmation to sender
            await update.message.reply_text(
                f"🎉 **تم التحويل بنجاح!**\n\n"
                f"👤 المستلم: `{target_id}`\n"
                f"💰 المبلغ المحول: {amount:,} غرام\n"
                f"📉 العمولة: {fee:,} غرام\n"
                f"💳 رصيدك المتبقي: {sender.balance:,} غرام",
                parse_mode="Markdown"
            )

            # Notify receiver
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"🎁 **وصلك تحويل رصيد جديد!**\n\n"
                         f"قام العضو `{user_id}` بتحويل **+{amount:,} غرام** إلى حسابك.\n"
                         f"💳 رصيدك الجديد: {receiver.balance:,} غرام",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
