from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, ForeignKey, Boolean,
    UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship
from utils.html_utils import utcnow

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_referred_by", "referred_by"),
        Index("ix_users_last_active_at", "last_active_at"),
        Index("ix_users_banned_until", "banned_until"),
    )

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(64), nullable=True)
    first_name = Column(String(64), nullable=True)
    balance = Column(Integer, default=0)
    language = Column(String(8), default="ar")
    referred_by = Column(BigInteger, nullable=True)
    is_captcha_verified = Column(Boolean, default=False)
    last_daily_bonus = Column(DateTime, nullable=True)
    last_spin_time = Column(DateTime, nullable=True)
    violations_count = Column(Integer, default=0)
    banned_until = Column(DateTime, nullable=True)
    vip_level = Column(Integer, default=1)
    claimed_milestones = Column(String(256), default="")
    last_active_at = Column(DateTime, default=utcnow)
    failed_voucher_attempts = Column(Integer, default=0)
    voucher_banned_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    # New security, verification & retention columns
    trust_score = Column(Integer, default=100)
    daily_streak = Column(Integer, default=0)
    tasks_since_captcha = Column(Integer, default=0)
    notifications_enabled = Column(Boolean, default=True)
    last_reminded_at = Column(DateTime, nullable=True)
    fee_free_until = Column(DateTime, nullable=True)
    captcha_attempts = Column(Integer, default=0)
    captcha_locked_until = Column(DateTime, nullable=True)
    referred_bonus_paid = Column(Boolean, default=False)
    join_bonus_paid = Column(Boolean, default=False)
    daily_quest_date = Column(String(16), nullable=True)

    # Relationships
    completed_tasks = relationship("UserTask", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_type_status", "task_type", "status"),
        Index("ix_tasks_created_by", "created_by"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)
    # Types: 'channel', 'group', 'post', 'bot_normal', 'bot_webapp', 'bot_conditions', 'reaction_random', 'reaction_fixed', 'premium'
    task_type = Column(String(32), nullable=False)
    target_url = Column(String(256), nullable=False)
    chat_id = Column(String(64), nullable=True)
    reward_grams = Column(Integer, nullable=False)
    total_qty = Column(Integer, nullable=False, default=100)
    completed_qty = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
    status = Column(String(16), default="active")  # active, completed, paused
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    # Targeting, escrow & auto-verification columns
    target_languages = Column(String(256), nullable=True)
    requires_premium = Column(Boolean, default=False)
    escrow_balance = Column(Integer, default=0)
    commission_paid = Column(Integer, default=0)
    bot_username = Column(String(64), nullable=True)
    required_emoji = Column(String(32), nullable=True)

    submissions = relationship("UserTask", back_populates="task")


class UserTask(Base):
    __tablename__ = "user_tasks"
    __table_args__ = (
        UniqueConstraint("user_id", "task_id", name="uq_user_task"),
        Index("ix_ut_user_status", "user_id", "status"),
        Index("ix_ut_task_status", "task_id", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    # Status: 'completed', 'pending_approval', 'approved', 'rejected', 'revision_requested', 'disputed'
    status = Column(String(32), default="completed")
    unsubscribed = Column(Boolean, default=False)
    proof_file_id = Column(String(256), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    completed_at = Column(DateTime, default=utcnow)

    # Proof verification & payout audit columns
    proof_file_unique_id = Column(String(128), nullable=True, index=True)
    proof_phash = Column(String(64), nullable=True, index=True)
    submitted_at = Column(DateTime, nullable=True)
    reward_paid = Column(Integer, default=0)

    user = relationship("User", back_populates="completed_tasks")
    task = relationship("Task", back_populates="submissions")


class SkippedTask(Base):
    __tablename__ = "skipped_tasks"
    __table_args__ = (
        UniqueConstraint("user_id", "task_id", name="uq_skipped_task"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)


class TaskReport(Base):
    __tablename__ = "task_reports"
    __table_args__ = (
        Index("ix_task_reports_status", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(32), default="open")  # open, resolved, dismissed
    created_at = Column(DateTime, default=utcnow)


class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    amount = Column(Integer, nullable=False)
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class VoucherRedemption(Base):
    __tablename__ = "voucher_redemptions"
    __table_args__ = (
        UniqueConstraint("voucher_id", "user_id", name="uq_voucher_redemption"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    redeemed_at = Column(DateTime, default=utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_tx_user_created", "user_id", "created_at"),
        Index("ix_tx_type_created", "trans_type", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    trans_type = Column(String(32), nullable=False)
    amount = Column(Integer, nullable=False)
    description = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="transactions")


class MandatoryChannel(Base):
    __tablename__ = "mandatory_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_username = Column(String(128), nullable=False)
    channel_link = Column(String(256), nullable=False)
    title = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class DisputeTicket(Base):
    __tablename__ = "dispute_tickets"
    __table_args__ = (
        UniqueConstraint("user_task_id", name="uq_dispute_ut"),
        Index("ix_dispute_status", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_task_id = Column(Integer, ForeignKey("user_tasks.id"), nullable=False)
    reason = Column(Text, nullable=True)
    proof_file_id = Column(String(256), nullable=True)
    # Status: 'open', 'resolved_worker_paid', 'resolved_rejected'
    status = Column(String(32), default="open")
    created_at = Column(DateTime, default=utcnow)


class VaultDeposit(Base):
    __tablename__ = "vault_deposits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    amount = Column(Integer, nullable=False)
    yield_amount = Column(Integer, nullable=False)
    duration_days = Column(Integer, nullable=False)  # 7 or 30
    lock_until = Column(DateTime, nullable=False)
    status = Column(String(16), default="active")
    created_at = Column(DateTime, default=utcnow)


class RaffleTicket(Base):
    __tablename__ = "raffle_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    ticket_code = Column(String(64), nullable=False)
    draw_id = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=utcnow)


class RaffleDraw(Base):
    __tablename__ = "raffle_draws"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prize_pool = Column(Integer, default=0)
    winner_user_id = Column(BigInteger, nullable=True)
    winner_ticket_code = Column(String(64), nullable=True)
    status = Column(String(16), default="active")
    created_at = Column(DateTime, default=utcnow)
    drawn_at = Column(DateTime, nullable=True)


class WeeklyLeaderboardRun(Base):
    __tablename__ = "weekly_leaderboard_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_key = Column(String(16), unique=True, nullable=False)
    created_at = Column(DateTime, default=utcnow)
