import io
import os
import re
import ast
import time
import asyncio
import sqlite3
import py_compile
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from PIL import Image, ImageDraw
from sqlalchemy import select, text

import config
from database.db import configure_db, init_db, migrate_sqlite_columns, create_safe_sqlite_backup, AsyncSessionLocal
from database.models import (
    Base,
    User,
    Task,
    UserTask,
    Voucher,
    VoucherRedemption,
    Transaction,
    MandatoryChannel,
    DisputeTicket,
    SkippedTask,
    TaskReport,
)
from utils.captcha import generate_image_captcha
from utils.image_hash import compute_dhash, is_similar_hash
from utils.security import rate_limiter
from utils.gatekeeper import reset_gatekeeper_caches
from utils.anti_unsub_checker import check_unsubs_once
from utils.scheduled_tasks import (
    compile_and_send_daily_report_once,
    run_retention_reminders_once,
    auto_approve_pending_proofs_once,
    distribute_weekly_leaderboard_once,
)
from utils.html_utils import utcnow
from handlers.bonus import claim_daily_bonus
from handlers.spin import spin_wheel_command
from handlers.transfer import handle_transfer_command
from handlers.vouchers import redeem_voucher
from handlers.levels import claim_milestone_callback
from handlers.task_actions import (
    award_task_completion,
    check_task_callback,
    start_post_callback,
    claim_post_callback,
    handle_bot_forward_message,
)
from handlers.proof_review import (
    process_proof_photo,
    handle_worker_dispute_callbacks,
)
from handlers.promotion import mytask_action_callback
from handlers.dynamic_subs import prompt_add_mandatory_channel
import main as bot_main


def _make_png_bytes(color=(200, 100, 50), pattern=1) -> bytes:
    img = Image.new("RGB", (120, 120), color)
    draw = ImageDraw.Draw(img)
    if pattern == 1:
        draw.rectangle([10, 10, 60, 60], fill=(20, 200, 220))
        draw.line([(0, 0), (120, 120)], fill=(255, 255, 255), width=5)
    elif pattern == 2:
        draw.ellipse([30, 10, 110, 90], fill=(250, 220, 30))
        draw.rectangle([0, 70, 50, 120], fill=(10, 20, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_mock_bot():
    bot = MagicMock()
    bot.id = 999999
    bot.username = "ZetaGramTestBot"
    bot.get_me = AsyncMock(return_value=SimpleNamespace(id=999999, username="ZetaGramTestBot"))
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.send_document = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=SimpleNamespace(status="member", is_member=True))
    return bot


def _make_context(bot, args=None, user_data=None):
    ctx = MagicMock()
    ctx.bot = bot
    ctx.args = args if args is not None else []
    ctx.user_data = user_data if user_data is not None else {}
    return ctx


def _make_message_update(user_id: int, text: str = "", is_premium: bool = False):
    msg = MagicMock()
    msg.text = text
    msg.reply_text = AsyncMock()
    msg.photo = []
    msg.forward_origin = None
    msg.chat_shared = None
    upd = MagicMock()
    upd.effective_user = SimpleNamespace(
        id=user_id, first_name=f"User{user_id}", username=f"user{user_id}", is_premium=is_premium, language_code="ar"
    )
    upd.message = msg
    upd.callback_query = None
    return upd


def _make_callback_update(user_id: int, data: str, is_premium: bool = False):
    query = MagicMock()
    query.data = data
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.edit_message_caption = AsyncMock()
    query.edit_message_reply_markup = AsyncMock()
    query.delete_message = AsyncMock()
    query.message = MagicMock()
    query.message.caption = None
    query.message.reply_text = AsyncMock()

    upd = MagicMock()
    upd.effective_user = SimpleNamespace(
        id=user_id, first_name=f"User{user_id}", username=f"user{user_id}", is_premium=is_premium, language_code="ar"
    )
    upd.callback_query = query
    upd.message = None
    return upd


@pytest_asyncio.fixture
async def temp_db(tmp_path):
    db_file = tmp_path / "test_zetagram.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    eng = configure_db(db_url)
    await init_db()
    rate_limiter.reset()
    reset_gatekeeper_caches()
    yield db_file
    await eng.dispose()


@pytest.mark.asyncio
async def test_db_wal_migration_and_backup(tmp_path):
    legacy_db = tmp_path / "legacy.db"
    conn = sqlite3.connect(legacy_db)
    conn.execute(
        "CREATE TABLE users (telegram_id BIGINT PRIMARY KEY, username VARCHAR(64), first_name VARCHAR(64), balance INTEGER DEFAULT 0, language VARCHAR(8) DEFAULT 'ar', referred_by BIGINT, created_at DATETIME)"
    )
    conn.execute(
        "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(128), task_type VARCHAR(32), target_url VARCHAR(256), chat_id VARCHAR(64), reward_grams INTEGER, total_qty INTEGER, completed_qty INTEGER, description TEXT, status VARCHAR(16), created_by BIGINT, created_at DATETIME)"
    )
    conn.execute(
        "CREATE TABLE user_tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id BIGINT, task_id INTEGER, status VARCHAR(32), proof_file_id VARCHAR(256), completed_at DATETIME)"
    )
    conn.execute(
        "CREATE TABLE vouchers (id INTEGER PRIMARY KEY AUTOINCREMENT, code VARCHAR(64), amount INTEGER, max_uses INTEGER, used_count INTEGER, created_at DATETIME)"
    )
    conn.commit()
    conn.close()

    db_url = f"sqlite+aiosqlite:///{legacy_db.as_posix()}"
    eng = configure_db(db_url)
    await init_db()
    migrate_sqlite_columns(db_url)

    async with AsyncSessionLocal() as session:
        mode = (await session.execute(text("PRAGMA journal_mode;"))).scalar()
        assert str(mode).lower() == "wal"

    check_conn = sqlite3.connect(legacy_db)
    user_cols = {c[1] for c in check_conn.execute("PRAGMA table_info(users)").fetchall()}
    task_cols = {c[1] for c in check_conn.execute("PRAGMA table_info(tasks)").fetchall()}
    ut_cols = {c[1] for c in check_conn.execute("PRAGMA table_info(user_tasks)").fetchall()}
    check_conn.close()

    assert {"trust_score", "daily_streak", "tasks_since_captcha", "fee_free_until", "daily_quest_date"} <= user_cols
    assert {"escrow_balance", "target_languages", "requires_premium", "bot_username"} <= task_cols
    assert {"proof_file_unique_id", "proof_phash", "submitted_at", "reward_paid"} <= ut_cols

    backup_file = tmp_path / "backup_copy.db"
    assert create_safe_sqlite_backup(str(backup_file), db_url) is True
    assert backup_file.exists() and backup_file.stat().st_size > 0
    bconn = sqlite3.connect(backup_file)
    assert "users" in {r[0] for r in bconn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    bconn.close()
    await eng.dispose()


def test_captcha_and_image_hashing():
    buf, ans, opts, caption = generate_image_captcha("ar")
    assert ans in opts
    assert len(opts) == 4
    with Image.open(buf) as im:
        assert im.format == "PNG"
        assert im.size == (320, 120)

    png1 = _make_png_bytes((200, 100, 50), pattern=1)
    png1_copy = _make_png_bytes((202, 101, 51), pattern=1)
    png2 = _make_png_bytes((30, 40, 200), pattern=2)

    h1 = compute_dhash(png1)
    h1_copy = compute_dhash(png1_copy)
    h2 = compute_dhash(png2)

    assert len(h1) == 16
    assert is_similar_hash(h1, h1_copy, max_distance=6) is True
    assert is_similar_hash(h1, h2, max_distance=6) is False


@pytest.mark.asyncio
async def test_gatekeeper_blocks_banned_unverified_and_unsubbed_but_not_api_error(temp_db):
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                telegram_id=101,
                first_name="Banned",
                balance=5000,
                is_captcha_verified=True,
                banned_until=utcnow() + timedelta(days=1),
            )
        )
        session.add(
            User(
                telegram_id=102,
                first_name="NoCaptcha",
                balance=5000,
                is_captcha_verified=False,
            )
        )
        session.add(
            User(
                telegram_id=103,
                first_name="Verified",
                balance=1000,
                is_captcha_verified=True,
            )
        )
        session.add(
            MandatoryChannel(
                channel_username="@MustJoinCh",
                channel_link="https://t.me/MustJoinCh",
                title="MustJoin",
                is_active=True,
            )
        )
        await session.commit()

    bot = _make_mock_bot()

    # 1. Banned user blocked from bonus, spin, and transfer
    upd_ban = _make_message_update(101)
    ctx_ban = _make_context(bot, args=["103", "500"])
    await claim_daily_bonus(upd_ban, ctx_ban)
    rate_limiter.reset()
    await spin_wheel_command(upd_ban, ctx_ban)
    rate_limiter.reset()
    await handle_transfer_command(upd_ban, ctx_ban)

    async with AsyncSessionLocal() as session:
        u101 = (await session.execute(select(User).where(User.telegram_id == 101))).scalar_one()
        assert u101.balance == 5000

    # 2. Unverified captcha user redirected to image captcha
    upd_nocap = _make_message_update(102)
    ctx_nocap = _make_context(bot)
    await claim_daily_bonus(upd_nocap, ctx_nocap)
    assert bot.send_photo.await_count == 1

    # 3. Mandatory channel returning "left" blocks bonus
    bot.get_chat_member = AsyncMock(return_value=SimpleNamespace(status="left"))
    upd_unsub = _make_message_update(103)
    ctx_unsub = _make_context(bot)
    await claim_daily_bonus(upd_unsub, ctx_unsub)
    async with AsyncSessionLocal() as session:
        u103 = (await session.execute(select(User).where(User.telegram_id == 103))).scalar_one()
        assert u103.balance == 1000

    # 4. Mandatory channel returning TelegramError does NOT lock out user
    from telegram.error import TelegramError
    reset_gatekeeper_caches()
    rate_limiter.reset()
    bot.get_chat_member = AsyncMock(side_effect=TelegramError("Chat not found"))
    await claim_daily_bonus(upd_unsub, ctx_unsub)
    async with AsyncSessionLocal() as session:
        u103 = (await session.execute(select(User).where(User.telegram_id == 103))).scalar_one()
        assert u103.balance == 1100  # Daily bonus day 1 granted!


@pytest.mark.asyncio
async def test_anti_unsub_no_false_ban_and_penalizes_confirmed_leave(temp_db):
    async with AsyncSessionLocal() as session:
        session.add(User(telegram_id=201, first_name="Worker", balance=2000, is_captcha_verified=True, trust_score=100))
        task = Task(
            title="TestCh",
            task_type="channel",
            target_url="https://t.me/TestCh",
            chat_id="@TestCh",
            reward_grams=750,
            total_qty=5,
            completed_qty=5,
            status="completed",
            escrow_balance=0,
            created_by=999,
        )
        session.add(task)
        await session.flush()
        session.add(
            UserTask(
                user_id=201,
                task_id=task.id,
                status="completed",
                reward_paid=750,
                completed_at=utcnow() - timedelta(hours=2),
            )
        )
        await session.commit()
        tid = task.id

    from telegram.error import TelegramError
    bot = _make_mock_bot()

    # Case A: TelegramError -> MUST NOT penalize
    bot.get_chat_member = AsyncMock(side_effect=TelegramError("Forbidden: bot was kicked"))
    res_err = await check_unsubs_once(bot, sleep_between=0)
    assert res_err["penalized"] == 0
    assert res_err["errors"] == 1
    async with AsyncSessionLocal() as session:
        u = (await session.execute(select(User).where(User.telegram_id == 201))).scalar_one()
        assert u.balance == 2000
        assert u.violations_count == 0
        assert u.banned_until is None

    # Case B: Confirmed 'left' -> Penalize, deduct, drop trust_score, ban 24h, reopen task slot!
    bot.get_chat_member = AsyncMock(return_value=SimpleNamespace(status="left"))
    res_left = await check_unsubs_once(bot, sleep_between=0)
    assert res_left["penalized"] == 1
    async with AsyncSessionLocal() as session:
        u = (await session.execute(select(User).where(User.telegram_id == 201))).scalar_one()
        t = (await session.execute(select(Task).where(Task.id == tid))).scalar_one()
        ut = (await session.execute(select(UserTask).where(UserTask.user_id == 201))).scalar_one()
        tx = (await session.execute(select(Transaction).where(Transaction.user_id == 201))).scalar_one()
        assert u.balance == 1250
        assert u.violations_count == 1
        assert u.trust_score == 85
        assert u.banned_until is not None
        assert ut.unsubscribed is True
        assert t.completed_qty == 4
        assert t.status == "active"
        assert t.escrow_balance == 750
        assert tx.trans_type == "unsub_penalty" and tx.amount == -750


@pytest.mark.asyncio
async def test_race_conditions_voucher_milestone_and_task_cap(temp_db):
    async with AsyncSessionLocal() as session:
        for uid in range(301, 306):
            session.add(
                User(telegram_id=uid, first_name=f"U{uid}", balance=0, is_captcha_verified=True)
            )
        session.add(Voucher(code="GRAM-ONCE-0001", amount=500, max_uses=1, used_count=0, created_by=999))
        task = Task(
            title="Cap1",
            task_type="channel",
            target_url="https://t.me/Cap1",
            chat_id="@Cap1",
            reward_grams=750,
            total_qty=1,
            completed_qty=0,
            escrow_balance=750,
            status="active",
            created_by=999,
        )
        session.add(task)
        # Setup user 301 with 10 completed tasks on a dummy task for milestone race
        dummy_task = Task(
            title="Dummy",
            task_type="post",
            target_url="https://t.me/d/1",
            reward_grams=10,
            total_qty=100,
            completed_qty=10,
            status="active",
            created_by=999,
        )
        session.add(dummy_task)
        await session.commit()
        cap_tid = task.id
        dummy_tid = dummy_task.id

    async with AsyncSessionLocal() as session:
        # Insert 10 dummy completed tasks for 301? UniqueConstraint on (user_id, task_id) -> create 10 tasks
        for i in range(10):
            dt = Task(title=f"DT{i}", task_type="post", target_url="https://t.me/d/1", reward_grams=10, total_qty=5, status="active", created_by=999)
            session.add(dt)
            await session.flush()
            session.add(UserTask(user_id=301, task_id=dt.id, status="completed"))
        await session.commit()

    bot = _make_mock_bot()

    # 1. 5 concurrent voucher redemptions for max_uses=1
    await asyncio.gather(
        *[
            redeem_voucher(_make_message_update(uid), _make_context(bot), "GRAM-ONCE-0001")
            for uid in range(301, 306)
        ]
    )
    async with AsyncSessionLocal() as session:
        v = (await session.execute(select(Voucher).where(Voucher.code == "GRAM-ONCE-0001"))).scalar_one()
        reds = (await session.execute(select(VoucherRedemption))).scalars().all()
        assert v.used_count == 1
        assert len(reds) == 1

    # 2. 3 concurrent milestone claims for user 301 (+100g)
    rate_limiter.reset()
    ms_updates = [_make_callback_update(301, "claim_m_tasks_10") for _ in range(3)]
    await asyncio.gather(
        *[claim_milestone_callback(u, _make_context(bot)) for u in ms_updates]
    )
    assert sum(u.callback_query.edit_message_text.await_count for u in ms_updates) == 1
    async with AsyncSessionLocal() as session:
        u301 = (await session.execute(select(User).where(User.telegram_id == 301))).scalar_one()
        txs = (
            await session.execute(
                select(Transaction).where(Transaction.user_id == 301, Transaction.trans_type == "reward")
            )
        ).scalars().all()
        assert len(txs) == 1
        assert txs[0].amount == 100

    # 3. 5 concurrent check_task_callback calls on total_qty=1
    rate_limiter.reset()
    await asyncio.gather(
        *[
            check_task_callback(_make_callback_update(uid, f"check_task_{cap_tid}"), _make_context(bot))
            for uid in range(301, 306)
        ]
    )
    async with AsyncSessionLocal() as session:
        t = (await session.execute(select(Task).where(Task.id == cap_tid))).scalar_one()
        uts = (await session.execute(select(UserTask).where(UserTask.task_id == cap_tid))).scalars().all()
        assert t.completed_qty == 1
        assert t.status == "completed"
        assert len(uts) == 1


@pytest.mark.asyncio
async def test_economy_transfers_rewards_and_suspicious_alert(temp_db):
    now = utcnow()
    async with AsyncSessionLocal() as session:
        # Receiver + 3 new accounts (< 7 days old)
        session.add(User(telegram_id=400, first_name="Receiver", balance=0, is_captcha_verified=True, created_at=now - timedelta(days=30)))
        for uid in (401, 402, 403):
            session.add(
                User(
                    telegram_id=uid,
                    first_name=f"New{uid}",
                    balance=1000,
                    is_captcha_verified=True,
                    vip_level=2,  # VIP 2 skips min-tasks check for testing transfer rules
                    created_at=now - timedelta(days=1),
                )
            )
        # User 404 is VIP 1 with 0 tasks (blocked from transfer) & small transfer (<100)
        session.add(User(telegram_id=404, first_name="BrandNew", balance=1000, is_captcha_verified=True, vip_level=1))
        # User 405 is VIP 4 (0% fee) with 3 tasks
        session.add(User(telegram_id=405, first_name="Vip4", balance=1000, is_captcha_verified=True, vip_level=4))
        for i in range(3):
            t = Task(title=f"T{i}", task_type="post", target_url="https://t.me/a/1", reward_grams=10, total_qty=10, status="active", created_by=999)
            session.add(t)
            await session.flush()
            session.add(UserTask(user_id=405, task_id=t.id, status="completed"))
        await session.commit()

    bot = _make_mock_bot()

    # Transfer < 100 rejected
    upd = _make_message_update(405)
    await handle_transfer_command(upd, _make_context(bot, args=["400", "40"]))
    assert "❌" in upd.message.reply_text.call_args.args[0]

    # New VIP 1 with < 3 tasks rejected
    upd404 = _make_message_update(404)
    await handle_transfer_command(upd404, _make_context(bot, args=["400", "200"]))
    assert "3" in upd404.message.reply_text.call_args.args[0]

    # VIP 4 transfers 101g with 0 fee
    rate_limiter.reset()
    await handle_transfer_command(upd, _make_context(bot, args=["400", "101"]))
    async with AsyncSessionLocal() as session:
        u405 = (await session.execute(select(User).where(User.telegram_id == 405))).scalar_one()
        assert u405.balance == 899  # 1000 - 101 (0 fee)

    # 3 new accounts (<7 days old) transferring to 400 within 24h triggers alert
    for uid in (401, 402, 403):
        rate_limiter.reset()
        await handle_transfer_command(_make_message_update(uid), _make_context(bot, args=["400", "105"]))

    # Verify security alert was sent to admin
    assert any("حسابات وهمية" in str(c) for c in bot.send_message.await_args_list)


@pytest.mark.asyncio
async def test_award_task_completion_commission_milestone_quest_recaptcha(temp_db):
    async with AsyncSessionLocal() as session:
        session.add(User(telegram_id=500, first_name="Referrer", balance=0, is_captcha_verified=True))
        session.add(
            User(
                telegram_id=501,
                first_name="Worker",
                balance=0,
                referred_by=500,
                is_captcha_verified=True,
                vip_level=4,  # +10% task bonus
                tasks_since_captcha=config.RECAPTCHA_TASK_INTERVAL - 5,
            )
        )
        tasks = []
        for i in range(5):
            t = Task(
                title=f"Mission {i}",
                task_type="post",
                target_url="https://t.me/m/1",
                reward_grams=200,
                total_qty=10,
                completed_qty=0,
                escrow_balance=2000,
                status="active",
                created_by=999,
            )
            session.add(t)
            tasks.append(t)
        await session.commit()
        t_ids = [t.id for t in tasks]

    bot = _make_mock_bot()
    async with AsyncSessionLocal() as session:
        worker = (await session.execute(select(User).where(User.telegram_id == 501))).scalar_one()
        for idx, tid in enumerate(t_ids):
            task = (await session.execute(select(Task).where(Task.id == tid))).scalar_one()
            task.completed_qty += 1
            ut = UserTask(user_id=501, task_id=tid, status="completed")
            session.add(ut)
            info = await award_task_completion(session, bot, worker, task, ut)
            if idx == 2:
                assert info["referrer_milestone_id"] == 500
            if idx == 4:
                assert info["quest_completed"] is True
                assert info["recaptcha_triggered"] is True
        await session.commit()

    async with AsyncSessionLocal() as session:
        ref = (await session.execute(select(User).where(User.telegram_id == 500))).scalar_one()
        w = (await session.execute(select(User).where(User.telegram_id == 501))).scalar_one()
        # 5 tasks * 220 (200 + 10% VIP4) + 150 daily quest = 1250
        assert w.balance == 1250
        assert w.is_captcha_verified is False
        # 5 * 20 (10% of 200) + 250 milestone = 350
        assert ref.balance == 350


@pytest.mark.asyncio
async def test_proof_idor_duplicate_hash_auto_approve_and_campaign_refund(temp_db):
    async with AsyncSessionLocal() as session:
        session.add(User(telegram_id=601, first_name="Worker1", balance=0, is_captcha_verified=True))
        session.add(User(telegram_id=602, first_name="Attacker", balance=0, is_captcha_verified=True))
        session.add(User(telegram_id=603, first_name="Creator", balance=1000, is_captcha_verified=True))
        t = Task(
            title="ProofTask",
            task_type="reaction_random",
            target_url="https://t.me/x/1",
            reward_grams=300,
            total_qty=5,
            completed_qty=0,
            escrow_balance=1500,
            status="active",
            created_by=603,
        )
        session.add(t)
        await session.flush()
        ut_approved = UserTask(user_id=601, task_id=t.id, status="approved", proof_file_unique_id="uniq_1")
        session.add(ut_approved)

        t2 = Task(
            title="StaleProofTask",
            task_type="bot_normal",
            target_url="https://t.me/b",
            reward_grams=400,
            total_qty=5,
            completed_qty=0,
            escrow_balance=2000,
            status="active",
            created_by=603,
        )
        session.add(t2)
        await session.flush()
        ut_stale = UserTask(
            user_id=601,
            task_id=t2.id,
            status="pending_approval",
            submitted_at=utcnow() - timedelta(hours=30),
        )
        session.add(ut_stale)
        await session.commit()
        approved_ut_id = ut_approved.id
        t2_id = t2.id

    bot = _make_mock_bot()

    # 1. IDOR check: User 602 cannot resubmit proof belonging to User 601, nor User 601 on already approved task
    ctx_att = _make_context(bot)
    await handle_worker_dispute_callbacks(_make_callback_update(602, f"resubmit_proof_{approved_ut_id}"), ctx_att)
    assert "revision_ut_id" not in ctx_att.user_data

    ctx_own = _make_context(bot)
    await handle_worker_dispute_callbacks(_make_callback_update(601, f"resubmit_proof_{approved_ut_id}"), ctx_own)
    assert "revision_ut_id" not in ctx_own.user_data

    # 2. Duplicate screenshot rejected (same file_unique_id or dhash)
    rate_limiter.reset()
    png_bytes = _make_png_bytes((200, 100, 50), pattern=1)
    dl_mock = AsyncMock(return_value=bytearray(png_bytes))
    bot.get_file = AsyncMock(return_value=SimpleNamespace(download_as_bytearray=dl_mock))

    upd_photo = _make_message_update(601)
    upd_photo.message.photo = [SimpleNamespace(file_id="fid_dup", file_unique_id="uniq_1")]
    ctx_photo = _make_context(bot, user_data={"pending_task_id": t2_id})
    await process_proof_photo(upd_photo, ctx_photo)
    assert "مكررة" in upd_photo.message.reply_text.call_args.args[0] or "مطابقة" in upd_photo.message.reply_text.call_args.args[0]

    # 3. Auto-approve stale proof older than 24h
    approved_cnt = await auto_approve_pending_proofs_once(bot)
    assert approved_cnt == 1
    async with AsyncSessionLocal() as session:
        w = (await session.execute(select(User).where(User.telegram_id == 601))).scalar_one()
        assert w.balance == 400

    # 4. Campaign cancellation refunds remaining escrow_balance to creator
    rate_limiter.reset()
    await mytask_action_callback(_make_callback_update(603, f"mytask_cancel_{t2_id}"), _make_context(bot))
    async with AsyncSessionLocal() as session:
        creator = (await session.execute(select(User).where(User.telegram_id == 603))).scalar_one()
        t2_db = (await session.execute(select(Task).where(Task.id == t2_id))).scalar_one()
        assert t2_db.status == "cancelled"
        assert t2_db.escrow_balance == 0
        # 1000 initial + 1600 remaining escrow (2000 - 400 auto-approved)
        assert creator.balance == 2600


@pytest.mark.asyncio
async def test_post_timer_and_bot_forward_and_admin_guard(temp_db):
    async with AsyncSessionLocal() as session:
        session.add(User(telegram_id=701, first_name="W701", balance=0, is_captcha_verified=True))
        t_post = Task(title="PostT", task_type="post", target_url="https://t.me/p/1", reward_grams=150, total_qty=5, escrow_balance=750, status="active", created_by=999)
        t_bot = Task(title="BotT", task_type="bot_normal", target_url="https://t.me/SomeTestBot", bot_username="@SomeTestBot", reward_grams=250, total_qty=5, escrow_balance=1250, status="active", created_by=999)
        session.add_all([t_post, t_bot])
        await session.commit()
        pid, bid = t_post.id, t_bot.id

    bot = _make_mock_bot()
    ctx = _make_context(bot)

    # Post timer: start then claim after simulated elapsed time
    await start_post_callback(_make_callback_update(701, f"start_post_{pid}"), ctx)
    assert f"post_timer_{pid}" in ctx.user_data
    ctx.user_data[f"post_timer_{pid}"] = time.time() - (config.MIN_POST_VIEW_SECONDS + 1)
    rate_limiter.reset()
    await claim_post_callback(_make_callback_update(701, f"claim_post_{pid}"), ctx)

    # Bot forward auto-verification
    from telegram import MessageOriginUser
    ctx.user_data["awaiting_bot_forward_task_id"] = bid
    upd_fwd = _make_message_update(701)
    bot_sender = MagicMock()
    bot_sender.is_bot = True
    bot_sender.username = "SomeTestBot"
    upd_fwd.message.forward_origin = MessageOriginUser(
        date=datetime.now(timezone.utc), sender_user=bot_sender
    )
    rate_limiter.reset()
    handled = await handle_bot_forward_message(upd_fwd, ctx)
    assert handled is True

    async with AsyncSessionLocal() as session:
        w = (await session.execute(select(User).where(User.telegram_id == 701))).scalar_one()
        assert w.balance == 400

    # Non-admin blocked from prompt_add_mandatory_channel
    ctx_nonadmin = _make_context(bot)
    await prompt_add_mandatory_channel(_make_callback_update(701, "add_mand_chan_prompt"), ctx_nonadmin)
    assert "awaiting_mand_chan" not in ctx_nonadmin.user_data


@pytest.mark.asyncio
async def test_regressions_pagination_daily_report_and_retention(temp_db):
    now = utcnow()
    yesterday = now - timedelta(hours=12)
    yesterday_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    y_noon = yesterday_start + timedelta(hours=12)

    async with AsyncSessionLocal() as session:
        # User created yesterday + inactive user (30h ago)
        session.add(User(telegram_id=801, first_name="YestUser", is_captcha_verified=True, created_at=y_noon, last_active_at=now))
        session.add(User(telegram_id=802, first_name="IdleUser", is_captcha_verified=True, created_at=now - timedelta(days=5), last_active_at=now - timedelta(hours=30), notifications_enabled=True))
        t = Task(title="BotNorm", task_type="bot_normal", target_url="https://t.me/b", reward_grams=100, total_qty=5, status="active", created_by=999)
        session.add(t)
        await session.flush()
        session.add(UserTask(user_id=801, task_id=t.id, status="completed", completed_at=y_noon))
        session.add(Transaction(user_id=801, trans_type="earn_task", amount=100, created_at=y_noon))
        await session.commit()

    bot = _make_mock_bot()

    # 1. Pagination for underscore category (bot_normal)
    await bot_main.handle_callbacks(_make_callback_update(801, "page_bot_normal_2"), _make_context(bot))
    await bot_main.handle_callbacks(_make_callback_update(801, "page_reaction_fixed_3"), _make_context(bot))

    # 2. Daily report queries yesterday window (not empty today)
    rep = await compile_and_send_daily_report_once(bot, now=now)
    assert "<code>1</code>" in rep
    assert "<code>100</code>" in rep

    # 3. Retention reminders run once per inactivity window
    sent1 = await run_retention_reminders_once(bot)
    sent2 = await run_retention_reminders_once(bot)
    assert sent1 == 1
    assert sent2 == 0


@pytest.mark.asyncio
async def test_weekly_leaderboard_payout_and_idempotency(temp_db):
    now = utcnow()
    this_monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    last_wed = this_monday - timedelta(days=5)

    async with AsyncSessionLocal() as session:
        session.add(User(telegram_id=901, first_name="Champ", balance=0, is_captcha_verified=True, created_at=last_wed - timedelta(days=10)))
        session.add(User(telegram_id=902, first_name="Invitee", balance=0, referred_by=901, is_captcha_verified=True, created_at=last_wed))
        t = Task(title="WTask", task_type="post", target_url="https://t.me/w/1", reward_grams=50, total_qty=10, status="active", created_by=999)
        session.add(t)
        await session.flush()
        session.add(UserTask(user_id=901, task_id=t.id, status="completed", completed_at=last_wed))
        await session.commit()

    bot = _make_mock_bot()
    res1 = await distribute_weekly_leaderboard_once(bot, now=now)
    res2 = await distribute_weekly_leaderboard_once(bot, now=now)
    assert res1 is not None and len(res1["awarded"]) == 2
    assert res2 is None  # Idempotent: does not double-pay same week

    async with AsyncSessionLocal() as session:
        u901 = (await session.execute(select(User).where(User.telegram_id == 901))).scalar_one()
        # Rank #1 in tasks (+1500) + Rank #1 in referrals (+1500) = 3000
        assert u901.balance == 3000


def _collect_main_callback_routes(main_path: str):
    with open(main_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=main_path)

    exact_routes = set()
    prefix_routes = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "handle_callbacks":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Compare):
                    if isinstance(sub.left, ast.Name) and sub.left.id == "data":
                        for op, comp in zip(sub.ops, sub.comparators):
                            if isinstance(op, ast.Eq) and isinstance(comp, ast.Constant) and isinstance(comp.value, str):
                                exact_routes.add(comp.value)
                            elif isinstance(op, ast.In) and isinstance(comp, (ast.Tuple, ast.List, ast.Set)):
                                for elt in comp.elts:
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                        exact_routes.add(elt.value)
                elif isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                    if (
                        sub.func.attr == "startswith"
                        and isinstance(sub.func.value, ast.Name)
                        and sub.func.value.id == "data"
                        and sub.args
                    ):
                        arg0 = sub.args[0]
                        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                            prefix_routes.add(arg0.value)
                        elif isinstance(arg0, (ast.Tuple, ast.List)):
                            for elt in arg0.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    prefix_routes.add(elt.value)
    return exact_routes, prefix_routes


def test_static_compile_and_no_dead_callbacks():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_files = []
    for folder in ("database", "handlers", "utils"):
        fpath = os.path.join(root, folder)
        for fn in os.listdir(fpath):
            if fn.endswith(".py"):
                py_files.append(os.path.join(fpath, fn))
    py_files.extend([os.path.join(root, "config.py"), os.path.join(root, "main.py")])

    for pf in py_files:
        py_compile.compile(pf, doraise=True)

    emitted = set()
    cb_pattern = re.compile(r'callback_data\s*=\s*f?["\']([^"\']+)["\']')
    for pf in py_files:
        with open(pf, "r", encoding="utf-8") as f:
            src = f.read()
        for match in cb_pattern.findall(src):
            clean = match.split("{", 1)[0]
            emitted.add(clean)

    exact_routes, prefix_routes = _collect_main_callback_routes(os.path.join(root, "main.py"))

    unmatched = []
    for cb in sorted(emitted):
        if cb in ("tasks_",):
            continue
        if cb in exact_routes:
            continue
        if any(cb.startswith(pref) or pref.startswith(cb) for pref in prefix_routes):
            continue
        unmatched.append(cb)

    assert not unmatched, f"Unrouted callback_data prefixes found: {unmatched}"
