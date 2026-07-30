# config.py – DEVILS WILL RISE EDITION 🔥
import os

# ============================================
# 🔥 BOT CONFIG – RAILWAY VARIABLES
# ============================================

BOT_TOKEN        = os.getenv("BOT_TOKEN", "8746962237:AAESKxN7MN3Tb_UnvaPTKfJWaBzeeZWB0P0")
ADMIN_IDS        = list(map(int, os.getenv("ADMIN_IDS", "5416091579").split(",")))
ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME", "@BOTMAKERGARVIT")
LOG_CHANNEL_ID   = int(os.getenv("LOG_CHANNEL_ID", "-1003589850886"))
LOG_CHANNEL_LINK = os.getenv("LOG_CHANNEL_LINK", "https://t.me/indsocialhub")
SUPPORT_GROUP    = os.getenv("SUPPORT_GROUP", "@indsocialhub")

# UPI CONFIG
UPI_ID           = os.getenv("UPI_ID", "imvishal739@fam")
UPI_NAME         = os.getenv("UPI_NAME", "VISHAL KUMAR")

# TELEGRAM API
API_ID           = int(os.getenv("API_ID", "36772021"))
API_HASH         = os.getenv("API_HASH", "9f0cdb1047c9042567a40ee221df330f")

# DATABASE
DATABASE_URL     = os.getenv("DATABASE_URL", "bot.db")

# BOT NAME
BOT_NAME         = os.getenv("BOT_NAME", "GARVIT AccountBot")

# GMAIL CONFIG
GMAIL_USER       = os.getenv("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip().replace(" ", "")

GMAIL_AVAILABLE = bool(GMAIL_USER and GMAIL_APP_PASSWORD)

# ============================================
# 🔥 CHECK_CONFIG FUNCTION – YEH MISSING THA
# ============================================
def check_config():
    """Check if all required config variables are set"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("❌ BOT_TOKEN missing")
    
    if not ADMIN_IDS or ADMIN_IDS == [0]:
        errors.append("❌ ADMIN_IDS missing")
    
    if not UPI_ID:
        errors.append("❌ UPI_ID missing")
    
    if errors:
        print("\n".join(errors))
        return False
    
    print(f"""
💀 DEVILS WILL RISE – CONFIG LOADED 💀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Bot: {BOT_NAME}
👑 Admins: {ADMIN_IDS}
📢 Channel: {LOG_CHANNEL_LINK}
💳 UPI: {UPI_ID}
📧 Gmail: {'✅ CONNECTED' if GMAIL_AVAILABLE else '❌ Not Set'}
📦 Database: {DATABASE_URL}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    return True


# ── FOR DEBUGGING ──────────────────────────────────────────────────
if __name__ == "__main__":
    check_config()
