import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import init_db, get_orders, update_order_status, create_order, get_order_client_id

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # Ваш Telegram ID

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


def get_order_keyboard(order_id, status, is_client=False):
    keyboard = []
    if status == "new":
        if is_client:
            keyboard.append([InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"cancel_{order_id}")])
        else:
            keyboard.append([InlineKeyboardButton(text="Завершить заказ", callback_data=f"complete_{order_id}")])
    keyboard.append([InlineKeyboardButton(text="📋 Услуги", callback_data="services")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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
    service_name, price = services[callback.data]

    order_id = create_order(callback.from_user.id, service_name, price)

    # Отправляем уведомление исполнителю
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Завершить заказ", callback_data=f"complete_{order_id}")],
        [InlineKeyboardButton(text="Чат с клиентом", callback_data=f"chat_{order_id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"🆕 Новая заявка #{order_id}\n"
        f"👤 Клиент: {callback.from_user.full_name} (ID: {callback.from_user.id})\n"
        f"📋 {service_name}\n"
        f"💰 {price}₽",
        reply_markup=keyboard
    )

    await callback.message.edit_text(
        f"✅ Заявка #{order_id} создана\n"
        f"Услуга: {service_name}\n"
        f"Цена: {price}₽\n\n"
        "Опишите задачу или приложите документы.\nЮрист скоро свяжется.",
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
        status_emoji = {"new": "🆕", "cancelled": "❌", "completed": "✅"}.get(order['status'], "⚪")
        text += f"{status_emoji} #{order['id']} {order['service_name']} {order['price']}₽ {order['status']}\n"

    await callback.message.edit_text(text, reply_markup=get_services_keyboard())


@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    if update_order_status(order_id, "cancelled"):
        await bot.send_message(ADMIN_ID, f"❌ Заявка #{order_id} отменена клиентом")
        await callback.message.edit_text(f"❌ Заявка #{order_id} отменена.")
    else:
        await callback.message.edit_text("Ошибка отмены заказа.")


@dp.callback_query(F.data.startswith("complete_"), F.from_user.id == ADMIN_ID)
async def complete_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    if update_order_status(order_id, "completed"):
        client_id = get_order_client_id(order_id)
        await bot.send_message(client_id, f"✅ Ваша заявка #{order_id} выполнена!")
        await callback.message.edit_text(f"✅ Заявка #{order_id} завершена.")
    else:
        await callback.message.edit_text("Ошибка.")


@dp.callback_query(F.data.startswith("chat_"), F.from_user.id == ADMIN_ID)
async def chat_with_client_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    client_id = get_order_client_id(order_id)
    await callback.message.edit_text(f"Открыт чат с клиентом {client_id}. Отвечайте на это сообщение, чтобы связаться.")


@dp.message(F.document | F.photo | F.text, F.from_user.id != ADMIN_ID)
async def client_message_handler(message: Message):
    await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    await message.answer("✅ Ваше сообщение получено. Исполнитель ответит вам.")


@dp.message(F.document | F.photo | F.text, F.from_user.id == ADMIN_ID)
async def admin_message_handler(message: Message):
    if message.reply_to_message and message.reply_to_message.forward_from:
        client_id = message.reply_to_message.forward_from.id
        if message.document or message.photo:
            await bot.forward_message(client_id, ADMIN_ID, message.message_id)
        else:
            await bot.send_message(client_id, message.text)
        await message.answer("✅ Сообщение отправлено клиенту.")
    else:
        await message.answer("Ответьте на сообщение клиента (Reply)!")


async def main():
    print("🚀 Personal Lawyer Bot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())







