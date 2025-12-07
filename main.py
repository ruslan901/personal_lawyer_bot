import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import init_db  # ← ТОЛЬКО init_db!

# Инициализация
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация БД
init_db()

def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Клиент", callback_data="client")],
        [InlineKeyboardButton(text="⚖️ Юрист", callback_data="lawyer")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("🤖 Lawyer Bot!\nВыберите роль:", reply_markup=get_main_menu())

async def main():
    print("🚀 Lawyer Bot запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



