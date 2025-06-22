from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers_main import register_handlers as register_main_handlers
from handlers_market import register_handlers as register_market_handlers
from handlers_extra import register_extra_handlers, BanCheckMiddleware
from admin import register_admin_handlers
from database import init_db
from config import BOT_TOKEN
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация базы данных
    init_db()
    
    # Настройка middleware для обработки сообщений
    dp.message.middleware(BanCheckMiddleware())
    
    # Регистрация обработчиков
    register_main_handlers(dp)  # Регистрируем основные обработчики
    register_market_handlers(dp)  # Регистрируем обработчики для магазинов, топов и работы
    register_extra_handlers(dp)  # Регистрируем дополнительные обработчики
    register_admin_handlers(dp)  # Регистрируем админские обработчики
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())