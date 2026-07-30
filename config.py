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

# ---------- PAYMENT ----------
UPI_ID = os.getenv("UPI_ID")

# ---------- GMAIL (for FamPay auto-payment) ----------
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# ---------- CONFIG VALIDATION ----------
def check_config():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN","8746962237:AAESKxN7MN3Tb_UnvaPTKfJWaBzeeZWB0P0")
    if not API_ID:
        missing.append("API_ID","36772021")
    if not API_HASH:
        missing.append("API_HASH","9f0cdb1047c9042567a40ee221df330f")
    if not ADMIN_IDS:
        missing.append("ADMIN_IDS","5416091579")
    if not UPI_ID:
        missing.append("UPI_ID","imvishal739@fam")
    if not GMAIL_EMAIL:
        missing.append("GMAIL_EMAIL")
    if not GMAIL_APP_PASSWORD:
        missing.append("GMAIL_APP_PASSWORD")
    
    if missing:
        raise EnvironmentError(
            f"❌ Missing env vars: {', '.join(missing)}\n"
            "Please set them in .env file"
        )
    print("✅ All configurations loaded successfully!")
