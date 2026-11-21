import time
import random
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Tuple, Dict, Union
from sqlalchemy import select, func, and_

from config import ADMIN_IDS, VIP_PERKS
from utils.i18n import get_text
from utils.html_utils import esc, utcnow


class RateLimiter:
    """Per-user sliding cooldown rate limiter with bounded memory pruning."""

    def __init__(self, cooldown_seconds: float = 1.0, max_entries: int = 5000):
        self.cooldown = cooldown_seconds
        self.max_entries = max_entries
        self.user_timestamps: Dict[int, float] = {}

    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        if len(self.user_timestamps) > self.max_entries:
            cutoff = now - max(self.cooldown * 10, 60.0)
            self.user_timestamps = {
                uid: ts for uid, ts in self.user_timestamps.items() if ts >= cutoff
            }
        last_time = self.user_timestamps.get(user_id, 0.0)
        if now - last_time < self.cooldown:
            return False
        self.user_timestamps[user_id] = now
        return True

    def reset(self):
        """Clear tracked timestamps (useful in tests)."""
        self.user_timestamps.clear()


rate_limiter = RateLimiter(cooldown_seconds=1.0)


class UserLockManager:
    """
    Manages per-resource asyncio Locks (int user_id, tuple, or str resource keys)
    to prevent race conditions and double-spending exploits.
    """

    def __init__(self, max_entries: int = 5000):
        self.max_entries = max_entries
        self._locks: Dict[str, asyncio.Lock] = {}

    @staticmethod
    def _normalize_key(key: Union[int, str, tuple]) -> str:
        if isinstance(key, int):
            return f"user:{key}"
        if isinstance(key, tuple) and len(key) == 2:
            return f"{key[0]}:{key[1]}"
        if isinstance(key, str) and key.startswith("u_") and key[2:].lstrip("-").isdigit():
            return f"user:{key[2:]}"
        return str(key)

    def get_lock(self, key: Union[int, str, tuple]) -> asyncio.Lock:
        norm = self._normalize_key(key)
        if len(self._locks) > self.max_entries:
            for k in [k for k, lk in self._locks.items() if not lk.locked()]:
                self._locks.pop(k, None)
                if len(self._locks) <= self.max_entries // 2:
                    break
        if norm not in self._locks:
            self._locks[norm] = asyncio.Lock()
        return self._locks[norm]

    @asynccontextmanager
    async def acquire_ordered_locks(self, *keys: Union[int, str, tuple]):
        """Acquire multiple locks in deterministic sorted order to prevent deadlocks."""
        unique_sorted = sorted({self._normalize_key(k) for k in keys})
        acquired = []
        try:
            for k in unique_sorted:
                lock = self.get_lock(k)
                await lock.acquire()
                acquired.append(lock)
            yield
        finally:
            for lock in reversed(acquired):
                lock.release()


user_lock_manager = UserLockManager()

_alert_timestamps: Dict[str, float] = {}


async def send_security_alert(
    bot, message: str, alert_key: str | None = None, cooldown: float = 60.0
):
    """Send throttled HTML security alert to all ADMIN_IDS."""
    if not bot:
        return
    now = time.time()
    key = alert_key or str(hash(message))
    if len(_alert_timestamps) > 2000:
        _alert_timestamps.clear()
    last_sent = _alert_timestamps.get(key, 0.0)
    if cooldown > 0 and (now - last_sent) < cooldown:
        return
    _alert_timestamps[key] = now

    full_msg = f"🚨 <b>تنبيه أمني عاجل من البوت:</b>\n\n{message}"
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=full_msg, parse_mode="HTML")
        except Exception as e:
            logging.debug("Failed to send security alert to %s: %s", admin_id, e)


def is_admin_user(user_id: int, bot=None, command_name: str = "") -> bool:
    """Strictly check if user_id is in ADMIN_IDS and alert admins (throttled) on unauthorized attempts."""
    if user_id in ADMIN_IDS:
        return True

    if bot and command_name:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                send_security_alert(
                    bot,
                    f"⚠️ محاولة تسلل غير مصرح بها للوحة الأدمن!\n"
                    f"👤 المستخدم: <code>{esc(user_id)}</code>\n"
                    f"📌 الأمر المحاول: <code>{esc(command_name)}</code>",
                    alert_key=f"unauth_{user_id}_{command_name}",
                    cooldown=60.0,
                )
            )
        except RuntimeError:
            pass
    return False


def get_vip_perks(vip_level: int | None) -> dict:
    """Return VIP perks dictionary for the given level (default level 1)."""
    return VIP_PERKS.get(vip_level or 1, VIP_PERKS[1])


async def detect_suspicious_transfer(
    session, sender_id: int, receiver_id: int, amount: int, bot
) -> bool:
    """
    Detect potential multi-account farming: >= 3 distinct newly created accounts
    (< 7 days old) transferring funds to the same receiver within 24 hours.
    """
    from database.models import User, Transaction

    now = utcnow()
    t_24h = now - timedelta(hours=24)
    t_7d = now - timedelta(days=7)

    # Check transactions received by receiver_id in the last 24h
    txs = (
        await session.execute(
            select(Transaction.description).where(
                and_(
                    Transaction.user_id == receiver_id,
                    Transaction.trans_type == "transfer_receive",
                    Transaction.created_at >= t_24h,
                )
            )
        )
    ).scalars().all()

    recent_sender_ids = set()
    for desc in txs:
        if desc:
            for token in desc.split():
                if token.isdigit():
                    recent_sender_ids.add(int(token))

    recent_sender_ids.add(sender_id)
    if len(recent_sender_ids) < 3:
        return False

    new_senders_count = (
        await session.execute(
            select(func.count(User.telegram_id)).where(
                and_(
                    User.telegram_id.in_(list(recent_sender_ids)),
                    User.created_at >= t_7d,
                )
            )
        )
    ).scalar() or 0

    if new_senders_count >= 3:
        await send_security_alert(
            bot,
            f"⚠️ <b>اشتباه تجميع حسابات وهمية (Multi-Account Farming)!</b>\n"
            f"👤 المستلم: <code>{esc(receiver_id)}</code>\n"
            f"📥 استلم تحويلات من <b>{new_senders_count}</b> حسابات حديثة خلال 24 ساعة (آخر تحويل: <code>{amount:,}</code> غرام).",
            alert_key=f"suspicious_rx_{receiver_id}",
            cooldown=300.0,
        )
        return True
    return False


def sanitize_amount(
    val: str, min_val: int = 1, max_val: int = 1_000_000_000, lang: str = "ar"
) -> Tuple[bool, int, str]:
    """
    Sanitize integer amounts to prevent negative values, zero, or overflow attacks.
    Returns: (is_valid, parsed_int, error_message)
    """
    try:
        val_clean = str(val).strip()
        num = int(val_clean)
        if num < min_val:
            return False, 0, get_text(lang, "err_amount_min", min_val=min_val)
        if num > max_val:
            return False, 0, get_text(lang, "err_amount_max", max_val=max_val)
        return True, num, ""
    except (ValueError, TypeError):
        return False, 0, get_text(lang, "err_amount_invalid")


def generate_math_captcha(lang: str = "ar"):
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    answer = num1 + num2

    wrong_answers = set()
    while len(wrong_answers) < 3:
        w = random.randint(2, 20)
        if w != answer:
            wrong_answers.add(w)

    options = list(wrong_answers) + [answer]
    random.shuffle(options)

    captcha_msg = get_text(lang, "captcha_text", num1=num1, num2=num2)
    return captcha_msg, answer, options
