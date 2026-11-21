import os
import logging
import asyncio
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageReactionHandler,
    PicklePersistence,
    filters,
    ContextTypes,
)
from sqlalchemy import select

from config import (
    BOT_TOKEN,
    PERSISTENCE_FILE,
    WEBHOOK_URL,
    WEBHOOK_PORT,
    WEBHOOK_SECRET_TOKEN,
)
from database.db import init_db, AsyncSessionLocal
from database.models import User
from handlers.start import (
    start_command,
    handle_captcha_callback,
    handle_captcha_refresh,
)
from handlers.earnings import (
    show_earnings_menu,
    show_bot_categories_menu,
    show_reactions_menu,
    show_rules_screen,
)
from handlers.task_actions import (
    handle_task_list,
    check_task_callback,
    start_post_callback,
    claim_post_callback,
    open_bot_task_callback,
    prompt_bot_forward_callback,
    handle_bot_forward_message,
    open_proof_task_callback,
    submit_proof_callback,
    skip_task_callback,
    report_task_callback,
    report_issue_callback,
    process_report_reason_input,
)
from handlers.reactions import handle_message_reaction_update
from handlers.account import show_account_info
from handlers.promotion import (
    show_promotion_menu,
    promo_category_selected,
    promo_subtype_selected,
    promo_account_type_selected,
    promo_audience_selected,
    toggle_promo_language,
    audience_done_callback,
    process_promo_price_input,
    process_promo_qty_text_input,
    process_qty_input,
    prompt_target_chat_picker,
    prompt_promo_code_callback,
    clear_promo_code_callback,
    process_promo_code_input,
    handle_stars_fee_free_payment,
    handle_pre_checkout,
    handle_successful_payment,
    handle_chat_shared_message,
    process_promo_target_input,
    promo_confirm_create_callback,
    show_promo_auto_settings,
    show_my_tasks,
    mytask_view_callback,
    mytask_action_callback,
)
from handlers.vouchers import (
    show_vouchers_menu,
    prompt_create_voucher,
    prompt_redeem_voucher,
    handle_create_voucher_command,
    process_create_voucher_input,
    redeem_voucher,
    show_my_vouchers,
    cancel_voucher_callback,
)
from handlers.transfer import (
    show_transfer_menu,
    prompt_transfer_callback,
    process_transfer_input,
    handle_transfer_command,
)
from handlers.levels import show_levels_menu, claim_milestone_callback
from handlers.history import show_transaction_history
from handlers.dynamic_subs import (
    show_mandatory_channels_admin,
    prompt_add_mandatory_channel,
    process_add_mandatory_channel,
    delete_mandatory_channel_callback,
)
from handlers.proof_review import (
    process_proof_photo,
    process_custom_reject_reason,
    handle_creator_proof_action,
    handle_worker_dispute_callbacks,
    handle_admin_dispute_action,
)
from handlers.vault import (
    show_vault_menu,
    prompt_vault_deposit,
    process_vault_deposit_input,
    show_my_vault_deposits,
    handle_withdraw_vault,
)
from handlers.raffle import (
    show_raffle_menu,
    handle_buy_raffle_tickets,
    show_my_raffle_tickets,
    handle_admin_draw_raffle,
)
from handlers.bonus import claim_daily_bonus
from handlers.info import (
    show_useful_links,
    show_instructions,
    show_bot_public_stats,
    check_forced_subscription,
    recheck_forced_sub_callback,
)
from handlers.language import show_language_menu, set_language_callback
from handlers.spin import spin_wheel_command
from handlers.leaderboard import show_leaderboard
from handlers.settings import show_user_settings, toggle_notifications_callback
from handlers.referrals import show_referral_menu, show_referrals_list
from handlers.admin import (
    show_admin_panel,
    admin_stats_view,
    admin_backup_db,
    admin_balance_help,
    handle_setbalance_command,
    handle_userinfo_command,
    admin_ban_help,
    handle_ban_command,
    handle_unban_command,
    admin_tasks_manage,
    handle_admin_task_action,
    admin_tickets_manage,
    admin_view_ticket_callback,
    admin_reports_manage,
    handle_admin_report_action,
    admin_broadcast_help,
    handle_broadcast_command,
    add_task_admin,
    admin_promos_menu,
    handle_add_promo_command,
    handle_flash_event_command,
    handle_stop_flash_command,
    handle_admin_promo_callbacks,
)
from utils.gatekeeper import enforce_user_access, clear_user_input_states
from utils.anti_unsub_checker import run_anti_unsub_checker
from utils.scheduled_tasks import (
    run_daily_backup_worker,
    run_retention_reminders_worker,
    run_daily_report_worker,
    run_proof_auto_approve_worker,
    run_weekly_leaderboard_worker,
)
from utils.i18n import TEXTS, get_text, get_user_lang

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Module-level list so PicklePersistence never attempts to pickle asyncio.Task objects
_bg_tasks: list[asyncio.Task] = []


async def post_init(application):
    await init_db()
    logging.info("Database initialized successfully (WAL mode).")
    _bg_tasks.clear()
    _bg_tasks.extend(
        [
            asyncio.create_task(run_anti_unsub_checker(application.bot)),
            asyncio.create_task(run_daily_backup_worker(application.bot)),
            asyncio.create_task(run_retention_reminders_worker(application.bot)),
            asyncio.create_task(run_daily_report_worker(application.bot)),
            asyncio.create_task(run_proof_auto_approve_worker(application.bot)),
            asyncio.create_task(run_weekly_leaderboard_worker(application.bot)),
        ]
    )


async def post_shutdown(application):
    for task in _bg_tasks:
        task.cancel()
    if _bg_tasks:
        await asyncio.gather(*_bg_tasks, return_exceptions=True)
    _bg_tasks.clear()


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    if isinstance(err, BadRequest) and "Message is not modified" in str(err):
        return
    logging.exception("Unhandled exception while processing update %s", update, exc_info=err)


def find_button_key(text: str) -> str | None:
    if not text:
        return None
    for _, text_dict in TEXTS.items():
        for key, val in text_dict.items():
            if key.startswith("btn_") and val == text:
                return key
    return None


async def handle_forwarded_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await handle_bot_forward_message(update, context):
        return
    if update.message and update.message.photo:
        await handle_photo_messages(update, context)
    elif update.message and update.message.text:
        await handle_text_messages(update, context)


async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    key = find_button_key(text)

    if key is not None:
        clear_user_input_states(context)
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
        elif key == "btn_leaderboard":
            await show_leaderboard(update, context)
        elif key == "btn_settings":
            await show_user_settings(update, context)
        return

    # State-based interactive text inputs
    if context.user_data.get("awaiting_mand_chan"):
        if await process_add_mandatory_channel(update, context):
            return

    if context.user_data.get("awaiting_create_voucher"):
        if await process_create_voucher_input(update, context):
            return

    if context.user_data.get("awaiting_voucher_code"):
        context.user_data.pop("awaiting_voucher_code", None)
        await redeem_voucher(update, context, text.strip())
        return

    if context.user_data.get("awaiting_vault_amount"):
        if await process_vault_deposit_input(update, context):
            return

    if context.user_data.get("awaiting_transfer_input"):
        if await process_transfer_input(update, context):
            return

    if context.user_data.get("awaiting_promo_price"):
        if await process_promo_price_input(update, context):
            return

    if context.user_data.get("awaiting_promo_qty"):
        if await process_promo_qty_text_input(update, context):
            return

    if context.user_data.get("awaiting_promo_code"):
        if await process_promo_code_input(update, context):
            return

    if context.user_data.get("awaiting_promo_target"):
        if await process_promo_target_input(update, context):
            return

    if context.user_data.get("awaiting_report_task_id") is not None:
        if await process_report_reason_input(update, context):
            return

    if context.user_data.get("awaiting_reject_reason_ut_id"):
        if await process_custom_reject_reason(update, context):
            return

    await enforce_user_access(update, context)


async def handle_photo_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_proof_photo(update, context)


async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # Auth/Pre-verification callbacks (exempt from full gatekeeper lock)
    if data.startswith("set_lang_"):
        await set_language_callback(update, context)
        return
    if data == "captcha_refresh":
        await handle_captcha_refresh(update, context)
        return
    if data.startswith("captcha_val_"):
        await handle_captcha_callback(update, context)
        return
    if data == "recheck_forced_sub":
        await recheck_forced_sub_callback(update, context)
        return
    if data == "close_menu":
        await query.answer()
        try:
            await query.delete_message()
        except Exception:
            pass
        return
    if data == "ignore":
        await query.answer()
        return

    # Referrals & Account
    if data == "my_referrals_list":
        await show_referrals_list(update, context)
    elif data == "show_referral_main":
        await show_referral_menu(update, context)
    elif data == "show_leaderboard":
        await show_leaderboard(update, context)
    elif data == "lb_tab_tasks":
        await show_leaderboard(update, context, tab="tasks")
    elif data == "lb_tab_refs":
        await show_leaderboard(update, context, tab="refs")
    elif data == "show_user_settings":
        await show_user_settings(update, context)
    elif data == "toggle_notifs":
        await toggle_notifications_callback(update, context)
    elif data == "open_lang_menu":
        await show_language_menu(update, context)

    # Earnings & Tasks
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
            lang = "ar"
            async with AsyncSessionLocal() as s:
                u = (
                    await s.execute(select(User).where(User.telegram_id == update.effective_user.id))
                ).scalar_one_or_none()
                lang = get_user_lang(u)
            await query.answer(get_text(lang, "premium_only_alert"), show_alert=True)
        else:
            await handle_task_list(update, context, "premium")
    elif data in (
        "tasks_channel",
        "tasks_group",
        "tasks_post",
        "tasks_bot_normal",
        "tasks_bot_webapp",
        "tasks_bot_conditions",
        "tasks_reaction_random",
        "tasks_reaction_fixed",
    ):
        cat = data.replace("tasks_", "")
        await handle_task_list(update, context, cat)
    elif data.startswith("page_"):
        body = data[5:]
        category, page_str = body.rsplit("_", 1)
        await handle_task_list(update, context, category, int(page_str))
    elif data.startswith("check_task_"):
        await check_task_callback(update, context)
    elif data.startswith("start_post_"):
        await start_post_callback(update, context)
    elif data.startswith("claim_post_"):
        await claim_post_callback(update, context)
    elif data.startswith("open_bot_task_"):
        await open_bot_task_callback(update, context)
    elif data.startswith("prompt_bot_fwd_"):
        await prompt_bot_forward_callback(update, context)
    elif data.startswith("open_proof_task_"):
        await open_proof_task_callback(update, context)
    elif data.startswith("submit_proof_"):
        await submit_proof_callback(update, context)
    elif data.startswith("skip_task_"):
        await skip_task_callback(update, context)
    elif data.startswith("report_task_"):
        await report_task_callback(update, context)
    elif data == "report_issue":
        await report_issue_callback(update, context)

    # Promotion Wizard & Campaign Dashboard
    elif data.startswith("promo_cat_"):
        await promo_category_selected(update, context)
    elif data.startswith("promo_sub_"):
        await promo_subtype_selected(update, context)
    elif data.startswith("account_type_"):
        await promo_account_type_selected(update, context)
    elif data in ("audience_all", "audience_custom"):
        await promo_audience_selected(update, context)
    elif data == "audience_done":
        await audience_done_callback(update, context)
    elif data.startswith("lang_"):
        await toggle_promo_language(update, context)
    elif data.startswith("qty_select_"):
        qty = int(data.split("_")[-1])
        await process_qty_input(update, context, qty)
    elif data == "pay_method_gram":
        await prompt_target_chat_picker(update, context)
    elif data == "promo_enter_code":
        await prompt_promo_code_callback(update, context)
    elif data == "promo_clear_code":
        await clear_promo_code_callback(update, context)
    elif data == "pay_method_stars":
        await handle_stars_fee_free_payment(update, context)
    elif data == "promo_confirm_create":
        await promo_confirm_create_callback(update, context)
    elif data == "promo_auto_settings":
        await show_promo_auto_settings(update, context)
    elif data == "promo_my_tasks":
        await show_my_tasks(update, context)
    elif data == "promo_back_main":
        await show_promotion_menu(update, context)
    elif data.startswith("mytask_view_"):
        await mytask_view_callback(update, context)
    elif data.startswith(("mytask_toggle_", "mytask_boost_", "mytask_cancel_")):
        await mytask_action_callback(update, context)

    # Vouchers & Account Features
    elif data == "my_vouchers":
        await show_vouchers_menu(update, context)
    elif data == "prompt_create_voucher":
        await prompt_create_voucher(update, context)
    elif data == "prompt_redeem_voucher":
        await prompt_redeem_voucher(update, context)
    elif data == "my_created_vouchers":
        await show_my_vouchers(update, context)
    elif data.startswith("cancel_voucher_"):
        await cancel_voucher_callback(update, context)
    elif data == "show_levels":
        await show_levels_menu(update, context)
    elif data.startswith("claim_m_"):
        await claim_milestone_callback(update, context)
    elif data == "show_tx_history":
        await show_transaction_history(update, context, page=1)
    elif data.startswith("tx_page_"):
        page = int(data.replace("tx_page_", ""))
        await show_transaction_history(update, context, page=page)
    elif data == "show_transfer_menu":
        await show_transfer_menu(update, context)
    elif data == "prompt_transfer_id":
        await prompt_transfer_callback(update, context)

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

    # Proof Review & Disputes
    elif data.startswith("proof_"):
        await handle_creator_proof_action(update, context)
    elif data.startswith("resubmit_proof_") or data.startswith("file_dispute_"):
        await handle_worker_dispute_callbacks(update, context)
    elif data.startswith("admin_disp_"):
        await handle_admin_dispute_action(update, context)

    # Admin Panel
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
    elif data == "admin_tickets_manage":
        await admin_tickets_manage(update, context)
    elif data.startswith("admin_view_ticket_"):
        await admin_view_ticket_callback(update, context)
    elif data == "admin_reports_manage":
        await admin_reports_manage(update, context)
    elif data.startswith("admin_report_"):
        await handle_admin_report_action(update, context)
    elif data == "admin_promos_menu":
        await admin_promos_menu(update, context)
    elif data.startswith(("admin_stop_flash_", "admin_notify_flash_", "admin_toggle_promo_")):
        await handle_admin_promo_callbacks(update, context)
    elif data == "admin_broadcast_help":
        await admin_broadcast_help(update, context)
    elif data == "admin_mand_subs_view":
        await show_mandatory_channels_admin(update, context)
    elif data == "add_mand_chan_prompt":
        await prompt_add_mandatory_channel(update, context)
    elif data.startswith("del_mand_chan_"):
        await delete_mandatory_channel_callback(update, context)
    else:
        await query.answer()


def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ Warning: Please set a valid BOT_TOKEN in config.py or .env file before running!")

    pers_dir = os.path.dirname(PERSISTENCE_FILE)
    if pers_dir:
        os.makedirs(pers_dir, exist_ok=True)

    persistence = PicklePersistence(filepath=PERSISTENCE_FILE)
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    app.add_error_handler(global_error_handler)

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("bonus", claim_daily_bonus))
    app.add_handler(CommandHandler("spin", spin_wheel_command))
    app.add_handler(CommandHandler("language", show_language_menu))
    app.add_handler(CommandHandler("admin", show_admin_panel))
    app.add_handler(CommandHandler("addtask", add_task_admin))
    app.add_handler(CommandHandler("addpromo", handle_add_promo_command))
    app.add_handler(CommandHandler("flash", handle_flash_event_command))
    app.add_handler(CommandHandler("stopflash", handle_stop_flash_command))
    app.add_handler(CommandHandler("transfer", handle_transfer_command))
    app.add_handler(CommandHandler("createvoucher", handle_create_voucher_command))
    app.add_handler(CommandHandler("setbalance", handle_setbalance_command))
    app.add_handler(CommandHandler("userinfo", handle_userinfo_command))
    app.add_handler(CommandHandler("ban", handle_ban_command))
    app.add_handler(CommandHandler("unban", handle_unban_command))
    app.add_handler(CommandHandler("broadcast", handle_broadcast_command))
    app.add_handler(CommandHandler("vault", show_vault_menu))
    app.add_handler(CommandHandler("raffle", show_raffle_menu))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(CommandHandler("settings", show_user_settings))

    # Automatic Message Reaction Verification (channels/groups where bot is admin)
    app.add_handler(MessageReactionHandler(handle_message_reaction_update))

    # Payments & Native Chat Sharing
    app.add_handler(PreCheckoutQueryHandler(handle_pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_successful_payment))
    app.add_handler(MessageHandler(filters.StatusUpdate.CHAT_SHARED, handle_chat_shared_message))

    # Forwarded messages (for instant bot verification), Photos, and Text
    app.add_handler(MessageHandler(filters.FORWARDED & ~filters.COMMAND, handle_forwarded_messages))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_messages))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    # Callback Query Handler
    app.add_handler(CallbackQueryHandler(handle_callbacks))

    print("🚀 ZetaGram Bot is launching...")
    if WEBHOOK_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=WEBHOOK_PORT,
            url_path="webhook",
            webhook_url=WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET_TOKEN or None,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
