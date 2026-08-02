import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TelegramError
from sqlalchemy import select, and_
from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask
from utils.telegram_api import check_user_subscription

async def run_anti_unsub_checker(bot: Bot):
    """
    Background worker that runs every hour to check if users un-subscribed within 7 days.
    """
    logging.info("Starting Anti-Unsub Background Checker Worker...")
    while True:
        try:
            await asyncio.sleep(3600) # Check every 1 hour
            seven_days_ago = datetime.utcnow() - timedelta(days=7)

            async with AsyncSessionLocal() as session:
                # Query completed channel/group tasks done in the last 7 days that haven't been marked unsubscribed yet
                stmt = select(UserTask, Task, User).join(Task).join(User).where(
                    and_(
                        Task.task_type.in_(["channel", "group"]),
                        UserTask.status == "completed",
                        UserTask.unsubscribed == False,
                        UserTask.completed_at >= seven_days_ago
                    )
                )

                results = (await session.execute(stmt)).all()

                for ut, task, user in results:
                    if not task.chat_id:
                        continue

                    # Check if user is still in chat
                    is_subbed = await check_user_subscription(bot, task.chat_id, user.telegram_id)
                    if not is_subbed:
                        # User left! Penalize user
                        ut.unsubscribed = True
                        user.balance = max(0, user.balance - task.reward_grams)
                        user.violations_count += 1

                        ban_duration = ""
                        if user.violations_count == 1:
                            user.banned_until = datetime.utcnow() + timedelta(hours=24)
                            ban_duration = "24 ساعة"
                        elif user.violations_count == 2:
                            user.banned_until = datetime.utcnow() + timedelta(days=7)
                            ban_duration = "7 أيام"
                        else:
                            user.banned_until = datetime.utcnow() + timedelta(days=36500)
                            ban_duration = "دائم"

                        await session.commit()

                        # Send notification message to user
                        try:
                            msg = (
                                f"⚠️ **تنبيه مخالفة وحظر!**\n\n"
                                f"لقد قمت بإلغاء الاشتراك من القناة/المجموعة: `{task.title}` قبل مرور 7 أيام.\n"
                                f"• 🔴 تم خصم -{task.reward_grams:,} غرام من رصيدك.\n"
                                f"• 🚫 تم فرض حظر على قدرتك على إكمال المهام لمدة: **{ban_duration}**.\n"
                                f"عدد المخالفات المسجلة عليك: {user.violations_count}"
                            )
                            await bot.send_message(chat_id=user.telegram_id, text=msg, parse_mode="Markdown")
                        except TelegramError:
                            pass

        except Exception as e:
            logging.error(f"Error in Anti-Unsub Checker Worker: {e}")
