import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database.models import Base
from config import DB_URL

engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def migrate_sqlite_columns():
    """Ensure all new columns exist in existing SQLite database tables."""
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        
        # User columns
        existing_user_cols = [c[1] for c in cursor.execute("PRAGMA table_info(users)").fetchall()]
        cols_to_add_users = {
            "is_captcha_verified": "is_captcha_verified BOOLEAN DEFAULT 0",
            "last_daily_bonus": "last_daily_bonus DATETIME",
            "violations_count": "violations_count INTEGER DEFAULT 0",
            "banned_until": "banned_until DATETIME",
            "vip_level": "vip_level INTEGER DEFAULT 1",
            "claimed_milestones": "claimed_milestones VARCHAR(256) DEFAULT ''",
            "last_active_at": "last_active_at DATETIME",
            "failed_voucher_attempts": "failed_voucher_attempts INTEGER DEFAULT 0",
            "voucher_banned_until": "voucher_banned_until DATETIME"
        }
        for col_name, col_sql in cols_to_add_users.items():
            if col_name not in existing_user_cols:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_sql}")
                
        # UserTask columns
        existing_ut_cols = [c[1] for c in cursor.execute("PRAGMA table_info(user_tasks)").fetchall()]
        if "unsubscribed" not in existing_ut_cols:
            cursor.execute("ALTER TABLE user_tasks ADD COLUMN unsubscribed BOOLEAN DEFAULT 0")
        if "rejection_reason" not in existing_ut_cols:
            cursor.execute("ALTER TABLE user_tasks ADD COLUMN rejection_reason TEXT")

        # Voucher columns
        existing_v_cols = [c[1] for c in cursor.execute("PRAGMA table_info(vouchers)").fetchall()]
        if "created_by" not in existing_v_cols:
            cursor.execute("ALTER TABLE vouchers ADD COLUMN created_by BIGINT")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration note: {e}")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    migrate_sqlite_columns()

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
