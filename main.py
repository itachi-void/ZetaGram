import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)

from config import BOT_TOKEN
from database.db import init_db
from handlers.start import start_command, handle_captcha_callback
from handlers.earnings import show_earnings_menu, show_bot_categories_menu, show_reactions_menu, show_rules_screen
from handlers.task_actions import handle_task_list, check_task_callback
from handlers.account import show_account_info
from handlers.promotion import (
    show_promotion_menu, promo_category_selected, promo_account_type_selected,
    promo_audience_selected, process_qty_input, prompt_target_chat_picker, show_my_tasks
)
from handlers.vouchers import show_vouchers_menu
from handlers.bonus import claim_daily_bonus
from handlers.info import (
    show_useful_links, show_instructions, show_bot_public_stats, check_forced_subscription
)
from handlers.language import show_language_menu, set_language_callback
from handlers.spin import spin_wheel_command
from handlers.admin import admin_stats, add_task_admin
from utils.security import rate_limiter
from utils.anti_unsub_checker import run_anti_unsub_checker

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def post_init(application):
    await init_db()
    logging.info("Database initialized successfully.")
    # Start background anti-unsub checker worker
    asyncio.create_task(run_anti_unsub_checker(application.bot))

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not rate_limiter.is_allowed(user_id):
        return

    text = update.message.text

    if text in ["🎁 المكافأة اليومية", "🎁 Daily Bonus"]:
        await claim_daily_bonus(update, context)
    elif text in ["🧑‍💻 الأرباح", "🧑‍💻 Earnings"]:
        await show_earnings_menu(update, context)
    elif text in ["📣 الترويج", "📣 Promotion"]:
        await show_promotion_menu(update, context)
    elif text in ["📱 حسابي", "📱 My Account"]:
        await show_account_info(update, context)
    elif text in ["🏷️ الشيكات", "🏷️ Vouchers"]:
        await show_vouchers_menu(update, context)
    elif text in ["روابط مفيدة", "Useful Links"]:
        await show_useful_links(update, context)
    elif text in ["📋 التعليمات", "📋 Instructions"]:
        await show_instructions(update, context)
    elif text in ["روبوتاتنا والإحصائيات 📊", "Our Bots & Stats 📊"]:
        await show_bot_public_stats(update, context)
    elif text in ["فحص الاشتراك 📣", "Check Subscription 📣"]:
        await check_forced_subscription(update, context)
    elif text in ["🌐 اللغة / Language", "🌐 Language"]:
        await show_language_menu(update, context)



async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not rate_limiter.is_allowed(user_id):
        await update.callback_query.answer("⚠️ يرجى الانتظار قليلاً وعدم الضغط السريع!", show_alert=True)
        return

    query = update.callback_query
    data = query.data

    if data.startswith("set_lang_"):
        await set_language_callback(update, context)
    elif data.startswith("captcha_val_"):
        await handle_captcha_callback(update, context)
    elif data == "earnings_menu":
        await show_earnings_menu(update, context)
    elif data == "tasks_bot_menu":
        await show_bot_categories_menu(update, context)
    elif data == "tasks_reactions_menu":
        await show_reactions_menu(update, context)
    elif data == "tasks_rules":
        await show_rules_screen(update, context)
    elif data == "tasks_premium":
        is_premium = getattr(update.effective_user, "is_premium", False)
        if not is_premium:
            await query.answer("⚡ فئة الشحن متاحة فقط لمستخدمي Telegram Premium", show_alert=True)
        else:
            await handle_task_list(update, context, "premium")
    elif data == "tasks_channel":
        await handle_task_list(update, context, "channel")
    elif data == "tasks_group":
        await handle_task_list(update, context, "group")
    elif data == "tasks_post":
        await handle_task_list(update, context, "post")
    elif data == "tasks_bot_normal":
        await handle_task_list(update, context, "bot_normal")
    elif data == "tasks_bot_webapp":
        await handle_task_list(update, context, "bot_webapp")
    elif data == "tasks_bot_conditions":
        await handle_task_list(update, context, "bot_conditions")
    elif data == "tasks_reaction_random":
        await handle_task_list(update, context, "reaction_random")
    elif data == "tasks_reaction_fixed":
        await handle_task_list(update, context, "reaction_fixed")
    elif data.startswith("promo_cat_"):
        await promo_category_selected(update, context)
    elif data.startswith("account_type_"):
        await promo_account_type_selected(update, context)
    elif data.startswith("audience_"):
        await promo_audience_selected(update, context)
    elif data.startswith("qty_select_"):
        qty = int(data.split("_")[-1])
        await process_qty_input(update, context, qty)
    elif data.startswith("pay_method_"):
        await prompt_target_chat_picker(update, context)
    elif data == "promo_my_tasks":
        await show_my_tasks(update, context)
    elif data == "promo_back_main":
        await show_promotion_menu(update, context)
    elif data.startswith("page_"):
        parts = data.split("_")
        category = parts[1]
        page = int(parts[2])
        await handle_task_list(update, context, category, page)
    elif data.startswith("check_task_"):
        await check_task_callback(update, context)
    elif data == "close_menu":
        await query.answer()
        await query.delete_message()
    elif data == "ignore":
        await query.answer()

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ Warning: Please set a valid BOT_TOKEN in config.py or .env file before running!")
    
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("bonus", claim_daily_bonus))
    app.add_handler(CommandHandler("spin", spin_wheel_command))
    app.add_handler(CommandHandler("language", show_language_menu))
    app.add_handler(CommandHandler("admin", admin_stats))
    app.add_handler(CommandHandler("addtask", add_task_admin))

    # Text message handler (Main Reply Keyboard)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    # Callback Query Handler (Inline Keyboards)
    app.add_handler(CallbackQueryHandler(handle_callbacks))

    print("🚀 Bot is launching...")
    app.run_polling()

if __name__ == "__main__":
    main()

