import time
import random

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

def generate_math_captcha():
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
    
    return f"🤖 **اختبار الأمان (الكابتشا):**\nيرجى حل المسألة التالية لإكمال التسجيل:\n\nكم يساوي: `{num1} + {num2}` ؟", answer, options
