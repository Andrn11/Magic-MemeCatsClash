from aiogram import Dispatcher, types
import sqlite3
import logging
import time
from banned_words import BANNED_WORDS  # Импортируем список запрещенных слов

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Подключение к базе данных
from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Добавление столбца name_timer_start, если он ещё не существует
def add_name_timer_start_column():
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        if "name_timer_start" not in [column[1] for column in columns]:
            cursor.execute("ALTER TABLE users ADD COLUMN name_timer_start INTEGER DEFAULT 0")
            conn.commit()
            logging.info("Столбец name_timer_start добавлен в таблицу users.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении столбца name_timer_start: {e}")

add_name_timer_start_column()

# Функция для проверки на запрещенные слова
def contains_banned_words(text):
    text_lower = text.lower()
    for word in BANNED_WORDS:
        if word in text_lower:
            return True
    return False

# Команда /name
async def name_command(message: types.Message):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личных сообщениях. Пожалуйста, напишите мне в личку.")
        return

    user_id = message.from_user.id
    current_time = int(time.time())

    cursor.execute(
        "UPDATE users SET name_timer_start = ? WHERE user_id = ?",
        (current_time, user_id),
    )
    conn.commit()

    await message.answer("Пожалуйста, введите ваше имя. Имя должно начинаться с символа '-'.")

# Команда /rename
async def rename_command(message: types.Message):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личных сообщениях. Пожалуйста, напишите мне в личку.")
        return

    user_id = message.from_user.id
    current_time = int(time.time())

    cursor.execute(
        "UPDATE users SET name_timer_start = ? WHERE user_id = ?",
        (current_time, user_id),
    )
    conn.commit()

    await message.answer("Пожалуйста, введите новое имя. Имя должно начинаться с символа '-'.")

# Обработка ввода имени
async def process_name(message: types.Message):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личных сообщениях. Пожалуйста, напишите мне в личку.")
        return

    user_id = message.from_user.id
    current_time = int(time.time())

    # Проверяем, была ли вызвана команда /name или /rename
    cursor.execute("SELECT name_timer_start FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    name_timer_start = result[0] if result else 0

    # Если команда /name или /rename не была вызвана, прерываем выполнение
    if name_timer_start == 0:
        return

    # Проверяем, прошло ли более 30 секунд с момента вызова команды
    time_elapsed = current_time - name_timer_start
    if time_elapsed > 50:
        # Если прошло больше 50 секунд, прерываем выполнение
        return
    elif time_elapsed > 30:
        # Если прошло больше 30 секунд, но меньше 50, просим начать заново
        await message.answer("30 секунд прошло. Попробуйте снова, начиная с команды /rename.")
        return

    name = message.text
    if not name.startswith('-'):
        await message.answer("Имя должно начинаться с символа '-'.")
        return

    name_without_dash = name[1:]

    # Логирование для отладки
    logging.info(f"Имя без дефиса: {name_without_dash}")

    # Проверка длины имени (не более 10 символов)
    if len(name_without_dash) > 10:
        await message.answer("Имя должно содержать не более 10 символов. Пожалуйста, введите другое имя.")
        return

    # Проверка на запрещенные слова
    if contains_banned_words(name_without_dash):
        await message.answer("Использование запрещенных слов недопустимо. Пожалуйста, введите другое имя.")
        return

    # Проверка, состоит ли имя только из букв "а" (в любом регистре)
    if all(char.lower() == 'a' for char in name_without_dash):
        logging.info("Имя состоит только из букв 'а'")  # Логирование для отладки

        # Обновление имени в базе данных
        cursor.execute(
            "UPDATE users SET username = ?, name_timer_start = 0 WHERE user_id = ?",
            (name_without_dash, user_id),
        )
        conn.commit()

        await message.delete()
        await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)

        # Стандартное сообщение
        await message.answer(
            f"Спасибо, {name_without_dash}! Теперь вы можете использовать бота:\n"
            "Напишите 'кот' для карточки кота 🐱\n"
            "Напишите 'магическая битва' для магической карты 🔮\n"
            "Напишите /help для помощи 📚\n"
            "https://t.me/MagicAndMemeCatsClash - Наш канал бота\n"
        )

        # Дополнительное сообщение, если имя состоит только из букв "а"
        await message.answer("А по оригинальний имя не мог придумать?")
        return  # Прерываем выполнение функции здесь

    # Если имя не состоит только из букв "а", обновляем имя и отправляем стандартное сообщение
    logging.info("Имя не состоит только из букв 'а'")  # Логирование для отладки

    cursor.execute(
        "UPDATE users SET username = ?, name_timer_start = 0 WHERE user_id = ?",
        (name_without_dash, user_id),
    )
    conn.commit()

    await message.delete()
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)

    await message.answer(
        f"Спасибо, {name_without_dash}! Теперь вы можете использовать бота:\n"
        "Напишите 'кот' для карточки кота 🐱\n"
        "Напишите 'магическая битва' для магической карты 🔮\n"
        "Напишите /help для помощи 📚\n"
        "https://t.me/MagicAndMemeCatsClash - Наш канал бота\n"
    )
async def start_command(message: types.Message):

    user_id = message.from_user.id
    current_time = int(time.time())

    cursor.execute("SELECT user_id, username FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.execute(
            "INSERT INTO users (user_id, name_timer_start) VALUES (?, ?)",
            (user_id, current_time),
        )
        conn.commit()
        logging.info(f"Пользователь {user_id} добавлен в базу данных.")

        await message.answer("Привет! Добро пожаловать! 🐱\nПожалуйста, напишите своё имя. Имя должно начинаться с символа '-'.")
    else:
        username = user_data[1]
        if username:
            await message.answer(
                f"С возвращением, {username}! Вы уже ввели имя.\n"
                "Напишите 'кот' для карточки кота 🐱\n"
                "Напишите 'магическая битва' для магической карты 🔮\n"
                "Напишите /help для помощи 📚\n"
                "https://t.me/MagicAndMemeCatsClash - Наш канал бота\n"
            )
        else:
            cursor.execute(
                "UPDATE users SET name_timer_start = ? WHERE user_id = ?",
                (current_time, user_id),
            )
            conn.commit()
            await message.answer("Пожалуйста, введите ваше имя. Имя должно начинаться с символа '-'.")

# Регистрация обработчиков
def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_message_handler(name_command, commands=["name"])
    dp.register_message_handler(rename_command, commands=["rename"])
    dp.register_message_handler(process_name, lambda message: message.chat.type == "private")