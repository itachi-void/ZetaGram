LANGUAGES = {
    "ar": "🇸🇦 العربية",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "uk": "🇺🇦 Українська",
    "zh": "🇨🇳 中文",
    "de": "🇩🇪 Deutsch",
    "es": "🇪🇸 Español",
    "fa": "🇮🇷 فارسی",
    "hi": "🇮🇳 हिंदी",
    "tr": "🇹🇷 Türkçe",
    "fr": "🇫🇷 Français",
    "id": "🇮🇩 Bahasa Indonesia",
    "bn": "🇧🇩 বাংলা",
    "pt": "🇧🇷 Português",
    "kk": "🇰🇿 Қاзақша",
    "uz": "🇺🇿 O'zbekcha",
}

TEXTS = {
    "ar": {
        "select_lang_first": "🌐 **يرجى اختيار لغتك المفضلّة للبدء:**\n🌐 **Please select your preferred language to start:**",
        "welcome": "🚧 **قريبًا... الانطلاقة الرسمية لـ GramPulse!** 🚀\n\nمرحبًا بك 👋 يا {name}\n\nأنت من أوائل الأشخاص الذين وصلوا إلى **GramPulse**، وهذا يعني أنك ستكون من أوائل المستفيدين عند الإطلاق الرسمي. 🎉\n\n💎 **ماذا ينتظرك؟**\n• 💰 تنفيذ مهام مقابل مكافآت.\n• 📣 الترويج للقنوات والمجموعات بسرعة وسهولة.\n• 👥 نظام دعوة الأصدقاء مع مكافآت إضافية.\n• 🎁 مكافآت يومية وعجلة حظ للأعضاء النشطين.\n\n⏳ **العد التنازلي بدأ...**\nالإطلاق الرسمي سيكون قريبًا جدًا، ونتطلع لأن تكون جزءًا من البداية.",
        "btn_earnings": "🧑‍💻 الأرباح",
        "btn_promotion": "📣 الترويج",
        "btn_account": "📱 حسابي",
        "btn_bonus": "🎁 المكافأة اليومية",
        "btn_vouchers": "🏷️ الشيكات",
        "btn_stats": "روبوتاتنا والإحصائيات 📊",
        "btn_check_sub": "فحص الاشتراك 📣",
        "btn_instructions": "📋 التعليمات",
        "btn_useful_links": "روابط مفيدة",
        "btn_language": "🌐 اللغة / Language",
        "lang_select_title": "🌐 **اختر لغة البوت / Select Bot Language:**",
        "lang_changed": "✅ تم تغيير لغة البوت إلى **العربية** بنجاح!",
    },
    "en": {
        "select_lang_first": "🌐 **Please select your preferred language to start:**",
        "welcome": "🚧 **Coming Soon... Official Launch of GramPulse!** 🚀\n\nWelcome 👋 {name}\n\nYou are one of the very first users to reach **GramPulse**! 🎉\n\n💎 **What awaits you?**\n• 💰 Complete tasks for rewards.\n• 📣 Promote channels & groups instantly.\n• 👥 Referral system with extra bonuses.\n• 🎁 Daily rewards & Lucky Wheel for active members.",
        "btn_earnings": "🧑‍💻 Earnings",
        "btn_promotion": "📣 Promotion",
        "btn_account": "📱 My Account",
        "btn_bonus": "🎁 Daily Bonus",
        "btn_vouchers": "🏷️ Vouchers",
        "btn_stats": "Our Bots & Stats 📊",
        "btn_check_sub": "Check Subscription 📣",
        "btn_instructions": "📋 Instructions",
        "btn_useful_links": "Useful Links",
        "btn_language": "🌐 Language / اللغة",
        "lang_select_title": "🌐 **Select Bot Language / اختر لغة البوت:**",
        "lang_changed": "✅ Bot language changed to **English** successfully!",
    },
    "ru": {
        "select_lang_first": "🌐 **Пожалуйста, выберите ваш язык:**",
        "welcome": "🚧 **Скоро... Официальный запуск GramPulse!** 🚀\n\nДобро пожаловать 👋 {name}\n\nВы один из первых пользователей **GramPulse**! 🎉\n\n💎 **Что вас ждет?**\n• 💰 Выполнение заданий за вознаграждение.\n• 📣 Продвижение каналов и групп.\n• 👥 Партнерская программа.\n• 🎁 Ежедневные бонусы и Колесо Удачи.",
        "btn_earnings": "🧑‍💻 Заработок",
        "btn_promotion": "📣 Продвижение",
        "btn_account": "📱 Мой аккаунт",
        "btn_bonus": "🎁 Ежедневный бонус",
        "btn_vouchers": "🏷️ Чек",
        "btn_stats": "Статистика 📊",
        "btn_check_sub": "Проверить подписку 📣",
        "btn_instructions": "📋 Инструкции",
        "btn_useful_links": "Полезные ссылки",
        "btn_language": "🌐 Язык / Language",
        "lang_select_title": "🌐 **Выберите язык бота:**",
        "lang_changed": "✅ Язык бота успешно изменен на **Русский**!",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    lang_dict = TEXTS.get(lang, TEXTS["en"])
    text_template = lang_dict.get(key, TEXTS["ar"].get(key, TEXTS["en"].get(key, "")))
    return text_template.format(**kwargs) if kwargs else text_template
