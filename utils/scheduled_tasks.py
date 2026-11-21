import os
import asyncio
import logging
import tempfile
from datetime import timedelta
from sqlalchemy import select, func, and_, or_

from config import ADMIN_IDS, AUTO_APPROVE_PROOF_HOURS, LEADERBOARD_PRIZES
from database.db import AsyncSessionLocal, create_safe_sqlite_backup
from database.models import (
    User,
    Task,
    UserTask,
    Transaction,
    DisputeTicket,
    TaskReport,
    WeeklyLeaderboardRun,
)
from utils.security import user_lock_manager
from utils.rewards import award_task_completion, dispatch_completion_notifications
from utils.i18n import get_text, get_user_lang
from utils.html_utils import esc, utcnow


async def run_daily_backup_once(bot) -> bool:
    """Create a WAL-safe SQLite backup copy and send it to all ADMIN_IDS."""
    now = utcnow()
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db", prefix="zetagram_bak_")
    os.close(tmp_fd)
    try:
        if not create_safe_sqlite_backup(tmp_path):
            return False
        now_str = now.strftime("%Y-%m-%d %H:%M")
        fname = f"auto_backup_{now.strftime('%Y%m%d_%H%M%S')}.db"
        sent_any = False
        for admin_id in ADMIN_IDS:
            try:
                with open(tmp_path, "rb") as f:
                    await bot.send_document(
                        chat_id=admin_id,
                        document=f,
                        filename=fname,
                        caption=f"💾 <b>النسخة الاحتياطية التلقائية لقاعدة البيانات</b>\n⏱️ التاريخ: <code>{now_str} UTC</code>",
                        parse_mode="HTML",
                    )
                sent_any = True
            except Exception as e:
                logging.debug("Backup delivery failed for admin %s: %s", admin_id, e)
        return sent_any
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


async def run_daily_backup_worker(bot):
    while True:
        try:
            await asyncio.sleep(24 * 3600)
            await run_daily_backup_once(bot)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error("Error in daily backup worker: %s", e)


async def run_retention_reminders_once(bot, batch_size: int = 100) -> int:
    """Send a single retention reminder per inactivity window (no repeat spam)."""
    now = utcnow()
    t_24h_ago = now - timedelta(hours=24)
    t_48h_ago = now - timedelta(hours=48)
    sent_count = 0

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User)
            .where(
                and_(
                    User.notifications_enabled == True,
                    or_(User.banned_until.is_(None), User.banned_until < now),
                    User.last_active_at <= t_24h_ago,
                    User.last_active_at >= t_48h_ago,
                    or_(User.last_reminded_at.is_(None), User.last_reminded_at < t_48h_ago),
                )
            )
            .limit(batch_size)
        )
        inactive_users = result.scalars().all()
        if not inactive_users:
            return 0

        targets = []
        for u in inactive_users:
            u.last_reminded_at = now
            targets.append((u.telegram_id, u.first_name or "", get_user_lang(u)))
        await session.commit()

    for uid, fname, u_lang in targets:
        try:
            await bot.send_message(
                chat_id=uid,
                text=get_text(u_lang, "notif_retention_reminder", name=esc(fname)),
                parse_mode="HTML",
            )
            sent_count += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)

    return sent_count


async def run_retention_reminders_worker(bot):
    while True:
        try:
            await asyncio.sleep(4 * 3600)
            await run_retention_reminders_once(bot)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error("Error in retention reminders worker: %s", e)


async def compile_and_send_daily_report_once(bot, now=None) -> str:
    """Compile yesterday's [yesterday_start, today_start) stats and send to ADMIN_IDS."""
    now = now or utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    async with AsyncSessionLocal() as session:
        new_users = (
            await session.execute(
                select(func.count(User.telegram_id)).where(
                    and_(User.created_at >= yesterday_start, User.created_at < today_start)
                )
            )
        ).scalar() or 0

        tasks_yesterday = (
            await session.execute(
                select(func.count(UserTask.id)).where(
                    and_(
                        UserTask.status.in_(["completed", "approved"]),
                        UserTask.completed_at >= yesterday_start,
                        UserTask.completed_at < today_start,
                    )
                )
            )
        ).scalar() or 0

        earned_yesterday = (
            await session.execute(
                select(func.sum(Transaction.amount)).where(
                    and_(
                        Transaction.created_at >= yesterday_start,
                        Transaction.created_at < today_start,
                        Transaction.amount > 0,
                    )
                )
            )
        ).scalar() or 0

        top_ref_row = (
            await session.execute(
                select(User.referred_by, func.count(User.telegram_id).label("cnt"))
                .where(
                    and_(
                        User.created_at >= yesterday_start,
                        User.created_at < today_start,
                        User.referred_by.isnot(None),
                    )
                )
                .group_by(User.referred_by)
                .order_by(func.count(User.telegram_id).desc())
                .limit(1)
            )
        ).first()
        top_ref_str = (
            f"<code>{top_ref_row[0]}</code> ({top_ref_row[1]} إحالة)" if top_ref_row else "لا يوجد"
        )

        open_disputes = (
            await session.execute(
                select(func.count(DisputeTicket.id)).where(DisputeTicket.status == "open")
            )
        ).scalar() or 0
        open_reports = (
            await session.execute(
                select(func.count(TaskReport.id)).where(TaskReport.status == "open")
            )
        ).scalar() or 0

    report_text = (
        f"📊 <b>تقرير النمو الإحصائي اليومي (ZetaGram):</b>\n\n"
        f"📅 <b>التاريخ:</b> <code>{yesterday_start.strftime('%Y-%m-%d')}</code>\n"
        f"👥 <b>الأعضاء الجدد:</b> <code>{new_users:,}</code>\n"
        f"✅ <b>المهام المكتملة:</b> <code>{tasks_yesterday:,}</code>\n"
        f"💰 <b>إجمالي الغرامات الموزعة:</b> <code>{earned_yesterday:,}</code> غرام\n"
        f"🏆 <b>أعلى داعي للأصدقاء:</b> {top_ref_str}\n"
        f"⚖️ <b>نزاعات مفتوحة:</b> <code>{open_disputes}</code> | 🚨 <b>بلاغات مفتوحة:</b> <code>{open_reports}</code>"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=report_text, parse_mode="HTML")
        except Exception:
            pass

    return report_text


async def run_daily_report_worker(bot):
    while True:
        try:
            now = utcnow()
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_until_midnight = max(1.0, (next_midnight - now).total_seconds())
            await asyncio.sleep(seconds_until_midnight)
            await compile_and_send_daily_report_once(bot)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error("Error in daily report worker: %s", e)


async def auto_approve_pending_proofs_once(bot, now=None) -> int:
    """Auto-approve pending proofs older than AUTO_APPROVE_PROOF_HOURS to protect workers."""
    now = now or utcnow()
    cutoff = now - timedelta(hours=AUTO_APPROVE_PROOF_HOURS)
    approved_count = 0

    async with AsyncSessionLocal() as session:
        pending_ids = (
            await session.execute(
                select(UserTask.id, UserTask.user_id, UserTask.task_id).where(
                    and_(
                        UserTask.status == "pending_approval",
                        or_(
                            and_(UserTask.submitted_at.isnot(None), UserTask.submitted_at <= cutoff),
                            and_(UserTask.submitted_at.is_(None), UserTask.completed_at <= cutoff),
                        ),
                    )
                )
            )
        ).all()

    for ut_id, uid, tid in pending_ids:
        reward_info = None
        creator_id = None
        creator_lang = "ar"
        worker_lang = "ar"
        task_title = ""
        async with user_lock_manager.acquire_ordered_locks(("ut", ut_id), ("user", uid), ("task", tid)):
            async with AsyncSessionLocal() as session:
                ut = (await session.execute(select(UserTask).where(UserTask.id == ut_id))).scalar_one_or_none()
                task = (await session.execute(select(Task).where(Task.id == tid))).scalar_one_or_none()
                user = (await session.execute(select(User).where(User.telegram_id == uid))).scalar_one_or_none()

                if not ut or ut.status != "pending_approval" or not task or not user:
                    continue

                if task.status == "active" and task.completed_qty < task.total_qty:
                    task.completed_qty += 1
                reward_info = await award_task_completion(
                    session, bot, user, task, ut, target_status="approved"
                )
                creator_id = task.created_by
                worker_lang = get_user_lang(user)
                if creator_id:
                    cr_user = (
                        await session.execute(select(User).where(User.telegram_id == creator_id))
                    ).scalar_one_or_none()
                    creator_lang = get_user_lang(cr_user)
                task_title = task.title
                await session.commit()
                approved_count += 1

        if reward_info:
            await dispatch_completion_notifications(bot, uid, reward_info)
            try:
                await bot.send_message(
                    chat_id=uid,
                    text=get_text(
                        worker_lang,
                        "notif_proof_auto_approved_worker",
                        title=esc(task_title),
                        reward=reward_info["total_reward"],
                    ),
                    parse_mode="HTML",
                )
            except Exception:
                pass
            if creator_id:
                try:
                    await bot.send_message(
                        chat_id=creator_id,
                        text=get_text(
                            creator_lang,
                            "notif_proof_auto_approved_creator",
                            worker_id=uid,
                            title=esc(task_title),
                            hours=AUTO_APPROVE_PROOF_HOURS,
                        ),
                        parse_mode="HTML",
                    )
                except Exception:
                    pass

    return approved_count


async def run_proof_auto_approve_worker(bot):
    while True:
        try:
            await asyncio.sleep(1800)
            await auto_approve_pending_proofs_once(bot)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error("Error in proof auto-approve worker: %s", e)


async def distribute_weekly_leaderboard_once(bot, now=None) -> dict | None:
    """
    Distribute weekly leaderboard prizes for the previous ISO week [prev_monday, this_monday).
    Idempotent via WeeklyLeaderboardRun(week_key).
    """
    now = now or utcnow()
    this_monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    prev_monday = this_monday - timedelta(days=7)
    iso_year, iso_week, _ = prev_monday.isocalendar()
    week_key = f"{iso_year}-W{iso_week:02d}"

    async with user_lock_manager.get_lock("weekly_leaderboard"):
        async with AsyncSessionLocal() as session:
            existing = (
                await session.execute(
                    select(WeeklyLeaderboardRun).where(WeeklyLeaderboardRun.week_key == week_key)
                )
            ).scalar_one_or_none()
            if existing:
                return None

            top_taskers = (
                await session.execute(
                    select(UserTask.user_id, func.count(UserTask.id).label("cnt"))
                    .where(
                        and_(
                            UserTask.status.in_(["completed", "approved"]),
                            UserTask.completed_at >= prev_monday,
                            UserTask.completed_at < this_monday,
                        )
                    )
                    .group_by(UserTask.user_id)
                    .order_by(func.count(UserTask.id).desc())
                    .limit(len(LEADERBOARD_PRIZES))
                )
            ).all()

            top_referrers = (
                await session.execute(
                    select(User.referred_by, func.count(User.telegram_id).label("cnt"))
                    .where(
                        and_(
                            User.referred_by.isnot(None),
                            User.created_at >= prev_monday,
                            User.created_at < this_monday,
                        )
                    )
                    .group_by(User.referred_by)
                    .order_by(func.count(User.telegram_id).desc())
                    .limit(len(LEADERBOARD_PRIZES))
                )
            ).all()

            awarded = []
            notify_meta = []
            for rank_idx, (uid, cnt) in enumerate(top_taskers):
                prize = LEADERBOARD_PRIZES[rank_idx]
                u = (await session.execute(select(User).where(User.telegram_id == uid))).scalar_one_or_none()
                if u:
                    u.balance += prize
                    session.add(
                        Transaction(
                            user_id=uid,
                            trans_type="leaderboard_prize",
                            amount=prize,
                            description=f"جائزة المركز #{rank_idx + 1} للمهام الأسبوعية ({week_key})",
                        )
                    )
                    awarded.append((uid, prize, f"المهام #{rank_idx + 1}"))
                    notify_meta.append((uid, prize, "lb_btn_tasks", rank_idx + 1, get_user_lang(u)))

            for rank_idx, (uid, cnt) in enumerate(top_referrers):
                prize = LEADERBOARD_PRIZES[rank_idx]
                u = (await session.execute(select(User).where(User.telegram_id == uid))).scalar_one_or_none()
                if u:
                    u.balance += prize
                    session.add(
                        Transaction(
                            user_id=uid,
                            trans_type="leaderboard_prize",
                            amount=prize,
                            description=f"جائزة المركز #{rank_idx + 1} للإحالات الأسبوعية ({week_key})",
                        )
                    )
                    awarded.append((uid, prize, f"الإحالات #{rank_idx + 1}"))
                    notify_meta.append((uid, prize, "lb_btn_refs", rank_idx + 1, get_user_lang(u)))

            session.add(WeeklyLeaderboardRun(week_key=week_key))
            await session.commit()

    for uid, prize, cat_key, rank_num, u_lang in notify_meta:
        cat_label = f"{get_text(u_lang, cat_key)} #{rank_num}"
        try:
            await bot.send_message(
                chat_id=uid,
                text=get_text(
                    u_lang,
                    "notif_leaderboard_winner",
                    week_key=week_key,
                    category=esc(cat_label),
                    prize=prize,
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass

    if awarded:
        summary = "\n".join([f"• <code>{u}</code> — {cat} (+{p:,} غرام)" for u, p, cat in awarded])
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"🏆 <b>توزيع جوائز الأسبوع ({week_key}):</b>\n\n{summary}",
                    parse_mode="HTML",
                )
            except Exception:
                pass

    return {"week_key": week_key, "awarded": awarded}


async def run_weekly_leaderboard_worker(bot):
    while True:
        try:
            await asyncio.sleep(3600)
            now = utcnow()
            if now.weekday() == 0:
                await distribute_weekly_leaderboard_once(bot, now=now)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error("Error in weekly leaderboard worker: %s", e)
