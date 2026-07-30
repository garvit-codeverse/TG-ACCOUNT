import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN        = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_IDS        = list(map(int, os.getenv("ADMIN_IDS", "8066849679").split(",")))
ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME", "@EVILTALKS")
LOG_CHANNEL_ID   = int(os.getenv("LOG_CHANNEL_ID", "-1003773215198"))
LOG_CHANNEL_LINK = os.getenv("LOG_CHANNEL_LINK", "https://t.me/ACCOUNT_SELLER_PRO")
SUPPORT_GROUP    = os.getenv("SUPPORT_GROUP", "@ACCSPRO_SUPPORT")
UPI_ID           = os.getenv("UPI_ID", "das20@fam")
UPI_NAME         = os.getenv("UPI_NAME", "EVILTALKS Store")
API_ID           = int(os.getenv("API_ID", "0"))
API_HASH         = os.getenv("API_HASH", "")
DATABASE_URL     = os.getenv("DATABASE_URL", "bot.db")
BOT_NAME         = "EVILTALKS AccountBot"

FORCE_JOIN_RAW = os.getenv("FORCE_JOIN_CHANNELS", "")

def get_force_join_channels():
    if not FORCE_JOIN_RAW.strip():
        return []
    channels = []
    for entry in FORCE_JOIN_RAW.split(","):
        entry = entry.strip()
        if ":" not in entry:
            continue
        idx     = entry.index(":")
        ch_id   = entry[:idx].strip()
        ch_link = entry[idx+1:].strip()
        try:
            channels.append({"id": int(ch_id), "link": ch_link})
        except Exception:
            pass
    return channels

FORCE_JOIN_CHANNELS = get_force_join_channels()
