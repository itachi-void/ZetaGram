from telegram import Bot
from telegram.error import TelegramError

async def check_user_subscription(bot: Bot, chat_id: str, user_id: int) -> bool:
    """
    Checks if a user is currently a member, admin, or creator of a channel/group.
    """
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except TelegramError as e:
        print(f"Error checking subscription for {user_id} in {chat_id}: {e}")
        return False
