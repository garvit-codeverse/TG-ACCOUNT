import os
from dotenv import load_dotenv

load_dotenv()

# ---------- BOT CREDENTIALS ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# ---------- DATABASE ----------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data.db")

# ---------- ADMIN ----------
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# ---------- FAMPAY PAYMENT ----------
UPI_ID = os.getenv("UPI_ID")  # Teri FamPay UPI ID

# ---------- GMAIL IMAP (FamPay receipt scan ke liye) ----------
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# ---------- CONFIG VALIDATION ----------
def check_config():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not ADMIN_IDS:
        missing.append("ADMIN_IDS")
    if not UPI_ID:
        missing.append("UPI_ID")
    if not GMAIL_EMAIL:
        missing.append("GMAIL_EMAIL")
    if not GMAIL_APP_PASSWORD:
        missing.append("GMAIL_APP_PASSWORD")
    
    if missing:
        raise EnvironmentError(
            f"❌ Missing env vars: {', '.join(missing)}\n"
            "Please set them in .env file"
        )
    print("✅ FamPay config loaded successfully!")
