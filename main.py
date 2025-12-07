import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import init_db, get_orders, update_order_status, create_order, get_order_client_id

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
PROVIDER_TOKEN = os.getenv("YOOMONEY_TOKEN")  # Ваш YouMoney токен

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
    service_name, price = services[callback.data]

    order_id = create_order(callback.from_user.id, service_name, price)

    # Кнопки исполнителю
    exec_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Завершить заказ", callback_data=f"complete_{order_id}")],
        [InlineKeyboardButton(text="💬 Чат с клиентом", callback_data=f"chat_{order_id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"🆕 Заявка #{order_id}\n"
        f"👤 {callback.from_user.full_name} (ID: {callback.from_user.id})\n"
        f"📋 {service_name}\n"
        f"💰 {price}₽",
        reply_markup=exec_keyboard
    )

    # Кнопка оплаты клиенту
    pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить {price}₽", callback_data=f"pay_{order_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{order_id}")]
    ])

    await callback.message.edit_text(
        f"✅ Заявка #{order_id}\n"
        f"📋 {service_name}\n"
        f"💰 {price}₽\n\n"
        "Выберите действие:",
        reply_markup=pay_keyboard
    )


@dp.callback_query(F.data.startswith("pay_"))
async def pay_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    order = get_orders(order_id)[0]  # Получаем заказ
    prices = [LabeledPrice(label=order['service_name'], amount=order['price'] * 100)]

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=order['service_name'],
        description=f"Заявка #{order_id}",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        payload=f"order_{order_id}"
    )


@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_q):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    order_id = int(message.successful_payment.invoice_payload.split("_")[1])
    update_order_status(order_id, "paid")
    await message.answer("✅ Оплата прошла! Ожидайте исполнителя.")
    await bot.send_message(ADMIN_ID, f"💳 Заявка #{order_id} оплачена!")


@dp.callback_query(F.data == "my_orders")
async def my_orders_handler(callback: CallbackQuery):
    orders = get_orders(callback.from_user.id)
    if not orders:
        await callback.message.edit_text("📭 Нет заказов.")
        return

    text = "📋 Ваши заказы:\n\n"
    for order in orders[:5]:
        status_emoji = {"new": "🆕", "cancelled": "❌", "completed": "✅", "paid": "💳"}.get(order['status'], "⚪")
        text += f"{status_emoji} #{order['id']} | {order['service_name']} | {order['price']}₽ | {order['status']}\n"

    await callback.message.edit_text(text, reply_markup=get_services_keyboard())


@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    if update_order_status(order_id, "cancelled"):
        await bot.send_message(ADMIN_ID, f"❌ Заявка #{order_id} отменена")
        await callback.message.edit_text(f"❌ Заявка #{order_id} отменена.")
    else:
        await callback.message.edit_text("Ошибка.")


@dp.callback_query(F.data.startswith("complete_"), F.from_user.id == ADMIN_ID)
async def complete_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    if update_order_status(order_id, "completed"):
        client_id = get_order_client_id(order_id)
        await bot.send_message(client_id, f"✅ Заявка #{order_id} выполнена!")
        await callback.message.edit_text(f"✅ Заявка #{order_id} завершена.")
    else:
        await callback.message.edit_text("Ошибка.")


@dp.callback_query(F.data.startswith("chat_"), F.from_user.id == ADMIN_ID)
async def chat_handler(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    client_id = get_order_client_id(order_id)
    await callback.message.edit_text(f"💬 Чат с клиентом {client_id} (#{order_id})\nОтвечайте на сообщения клиента!")


# ✅ ПЕРЕПИСКА РАБОТАЕТ
current_chats = {}  # {client_id: order_id}


@dp.message(F.text | F.document | F.photo, F.from_user.id != ADMIN_ID)
async def client_message(message: Message):
    await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    await message.answer("✅ Сообщение отправлено исполнителю.")


@dp.message(F.text | F.document | F.photo, F.from_user.id == ADMIN_ID)
async def admin_message(message: Message):
    if message.reply_to_message and message.reply_to_message.forward_from:
        client_id = message.reply_to_message.forward_from.id
        await bot.forward_message(client_id, ADMIN_ID, message.message_id)
        await message.answer(f"✅ Отправлено клиенту {client_id}")
    else:
        await message.answer("Ответьте на сообщение клиента (Reply)!")


async def main():
    print("🚀 Personal Lawyer Bot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())








