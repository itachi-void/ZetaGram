EN_TEXTS = {
    # Onboarding, Language & Security Captcha
    "select_lang_first": "🌐 <b>Please select your preferred language to start:</b>",
    "lang_select_title": "🌐 <b>Select Bot Language:</b>",
    "lang_changed": "✅ Bot language changed to <b>English</b> successfully!",
    "captcha_text": "🤖 <b>Security Check (Captcha):</b>\nPlease solve the following math problem to complete registration:\n\nWhat is: <code>{num1} + {num2}</code> ?",
    "captcha_image_caption": "🛡️ <b>Security Check (ZetaGram):</b>\n\nLook at the image and choose the correct answer below.\n⏳ Valid for 2 minutes.",
    "captcha_btn_refresh": "🔄 Refresh Image",
    "captcha_wrong": "❌ Wrong answer! Please try again.",
    "captcha_expired": "⌛ Captcha expired! A new image has been generated.",
    "captcha_locked": "⛔ Captcha attempts temporarily locked due to repeated wrong answers.\nPlease wait <b>{mins} minutes</b>.",
    "captcha_locked_alert": "⛔ Captcha attempts temporarily locked.",
    "captcha_success": "🎉 Captcha verified successfully!",
    "recaptcha_required": "🛡️ <b>Periodic Security Check:</b>\nYou completed {count} tasks! Please solve this quick captcha to continue.",
    "rate_limited": "⚠️ Please wait a moment and avoid rapid clicking!",
    "not_registered": "❌ Account not found. Please send /start to register first.",
    "account_error": "❌ An error occurred loading your account.",
    "banned_notice": "🚫 <b>Your account is temporarily restricted!</b>\n\n⏳ Expires at: <code>{until}</code>\n⚠️ Violations: {violations}",
    "forced_sub_required": "⚠️ <b>Please subscribe to the required channels below to continue:</b>\nJoin them and tap Check Now.",
    "forced_sub_ok": "✅ <b>All required subscriptions are active!</b>",
    "forced_sub_verified_alert": "✅ Subscriptions verified successfully!",
    "forced_sub_missing_alert": "❌ You haven't joined all required channels yet!",
    "btn_recheck_now": "🔄 Check Now",
    "err_amount_min": "❌ Amount must be at least {min_val:,}.",
    "err_amount_max": "❌ Amount exceeds the maximum allowed ({max_val:,}).",
    "err_amount_invalid": "❌ Please enter a valid whole number.",

    # Main Menu Keyboard Buttons
    "btn_referrals": "👥 Referral System",
    "btn_bonus": "🎁 Daily Bonus",
    "btn_earnings": "🧑‍💻 Earnings",
    "btn_promotion": "📣 Promotion",
    "btn_account": "📱 My Account",
    "btn_vouchers": "🏷️ Vouchers",
    "btn_stats": "Our Bots & Stats 📊",
    "btn_check_sub": "Check Subscription 📣",
    "btn_instructions": "📋 Instructions",
    "btn_useful_links": "Useful Links",
    "btn_language": "🌐 Language",
    "btn_leaderboard": "🏆 Leaderboard",
    "btn_settings": "⚙️ Settings",
    "btn_back": "🔙 Back",
    "btn_close": "🔙 Close",
    "btn_report": "🔴 Report",
    "btn_cancel": "❌ Cancel",

    # Welcome & Start
    "welcome": (
        "🚀 <b>Welcome to ZetaGram!</b>\n\n"
        "Hello 👋 {name}\n\n"
        "A smart, trusted platform to earn Grams and promote Telegram channels, groups, and bots safely. 🎉\n\n"
        "💎 <b>What awaits you?</b>\n"
        "• 💰 Complete quick verified tasks for instant rewards.\n"
        "• 📣 Promote channels, groups &amp; bots with targeted audiences.\n"
        "• 👥 Referral program (+100 Grams join bonus + 250 active + 10% commission).\n"
        "• 🎁 Escalating daily streak bonus, daily quest &amp; Lucky Wheel.\n"
        "• 🏛️ Savings Vault, Weekly Raffle &amp; Leaderboard."
    ),
    "welcome_join_bonus": "\n\n🎁 <b>Referral Gift:</b> <b>+{bonus:,} Grams</b> have been credited to your balance!",
    "welcome_flash_banner": "\n\n🔥 <b>Flash Event (Happy Hour) is LIVE NOW!</b>\n<b>{title}</b> — Earn <b>{mult}</b> rewards until <code>{ends} UTC</code>!",

    # Flash Events & System Notifications
    "flash_banner_earnings": "🔥 <b>Flash Event LIVE NOW: {title} ({mult})!</b>\n⏰ Ends at: <code>{ends} UTC</code> — All tasks pay multiplied rewards!\n\n",
    "flash_bonus_note": " (includes +{flash_bonus:,} Grams {mult}🔥 bonus)",
    "flash_broadcast_notif": (
        "🔥 <b>Happy Hour Started on {bot_name}!</b>\n\n"
        "🎉 <b>{title}</b>\n"
        "⚡ Reward Multiplier: <b>{mult}</b> on all tasks!\n"
        "⏳ Active until: <code>{ends} UTC</code>\n\n"
        "Open Earnings now and maximize your Grams!"
    ),
    "daily_quest_done": "🎯 <b>Daily Quest Completed!</b>\nYou completed {target} tasks today and earned <b>+{reward:,} Grams</b>!",
    "notif_referral_milestone": "🎉 <b>Congrats!</b> Your invited friend (<code>{invitee_id}</code>) completed 3 tasks — you earned <b>+{bonus:,} Grams</b>!",
    "notif_retention_reminder": "👋 <b>Hi {name}!</b> Don't miss your daily streak bonus on ZetaGram! 🎁\n\nOpen the bot now to claim your escalating bonus, spin the wheel, and finish your daily quest! 🎡",
    "notif_proof_auto_approved_worker": "✅ <b>Your Proof Was Auto-Approved!</b>\nTask: <b>{title}</b>\n💰 <b>+{reward:,} Grams</b> added to your balance after the review timeout.",
    "notif_proof_auto_approved_creator": "⏱️ <b>Pending Proof Auto-Approved:</b>\nWorker <code>{worker_id}</code> proof for <b>{title}</b> was auto-approved after {hours}h without response.",
    "notif_leaderboard_winner": "🏆 <b>Congrats! You won a Weekly Leaderboard Prize ({week_key})!</b>\n📌 Category: <b>{category}</b>\n🎁 Prize: <b>+{prize:,} Grams</b> credited to your balance!",
    "notif_unsub_penalty": (
        "⚠️ <b>Violation &amp; Restriction Notice!</b>\n\n"
        "You left the channel/group: <code>{title}</code> before completing 7 days.\n"
        "• 🔴 Deducted: <b>-{deducted:,}</b> Grams from your balance.\n"
        "• 🚫 Task restriction duration: <b>{duration}</b>.\n"
        "• ⚠️ Total violations: {violations}"
    ),
    "ban_dur_24h": "24 hours",
    "ban_dur_7d": "7 days",
    "ban_dur_perm": "Permanent",

    # VIP Titles, Milestones & Transaction Types
    "vip_title_1": "🥉 Starter",
    "vip_title_2": "🥈 Active",
    "vip_title_3": "🥇 Expert",
    "vip_title_4": "💎 VIP Elite",
    "ms_tasks_10": "Complete 10 Tasks",
    "ms_tasks_50": "Complete 50 Tasks",
    "ms_tasks_100": "Complete 100 Tasks",
    "ms_refs_10": "Invite 10 Friends",
    "tx_type_earn_task": "🧑‍💻 Task Earned",
    "tx_type_spend_promo": "📣 Campaign Created",
    "tx_type_promo_refund": "↩️ Campaign Refund",
    "tx_type_voucher_claim": "🎁 Voucher Claimed",
    "tx_type_voucher_create": "🏷️ Voucher Created",
    "tx_type_voucher_refund": "↩️ Voucher Refund",
    "tx_type_transfer_send": "💸 Transfer Sent",
    "tx_type_transfer_receive": "📥 Transfer Received",
    "tx_type_daily_bonus": "🎁 Daily Bonus",
    "tx_type_daily_quest": "🎯 Daily Quest",
    "tx_type_spin": "🎡 Lucky Spin",
    "tx_type_admin_adjust": "⚙️ Admin Adjustment",
    "tx_type_reward": "🏅 Reward",
    "tx_type_referral_milestone": "👥 Referral Milestone",
    "tx_type_referral_commission": "💎 Referral Commission",
    "tx_type_vault_deposit": "🏛️ Vault Deposit",
    "tx_type_vault_withdraw": "💰 Vault Withdraw",
    "tx_type_raffle_buy": "🎫 Raffle Ticket",
    "tx_type_raffle_win": "🏆 Raffle Win",
    "tx_type_unsub_penalty": "⚠️ Early Unsub Penalty",
    "tx_type_leaderboard_prize": "🏆 Leaderboard Prize",
    "tx_type_default": "💰 Transaction",

    # Account & Settings
    "account_summary": (
        "📱 <b>Your {bot_name} Account Overview:</b>\n\n"
        "🆔 <b>Account ID:</b> <code>{telegram_id}</code>\n"
        "👤 <b>Name:</b> {first_name}\n"
        "🏅 <b>Level:</b> {level_title}\n"
        "🛡️ <b>Trust Score:</b> <code>{trust_score}/200</code>\n"
        "🔥 <b>Daily Streak:</b> <code>{streak}</code> days\n"
        "🎯 <b>Daily Quest:</b> <code>{quest_progress}/{quest_target}</code> tasks\n"
        "💰 <b>Balance:</b> <code>{balance:,}</code> Grams\n"
        "✅ <b>Completed Tasks:</b> {completed_count}\n"
        "👥 <b>Referrals:</b> {referrals_count}\n\n"
        "🔗 <b>Your Referral Link:</b>\n"
        "<code>{ref_link}</code>\n\n"
        "🎁 Share your link to earn instant bonuses and 10% lifetime commission!"
    ),
    "account_btn_levels": "🏅 Levels & Milestones",
    "account_btn_history": "📜 Transaction History",
    "account_btn_vault": "🏛️ Savings Vault",
    "account_btn_raffle": "🎟️ Weekly Raffle",
    "account_btn_transfer": "💸 Transfer Grams",
    "account_btn_vouchers": "🏷️ Vouchers & Checks",
    "account_btn_leaderboard": "🏆 Leaderboard",
    "account_btn_settings": "⚙️ Settings",

    "settings_title": (
        "⚙️ <b>Account Settings &amp; Trust Status:</b>\n\n"
        "🔔 <b>Reminders &amp; Event Alerts:</b> {notif_str}\n"
        "🌐 <b>Current Language:</b> <code>{lang}</code>\n"
        "🏅 <b>VIP Level:</b> {level_title}\n"
        "🛡️ <b>Trust Score:</b> <code>{trust_score}/200</code>\n"
        "⚠️ <b>Violations Count:</b> <code>{violations}</code>"
    ),
    "settings_notif_on": "🔔 Enabled",
    "settings_notif_off": "🔕 Muted",
    "settings_btn_disable_notif": "🔕 Mute Reminders",
    "settings_btn_enable_notif": "🔔 Enable Reminders",
    "settings_btn_change_lang": "🌐 Change Language",
    "settings_notif_enabled_alert": "🔔 Reminders enabled.",
    "settings_notif_disabled_alert": "🔕 Reminders muted.",

    # Info & Public Stats
    "info_useful_links": (
        "🔗 <b>Useful Links ({bot_name}):</b>\n\n"
        "{links_str}"
        "💡 Tap any link above to follow network news and updates."
    ),
    "info_no_links": "No additional links configured right now.\n\n",
    "default_official_channel": "Official Channel",
    "info_instructions": (
        "📋 <b>How to Use {bot_name}:</b>\n\n"
        "1️⃣ <b>Earn Grams:</b> Open «🧑‍💻 Earnings» to join channels, react to posts, view posts, or try bots.\n"
        "2️⃣ <b>Promote Easily:</b> Open «📣 Promotion» with full Escrow protection and Promo Code discounts.\n"
        "3️⃣ <b>Daily Rewards &amp; Quests:</b> Claim escalating daily bonuses up to +500 Grams, finish {quest_target} daily tasks (+{quest_reward} Grams), and spin the Lucky Wheel (<code>/spin</code>).\n"
        "4️⃣ <b>Referral Program:</b> Earn +{ref_active_bonus} Grams per active invitee + <b>10% lifetime commission</b> (your friend gets +{ref_join_bonus} Grams).\n"
        "5️⃣ <b>Vault &amp; Raffle:</b> Grow your balance in the Savings Vault (<code>/vault</code>) or join the Weekly Raffle (<code>/raffle</code>).\n\n"
        "⚠️ <b>Important:</b> Never leave promoted channels/groups within 7 days to avoid penalties."
    ),
    "info_public_stats": (
        "📊 <b>{bot_name} Network Statistics:</b>\n\n"
        "👥 <b>Total Users:</b> <code>{users_cnt:,}</code>\n"
        "📌 <b>Total Campaigns:</b> <code>{tasks_cnt:,}</code>\n"
        "✅ <b>Completed Tasks:</b> <code>{completed_cnt:,}</code>\n"
        "⚡ <b>Verification:</b> Instant &amp; 100% Protected"
    ),
    "info_btn_leaderboard": "🏆 Weekly Leaderboard",

    # Referrals
    "ref_menu": (
        "👥 <b>Referral &amp; Commission System ({bot_name}):</b>\n\n"
        "Invite your friends and earn steady rewards!\n\n"
        "📊 <b>Your Stats:</b>\n"
        "• 👥 <b>Total Invited:</b> <code>{total_invites}</code> users\n"
        "• ⚡ <b>Active Friends (3+ tasks):</b> <code>{active_invites}</code> users\n"
        "• 💰 <b>Total Referral Earnings:</b> <code>{total_earned:,}</code> Grams\n\n"
        "🎁 <b>Reward Breakdown:</b>\n"
        "• Your friend receives <b>+{join_bonus:,} Grams</b> upon joining &amp; verifying.\n"
        "• You receive <b>+{active_bonus:,} Grams</b> when they complete 3 tasks.\n"
        "• Plus <b>10% lifetime commission</b> on all tasks they complete!\n\n"
        "🔗 <b>Your Referral Link:</b>\n"
        "<code>{ref_link}</code>"
    ),
    "ref_btn_share": "📤 Share Referral Link",
    "ref_share_text": "Join {bot_name} to earn Grams and promote channels & groups!",
    "ref_btn_list": "👥 My Referrals",
    "ref_list_empty": "👥 <b>My Referrals:</b>\n\nNo one has joined via your link yet. Share it to start earning!",
    "ref_list_title": "👥 <b>Invited Users ({count}):</b>\n\n",
    "ref_status_active": "✅ (Active)",
    "ref_status_pending": "⌛ ({cnt}/3 tasks)",

    # Leaderboard
    "lb_title": "🏆 <b>Weekly Leaderboard</b>\n",
    "lb_tab_tasks_title": "✅ <b>Top Task Earners This Week:</b>\n",
    "lb_tab_refs_title": "👥 <b>Top Referrers This Week:</b>\n",
    "lb_unit_tasks": "tasks",
    "lb_unit_refs": "invites",
    "lb_empty": "No activity recorded yet this week — claim #1 now!\n",
    "lb_row": "{medal} <b>{name}</b>: <code>{cnt}</code> {unit}{prize_note}",
    "lb_prize_note": " — 🎁 <code>+{prize:,}</code> Grams",
    "lb_footer": (
        "\n📊 <b>Your Weekly Score:</b> <code>{my_score}</code> {unit}\n"
        "🎁 <b>Top 3 Prizes:</b> "
        "🥇 {p1:,} | 🥈 {p2:,} | 🥉 {p3:,} Grams"
    ),
    "lb_btn_tasks": "Top Earners",
    "lb_btn_refs": "Top Referrers",

    # Levels & Milestones
    "levels_menu": (
        "🏅 <b>Achievements &amp; VIP Levels:</b>\n\n"
        "👤 <b>Current Level:</b> {level_title}\n"
        "✅ <b>Completed Tasks:</b> {completed_tasks}\n"
        "👥 <b>Invited Users:</b> {referrals}\n\n"
        "✨ <b>Active VIP Perks:</b>\n"
        "• 📣 Promotion Fee: <code>{promo_fee}%</code>\n"
        "• 💸 Transfer Fee: <code>{transfer_fee}%</code>\n"
        "• 💰 Task Bonus: <code>+{task_bonus}%</code>\n"
        "• 🏛️ Vault Extra Yield: <code>+{vault_bonus}%</code>\n\n"
        "🎁 <b>Milestones:</b>"
    ),
    "levels_btn_claimed": "✅ {title} (Claimed)",
    "levels_btn_claim": "🎁 Claim: {title} (+{reward:,} Grams)",
    "levels_btn_locked": "🔒 {title} (+{reward:,} Grams)",
    "levels_err_unknown": "❌ Unknown milestone",
    "levels_err_already": "⚠️ You already claimed this reward!",
    "levels_err_requirements": "❌ Milestone requirements not met yet!",
    "levels_claimed_alert": "🎉 Congrats! +{reward:,} Grams added & level updated!",

    # Transaction History
    "history_empty": "📜 <b>Transaction History:</b>\n\nNo transactions recorded yet.",
    "history_title": "📜 <b>Transaction History (Page {page}/{total_pages}):</b>\n\n",
    "history_row": "{icon}\n🔹 Amount: <code>{sign}{amount:,}</code> Grams\n{details_line}⏱️ Date: {dt_str}\n─────────────────\n",
    "history_details_line": "💬 Details: {desc}\n",
    "history_btn_prev": "◀️ Prev",
    "history_btn_next": "Next ▶️",

    # Daily Bonus & Lucky Spin
    "bonus_already_claimed": (
        "⌛ <b>You already claimed today's bonus!</b>\n\n"
        "🔥 Current streak: <b>{streak} days</b>\n"
        "Next claim available in: <b>{hours}h {minutes}m</b>."
    ),
    "bonus_claimed_success": (
        "🎁 <b>Daily Bonus Claimed!</b>\n\n"
        "🔥 <b>Login Streak:</b> Day <b>{streak}</b>\n"
        "💰 <b>Reward:</b> +{reward:,} Grams\n"
        "💳 <b>New Balance:</b> {balance:,} Grams\n\n"
        "✨ Tomorrow's reward: <b>+{next_reward:,} Grams</b>!"
    ),
    "spin_already_used": (
        "⌛ <b>You already used today's Lucky Spin!</b>\n\n"
        "Try again in: <b>{hours}h {minutes}m</b>."
    ),
    "spin_rolling_1": "🎰 <b>Spinning the Lucky Wheel...</b>\n\n🌀 <code>[ 100 | 500 | 50 | 1000 | 250 | 2000 ]</code> 🌀",
    "spin_rolling_2": "🎰 <b>Almost there... ⚡</b>\n\n🌀 <code>[ 250 | 2000 | 50 | 500 | 1000 ]</code> 🌀",
    "spin_jackpot_badge": "🎉 <b>JACKPOT WINNER!</b> 🎉\n",
    "spin_result": (
        "🎰 <b>Lucky Wheel Result:</b>\n\n"
        "{badge}"
        "🎁 <b>You won:</b> <code>+{prize:,}</code> Grams!\n"
        "💳 <b>Current Balance:</b> <code>{balance:,}</code> Grams\n\n"
        "Come back tomorrow for another spin! 🎡"
    ),

    # Savings Vault
    "vault_menu": (
        "🏛️ <b>Savings &amp; Staking Vault:</b>\n\n"
        "Lock your Grams safely in the Vault and earn guaranteed yield!\n\n"
        "💳 <b>Available Balance:</b> <code>{balance:,}</code> Grams\n"
        "📦 <b>Active Deposits:</b> <code>{active_count}/{max_active}</code>\n"
        "🏅 <b>VIP Extra Yield ({level_title}):</b> <code>+{bonus_pct}%</code>\n\n"
        "📈 <b>Available Plans:</b>\n"
        "1️⃣ <b>7-Day Plan:</b> Base yield <b>+5%</b> (+ VIP bonus).\n"
        "2️⃣ <b>30-Day Plan:</b> Base yield <b>+20%</b> (+ VIP bonus).\n"
        "🔒 Max single deposit: <code>{max_deposit:,}</code> Grams."
    ),
    "vault_btn_7d": "➕ Deposit 7 Days (+5%)",
    "vault_btn_30d": "➕ Deposit 30 Days (+20%)",
    "vault_btn_my": "📜 My Deposits & Withdrawals",
    "vault_prompt": (
        "➕ <b>New Vault Deposit ({days} days - +{rate_pct}% base yield):</b>\n\n"
        "Send the amount of Grams to lock "
        "(Min: 500, Max: {max_deposit:,} Grams)."
    ),
    "vault_err_insufficient": "❌ Insufficient balance for this deposit.",
    "vault_err_max_active": "⚠️ You reached the limit of {max_active} active deposits. Wait for one to mature first.",
    "vault_deposit_created": (
        "🎉 <b>Vault Deposit Created!</b>\n\n"
        "💰 <b>Locked Amount:</b> <code>{amount:,}</code> Grams\n"
        "📈 <b>Expected Yield:</b> <code>+{yield_amount:,}</code> Grams\n"
        "⏱️ <b>Unlocks On:</b> <code>{lock_until}</code>"
    ),
    "vault_my_empty": "🏛️ <b>My Vault Deposits:</b>\n\nYou have no deposits yet.",
    "vault_my_header": "🏛️ <b>My Vault Deposits:</b>\n\n",
    "vault_row_withdrawn": "✅ <b>Completed #{dep_id}</b> ({days}d)\n Principal: <code>{amount:,}</code> + Yield <code>{yield_amount:,}</code> Grams\n\n",
    "vault_row_active": "🔹 <b>Deposit #{dep_id}</b> ({days}d) | {status}\n Amount: <code>{amount:,}</code> | Yield: <code>+{yield_amount:,}</code> Grams\n\n",
    "vault_status_ready": "🟢 Ready to Withdraw",
    "vault_status_locked": "⏳ Locked until {date}",
    "vault_btn_withdraw": "🎁 Withdraw #{dep_id} + Yield",
    "vault_err_not_found": "❌ Deposit not found or already withdrawn.",
    "vault_err_not_matured": "⏳ Lock period has not ended yet!",
    "vault_withdrawn_alert": "🎉 Withdrew +{total_payout:,} Grams to your balance!",

    # Weekly Raffle
    "raffle_menu": (
        "🎟️ <b>Weekly Raffle System:</b>\n\n"
        "Buy tickets to compete for the weekly prize pool!\n\n"
        "🏆 <b>Current Prize Pool:</b> <code>{prize_pool:,}</code> Grams\n"
        "🎫 <b>Your Tickets This Draw:</b> <code>{user_tickets}</code>\n"
        "👥 <b>Total Tickets Sold:</b> <code>{total_tickets}</code>\n"
        "💰 <b>Ticket Price:</b> <code>{ticket_price:,}</code> Grams\n"
        "💳 <b>Available Balance:</b> <code>{balance:,}</code> Grams\n"
    ),
    "raffle_btn_buy_1": "🎫 Buy 1 Ticket (100)",
    "raffle_btn_buy_5": "🎟️ Buy 5 Tickets (500)",
    "raffle_btn_my": "📜 My Tickets",
    "raffle_btn_admin_draw": "🎲 Draw Winner Now (Admin)",
    "raffle_err_invalid_qty": "❌ Invalid ticket count.",
    "raffle_err_insufficient": "❌ Insufficient balance to buy tickets!",
    "raffle_buy_success": "🎉 Purchased {count} raffle ticket(s)!",
    "raffle_my_empty": "🎫 <b>My Tickets:</b>\n\nYou haven't bought any tickets for the current draw yet.",
    "raffle_my_list": "🎫 <b>Your Tickets (#Draw-{draw_id}):</b>\n\nTotal Tickets: <code>{count}</code>\nCodes:\n{codes}",
    "raffle_draw_empty": "❌ No active draw or empty prize pool!",
    "raffle_draw_no_tickets": "❌ No tickets purchased in this draw yet.",
    "raffle_draw_done_alert": "🎲 Winner drawn successfully!",
    "raffle_draw_summary": (
        "🎉 <b>Weekly Raffle Winner!</b> 🎉\n\n"
        "🏆 <b>Grand Prize:</b> <code>+{prize:,}</code> Grams!\n"
        "👤 <b>Winner:</b> <code>{winner_id}</code>\n"
        "🎫 <b>Winning Ticket:</b> <code>{ticket_code}</code>\n\n"
        "Prize credited automatically. A fresh weekly draw is now live! 🚀"
    ),
    "raffle_winner_dm": "🥳 <b>Congrats! You won the Weekly Raffle!</b>\n<b>+{prize:,} Grams</b> added to your account!",

    # Vouchers
    "vouchers_menu": (
        "🏷️ <b>Gift Vouchers &amp; Checks:</b>\n\n"
        "Redeem voucher codes or create shareable gift checks funded by your balance.\n\n"
        "Quick command:\n"
        "<code>/createvoucher &lt;amount&gt; &lt;max_uses&gt;</code>"
    ),
    "vouchers_btn_redeem": "🎁 Redeem Voucher",
    "vouchers_btn_create": "➕ Create Voucher",
    "vouchers_btn_my": "📜 My Created Vouchers",
    "voucher_prompt_redeem": "🎁 <b>Redeem Voucher:</b>\n\nSend the voucher code now (e.g. <code>GRAM-ABCD-1234</code>).",
    "voucher_prompt_create": (
        "➕ <b>Create New Voucher:</b>\n\n"
        "Send amount per claim and max claims separated by a space:\n"
        "<code>&lt;amount&gt; &lt;max_uses&gt;</code>\n\n"
        "Example: <code>500 10</code>"
    ),
    "voucher_cmd_usage": (
        "⚠️ <b>Invalid Usage!</b>\n"
        "Format: <code>/createvoucher &lt;amount&gt; [max_uses]</code>\n\n"
        "Example: <code>/createvoucher 500 5</code>"
    ),
    "voucher_err_enter_amount": "❌ Please enter the amount.",
    "voucher_err_new_account": (
        "🛡️ <b>New Account Protection:</b>\n"
        "Complete at least <b>{min_tasks} tasks</b> before creating vouchers ({completed}/{min_tasks})."
    ),
    "voucher_err_insufficient": (
        "❌ Insufficient balance!\n"
        "Required: {total_cost:,} Grams ({amount:,} × {max_uses})\n"
        "Current balance: {balance:,} Grams"
    ),
    "voucher_created": (
        "🎉 <b>Voucher Created!</b>\n\n"
        "🏷️ <b>Code:</b> <code>{code}</code>\n"
        "💰 <b>Value per Claim:</b> {amount:,} Grams\n"
        "👥 <b>Max Claims:</b> {max_uses}\n"
        "💳 <b>Deducted:</b> {total_cost:,} Grams\n\n"
        "🔗 <b>Direct Link:</b>\n<code>{v_link}</code>"
    ),
    "voucher_locked_bruteforce": "⛔ <b>Voucher redemption temporarily locked!</b>\nPlease wait <b>{mins} minutes</b>.",
    "voucher_locked_now": "⛔ <b>Voucher redemption locked for 15 minutes due to repeated invalid codes!</b>",
    "voucher_invalid_attempt": "❌ Invalid or expired voucher code. (Attempt {attempts}/5)",
    "voucher_exhausted": "⚠️ This voucher has reached its maximum claims.",
    "voucher_already_used": "⚠️ You already redeemed this voucher!",
    "voucher_redeemed_success": "🎉 Voucher redeemed! <b>+{amount:,} Grams</b> added to your balance!",
    "voucher_my_empty": "📜 <b>My Created Vouchers:</b>\n\nYou haven't created any vouchers yet.",
    "voucher_my_header": "📜 <b>Your Last 10 Created Vouchers:</b>\n\n",
    "voucher_row": "🏷️ <code>{code}</code> — {amount:,} Grams | {status}\n",
    "voucher_status_active": "🟢 Remaining {rem}/{max_uses}",
    "voucher_status_done": "⚪ Completed/Cancelled",
    "voucher_btn_cancel": "🗑️ Cancel {code} & Refund {refund:,}",
    "voucher_err_not_owner": "❌ Voucher not found or not owned by you.",
    "voucher_err_not_found": "❌ Voucher not found.",
    "voucher_err_already_done": "⚠️ This voucher is already exhausted or cancelled.",
    "voucher_cancelled_alert": "✅ Voucher cancelled! Refunded +{refund:,} Grams!",

    # Balance Transfers
    "transfer_menu": (
        "💸 <b>Peer-to-Peer Balance Transfer:</b>\n\n"
        "Send Grams directly to any member using their Telegram ID.\n"
        "• 💵 <b>Min Transfer:</b> <code>{min_amt:,}</code> Grams\n"
        "• 📊 <b>Daily Limit:</b> <code>{daily_limit:,}</code> Grams\n"
        "• 📉 <b>Your Fee ({level_title}):</b> <code>{fee_pct}%</code>\n\n"
        "Quick command:\n"
        "<code>/transfer &lt;ID&gt; &lt;amount&gt;</code>"
    ),
    "transfer_btn_start": "💸 Start Transfer",
    "transfer_prompt": (
        "💸 <b>Send Grams:</b>\n\n"
        "Send the recipient Telegram ID and amount separated by a space:\n"
        "<code>&lt;recipient_id&gt; &lt;amount&gt;</code>\n\n"
        "Example: <code>123456789 500</code>"
    ),
    "transfer_prompt_err": "⚠️ Send ID and amount separated by space, e.g. <code>123456789 500</code>",
    "transfer_cmd_usage": (
        "⚠️ <b>Invalid Usage!</b>\n"
        "Format: <code>/transfer &lt;recipient_id&gt; &lt;amount&gt;</code>\n\n"
        "Example: <code>/transfer 123456789 500</code>"
    ),
    "transfer_err_bad_id": "❌ Please enter a valid numeric recipient ID.",
    "transfer_err_self": "❌ You cannot transfer Grams to yourself!",
    "transfer_err_target_not_found": "❌ No user found with that Telegram ID!",
    "transfer_err_new_account": (
        "🛡️ <b>New Account Protection:</b>\n"
        "Complete at least <b>{min_tasks} tasks</b> before transferring funds ({completed}/{min_tasks})."
    ),
    "transfer_err_daily_limit": (
        "⛔ <b>Daily transfer limit exceeded ({daily_limit:,} Grams)!</b>\n"
        "Remaining today: <code>{rem_limit:,}</code> Grams."
    ),
    "transfer_err_insufficient": (
        "❌ Insufficient balance!\n"
        "Amount: {amount:,}\n"
        "Fee ({fee_pct}%): {fee:,}\n"
        "Total required: {total_deduct:,} Grams\n"
        "Current balance: {balance:,} Grams"
    ),
    "transfer_success_sender": (
        "🎉 <b>Transfer Successful!</b>\n\n"
        "👤 Recipient: <code>{target_id}</code>\n"
        "💰 Sent: {amount:,} Grams\n"
        "📉 Fee: {fee:,} Grams\n"
        "💳 Remaining Balance: {sender_bal:,} Grams"
    ),
    "transfer_received_dm": (
        "🎁 <b>You Received a Transfer!</b>\n\n"
        "User <code>{sender_id}</code> sent you <b>+{amount:,} Grams</b>.\n"
        "💳 New Balance: {receiver_bal:,} Grams"
    ),

    # Earnings Menus & Task Execution & Auto-Reactions
    "earnings_menu": (
        "📣 Channel Tasks: {channel_count}\n"
        "👤 Group Tasks: {group_count}\n"
        "👁️ Post View Tasks: {post_count}\n"
        "🤖 Bot Tasks: {bot_count}\n"
        "⚡ Premium Tasks: {premium_count}\n"
        "🔥 Reaction Tasks: {reactions_count}\n\n"
        "🔔 Choose an earning category 👇"
    ),
    "earnings_btn_channel": "📣 Join Channels",
    "earnings_btn_group": "👥 Join Groups",
    "earnings_btn_post": "👁️ View Posts",
    "earnings_btn_bot": "🤖 Bot Tasks",
    "earnings_btn_reactions": "🔥 Reactions",
    "earnings_btn_premium": "⚡ Premium Boost",
    "earnings_btn_rules": "📕 Rules",
    "earnings_bot_menu": (
        "Choose bot task category.\n"
        "Standard: {bot_normal}\n"
        "Web App: {bot_webapp}\n"
        "With Conditions: {bot_conditions}\n\n"
        "📱 <b>Web App Bots</b>\nBots with Mini App integration.\n\n"
        "🤖 <b>Standard Bots</b>\nClassic Telegram bots.\n\n"
        "📋 <b>Bots With Conditions</b>\nRequire captcha, language, or sponsor join."
    ),
    "earnings_btn_bot_normal": "🤖 Standard Bots",
    "earnings_btn_bot_webapp": "📱 Web App Bots",
    "earnings_btn_bot_conditions": "📋 Extra Conditions",
    "earnings_reactions_menu": (
        "Choose reaction category.\n"
        "Any Reaction: {reaction_random}\n"
        "Fixed Emoji: {reaction_fixed}\n\n"
        "Any Reaction – react with any emoji to qualify.\n\n"
        "Fixed Emoji – use the specified emoji to get paid."
    ),
    "earnings_btn_reaction_random": "🎲 Any Reactions",
    "earnings_btn_reaction_fixed": "🎯 Fixed Emoji Reactions",
    "earnings_rules_text": (
        "📕 <b>Task Rules:</b>\n\n"
        "Never leave channels/groups before <b>7 days</b>.\n"
        "Violations trigger automatic clawback, trust score penalty, and bans:\n\n"
        "• 1st violation – 24h ban\n"
        "• 2nd violation – 7d ban\n"
        "• 3+ violations – <b>Permanent ban</b>"
    ),
    "premium_only_alert": "⚡ This category is exclusive to Telegram Premium subscribers.",

    "task_list_channel_header": (
        "📣 <b>Join a channel/group, then tap «🔄 Check»:</b>\n\n"
        "⚠️ Leaving before 7 days results in automatic clawback and restrictions."
    ),
    "task_list_post_header": (
        "👁️ <b>Post View Tasks:</b>\n\n"
        "Open a post, view it for {seconds}s, then claim your reward."
    ),
    "task_list_reactions_header": (
        "🔥 <b>Post Reaction Tasks:</b>\n\n"
        "React to the post! Tasks marked with ⚡ verify and pay <b>instantly without screenshots</b>!"
    ),
    "task_list_premium_header": (
        "⚡ <b>Exclusive Telegram Premium Tasks:</b>\n\n"
        "Higher rewards for Premium users! Choose a task:"
    ),
    "task_list_bot_header": (
        "🤖 <b>Bot Tasks:</b>\n\n"
        "Choose a bot task for instant forward verification or screenshot proof."
    ),
    "task_list_empty": "❌ No tasks available for you right now",
    "task_btn_subscribe_item": "Join | +{reward:,} 💰",
    "task_btn_check": "🔄 Check",
    "task_btn_post_item": "👁️ View Post +{reward:,} Grams",
    "task_btn_bot_item": "🤖 Open Bot | +{reward:,} Grams",
    "task_btn_reaction_item": "{prefix}React & Earn | +{reward:,} Grams",
    "task_err_unavailable": "❌ This task is unavailable or already completed.",
    "task_err_own": "❌ You cannot complete your own task!",
    "task_err_already": "⚠️ You already completed this task!",
    "task_err_not_member": "❌ Membership not detected yet! Subscribe first, then tap Check.",
    "task_err_check_api": "⚠️ Could not verify channel membership right now, please retry shortly.",
    "task_err_completed_now": "❌ This task just reached its target quantity.",
    "task_completed_alert": "🎉 Verified! +{reward:,} Grams added to your balance{flash_note}.",

    "post_task_detail": (
        "👁️ <b>View Post Task:</b> {title}\n\n"
        "1️⃣ Tap «Open Post» and read it for at least <b>{seconds} seconds</b>.\n"
        "2️⃣ Return and tap «✅ Claim Reward (+{reward:,} Grams)»."
    ),
    "post_btn_open": "🔗 Open Post Now",
    "post_btn_claim": "✅ Claim (+{reward:,})",
    "post_err_open_first": "❌ Please open the post first!",
    "post_err_wait": "⏳ Please wait {rem} more second(s) before claiming.",
    "post_err_already": "⚠️ You already claimed this post reward!",
    "post_claimed_alert": "🎉 +{reward:,} Grams added to your balance{flash_note}!",

    "bot_task_detail": (
        "🤖 <b>Bot Task:</b> {title}\n"
        "💰 <b>Reward:</b> <code>{reward:,}</code> Grams\n"
        "{desc_line}"
        "\nChoose verification method after starting the bot:"
    ),
    "task_desc_line": "📝 <b>Instructions:</b> {desc}\n",
    "bot_btn_open": "🚀 Launch Bot",
    "bot_btn_fwd": "📨 Instant Forward Verify",
    "bot_btn_proof": "📸 Submit Screenshot",
    "bot_fwd_err_disabled": "❌ Instant forward verification is not enabled for this task.",
    "bot_fwd_prompt": (
        "📨 <b>Instant Forward Verification:</b>\n\n"
        "1️⃣ Open <code>{bot_username}</code> and tap <code>/start</code>.\n"
        "2️⃣ <b>Forward</b> its welcome message here within 5 minutes."
    ),
    "bot_fwd_err_not_bot": (
        "❌ That forwarded message is not from a bot (or forward privacy is hidden). "
        "Forward a message directly from the bot or submit a screenshot."
    ),
    "bot_fwd_err_stale": "⌛ That forwarded message is older than 5 minutes. Send /start again and forward the fresh reply.",
    "bot_fwd_err_wrong_bot": "❌ Message is from a different bot (<code>@{actual}</code>), expected (<code>@{expected}</code>).",
    "bot_fwd_success": "🎉 <b>Instant Bot Verification Passed!</b>\n💰 <b>+{reward:,} Grams</b> added to your balance{flash_note}!",

    "proof_task_detail": (
        "🔥 <b>Task Details:</b> {title}\n"
        "💰 <b>Reward:</b> <code>{reward:,}</code> Grams\n"
        "{emoji_line}"
        "{desc_line}"
        "{steps_text}"
    ),
    "proof_emoji_line": "🎭 <b>Required Emoji:</b> {emoji}\n",
    "proof_task_manual_steps": "\n1️⃣ Open the link and complete the requirement.\n2️⃣ Tap «📸 Submit Proof» and send your screenshot.",
    "proof_task_auto_note": (
        "\n⚡ <b>Instant Auto-Verification Enabled!</b>\n"
        "1️⃣ Open the post and add the reaction — your reward will be paid <b>automatically without any screenshot</b>!\n"
        "2️⃣ Or tap Submit Proof to upload a screenshot manually if needed."
    ),
    "proof_btn_open": "🔗 Open Link",
    "proof_btn_submit": "📸 Submit Screenshot Proof",
    "proof_submit_prompt": (
        "📸 <b>Submit Execution Proof:</b>\n\n"
        "Send a clear <b>screenshot photo</b> right here for review and payout."
    ),
    "task_skipped_alert": "⏭️ Task skipped and hidden.",
    "report_task_prompt": "🚨 <b>Report Task #{task_id}:</b>\n\nSend the reason for reporting this task (e.g. broken link / spam).",
    "report_issue_prompt": "🚨 <b>Report an Issue:</b>\n\nDescribe the issue or task ID and admins will review it.",
    "report_received": "✅ <b>Report received! Our team will review it shortly.</b>",

    "reaction_auto_paid": (
        "⚡ <b>Reaction Auto-Verified!</b>\n"
        "📌 Task: <b>{title}</b>\n"
        "💰 <b>+{reward:,} Grams</b> credited instantly without a screenshot!"
    ),
    "reaction_auto_paid_flash": (
        "⚡ <b>Reaction Auto-Verified!</b>\n"
        "📌 Task: <b>{title}</b>\n"
        "🔥 Flash Event ({mult}) active!\n"
        "💰 <b>+{reward:,} Grams</b> (including +{flash_bonus:,} bonus) credited instantly!"
    ),

    # Proof Submission & Review
    "proof_err_duplicate": "🚫 <b>Photo Automatically Rejected!</b>\nThis screenshot matches a previously submitted proof. Please upload a fresh screenshot.",
    "proof_err_already_pending": "⚠️ You already have an approved or pending submission for this task.",
    "proof_submitted": (
        "✅ <b>Screenshot Proof Received!</b>\n"
        "Sent to the advertiser for review (auto-approved after 24h if no action is taken)."
    ),
    "proof_creator_caption": (
        "📩 <b>New Proof Submission for Your Campaign!</b>\n\n"
        "📌 Task: {title}\n"
        "👤 Worker: <code>{worker_id}</code>\n"
        "💰 Reward: {reward:,} Grams\n\n"
        "Review and choose an action:"
    ),
    "proof_creator_revision_caption": (
        "🔄 <b>Updated Proof Resubmitted!</b>\n\n"
        "📌 Task: {title}\n"
        "👤 Worker: <code>{worker_id}</code>\n\n"
        "Please review:"
    ),
    "proof_btn_approve": "✅ Approve & Pay",
    "proof_btn_reject": "❌ Reject with Reason",
    "proof_btn_revision": "🔄 Request Revision",
    "proof_err_not_found": "❌ Submission record not found.",
    "proof_err_forbidden": "❌ You do not own this campaign!",
    "proof_err_already_handled": "⚠️ This submission was already handled!",
    "proof_worker_rejected": (
        "❌ <b>Your proof was rejected for task ({title}).</b>\n\n"
        "📝 <b>Reason:</b> {reason}\n\n"
        "You can submit a clearer screenshot or open a dispute for admin review."
    ),
    "proof_btn_resubmit": "📤 Resubmit Proof",
    "proof_btn_dispute": "⚖️ Open Dispute Ticket",
    "proof_rej_quick_unclear": "📷 Unclear Screenshot",
    "proof_rej_quick_notdone": "❌ Task Incomplete",
    "proof_rej_quick_rules": "🚫 Rules Violation",
    "proof_rej_reason_unclear": "Screenshot is unclear and does not confirm completion",
    "proof_rej_reason_notdone": "Task instructions were not fully completed",
    "proof_rej_reason_rules": "Instructions violated or mismatched screenshot",
    "proof_rej_custom_btn": "✍️ Custom Reason",
    "proof_rej_custom_prompt": "✍️ Type the rejection reason for submission <code>#{ut_id}</code> now:",
    "proof_rej_done_alert": "❌ Proof rejected and reason sent to worker.",
    "proof_rej_caption": "❌ <b>Proof Rejected.</b>\n📝 Reason: {reason}",
    "proof_rej_custom_done": "❌ <b>Proof rejected for {title} and reason sent to worker.</b>",
    "proof_rev_submitted": "✅ <b>Revised proof submitted successfully!</b>",
    "proof_approve_done_alert": "✅ Proof approved and worker paid!",
    "proof_approve_caption": "✅ <b>Approved &amp; paid +{reward:,} Grams to worker.</b>",
    "proof_worker_approved": "🎉 <b>Congrats!</b> Your proof for (<b>{title}</b>) was approved and <b>+{reward:,} Grams</b> added{flash_note}!",
    "proof_rev_done_alert": "🔄 Revision requested from worker.",
    "proof_rev_caption": "🔄 <b>Revision requested from worker.</b>",
    "proof_worker_rev_req": "🔄 <b>Advertiser requested a revision for ({title}).</b>\n\nPlease take a clearer screenshot and resubmit.",
    "proof_rev_prompt": "📤 <b>Resubmit Screenshot Proof:</b>\n\nSend the new screenshot image right here now.",
    "proof_err_cannot_resubmit": "⚠️ Cannot resubmit in current status.",
    "dispute_err_not_rejected": "⚠️ Only rejected proofs can be disputed.",
    "dispute_err_exists": "⚠️ A dispute ticket already exists for this submission!",
    "dispute_filed_alert": "⚖️ Dispute ticket escalated to admins!",
    "dispute_filed_msg": "⚖️ <b>Dispute ticket submitted to Admins.</b> Funds will be settled after review.",
    "dispute_worker_won_dm": "⚖️ <b>Admin Decision:</b> Your dispute succeeded! <b>+{paid:,} Grams</b> added to your balance!",
    "dispute_worker_lost_dm": "⚖️ <b>Admin Decision:</b> Your dispute was reviewed and the advertiser's rejection was upheld.",

    # Promotion Wizard, Promo Codes & Campaign Management
    "promo_menu": (
        "📣 <b>What would you like to promote?</b>\n\n"
        "💳 <b>Your Balance:</b> <code>{balance:,}</code> Grams\n"
        "📉 <b>Current Fee Rate:</b> <code>{fee_pct}%</code>"
    ),
    "promo_btn_group": "👥 Group",
    "promo_btn_channel": "📣 Channel",
    "promo_btn_bot": "🤖 Bot",
    "promo_btn_post": "👁️ Post",
    "promo_btn_reactions": "🔥 Reactions",
    "promo_btn_premium": "⚡ Premium Boost",
    "promo_btn_settings": "⚙️ Fee & Escrow Settings",
    "promo_btn_my_tasks": "💼 My Campaigns",

    "promo_bot_type_prompt": "🤖 <b>Select Bot Campaign Type:</b>",
    "promo_btn_bot_normal": "🤖 Standard Bot",
    "promo_btn_bot_webapp": "📱 Web App Bot",
    "promo_btn_bot_conditions": "📋 Bot with Conditions",
    "promo_reaction_type_prompt": "🔥 <b>Select Reaction Type:</b>",
    "promo_btn_reaction_random": "🎲 Any Emoji Reaction",
    "promo_btn_reaction_fixed": "🎯 Fixed Emoji Reaction",

    "promo_account_type_prompt": (
        "Choose target account tier:\n\n"
        "1️⃣ <b>All Users</b> – Fastest reach across all ZetaGram members.\n"
        "🔴 Minimum reward per action – 750 Grams\n\n"
        "2️⃣ <b>Telegram Premium</b> – Verified Telegram Premium accounts only 🌟 Higher engagement quality.\n"
        "🔴 Minimum reward per action – 1,400 Grams"
    ),
    "promo_btn_acc_all": "1️⃣ All Users",
    "promo_btn_acc_premium": "2️⃣ Telegram Premium Only 🌟",

    "promo_audience_prompt": (
        "🎯 <b>Audience:</b> 🌐 Global / No Restriction\n\n"
        "🌍 <b>Choose target languages for your task:</b>\n\n"
        "💡 <i>Targeting specific languages adds +100 Grams to the minimum reward.</i>"
    ),
    "promo_btn_audience_all": "🌍 Allow Everyone",
    "promo_btn_audience_custom": "🎯 Select Specific Languages",
    "promo_lang_unlimited": "🌐 No Restrictions",
    "promo_lang_grid_prompt": (
        "🎯 <b>Selected Languages:</b> {selected}\n\n"
        "🌍 <b>Tap languages to toggle:</b>\n"
        "💡 <i>Custom targeting adds +100 Grams to minimum unit reward.</i>"
    ),
    "promo_btn_lang_done": "✅ Confirm ({count} selected)",

    "promo_price_prompt": (
        "Set the reward per completed action.\n\n"
        "🔴 <b>Minimum Unit Reward – {min_price:,} Grams</b>\n\n"
        "💡 <i>Tip: Rewards above {fast_price:,} Grams rank higher in task lists.</i>\n\n"
        "📝 <b>Enter reward per user (whole number):</b>"
    ),
    "promo_qty_prompt": (
        "{error_prefix}"
        "🔔 <b>Your applied fee rate is {fee_pct}%.</b>\n\n"
        "💵 <b>Reward per action:</b> {price:,} Grams\n"
        "💰 <b>Your balance:</b> {balance:,} Grams\n\n"
        "📝 <b>Enter desired quantity (min 3), or pick below:</b>\n"
        "<b>Max affordable quantity:</b> {max_qty}"
    ),
    "promo_btn_max_qty": "(Max for balance) {max_qty}",
    "promo_err_min_qty": "❌ Error! Minimum campaign quantity is 3.",
    "promo_err_max_qty": "❌ Insufficient balance for {qty}. Maximum for your balance is {max_qty}.",

    "promo_payment_method": (
        "💳 <b>Select Payment Method:</b>\n\n"
        "• Escrow Cost: <code>{base_cost:,}</code> Grams\n"
        "• Applied Fee ({fee_pct}%): <code>{commission:,}</code> Grams\n"
        "{discount_line}"
        "• <b>Final Total:</b> <code>{total_gram:,}</code> Grams\n\n"
        "💡 Or unlock <b>0% fees for 24h</b> with <b>{stars_cost} ⭐ Telegram Stars</b>!"
    ),
    "promo_payment_discount_line": "🎟️ <b>Promo Code ({code}):</b> <code>-{discount:,}</code> Grams\n",
    "promo_btn_pay_gram": "💎 Pay {total_gram:,} GRAMS",
    "promo_btn_enter_code": "🎟️ Enter Promo Code",
    "promo_btn_clear_code": "🗑️ Remove Code ({code})",
    "promo_btn_pay_stars": "🌟 Pay {stars_cost} Telegram Stars (0% Fee 24h)",
    "promo_stars_unavailable": "⚠️ Telegram Stars checkout is currently unavailable; please pay with GRAMS.",
    "promo_stars_title": "24h 0% Promotion Fee Pass",
    "promo_stars_desc": "Waive all campaign creation commissions for 24 hours on ZetaGram.",
    "promo_stars_activated": "🌟 <b>24h Fee-Free Pass Activated!</b>\nYour campaign total with 0% fee is now: <code>{total:,}</code> Grams.",

    "promo_code_prompt": "🎟️ <b>Apply Promo Code:</b>\n\nSend your discount code in chat now.",
    "promo_code_applied": "✅ <b>Promo code <code>{code}</code> applied!</b> You saved <code>{discount:,}</code> Grams.",
    "promo_code_cleared": "🗑️ Promo code removed.",
    "promo_err_invalid": "❌ Invalid or inactive promo code.",
    "promo_err_expired": "⌛ This promo code has expired.",
    "promo_err_exhausted": "⚠️ This promo code has reached its redemption limit.",
    "promo_err_min_order": "⚠️ This promo code requires a minimum base order of <code>{min_order:,}</code> Grams.",
    "promo_err_already_used": "⚠️ You already redeemed this promo code!",
    "promo_err_code_race": "⚠️ Promo code could not be claimed (limit just reached). Recreate without code or try another.",

    "promo_kind_channel": "Channel",
    "promo_kind_group": "Group",
    "promo_btn_pick_chat": "📣 Select {kind}",
    "promo_target_chat_prompt": (
        "📌 <b>Select Target {kind}:</b>\n\n"
        "⚠️ <b>The bot MUST be an Admin in your {kind} to verify memberships.</b>\n\n"
        "1️⃣ Tap «📣 Select {kind}» below for instant setup.\n"
        "2️⃣ Or send manually as:\n"
        "<code>@username_or_link | Campaign Title</code>\n"
        "Example: <code>@MyChannel | Tech News</code>"
    ),
    "promo_target_url_prompt": (
        "🔗 <b>Enter Task Link &amp; Title:</b>\n\n"
        "Send details separated by <code>|</code>:\n"
        "<code>URL | Campaign Title{extra_hint}</code>\n\n"
        "Example:\n<code>https://t.me/my_target/15 | Boost Post{extra_hint}</code>"
    ),
    "promo_err_bot_not_admin": (
        "❌ <b>Bot is NOT an admin in this chat!</b> (Status: <code>{status}</code>)\n"
        "Promote the bot as Administrator first, then retry."
    ),
    "promo_err_invite_fetch": "⚠️ Could not fetch invite link automatically. Please enter manually: <code>URL | Title</code>",
    "promo_chat_verified": "✅ Chat verified successfully!",
    "promo_err_target_format": "⚠️ Invalid format. Use <code>|</code>:\n<code>@username_or_link | Campaign Title</code>",
    "promo_err_bad_url": "❌ Enter a valid https:// URL or @username.",
    "promo_err_need_public_chat": "❌ Use a public @username or the Select Chat button for admin verification.",

    "promo_auto_rx_badge_on": "\n⚡ <b>Reaction Verification:</b> Instant Auto-Verify (no screenshots needed)!",
    "promo_auto_rx_badge_off": "\n📸 <b>Reaction Verification:</b> Screenshot review (make the bot admin in the channel for instant auto-verification).",
    "promo_confirm_summary": (
        "📋 <b>Review &amp; Confirm Campaign:</b>\n\n"
        "📌 <b>Title:</b> {title}\n"
        "📂 <b>Category:</b> <code>{cat}</code>\n"
        "🔗 <b>Link:</b> {url}\n"
        "👥 <b>Target Quantity:</b> <code>{qty:,}</code>\n"
        "💵 <b>Worker Reward:</b> <code>{price:,}</code> Grams\n"
        "🌍 <b>Audience:</b> {audience}"
        "{rx_badge}\n"
        "💳 <b>Total Deducted:</b> <code>{total_gram:,}</code> Grams (Protected by Escrow)"
    ),
    "promo_audience_all": "Everyone",
    "promo_btn_confirm_create": "✅ Confirm & Launch Campaign",
    "promo_err_expired_session": "❌ Campaign draft expired, please start again.",
    "promo_err_insufficient": "❌ Insufficient balance!",
    "promo_created_alert": "🎉 Campaign launched successfully!",
    "promo_created_msg": (
        "🚀 <b>Campaign (#{task_id}) Launched!</b>\n\n"
        "📌 <b>Title:</b> {title}\n"
        "🛡️ <b>Escrow Locked:</b> <code>{escrow:,}</code> Grams\n\n"
        "Manage it anytime in «💼 My Campaigns»."
    ),
    "promo_btn_view_my": "💼 View My Campaigns",

    "promo_settings_view": (
        "⚙️ <b>Promotion Fees &amp; Escrow Info:</b>\n\n"
        "🏅 <b>VIP Level:</b> {level_title}\n"
        "📉 <b>Your VIP Fee Rate:</b> <code>{vip_fee}%</code>\n"
        "🌟 <b>Telegram Stars 0% Pass:</b> {stars_status}\n\n"
        "🛡️ <b>Escrow Protection:</b>\n"
        "• Worker rewards are locked safely in Escrow and released only upon verification.\n"
        "• Cancelling a campaign refunds your remaining net Escrow immediately."
    ),
    "promo_stars_on": "🟢 Active until <code>{until} UTC</code> (0% fee)",
    "promo_stars_off": "⚪ Inactive",

    "promo_my_empty": "💼 <b>My Campaigns:</b>\n\nYou have no campaigns yet.",
    "promo_my_header": "💼 <b>Your Campaigns (tap to manage):</b>\n\n",
    "promo_my_btn_manage": "{icon} Manage: {title}",
    "promo_task_view": (
        "💼 <b>Manage Campaign #{task_id}:</b> {title}\n\n"
        "📊 <b>Progress:</b> <code>{completed}/{total}</code> (Remaining: {remaining})\n"
        "💵 <b>Unit Reward:</b> <code>{reward:,}</code> Grams\n"
        "🛡️ <b>Remaining Escrow:</b> <code>{escrow:,}</code> Grams\n"
        "📌 <b>Status:</b> <code>{status}</code>"
    ),
    "promo_btn_pause": "⏸️ Pause Campaign",
    "promo_btn_resume": "▶️ Resume Campaign",
    "promo_btn_boost": "🚀 Boost Reward +100 (Cost {boost_cost:,})",
    "promo_btn_cancel": "🗑️ Cancel & Refund Remaining",
    "promo_btn_back_my": "🔙 Back to My Campaigns",
    "promo_err_task_not_found": "❌ Campaign not found.",
    "promo_err_task_closed": "⚠️ Cannot modify a completed or cancelled campaign.",
    "promo_toggled_alert": "✅ Status changed to {status}",
    "promo_err_boost_closed": "⚠️ Campaign is not active or already finished.",
    "promo_err_boost_balance": "❌ Insufficient balance! Needed: {extra_cost:,} Grams.",
    "promo_boosted_alert": "🚀 Campaign reward boosted by +100!",
    "promo_err_already_closed": "⚠️ Campaign is already completed or cancelled.",
    "promo_cancelled_alert": "✅ Campaign cancelled & refunded +{refund:,} Grams!",
}
