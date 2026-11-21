import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from database.db import AsyncSessionLocal
from database.models import Transaction
from utils.gatekeeper import enforce_user_access
from utils.html_utils import esc

TX_PAGE_SIZE = 10

TYPE_ICONS = {
    "earn_task": "🧑‍💻 كسب مهمة",
    "spend_promo": "📣 إنشاء ترويج",
    "promo_refund": "↩️ استرداد ترويج",
    "voucher_claim": "🎁 استبدال شيك",
    "voucher_create": "🏷️ إنشاء شيك",
    "voucher_refund": "↩️ استرداد شيك",
    "transfer_send": "💸 تحويل مرسل",
    "transfer_receive": "📥 تحويل مستلم",
    "daily_bonus": "🎁 مكافأة يومية",
    "daily_quest": "🎯 تحدي يومي",
    "spin": "🎡 عجلة الحظ",
    "admin_adjust": "⚙️ تعديل أدمن",
    "reward": "🏅 مكافأة",
    "referral_milestone": "👥 مكافأة إحالة",
    "referral_commission": "💎 عمولة إحالة",
    "vault_deposit": "🏛️ إيداع خزنة",
    "vault_withdraw": "💰 سحب خزنة",
    "raffle_buy": "🎫 شراء تذكرة",
    "raffle_win": "🏆 فوز يانصيب",
    "unsub_penalty": "⚠️ خصم إلغاء اشتراك",
    "leaderboard_prize": "🏆 جائزة متصدرين",
}


async def show_transaction_history(
    update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1
):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        total = (
            await session.execute(
                select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
            )
        ).scalar() or 0
        total_pages = max(1, math.ceil(total / TX_PAGE_SIZE))
        page = max(1, min(page, total_pages))

        result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .offset((page - 1) * TX_PAGE_SIZE)
            .limit(TX_PAGE_SIZE)
        )
        transactions = result.scalars().all()

    if not transactions:
        text = "📜 <b>سجل المعاملات:</b>\n\nلا توجد معاملات مسجلة في حسابك حتى الآن."
    else:
        text = f"📜 <b>سجل المعاملات (صفحة {page}/{total_pages}):</b>\n\n"
        for tx in transactions:
            icon = TYPE_ICONS.get(tx.trans_type, "💰 معاملة")
            sign = "+" if tx.amount > 0 else ""
            dt_str = tx.created_at.strftime("%Y-%m-%d %H:%M")
            text += f"{icon}\n"
            text += f"🔹 المبلغ: <code>{sign}{tx.amount:,}</code> غرام\n"
            if tx.description:
                text += f"💬 التفاصيل: {esc(tx.description)}\n"
            text += f"⏱️ التاريخ: {dt_str}\n"
            text += "─────────────────\n"

    keyboard = []
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️ السابق", callback_data=f"tx_page_{page - 1}"))
        nav_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("التالي ▶️", callback_data=f"tx_page_{page + 1}"))
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")])
    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)
