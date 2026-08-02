import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(id_str) for id_str in os.getenv("ADMIN_IDS", "123456789").split(",") if id_str.strip().isdigit()]
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@YourRequiredChannel")
REQUIRED_CHANNEL_LINK = os.getenv("REQUIRED_CHANNEL_LINK", "https://t.me/YourRequiredChannel")

DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")
