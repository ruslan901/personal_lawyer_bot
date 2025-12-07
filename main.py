import asyncio
import logging
import os
import signal
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database import init_db, conn
from utils import setup_lock, cleanup_lock
from handlers.start import router as start_router
from handlers.services import router as services_router
from handlers.orders import router as orders_router
from handlers.chat import router as chat_router
from handlers.lawyer import router as lawyer_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(services_router)
    dp.include_router(orders_router)
    dp.include_router(chat_router)
    dp.include_router(lawyer_router)

    setup_lock()
    await init_db()

    try:
        logger.info("🚀 Запуск lawyer_bot...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, skip_updates=True)
    finally:
        cleanup_lock()
        await bot.session.close()
        conn.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Остановка...")

