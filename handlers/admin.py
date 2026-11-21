import os
import asyncio
import tempfile
from datetime import timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func, or_

from config import BOT_NAME
from database.db import AsyncSessionLocal, create_safe_sqlite_backup
from database.models import (
    User,
    Task,
    UserTask,
    DisputeTicket,
    TaskReport,
    Transaction,
    PromoCode,
    FlashEvent,
)
from utils.security import is_admin_user, sanitize_amount, user_lock_manager
from utils.telegram_api import parse_telegram_post_link, check_bot_is_admin
from utils.promotions import format_multiplier
from utils.i18n import get_text, get_user_lang
from utils.html_utils import esc, utcnow


async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "/admin"):
        return

    query = update.callback_query
    if query:
        await query.answer()

    text = (
        f"⚙️ <b>لوحة أدمن {esc(BOT_NAME)} التفاعلية الرئيسية:</b>\n\n"
        "مرحباً بك عزيزي الأدمن 👋 اختر القسم المراد التحكم به من القائمة أدناه:"
    )

    keyboard = [
        [
            InlineKeyboardButton("📊 الإحصائيات العامة", callback_data="admin_stats_view"),
            InlineKeyboardButton("💾 تحميل النسخة الاحتياطية", callback_data="admin_backup_db"),
        ],
        [
            InlineKeyboardButton("➕/➖ تعديل رصيد مستخدم", callback_data="admin_balance_help"),
            InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_ban_help"),
        ],
        [
            InlineKeyboardButton("📑 إدارة المهام النشطة", callback_data="admin_tasks_manage"),
            InlineKeyboardButton("⚖️ تذاكر الاعتراض والنزاع", callback_data="admin_tickets_manage"),
        ],
        [
            InlineKeyboardButton("🚨 بلاغات المهام", callback_data="admin_reports_manage"),
            InlineKeyboardButton("📢 الاشتراك الإجباري", callback_data="admin_mand_subs_view"),
        ],
        [
            InlineKeyboardButton("🔥 العروض والأكواد (Promos & Events)", callback_data="admin_promos_menu"),
        ],
        [
            InlineKeyboardButton("📢 الإذاعة العامة (Broadcast)", callback_data="admin_broadcast_help"),
        ],
    ]

    markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def admin_stats_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_stats_view"):
        return

    query = update.callback_query
    if query:
        await query.answer()

    async with AsyncSessionLocal() as session:
        users_count = (await session.execute(select(func.count(User.telegram_id)))).scalar() or 0
        tasks_count = (await session.execute(select(func.count(Task.id)))).scalar() or 0
        active_tasks = (
            await session.execute(select(func.count(Task.id)).where(Task.status == "active"))
        ).scalar() or 0
        completed_tasks = (
            await session.execute(
                select(func.count(UserTask.id)).where(UserTask.status.in_(["completed", "approved"]))
            )
        ).scalar() or 0
        open_tickets = (
            await session.execute(
                select(func.count(DisputeTicket.id)).where(DisputeTicket.status == "open")
            )
        ).scalar() or 0
        open_reports = (
            await session.execute(
                select(func.count(TaskReport.id)).where(TaskReport.status == "open")
            )
        ).scalar() or 0

    text = (
        f"📊 <b>إحصائيات النظام الشاملة:</b>\n\n"
        f"👥 <b>إجمالي المستخدمين:</b> <code>{users_count:,}</code>\n"
        f"📌 <b>إجمالي المهام:</b> <code>{tasks_count:,}</code>\n"
        f"🟢 <b>المهام النشطة:</b> <code>{active_tasks:,}</code>\n"
        f"✅ <b>المهام المكتملة:</b> <code>{completed_tasks:,}</code>\n"
        f"⚖️ <b>تذاكر الاعتراض المفتوحة:</b> <code>{open_tickets:,}</code>\n"
        f"🚨 <b>بلاغات المهام المفتوحة:</b> <code>{open_reports:,}</code>"
    )

    keyboard = [[InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin_main_menu")]]
    markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def admin_backup_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_backup_db"):
        return

    query = update.callback_query
    if query:
        await query.answer("⏳ جاري إنشاء نسخة آمنة...")

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db", prefix="zetagram_manual_")
    os.close(tmp_fd)
    try:
        if not create_safe_sqlite_backup(tmp_path):
            await context.bot.send_message(
                chat_id=user_id, text="❌ تعذر إنشاء نسخة احتياطية من قاعدة البيانات."
            )
            return

        fname = f"bot_backup_{utcnow().strftime('%Y%m%d_%H%M%S')}.db"
        with open(tmp_path, "rb") as f:
            await context.bot.send_document(
                chat_id=user_id,
                document=f,
                filename=fname,
                caption="💾 <b>نسخة احتياطية آمنة (WAL-safe) لقاعدة بيانات البوت</b>",
                parse_mode="HTML",
            )
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


async def admin_balance_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_balance_help"):
        return

    query = update.callback_query
    await query.answer()
    text = (
        "➕/➖ <b>تعليمات تعديل رصيد مستخدم:</b>\n\n"
        "يمكنك إضافة أو خصم رصيد أي مستخدم عبر التعليمة التالية:\n"
        "<code>/setbalance &lt;user_id&gt; &lt;المبلغ&gt;</code>\n\n"
        "مثال للإضافة: <code>/setbalance 123456789 5000</code>\n"
        "مثال للخصم: <code>/setbalance 123456789 -2000</code>\n\n"
        "كما يمكنك عرض ملف أي مستخدم via:\n"
        "<code>/userinfo &lt;user_id&gt;</code>"
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_main_menu")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_setbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "/setbalance"):
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ <b>الاستخدام الخاطئ!</b>\n"
            "الصيغة: <code>/setbalance &lt;user_id&gt; &lt;المبلغ&gt;</code>",
            parse_mode="HTML",
        )
        return

    try:
        target_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال أرقام صحيحة.")
        return

    async with user_lock_manager.get_lock(target_id):
        async with AsyncSessionLocal() as session:
            target_user = (
                await session.execute(select(User).where(User.telegram_id == target_id))
            ).scalar_one_or_none()
            if not target_user:
                await update.message.reply_text("❌ لم يتم العثور على هذا المستخدم في القاعدة.")
                return

            target_user.balance = max(0, target_user.balance + amount)
            session.add(
                Transaction(
                    user_id=target_id,
                    trans_type="admin_adjust",
                    amount=amount,
                    description=f"تعديل بواسطة الأدمن {user_id}",
                )
            )
            await session.commit()
            new_bal = target_user.balance

    await update.message.reply_text(
        f"✅ <b>تم تعديل الرصيد بنجاح!</b>\n"
        f"👤 المستهدف: <code>{target_id}</code>\n"
        f"💰 التغيير: <code>{amount:+,}</code> غرام\n"
        f"💳 الرصيد الجديد: <code>{new_bal:,}</code> غرام",
        parse_mode="HTML",
    )


async def handle_userinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "/userinfo"):
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "الصيغة: <code>/userinfo &lt;user_id&gt;</code>", parse_mode="HTML"
        )
        return

    target_id = int(args[0])
    async with AsyncSessionLocal() as session:
        u = (
            await session.execute(select(User).where(User.telegram_id == target_id))
        ).scalar_one_or_none()
        if not u:
            await update.message.reply_text("❌ لم يتم العثور على المستخدم.")
            return
        tasks_done = (
            await session.execute(
                select(func.count(UserTask.id)).where(
                    UserTask.user_id == target_id,
                    UserTask.status.in_(["completed", "approved"]),
                )
            )
        ).scalar() or 0
        refs = (
            await session.execute(
                select(func.count(User.telegram_id)).where(User.referred_by == target_id)
            )
        ).scalar() or 0

    ban_str = (
        u.banned_until.strftime("%Y-%m-%d %H:%M UTC")
        if u.banned_until and utcnow() < u.banned_until
        else "غير محظور"
    )
    text = (
        f"👤 <b>ملف المستخدم <code>{target_id}</code>:</b>\n\n"
        f"• الاسم: {esc(u.first_name)} (@{esc(u.username or '-')})\n"
        f"• الرصيد: <code>{u.balance:,}</code> غرام\n"
        f"• المستوى: <code>VIP {u.vip_level or 1}</code>\n"
        f"• نقاط الثقة: <code>{u.trust_score if u.trust_score is not None else 100}</code>\n"
        f"• الكابتشا: {'✅ موثق' if u.is_captcha_verified else '❌ غير موثق'}\n"
        f"• المهام المكتملة: <code>{tasks_done}</code> | الإحالات: <code>{refs}</code>\n"
        f"• المخالفات: <code>{u.violations_count or 0}</code> | الحظر: <code>{ban_str}</code>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def admin_ban_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_ban_help"):
        return

    query = update.callback_query
    await query.answer()
    text = (
        "🚫 <b>تعليمات إدارة الحظر:</b>\n\n"
        "لحظر مستخدم لمدة معينة بالأيام:\n"
        "<code>/ban &lt;user_id&gt; &lt;عدد_الأيام&gt;</code> (مثال: <code>/ban 123456789 7</code>)\n\n"
        "لإلغاء حظر مستخدم:\n"
        "<code>/unban &lt;user_id&gt;</code> (مثال: <code>/unban 123456789</code>)"
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_main_menu")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "/ban"):
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "الصيغة: <code>/ban &lt;user_id&gt; [عدد_الأيام]</code>", parse_mode="HTML"
        )
        return

    try:
        target_id = int(args[0])
        days = int(args[1]) if len(args) > 1 else 30
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال آيدي وعدد أيام صحيحة.")
        return

    async with AsyncSessionLocal() as session:
        target_user = (
            await session.execute(select(User).where(User.telegram_id == target_id))
        ).scalar_one_or_none()
        if not target_user:
            await update.message.reply_text("❌ لم يتم العثور على هذا المستخدم.")
            return

        target_user.banned_until = utcnow() + timedelta(days=days)
        await session.commit()

    await update.message.reply_text(
        f"🚫 تم حظر العضو <code>{target_id}</code> لمدة {days} يوم.", parse_mode="HTML"
    )


async def handle_unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "/unban"):
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "الصيغة: <code>/unban &lt;user_id&gt;</code>", parse_mode="HTML"
        )
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال آيدي صحيح.")
        return

    async with AsyncSessionLocal() as session:
        target_user = (
            await session.execute(select(User).where(User.telegram_id == target_id))
        ).scalar_one_or_none()
        if target_user:
            target_user.banned_until = None
            await session.commit()

    await update.message.reply_text(
        f"✅ تم إلغاء حظر العضو <code>{target_id}</code> بنجاح.", parse_mode="HTML"
    )


async def admin_tasks_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_tasks_manage"):
        return

    query = update.callback_query
    await query.answer()

    async with AsyncSessionLocal() as session:
        tasks = (
            await session.execute(select(Task).order_by(Task.created_at.desc()).limit(10))
        ).scalars().all()

    text = "📑 <b>إدارة المهام (آخر 10 مهام):</b>\n\n"
    keyboard = []

    if not tasks:
        text += "لا توجد مهام مضافة في القاعدة."
    else:
        for t in tasks:
            status_icon = "🟢" if t.status == "active" else "🔴"
            text += f"{status_icon} <b>{esc(t.title)}</b> (ID: <code>{t.id}</code>)\n"
            text += f"النوع: <code>{esc(t.task_type)}</code> | المنفذ: <code>{t.completed_qty}/{t.total_qty}</code>\n\n"
            keyboard.append(
                [
                    InlineKeyboardButton(f"🗑️ حذف #{t.id}", callback_data=f"admin_deltask_{t.id}"),
                    InlineKeyboardButton(
                        f"⏯️ تبديل الحالة #{t.id}", callback_data=f"admin_toggletask_{t.id}"
                    ),
                ]
            )

    keyboard.append([InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin_main_menu")])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_admin_task_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_task_action"):
        return

    query = update.callback_query
    data = query.data
    if data.startswith("admin_deltask_"):
        t_id = int(data.replace("admin_deltask_", ""))
        async with AsyncSessionLocal() as session:
            t = (await session.execute(select(Task).where(Task.id == t_id))).scalar_one_or_none()
            if t:
                await session.delete(t)
                await session.commit()
                await query.answer("✅ تم حذف المهمة بنجاح", show_alert=True)
    elif data.startswith("admin_toggletask_"):
        t_id = int(data.replace("admin_toggletask_", ""))
        async with AsyncSessionLocal() as session:
            t = (await session.execute(select(Task).where(Task.id == t_id))).scalar_one_or_none()
            if t:
                t.status = "paused" if t.status == "active" else "active"
                await session.commit()
                await query.answer(f"✅ تم تغيير حالة المهمة إلى {t.status}", show_alert=True)

    await admin_tasks_manage(update, context)


async def admin_tickets_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_tickets_manage"):
        return

    query = update.callback_query
    await query.answer()

    async with AsyncSessionLocal() as session:
        tickets = (
            await session.execute(
                select(DisputeTicket)
                .where(DisputeTicket.status == "open")
                .order_by(DisputeTicket.created_at.desc())
                .limit(10)
            )
        ).scalars().all()

    keyboard = []
    if not tickets:
        text = "⚖️ <b>تذاكر الاعتراض المفتوحة:</b>\n\nلا توجد تذاكر مفتوحة حالياً! ✅"
    else:
        text = f"⚖️ <b>تذاكر الاعتراض المفتوحة ({len(tickets)}):</b>\n\nاختر تذكرة لمراجعتها والبت فيها:"
        for tk in tickets:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🎟️ تذكرة #{tk.id} — عامل {tk.user_id} (مهمة #{tk.task_id})",
                        callback_data=f"admin_view_ticket_{tk.id}",
                    )
                ]
            )

    keyboard.append([InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin_main_menu")])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_view_ticket_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_view_ticket"):
        return

    query = update.callback_query
    await query.answer()
    ticket_id = int(query.data.replace("admin_view_ticket_", ""))

    async with AsyncSessionLocal() as session:
        tk = (
            await session.execute(select(DisputeTicket).where(DisputeTicket.id == ticket_id))
        ).scalar_one_or_none()
        task = (
            await session.execute(select(Task).where(Task.id == tk.task_id))
        ).scalar_one_or_none() if tk else None

    if not tk:
        await query.answer("❌ التذكرة غير موجودة.", show_alert=True)
        return

    caption = (
        f"⚖️ <b>تفاصيل التذكرة (#Ticket-{tk.id})</b>\n\n"
        f"👤 <b>العامل:</b> <code>{tk.user_id}</code>\n"
        f"👤 <b>المعلن:</b> <code>{task.created_by if task else '-'}</code>\n"
        f"📌 <b>المهمة:</b> {esc(task.title if task else '-')}\n"
        f"💰 <b>المستحق:</b> <code>{task.reward_grams if task else 0:,}</code> غرام\n"
        f"📝 <b>سبب الرفض الأصلي:</b> {esc(tk.reason or '-')}"
    )
    keyboard = [
        [
            InlineKeyboardButton("💰 اعتماد ودفع للعامل", callback_data=f"admin_disp_pay_{tk.id}"),
            InlineKeyboardButton("❌ تأكيد الرفض والإغلاق", callback_data=f"admin_disp_rej_{tk.id}"),
        ],
        [InlineKeyboardButton("🔙 رجوع للتذاكر", callback_data="admin_tickets_manage")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if tk.proof_file_id:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=tk.proof_file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=markup,
        )
    else:
        await query.edit_message_text(caption, parse_mode="HTML", reply_markup=markup)


async def admin_reports_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_reports_manage"):
        return

    query = update.callback_query
    await query.answer()

    async with AsyncSessionLocal() as session:
        reports = (
            await session.execute(
                select(TaskReport)
                .where(TaskReport.status == "open")
                .order_by(TaskReport.created_at.desc())
                .limit(10)
            )
        ).scalars().all()

    keyboard = []
    if not reports:
        text = "🚨 <b>بلاغات المهام المفتوحة:</b>\n\nلا توجد بلاغات مفتوحة حالياً! ✅"
    else:
        text = f"🚨 <b>بلاغات المهام المفتوحة ({len(reports)}):</b>\n\n"
        for r in reports:
            text += f"• <b>بلاغ #{r.id}</b> — مهمة <code>#{r.task_id}</code> من <code>{r.reporter_id}</code>\n  السبب: {esc(r.reason)}\n"
            keyboard.append(
                [
                    InlineKeyboardButton(f"⏸️ إيقاف #{r.task_id}", callback_data=f"admin_report_pause_{r.id}"),
                    InlineKeyboardButton(f"🗑️ حذف #{r.task_id}", callback_data=f"admin_report_del_{r.id}"),
                    InlineKeyboardButton("✔️ إغلاق", callback_data=f"admin_report_dismiss_{r.id}"),
                ]
            )

    keyboard.append([InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin_main_menu")])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_admin_report_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_report"):
        return

    query = update.callback_query
    parts = query.data.split("_")
    # admin_report_<action>_<rid>
    action = parts[2]
    rid = int(parts[3])

    async with AsyncSessionLocal() as session:
        rep = (await session.execute(select(TaskReport).where(TaskReport.id == rid))).scalar_one_or_none()
        if not rep:
            await query.answer("❌ البلاغ غير موجود.", show_alert=True)
            return
        task = (await session.execute(select(Task).where(Task.id == rep.task_id))).scalar_one_or_none()

        if action == "pause" and task:
            task.status = "paused"
            rep.status = "resolved"
        elif action == "del" and task:
            await session.delete(task)
            rep.status = "resolved"
        elif action == "dismiss":
            rep.status = "dismissed"
        await session.commit()

    await query.answer("✅ تم تنفيذ الإجراء على البلاغ!", show_alert=True)
    await admin_reports_manage(update, context)


async def admin_broadcast_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_broadcast_help"):
        return

    query = update.callback_query
    await query.answer()
    text = (
        "📢 <b>إذاعة رسالة لجميع المستخدمين:</b>\n\n"
        "يمكنك إرسال إذاعة لجميع مستخدمي البوت عبر التعليمة التالية:\n"
        "<code>/broadcast &lt;الرسالة&gt;</code>\n\n"
        "أو قم بالرد على أي رسالة (نص، صورة، فيديو، ميديا) بالتعليمة:\n"
        "<code>/broadcast</code>"
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_main_menu")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def _run_broadcast_bg(bot, admin_id: int, all_user_ids: list, broadcast_text: str, reply_msg):
    success = 0
    failed = 0
    for uid in all_user_ids:
        try:
            if reply_msg:
                await reply_msg.copy(chat_id=uid)
            else:
                await bot.send_message(chat_id=uid, text=broadcast_text)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    try:
        await bot.send_message(
            chat_id=admin_id,
            text=(
                f"✅ <b>تم الانتهاء من الإذاعة!</b>\n\n"
                f"🎯 الناجح: {success:,}\n"
                f"❌ الفاشل: {failed:,}"
            ),
            parse_mode="HTML",
        )
    except Exception:
        pass


async def handle_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "/broadcast"):
        return

    reply = update.message.reply_to_message
    broadcast_text = " ".join(context.args)

    if not reply and not broadcast_text:
        await update.message.reply_text(
            "⚠️ يرجى كتابة نص الرسالة بعد <code>/broadcast</code> أو الرد على الرسالة المراد إذاعتها.",
            parse_mode="HTML",
        )
        return

    async with AsyncSessionLocal() as session:
        all_user_ids = (await session.execute(select(User.telegram_id))).scalars().all()

    await update.message.reply_text(f"🚀 جاري بدء الإذاعة في الخلفية لـ {len(all_user_ids):,} مستخدم...")
    asyncio.create_task(
        _run_broadcast_bg(context.bot, user_id, list(all_user_ids), broadcast_text, reply)
    )


async def add_task_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "/addtask"):
        return

    args = context.args
    if len(args) < 6:
        await update.message.reply_text(
            "⚠️ <b>الاستخدام الخاطئ!</b>\n"
            "التعليمة الصحيحة:\n"
            "<code>/addtask &lt;type&gt; &lt;reward&gt; &lt;qty&gt; &lt;target_url&gt; &lt;chat_id&gt; &lt;title...&gt;</code>\n\n"
            "أنواع المهام المتاحة:\n<code>channel</code>, <code>group</code>, <code>post</code>, "
            "<code>bot_normal</code>, <code>bot_webapp</code>, <code>bot_conditions</code>, "
            "<code>reaction_random</code>, <code>reaction_fixed</code>, <code>premium</code>",
            parse_mode="HTML",
        )
        return

    task_type = args[0]
    ok_r, reward, err_r = sanitize_amount(args[1], min_val=1, max_val=1_000_000)
    if not ok_r:
        await update.message.reply_text(err_r)
        return
    ok_q, qty, err_q = sanitize_amount(args[2], min_val=1, max_val=1_000_000)
    if not ok_q:
        await update.message.reply_text(err_q)
        return

    target_url = args[3]
    chat_id = None if args[4] in ("-", "none", "null") else args[4]
    title = " ".join(args[5:])

    target_msg_id = None
    auto_rx = False
    if task_type in ("reaction_random", "reaction_fixed"):
        parsed_chat, parsed_msg = parse_telegram_post_link(target_url)
        if not chat_id and parsed_chat:
            chat_id = parsed_chat
        target_msg_id = parsed_msg
        if chat_id and target_msg_id:
            is_adm, _ = await check_bot_is_admin(context.bot, chat_id)
            auto_rx = bool(is_adm)

    async with AsyncSessionLocal() as session:
        new_task = Task(
            title=title[:128],
            task_type=task_type,
            target_url=target_url,
            chat_id=chat_id,
            reward_grams=reward,
            total_qty=qty,
            escrow_balance=reward * qty,
            requires_premium=(task_type == "premium"),
            target_message_id=target_msg_id,
            auto_verify_reactions=auto_rx,
            created_by=user_id,
        )
        session.add(new_task)
        await session.commit()
        tid = new_task.id

    rx_info = " ⚡ (تحقق تفاعل تلقائي مفعّل)" if auto_rx else ""
    await update.message.reply_text(
        f"🎉 تم إضافة المهمة بنجاح برقم ID: <code>{tid}</code>{rx_info}", parse_mode="HTML"
    )


async def admin_promos_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_promos_menu"):
        return

    query = update.callback_query
    if query:
        await query.answer()

    now = utcnow()
    async with AsyncSessionLocal() as session:
        events = (
            await session.execute(
                select(FlashEvent)
                .where(FlashEvent.is_active == True, FlashEvent.ends_at > now)
                .order_by(FlashEvent.id.desc())
                .limit(5)
            )
        ).scalars().all()
        promos = (
            await session.execute(
                select(PromoCode).order_by(PromoCode.id.desc()).limit(10)
            )
        ).scalars().all()

    lines = ["🔥 <b>إدارة العروض الترويجية وساعات الذروة:</b>\n"]
    keyboard = []

    if events:
        lines.append("⚡ <b>أحداث ساعات الذروة النشطة:</b>")
        for ev in events:
            mult_s = format_multiplier(ev.multiplier_pct)
            lines.append(
                f"• <b>#{ev.id} {esc(ev.title)}</b> — <code>{mult_s}</code> (حتى <code>{ev.ends_at.strftime('%Y-%m-%d %H:%M UTC')}</code>)"
            )
            keyboard.append(
                [
                    InlineKeyboardButton(f"⏹️ إيقاف #{ev.id}", callback_data=f"admin_stop_flash_{ev.id}"),
                    InlineKeyboardButton(f"📢 إشعار الكل #{ev.id}", callback_data=f"admin_notify_flash_{ev.id}"),
                ]
            )
    else:
        lines.append("⚪ لا توجد أحداث ساعات ذروة نشطة حالياً.")

    lines.append("\n🎟️ <b>أكواد الخصم الأخيرة:</b>")
    if promos:
        for p in promos:
            st = "🟢" if p.is_active else "🔴"
            scope_ar = "الإجمالي" if p.discount_scope == "total" else "العمولة"
            lines.append(
                f"{st} <code>{esc(p.code)}</code> — خصم <b>{p.discount_percent}%</b> ({scope_ar}) | "
                f"الاستخدام: <code>{p.used_count}/{p.max_uses}</code>"
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"⏯️ {'تعطيل' if p.is_active else 'تفعيل'} {p.code}",
                        callback_data=f"admin_toggle_promo_{p.id}",
                    )
                ]
            )
    else:
        lines.append("لا توجد أكواد خصم مضافة بعد.")

    lines.append(
        "\n📌 <b>الأوامر السريعة للأدمن:</b>\n"
        "• إنشاء كود خصم:\n"
        "<code>/addpromo &lt;CODE&gt; &lt;DISCOUNT_%&gt; &lt;MAX_USES&gt; [commission|total] [HOURS] [MIN_ORDER]</code>\n"
        "• إطلاق ساعات ذروة (مثال 2x لمدة ساعتين):\n"
        "<code>/flash &lt;MULTIPLIER&gt; &lt;HOURS&gt; [TITLE...]</code>\n"
        "• إيقاف كل الأحداث: <code>/stopflash</code>"
    )

    keyboard.append([InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin_main_menu")])
    markup = InlineKeyboardMarkup(keyboard)
    text = "\n".join(lines)
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def handle_add_promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "/addpromo"):
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "⚠️ <b>الصيغة الصحيحة:</b>\n"
            "<code>/addpromo &lt;CODE&gt; &lt;DISCOUNT_%&gt; &lt;MAX_USES&gt; [commission|total] [HOURS_VALID] [MIN_ORDER]</code>\n\n"
            "مثال: <code>/addpromo ZETA50 50 100 commission 72 1000</code>",
            parse_mode="HTML",
        )
        return

    code = args[0].strip().upper()
    if len(code) < 2 or len(code) > 40 or not code.replace("-", "").replace("_", "").isalnum():
        await update.message.reply_text("❌ كود الخصم يجب أن يتكون من 2 إلى 40 حرف/رقم إنجليزي.")
        return

    scope = "commission"
    if len(args) >= 4 and args[3].strip().lower() in ("commission", "total"):
        scope = args[3].strip().lower()

    max_pct = 50 if scope == "total" else 100
    ok_d, pct, err_d = sanitize_amount(args[1], min_val=1, max_val=max_pct)
    if not ok_d:
        await update.message.reply_text(err_d)
        return

    ok_u, max_uses, err_u = sanitize_amount(args[2], min_val=1, max_val=1_000_000)
    if not ok_u:
        await update.message.reply_text(err_u)
        return

    expires_at = None
    if len(args) >= 5:
        try:
            hours = float(args[4])
            if hours > 0:
                expires_at = utcnow() + timedelta(hours=min(hours, 8760))
        except ValueError:
            await update.message.reply_text("❌ عدد الساعات غير صحيح.")
            return

    min_order = 0
    if len(args) >= 6:
        ok_m, min_order, err_m = sanitize_amount(args[5], min_val=0, max_val=100_000_000)
        if not ok_m:
            await update.message.reply_text(err_m)
            return

    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(select(PromoCode).where(PromoCode.code == code))
        ).scalar_one_or_none()
        if existing:
            await update.message.reply_text(f"⚠️ الكود <code>{esc(code)}</code> موجود مسبقاً.", parse_mode="HTML")
            return

        promo = PromoCode(
            code=code,
            discount_percent=pct,
            discount_scope=scope,
            max_uses=max_uses,
            used_count=0,
            min_order_grams=min_order,
            expires_at=expires_at,
            is_active=True,
            created_by=user_id,
        )
        session.add(promo)
        await session.commit()

    exp_str = expires_at.strftime("%Y-%m-%d %H:%M UTC") if expires_at else "غير محدد"
    await update.message.reply_text(
        f"✅ <b>تم إنشاء كود الخصم بنجاح!</b>\n\n"
        f"🎟️ الكود: <code>{esc(code)}</code>\n"
        f"📉 الخصم: <b>{pct}%</b> (<code>{scope}</code>)\n"
        f"👥 الاستخدامات: <code>{max_uses:,}</code>\n"
        f"💵 الحد الأدنى للطلب: <code>{min_order:,}</code> غرام\n"
        f"⏳ الصلاحية: <code>{exp_str}</code>",
        parse_mode="HTML",
    )


async def handle_flash_event_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "/flash"):
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ <b>الصيغة الصحيحة:</b>\n"
            "<code>/flash &lt;MULTIPLIER&gt; &lt;HOURS&gt; [TITLE...]</code>\n\n"
            "مثال: <code>/flash 2 3 Happy Hour X2</code>",
            parse_mode="HTML",
        )
        return

    try:
        multiplier = float(args[0])
        hours = float(args[1])
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال أرقام صحيحة للمضاعف وعدد الساعات.")
        return

    if not (1.1 <= multiplier <= 5.0):
        await update.message.reply_text("❌ المضاعف يجب أن يكون بين 1.1 و 5.0 (مثال: 1.5 أو 2).")
        return
    if not (0.25 <= hours <= 168.0):
        await update.message.reply_text("❌ المدة يجب أن تكون بين 0.25 و 168 ساعة.")
        return

    mult_pct = int(round(multiplier * 100))
    title = " ".join(args[2:]).strip()[:120] if len(args) > 2 else f"Happy Hour {format_multiplier(mult_pct)}"
    now = utcnow()
    ends_at = now + timedelta(hours=hours)

    async with AsyncSessionLocal() as session:
        ev = FlashEvent(
            title=title,
            multiplier_pct=mult_pct,
            starts_at=now,
            ends_at=ends_at,
            is_active=True,
            created_by=user_id,
        )
        session.add(ev)
        await session.commit()
        ev_id = ev.id

    await update.message.reply_text(
        f"🔥 <b>تم إطلاق حدث ساعات الذروة (#{ev_id})!</b>\n\n"
        f"🏷️ العنوان: <b>{esc(title)}</b>\n"
        f"⚡ المضاعف: <code>{format_multiplier(mult_pct)}</code>\n"
        f"⏰ ينتهي في: <code>{ends_at.strftime('%Y-%m-%d %H:%M UTC')}</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📢 إرسال إشعار للمستخدمين", callback_data=f"admin_notify_flash_{ev_id}")],
                [InlineKeyboardButton("⏹️ إيقاف الحدث", callback_data=f"admin_stop_flash_{ev_id}")],
            ]
        ),
    )


async def handle_stop_flash_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "/stopflash"):
        return

    async with AsyncSessionLocal() as session:
        active_events = (
            await session.execute(select(FlashEvent).where(FlashEvent.is_active == True))
        ).scalars().all()
        stopped = 0
        for ev in active_events:
            ev.is_active = False
            stopped += 1
        await session.commit()

    await update.message.reply_text(
        f"⏹️ تم إيقاف <b>{stopped}</b> حدث ساعات ذروة.", parse_mode="HTML"
    )


async def _run_flash_notify_bg(
    bot, admin_id: int, title: str, mult_str: str, ends_str: str, recipients: list[tuple[int, str]]
):
    sent = 0
    failed = 0
    for uid, u_lang in recipients:
        try:
            msg = get_text(
                u_lang,
                "flash_broadcast_notif",
                bot_name=esc(BOT_NAME),
                title=esc(title),
                mult=mult_str,
                ends=ends_str,
            )
            await bot.send_message(chat_id=uid, text=msg, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    try:
        await bot.send_message(
            chat_id=admin_id,
            text=f"📢 اكتمل إشعار حدث الذروة: ✅ {sent:,} | ❌ {failed:,}",
        )
    except Exception:
        pass


async def handle_admin_promo_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context.bot, "admin_promo_cb"):
        return

    query = update.callback_query
    data = query.data

    if data.startswith("admin_stop_flash_"):
        ev_id = int(data.replace("admin_stop_flash_", ""))
        async with AsyncSessionLocal() as session:
            ev = (await session.execute(select(FlashEvent).where(FlashEvent.id == ev_id))).scalar_one_or_none()
            if ev:
                ev.is_active = False
                await session.commit()
        await query.answer("⏹️ تم إيقاف حدث الذروة.", show_alert=True)
        await admin_promos_menu(update, context)

    elif data.startswith("admin_toggle_promo_"):
        pid = int(data.replace("admin_toggle_promo_", ""))
        async with AsyncSessionLocal() as session:
            p = (await session.execute(select(PromoCode).where(PromoCode.id == pid))).scalar_one_or_none()
            if p:
                p.is_active = not bool(p.is_active)
                await session.commit()
        await query.answer("✅ تم تحديث حالة الكود.", show_alert=True)
        await admin_promos_menu(update, context)

    elif data.startswith("admin_notify_flash_"):
        ev_id = int(data.replace("admin_notify_flash_", ""))
        async with AsyncSessionLocal() as session:
            ev = (await session.execute(select(FlashEvent).where(FlashEvent.id == ev_id))).scalar_one_or_none()
            if not ev or not ev.is_active:
                await query.answer("⚠️ الحدث غير نشط أو غير موجود.", show_alert=True)
                return
            rows = (
                await session.execute(
                    select(User.telegram_id, User.language).where(
                        or_(User.notifications_enabled == True, User.notifications_enabled.is_(None))
                    )
                )
            ).all()

        recipients = [(uid, (lang or "ar").lower()) for uid, lang in rows]
        await query.answer("📢 جاري إرسال الإشعارات بالخلفية...", show_alert=True)
        asyncio.create_task(
            _run_flash_notify_bg(
                context.bot,
                user_id,
                ev.title,
                format_multiplier(ev.multiplier_pct),
                ev.ends_at.strftime("%Y-%m-%d %H:%M"),
                recipients,
            )
        )

