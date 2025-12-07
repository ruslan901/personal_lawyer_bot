import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import init_db

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # Ваш Telegram ID
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация БД
init_db()

# Главное меню (ТОЛЬКО клиент)
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Услуги", callback_data="services")],
        [InlineKeyboardButton(text="📞 Мои заказы", callback_data="my_orders")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "🤖 **Personal Lawyer Bot** (только для вас)\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "services")
async def services_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Консультация 30мин - 500₽", callback_data="service_consult_500")],
        [InlineKeyboardButton(text="Документ 1стр - 1000₽", callback_data="service_doc_1000")],
        [InlineKeyboardButton(text="Исковое 5стр - 5000₽", callback_data="service_isk_5000")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main")]
    ])
    await callback.message.edit_text(
        "📋 **Услуги:**\n\n"
        "• Консультация 30мин - 500₽\n"
        "• Документ 1стр - 1000₽\n"
        "• Исковое 5стр - 5000₽",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def main():
    print("🚀 Personal Lawyer Bot запущен (только клиентский режим)!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




