from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import MandatoryChannel
from config import ADMIN_IDS, REQUIRED_CHANNEL, REQUIRED_CHANNEL_LINK

async def get_active_mandatory_channels():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(MandatoryChannel).where(MandatoryChannel.is_active == True))
        channels = result.scalars().all()
        
    if not channels:
        # Fallback to config default channel if DB is empty
        return [{
            "id": 0,
            "channel_username": REQUIRED_CHANNEL,
            "channel_link": REQUIRED_CHANNEL_LINK,
            "title": "القناة الرسمية"
        }]
    return [
        {
            "id": c.id,
            "channel_username": c.channel_username,
            "channel_link": c.channel_link,
            "title": c.title or c.channel_username
        }
        for c in channels
    ]

async def show_mandatory_channels_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    query = update.callback_query
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(MandatoryChannel))
        channels = result.scalars().all()

    text = "📢 **إدارة قنوات الاشتراك الإجباري:**\n\n"
    keyboard = []

    if not channels:
        text += f"لا توجد قنوات خاصة بالـ DB. القناة الافتراضية حالياً من config: `{REQUIRED_CHANNEL}`\n"
    else:
        for c in channels:
            status_icon = "🟢" if c.is_active else "🔴"
            text += f"{status_icon} **{c.title or c.channel_username}**\n المعرف: `{c.channel_username}` | الرابط: {c.channel_link}\n"
            keyboard.append([
                InlineKeyboardButton(f"❌ حذف {c.channel_username}", callback_data=f"del_mand_chan_{c.id}")
            ])

    keyboard.append([InlineKeyboardButton("➕ إضافة قناة اشتراك إجباري", callback_data="add_mand_chan_prompt")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin_main_menu")])

    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

async def prompt_add_mandatory_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_mand_chan"] = True

    await query.edit_message_text(
        "➕ **إضافة قناة اشتراك إجباري جديدة:**\n\n"
        "يرجى إرسال تفاصيل القناة بالصيغة التالية:\n"
        "`<المعرف> <الرابط> <اسم القناة...>`\n\n"
        "مثال:\n"
        "`@GramPulseChannel https://t.me/GramPulseChannel قناة الجرام بولس الرسمية`",
        parse_mode="Markdown"
    )

async def process_add_mandatory_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS or not context.user_data.get("awaiting_mand_chan"):
        return False

    text = update.message.text.strip()
    parts = text.split(maxsplit=2)

    if len(parts) < 2:
        await update.message.reply_text("⚠️ يرجى إدخال المعرف والرابط بشكل صحيح.")
        return True

    username = parts[0]
    link = parts[1]
    title = parts[2] if len(parts) > 2 else username

    async with AsyncSessionLocal() as session:
        new_chan = MandatoryChannel(
            channel_username=username,
            channel_link=link,
            title=title,
            is_active=True
        )
        session.add(new_chan)
        await session.commit()

    context.user_data["awaiting_mand_chan"] = False
    await update.message.reply_text(f"🎉 تم إضافة القناة الإجبارية `{username}` بنجاح!", parse_mode="Markdown")
    return True

async def delete_mandatory_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    chan_id = int(query.data.replace("del_mand_chan_", ""))
    async with AsyncSessionLocal() as session:
        chan = (await session.execute(select(MandatoryChannel).where(MandatoryChannel.id == chan_id))).scalar_one_or_none()
        if chan:
            await session.delete(chan)
            await session.commit()
            await query.answer("✅ تم حذف القناة بنجاح", show_alert=True)

    await show_mandatory_channels_admin(update, context)
