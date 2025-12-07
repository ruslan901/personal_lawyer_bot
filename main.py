import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ContentType
from database import init_db, get_orders, update_order_status, create_order

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

init_db()


# Клавиатуры
def get_services_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Юридическая консультация от 2500₽", callback_data="service_consult")],
        [InlineKeyboardButton(text="Составление документов от 3000₽", callback_data="service_doc")],
        [InlineKeyboardButton(text="Представительские услуги от 5000₽", callback_data="service_rep")],
        [InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders")]
    ])


def get_order_keyboard(order_id, status):
    keyboard = []
    if status == "new":
        keyboard.append([InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"cancel_{order_id}")])
    elif status == "completed":
        keyboard.append([InlineKeyboardButton(text="⭐ Оценить", callback_data=f"rate_{order_id}")])
    keyboard.append([InlineKeyboardButton(text="📋 Услуги", callback_data="services")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Клиентские хендлеры
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "🤖 **Личный юридический помощник**\n\n"
        "Выберите услугу:",
        reply_markup=get_services_keyboard(),
        parse_mode="Markdown"
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

    # Уведомить юриста
    await bot.send_message(
        ADMIN_ID,
        f"🆕 **Новый заказ #{order_id}**\n"
        f"👤 Клиент: {callback.from_user.full_name} (`{callback.from_user.id}`)\n"
        f"📋 Услуга: {service_data[0]}\n"
        f"💰 Цена: {service_data[1]}₽\n"
        f"📱 Чат: https://t.me/{(await bot.get_me()).username}?start=chat_{order_id}",
        parse_mode="Markdown"
    )

    await callback.message.edit_text(
        f"✅ **Заказ #{order_id} создан**\n\n"
        f"📋 **Услуга:** {service_data[0]}\n"
        f"💰 **Цена:** {service_data[1]}₽\n\n"
        "💬 Напишите детали задачи или приложите документы.\n"
        "Юрист свяжется с вами в ближайшее время.",
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "my_orders")
async def my_orders_handler(callback: CallbackQuery):
    orders = get_orders(callback.from_user.id)
    if not orders:
        await callback.message.edit_text("📭 У вас нет активных заказов.")
        return

    text = "📋 **Ваши заказы:**\n\n"
    for order in orders[:5]:  # Показать последние 5
        status_emoji = {"new": "🆕", "cancelled": "❌", "completed": "✅"}.get(order['status'], "⚪")
        text += f"{status_emoji} #{order['id']} | {order['service_name']} | {order['price']}₽ | {order['status']}\n"

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_services_keyboard())


@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    if update_order_status(order_id, "cancelled"):
        await bot.send_message(ADMIN_ID, f"❌ **Заказ #{order_id} отменён клиентом**")
        await callback.message.edit_text(f"❌ Заказ #{order_id} отменён.")
    else:
        await callback.message.edit_text("Ошибка отмены заказа.")


# Юристские хендлеры (только для ADMIN_ID)
@dp.callback_query(F.data.startswith("complete_"), F.from_user.id == ADMIN_ID)
async def complete_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    if update_order_status(order_id, "completed"):
        # Найти клиента
        conn = sqlite3.connect('/app/database.db')
        client_id = conn.execute("SELECT client_id FROM orders WHERE id = ?", (order_id,)).fetchone()[0]
        conn.close()
        await bot.send_message(client_id, f"✅ Заказ #{order_id} выполнен!")
        await callback.message.edit_text(f"✅ Заказ #{order_id} завершён.")
    else:
        await callback.message.edit_text("Ошибка.")


# Переписка клиент ↔ юрист
@dp.message(F.document | F.photo | F.text, F.from_user.id != ADMIN_ID)
async def client_message_handler(message: Message):
    # Переслать юриста
    await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    await message.answer("✅ Сообщение отправлено юристу.")


@dp.message(F.document | F.photo | F.text, F.from_user.id == ADMIN_ID)
async def admin_message_handler(message: Message):
    if message.text and message.text.startswith("@"):
        # @client_id текст
        parts = message.text.split(" ", 1)
        client_id = int(parts[0][1:])
        text = parts[1] if len(parts) > 1 else ""
        await bot.send_message(client_id, text)
        await message.answer(f"✅ Отправлено клиенту {client_id}")
    else:
        await message.answer("Формат: @client_id текст сообщения")


async def main():
    print("🚀 Lawyer Bot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())





