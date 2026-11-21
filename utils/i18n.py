from utils.locales import AR_TEXTS, EN_TEXTS, RU_TEXTS, OTHER_TEXTS

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
    "kk": "🇰🇿 Қазақша",
    "uz": "🇺🇿 O'zbekcha",
}

TEXTS = {
    "ar": AR_TEXTS,
    "en": EN_TEXTS,
    "ru": RU_TEXTS,
    **OTHER_TEXTS,
}


def get_user_lang(user) -> str:
    """Safely return a user's normalized 2-letter language preference (default 'ar')."""
    if user and getattr(user, "language", None):
        return str(user.language).lower()
    return "ar"


def get_text(_lang: str, _key: str, /, **kwargs) -> str:
    """Look up localized text with fallback chain: lang -> 'en' -> 'ar' -> key."""
    norm_lang = (_lang or "ar").lower()
    lang_dict = TEXTS.get(norm_lang, EN_TEXTS)
    text_template = lang_dict.get(_key)
    if text_template is None:
        text_template = EN_TEXTS.get(_key)
    if text_template is None:
        text_template = AR_TEXTS.get(_key, _key)

    if kwargs:
        try:
            return text_template.format(**kwargs)
        except Exception:
            return text_template
    return text_template


def get_vip_title(lang: str, vip_level: int | None) -> str:
    lvl = vip_level if vip_level in (1, 2, 3, 4) else 1
    return get_text(lang, f"vip_title_{lvl}")


def get_tx_type_label(lang: str, trans_type: str) -> str:
    key = f"tx_type_{trans_type}"
    if key in AR_TEXTS:
        return get_text(lang, key)
    return get_text(lang, "tx_type_default")


def get_milestone_title(lang: str, milestone_id: str) -> str:
    key = f"ms_{milestone_id}"
    if key in AR_TEXTS:
        return get_text(lang, key)
    return milestone_id
