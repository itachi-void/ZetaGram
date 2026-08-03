import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)

from config import BOT_TOKEN
from database.db import init_db, AsyncSessionLocal
from database.models import User
from handlers.start import start_command, handle_captcha_callback
from handlers.earnings import show_earnings_menu, show_bot_categories_menu, show_reactions_menu, show_rules_screen
from handlers.task_actions import handle_task_list, check_task_callback
from handlers.account import show_account_info
from handlers.promotion import (
    show_promotion_menu, promo_category_selected, promo_account_type_selected,
    promo_audience_selected, process_qty_input, prompt_target_chat_picker, show_my_tasks
)
from handlers.vouchers import (
    show_vouchers_menu, prompt_create_voucher, prompt_redeem_voucher,
    handle_create_voucher_command, process_create_voucher_input, redeem_voucher
)
from handlers.transfer import show_transfer_menu, handle_transfer_command
from handlers.levels import show_levels_menu, claim_milestone_callback
from handlers.history import show_transaction_history
from handlers.dynamic_subs import (
    show_mandatory_channels_admin, prompt_add_mandatory_channel,
    process_add_mandatory_channel, delete_mandatory_channel_callback
)
from handlers.proof_review import (
    process_proof_photo, handle_creator_proof_action,
    handle_worker_dispute_callbacks, handle_admin_dispute_action
)
from handlers.vault import (
    show_vault_menu, prompt_vault_deposit, process_vault_deposit_input,
    show_my_vault_deposits, handle_withdraw_vault
)
from handlers.raffle import (
    show_raffle_menu, handle_buy_raffle_tickets, show_my_raffle_tickets,
    handle_admin_draw_raffle
)
from handlers.bonus import claim_daily_bonus
from handlers.info import (
    show_useful_links, show_instructions, show_bot_public_stats, check_forced_subscription
)
from handlers.language import show_language_menu, set_language_callback
from handlers.spin import spin_wheel_command
from handlers.referrals import show_referral_menu, show_referrals_list
from handlers.admin import (
    show_admin_panel, admin_stats_view, admin_backup_db, admin_balance_help,
    handle_setbalance_command, admin_ban_help, handle_ban_command, handle_unban_command,
    admin_tasks_manage, handle_admin_task_action, admin_broadcast_help, handle_broadcast_command,
    add_task_admin
)
from utils.security import rate_limiter
from utils.anti_unsub_checker import run_anti_unsub_checker
from utils.scheduled_tasks import (
    run_daily_backup_worker, run_retention_reminders_worker, run_daily_report_worker
)
from utils.i18n import TEXTS
from sqlalchemy import select

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def post_init(application):
    await init_db()
    logging.info("Database initialized successfully.")
    # Start background async workers
    asyncio.create_task(run_anti_unsub_checker(application.bot))
    asyncio.create_task(run_daily_backup_worker(application.bot))
    asyncio.create_task(run_retention_reminders_worker(application.bot))
    asyncio.create_task(run_daily_report_worker(application.bot))

async def update_user_activity(user_id: int):
    try:
        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
            if user:
                user.last_active_at = datetime.utcnow()
                await session.commit()
    except Exception:
        pass

def find_button_key(text: str) -> str | None:
    for lang_code, text_dict in TEXTS.items():
        for key, val in text_dict.items():
            if key.startswith("btn_") and val == text:
                return key
    return None

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not rate_limiter.is_allowed(user_id):
        return

    await update_user_activity(user_id)

    # Check state-based text handlers
    if context.user_data.get("awaiting_mand_chan"):
        if await process_add_mandatory_channel(update, context):
            return

    if context.user_data.get("awaiting_create_voucher"):
        if await process_create_voucher_input(update, context):
            return

    if context.user_data.get("awaiting_voucher_code"):
        context.user_data.pop("awaiting_voucher_code", None)
        await redeem_voucher(update, context, update.message.text.strip())
        return

    if context.user_data.get("awaiting_vault_amount"):
        if await process_vault_deposit_input(update, context):
            return

    text = update.message.text
    key = find_button_key(text)

    if key == "btn_referrals":
        await show_referral_menu(update, context)
    elif key == "btn_bonus":
        await claim_daily_bonus(update, context)
    elif key == "btn_earnings":
        await show_earnings_menu(update, context)
    elif key == "btn_promotion":
        await show_promotion_menu(update, context)
    elif key == "btn_account":
        await show_account_info(update, context)
    elif key == "btn_vouchers":
        await show_vouchers_menu(update, context)
    elif key == "btn_useful_links":
        await show_useful_links(update, context)
    elif key == "btn_instructions":
        await show_instructions(update, context)
    elif key == "btn_stats":
        await show_bot_public_stats(update, context)
    elif key == "btn_check_sub":
        await check_forced_subscription(update, context)
    elif key == "btn_language":
        await show_language_menu(update, context)

async def handle_photo_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not rate_limiter.is_allowed(user_id):
        return

    await update_user_activity(user_id)
    await process_proof_photo(update, context)

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not rate_limiter.is_allowed(user_id):
        await update.callback_query.answer("⚠️ يرجى الانتظار قليلاً وعدم الضغط السريع!", show_alert=True)
        return

    await update_user_activity(user_id)

    query = update.callback_query
    data = query.data

    # Main & Navigation Callbacks
    if data == "my_referrals_list":
        await show_referrals_list(update, context)
    elif data == "show_referral_main":
        await show_referral_menu(update, context)
    elif data.startswith("set_lang_"):
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
    elif data in ["tasks_channel", "tasks_group", "tasks_post", "tasks_bot_normal", "tasks_bot_webapp", "tasks_bot_conditions", "tasks_reaction_random", "tasks_reaction_fixed"]:
        cat = data.replace("tasks_", "")
        await handle_task_list(update, context, cat)
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

    # Vouchers & Account Features
    elif data == "my_vouchers":
        await show_vouchers_menu(update, context)
    elif data == "prompt_create_voucher":
        await prompt_create_voucher(update, context)
    elif data == "prompt_redeem_voucher":
        await prompt_redeem_voucher(update, context)
    elif data == "show_levels":
        await show_levels_menu(update, context)
    elif data.startswith("claim_m_"):
        await claim_milestone_callback(update, context)
    elif data == "show_tx_history":
        await show_transaction_history(update, context)
    elif data == "show_transfer_menu":
        await show_transfer_menu(update, context)

    # Vault Callbacks
    elif data == "show_vault_menu":
        await show_vault_menu(update, context)
    elif data.startswith("vault_deposit_"):
        await prompt_vault_deposit(update, context)
    elif data == "my_vault_deposits":
        await show_my_vault_deposits(update, context)
    elif data.startswith("withdraw_vault_"):
        await handle_withdraw_vault(update, context)

    # Raffle Callbacks
    elif data == "show_raffle_menu":
        await show_raffle_menu(update, context)
    elif data.startswith("buy_raffle_"):
        await handle_buy_raffle_tickets(update, context)
    elif data == "my_raffle_tickets":
        await show_my_raffle_tickets(update, context)
    elif data == "admin_draw_raffle_now":
        await handle_admin_draw_raffle(update, context)

    # Proof Review & Disputes Callbacks
    elif data.startswith("proof_"):
        await handle_creator_proof_action(update, context)
    elif data.startswith("resubmit_proof_") or data.startswith("file_dispute_"):
        await handle_worker_dispute_callbacks(update, context)
    elif data.startswith("admin_disp_"):
        await handle_admin_dispute_action(update, context)

    # Admin Panel Callbacks
    elif data == "admin_main_menu":
        await show_admin_panel(update, context)
    elif data == "admin_stats_view":
        await admin_stats_view(update, context)
    elif data == "admin_backup_db":
        await admin_backup_db(update, context)
    elif data == "admin_balance_help":
        await admin_balance_help(update, context)
    elif data == "admin_ban_help":
        await admin_ban_help(update, context)
    elif data == "admin_tasks_manage":
        await admin_tasks_manage(update, context)
    elif data.startswith("admin_deltask_") or data.startswith("admin_toggletask_"):
        await handle_admin_task_action(update, context)
    elif data == "admin_broadcast_help":
        await admin_broadcast_help(update, context)
    elif data == "admin_mand_subs_view":
        await show_mandatory_channels_admin(update, context)
    elif data == "add_mand_chan_prompt":
        await prompt_add_mandatory_channel(update, context)
    elif data.startswith("del_mand_chan_"):
        await delete_mandatory_channel_callback(update, context)

    # Close & Ignore
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
    app.add_handler(CommandHandler("admin", show_admin_panel))
    app.add_handler(CommandHandler("addtask", add_task_admin))
    app.add_handler(CommandHandler("transfer", handle_transfer_command))
    app.add_handler(CommandHandler("createvoucher", handle_create_voucher_command))
    app.add_handler(CommandHandler("setbalance", handle_setbalance_command))
    app.add_handler(CommandHandler("ban", handle_ban_command))
    app.add_handler(CommandHandler("unban", handle_unban_command))
    app.add_handler(CommandHandler("broadcast", handle_broadcast_command))
    app.add_handler(CommandHandler("vault", show_vault_menu))
    app.add_handler(CommandHandler("raffle", show_raffle_menu))

    # Text message handler (Main Reply Keyboard + text inputs)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    # Photo message handler (Proof screenshots)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_messages))

    # Callback Query Handler (Inline Keyboards)
    app.add_handler(CallbackQueryHandler(handle_callbacks))

    print("🚀 Bot is launching...")
    app.run_polling()

if __name__ == "__main__":
    main()
