import asyncio
import os
import sqlite3
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ContentType
from database import init_db, get_orders, update_order_status, create_order, get_order_client_id

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # Вы = Исполнитель

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

init_db()


def get_services_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Юридическая консультация от 2500₽", callback_data="service_consult")],
        [InlineKeyboardButton(text="Составление документов от 3000₽", callback_data="service_doc")],
        [InlineKeyboardButton(text="Представительские услуги от 5000₽", callback_data="service_rep")],
        [InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders")]
    ])


@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "🤖 Личный юридический помощник\n\n"
        "Выберите услугу:",
        reply_markup=get_services_keyboard()
    )


@dp.callback_query(F.data.in_({"service_consult", "service_doc", "service_rep"}))
async def create_order_handler(callback: CallbackQuery):
    services = {
        "service_consult": ("Юридическая консультация", 2500),
        "service_doc": ("Составление документов", 3000),
        "service_rep": ("Представительские услуги", 5000)
    }
    service_data = services[callback.data]

    order_id = create_order(callback.from_user.id, service_data[0], service_data[1])

    # ✅ ИСПРАВЛЕНО: Админ получает заявку + кнопки управления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполнить заказ", callback_data=f"complete_{order_id}")],
        [InlineKeyboardButton(text="📱 Чат с клиентом", callback_data=f"chat_{order_id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"🆕 Новая заявка #{order_id}\n"
        f"👤 Клиент: {callback.from_user.full_name} (ID: {callback.from_user.id})\n"
        f"📋 {service_data[0]}\n"
        f"💰 {service_data[1]}₽",
        reply_markup=keyboard
    )

    await callback.message.edit_text(
        f"✅ Заявка #{order_id} создана\n"
        f"Услуга: {service_data[0]}\n"
        f"Цена: {service_data[1]}₽\n\n"
        "💬 Напишите детали задачи / приложите документы.\n"
        "Юрист свяжется скоро.",
        reply_markup=get_services_keyboard()
    )


@dp.callback_query(F.data == "my_orders")
async def my_orders_handler(callback: CallbackQuery):
    orders = get_orders(callback.from_user.id)
    if not orders:
        await callback.message.edit_text("📭 Нет активных заказов.")
        return

    text = "📋 Ваши заказы:\n\n"
    for order in orders[:5]:
        status_emoji = {"new": "🆕", "cancelled": "❌", "completed": "✅"}[order['status']]
        text += f"{status_emoji} #{order['id']} | {order['service_name']} | {order['price']}₽\n"

    await callback.message.edit_text(text, reply_markup=get_services_keyboard())


# ✅ ИСПОЛНИТЕЛЬ (админ) управляет заказами
@dp.callback_query(F.data.startswith("complete_"), F.from_user.id == ADMIN_ID)
async def complete_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    if update_order_status(order_id, "completed"):
        client_id = get_order_client_id(order_id)
        await bot.send_message(client_id, f"✅ Заявка #{order_id} выполнена!")
        await callback.message.edit_text(f"✅ Заявка #{order_id} завершена.")
    else:
        await callback.message.edit_text("Ошибка.")


@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    if update_order_status(order_id, "cancelled"):
        await bot.send_message(ADMIN_ID, f"❌ Заявка #{order_id} отменена клиентом")
        await callback.message.edit_text(f"❌ Заявка #{order_id} отменена.")
    else:
        await callback.message.edit_text("Ошибка.")


# ✅ ПЕРЕПИСКА: Клиент ↔ Исполнитель (админ)
@dp.message(F.document | F.photo | F.text, F.from_user.id != ADMIN_ID)
async def client_message_handler(message: Message):
    await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    await message.answer("✅ Получено исполнителем.")


@dp.message(F.document | F.photo | F.text, F.from_user.id == ADMIN_ID)
async def admin_message_handler(message: Message):
    if message.reply_to_message and message.reply_to_message.forward_from:
        client_id = message.reply_to_message.forward_from.id
        if message.document:
            await bot.forward_message(client_id, ADMIN_ID, message.message_id)
        elif message.photo:
            await bot.forward_message(client_id, ADMIN_ID, message.message_id)
        else:
            await bot.send_message(client_id, message.text)
        await message.answer("✅ Отправлено клиенту")
    else:
        await message.answer("Ответьте на сообщение клиента (Reply).")


# Админ видит все заявки
@dp.message(Command("orders"), F.from_user.id == ADMIN_ID)
async def admin_orders(message: Message):
    orders = get_orders()
    text = "📋 Все заявки:\n\n"
    for order in orders[:10]:
        status_emoji = {"new": "🆕", "cancelled": "❌", "completed": "✅"}[order['status']]
        text += f"{status_emoji} #{order['id']} | {order['service_name']} | {order['price']}₽\n"
    await message.answer(text)


async def main():
    print("🚀 Personal Lawyer Bot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())






