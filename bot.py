import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from config import BOT_TOKEN, check_config
from database import init_db
from handlers import user, admin, payment, otp, deposit, settings, session_manager

# ---------- LOGGING ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ---------- CONFIG VALIDATION ----------
try:
    check_config()
except Exception as e:
    logger.critical(f"Config error: {e}")
    sys.exit(1)

# ---------- BOT & DISPATCHER ----------
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

# ---------- REGISTER ROUTERS ----------
dp.include_router(admin.router)
dp.include_router(settings.router)
dp.include_router(session_manager.router)
dp.include_router(payment.router)
dp.include_router(otp.router)
dp.include_router(deposit.router)
dp.include_router(user.router)

# ---------- GLOBAL ERROR HANDLER ----------
@dp.error()
async def global_error_handler(event: ErrorEvent):
    logger.error(f"Unhandled error: {event.exception}", exc_info=True)
    # Optionally notify user if possible
    if event.update.message:
        await event.update.message.answer(
            "❌ Something went wrong. Please try again later."
        )
    return True

# ---------- MAIN ----------
async def main():
    try:
        await init_db()
        logger.info("✅ Database initialized.")
    except Exception as e:
        logger.critical(f"Database init failed: {e}")
        sys.exit(1)

    logger.info("🚀 Bot is starting...")
    try:
        # Drop pending updates to avoid old messages
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.critical(f"Polling failed: {e}")
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user.")
