AR_TEXTS = {
    # Onboarding, Language & Security Captcha
    "select_lang_first": "🌐 <b>يرجى اختيار لغتك المفضلة للبدء:</b>",
    "lang_select_title": "🌐 <b>اختر لغة البوت:</b>",
    "lang_changed": "✅ تم تغيير لغة البوت إلى <b>العربية</b> بنجاح!",
    "captcha_text": "🤖 <b>اختبار الأمان (الكابتشا):</b>\nيرجى حل المسألة التالية لإكمال التسجيل:\n\nكم يساوي: <code>{num1} + {num2}</code> ؟",
    "captcha_image_caption": "🛡️ <b>تحقق الأمان (ZetaGram):</b>\n\nانظر إلى الصورة واختر الإجابة الصحيحة من الأزرار أدناه.\n⏳ الصلاحية: دقيقتان.",
    "captcha_btn_refresh": "🔄 تحديث الصورة",
    "captcha_wrong": "❌ إجابة خاطئة! حاول مرة أخرى.",
    "captcha_expired": "⌛ انتهت صلاحية الكابتشا! تم توليد صورة جديدة.",
    "captcha_locked": "⛔ تم قفل محاولات الكابتشا مؤقتاً بسبب التكرار الخاطئ.\nيرجى الانتظار <b>{mins} دقيقة</b>.",
    "captcha_locked_alert": "⛔ محاولات الكابتشا مقفلة مؤقتاً.",
    "captcha_success": "🎉 تم اجتياز اختبار الكابتشا بنجاح!",
    "recaptcha_required": "🛡️ <b>تحقق أمني دوري:</b>\nأكملت {count} مهام بنجاح! يرجى حل الكابتشا السريعة للمتابعة.",
    "rate_limited": "⚠️ يرجى الانتظار قليلاً وعدم الضغط السريع!",
    "not_registered": "❌ لم يتم العثور على حسابك. يرجى كتابة /start لتسجيل الحساب.",
    "account_error": "❌ حدث خطأ في بيانات حسابك.",
    "banned_notice": "🚫 <b>حسابك محظور مؤقتاً من استخدام هذه الميزة!</b>\n\n⏳ ينتهي الحظر في: <code>{until}</code>\n⚠️ عدد المخالفات: {violations}",
    "forced_sub_required": "⚠️ <b>يجب الاشتراك في القنوات الإجبارية التالية للمتابعة:</b>\nاشترك في القنوات أدناه ثم اضغط على «تحقق الآن».",
    "forced_sub_ok": "✅ <b>حسابك مفعّل ومكتمل الاشتراك في جميع القنوات الإجبارية!</b>",
    "forced_sub_verified_alert": "✅ تم التحقق من الاشتراك بنجاح!",
    "forced_sub_missing_alert": "❌ لم تنضم لجميع القنوات الإجبارية بعد!",
    "btn_recheck_now": "🔄 تحقق الآن",
    "err_amount_min": "❌ المبلغ يجب أن يكون {min_val:,} على الأقل.",
    "err_amount_max": "❌ المبلغ يتجاوز الحد الأقصى المسموح به ({max_val:,}).",
    "err_amount_invalid": "❌ يرجى إدخال رقم صحيح.",

    # Main Menu Keyboard Buttons
    "btn_referrals": "👥 نظام الدعوات",
    "btn_bonus": "🎁 المكافأة اليومية",
    "btn_earnings": "🧑‍💻 الأرباح",
    "btn_promotion": "📣 الترويج",
    "btn_account": "📱 حسابي",
    "btn_vouchers": "🏷️ الشيكات",
    "btn_stats": "روبوتاتنا والإحصائيات 📊",
    "btn_check_sub": "فحص الاشتراك 📣",
    "btn_instructions": "📋 التعليمات",
    "btn_useful_links": "روابط مفيدة",
    "btn_language": "🌐 اللغة",
    "btn_leaderboard": "🏆 المتصدرين",
    "btn_settings": "⚙️ الإعدادات",
    "btn_back": "🔙 رجوع",
    "btn_close": "🔙 إغلاق",
    "btn_report": "🔴 تبليغ",
    "btn_cancel": "❌ إلغاء",

    # Welcome & Start
    "welcome": (
        "🚀 <b>مرحباً بك في ZetaGram!</b>\n\n"
        "أهلاً بك 👋 يا {name}\n\n"
        "منصة ذكية ومتكاملة لكسب الغرامات وترويج القنوات والمجموعات بأمان وموثوقية عالية. 🎉\n\n"
        "💎 <b>ماذا ينتظرك؟</b>\n"
        "• 💰 تنفيذ مهام سريعة وموثقة مقابل مكافآت.\n"
        "• 📣 الترويج للقنوات والمجموعات والبوتات باستهداف دقيق.\n"
        "• 👥 نظام دعوة الأصدقاء (+100 غرام فورية + 250 غرام + 10% عمولة).\n"
        "• 🎁 مكافآت يومية تصاعدية، تحدي يومي، وعجلة حظ.\n"
        "• 🏛️ خزنة استثمارية، يانصيب أسبوعي، ولوحة متصدرين."
    ),
    "welcome_join_bonus": "\n\n🎁 <b>هدية الدعوة:</b> تم إضافة <b>+{bonus:,} غرام</b> إلى رصيدك فور التفعيل!",
    "welcome_flash_banner": "\n\n🔥 <b>عرض ساعات الذروة (Flash Event) شغّال الآن!</b>\n<b>{title}</b> — أرباح مضاعفة <b>{mult}</b> حتى <code>{ends} UTC</code>!",

    # Flash Events & System Notifications
    "flash_banner_earnings": "🔥 <b>حدث ساعات الذروة نشط الآن: {title} ({mult})!</b>\n⏰ ينتهي في: <code>{ends} UTC</code> — كل المهام تمنح أرباحاً مضاعفة!\n\n",
    "flash_bonus_note": " (يشمل +{flash_bonus:,} غرام مكافأة {mult}🔥)",
    "flash_broadcast_notif": (
        "🔥 <b>انطلقت ساعات الذروة في {bot_name}!</b>\n\n"
        "🎉 <b>{title}</b>\n"
        "⚡ مضاعف الأرباح: <b>{mult}</b> على جميع المهام!\n"
        "⏳ العرض مستمر حتى: <code>{ends} UTC</code>\n\n"
        "سارع بتنفيذ المهام من قائمة الأرباح الآن!"
    ),
    "daily_quest_done": "🎯 <b>إنجاز التحدي اليومي!</b>\nأكملت {target} مهام اليوم وحصلت على مكافأة إضافية <b>+{reward:,} غرام</b>!",
    "notif_referral_milestone": "🎉 <b>مبروك!</b> لقد أكمل صديقك المدعو (<code>{invitee_id}</code>) 3 مهام، وتم إضافة <b>+{bonus:,} غرام</b> إلى رصيدك!",
    "notif_retention_reminder": "👋 <b>مرحباً {name}!</b> نسينا أن نذكرك بالمكافأة اليومية في ZetaGram! 🎁\n\nادخل البوت الآن واحصل على مكافأتك التصاعدية + عجلة الحظ والتحدي اليومي! 🎡",
    "notif_proof_auto_approved_worker": "✅ <b>تمت الموافقة التلقائية على إثباتك!</b>\nالمهمة: <b>{title}</b>\n💰 تمت إضافة <b>+{reward:,} غرام</b> إلى رصيدك بعد انتهاء مهلة المراجعة.",
    "notif_proof_auto_approved_creator": "⏱️ <b>اعتماد تلقائي لإثبات معلق:</b>\nتم اعتماد إثبات المستخدم <code>{worker_id}</code> في مهمة <b>{title}</b> تلقائياً لتجاوز مهلة {hours} ساعة.",
    "notif_leaderboard_winner": "🏆 <b>مبروك! فزت بجائزة المتصدرين الأسبوعية ({week_key})!</b>\n📌 التصنيف: <b>{category}</b>\n🎁 الجائزة: <b>+{prize:,} غرام</b> تم إضافتها لرصيدك!",
    "notif_unsub_penalty": (
        "⚠️ <b>تنبيه مخالفة وحظر!</b>\n\n"
        "لقد قمت بإلغاء الاشتراك من القناة/المجموعة: <code>{title}</code> قبل مرور 7 أيام.\n"
        "• 🔴 تم خصم <b>-{deducted:,}</b> غرام من رصيدك.\n"
        "• 🚫 تم فرض حظر من تنفيذ المهام لمدة: <b>{duration}</b>.\n"
        "• ⚠️ عدد المخالفات المسجلة عليك: {violations}"
    ),
    "ban_dur_24h": "24 ساعة",
    "ban_dur_7d": "7 أيام",
    "ban_dur_perm": "دائم",

    # VIP Titles, Milestones & Transaction Types
    "vip_title_1": "🥉 مبتدئ",
    "vip_title_2": "🥈 نشيط",
    "vip_title_3": "🥇 خبير",
    "vip_title_4": "💎 VIP مميز",
    "ms_tasks_10": "إكمال 10 مهام",
    "ms_tasks_50": "إكمال 50 مهمة",
    "ms_tasks_100": "إكمال 100 مهمة",
    "ms_refs_10": "دعوة 10 أصدقاء",
    "tx_type_earn_task": "🧑‍💻 كسب مهمة",
    "tx_type_spend_promo": "📣 إنشاء ترويج",
    "tx_type_promo_refund": "↩️ استرداد ترويج",
    "tx_type_voucher_claim": "🎁 استبدال شيك",
    "tx_type_voucher_create": "🏷️ إنشاء شيك",
    "tx_type_voucher_refund": "↩️ استرداد شيك",
    "tx_type_transfer_send": "💸 تحويل مرسل",
    "tx_type_transfer_receive": "📥 تحويل مستلم",
    "tx_type_daily_bonus": "🎁 مكافأة يومية",
    "tx_type_daily_quest": "🎯 تحدي يومي",
    "tx_type_spin": "🎡 عجلة الحظ",
    "tx_type_admin_adjust": "⚙️ تعديل أدمن",
    "tx_type_reward": "🏅 مكافأة",
    "tx_type_referral_milestone": "👥 مكافأة إحالة",
    "tx_type_referral_commission": "💎 عمولة إحالة",
    "tx_type_vault_deposit": "🏛️ إيداع خزنة",
    "tx_type_vault_withdraw": "💰 سحب خزنة",
    "tx_type_raffle_buy": "🎫 شراء تذكرة",
    "tx_type_raffle_win": "🏆 فوز يانصيب",
    "tx_type_unsub_penalty": "⚠️ خصم إلغاء اشتراك",
    "tx_type_leaderboard_prize": "🏆 جائزة متصدرين",
    "tx_type_default": "💰 معاملة",

    # Account & Settings
    "account_summary": (
        "📱 <b>معلومات حسابك في {bot_name}:</b>\n\n"
        "🆔 <b>معرف الحساب:</b> <code>{telegram_id}</code>\n"
        "👤 <b>الاسم:</b> {first_name}\n"
        "🏅 <b>المستوى:</b> {level_title}\n"
        "🛡️ <b>نقاط الثقة:</b> <code>{trust_score}/200</code>\n"
        "🔥 <b>سلسلة الدخول اليومي:</b> <code>{streak}</code> يوم\n"
        "🎯 <b>التحدي اليومي:</b> <code>{quest_progress}/{quest_target}</code> مهام\n"
        "💰 <b>الرصيد:</b> <code>{balance:,}</code> غرام\n"
        "✅ <b>المهام المكتملة:</b> {completed_count}\n"
        "👥 <b>عدد الإحالات:</b> {referrals_count}\n\n"
        "🔗 <b>رابط الإحالة الخاص بك:</b>\n"
        "<code>{ref_link}</code>\n\n"
        "🎁 شارك رابط الإحالة مع أصدقائك واكسب مكافآت فورية وعمولة 10%!"
    ),
    "account_btn_levels": "🏅 الإنجازات والمستويات",
    "account_btn_history": "📜 سجل المعاملات",
    "account_btn_vault": "🏛️ الخزنة والاستثمار",
    "account_btn_raffle": "🎟️ اليانصيب والسحب",
    "account_btn_transfer": "💸 تحويل رصيد",
    "account_btn_vouchers": "🏷️ الشيكات والكوبونات",
    "account_btn_leaderboard": "🏆 لوحة المتصدرين",
    "account_btn_settings": "⚙️ الإعدادات",

    "settings_title": (
        "⚙️ <b>إعدادات الحساب وحالة الثقة:</b>\n\n"
        "🔔 <b>إشعارات التذكير والعروض:</b> {notif_str}\n"
        "🌐 <b>اللغة الحالية:</b> <code>{lang}</code>\n"
        "🏅 <b>المستوى:</b> {level_title}\n"
        "🛡️ <b>نقاط الثقة:</b> <code>{trust_score}/200</code>\n"
        "⚠️ <b>عدد المخالفات:</b> <code>{violations}</code>"
    ),
    "settings_notif_on": "🔔 مفعّلة",
    "settings_notif_off": "🔕 متوقفة",
    "settings_btn_disable_notif": "🔕 إيقاف التذكيرات",
    "settings_btn_enable_notif": "🔔 تفعيل التذكيرات",
    "settings_btn_change_lang": "🌐 تغيير اللغة",
    "settings_notif_enabled_alert": "🔔 تم تفعيل التذكيرات.",
    "settings_notif_disabled_alert": "🔕 تم إيقاف التذكيرات.",

    # Info & Public Stats
    "info_useful_links": (
        "🔗 <b>الروابط المفيدة ({bot_name}):</b>\n\n"
        "{links_str}"
        "💡 اضغط على الروابط أعلاه لمتابعة آخر التحديثات وأخبار الشبكة."
    ),
    "info_no_links": "لا توجد روابط إضافية مضافة حالياً.\n\n",
    "default_official_channel": "القناة الرسمية",
    "info_instructions": (
        "📋 <b>دليل وتعليمات استخدام {bot_name}:</b>\n\n"
        "1️⃣ <b>كسب الأرباح:</b> اختر «🧑‍💻 الأرباح» واشترك في القنوات أو نفّذ مهام التفاعلات والبوتات والمنشورات.\n"
        "2️⃣ <b>الترويج لقناتك:</b> اختر «📣 الترويج» وحدد النوع والجمهور والسعر مع ضمان مالي Escrow كامل وأكواد خصم.\n"
        "3️⃣ <b>المكافأة اليومية والتحدي:</b> سلسلة دخول يومي تصاعدية حتى +500 غرام + "
        "تحدي {quest_target} مهام يومية (+{quest_reward} غرام) + عجلة الحظ (<code>/spin</code>).\n"
        "4️⃣ <b>نظام الإحالة:</b> ادعُ أصدقاءك واكسب "
        "+{ref_active_bonus} غرام عن كل صديق نشط + <b>10% عمولة دائمة</b> (ويحصل صديقك على +{ref_join_bonus} غرام).\n"
        "5️⃣ <b>الخزنة واليانصيب والشيكات:</b> استثمر رصيدك في الخزنة (<code>/vault</code>) أو شارك باليانصيب (<code>/raffle</code>).\n\n"
        "⚠️ <b>ملاحظة هامة:</b> يُمنع مغادرة القنوات قبل 7 أيام لتجنب الخصم التلقائي والحظر."
    ),
    "info_public_stats": (
        "📊 <b>إحصائيات شبكة {bot_name}:</b>\n\n"
        "👥 <b>إجمالي المستخدمين:</b> <code>{users_cnt:,}</code>\n"
        "📌 <b>إجمالي الحملات:</b> <code>{tasks_cnt:,}</code>\n"
        "✅ <b>المهام المنفذة بنجاح:</b> <code>{completed_cnt:,}</code>\n"
        "⚡ <b>سرعة التحقق:</b> فوري وآمن 100%"
    ),
    "info_btn_leaderboard": "🏆 لوحة المتصدرين الأسبوعية",

    # Referrals
    "ref_menu": (
        "👥 <b>نظام دعوة الأصدقاء والمكافآت ({bot_name}):</b>\n\n"
        "قم بدعوة أصدقائك لاستخدام البوت واكسب مكافآت حقيقية ومستمرة!\n\n"
        "📊 <b>إحصائيات إحالاتك:</b>\n"
        "• 👥 <b>إجمالي المدعوين:</b> <code>{total_invites}</code> عضو\n"
        "• ⚡ <b>الأصدقاء النشطون (أكملوا 3 مهام):</b> <code>{active_invites}</code> عضو\n"
        "• 💰 <b>إجمالي أرباحك من الإحالات:</b> <code>{total_earned:,}</code> غرام\n\n"
        "🎁 <b>تفاصيل المكافآت:</b>\n"
        "• يحصل صديقك على <b>+{join_bonus:,} غرام</b> فور الانضمام واجتياز الكابتشا.\n"
        "• تحصل أنت على <b>+{active_bonus:,} غرام</b> فور إكمال صديقك 3 مهام.\n"
        "• وتحصل على <b>10% عمولة دائمة</b> من أرباح أصدقائك في كل مهمة!\n\n"
        "🔗 <b>رابط الدعوة الخاص بك:</b>\n"
        "<code>{ref_link}</code>"
    ),
    "ref_btn_share": "📤 مشاركة رابط الدعوة",
    "ref_share_text": "اشترك في بوت {bot_name} لكسب الغرامات وترويج القنوات والمجموعات!",
    "ref_btn_list": "👥 قائمة المدعوين",
    "ref_list_empty": "👥 <b>قائمة المدعوين:</b>\n\nلم يقم أحد بالانضمام عبر رابطك بعد. انشر رابطك واكسب المكافآت!",
    "ref_list_title": "👥 <b>قائمة الأعضاء المدعوين ({count}):</b>\n\n",
    "ref_status_active": "✅ (نشط)",
    "ref_status_pending": "⌛ ({cnt}/3 مهام)",

    # Leaderboard
    "lb_title": "🏆 <b>لوحة المتصدرين الأسبوعية (Weekly Leaderboard)</b>\n",
    "lb_tab_tasks_title": "✅ <b>أفضل منفذي المهام هذا الأسبوع:</b>\n",
    "lb_tab_refs_title": "👥 <b>أفضل الداعين هذا الأسبوع:</b>\n",
    "lb_unit_tasks": "مهمة",
    "lb_unit_refs": "إحالة",
    "lb_empty": "لا يوجد نشاط مسجل هذا الأسبوع بعد — كن أول المتصدرين!\n",
    "lb_row": "{medal} <b>{name}</b>: <code>{cnt}</code> {unit}{prize_note}",
    "lb_prize_note": " — 🎁 <code>+{prize:,}</code> غرام",
    "lb_footer": (
        "\n📊 <b>نتيجتك هذا الأسبوع:</b> <code>{my_score}</code> {unit}\n"
        "🎁 <b>جوائز المراكز الثلاثة الأولى:</b> "
        "🥇 {p1:,} | 🥈 {p2:,} | 🥉 {p3:,} غرام"
    ),
    "lb_btn_tasks": "أفضل المنفذين",
    "lb_btn_refs": "أفضل الداعين",

    # Levels & Milestones
    "levels_menu": (
        "🏅 <b>قسم الإنجازات ومستويات VIP:</b>\n\n"
        "👤 <b>مستواك الحالي:</b> {level_title}\n"
        "✅ <b>المهام المكتملة:</b> {completed_tasks}\n"
        "👥 <b>الأعضاء المدعوين:</b> {referrals}\n\n"
        "✨ <b>مزايا مستواك الفعلية:</b>\n"
        "• 📣 عمولة الترويج: <code>{promo_fee}%</code>\n"
        "• 💸 عمولة التحويل: <code>{transfer_fee}%</code>\n"
        "• 💰 مكافأة إضافية على المهام: <code>+{task_bonus}%</code>\n"
        "• 🏛️ عائد إضافي للخزنة: <code>+{vault_bonus}%</code>\n\n"
        "🎁 <b>المكافآت والإنجازات المتاحة:</b>"
    ),
    "levels_btn_claimed": "✅ {title} (تم الاستلام)",
    "levels_btn_claim": "🎁 استلام مكافأة: {title} (+{reward:,} غرام)",
    "levels_btn_locked": "🔒 {title} (+{reward:,} غرام)",
    "levels_err_unknown": "❌ إنجاز غير معروف",
    "levels_err_already": "⚠️ لقد قمت باستلام هذه المكافأة مسبقاً!",
    "levels_err_requirements": "❌ لم تحقق متطلبات هذا الإنجاز بعد!",
    "levels_claimed_alert": "🎉 مبروك! تم إضافة +{reward:,} غرام وتحديث مستواك!",

    # Transaction History
    "history_empty": "📜 <b>سجل المعاملات:</b>\n\nلا توجد معاملات مسجلة في حسابك حتى الآن.",
    "history_title": "📜 <b>سجل المعاملات (صفحة {page}/{total_pages}):</b>\n\n",
    "history_row": "{icon}\n🔹 المبلغ: <code>{sign}{amount:,}</code> غرام\n{details_line}⏱️ التاريخ: {dt_str}\n─────────────────\n",
    "history_details_line": "💬 التفاصيل: {desc}\n",
    "history_btn_prev": "◀️ السابق",
    "history_btn_next": "التالي ▶️",

    # Daily Bonus & Lucky Spin
    "bonus_already_claimed": (
        "⌛ <b>لقد حصلت على مكافأتك اليومية بالفعل!</b>\n\n"
        "🔥 سلسلتك الحالية: <b>{streak} يوم</b>\n"
        "يمكنك المطالبة بالمكافأة القادمة بعد: <b>{hours} ساعة و {minutes} دقيقة</b>."
    ),
    "bonus_claimed_success": (
        "🎁 <b>مبروك! تم إضافة المكافأة اليومية إلى رصيدك!</b>\n\n"
        "🔥 <b>سلسلة الدخول المتتالية:</b> اليوم <b>{streak}</b>\n"
        "💰 <b>الهدية المستلمة:</b> +{reward:,} غرام\n"
        "💳 <b>رصيدك الحالي:</b> {balance:,} غرام\n\n"
        "✨ مكافأتك غداً ستكون: <b>+{next_reward:,} غرام</b>!"
    ),
    "spin_already_used": (
        "⌛ <b>لقد استخدمت لفة اليوم بالفعل!</b>\n\n"
        "يمكنك تدوير عجلة الحظ مجدداً بعد: <b>{hours} ساعة و {minutes} دقيقة</b>."
    ),
    "spin_rolling_1": "🎰 <b>جاري تدوير عجلة الحظ...</b>\n\n🌀 <code>[ 100 | 500 | 50 | 1000 | 250 | 2000 ]</code> 🌀",
    "spin_rolling_2": "🎰 <b>جاري التدوير... ⚡</b>\n\n🌀 <code>[ 250 | 2000 | 50 | 500 | 1000 ]</code> 🌀",
    "spin_jackpot_badge": "🎉 <b>الجائزة الكبرى (JACKPOT)!</b> 🎉\n",
    "spin_result": (
        "🎰 <b>نتيجة عجلة الحظ:</b>\n\n"
        "{badge}"
        "🎁 <b>مبروك! فزت بـ:</b> <code>+{prize:,}</code> غرام!\n"
        "💳 <b>رصيدك الحالي:</b> <code>{balance:,}</code> غرام\n\n"
        "عد غداً لتدوير العجلة والحصول على الجائزة القادمة! 🎡"
    ),

    # Savings Vault
    "vault_menu": (
        "🏛️ <b>خزنة التوفير والأرباح (Savings Vault):</b>\n\n"
        "جمّد غراماتك في الخزنة واحصل على عوائد مجانية مضافة لرصيدك!\n\n"
        "💳 <b>رصيدك المتاح:</b> <code>{balance:,}</code> غرام\n"
        "📦 <b>الودائع النشطة:</b> <code>{active_count}/{max_active}</code>\n"
        "🏅 <b>عائد إضافي لمستواك ({level_title}):</b> <code>+{bonus_pct}%</code>\n\n"
        "📈 <b>خطط الاستثمار المتاحة:</b>\n"
        "1️⃣ <b>خطة 7 أيام:</b> عائد أساسي <b>+5%</b> (+ عائد VIP).\n"
        "2️⃣ <b>خطة 30 يوم:</b> عائد أساسي <b>+20%</b> (+ عائد VIP).\n"
        "🔒 الحد الأقصى للإيداع الواحد: <code>{max_deposit:,}</code> غرام."
    ),
    "vault_btn_7d": "➕ إيداع 7 أيام (+5%)",
    "vault_btn_30d": "➕ إيداع 30 يوم (+20%)",
    "vault_btn_my": "📜 ودائعي واسترداد الأرباح",
    "vault_prompt": (
        "➕ <b>إنشاء إيداع جديد ({days} يوم - عائد أساسي +{rate_pct}%):</b>\n\n"
        "يرجى إرسال مبلغ الغرامات المراد تجميده في الشات مباشرة "
        "(الحد الأدنى: 500، الحد الأقصى: {max_deposit:,} غرام)."
    ),
    "vault_err_insufficient": "❌ رصيدك الحالي غير كافٍ لإتمام هذا الإيداع.",
    "vault_err_max_active": "⚠️ وصلت للحد الأقصى للودائع النشطة ({max_active}). انتظر فك وديعة قبل إنشاء جديدة.",
    "vault_deposit_created": (
        "🎉 <b>تم إنشاء الإيداع بنجاح!</b>\n\n"
        "💰 <b>المبلغ المجمد:</b> <code>{amount:,}</code> غرام\n"
        "📈 <b>الأرباح المتوقعة:</b> <code>+{yield_amount:,}</code> غرام\n"
        "⏱️ <b>تاريخ الفك والتصفية:</b> <code>{lock_until}</code>"
    ),
    "vault_my_empty": "🏛️ <b>ودائعي في الخزنة:</b>\n\nلا توجد لديك أي ودائع حالياً.",
    "vault_my_header": "🏛️ <b>ودائعي في الخزنة:</b>\n\n",
    "vault_row_withdrawn": "✅ <b>إيداع منتهي #{dep_id}</b> ({days} يوم)\n المبلغ: <code>{amount:,}</code> + أرباح <code>{yield_amount:,}</code> غرام\n\n",
    "vault_row_active": "🔹 <b>إيداع #{dep_id}</b> ({days} يوم) | {status}\n المبلغ: <code>{amount:,}</code> | الأرباح: <code>+{yield_amount:,}</code> غرام\n\n",
    "vault_status_ready": "🟢 جاهز للاسترداد",
    "vault_status_locked": "⏳ متبقي حتى {date}",
    "vault_btn_withdraw": "🎁 استرداد إيداع #{dep_id} مع الأرباح",
    "vault_err_not_found": "❌ تعذر العثور على هذا الإيداع أو تم استرداده مسبقاً.",
    "vault_err_not_matured": "⏳ لم ينتهي وقت التجميد بعد!",
    "vault_withdrawn_alert": "🎉 تم استرداد +{total_payout:,} غرام إلى رصيدك بنجاح!",

    # Weekly Raffle
    "raffle_menu": (
        "🎟️ <b>نظام السحب واليانصيب الأسبوعي (Weekly Raffle):</b>\n\n"
        "اشترِ تذاكر الدخول ونافس باقي الأعضاء على مسبح الجوائز الأسبوعي الضخم!\n\n"
        "🏆 <b>مسبح الجوائز الحالي:</b> <code>{prize_pool:,}</code> غرام\n"
        "🎫 <b>تذكرتك الحالية في هذا السحب:</b> <code>{user_tickets}</code> تذكرة\n"
        "👥 <b>إجمالي تذاكر المشاركين:</b> <code>{total_tickets}</code> تذكرة\n"
        "💰 <b>سعر التذكرة الواحدة:</b> <code>{ticket_price:,}</code> غرام\n"
        "💳 <b>رصيدك المتاح:</b> <code>{balance:,}</code> غرام\n"
    ),
    "raffle_btn_buy_1": "🎫 شراء تذكرة واحدة (100 غرام)",
    "raffle_btn_buy_5": "🎟️ شراء 5 تذاكر (500 غرام)",
    "raffle_btn_my": "📜 تذاكري في السحب",
    "raffle_btn_admin_draw": "🎲 إعلان الفائز والسحب الآن (أدمن)",
    "raffle_err_invalid_qty": "❌ عدد التذاكر غير صالح.",
    "raffle_err_insufficient": "❌ رصيدك الحالي غير كافٍ لشراء التذاكر!",
    "raffle_buy_success": "🎉 تم شراء {count} تذكرة يانصيب بنجاح!",
    "raffle_my_empty": "🎫 <b>تذاكري في السحب الحالي:</b>\n\nلم تقم بشراء أي تذاكر في السحب الحالي بعد.",
    "raffle_my_list": "🎫 <b>تذاكرك الحالية (#Draw-{draw_id}):</b>\n\nإجمالي عدد تذاكرك: <code>{count}</code>\nأكواد التذاكر:\n{codes}",
    "raffle_draw_empty": "❌ لا يوجد سحب نشط أو لا توجد تذاكر مشاركة بعد!",
    "raffle_draw_no_tickets": "❌ لم يقم أحد بشراء تذاكر في هذا السحب بعد.",
    "raffle_draw_done_alert": "🎲 تم السحب وإعلان الفائز بنجاح!",
    "raffle_draw_summary": (
        "🎉 <b>مبروك للفائز بسحب اليانصيب الأسبوعي!</b> 🎉\n\n"
        "🏆 <b>الجائزة الكبرى:</b> <code>+{prize:,}</code> غرام!\n"
        "👤 <b>الفائز:</b> <code>{winner_id}</code>\n"
        "🎫 <b>رقم التذكرة الفائزة:</b> <code>{ticket_code}</code>\n\n"
        "تم السحب عشوائياً بنجاح وإضافة الجائزة إلى رصيد الفائز. تم بدء سحب أسبوعي جديد الآن! 🚀"
    ),
    "raffle_winner_dm": "🥳 <b>مبروك! فزت بالسحب الأسبوعي لليانصيب!</b>\nتم إضافة <b>+{prize:,} غرام</b> إلى حسابك!",

    # Vouchers
    "vouchers_menu": (
        "🏷️ <b>قسم الشيكات والكوبونات:</b>\n\n"
        "يمكنك استبدال الشيكات التي تملكها أو إنشاء شيكات هدايا لأصدقائك أو لقناتك خصماً من رصيدك.\n\n"
        "يمكنك أيضاً استخدام التعليمة السريعة للإنشاء:\n"
        "<code>/createvoucher &lt;المبلغ&gt; &lt;عدد_الاستخدامات&gt;</code>"
    ),
    "vouchers_btn_redeem": "🎁 استبدال شيك",
    "vouchers_btn_create": "➕ إنشاء شيك جديد",
    "vouchers_btn_my": "📜 شيكاتي المنشأة وإلغاؤها",
    "voucher_prompt_redeem": "🎁 <b>استبدال شيك:</b>\n\nيرجى إرسال رمز الشيك في الشات مباشرة (مثال: <code>GRAM-ABCD-1234</code>).",
    "voucher_prompt_create": (
        "➕ <b>إنشاء شيك جديد:</b>\n\n"
        "يرجى إرسال المبلغ وعدد مرات الاستخدام مفصولة بمسافة:\n"
        "<code>&lt;المبلغ_لكل_استخدام&gt; &lt;عدد_المستخدمين&gt;</code>\n\n"
        "مثال: <code>500 10</code> (إنشاء شيك بـ 500 غرام لـ 10 أعضاء)."
    ),
    "voucher_cmd_usage": (
        "⚠️ <b>الاستخدام الخاطئ!</b>\n"
        "الصيغة:\n"
        "<code>/createvoucher &lt;المبلغ&gt; [عدد_الاستخدامات]</code>\n\n"
        "مثال: <code>/createvoucher 500 5</code>"
    ),
    "voucher_err_enter_amount": "❌ يرجى إدخال المبلغ.",
    "voucher_err_new_account": (
        "🛡️ <b>حماية الحسابات الجديدة:</b>\n"
        "يجب إكمال <b>{min_tasks} مهام</b> على الأقل قبل إنشاء الشيكات (مهامك الحالية: {completed}/{min_tasks})."
    ),
    "voucher_err_insufficient": (
        "❌ رصيدك غير كافٍ!\n"
        "المبلغ الإجمالي المطلوب: {total_cost:,} غرام ({amount:,} × {max_uses})\n"
        "رصيدك الحالي: {balance:,} غرام"
    ),
    "voucher_created": (
        "🎉 <b>تم إنشاء الشيك بنجاح!</b>\n\n"
        "🏷️ <b>رمز الشيك:</b> <code>{code}</code>\n"
        "💰 <b>قيمة الاستخدام:</b> {amount:,} غرام\n"
        "👥 <b>الحد الأقصى للاستخدام:</b> {max_uses} أعضاء\n"
        "💳 <b>التكلفة المخصومة:</b> {total_cost:,} غرام\n\n"
        "🔗 <b>رابط الشيك المباشر:</b>\n<code>{v_link}</code>"
    ),
    "voucher_locked_bruteforce": "⛔ <b>تم قفل إدخال الشيكات لمحاولات التخمين!</b>\nيرجى الانتظار <b>{mins} دقيقة</b> قبل المحاولة مجدداً.",
    "voucher_locked_now": "⛔ <b>تم حظر استخدام الشيكات لحسابك لمدة 15 دقيقة بسبب تكرار إدخال أكواد خاطئة!</b>",
    "voucher_invalid_attempt": "❌ رمز الشيك غير صحيح أو ملغى. (محاولة {attempts}/5)",
    "voucher_exhausted": "⚠️ هذا الشيك تم استخدامه بالكامل بالحد الأقصى.",
    "voucher_already_used": "⚠️ لقد قمت باستبدال هذا الشيك مسبقاً!",
    "voucher_redeemed_success": "🎉 تم شحن رصيدك بنجاح بمقدار <b>+{amount:,} غرام</b>!",
    "voucher_my_empty": "📜 <b>شيكاتي المنشأة:</b>\n\nلم تقم بإنشاء أي شيكات حتى الآن.",
    "voucher_my_header": "📜 <b>آخر 10 شيكات قمت بإنشائها:</b>\n\n",
    "voucher_row": "🏷️ <code>{code}</code> — {amount:,} غرام | {status}\n",
    "voucher_status_active": "🟢 متبقي {rem}/{max_uses}",
    "voucher_status_done": "⚪ مكتمل/ملغى",
    "voucher_btn_cancel": "🗑️ إلغاء {code} واسترداد {refund:,}",
    "voucher_err_not_owner": "❌ الشيك غير موجود أو لا تملكه.",
    "voucher_err_not_found": "❌ الشيك غير موجود.",
    "voucher_err_already_done": "⚠️ هذا الشيك مستهلك أو ملغى بالفعل.",
    "voucher_cancelled_alert": "✅ تم إلغاء الشيك واسترداد +{refund:,} غرام!",

    # Balance Transfers
    "transfer_menu": (
        "💸 <b>نظام تحويل الرصيد بين الأعضاء:</b>\n\n"
        "يمكنك إرسال غرامات من رصيدك لأي عضو آخر باستخدام معرفه (Telegram ID).\n"
        "• 💵 <b>الحد الأدنى للتحويل:</b> <code>{min_amt:,}</code> غرام\n"
        "• 📊 <b>الحد الأقصى اليومي:</b> <code>{daily_limit:,}</code> غرام\n"
        "• 📉 <b>عمولتك الحالية ({level_title}):</b> <code>{fee_pct}%</code>\n\n"
        "استخدم التعليمة المباشرة:\n"
        "<code>/transfer &lt;ID&gt; &lt;المبلغ&gt;</code>\n\n"
        "أو اضغط على الزر أدناه للتحويل التفاعلي."
    ),
    "transfer_btn_start": "💸 بدء تحويل رصيد",
    "transfer_prompt": (
        "💸 <b>تحويل رصيد:</b>\n\n"
        "أرسل آيدي المستلم والمبلغ مفصولين بمسافة:\n"
        "<code>&lt;ID_المستلم&gt; &lt;المبلغ&gt;</code>\n\n"
        "مثال: <code>123456789 500</code>"
    ),
    "transfer_prompt_err": "⚠️ يرجى إرسال الآيدي والمبلغ مفصولين بمسافة، مثال: <code>123456789 500</code>",
    "transfer_cmd_usage": (
        "⚠️ <b>الاستخدام الخاطئ!</b>\n"
        "الصيغة الصحيحة:\n"
        "<code>/transfer &lt;ID_المستلم&gt; &lt;المبلغ&gt;</code>\n\n"
        "مثال: <code>/transfer 123456789 500</code>"
    ),
    "transfer_err_bad_id": "❌ يرجى إدخال آيدي مستلم صحيح.",
    "transfer_err_self": "❌ لا يمكنك تحويل الرصيد لنفسك!",
    "transfer_err_target_not_found": "❌ لم يتم العثور على مستخدم بهذا الآيدي في البوت!",
    "transfer_err_new_account": (
        "🛡️ <b>حماية الحسابات الجديدة:</b>\n"
        "يجب إكمال <b>{min_tasks} مهام</b> على الأقل قبل تفعيل ميزة تحويل الرصيد (مهامك: {completed}/{min_tasks})."
    ),
    "transfer_err_daily_limit": (
        "⛔ <b>تجاوزت الحد اليومي للتحويلات ({daily_limit:,} غرام)!</b>\n"
        "المتبقي لك اليوم: <code>{rem_limit:,}</code> غرام."
    ),
    "transfer_err_insufficient": (
        "❌ رصيدك غير كافٍ!\n"
        "المبلغ المراد تحويله: {amount:,}\n"
        "العمولة ({fee_pct}%): {fee:,}\n"
        "إجمالي المطلوب خصمه: {total_deduct:,} غرام\n"
        "رصيدك الحالي: {balance:,} غرام"
    ),
    "transfer_success_sender": (
        "🎉 <b>تم التحويل بنجاح!</b>\n\n"
        "👤 المستلم: <code>{target_id}</code>\n"
        "💰 المبلغ المحول: {amount:,} غرام\n"
        "📉 العمولة: {fee:,} غرام\n"
        "💳 رصيدك المتبقي: {sender_bal:,} غرام"
    ),
    "transfer_received_dm": (
        "🎁 <b>وصلك تحويل رصيد جديد!</b>\n\n"
        "قام العضو <code>{sender_id}</code> بتحويل <b>+{amount:,} غرام</b> إلى حسابك.\n"
        "💳 رصيدك الجديد: {receiver_bal:,} غرام"
    ),

    # Earnings Menus & Task Execution & Auto-Reactions
    "earnings_menu": (
        "📣 مهام القنوات: {channel_count}\n"
        "👤 مهام المجموعات: {group_count}\n"
        "👁️ مهام المشاهدة: {post_count}\n"
        "🤖 مهام البوت: {bot_count}\n"
        "⚡ مهام الشحن: {premium_count}\n"
        "🔥 مهام التفاعل: {reactions_count}\n\n"
        "🔔 اختر طريقة الكسب 👇"
    ),
    "earnings_btn_channel": "📣 اشترك في القناة",
    "earnings_btn_group": "👥 انضم إلى المجموعة",
    "earnings_btn_post": "👁️ عرض المنشورات",
    "earnings_btn_bot": "🤖 الانتقال إلى البوت",
    "earnings_btn_reactions": "🔥 تفاعلات",
    "earnings_btn_premium": "⚡ شحن بريميوم",
    "earnings_btn_rules": "📕 القواعد",
    "earnings_bot_menu": (
        "اختر فئة البوت.\n"
        "العادية: {bot_normal}\n"
        "الويب: {bot_webapp}\n"
        "مع الشروط: {bot_conditions}\n\n"
        "📱 <b>بوتات مع Web App</b>\n"
        "بوتات تملك تكاملاً مع تطبيقات الويب.\n\n"
        "🤖 <b>بوتات عادية</b>\n"
        "بوتات تليجرام التقليدية دون واجهات ويب إضافية.\n\n"
        "📋 <b>بوتات بشروط إضافية</b>\n"
        "يجب تنفيذ إجراءات إضافية: اجتياز كابتشا، اختيار لغة، أو الاشتراك في قنوات."
    ),
    "earnings_btn_bot_normal": "🤖 بوتات عادية",
    "earnings_btn_bot_webapp": "📱 بوتات مع Web App",
    "earnings_btn_bot_conditions": "📋 مع شروط إضافية",
    "earnings_reactions_menu": (
        "اختر فئة التفاعل.\n"
        "أي تفاعل: {reaction_random}\n"
        "التفاعل المحدد: {reaction_fixed}\n\n"
        "أي تفاعل – يمكنك اختيار ما تريد للحصول على الدفع.\n\n"
        "التفاعل المحدد – يجب استخدام التفاعل المذكور للدفع."
    ),
    "earnings_btn_reaction_random": "🎲 تفاعلات عشوائية",
    "earnings_btn_reaction_fixed": "🎯 تفاعلات ثابتة",
    "earnings_rules_text": (
        "📕 <b>قواعد تنفيذ المهام:</b>\n\n"
        "يُمنع إلغاء الاشتراك من القنوات/المجموعات قبل مرور <b>7 أيام</b>.\n"
        "مخالفة القاعدة تعني خصم المكافأة تلقائياً، خفض نقاط الثقة، وحظر تنفيذ المهام:\n\n"
        "• مخالفة أولى – حظر 24 ساعة\n"
        "• مخالفتان – حظر 7 أيام\n"
        "• ثلاث مخالفات أو أكثر – <b>حظر دائم</b>"
    ),
    "premium_only_alert": "⚡ فئة الشحن متاحة فقط لمستخدمي Telegram Premium",

    "task_list_channel_header": (
        "📣 <b>اختر مهمة للاشتراك ثم اضغط «🔄 فحص»:</b>\n\n"
        "⚠️ يُمنع مغادرة القنوات/المجموعات قبل 7 أيام، وإلا سيتم خصم المكافأة وحظر حسابك من المهام."
    ),
    "task_list_post_header": (
        "👁️ <b>مهام مشاهدة المنشورات:</b>\n\n"
        "اضغط على المهمة لفتح المنشور وانتظر {seconds} ثوانٍ ثم اضغط استلام."
    ),
    "task_list_reactions_header": (
        "🔥 <b>مهام التفاعلات:</b>\n\n"
        "تفاعَل مع المنشور؛ المهام التي تحمل ⚡ تُوثَّق تلقائياً فور تفاعلك بدون لقطة شاشة!"
    ),
    "task_list_premium_header": (
        "⚡ <b>مهام Telegram Premium الحصرية:</b>\n\n"
        "مكافآت مضاعفة لمشتركي بريميوم! اختر مهمة للبدء:"
    ),
    "task_list_bot_header": (
        "🤖 <b>مهام البوتات:</b>\n\n"
        "اختر مهمة للدخول إلى البوت والتحقق التلقائي أو إرسال لقطة شاشة."
    ),
    "task_list_empty": "❌ لا توجد مهام متاحة لك حالياً",
    "task_btn_subscribe_item": "اشتراك | +{reward:,} 💰",
    "task_btn_check": "🔄 فحص",
    "task_btn_post_item": "👁️ مشاهدة منشور +{reward:,} غرام",
    "task_btn_bot_item": "🤖 تنفيذ البوت | +{reward:,} غرام",
    "task_btn_reaction_item": "{prefix}تنفيذ وإثبات | +{reward:,} غرام",
    "task_err_unavailable": "❌ هذه المهمة غير متاحة الآن أو اكتملت.",
    "task_err_own": "❌ لا يمكنك تنفيذ مهمتك الخاصة!",
    "task_err_already": "⚠️ لقد قمت بإكمال هذه المهمة بالفعل!",
    "task_err_not_member": "❌ لم يتم التحقق من الانضمام بعد! اشترك أولاً ثم اضغط فحص.",
    "task_err_check_api": "⚠️ تعذر التحقق من القناة حالياً، يرجى المحاولة بعد لحظات.",
    "task_err_completed_now": "❌ اكتمل العدد المطلوب لهذه المهمة للتو.",
    "task_completed_alert": "🎉 تم التحقق بنجاح! تمت إضافة +{reward:,} غرام إلى رصيدك{flash_note}.",

    "post_task_detail": (
        "👁️ <b>مهمة مشاهدة منشور:</b> {title}\n\n"
        "1️⃣ اضغط على «فتح المنشور» وتصفّحه لمدة <b>{seconds} ثوانٍ</b> على الأقل.\n"
        "2️⃣ عُد واضغط «✅ استلام المكافأة (+{reward:,} غرام)»."
    ),
    "post_btn_open": "🔗 فتح المنشور الآن",
    "post_btn_claim": "✅ استلام المكافأة (+{reward:,})",
    "post_err_open_first": "❌ يرجى فتح المنشور أولاً!",
    "post_err_wait": "⏳ يرجى قراءة المنشور والانتظار {rem} ثانية إضافية.",
    "post_err_already": "⚠️ لقد استلمت مكافأة هذا المنشور مسبقاً!",
    "post_claimed_alert": "🎉 تمت إضافة +{reward:,} غرام لرصيدك{flash_note}!",

    "bot_task_detail": (
        "🤖 <b>مهمة بوت:</b> {title}\n"
        "💰 <b>المكافأة:</b> <code>{reward:,}</code> غرام\n"
        "{desc_line}"
        "\nاختر طريقة التحقق بعد تشغيل البوت:"
    ),
    "task_desc_line": "📝 <b>التعليمات:</b> {desc}\n",
    "bot_btn_open": "🚀 الانتقال للبوت",
    "bot_btn_fwd": "📨 تحقق تلقائي فوري (Forward)",
    "bot_btn_proof": "📸 إرسال إثبات بالصورة",
    "bot_fwd_err_disabled": "❌ التحقق التلقائي غير مفعل لهذه المهمة.",
    "bot_fwd_prompt": (
        "📨 <b>التحقق التلقائي عبر إعادة التوجيه:</b>\n\n"
        "1️⃣ افتح البوت <code>{bot_username}</code> واضغط <code>/start</code>.\n"
        "2️⃣ قم بعمل <b>إعادة توجيه (Forward)</b> لرسالة الترحيب من البوت إلى هنا خلال 5 دقائق."
    ),
    "bot_fwd_err_not_bot": (
        "❌ الرسالة المعاد توجيهها ليست من بوت (أو أن خصوصية التوجيه مخفية). "
        "يرجى إعادة توجيه رسالة مباشرة من البوت المطلوب أو استخدام إثبات الصورة."
    ),
    "bot_fwd_err_stale": "⌛ رسالة البوت المعاد توجيهها قديمة (أكثر من 5 دقائق). أرسل /start للبوت الآن وأعد توجيه الرسالة الجديدة.",
    "bot_fwd_err_wrong_bot": "❌ هذه الرسالة من بوت مختلف (<code>@{actual}</code>) وليس البوت المطلوب (<code>@{expected}</code>).",
    "bot_fwd_success": "🎉 <b>تم التحقق الفوري من البوت بنجاح!</b>\n💰 تم إضافة <b>+{reward:,} غرام</b> إلى رصيدك{flash_note}!",

    "proof_task_detail": (
        "🔥 <b>تفاصيل المهمة:</b> {title}\n"
        "💰 <b>المكافأة:</b> <code>{reward:,}</code> غرام\n"
        "{emoji_line}"
        "{desc_line}"
        "{steps_text}"
    ),
    "proof_emoji_line": "🎭 <b>التفاعل المطلوب:</b> {emoji}\n",
    "proof_task_manual_steps": "\n1️⃣ افتح الرابط ونفذ المطلوب.\n2️⃣ اضغط «📸 إرسال صورة الإثبات» وأرسل لقطة الشاشة.",
    "proof_task_auto_note": (
        "\n⚡ <b>تحقق تلقائي فوري مفعّل!</b>\n"
        "1️⃣ افتح المنشور وتفاعل بالإيموجي المطلوب وسيتم صرف المكافأة <b>تلقائياً بدون صورة</b> خلال ثوانٍ.\n"
        "2️⃣ أو يمكنك إرسال لقطة شاشة إذا تعذر الرصد التلقائي."
    ),
    "proof_btn_open": "🔗 فتح الرابط",
    "proof_btn_submit": "📸 إرسال صورة الإثبات",
    "proof_submit_prompt": (
        "📸 <b>إرسال إثبات التنفيذ:</b>\n\n"
        "قم بإرسال <b>صورة لقطة الشاشة (Screenshot)</b> هنا الآن ليتم مراجعتها وصرف المكافأة."
    ),
    "task_skipped_alert": "⏭️ تم تخطي المهمة وإخفاؤها.",
    "report_task_prompt": "🚨 <b>تبليغ عن المهمة #{task_id}:</b>\n\nاكتب سبب التبليغ في رسالة الآن (مثال: الرابط معطل / قناة مخالفة).",
    "report_issue_prompt": "🚨 <b>تبليغ عن مشكلة:</b>\n\nاكتب تفاصيل المشكلة أو رقم المهمة في رسالة الآن ليتم مراجعتها من الإدارة.",
    "report_received": "✅ <b>تم استلام بلاغك وسيتم مراجعته من الإدارة!</b>",

    "reaction_auto_paid": (
        "⚡ <b>تم التحقق التلقائي من تفاعلك بنجاح!</b>\n"
        "📌 المهمة: <b>{title}</b>\n"
        "💰 تمت إضافة <b>+{reward:,} غرام</b> إلى رصيدك فوراً!"
    ),
    "reaction_auto_paid_flash": (
        "⚡ <b>تم التحقق التلقائي من تفاعلك بنجاح!</b>\n"
        "📌 المهمة: <b>{title}</b>\n"
        "🔥 حدث ساعات الذروة ({mult}) نشط!\n"
        "💰 تمت إضافة <b>+{reward:,} غرام</b> (يشمل +{flash_bonus:,} مكافأة مضاعفة) إلى رصيدك!"
    ),

    # Proof Submission & Review
    "proof_err_duplicate": "🚫 <b>تم رفض الصورة تلقائياً!</b>\nهذه الصورة مطابقة أو مكررة من إثبات سابق. يرجى إرسال لقطة شاشة جديدة أصلية.",
    "proof_err_already_pending": "⚠️ لديك إثبات معتمد أو قيد المراجعة لهذه المهمة بالفعل.",
    "proof_submitted": (
        "✅ <b>تم استلام صورة الإثبات بنجاح!</b>\n"
        "تم إرسال الإثبات لصاحب المهمة للمراجعة (وسيُعتمد تلقائياً بعد 24 ساعة في حال عدم الرد)."
    ),
    "proof_creator_caption": (
        "📩 <b>إثبات تنفيذ جديد لمهمتك!</b>\n\n"
        "📌 المهمة: {title}\n"
        "👤 المنفذ: <code>{worker_id}</code>\n"
        "💰 المكافأة: {reward:,} غرام\n\n"
        "يرجى المعاينة واختيار الإجراء المناسب:"
    ),
    "proof_creator_revision_caption": (
        "🔄 <b>تم إعادة تقديم إثبات جديد للمهمة!</b>\n\n"
        "📌 المهمة: {title}\n"
        "👤 المنفذ: <code>{worker_id}</code>\n\n"
        "يرجى المراجعة واتخاذ الإجراء:"
    ),
    "proof_btn_approve": "✅ قبول ودفع",
    "proof_btn_reject": "❌ رفض مع سبب",
    "proof_btn_revision": "🔄 طلب إعادة مراجعة",
    "proof_err_not_found": "❌ لم يتم العثور على سجل هذه المهمة.",
    "proof_err_forbidden": "❌ أنت لست صاحب هذه المهمة!",
    "proof_err_already_handled": "⚠️ تم التعامل مع هذا الإثبات مسبقاً!",
    "proof_worker_rejected": (
        "❌ <b>تم رفض إثباتك في المهمة ({title}).</b>\n\n"
        "📝 <b>سبب الرفض:</b> {reason}\n\n"
        "يمكنك إرسال إثبات جديد أو فتح اعتراض لمراجعة الإدارة."
    ),
    "proof_btn_resubmit": "📤 إرسال إثبات جديد",
    "proof_btn_dispute": "⚖️ فتح اعتراض (تذكرة أدمن)",
    "proof_rej_quick_unclear": "📷 الصورة غير واضحة",
    "proof_rej_quick_notdone": "❌ لم ينفذ المطلوب",
    "proof_rej_quick_rules": "🚫 مخالفة الشروط",
    "proof_rej_reason_unclear": "الصورة غير واضحة ولا تُظهر إتمام المطلوب",
    "proof_rej_reason_notdone": "لم يتم تنفيذ شروط المهمة بالكامل",
    "proof_rej_reason_rules": "مخالفة تعليمات المهمة أو لقطة شاشة غير مطابقة",
    "proof_rej_custom_btn": "✍️ كتابة سبب مخصص",
    "proof_rej_custom_prompt": "✍️ اكتب سبب رفض الإثبات للمعاملة <code>#{ut_id}</code> الآن:",
    "proof_rej_done_alert": "❌ تم رفض الإثبات وإرسال السبب للمنفذ.",
    "proof_rej_caption": "❌ <b>تم رفض الإثبات.</b>\n📝 السبب: {reason}",
    "proof_rej_custom_done": "❌ <b>تم رفض الإثبات في مهمة {title} وإرسال السبب للمنفذ.</b>",
    "proof_rev_submitted": "✅ <b>تم إعادة إرسال صورة الإثبات بنجاح!</b>",
    "proof_approve_done_alert": "✅ تم قبول المهمة وتحويل الرصيد للمنفذ بنجاح!",
    "proof_approve_caption": "✅ <b>تم قبول هذه المهمة ودفع +{reward:,} غرام للمنفذ.</b>",
    "proof_worker_approved": "🎉 <b>مبروك!</b> تم قبول إثبات المهمة (<b>{title}</b>) وإضافة <b>+{reward:,} غرام</b> إلى رصيدك{flash_note}!",
    "proof_rev_done_alert": "🔄 تم طلب إعادة مراجعة جديدة من المنفذ.",
    "proof_rev_caption": "🔄 <b>تم طلب إعادة مراجعة وإرسال إثبات جديد من المنفذ.</b>",
    "proof_worker_rev_req": "🔄 <b>طلب صاحب المهمة ({title}) إعادة مراجعة جديدة.</b>\n\nيرجى التقاط صورة إثبات أوضح وإرسالها مجدداً.",
    "proof_rev_prompt": "📤 <b>إعادة إرسال إثبات الصورة:</b>\n\nيرجى إرسال صورة الإثبات الجديدة الآن مباشرة في الشات.",
    "proof_err_cannot_resubmit": "⚠️ لا يمكن إعادة الإرسال في الحالة الحالية.",
    "dispute_err_not_rejected": "⚠️ يمكن الاعتراض فقط على الإثباتات المرفوضة.",
    "dispute_err_exists": "⚠️ تم فتح تذكرة اعتراض لهذا الإثبات مسبقاً!",
    "dispute_filed_alert": "⚖️ تم فتح تذكرة اعتراض وتصعيدها للأدمن بنجاح!",
    "dispute_filed_msg": "⚖️ <b>تم رفع تذكرة اعتراض للأدمن.</b> سيتم مراجعة الإثبات وتصفية الحقوق فوراً.",
    "dispute_worker_won_dm": "⚖️ <b>قرار الأدمن:</b> تم قبول اعتراضك وإضافة <b>+{paid:,} غرام</b> لرصيدك!",
    "dispute_worker_lost_dm": "⚖️ <b>قرار الأدمن:</b> تم مراجعة الإثبات وتأكيد صحة موقف صاحب المهمة وإغلاق الاعتراض.",

    # Promotion Wizard, Promo Codes & Campaign Management
    "promo_menu": (
        "📣 <b>ماذا تريد أن تروّج؟</b>\n\n"
        "💳 <b>رصيدك:</b> <code>{balance:,}</code> غرام\n"
        "📉 <b>عمولتك الحالية:</b> <code>{fee_pct}%</code>"
    ),
    "promo_btn_group": "👥 مجموعة",
    "promo_btn_channel": "📣 قناة",
    "promo_btn_bot": "🤖 بوت",
    "promo_btn_post": "👁️ منشور",
    "promo_btn_reactions": "🔥 التفاعلات",
    "promo_btn_premium": "⚡ شحن بريميوم",
    "promo_btn_settings": "⚙️ إعدادات الترويج والعمولة",
    "promo_btn_my_tasks": "💼 مهامي وإدارتها",

    "promo_bot_type_prompt": "🤖 <b>اختر نوع حملة البوت:</b>",
    "promo_btn_bot_normal": "🤖 بوت عادي",
    "promo_btn_bot_webapp": "📱 بوت Web App",
    "promo_btn_bot_conditions": "📋 بوت بشروط إضافية",
    "promo_reaction_type_prompt": "🔥 <b>اختر نوع التفاعل المطلوب:</b>",
    "promo_btn_reaction_random": "🎲 تفاعل عشوائي",
    "promo_btn_reaction_fixed": "🎯 تفاعل محدد بإيموجي",

    "promo_account_type_prompt": (
        "اختر نوع الحساب:\n\n"
        "1️⃣ <b>جميع المستخدمين</b> – متاح لكل مستخدمي ZetaGram للانتشار السريع.\n"
        "🔴 الحد الأدنى للسعر للوحدة – 750 غرام\n\n"
        "2️⃣ <b>Telegram Premium</b> – متاح فقط لمستخدمي Telegram Premium 🌟 الجمهور أعلى جودة.\n"
        "🔴 الحد الأدنى للسعر للوحدة – 1,400 غرام"
    ),
    "promo_btn_acc_all": "1️⃣ متاح لجميع المستخدمين",
    "promo_btn_acc_premium": "2️⃣ فقط مستخدمو Telegram Premium 🌟",

    "promo_audience_prompt": (
        "🎯 <b>الجمهور:</b> 🌐 بدون قيود\n\n"
        "🌍 <b>اختر الجمهور المستهدف للمهمة:</b>\n\n"
        "💡 <i>يُضاف +100 غرام للحد الأدنى عند تخصيص لغات محددة.</i>"
    ),
    "promo_btn_audience_all": "🌍 السماح للجميع",
    "promo_btn_audience_custom": "🎯 اختيار لغات محددة",
    "promo_lang_unlimited": "🌐 بدون قيود",
    "promo_lang_grid_prompt": (
        "🎯 <b>اللغات المختارة:</b> {selected}\n\n"
        "🌍 <b>اضغط على اللغات لاختيارها أو إلغائها:</b>\n"
        "💡 <i>تحديد لغة يضيف +100 غرام للحد الأدنى للسعر.</i>"
    ),
    "promo_btn_lang_done": "✅ تأكيد ({count} لغة)",

    "promo_price_prompt": (
        "حدد سعر اشتراك/تنفيذ واحد. لإنشاء مهمة، يجب أن يكون لديك رصيد كافٍ.\n\n"
        "🔴 <b>السعر الأدنى للوحدة – {min_price:,} غرام</b>\n\n"
        "💡 <i>ملاحظة: لظهور أسرع في أعلى القائمة اجعل السعر أعلى من {fast_price:,} غرام.</i>\n\n"
        "📝 <b>اكتب السعر المطلوب للمشترك الواحد الآن (رقم صحيح):</b>"
    ),
    "promo_qty_prompt": (
        "{error_prefix}"
        "🔔 <b>تنبيه: العمولة المطبقة لحسابك هي {fee_pct}%.</b>\n\n"
        "💵 <b>سعر التنفيذ الواحد:</b> {price:,} غرام\n"
        "💰 <b>رصيدك:</b> {balance:,} غرام\n\n"
        "📝 <b>اكتب عدد التنفيذات المطلوب (أدنى حد 3)، أو اختر:</b>\n"
        "<b>الحد الأقصى لرصيدك:</b> {max_qty}"
    ),
    "promo_btn_max_qty": "(الحد الأقصى لرصيدك) {max_qty}",
    "promo_err_min_qty": "❌ خطأ! الحد الأدنى لعدد المشتركين في المهمة – 3.",
    "promo_err_max_qty": "❌ خطأ! الرصيد لا يكفي لإنشاء المهمة بعدد {qty}. الحد الأقصى لرصيدك هو {max_qty}.",

    "promo_payment_method": (
        "💳 <b>اختر طريقة الدفع لمهمتك:</b>\n\n"
        "• التكلفة الصافية: <code>{base_cost:,}</code> غرام\n"
        "• العمولة المطبقة ({fee_pct}%): <code>{commission:,}</code> غرام\n"
        "{discount_line}"
        "• <b>الإجمالي النهائي:</b> <code>{total_gram:,}</code> غرام\n\n"
        "💡 يمكنك التبرع بـ <b>{stars_cost} ⭐</b> لإلغاء العمولة نهائياً لمدة 24 ساعة!"
    ),
    "promo_payment_discount_line": "🎟️ <b>كود الخصم ({code}):</b> <code>-{discount:,}</code> غرام\n",
    "promo_btn_pay_gram": "💎 دفع {total_gram:,} GRAM",
    "promo_btn_enter_code": "🎟️ لدي كود خصم (Promo Code)",
    "promo_btn_clear_code": "🗑️ إزالة كود الخصم ({code})",
    "promo_btn_pay_stars": "🌟 دفع {stars_cost} Telegram Stars (إعفاء عمولة 24س)",
    "promo_stars_unavailable": "⚠️ الدفع عبر Telegram Stars غير مفعل حالياً، يمكنك الدفع برصيد GRAM مباشرة.",
    "promo_stars_title": "إعفاء عمولة الترويج 24 ساعة",
    "promo_stars_desc": "إلغاء كامل عمولة إنشاء الحملات الترويجية لمدة 24 ساعة في ZetaGram.",
    "promo_stars_activated": "🌟 <b>تم تفعيل الإعفاء من العمولة لمدة 24 ساعة بنجاح!</b>\nأصبحت تكلفة حملتك بدون عمولة: <code>{total:,}</code> غرام.",

    "promo_code_prompt": "🎟️ <b>إدخال كود الخصم (Promo Code):</b>\n\nأرسل كود الخصم في الشات الآن لتطبيقه على حملتك.",
    "promo_code_applied": "✅ <b>تم تطبيق كود الخصم <code>{code}</code> بنجاح!</b> وفّرت <code>{discount:,}</code> غرام.",
    "promo_code_cleared": "🗑️ تم إزالة كود الخصم.",
    "promo_err_invalid": "❌ كود الخصم غير صحيح أو متوقف حالياً.",
    "promo_err_expired": "⌛ انتهت صلاحية كود الخصم هذا.",
    "promo_err_exhausted": "⚠️ تم استهلاك كود الخصم بالحد الأقصى المسموح به.",
    "promo_err_min_order": "⚠️ هذا الكود يتطلب طلباً بحد أدنى <code>{min_order:,}</code> غرام.",
    "promo_err_already_used": "⚠️ لقد استخدمت كود الخصم هذا مسبقاً!",
    "promo_err_code_race": "⚠️ تعذر تطبيق كود الخصم (ربما انتهت استخداماته للتو). اختر السعر أو أنشئ الحملة بدونه.",

    "promo_kind_channel": "القناة",
    "promo_kind_group": "المجموعة",
    "promo_btn_pick_chat": "📣 اختيار {kind}",
    "promo_target_chat_prompt": (
        "📌 <b>تحديد {kind} المستهدفة:</b>\n\n"
        "⚠️ <b>يجب أن يكون البوت مشرفاً في {kind} للتحقق من اشتراكات الأعضاء.</b>\n\n"
        "1️⃣ اضغط زر «📣 اختيار {kind}» أدناه لاختيارها فوراً.\n"
        "2️⃣ أو أرسل بياناتها يدوياً بالصيغة:\n"
        "<code>@username_أو_الرابط | اسم الحملة</code>\n"
        "مثال: <code>@MyChannel | قناتي التقنية</code>"
    ),
    "promo_target_url_prompt": (
        "🔗 <b>أدخل رابط المهمة وعنوانها:</b>\n\n"
        "أرسل البيانات مفصولة بـ <code>|</code> بالصيغة التالية:\n"
        "<code>الرابط | عنوان المهمة{extra_hint}</code>\n\n"
        "مثال:\n<code>https://t.me/my_target/15 | دعم منشور مهم{extra_hint}</code>"
    ),
    "promo_err_bot_not_admin": (
        "❌ <b>البوت ليس مشرفاً في هذه المحادثة!</b> (الحالة: <code>{status}</code>)\n"
        "يرجى رفع البوت كمشرف أولاً ثم المحاولة مجدداً."
    ),
    "promo_err_invite_fetch": "⚠️ تعذر جلب رابط دعوة للمحادثة تلقائياً. يرجى إرسال الرابط والاسم يدوياً: <code>الرابط | الاسم</code>",
    "promo_chat_verified": "✅ تم التحقق من المحادثة بنجاح!",
    "promo_err_target_format": "⚠️ يرجى الإدخال بالصيغة الصحيحة مفصولة بـ <code>|</code>:\n<code>@username_أو_الرابط | عنوان المهمة</code>",
    "promo_err_bad_url": "❌ يرجى إدخال رابط يبدأ بـ https:// أو معرف يبدأ بـ @.",
    "promo_err_need_public_chat": "❌ يجب استخدام معرف عام (@username) أو زر اختيار القناة للتحقق.",

    "promo_auto_rx_badge_on": "\n⚡ <b>التحقق من التفاعلات:</b> تلقائي فوري بدون لقطة شاشة!",
    "promo_auto_rx_badge_off": "\n📸 <b>التحقق من التفاعلات:</b> عبر لقطة شاشة (لتفعيل التحقق التلقائي أضف البوت كمشرف في القناة).",
    "promo_confirm_summary": (
        "📋 <b>مراجعة وتأكيد الحملة الترويجية:</b>\n\n"
        "📌 <b>العنوان:</b> {title}\n"
        "📂 <b>الفئة:</b> <code>{cat}</code>\n"
        "🔗 <b>الرابط:</b> {url}\n"
        "👥 <b>العدد المطلوب:</b> <code>{qty:,}</code>\n"
        "💵 <b>مكافأة المنفذ:</b> <code>{price:,}</code> غرام\n"
        "🌍 <b>الجمهور:</b> {audience}"
        "{rx_badge}\n"
        "💳 <b>التكلفة الإجمالية المخصومة:</b> <code>{total_gram:,}</code> غرام (الضمان المالي Escrow)"
    ),
    "promo_audience_all": "الجميع",
    "promo_btn_confirm_create": "✅ تأكيد وإنشاء الحملة الآن",
    "promo_err_expired_session": "❌ انتهت بيانات الحملة، يرجى البدء من جديد.",
    "promo_err_insufficient": "❌ رصيدك غير كافٍ الآن!",
    "promo_created_alert": "🎉 تم إطلاق حملتك الترويجية بنجاح!",
    "promo_created_msg": (
        "🚀 <b>تم إطلاق الحملة (#{task_id}) بنجاح!</b>\n\n"
        "📌 <b>العنوان:</b> {title}\n"
        "🛡️ <b>الضمان المالي (Escrow):</b> <code>{escrow:,}</code> غرام\n\n"
        "يمكنك متابعتها وإدارتها في أي وقت من قسم «💼 مهامي وإدارتها»."
    ),
    "promo_btn_view_my": "💼 عرض حملاتي",

    "promo_settings_view": (
        "⚙️ <b>إعدادات الترويج والعمولة:</b>\n\n"
        "🏅 <b>مستواك:</b> {level_title}\n"
        "📉 <b>عمولة الترويج لمستواك:</b> <code>{vip_fee}%</code>\n"
        "🌟 <b>إعفاء العمولة عبر Telegram Stars:</b> {stars_status}\n\n"
        "🛡️ <b>نظام الضمان المالي (Escrow):</b>\n"
        "• يتم حجز أجر المنفذين كاملاً داخل الحملة ولا يُصرف إلا بعد التحقق.\n"
        "• عند إلغاء أي حملة يُردّ الرصيد الصافي المتبقي لحسابك فوراً."
    ),
    "promo_stars_on": "🟢 مفعل حتى <code>{until} UTC</code> (عمولة 0%)",
    "promo_stars_off": "⚪ غير مفعل حالياً",

    "promo_my_empty": "💼 <b>مهامي:</b>\n\nليس لديك أي حملات ترويجية قائمة حالياً.",
    "promo_my_header": "💼 <b>قائمة حملاتك الترويجية (اضغط لإدارة الحملة):</b>\n\n",
    "promo_my_btn_manage": "{icon} إدارة: {title}",
    "promo_task_view": (
        "💼 <b>إدارة الحملة #{task_id}:</b> {title}\n\n"
        "📊 <b>التقدم:</b> <code>{completed}/{total}</code> (متبقي: {remaining})\n"
        "💵 <b>السعر للوحدة:</b> <code>{reward:,}</code> غرام\n"
        "🛡️ <b>الضمان المتبقي (Escrow):</b> <code>{escrow:,}</code> غرام\n"
        "📌 <b>الحالة:</b> <code>{status}</code>"
    ),
    "promo_btn_pause": "⏸️ إيقاف مؤقت",
    "promo_btn_resume": "▶️ استئناف الحملة",
    "promo_btn_boost": "🚀 رفع السعر +100 غرام (بتكلفة {boost_cost:,})",
    "promo_btn_cancel": "🗑️ إلغاء الحملة واسترداد المتبقي",
    "promo_btn_back_my": "🔙 رجوع لحملاتي",
    "promo_err_task_not_found": "❌ الحملة غير موجودة.",
    "promo_err_task_closed": "⚠️ لا يمكن تغيير حالة حملة منتهية أو ملغاة.",
    "promo_toggled_alert": "✅ تم تغيير الحالة إلى {status}",
    "promo_err_boost_closed": "⚠️ الحملة غير نشطة أو مكتملة.",
    "promo_err_boost_balance": "❌ رصيدك غير كافٍ! المطلوب {extra_cost:,} غرام.",
    "promo_boosted_alert": "🚀 تم رفع سعر المهمة بنجاح!",
    "promo_err_already_closed": "⚠️ الحملة مكتملة أو ملغاة بالفعل.",
    "promo_cancelled_alert": "✅ تم إلغاء الحملة واسترداد +{refund:,} غرام لرصيدك!",
}
