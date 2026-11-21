from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from config import BOT_NAME, REFERRAL_JOIN_BONUS, REFERRAL_ACTIVE_BONUS, DAILY_QUEST_TARGET, DAILY_QUEST_REWARD
from database.db import AsyncSessionLocal
from database.models import User, Task, UserTask
from utils.telegram_api import check_user_subscription_status
from utils.gatekeeper import (
    enforce_user_access,
    get_mandatory_channels_list,
    invalidate_sub_cache,
)
from utils.i18n import get_text
from utils.html_utils import esc


async def show_useful_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    channels = await get_mandatory_channels_list()
    links_str = ""
    for c in channels:
        links_str += f"📢 <b>{esc(c['title'])}:</b>\n{esc(c['channel_link'])}\n\n"
    if not links_str:
        links_str = "لا توجد روابط إضافية مضافة حالياً.\n\n"

    text = (
        f"🔗 <b>الروابط المفيدة ({esc(BOT_NAME)}):</b>\n\n"
        f"{links_str}"
        "💡 اضغط على الروابط أعلاه لمتابعة آخر التحديثات وأخبار الشبكة."
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]]
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )


async def show_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    text = (
        f"📋 <b>دليل وتعليمات استخدام {esc(BOT_NAME)}:</b>\n\n"
        "1️⃣ <b>كسب الأرباح:</b> اختر «🧑‍💻 الأرباح» واشترك في القنوات أو نفّذ مهام البوتات والمنشورات.\n"
        "2️⃣ <b>الترويج لقناتك:</b> اختر «📣 الترويج» وحدد النوع والجمهور والسعر مع ضمان مالي Escrow كامل.\n"
        "3️⃣ <b>المكافأة اليومية والتحدي:</b> سلسلة دخول يومي تصاعدية حتى +500 غرام + "
        f"تحدي {DAILY_QUEST_TARGET} مهام يومية (+{DAILY_QUEST_REWARD} غرام) + عجلة الحظ (<code>/spin</code>).\n"
        "4️⃣ <b>نظام الإحالة:</b> ادعُ أصدقاءك واكسب "
        f"+{REFERRAL_ACTIVE_BONUS} غرام عن كل صديق نشط + <b>10% عمولة دائمة</b> (ويحصل صديقك على +{REFERRAL_JOIN_BONUS} غرام).\n"
        "5️⃣ <b>الخزنة واليانصيب والشيكات:</b> استثمر رصيدك في الخزنة (<code>/vault</code>) أو شارك باليانصيب (<code>/raffle</code>).\n\n"
        "⚠️ <b>ملاحظة هامة:</b> يُمنع مغادرة القنوات قبل 7 أيام لتجنب الخصم التلقائي والحظر."
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]]
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_bot_public_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, _ = await enforce_user_access(update, context)
    if not ok:
        return

    async with AsyncSessionLocal() as session:
        users_cnt = (await session.execute(select(func.count(User.telegram_id)))).scalar() or 0
        tasks_cnt = (await session.execute(select(func.count(Task.id)))).scalar() or 0
        completed_cnt = (
            await session.execute(
                select(func.count(UserTask.id)).where(UserTask.status.in_(["completed", "approved"]))
            )
        ).scalar() or 0

    text = (
        f"📊 <b>إحصائيات شبكة {esc(BOT_NAME)}:</b>\n\n"
        f"👥 <b>إجمالي المستخدمين:</b> <code>{users_cnt:,}</code>\n"
        f"📌 <b>إجمالي الحملات:</b> <code>{tasks_cnt:,}</code>\n"
        f"✅ <b>المهام المنفذة بنجاح:</b> <code>{completed_cnt:,}</code>\n"
        f"⚡ <b>سرعة التحقق:</b> فوري وآمن 100%"
    )
    keyboard = [
        [InlineKeyboardButton("🏆 لوحة المتصدرين الأسبوعية", callback_data="show_leaderboard")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")],
    ]
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def _find_unsubbed_mandatory(bot, user_id: int):
    channels = await get_mandatory_channels_list()
    unsubbed = []
    for c in channels:
        status = await check_user_subscription_status(bot, c["channel_username"], user_id)
        if status == "not_member":
            unsubbed.append(c)
    return unsubbed


async def check_forced_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(
        update, context, require_mandatory_sub=False
    )
    if not ok:
        return

    user_id = update.effective_user.id
    lang = user.language if user and user.language else "ar"
    invalidate_sub_cache(user_id)

    unsubbed = await _find_unsubbed_mandatory(context.bot, user_id)
    if not unsubbed:
        await update.message.reply_text(get_text(lang, "forced_sub_ok"), parse_mode="HTML")
    else:
        keyboard = [
            [InlineKeyboardButton(f"📢 {c['title']}", url=c["channel_link"])]
            for c in unsubbed
        ]
        keyboard.append([InlineKeyboardButton("🔄 تحقق الآن", callback_data="recheck_forced_sub")])
        await update.message.reply_text(
            get_text(lang, "forced_sub_required"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def recheck_forced_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, user = await enforce_user_access(
        update, context, require_mandatory_sub=False
    )
    if not ok:
        return

    query = update.callback_query
    user_id = update.effective_user.id
    lang = user.language if user and user.language else "ar"
    invalidate_sub_cache(user_id)

    unsubbed = await _find_unsubbed_mandatory(context.bot, user_id)
    if not unsubbed:
        await query.answer("✅ تم التحقق من الاشتراك بنجاح!", show_alert=True)
        await query.edit_message_text(get_text(lang, "forced_sub_ok"), parse_mode="HTML")
    else:
        await query.answer("❌ لم تنضم لجميع القنوات الإجبارية بعد!", show_alert=True)
        keyboard = [
            [InlineKeyboardButton(f"📢 {c['title']}", url=c["channel_link"])]
            for c in unsubbed
        ]
        keyboard.append([InlineKeyboardButton("🔄 تحقق الآن", callback_data="recheck_forced_sub")])
        await query.edit_message_text(
            get_text(lang, "forced_sub_required"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
