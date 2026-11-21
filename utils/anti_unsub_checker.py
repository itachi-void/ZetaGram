import asyncio
import logging
from datetime import timedelta
from telegram import Bot
from telegram.error import TelegramError
from sqlalchemy import select, and_

from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask, Transaction
from utils.telegram_api import check_user_subscription_status
from utils.security import user_lock_manager, send_security_alert
from utils.html_utils import esc, utcnow


async def check_unsubs_once(bot: Bot, sleep_between: float = 0.08) -> dict:
    """
    Single pass checking whether users left channel/group tasks within 7 days.
    NEVER penalizes when Telegram API returns 'error'.
    """
    now = utcnow()
    seven_days_ago = now - timedelta(days=7)
    stats = {"checked": 0, "penalized": 0, "errors": 0}

    async with AsyncSessionLocal() as session:
        stmt = (
            select(UserTask.id, UserTask.user_id, UserTask.task_id, Task.chat_id, Task.title)
            .join(Task, UserTask.task_id == Task.id)
            .where(
                and_(
                    Task.task_type.in_(["channel", "group"]),
                    UserTask.status.in_(["completed", "approved"]),
                    UserTask.unsubscribed == False,
                    UserTask.completed_at >= seven_days_ago,
                    Task.chat_id.isnot(None),
                )
            )
        )
        rows = (await session.execute(stmt)).all()

    task_errors = {}
    alerted_tasks = set()

    for ut_id, uid, tid, chat_id, task_title in rows:
        if not chat_id:
            continue
        if task_errors.get(tid, 0) >= 3:
            continue

        stats["checked"] += 1
        status = await check_user_subscription_status(bot, chat_id, uid)

        if status == "error":
            stats["errors"] += 1
            task_errors[tid] = task_errors.get(tid, 0) + 1
            if task_errors[tid] >= 3 and tid not in alerted_tasks:
                alerted_tasks.add(tid)
                await send_security_alert(
                    bot,
                    f"⚠️ <b>تعذر فحص الاشتراكات للمهمة #{tid}</b> ({esc(task_title)})\n"
                    f"القناة <code>{esc(chat_id)}</code> تعيد أخطاء API (ربما أُزيل البوت من الإشراف). تم تخطي باقي الفحوصات لها دون معاقبة الأعضاء.",
                    alert_key=f"unsub_task_err_{tid}",
                    cooldown=3600.0,
                )
        elif status == "not_member":
            deducted = 0
            ban_duration = ""
            violations = 0
            title_snap = task_title

            async with user_lock_manager.acquire_ordered_locks(("user", uid), ("task", tid)):
                async with AsyncSessionLocal() as session:
                    ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
                    task = (await session.execute(select(Task).where(Task.id == tid))).scalar_one_or_none()
                    user = (await session.execute(select(User).where(User.telegram_id == uid))).scalar_one_or_none()

                    if ut and task and user and not ut.unsubscribed:
                        ut.unsubscribed = True
                        penalty_base = ut.reward_paid or task.reward_grams
                        deducted = min(user.balance, penalty_base)
                        user.balance -= deducted
                        user.trust_score = max(0, (user.trust_score or 100) - 15)
                        user.violations_count = (user.violations_count or 0) + 1
                        violations = user.violations_count

                        if violations == 1:
                            user.banned_until = now + timedelta(hours=24)
                            ban_duration = "24 ساعة"
                        elif violations == 2:
                            user.banned_until = now + timedelta(days=7)
                            ban_duration = "7 أيام"
                        else:
                            user.banned_until = now + timedelta(days=36500)
                            ban_duration = "دائم"

                        # Re-open 1 slot on the task & restore escrow
                        task.completed_qty = max(0, task.completed_qty - 1)
                        task.escrow_balance = (task.escrow_balance or 0) + task.reward_grams
                        if task.status == "completed" and task.completed_qty < task.total_qty:
                            task.status = "active"

                        session.add(
                            Transaction(
                                user_id=uid,
                                trans_type="unsub_penalty",
                                amount=-deducted,
                                description=f"خصم إلغاء اشتراك: {task.title}",
                            )
                        )
                        title_snap = task.title
                        await session.commit()
                        stats["penalized"] += 1

            if ban_duration:
                try:
                    msg = (
                        f"⚠️ <b>تنبيه مخالفة وحظر!</b>\n\n"
                        f"لقد قمت بإلغاء الاشتراك من القناة/المجموعة: <code>{esc(title_snap)}</code> قبل مرور 7 أيام.\n"
                        f"• 🔴 تم خصم <b>-{deducted:,}</b> غرام من رصيدك.\n"
                        f"• 🚫 تم فرض حظر من تنفيذ المهام لمدة: <b>{ban_duration}</b>.\n"
                        f"• ⚠️ عدد المخالفات المسجلة عليك: {violations}"
                    )
                    await bot.send_message(chat_id=uid, text=msg, parse_mode="HTML")
                except TelegramError:
                    pass
                except Exception:
                    pass

        if sleep_between > 0:
            await asyncio.sleep(sleep_between)

    return stats


async def run_anti_unsub_checker(bot: Bot):
    """Background worker running every hour to detect early channel/group unsubscriptions."""
    logging.info("Starting Anti-Unsub Background Checker Worker...")
    while True:
        try:
            await asyncio.sleep(3600)
            await check_unsubs_once(bot)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error("Error in Anti-Unsub Checker Worker: %s", e)
