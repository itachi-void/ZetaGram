import re
import asyncio
import logging
from typing import Literal, Tuple, Optional
from telegram import Bot
from telegram.error import RetryAfter, TelegramError


def normalize_emoji(emoji: Optional[str]) -> str:
    """Normalize an emoji string by stripping whitespace and variation selector FE0F."""
    if not emoji:
        return ""
    return emoji.strip().replace("\ufe0f", "")


def parse_telegram_post_link(url: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Parse public (https://t.me/<username>/<msg_id>) or private supergroup/channel
    (https://t.me/c/<internal_id>/<msg_id>) post URLs.
    Returns (chat_ref, message_id) or (None, None) if not a recognizable post link.
    """
    if not url or not isinstance(url, str):
        return None, None
    clean = url.strip().split("?", 1)[0].split("#", 1)[0].rstrip("/")
    m_priv = re.match(
        r"^https?://(?:t\.me|telegram\.me)/c/(\d+)/(\d+)(?:/\d+)?$",
        clean,
        re.IGNORECASE,
    )
    if m_priv:
        internal_id, msg_id_str = m_priv.group(1), m_priv.group(2)
        return f"-100{internal_id}", int(msg_id_str)

    m_pub = re.match(
        r"^https?://(?:t\.me|telegram\.me)/([A-Za-z][A-Za-z0-9_]{3,})/(\d+)(?:/\d+)?$",
        clean,
        re.IGNORECASE,
    )
    if m_pub:
        username, msg_id_str = m_pub.group(1), m_pub.group(2)
        if username.lower() in ("c", "joinchat", "addstickers", "share", "s"):
            return None, None
        return f"@{username}", int(msg_id_str)

    return None, None


async def check_user_subscription_status(
    bot: Bot, chat_id: str | int, user_id: int
) -> Literal["member", "not_member", "error"]:
    """
    Safely check whether user_id is a member of chat_id.
    Returns 'not_member' ONLY on confirmed non-membership ('left', 'kicked', or restricted non-member).
    Returns 'error' on API/network/permission errors so callers never false-ban users.
    """
    for attempt in range(2):
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            status = getattr(member, "status", None)
            if status in ("member", "administrator", "creator"):
                return "member"
            if status == "restricted":
                return "member" if getattr(member, "is_member", False) else "not_member"
            if status in ("left", "kicked"):
                return "not_member"
            return "error"
        except RetryAfter as e:
            wait_sec = float(getattr(e, "retry_after", 0) or 0)
            if attempt == 0 and wait_sec <= 5:
                await asyncio.sleep(wait_sec + 0.1)
                continue
            logging.warning("RetryAfter checking subscription for %s in %s: %s", user_id, chat_id, e)
            return "error"
        except TelegramError as e:
            logging.warning("TelegramError checking subscription for %s in %s: %s", user_id, chat_id, e)
            return "error"
        except Exception as e:
            logging.warning("Unexpected error checking subscription for %s in %s: %s", user_id, chat_id, e)
            return "error"
    return "error"


async def check_user_subscription(bot: Bot, chat_id: str | int, user_id: int) -> bool:
    """Backward-compatible boolean wrapper returning True only when confirmed a member."""
    return (await check_user_subscription_status(bot, chat_id, user_id)) == "member"


async def check_bot_is_admin(bot: Bot, chat_id: str | int) -> Tuple[bool, str]:
    """Verify that the bot is an administrator or creator of chat_id."""
    try:
        bot_id = bot.id
        member = await bot.get_chat_member(chat_id=chat_id, user_id=bot_id)
        status = getattr(member, "status", "")
        if status in ("administrator", "creator"):
            return True, status
        return False, status or "not_admin"
    except TelegramError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)
