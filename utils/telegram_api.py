import asyncio
import logging
from typing import Literal, Tuple
from telegram import Bot
from telegram.error import RetryAfter, TelegramError


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
