from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select

from database.db import AsyncSessionLocal
from database.models import User
from handlers.start import start_command_after_language, build_language_keyboard
from utils.i18n import get_text


async def show_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        lang = user.language if user else "ar"

    text = get_text(lang, "lang_select_title")
    reply_markup = build_language_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=reply_markup
        )


async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    new_lang = query.data.replace("set_lang_", "")

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()
        if user:
            user.language = new_lang
            await session.commit()

    try:
        await query.delete_message()
    except Exception:
        pass
    await start_command_after_language(update, context, new_lang)
