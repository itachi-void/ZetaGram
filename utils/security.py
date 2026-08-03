import time
import random
import asyncio
from typing import Tuple, Dict
from config import ADMIN_IDS
from utils.i18n import get_text

class RateLimiter:
    def __init__(self, cooldown_seconds: float = 1.0):
        self.cooldown = cooldown_seconds
        self.user_timestamps = {}

    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        last_time = self.user_timestamps.get(user_id, 0)
        if now - last_time < self.cooldown:
            return False
        self.user_timestamps[user_id] = now
        return True

rate_limiter = RateLimiter(cooldown_seconds=1.0)

class UserLockManager:
    """
    Manages per-user asyncio Locks to prevent race condition / double spending exploits
    when multiple concurrent requests arrive from the same user.
    """
    def __init__(self):
        self._locks: Dict[int, asyncio.Lock] = {}

    def get_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

user_lock_manager = UserLockManager()

async def send_security_alert(bot, message: str):
    """Sends immediate security alert to all ADMIN_IDS."""
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=f"🚨 **تنبيه أمني عاجل من البوت:**\n\n{message}",
                parse_mode="Markdown"
            )
        except Exception:
            pass

def is_admin_user(user_id: int, bot=None, command_name: str = "") -> bool:
    """Strictly checks if user_id is in ADMIN_IDS and alerts admins on unauthorized attempts."""
    if user_id in ADMIN_IDS:
        return True
    
    if bot and command_name:
        asyncio.create_task(
            send_security_alert(
                bot,
                f"⚠️ محاولة تسلل غير مصرح بها للوحة الأدمن!\n"
                f"👤 المستخدم: `{user_id}`\n"
                f"📌 الأمر المحاول: `{command_name}`"
            )
        )
    return False

def sanitize_amount(val: str, min_val: int = 1, max_val: int = 1_000_000_000) -> Tuple[bool, int, str]:
    """
    Sanitizes integer amounts to prevent negative values, zero, or overflow attacks.
    Returns: (is_valid, parsed_int, error_message)
    """
    try:
        val_clean = str(val).strip()
        num = int(val_clean)
        if num < min_val:
            return False, 0, f"❌ المبلغ يجب أن يكون {min_val:,} على الأقل."
        if num > max_val:
            return False, 0, f"❌ المبلغ يتجاوز الحد الأقصى المسموح به ({max_val:,})."
        return True, num, ""
    except (ValueError, TypeError):
        return False, 0, "❌ يرجى إدخال رقم صحيح."

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
