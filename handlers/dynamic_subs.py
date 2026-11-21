from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select

from config import BOT_NAME, REQUIRED_CHANNEL
from database.db import AsyncSessionLocal
from database.models import MandatoryChannel
from utils.security import is_admin_user
from utils.gatekeeper import get_mandatory_channels_list, invalidate_sub_cache
from utils.telegram_api import check_bot_is_admin
from utils.html_utils import esc


async def get_active_mandatory_channels():
    return await get_mandatory_channels_list()


async def show_mandatory_channels_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_mand_subs_view"):
        return

    query = update.callback_query
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        channels = (await session.execute(select(MandatoryChannel))).scalars().all()

    text = "📢 <b>إدارة قنوات الاشتراك الإجباري:</b>\n\n"
    keyboard = []

    if not channels:
        text += f"لا توجد قنوات خاصة بالقاعدة. القناة الافتراضية من الإعدادات: <code>{esc(REQUIRED_CHANNEL)}</code>\n"
    else:
        for c in channels:
            status_icon = "🟢" if c.is_active else "🔴"
            text += (
                f"{status_icon} <b>{esc(c.title or c.channel_username)}</b>\n"
                f" المعرف: <code>{esc(c.channel_username)}</code> | الرابط: {esc(c.channel_link)}\n"
            )
            keyboard.append(
                [InlineKeyboardButton(f"❌ حذف {c.channel_username}", callback_data=f"del_mand_chan_{c.id}")]
            )

    keyboard.append([InlineKeyboardButton("➕ إضافة قناة اشتراك إجباري", callback_data="add_mand_chan_prompt")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin_main_menu")])

    markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def prompt_add_mandatory_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "add_mand_chan_prompt"):
        return

    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_mand_chan"] = True

    await query.edit_message_text(
        "➕ <b>إضافة قناة اشتراك إجباري جديدة:</b>\n\n"
        "يرجى إرسال تفاصيل القناة بالصيغة التالية:\n"
        "<code>&lt;المعرف&gt; &lt;الرابط&gt; &lt;اسم القناة...&gt;</code>\n\n"
        "مثال:\n"
        f"<code>@ZetaGramChannel https://t.me/ZetaGramChannel قناة {esc(BOT_NAME)} الرسمية</code>",
        parse_mode="HTML",
    )


async def process_add_mandatory_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "process_add_mandatory_channel") or not context.user_data.get("awaiting_mand_chan"):
        return False

    text = update.message.text.strip()
    parts = text.split(maxsplit=2)

    if len(parts) < 2:
        await update.message.reply_text("⚠️ يرجى إدخال المعرف والرابط بشكل صحيح.")
        return True

    username = parts[0]
    link = parts[1]
    title = parts[2] if len(parts) > 2 else username

    is_admin, _ = await check_bot_is_admin(context.bot, username)

    async with AsyncSessionLocal() as session:
        session.add(
            MandatoryChannel(
                channel_username=username,
                channel_link=link,
                title=title,
                is_active=True,
            )
        )
        await session.commit()

    context.user_data.pop("awaiting_mand_chan", None)
    invalidate_sub_cache()

    warn = ""
    if not is_admin:
        warn = "\n\n⚠️ <b>تنبيه:</b> البوت ليس مشرفاً في هذه القناة حالياً؛ يرجى رفعه كمشرف حتى يتم التحقق بدقة."
    await update.message.reply_text(
        f"🎉 تم إضافة القناة الإجبارية <code>{esc(username)}</code> بنجاح!{warn}",
        parse_mode="HTML",
    )
    return True


async def delete_mandatory_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "del_mand_chan"):
        return

    chan_id = int(query.data.replace("del_mand_chan_", ""))
    async with AsyncSessionLocal() as session:
        chan = (
            await session.execute(select(MandatoryChannel).where(MandatoryChannel.id == chan_id))
        ).scalar_one_or_none()
        if chan:
            await session.delete(chan)
            await session.commit()
            invalidate_sub_cache()
            await query.answer("✅ تم حذف القناة بنجاح", show_alert=True)

    await show_mandatory_channels_admin(update, context)
