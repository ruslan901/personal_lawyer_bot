from aiogram import F
from database import create_order
from config import USLUGI, YOOMONEY_WALLET, LAWYER_ID
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

@dp.callback_query(F.data.startswith("usluga_"))
async def usluga_handler(callback: types.CallbackQuery):
    # Логика выбора услуги (как в оригинале)
    pass

@dp.callback_query(F.data.startswith("oplata_"))
async def oplata_handler(callback: types.CallbackQuery):
    # Полная логика создания заказа, отправки юристу (как в оригинале)
    pass
