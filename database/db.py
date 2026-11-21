import os
import sqlite3
import logging
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from database.models import Base
from config import DB_URL

_current_db_url = DB_URL


def get_sqlite_db_path(db_url: str | None = None) -> str | None:
    """Parse SQLite file path from a SQLAlchemy URL; return None for :memory: or non-SQLite."""
    url = db_url or _current_db_url
    if not url or not url.startswith("sqlite"):
        return None
    for prefix in ("sqlite+aiosqlite:///", "sqlite:///"):
        if url.startswith(prefix):
            path = url[len(prefix):].split("?", 1)[0]
            if not path or path == ":memory:" or path.startswith("file::memory:"):
                return None
            return path
    return None


def _attach_sqlite_pragmas(async_engine):
    if not str(async_engine.url).startswith("sqlite"):
        return

    @event.listens_for(async_engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA busy_timeout=5000;")
        finally:
            cursor.close()


engine = create_async_engine(DB_URL, echo=False)
_attach_sqlite_pragmas(engine)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def configure_db(db_url: str):
    """Reconfigure engine and AsyncSessionLocal (useful for isolated tests)."""
    global engine, _current_db_url
    _current_db_url = db_url
    new_engine = create_async_engine(db_url, echo=False)
    _attach_sqlite_pragmas(new_engine)
    engine = new_engine
    AsyncSessionLocal.configure(bind=new_engine)
    return new_engine


def migrate_sqlite_columns(db_url: str | None = None):
    """Ensure all new columns and indexes exist in an existing SQLite database."""
    db_path = get_sqlite_db_path(db_url)
    if not db_path or not os.path.exists(db_path):
        return

    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()

        def add_missing(table: str, cols: dict):
            existing = {c[1] for c in cursor.execute(f"PRAGMA table_info({table})").fetchall()}
            for col_name, col_sql in cols.items():
                if col_name not in existing:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_sql}")

        add_missing("users", {
            "is_captcha_verified": "is_captcha_verified BOOLEAN DEFAULT 0",
            "last_daily_bonus": "last_daily_bonus DATETIME",
            "last_spin_time": "last_spin_time DATETIME",
            "violations_count": "violations_count INTEGER DEFAULT 0",
            "banned_until": "banned_until DATETIME",
            "vip_level": "vip_level INTEGER DEFAULT 1",
            "claimed_milestones": "claimed_milestones VARCHAR(256) DEFAULT ''",
            "last_active_at": "last_active_at DATETIME",
            "failed_voucher_attempts": "failed_voucher_attempts INTEGER DEFAULT 0",
            "voucher_banned_until": "voucher_banned_until DATETIME",
            "trust_score": "trust_score INTEGER DEFAULT 100",
            "daily_streak": "daily_streak INTEGER DEFAULT 0",
            "tasks_since_captcha": "tasks_since_captcha INTEGER DEFAULT 0",
            "notifications_enabled": "notifications_enabled BOOLEAN DEFAULT 1",
            "last_reminded_at": "last_reminded_at DATETIME",
            "fee_free_until": "fee_free_until DATETIME",
            "captcha_attempts": "captcha_attempts INTEGER DEFAULT 0",
            "captcha_locked_until": "captcha_locked_until DATETIME",
            "referred_bonus_paid": "referred_bonus_paid BOOLEAN DEFAULT 0",
            "join_bonus_paid": "join_bonus_paid BOOLEAN DEFAULT 0",
            "daily_quest_date": "daily_quest_date VARCHAR(16)",
        })

        add_missing("tasks", {
            "target_languages": "target_languages VARCHAR(256)",
            "requires_premium": "requires_premium BOOLEAN DEFAULT 0",
            "escrow_balance": "escrow_balance INTEGER DEFAULT 0",
            "commission_paid": "commission_paid INTEGER DEFAULT 0",
            "bot_username": "bot_username VARCHAR(64)",
            "required_emoji": "required_emoji VARCHAR(32)",
            "target_message_id": "target_message_id BIGINT",
            "auto_verify_reactions": "auto_verify_reactions BOOLEAN DEFAULT 0",
            "promo_code_used": "promo_code_used VARCHAR(64)",
            "promo_subsidy": "promo_subsidy INTEGER DEFAULT 0",
        })

        add_missing("user_tasks", {
            "unsubscribed": "unsubscribed BOOLEAN DEFAULT 0",
            "rejection_reason": "rejection_reason TEXT",
            "proof_file_unique_id": "proof_file_unique_id VARCHAR(128)",
            "proof_phash": "proof_phash VARCHAR(64)",
            "submitted_at": "submitted_at DATETIME",
            "reward_paid": "reward_paid INTEGER DEFAULT 0",
        })

        add_missing("vouchers", {
            "created_by": "created_by BIGINT",
        })

        regular_indexes = [
            "CREATE INDEX IF NOT EXISTS ix_users_referred_by ON users(referred_by)",
            "CREATE INDEX IF NOT EXISTS ix_users_last_active_at ON users(last_active_at)",
            "CREATE INDEX IF NOT EXISTS ix_users_banned_until ON users(banned_until)",
            "CREATE INDEX IF NOT EXISTS ix_tasks_type_status ON tasks(task_type, status)",
            "CREATE INDEX IF NOT EXISTS ix_tasks_created_by ON tasks(created_by)",
            "CREATE INDEX IF NOT EXISTS ix_tasks_chat_msg ON tasks(chat_id, target_message_id)",
            "CREATE INDEX IF NOT EXISTS ix_ut_user_status ON user_tasks(user_id, status)",
            "CREATE INDEX IF NOT EXISTS ix_ut_task_status ON user_tasks(task_id, status)",
            "CREATE INDEX IF NOT EXISTS ix_user_tasks_proof_file_unique_id ON user_tasks(proof_file_unique_id)",
            "CREATE INDEX IF NOT EXISTS ix_user_tasks_proof_phash ON user_tasks(proof_phash)",
            "CREATE INDEX IF NOT EXISTS ix_tx_user_created ON transactions(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS ix_tx_type_created ON transactions(trans_type, created_at)",
            "CREATE INDEX IF NOT EXISTS ix_dispute_status ON dispute_tickets(status)",
            "CREATE INDEX IF NOT EXISTS ix_task_reports_status ON task_reports(status)",
            "CREATE INDEX IF NOT EXISTS ix_flash_events_active_window ON flash_events(is_active, starts_at, ends_at)",
        ]
        for idx_sql in regular_indexes:
            try:
                cursor.execute(idx_sql)
            except Exception as e:
                logging.debug("Index note (%s): %s", idx_sql, e)

        unique_indexes = [
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_task ON user_tasks(user_id, task_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_voucher_redemption ON voucher_redemptions(voucher_id, user_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_dispute_ut ON dispute_tickets(user_task_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_promo_redemption ON promo_code_redemptions(promo_code_id, user_id)",
        ]
        for uidx_sql in unique_indexes:
            try:
                cursor.execute(uidx_sql)
            except Exception as e:
                logging.warning("Unique index skipped due to legacy duplicates (%s): %s", uidx_sql, e)

        conn.commit()
    except Exception as e:
        logging.warning("Migration note: %s", e)
    finally:
        if conn is not None:
            conn.close()


def create_safe_sqlite_backup(dest_path: str, db_url: str | None = None) -> bool:
    """Create an atomic, WAL-safe SQLite backup copy using sqlite3.Connection.backup()."""
    src_path = get_sqlite_db_path(db_url)
    if not src_path or not os.path.exists(src_path):
        return False

    src_conn = None
    dst_conn = None
    try:
        src_conn = sqlite3.connect(src_path, timeout=5.0)
        dst_conn = sqlite3.connect(dest_path)
        src_conn.backup(dst_conn)
        return True
    except Exception as e:
        logging.error("SQLite safe backup failed: %s", e)
        return False
    finally:
        if dst_conn is not None:
            dst_conn.close()
        if src_conn is not None:
            src_conn.close()


async def init_db():
    sqlite_path = get_sqlite_db_path(_current_db_url)
    if sqlite_path:
        db_dir = os.path.dirname(sqlite_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    migrate_sqlite_columns(_current_db_url)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
