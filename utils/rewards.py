from sqlalchemy import select, func, and_
from config import (
    REFERRAL_ACTIVE_BONUS,
    REFERRAL_COMMISSION_RATE,
    DAILY_QUEST_TARGET,
    DAILY_QUEST_REWARD,
    RECAPTCHA_TASK_INTERVAL,
)
from database.models import User, Task, UserTask, Transaction
from utils.security import get_vip_perks
from utils.html_utils import esc, utcnow


async def award_task_completion(
    session,
    bot,
    user: User,
    task: Task,
    submission: UserTask,
    target_status: str = "completed",
) -> dict:
    """
    Award worker for completing a task inside an existing lock & DB session.
    Handles: VIP bonus, escrow deduction, 10% referral commission,
    3-task referral milestone, daily quest bonus, and periodic re-captcha trigger.
    Caller must commit the session and then dispatch any returned post-commit notifications.
    """
    now = utcnow()
    perks = get_vip_perks(user.vip_level)
    bonus = int(task.reward_grams * perks["task_bonus"])
    total_reward = task.reward_grams + bonus

    submission.status = target_status
    submission.reward_paid = total_reward
    submission.completed_at = now

    user.balance += total_reward
    user.trust_score = min(200, (user.trust_score or 100) + 2)
    user.tasks_since_captcha = (user.tasks_since_captcha or 0) + 1

    task.escrow_balance = max(0, (task.escrow_balance or 0) - task.reward_grams)
    if task.completed_qty >= task.total_qty:
        task.status = "completed"

    session.add(
        Transaction(
            user_id=user.telegram_id,
            trans_type="earn_task",
            amount=total_reward,
            description=f"كسب من مهمة: {task.title}",
        )
    )

    await session.flush()

    comm = 0
    referrer_milestone_id = None
    if user.referred_by and user.referred_by != user.telegram_id:
        referrer = (
            await session.execute(select(User).where(User.telegram_id == user.referred_by))
        ).scalar_one_or_none()
        if referrer:
            comm = int(task.reward_grams * REFERRAL_COMMISSION_RATE)
            if comm >= 1:
                referrer.balance += comm
                session.add(
                    Transaction(
                        user_id=referrer.telegram_id,
                        trans_type="referral_commission",
                        amount=comm,
                        description=f"عمولة 10% من أرباح الصديق {user.telegram_id}",
                    )
                )

            completed_total = (
                await session.execute(
                    select(func.count(UserTask.id)).where(
                        and_(
                            UserTask.user_id == user.telegram_id,
                            UserTask.status.in_(["completed", "approved"]),
                        )
                    )
                )
            ).scalar() or 0

            if completed_total >= 3 and not user.referred_bonus_paid:
                user.referred_bonus_paid = True
                referrer.balance += REFERRAL_ACTIVE_BONUS
                session.add(
                    Transaction(
                        user_id=referrer.telegram_id,
                        trans_type="referral_milestone",
                        amount=REFERRAL_ACTIVE_BONUS,
                        description=f"مكافأة دعوة صديق ({user.telegram_id}) أتم 3 مهام",
                    )
                )
                referrer_milestone_id = referrer.telegram_id

    # Daily Quest check
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = today_start.strftime("%Y-%m-%d")
    today_count = (
        await session.execute(
            select(func.count(UserTask.id)).where(
                and_(
                    UserTask.user_id == user.telegram_id,
                    UserTask.status.in_(["completed", "approved"]),
                    UserTask.completed_at >= today_start,
                )
            )
        )
    ).scalar() or 0

    quest_completed = False
    if today_count >= DAILY_QUEST_TARGET and user.daily_quest_date != today_str:
        user.daily_quest_date = today_str
        user.balance += DAILY_QUEST_REWARD
        session.add(
            Transaction(
                user_id=user.telegram_id,
                trans_type="daily_quest",
                amount=DAILY_QUEST_REWARD,
                description=f"مكافأة التحدي اليومي ({DAILY_QUEST_TARGET} مهام)",
            )
        )
        quest_completed = True

    # Periodic Re-Captcha check
    recaptcha_triggered = False
    if (user.tasks_since_captcha or 0) >= RECAPTCHA_TASK_INTERVAL:
        user.is_captcha_verified = False
        user.tasks_since_captcha = 0
        recaptcha_triggered = True

    return {
        "total_reward": total_reward,
        "bonus": bonus,
        "quest_completed": quest_completed,
        "recaptcha_triggered": recaptcha_triggered,
        "task_finished": task.status == "completed",
        "referrer_milestone_id": referrer_milestone_id,
        "commission_paid": comm,
    }


async def dispatch_completion_notifications(bot, user_id: int, reward_info: dict):
    """Send post-commit notifications for referral milestone and daily quest."""
    if not bot:
        return
    if reward_info.get("referrer_milestone_id"):
        try:
            await bot.send_message(
                chat_id=reward_info["referrer_milestone_id"],
                text=(
                    f"🎉 <b>مبروك!</b> لقد أكمل صديقك المدعو (<code>{esc(user_id)}</code>) 3 مهام، "
                    f"وتم إضافة <b>+{REFERRAL_ACTIVE_BONUS:,} غرام</b> إلى رصيدك!"
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass
    if reward_info.get("quest_completed"):
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎯 <b>إنجاز التحدي اليومي!</b>\n"
                    f"أكملت {DAILY_QUEST_TARGET} مهام اليوم وحصلت على مكافأة إضافية "
                    f"<b>+{DAILY_QUEST_REWARD:,} غرام</b>!"
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass
