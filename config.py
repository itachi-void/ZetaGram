import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [
    int(id_str)
    for id_str in os.getenv("ADMIN_IDS", "123456789").split(",")
    if id_str.strip().isdigit()
]
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@YourRequiredChannel")
REQUIRED_CHANNEL_LINK = os.getenv("REQUIRED_CHANNEL_LINK", "https://t.me/YourRequiredChannel")

DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")

BOT_NAME = os.getenv("BOT_NAME", "ZetaGram")
PERSISTENCE_FILE = os.getenv("PERSISTENCE_FILE", "bot_persistence.pickle")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN", "")

# Economy & Security Constants
MIN_TRANSFER_AMOUNT = 100
DAILY_TRANSFER_LIMIT = 50_000
MIN_TASKS_FOR_TRANSFER = 3
MAX_VAULT_DEPOSIT = 100_000
MAX_ACTIVE_VAULT_DEPOSITS = 5
RECAPTCHA_TASK_INTERVAL = 15
AUTO_APPROVE_PROOF_HOURS = 24
REFERRAL_JOIN_BONUS = 100
REFERRAL_ACTIVE_BONUS = 250
REFERRAL_COMMISSION_RATE = 0.10
DAILY_QUEST_TARGET = 5
DAILY_QUEST_REWARD = 150
MIN_POST_VIEW_SECONDS = 7
CAPTCHA_TTL_SECONDS = 120
CAPTCHA_MAX_ATTEMPTS = 3
CAPTCHA_LOCK_MINUTES = 5
STARS_FEE_FREE_COST = 50
STREAK_REWARDS = [100, 150, 200, 250, 300, 400, 500]
LEADERBOARD_PRIZES = [1500, 1000, 500]

VIP_PERKS = {
    1: {"title": "🥉 مبتدئ", "promo_fee": 0.15, "transfer_fee": 0.02, "task_bonus": 0.00, "vault_bonus": 0.00},
    2: {"title": "🥈 نشيط", "promo_fee": 0.13, "transfer_fee": 0.015, "task_bonus": 0.03, "vault_bonus": 0.01},
    3: {"title": "🥇 خبير", "promo_fee": 0.11, "transfer_fee": 0.01, "task_bonus": 0.05, "vault_bonus": 0.02},
    4: {"title": "💎 VIP مميز", "promo_fee": 0.08, "transfer_fee": 0.00, "task_bonus": 0.10, "vault_bonus": 0.03},
}
