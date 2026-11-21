import time
import logging
from typing import Tuple, Optional, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select

from config import ADMIN_IDS, REQUIRED_CHANNEL, REQUIRED_CHANNEL_LINK
from database.db import AsyncSessionLocal
from database.models import User, MandatoryChannel
from utils.security import rate_limiter
from utils.telegram_api import check_user_subscription_status
from utils.captcha import send_captcha_challenge
from utils.i18n import get_text
from utils.html_utils import esc, utcnow

_last_activity_write: Dict[int, float] = {}
_sub_cache: Dict[Tuple[int, str], Tuple[bool, float]] = {}
_last_allowed_update: Dict[int, Tuple[int, float]] = {}

ACTIVITY_WRITE_INTERVAL = 60.0
SUB_CACHE_TTL = 120.0

_INPUT_STATE_KEYS = (
    "awaiting_mand_chan",
    "awaiting_create_voucher",
    "awaiting_voucher_code",
    "awaiting_vault_amount",
    "awaiting_transfer_input",
    "awaiting_promo_price",
    "awaiting_promo_qty",
    "awaiting_promo_target",
    "awaiting_promo_code",
    "awaiting_report_task_id",
    "awaiting_reject_reason_ut_id",
    "awaiting_bot_forward_task_id",
    "pending_task_id",
    "revision_ut_id",
)


def clear_user_input_states(context: ContextTypes.DEFAULT_TYPE):
    """Clear any lingering interactive prompt states so menu switches stay clean."""
    if not context or not getattr(context, "user_data", None):
        return
    for key in _INPUT_STATE_KEYS:
        context.user_data.pop(key, None)


def invalidate_sub_cache(user_id: Optional[int] = None):
    """Invalidate mandatory-channel subscription cache for one user or everyone."""
    if user_id is None:
        _sub_cache.clear()
        return
    to_del = [k for k in _sub_cache if k[0] == user_id]
    for k in to_del:
        _sub_cache.pop(k, None)


def reset_gatekeeper_caches():
    """Reset in-memory gatekeeper caches (useful in tests)."""
    _last_activity_write.clear()
    _sub_cache.clear()
    _last_allowed_update.clear()


async def get_mandatory_channels_list(lang: str = "ar"):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MandatoryChannel).where(MandatoryChannel.is_active == True)
        )
        channels = result.scalars().all()

    if not channels:
        if not REQUIRED_CHANNEL or REQUIRED_CHANNEL == "@YourRequiredChannel":
            return []
        return [
            {
                "id": 0,
                "channel_username": REQUIRED_CHANNEL,
                "channel_link": REQUIRED_CHANNEL_LINK,
                "title": get_text(lang, "default_official_channel"),
            }
        ]
    return [
        {
            "id": c.id,
            "channel_username": c.channel_username,
            "channel_link": c.channel_link,
            "title": c.title or c.channel_username,
        }
        for c in channels
    ]


async def _reply_or_alert(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, markup=None):
    user_id = update.effective_user.id
    if update.callback_query:
        try:
            plain = text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
            await update.callback_query.answer(plain[:195], show_alert=True)
        except Exception:
            pass
        if markup is not None:
            await context.bot.send_message(
                chat_id=user_id, text=text, parse_mode="HTML", reply_markup=markup
            )
    elif update.message:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await context.bot.send_message(chat_id=user_id, text=text, parse_mode="HTML", reply_markup=markup)


async def enforce_user_access(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    require_captcha: bool = True,
    require_unbanned: bool = True,
    require_mandatory_sub: bool = True,
    apply_rate_limit: bool = True,
) -> Tuple[bool, Optional[User]]:
    """
    Centralized security gatekeeper for commands, text/photo handlers, and callbacks.
    Checks: rate limit -> user registered -> banned_until -> captcha -> mandatory channels.
    """
    if not update.effective_user:
        return False, None

    user_id = update.effective_user.id
    is_admin = user_id in ADMIN_IDS
    hint_lang = (getattr(update.effective_user, "language_code", None) or "ar")[:2].lower()

    now_ts = time.time()
    if apply_rate_limit and not is_admin:
        update_marker = getattr(update, "update_id", None)
        if not isinstance(update_marker, int):
            update_marker = id(update)
        prev = _last_allowed_update.get(user_id)
        same_update = prev is not None and prev[0] == update_marker and (now_ts - prev[1]) < 10.0
        if not same_update:
            if not rate_limiter.is_allowed(user_id):
                if update.callback_query:
                    try:
                        await update.callback_query.answer(
                            get_text(hint_lang, "rate_limited"), show_alert=True
                        )
                    except Exception:
                        pass
                return False, None
            _last_allowed_update[user_id] = (update_marker, now_ts)
            if len(_last_allowed_update) > 5000:
                _last_allowed_update.clear()
    now_dt = utcnow()
    should_touch_activity = (now_ts - _last_activity_write.get(user_id, 0.0)) >= ACTIVITY_WRITE_INTERVAL

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == user_id))
        ).scalar_one_or_none()

        if not user:
            await _reply_or_alert(update, context, get_text(hint_lang, "not_registered"))
            return False, None

        if should_touch_activity:
            user.last_active_at = now_dt
            await session.commit()
            _last_activity_write[user_id] = now_ts
            if len(_last_activity_write) > 5000:
                _last_activity_write.clear()

    lang = (user.language or "ar").lower()

    if require_unbanned and not is_admin:
        if user.banned_until and now_dt < user.banned_until:
            until_str = user.banned_until.strftime("%Y-%m-%d %H:%M UTC")
            msg = get_text(
                lang,
                "banned_notice",
                until=until_str,
                violations=user.violations_count or 0,
            )
            await _reply_or_alert(update, context, msg)
            return False, user

    if require_captcha and not is_admin:
        if not user.is_captcha_verified:
            await send_captcha_challenge(
                update, context, lang=lang, locked_until=user.captcha_locked_until
            )
            return False, user

    if require_mandatory_sub and not is_admin:
        channels = await get_mandatory_channels_list(lang=lang)
        if channels:
            unsubbed = []
            for ch in channels:
                cname = ch["channel_username"]
                cache_key = (user_id, cname)
                cached = _sub_cache.get(cache_key)
                if cached and (now_ts - cached[1]) < SUB_CACHE_TTL:
                    if not cached[0]:
                        unsubbed.append(ch)
                    continue

                status = await check_user_subscription_status(context.bot, cname, user_id)
                if status == "member":
                    _sub_cache[cache_key] = (True, now_ts)
                elif status == "not_member":
                    _sub_cache[cache_key] = (False, now_ts)
                    unsubbed.append(ch)
                else:
                    # Do NOT lock out users if a mandatory channel misbehaves or API errors
                    logging.warning(
                        "Mandatory channel check returned error for user %s in %s",
                        user_id,
                        cname,
                    )

            if len(_sub_cache) > 10000:
                _sub_cache.clear()

            if unsubbed:
                keyboard = [
                    [InlineKeyboardButton(f"📢 {ch['title']}", url=ch["channel_link"])]
                    for ch in unsubbed
                ]
                keyboard.append(
                    [InlineKeyboardButton(get_text(lang, "btn_recheck_now"), callback_data="recheck_forced_sub")]
                )
                await _reply_or_alert(
                    update,
                    context,
                    get_text(lang, "forced_sub_required"),
                    markup=InlineKeyboardMarkup(keyboard),
                )
                return False, user

    return True, user
