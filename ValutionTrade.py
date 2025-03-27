import random
import time
import logging
import sqlite3
import asyncio
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
from CheckName import check_name
from advanced_logger import log_operation_async

with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

logging.basicConfig(level=logging.INFO)

from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Добавляем колонку для нотокоинов в таблицу users
def add_notocoins_column():
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        if "notocoins" not in [column[1] for column in columns]:
            cursor.execute("ALTER TABLE users ADD COLUMN notocoins INTEGER DEFAULT 0")
            conn.commit()
            logging.info("Столбец notocoins добавлен в таблицу users.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении столбца notocoins: {e}")

add_notocoins_column()

def create_exchange_rates_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchange_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            previous_rate REAL,
            current_rate REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

create_exchange_rates_table()

# Инициализация курсов
exchange_rate_cat_to_magic = 0.5
exchange_rate_cat_to_noto = 0.1  # 5000 котокоинов = 500 нотокоинов
exchange_rate_magic_to_noto = 0.2  # 2500 магических коинов = 500 нотокоинов

previous_exchange_rate_cat_to_magic = exchange_rate_cat_to_magic
previous_exchange_rate_cat_to_noto = exchange_rate_cat_to_noto
previous_exchange_rate_magic_to_noto = exchange_rate_magic_to_noto

last_rate_update = time.time()

def update_exchange_rate():
    global exchange_rate_cat_to_magic, exchange_rate_cat_to_noto, exchange_rate_magic_to_noto
    global last_rate_update, previous_exchange_rate_cat_to_magic, previous_exchange_rate_cat_to_noto, previous_exchange_rate_magic_to_noto
    current_time = time.time()
    if current_time - last_rate_update >= config['exchange_rate_update_interval']:
        previous_exchange_rate_cat_to_magic = exchange_rate_cat_to_magic
        previous_exchange_rate_cat_to_noto = exchange_rate_cat_to_noto
        previous_exchange_rate_magic_to_noto = exchange_rate_magic_to_noto

        # Обновляем курс котокоины -> магические коины
        change_percent = random.uniform(-0.1, 0.3)  # Увеличение на 10%-30% или уменьшение на 5%-10%
        exchange_rate_cat_to_magic = max(0.4, min(1.0, round(exchange_rate_cat_to_magic * (1 + change_percent), 2)))

        # Обновляем курс котокоины -> нотокоины
        change_percent = random.uniform(-0.1, 0.5)  # Увеличение на 30%-50% или уменьшение на 1%-10%
        exchange_rate_cat_to_noto = max(0.05, min(0.2, round(exchange_rate_cat_to_noto * (1 + change_percent), 2)))

        # Обновляем курс магические коины -> нотокоины
        change_percent = random.uniform(-0.25, 0.5)  # Увеличение на 30%-50% или уменьшение на 10%-25%
        exchange_rate_magic_to_noto = max(0.1, min(0.3, round(exchange_rate_magic_to_noto * (1 + change_percent), 2)))

        last_rate_update = current_time

        cursor.execute('''
            INSERT INTO exchange_rates (previous_rate, current_rate)
            VALUES (?, ?)
        ''', (previous_exchange_rate_cat_to_magic, exchange_rate_cat_to_magic))
        conn.commit()

        logging.info(f"Курс обновлен: 1000 котокоинов = {int(1000 * exchange_rate_cat_to_magic)} магических коинов")
        logging.info(f"Курс обновлен: 5000 котокоинов = {int(5000 * exchange_rate_cat_to_noto)} нотокоинов")
        logging.info(f"Курс обновлен: 2500 магических коинов = {int(2500 * exchange_rate_magic_to_noto)} нотокоинов")

async def on_startup(dp: Dispatcher):
    exchange_rate_update_interval = config['exchange_rate_update_interval']

    async def update_rate_periodically():
        while True:
            update_exchange_rate()
            await asyncio.sleep(exchange_rate_update_interval)

    asyncio.create_task(update_rate_periodically())

async def exchange_command(message: types.Message):
    if not await check_name(message):
        return
    update_exchange_rate()
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🐱 Котокоины → 🔮 Магические коины", callback_data="exchange_cat_to_magic"),
        InlineKeyboardButton("🔮 Магические коины → 🐱 Котокоины", callback_data="exchange_magic_to_cat"),
        InlineKeyboardButton("🐱 Котокоины → 🎵 Нотокоины", callback_data="exchange_cat_to_noto"),
        InlineKeyboardButton("🔮 Магические коины → 🎵 Нотокоины", callback_data="exchange_magic_to_noto"),
        InlineKeyboardButton("📈 Проверить курс", callback_data="check_rate"),
    )
    await message.answer(
        f"Текущий курс обмена:\n"
        f"\n"
        f"1000 котокоинов = {int(1000 * exchange_rate_cat_to_magic)} магических коинов\n"
        f"5000 котокоинов = {int(5000 * exchange_rate_cat_to_noto)} нотокоинов\n"
        f"2500 магических коинов = {int(2500 * exchange_rate_magic_to_noto)} нотокоинов\n\n"
        f"Курс меняется каждую минуту, не забывайте его проверять.\n"
        "Выберите направление обмена:",
        reply_markup=keyboard,
        parse_mode=types.ParseMode.MARKDOWN,
    )

async def exchange_callback(callback: types.CallbackQuery):
    await callback.message.delete()
    data = callback.data
    if data == "check_rate":
        # Проверка курса котокоины -> магические коины
        if exchange_rate_cat_to_magic > previous_exchange_rate_cat_to_magic:
            cat_to_magic_status = "поднялся 📈"
        elif exchange_rate_cat_to_magic < previous_exchange_rate_cat_to_magic:
            cat_to_magic_status = "упал 📉"
        else:
            cat_to_magic_status = "остался прежним ⚖️"

        # Проверка курса котокоины -> нотокоины
        if exchange_rate_cat_to_noto > previous_exchange_rate_cat_to_noto:
            cat_to_noto_status = "поднялся 📈"
        elif exchange_rate_cat_to_noto < previous_exchange_rate_cat_to_noto:
            cat_to_noto_status = "упал 📉"
        else:
            cat_to_noto_status = "остался прежним ⚖️"

        # Проверка курса магические коины -> нотокоины
        if exchange_rate_magic_to_noto > previous_exchange_rate_magic_to_noto:
            magic_to_noto_status = "поднялся 📈"
        elif exchange_rate_magic_to_noto < previous_exchange_rate_magic_to_noto:
            magic_to_noto_status = "упал 📉"
        else:
            magic_to_noto_status = "остался прежним ⚖️"

        # Формируем сообщение с текущими курсами
        message_text = (
            f"Текущие курсы обмена:\n\n"
            f"🐱 Котокоины → 🔮 Магические коины:\n"
            f"1000 котокоинов = {int(1000 * exchange_rate_cat_to_magic)} магических коинов ({cat_to_magic_status})\n\n"
            f"🐱 Котокоины → 🎵 Нотокоины:\n"
            f"5000 котокоинов = {int(5000 * exchange_rate_cat_to_noto)} нотокоинов ({cat_to_noto_status})\n\n"
            f"🔮 Магические коины → 🎵 Нотокоины:\n"
            f"2500 магических коинов = {int(2500 * exchange_rate_magic_to_noto)} нотокоинов ({magic_to_noto_status})\n"
        )

        await callback.message.answer(message_text)


async def exchange_callback_(callback: types.CallbackQuery):
    await callback.message.delete()
    data = callback.data
    if data == "exchange_cat_to_magic":
        await choose_amount(callback.message, "cat_to_magic")
    elif data == "exchange_magic_to_cat":
        await choose_amount(callback.message, "magic_to_cat")
    elif data == "exchange_cat_to_noto":
        await choose_amount(callback.message, "cat_to_noto")
    elif data == "exchange_magic_to_noto":
        await choose_amount(callback.message, "magic_to_noto")


async def choose_amount(message: types.Message, exchange_type: str):
    keyboard = InlineKeyboardMarkup(row_width=3)
    amounts = [100, 500, 1000, 2000, 5000, 10000]
    for amount in amounts:
        keyboard.insert(InlineKeyboardButton(str(amount), callback_data=f"amount_{exchange_type}_{amount}"))

    await message.answer(
        "Выберите сумму для обмена:",
        reply_markup=keyboard,
        parse_mode=types.ParseMode.MARKDOWN,
    )

async def amount_callback(callback: types.CallbackQuery):
    await callback.message.delete()  # Удаляем сообщение с кнопками выбора суммы
    try:
        data = callback.data.split("_")
        logging.info(f"Полученные данные: {data}")

        if len(data) < 4 or data[0] != "amount":
            logging.error(f"Неверный формат данных: {callback.data}")
            await callback.answer("Неверный формат данных. Попробуйте снова.")
            return

        exchange_type = f"{data[1]}_to_{data[3]}"
        amount = int(data[-1])

        logging.info(f"Тип обмена: {exchange_type}, сумма: {amount}")

        if amount not in [100, 500, 1000, 2000, 5000, 10000]:
            logging.error(f"Неверная сумма: {amount}")
            await callback.answer("Неверная сумма. Попробуйте снова.")
            return

        user_id = callback.from_user.id
        cursor.execute("SELECT cat_coins, magic_coins, notocoins FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            await callback.answer("У вас еще нет профиля. Получите кота, чтобы создать его!")
            return

        cat_coins, magic_coins, notocoins = user_data

        # Сохраняем chat_id для отправки сообщения
        chat_id = callback.message.chat.id

        if exchange_type == "magic_to_cat":
            if magic_coins < amount:
                await callback.answer(f"У вас недостаточно магических коинов. У вас {magic_coins}, а нужно {amount}.")
                return

            exchanged_cat_coins = int(amount / exchange_rate_cat_to_magic)
            cursor.execute("UPDATE users SET magic_coins = magic_coins - ?, cat_coins = cat_coins + ? WHERE user_id = ?", (amount, exchanged_cat_coins, user_id))
            conn.commit()
            await callback.bot.send_message(chat_id, f"Вы обменяли {amount} магических коинов на {exchanged_cat_coins} котокоинов.")
            logging.info(f"Обмен завершен: {amount} магических коинов на {exchanged_cat_coins} котокоинов.")

        elif exchange_type == "cat_to_magic":
            if cat_coins < amount:
                await callback.answer(f"У вас недостаточно котокоинов. У вас {cat_coins}, а нужно {amount}.")
                return

            exchanged_magic_coins = int(amount * exchange_rate_cat_to_magic)
            cursor.execute("UPDATE users SET cat_coins = cat_coins - ?, magic_coins = magic_coins + ? WHERE user_id = ?", (amount, exchanged_magic_coins, user_id))
            conn.commit()
            await callback.bot.send_message(chat_id, f"Вы обменяли {amount} котокоинов на {exchanged_magic_coins} магических коинов.")
            logging.info(f"Обмен завершен: {amount} котокоинов на {exchanged_magic_coins} магических коинов.")

        elif exchange_type == "cat_to_noto":
            if cat_coins < amount:
                await callback.answer(f"У вас недостаточно котокоинов. У вас {cat_coins}, а нужно {amount}.")
                return

            exchanged_notocoins = int(amount * exchange_rate_cat_to_noto)
            cursor.execute("UPDATE users SET cat_coins = cat_coins - ?, notocoins = notocoins + ? WHERE user_id = ?", (amount, exchanged_notocoins, user_id))
            conn.commit()
            await callback.bot.send_message(chat_id, f"Вы обменяли {amount} котокоинов на {exchanged_notocoins} нотокоинов.")
            logging.info(f"Обмен завершен: {amount} котокоинов на {exchanged_notocoins} нотокоинов.")

        elif exchange_type == "magic_to_noto":
            if magic_coins < amount:
                await callback.answer(f"У вас недостаточно магических коинов. У вас {magic_coins}, а нужно {amount}.")
                return

            exchanged_notocoins = int(amount * exchange_rate_magic_to_noto)
            cursor.execute("UPDATE users SET magic_coins = magic_coins - ?, notocoins = notocoins + ? WHERE user_id = ?", (amount, exchanged_notocoins, user_id))
            conn.commit()
            await callback.bot.send_message(chat_id, f"Вы обменяли {amount} магических коинов на {exchanged_notocoins} нотокоинов.")
            logging.info(f"Обмен завершен: {amount} магических коинов на {exchanged_notocoins} нотокоинов.")

        await callback.answer()

    except ValueError as e:
        logging.error(f"Ошибка при обработке суммы: {e}")
        await callback.answer("Произошла ошибка при обработке суммы. Убедитесь, что вы выбрали правильную сумму.")
    except Exception as e:
        logging.error(f"Ошибка в amount_callback: {e}")
        await callback.answer("Произошла ошибка. Попробуйте снова.")



def register_valution_trade_handlers(dp: Dispatcher):
    dp.register_message_handler(exchange_command, commands=["exchange"])
    dp.register_callback_query_handler(exchange_callback_, lambda c: c.data.startswith("exchange_"))
    dp.register_callback_query_handler(amount_callback, lambda c: c.data.startswith("amount_"))
    dp.register_callback_query_handler(exchange_callback)