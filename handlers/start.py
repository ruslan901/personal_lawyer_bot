from aiogram import F, types
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from database import has_active_order
from keyboards import get_main_keyboard

async def start_handler(message: types.Message, bot, dp: Dispatcher):
    user_id = message.from_user.id
    if user_id == config.LAWYER_ID:
        await message.answer("👨‍⚖️ **Админ-панель юриста**...", parse_mode='Markdown')
        return
    active = has_active_order(user_id)
    if active:
        await message.answer(f"⚠️ **Активный заказ #{active[0]}**...", parse_mode='Markdown')
        return
    await message.answer("👨‍⚖️ **Ваш персональный юрист**...", reply_markup=get_main_keyboard(), parse_mode='Markdown')
