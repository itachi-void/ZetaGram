import os
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask, Transaction
from config import ADMIN_IDS

async def run_daily_backup_worker(bot):
    """
    Background worker that runs every 24 hours to automatically send a
    database backup file (bot.db) to all ADMIN_IDS.
    """
    while True:
        try:
            await asyncio.sleep(24 * 3600) # Sleep 24 hours
            db_path = "bot.db"
            if os.path.exists(db_path):
                now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                for admin_id in ADMIN_IDS:
                    try:
                        await bot.send_document(
                            chat_id=admin_id,
                            document=open(db_path, "rb"),
                            filename=f"auto_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db",
                            caption=f"💾 **النسخة الاحتياطية التلقائية لقاعدة البيانات (bot.db)**\n⏱️ التاريخ: `{now_str} UTC`",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in daily backup worker: {e}")

async def run_retention_reminders_worker(bot):
    """
    Background worker running every 4 hours to send friendly retention reminders to
    users who have been inactive for between 24 and 48 hours.
    """
    while True:
        try:
            await asyncio.sleep(4 * 3600)
            now = datetime.utcnow()
            t_24h_ago = now - timedelta(hours=24)
            t_48h_ago = now - timedelta(hours=48)

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User.telegram_id, User.first_name)
                    .where(and_(User.last_active_at <= t_24h_ago, User.last_active_at >= t_48h_ago))
                    .limit(50)
                )
                inactive_users = result.all()

            for uid, fname in inactive_users:
                try:
                    await bot.send_message(
                        chat_id=uid,
                        text=f"👋 **مرحباً {fname or ''}!** نسينا أن نذكرك بالمكافأة اليومية! 🎁\n\n"
                             f"قم بدخول البوت الآن واحصل على **+100 غرام مجاناً** وتدور عجلة الحظ للفوز بجوائز إضافية! 🎡",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in retention reminders worker: {e}")

async def run_daily_report_worker(bot):
    """
    Background worker that runs every day at midnight (UTC) to compile
    a daily growth report and deliver it to all ADMIN_IDS.
    """
    while True:
        try:
            now = datetime.utcnow()
            # Calculate seconds until next midnight
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_until_midnight = (next_midnight - now).total_seconds()
            await asyncio.sleep(seconds_until_midnight)

            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            async with AsyncSessionLocal() as session:
                # New users registered today
                new_users = (await session.execute(
                    select(func.count(User.telegram_id)).where(User.created_at >= today_start)
                )).scalar() or 0

                # Completed tasks today
                tasks_today = (await session.execute(
                    select(func.count(UserTask.id)).where(UserTask.completed_at >= today_start)
                )).scalar() or 0

                # Total points earned today
                earned_today = (await session.execute(
                    select(func.sum(Transaction.amount)).where(
                        and_(Transaction.created_at >= today_start, Transaction.amount > 0)
                    )
                )).scalar() or 0

                # Top referral inviter today
                top_ref_res = await session.execute(
                    select(User.referred_by, func.count(User.telegram_id).label("cnt"))
                    .where(and_(User.created_at >= today_start, User.referred_by.isnot(None)))
                    .group_by(User.referred_by)
                    .order_by(func.count(User.telegram_id).desc())
                    .limit(1)
                )
                top_ref_row = top_ref_res.first()
                top_ref_str = f"`{top_ref_row[0]}` ({top_ref_row[1]} إحالة)" if top_ref_row else "لا يوجد"

            report_text = (
                f"📊 **تقرير النمو الإحصائي اليومي (Daily Growth Report):**\n\n"
                f"📅 **التاريخ:** `{today_start.strftime('%Y-%m-%d')}`\n"
                f"👥 **الأعضاء الجدد اليوم:** `{new_users:,}`\n"
                f"✅ **المهام المنفذة اليوم:** `{tasks_today:,}`\n"
                f"💰 **إجمالي الغرامات المكتسبة اليوم:** `{earned_today:,}` غرام\n"
                f"🏆 **أعلى داعي للأصدقاء اليوم:** {top_ref_str}\n"
            )

            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(chat_id=admin_id, text=report_text, parse_mode="Markdown")
                except Exception:
                    pass

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in daily report worker: {e}")
