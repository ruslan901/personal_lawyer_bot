import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import os
from database import init_db, get_async_db

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ИНИЦИАЛИЗАЦИЯ БАЗЫ ПРИ СТАРТЕ
init_db()

# Главное меню
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Клиент", callback_data="client")],
        [InlineKeyboardButton(text="⚖️ Юрист", callback_data="lawyer")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "🤖 Добро пожаловать в Lawyer Bot!\n\n"
        "Выберите свою роль:",
        reply_markup=get_main_menu()
    )

@dp.callback_query(F.data == "client")
async def client_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Услуги", callback_data="services")],
        [InlineKeyboardButton(text="📞 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main")]
    ])
    await callback.message.edit_text(
        "👤 **Клиент**\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "lawyer")
async def lawyer_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Взять заказ", callback_data="take_order")],
        [InlineKeyboardButton(text="📋 Мои заказы", callback_data="lawyer_orders")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main")]
    ])
    await callback.message.edit_text(
        "⚖️ **Юрист**\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def main():
    print("🚀 Lawyer Bot запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


