RU_TEXTS = {
    # Onboarding, Language & Security Captcha
    "select_lang_first": "🌐 <b>Пожалуйста, выберите предпочитаемый язык для начала:</b>",
    "lang_select_title": "🌐 <b>Выберите язык бота:</b>",
    "lang_changed": "✅ Язык бота успешно изменён на <b>Русский</b>!",
    "captcha_text": "🤖 <b>Проверка безопасности (Капча):</b>\nПожалуйста, решите пример для завершения регистрации:\n\nСколько будет: <code>{num1} + {num2}</code> ?",
    "captcha_image_caption": "🛡️ <b>Проверка безопасности (ZetaGram):</b>\n\nПосмотрите на изображение и выберите правильный ответ ниже.\n⏳ Действует 2 минуты.",
    "captcha_btn_refresh": "🔄 Обновить картинку",
    "captcha_wrong": "❌ Неверный ответ! Попробуйте ещё раз.",
    "captcha_expired": "⌛ Время капчи истекло! Сгенерирована новая картинка.",
    "captcha_locked": "⛔ Попытки ввода капчи временно заблокированы из-за частых ошибок.\nПодождите <b>{mins} мин.</b>.",
    "captcha_locked_alert": "⛔ Попытки ввода капчи временно заблокированы.",
    "captcha_success": "🎉 Капча успешно пройдена!",
    "recaptcha_required": "🛡️ <b>Плановая проверка безопасности:</b>\nВы выполнили {count} заданий! Пройдите быструю капчу для продолжения.",
    "rate_limited": "⚠️ Пожалуйста, подождите немного и не нажимайте слишком часто!",
    "not_registered": "❌ Аккаунт не найден. Нажмите /start для регистрации.",
    "account_error": "❌ Произошла ошибка при загрузке данных аккаунта.",
    "banned_notice": "🚫 <b>Ваш аккаунт временно ограничен!</b>\n\n⏳ Истекает: <code>{until}</code>\n⚠️ Нарушений: {violations}",
    "forced_sub_required": "⚠️ <b>Для продолжения подпишитесь на обязательные каналы ниже:</b>\nПодпишитесь и нажмите «Проверить».",
    "forced_sub_ok": "✅ <b>Все обязательные подписки активны!</b>",
    "forced_sub_verified_alert": "✅ Подписки успешно проверены!",
    "forced_sub_missing_alert": "❌ Вы ещё не подписались на все обязательные каналы!",
    "btn_recheck_now": "🔄 Проверить сейчас",
    "err_amount_min": "❌ Сумма должна быть не менее {min_val:,}.",
    "err_amount_max": "❌ Сумма превышает допустимый максимум ({max_val:,}).",
    "err_amount_invalid": "❌ Введите корректное целое число.",

    # Main Menu Keyboard Buttons
    "btn_referrals": "👥 Реферальная система",
    "btn_bonus": "🎁 Ежедневный бонус",
    "btn_earnings": "🧑‍💻 Заработок",
    "btn_promotion": "📣 Продвижение",
    "btn_account": "📱 Мой аккаунт",
    "btn_vouchers": "🏷️ Чеки",
    "btn_stats": "Наши боты и статистика 📊",
    "btn_check_sub": "Проверить подписку 📣",
    "btn_instructions": "📋 Инструкции",
    "btn_useful_links": "Полезные ссылки",
    "btn_language": "🌐 Язык",
    "btn_leaderboard": "🏆 Лидеры",
    "btn_settings": "⚙️ Настройки",
    "btn_back": "🔙 Назад",
    "btn_close": "🔙 Закрыть",
    "btn_report": "🔴 Жалоба",
    "btn_cancel": "❌ Отмена",

    # Welcome & Start
    "welcome": (
        "🚀 <b>Добро пожаловать в ZetaGram!</b>\n\n"
        "Привет 👋 {name}\n\n"
        "Надёжная платформа для заработка граммов и безопасного продвижения каналов, групп и ботов в Telegram. 🎉\n\n"
        "💎 <b>Что вас ждёт?</b>\n"
        "• 💰 Быстрые задания с проверкой и мгновенными выплатами.\n"
        "• 📣 Продвижение каналов, групп и ботов с точным таргетингом.\n"
        "• 👥 Партнёрская программа (+100 за вход + 250 за активность + 10% комиссия).\n"
        "• 🎁 Растущий ежедневный бонус, квест дня и Колесо Удачи.\n"
        "• 🏛️ Сейф, еженедельная лотерея и таблица лидеров."
    ),
    "welcome_join_bonus": "\n\n🎁 <b>Бонус за приглашение:</b> На ваш баланс начислено <b>+{bonus:,} г</b>!",
    "welcome_flash_banner": "\n\n🔥 <b>Счастливый час (Flash Event) УЖЕ ИДЁТ!</b>\n<b>{title}</b> — награды умножены на <b>{mult}</b> до <code>{ends} UTC</code>!",

    # Flash Events & System Notifications
    "flash_banner_earnings": "🔥 <b>Идёт акция: {title} ({mult})!</b>\n⏰ До: <code>{ends} UTC</code> — все задания платят повышенную награду!\n\n",
    "flash_bonus_note": " (включая +{flash_bonus:,} г бонус {mult}🔥)",
    "flash_broadcast_notif": (
        "🔥 <b>Счастливый час запущен в {bot_name}!</b>\n\n"
        "🎉 <b>{title}</b>\n"
        "⚡ Множитель наград: <b>{mult}</b> на все задания!\n"
        "⏳ Действует до: <code>{ends} UTC</code>\n\n"
        "Открывайте «Заработок» и получайте максимум граммов!"
    ),
    "daily_quest_done": "🎯 <b>Ежедневный квест выполнен!</b>\nВы выполнили {target} заданий за сегодня и получили бонус <b>+{reward:,} г</b>!",
    "notif_referral_milestone": "🎉 <b>Поздравляем!</b> Ваш друг (<code>{invitee_id}</code>) выполнил 3 задания — вам начислено <b>+{bonus:,} г</b>!",
    "notif_retention_reminder": "👋 <b>Привет, {name}!</b> Не забудьте забрать ежедневный бонус в ZetaGram! 🎁\n\nЗаходите в бота за серией наград, Колесом Удачи и квестом дня! 🎡",
    "notif_proof_auto_approved_worker": "✅ <b>Отчёт одобрен автоматически!</b>\nЗадание: <b>{title}</b>\n💰 На баланс начислено <b>+{reward:,} г</b> после окончания срока проверки.",
    "notif_proof_auto_approved_creator": "⏱️ <b>Автоодобрение отчёта:</b>\nОтчёт пользователя <code>{worker_id}</code> по заданию <b>{title}</b> одобрен автоматически спустя {hours} ч.",
    "notif_leaderboard_winner": "🏆 <b>Поздравляем! Вы победили в недельном рейтинге ({week_key})!</b>\n📌 Категория: <b>{category}</b>\n🎁 Приз: <b>+{prize:,} г</b> зачислен на баланс!",
    "notif_unsub_penalty": (
        "⚠️ <b>Предупреждение о нарушении!</b>\n\n"
        "Вы покинули канал/группу <code>{title}</code> ранее 7 дней.\n"
        "• 🔴 Списано: <b>-{deducted:,}</b> г с баланса.\n"
        "• 🚫 Блокировка заданий: <b>{duration}</b>.\n"
        "• ⚠️ Всего нарушений: {violations}"
    ),
    "ban_dur_24h": "24 часа",
    "ban_dur_7d": "7 дней",
    "ban_dur_perm": "Навсегда",

    # VIP Titles, Milestones & Transaction Types
    "vip_title_1": "🥉 Новичок",
    "vip_title_2": "🥈 Активный",
    "vip_title_3": "🥇 Эксперт",
    "vip_title_4": "💎 VIP Элита",
    "ms_tasks_10": "Выполнить 10 заданий",
    "ms_tasks_50": "Выполнить 50 заданий",
    "ms_tasks_100": "Выполнить 100 заданий",
    "ms_refs_10": "Пригласить 10 друзей",
    "tx_type_earn_task": "🧑‍💻 Награда за задание",
    "tx_type_spend_promo": "📣 Создание кампании",
    "tx_type_promo_refund": "↩️ Возврат за кампанию",
    "tx_type_voucher_claim": "🎁 Активация чека",
    "tx_type_voucher_create": "🏷️ Создание чека",
    "tx_type_voucher_refund": "↩️ Возврат по чеку",
    "tx_type_transfer_send": "💸 Перевод отправлен",
    "tx_type_transfer_receive": "📥 Перевод получен",
    "tx_type_daily_bonus": "🎁 Ежедневный бонус",
    "tx_type_daily_quest": "🎯 Квест дня",
    "tx_type_spin": "🎡 Колесо Удачи",
    "tx_type_admin_adjust": "⚙️ Корректировка админа",
    "tx_type_reward": "🏅 Награда",
    "tx_type_referral_milestone": "👥 Бонус за друга",
    "tx_type_referral_commission": "💎 Реферальная комиссия",
    "tx_type_vault_deposit": "🏛️ Вклад в сейф",
    "tx_type_vault_withdraw": "💰 Вывод из сейфа",
    "tx_type_raffle_buy": "🎫 Билет лотереи",
    "tx_type_raffle_win": "🏆 Выигрыш в лотерее",
    "tx_type_unsub_penalty": "⚠️ Штраф за отписку",
    "tx_type_leaderboard_prize": "🏆 Приз рейтинга",
    "tx_type_default": "💰 Операция",

    # Account & Settings
    "account_summary": (
        "📱 <b>Ваш профиль в {bot_name}:</b>\n\n"
        "🆔 <b>ID аккаунта:</b> <code>{telegram_id}</code>\n"
        "👤 <b>Имя:</b> {first_name}\n"
        "🏅 <b>Уровень:</b> {level_title}\n"
        "🛡️ <b>Рейтинг доверия:</b> <code>{trust_score}/200</code>\n"
        "🔥 <b>Серия дней:</b> <code>{streak}</code> дн.\n"
        "🎯 <b>Квест дня:</b> <code>{quest_progress}/{quest_target}</code>\n"
        "💰 <b>Баланс:</b> <code>{balance:,}</code> г\n"
        "✅ <b>Выполнено заданий:</b> {completed_count}\n"
        "👥 <b>Рефералов:</b> {referrals_count}\n\n"
        "🔗 <b>Ваша реферальная ссылка:</b>\n"
        "<code>{ref_link}</code>\n\n"
        "🎁 Делитесь ссылкой и получайте бонусы и 10% комиссии пожизненно!"
    ),
    "account_btn_levels": "🏅 Уровни и достижения",
    "account_btn_history": "📜 История операций",
    "account_btn_vault": "🏛️ Сейф и доход",
    "account_btn_raffle": "🎟️ Лотерея",
    "account_btn_transfer": "💸 Перевод баланса",
    "account_btn_vouchers": "🏷️ Чеки и ваучеры",
    "account_btn_leaderboard": "🏆 Таблица лидеров",
    "account_btn_settings": "⚙️ Настройки",

    "settings_title": (
        "⚙️ <b>Настройки аккаунта и доверие:</b>\n\n"
        "🔔 <b>Уведомления и акции:</b> {notif_str}\n"
        "🌐 <b>Текущий язык:</b> <code>{lang}</code>\n"
        "🏅 <b>VIP уровень:</b> {level_title}\n"
        "🛡️ <b>Рейтинг доверия:</b> <code>{trust_score}/200</code>\n"
        "⚠️ <b>Нарушений:</b> <code>{violations}</code>"
    ),
    "settings_notif_on": "🔔 Включены",
    "settings_notif_off": "🔕 Отключены",
    "settings_btn_disable_notif": "🔕 Отключить уведомления",
    "settings_btn_enable_notif": "🔔 Включить уведомления",
    "settings_btn_change_lang": "🌐 Сменить язык",
    "settings_notif_enabled_alert": "🔔 Уведомления включены.",
    "settings_notif_disabled_alert": "🔕 Уведомления отключены.",

    # Info & Public Stats
    "info_useful_links": (
        "🔗 <b>Полезные ссылки ({bot_name}):</b>\n\n"
        "{links_str}"
        "💡 Нажмите на любую ссылку, чтобы следить за новостями."
    ),
    "info_no_links": "Дополнительных ссылок пока нет.\n\n",
    "default_official_channel": "Официальный канал",
    "info_instructions": (
        "📋 <b>Руководство по {bot_name}:</b>\n\n"
        "1️⃣ <b>Заработок:</b> Откройте «🧑‍💻 Заработок» и подписывайтесь, ставьте реакции, смотрите посты или ботов.\n"
        "2️⃣ <b>Продвижение:</b> В разделе «📣 Продвижение» средства защищены Escrow, а промокоды дают скидки.\n"
        "3️⃣ <b>Ежедневные награды:</b> Серия входа до +500 г, квест дня из {quest_target} заданий (+{quest_reward} г) и Колесо Удачи (<code>/spin</code>).\n"
        "4️⃣ <b>Рефералы:</b> +{ref_active_bonus} г за активного друга + <b>10% комиссии</b> (другу +{ref_join_bonus} г).\n"
        "5️⃣ <b>Сейф и лотерея:</b> Инвестируйте в сейф (<code>/vault</code>) или играйте в лотерею (<code>/raffle</code>).\n\n"
        "⚠️ <b>Важно:</b> Не отписывайтесь от каналов/групп раньше 7 дней во избежание штрафа."
    ),
    "info_public_stats": (
        "📊 <b>Статистика сети {bot_name}:</b>\n\n"
        "👥 <b>Пользователей:</b> <code>{users_cnt:,}</code>\n"
        "📌 <b>Всего кампаний:</b> <code>{tasks_cnt:,}</code>\n"
        "✅ <b>Выполнено заданий:</b> <code>{completed_cnt:,}</code>\n"
        "⚡ <b>Проверка:</b> Мгновенная и защищённая"
    ),
    "info_btn_leaderboard": "🏆 Недельный рейтинг",

    # Referrals
    "ref_menu": (
        "👥 <b>Реферальная программа ({bot_name}):</b>\n\n"
        "Приглашайте друзей и получайте стабильный доход!\n\n"
        "📊 <b>Ваша статистика:</b>\n"
        "• 👥 <b>Всего приглашено:</b> <code>{total_invites}</code>\n"
        "• ⚡ <b>Активных (3+ задания):</b> <code>{active_invites}</code>\n"
        "• 💰 <b>Доход с рефералов:</b> <code>{total_earned:,}</code> г\n\n"
        "🎁 <b>Условия вознаграждения:</b>\n"
        "• Друг получает <b>+{join_bonus:,} г</b> сразу после регистрации.\n"
        "• Вы получаете <b>+{active_bonus:,} г</b> за каждые 3 выполненных другом задания.\n"
        "• Плюс <b>10% комиссия</b> с каждого выполненного ими задания!\n\n"
        "🔗 <b>Ваша ссылка:</b>\n"
        "<code>{ref_link}</code>"
    ),
    "ref_btn_share": "📤 Поделиться ссылкой",
    "ref_share_text": "Присоединяйся к {bot_name} — зарабатывай граммы и продвигай свои каналы!",
    "ref_btn_list": "👥 Мои рефералы",
    "ref_list_empty": "👥 <b>Мои рефералы:</b>\n\nПо вашей ссылке пока никто не перешёл.",
    "ref_list_title": "👥 <b>Приглашённые пользователи ({count}):</b>\n\n",
    "ref_status_active": "✅ (Активен)",
    "ref_status_pending": "⌛ ({cnt}/3 заданий)",

    # Leaderboard
    "lb_title": "🏆 <b>Недельный рейтинг лидеров</b>\n",
    "lb_tab_tasks_title": "✅ <b>Топ исполнителей недели:</b>\n",
    "lb_tab_refs_title": "👥 <b>Топ пригласителей недели:</b>\n",
    "lb_unit_tasks": "заданий",
    "lb_unit_refs": "приглаш.",
    "lb_empty": "На этой неделе пока нет активности — станьте первым!\n",
    "lb_row": "{medal} <b>{name}</b>: <code>{cnt}</code> {unit}{prize_note}",
    "lb_prize_note": " — 🎁 <code>+{prize:,}</code> г",
    "lb_footer": (
        "\n📊 <b>Ваш счёт за неделю:</b> <code>{my_score}</code> {unit}\n"
        "🎁 <b>Призы Топ-3:</b> "
        "🥇 {p1:,} | 🥈 {p2:,} | 🥉 {p3:,} г"
    ),
    "lb_btn_tasks": "Топ исполнителей",
    "lb_btn_refs": "Топ рефералов",

    # Levels & Milestones
    "levels_menu": (
        "🏅 <b>Достижения и VIP уровни:</b>\n\n"
        "👤 <b>Текущий уровень:</b> {level_title}\n"
        "✅ <b>Выполнено заданий:</b> {completed_tasks}\n"
        "👥 <b>Приглашено друзей:</b> {referrals}\n\n"
        "✨ <b>Ваши привилегии:</b>\n"
        "• 📣 Комиссия рекламы: <code>{promo_fee}%</code>\n"
        "• 💸 Комиссия перевода: <code>{transfer_fee}%</code>\n"
        "• 💰 Бонус к заданиям: <code>+{task_bonus}%</code>\n"
        "• 🏛️ Доп. доход сейфа: <code>+{vault_bonus}%</code>\n\n"
        "🎁 <b>Доступные достижения:</b>"
    ),
    "levels_btn_claimed": "✅ {title} (Получено)",
    "levels_btn_claim": "🎁 Забрать: {title} (+{reward:,} г)",
    "levels_btn_locked": "🔒 {title} (+{reward:,} г)",
    "levels_err_unknown": "❌ Неизвестное достижение",
    "levels_err_already": "⚠️ Вы уже получили эту награду!",
    "levels_err_requirements": "❌ Условия достижения ещё не выполнены!",
    "levels_claimed_alert": "🎉 Начислено +{reward:,} г и уровень обновлён!",

    # Transaction History
    "history_empty": "📜 <b>История операций:</b>\n\nУ вас пока нет операций.",
    "history_title": "📜 <b>История операций (Стр. {page}/{total_pages}):</b>\n\n",
    "history_row": "{icon}\n🔹 Сумма: <code>{sign}{amount:,}</code> г\n{details_line}⏱️ Дата: {dt_str}\n─────────────────\n",
    "history_details_line": "💬 Детали: {desc}\n",
    "history_btn_prev": "◀️ Назад",
    "history_btn_next": "Вперёд ▶️",

    # Daily Bonus & Lucky Spin
    "bonus_already_claimed": (
        "⌛ <b>Вы уже забрали сегодняшний бонус!</b>\n\n"
        "🔥 Текущая серия: <b>{streak} дн.</b>\n"
        "Следующий бонус через: <b>{hours} ч {minutes} мин</b>."
    ),
    "bonus_claimed_success": (
        "🎁 <b>Ежедневный бонус получен!</b>\n\n"
        "🔥 <b>Серия входов:</b> День <b>{streak}</b>\n"
        "💰 <b>Награда:</b> +{reward:,} г\n"
        "💳 <b>Новый баланс:</b> {balance:,} г\n\n"
        "✨ Завтрашний бонус: <b>+{next_reward:,} г</b>!"
    ),
    "spin_already_used": (
        "⌛ <b>Вы уже крутили Колесо Удачи сегодня!</b>\n\n"
        "Приходите снова через: <b>{hours} ч {minutes} мин</b>."
    ),
    "spin_rolling_1": "🎰 <b>Крутим Колесо Удачи...</b>\n\n🌀 <code>[ 100 | 500 | 50 | 1000 | 250 | 2000 ]</code> 🌀",
    "spin_rolling_2": "🎰 <b>Почти готово... ⚡</b>\n\n🌀 <code>[ 250 | 2000 | 50 | 500 | 1000 ]</code> 🌀",
    "spin_jackpot_badge": "🎉 <b>ДЖЕКПОТ!</b> 🎉\n",
    "spin_result": (
        "🎰 <b>Результат Колеса Удачи:</b>\n\n"
        "{badge}"
        "🎁 <b>Вы выиграли:</b> <code>+{prize:,}</code> г!\n"
        "💳 <b>Баланс:</b> <code>{balance:,}</code> г\n\n"
        "Заходите завтра за новым вращением! 🎡"
    ),

    # Savings Vault
    "vault_menu": (
        "🏛️ <b>Инвестиционный Сейф:</b>\n\n"
        "Заморозьте граммы в сейфе и получайте гарантированный доход!\n\n"
        "💳 <b>Доступный баланс:</b> <code>{balance:,}</code> г\n"
        "📦 <b>Активных вкладов:</b> <code>{active_count}/{max_active}</code>\n"
        "🏅 <b>Бонус уровня ({level_title}):</b> <code>+{bonus_pct}%</code>\n\n"
        "📈 <b>Тарифы:</b>\n"
        "1️⃣ <b>План 7 дней:</b> +5% (+ VIP бонус).\n"
        "2️⃣ <b>План 30 дней:</b> +20% (+ VIP бонус).\n"
        "🔒 Макс. вклад: <code>{max_deposit:,}</code> г."
    ),
    "vault_btn_7d": "➕ Вклад на 7 дней (+5%)",
    "vault_btn_30d": "➕ Вклад на 30 дней (+20%)",
    "vault_btn_my": "📜 Мои вклады и вывод",
    "vault_prompt": (
        "➕ <b>Новый вклад ({days} дн. - +{rate_pct}%):</b>\n\n"
        "Отправьте сумму граммов для вклада "
        "(Мин: 500, Макс: {max_deposit:,} г)."
    ),
    "vault_err_insufficient": "❌ Недостаточно средств на балансе.",
    "vault_err_max_active": "⚠️ Достигнут лимит активных вкладов ({max_active}).",
    "vault_deposit_created": (
        "🎉 <b>Вклад успешно открыт!</b>\n\n"
        "💰 <b>Сумма:</b> <code>{amount:,}</code> г\n"
        "📈 <b>Ожидаемый доход:</b> <code>+{yield_amount:,}</code> г\n"
        "⏱️ <b>Разблокировка:</b> <code>{lock_until}</code>"
    ),
    "vault_my_empty": "🏛️ <b>Мои вклады:</b>\n\nУ вас пока нет вкладов.",
    "vault_my_header": "🏛️ <b>Мои вклады:</b>\n\n",
    "vault_row_withdrawn": "✅ <b>Завершён #{dep_id}</b> ({days} дн.)\n Тело: <code>{amount:,}</code> + Доход <code>{yield_amount:,}</code> г\n\n",
    "vault_row_active": "🔹 <b>Вклад #{dep_id}</b> ({days} дн.) | {status}\n Сумма: <code>{amount:,}</code> | Доход: <code>+{yield_amount:,}</code> г\n\n",
    "vault_status_ready": "🟢 Готов к выводу",
    "vault_status_locked": "⏳ До {date}",
    "vault_btn_withdraw": "🎁 Забрать вклад #{dep_id} с прибылью",
    "vault_err_not_found": "❌ Вклад не найден или уже закрыт.",
    "vault_err_not_matured": "⏳ Срок вклада ещё не истёк!",
    "vault_withdrawn_alert": "🎉 Зачислено +{total_payout:,} г на баланс!",

    # Weekly Raffle
    "raffle_menu": (
        "🎟️ <b>Еженедельная Лотерея:</b>\n\n"
        "Покупайте билеты и выигрывайте крупный призовой фонд!\n\n"
        "🏆 <b>Призовой фонд:</b> <code>{prize_pool:,}</code> г\n"
        "🎫 <b>Ваши билеты:</b> <code>{user_tickets}</code>\n"
        "👥 <b>Всего билетов:</b> <code>{total_tickets}</code>\n"
        "💰 <b>Цена билета:</b> <code>{ticket_price:,}</code> г\n"
        "💳 <b>Ваш баланс:</b> <code>{balance:,}</code> г\n"
    ),
    "raffle_btn_buy_1": "🎫 Купить 1 билет (100 г)",
    "raffle_btn_buy_5": "🎟️ Купить 5 билетов (500 г)",
    "raffle_btn_my": "📜 Мои билеты",
    "raffle_btn_admin_draw": "🎲 Провести розыгрыш (Админ)",
    "raffle_err_invalid_qty": "❌ Некорректное количество билетов.",
    "raffle_err_insufficient": "❌ Недостаточно средств для покупки билетов!",
    "raffle_buy_success": "🎉 Куплено билетов: {count}!",
    "raffle_my_empty": "🎫 <b>Мои билеты:</b>\n\nВ этом розыгрыше у вас пока нет билетов.",
    "raffle_my_list": "🎫 <b>Ваши билеты (#Draw-{draw_id}):</b>\n\nВсего: <code>{count}</code>\nКоды:\n{codes}",
    "raffle_draw_empty": "❌ Нет активного розыгрыша или пустой фонд!",
    "raffle_draw_no_tickets": "❌ В этом розыгрыше ещё нет билетов.",
    "raffle_draw_done_alert": "🎲 Розыгрыш проведён!",
    "raffle_draw_summary": (
        "🎉 <b>Победитель лотереи определён!</b> 🎉\n\n"
        "🏆 <b>Главный приз:</b> <code>+{prize:,}</code> г!\n"
        "👤 <b>Победитель:</b> <code>{winner_id}</code>\n"
        "🎫 <b>Выигрышный билет:</b> <code>{ticket_code}</code>\n\n"
        "Награда начислена. Открыт новый недельный розыгрыш! 🚀"
    ),
    "raffle_winner_dm": "🥳 <b>Поздравляем! Вы выиграли в лотерее!</b>\nНа баланс зачислено <b>+{prize:,} г</b>!",

    # Vouchers
    "vouchers_menu": (
        "🏷️ <b>Чеки и Ваучеры:</b>\n\n"
        "Активируйте чеки или создавайте подарочные чеки для друзей и каналов.\n\n"
        "Быстрая команда:\n"
        "<code>/createvoucher &lt;сумма&gt; &lt;активаций&gt;</code>"
    ),
    "vouchers_btn_redeem": "🎁 Активировать чек",
    "vouchers_btn_create": "➕ Создать чек",
    "vouchers_btn_my": "📜 Мои созданные чеки",
    "voucher_prompt_redeem": "🎁 <b>Активация чека:</b>\n\nОтправьте код чека (например: <code>GRAM-ABCD-1234</code>).",
    "voucher_prompt_create": (
        "➕ <b>Создать новый чек:</b>\n\n"
        "Укажите сумму на 1 активацию и число активаций через пробел:\n"
        "<code>&lt;сумма&gt; &lt;активаций&gt;</code>\n\n"
        "Пример: <code>500 10</code>"
    ),
    "voucher_cmd_usage": (
        "⚠️ <b>Неверный формат!</b>\n"
        "Формат: <code>/createvoucher &lt;сумма&gt; [активаций]</code>\n\n"
        "Пример: <code>/createvoucher 500 5</code>"
    ),
    "voucher_err_enter_amount": "❌ Введите сумму.",
    "voucher_err_new_account": (
        "🛡️ <b>Защита новых аккаунтов:</b>\n"
        "Выполните не менее <b>{min_tasks} заданий</b> перед созданием чеков ({completed}/{min_tasks})."
    ),
    "voucher_err_insufficient": (
        "❌ Недостаточно средств!\n"
        "Требуется: {total_cost:,} г ({amount:,} × {max_uses})\n"
        "Ваш баланс: {balance:,} г"
    ),
    "voucher_created": (
        "🎉 <b>Чек успешно создан!</b>\n\n"
        "🏷️ <b>Код:</b> <code>{code}</code>\n"
        "💰 <b>Номинал:</b> {amount:,} г\n"
        "👥 <b>Активаций:</b> {max_uses}\n"
        "💳 <b>Списано:</b> {total_cost:,} г\n\n"
        "🔗 <b>Ссылка на чек:</b>\n<code>{v_link}</code>"
    ),
    "voucher_locked_bruteforce": "⛔ <b>Ввод чеков временно заблокирован!</b>\nПодождите <b>{mins} мин.</b>.",
    "voucher_locked_now": "⛔ <b>Использование чеков заблокировано на 15 минут из-за неверных кодов!</b>",
    "voucher_invalid_attempt": "❌ Неверный или отменённый чек. (Попытка {attempts}/5)",
    "voucher_exhausted": "⚠️ Все активации этого чека уже использованы.",
    "voucher_already_used": "⚠️ Вы уже активировали этот чек ранее!",
    "voucher_redeemed_success": "🎉 Чек активирован! На баланс начислено <b>+{amount:,} г</b>!",
    "voucher_my_empty": "📜 <b>Мои чеки:</b>\n\nВы ещё не создавали чеки.",
    "voucher_my_header": "📜 <b>Последние 10 созданных чеков:</b>\n\n",
    "voucher_row": "🏷️ <code>{code}</code> — {amount:,} г | {status}\n",
    "voucher_status_active": "🟢 Осталось {rem}/{max_uses}",
    "voucher_status_done": "⚪ Завершён/Отменён",
    "voucher_btn_cancel": "🗑️ Отменить {code} и вернуть {refund:,}",
    "voucher_err_not_owner": "❌ Чек не найден или не принадлежит вам.",
    "voucher_err_not_found": "❌ Чек не найден.",
    "voucher_err_already_done": "⚠️ Чек уже исчерпан или отменён.",
    "voucher_cancelled_alert": "✅ Чек отменён! Возвращено +{refund:,} г!",

    # Balance Transfers
    "transfer_menu": (
        "💸 <b>Перевод баланса между пользователями:</b>\n\n"
        "Отправляйте граммы другим участникам по их Telegram ID.\n"
        "• 💵 <b>Мин. перевод:</b> <code>{min_amt:,}</code> г\n"
        "• 📊 <b>Дневной лимит:</b> <code>{daily_limit:,}</code> г\n"
        "• 📉 <b>Комиссия ({level_title}):</b> <code>{fee_pct}%</code>\n\n"
        "Команда:\n"
        "<code>/transfer &lt;ID&gt; &lt;сумма&gt;</code>"
    ),
    "transfer_btn_start": "💸 Начать перевод",
    "transfer_prompt": (
        "💸 <b>Перевод средств:</b>\n\n"
        "Отправьте ID получателя и сумму через пробел:\n"
        "<code>&lt;ID_получателя&gt; &lt;сумма&gt;</code>\n\n"
        "Пример: <code>123456789 500</code>"
    ),
    "transfer_prompt_err": "⚠️ Укажите ID и сумму через пробел, например: <code>123456789 500</code>",
    "transfer_cmd_usage": (
        "⚠️ <b>Неверный формат!</b>\n"
        "Формат: <code>/transfer &lt;ID_получателя&gt; &lt;сумма&gt;</code>\n\n"
        "Пример: <code>/transfer 123456789 500</code>"
    ),
    "transfer_err_bad_id": "❌ Введите корректный числовой ID получателя.",
    "transfer_err_self": "❌ Нельзя переводить средства самому себе!",
    "transfer_err_target_not_found": "❌ Пользователь с таким ID не найден в боте!",
    "transfer_err_new_account": (
        "🛡️ <b>Защита новых аккаунтов:</b>\n"
        "Выполните не менее <b>{min_tasks} заданий</b> перед переводами ({completed}/{min_tasks})."
    ),
    "transfer_err_daily_limit": (
        "⛔ <b>Превышен дневной лимит переводов ({daily_limit:,} г)!</b>\n"
        "Доступно сегодня: <code>{rem_limit:,}</code> г."
    ),
    "transfer_err_insufficient": (
        "❌ Недостаточно средств!\n"
        "Сумма: {amount:,}\n"
        "Комиссия ({fee_pct}%): {fee:,}\n"
        "Итого к списанию: {total_deduct:,} г\n"
        "Ваш баланс: {balance:,} г"
    ),
    "transfer_success_sender": (
        "🎉 <b>Перевод выполнен!</b>\n\n"
        "👤 Получатель: <code>{target_id}</code>\n"
        "💰 Отправлено: {amount:,} г\n"
        "📉 Комиссия: {fee:,} г\n"
        "💳 Остаток: {sender_bal:,} г"
    ),
    "transfer_received_dm": (
        "🎁 <b>Вам поступил перевод!</b>\n\n"
        "Пользователь <code>{sender_id}</code> отправил вам <b>+{amount:,} г</b>.\n"
        "💳 Новый баланс: {receiver_bal:,} г"
    ),

    # Earnings Menus & Task Execution & Auto-Reactions
    "earnings_menu": (
        "📣 Каналы: {channel_count}\n"
        "👤 Группы: {group_count}\n"
        "👁️ Просмотры: {post_count}\n"
        "🤖 Боты: {bot_count}\n"
        "⚡ Premium: {premium_count}\n"
        "🔥 Реакции: {reactions_count}\n\n"
        "🔔 Выберите категорию заработка 👇"
    ),
    "earnings_btn_channel": "📣 Подписка на каналы",
    "earnings_btn_group": "👥 Вступить в группы",
    "earnings_btn_post": "👁️ Просмотр постов",
    "earnings_btn_bot": "🤖 Перейти к ботам",
    "earnings_btn_reactions": "🔥 Реакции",
    "earnings_btn_premium": "⚡ Premium задания",
    "earnings_btn_rules": "📕 Правила",
    "earnings_bot_menu": (
        "Выберите категорию ботов.\n"
        "Обычные: {bot_normal}\n"
        "Web App: {bot_webapp}\n"
        "С условиями: {bot_conditions}\n\n"
        "📱 <b>Web App боты</b>\nБоты с мини-приложениями.\n\n"
        "🤖 <b>Обычные боты</b>\nСтандартные боты Telegram.\n\n"
        "📋 <b>С условиями</b>\nТребуют капчу, выбор языка или подписку."
    ),
    "earnings_btn_bot_normal": "🤖 Обычные боты",
    "earnings_btn_bot_webapp": "📱 Web App боты",
    "earnings_btn_bot_conditions": "📋 С доп. условиями",
    "earnings_reactions_menu": (
        "Выберите категорию реакций.\n"
        "Любая реакция: {reaction_random}\n"
        "Точный эмодзи: {reaction_fixed}\n\n"
        "Любая реакция – поставьте любой эмодзи.\n\n"
        "Точный эмодзи – используйте указанный эмодзи."
    ),
    "earnings_btn_reaction_random": "🎲 Случайная реакция",
    "earnings_btn_reaction_fixed": "🎯 Фиксированный эмодзи",
    "earnings_rules_text": (
        "📕 <b>Правила выполнения заданий:</b>\n\n"
        "Запрещено отписываться от каналов/групп ранее <b>7 дней</b>.\n"
        "Нарушение ведёт к автосписанию награды и блокировке:\n\n"
        "• 1-е нарушение – бан на 24 часа\n"
        "• 2-е нарушение – бан на 7 дней\n"
        "• 3+ нарушений – <b>Вечный бан</b>"
    ),
    "premium_only_alert": "⚡ Категория доступна только для подписчиков Telegram Premium.",

    "task_list_channel_header": (
        "📣 <b>Подпишитесь и нажмите «🔄 Проверить»:</b>\n\n"
        "⚠️ Отписка до 7 дней приведёт к списанию награды и блокировке."
    ),
    "task_list_post_header": (
        "👁️ <b>Просмотр постов:</b>\n\n"
        "Откройте пост, читайте минимум {seconds} сек., затем заберите награду."
    ),
    "task_list_reactions_header": (
        "🔥 <b>Задания на реакции:</b>\n\n"
        "Поставьте реакцию! Задания со значком ⚡ проверяются и оплачиваются <b>автоматически без скриншота</b>!"
    ),
    "task_list_premium_header": (
        "⚡ <b>Эксклюзивные задания Telegram Premium:</b>\n\n"
        "Повышенные выплаты для Premium! Выберите задание:"
    ),
    "task_list_bot_header": (
        "🤖 <b>Задания с ботами:</b>\n\n"
        "Выберите задание для мгновенной проверки пересылкой или скриншотом."
    ),
    "task_list_empty": "❌ Сейчас нет доступных заданий",
    "task_btn_subscribe_item": "Подписаться | +{reward:,} 💰",
    "task_btn_check": "🔄 Проверить",
    "task_btn_post_item": "👁️ Пост +{reward:,} г",
    "task_btn_bot_item": "🤖 Запустить | +{reward:,} г",
    "task_btn_reaction_item": "{prefix}Реакция | +{reward:,} г",
    "task_err_unavailable": "❌ Задание недоступно или уже выполнено.",
    "task_err_own": "❌ Нельзя выполнять собственное задание!",
    "task_err_already": "⚠️ Вы уже выполнили это задание!",
    "task_err_not_member": "❌ Подписка не обнаружена! Сначала вступите, затем проверьте.",
    "task_err_check_api": "⚠️ Ошибка проверки канала, повторите через несколько секунд.",
    "task_err_completed_now": "❌ Лимит этого задания только что исчерпан.",
    "task_completed_alert": "🎉 Проверено! На баланс начислено +{reward:,} г{flash_note}.",

    "post_task_detail": (
        "👁️ <b>Просмотр поста:</b> {title}\n\n"
        "1️⃣ Нажмите «Открыть пост» и смотрите минимум <b>{seconds} сек.</b>.\n"
        "2️⃣ Вернитесь и нажмите «✅ Забрать награду (+{reward:,} г)»."
    ),
    "post_btn_open": "🔗 Открыть пост",
    "post_btn_claim": "✅ Забрать (+{reward:,})",
    "post_err_open_first": "❌ Сначала откройте пост!",
    "post_err_wait": "⏳ Подождите ещё {rem} сек. перед получением.",
    "post_err_already": "⚠️ Вы уже получили награду за этот пост!",
    "post_claimed_alert": "🎉 +{reward:,} г добавлено на баланс{flash_note}!",

    "bot_task_detail": (
        "🤖 <b>Задание с ботом:</b> {title}\n"
        "💰 <b>Награда:</b> <code>{reward:,}</code> г\n"
        "{desc_line}"
        "\nВыберите способ проверки после запуска бота:"
    ),
    "task_desc_line": "📝 <b>Инструкция:</b> {desc}\n",
    "bot_btn_open": "🚀 Перейти в бота",
    "bot_btn_fwd": "📨 Мгновенная проверка (Forward)",
    "bot_btn_proof": "📸 Отправить скриншот",
    "bot_fwd_err_disabled": "❌ Проверка пересылкой отключена для этого задания.",
    "bot_fwd_prompt": (
        "📨 <b>Мгновенная проверка пересылкой:</b>\n\n"
        "1️⃣ Откройте <code>{bot_username}</code> и нажмите <code>/start</code>.\n"
        "2️⃣ <b>Перешлите</b> приветственное сообщение бота сюда в течение 5 минут."
    ),
    "bot_fwd_err_not_bot": (
        "❌ Сообщение переслано не от бота (или скрыта пересылка). "
        "Перешлите сообщение прямо из бота или отправьте скриншот."
    ),
    "bot_fwd_err_stale": "⌛ Сообщение старше 5 минут. Нажмите /start снова и перешлите новое.",
    "bot_fwd_err_wrong_bot": "❌ Сообщение от другого бота (<code>@{actual}</code>), нужен (<code>@{expected}</code>).",
    "bot_fwd_success": "🎉 <b>Бот успешно подтверждён!</b>\n💰 Начислено <b>+{reward:,} г</b>{flash_note}!",

    "proof_task_detail": (
        "🔥 <b>Детали задания:</b> {title}\n"
        "💰 <b>Награда:</b> <code>{reward:,}</code> г\n"
        "{emoji_line}"
        "{desc_line}"
        "{steps_text}"
    ),
    "proof_emoji_line": "🎭 <b>Нужный эмодзи:</b> {emoji}\n",
    "proof_task_manual_steps": "\n1️⃣ Перейдите по ссылке и выполните условие.\n2️⃣ Нажмите «📸 Отправить скриншот».",
    "proof_task_auto_note": (
        "\n⚡ <b>Включена мгновенная автопроверка!</b>\n"
        "1️⃣ Откройте пост и поставьте реакцию — награда придёт <b>автоматически без скриншота</b>!\n"
        "2️⃣ Или отправьте скриншот вручную при необходимости."
    ),
    "proof_btn_open": "🔗 Открыть ссылку",
    "proof_btn_submit": "📸 Отправить скриншот",
    "proof_submit_prompt": (
        "📸 <b>Отправка отчёта:</b>\n\n"
        "Пришлите сюда <b>скриншот</b> выполнения для проверки и оплаты."
    ),
    "task_skipped_alert": "⏭️ Задание пропущено и скрыто.",
    "report_task_prompt": "🚨 <b>Жалоба на задание #{task_id}:</b>\n\nОпишите причину жалобы (например: нерабочая ссылка / спам).",
    "report_issue_prompt": "🚨 <b>Сообщить о проблеме:</b>\n\nНапишите подробности или ID задания для модераторов.",
    "report_received": "✅ <b>Жалоба принята и будет рассмотрена администрацией!</b>",

    "reaction_auto_paid": (
        "⚡ <b>Реакция подтверждена автоматически!</b>\n"
        "📌 Задание: <b>{title}</b>\n"
        "💰 Начислено <b>+{reward:,} г</b> без скриншота!"
    ),
    "reaction_auto_paid_flash": (
        "⚡ <b>Реакция подтверждена автоматически!</b>\n"
        "📌 Задание: <b>{title}</b>\n"
        "🔥 Акция ({mult}) активна!\n"
        "💰 Начислено <b>+{reward:,} г</b> (вкл. +{flash_bonus:,} бонус)!"
    ),

    # Proof Submission & Review
    "proof_err_duplicate": "🚫 <b>Скриншот отклонён автоматически!</b>\nЭтот снимок уже использовался ранее. Сделайте свежий скриншот.",
    "proof_err_already_pending": "⚠️ Отчёт по этому заданию уже на проверке или одобрен.",
    "proof_submitted": (
        "✅ <b>Скриншот принят!</b>\n"
        "Отправлено рекламодателю (автоодобрение через 24 часа, если нет ответа)."
    ),
    "proof_creator_caption": (
        "📩 <b>Новый отчёт по вашей кампании!</b>\n\n"
        "📌 Задание: {title}\n"
        "👤 Исполнитель: <code>{worker_id}</code>\n"
        "💰 Награда: {reward:,} г\n\n"
        "Проверьте и выберите действие:"
    ),
    "proof_creator_revision_caption": (
        "🔄 <b>Обновлённый отчёт от исполнителя!</b>\n\n"
        "📌 Задание: {title}\n"
        "👤 Исполнитель: <code>{worker_id}</code>\n\n"
        "Проверьте и примите решение:"
    ),
    "proof_btn_approve": "✅ Принять и оплатить",
    "proof_btn_reject": "❌ Отклонить с причиной",
    "proof_btn_revision": "🔄 Запросить повтор",
    "proof_err_not_found": "❌ Запись отчёта не найдена.",
    "proof_err_forbidden": "❌ Вы не владелец этой кампании!",
    "proof_err_already_handled": "⚠️ Этот отчёт уже обработан!",
    "proof_worker_rejected": (
        "❌ <b>Ваш отчёт отклонён ({title}).</b>\n\n"
        "📝 <b>Причина:</b> {reason}\n\n"
        "Вы можете отправить новый скриншот или открыть спор для администратора."
    ),
    "proof_btn_resubmit": "📤 Отправить снова",
    "proof_btn_dispute": "⚖️ Открыть спор (Админ)",
    "proof_rej_quick_unclear": "📷 Плохое качество",
    "proof_rej_quick_notdone": "❌ Условия не выполнены",
    "proof_rej_quick_rules": "🚫 Нарушение правил",
    "proof_rej_reason_unclear": "Скриншот нечёткий и не подтверждает выполнение",
    "proof_rej_reason_notdone": "Условия задания выполнены не полностью",
    "proof_rej_reason_rules": "Нарушение инструкций или несоответствие скриншота",
    "proof_rej_custom_btn": "✍️ Своя причина",
    "proof_rej_custom_prompt": "✍️ Введите причину отклонения для заявки <code>#{ut_id}</code>:",
    "proof_rej_done_alert": "❌ Отчёт отклонён, причина отправлена исполнителю.",
    "proof_rej_caption": "❌ <b>Отчёт отклонён.</b>\n📝 Причина: {reason}",
    "proof_rej_custom_done": "❌ <b>Отчёт по заданию {title} отклонён, уведомление отправлено.</b>",
    "proof_rev_submitted": "✅ <b>Новый скриншот успешно отправлен!</b>",
    "proof_approve_done_alert": "✅ Принято! Награда выплачена исполнителю.",
    "proof_approve_caption": "✅ <b>Принято и выплачено +{reward:,} г исполнителю.</b>",
    "proof_worker_approved": "🎉 <b>Поздравляем!</b> Отчёт по (<b>{title}</b>) принят, начислено <b>+{reward:,} г</b>{flash_note}!",
    "proof_rev_done_alert": "🔄 Запрос на повторную отправку отправлен.",
    "proof_rev_caption": "🔄 <b>Запрошен новый скриншот у исполнителя.</b>",
    "proof_worker_rev_req": "🔄 <b>Рекламодатель запросил повторный отчёт для ({title}).</b>\n\nПришлите более чёткий скриншот.",
    "proof_rev_prompt": "📤 <b>Повторная отправка отчёта:</b>\n\nПришлите новое фото прямо сейчас.",
    "proof_err_cannot_resubmit": "⚠️ Повторная отправка невозможна в текущем статусе.",
    "dispute_err_not_rejected": "⚠️ Оспорить можно только отклонённый отчёт.",
    "dispute_err_exists": "⚠️ Спор по этому отчёту уже открыт!",
    "dispute_filed_alert": "⚖️ Тикет спора отправлен администраторам!",
    "dispute_filed_msg": "⚖️ <b>Спор передан администраторам.</b> Решение будет принято после проверки.",
    "dispute_worker_won_dm": "⚖️ <b>Решение админа:</b> Спор решён в вашу пользу! Начислено <b>+{paid:,} г</b>!",
    "dispute_worker_lost_dm": "⚖️ <b>Решение админа:</b> После проверки отказ рекламодателя признан обоснованным.",

    # Promotion Wizard, Promo Codes & Campaign Management
    "promo_menu": (
        "📣 <b>Что вы хотите продвигать?</b>\n\n"
        "💳 <b>Ваш баланс:</b> <code>{balance:,}</code> г\n"
        "📉 <b>Текущая комиссия:</b> <code>{fee_pct}%</code>"
    ),
    "promo_btn_group": "👥 Группа",
    "promo_btn_channel": "📣 Канал",
    "promo_btn_bot": "🤖 Бот",
    "promo_btn_post": "👁️ Пост",
    "promo_btn_reactions": "🔥 Реакции",
    "promo_btn_premium": "⚡ Premium",
    "promo_btn_settings": "⚙️ Настройки комиссии",
    "promo_btn_my_tasks": "💼 Мои кампании",

    "promo_bot_type_prompt": "🤖 <b>Выберите тип кампании для бота:</b>",
    "promo_btn_bot_normal": "🤖 Обычный бот",
    "promo_btn_bot_webapp": "📱 Web App бот",
    "promo_btn_bot_conditions": "📋 Бот с условиями",
    "promo_reaction_type_prompt": "🔥 <b>Выберите тип реакции:</b>",
    "promo_btn_reaction_random": "🎲 Любой эмодзи",
    "promo_btn_reaction_fixed": "🎯 Точный эмодзи",

    "promo_account_type_prompt": (
        "Выберите тип аккаунтов:\n\n"
        "1️⃣ <b>Все пользователи</b> – максимальный охват.\n"
        "🔴 Мин. цена за 1 выполнение – 750 г\n\n"
        "2️⃣ <b>Telegram Premium</b> – только аккаунты Premium 🌟 Высшее качество.\n"
        "🔴 Мин. цена за 1 выполнение – 1,400 г"
    ),
    "promo_btn_acc_all": "1️⃣ Все пользователи",
    "promo_btn_acc_premium": "2️⃣ Только Telegram Premium 🌟",

    "promo_audience_prompt": (
        "🎯 <b>Аудитория:</b> 🌐 Без ограничений\n\n"
        "🌍 <b>Выберите целевые языки:</b>\n\n"
        "💡 <i>Выбор конкретных языков добавляет +100 г к минимальной цене.</i>"
    ),
    "promo_btn_audience_all": "🌍 Разрешить всем",
    "promo_btn_audience_custom": "🎯 Выбрать языки",
    "promo_lang_unlimited": "🌐 Без ограничений",
    "promo_lang_grid_prompt": (
        "🎯 <b>Выбрано:</b> {selected}\n\n"
        "🌍 <b>Нажмите на языки для выбора:</b>\n"
        "💡 <i>Языковой таргетинг добавляет +100 г к минимальной ставке.</i>"
    ),
    "promo_btn_lang_done": "✅ Подтвердить ({count})",

    "promo_price_prompt": (
        "Укажите награду за одно выполнение.\n\n"
        "🔴 <b>Минимальная цена – {min_price:,} г</b>\n\n"
        "💡 <i>Для быстрого выхода в топ укажите выше {fast_price:,} г.</i>\n\n"
        "📝 <b>Введите цену (целое число):</b>"
    ),
    "promo_qty_prompt": (
        "{error_prefix}"
        "🔔 <b>Ваша комиссия: {fee_pct}%.</b>\n\n"
        "💵 <b>Цена за выполнение:</b> {price:,} г\n"
        "💰 <b>Ваш баланс:</b> {balance:,} г\n\n"
        "📝 <b>Введите количество (мин. 3) или выберите:</b>\n"
        "<b>Макс. для баланса:</b> {max_qty}"
    ),
    "promo_btn_max_qty": "(Максимум) {max_qty}",
    "promo_err_min_qty": "❌ Ошибка! Минимум 3 выполнения.",
    "promo_err_max_qty": "❌ Недостаточно средств для {qty}. Максимум: {max_qty}.",

    "promo_payment_method": (
        "💳 <b>Выберите способ оплаты:</b>\n\n"
        "• Бюджет Escrow: <code>{base_cost:,}</code> г\n"
        "• Комиссия ({fee_pct}%): <code>{commission:,}</code> г\n"
        "{discount_line}"
        "• <b>Итого к оплате:</b> <code>{total_gram:,}</code> г\n\n"
        "💡 Отключите комиссию на 24ч всего за <b>{stars_cost} ⭐ Telegram Stars</b>!"
    ),
    "promo_payment_discount_line": "🎟️ <b>Промокод ({code}):</b> <code>-{discount:,}</code> г\n",
    "promo_btn_pay_gram": "💎 Оплатить {total_gram:,} GRAM",
    "promo_btn_enter_code": "🎟️ Ввести промокод",
    "promo_btn_clear_code": "🗑️ Убрать промокод ({code})",
    "promo_btn_pay_stars": "🌟 Оплатить {stars_cost} Stars (0% на 24ч)",
    "promo_stars_unavailable": "⚠️ Оплата Stars сейчас недоступна, используйте баланс GRAM.",
    "promo_stars_title": "Отключение комиссии на 24 часа",
    "promo_stars_desc": "Полная отмена комиссии при создании рекламных кампаний на 24 часа.",
    "promo_stars_activated": "🌟 <b>Комиссия 0% активирована на 24 часа!</b>\nСумма без комиссии: <code>{total:,}</code> г.",

    "promo_code_prompt": "🎟️ <b>Активация промокода:</b>\n\nОтправьте промокод в чат прямо сейчас.",
    "promo_code_applied": "✅ <b>Промокод <code>{code}</code> применён!</b> Экономия: <code>{discount:,}</code> г.",
    "promo_code_cleared": "🗑️ Промокод удалён.",
    "promo_err_invalid": "❌ Промокод не найден или отключён.",
    "promo_err_expired": "⌛ Срок действия промокода истёк.",
    "promo_err_exhausted": "⚠️ Лимит использований промокода исчерпан.",
    "promo_err_min_order": "⚠️ Минимальный заказ для этого промокода: <code>{min_order:,}</code> г.",
    "promo_err_already_used": "⚠️ Вы уже использовали этот промокод!",
    "promo_err_code_race": "⚠️ Не удалось применить промокод (лимит исчерпан). Попробуйте без него.",

    "promo_kind_channel": "канал",
    "promo_kind_group": "группу",
    "promo_btn_pick_chat": "📣 Выбрать {kind}",
    "promo_target_chat_prompt": (
        "📌 <b>Выберите целевой {kind}:</b>\n\n"
        "⚠️ <b>Бот ДОЛЖЕН быть администратором в вашем чате ({kind}) для проверки подписок.</b>\n\n"
        "1️⃣ Нажмите кнопку «📣 Выбрать {kind}» ниже.\n"
        "2️⃣ Или отправьте вручную:\n"
        "<code>@username_или_ссылка | Название</code>\n"
        "Пример: <code>@MyChannel | Мой канал</code>"
    ),
    "promo_target_url_prompt": (
        "🔗 <b>Введите ссылку и название:</b>\n\n"
        "Разделите данные символом <code>|</code>:\n"
        "<code>Ссылка | Название{extra_hint}</code>\n\n"
        "Пример:\n<code>https://t.me/my_target/15 | Поддержка поста{extra_hint}</code>"
    ),
    "promo_err_bot_not_admin": (
        "❌ <b>Бот не является админом этого чата!</b> (Статус: <code>{status}</code>)\n"
        "Сделайте бота администратором и повторите попытку."
    ),
    "promo_err_invite_fetch": "⚠️ Не удалось получить ссылку автоматически. Отправьте вручную: <code>Ссылка | Название</code>",
    "promo_chat_verified": "✅ Чат успешно проверен!",
    "promo_err_target_format": "⚠️ Неверный формат. Используйте <code>|</code>:\n<code>@username_или_ссылка | Название</code>",
    "promo_err_bad_url": "❌ Введите корректную ссылку https:// или @username.",
    "promo_err_need_public_chat": "❌ Укажите публичный @username или выберите чат через кнопку.",

    "promo_auto_rx_badge_on": "\n⚡ <b>Проверка реакций:</b> Автоматически без скриншотов!",
    "promo_auto_rx_badge_off": "\n📸 <b>Проверка реакций:</b> По скриншотам (сделайте бота админом канала для автопроверки).",
    "promo_confirm_summary": (
        "📋 <b>Подтверждение кампании:</b>\n\n"
        "📌 <b>Название:</b> {title}\n"
        "📂 <b>Категория:</b> <code>{cat}</code>\n"
        "🔗 <b>Ссылка:</b> {url}\n"
        "👥 <b>Количество:</b> <code>{qty:,}</code>\n"
        "💵 <b>Награда исполнителю:</b> <code>{price:,}</code> г\n"
        "🌍 <b>Аудитория:</b> {audience}"
        "{rx_badge}\n"
        "💳 <b>К списанию:</b> <code>{total_gram:,}</code> г (Escrow-защита)"
    ),
    "promo_audience_all": "Все",
    "promo_btn_confirm_create": "✅ Подтвердить и запустить",
    "promo_err_expired_session": "❌ Данные кампании устарели, начните заново.",
    "promo_err_insufficient": "❌ Недостаточно средств на балансе!",
    "promo_created_alert": "🎉 Кампания успешно запущена!",
    "promo_created_msg": (
        "🚀 <b>Кампания (#{task_id}) запущена!</b>\n\n"
        "📌 <b>Название:</b> {title}\n"
        "🛡️ <b>Escrow резерв:</b> <code>{escrow:,}</code> г\n\n"
        "Управляйте кампанией в разделе «💼 Мои кампании»."
    ),
    "promo_btn_view_my": "💼 Мои кампании",

    "promo_settings_view": (
        "⚙️ <b>Настройки комиссий и Escrow:</b>\n\n"
        "🏅 <b>VIP уровень:</b> {level_title}\n"
        "📉 <b>Комиссия VIP:</b> <code>{vip_fee}%</code>\n"
        "🌟 <b>Тариф 0% (Telegram Stars):</b> {stars_status}\n\n"
        "🛡️ <b>Гарантия Escrow:</b>\n"
        "• Средства исполнителей резервируются в Escrow и списываются только после проверки.\n"
        "• При отмене кампании неиспользованный остаток возвращается на баланс."
    ),
    "promo_stars_on": "🟢 Активен до <code>{until} UTC</code> (0%)",
    "promo_stars_off": "⚪ Не активен",

    "promo_my_empty": "💼 <b>Мои кампании:</b>\n\nУ вас пока нет активных кампаний.",
    "promo_my_header": "💼 <b>Ваши кампании (нажмите для управления):</b>\n\n",
    "promo_my_btn_manage": "{icon} Кампания: {title}",
    "promo_task_view": (
        "💼 <b>Кампания #{task_id}:</b> {title}\n\n"
        "📊 <b>Прогресс:</b> <code>{completed}/{total}</code> (Осталось: {remaining})\n"
        "💵 <b>Цена за ед.:</b> <code>{reward:,}</code> г\n"
        "🛡️ <b>Остаток Escrow:</b> <code>{escrow:,}</code> г\n"
        "📌 <b>Статус:</b> <code>{status}</code>"
    ),
    "promo_btn_pause": "⏸️ Пауза",
    "promo_btn_resume": "▶️ Возобновить",
    "promo_btn_boost": "🚀 Поднять цену +100 г ({boost_cost:,})",
    "promo_btn_cancel": "🗑️ Отменить и вернуть остаток",
    "promo_btn_back_my": "🔙 К моим кампаниям",
    "promo_err_task_not_found": "❌ Кампания не найдена.",
    "promo_err_task_closed": "⚠️ Нельзя изменить завершённую или отменённую кампанию.",
    "promo_toggled_alert": "✅ Статус изменён на {status}",
    "promo_err_boost_closed": "⚠️ Кампания неактивна или завершена.",
    "promo_err_boost_balance": "❌ Недостаточно средств! Нужно {extra_cost:,} г.",
    "promo_boosted_alert": "🚀 Ставка повышена на +100 г!",
    "promo_err_already_closed": "⚠️ Кампания уже завершена или отменена.",
    "promo_cancelled_alert": "✅ Отменено! Возвращено +{refund:,} г на баланс!",
}
