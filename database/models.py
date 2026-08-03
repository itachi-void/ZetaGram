from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

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
    last_active_at = Column(DateTime, default=datetime.utcnow)
    failed_voucher_attempts = Column(Integer, default=0)
    voucher_banned_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    completed_tasks = relationship("UserTask", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)
    # Types: 'channel', 'group', 'post', 'bot_normal', 'bot_webapp', 'bot_conditions', 'reaction_random', 'reaction_fixed'
    task_type = Column(String(32), nullable=False)
    target_url = Column(String(256), nullable=False)
    chat_id = Column(String(64), nullable=True) # Channel/Group handle or numeric ID
    reward_grams = Column(Integer, nullable=False)
    total_qty = Column(Integer, nullable=False, default=100)
    completed_qty = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
    status = Column(String(16), default="active") # active, completed, paused
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("UserTask", back_populates="task")

class UserTask(Base):
    __tablename__ = "user_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    # Status: 'completed', 'pending_approval', 'approved', 'rejected', 'revision_requested', 'disputed'
    status = Column(String(32), default="completed")
    unsubscribed = Column(Boolean, default=False)
    proof_file_id = Column(String(256), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="completed_tasks")
    task = relationship("Task", back_populates="submissions")

class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    amount = Column(Integer, nullable=False)
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class VoucherRedemption(Base):
    __tablename__ = "voucher_redemptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    redeemed_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    # Types: 'earn_task', 'spend_promo', 'voucher_claim', 'voucher_create', 'transfer_send', 'transfer_receive', 'daily_bonus', 'spin', 'admin_adjust', 'reward', 'vault_deposit', 'vault_withdraw', 'raffle_buy', 'raffle_win'
    trans_type = Column(String(32), nullable=False)
    amount = Column(Integer, nullable=False)
    description = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")

class MandatoryChannel(Base):
    __tablename__ = "mandatory_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_username = Column(String(128), nullable=False)
    channel_link = Column(String(256), nullable=False)
    title = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DisputeTicket(Base):
    __tablename__ = "dispute_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_task_id = Column(Integer, ForeignKey("user_tasks.id"), nullable=False)
    reason = Column(Text, nullable=True)
    proof_file_id = Column(String(256), nullable=True)
    # Status: 'open', 'resolved_worker_paid', 'resolved_rejected'
    status = Column(String(32), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)

class VaultDeposit(Base):
    __tablename__ = "vault_deposits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    amount = Column(Integer, nullable=False)
    yield_amount = Column(Integer, nullable=False)
    duration_days = Column(Integer, nullable=False) # 7 or 30
    lock_until = Column(DateTime, nullable=False)
    # Status: 'active', 'withdrawn'
    status = Column(String(16), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class RaffleTicket(Base):
    __tablename__ = "raffle_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    ticket_code = Column(String(64), nullable=False)
    draw_id = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class RaffleDraw(Base):
    __tablename__ = "raffle_draws"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prize_pool = Column(Integer, default=0)
    winner_user_id = Column(BigInteger, nullable=True)
    winner_ticket_code = Column(String(64), nullable=True)
    status = Column(String(16), default="active") # 'active', 'completed'
    created_at = Column(DateTime, default=datetime.utcnow)
    drawn_at = Column(DateTime, nullable=True)
