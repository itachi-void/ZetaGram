import random
import string
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func, and_
from database.db import AsyncSessionLocal
from database.models import User, RaffleTicket, RaffleDraw, Transaction
from utils.security import user_lock_manager, is_admin_user, send_security_alert

TICKET_PRICE = 100 # 100 Grams per ticket

def generate_ticket_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return f"TICK-{''.join(random.choices(chars, k=6))}"

async def get_or_create_active_draw(session):
    draw = (await session.execute(select(RaffleDraw).where(RaffleDraw.status == "active"))).scalar_one_or_none()
    if not draw:
        draw = RaffleDraw(prize_pool=0, status="active")
        session.add(draw)
        await session.commit()
    return draw

async def show_raffle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        draw = await get_or_create_active_draw(session)

        user_tickets_cnt = (await session.execute(
            select(func.count(RaffleTicket.id)).where(and_(RaffleTicket.draw_id == draw.id, RaffleTicket.user_id == user_id))
        )).scalar() or 0

        total_tickets_cnt = (await session.execute(
            select(func.count(RaffleTicket.id)).where(RaffleTicket.draw_id == draw.id)
        )).scalar() or 0

        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        balance = user.balance if user else 0

    text = (
        f"🎟️ **نظام السحب واليانصيب الأسبوعي (Weekly Raffle):**\n\n"
        f"اشترِ تذاكر الدخول ومنافسة باقي الأعضاء على مسبح الجوائز الأسبوعي الضخم!\n\n"
        f"🏆 **مسبح الجوائز الحالي:** `{draw.prize_pool:,}` غرام\n"
        f"🎫 **تذكرتك الحالية في هذا السحب:** `{user_tickets_cnt}` تذكرة\n"
        f"👥 **إجمالي تذاكر المشاركين:** `{total_tickets_cnt}` تذكرة\n"
        f"💰 **سعر التذكرة الواحدة:** `{TICKET_PRICE:,}` غرام\n"
        f"💳 **رصيدك المتاح:** `{balance:,}` غرام\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎫 شراء تذكرة واحدة (100 غرام)", callback_data="buy_raffle_1"),
            InlineKeyboardButton("🎟️ شراء 5 تذاكر (500 غرام)", callback_data="buy_raffle_5")
        ],
        [InlineKeyboardButton("📜 تذاكري في السحب", callback_data="my_raffle_tickets")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]
    ]
    if is_admin_user(user_id):
        keyboard.append([InlineKeyboardButton("🎲 إعلان الفائز والسحب الآن (أدمن)", callback_data="admin_draw_raffle_now")])

    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def handle_buy_raffle_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    count = int(query.data.replace("buy_raffle_", ""))
    total_cost = count * TICKET_PRICE

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
            if not user or user.balance < total_cost:
                await query.answer("❌ رصيدك الحالي غير كافٍ لشراء التذاكر!", show_alert=True)
                return

            draw = await get_or_create_active_draw(session)

            user.balance -= total_cost
            draw.prize_pool += total_cost

            created_codes = []
            for _ in range(count):
                code = generate_ticket_code()
                t = RaffleTicket(user_id=user_id, ticket_code=code, draw_id=draw.id)
                session.add(t)
                created_codes.append(code)

            tx = Transaction(
                user_id=user_id,
                trans_type="raffle_buy",
                amount=-total_cost,
                description=f"شراء {count} تذاكر يانصيب (#Draw-{draw.id})"
            )
            session.add(tx)
            await session.commit()

        await query.answer(f"🎉 تم شراء {count} تذكرة يانصيب بنجاح!", show_alert=True)
        await show_raffle_menu(update, context)

async def show_my_raffle_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    async with AsyncSessionLocal() as session:
        draw = await get_or_create_active_draw(session)
        tickets = (await session.execute(
            select(RaffleTicket).where(and_(RaffleTicket.draw_id == draw.id, RaffleTicket.user_id == user_id))
        )).scalars().all()

    if not tickets:
        text = "🎫 **تذاكري في السحب الحالي:**\n\nلم تقم بشراء أي تذاكر في السحب الحالي بعد."
    else:
        codes_str = ", ".join([f"`{t.ticket_code}`" for t in tickets[:20]])
        text = (
            f"🎫 **تذاكرك الحالية (#Draw-{draw.id}):**\n\n"
            f"إجمالي عدد تذاكرك: `{len(tickets)}`\n"
            f"أكواد التذاكر:\n{codes_str}"
        )

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="show_raffle_menu")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_admin_draw_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    async with AsyncSessionLocal() as session:
        draw = (await session.execute(select(RaffleDraw).where(RaffleDraw.status == "active"))).scalar_one_or_none()
        if not draw or draw.prize_pool == 0:
            await query.answer("❌ لا يوجد سحب نشط أو لا توجد تذاكر مشاركة بعد!", show_alert=True)
            return

        all_tickets = (await session.execute(
            select(RaffleTicket).where(RaffleTicket.draw_id == draw.id)
        )).scalars().all()

        if not all_tickets:
            await query.answer("❌ لم يقم أحد بشراء تذاكر في هذا السحب بعد.", show_alert=True)
            return

        winner_ticket = random.choice(all_tickets)
        winner_user = (await session.execute(select(User).where(User.telegram_id == winner_ticket.user_id))).scalar_one_or_none()

        draw.winner_user_id = winner_ticket.user_id
        draw.winner_ticket_code = winner_ticket.ticket_code
        draw.status = "completed"
        draw.drawn_at = datetime.utcnow()

        if winner_user:
            winner_user.balance += draw.prize_pool
            tx = Transaction(
                user_id=winner_user.telegram_id,
                trans_type="raffle_win",
                amount=draw.prize_pool,
                description=f"جائزة الفوز باليانصيب الأسبوعي (#Draw-{draw.id})"
            )
            session.add(tx)

        await session.commit()

        winner_id = winner_ticket.user_id
        prize = draw.prize_pool
        t_code = winner_ticket.ticket_code

        # Create new active draw
        new_draw = RaffleDraw(prize_pool=0, status="active")
        session.add(new_draw)
        await session.commit()

    await query.answer("🎲 تم السحب وإعلان الفائز بنجاح!", show_alert=True)

    win_msg = (
        f"🎉 **مبروك للفائز بسحب اليانصيب الأسبوعي!** 🎉\n\n"
        f"🏆 **الجائزة الكبرى:** `+{prize:,}` غرام!\n"
        f"👤 **الفائز:** `{winner_id}`\n"
        f"🎫 **رقم التذكرة الفائزة:** `{t_code}`\n\n"
        f"تم السحب عشوائياً بنجاح وإضافة الجائزة إلى رصيد الفائز. تم بدء سحب أسبوعي جديد الآن! 🚀"
    )
    await query.edit_message_text(win_msg, parse_mode="Markdown")

    try:
        await context.bot.send_message(
            chat_id=winner_id,
            text=f"🥳 **مبروك! فزت بالسحب الأسبوعي لليانصيب!**\nتم إضافة **+{prize:,} غرام** إلى حسابك!",
            parse_mode="Markdown"
        )
    except Exception:
        pass
