from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import Transaction

TYPE_ICONS = {
    "earn_task": "🧑‍💻 كسب مهمة",
    "spend_promo": "📣 إنشاء ترويج",
    "voucher_claim": "🎁 استبدال شيك",
    "voucher_create": "🏷️ إنشاء شيك",
    "transfer_send": "💸 تحويل مرسل",
    "transfer_receive": "📥 تحويل مستلم",
    "daily_bonus": "🎁 مكافأة يومية",
    "spin": "🎡 عجلة الحظ",
    "admin_adjust": "⚙️ تعديل أدمن",
    "reward": "🏅 مكافأة إنجاز"
}

async def show_transaction_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(15)
        )
        transactions = result.scalars().all()

    if not transactions:
        text = "📜 **سجل المعاملات:**\n\nلا توجد معاملات مسجلة في حسابك حتى الآن."
    else:
        text = "📜 **سجل آخر 15 معاملة في حسابك:**\n\n"
        for tx in transactions:
            icon = TYPE_ICONS.get(tx.trans_type, "💰 معاملة")
            sign = "+" if tx.amount > 0 else ""
            dt_str = tx.created_at.strftime("%Y-%m-%d %H:%M")
            text += f"{icon}\n"
            text += f"🔹 المبلغ: `{sign}{tx.amount:,}` غرام\n"
            if tx.description:
                text += f"💬 التفاصيل: {tx.description}\n"
            text += f"⏱️ التاريخ: {dt_str}\n"
            text += "─────────────────\n"

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]]
    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)
