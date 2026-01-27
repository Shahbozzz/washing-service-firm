import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from client import router as client_router
from admin import router as admin_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable not set!")
    
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(client_router)
    dp.include_router(admin_router)
    
    logger.info("Bot ishga tushdi...")
    
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi")
    except Exception as e:
        logger.error(f"Xatolik yuz berdi: {e}")