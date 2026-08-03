import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import User, Voucher, VoucherRedemption, Transaction
from utils.security import user_lock_manager, sanitize_amount, send_security_alert

def generate_voucher_code(length=8) -> str:
    chars = string.ascii_uppercase + string.digits
    rand_str = "".join(random.choices(chars, k=length))
    return f"GRAM-{rand_str[:4]}-{rand_str[4:]}"

async def show_vouchers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    text = (
        "🏷️ **قسم الشيكات والكوبونات:**\n\n"
        "يمكنك استبدال الشيكات التي تملكها أو إنشاء شيكات هدايا لأصدقائك أو لقناتك خصماً من رصيدك.\n\n"
        "يمكنك أيضاً استخدام التعليمة السريعة للإنشاء:\n"
        "`/createvoucher <المبلغ> <عدد_الاستخدامات>`"
    )
    keyboard = [
        [
            InlineKeyboardButton("🎁 استبدال شيك", callback_data="prompt_redeem_voucher"),
            InlineKeyboardButton("➕ إنشاء شيك جديد", callback_data="prompt_create_voucher")
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def prompt_redeem_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_voucher_code"] = True
    await query.edit_message_text(
        "🎁 **استبدال شيك:**\n\n"
        "يرجى إرسال رمز الشيك في الشات مباشرة (مثال: `GRAM-ABCD-1234`).",
        parse_mode="Markdown"
    )

async def prompt_create_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_create_voucher"] = True
    await query.edit_message_text(
        "➕ **إنشاء شيك جديد:**\n\n"
        "يرجى إرسال المبلغ وعدد مرات الاستخدام مفصولة بمسافة:\n"
        "`<المبلغ_لكل_استخدام> <عدد_المستخدمين>`\n\n"
        "مثال: `500 10` (إنشاء شيك بـ 500 غرام لـ 10 أعضاء).",
        parse_mode="Markdown"
    )

async def handle_create_voucher_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "⚠️ **الاستخدام الخاطئ!**\n"
            "الصيغة:\n"
            "`/createvoucher <المبلغ> [عدد_الاستخدامات]`\n\n"
            "مثال: `/createvoucher 500 5`",
            parse_mode="Markdown"
        )
        return

    ok_amt, amount, err_amt = sanitize_amount(args[0], min_val=1)
    if not ok_amt:
        await update.message.reply_text(err_amt)
        return

    max_uses = 1
    if len(args) > 1:
        ok_u, max_uses, err_u = sanitize_amount(args[1], min_val=1, max_val=10_000)
        if not ok_u:
            await update.message.reply_text(err_u)
            return

    await create_and_send_voucher(update, context, amount, max_uses)

async def process_create_voucher_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()

    if len(parts) < 1:
        await update.message.reply_text("❌ يرجى إدخال المبلغ.")
        return True

    ok_amt, amount, err_amt = sanitize_amount(parts[0], min_val=1)
    if not ok_amt:
        await update.message.reply_text(err_amt)
        return True

    max_uses = 1
    if len(parts) > 1:
        ok_u, max_uses, err_u = sanitize_amount(parts[1], min_val=1, max_val=10_000)
        if not ok_u:
            await update.message.reply_text(err_u)
            return True

    context.user_data["awaiting_create_voucher"] = False
    await create_and_send_voucher(update, context, amount, max_uses)
    return True

async def create_and_send_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int, max_uses: int):
    user_id = update.effective_user.id

    async with user_lock_manager.get_lock(user_id):
        total_cost = amount * max_uses

        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
            if not user or user.balance < total_cost:
                await update.message.reply_text(
                    f"❌ رصيدك غير كافٍ!\n"
                    f"المبلغ الإجمالي المطلوب: {total_cost:,} غرام ({amount:,} × {max_uses})\n"
                    f"رصيدك الحالي: {user.balance if user else 0:,} غرام"
                )
                return

            user.balance -= total_cost
            code = generate_voucher_code()

            voucher = Voucher(
                code=code,
                amount=amount,
                max_uses=max_uses,
                used_count=0,
                created_by=user_id
            )
            session.add(voucher)

            tx = Transaction(
                user_id=user_id,
                trans_type="voucher_create",
                amount=-total_cost,
                description=f"إنشاء شيك {code} بقيمة {amount} لـ {max_uses} مستخدمين"
            )
            session.add(tx)

            await session.commit()

    bot_info = await context.bot.get_me()
    v_link = f"https://t.me/{bot_info.username}?start=v_{code}"

    res_text = (
        f"🎉 **تم إنشاء الشيك بنجاح!**\n\n"
        f"🏷️ **رمز الشيك:** `{code}`\n"
        f"💰 **قيمة الاستخدام:** {amount:,} غرام\n"
        f"👥 **الحد الأقصى للاستخدام:** {max_uses} أعضاء\n"
        f"💳 **التكلفة المخصومة:** {total_cost:,} غرام\n\n"
        f"🔗 **رابط الشيك المباشر:**\n`{v_link}`"
    )
    await update.message.reply_text(res_text, parse_mode="Markdown")

async def redeem_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    user_id = update.effective_user.id
    code = code.strip().upper()

    if code.startswith("V_"):
        code = code[2:]

    now = datetime.utcnow()

    async with user_lock_manager.get_lock(user_id):
        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
            if not user:
                return

            # Check voucher ban status
            if user.voucher_banned_until and now < user.voucher_banned_until:
                rem = user.voucher_banned_until - now
                mins = max(1, int(rem.total_seconds() / 60))
                await update.message.reply_text(
                    f"⛔ **تم قفل إدخال الشيكات لمسابقة التخمين!**\n"
                    f"يرجى الانتظار **{mins} دقيقة** قبل المحاولة مجدداً.",
                    parse_mode="Markdown"
                )
                return

            voucher = (await session.execute(select(Voucher).where(Voucher.code == code))).scalar_one_or_none()

            if not voucher:
                user.failed_voucher_attempts = (user.failed_voucher_attempts or 0) + 1
                if user.failed_voucher_attempts >= 5:
                    user.voucher_banned_until = now + timedelta(minutes=15)
                    user.failed_voucher_attempts = 0
                    await session.commit()

                    await send_security_alert(
                        context.bot,
                        f"⚠️ **تخمين متكرر للشيكات (Anti-Bruteforce)!**\n"
                        f"👤 المستخدم: `{user_id}` قام بإدخال كود شيك خاطئ 5 مرات متتالية.\n"
                        f"🔒 تم قفل استبدال الشيكات له لمدة 15 دقيقة تلقائياً."
                    )
                    await update.message.reply_text(
                        "⛔ **تم حظر استخدام الشيكات لحسابك لمدة 15 دقيقة بسبب تكرار إدخال أكواد خاطئة!**",
                        parse_mode="Markdown"
                    )
                    return
                else:
                    await session.commit()
                    await update.message.reply_text(
                        f"❌ رمز الشيك غير صحيح أو ملغى. (محاولة {user.failed_voucher_attempts}/5)"
                    )
                    return

            if voucher.used_count >= voucher.max_uses:
                await update.message.reply_text("⚠️ هذا الشيك تم استخدامه بالكامل بالحد الأقصى.")
                return

            already_used = (await session.execute(
                select(VoucherRedemption).where(VoucherRedemption.voucher_id == voucher.id, VoucherRedemption.user_id == user_id)
            )).scalar_one_or_none()

            if already_used:
                await update.message.reply_text("⚠️ لقد قمت باستبدال هذا الشيك مسبقاً!")
                return

            # Success! Reset failed attempts
            user.failed_voucher_attempts = 0
            user.balance += voucher.amount

            voucher.used_count += 1
            redemption = VoucherRedemption(voucher_id=voucher.id, user_id=user_id)
            session.add(redemption)

            tx = Transaction(
                user_id=user_id,
                trans_type="voucher_claim",
                amount=voucher.amount,
                description=f"استبدال شيك {code}"
            )
            session.add(tx)

            await session.commit()

            await update.message.reply_text(f"🎉 تم شحن رصيدك بنجاح بمقدار **+{voucher.amount:,} غرام**!", parse_mode="Markdown")
