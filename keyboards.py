from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import USLUGI

def get_main_keyboard():
    kb = InlineKeyboardBuilder()
    for key in USLUGI: kb.button(text=USLUGI[key]['name'], callback_data=f"usluga_{key}")
    kb.button(text="ℹ️ Цены", callback_data="prices").adjust(1)
    return kb.as_markup()
