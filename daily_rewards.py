import logging
import sqlite3
import time
from aiogram import types, Dispatcher
from database import get_db_connection

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Подключение к базе данных
conn = get_db_connection()
cursor = conn.cursor()

# Создаем таблицу для отслеживания времени последнего использования команды /daily
cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_rewards (
    user_id INTEGER PRIMARY KEY,
    last_daily_time INTEGER DEFAULT 0
)
''')
conn.commit()

# Создаем таблицу для отслеживания страйков
cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_strikes (
    user_id INTEGER PRIMARY KEY,
    strike_count INTEGER DEFAULT 0,
    last_strike_time INTEGER DEFAULT 0
)
''')
conn.commit()

async def daily_command(message: types.Message):
    user_id = message.from_user.id
    current_time = int(time.time())

    # Проверяем, когда пользователь последний раз использовал команду /daily
    cursor.execute("SELECT last_daily_time FROM daily_rewards WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        last_daily_time = result[0]
        if current_time - last_daily_time < 86400:  # 86400 секунд = 24 часа
            remaining_time = 86400 - (current_time - last_daily_time)
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            await message.answer(f"Вы уже получали награду сегодня. Попробуйте снова через {hours} часов {minutes} минут.")
            return
    else:
        # Если пользователь еще не использовал команду /daily, добавляем запись в таблицу
        cursor.execute("INSERT INTO daily_rewards (user_id, last_daily_time) VALUES (?, ?)", (user_id, current_time))
        conn.commit()

    # Проверяем страйк
    cursor.execute("SELECT strike_count, last_strike_time FROM daily_strikes WHERE user_id = ?", (user_id,))
    strike_data = cursor.fetchone()

    if strike_data:
        strike_count, last_strike_time = strike_data
        if current_time - last_strike_time >= 86400:  # Если прошло больше 24 часов, сбрасываем страйк
            strike_count = 0
            cursor.execute("UPDATE daily_strikes SET strike_count = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
    else:
        strike_count = 0
        cursor.execute("INSERT INTO daily_strikes (user_id, strike_count, last_strike_time) VALUES (?, ?, ?)", (user_id, strike_count, current_time))
        conn.commit()

    # Увеличиваем страйк
    strike_count += 1
    cursor.execute("UPDATE daily_strikes SET strike_count = ?, last_strike_time = ? WHERE user_id = ?", (strike_count, current_time, user_id))
    conn.commit()

    # Рассчитываем награду
    base_reward = 500
    if strike_count >= 3:
        bonus_percentage = 5 + (strike_count - 3) * 2
        reward = int(base_reward * (1 + bonus_percentage / 100))
    else:
        reward = base_reward

    # Выдаем награду
    cursor.execute("UPDATE users SET cat_coins = cat_coins + ?, magic_coins = magic_coins + ?, note_coins = note_coins + ? WHERE user_id = ?", (reward, reward, reward, user_id))
    conn.commit()

    # Обновляем время последнего использования команды /daily
    cursor.execute("UPDATE daily_rewards SET last_daily_time = ? WHERE user_id = ?", (current_time, user_id))
    conn.commit()

    await message.answer(
        f"🎉 Вы получили ежедневную награду!\n"
        f"🐱 +{reward} котокоинов\n"
        f"🔮 +{reward} магических коинов\n"
        f"🎵 +{reward} нотокоинов\n"
        f"Приходите завтра за новой наградой!"
    )

async def daily_strike_command(message: types.Message):
    user_id = message.from_user.id

    # Проверяем страйк
    cursor.execute("SELECT strike_count, last_strike_time FROM daily_strikes WHERE user_id = ?", (user_id,))
    strike_data = cursor.fetchone()

    if strike_data:
        strike_count, last_strike_time = strike_data
        current_time = int(time.time())
        if current_time - last_strike_time >= 86400:  # Если прошло больше 24 часов, сбрасываем страйк
            strike_count = 0
            cursor.execute("UPDATE daily_strikes SET strike_count = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
        await message.answer(f"Ваш текущий страйк: {strike_count}")
    else:
        await message.answer("У вас нет страйка.")

def register_daily_handlers(dp: Dispatcher):
    dp.register_message_handler(daily_command, commands=["daily"])
    dp.register_message_handler(daily_strike_command, commands=["daily_strike"])