import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func, and_

from database.db import AsyncSessionLocal
from database.models import User, RaffleTicket, RaffleDraw, Transaction
from utils.security import user_lock_manager, is_admin_user
from utils.gatekeeper import enforce_user_access
from utils.i18n import get_text, get_user_lang
from utils.html_utils import utcnow

TICKET_PRICE = 100


def generate_ticket_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return f"TICK-{''.join(random.choices(chars, k=6))}"


async def get_or_create_active_draw(session):
    draw = (
        await session.execute(select(RaffleDraw).where(RaffleDraw.status == "active"))
    ).scalar_one_or_none()
    if not draw:
        draw = RaffleDraw(prize_pool=0, status="active")
        session.add(draw)
        await session.commit()
    return draw


async def show_raffle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        draw = await get_or_create_active_draw(session)

        user_tickets_cnt = (
            await session.execute(
                select(func.count(RaffleTicket.id)).where(
                    and_(RaffleTicket.draw_id == draw.id, RaffleTicket.user_id == user_id)
                )
            )
        ).scalar() or 0

        total_tickets_cnt = (
            await session.execute(
                select(func.count(RaffleTicket.id)).where(RaffleTicket.draw_id == draw.id)
            )
        ).scalar() or 0

        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        if user:
            lang = get_user_lang(user)
        balance = user.balance if user else 0

    text = get_text(
        lang,
        "raffle_menu",
        prize_pool=draw.prize_pool,
        user_tickets=user_tickets_cnt,
        total_tickets=total_tickets_cnt,
        ticket_price=TICKET_PRICE,
        balance=balance,
    )

    keyboard = [
        [
            InlineKeyboardButton(get_text(lang, "raffle_btn_buy_1"), callback_data="buy_raffle_1"),
            InlineKeyboardButton(get_text(lang, "raffle_btn_buy_5"), callback_data="buy_raffle_5"),
        ],
        [InlineKeyboardButton(get_text(lang, "raffle_btn_my"), callback_data="my_raffle_tickets")],
        [InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="close_menu")],
    ]
    if is_admin_user(user_id):
        keyboard.append(
            [
                InlineKeyboardButton(
                    get_text(lang, "raffle_btn_admin_draw"), callback_data="admin_draw_raffle_now"
                )
            ]
        )

    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def handle_buy_raffle_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    count = int(query.data.replace("buy_raffle_", ""))
    if count <= 0 or count > 100:
        await query.answer(get_text(lang, "raffle_err_invalid_qty"), show_alert=True)
        return
    total_cost = count * TICKET_PRICE

    async with user_lock_manager.acquire_ordered_locks("raffle_draw", f"u_{user_id}"):
        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            if not user or user.balance < total_cost:
                await query.answer(get_text(lang, "raffle_err_insufficient"), show_alert=True)
                return

            lang = get_user_lang(user)
            draw = await get_or_create_active_draw(session)

            user.balance -= total_cost
            draw.prize_pool += total_cost

            for _ in range(count):
                code = generate_ticket_code()
                session.add(RaffleTicket(user_id=user_id, ticket_code=code, draw_id=draw.id))

            session.add(
                Transaction(
                    user_id=user_id,
                    trans_type="raffle_buy",
                    amount=-total_cost,
                    description=f"شراء {count} تذاكر يانصيب (#Draw-{draw.id})",
                )
            )
            await session.commit()

    await query.answer(get_text(lang, "raffle_buy_success", count=count), show_alert=True)
    await show_raffle_menu(update, context)


async def show_my_raffle_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, db_user = await enforce_user_access(update, context)
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_user_lang(db_user)
    await query.answer()

    async with AsyncSessionLocal() as session:
        draw = await get_or_create_active_draw(session)
        tickets = (
            await session.execute(
                select(RaffleTicket).where(
                    and_(RaffleTicket.draw_id == draw.id, RaffleTicket.user_id == user_id)
                )
            )
        ).scalars().all()

    if not tickets:
        text = get_text(lang, "raffle_my_empty")
    else:
        codes_str = ", ".join([f"<code>{t.ticket_code}</code>" for t in tickets[:20]])
        text = get_text(
            lang,
            "raffle_my_list",
            draw_id=draw.id,
            count=len(tickets),
            codes=codes_str,
        )

    keyboard = [[InlineKeyboardButton(get_text(lang, "btn_back"), callback_data="show_raffle_menu")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_admin_draw_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_draw_raffle_now"):
        return

    winner_lang = "ar"
    admin_lang = "ar"
    async with user_lock_manager.get_lock("raffle_draw"):
        async with AsyncSessionLocal() as session:
            admin_user = (
                await session.execute(select(User).where(User.telegram_id == user_id))
            ).scalar_one_or_none()
            admin_lang = get_user_lang(admin_user)

            draw = (
                await session.execute(select(RaffleDraw).where(RaffleDraw.status == "active"))
            ).scalar_one_or_none()
            if not draw or draw.prize_pool == 0:
                await query.answer(get_text(admin_lang, "raffle_draw_empty"), show_alert=True)
                return

            all_tickets = (
                await session.execute(
                    select(RaffleTicket).where(RaffleTicket.draw_id == draw.id)
                )
            ).scalars().all()
            if not all_tickets:
                await query.answer(get_text(admin_lang, "raffle_draw_no_tickets"), show_alert=True)
                return

            winner_ticket = random.choice(all_tickets)
            winner_user = (
                await session.execute(
                    select(User).where(User.telegram_id == winner_ticket.user_id)
                )
            ).scalar_one_or_none()

            draw.winner_user_id = winner_ticket.user_id
            draw.winner_ticket_code = winner_ticket.ticket_code
            draw.status = "completed"
            draw.drawn_at = utcnow()

            if winner_user:
                winner_lang = get_user_lang(winner_user)
                winner_user.balance += draw.prize_pool
                session.add(
                    Transaction(
                        user_id=winner_user.telegram_id,
                        trans_type="raffle_win",
                        amount=draw.prize_pool,
                        description=f"جائزة الفوز باليانصيب الأسبوعي (#Draw-{draw.id})",
                    )
                )

            winner_id = winner_ticket.user_id
            prize = draw.prize_pool
            t_code = winner_ticket.ticket_code

            session.add(RaffleDraw(prize_pool=0, status="active"))
            await session.commit()

    await query.answer(get_text(admin_lang, "raffle_draw_done_alert"), show_alert=True)

    win_msg = get_text(
        admin_lang,
        "raffle_draw_summary",
        prize=prize,
        winner_id=winner_id,
        ticket_code=t_code,
    )
    await query.edit_message_text(win_msg, parse_mode="HTML")

    try:
        await context.bot.send_message(
            chat_id=winner_id,
            text=get_text(winner_lang, "raffle_winner_dm", prize=prize),
            parse_mode="HTML",
        )
    except Exception:
        pass
