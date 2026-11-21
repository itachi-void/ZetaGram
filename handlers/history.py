import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from database.db import AsyncSessionLocal
from database.models import Transaction
from utils.gatekeeper import enforce_user_access
from utils.i18n import get_text, get_user_lang, get_tx_type_label
from utils.html_utils import esc

TX_PAGE_SIZE = 10


async def show_transaction_history(
    update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1
):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
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
        text = get_text(lang, "history_empty")
    else:
        text = get_text(lang, "history_title", page=page, total_pages=total_pages)
        for tx in transactions:
            icon = get_tx_type_label(lang, tx.trans_type)
            sign = "+" if tx.amount > 0 else ""
            dt_str = tx.created_at.strftime("%Y-%m-%d %H:%M")
            details_line = (
                get_text(lang, "history_details_line", desc=esc(tx.description))
                if tx.description
                else ""
            )
            text += get_text(
                lang,
                "history_row",
                icon=icon,
                sign=sign,
                amount=tx.amount,
                details_line=details_line,
                dt_str=dt_str,
            )

    keyboard = []
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(get_text(lang, "history_btn_prev"), callback_data=f"tx_page_{page - 1}")
            )
        nav_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(get_text(lang, "history_btn_next"), callback_data=f"tx_page_{page + 1}")
            )
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")])
    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)
