import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import User, Voucher, VoucherRedemption

async def show_vouchers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🏷️ **قسم الشيكات والكوبونات:**\n\n"
        "يمكنك استبدال الشيكات التي تملكها أو إنشاء شيكات هدايا لأصدقائك من رصيدك."
    )
    keyboard = [
        [InlineKeyboardButton("🎁 استبدال شيك", callback_data="redeem_voucher_prompt")],
        [InlineKeyboardButton("➕ إنشاء شيك جديد", callback_data="create_voucher_prompt")]
    ]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def redeem_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    user_id = update.effective_user.id
    code = code.strip().upper()

    async with AsyncSessionLocal() as session:
        voucher = (await session.execute(select(Voucher).where(Voucher.code == code))).scalar_one_or_none()

        if not voucher:
            await update.message.reply_text("❌ رمز الشيك غير صحيح أو ملغى.")
            return

        if voucher.used_count >= voucher.max_uses:
            await update.message.reply_text("⚠️ هذا الشيك تم استخدامه بالكامل بالحد الأقصى.")
            return

        # Check if user already used this voucher
        already_used = (await session.execute(
            select(VoucherRedemption).where(VoucherRedemption.voucher_id == voucher.id, VoucherRedemption.user_id == user_id)
        )).scalar_one_or_none()

        if already_used:
            await update.message.reply_text("⚠️ لقد قمت باستبدال هذا الشيك مسبقاً!")
            return

        # Redeem voucher
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if user:
            user.balance += voucher.amount

        voucher.used_count += 1
        redemption = VoucherRedemption(voucher_id=voucher.id, user_id=user_id)
        session.add(redemption)
        await session.commit()

        await update.message.reply_text(f"🎉 تم شحن رصيدك بنجاح بمقدار +{voucher.amount:,} غرام!")
