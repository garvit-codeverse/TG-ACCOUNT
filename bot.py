# bot.py – DEVILS WILL RISE EDITION 🔥 (FIXED)
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from config import BOT_TOKEN, ADMIN_IDS, check_config
import database as db

logging.basicConfig(level=logging.INFO)

if not check_config():
    exit(1)

# ── DATABASE INIT (SYNC) ──
db.init_db()
print("✅ Database initialized")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ── IMPORT HANDLERS ──────────────────────────────────────────────
from handlers import browse, payment, user, admin, deposit, otp, settings, session_manager

dp.include_router(browse.router)
dp.include_router(payment.router)
dp.include_router(user.router)
dp.include_router(admin.router)
dp.include_router(deposit.router)
dp.include_router(otp.router)
dp.include_router(settings.router)
dp.include_router(session_manager.router)

# ── START COMMAND ──────────────────────────────────────────────────
@dp.message(Command("start"))
async def start_cmd(msg: Message):
    await db.create_user(msg.from_user.id, msg.from_user.username or "", msg.from_user.full_name or "")
    
    await msg.answer(
        f"🎉 <b>Welcome to GARVIT AccountBot!</b>\n\n"
        f"🔥 Buy premium accounts easily\n"
        f"💳 Pay via UPI (Auto-verify)\n"
        f"📱 Instant delivery after payment\n\n"
        f"Use /browse to see available accounts\n"
        f"Use /profile to see your stats",
        parse_mode="HTML"
    )

# ── SUPPORT ────────────────────────────────────────────────────────
@dp.message(Command("support"))
async def support_cmd(msg: Message):
    from config import SUPPORT_GROUP
    await msg.answer(
        f"🆘 <b>Support</b>\n\n"
        f"Join: {SUPPORT_GROUP}\n"
        f"Contact: @BOTMAKERGARVIT",
        parse_mode="HTML"
    )

# ── MAIN ───────────────────────────────────────────────────────────
async def main():
    print("💀 DEVILS WILL RISE – BOT STARTED 💀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
if __name__ == "__main__":
    asyncio.run(main())
