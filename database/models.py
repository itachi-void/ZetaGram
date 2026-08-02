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
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    completed_tasks = relationship("UserTask", back_populates="user")




class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)
    # Types: 'channel', 'group', 'post', 'bot_normal', 'bot_webapp', 'bot_conditions'
    task_type = Column(String(32), nullable=False)
    target_url = Column(String(256), nullable=False)
    chat_id = Column(String(64), nullable=True) # Channel/Group handle or numeric ID for getChatMember
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
    # Status: 'completed', 'pending_proof', 'rejected'
    status = Column(String(32), default="completed")
    unsubscribed = Column(Boolean, default=False)
    proof_file_id = Column(String(256), nullable=True)
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
    created_at = Column(DateTime, default=datetime.utcnow)

class VoucherRedemption(Base):
    __tablename__ = "voucher_redemptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    redeemed_at = Column(DateTime, default=datetime.utcnow)
