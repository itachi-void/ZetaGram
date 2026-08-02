from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import User
from config import REQUIRED_CHANNEL, REQUIRED_CHANNEL_LINK
from utils.security import generate_math_captcha
from utils.i18n import get_text, LANGUAGES

def get_main_keyboard(lang: str = "ar"):
    return ReplyKeyboardMarkup(
        [
            ["👥 نظام الدعوات", get_text(lang, "btn_bonus")],
            [get_text(lang, "btn_earnings"), get_text(lang, "btn_promotion")],
            [get_text(lang, "btn_account"), get_text(lang, "btn_vouchers")],
            [get_text(lang, "btn_stats"), get_text(lang, "btn_check_sub")],
            [get_text(lang, "btn_useful_links"), get_text(lang, "btn_language")]
        ],
        resize_keyboard=True
    )


def build_language_keyboard():
    keyboard = []
    lang_items = list(LANGUAGES.items())
    
    for i in range(0, len(lang_items), 2):
        row = []
        code1, name1 = lang_items[i]
        row.append(InlineKeyboardButton(name1, callback_data=f"set_lang_{code1}"))
        if i + 1 < len(lang_items):
            code2, name2 = lang_items[i + 1]
            row.append(InlineKeyboardButton(name2, callback_data=f"set_lang_{code2}"))
        keyboard.append(row)
        
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    referred_by = int(args[0]) if args and args[0].isdigit() else None

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user.id))
        db_user = result.scalar_one_or_none()

        if not db_user:
            if referred_by == user.id:
                referred_by = None

            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                referred_by=referred_by,
                is_captcha_verified=False
            )
            session.add(db_user)
            await session.commit()

            # For first time users: prompt for language selection first!
            text = (
                "🌐 **يرجى اختيار لغتك المفضلّة للبدء:**\n"
                "🌐 **Please select your preferred language to start:**"
            )
            await update.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=build_language_keyboard()
            )
            return

        lang = db_user.language or "ar"
        await start_command_after_language(update, context, lang)

async def start_command_after_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name

    async with AsyncSessionLocal() as session:
        db_user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()

        # Check Captcha if not verified
        if db_user and not db_user.is_captcha_verified:
            text, answer, options = generate_math_captcha()
            context.user_data["captcha_answer"] = answer

            keyboard = []
            row = []
            for opt in options:
                row.append(InlineKeyboardButton(str(opt), callback_data=f"captcha_val_{opt}"))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)

            if update.callback_query:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return

    welcome_text = get_text(lang, "welcome", name=first_name)

    if update.callback_query:
        await context.bot.send_message(
            chat_id=user_id,
            text=welcome_text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=get_main_keyboard(lang)
        )
    else:
        await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=get_main_keyboard(lang)
        )

async def handle_captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    selected_val = int(query.data.split("_")[-1])
    correct_ans = context.user_data.get("captcha_answer")

    if selected_val != correct_ans:
        await query.answer("❌ إجابة خاطئة! حاول مرة أخرى.", show_alert=True)
        text, answer, options = generate_math_captcha()
        context.user_data["captcha_answer"] = answer
        keyboard = []
        row = []
        for opt in options:
            row.append(InlineKeyboardButton(str(opt), callback_data=f"captcha_val_{opt}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Correct Captcha Answer!
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if user:
            user.is_captcha_verified = True
            lang = user.language or "ar"
            await session.commit()

    await query.answer("🎉 تم اجتياز اختبار الكابتشا بنجاح!", show_alert=True)
    await query.delete_message()
    
    welcome_text = get_text(lang, "welcome", name=update.effective_user.first_name)
    await context.bot.send_message(
        chat_id=user_id,
        text=welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(lang)
    )
